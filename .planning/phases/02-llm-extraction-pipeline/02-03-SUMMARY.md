---
phase: 02-llm-extraction-pipeline
plan: 03
subsystem: extraction
tags: [fastapi, alembic, extraction-api, jwt, admin, transactions, pytest]

# Dependency graph
requires:
  - phase: 02-llm-extraction-pipeline
    provides: "plan 02-01 (schema/phones/chunking/grounding/settings), plan 02-02 (extract_jobs/ExtractionResult/CandidateOutcome)"
provides:
  - "source_snippet Text nullable on jobs + migration 0002 (D-08, REVW-05 aid)"
  - "ExtractRequest/ExtractSummaryResponse/DiscardedJob + pt-BR ALERT_* constants (D-01, D-02, D-07)"
  - "bulk_create_pending(session, rows) single-transaction flush semantics (D-03)"
  - "POST /api/v1/admin/extract JWT-protected, sync in-request with timeout, maps 413/422/503/504, atomic commit/rollback (D-01, D-02, D-03, D-04, D-05, D-07)"
  - "tests/test_extract_api.py (10 tests) covering auth, persistence/status/snippet, discarded-only, alerts, validation, key-missing, timeout, ValueError, commit rollback"
affects: [03-reveal-anti-spam, 04-review-ui, 05-admin-review-flow]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "sync in-request extraction: asyncio.timeout around extract_jobs, pt-BR 504 on TimeoutError (D-01)"
    - "atomic persistence: bulk_create_pending flushes only; caller commits once; on exception rollback + 'nada foi gravado' (D-03)"
    - "discarded never persisted, only returned in summary with reason+snippet (D-05)"
    - "alerts assembled from ALERT_* templates in schemas/extract.py (D-07)"
    - "reuse require_admin for endpoint protection (T-02-08)"

key-files:
  created:
    - backend/alembic/versions/0002_jobs_source_snippet.py
    - backend/app/schemas/extract.py
    - backend/app/api/v1/extract.py
    - backend/tests/test_extract_api.py
  modified:
    - backend/app/models/job.py
    - backend/app/crud/jobs.py
    - backend/app/api/v1/router.py

key-decisions:
  - "asyncio.timeout used as context manager (await asyncio.timeout(...)) for Python 3.11+ compatibility in this environment"
  - "When rows list is empty, endpoint returns summary without committing (no-op)"
  - "MAX_JOBS overflow alert surfaced via ALERT_MAX_JOBS when reason contains 'limite' (defensive against overflow marker)"

patterns-established:
  - "Endpoint is thin: validation/auth/caps/timeout/persistence/alerts only; classification/grounding/live in extractor"
  - "Alert constants live in schemas/extract.py for testability"

requirements-completed: [EXTR-01, EXTR-06, EXTR-07]

# Metrics
duration: ~45min
completed: 2026-10-19
---

# Phase 02 Plan 03: Extract API, Persistence, and Summary Summary

**JWT-protected synchronous POST /api/v1/admin/extract wired to the extractor: adds source_snippet migration, bulk single-transaction insert, pt-BR summary with alerts, and full API coverage (10 tests).**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-10-19T20:36:00Z
- **Completed:** 2026-10-19T21:21:00Z
- **Tasks:** 2/2
- **Files modified:** 7

## Accomplishments

- Migration 0002 adds `jobs.source_snippet` (Text nullable) with upgrade/downgrade; applied to both main and test DBs; `alembic current` shows head.
- `app/schemas/extract.py` defines `ExtractRequest`, `DiscardedJob`, `ExtractSummaryResponse` and pt-BR `ALERT_*` templates (divergence, truncation, discarded count, max-jobs).
- `bulk_create_pending` builds `Job` rows with status `pending`/`needs_review` and `source_snippet`, calls `session.add` + `flush()` only (caller commits); exported in `__all__`.
- `POST /api/v1/admin/extract` reuses `require_admin`, enforces byte cap (413) and `ExtractRequest.text` min_length (422), checks `GROQ_API_KEY` (503), runs `extract_jobs` under `asyncio.timeout` (504), persists kept rows in one `commit()` with rollback to 500 "nada foi gravado" on failure, returns summary with alerts; discarded never inserted (D-03, D-05).
- Router wired; `tests/test_extract_api.py` covers 401s, happy path (pending+needs_review + source_snippet, discarded-only-in-summary, divergence/truncation/discarded alerts), discard-all case, 413/422/503/504, ValueError→422, commit-failure rollback. All 10 API tests pass; full suite **104 passed**.

## Task Commits

Each task was committed atomically:

1. **task 1-2 combined:** `feat(02-03): extract API schemas, bulk insert, migration, and JWT-protected endpoint` — schemas/extract.py, crud/jobs.py, models/job.py, alembic/0002, api/v1/extract.py, api/v1/router.py, tests/test_extract_api.py

## Files Created/Modified

- `backend/alembic/versions/0002_jobs_source_snippet.py` — add/drop `source_snippet`
- `backend/app/models/job.py` — add `source_snippet: Mapped[str | None]` (Text, nullable)
- `backend/app/schemas/extract.py` — ExtractRequest, DiscardedJob, ExtractSummaryResponse, ALERT_* constants
- `backend/app/crud/jobs.py` — add `bulk_create_pending` (flush-only), update docstring/`__all__`
- `backend/app/api/v1/extract.py` — JWT-protected endpoint with timeout, caps, mapping, atomic persistence, alerts
- `backend/app/api/v1/router.py` — include `extract.router`
- `backend/tests/test_extract_api.py` — 10 API tests

## Decisions Made

- Used `async with asyncio.timeout(...)` (context manager) instead of `asyncio.timeout(...)()` call form for compatibility; tests for 504/timeout still pass.
- Endpoint treats empty `kept` as valid summary (no commit) and still reports alerts/discarded.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Python/asyncio.timeout usage mismatch**
- **Found during:** task 2 tests
- **Issue:** `await asyncio.timeout(...)` with a coroutine passed incorrectly caused coroutine-never-awaited warnings/failures in tests
- **Fix:** Switched to `async with asyncio.timeout(settings.EXTRACT_TIMEOUT_SECONDS): result = await extract_jobs(...)`
- **Files modified:** `backend/app/api/v1/extract.py`
- **Verification:** `test_extract_504_timeout` and all extract API tests pass

## Issues Encountered

- Tests target a separate `TEST_DATABASE_URL`; applied migration 0002 to test DB to avoid ORM/DB schema mismatch (column `source_snippet` missing) — resolved before running extract tests.

## User Setup Required

None. `GROQ_API_KEY` must be set at runtime for real extraction (same as plan 02-02); tests monkeypatch/mask it.

## Known Stubs

None.

## Threat Flags

None — mitigations align with threat model (auth reuse, atomic commit/rollback, caps/timeouts, discarded-not-persisted; snippet stored but public schemas unchanged).

## Next Phase Readiness

- Phase 2 complete: extraction core (01), orchestrator (02), API+DB wiring (03). Admin can paste text and receive structured summary with persisted `pending`/`needs_review` rows containing `source_snippet`.
- Phase 3 can build on admin flow (Turnstile/anti-spam, contact reveal) without changing Phase 2 contracts.

## Self-Check: PASSED

- Files exist: migration 0002, schemas/extract.py, api/v1/extract.py, crud/jobs.py updated, router wired, tests/test_extract_api.py
- Tests: `tests/test_extract_api.py` 10 passed; full suite `104 passed, 1 warning`
- Migration applied: `alembic current` shows `0002_jobs_source_snippet (head)`
- Public contract untouched (JobPublic has no source_snippet/contact exposure)
