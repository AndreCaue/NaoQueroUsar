import logging
import uuid
from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.client_ip import UNKNOWN_IP, resolve_client_ip
from app.core.config import get_settings
from app.core.ratelimit import chat_search_limit, limiter, reveal_limit
from app.crud import get_published, list_published
from app.db.session import get_session
from app.deps import get_turnstile_verifier
from app.schemas.chat import ChatSearchRequest, ChatSearchResponse, ChatSearchResults
from app.schemas.job import (
    ContactRevealResponse,
    JobListResponse,
    JobPublic,
    ReportRequest,
    RevealRequest,
)
from app.services.cities import resolve_city, resolve_sort
from app.services.intent.mapper import build_empty_intent
from app.services.intent.parser import extract_and_map_intent
from app.services.intent.schema import IntentContract
from app.services.turnstile import TurnstileVerifier, turnstile_error_detail

# Mounted by router.py without an extra prefix, so these resolve to
# /api/v1/public/jobs and /api/v1/public/jobs/{id}. NO auth dependency:
# the public read surface is anonymous by design (D-16).
router = APIRouter(prefix="/public", tags=["public"])

logger = logging.getLogger(__name__)

# Reports are relayed to the master through the log only — the reason is
# truncated and stripped of control characters so a report cannot forge log
# lines or smuggle personal data into a persistent sink (T-06-05).
_LOG_REASON_MAX = 500

_CHAT_GUIDANCE_LLM = (
    "Não foi possível interpretar sua busca agora. "
    "Tente usar palavras-chave na busca manual (ex.: cargo, empresa ou cidade)."
)
_CHAT_GUIDANCE_NO_PARAMS = (
    "Não consegui identificar filtros na sua mensagem. "
    "Use palavras-chave na busca manual ou informe cargo/cidade/ordenação."
)
_CHAT_GUIDANCE_APPROX = (
    "Filtros como salário/modalidade/contrato/senioridade não possuem filtro estruturado garantido; "
    "quando possível foi usada apenas aproximação textual. "
    "Cidades fora da lista suportada (São Paulo, Rio de Janeiro, Belo Horizonte, Remoto) "
    "não são inferidas automaticamente."
)
_APPROX_LIMITATION_CODES = {
    "unsupported_structured_filter",
    "textual_approximation_in_q",
    "non_native_fields_limited",
    "not_in_whitelist",
}


def _log_safe(value: str | None) -> str | None:
    """Collapse all whitespace/control chars and truncate for the log."""
    if value is None:
        return None
    return " ".join(value.split())[:_LOG_REASON_MAX]


def _chat_degraded_contract(
    message: str | None, reason_code: str, guidance: str, limitation: str | None = None
) -> IntentContract:
    """Build a safe degraded interpretation contract with no automatic results."""
    contract = build_empty_intent(message, reason_code="no_extractable_params")
    contract = contract.model_copy(deep=True)
    contract.applied_params.q = None
    contract.applied_params.city = None
    contract.applied_params.sort = None
    if limitation and limitation not in contract.limitations:
        contract.limitations.append(limitation)
    if reason_code == "llm_unavailable":
        contract.limitations.append("llm_unavailable")
    elif reason_code == "timeout":
        contract.limitations.append("llm_timeout")
    elif reason_code == "no_extractable_params":
        contract.limitations.append("no_extractable_params")
    contract.meta = {
        **(contract.meta or {}),
        "degraded": True,
        "degradation_reason": reason_code,
        "guidance": guidance,
    }
    for fs in contract.field_statuses:
        if getattr(fs.status, "value", fs.status) in {"aplicado", "aproximado"}:
            fs.status = "ignorado"
            fs.applied = None
        if reason_code in {"llm_unavailable", "timeout"}:
            fs.reason_code = reason_code
    return contract


def _is_effectively_no_params(contract: IntentContract) -> bool:
    applied = contract.applied_params
    if applied.q or applied.city or applied.sort:
        return False
    for fs in contract.field_statuses:
        status = getattr(fs.status, "value", fs.status)
        if status in {"aplicado", "aproximado"}:
            return False
    return True


