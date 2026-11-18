---
phase: 21-interface-de-chat-e-integracao-no-board
plan: 01
subsystem: ui
tags: [nextjs, typescript, vitest, chat-search, filters]
requires:
  - phase: 20-api-publica-de-chat-search-resiliente
    provides: Public POST /api/v1/public/chat-search contract (interpretation + JobPublic results, no contacts)
provides:
  - Vitest harness and chat-focused test script for frontend pure-logic tests
  - Typed chat-search request/response models and browser client in frontend/lib/api.ts
  - Pure mapping helpers from chat applied_params to canonical board Filters/href semantics
affects: [21-02, frontend-chat-ui, board-url-application]
tech-stack:
  added: [vitest@^2.1.9]
  patterns: [typed public chat client with ApiError/timeout handling, normalizeFilters-based applied_params mapping]
key-files:
  created:
    - frontend/vitest.config.ts
    - frontend/lib/chatApply.ts
    - frontend/lib/chatApply.test.ts
  modified:
    - frontend/package.json
    - frontend/package-lock.json
    - frontend/lib/api.ts
key-decisions:
  - "Configured Vitest with @ alias resolution and node environment for lib/**/*.test.ts pure-logic coverage."
  - "Kept chat client/types strictly contact-free (JobPublic results only) and surfaced transport/timeout failures as ApiError(status 0) with pt-BR-safe messages."
patterns-established:
  - "Pattern: Chat applied params flow through normalizeFilters with page reset to 1 and vaga cleared before canonical board application."
  - "Pattern: canApplyChatToBoard blocks degraded or non-useful/default-only states from apply actions."
requirements-completed: [UI-01, UI-02, UI-03]
duration: 8min
completed: 2026-11-18
---

# Phase 21 Plan 01: Chat Foundations Summary

**Vitest-backed frontend chat foundation with typed /api/v1/public/chat-search client and tested applied_params-to-board mapping that enforces canonical URL/reset/degraded rules.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-11-18T00:24:00Z
- **Completed:** 2026-11-18T00:32:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added a minimal frontend Vitest harness (`test`, `test:chat`) and node-environment config to run Phase 21 pure-logic tests.
- Implemented chat-search request/response/interpretation types and `chatSearch` POST client in `frontend/lib/api.ts` with 15s timeout, non-2xx `ApiError` handling, and pt-BR transport/timeout fallback messages.
- Implemented and unit-tested `appliedParamsToBoardFilters` and `canApplyChatToBoard` to map server `applied_params` through canonical filter normalization while resetting `page` to 1 and clearing `vaga`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add frontend Vitest harness and test scripts (Wave 0)** - `7de10df` (chore)
2. **Task 2: Implement typed chat-search client and applied_params-to-board mapping with tests** - `aaf6cc1` (feat)

## Files Created/Modified
- `frontend/vitest.config.ts` - Vitest node config, `lib/**/*.test.ts` include, and `@` alias resolution for tests.
- `frontend/package.json` - Added `test`/`test:chat` scripts and `vitest` devDependency.
- `frontend/package-lock.json` - Lockfile updated for Vitest installation.
- `frontend/lib/api.ts` - Added `Chat*` contract types and `chatSearch` client for `POST /api/v1/public/chat-search`.
- `frontend/lib/chatApply.ts` - Added pure helpers to convert applied params to canonical board filters and gate apply eligibility.
- `frontend/lib/chatApply.test.ts` - Unit tests covering mapping/reset/normalization and degraded/non-useful apply cases.

## Decisions Made
- Used Vitest (node environment) for fast, dependency-light pure-logic verification aligned with Wave 0 validation needs.
- Modeled chat interpretation/meta to include `degraded`, `degradation_reason`, and `guidance` while keeping result items as `JobPublic` only (no contact fields).
- Treated timeout/network failures as `ApiError` with status 0 and clear pt-BR messages consistent with existing browser client patterns.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added `@` path alias resolution to Vitest config**
- **Found during:** Task 2 (test execution)
- **Issue:** `npm --prefix frontend run test:chat` failed to resolve `@/lib/*` imports in tests/config context.
- **Fix:** Added `resolve.alias["@"]` in `frontend/vitest.config.ts` pointing to the frontend root.
- **Files modified:** `frontend/vitest.config.ts`
- **Verification:** `npm --prefix frontend run test:chat` passes (6 tests).
- **Committed in:** `aaf6cc1` (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required for the planned automated verification to run; no scope creep.

## Issues Encountered
- `npm --prefix frontend run test -- --version` (as written in Task 1 verification) exited non-zero because `vitest run` reports no matching test files before Task 2; harness functionality was confirmed via `npm --prefix frontend exec -- vitest --version` and subsequent `npm --prefix frontend run test:chat` (6 passing).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Chat contract client and deterministic apply-mapping primitives are ready for Phase 21 UI integration (chat panel, interpretation rendering, apply/open-detail flows).
- Frontend has a repeatable automated check for chat mapping/client-contract helpers (`npm --prefix frontend run test:chat`).

## Self-Check: PASSED

- FOUND: frontend/vitest.config.ts
- FOUND: frontend/lib/api.ts
- FOUND: frontend/lib/chatApply.ts
- FOUND: frontend/lib/chatApply.test.ts
- FOUND: .planning/phases/21-interface-de-chat-e-integracao-no-board/21-01-SUMMARY.md
- FOUND commit: 7de10df
- FOUND commit: aaf6cc1

---
*Phase: 21-interface-de-chat-e-integracao-no-board*
*Completed: 2026-11-18*
