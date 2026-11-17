---
phase: 19-contrato-de-intencao-e-mapeamento-seguro
reviewed: 2026-11-17T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - backend/app/services/intent/__init__.py
  - backend/app/services/intent/schema.py
  - backend/app/services/intent/mapper.py
  - backend/app/services/intent/client.py
  - backend/app/services/intent/parser.py
  - backend/tests/test_intent_schema.py
  - backend/tests/test_intent_mapper.py
  - backend/tests/test_intent_client.py
  - backend/tests/test_intent_parser.py
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 19: Code Review Report

**Reviewed:** 2026-11-17T00:00:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Review of the intent extraction/mapping stack (schema, Groq client seam, deterministic mapper, parser orchestration, and tests). Core safety properties are present: strict Pydantic schemas (`extra="forbid"`), untrusted input delimiting/sanitization, bounded model-chain fallback/repair, whitelist-based city application, explicit-only sort, and safe degradation to empty contracts. No blocker-level correctness/security defects identified in the reviewed scope. Findings focus on debuggability/observability and minor data-quality gaps.

## Warnings

### WR-01: Broad exception swallowing can hide mapper/programming defects

**File:** `backend/app/services/intent/parser.py:59-63`
**Issue:** `extract_and_map_intent` catches `(IntentExtractionError, ValidationError, Exception)` and always returns `build_empty_intent(..., reason_code="no_extractable_params")`. This provides safe degradation for runtime/provider failures, but it also masks unexpected programming errors in `map_intent`/contract handling (e.g. `AttributeError`, logic regressions), making defects silent in production and harder to diagnose.
**Fix:**
```python
    try:
        candidate = await parse_intent(text, settings, client=client, sleep=sleep)
    except (IntentExtractionError, ValidationError):
        return build_empty_intent(text, reason_code="no_extractable_params")

    try:
        contract = map_intent(candidate, raw_text=raw_text)
    except Exception:
        # preserve safe fallback, but record for observability (logger/metric)
        logger.exception("intent mapping failed; degrading to empty intent")
        return build_empty_intent(text, reason_code="no_extractable_params")
```

### WR-02: Repair-path infrastructure errors are treated as model failure and fall through chain

**File:** `backend/app/services/intent/client.py:256-285`
**Issue:** After an initial schema `ValidationError`, the repair request/parse is attempted; if the repair call raises a non-`ValidationError` exception (network/timeout/provider error) it is caught by the outer `except Exception` and the code continues to the next model. This loses the fact that the first model produced invalid structured output (and required repair), can trigger unnecessary fallback traffic, and reduces diagnosability of schema-adherence issues.
**Fix:**
```python
            except ValidationError:
                try:
                    repair_messages = build_messages(text, extra_user=REPAIR_PROMPT)
                    response = await _create_once(
                        client, model=model, messages=repair_messages, settings=settings
                    )
                    choice = response.choices[0]
                    content = (choice.message.content or "{}")
                    return _parse_intent_output(content)
                except ValidationError as exc:
                    raise IntentExtractionError(
                        "Resposta do LLM de intenção inválida mesmo após correção.",
                        model=model,
                    ) from exc
                except Exception as exc:
                    last_failure = f"{model} (repair): {exc}"
                    break  # or continue, but record repair-stage failure explicitly
```

## Info

### IN-01: Salary bounds/currency are not semantically validated

**File:** `backend/app/services/intent/schema.py:53-60`, `backend/app/services/intent/mapper.py:347-372`
**Issue:** `IntentSalary` accepts any numeric `min`/`max` and arbitrary `currency` string, and the mapper preserves/normalizes minimally without checking semantic validity (e.g. `min > max`, negative values, unexpected currency). Today salary is never applied as a structured filter, so impact is limited to understood/trace fields, but malformed ranges can propagate into the contract.
**Fix:** Add lightweight validation/normalization (e.g. reject or swap inverted bounds, clamp/flag negatives, normalize unsupported currency to `BRL` or mark as ignored with a specific reason) when building `understood.salary`.

### IN-02: Mapper status/reason derivation contains redundant branches

**File:** `backend/app/services/intent/mapper.py:294-320`, `backend/app/services/intent/mapper.py:329-344`
**Issue:** Some conditional paths assign reason/status fields that are immediately overwritten or encoded via convoluted expressions (e.g. city reason normalization and `reason_code` adjustment; duplicate `q_reason_code = "normalized"` assignments). Behavior appears correct for covered cases, but complexity raises maintenance risk.
**Fix:** Refactor to compute `(applied, status, reason_code, reason)` once per field via small helpers/clear branches to improve readability and reduce future regression risk.

---
_Reviewed: 2026-11-17T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
