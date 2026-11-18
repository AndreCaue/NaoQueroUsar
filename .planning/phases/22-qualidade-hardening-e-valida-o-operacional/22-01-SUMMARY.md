---
phase: 22-qualidade-hardening-e-valida-o-operacional
plan: "01"
subsystem: api
tags: [fastapi, chat-search, observability, kill-switch, pytest, privacy]

# Dependency graph
requires:
  - phase: 20-api-publica-de-chat-search-resiliente
    provides: public chat-search endpoint, intent/search orchestration, degraded-safe response contract
  - phase: 21-interface-de-chat-e-integracao-no-board
    provides: public chat UI integration expecting safe interpretation/results behavior
provides:
  - CHAT_SEARCH_ENABLED operational kill-switch with env/config wiring
  - Public GET /api/v1/public/chat-search/status availability signal
  - Controlled chat_disabled 200 response with pt-BR guidance, empty JobPublic results, and no LLM/DB work
  - Structured no-PII chat_search logging (outcome/reason/latency/counts) per request
  - Automated coverage for disabled/status/logging behavior and DB-independent intent pure suites
affects: [22-02, 22-03, frontend-chat-toggle]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Feature-flag short-circuit at public endpoint boundary before intent/DB work"
    - "Per-request structured logging via try/finally with safe aggregate fields only"

key-files:
  created:
    - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-01-SUMMARY.md
  modified:
    - backend/app/core/config.py
    - backend/.env.example
    - backend/app/api/v1/public.py
    - backend/tests/test_chat_search_api.py
    - backend/tests/conftest.py

key-decisions:
  - "Enforced CHAT_SEARCH_ENABLED at the chat-search boundary so disabled mode never triggers intent extraction or published-job queries."
  - "Logged only operational aggregates (outcome/reason/latency_ms/results_count/total/page/limit) for chat_search events, explicitly excluding message/contact data."
  - "Kept /api/v1/public/jobs and manual board flows independent by exposing a read-only status signal instead of coupling routes."

patterns-established:
  - "Disabled chat returns a degraded IntentContract (chat_disabled) with ignored fields and null applied params for safe UI guidance."
  - "Pure intent unit modules are whitelisted for DB-independent pytest collection."

requirements-completed: [QA-02, QA-03]

# Metrics
duration: 25min
completed: 2026-11-18
---

# Phase 22 Plan 01: Chat Search Operational Controls Summary

**Chat-search kill-switch with public status signaling and no-PII structured request logging, backed by automated disabled-path and harness coverage.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-11-18T08:00:00-03:00
- **Completed:** 2026-11-18T08:20:32-03:00
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Added `CHAT_SEARCH_ENABLED` in settings/.env and a public `GET /api/v1/public/chat-search/status` endpoint so operators/frontend can detect chat availability without exposing secrets.
- Implemented a safe `chat_disabled` short-circuit in `POST /api/v1/public/chat-search` that returns controlled pt-BR guidance, empty `JobPublic` results, and performs no intent extraction or DB listing.
- Instrumented one structured `chat_search` log event per request with outcome/reason/latency/counts only, and expanded automated coverage for disabled/status/logging plus DB-independent intent pure suites.

## Task Commits

Each task was committed atomically:

1. **Task 1: Adicionar kill-switch/config e sinal de status com resposta segura controlada** - `d4537b4` (feat)
2. **Task 2: Instrumentar logging estruturado do chat-search sem PII e sem regressão de respostas** - `13c09d4` (feat)
3. **Task 3: Tornar suites de intent puras executáveis sem DB e consolidar harness de QA-02** - `64fcb99` (test)

**Plan metadata:** (this commit)

## Files Created/Modified
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-01-SUMMARY.md` - Execution summary and traceability for plan 22-01
- `backend/app/core/config.py` - Added `CHAT_SEARCH_ENABLED` operational toggle
- `backend/.env.example` - Documented `CHAT_SEARCH_ENABLED` kill-switch env
- `backend/app/api/v1/public.py` - Added status endpoint, `chat_disabled` safe degraded handling, short-circuit enforcement, and structured no-PII request logging
- `backend/tests/test_chat_search_api.py` - Added coverage for disabled/status behavior and caplog assertions for safe logging
- `backend/tests/conftest.py` - Whitelisted pure intent test modules for DB-independent collection

## Decisions Made
- Returned disabled chat responses as `200` degraded contracts (not 4xx/5xx) with explicit pt-BR guidance to preserve safe UX and keep manual board flows usable.
- Emitted exactly one `logger.info("chat_search", extra={...})` event in `finally` to ensure operational visibility even on error/disabled/degraded paths without leaking request content.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ensured disabled field statuses use enum values**
- **Found during:** Task 1 (kill-switch disabled response implementation)
- **Issue:** Assigning `"ignorado"` strings to intent field statuses produced Pydantic serialization warnings in tests; enum instances are the correct type.
- **Fix:** Set `FieldStatus.IGNORADO` (enum) for affected statuses in the degraded/disabled contract path.
- **Files modified:** `backend/app/api/v1/public.py`
- **Verification:** `cd backend; python -m pytest -q tests/test_chat_search_api.py -k "chat_search_disabled_returns_controlled_guidance_without_contacts or chat_search_disabled_short_circuits_intent_and_db or chat_search_status_endpoint_reflects_toggle or public_jobs_remain_independent_when_chat_disabled"` passed without serializer warnings.
- **Committed in:** `d4537b4` (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Correctness/typing fix only; no scope creep and no change to required behavior or security guarantees.

## Issues Encountered
- Plan verification selector `-k "disabled or status"` also matched a newly added logging test name (`*_disabled_emits_*`) before Task 2 logging was implemented; Task 1 behavior was verified with the four explicit disabled/status/non-regression tests plus `tests/test_ratelimit.py`.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend now exposes a safe operational kill-switch and availability signal for chat, plus structured no-PII request telemetry hooks for QA/ops validation.
- Ready for Phase 22 follow-up plans (MVP examples matrix/validation consolidation and UI/manual hardening as scoped), with manual board/search paths preserved.

## Self-Check: PASSED
- FOUND: `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-01-SUMMARY.md`
- FOUND: `d4537b4`
- FOUND: `13c09d4`
- FOUND: `64fcb99`

---
*Phase: 22-qualidade-hardening-e-valida-o-operacional*
*Completed: 2026-11-18*
