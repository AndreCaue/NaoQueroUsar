---
phase: 31-independent-publish-pipeline
plan: 02
subsystem: api, ui
tags: [instagram, facebook, social-publish, admin, fastapi, nextjs, audit]
requires:
  - phase: 31-independent-publish-pipeline
    provides: Provider-aware publish pipeline, IG reconciliation, safe status fields, and by_provider worker counters
provides:
  - Provider-aware admin approve dispatch for FB and IG with isolated failure handling
  - Provider-aware worker/status/list/retry/log admin endpoints with safe audit data
  - Deterministic retry resolution by post_id/provider with reconciliation-aware IG retry
  - Admin UI for per-provider status, IDs/permalink/timestamps, audit history, and actionable IG blocked states
affects: [31-VERIFICATION, admin-social-posts, admin-review, publish-operations]
tech-stack:
  added: []
  patterns:
    - "Approve dispatch registers/schedules FB and IG independently in isolated try/except blocks while keeping FB primary response"
    - "Retry resolves target by job social_post row and enforces provider mismatch/ambiguity guards with no mutation"
    - "Admin audit UI fetches safe SocialPostLog history lazily per provider/job"
key-files:
  created:
    - .planning/phases/31-independent-publish-pipeline/31-02-SUMMARY.md
  modified:
    - backend/app/api/v1/admin.py
    - backend/app/schemas/social_posts.py
    - backend/app/crud/social_posts.py
    - backend/tests/test_admin_social_publish.py
    - backend/tests/test_admin_instagram_social_posts.py
    - frontend/lib/api.ts
    - frontend/app/admin/social-posts/SocialPostsClient.tsx
    - frontend/app/admin/review/EditJobDialog.tsx
    - frontend/app/admin/review/ReviewQueue.tsx
key-decisions:
  - "Kept JobApproveResponse.social as the FB-primary backward-compatible outcome while dispatching IG independently in a separate guarded block"
  - "Retry defaults to Facebook only when the resolved target is unambiguously Facebook; ambiguous/mismatched provider requests return 409/400 with no mutation"
  - "Social audit logs exposed via safe endpoint/schemas only (attempt/result/http_status/error_message/response_summary/external_post_id/created_at)"
patterns-established:
  - "Provider-aware admin social observability: status/list/log endpoints return safe per-platform fields and no tokens/raw payloads"
  - "UI reconciliation clarity: IG reconciliation-required and rate-limit states are shown as actionable pt-BR guidance; retry remains same action"
requirements-completed: [PUBL-01, PUBL-03, PUBL-04, PUBL-05]
duration: 35min
completed: 2026-11-25
---

# Phase 31 Plan 02: Independent Publish Pipeline Summary

**Provider-aware admin publish surfaces for FB/IG with deterministic reconciliation-safe retry, safe audit logs, and actionable per-platform status UI**

## Performance

- **Duration:** 35 min
- **Started:** 2026-11-25T23:30:00Z
- **Completed:** 2026-11-26T00:05:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Added provider-aware admin social endpoints: worker `by_provider` breakdown, provider-filtered social-posts list, deterministic provider-aware retry with ambiguity/mismatch guards, and safe social-post audit log endpoint.
- Made approve dispatch independent for Facebook and Instagram: IG registration/dispatch runs in isolated try/except and does not block site/FB outcomes; FB primary social response remains backward-compatible.
- Updated frontend admin API/types and UI to surface FB/IG per-provider status, attempts/timestamps, IDs/permalink, reconciliation/rate-limit actionable pt-BR messages, IG retry, and lazy safe audit history.

## Task Commits

Each task was committed atomically:

1. **Task 1: Make admin approve/worker/retry/status endpoints provider-aware and auditable** - `0ad7097` (feat)
2. **Task 2: Update admin frontend for per-platform status, reconciliation retry, and audit history** - `c866584` (feat)

**Plan metadata:** `55fbbf9` (docs: complete plan)

## Files Created/Modified
- `backend/app/api/v1/admin.py` - Provider-aware approve dispatch, worker by_provider, deterministic retry resolution/wrappers, provider-aware list, and safe log endpoint.
- `backend/app/schemas/social_posts.py` - Added `SocialPostLogItem` and `SocialPostLogsResponse` safe audit schemas.
- `backend/app/crud/social_posts.py` - Added safe log listing helper and provider-aware/all-provider social status listing.
- `backend/tests/test_admin_social_publish.py` - Added coverage for independent FB/IG approve dispatch, worker by_provider, retry disambiguation, provider list/logs.
- `backend/tests/test_admin_instagram_social_posts.py` - Added coverage for safe IG status/log fields and reconciliation-aware retry API behavior.
- `frontend/lib/api.ts` - Extended social status types and added provider-aware retry/list/log API functions.
- `frontend/app/admin/social-posts/SocialPostsClient.tsx` - Provider-aware FB/IG status cards, audit history, and provider-specific retry.
- `frontend/app/admin/review/EditJobDialog.tsx` - IG retry button and reconciliation/permalink/ID/timestamp/rate-limit messaging.
- `frontend/app/admin/review/ReviewQueue.tsx` - Clarified FB-specific social approval toast copy.

## Decisions Made
- Preserved backward compatibility by keeping `JobApproveResponse.social` as the Facebook-oriented primary outcome while still dispatching Instagram independently.
- Enforced deterministic retry target resolution by job social post row: omitted provider is accepted only for unambiguously Facebook targets; ambiguous or mismatched provider requests fail safely with no mutation.
- Kept audit history strictly safe and operator-focused (no tokens, no raw payloads), exposing only sanitized log fields.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ESLint CLI flag in plan verification not supported by flat config**
- **Found during:** Task 2 (frontend verification)
- **Issue:** `npm run lint -- --file ...` failed because the project uses ESLint flat config and rejects `--file`.
- **Fix:** Ran equivalent targeted lint: `npx eslint app/admin/social-posts/SocialPostsClient.tsx app/admin/review/EditJobDialog.tsx app/admin/review/ReviewQueue.tsx lib/api.ts`.
- **Files modified:** None (verification command adaptation only)
- **Verification:** ESLint exited 0 with warnings only.
- **Committed in:** N/A (no code change)

---

**Total deviations:** 1 auto-fixed (1 blocking verification adaptation)
**Impact on plan:** No scope creep. Verification adapted to project ESLint config; required files were linted successfully.

## Issues Encountered
- `cd backend && pytest -q tests/test_admin_social_publish.py tests/test_admin_instagram_social_posts.py -k "approve or worker or retry or status or logs or instagram or provider"` failed in this worktree environment with `asyncpg.exceptions.UndefinedColumnError: column social_posts.ig_container_id does not exist` / missing IG reconciliation columns. This matches the 31-01 known environment issue: local test DB schema is not migrated to include migration 0008. Failures were schema-environment errors, not code assertion mismatches in the new endpoints.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plan 31-02 admin/API/UI surfaces are implemented for provider-aware publish observability and reconciliation-safe retry.
- Phase 31 verification should run in an environment with migration 0008 applied to the test DB to get meaningful DB-backed pytest results.
- No STATE.md or ROADMAP.md updates were made (orchestrator-owned in parallel worktree mode).

## Self-Check: PASSED

- FOUND: .planning/phases/31-independent-publish-pipeline/31-02-SUMMARY.md
- FOUND: 0ad7097
- FOUND: c866584
- FOUND: backend/app/api/v1/admin.py
- FOUND: frontend/app/admin/social-posts/SocialPostsClient.tsx

---
*Phase: 31-independent-publish-pipeline*
*Completed: 2026-11-25*
