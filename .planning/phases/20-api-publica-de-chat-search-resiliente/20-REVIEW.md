---
phase: 20-api-publica-de-chat-search-resiliente
reviewed: 2026-11-17T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - backend/.env.example
  - backend/app/api/v1/public.py
  - backend/app/core/config.py
  - backend/app/core/ratelimit.py
  - backend/app/schemas/chat.py
  - backend/app/services/intent/client.py
  - backend/app/services/intent/parser.py
  - backend/tests/test_chat_search_api.py
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-11-17T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the chat-search public API surface, supporting config/rate-limit/schema, intent extraction client/parser, and API tests. The implementation generally follows a defensive pattern (separate chat timeout, fail-safe degradation, no contacts in results, rate limiting, bounded LLM repair). No clear security vulnerabilities or data-loss paths were identified in the reviewed scope.

However, degradation classification and resilience logic have correctness/quality gaps that can produce misleading user signaling and reduce fallback effectiveness. Some minor dead/duplicative logic was also observed.

## Warnings

### WR-01: Timeout failures can be misclassified as generic LLM unavailability

**File:** `backend/app/api/v1/public.py:269-286`
**Issue:** When intent extraction fails, the endpoint classifies the failure as `timeout` only if the string `"timeout"` appears in `str(exc)`; otherwise it falls back to `llm_unavailable`. Exceptions such as `asyncio.TimeoutError` often stringify to an empty message, and provider/client timeout exceptions may not contain that exact token, so real timeouts can be reported as generic unavailability. This yields incorrect `degradation_reason`, limitation metadata, and user guidance compared to the intended timeout path (and diverges from the explicit timeout-degradation behavior expected by the endpoint contract/tests for timeout cases).
**Fix:**
```python
import asyncio

# ...
except Exception as exc:  # noqa: BLE001 - fallback controlado (D-08/D-09)
    logger.warning("chat_search_intent_failed", extra={"reason": type(exc).__name__})
    is_timeout = isinstance(exc, (asyncio.TimeoutError, TimeoutError)) or "timeout" in str(exc).lower()
    reason_code = "timeout" if is_timeout else "llm_unavailable"
    guidance = _CHAT_GUIDANCE_LLM
    limitation = "llm_timeout" if reason_code == "timeout" else "llm_unavailable"
    degraded = _chat_degraded_contract(
        payload.message,
        reason_code,
        guidance,
        limitation=limitation,
    )
    return ChatSearchResponse(...)
```
(Adjust exception types to include provider-specific timeout classes if used by the Groq/HTTP stack.)

### WR-02: Schema-validation failure after repair aborts fallback to secondary model

**File:** `backend/app/services/intent/client.py:268-301`
**Issue:** For each model, the client retries once on `ValidationError` (repair) and, if the repaired response is still invalid, raises `IntentExtractionError` immediately. Because `IntentExtractionError` is re-raised in the outer handler, the code does not continue to the next model in `model_chain`. A transient schema/format issue on the primary model therefore prevents trying `GROQ_MODEL_FALLBACK`, reducing resilience and increasing unnecessary degraded responses for chat-search.
**Fix:**
```python
for model in chain:
    try:
        messages = build_messages(text)
        response = await _create_once(
            client, model=model, messages=messages, settings=settings, timeout_seconds=timeout_seconds
        )
        try:
            return _parse_intent_output(response.choices[0].message.content or "{}")
        except ValidationError:
            repair_messages = build_messages(text, extra_user=REPAIR_PROMPT)
            response = await _create_once(
                client,
                model=model,
                messages=repair_messages,
                settings=settings,
                timeout_seconds=timeout_seconds,
            )
            try:
                return _parse_intent_output(response.choices[0].message.content or "{}")
            except ValidationError as exc:
                last_failure = f"{model}: invalid schema after repair ({exc})"
                continue  # try fallback model instead of failing fast
    except IntentExtractionError as exc:
        last_failure = f"{model}: {exc.detail}"
        continue
    except Exception as exc:  # noqa: BLE001
        last_failure = f"{model}: {exc}"
        continue

raise IntentExtractionError(
    "Todos os modelos falharam na extração de intenção. "
    f"Último erro: {last_failure}.",
    model=chain[-1],
)
```
(If fail-fast-on-schema is intentional by product decision, document it explicitly and keep behavior consistent with resilience goals.)

