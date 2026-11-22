---
phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review
plan: 01
subsystem: api
tags: [python, fastapi, pytest, intent, mapper, nlp]

# Dependency graph
requires:
  - phase: 23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3
    provides: Intent mapper/parser baseline and audit-identified CR-01/WR-03 findings
provides:
  - Canonical raw-text city conflict/divergence handling in deterministic intent mapper (CR-01/D-01..D-04)
  - Non-native influence detection by normalized token-set membership, preventing substring false positives (WR-03/D-05..D-06)
  - Deterministic regression coverage for city conflicts, safe fallbacks, and token-set influence
affects: [phase-24, intent, chat, api]

# Tech tracking
tech-stack:
  added: []
  patterns: [Canonical raw-text city signal via _detect_city_from_raw_text, normalized token-set membership for non-native influence]

key-files:
  created: []
  modified:
    - backend/app/services/intent/mapper.py
    - backend/tests/test_intent_mapper.py

key-decisions:
  - "Used _detect_city_from_raw_text(raw) as canonical raw city/conflict signal in candidate-present flow (D-02)"
  - "General non_whitelist_raw_conflict guard blocks promotion of supported city when non-whitelist city participates in explicit conflict (D-03)"
  - "Non-native influence uses normalized token-set membership (aq_tokens) instead of substring in full applied_q (D-05)"

patterns-established:
  - "City safety: raw conflict or raw-vs-candidate supported divergence => conflict_resolved, no applied city"
  - "Token influence: compare normalized tokens by set membership, not substring containment"

requirements-completed: [CL-01, CL-05]

# Metrics
duration: ~15min
completed: 2026-11-22
---

# Phase 24 Plan 01: Intent Mapper City Conflict and Token-Set Influence Summary

**Deterministic intent mapper now blocks candidate-present raw city conflicts/divergences and detects non-native influence by token-set membership, closing CR-01 and WR-03 regressions**

## Performance

- **Duration:** ~15 min (including recovery/finalization)
- **Started:** 2026-11-21T22:25:00Z (approx)
- **Completed:** 2026-11-21T22:39:30Z (approx)
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Closed CR-01: candidate-present alias/abbreviation/remote raw-text city conflicts and raw-vs-candidate supported divergence now resolve to `conflict_resolved` with no applied city.
- Preserved safe city behavior: same canonical city applies, candidate-absent single safe raw city applies, non-whitelist candidate remains `not_in_whitelist`, and non-whitelist-vs-supported explicit conflicts do not promote supported city.
- Closed WR-03: non-native influence detection uses normalized token-set membership, preventing substring false positives while preserving genuine textual approximation.

## Task Commits

Each task was committed atomically:

1. **Task 1: Corrigir CR-01 - conflito de cidade raw-text canônico com candidato presente** - `0c985b8` (fix)
2. **Task 2: Corrigir WR-03 - influência não nativa por token-set normalizado** - `d43ad15` (fix)

**Plan metadata:** recorded in final docs commit for this plan.

## Files Created/Modified

- `backend/app/services/intent/mapper.py` - Canonical raw-city conflict/divergence handling and token-set non-native influence detection.
- `backend/tests/test_intent_mapper.py` - CR-01 conflict/divergence/safeguard regressions and WR-03 token-set regression.

## Decisions Made

- Followed plan as specified for D-01..D-06. No contract/schema/API shape changes.
- Kept D-03 guard general (non-whitelist-vs-supported explicit conflict class), not token-name-specific.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adjusted existing Campinas/remoto combo expectation to CR-01-safe behavior**
- **Found during:** Task 1 (CR-01 regression run)
- **Issue:** `test_mvp_analista_dados_campinas_ou_remoto_salary_combo` expected `not_in_whitelist`; under D-03 the explicit "Campinas ou Remoto" conflict must resolve as `conflict_resolved` and not promote Remoto.
- **Fix:** Updated that test expectation to `conflict_resolved` per plan/D-03.
- **Files modified:** `backend/tests/test_intent_mapper.py`
- **Verification:** `cd backend && pytest -q tests/test_intent_mapper.py` (18 passed)
- **Committed in:** `0c985b8` (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - behavior aligned to plan/D-03)
**Impact on plan:** Necessary for correctness/safety. No scope creep.

## Authentication Gates

None.

## Issues Encountered

- **Execution recovery:** Task 1 was already committed on `main` (`0c985b8`), but the executor session did not produce `24-01-SUMMARY.md`. Task 2/WR-03 was resumed from current HEAD and completed without repeating CR-01.
- **Pre-existing/stale regression outside WR-03 scope:** `cd backend && pytest -q tests/test_intent_schema.py tests/test_intent_parser.py` => 1 failed, 13 passed. Failure: `tests/test_intent_parser.py::test_extract_and_map_intent_maps_coherent_candidate_deterministically` expects `applied_params.city in {"São Paulo","Remoto"}` for raw `"dev pleno SP remoto"`, but CR-01 now correctly treats "SP" vs "Remoto" as raw conflict and returns `city=None`, `conflict_resolved`. This is caused by CR-01 behavior, not WR-03 token-set change. Not modified in this recovery to avoid out-of-scope test edits.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CR-01 and WR-03 mapper fixes are implemented with deterministic mapper coverage.
- Phase verification should account for the stale parser test expectation conflicting with CR-01-safe behavior; decide whether to update that parser test/contract expectation as a follow-up.

## Self-Check: PASSED

- FOUND: backend/app/services/intent/mapper.py
- FOUND: backend/tests/test_intent_mapper.py
- FOUND: .planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-01-SUMMARY.md
- FOUND: 0c985b8 fix(24-01): resolve raw-text city conflicts with candidate present
- FOUND: d43ad15 fix(24-01): use token-set membership for non-native influence (WR-03)

---
*Phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review*
*Completed: 2026-11-22*