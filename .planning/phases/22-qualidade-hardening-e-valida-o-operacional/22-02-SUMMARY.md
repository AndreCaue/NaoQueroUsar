---
phase: 22-qualidade-hardening-e-valida-o-operacional
plan: 02
subsystem: ui
tags: [nextjs, react, typescript, chat, kill-switch, vitest]

# Dependency graph
requires:
  - phase: 22-01
    provides: Operational chat kill-switch config, disabled response contract, and public chat-search status endpoint
provides:
  - Frontend chat status consumption and UX gating for confirmed-disabled chat state
  - Safe handling of chat_disabled responses without applying results to the canonical board
  - Pure chat-apply gating/tests that block disabled or degraded chat state from board application
affects: [22-03, phase-22-qa, public-chat]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Non-blocking chat availability check with backend-authoritative fail-safe behavior
    - UI response sanitization for disabled chat guidance without exposing internal reason tokens

key-files:
  created:
    - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-02-SUMMARY.md
  modified:
    - frontend/lib/api.ts
    - frontend/components/board/chat/ChatWidget.tsx
    - frontend/lib/chatApply.ts
    - frontend/lib/chatApply.test.ts

key-decisions:
  - "Treat chat status as UX-only: hide launcher/panel only when disabled is confirmed, but keep backend authoritative and fail safe if status fetch errors"
  - "On chat_disabled responses, stop rendering/opening chat UI, clear/apply nothing, and route users to manual board search with safe guidance"
  - "Sanitize disabled chat responses in the UI by removing internal chat_disabled limitation tokens while preserving safe pt-BR guidance"

patterns-established:
  - "Chat availability gating: consult status asynchronously on mount and never block board render/manual flows"
  - "Disabled chat defense-in-depth: block apply in pure helpers and in widget flow even if degraded metadata shape varies"

requirements-completed: [QA-02, QA-03]

# Metrics
duration: 4min
completed: 2026-11-18
---

# Phase 22 Plan 02: Chat kill-switch UI gating Summary

**Frontend chat status gating that hides disabled chat entrypoints, safely handles `chat_disabled` responses, and preserves manual board search with pure Vitest-covered apply guards**

## Performance

- **Duration:** 4 min
- **Started:** 2026-11-18T11:18:42Z
- **Completed:** 2026-11-18T11:22:27Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added public chat status types/client support in `frontend/lib/api.ts` to consume `GET /api/v1/public/chat-search/status` with short timeout/error handling.
- Updated `ChatWidget` to consult chat availability asynchronously, hide launcher/panel when disabled is confirmed, and safely handle `chat_disabled` responses without applying results or exposing internal details.
- Hardened pure chat-apply logic and Vitest coverage so disabled/degraded chat states (including `degradation_reason: "chat_disabled"`) cannot be applied to canonical board filters.

## Task Commits

Each task was committed atomically:

1. **Task 1: Consumir status do chat e ocultar launcher/painel quando desativado** - `fd05013` (feat)
2. **Task 2: Reforçar gating puro de aplicação do chat para estados desativados/degradados** - `ec4b9f7` (test)

**Plan metadata:** `2cc4b00` (docs: complete plan)

## Files Created/Modified
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-02-SUMMARY.md` - Execution summary, decisions, verification, and self-check for plan 22-02
- `frontend/lib/api.ts` - Added `ChatSearchStatus` and `getChatSearchStatus()` for backend chat availability signaling
- `frontend/components/board/chat/ChatWidget.tsx` - Added non-blocking status gating, disabled-response handling, and launcher/panel suppression for confirmed-disabled chat
- `frontend/lib/chatApply.ts` - Blocked `canApplyChatToBoard` for degraded state and explicit `chat_disabled` degradation reason
- `frontend/lib/chatApply.test.ts` - Extended pure tests to cover `chat_disabled` gating while preserving existing apply/mapping behavior

## Decisions Made
- Kept chat enabled by default in UI state and only hid chat entry when status explicitly confirmed `enabled:false`, preserving board usability if status fetch fails (backend remains authoritative).
- Treated `chat_disabled` responses as non-applicable terminal UX state for chat interaction: disable chat UI, clear active/applyable results, and focus manual search without mutating board filters.
- Removed internal `chat_disabled` limitation tokens from UI-facing sanitized disabled responses to avoid leaking reason codes while keeping safe guidance/manual-search fallback.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Sanitized disabled chat response limitations for safe UI copy**
- **Found during:** Task 1 (Consumir status do chat e ocultar launcher/painel quando desativado)
- **Issue:** Backend disabled responses may include `chat_disabled` in limitations/reason metadata; rendering those tokens would expose internal reason codes in user-facing UI
- **Fix:** Added UI-side sanitization for `chat_disabled` responses to strip internal limitation token while preserving safe pt-BR guidance and degraded/non-applicable state
- **Files modified:** `frontend/components/board/chat/ChatWidget.tsx`
- **Verification:** `cd frontend && npm run test:chat && npm test` passed; disabled handling keeps guidance/manual-search path without applying results
- **Committed in:** `fd05013` (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Auto-fix required for UI safety/privacy consistency with plan threat guidance. No scope creep; no board/manual-flow regression introduced.

## Issues Encountered
- `git merge-base HEAD eb32d56a4b3b47bff5ae0cad3d18532506f6ab79` could not resolve the full base hash object in this repository state, but `HEAD` (`eb32d56`) already matched the required base prefix; execution proceeded without reset.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Frontend now respects backend chat kill-switch signaling and keeps manual board search/list/detail flows independent when chat is disabled or degraded.
- Ready for remaining Phase 22 work (e.g. 22-03 operational validation/QA artifacts) with chat disabled-state UX and pure gating coverage in place.
- No blockers identified.

## Self-Check: PASSED

- FOUND: `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-02-SUMMARY.md`
- FOUND: `frontend/lib/api.ts`
- FOUND: `frontend/components/board/chat/ChatWidget.tsx`
- FOUND: `frontend/lib/chatApply.ts`
- FOUND: `frontend/lib/chatApply.test.ts`
- FOUND commit: `fd05013`
- FOUND commit: `ec4b9f7`
- Verified: `cd frontend && npm run test:chat && npm test` (exit 0)

---
*Phase: 22-qualidade-hardening-e-valida-o-operacional*
*Completed: 2026-11-18*
