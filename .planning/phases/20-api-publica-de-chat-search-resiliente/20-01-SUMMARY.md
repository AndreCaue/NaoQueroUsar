---
phase: 20-api-publica-de-chat-search-resiliente
plan: 01
subsystem: api
tags: [fastapi, pydantic, groq, ratelimit, search, intent]
requires:
  - phase: 19-contrato-de-intencao-e-mapeamento-seguro
    provides: Intent extraction/mapping seam and deterministic IntentContract
provides:
  - Public POST /api/v1/public/chat-search with interpretation+results envelope
  - Dedicated chat-search config, request/response schemas, and intent timeout seam
  - Resilient LLM fallback to safe degraded 200 responses without automatic results
affects: [20-api-publica-de-chat-search-resiliente, frontend-public-chat]
tech-stack:
  added: []
  patterns: [server-authoritative intent application, endpoint-scoped rate limiting, short-budget intent extraction with degraded fallback]
key-files:
  created:
    - backend/app/schemas/chat.py
  modified:
    - backend/app/core/config.py
    - backend/app/core/ratelimit.py
    - backend/app/services/intent/client.py
    - backend/app/services/intent/parser.py
    - backend/app/api/v1/public.py
    - backend/.env.example
key-decisions:
  - "Reused existing intent seam and JobPublic/list_published contracts so chat-search stays server-authoritative and contact-safe."
  - "Dedicated chat timeout/rate/message knobs keep public NL search cost/abuse bounded while preserving existing admin extraction behavior."
patterns-established:
  - "Chat intent failures degrade to 200 with explicit degraded/guidance metadata instead of leaking errors or running automatic broad searches."
requirements-completed: [API-01, API-02, API-03]
duration: 12 min
completed: 2026-11-17
---

# Phase 20 Plan 01: API pública de chat-search resiliente Summary

**Public chat-search endpoint that maps pt-BR messages to a safe intent contract, runs deterministic `list_published` search, and degrades transparently when intent extraction is unavailable.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-11-17T22:58:00Z
- **Completed:** 2026-11-17T23:10:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Added dedicated chat-search settings, rate-limit helper, request/response schemas, and env documentation for the public NL search flow.
- Extended the intent client/parser seam with an optional timeout budget so chat extraction can fail fast without changing existing admin/default Groq behavior.
- Implemented `POST /api/v1/public/chat-search` with IP+endpoint rate limiting, safe pt-BR validation/error handling, deterministic `JobPublic` results, and controlled 200 degraded responses with guidance metadata.

## Task Commits

Each task was committed atomically:

1. **Task 1: Adicionar knobs/config, timeout de intent dedicado e schemas do chat-search** - `c190bf0` (feat)
2. **Task 2: Implementar endpoint POST /api/v1/public/chat-search com orquestração, fallback e erros pt-BR seguros** - `481c28c` (feat)

## Files Created/Modified
- `backend/app/schemas/chat.py` - Chat-search request/results/response envelope with `IntentContract` interpretation and contact-free `JobPublic` results.
- `backend/app/core/config.py` - Dedicated chat-search rate limit, max message size, and short intent timeout settings.
- `backend/app/core/ratelimit.py` - `chat_search_limit()` helper reusing the endpoint-scoped limiter.
- `backend/app/services/intent/client.py` - Optional per-call intent timeout propagated to Groq client/create calls.
- `backend/app/services/intent/parser.py` - Optional timeout propagation through intent parsing/extraction.
- `backend/app/api/v1/public.py` - Public chat-search endpoint, degraded contract builder, approximation guidance, deterministic search orchestration, and safe logging/errors.
- `backend/.env.example` - Documented chat-search knobs.

## Decisions Made
- Reused the Phase 19 intent package and existing public search/listing contracts instead of introducing parallel parsing or search logic.
- Represented unavailable/timeout/no-params cases as safe degraded 200 interpretations with empty `results` (`items=[]`, `total=0`) and explicit `meta.degraded`, `degradation_reason`, and `guidance`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Threat Flags

None - no new trust-boundary surface beyond the planned public endpoint; rate limiting, server-authoritative applied params, contact-free `JobPublic` responses, and safe degraded handling were implemented per plan.

## Next Phase Readiness
- Backend chat-search contract is in place for frontend/public consumer work and for follow-up Phase 20 plan coverage.
- Existing intent tests remain green; broader DB-backed/public endpoint integration tests were not run in this execution.

## Self-Check: PASSED

- FOUND: backend/app/schemas/chat.py
- FOUND: backend/app/api/v1/public.py
- FOUND: c190bf0
- FOUND: 481c28c

---
*Phase: 20-api-publica-de-chat-search-resiliente*
*Completed: 2026-11-17*
