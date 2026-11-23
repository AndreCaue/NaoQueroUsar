---
phase: 28-polimento-ux-da-home
plan: 02
subsystem: ui
tags: [nextjs, react, tailwind, public-board, cities, filters, ux]

# Dependency graph
requires:
  - phase: 28-polimento-ux-da-home
    provides: JobListResponse.available_cities public board contract (28-01)
provides:
  - Frontend JobListResponse.available_cities contract consumption
  - Obsolete selected city URL cleanup via RSC redirect (D-03)
  - Active-only city chips rendered from board payload in CITY_OPTIONS order (D-01, D-02)
  - Active/inactive city chip hover feedback per UI-SPEC (D-10, D-11, D-12)
affects: [28-03, frontend-board, public-home]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BoardToolbar receives availableCities from server board payload; chip set is filter-independent"
    - "Obsolete URL city is canonically cleaned with next/navigation redirect before rendering stale board state"

key-files:
  created: []
  modified:
    - frontend/lib/api.ts
    - frontend/app/(public)/page.tsx
    - frontend/components/board/BoardToolbar.tsx

key-decisions:
  - "Cleaned obsolete selected city in the RSC page with redirect(buildBoardHref(...city:null,page:1,vaga:null)) to avoid stale empty dead-end"
  - "Kept city chip hover feedback token-based (hover:bg-accent/10, hover:bg-accent-strong-hover) with no layout-shifting styles"

patterns-established:
  - "Public board metadata consumed by UI must come from the same board payload, not separate client fetches"
  - "URL-driven filters are treated as untrusted and canonicalized against server-provided available_cities"

requirements-completed: [CITY-01, UIUX-01]

# Metrics
duration: 3min
completed: 2026-11-22
---

# Phase 28 Plan 02: Active City Chips and Hover Feedback Summary

**Public home board consumes `available_cities`, renders only active city chips in stable order, and applies UI-SPEC hover feedback while canonicalizing obsolete city URLs.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-11-23T01:15:24Z
- **Completed:** 2026-11-23T01:18:42Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extended the frontend `JobListResponse` contract with `available_cities` and propagated it from the RSC board page to `BoardToolbar`.
- Implemented D-03 obsolete-city cleanup: when a selected URL city is not in server-provided `available_cities`, the page redirects to the broad board URL with city cleared.
- Rendered `Todas` plus only active city chips filtered from `CITY_OPTIONS`, preserving stable order and adding UI-SPEC-compliant active/inactive hover feedback without layout shift.

## task Commits

Each task was committed atomically:

1. **Task 1: Extend frontend board contract and enforce D-03 obsolete-city cleanup** - `cfbce44` (feat)
2. **Task 2: Render active-only city chips with D-10/D-11 hover feedback** - `998e810` (feat)

**Plan metadata:** `de33ab2` (docs: complete plan)

## Files Created/Modified
- `frontend/lib/api.ts` - Adds `available_cities: string[]` to `JobListResponse`.
- `frontend/app/(public)/page.tsx` - Reads `available_cities`, redirects obsolete selected city URLs, and passes `availableCities` to `BoardToolbar`.
- `frontend/components/board/BoardToolbar.tsx` - Accepts `availableCities`, renders active-only city chips, and applies D-10/D-11/D-12 hover classes.

## Decisions Made
- Used RSC `redirect()` with `buildBoardHref({ ...filters, city: null, page: 1, vaga: null })` when the selected city is absent from `available_cities`, satisfying D-03 without client state.
- Kept chip hover behavior in existing Tailwind/token classes (`hover:bg-accent/10`, `hover:bg-accent-strong-hover`, `transition-colors`) to preserve layout stability.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- PowerShell rejected `npm run lint -- --file ...` / unquoted paths containing parentheses; verified using `npx eslint` with quoted file paths and the plan's frontend test command.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Home board now consumes the 28-01 `available_cities` contract and enforces active-city UX behavior for CITY-01.
- Ready for 28-03 UI/UX polish work; no blockers identified.

## Self-Check: PASSED

- FOUND: .planning/phases/28-polimento-ux-da-home/28-02-SUMMARY.md
- FOUND: cfbce44
- FOUND: 998e810

---
*Phase: 28-polimento-ux-da-home*
*Completed: 2026-11-22*