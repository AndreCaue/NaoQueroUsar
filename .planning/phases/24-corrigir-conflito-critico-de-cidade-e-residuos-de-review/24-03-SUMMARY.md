---
phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review
plan: 03
subsystem: api, ui
tags: [python, fastapi, pytest, intent, mapper, react, accessibility, focus]
gap_closure: true

# Dependency graph
requires:
  - phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review
    provides: CR-01/WR-03 mapper baseline and chat focus helper/detail behavior from 24-01/24-02
provides:
  - D-03 city conflict guard narrowed so '/' only counts as city-alt separator adjacent to supported city mention
  - Regression coverage for slash-separated non-city queries with safe supported city application
  - ChatPanel close button guarded by dismissible while preserving mounted focusable D-08 fallback
affects: [phase-24, intent, chat, ui, accessibility]

# Tech tracking
tech-stack:
  added: []
  patterns: [Slash-as-city-alt only when adjacent to supported city token, aria-disabled for non-dismissible mounted focus fallback]

key-files:
  created: []
  modified:
    - backend/app/services/intent/mapper.py
    - backend/tests/test_intent_mapper.py
    - frontend/components/board/chat/ChatPanel.tsx

key-decisions:
  - "Treat '/' as D-03 conflict separator only when adjacent to a supported whitelist city mention; keep natural-language ou/or/vs separators unchanged"
  - "Use aria-disabled + no-op click for non-dismissible ChatPanel close control instead of HTML disabled so #chat-panel-close remains focusable as D-08 fallback"

patterns-established:
  - "City conflict parsing: split on '/' only for supported-city-alt forms; never for generic role/stack slashes"
  - "Focus fallback controls: keep mounted and focusable during detail-open state; guard action with dismissible"

requirements-completed: [CL-01, CL-05]

# Metrics
duration: ~10min
completed: 2026-11-22
---

# Phase 24 Plan 03: Gap Closure - Slash City Conflict and Chat Close Focus Fallback Summary

**Narrowed D-03 slash conflict detection to prevent non-city false positives and guarded ChatPanel close action during detail-open state while keeping the D-08 focus fallback mounted and focusable**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-11-21T23:27:00Z (approx)
- **Completed:** 2026-11-21T23:29:30Z (approx)
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Closed 24-VERIFICATION Gap 1 (CR-01/D-03): slash-separated non-city terms like `analista/pleno em sp`, `dev/frontend remoto`, and `dev/frontend em sp` no longer produce false `conflict_resolved`; safe supported city is applied when applicable.
- Preserved D-01/D-03 safety: existing non-whitelist-vs-supported conflicts (`vaga em campinas ou remoto`, `vaga em curitiba ou sao paulo`) remain `conflict_resolved` with no wrong city promoted.
- Closed 24-VERIFICATION Gap 2 (WR-01/D-08 edge case): ChatPanel close button now respects `dismissible` (`onClick` guarded, `aria-disabled` set) while remaining mounted/focusable; Escape/backdrop guards unchanged; no focus trap added.

## Task Commits

Each task was committed atomically:

1. **Task 1: Remover falso positivo de conflito de cidade por '/' não-cidade no mapper** - `c2b7106` (fix)
2. **Task 2: Guardar botão Fechar chat durante detalhe aberto para preservar fallback de foco D-08** - `33107f0` (fix)

**Plan metadata:** committed separately as docs metadata (SUMMARY).

## Files Created/Modified

- `backend/app/services/intent/mapper.py` - Narrowed D-03 conflict separator handling: `ou/or/vs` always, `/` only when adjacent to supported city mention; split pattern conditional on `has_slash_city_alt`.
- `backend/tests/test_intent_mapper.py` - Added `test_slash_non_city_terms_do_not_trigger_city_conflict_cr01` covering slash non-city queries with safe supported-city application.
- `frontend/components/board/chat/ChatPanel.tsx` - Guarded close button click with `dismissible` and added `aria-disabled={!dismissible || undefined}`; kept button mounted/focusable (no HTML `disabled`).

## Decisions Made

- Followed plan exactly for D-01/D-03 and D-07/D-08. No contract/schema/API/contact-surface changes.
- Did not add focus trap custom behavior (WR-02/D-14 remains deferred per plan/context).

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Threat Flags

None - no new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries. Changes are deterministic mapper guard and client-side focus/click guard.

## Issues Encountered

- **Manual WR-01 keyboard edge case not executed in CLI environment:** The required browser/manual acceptance (open chat, open detail, attempt close chat while detail open, close detail, confirm focus returns to connected trigger or `#chat-panel-close`, never `document.body`) was not run here. Code-path guard is in place (`dismissible={!selectedJob}` in ChatWidget, `onClick`/`aria-disabled` guard in ChatPanel, Escape/backdrop guards unchanged, `chatFocus` fallback helper unchanged). Human/browser UAT should confirm.

## User Setup Required

None - no external service configuration required.

## Verification

- `cd backend && pytest -q tests/test_intent_mapper.py` — **19 passed**
- `cd backend && pytest -q tests/test_intent_schema.py tests/test_intent_parser.py` — **14 passed**
- `cd frontend && npm run test -- lib/chatApply.test.ts lib/chatFocus.test.ts` — **11 passed** (2 files)
- Manual WR-01 edge case — **NOT RUN (human/browser verification required)**

## Next Phase Readiness

- Verification gaps CR-01 slash false-positive and WR-01 close-button/focus-fallback edge case are addressed in code with automated regressions passing.
- Phase 24 verification/human UAT can recheck WR-01 keyboard flow in browser to confirm no `document.body` focus and no chat dismiss while detail open.

## Self-Check: PASSED

- FOUND: backend/app/services/intent/mapper.py
- FOUND: backend/tests/test_intent_mapper.py
- FOUND: frontend/components/board/chat/ChatPanel.tsx
- FOUND: .planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-03-SUMMARY.md
- FOUND: c2b7106 fix(24-03): avoid slash false positive in city conflict guard
- FOUND: 33107f0 fix(24-03): guard chat close button while detail is open

---
*Phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review*
*Completed: 2026-11-22*