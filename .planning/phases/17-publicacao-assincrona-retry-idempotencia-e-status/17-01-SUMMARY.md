---
phase: 17-publicacao-assincrona-retry-idempotencia-e-status
plan: 01
subsystem: backend-social
tags: [fastapi, sqlalchemy, facebook-graph, httpx, async, retry, idempotency, social-publishing]
requires:
  - phase: 14-fundacao-social-dados-e-configuracao
    provides: SocialPost/SocialAccount/SocialPostLog models, token crypto, publish contracts and settings
  - phase: 15-oauth-meta-e-integracoes-no-admin
    provides: Connected Facebook account persistence and reconnect status semantics
  - phase: 16-geracao-revisao-e-aprovacao-do-post-social
    provides: Scheduled social draft records and public job link generation helpers
provides:
  - Real Facebook Graph feed publisher with safe categorized results and backend-only token usage
  - Shared social publish pipeline with atomic claim/lock, publishing transition, retry/backoff, and idempotency guards
  - Safe pt-BR failure mapping and sanitized social publish attempt logging
affects: [17-02-cron-dispatch-retry-endpoints, 17-03-admin-status-ui, social-publishing]
tech-stack:
  added: []
  patterns: [for-update-skip-locked claim, backend-only token in memory, safe error classification, configurable backoff, idempotent publish processing, sanitized audit logging]
key-files:
  created:
    - backend/app/crud/social_accounts.py
    - backend/app/services/social/publish_pipeline.py
    - backend/tests/test_facebook_publisher.py
    - backend/tests/test_social_retry_policy.py
    - backend/tests/test_social_idempotency.py
    - backend/tests/test_social_publish_pipeline.py
  modified:
    - backend/app/services/social/types.py
    - backend/app/services/social/facebook.py
    - backend/app/crud/social_posts.py
    - backend/tests/conftest.py
    - backend/tests/test_social_publisher.py
key-decisions:
  - "Classified httpx timeout during Graph publish as ambiguous and never auto-retried it to avoid duplicate external posts (D-11)."
  - "Treated integration absence/decrypt issues and unknown publish outcomes as non-auto-retryable safe failures with pt-BR guidance, while transient failures use configured backoff."
  - "Implemented claim in a short DB transaction (FOR UPDATE SKIP LOCKED + publishing state) and processed items in separate sessions to avoid holding locks during HTTP calls."
patterns-established:
  - "Publish pipeline resolves link/account/token per claim, passes token only in-memory payload, and persists only sanitized log/error fields."
  - "Retry scheduling is derived from SOCIAL_MAX_ATTEMPTS and social_retry_delays_list with final states represented by failed + next_retry_at=None."
requirements-completed: [PUB-01, PUB-04, PUB-05, PUB-06, PUB-07]
duration: 4min
completed: 2026-11-16
---

# Phase 17 Plan 01: Publicação assíncrona, retry, idempotência e status Summary

**Facebook Graph feed publishing core with locked claim pipeline, configurable safe retry/backoff, idempotent processing, and sanitized attempt logging for social posts.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-11-16T13:01:22Z
- **Completed:** 2026-11-16T13:05:21Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Replaced the Facebook publisher stub with a real async Graph API `/{page_id}/feed` implementation that sends `message`/`link`, uses backend-only page token context, extracts `external_post_id`, and returns safe categorized outcomes including `ambiguous`.
- Added shared publish pipeline primitives: account lookup, due-post claiming with `FOR UPDATE SKIP LOCKED`, publishing/idempotency guards, configurable retry computation, pt-BR safe error mapping, and sanitized `SocialPostLog` persistence.
- Implemented unit tests covering Graph request/success/error classification, retry policy defaults/exhaustion, idempotent no-op behavior, ambiguous no-auto-retry handling, and blocked integration/transient retry pipeline paths.

## Task Commits

Each task was committed atomically:

1. **Task 1: Wave 0 scaffolds + FacebookPublisher real e contrato de publicação seguro** - `b374f9c` (feat)
2. **Task 2: CRUD de conta/claim, pipeline compartilhado com retry/backoff/idempotência e logging seguro** - `bc5965b` (feat)

**Plan metadata:** pending (docs commit for SUMMARY/state updates as applicable)

## Files Created/Modified
- `backend/app/services/social/types.py` - Adds `ambiguous` publish failure category and backend-only `page_id`/`page_access_token` payload fields.
- `backend/app/services/social/facebook.py` - Implements real Graph feed publish call with safe success/error classification and no secret leakage.
- `backend/app/crud/social_accounts.py` - Adds helpers to resolve connected/available Facebook account for safe publishing decisions.
- `backend/app/crud/social_posts.py` - Adds claim/query/transition helpers (`with_for_update(skip_locked=True)`, publishing/published/failed updates, idempotency-aware claim).
- `backend/app/services/social/publish_pipeline.py` - Implements shared claim/process/retry/idempotency pipeline, safe pt-BR messages, backoff computation, and sanitized logging.
- `backend/tests/conftest.py` - Allows Phase 17 social publish unit tests to run without a configured test database.
- `backend/tests/test_facebook_publisher.py` - Verifies Graph request shape, external id extraction, and transient/ambiguous classification.
- `backend/tests/test_social_retry_policy.py` - Verifies retry backoff progression and exhaustion behavior.
- `backend/tests/test_social_idempotency.py` - Verifies published/external-id no-op and ambiguous no-auto-retry behavior.
- `backend/tests/test_social_publish_pipeline.py` - Verifies blocked integration handling and transient retry scheduling.
- `backend/tests/test_social_publisher.py` - Updates contract tests to align with real safe publisher behavior.

## Decisions Made
- Kept claim locking and state transition atomic but processed HTTP publishes outside the claim transaction (per-item sessions) to reduce lock hold time while preserving no-duplicate semantics.
- Mapped ambiguous/unknown/integration-blocked outcomes to safe terminal states without automatic retry; only transient failures schedule `next_retry_at` until attempts are exhausted.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Enabled Phase 17 social publish unit tests to run without DB configuration**
- **Found during:** Task 1/2 (test execution in environment without configured test DB)
- **Issue:** Global pytest collection skip would prevent required Phase 17 unit verification from running.
- **Fix:** Added the Phase 17 test modules (and updated social publisher contract test) to `conftest.py` DB-independent allowlist.
- **Files modified:** `backend/tests/conftest.py`
- **Verification:** `cd backend && python -m pytest -q tests/test_facebook_publisher.py tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py tests/test_social_idempotency.py -x` passes (8 passed).
- **Committed in:** `bc5965b` (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for reliable automated verification in this environment; no scope creep.

## Authentication Gates

None.

## Issues Encountered
- PowerShell-specific command separators/`nul` redirection caused minor shell command failures while scaffolding; resolved by using `write`/safe commands and continuing implementation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Core publish engine (FacebookPublisher + shared claim/retry/idempotency/logging pipeline) is ready for 17-02 to wire cron/dispatch/retry endpoints and for 17-03 status/UI integration.
- No blockers identified for wiring endpoints/background dispatch to `run_social_publish_cycle` / `process_social_post_safe`.

## Self-Check: PASSED

- FOUND: `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-01-SUMMARY.md`
- FOUND commit: `b374f9c`
- FOUND commit: `bc5965b`
- Verified: `cd backend && python -m pytest -q tests/test_facebook_publisher.py tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py tests/test_social_idempotency.py -x` (8 passed)

---
*Phase: 17-publicacao-assincrona-retry-idempotencia-e-status*
*Completed: 2026-11-16*
