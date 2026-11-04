---
phase: 02-llm-extraction-pipeline
verified: 2026-11-03T22:35:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification: true
previous_verified: 2026-10-20T23:23:43Z
previous_status: gaps_found
previous_score: 3/5 must-haves verified
gaps: []
human_verification: pending (post-fix live re-smoke — needs a real GROQ_API_KEY)
---

# Phase 02: LLM Extraction Pipeline — Verification Report

**Phase Goal:** O admin cola um texto bruto com várias vagas e obtém cards estruturados com status `pending`, sem vagas perdidas nem campos inventados.
**Originally verified:** 2026-10-20 (gaps_found, 3/5)
**Re-verified:** 2026-11-03
**Status:** PASSED
**Re-verification:** Yes — after the review-fix pass (`02-REVIEW-FIX.md`)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1 — paste with multiple vagas → structured list, each row into DB as `pending`; created only if ≥1 contact | ✓ VERIFIED | Pipeline, endpoint, persistence and pending/needs_review mapping all tested (API tests assert DB rows with status pending + source_snippet). CR-01 is closed: `contact_email=""`/whitespace is normalized to `None` *before* the contact gate, so the row is discarded with `sem contato válido` and never reaches the DB CHECK (`extractor.py:218`, test `test_empty_email_is_treated_as_no_contact`). Live spot-check: blank and both-blank contacts → `discard` |
| 2 | SC2 — schema/grounding failures → needs_review/invalid instead of invented data | ✓ VERIFIED | Strict `EXTRACTION_JSON_SCHEMA` + Pydantic `extra="forbid"`; grounding discards ungrounded title, clears ungrounded contacts, clears+flags minor fields. WR-01 closed: every width-limited column is clipped in `_process_row` with a `needs_review` reason (`_clip`), title grounded first then capped at 200; a 250-char title now yields a 200-char `save_needs_review` row and the rest of the batch survives. WR-04 closed: delimiter tokens in the paste are neutralized |
| 3 | SC3 — large pastes chunked/throttled under Groq TPM; truncation and divergence flagged | ✓ VERIFIED | `chunk_text` under `EXTRACT_CHUNK_MAX_TOKENS` (lossless contiguous slices, property-tested); inter-chunk sleep only between calls; 429 retried ≤3× honoring retry-after capped at 30s; `truncated` from any `finish_reason=="length"`; `divergent` from the count pre-pass; endpoint surfaces pt-BR alerts |
| 4 | SC4 — pt-BR phones → E.164 (wa.me-ready); input delimited to reduce prompt injection | ✓ VERIFIED | `normalize_phone` → `+55...` or None (parametrized table tests). WR-03 closed: grounding also matches the national portion (digits after `+55`) against the chunk digits, so a source `(11) 91234-5678` vs LLM `+5511912345678` is kept (`test_phone_with_country_code_added_by_llm_is_kept`); fabricated numbers are still discarded. WR-04 closed: `wrap_untrusted()` sanitizes `<TEXTO_FONTE>`/`</TEXTO_FONTE>` before wrapping, and the count pre-pass uses the same wrapper |
| 5 | SC5 — GROQ_MODEL configurable via env with fallback chain and clear error, never hardcoded | ✓ VERIFIED | `Settings.GROQ_MODEL`/`GROQ_MODEL_FALLBACK` (never hardcoded), `model_chain()` dedupe, dead-model switch and exhausted-chain pt-BR error all tested. WR-02 closed: `extract.py` maps `ExtractionAPIError` → HTTP 503 with `exc.detail`, so rate-limit/dead-model/bad-key messages reach the admin (`test_extract_503_from_extraction_api_error`) |

**Score:** 5/5 truths verified

### Gaps Closed in This Re-verification

