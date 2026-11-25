---
phase: 31-independent-publish-pipeline
plan: 01
subsystem: api
tags: [instagram, graph-api, publish-pipeline, reconciliation, sqlalchemy, fastapi]

# Dependency graph
requires:
  - phase: 30-instagram-review-experience
    provides: Instagram draft/review/status contracts, publish_enabled toggle, per-provider social post flows
  - phase: 29-meta-ig-readiness-media-foundation
    provides: IG readiness fields on SocialAccount, image_media.prepare_instagram_media validation, public media contracts
provides:
  - Instagram Graph 2-step publisher with bounded status polling, permalink best-effort, and safe error classification
  - Provider-aware social publish pipeline for Facebook and Instagram with isolated claim/process blocks
  - SocialPost IG reconciliation/publish metadata and safe admin-facing status fields
  - Reconciliation-before-republish flow for ambiguous IG outcomes and no-retry-storm rate-limit handling
affects: [31-02, admin-social-status, publish-worker, instagram-retry]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Provider-aware publish pipeline with shared claim/log/idempotency core and per-provider handlers"
    - "Ambiguous IG publish persisted as failed + reconciliation_required + next_retry_at=None"
    - "Manual retry reconciles known IG container/media IDs before any new publish"

key-files:
  created:
    - backend/alembic/versions/0008_instagram_publish_reconciliation.py
    - backend/app/services/social/instagram.py
    - backend/tests/test_instagram_publisher.py
  modified:
    - backend/app/models/social_post.py
    - backend/app/schemas/social_posts.py
    - backend/app/services/social/types.py
    - backend/app/services/social/publish_pipeline.py
    - backend/app/crud/social_posts.py
    - backend/app/crud/social_accounts.py
    - backend/app/core/config.py
    - backend/tests/test_social_publish_pipeline.py
    - backend/tests/conftest.py

key-decisions:
  - "Represented IG ambiguity as failed + ig_reconciliation_required/ig_reconciliation_state metadata with next_retry_at=None; no auto-retry"
  - "Classified IG 2207042/content_publishing_limit/rate-limit responses as blocked permanent actionable errors with ig_last_publish_error_code"
  - "Allowed IG manual retry when reconciliation is required and performed Graph reconciliation before any new publish/container creation"
  - "Treated Instagram account_status as provider-specific in retry-state display; pipeline preflight enforces IG readiness and safe final failures"

patterns-established:
  - "IG publish metadata pattern: container/media/permalink/reconciliation fields on social_posts, safe audit fields in SocialPostStatusItem"
  - "Rate-limit safety pattern: authoritative Graph runtime errors mapped to actionable pt-BR state, no retry storm"

requirements-completed: [PUBL-01, PUBL-02, PUBL-03, PUBL-04, PUBL-05]

# Metrics
duration: 45min
completed: 2026-11-25
---

# Phase 31 Plan 01: Independent Publish Pipeline Summary

**Instagram Graph 2-step publishing with provider-isolated FB/IG pipeline, reconciliation-safe ambiguity handling, and rate-limit blocked states without retry storms**

## Performance

- **Duration:** 45 min
- **Started:** 2026-11-25T20:00:00Z
- **Completed:** 2026-11-25T20:45:00Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments
- Added explicit IG publish/reconciliation schema and contracts: migration 0008, SocialPost IG fields, safe schema fields, PublishResult/Payload metadata, and bounded IG config knobs.
- Implemented `InstagramPublisher` with Graph container creation, bounded status polling, media publish, best-effort permalink fetch, and safe mapping for timeout/ambiguity/rate-limit/content-publishing-limit cases.
- Refactored publish pipeline to process Facebook and Instagram in isolated provider blocks, claim only `publish_enabled=true` posts, reconcile ambiguous IG containers before republish, and persist actionable safe audit/retry state.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add IG publish/reconciliation schema, contracts, and test scaffolds** - `2c26917` (feat)
2. **Task 2: Implement Instagram publisher and safe Graph error mapping** - `7f86c16` (feat)
3. **Task 3: Integrate provider-aware pipeline, reconciliation, and CRUD retry-state** - `f84ea9e` (feat)

**Plan metadata:** `1e9a6e6` (docs: complete plan)

