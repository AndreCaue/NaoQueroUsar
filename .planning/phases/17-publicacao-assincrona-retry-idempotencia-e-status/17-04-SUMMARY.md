---
phase: 17-publicacao-assincrona-retry-idempotencia-e-status
plan: 04
subsystem: backend-social
tags: [fastapi, sqlalchemy, pytest, async, publish-pipeline, retry, idempotency, recovery]
requires:
  - phase: 17-publicacao-assincrona-retry-idempotencia-e-status
    provides: claim/process publish pipeline, retry eligibility/state contracts, and Phase 17 verification gap baseline (17-01/17-02/17-03)
provides:
  - compensatory recovery in publish cycle for claimed posts left in publishing after post-claim exceptions without external_post_id
  - explicit ambiguous/manual-review retry blocking to prevent duplicate Facebook publication
  - automated regression coverage for post-claim crash recovery and safe counters/logging
affects: [phase-17-closeout, social-publishing, admin-retry]
tech-stack:
  added: []
  patterns: [best-effort compensatory recovery transaction, ambiguous no-auto-retry/manual-review gate, sanitized operational logging]
key-files:
  created: []
  modified:
    - backend/app/services/social/publish_pipeline.py
    - backend/app/crud/social_posts.py
    - backend/tests/test_social_publish_pipeline.py
key-decisions:
  - "Recovered post-claim processing exceptions by reopening a best-effort session/transaction, failing orphaned `publishing` posts without `external_post_id` as ambiguous with coherent attempt/log state and no auto-retry."
  - "Blocked manual retry for recovered ambiguous/manual-review failures (`failed` + `next_retry_at=None` + ambiguous message) to require conscious Facebook verification before any new attempt."
patterns-established:
  - "Post-claim exception handling must preserve idempotency: recover orphaned publishing state safely, but never mutate posts already published or carrying `external_post_id`."
requirements-completed: [PUB-04, PUB-06, PUB-07, UI-02]
duration: 12min
completed: 2026-11-16
---

# Phase 17 Plan 04: Publicação assíncrona, retry, idempotência e status Summary

**Compensatory recovery for post-claim publish exceptions that safely resolves orphaned `publishing` posts, blocks ambiguous duplicate-risk retries, and adds automated regression coverage.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-11-16T14:00:00Z
- **Completed:** 2026-11-16T14:12:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added per-item compensatory recovery in `run_social_publish_cycle` so exceptions after a committed claim no longer leave posts stuck in `publishing`: orphaned items without `external_post_id` are persisted as safe `failed` ambiguous state with incremented attempts, `next_retry_at=None`, and sanitized log `result="ambiguous"` / `response_summary="post_claim_processing_exception"`.
- Preserved idempotency/no-duplication guarantees during recovery by leaving posts already `published` or carrying `external_post_id` untouched and accounting them safely, while containing recovery failures without crashing the worker cycle.
- Tightened retry eligibility so ambiguous/manual-review failed posts with `next_retry_at is None` and the ambiguous verification message return `can_retry=false` with explicit guidance to verify on Facebook first, even when the account is connected.
- Added async unit coverage for the post-claim crash path proving the cycle does not raise, the post exits `publishing` into a safe ambiguous state, counters/logging are coherent, and retry remains blocked.

## Task Commits

Each task was committed atomically:

1. **Task 1: Recuperação compensatória pós-claim no pipeline com política sem duplicidade** - `53fc5e2` (fix)
2. **Task 2: Cobertura automatizada do crash/exceção pós-claim** - `703ebab` (test)

**Plan metadata:** pending (this summary commit)

## Files Created/Modified
- `backend/app/services/social/publish_pipeline.py` - adds best-effort compensatory recovery in the per-item exception path to persist safe ambiguous failure/log state or preserve idempotent published outcomes.
- `backend/app/crud/social_posts.py` - blocks retry eligibility for ambiguous/manual-review failed posts requiring conscious Facebook verification before retry.
- `backend/tests/test_social_publish_pipeline.py` - adds post-claim exception recovery regression test and ambiguous retry-state assertion.

## Decisions Made
- Treated post-claim processing exceptions as ambiguous verification outcomes (not transient auto-retryable failures) to prioritize duplicate prevention when remote publish state cannot be confirmed.
- Implemented recovery as a separate best-effort session/transaction after the failed item transaction, so claim persistence and worker progress remain resilient without widening scope.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Verification in this environment ran the plan-specified pytest targets successfully (`cd backend && python -m pytest -q tests/test_social_publish_pipeline.py tests/test_social_idempotency.py -x` → 6 passed). No DB-backed integration tests were required by this gap-closure plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 17 verification gap for orphaned `publishing` posts after post-claim exceptions is addressed in code and covered by automated tests.
- Remaining Phase 17 validation items are operational/human checks already noted in verification artifacts (real Meta publish/cron behavior and end-to-end admin UX in integrated environments).

## Self-Check: PASSED

- FOUND: `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-04-SUMMARY.md`
- FOUND: `backend/app/services/social/publish_pipeline.py`
- FOUND: `backend/app/crud/social_posts.py`
- FOUND: `backend/tests/test_social_publish_pipeline.py`
- FOUND commit: `53fc5e2`
- FOUND commit: `703ebab`
- Verified: `cd backend && python -m pytest -q tests/test_social_publish_pipeline.py tests/test_social_idempotency.py -x` (6 passed)

---
*Phase: 17-publicacao-assincrona-retry-idempotencia-e-status*
*Completed: 2026-11-16*
