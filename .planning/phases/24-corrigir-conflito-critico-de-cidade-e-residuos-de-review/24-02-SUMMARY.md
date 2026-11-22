---
phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review
plan: 02
subsystem: ui
tags: [react, nextjs, a11y, focus, chat, dialog, vitest]

# Dependency graph
requires:
  - phase: 23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3
    provides: Chat detail baseline and audit-identified WR-01 focus-loss finding
provides:
  - Stable chat detail close focus restore to connected trigger or mounted ChatPanel fallback
  - ChatPanel dismissibility guard so native detail dialog can remain active while chat stays mounted
  - Deterministic Vitest coverage for focus target fallback selection
affects: [phase-24, chat, a11y]

# Tech tracking
tech-stack:
  added: []
  patterns: [Pure DOM target selection helper for focus restore, mounted-panel/detail coexistence with dismissible guard]

key-files:
  created:
    - frontend/lib/chatFocus.ts
    - frontend/lib/chatFocus.test.ts
  modified:
    - frontend/components/board/chat/ChatPanel.tsx
    - frontend/components/board/chat/ChatWidget.tsx

key-decisions:
  - "Kept ChatPanel mounted during chat-opened job detail and suppressed panel dismiss only while detail is open (D-07)"
  - "Restored focus via getChatDetailCloseFocusTarget to connected trigger or #chat-panel-close fallback; never document.body (D-08)"
  - "Did not add custom focus trap; native dialog remains the accessibility boundary (WR-02/D-14 deferred)"

patterns-established:
  - "Focus restore fallback: prefer original trigger.isConnected, else mounted stable fallback, else no-op"
  - "Mounted overlay coexistence: keep background panel mounted but disable its dismiss handlers while native modal dialog is active"

requirements-completed: [CL-05]

# Metrics
duration: 2min
completed: 2026-11-22
---

# Phase 24 Plan 02: Chat Detail Focus Restore Summary

**Chat detail close now restores keyboard focus to the originating trigger or mounted chat close fallback while keeping ChatPanel mounted behind the native dialog**

## Performance

- **Duration:** 2 min 16s
- **Started:** 2026-11-22T00:24:22Z
- **Completed:** 2026-11-22T00:26:38Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `getChatDetailCloseFocusTarget` to deterministically select a connected trigger or mounted fallback without ever returning `document.body`.
- Updated `ChatPanel` with a stable `#chat-panel-close` fallback, `dismissible` guard, and Escape/backdrop suppression while detail is active.
- Updated `ChatWidget` to keep the chat panel mounted during detail open and restore focus on close through the helper and `requestAnimationFrame`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar helper testável de foco e tornar ChatPanel compatível com montagem durante detalhe** - `c148f84` (test), `65a3a3b` (feat)
2. **Task 2: Manter ChatPanel montado no detalhe e restaurar foco para alvo estável** - `0e3b04a` (fix)

**Plan metadata:** recorded in final docs commit for this plan.

_Note: TDD task has multiple commits (test → feat)._

## Files Created/Modified

- `frontend/lib/chatFocus.ts` - Pure helper selecting connected trigger or mounted fallback for detail-close focus restore.
- `frontend/lib/chatFocus.test.ts` - Vitest coverage for connected/disconnected/null/undefined focus target selection.
- `frontend/components/board/chat/ChatPanel.tsx` - Adds `dismissible` behavior and stable `chat-panel-close` fallback button id.
- `frontend/components/board/chat/ChatWidget.tsx` - Keeps chat mounted during detail open and restores focus safely on detail close.

## Decisions Made

- Kept the fix minimal and local to chat focus orchestration; no custom focus trap added because the native `JobDetailDialog` remains the modal boundary (WR-02/D-14 deferred).
- Used `document.getElementById("chat-panel-close")` as the mounted fallback target only when the original trigger is disconnected.

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Issues Encountered

- Manual WR-01 keyboard acceptance was not executed in this non-interactive execution. Automated coverage confirms helper fallback selection and chatApply/chatFocus regression suites pass; component keyboard flow remains for human/manual verification as recorded in plan verification.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- WR-01 chat detail-close focus restore primitives are in place and covered by deterministic helper tests.
- Phase 24 Plan 01 (city conflict) is independent; phase-level readiness depends on that plan and any required manual WR-01 keyboard acceptance.

## Self-Check: PASSED

- FOUND: frontend/lib/chatFocus.ts
- FOUND: frontend/lib/chatFocus.test.ts
- FOUND: frontend/components/board/chat/ChatPanel.tsx
- FOUND: frontend/components/board/chat/ChatWidget.tsx
- FOUND: .planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-02-SUMMARY.md
- FOUND: c148f84 test(24-02): add failing test for chat focus restore
- FOUND: 65a3a3b feat(24-02): add stable chat detail focus restore primitives
- FOUND: 0e3b04a fix(24-02): restore chat focus after detail close

---
*Phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review*
*Completed: 2026-11-22*
