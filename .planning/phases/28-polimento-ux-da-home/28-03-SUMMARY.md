---
phase: 28-polimento-ux-da-home
plan: 03
subsystem: ui
tags: [nextjs, react, tailwind, accessibility, listbox, hover, ux]

# Dependency graph
requires:
  - phase: 28-polimento-ux-da-home
    provides: Active city chips and board toolbar baseline from 28-02
provides:
  - Accessible custom sort listbox replacing native select in BoardToolbar
  - Consistent accent hover/focus language across sort, city chips, and job cards
  - Medium job card hover feedback without layout shift
affects: [28-verify, frontend-board, public-home]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Custom button+listbox dropdown with aria-activedescendant, keyboard, outside-click, and Escape focus return"
    - "Token-consistent hover feedback: accent border/text with subtle accent background tint"

key-files:
  created:
    - frontend/components/board/SortDropdown.tsx
  modified:
    - frontend/components/board/BoardToolbar.tsx
    - frontend/components/board/JobCard.tsx

key-decisions:
  - "Implemented SortDropdown as a client button+listbox with aria-activedescendant and option button focus for keyboard/active styling"
  - "Kept hover feedback token-based and layout-stable (transition-colors, no border/padding/transform changes)"

patterns-established:
  - "Interactive board controls use accent border/text plus subtle accent/10 background for hover/focus consistency"
  - "Custom dropdowns close on select, outside click, and Escape while restoring focus to trigger"

requirements-completed: [UIUX-01]

# Metrics
duration: 2min
completed: 2026-11-22
---

# Phase 28 Plan 03: Sort Dropdown and Card Hover Polish Summary

**Accessible custom sort listbox and medium card hover feedback completed the Phase 28 home UX polish with consistent accent interaction states.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-11-22T22:22:42Z
- **Completed:** 2026-11-22T22:24:51Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Replaced BoardToolbar native sort `<select>` with an accessible `SortDropdown` listbox supporting click, Arrow keys, Enter/Space, Escape, outside click, and focus return.
- Applied consistent D-07/D-08/D-12 accent hover/focus styling to the sort trigger/options while preserving existing board URL commit behavior through `commit({ sort })`.
- Added D-09 medium hover feedback to job cards (`hover:bg-[rgba(139,92,246,0.04)]`) without changing layout dimensions or existing focus-within behavior.

## task Commits

Each task was committed atomically:

1. **Task 1: Create accessible SortDropdown and replace native select in BoardToolbar** - `153ef7c` (feat)
2. **Task 2: Apply medium JobCard hover and verify UIUX-01 consistency** - `99f455c` (feat)

**Plan metadata:** `912abc0` (docs: complete plan)

## Files Created/Modified
- `frontend/components/board/SortDropdown.tsx` - New accessible custom sort listbox for `recentes`/`antigas`.
- `frontend/components/board/BoardToolbar.tsx` - Integrates `SortDropdown` and removes native sort select.
- `frontend/components/board/JobCard.tsx` - Adds medium hover background cue with existing accent/focus behavior.

## Decisions Made
- Used a client-side button+listbox pattern with `aria-activedescendant`, roving active index, and option focus to satisfy D-05/D-06 keyboard and ARIA behavior without new dependencies.
- Kept all visual feedback in existing Tailwind/token classes to preserve the dark/roxo language and avoid layout shift.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Plan lint verification used `--file`, which is unsupported by the frontend ESLint flat config; verified with equivalent `npx eslint` on the same files and then ran the required frontend test suite (`npm test -- --run`, 29/29 passing).
- Manual UIUX-01 browser checks from `28-VALIDATION.md` remain required for hover/keyboard/Escape/outside-click/focus-return and layout-shift confirmation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 28 UIUX-01 implementation changes are complete and automated lint/tests pass.
- Ready for `/gsd-verify-work 28` to run manual UIUX-01 checks and close phase verification.

## Self-Check: PASSED

- FOUND: .planning/phases/28-polimento-ux-da-home/28-03-SUMMARY.md
- FOUND: 153ef7c
- FOUND: 99f455c

---
*Phase: 28-polimento-ux-da-home*
*Completed: 2026-11-22*