### WR-03: Degraded contract builder can append duplicate limitation codes

**File:** `backend/app/api/v1/public.py:69-101`, `backend/app/api/v1/public.py:269-286`
**Issue:** `_chat_degraded_contract` appends `limitation` when provided and then appends `reason_code`-derived limitations (`llm_unavailable` / `llm_timeout` / `no_extractable_params`). Callers pass the same derived values (e.g. `limitation="llm_timeout"` with `reason_code="timeout"` semantics mapped later), producing duplicate entries in `interpretation.limitations`. Duplicates create noisy, inconsistent API payloads and make downstream UI/analytics handling less deterministic.
**Fix:**
```python
def _chat_degraded_contract(
    message: str | None, reason_code: str, guidance: str, limitation: str | None = None
) -> IntentContract:
    contract = build_empty_intent(message, reason_code="no_extractable_params").model_copy(deep=True)
    contract.applied_params.q = None
    contract.applied_params.city = None
    contract.applied_params.sort = None

    limitations: list[str] = list(contract.limitations or [])
    if limitation:
        limitations.append(limitation)
    if reason_code == "llm_unavailable":
        limitations.append("llm_unavailable")
    elif reason_code == "timeout":
        limitations.append("llm_timeout")
    elif reason_code == "no_extractable_params":
        limitations.append("no_extractable_params")
    # de-duplicate while preserving order
    contract.limitations = list(dict.fromkeys(limitations))

    contract.meta = {
        **(contract.meta or {}),
        "degraded": True,
        "degradation_reason": reason_code,
        "guidance": guidance,
    }
    # ...
    return contract
```
And avoid passing a redundant `limitation` from the caller when it is equivalent to the reason-derived code.

## Info

### IN-01: Redundant/unreachable empty-message guard in endpoint

**File:** `backend/app/api/v1/public.py:268-269`, `backend/app/schemas/chat.py:11-24`
**Issue:** `ChatSearchRequest` enforces non-empty stripped `message` via Pydantic validation, so requests with blank/empty messages should be rejected before the handler runs. The additional handler check `if not payload.message or not payload.message.strip(): raise HTTPException(400, ...)` is effectively redundant and can drift from schema behavior (400 vs 422) without providing extra protection.
**Fix:**
```python
# Rely on schema validation as the single source of truth for message presence/length.
# Keep only business-level checks here if they cannot be expressed in the schema.
```
Alternatively, if a consistent 400 is desired for this case, enforce it via a shared validation/exception path rather than duplicating logic.

### IN-02: Rate-limit env settings are not range-validated like other tunables

**File:** `backend/app/core/config.py:55-59`, `backend/app/core/ratelimit.py:97-108`
**Issue:** `CHAT_SEARCH_RATE_LIMIT`, `REVEAL_RATE_LIMIT`, and `LOGIN_RATE_LIMIT` are accepted as arbitrary strings and passed through to `slowapi` at runtime. Unlike `SOCIAL_*` numeric/format settings, malformed values are not caught at startup, which can surface as runtime misconfiguration when the limited route is first hit. This is a minor operability/quality concern for a public endpoint.
**Fix:**
```python
import re
from pydantic import field_validator

_RATE_RE = re.compile(r"^\s*\d+\s*/\s*(second|minute|hour|day)\s*$", re.IGNORECASE)

@field_validator("CHAT_SEARCH_RATE_LIMIT", "REVEAL_RATE_LIMIT", "LOGIN_RATE_LIMIT")
@classmethod
def _validate_rate_limits(cls, value: str) -> str:
    if not _RATE_RE.match(value or ""):
        raise ValueError("Rate limit deve seguir o formato '<n>/<second|minute|hour|day>'")
    return value.strip()
```
(Align accepted units with the limiter configuration used in production.)

---

_Reviewed: 2026-11-17T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_