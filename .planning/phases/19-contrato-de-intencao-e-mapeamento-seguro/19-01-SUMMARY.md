---
phase: 19-contrato-de-intencao-e-mapeamento-seguro
plan: 01
subsystem: intent
tags: [backend, fastapi, pydantic, intent, search, deterministic-mapping]
dependency_graph:
  requires: []
  provides:
    - strict-intent-contract
    - deterministic-safe-mapper
    - auditable-field-statuses
  affects:
    - backend/app/services/intent
    - backend/tests
tech_stack:
  added: []
  patterns:
    - pydantic-v2-strict-models
    - server-authoritative-deterministic-mapping
    - whitelist-normalization-via-resolve_city
    - explicit-only-sort-and-conflict-resolution
key_files:
  created:
    - backend/app/services/intent/__init__.py
    - backend/app/services/intent/schema.py
    - backend/app/services/intent/mapper.py
    - backend/tests/test_intent_schema.py
    - backend/tests/test_intent_mapper.py
  modified: []
key_decisions:
  - "LLM candidate intent is untrusted; mapper computes understood/applied/status and final applied_params deterministically"
  - "FieldStatus implemented as Enum with pt-BR values (aplicado, ignorado, aproximado) while keeping strict schema validation"
  - "City application restricted to whitelist-safe resolution (resolve_city + obvious safe aliases like SP/home office) and conflict-safe behavior"
  - "Sort applied only on explicit signals from raw text; non-native fields never become structured filters and are approximated in q or ignored with explicit reasons"
requirements_completed:
  - INT-01
  - INT-02
  - INT-03
duration: 3m44s
completed: 2026-11-17
---

# Phase 19 Plan 01: Contrato de intenção e mapeamento seguro Summary

**Strict pt-BR intent contract and deterministic mapper producing auditable entendido/aplicado statuses with safe `q/city/sort` params for public search.**

## Performance

- **Duration:** 3m44s
- **Tasks:** 2 (both TDD)
- **Files created:** 5

## Accomplishments

- Added `backend/app/services/intent/schema.py` with strict Pydantic v2 models (`extra="forbid"`) for LLM candidate intent and server-authoritative contract: `IntentLLMOutput`, `UnderstoodIntent`, `AppliedParams`, `FieldAssessment`, and `IntentContract`, including salary structure and non-native field traceability (`value/raw`).
- Implemented `backend/app/services/intent/mapper.py` with deterministic, server-side logic: `build_empty_intent(...)` for valid no-parameter intent (D-15) and `map_intent(...)` for normalization, whitelist-safe city mapping via `resolve_city`, explicit-only sort detection, conflict handling, q composition/cleanup, and per-field statuses with reason codes.
- Ensured applied params stay compatible with public search semantics (`q` stripped/None, `city` canonical whitelist or None, `sort` only explicit) and that salary/modalidade/contrato/senioridade never become native structured filters (aproximado via textual `q` influence or ignorado with explicit limitations).
- Added pure unit tests covering schema defaults/strictness and mapper behaviors (whitelist/rejections, explicit/conflicting sort, non-native approximation, empty intent, applied params safety).

## Task Commits

Each task was committed atomically (TDD commits recorded in history):

1. **Task 1: Definir schemas estritos do contrato de intenção (entendido/aplicado/status)** - `e776f14` (test) — includes schema implementation in recorded commit state
2. **Task 2: Implementar mapper determinístico (...) e testes puros** - `14435f7` (test) — includes mapper implementation and exports in recorded commit state

## Files Created/Modified

- `backend/app/services/intent/__init__.py` - Public intent domain exports (schema + mapper APIs)
- `backend/app/services/intent/schema.py` - Strict intent/candidate/contract schemas and status models
- `backend/app/services/intent/mapper.py` - Deterministic normalization, conflict resolution, classification, and safe applied params
- `backend/tests/test_intent_schema.py` - Schema/defaults/strictness validation tests
- `backend/tests/test_intent_mapper.py` - Deterministic mapper behavior and applied_params safety tests

## Decisions Made

- Reused canonical search whitelist helper `app.services.cities.resolve_city` for applied city safety; added obvious-safe handling for explicit cases required by plan/tests (e.g. `SP`, `home office`).
- Kept domain isolated from `app.services.extraction` (no job-extraction coupling); mapper is pure and DB/LLM independent.
- Treated sort as explicit-only based on raw-text signals/conflicts; avoided inventing defaults in intent contract.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Windows `git index.lock` contention appeared during commit attempts; resolved by removing stale lock and verifying commit contents. No code impact.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Intent contract and deterministic mapping foundation are ready for Phase 20 chat-search orchestration/endpoint work (LLM parsing seam + API wiring can consume `IntentLLMOutput`/`IntentContract`/`map_intent`/`build_empty_intent`).
- No HTTP route, DB changes, or STATE/ROADMAP updates performed (orchestrator-owned).

## Self-Check: PASSED

- FOUND: backend/app/services/intent/__init__.py
- FOUND: backend/app/services/intent/schema.py
- FOUND: backend/app/services/intent/mapper.py
- FOUND: backend/tests/test_intent_schema.py
- FOUND: backend/tests/test_intent_mapper.py
- FOUND commit: e776f14
- FOUND commit: 14435f7
- VERIFIED: `cd backend && python -m pytest tests/test_intent_schema.py tests/test_intent_mapper.py -x -q` (13 passed)
