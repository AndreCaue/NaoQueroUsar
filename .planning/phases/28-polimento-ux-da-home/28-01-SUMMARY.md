---
phase: 28-polimento-ux-da-home
plan: 01
subsystem: api
tags: [fastapi, pydantic, sqlalchemy, pytest, public-board, cities]

# Dependency graph
requires:
  - phase: 27-controles-por-ambiente
    provides: Public board baseline and env-controlled public UI behavior
provides:
  - JobListResponse.available_cities additive public contract (D-04)
  - Published/non-expired active city query independent of q/city/sort (D-01, D-02)
  - Backend regression tests for CITY-01 available_cities contract
affects: [28-02, 28-03, frontend-board, public-api-contract]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Board-level metadata computed from published/non-expired jobs independent of request filters"
    - "Canonical DB city names mapped to stable public slugs in ACTIVE_CITY_SLUG_ORDER"

key-files:
  created: []
  modified:
    - backend/app/schemas/job.py
    - backend/app/services/cities.py
    - backend/app/crud/jobs.py
    - backend/app/crud/__init__.py
    - backend/app/api/v1/public.py
    - backend/tests/test_public_api.py
    - backend/tests/test_public_search.py

key-decisions:
  - "Returned available_cities as supported slugs in stable CITY_OPTIONS order via canonical-to-slug mapping"
  - "Computed available_cities with a dedicated published/non-expired distinct query, not from filtered board results"

patterns-established:
  - "Public board metadata fields must remain contact-free and additive to JobListResponse"
  - "Active-city contract tests must prove filter independence (q/city/sort) and inactive-city omission"

requirements-completed: [CITY-01]

# Metrics
duration: 8min
completed: 2026-11-22
---

# Phase 28 Plan 01: Active Cities Board Contract Summary

**Public jobs board now returns stable `available_cities` slugs from published/non-expired jobs, independent of search filters and without exposing contact data.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-11-22T22:02:00-03:00
- **Completed:** 2026-11-22T22:10:07-03:00
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Extended `JobListResponse` with additive `available_cities: list[str]` while preserving the contact-free public contract.
- Added canonical-to-slug city mapping and a dedicated `list_active_cities` CRUD query over published/non-expired jobs only.
- Returned `available_cities` from `GET /api/v1/public/jobs` in the same payload and locked the behavior with CITY-01 regression tests.

## task Commits

Each task was committed atomically:

1. **Task 1: Add available_cities board contract and active-city query** - `632b537` (feat)
2. **Task 2: Add backend CITY-01 regression tests for available_cities contract** - `8d1df5a` (test)

**Plan metadata:** `pending` (docs: complete plan)

## Files Created/Modified
- `backend/app/schemas/job.py` - Adds `available_cities` to `JobListResponse`.
- `backend/app/services/cities.py` - Adds canonical DB city to public slug mapping and stable active-city order.
- `backend/app/crud/jobs.py` - Adds `list_active_cities` published/non-expired distinct query independent of board filters.
- `backend/app/crud/__init__.py` - Exports `list_active_cities`.
- `backend/app/api/v1/public.py` - Includes `available_cities` in `GET /api/v1/public/jobs` response.
- `backend/tests/test_public_api.py` - Asserts `available_cities` contract and contact-free payload.
- `backend/tests/test_public_search.py` - Asserts `available_cities` independence from q/city filters and inactive-city omission.

## Decisions Made
- Returned `available_cities` as supported public slugs in stable `ACTIVE_CITY_SLUG_ORDER` to align backend contract with frontend `CITY_OPTIONS`.
- Kept active-city computation in a dedicated CRUD query using only `published` + `expires_at > now()` predicates, never request `q/city/sort`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Local PowerShell `&&`/`||` separators are invalid; used PowerShell-compatible command separators when running checks.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backend CITY-01 contract is ready for Phase 28 Plan 02 to consume `available_cities` in the home board UI.
- Public payload remains contact-free; no blockers identified.

## Self-Check: PASSED

- FOUND: .planning/phases/28-polimento-ux-da-home/28-01-SUMMARY.md
- FOUND: 632b537
- FOUND: 8d1df5a

---
*Phase: 28-polimento-ux-da-home*
*Completed: 2026-11-22*
