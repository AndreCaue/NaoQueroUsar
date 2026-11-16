---
phase: 18-testes-documentacao-e-fechamento-de-gaps-v11
plan: 02
subsystem: testing
tags: [pytest, facebook, meta-oauth, social-worker, idempotency, mocks]
requires:
  - phase: 17-publicacao-assincrona-retry-idempotencia-e-status
    provides: publish pipeline, worker claim/retry contracts, social status/retry APIs
provides:
  - Deterministic offline coverage for TEST-01/TEST-02 (social generation/fallback, Graph publisher classification, retry/backoff, Meta OAuth/integrations mocked flows)
  - Strengthened TEST-03 evidence for claim/idempotent reexecution, no-duplicate guards, and ambiguous post-claim recovery without auto-retry
  - Explicit audit-matrix handoff for DB-backed social admin/worker suites blocked by unmigrated test schema
affects: [18-03, 18-04, verification, social-ops-evidence]
tech-stack:
  added: []
  patterns: [mocked-httpx-graph-publisher, deterministic-retry/backoff-assertions, idempotent-cycle/reexecution-guards, db-env-handoff-recording]
key-files:
  created:
    - .planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-02-SUMMARY.md
  modified:
    - backend/tests/test_facebook_publisher.py
    - backend/tests/test_social_retry_policy.py
    - backend/tests/test_social_idempotency.py
    - backend/tests/test_social_worker_claim.py
    - backend/tests/test_social_publish_pipeline.py
    - .planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-AUDIT-MATRIX.md
key-decisions:
  - "Kept all TEST-01..03 execution offline/deterministic (mocked Groq/Graph/HTTP/OAuth dependencies); no production app behavior changed because existing contracts already satisfied the exercised cases."
  - "Recorded DB-backed worker/admin social suites as evidence partial+handoff in 18-AUDIT-MATRIX.md when test DB schema was not migrated, instead of fabricating pass results."
patterns-established:
  - "Publisher tests explicitly assert Graph POST contract and transient/permanent/ambiguous classification via monkeypatched httpx.AsyncClient"
  - "Retry/idempotency tests assert configured backoff boundaries and no-duplicate/ambiguous-no-auto-retry outcomes across repeated processing"
requirements-completed: [TEST-01, TEST-02, TEST-03]
duration: 35min
completed: 2026-11-16
---

# Phase 18 Plan 02: Social/worker automated coverage hardening Summary

**Offline pytest coverage for social generation, Graph/OAuth contracts, retry/backoff, and idempotent worker recovery with explicit DB-backed handoff where schema is unavailable**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-11-16T14:55:00Z
- **Completed:** 2026-11-16T15:30:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Hardened TEST-01/TEST-02 deterministic coverage: Facebook publisher Graph POST/classification cases (including 429/permanent), configurable retry/backoff progression/exhaustion assertions, and verified existing LLM-mocked generation/fallback plus Meta OAuth/integrations suites remain offline and green.
- Strengthened TEST-03 idempotency/claim evidence: repeated worker cycle trigger modeled as no-duplicate/idempotent, repeated processing of published/external-post state remains no-op, targeted post dispatch/reexecution path preserved, and ambiguous recovery remains without auto-retry.
- Recorded environment-blocked DB-backed social admin/worker execution in `18-AUDIT-MATRIX.md` with exact commands and acceptance criteria (including `tests/test_admin_social_publish.py` / `tests/test_admin_social_retry_api.py`) instead of claiming unexecuted passes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Completar TEST-01 e TEST-02 com geração/classificação/backoff e mocks Graph/OAuth** - `bd08949` (test)
2. **Task 2: Completar TEST-03 para claim/SKIP LOCKED, concorrência simulada e idempotência sem duplicatas** - `3989a49` (test)

## Files Created/Modified
- `backend/tests/test_facebook_publisher.py` - Added explicit 429 transient and definitive permanent Graph error classification assertions (mocked `httpx.AsyncClient`).
- `backend/tests/test_social_retry_policy.py` - Added configured max-attempts/delay backoff boundary assertions for `compute_next_retry`.
- `backend/tests/test_social_idempotency.py` - Added repeated processing/no-duplicate guard for already-published/external-post state.
- `backend/tests/test_social_worker_claim.py` - Modeled second protected worker trigger as idempotent pipeline outcome with no duplicate publish.
- `backend/tests/test_social_publish_pipeline.py` - Asserted repeated targeted `post_id` dispatch remains on the same idempotent pipeline path.
- `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-AUDIT-MATRIX.md` - Added TEST-03 evidence/handoff table for offline results and DB-backed blockers/commands.

## Decisions Made
- Treated existing social/OAuth implementation as contract-correct for exercised scenarios; applied test-only hardening (no `backend/app/services/social/*` code changes) to make TEST-01..03 evidence explicit and deterministic.
- Used audit-matrix handoff with exact pytest commands and "evidência parcial+handoff" for DB-dependent suites that could not run in an unmigrated test schema environment.

## Deviations from Plan

None - plan executed as specified. Execution-environment blockers for DB-backed suites were handled via the plan's required handoff recording (not code deviations).

## Issues Encountered
- `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_social_worker_claim.py -x` failed during DB fixture setup in this environment (`relation "jobs" does not exist`) because `DATABASE_URL/TEST_DATABASE_URL` pointed to an unmigrated schema; offline/DB-independent subsets for TEST-03 (`tests/test_social_idempotency.py`, `tests/test_social_publish_pipeline.py`) passed (**7 passed**). Recorded in `18-AUDIT-MATRIX.md`.
- DB-backed admin social suites (`tests/test_admin_social_publish.py`, `tests/test_admin_social_retry_api.py`, `tests/test_admin_social_status_api.py`, `tests/test_admin_social_posts.py`) were not executable without migrated DB schema; handoff recorded with required command/criteria.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Threat Flags

None - no new network endpoints, auth paths, file access patterns, or trust-boundary schema changes introduced (test/handoff updates only).

## Next Phase Readiness
- TEST-01/TEST-02/TEST-03 offline automated evidence is strengthened and documented; DB-backed verification remains an explicit, reproducible handoff pending migrated test database.
- Ready for remaining Phase 18 gap-closure/documentation work that depends on this evidence baseline.

## Self-Check: PASSED

- FOUND: `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-02-SUMMARY.md`
- FOUND: `backend/tests/test_facebook_publisher.py`
- FOUND: `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-AUDIT-MATRIX.md`
- FOUND commit: `bd08949`
- FOUND commit: `3989a49`

---
*Phase: 18-testes-documentacao-e-fechamento-de-gaps-v11*
*Completed: 2026-11-16*
