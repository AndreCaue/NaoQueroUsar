---
phase: 29-meta-ig-readiness-media-foundation
plan: 01
subsystem: api
tags: [meta, instagram, oauth, fastapi, sqlalchemy, alembic, pydantic]

# Dependency graph
requires:
  - phase: 15-meta-oauth-integracoes-admin
    provides: Meta OAuth connection, encrypted SocialAccount token storage, admin integrations endpoints
provides:
  - Additive Instagram readiness fields on SocialAccount with migration 0006
  - Durable SocialMediaAsset model and Instagram media schema contracts
  - Meta status/verify/connect flows with safe Instagram readiness resolution
  - META-01/META-02 offline backend tests and no-secret assertions
affects: [29-02, 29-03, 30, 31]

# Tech tracking
tech-stack:
  added: [Pillow==13.0.0]
  patterns: [additive IG readiness separate from FB connection status, connect/verify IG refresh only, safe pt-BR Graph error mapping]

key-files:
  created:
    - backend/app/models/social_media_asset.py
    - backend/alembic/versions/0006_ig_readiness_media_foundation.py
    - backend/app/schemas/social_media.py
    - backend/app/services/social/instagram_readiness.py
    - backend/tests/test_meta_oauth_instagram.py
    - backend/tests/test_integrations_instagram.py
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/.env.example
    - backend/app/core/config.py
    - backend/app/models/social_account.py
    - backend/app/models/__init__.py
    - backend/alembic/env.py
    - backend/app/schemas/social_integrations.py
    - backend/app/services/social/meta_oauth.py

key-decisions:
  - "IG readiness is additive and persisted on SocialAccount; Facebook status remains authoritative (D-13/D-15)"
  - "IG readiness refreshes on connect/confirm/verify, not on status GET (D-14)"
  - "MEDIA_PUBLIC_BASE_URL is explicit HTTPS public/non-localhost config for Phase 29 media foundation (D-12)"

patterns-established:
  - "Instagram readiness resolver: isolated service returns safe actionable states, never raw Graph payloads"
  - "Meta integration responses include additive `instagram` object without exposing tokens/secrets"

requirements-completed: [META-01, META-02]

# Metrics
duration: 8min
completed: 2026-11-23
---

# Phase 29 Plan 01: Meta/IG Readiness & Media Foundation Summary

**Additive Instagram readiness on the existing Meta connection, with persisted IG account readiness, safe pt-BR status/verify contracts, and Phase 29 media foundation schemas/migration.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-11-23T13:07:12Z
- **Completed:** 2026-11-23T13:15:08Z
- **Tasks:** 3
- **Files modified:** 15

## Accomplishments
- Added SocialAccount IG readiness fields, SocialMediaAsset durable model, migration 0006, and Instagram media validation/prepare schemas.
- Extended Meta OAuth scope and flows to resolve/persist `ig_user_id` readiness on connect/confirm/verify, keeping Facebook connection semantics authoritative.
- Added offline META-01/META-02 tests covering ready/missing linkage/missing permissions, D-15 FB non-regression, and no token/secret leakage.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Phase 29 foundation schema/config/migration/models and Wave 0 test stubs** - `aea526c` (feat)
2. **Task 2: Implement IG readiness resolution and integrations API** - `6362809` (feat)
3. **Task 3: Add META-01/META-02 backend tests and security assertions** - `376ab3e` (test)

**Plan metadata:** recorded in final docs commit for 29-01

