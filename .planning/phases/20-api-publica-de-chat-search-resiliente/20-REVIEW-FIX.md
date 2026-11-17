---
phase: 20-api-publica-de-chat-search-resiliente
fixed_at: 2026-11-17T00:00:00Z
review_path: C:\Users\AndreC\Desktop\Teste\NaoQueroUsar\.planning\phases\20-api-publica-de-chat-search-resiliente\20-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 20: Code Review Fix Report

**Fixed at:** 2026-11-17T00:00:00Z
**Source review:** C:\Users\AndreC\Desktop\Teste\NaoQueroUsar\.planning\phases\20-api-publica-de-chat-search-resiliente\20-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 2
- Fixed: 2
- Skipped: 0

## Fixed Issues

### WR-01: Parser engole exceções de extração e impede classificação correta de degradação (LLM indisponível/timeout)

**Files modified:** `backend/app/services/intent/parser.py`
**Commit:** 69de9d3
**Applied fix:** `extract_and_map_intent` no longer catches `IntentExtractionError`/`ValidationError`/generic exceptions from intent parsing; extraction/provider failures now propagate so the API layer can classify timeout vs LLM unavailability and return the intended degraded response. Empty input and "no extractable params" after deterministic mapping still degrade safely. (fixed: requires human verification)

### WR-02: Limite máximo da mensagem é hardcoded no schema e ignora `CHAT_SEARCH_MAX_MESSAGE_CHARS`

**Files modified:** `backend/app/schemas/chat.py`
**Commit:** 90b6621
**Applied fix:** `ChatSearchRequest` now enforces the configured `CHAT_SEARCH_MAX_MESSAGE_CHARS` (via settings with safe fallback to 400) in the message validator instead of a hardcoded `max_length=400`, aligning runtime validation with documented/env-configurable behavior.

---

_Fixed: 2026-11-17T00:00:00Z_
_Fixer: OpenCode (gsd-code-fixer)_
_Iteration: 1_
