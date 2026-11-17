---
phase: 20-api-publica-de-chat-search-resiliente
fixed_at: 2026-11-17T23:19:15Z
review_path: .planning/phases/20-api-publica-de-chat-search-resiliente/20-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 20: Code Review Fix Report

**Fixed at:** 2026-11-17T23:19:15Z
**Source review:** .planning/phases/20-api-publica-de-chat-search-resiliente/20-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### WR-01: Timeout failures can be misclassified as generic LLM unavailability

**Files modified:** `backend/app/api/v1/public.py`
**Commit:** 23cf282
**Applied fix:** Added `asyncio` import and classified intent extraction failures as timeout when the exception is `asyncio.TimeoutError`/`TimeoutError` or contains "timeout" case-insensitively; preserved controlled degraded response with correct `timeout` reason and guidance.

### WR-02: Schema-validation failure after repair aborts fallback to secondary model

**Files modified:** `backend/app/services/intent/client.py`
**Commit:** bdce472
**Applied fix:** When schema validation still fails after a repair attempt for a model, record the failure and continue to the next model in the chain (instead of failing fast), and treat `IntentExtractionError` as a per-model failure to allow fallback; raise aggregated failure only after all models are exhausted.

### WR-03: Degraded contract builder can append duplicate limitation codes

**Files modified:** `backend/app/api/v1/public.py`
**Commit:** 4959581
**Applied fix:** Reworked degraded contract limitation assembly to collect limitations and de-duplicate while preserving order, and removed redundant caller-provided limitation for timeout/unavailable degradation paths to avoid duplicate `llm_timeout`/`llm_unavailable` entries.

---

_Fixed: 2026-11-17T23:19:15Z_
_Fixer: OpenCode (gsd-code-fixer)_
_Iteration: 1_
