---
phase: 20-api-publica-de-chat-search-resiliente
plan: 02
subsystem: testing
tags: [pytest, fastapi, chat-search, intent, ratelimit, fallback]
requires:
  - phase: 20-api-publica-de-chat-search-resiliente
    provides: Public chat-search endpoint, schemas, and intent timeout/degraded handling (20-01)
provides:
  - Deterministic automated coverage for POST /api/v1/public/chat-search contract, protections, fallback, and partial-support signaling
affects: [20-api-publica-de-chat-search-resiliente, frontend-public-chat]
tech-stack:
  added: []
  patterns: [mocked intent seam for HTTP contract tests, deterministic equivalence checks against public jobs search]
key-files:
  created:
    - backend/tests/test_chat_search_api.py
  modified: []
key-decisions:
  - "Mocked `app.api.v1.public.extract_and_map_intent` to validate chat-search behavior deterministically without Groq/network dependencies."
  - "Asserted degraded and partial-support contracts via response envelope/meta/limitations fields rather than coupling tests to internal implementation details."
patterns-established:
  - "Chat-search tests compare effective `applied_params` results against `GET /api/v1/public/jobs` and enforce contact-free/public-safe payloads."
requirements-completed: [API-01, API-02, API-03]
duration: 15 min
completed: 2026-11-17
---

# Phase 20 Plan 02: Cobertura automatizada do chat-search Summary

**Deterministic pytest coverage for the public chat-search API validating interpretation/results equivalence, pt-BR protections, resilient degraded fallback, and explicit partial-support signaling with mocked intent extraction.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-11-17T23:12:00Z
- **Completed:** 2026-11-17T23:27:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Added `backend/tests/test_chat_search_api.py` covering contract equivalence between `POST /api/v1/public/chat-search` and deterministic public jobs search for effective `applied_params`, including pagination/total consistency and contact-free `results.items`.
- Added protection and resilience coverage for invalid/oversized messages, endpoint rate limiting (`429` with pt-BR detail and `Retry-After`), and safe 200 degraded responses on intent failure/timeout/no-extractable-params with empty results and pt-BR guidance metadata.
- Added partial-support assertions ensuring non-native/approximated fields and non-whitelist cities remain explicitly signaled/limited without unsafe inference or guaranteed structured filtering claims.

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar suíte de contrato e equivalência do chat-search (API-01)** - `3d7c13b` (test)
2. **Task 2: Cobrir proteções, fallback degradado e suporte parcial (API-02, API-03)** - `a0aaaee` (test)

## Files Created/Modified
- `backend/tests/test_chat_search_api.py` - End-to-end API contract tests for chat-search success, equivalence, privacy, validation/rate limiting, degraded fallback, and partial-support signaling.

## Decisions Made
- Used monkeypatched intent extraction responses/exceptions to exercise success, timeout/unavailable, empty-intent, and approximation scenarios without external services.
- Kept assertions aligned with server-authoritative contract fields (`interpretation`, `results`, `applied_params`, `meta.degraded/degradation_reason/guidance`, limitations/statuses) and public contact-safety guarantees.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Threat Flags

None - tests validate planned mitigations (rate limit/validation, contact-free responses, safe degraded handling) without introducing new trust-boundary surface.

## Next Phase Readiness
- Phase 20 chat-search behavior is covered by deterministic automated tests for contract, resilience, and limitation signaling, supporting frontend/public consumer integration.
- Existing public search and intent parser suites remained green in sanity checks.

## Self-Check: PASSED

- FOUND: .planning/phases/20-api-publica-de-chat-search-resiliente/20-02-SUMMARY.md
- FOUND: backend/tests/test_chat_search_api.py
- FOUND: 3d7c13b
- FOUND: a0aaaee

---
*Phase: 20-api-publica-de-chat-search-resiliente*
*Completed: 2026-11-17*
