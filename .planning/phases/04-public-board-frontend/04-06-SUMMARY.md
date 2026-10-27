---
phase: 04-public-board-frontend
plan: 06
subsystem: ui
tags: [nextjs, ads, accessibility, reduced-motion, ssr-gate, powershell, pt-br]
requires:
  - phase: 04-public-board-frontend
    provides: public shell and tokens (`04-01`)
  - phase: 04-public-board-frontend
    provides: public jobs API + demo seed (`04-02`)
  - phase: 04-public-board-frontend
    provides: SSR board and native dialog (`04-03`)
  - phase: 04-public-board-frontend
    provides: contact reveal and deep links (`04-04`)
  - phase: 04-public-board-frontend
    provides: URL-driven filter toolbar (`04-05`)
provides:
  - `AdSlot` shared component (header 90px, sidebar 300x250 at lg, inline 90px every 6 cards) — fixed heights, no scripts
  - Focus ring, reduced-motion, hover-only card border, dialog safe-area and text-wrap polish in `public.css`
  - `scripts/verify-ssr.ps1` (UTF-8 BOM) — executable SSR/URL/deep-link/admin-isolation gate
affects: []
tech-stack:
  added: []
  patterns:
    - "Ad placeholders are static, script-free boxes labelled 'Espaço publicitário' with dashed #6d5a91 border"
    - "Reduced-motion kills pulse/transitions/scroll-behavior; card border changes only on hover (hover-capable) or focus-within"
    - "SSR gate asserts contact fields are absent from HTML and admin stylesheets never contain --color-canvas"
key-files:
  created:
    - frontend/components/board/AdSlot.tsx
    - frontend/scripts/verify-ssr.ps1
  modified:
    - frontend/components/board/JobGrid.tsx
    - frontend/app/(public)/page.tsx
    - frontend/app/(public)/public.css
key-decisions:
  - "AdSlot stays a plain shared component (no 'use client') so both the RSC page and the client grid can import it."
  - "Inline slots render after cards 6/12/18 only when a following card exists (no trailing slot)."
  - "verify-ssr.ps1 is saved as UTF-8 with BOM so PowerShell 5.1 parses pt-BR literals correctly."
  - "The human checkpoint (15 UAT steps) was approved by the user."
requirements-completed: [UIUX-01, UIUX-02, UIUX-03]
duration: ~25min
completed: 2026-10-26
---

# Phase 4 Plan 6: Ads, accessibility polish and SSR gate Summary

**Reserved ad inventory, focus/motion/hover polish, and an executable SSR gate proving jobs/ads/deep-links in HTML with no contact data**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3 (2 auto + 1 human checkpoint, approved)
- **Files modified:** 5 (2 created, 3 modified)
- **Tests:** `npm run lint` + `npm run build` green; `/` dynamic; verify-ssr.ps1 parses as PowerShell with BOM

## Accomplishments

- `AdSlot` renders header (90px, max 728px centered), sidebar (300x250, sticky top-96, lg+ only) and inline (col-span-full, 90px) boxes with the exact label `Espaço publicitário`, dashed `#6d5a91` border, no scripts/iframe/raw HTML.
- `page.tsx` places the header slot above a two-column `lg:grid` (content + 300px sidebar); `JobGrid` renders an inline slot after every 6th card (when not the last).
- `public.css` adds the global focus-visible ring, `:focus:not(:focus-visible)` reset, reduced-motion (including `.animate-pulse`), hover-only card border, `text-wrap: balance` on h1/dialog title, `overflow-wrap: anywhere`, `min-height: 44px` touch targets, dialog backdrop/safe-area/max-height rules.
- `verify-ssr.ps1` (UTF-8 BOM) asserts: home SSR (jobs, ads >= 3, no contact fields), positive CSS control (`--color-canvas`), doacoes/admin isolation (admin stylesheets never contain `--color-canvas`), empty/out-of-range states, pagination (`Página 2 de`), API seed (>=25), limit cap (422), valid/bogus/malformed deep links (server-rendered not-found panel), API contract (limit=1, city slug/canonical, sort direction, search, unknown city).

## task Commits

1. **task 1: reserve the three ad slots** - (feat, 3 files)
2. **task 2: polish focus/motion/hover and add the SSR gate script** - (feat, 2 files)
3. **task 3: human verification of the public board** - approved by user

## Files Created/Modified

- `frontend/components/board/AdSlot.tsx` - new shared ad placeholder
- `frontend/components/board/JobGrid.tsx` - inline ad after every 6th card
- `frontend/app/(public)/page.tsx` - header slot + two-column layout with sidebar ad
- `frontend/app/(public)/public.css` - focus/motion/hover/dialog polish
- `frontend/scripts/verify-ssr.ps1` - SSR/URL/deep-link/admin gate (UTF-8 BOM)

## Decisions Made

- The human UAT (15 steps) was approved; the open Turnstile `action` blocker from Phase 03 was accepted as a known dev-only limitation and does not block the phase (anti-spam gate untouched).

## Deviations from Plan

None material.

## Issues Encountered

- PowerShell 5.1 console encoding mangles accented literals in interactive checks; the gate script itself is saved as UTF-8 with BOM and parses cleanly.

## User Setup Required

None for the build. Running `verify-ssr.ps1` requires the backend on :8000 and the built frontend on :3100 (see the script params).

## Next Phase Readiness

- Phase 4 is complete. Ready for Phase 5 (admin review area) or verification.

---
*Phase: 04-public-board-frontend*
*Completed: 2026-10-26*

## Self-Check: PASSED

- `frontend/components/board/AdSlot.tsx` exists.
- `frontend/scripts/verify-ssr.ps1` exists with UTF-8 BOM and parses.
- `npm run lint` and `npm run build` pass with `/` rendered as `ƒ (Dynamic)`.
- Human checkpoint approved.
