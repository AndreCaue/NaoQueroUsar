---
phase: 02-llm-extraction-pipeline
plan: 02
subsystem: extraction
tags: [groq, llm-extraction, structured-outputs, rate-limiting, grounding, pytest, async]

# Dependency graph
requires:
  - phase: 02-llm-extraction-pipeline
    provides: "plan 02-01 — strict JSON schema + Pydantic models (ExtractedJobRaw/ExtractionLLMOutput/JobCandidate), prompt delimiters, chunk_text/estimate_tokens, normalize_phone, is_grounded/normalize_for_grounding, GROQ_*/EXTRACT_* Settings"
provides:
  - "async Groq call seam (call_extraction) with strict json_schema payload, never-hardcoded model chain, dead-model tracking across chunks, retry-after-honoring bounded 429 retry, connection retry, one repair attempt, pt-BR ExtractionAPIError"
  - "extract_jobs orchestrator: chunking + inter-chunk pacing (single-chunk shortcut), best-effort count pre-pass (EXTR-09/D-07), grounding + D-05/D-06 classification, EXTRACT_MAX_JOBS cap → ExtractionResult"
  - "CandidateOutcome enum (save / save_needs_review / discard) — the persistence contract plan 03 consumes"
  - "FakeGroq + injected-sleep test harness: 45 tests, zero network/DB"
