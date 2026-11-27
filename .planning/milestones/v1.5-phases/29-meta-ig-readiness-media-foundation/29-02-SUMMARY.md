---
phase: 29-meta-ig-readiness-media-foundation
plan: 02
subsystem: api
tags: [instagram, pillow, fastapi, media, validation, postgres, pydantic]

# Dependency graph
requires:
  - phase: 29-meta-ig-readiness-media-foundation
    provides: SocialMediaAsset model, Instagram media schemas, MEDIA_PUBLIC_BASE_URL config, and IG readiness foundation from 29-01
provides:
  - Deterministic Pillow 1080x1350 JPEG IG card renderer with bundled DejaVu fonts
  - Versioned Instagram media hash/validation/prepare service with safe pt-BR IMAG-01 contract
  - Public unauthenticated `/api/v1/public/ig-media/{job_id}/{version}.jpg` endpoint with immutable cache headers
  - Admin prepare endpoint `/api/v1/admin/jobs/{job_id}/instagram/media/prepare` returning provenance/validation
  - IMAG-01/02/03 offline automated tests for rendering, validation, and public serving
affects: [29-03, 30, 31]

# Tech tracking
tech-stack:
  added: []
  patterns: [deterministic card render from job data only, version-hash media URL keyed by card-relevant fields, explicit MEDIA_PUBLIC_BASE_URL validation before IG publish readiness]

key-files:
  created:
    - backend/app/services/social/image_card.py
    - backend/app/services/social/image_media.py
    - backend/app/crud/social_media.py
    - backend/assets/fonts/README.md
    - backend/assets/fonts/DejaVuSans.ttf
    - backend/assets/fonts/DejaVuSans-Bold.ttf
    - backend/tests/test_ig_media_card.py
    - backend/tests/test_ig_media_validation.py
    - backend/tests/test_public_ig_media.py
  modified:
    - backend/app/api/v1/public.py
    - backend/app/api/v1/admin.py
    - backend/tests/conftest.py

key-decisions:
  - "IG media version hash uses only card-relevant job fields (template/title/company/city/contract_type/salary) so contact-only edits do not invalidate the intended image"
  - "Public IG media serving only resolves exact stored/current-hash assets by job_id+version, preventing arbitrary render abuse while allowing deterministic cache rebuild"
  - "IMAG-01 validation is returned as explicit pt-BR contract; Instagram blocking is contract-only in Phase 29, with enforcement/revalidation in Phases 30/31"

patterns-established:
  - "Bundled-font-only rendering: image_card loads repo-vendored DejaVu fonts and fails clearly if missing"
  - "Media prepare contract: prepare endpoint returns image URL, version hash, validation, byte size, and safe provenance for exact intended image"

requirements-completed: [IMAG-01, IMAG-02, IMAG-03]

# Metrics
duration: 25min
completed: 2026-11-23
---

# Phase 29 Plan 02: Meta/IG Readiness & Media Foundation Summary

**Deterministic 1080x1350 EmpregaNoix IG card service with versioned public HTTPS media serving and explicit pt-BR IMAG-01 validation/provenance contracts.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-11-23T16:15:00Z
- **Completed:** 2026-11-23T16:40:00Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments
- Built a deterministic Pillow renderer for Instagram job cards (1080x1350 JPEG, sRGB/RGB, <8MB guard, dark EmpregaNoix brand, "link na bio", no contact fields) with repo-bundled DejaVu fonts and provenance README.
- Implemented IG media hash/versioning, durable asset CRUD, explicit `MEDIA_PUBLIC_BASE_URL` validation, public unauthenticated versioned media serving, and admin prepare endpoint returning IMAG-01 validation/provenance.
- Replaced Wave 0 stubs with IMAG-01/02/03 automated tests covering deterministic rendering/hash relevance, pt-BR validation/public-URL contract, and public no-auth image serving/404 behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build deterministic IG card renderer, media service, and Wave 0 test stubs** - `79c036e` (feat)
2. **Task 2: Expose public/admin IG media endpoints and IMAG-01 validation contract** - `2f0428c` (feat)
3. **Task 3: Add IMAG-01/02/03 automated tests** - `61a26a6` (test)

**Plan metadata:** recorded in final docs commit for 29-02

