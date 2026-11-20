---
phase: 23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3
plan: 01
subsystem: api
tags: [intent, mapper, nlp, fastapi, pytest, city-whitelist]

# Dependency graph
requires:
  - phase: 19
    provides: Intent contract and deterministic city mapping seam hardened in this plan
provides:
  - Deterministic raw-text city fallback no longer maps ambiguous "rio" mentions to "Rio de Janeiro"
  - Regression coverage for Rio Grande do Sul / Rio Branco false positives while preserving safe RJ detection
affects: [phase-23, chat-search, intent-mapping, audit-closure]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Whitelist-only raw-text city detection must avoid ambiguous bare tokens; prefer explicit canonical forms (rj, rio de janeiro)"

key-files:
  created: []
  modified:
    - backend/app/services/intent/mapper.py
    - backend/tests/test_intent_mapper.py

key-decisions:
  - "Remove bare \\brio\\b from raw-text Rio de Janeiro fallback and rely on \\brj\\b / \\brio\\s+de\\s+janeiro\\b to prevent false positives without inventing cities"

patterns-established:
  - "Raw-text city fallback regressions must include negative cases for ambiguous geographic names and positive cases for supported whitelist forms"

requirements-completed: [CL-01]

# Metrics
duration: 7min
completed: 2026-11-20
---

# Phase 23 Plan 01: Intent City Fallback Hardening Summary

**Hardened intent city fallback to reject ambiguous "rio" mentions while preserving safe whitelist-only Rio de Janeiro detection**

## Performance

- **Duration:** 7 min
- **Started:** 2026-11-20T20:10:00Z
- **Completed:** 2026-11-20T20:16:52Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Removed the ambiguous raw-text `\brio\b` pattern from Rio de Janeiro fallback detection in the intent mapper.
- Added deterministic regression coverage proving "Rio Grande do Sul" and "Rio Branco" are not mapped to "Rio de Janeiro" when no explicit city candidate is provided.
- Preserved safe supported RJ detection paths (`"rio de janeiro"` and `"rj"`) and kept existing mapper safeguards green.

## Task Commits

Each task was committed atomically:

1. **Task 1: Endurecer fallback raw-text de cidade no mapper e cobrir falsos positivos/positivos seguros** - `8d0c621` (test), `27e1a8c` (fix)

**Plan metadata:** pending final docs commit (recorded in this execution)

_Note: TDD task with RED and GREEN commits._

## Files Created/Modified
- `backend/app/services/intent/mapper.py` - Removed ambiguous bare `\brio\b` raw-text pattern from Rio de Janeiro whitelist detection.
- `backend/tests/test_intent_mapper.py` - Added false-positive safeguards for "Rio Grande do Sul"/"Rio Branco" while retaining supported RJ cases.

## Decisions Made
- Followed plan as specified: narrowed Rio de Janeiro raw-text detection to safe explicit signals only (`\brj\b`, `\brio\s+de\s+janeiro\b`) with no whitelist expansion.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- CL-01 code/test hardening for the reported false-positive hotspot is in place and covered by deterministic tests.
- Ready for remaining Phase 23 plan executions and subsequent audit/UAT closure work.

## Self-Check: PASSED

- FOUND: backend/app/services/intent/mapper.py
- FOUND: backend/tests/test_intent_mapper.py
- FOUND: .planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-01-SUMMARY.md
- FOUND commit: 8d0c621
- FOUND commit: 27e1a8c

---
*Phase: 23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3*
*Completed: 2026-11-20*