def _apply_approx_guidance(contract: IntentContract) -> IntentContract:
    """Keep approximation/limitation signals explicit and user-facing (pt-BR)."""
    has_approx = False
    for lim in contract.limitations or []:
        if lim in _APPROX_LIMITATION_CODES:
            has_approx = True
            break
    if not has_approx:
        for fs in contract.field_statuses:
            status = getattr(fs.status, "value", fs.status)
            if status == "aproximado" or fs.reason_code in _APPROX_LIMITATION_CODES:
                has_approx = True
                break
    if not has_approx:
        return contract
    meta = deepcopy(contract.meta or {})
    if not meta.get("guidance"):
        meta["guidance"] = _CHAT_GUIDANCE_APPROX
    contract.meta = meta
    if _CHAT_GUIDANCE_APPROX not in (contract.limitations or []):
        contract.limitations = list(contract.limitations or []) + [_CHAT_GUIDANCE_APPROX]
    return contract

# ``city`` aliases accepted from the URL (D-05/D-06b): the slug, the canonical
# DB spelling and the accented label all resolve to the value actually stored
# in ``jobs.city`` — which is the accented form of ``ALLOWED_CITIES`` in
# ``app/services/extraction/extractor.py``. Unknown values are ignored (200).
# The table itself lives in ``app.services.cities`` (shared with the admin).


@router.get("/jobs", response_model=JobListResponse)
async def list_public_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    q: str | None = Query(None, max_length=80),
    city: str | None = Query(None, max_length=40),
    sort: str = Query("recentes", max_length=20),
    session: AsyncSession = Depends(get_session),
) -> JobListResponse:
    """List published, non-expired jobs (contact-free), filtered and sorted.

    ``q`` searches title + company + activities + requirements, accent- and
    case-insensitively (SRCH-01/D-03). ``city`` is an independent filter
    combined with AND — it never replaces ``q`` (SRCH-02/D-05). ``sort`` is
    ``recentes`` (default) or ``antigas`` (SRCH-03/D-06). Unknown ``city``
    values are ignored and unknown ``sort`` values fall back to ``recentes`` —
    a bad URL never produces a 400. Items and ``total`` share one predicate
    list (04-RESEARCH Pattern 3).
    """
    term = q.strip() if q else None
    if not term:
        term = None

    items, total = await list_published(
        session,
        page=page,
        limit=limit,
        q=term,
        city=resolve_city(city),
        sort=resolve_sort(sort),
    )
    return JobListResponse(
        items=[JobPublic.model_validate(job) for job in items],
        page=page,
        limit=limit,
        total=total,
    )



