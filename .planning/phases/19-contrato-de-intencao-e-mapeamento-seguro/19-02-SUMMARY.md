---
phase: 19-contrato-de-intencao-e-mapeamento-seguro
plan: 02
subsystem: intent
tags: [backend, fastapi, pydantic, intent, groq, parser, secure-prompting]
dependency_graph:
  requires:
    - 19-01 (intent schema and deterministic mapper)
  provides:
    - intent-groq-client-seam
    - intent-parser-orchestrator
    - safe-empty-intent-contract-api
  affects:
    - backend/app/services/intent
    - backend/tests
tech_stack:
  added: []
  patterns:
    - groq-strict-json-schema-seam
    - untrusted-input-delimitation
    - injectable-llm-client-for-tests
    - deterministic-safe-degradation
key_files:
  created:
    - backend/app/services/intent/client.py
    - backend/app/services/intent/parser.py
    - backend/tests/test_intent_client.py
    - backend/tests/test_intent_parser.py
  modified:
    - backend/app/services/intent/__init__.py
key_decisions:
  - "Intent LLM seam isolated in `services/intent` with env-driven GROQ model chain/timeout and no coupling to job extraction domain"
  - "User NL query treated as untrusted data via `<CONSULTA_BUSCA>` delimiters/sanitization and strict server-side schema validation of LLM output"
  - "Parser degrades empty/generic/failed extraction paths to deterministic safe IntentContract (`build_empty_intent`) instead of opaque technical failures"
requirements_completed:
  - INT-01
  - INT-02
  - INT-03
duration: 2m22s
completed: 2026-11-17
---

# Phase 19 Plan 02: Contrato de intenção e mapeamento seguro Summary

**Groq intent client seam and deterministic parser/orchestrator producing safe, schema-validated intent contracts (including empty/failure fallbacks) ready for Phase 20 consumption.**

## Performance

- **Duration:** 2m22s
- **Tasks:** 2 (both TDD)
- **Files modified:** 5

## Accomplishments

- Added `backend/app/services/intent/client.py` with isolated intent extraction seam: pt-BR system prompt, `<CONSULTA_BUSCA>` untrusted-input wrapping/sanitization, strict `json_schema` (`search_intent`, `strict: true`) for `IntentLLMOutput`, env-driven `model_chain`/timeout reuse, lazy real-client construction, bounded parse/repair fallback, and injectable `client`/`sleep` for network-free tests.
- Added `backend/app/services/intent/parser.py` with `parse_intent` and `extract_and_map_intent` orchestration: empty/whitespace input short-circuits to safe contracts without LLM calls, successful candidates map through deterministic `map_intent`, and LLM/parse/call failures degrade to `build_empty_intent(..., reason_code="no_extractable_params")` to avoid opaque contract-level errors.
- Updated `backend/app/services/intent/__init__.py` to export the consolidated public API (`IntentExtractionError`, `call_intent_llm`, `parse_intent`, `extract_and_map_intent` plus schema/mapper types).
- Added `backend/tests/test_intent_client.py` and `backend/tests/test_intent_parser.py` covering prompt delimitation/sanitization, strict response format/model chain, fake-client parsing, empty/generic/coherent/injection-shaped inputs, and safe degradation on simulated failures (no network/DB).

## Task Commits

Each task was committed atomically (TDD):

1. **Task 1: Implementar client Groq de intent (strict schema, prompt seguro, seam injetável)** - `94c9833` (test), `d1a80bb` (feat)
2. **Task 2: Implementar parser/orquestrador e API interna do intent (vazio seguro, parse+map, exports)** - `48f2a47` (test), `400d14f` (feat)

## Files Created/Modified

- `backend/app/services/intent/client.py` - Groq strict JSON intent client, secure prompt wrapping, model chain, injectable seam and parsing/repair
- `backend/app/services/intent/parser.py` - Parse/map orchestration with safe empty/failure handling
- `backend/app/services/intent/__init__.py` - Consolidated public exports for intent domain
- `backend/tests/test_intent_client.py` - Client seam, strict payload, and untrusted-input tests (fake client)
- `backend/tests/test_intent_parser.py` - Parser/contract safety and deterministic mapping integration tests (fake client)

## Decisions Made

- Reused extraction robustness patterns (strict JSON schema, fence stripping, repair attempt, injectable client/sleep, env model chain) while keeping intent domain fully isolated from `app.services.extraction` job schemas/extractor.
- Chose contract-level safe degradation (`no_extractable_params`) for unrecoverable LLM/parse failures so downstream Phase 20 can rely on a structured intent result instead of opaque technical crashes.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Intent service API is complete for internal consumption: `extract_and_map_intent`/`parse_intent` + strict schema + deterministic mapper produce auditable, safe contracts compatible with public search semantics (`q/city/sort`).
- Phase 20 can wire the public chat-search endpoint/UX protections on top of this seam; no HTTP route, DB changes, or STATE/ROADMAP updates were made (orchestrator-owned).

## Self-Check: PASSED

- FOUND: backend/app/services/intent/client.py
- FOUND: backend/app/services/intent/parser.py
- FOUND: backend/app/services/intent/__init__.py
- FOUND: backend/tests/test_intent_client.py
- FOUND: backend/tests/test_intent_parser.py
- FOUND commit: 94c9833
- FOUND commit: d1a80bb
- FOUND commit: 48f2a47
- FOUND commit: 400d14f
- VERIFIED: `cd backend && python -m pytest tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_client.py tests/test_intent_parser.py -x -q` (25 passed)
