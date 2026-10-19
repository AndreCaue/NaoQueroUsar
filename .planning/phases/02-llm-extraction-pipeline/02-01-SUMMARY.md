---
phase: 02-llm-extraction-pipeline
plan: 01
subsystem: extraction
tags: [groq, llm-extraction, pydantic, json-schema, phone-normalization, chunking, grounding, pytest]

# Dependency graph
requires:
  - phase: 01-backend-foundation-data-admin-auth
    provides: FastAPI app skeleton, Job model with columns the LLM schema mirrors, Settings base, pytest harness
provides:
  - groq==1.7.0 locked dependency + GROQ_*/EXTRACT_* env-configurable Settings (never-hardcoded model chain)
  - Strict Groq Structured-Outputs JSON schema (EXTRACTION_JSON_SCHEMA) + Pydantic LLM-output models (ExtractedJobRaw/ExtractionLLMOutput/JobCandidate) + prompt delimiters
  - Deterministic services: normalize_phone (pt-BR → E.164), chunk_text (token-budgeted contiguous slice chunker), is_grounded/normalize_for_grounding
  - Unit test suite for all extraction pure logic (31 tests, no network/DB)
affects: [03-groq-extractor-client, 04-extract-api-admin-flow, 03-reveal-anti-spam]

# Tech tracking
tech-stack:
  added: [groq==1.7.0]
  patterns:
    - "never-hardcoded LLM model: GROQ_MODEL/GROQ_MODEL_FALLBACK via Settings (PITFALL 1)"
    - "strict JSON schema as anti-hallucination type gate; semantic validation deferred to extractor"
    - "chunks are contiguous exact slices of input (losslessness contract)"
    - "TDD RED/GREEN commits per plan gate"

key-files:
  created:
    - backend/app/services/extraction/schema.py
    - backend/app/services/extraction/phones.py
    - backend/app/services/extraction/chunking.py
    - backend/app/services/extraction/grounding.py
    - backend/tests/test_extraction_core.py
  modified:
    - backend/app/core/config.py
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/.env.example

key-decisions:
  - "chunk_text returns contiguous exact slices of the original text (joined they reconstruct it modulo trailing whitespace), so the plan's losslessness contract ' '.join(''.join(chunks).split()) == ' '.join(text.split()) holds; when a paragraph boundary is chosen as the cut, the separator attaches to the FOLLOWING chunk (leading whitespace) so every emitted chunk stays ≤ budget"
  - "phone DDD validated as ^[1-9][1-9]$, local must be 10 (landline) or 11 (mobile starting 9) digits, bare 8-9 digit numbers rejected as ambiguous (no DDD), country code 55 stripped only when total length 12/13"
  - "grounding keep-set is [a-z0-9@.+_] after NFKD accent stripping — contacts/salaries survive normalization, punctuation/emoji do not"

patterns-established:
  - "extraction package is pure-logic: no fastapi/sqlalchemy/network imports in app/services/extraction/* (verified)"
  - "unit tests for extraction core run without DB (test_extraction_core.py independent of conftest fixtures)"

requirements-completed: [EXTR-03, EXTR-05, EXTR-08]

# Metrics
duration: 21min
completed: 2026-10-19
---

# Phase 02 Plan 01: Extraction Core — Settings, Strict Schema, and Pure-Logic Services Summary

**Env-configurable Groq model chain + strict Structured-Outputs JSON contract + tested pt-BR phone/grounding/chunking services — the pure-logic foundation of the extraction pipeline, with zero network calls.**

## Performance

- **Duration:** 21 min
- **Started:** 2026-10-19T19:46:58Z
- **Completed:** 2026-10-19T20:08:02Z
- **Tasks:** 2/2
- **Files modified:** 8

## Accomplishments
- `groq==1.7.0` locked; Settings exposes GROQ_API_KEY/GROQ_MODEL/GROQ_MODEL_FALLBACK/GROQ_TIMEOUT_SECONDS + five EXTRACT_* caps, all documented in .env.example (models never hardcoded — D-0x model-chain, EXTR-04 caps)
- `EXTRACTION_JSON_SCHEMA` is strict-ready (every property required, additionalProperties false, nullables as type unions) mirrored by Pydantic models that reject missing-title/extra-key rows; prompt delimiters `<TEXTO_FONTE>` ready for plan 02
- Three deterministic services with 31 passing tests: pt-BR phones → E.164 or None (never raises), accent/case/emoji-insensitive grounding, paragraph-first chunker under token budget with lossless contiguous slices
- Full suite 49 passed — no Phase 1 regressions; extraction package imports nothing from fastapi/sqlalchemy/network

## task Commits

Each task was committed atomically:

1. **task 1: groq dep + env config + strict extraction schema** - `eb004e7` (feat)
2. **task 2: chunker, phone normalizer, grounding — TDD (RED)** - `c5e2cf9` (test)
3. **task 2: chunker, phone normalizer, grounding — TDD (GREEN)** - `5d797aa` (feat)

**TDD Gate Compliance:** RED (`c5e2cf9`) → GREEN (`5d797aa`) both present — plan-level gate satisfied.