@router.get("/jobs/{job_id}", response_model=JobPublic)
async def get_public_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> JobPublic:
    """Return public detail for a published, non-expired job; 404 otherwise (D-17)."""
    # Phase boundary (D-18): no reveal/contact endpoint here — that is Phase 3.
    job = await get_published(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return JobPublic.model_validate(job)


@router.post("/jobs/{job_id}/reveal-contact", response_model=ContactRevealResponse)
@limiter.limit(reveal_limit)
async def reveal_contact(
    request: Request,
    job_id: uuid.UUID,
    payload: RevealRequest,
    session: AsyncSession = Depends(get_session),
    verifier: TurnstileVerifier = Depends(get_turnstile_verifier),
) -> ContactRevealResponse:
    """Reveal the contact of a published job behind the anti-bot gate.

    This is the **only** way a contact leaves the database (PUBL-05): the
    public list/detail stay contact-free.

    The order of the checks is the contract (D-03):

    1. **rate limit** — applied by the decorator, per resolved IP (D-05/D-10);
    2. **job lookup** — ``published`` and not expired, otherwise 404. It comes
       *before* the Turnstile call so a made-up UUID never spends a Cloudflare
       verification;
    3. **Siteverify** — the token is checked server-side, with the ``reveal``
       action binding (a token minted for ``login`` is refused);
    4. **200** — the contact, raw.

    A failed verification is **always** a 403, never a degraded 200 (D-13):
    the copy distinguishes "the challenge was refused" from "the verification
    itself is unavailable" (``turnstile_error_detail``).

    The Siteverify ``hostname`` is deliberately **not** checked: it changes
    between localhost and production, and the action binding already prevents
    a token from being reused across flows. Phase 4 must not invent that
    check.
    """
    job = await get_published(session, job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail="Vaga não encontrada ou expirada."
        )

    ip = resolve_client_ip(request)
    result = await verifier.verify(
        payload.cf_token,
        None if ip == UNKNOWN_IP else ip,
        expected_action="reveal",
        idempotency_key=str(uuid.uuid4()),
    )
    if not result.success:
        raise HTTPException(
            status_code=403, detail=turnstile_error_detail(result.error_codes)
        )

    return ContactRevealResponse(
        job_id=job.id,
        contact_email=job.contact_email,
        contact_phone=job.contact_phone,
    )


@router.post("/chat-search", response_model=ChatSearchResponse)
@limiter.limit(chat_search_limit)
async def chat_search(
    request: Request,
    payload: ChatSearchRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatSearchResponse:
    """Busca pública por linguagem natural com interpretação transparente (API-01..03)."""
    settings = get_settings()
    chat_timeout = getattr(settings, "CHAT_SEARCH_INTENT_TIMEOUT_SECONDS", 12)

    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Mensagem inválida para busca por chat.")

    try:
        try:
            contract = await extract_and_map_intent(
                payload.message, settings, timeout_seconds=chat_timeout
            )
        except Exception as exc:  # noqa: BLE001 - fallback controlado (D-08/D-09)
            logger.warning("chat_search_intent_failed", extra={"reason": type(exc).__name__})
            reason_code = "timeout" if "timeout" in str(exc).lower() else "llm_unavailable"
            guidance = _CHAT_GUIDANCE_LLM
            degraded = _chat_degraded_contract(
                payload.message,
                reason_code,
                guidance,
                limitation=("llm_timeout" if reason_code == "timeout" else "llm_unavailable"),
            )
            return ChatSearchResponse(
                interpretation=degraded,
                results=ChatSearchResults(
                    items=[], page=payload.page, limit=payload.limit, total=0
                ),
            )

        if contract is None or _is_effectively_no_params(contract):
            degraded = _chat_degraded_contract(
                payload.message,
                "no_extractable_params",
                _CHAT_GUIDANCE_NO_PARAMS,
                limitation="no_extractable_params",
            )
            return ChatSearchResponse(
                interpretation=degraded,
                results=ChatSearchResults(
                    items=[], page=payload.page, limit=payload.limit, total=0
                ),
            )

        contract = _apply_approx_guidance(contract)
        applied = contract.applied_params
        items, total = await list_published(
            session,
            page=payload.page,
            limit=payload.limit,
            q=applied.q,
            city=applied.city,
            sort=(applied.sort or "recentes"),
        )
        return ChatSearchResponse(
            interpretation=contract,
            results=ChatSearchResults(
                items=[JobPublic.model_validate(job) for job in items],
                page=payload.page,
                limit=payload.limit,
                total=total,
            ),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("chat_search_unexpected_error")
        raise HTTPException(
            status_code=500, detail="Erro interno ao processar a busca por chat."
        )


@router.post("/jobs/{job_id}/report")
@limiter.limit("5/minute")
async def report_job(
    request: Request,
    job_id: uuid.UUID,
    payload: ReportRequest | None = None,
) -> dict[str, str]:
    """Accept an anonymous report and log it — nothing is persisted.

    Accept-and-log by design (TRST-02, D-06): the endpoint never reveals
    whether the job exists or is published, so it answers
    ``{"status": "ok"}`` for any well-formed payload instead of 404 —
    a visitor (or a scraper walking ids) cannot use it as an enumeration
    oracle. The report goes to the structured log only: no table, no
    migration, no automatic follow-up; the master reviews the logs.

    Rate-limited per resolved IP (5/minute) — the endpoint is anonymous and
    unauthenticated by design, so without a throttle it is a log-flooding /
    disk-exhaustion vector on a free-tier host (WR-01). Over the limit the
    caller gets the shared 429 (pt-BR, ``Retry-After``).
    """
    reason = payload.reason if payload else None
    # key=value pairs: the project's formatter is plain text, so the fields
    # travel in the message itself (greppable, one line per report).
    logger.info(
        "job_report job_id=%s reason=%s ip=%s",
        str(job_id),
        _log_safe(reason),
        resolve_client_ip(request),
    )
    return {"status": "ok"}
