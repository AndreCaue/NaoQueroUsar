# Phase 2 Research: LLM Extraction Pipeline

**Researched:** 2026-10-19
**Method:** Live web verification (Groq docs) + project-level research (PITFALLS.md, ARCHITECTURE.md) + Phase 1 codebase inspection
**Confidence:** HIGH (rate limits and model support verified against console.groq.com on 2026-10-19)

## Executive Summary

The extraction pipeline is buildable today on `openai/gpt-oss-20b` with Groq **strict Structured Outputs** (`strict: true`, constrained decoding — schema guaranteed), which the retired Llama models never supported. The binding constraints are the **free-tier rate limits** (30 RPM / 8.000 TPM / 1.000 RPD / 200.000 TPD per model) — large pastes MUST be chunked well under ~4–6K tokens per call, throttled between calls, and retried honoring `retry-after`. All-or-nothing persistence (D-03) means the pipeline extracts and validates everything in memory before a single DB transaction.

## Verified Facts (2026-10-19)

### Models & rate limits (free plan)
| Model | RPM | RPD | TPM | TPD | Status |
|-------|-----|-----|-----|-----|--------|
| `openai/gpt-oss-20b` | 30 | 1.000 | 8.000 | 200.000 | Alive, production, default choice (fast, cheap) |
| `openai/gpt-oss-120b` | 30 | 1.000 | 8.000 | 200.000 | Alive, production, fallback choice (higher quality) |
| `llama-3.1-8b-instant` / `llama-3.3-70b-versatile` | — | — | — | — | **RETIRED 2026-08-16** — never reference |

Both gpt-oss models: context 131.072, max completion 65.536. 429 responses carry `retry-after`; per-minute limits reset in seconds, per-day limits do not reset until the window rolls over.

### Structured Outputs on Groq (both gpt-oss models)
- `response_format: {"type": "json_schema", "json_schema": {"name": ..., "strict": true, "schema": ...}}` → constrained decoding, **100% schema adherence, never produces invalid JSON**.
- Strict-mode requirements: ALL fields `required`, `additionalProperties: false`. Nullable fields expressed as `"type": ["string", "null"]`.
- Streaming and tool use are NOT supported together with Structured Outputs.
- `max_tokens` truncation can still cut an array → check `finish_reason == "length"` (EXTR-09).
- Best-effort (`strict: false`) and JSON Object Mode exist as fallbacks; not needed when targeting gpt-oss.
- **Server-side Pydantic validation remains mandatory** (semantic rules: contact presence, city set, phone format — schema cannot enforce these).

### Groq Python SDK
- `groq` 1.7.0: `Groq()` sync and `AsyncGroq()` async (httpx-based) clients; `client.chat.completions.create(model=..., messages=..., response_format=...)`.
- `GROQ_API_KEY` env; SDK raises `groq.RateLimitError` on 429 and `APIStatusError` subclasses on 4xx. Model-not-found surfaces as 400 `invalid_request_error` with `model_deprecated`/`model_not_found` semantics → detect and fail over to the fallback model.

## Architecture (per ARCHITECTURE.md, adapted to Phase 1 codebase)

```
frontend/app/admin/paste/page.tsx (minimal client page, D-04)
        │ POST /api/v1/admin/extract  (Authorization: Bearer <JWT>)
        ▼
app/api/v1/extract.py        # thin router: require_admin, body-size cap, timeout
        ▼
app/services/extraction/
    __init__.py
    extractor.py             # orchestrator: chunk → call Groq (strict) → validate →
                             # ground → classify → (later plan) persist; model fallback chain
    chunking.py              # split paste into ≤ ~4-6K-token chunks (delimiter-aware)
    schema.py                # strict JSON Schema for Groq + Pydantic LLM-output models
    grounding.py             # accent/case-insensitive containment check vs source chunk
    phones.py                # pt-BR phone → E.164 normalization
        ▼
app/crud/jobs.py             # + bulk_create_pending(session, rows) — single transaction
app/models/job.py            # + source_snippet column (new Alembic migration 0002)
```