## Files Created/Modified
- `backend/app/services/extraction/schema.py` — EXTRACTION_JSON_SCHEMA, ExtractedJobRaw, ExtractionLLMOutput, JobCandidate, START_DELIM/END_DELIM
- `backend/app/services/extraction/phones.py` — normalize_phone: pt-BR formats → +55 E.164 or None (T-02-01 mitigate)
- `backend/app/services/extraction/chunking.py` — chunk_text + estimate_tokens: paragraph-first greedy packer, line/word fallback, hard floor (T-02-03 mitigate)
- `backend/app/services/extraction/grounding.py` — normalize_for_grounding (idempotent) + is_grounded containment check
- `backend/tests/test_extraction_core.py` — 31 tests: parametrized phone table, seeded property test (random.Random(42) × 10 pastes × 3 budgets), schema strict-validation
- `backend/app/core/config.py` — Settings extended with GROQ_* and EXTRACT_* fields (defaults per plan)
- `backend/pyproject.toml` / `backend/uv.lock` — groq==1.7.0 pinned and synced
- `backend/.env.example` — `# --- Groq / Extração (Phase 2) ---` section documenting every new var
- `backend/app/services/__init__.py`, `backend/app/services/extraction/__init__.py` — package markers

## Decisions Made
- Chunks are contiguous exact slices of the input; on a paragraph-boundary cut the separator travels with the following chunk (leading whitespace), which simultaneously guarantees the plan's `''.join(chunks)` losslessness contract and strict per-chunk budget compliance
- Blank-line preference is asserted by boundary position (first chunk == whole paragraph, second carries the separator), not by fully-stripped equality, because exact-slice semantics require the separator to live in one of the two chunks
- Phone landline first digit checked as digit-only (permissive) rather than the strict 2–5 range — plan's concrete implementation note allowed this; DDD regex and mobile-9 rules are strict

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Initial chunker dropped inter-chunk whitespace, breaking the plan's losslessness contract**
- **Found during:** task 2 (TDD GREEN run — plan-mandated property test failed 1/31)
- **Issue:** First implementation stripped each block/chunk independently, so `''.join(chunks)` merged words across chunk boundaries ("…vaga" + "segundo…" → "…vagasegundo…") and failed `' '.join(''.join(chunks).split()) == ' '.join(text.split())`
- **Fix:** Rewrote chunker to emit contiguous exact slices of the original text (paragraph segments → oversized-block line expansion → word-run expansion), cutting only at content boundaries so separators are never lost; adapted two test assertions to exact-slice semantics (boundary-position check for blank-line preference; empty-line filter for the newline-split check)
- **Files modified:** backend/app/services/extraction/chunking.py, backend/tests/test_extraction_core.py
- **Verification:** 31/31 tests pass incl. 10×3-budget seeded property test; full suite 49 passed
- **Committed in:** 5d797aa (part of task 2 GREEN commit)

**2. [Rule 3 - Blocking] `uv` CLI not on PATH in execution session**
- **Found during:** task 1 (uv lock step)
- **Issue:** `uv` command not recognized; uv 0.13.1 is installed as a pip package, not a standalone binary
- **Fix:** Invoked via `python -m uv lock` / `python -m uv sync` — same result (lock resolved, groq 1.7.0 + distro + sniffio installed into .venv)
- **Files modified:** backend/uv.lock (as planned)
- **Verification:** lock resolved; import check `from app.services.extraction.schema import ...` passes
- **Committed in:** eb004e7 (part of task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both necessary for plan-specified correctness (property test) and task completion. No scope creep.

## Issues Encountered
- The plan's own losslessness contract and blank-line test pulled in opposite directions until chunks were made exact slices — resolved inside task 2 as documented above (test details were adjusted, the plan's behavior bullets all remain covered)

## User Setup Required
None - no external service configuration required for this plan (GROQ_API_KEY blank is valid: endpoint errors clearly until configured in plan 03).

## Known Stubs
None. Nullable Pydantic field defaults (`str | None = None`) mirror the strict JSON schema's required-and-nullable unions and the Job table's nullable columns — intentional contract, not placeholder data.

## Threat Flags
None — no new security-relevant surface beyond the plan's threat register (T-02-01 phones mitigated, T-02-02 GROQ_API_KEY accept, T-02-03 chunking mitigated).

## Next Phase Readiness
- Plan 02 (extractor) can now consume: schema module (strict mode + delimiters), chunk_text under EXTRACT_CHUNK_MAX_TOKENS, normalize_phone/is_grounded for semantic validation, Settings GROQ_* for the client — all under test
- No blockers. Reminder: GROQ_API_KEY must be provided before plan 03/04 integration testing (env documented)

---
*Phase: 02-llm-extraction-pipeline*
*Completed: 2026-10-19*

## Self-Check: PASSED

- All 10 key files exist on disk (schema/phones/chunking/grounding/tests/config/pyproject/uv.lock/.env.example)
- All 3 task commits found in history: eb004e7, c5e2cf9, 5d797aa
- Verification re-run: 31/31 extraction tests pass, full suite 49 passed, schema import check OK
