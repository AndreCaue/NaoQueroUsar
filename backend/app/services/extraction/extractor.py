"""Extraction orchestrator: chunking → throttled strict Groq calls → grounding
→ D-05/D-06 classification → ``ExtractionResult``.

**This module never touches the DB or FastAPI.** D-03 (all-or-nothing) is the
caller's single transaction over ``result.kept`` — persistence and the HTTP
summary belong to plan 03.

Decision → code map:

- **D-03:** pure orchestration; nothing is saved here (atomic commit upstream).
- **D-05:** only a missing/ungrounded title or the absence of BOTH contacts
  discard a row; every other defect lands in ``save_needs_review``.
- **D-06:** obvious city variants (``CITY_MAP``) normalize to the canonical
  set; anything else keeps its raw text and is flagged ``needs_review``.
- **D-07:** a detected-count pre-pass vs the extracted total sets
  ``divergent``; the extracted rows are still returned (the summary alert is
  built upstream, plan 03). The count request is best-effort — any failure
  sets ``detected_count = None`` and never blocks the pipeline.
- **D-08:** every discarded row carries ``reason`` + ``snippet`` (and the raw
  LLM row) so the master can fix and re-insert manually.
- **T-02-05 (hallucination):** grounding via ``is_grounded`` on every field;
  critical ungrounded → discard, minor ungrounded → cleared + ``needs_review``.
- **T-02-06 (DoS/cost):** byte cap, ``EXTRACT_MAX_JOBS`` cap, token-budgeted
  chunks, inter-chunk pacing, and the client's bounded retries/dead models.

Count pre-pass (EXTR-09): a single-chunk paste is one Groq call — the
extracted count IS the result, so a separate count request is pointless
(``detected_count`` equals the extraction). Multi-chunk pastes get a cheap
``estimate_job_count`` request over the FULL text first.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable

from app.services.extraction.chunking import chunk_text
from app.services.extraction.client import (
    _build_real_client,
    call_extraction,
    model_chain,
    strip_markdown_fences,
    wrap_untrusted,
)
from app.services.extraction.grounding import is_grounded, normalize_for_grounding
from app.services.extraction.phones import normalize_phone
from app.services.extraction.schema import ExtractedJobRaw, JobCandidate

# --- D-06 city table --------------------------------------------------------

ALLOWED_CITIES: tuple[str, ...] = (
    "São Paulo",
    "Rio de Janeiro",
    "Belo Horizonte",
    "Remoto",
)

# Obvious variants only — deliberately small and explicit (D-06). Canonical
# spellings (any case, with accents) are matched by ALLOWED_CITIES below.
CITY_MAP: dict[str, str] = {
    "sp": "São Paulo",
    "sao paulo": "São Paulo",
    "rj": "Rio de Janeiro",
    "rio": "Rio de Janeiro",
    "rio de janeiro": "Rio de Janeiro",
    "bh": "Belo Horizonte",
    "belo horizonte": "Belo Horizonte",
    "remoto": "Remoto",
    "home office": "Remoto",
}

_STATE_SUFFIX = re.compile(r"\s*/\s*[a-zA-Z]{2}\s*$")

SNIPPET_CAP = 300
SNIPPET_RADIUS = 150

# --- DB column widths (app/models/job.py) -----------------------------------
# WR-01: clip the fields the LLM returns at the column width before they ever
# reach persistence, so one over-long string can never abort the entire
# single-transaction batch with ``StringDataRightTruncation``. The limits are
# deliberately NOT enforced on ``ExtractedJobRaw``: a Pydantic ValidationError
# there triggers the client's schema-repair turn and, on a second failure,
# fails the WHOLE batch — the exact failure mode this avoids.
TITLE_MAX = 200
COMPANY_MAX = 150
SALARY_MAX = 80
BENEFITS_MAX = 255
CITY_MAX = 80
EMAIL_MAX = 254

COUNT_JSON_SCHEMA = {
    "type": "object",
    "properties": {"count": {"type": "integer", "minimum": 0}},
    "required": ["count"],
    "additionalProperties": False,
}


class CandidateOutcome(str, Enum):
    """What the caller should do with a candidate (plan 03 maps to JobStatus)."""

    save = "save"
    save_needs_review = "save_needs_review"
    discard = "discard"


@dataclass
class ExtractionResult:
    """Classified, grounded candidates awaiting persistence (never published)."""

    kept: list[tuple[JobCandidate, CandidateOutcome]]
    discarded: list[dict]
    detected_count: int | None
    extracted_count: int
    truncated: bool
    divergent: bool
    model_used: str
    chunks: int


def normalize_city(raw_city: str | None) -> str:
    """Map an obvious variant onto the canonical city (D-06); else return the raw text."""
    raw = (raw_city or "").strip()
    key = _STATE_SUFFIX.sub("", raw.lower()).strip()
    key = " ".join(key.split())
    if key in CITY_MAP:
        return CITY_MAP[key]
    for canonical in ALLOWED_CITIES:
        if key == canonical.lower():
            return canonical
    return raw


def _snippet_for(title: str, chunk: str) -> str:
    """±150 chars around the title match in the chunk (fallback: first 300)."""
    text = chunk.strip()
    haystack = text.lower()
    needle = (title or "").lower().strip()
    idx = haystack.find(needle) if needle else -1
    if idx < 0:
        return text[:SNIPPET_CAP]
    start = max(0, idx - SNIPPET_RADIUS)
    end = min(len(text), idx + len(needle) + SNIPPET_RADIUS)
    if end - start > SNIPPET_CAP:
        end = start + SNIPPET_CAP
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"


def _digits(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def _clip(
    value: str | None,
    limit: int,
    field: str,
    reasons: list[str],
) -> str | None:
    """Strip + cap an optional field at its DB column width (WR-01).

    Blank values become ``None`` (so ``""`` is never persisted as data) and a
    value that had to be cut is flagged in ``reasons`` so the row lands in
    ``needs_review`` instead of being saved silently altered.
    """
    text = (value or "").strip()
    if not text:
        return None
    if len(text) > limit:
        reasons.append(
            f"campo '{field}' truncado em {limit} caracteres (limite do banco)"
        )
        return text[:limit]
    return text


def _process_row(row: ExtractedJobRaw, chunk: str) -> tuple[JobCandidate | None, CandidateOutcome, str | None]:
    """Ground + classify one LLM row against its source chunk.

    Returns ``(candidate, outcome, discard_reason)``; ``candidate`` is ``None``
    when the row is discarded (D-05: only title/contact failures discard).
    """
    needs_review_reasons: list[str] = []
    snippet = _snippet_for(row.title, chunk)
    raw_city = (row.city or "").strip()
    # WR-01: cap the city at its column width and treat a blank city as missing.
    city = _clip(normalize_city(raw_city), CITY_MAX, "city", needs_review_reasons) or ""

    haystack = normalize_for_grounding(chunk)
    chunk_digits = _digits(chunk)

    # --- grounding: critical fields (title, contacts) -----------------------
    title = (row.title or "").strip()
    if not title:
        return None, CandidateOutcome.discard, "sem título"
    if not is_grounded(title, haystack):
        return (
            None,
            CandidateOutcome.discard,
            "título não encontrado no texto-fonte (possível alucinação)",
        )
    if len(title) > TITLE_MAX:
        # WR-01: ground the full title first, then cap it at the column width.
        needs_review_reasons.append(
            f"campo 'title' truncado em {TITLE_MAX} caracteres (limite do banco)"
        )
        title = title[:TITLE_MAX]

    # "" is absence of contact, not a contact (CR-01): normalize it to None so
    # the D-05 check below discards the row instead of handing it to the DB,
    # where the ``at_least_one_contact`` CHECK would abort the WHOLE batch.
    contact_email = (row.contact_email or "").strip() or None
    if contact_email and not is_grounded(contact_email, haystack):
        contact_email = None  # ungrounded contact is cleared (T-02-05)
    if contact_email is not None and len(contact_email) > EMAIL_MAX:
        # WR-01: never persist a truncated address — it would be unusable.
        contact_email = None

    contact_phone = normalize_phone(row.contact_phone)
    if contact_phone is not None:
        raw_digits = _digits(row.contact_phone)
        # WR-03: the LLM often canonicalizes to +55…, while the source only
        # carries the national number — ground the national portion too.
        national = (
            contact_phone[3:] if contact_phone.startswith("+55") else contact_phone
        )
        grounded = (
            is_grounded(contact_phone, haystack)
            or (bool(raw_digits) and raw_digits in chunk_digits)
            or (len(national) >= 10 and national in chunk_digits)
        )
        if not grounded:
            contact_phone = None

    if contact_email is None and contact_phone is None:
        return None, CandidateOutcome.discard, "sem contato válido"

    # --- grounding: minor fields (cleared + needs_review, D-05) -------------
    minor: dict[str, str | None] = {
        "company": row.company,
        "activities": row.activities,
        "requirements": row.requirements,
        "salary": row.salary,
        "benefits": row.benefits,
    }
    for name, value in minor.items():
        if value and not is_grounded(value, haystack):
            minor[name] = None
            needs_review_reasons.append(f"campo '{name}' não confere com o texto-fonte")

    # WR-01: cap the width-limited minor columns (activities/requirements are
    # Text columns and need no clipping).
    minor["company"] = _clip(minor["company"], COMPANY_MAX, "company", needs_review_reasons)
    minor["salary"] = _clip(minor["salary"], SALARY_MAX, "salary", needs_review_reasons)
    minor["benefits"] = _clip(
        minor["benefits"], BENEFITS_MAX, "benefits", needs_review_reasons
    )

    # City grounding (D-06): try the RAW form first, then the MAPPED canonical
    # ("SP" in the source ~ "São Paulo"; "São Paulo" in the source ~ mapped
    # value). Ungrounded as either → needs_review (the value stays raw anyway,
    # since an unmappable city is never in ALLOWED_CITIES).
    if raw_city and not (
        is_grounded(raw_city, haystack) or is_grounded(city, haystack)
    ):
        needs_review_reasons.append("campo 'city' não confere com o texto-fonte")

    candidate = JobCandidate(
        title=title,
        company=minor["company"],
        activities=minor["activities"],
        requirements=minor["requirements"],
        salary=minor["salary"],
        benefits=minor["benefits"],
        city=city,
        contact_email=contact_email,
        contact_phone=contact_phone,
        source_snippet=snippet,
        raw_city=raw_city,
    )

    # WR-01: a blank city is a MISSING city (never a silent save); anything
    # else outside the canonical set keeps its raw text and needs review (D-06).
    if not raw_city:
        needs_review_reasons.append("cidade ausente ou vazia no texto-fonte")
    elif city not in ALLOWED_CITIES:
        needs_review_reasons.append("cidade fora do conjunto permitido (D-06)")

    if needs_review_reasons:
        return candidate, CandidateOutcome.save_needs_review, None
    return candidate, CandidateOutcome.save, None


async def estimate_job_count(
    text: str,
    settings: Any,
    *,
    client: Any | None = None,
) -> int | None:
    """Cheap ``{"count": n}`` pre-pass over the FULL text (EXTR-09, D-07).

    Best-effort: ANY failure (network, schema, model churn) returns ``None``
    so the divergence check is skipped without ever blocking the pipeline.

    No pacing/retry ``sleep`` seam lives here (IN-01): this is a single
    best-effort call per extraction, never part of the paced chunk loop.
    """
    try:
        if client is None:
            client = _build_real_client(settings)
    except Exception:
        return None

    messages = [
        {
            "role": "system",
            "content": (
                "Você conta vagas de emprego em pt-BR de textos informais de "
                "grupos de WhatsApp/Telegram. Retorne APENAS JSON no formato "
                '{"count": <número de vagas no texto>}.'
            ),
        },
        {
            "role": "user",
            "content": wrap_untrusted(text),
        },
    ]

    for model in model_chain(settings):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "contagem_vagas",
                        "strict": True,
                        "schema": COUNT_JSON_SCHEMA,
                    },
                },
                temperature=0,
                timeout=settings.GROQ_TIMEOUT_SECONDS,
            )
            content = strip_markdown_fences(
                response.choices[0].message.content or "{}"
            )
            count = int(json.loads(content)["count"])
            return count if count >= 0 else None
        except Exception:
            continue  # best-effort: try the next model, then give up
    return None


async def extract_jobs(
    text: str,
    settings: Any,
    *,
    client: Any | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> ExtractionResult:
    """Turn raw pasted text into classified, grounded candidates.

    ``client`` is the duck-typed Groq seam (tests inject ``FakeGroq``);
    ``sleep`` is injectable so tests never wait on the pacing delay.
    Raises ``ValueError`` (pt-BR) for empty/oversized input and
    ``ExtractionAPIError`` when every model fails.

    One client is built for the whole extraction and closed afterwards
    (IN-02): a per-chunk ``AsyncGroq`` leaked one connection pool per chunk.
    An injected client belongs to the caller and is never closed here.
    """
    if not text or not text.strip():
        raise ValueError("Texto vazio — cole o conteúdo de uma ou mais vagas.")

    byte_len = len(text.encode("utf-8"))
    if byte_len > settings.EXTRACT_MAX_TEXT_BYTES:
        raise ValueError(
            f"Texto muito grande: {byte_len} bytes (limite "
            f"{settings.EXTRACT_MAX_TEXT_BYTES}). Divida o conteúdo e cole em "
            "partes."
        )

    owns_client = client is None
    if owns_client:
        client = _build_real_client(settings)
    try:
        return await _extract_with_client(text, settings, client=client, sleep=sleep)
    finally:
        if owns_client:
            await _close_quietly(client)


async def _close_quietly(client: Any) -> None:
    """Close a self-built provider client, ignoring a non-async ``close``."""
    close = getattr(client, "close", None)
    if close is None:
        return
    result = close()
    if inspect.isawaitable(result):
        await result


async def _extract_with_client(
    text: str,
    settings: Any,
    *,
    client: Any,
    sleep: Callable[[float], Awaitable[None]],
) -> ExtractionResult:
    chunks = chunk_text(text, settings.EXTRACT_CHUNK_MAX_TOKENS)

    # --- count pre-pass (EXTR-09 / D-07): only when it costs a real call ----
    detected_count: int | None = None
    if len(chunks) > 1:
        detected_count = await estimate_job_count(text, settings, client=client)

    # --- chunk loop: throttled strict calls ---------------------------------
    all_rows: list[tuple[ExtractedJobRaw, str]] = []
    finish_reasons: list[str] = []
    models_used: list[str] = []
    dead_models: set[str] = set()

    for index, chunk in enumerate(chunks):
        if index > 0:
            # Free-tier pacing (RPM 30): never sleep before the first call.
            await sleep(settings.EXTRACT_CHUNK_DELAY_SECONDS)
        raw = await call_extraction(
            chunk, settings, client=client, sleep=sleep, dead_models=dead_models
        )
        all_rows.extend((row, chunk) for row in raw.rows)
        finish_reasons.extend(raw.finish_reasons)
        # IN-05: the primary model can die mid-run, so report every distinct
        # model that actually produced rows (insertion order, deduplicated).
        if raw.model_used not in models_used:
            models_used.append(raw.model_used)

    extracted_count = len(all_rows)

    # --- grounding + D-05/D-06 classification -------------------------------
    kept: list[tuple[JobCandidate, CandidateOutcome]] = []
    discarded: list[dict] = []
    for row, chunk in all_rows:
        candidate, outcome, discard_reason = _process_row(row, chunk)
        if outcome is CandidateOutcome.discard:
            discarded.append(
                {
                    "reason": discard_reason,
                    "snippet": _snippet_for(row.title, chunk),
                    "raw": row.model_dump(),
                }
            )
        else:
            kept.append((candidate, outcome))

    # --- EXTRACT_MAX_JOBS cap over real rows (kept first) -------------------
    # IN-04: the overflow marker is metadata and does NOT consume one of the
    # cap slots, so exactly ``cap`` real rows survive and the reported count
    # matches the rows actually dropped (previously one extra kept row was
    # silently discarded while the alert under-reported the overflow).
    cap = settings.EXTRACT_MAX_JOBS
    total_rows = len(kept) + len(discarded)
    if total_rows > cap:
        overflow = total_rows - cap
        if len(kept) > cap:
            first_dropped = kept[cap][0].model_dump()
            kept = kept[:cap]
            discarded = []
        else:
            allowance = cap - len(kept)
            dropped_from_discarded = discarded[allowance:]
            first_dropped = (
                dropped_from_discarded[0]["raw"] if dropped_from_discarded else {}
            )
            discarded = discarded[:allowance]
        discarded.append(
            {
                "reason": (
                    f"excedeu o limite de {cap} vagas por extração — "
                    f"{overflow} linha(s) descartada(s) por segurança"
                ),
                "snippet": "",
                "raw": first_dropped,
            }
        )

    truncated = any(reason == "length" for reason in finish_reasons)
    divergent = detected_count is not None and detected_count != extracted_count

    return ExtractionResult(
        kept=kept,
        discarded=discarded,
        detected_count=detected_count,
        extracted_count=extracted_count,
        truncated=truncated,
        divergent=divergent,
        model_used=", ".join(models_used),
        chunks=len(chunks),
    )
