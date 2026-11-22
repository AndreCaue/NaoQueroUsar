---
phase: 27-controles-por-ambiente
plan: 01
subsystem: ui
tags: [nextjs, env, ads, donation, security, vitest]

# Dependency graph
requires:
  - phase: 26-acesso-admin-dedicado
    provides: Public layout/header stable after admin entry separation
provides:
  - Central public env helpers for ads flag and donation URL validation
  - Env-gated AdSlot rendering across header, sidebar, and inline placements
  - Safe Doações header destination with external http(s) or /doacoes fallback
  - Env-aware SSR verification script for ads enabled/disabled states
affects: [28-polimento-ux-da-home, deploy-config, verify-ssr]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Central NEXT_PUBLIC env parsing helpers with pure, testable functions"
    - "Single AdSlot gate controls all public ad placements uniformly"
    - "External donation URLs allowed only as absolute http/https with noopener noreferrer"

key-files:
  created:
    - frontend/lib/publicEnv.ts
    - frontend/lib/publicEnv.test.ts
  modified:
    - frontend/components/board/AdSlot.tsx
    - frontend/app/(public)/layout.tsx
    - frontend/app/(public)/page.tsx
    - frontend/.env.example
    - frontend/.env.local.example
    - frontend/scripts/verify-ssr.ps1

key-decisions:
  - "Parse NEXT_PUBLIC_ADS_ENABLED with explicit disable allowlist (false/0/off/no/disabled, case-insensitive); absent/unknown values keep ads visible (D-01)."
  - "Accept donation destination only as absolute http/https URL; any absent/invalid/unsafe value falls back to internal /doacoes (D-04/D-05)."
  - "Collapse public ad layout container when ads disabled to avoid an empty desktop sidebar gutter while keeping all ad placements absent."

patterns-established:
  - "Public env controls: read NEXT_PUBLIC_* via static property access and validate through pure helpers"
  - "Ad visibility: gate at AdSlot component boundary so all placements obey one flag"

requirements-completed: [ADS-01, DONA-01]

# Metrics
duration: 4 min
completed: 2026-11-22
---

# Phase 27 Plan 01: Controles por Ambiente Summary

**Env-driven public ad visibility and safe donation destination controls using testable NEXT_PUBLIC helpers, central AdSlot gating, and env-aware SSR verification**

## Performance

- **Duration:** 4 min
- **Started:** 2026-11-22T22:57:20-03:00
- **Completed:** 2026-11-22T23:01:01-03:00
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Added `publicEnv` helpers with unit tests covering default-visible ads, explicit disable values, and strict http/https donation URL validation (ADS-01, DONA-01, D-01, D-04, D-05).
- Gated all public ad placements through `AdSlot` and made the header Doações button open a validated external URL in a new tab or safely fall back to `/doacoes` (D-02, D-03, D-04, D-05, D-06).
- Documented the new env vars in frontend env examples and made `verify-ssr.ps1` accept ads-enabled and ads-disabled states without false negatives.

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar helpers publicEnv com parsing seguro e testes (ADS-01, DONA-01, D-01, D-04, D-05)** - `044ae17` (test), `c3d2c71` (feat)
2. **Task 2: Aplicar gate central de anúncios e destino seguro de Doações na UI pública (ADS-01, DONA-01, D-02, D-03, D-04, D-05, D-06)** - `5846c55` (feat)
3. **Task 3: Documentar env vars e tornar verify-ssr.ps1 env-aware (ADS-01, DONA-01)** - `8570cf5` (docs)

**Plan metadata:** recorded in final docs commit for this plan.

_Note: TDD task produced RED (test) and GREEN (feat) commits._

## Files Created/Modified
- `frontend/lib/publicEnv.ts` - Pure helpers for ads flag parsing and safe donation URL validation with static NEXT_PUBLIC access.
- `frontend/lib/publicEnv.test.ts` - Vitest coverage for D-01/D-04/D-05 parsing, case/trim handling, and unsafe URL rejection.
- `frontend/components/board/AdSlot.tsx` - Central ad gate returns null when ads disabled; enabled markup/a11y unchanged.
- `frontend/app/(public)/layout.tsx` - Header Doações renders external anchor with noopener/noreferrer or internal /doacoes fallback.
- `frontend/app/(public)/page.tsx` - Public page conditionally renders ad placements and collapses ad layout when disabled.
- `frontend/.env.example` - Documents NEXT_PUBLIC_ADS_ENABLED and NEXT_PUBLIC_DONATION_URL with D-01/D-04/D-05/D-06 semantics.
- `frontend/.env.local.example` - Adds local-dev defaults/comments for new public env controls.
- `frontend/scripts/verify-ssr.ps1` - Adds Get-AdsEnabled and env-aware ad assertions for default and disabled modes.

## Decisions Made
- Used a pure helper module (`frontend/lib/publicEnv.ts`) as the single source of truth for env parsing to keep UI components simple and tests deterministic.
- Treated any non-explicit ad-disable value as visible, preserving current behavior by default (D-01).
- Treated invalid donation URLs as absent and fell back to `/doacoes`, preventing unsafe schemes and broken destinations (D-05).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Collapsed desktop ad grid when ads disabled**
- **Found during:** Task 2 (Aplicar gate central de anúncios e destino seguro de Doações na UI pública)
- **Issue:** Omitting the sidebar aside alone would leave an explicit 300px desktop grid track, creating an empty gutter when ads were disabled.
- **Fix:** Made the board container grid class conditional on `adsEnabled` so the layout collapses cleanly when ad placements are hidden.
- **Files modified:** frontend/app/(public)/page.tsx
- **Verification:** `cd frontend && npx vitest run lib/publicEnv.test.ts && npm run build` passed; ad placements remain conditionally rendered.
- **Committed in:** 5846c55 (part of task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Necessary for clean layout when ads are disabled. No scope creep; ad gate and donation behavior remain as specified.

## Issues Encountered
- PowerShell does not accept `&&` in this environment; verification commands were run as separate sequential commands with exit-code checks. No impact on deliverables.

## User Setup Required

None - no external service configuration required. New `NEXT_PUBLIC_*` vars are documented in `frontend/.env.example`; changing them requires rebuild/redeploy.

## Next Phase Readiness
- Phase 27 env controls are in place for ads and donations, with safe defaults and build/test verification.
- Phase 28 can focus on home UX polish; no blockers identified.

## Self-Check: PASSED

- FOUND: frontend/lib/publicEnv.ts
- FOUND: frontend/lib/publicEnv.test.ts
- FOUND: frontend/components/board/AdSlot.tsx
- FOUND: frontend/app/(public)/layout.tsx
- FOUND: frontend/app/(public)/page.tsx
- FOUND: frontend/.env.example
- FOUND: frontend/.env.local.example
- FOUND: frontend/scripts/verify-ssr.ps1
- FOUND commit: 044ae17
- FOUND commit: c3d2c71
- FOUND commit: 5846c55
- FOUND commit: 8570cf5

---
*Phase: 27-controles-por-ambiente*
*Completed: 2026-11-22*