## Files Created/Modified
- `backend/app/models/social_account.py` - Additive IG readiness fields; FB status remains authoritative.
- `backend/app/models/social_media_asset.py` - Durable IG media asset model keyed by job/provider/version hash.
- `backend/alembic/versions/0006_ig_readiness_media_foundation.py` - Adds IG readiness columns and `social_media_assets` table.
- `backend/app/services/social/instagram_readiness.py` - Isolated IG Graph readiness resolution and safe state mapping.
- `backend/app/services/social/meta_oauth.py` - Resolves/persists IG readiness on connect/verify; exposes additive `instagram` in status/action payloads.
- `backend/app/schemas/social_integrations.py` - Additive `MetaInstagramReadiness` and `instagram` fields.
- `backend/app/schemas/social_media.py` - Instagram media validation/prepare contract primitives for downstream phases.
- `backend/app/core/config.py` - Validates explicit public HTTPS `MEDIA_PUBLIC_BASE_URL`.
- `backend/.env.example` - Documents Phase 29 IG/media public base URL.
- `backend/tests/test_meta_oauth_instagram.py` - META-01/META-02 service readiness coverage.
- `backend/tests/test_integrations_instagram.py` - META-01/META-02 integrations API and no-secret assertions.

## Decisions Made
- Followed D-13/D-14/D-15/D-16 as planned: additive IG readiness, connect/verify refresh, FB status non-regression, alert/reconnect strategy.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Marked IG readiness as needs_reconnect on definitive FB reconnect transitions**
- **Found during:** Task 2 (IG readiness resolution and integrations API)
- **Issue:** `mark_needs_reconnect` updated Facebook status but could leave stale IG readiness fields.
- **Fix:** Set IG readiness to safe `needs_reconnect` with checked timestamp/error and clear IG IDs on definitive FB reconnect.
- **Files modified:** backend/app/services/social/meta_oauth.py
- **Verification:** Task 3 verify suite passed; FB/IG state mapping remains safe.
- **Committed in:** 6362809 (part of Task 2 commit)

**2. [Rule 2 - Missing Critical] Included additive instagram payload in confirm/disconnect action responses**
- **Found during:** Task 2 (IG readiness resolution and integrations API)
- **Issue:** Action responses could omit the new additive Instagram readiness object, creating inconsistent contracts.
- **Fix:** Returned `instagram` in confirm-page and disconnect responses using existing safe helpers.
- **Files modified:** backend/app/services/social/meta_oauth.py
- **Verification:** Integration status/verify contract tests pass; payload remains additive.
- **Committed in:** 6362809 (part of Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 missing critical)
**Impact on plan:** Both auto-fixes preserve contract consistency and safe reconnect semantics. No scope creep.

## Issues Encountered
- `uv run pytest` initially reported exit code 1 in PowerShell after dependency install; rerun confirmed `11 passed` / `EXIT:0`.

## User Setup Required

**External services require manual configuration.** See plan frontmatter `user_setup` for:
- Confirm Meta app permissions include `instagram_basic` and `instagram_content_publish`
- Ensure target Facebook Page is linked to an Instagram Business/Creator account

## Next Phase Readiness
- IG readiness backend contracts and migration are in place for Phase 29 Plan 02 media/public endpoint work.
- Phase 30 can consume additive `instagram` status payload and Phase 31 can rely on persisted IG readiness fields.
- Live Meta permission/linkage confirmation remains a manual operational prerequisite.

## Self-Check: PASSED

- FOUND: backend/app/models/social_media_asset.py
- FOUND: backend/alembic/versions/0006_ig_readiness_media_foundation.py
- FOUND: backend/app/schemas/social_media.py
- FOUND: backend/app/services/social/instagram_readiness.py
- FOUND: backend/tests/test_meta_oauth_instagram.py
- FOUND: backend/tests/test_integrations_instagram.py
- FOUND: .planning/phases/29-meta-ig-readiness-media-foundation/29-01-SUMMARY.md
- FOUND: aea526c feat(29-01): add IG readiness and media foundation
- FOUND: 6362809 feat(29-01): add Instagram readiness resolution to Meta integration
- FOUND: 376ab3e test(29-01): cover Instagram readiness and integration safety

---
*Phase: 29-meta-ig-readiness-media-foundation*
*Completed: 2026-11-23*