## Files Created/Modified
- `backend/app/services/social/image_card.py` - Deterministic Pillow renderer, bundled font loader, 1080x1350 JPEG/size guard, no-contact card layout.
- `backend/app/services/social/image_media.py` - Card hash, public base URL validation, media prepare contract, and public asset get/build behavior.
- `backend/app/crud/social_media.py` - Durable social media asset lookup/upsert by job/provider/version.
- `backend/app/api/v1/public.py` - Unauthenticated versioned IG media endpoint with immutable JPEG response headers.
- `backend/app/api/v1/admin.py` - Admin Instagram media prepare endpoint with IMAG-01/03 validation/provenance response.
- `backend/assets/fonts/README.md` - DejaVu font provenance, license, and bundled-only rendering rule.
- `backend/assets/fonts/DejaVuSans.ttf` - Bundled regular font for deterministic rendering.
- `backend/assets/fonts/DejaVuSans-Bold.ttf` - Bundled bold font for deterministic rendering.
- `backend/tests/test_ig_media_card.py` - IMAG-02/03 deterministic render/hash tests.
- `backend/tests/test_ig_media_validation.py` - IMAG-01 validation contract tests (missing/invalid/public URL/ready).
- `backend/tests/test_public_ig_media.py` - IMAG-03 public endpoint no-auth/404/token-leakage tests.
- `backend/tests/conftest.py` - Kept IG card unit test db-independent while allowing DB-backed IG media tests.

## Decisions Made
- Followed plan as specified for D-01..D-12: deterministic generated card, no upload/logo, versioned public URL, explicit `MEDIA_PUBLIC_BASE_URL`, and IG-only blocking contract.
- Kept public media rebuild strict to the current expected hash for the requested job/version to avoid arbitrary render abuse while preserving rebuild-on-miss behavior.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adjusted Wave 0 test DB-independence for real IMAG tests**
- **Found during:** Task 3 (Add IMAG-01/02/03 automated tests)
- **Issue:** Task 1 registered all three Wave 0 stubs as db-independent; once replaced with DB-backed validation/public endpoint tests, that classification would be incorrect in no-DB environments.
- **Fix:** Kept `test_ig_media_card.py` db-independent and removed DB-backed IG validation/public tests from the db-independent skip list.
- **Files modified:** backend/tests/conftest.py
- **Verification:** `cd backend && uv run pytest tests/test_ig_media_card.py tests/test_ig_media_validation.py tests/test_public_ig_media.py -q` passed (9 passed).
- **Committed in:** 61a26a6 (part of Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Small test-harness correction required for accurate execution in DB/no-DB environments. No scope creep.

## Issues Encountered
- The configured test database had `alembic_version.version_num` as `VARCHAR(32)`, but revision `0006_ig_readiness_media_foundation` exceeds 32 chars; applying migrations for the test DB required widening the column to `VARCHAR(128)` before `alembic upgrade head` succeeded. The dev/app DB migration also encountered the same constraint during local upgrade; both were unblocked locally.
- `git status` shows unrelated pre-existing local changes/untracked items (`frontend/next-env.d.ts`, `.gsd-temp/*`); they were intentionally left unstaged and uncommitted.

## User Setup Required

**External services require manual configuration.** See plan frontmatter `user_setup` for:
- `MEDIA_PUBLIC_BASE_URL` must point to a public HTTPS backend base URL
- Backend deployment/reverse proxy must expose `/api/v1/public/ig-media/*` over HTTPS with no auth

## Next Phase Readiness
- Phase 29 Plan 03 can build Integrations IG readiness UX on top of the existing additive backend contracts and use this media foundation for operator messaging where needed.
- Phase 30 can consume the admin prepare endpoint and IMAG-01 validation/provenance contract for Instagram review preview/blocking UX.
- Phase 31 can reuse the exact versioned public image URL contract and must revalidate IMAG-01 before publish.

## Self-Check: PASSED

- FOUND: .planning/phases/29-meta-ig-readiness-media-foundation/29-02-SUMMARY.md
- FOUND: backend/app/services/social/image_card.py
- FOUND: backend/app/services/social/image_media.py
- FOUND: backend/app/crud/social_media.py
- FOUND: backend/app/api/v1/public.py
- FOUND: backend/app/api/v1/admin.py
- FOUND: backend/assets/fonts/DejaVuSans.ttf
- FOUND: backend/assets/fonts/DejaVuSans-Bold.ttf
- FOUND: backend/tests/test_ig_media_card.py
- FOUND: backend/tests/test_ig_media_validation.py
- FOUND: backend/tests/test_public_ig_media.py
- FOUND: 79c036e feat(29-02): add deterministic IG card renderer and media service
- FOUND: 2f0428c feat(29-02): expose public and admin Instagram media endpoints
- FOUND: 61a26a6 test(29-02): cover IG media card, validation, and public endpoint contracts

---
*Phase: 29-meta-ig-readiness-media-foundation*
*Completed: 2026-11-23*