## Files Created/Modified
- `backend/alembic/versions/0008_instagram_publish_reconciliation.py` - Adds IG container/media/permalink/reconciliation columns to `social_posts`.
- `backend/app/models/social_post.py` - Persists IG reconciliation and publish metadata on SocialPost.
- `backend/app/schemas/social_posts.py` - Exposes safe IG audit/permalink/reconciliation fields and worker `by_provider`.
- `backend/app/services/social/types.py` - Extends PublishResult/SocialPostPayload with safe IG metadata fields.
- `backend/app/core/config.py` - Adds bounded IG HTTP/poll/attempt budget settings with validation.
- `backend/app/services/social/instagram.py` - Implements InstagramPublisher 2-step Graph flow and safe error classification.
- `backend/app/services/social/publish_pipeline.py` - Adds provider-aware claim/process/reconciliation and isolated FB/IG cycle handling.
- `backend/app/crud/social_posts.py` - Filters claim eligibility by `publish_enabled` and exposes IG-aware retry/status fields.
- `backend/app/crud/social_accounts.py` - Reviewed for IG helper need; no helper added (existing FB-linked account fields reused).
- `backend/tests/test_instagram_publisher.py` - Contract and behavior tests for IG publish, ambiguity, rate limit, permalink best-effort.
- `backend/tests/test_social_publish_pipeline.py` - Pipeline tests for publish_enabled, IG ambiguity/reconciliation, rate limit, and provider isolation.
- `backend/tests/conftest.py` - Marks `test_instagram_publisher.py` as DB-independent for unit execution.

## Decisions Made
- Kept `SocialPost.external_post_id` as the final published media ID and stored container/permalink/reconciliation state in explicit IG columns.
- Used Graph runtime error responses (2207042/content_publishing_limit/rate-limit signatures) as authoritative reactive PUBL-05 handling; no proactive pre-publish limit query added.
- Preserved Facebook behavior and public contracts while extending worker response with optional `by_provider` for observability.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added DB-independent test registration for new Instagram publisher tests**
- **Found during:** Task 1 (test scaffolding)
- **Issue:** `backend/tests/conftest.py` skips DB-dependent tests when no test DB is configured; new `test_instagram_publisher.py` was not in the allowlist.
- **Fix:** Added `test_instagram_publisher.py` to `db_independent` set.
- **Files modified:** backend/tests/conftest.py
- **Verification:** `pytest -q tests/test_instagram_publisher.py tests/test_social_publisher.py -k contract` passed in DB-less mode.
- **Committed in:** 2c26917 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed test hang caused by recursive asyncio.sleep monkeypatch**
- **Found during:** Task 2 (Instagram publisher test verification)
- **Issue:** Test patched `ig_mod.asyncio.sleep` to call `asyncio.sleep(0)`, which recursed into the patched function and hung.
- **Fix:** Captured original sleep reference before monkeypatch and returned `orig_sleep(0)`.
- **Files modified:** backend/tests/test_instagram_publisher.py
- **Verification:** Targeted polling test passed; full task 2 verify command passed.
- **Committed in:** 7f86c16 (Task 2 commit)

**3. [Rule 1 - Bug] Avoided extra targeted post_id session lookup that broke strict fake session factory tests**
- **Found during:** Task 3 (pipeline refactor regression check)
- **Issue:** Pre-lookup of target provider opened an extra session, causing existing strict fake-session pipeline recovery test to fail with "unexpected extra session".
- **Fix:** Removed pre-lookup and stopped provider iteration after targeted post_id match in claim phase.
- **Files modified:** backend/app/services/social/publish_pipeline.py
- **Verification:** `pytest -q tests/test_social_publish_pipeline.py` passed (5 passed), then full target pair passed (16 passed).
- **Committed in:** f84ea9e (Task 3 commit)

---

**Total deviations:** 3 auto-fixed (2 bug, 1 blocking)
**Impact on plan:** All fixes were required for correctness/testability. No scope creep; all changes stayed within Phase 31 publish-core behavior.

## Issues Encountered
- Regression guard `pytest -q tests/test_admin_instagram_social_posts.py -k "approve or instagram or publish_enabled"` failed in this environment with `asyncpg.exceptions.UndefinedColumnError: column social_posts.ig_container_id does not exist`, indicating the local test DB schema has not been migrated to include 0008. This is an environment migration state issue, not a code assertion failure in the touched unit tests.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backend publish core for PUBL-01..05 is in place: IG publisher, provider-aware pipeline, reconciliation metadata, and safe retry/rate-limit states.
- Phase 31-02 can focus on admin/API/UI surfaces for provider-aware status/audit/retry presentation and any endpoint wiring/extensions.
- Local/CI test DBs must apply migration 0008 before DB-backed admin Instagram regression tests can pass.

## Self-Check: PASSED

- FOUND: .planning/phases/31-independent-publish-pipeline/31-01-SUMMARY.md
- FOUND: 2c26917
- FOUND: 7f86c16
- FOUND: f84ea9e
- FOUND: backend/app/services/social/instagram.py
- FOUND: backend/alembic/versions/0008_instagram_publish_reconciliation.py

---
*Phase: 31-independent-publish-pipeline*
*Completed: 2026-11-25*
