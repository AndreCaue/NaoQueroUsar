"""Deterministic, server-authoritative intent mapping (INT-03, D-01..D-12,D-15).

LLM output is treated as an untrusted candidate ("understood" proposal). This
module computes the final contract: normalized understood intent, per-field
statuses (aplicado/ignorado/aproximado + reason), and safe `applied_params`
compatible with public search (`list_published(q, city, sort)`).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.services.cities import resolve_city
from app.services.intent.schema import (
    AppliedParams,
    FieldAssessment,
    FieldStatus,
    IntentContract,
    IntentLLMOutput,
    IntentSalary,
    UnderstoodIntent,
)


_ALL_FIELDS = ("q", "city", "salary", "work_mode", "contract_type", "seniority", "sort")

_SORT_RECENT_RE = re.compile(r"\b(mais\s+recentes?|recentes?|mais\s+novas?|novas?)\b", re.IGNORECASE)
_SORT_OLD_RE = re.compile(r"\b(mais\s+antigas?|antigas?|mais\s+velhas?|velhas?)\b", re.IGNORECASE)

_GENERIC_Q_TERMS = {"vaga", "vagas", "emprego", "empregos", "trabalho", "trabalhos"}


def _strip_accents_lower(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    without = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without.lower()


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _has_explicit_sort_recent(text: str) -> bool:
    return bool(_SORT_RECENT_RE.search(text or ""))


def _has_explicit_sort_old(text: str) -> bool:
    return bool(_SORT_OLD_RE.search(text or ""))


def _detect_explicit_sort(raw_text: str) -> tuple[str | None, str | None]:
    """Return (sort, conflict_reason_code_or_none) based on explicit signals only."""
    text = raw_text or ""
    recent = _has_explicit_sort_recent(text)
    old = _has_explicit_sort_old(text)
    if recent and old:
        return None, "conflict_resolved"
    if old:
        return "antigas", None
    if recent:
        return "recentes", None
    return None, None


def _resolve_city_safe(raw_city: str | None, raw_text: str = "") -> tuple[str | None, str]:
    """Resolve city via whitelist/obvious-safe mentions. Returns (applied, reason_code)."""
    # Explicit candidate first
    if raw_city:
        normalized = _normalize_whitespace(raw_city).lower()
        # obvious safe remote/home-office mentions
        if normalized in {"home office", "home-office", "trabalho remoto", "remoto"}:
            return "Remoto", "normalized"
        # reject clear non-city modalities
        if normalized in {"hibrido", "híbrido", "presencial"}:
            return None, "not_in_whitelist"

        # Safe abbreviations / common aliases (whitelist only)
        abbr = _strip_accents_lower(normalized)
        abbr_map = {
            "sp": "São Paulo",
            "sao paulo": "São Paulo",
            "rj": "Rio de Janeiro",
            "rio": "Rio de Janeiro",
            "rio de janeiro": "Rio de Janeiro",
            "bh": "Belo Horizonte",
            "belo horizonte": "Belo Horizonte",
        }
        if abbr in abbr_map:
            return abbr_map[abbr], "normalized"

        resolved = resolve_city(raw_city)
        if resolved:
            return resolved, "normalized"
        return None, "not_in_whitelist"

    # Fallback: detect unequivocal remote mentions in raw text when candidate absent
    text_norm = _strip_accents_lower(raw_text or "")
    if re.search(r"\b(home[\s-]?office|trabalho\s+remoto|remoto)\b", text_norm):
        return "Remoto", "normalized"
    return None, "missing"


def _clean_q_terms(q: str | None) -> str | None:
    if q is None:
        return None
    value = _normalize_whitespace(q)
    if not value:
        return None
    tokens = value.split(" ")
    filtered: list[str] = []
    for tok in tokens:
        key = _strip_accents_lower(tok)
        # drop generic isolated noise terms
        if key in _GENERIC_Q_TERMS:
            continue
        # avoid polluting with standalone salary-like numeric tokens
        if re.fullmatch(r"r?\$?\d+([.,]\d+)?k?", key):
            # keep if mixed with letters? fullmatch means purely numeric-ish
            continue
        filtered.append(tok)
    result = _normalize_whitespace(" ".join(filtered))
    return result or None


def _collect_native_approx_terms(candidate: IntentLLMOutput) -> list[str]:
    terms: list[str] = []
    if candidate.seniority and (candidate.seniority.value or candidate.seniority.raw):
        val = (candidate.seniority.value.value if candidate.seniority and candidate.seniority.value else None) or (
            candidate.seniority.raw if candidate.seniority else None
        )
        if val:
            terms.append(str(val))
    if candidate.contract_type and (candidate.contract_type.value or candidate.contract_type.raw):
        val = (candidate.contract_type.value.value if candidate.contract_type and candidate.contract_type.value else None) or (
            candidate.contract_type.raw if candidate.contract_type else None
        )
        if val:
            terms.append(str(val))
    if candidate.work_mode and (candidate.work_mode.value or candidate.work_mode.raw):
        # only textual approximation when useful and not already represented as applied city
        val = (candidate.work_mode.value.value if candidate.work_mode and candidate.work_mode.value else None) or (
            candidate.work_mode.raw if candidate.work_mode else None
        )
        if val and _strip_accents_lower(str(val)) not in {"remoto", "home office", "home-office", "trabalho remoto"}:
            terms.append(str(val))
    # dedupe case-insensitively preserving order
    seen: set[str] = set()
    out: list[str] = []
    for t in terms:
        k = _strip_accents_lower(_normalize_whitespace(str(t)))
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(_normalize_whitespace(str(t)))
    return out


def _compose_q(candidate: IntentLLMOutput, approx_terms: list[str]) -> str | None:
    base = _clean_q_terms(candidate.q)
    parts: list[str] = []
    if base:
        parts.extend(base.split(" "))
    existing = {_strip_accents_lower(p) for p in parts}
    for term in approx_terms:
        for tok in _normalize_whitespace(term).split(" "):
            k = _strip_accents_lower(tok)
            if not k or k in existing or k in _GENERIC_Q_TERMS:
                continue
            parts.append(tok)
            existing.add(k)
    result = _clean_q_terms(" ".join(parts)) if parts else None
    return result


def _build_field_status(
    field: str,
    understood: Any,
    applied: Any,
    status: FieldStatus | str,
    reason_code: str,
    reason: str,
) -> FieldAssessment:
    status_value = status.value if isinstance(status, FieldStatus) else status
    return FieldAssessment(
        field=field,
        understood=understood,
        applied=applied,
        status=status_value,  # pydantic will coerce to Enum
        reason_code=reason_code,
        reason=reason,
    )


def build_empty_intent(raw_text: str | None = None, reason_code: str = "empty_input") -> IntentContract:
    """Return a valid empty/clear intent contract with no applied filters (D-15)."""
    understood = UnderstoodIntent(
        q=None,
        city=None,
        salary=None,
        work_mode=None,
        contract_type=None,
        seniority=None,
        sort=None,
    )
    applied_params = AppliedParams(q=None, city=None, sort=None)
    reason = "Nenhum parâmetro extraível informado."
    statuses = [
        _build_field_status(
            field=name,
            understood=None,
            applied=None,
            status=FieldStatus.IGNORADO,
            reason_code=reason_code if name == "q" else "no_extractable_params",
            reason=reason,
        )
        for name in _ALL_FIELDS
    ]
    return IntentContract(
        understood=understood,
        field_statuses=statuses,
        applied_params=applied_params,
        limitations=["no_extractable_params"],
        meta={},
    )


def map_intent(candidate: IntentLLMOutput, raw_text: str = "") -> IntentContract:
    """Deterministically normalize/map candidate intent to safe applied params."""
    # ----- UNDERSTOOD (safe mirror, no invention) -----
    understood_salary = candidate.salary
    understood = UnderstoodIntent(
        q=_clean_q_terms(candidate.q),
        city=candidate.city.strip() if isinstance(candidate.city, str) and candidate.city.strip() else candidate.city,
        salary=understood_salary,
        work_mode=candidate.work_mode,
        contract_type=candidate.contract_type,
        seniority=candidate.seniority,
        sort=candidate.sort,
    )

    statuses: list[FieldAssessment] = []
    limitations: list[str] = []
    raw = raw_text or ""

    # ----- SORT (explicit only, D-06/D-07) -----
    explicit_sort, sort_conflict = _detect_explicit_sort(raw)
    # If candidate provided sort but text has no explicit signal, do not trust as applied preference.
    if sort_conflict:
        applied_sort = None
        sort_status = FieldStatus.IGNORADO
        sort_reason_code = "conflict_resolved"
        sort_reason = "Pedido de ordenação conflitante; nenhuma ordenação aplicada."
    elif explicit_sort in {"recentes", "antigas"}:
        applied_sort = explicit_sort
        sort_status = FieldStatus.APLICADO
        sort_reason_code = "normalized"
        sort_reason = "Ordenação explícita aplicada com segurança."
        understood.sort = explicit_sort  # reflect explicit understood/applied intent
    else:
        applied_sort = None
        sort_status = FieldStatus.IGNORADO
        sort_reason_code = "not_explicit"
        sort_reason = "Ordenação não informada explicitamente; nenhuma preferência aplicada."
        understood.sort = None
    statuses.append(
        _build_field_status(
            "sort",
            understood.sort if explicit_sort or sort_conflict else (candidate.sort if candidate.sort is None else None),
            applied_sort,
            sort_status,
            sort_reason_code,
            sort_reason,
        )
    )

    # ----- CITY (whitelist only, D-05) -----
    # simple conflict heuristic: multiple known distinct city tokens in raw text
    lowered = _strip_accents_lower(raw)
    mentioned = []
    for token, canon in (("sao paulo", "São Paulo"), ("rio de janeiro", "Rio de Janeiro"), ("belo horizonte", "Belo Horizonte"), ("campinas", "Campinas")):
        if token in lowered:
            mentioned.append(canon)
    distinct_whitelist = {m for m in mentioned if m in {"São Paulo", "Rio de Janeiro", "Belo Horizonte"}}
    city_conflict = len(distinct_whitelist) > 1

    if city_conflict:
        applied_city = None
        city_status = FieldStatus.IGNORADO
        city_reason_code = "conflict_resolved"
        city_reason = "Múltiplas cidades incompatíveis; nenhuma cidade aplicada."
    else:
        applied_city, city_reason_code = _resolve_city_safe(candidate.city, raw)
        if applied_city:
            city_status = FieldStatus.APLICADO
            city_reason = "Cidade aplicada via whitelist segura." if applied_city != "Remoto" or _resolve_city_safe(candidate.city, raw)[1] else "Cidade remota aplicada via whitelist segura."
            if city_reason_code == "normalized":
                city_reason = "Cidade normalizada e aplicada via whitelist segura."
        else:
            if city_reason_code == "not_in_whitelist":
                city_status = FieldStatus.IGNORADO
                city_reason = "Cidade fora da whitelist suportada; não aplicada."
            elif city_reason_code == "missing":
                city_status = FieldStatus.IGNORADO
                city_reason = "Cidade não informada; nenhum filtro de cidade aplicado."
            else:
                city_status = FieldStatus.IGNORADO
                city_reason = "Cidade não pôde ser aplicada com segurança."

    statuses.append(
        _build_field_status(
            "city",
            candidate.city,
            applied_city,
            city_status,
            city_reason_code if not (not applied_city and city_reason_code == "normalized") else "missing",
            city_reason,
        )
    )

    # ----- NON-NATIVE FIELDS / Q COMPOSITION (D-01,D-08,D-10,D-12) -----
    approx_terms = _collect_native_approx_terms(candidate)
    # work_mode 'remoto' mapped to city already counts as applied for city; avoid duplicate textual noise
    if applied_city == "Remoto":
        approx_terms = [t for t in approx_terms if _strip_accents_lower(t) not in {"remoto", "home office", "home-office", "trabalho remoto"}]

    applied_q = _compose_q(candidate, approx_terms)
    # q field status
    if applied_q:
        q_reason_code = "normalized"
        # if differs from understood/contains approximations, still applied as text search
        q_status = FieldStatus.APLICADO
        q_reason = "Termo de busca textual normalizado e aplicado."
        if approx_terms and (candidate.q is None or _clean_q_terms(candidate.q) != applied_q):
            q_reason_code = "normalized"
            q_reason = "Termo de busca textual composto/normalizado e aplicado."
    else:
        q_status = FieldStatus.IGNORADO
        q_reason_code = "missing"
        q_reason = "Nenhum termo textual útil para busca."
    statuses.append(
        _build_field_status("q", understood.q or candidate.q, applied_q, q_status, q_reason_code, q_reason)
    )

    # salary: understood structured but never applied as structured filter
    if candidate.salary and (candidate.salary.min is not None or candidate.salary.max is not None):
        # normalize currency default BRL in understood representation
        sal = candidate.salary
        understood.salary = IntentSalary(min=sal.min, max=sal.max, currency=sal.currency or "BRL")
        statuses.append(
            _build_field_status(
                "salary",
                understood.salary.model_dump(),
                None,
                FieldStatus.IGNORADO,
                "unsupported_structured_filter",
                "Faixa salarial entendida, mas não há filtro salarial nativo; não aplicada.",
            )
        )
        limitations.append("unsupported_structured_filter")
    else:
        statuses.append(
            _build_field_status(
                "salary",
                candidate.salary.model_dump() if candidate.salary else None,
                None,
                FieldStatus.IGNORADO,
                "missing",
                "Faixa salarial não informada.",
            )
        )

    # modality/contract/seniority: aproximado if influenced q, else ignorado
    def _assess_non_native(field_name: str, obj: Any, value_for_understood: Any) -> None:
        has_signal = False
        if obj is not None:
            val = getattr(obj, "value", None)
            rawv = getattr(obj, "raw", None)
            has_signal = bool(val or rawv)
        if not has_signal:
            statuses.append(
                _build_field_status(
                    field_name,
                    value_for_understood,
                    None,
                    FieldStatus.IGNORADO,
                    "missing",
                    "Campo não informado.",
                )
            )
            return

        influenced = False
        # detect if any of its terms are present in applied_q tokens
        raw_terms = []
        if obj is not None:
            if getattr(obj, "value", None):
                v = obj.value.value if hasattr(obj.value, "value") else obj.value
                raw_terms.append(str(v))
            if getattr(obj, "raw", None):
                raw_terms.append(str(obj.raw))
        if applied_q:
            aq = _strip_accents_lower(applied_q)
            for t in raw_terms:
                for tok in _normalize_whitespace(str(t)).split(" "):
                    k = _strip_accents_lower(tok)
                    if k and k in aq:
                        influenced = True
                        break
                if influenced:
                    break

        # Remoto as modality is effectively represented via applied city (aplicado for city)
        if field_name == "work_mode" and applied_city == "Remoto":
            statuses.append(
                _build_field_status(
                    field_name,
                    value_for_understood,
                    "Remoto",
                    FieldStatus.APLICADO,
                    "normalized",
                    "Modalidade remota aplicada como cidade na whitelist.",
                )
            )
            return

        if influenced:
            statuses.append(
                _build_field_status(
                    field_name,
                    value_for_understood,
                    {"q_terms": [t for t in raw_terms if t]},
                    FieldStatus.APROXIMADO,
                    "textual_approximation_in_q",
                    "Campo sem filtro estruturado nativo; usado como aproximação textual em q.",
                )
            )
            limitations.extend(["non_native_fields_limited", "textual_approximation_in_q"])
        else:
            statuses.append(
                _build_field_status(
                    field_name,
                    value_for_understood,
                    None,
                    FieldStatus.IGNORADO,
                    "unsupported_structured_filter",
                    "Campo sem filtro estruturado nativo; não aplicado.",
                )
            )
            limitations.append("non_native_fields_limited")

    _assess_non_native(
        "work_mode",
        candidate.work_mode,
        candidate.work_mode.model_dump() if candidate.work_mode else None,
    )
    _assess_non_native(
        "contract_type",
        candidate.contract_type,
        candidate.contract_type.model_dump() if candidate.contract_type else None,
    )
    _assess_non_native(
        "seniority",
        candidate.seniority,
        candidate.seniority.model_dump() if candidate.seniority else None,
    )

    # ensure deterministic unique limitations order-preserving
    seen_lim: set[str] = set()
    uniq_limits: list[str] = []
    for lim in limitations:
        if lim not in seen_lim:
            seen_lim.add(lim)
            uniq_limits.append(lim)

    applied_params = AppliedParams(q=applied_q, city=applied_city, sort=applied_sort)

    # sanity: applied_params city must be canonical whitelist or None
    if applied_params.city is not None:
        # resolve_city returns canonical for canonical inputs too
        canon = resolve_city(applied_params.city)
        if canon != applied_params.city and applied_params.city not in {"São Paulo", "Rio de Janeiro", "Belo Horizonte", "Remoto"}:
            applied_params.city = None

    # q empty after strip => None (compat)
    if applied_params.q is not None and not applied_params.q.strip():
        applied_params.q = None

    return IntentContract(
        understood=understood,
        field_statuses=statuses,
        applied_params=applied_params,
        limitations=uniq_limits,
        meta={},
    )
