---
phase: 30-instagram-review-experience
plan: 01
subsystem: api
tags: [instagram, fastapi, pydantic, sqlalchemy, social-posts, admin]
requires:
  - phase: 29-meta-ig-readiness-media-foundation
    provides: Instagram media prepare/validation contract and IG readiness foundation
provides:
  - Per-job Instagram draft/status admin contracts isolated from Facebook provider rows
  - publish_enabled persistence on social_posts with backward-compatible migration
  - Deterministic Instagram template C generator with "link na bio" CTA
  - Server-side Instagram caption/image guards and approve guard for enabled IG drafts
affects: [30-02-instagram-review-ui, 31-instagram-publish-pipeline]
tech-stack:
  added: []
  patterns: [provider-scoped social draft/status endpoints, publish_enabled review toggle persistence, IG review-time image validation guard]
key-files:
  created:
    - backend/alembic/versions/0007_instagram_review_social_post_publish_enabled.py
    - backend/tests/test_admin_instagram_social_posts.py
  modified:
    - backend/app/models/social_post.py
    - backend/app/schemas/social_posts.py
    - backend/app/crud/social_posts.py
    - backend/app/services/social/post_generation.py
    - backend/app/api/v1/admin.py
key-decisions:
  - "Instagram draft default uses deterministic template C (no LLM) with 'link na bio' CTA and no Facebook draft reuse"
  - "Instagram PUT/save stores trimmed admin-authored caption without public-link injection or contact/company sanitization rewrite"
  - "Approve blocks only when Instagram publish_enabled draft is invalid; disabling Instagram restores site/Facebook approval path"
patterns-established:
  - "Provider isolation: Instagram review endpoints use provider='instagram' CRUD rows without mutating Facebook drafts"
  - "Review guard: enabled Instagram drafts are revalidated for 2200-char caption and IMAG-01 image readiness before save/generate/approve"
requirements-completed: [REVW-01, REVW-02, REVW-03, REVW-04]
duration: 15min
completed: 2026-11-25
---

# Phase 30 Plan 01: Instagram Review Backend Contracts Summary

**Instagram review backend contracts with per-job `publish_enabled` drafts, deterministic template C captions, and server-side image/caption guards isolated from Facebook**

## Performance

- **Duration:** 15 min
- **Started:** 2026-11-25T11:10:00-03:00 (approx)
- **Completed:** 2026-11-25T11:23:55-03:00
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Added `publish_enabled` to `social_posts` with backward-compatible migration and widened draft/status schemas for `provider="instagram"`.
- Implemented Instagram draft/status admin endpoints, deterministic template C generation, 2200-char caption validation, and D-07 image validation when Instagram is enabled.
- Added approve guard that blocks only invalid enabled Instagram drafts while preserving Facebook/site independence, with regression tests covering isolation and guard behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add publish_enabled persistence and IG draft/status contracts** - `c2972f4` (feat)
2. **Task 2: Add Instagram template C generator and IG draft/status admin endpoints with validation guards** - `9a0b44a` (feat)
3. **Task 3: Add backend tests for Instagram review contracts and Facebook isolation** - `6d3ae01` (test)

**Plan metadata:** `475e68d` (docs: complete plan)

## Files Created/Modified

- `backend/alembic/versions/0007_instagram_review_social_post_publish_enabled.py` - Adds `publish_enabled` boolean column defaulting true for backward compatibility.
- `backend/app/models/social_post.py` - Persists `publish_enabled` on `SocialPost`.
- `backend/app/schemas/social_posts.py` - Widened provider literals and added `publish_enabled` draft fields.
- `backend/app/crud/social_posts.py` - Provider-aware status building and draft upsert support for `publish_enabled`.
- `backend/app/services/social/post_generation.py` - Deterministic Instagram template C and draft generator.
- `backend/app/api/v1/admin.py` - Instagram draft/status endpoints, caption/image validation helper, and approve-time IG guard.
- `backend/tests/test_admin_instagram_social_posts.py` - Contract/regression coverage for IG draft isolation, 2200 limit, D-07, and approve guard.

## Decisions Made

- Kept Instagram caption save semantics admin-authored: trim + 2200-char limit only; no `sanitize_and_enforce_policy` link injection to preserve D-01/D-09 "link na bio" behavior.
- Defaulted generated Instagram draft `publish_enabled` to `False` when absent, matching review-toggle opt-in while keeping existing DB rows backward-compatible.
- Used `prepare_instagram_media` as the server-side D-07 readiness check for enabled Instagram drafts on save/generate/approve.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Applied migration to test database before running pytest**
- **Found during:** Task 1 verification
- **Issue:** Test database lacked `social_posts.publish_enabled` after model/migration changes, causing DB-backed admin social tests to fail with `UndefinedColumnError`.
- **Fix:** Ran Alembic upgrade against the test database (using `TEST_DATABASE_URL`) so verification executed against current schema.
- **Files modified:** None (test DB schema only)
- **Verification:** `cd backend && pytest -q tests/test_admin_social_posts.py` passed after migration.
- **Committed in:** N/A (environment operation)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Verification-only environment fix; no product scope change.

## Issues Encountered

- Alembic defaults to `DATABASE_URL`; the local test DB used by pytest was behind on the new migration. Upgrading with `TEST_DATABASE_URL` resolved the mismatch.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Backend IG review contracts are ready for Phase 30 Plan 02 UI wiring (`/instagram/social-post`, `/instagram/social-status`, `publish_enabled`, caption/image validation messages).
- Phase 31 can build publish pipeline on top of provider-isolated IG drafts/status rows without changing Facebook flow.

## Self-Check: PASSED

- FOUND: `.planning/phases/30-instagram-review-experience/30-01-SUMMARY.md`
- FOUND: `c2972f4`
- FOUND: `9a0b44a`
- FOUND: `6d3ae01`
- FOUND: `backend/app/models/social_post.py`
- FOUND: `backend/alembic/versions/0007_instagram_review_social_post_publish_enabled.py`
- FOUND: `backend/app/schemas/social_posts.py`
- FOUND: `backend/app/crud/social_posts.py`
- FOUND: `backend/app/services/social/post_generation.py`
- FOUND: `backend/app/api/v1/admin.py`
- FOUND: `backend/tests/test_admin_instagram_social_posts.py`

---
*Phase: 30-instagram-review-experience*
*Completed: 2026-11-25*