affects: [02-03-extract-api-admin-flow, 03-reveal-anti-spam, phase-03, phase-04, phase-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "single-chunk boundary in call_extraction; chunking/pacing/orchestration live in extractor.py"
    - "dead_models set shared across chunks so a model-not-found model is never retried (no retry storms, T-02-06)"
    - "count pre-pass skipped for single-chunk pastes (already a cheap call); best-effort, never blocks (EXTR-09)"
    - "city grounded as written OR mapped (raw 'SP' ~ canonical 'São Paulo') to avoid false needs_review (D-06)"
    - "extraction package remains pure: no fastapi/sqlalchemy/network imports (verified)"

key-files:
  created:
    - backend/app/services/extraction/client.py
    - backend/app/services/extraction/extractor.py
    - backend/tests/test_extractor.py
  modified: []

key-decisions:
  - "call_extraction handles ONE text unit; extract_jobs owns chunk_text + EXTRACT_CHUNK_DELAY pacing — this boundary is documented in both module docstrings so plan 03 wires per-chunk calls correctly"
  - "Single-chunk pastes set detected_count=None (the extraction IS the cheap call); the count pre-pass only fires for multi-chunk pastes, avoiding a redundant Groq call (EXTR-09/D-07)"
  - "City grounding passes when EITHER the raw value OR the mapped canonical is present, so 'SP' → 'São Paulo' stays a clean save while a truly absent city (Manaus) is flagged needs_review"
  - "EXTRACT_MAX_JOBS overflow collapses discarded rows into ONE 'excedeu o limite' entry (kept rows preserved first); this never discards kept rows"
  - "Injection defense is structural: rows come only from the scripted/parsed JSON response, extra='forbid' + additionalProperties:false reject injection-shaped fields"

patterns-established:
  - "injectable seams (client=..., sleep=...) make every failure mode (429, model churn, connection, truncation, divergence, hallucination) testable with zero network"
  - "extraction orchestrator returns classified candidates and NEVER touches the DB — D-03 atomicity belongs to the caller (plan 03)"

requirements-completed: [EXTR-02, EXTR-03, EXTR-04, EXTR-09]

# Metrics
duration: 18min
completed: 2026-10-19
---

# Phase 02 Plan 02: Groq Client Seam and Extraction Orchestrator Summary

**Async Groq extraction pipeline with never-hardcoded model fallback, retry-after-honoring 429 backoff, best-effort divergence pre-pass, and grounding-driven D-05/D-06 classification — 45 FakeGroq tests, zero live API calls.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-10-19T20:16:27Z
- **Completed:** 2026-10-19T20:34:53Z
- **Tasks:** 2/2
- **Files modified:** 3 (all created)

## Accomplishments
- `call_extraction` sends strict Structured-Outputs payloads (`json_schema` + `strict: true` + `EXTRACTION_JSON_SCHEMA`), wraps untrusted text in EXTR-08 delimiters flagged as raw data, and validates responses with Pydantic plus a single repair attempt
- Model chain `[GROQ_MODEL, GROQ_MODEL_FALLBACK]` (deduplicated, never hardcoded); a model that fails with model-not-found/deprecated is marked dead for the whole extraction, and chain exhaustion raises a pt-BR `ExtractionAPIError` naming `GROQ_MODEL`
- 429s retried at most 3× honoring `retry-after` capped at 30s (default backoff 2/4/8s); connection errors retried once; rate-limit exhaustion surfaces "limite de taxa"
- `extract_jobs` chunks under `EXTRACT_CHUNK_MAX_TOKENS`, sleeps `EXTRACT_CHUNK_DELAY_SECONDS` only *between* chunks, runs a best-effort count pre-pass for multi-chunk pastes (D-07 divergence), grounds every field, and classifies into `save` / `save_needs_review` / `discard`
- D-05 enforced exactly: only a missing/ungrounded title or the absence of both contacts discard; minor ungrounded fields are cleared and flagged needs_review; D-06 `CITY_MAP` maps obvious variants and preserves raw city text otherwise
- 45 tests in `test_extractor.py` (17 client + 28 orchestrator) plus the 31 core tests all green; full suite 94 passed against Neon

## task Commits

Each task was committed atomically:

1. **task 1: Groq async client seam with fallback chain + 429 retry** - `4f74ab1` (feat)
2. **task 2: extraction orchestrator — chunking, throttling, grounding, classification** - `b5ad05b` (feat)

**Plan metadata:** `b5ad05b` is the last code commit; the docs SUMMARY commit follows via the orchestrator.

_Note: neither task was `tdd="true"`; this plan is `type: execute`, so no RED/GREEN gate applies._

## Files Created/Modified
- `backend/app/services/extraction/client.py` — `ExtractionAPIError`, `RawExtraction`, `call_extraction`, strict payload builder, model chain, 429/connection/model-missing mapping, repair path
- `backend/app/services/extraction/extractor.py` — `CandidateOutcome`, `ExtractionResult`, `extract_jobs`, `estimate_job_count`, `CITY_MAP`/`normalize_city`, per-row grounding + classification
- `backend/tests/test_extractor.py` — `FakeGroq`, `SleepRecorder`, `make_settings`, error factories + 45 tests (client + orchestrator)

## Decisions Made
- `call_extraction` owns exactly one text unit and the fallback/retry logic; `extract_jobs` owns chunking, pacing, counting, grounding and classification (boundary documented in both docstrings)
- Single-chunk pastes set `detected_count=None` because the extraction request is already the cheap call — the count pre-pass fires only for multi-chunk pastes (saves one Groq call)
- City grounding succeeds on the raw value OR the mapped canonical, so "SP" → "São Paulo" is a clean `save` while a city absent from the source is `needs_review`
- EXTRACT_MAX_JOBS overflow records a single "excedeu o limite" discarded entry rather than dropping rows silently

## Deviations from Plan

None - plan executed exactly as written. (The acceptance criteria's parenthetical about a possible `estimate_job_count` helper was implemented as the multi-chunk count pre-pass, exactly as described in the action step.)

## Issues Encountered
- Initial orchestrator tests over-specified LLM rows (reusing `clean_row`, whose `company`/`activities`/`salary` were not present in the short test paste), which correctly pushed them to `save_needs_review`. Fixed the test fixtures to script rows whose fields actually appear in the paste — the implementation behavior was correct throughout (grounding worked as intended).

## User Setup Required
`GROQ_API_KEY` is required for *real* extraction at runtime (plan 03/04 integration), but this plan's tests use an injected fake client and need no key. Set it in `backend/.env` from https://console.groq.com/keys (free). See the plan's `user_setup` block.

## Known Stubs
None. The module intentionally does not persist anything (D-03 — persistence/HTTP belong to plan 03), and the count pre-pass returning `None` on failure is a documented, tested best-effort path — not a placeholder.

## Threat Flags
None — no new security-relevant surface beyond the plan's threat register. T-02-04 (prompt injection: delimiters + strict schema + data-only framing), T-02-05 (hallucination: grounding + clear/discard), T-02-06 (DoS/cost: byte cap, job cap, dead-model switch, bounded retries) and T-02-07 (rate limits: pacing + pt-BR 429 surfacing) are all mitigated as planned.

## Next Phase Readiness
- Plan 03 (extract API + admin flow) can consume `extract_jobs(text, settings)` → `ExtractionResult`, mapping `CandidateOutcome.save → JobStatus.pending`, `save_needs_review → needs_review`, persisting `result.kept` in one transaction (D-03) and building the summary from `discarded` / `divergent` / `truncated` / `model_used`
- `GROQ_API_KEY` must be configured before live integration testing (env documented)
- No blockers

---
*Phase: 02-llm-extraction-pipeline*
*Completed: 2026-10-19*

## Self-Check: PASSED

- Files exist: backend/app/services/extraction/client.py, backend/app/services/extraction/extractor.py, backend/tests/test_extractor.py
- Commits found: 4f74ab1, b5ad05b
- Verification re-run: tests/test_extractor.py 45 passed; tests/test_extractor.py + tests/test_extraction_core.py 76 passed; full suite 94 passed; grep gates OK (call_extraction ×2, no requests/Groq(/db imports in services)
