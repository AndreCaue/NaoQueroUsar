---
phase: 02-llm-extraction-pipeline
status: all_fixed
findings_in_scope: 5
fixed: 5
skipped: 0
iteration: 1
date: 2026-11-03
review_path: .planning/phases/02-llm-extraction-pipeline/02-REVIEW.md
---

# Phase 02: Code Review Fix Report

**Scope:** Critical + Warning (CR-01, WR-01, WR-02, WR-03, WR-04)
**Result:** 5 of 5 fixed, 0 skipped
**Tests:** focused extraction suite `97 passed` (was 86 before the fixes)

## Fixes Applied

### CR-01 — Empty-string `contact_email` aborted the whole batch

- **File:** `backend/app/services/extraction/extractor.py`
- **Change:** `contact_email = (row.contact_email or "").strip() or None` before the D-05 check, so `""`/whitespace is absence of contact and the row is discarded with `sem contato válido`.
- **Test:** `test_empty_email_is_treated_as_no_contact` (parametrized `""` and `"   "`).
- **Commit:** `49088cb`

### WR-01 — Over-long LLM fields could fail the whole transaction

- **Files:** `backend/app/services/extraction/extractor.py`
- **Change:** DB column widths declared as constants; `_clip()` strips/caps optional fields and records a `needs_review` reason when it truncates. Title is grounded first, then capped at 200. Blank city is treated as missing and flagged; unmapped city keeps raw text + `needs_review`. Deliberately NOT enforced on `ExtractedJobRaw`: a Pydantic `ValidationError` would trigger the repair turn and, failing twice, abort the entire batch — the exact failure mode being avoided.
- **Tests:** `test_overlong_title_is_truncated_without_failing_the_batch`, `test_overlong_optional_fields_are_truncated_to_column_widths`, `test_blank_city_is_flagged_for_review`.
- **Commit:** `8c49d0a`

### WR-02 — `ExtractionAPIError` became a generic 500

- **File:** `backend/app/api/v1/extract.py`
- **Change:** dedicated `except ExtractionAPIError` → HTTP 503 with the client's curated pt-BR `detail`, preserving rate-limit / dead-model / bad-key guidance for the admin.
- **Test:** `test_extract_503_from_extraction_api_error`.
- **Commit:** `d58053f`

### WR-03 — Valid phone rejected when the LLM adds `+55`

- **File:** `backend/app/services/extraction/extractor.py`
- **Change:** grounding now also matches the national portion (digits after `+55`) against the chunk digits, so `(11) 91234-5678` in the source matches `+5511912345678` from the model. Fabricated numbers are still cut (regression covered).
- **Tests:** `test_phone_with_country_code_added_by_llm_is_kept`, `test_fabricated_phone_is_still_discarded`.
- **Commit:** `2c2ce9e`

### WR-04 — Prompt-injection delimiter could be closed by the paste

- **Files:** `backend/app/services/extraction/client.py`, `backend/app/services/extraction/extractor.py`
- **Change:** new `sanitize_untrusted()` / `wrap_untrusted()` rewrite literal `<TEXTO_FONTE>` / `</TEXTO_FONTE>` inside the paste, so the whole pasted text stays inside one data region. The count pre-pass (`estimate_job_count`) now uses the same wrapper instead of building its own message. Documented that grounding remains chunk-level, so the deeper cross-row contact contamination risk is unchanged (not part of this fix).
- **Tests:** `test_build_messages_neutralizes_delimiter_breakout`, `test_prompt_injection_with_delimiter_breakout_is_neutralized`, `test_estimate_job_count_uses_the_sanitized_wrapper`.
- **Commit:** `efbefa1`

## Not in Scope (Info findings, still open)

`IN-01..IN-08` were not fixed in this pass (default scope is Critical + Warning):
dead `sleep` parameter, per-chunk `AsyncGroq` construction, dead landline branch,
`EXTRACT_MAX_JOBS` off-by-one reporting, first-model-only `model_used`,
`updated_at` (note: a `jobs_updated_at` BEFORE UPDATE trigger already exists in the
DB, so this finding is stale), unused `passlib` dependency, and the admin token
dead-end without logout.

## Verification

```
cd backend
.venv\Scripts\python.exe -m pytest tests/test_extractor.py tests/test_extract_api.py tests/test_extraction_core.py -q
# 97 passed, 1 warning in 44.15s
```

The full backend suite was not re-run in this pass (see next step).