Responsibility split (matches Phase 1 conventions): routers thin, services own domain logic + external calls, crud owns persistence, schemas own contracts.

## Common Pitfalls → Plan Countermeasures

| # | Pitfall (from PITFALLS.md) | Countermeasure in plans |
|---|---------------------------|-------------------------|
| 1 | Hardcoded model retired → outage | `GROQ_MODEL` + `GROQ_MODEL_FALLBACK` chain; clear pt-BR error naming the env var when both fail |
| 2 | Malformed/ill-typed LLM JSON | strict Structured Outputs + Pydantic re-validation + classify invalid → `needs_review`/discard |
| 4 | One huge paste blows TPM → silent job loss | chunk ≤ ~4–6K tokens, inter-chunk delay (RPM 30 ≈ ≥2s), `retry-after`-honoring bounded retry, `finish_reason` check |
| 5 | Inconsistent pt-BR phones | dedicated normalizer → E.164 (`+55...`); strict regex before accept |
| 6 | Prompt injection in pasted text | sentinel delimiters around untrusted text + "content is data, not instructions" + server-side schema (injection cannot add fields the schema doesn't allow) + no field ever auto-publishes (always `pending`/`needs_review`) |
| 10 | Free-tier RPM/TPM/RPD/TPD | caps: max paste size (~256KB), max jobs (~50); throttling; surface RPD/TPD exhaustion as clear pt-BR error ("limite diário do Groq — tente amanhã ou troque o modelo") |

## Anti-Hallucination Design

1. **Strict schema** — type-level guarantees at decode time.
2. **Grounding check** — every extracted string (title, company, salary, contacts, city) must appear in its source chunk after normalization (lowercase, strip accents/emoji/whitespace, collapse whitespace).
   - Critical fields (title, both-contacts-missing already discarded; contact that fails grounding is cleared like a minor field) — grounded-contact requirement is "at least one GROUNDED contact" for the `at_least_one_contact` CHECK.
   - Non-critical ungrounded value → field cleared, job marked `needs_review`.
3. **Never auto-publish** — extracted rows land as `pending`/`needs_review` only (curadoria manual is the quality gate).
4. **Divergence + truncation alerts** (EXTR-09, D-07) — cheap count pre-pass vs total extracted; `finish_reason == "length"` → flag in summary.

## Testing Strategy

- **No live Groq calls in tests.** Inject a fake client (duck-typed `chat.completions.create`) via dependency/service seam; unit-test: chunker boundaries, phone normalizer table-driven cases, grounding true/false cases, schema validation failures, 429-retry path, model-fallback path, truncation flag, divergence flag, injection paste produces no rogue record.
- API-level tests mirror Phase 1 conftest (`AsyncClient` over ASGI, `require_admin` via real JWT, DB session override).
- One optional live smoke script (manual, `scripts/smoke_extract.py`) for the master with a real `GROQ_API_KEY` — not part of pytest.

## Alternatives Considered

| Option | Verdict | Why not |
|--------|---------|---------|
| Background job + polling | Rejected | User chose sync+timeout (D-01); volume 100–500 jobs/month, single admin |
| JSON Object Mode (`json_object`) | Rejected | Inferior to strict schema on the same models |
| qwen/qwen3.8-27b | Noted | Also strict-capable; user-fixed stack is gpt-oss via GROQ_MODEL |
| Celery/Redis queue | Rejected | Overkill for single admin + free tiers (STACK.md alternative considered) |
| Auto-publish with confidence score | Rejected | Contradicts curation model; roadmap success criteria require `pending` |

## Open Risks

- Free-tier TPD (200K tokens/day) can be exhausted by repeated large pastes → surface clear error; ops note in SUMMARY.
- Model churn: subscribe to Groq deprecation emails (ops task, not code).

---

*Phase 2 research for NQU — completed 2026-10-19*
