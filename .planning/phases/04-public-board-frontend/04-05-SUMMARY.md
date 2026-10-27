---
phase: 04-public-board-frontend
plan: 05
subsystem: ui
tags: [nextjs, client-component, url-state, debounce, filters, aria]
requires:
  - phase: 04-public-board-frontend
    provides: public shell and tokens (`04-01`)
  - phase: 04-public-board-frontend
    provides: public jobs API with `q`/`city`/`sort`/`page` (`04-02`)
  - phase: 04-public-board-frontend
    provides: SSR board, `normalizeFilters`, `buildBoardHref`, `hasActiveFilters` (`04-03`)
  - phase: 04-public-board-frontend
    provides: server-side `?vaga=` resolution and not-found panel (`04-04`)
provides:
  - `BoardToolbar` client component: debounced search, city chips, sort select, live count
  - URL as the single source of truth for `q`/`city`/`sort`/`page` (reset to page 1, drop `vaga` on any filter change)
  - Four distinct empty/out-of-range states with approved copy
  - Keyboard-usable toolbar (44px targets, visible focus, aria-pressed chips, aria-live count)
affects: [04-06]
tech-stack:
  added: []
  patterns:
    - "Filter writes go through `router.replace` inside `startTransition` (no `push`, no history pollution)"
    - "Debounced typing (300 ms) with immediate commit on Enter/clear/chip change"
    - "Single `aria-live` count region; empty states replace it rather than duplicate it"
    - "Grid remount keyed on `q|city|sort|page` so card expansion/dialog reset on filter change"
key-files:
  created:
    - frontend/components/board/BoardToolbar.tsx
  modified:
    - frontend/app/(public)/page.tsx
key-decisions:
  - "Debounce constant is 300 ms; `maxLength={80}` enforced on both client and server (04-02 already clamps)."
  - "City chips are single-select (`Todas` + the 4 cities) with `aria-pressed`; mobile scrolls horizontally, desktop wraps."
  - "Count region renders only when `total > 0`; empty states carry their own copy (no duplicate live region)."
  - "Kept the 04-04 server-rendered not-found panel above the grid; it survives the toolbar rewrite."
  - "Grid `key` uses `q|city|sort|page` (not `buildBoardHref`) so an open `?vaga=` deep link does not force a remount."
requirements-completed: [PUBL-01, SRCH-01, SRCH-02, SRCH-03]
duration: ~15min
completed: 2026-10-26
---

# Phase 4 Plan 5: Filter toolbar Summary

**URL-driven search, city chips and sort on the board, with debounced typing, four approved empty states and a single live count region**

## Performance

- **Duration:** ~15 min
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)
- **Tests:** `npm run lint` + `npm run build` green; `/` still `ƒ (Dynamic)`

## Accomplishments

- `BoardToolbar` commits `q`/`city`/`sort` through `router.replace(buildBoardHref(...), { scroll: false })` inside `startTransition`, always resetting `page` to 1 and dropping `vaga`.
- Typing debounces at 300 ms; Enter flushes immediately, Escape clears and commits `{ q: "" }`, and a clear button (44×44) commits immediately.
- City chips are single-select (`Todas` + São Paulo, Rio de Janeiro, Belo Horizonte, Remoto) with `aria-pressed`; mobile horizontal scroll, desktop wrap.
- Native sort select (`Mais recentes`/`Mais antigas`) commits on change.
- Count renders in an `aria-live="polite"` `role="status"` region only when `total > 0`.
- Page wires the toolbar under the subtitle and keeps the four empty/out-of-range states (`Nenhuma vaga encontrada`, `Nenhuma vaga publicada ainda`, `Nenhuma vaga nesta página`, plus the not-found panel) with the approved copy and `Limpar filtros`/`Voltar para a primeira página` CTAs.
- `loading.tsx` already matches the final grid (`grid-cols-1 … xl:grid-cols-3`) with `aria-busy` and reduced-motion-safe pulse.

## task Commits

1. **task 1: build the toolbar (debounced search, chips, sort, live count)** - `65d763c` (feat)
2. **task 2: wire the toolbar into the page and finish the board states** - `c052be9` (feat)

## Files Created/Modified

- `frontend/components/board/BoardToolbar.tsx` - new client toolbar
- `frontend/app/(public)/page.tsx` - toolbar wiring, standalone count removed, grid key updated

## Decisions Made

- Single `aria-live` region lives in the toolbar; the page no longer renders its own count paragraph (avoids duplicate announcements).
- Grid remount key is `q|city|sort|page` rather than the full href, so opening a `?vaga=` dialog never remounts the grid.

## Deviations from Plan

None material.

## Issues Encountered

- `npm run lint` warns about the inferred workspace root from a parent `package-lock.json`; build and routes unaffected.

## User Setup Required

None.

## Next Phase Readiness

- Board is fully interactive and URL-driven; ready for 04-06 (ad slots, accessibility polish, SSR gate, human checkpoint).

---
*Phase: 04-public-board-frontend*
*Completed: 2026-10-26*

## Self-Check: PASSED

- `frontend/components/board/BoardToolbar.tsx` exists.
- Commits `65d763c`, `c052be9` exist in git history.
- `npm run lint` and `npm run build` pass with `/` rendered as `ƒ (Dynamic)`.