| Finding | Previous state | Fix | Commit | Test |
| ------- | -------------- | --- | ------ | ---- |
| CR-01 | `contact_email=""` passed the gate → whole-batch 500 | strip-or-None before D-05 | `49088cb` | `test_empty_email_is_treated_as_no_contact` |
| WR-01 | over-long field aborted the single transaction; `city=""` saved silently | `_clip()` per column width + blank city → needs_review | `8c49d0a` | `test_overlong_title_is_truncated_without_failing_the_batch`, `test_overlong_optional_fields_are_truncated_to_column_widths`, `test_blank_city_is_flagged_for_review` |
| WR-02 | `ExtractionAPIError` → generic 500 | `except ExtractionAPIError → 503` | `d58053f` | `test_extract_503_from_extraction_api_error` |
| WR-03 | `+55`-expanded phone discarded a real contact | national-portion grounding branch | `2c2ce9e` | `test_phone_with_country_code_added_by_llm_is_kept`, `test_fabricated_phone_is_still_discarded` |
| WR-04 | embedded `</TEXTO_FONTE>` broke the data frame | `sanitize_untrusted()` / `wrap_untrusted()` (also in the count pre-pass) | `efbefa1` | `test_build_messages_neutralizes_delimiter_breakout`, `test_prompt_injection_with_delimiter_breakout_is_neutralized`, `test_estimate_job_count_uses_the_sanitized_wrapper` |

### Behavioral Spot-Checks (2026-11-03)

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full backend suite | `python -m pytest -q` (backend/) | **247 passed, 3 skipped** in 473s | ✓ PASS |
| Focused extraction suite | `pytest tests/test_extractor.py tests/test_extract_api.py tests/test_extraction_core.py -q` | **97 passed** | ✓ PASS |
| Blank email | `_process_row(email="", phone=None)` | `discard`, `sem contato válido` | ✓ PASS |
| Both blank contacts | `_process_row(email="", phone="")` | `discard`, `sem contato válido` | ✓ PASS |
| `+55`-expanded phone vs national source | `_process_row(phone="+5511912345678")` over `(11) 91234-5678` | kept, `+5511912345678` | ✓ PASS |
| Over-long title | `_process_row(title="A"*250)` | 200 chars, `save_needs_review` | ✓ PASS |

### Requirements Coverage

| Requirement | Status | Evidence |
| ----------- | ------ | -------- |
| EXTR-01 | ✓ SATISFIED | Byte-capped sync endpoint + `/admin/paste` UI + approved live smoke |
| EXTR-02 | ✓ SATISFIED | `extract_jobs` → `ExtractionResult`; strict structured outputs; FakeGroq happy-path + multi-chunk |
| EXTR-03 | ✓ SATISFIED | Strict schema + repair turn + grounding; blank contacts now discard and over-long fields clip to needs_review instead of 500 |
| EXTR-04 | ✓ SATISFIED | Token-budgeted chunks, inter-chunk delay, retry-after backoff, dead-model switch |
| EXTR-05 | ✓ SATISFIED | `normalize_phone` table-tested; normalized value persists |
| EXTR-06 | ✓ SATISFIED | `save→pending`, `save_needs_review→needs_review`; API test asserts DB row |
| EXTR-07 | ✓ SATISFIED | Contact gate now holds for empty/blank strings (CR-01 closed) |
| EXTR-08 | ✓ SATISFIED | Delimiters + data-only instruction + strict schema + injection tests; breakout neutralized (WR-04 closed) |
| EXTR-09 | ✓ SATISFIED | `truncated`/`divergent` flags + count pre-pass + pt-BR alerts |

### Remaining Findings (Info — do not affect must-haves)

IN-01..IN-08 from `02-REVIEW.md` were not in the fix scope. Notable:
IN-02 (per-chunk `AsyncGroq` not closed), IN-07 (`passlib` declared but `bcrypt` imported directly) and
IN-08 (admin paste form has no logout path after token expiry) are worth a later cleanup pass.
IN-06 is stale: a `jobs_updated_at` BEFORE UPDATE trigger already maintains `updated_at` in the DB.

### Human Verification Required (post-fix)

The original live smoke (plan 02-04 task 2, approved 2026-10-20) still stands for the happy path. Recommended re-smoke with a real `GROQ_API_KEY`:

1. **Empty-contact paste** via `/admin/paste`: expect 200 with the contact-less vaga in `discarded` ("sem contato válido") and the other saved `pending` — no 500.
2. **Model failure**: point `GROQ_MODEL` and fallback at a nonexistent model; expect a pt-BR error naming `GROQ_MODEL` in the UI (not "Erro 500").

---

_Full fix detail: `02-REVIEW-FIX.md`_
_Initial verification (gaps_found, 3/5): 2026-10-20T23:23:43Z_
_Re-verified: 2026-11-03_
