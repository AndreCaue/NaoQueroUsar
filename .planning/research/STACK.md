# Stack Research

**Domain:** NL chat search (intent extraction → structured params → existing public job search) for EmpregaNoix v1.3
**Researched:** 2026-11-17
**Confidence:** HIGH (core recommendation) / MEDIUM (alternative providers, evolving free tiers)

## Scope & Baseline (Do Not Re-research Broadly)

**Existing, validated stack (reuse):** Next.js 16 App Router + Tailwind 4 + React 19 (frontend), FastAPI + Pydantic v2 + SQLAlchemy 2 async + asyncpg/Neon (backend), Groq Python SDK for LLM extraction, slowapi rate limiting, Turnstile patterns, APScheduler/cron patterns, pytest/Vitest/Playwright.

**Existing integration points (confirmed in code):**
- `backend/app/services/extraction/client.py` — Groq strict Structured Outputs (`response_format` json_schema, `strict: true`), model chain + fallback, 429/retry, timeout, untrusted-text delimiter wrapping/sanitization, Pydantic validation, pt-BR error surfacing.
- `backend/app/services/extraction/schema.py` — strict JSON schema + Pydantic models pattern for LLM outputs.
- `backend/app/core/config.py` — `GROQ_API_KEY`, `GROQ_MODEL`/`GROQ_MODEL_FALLBACK` (`openai/gpt-oss-20b`/`120b`), `GROQ_TIMEOUT_SECONDS`, env-tunable rate limits (`REVEAL_RATE_LIMIT`, `LOGIN_RATE_LIMIT`), CORS/Turnstile controls.
- `backend/app/api/v1/public.py` — anonymous public routes, `@limiter.limit(...)`, `JobPublic` contact-free responses, `list_public_jobs` params `q` (max 80), `city` (whitelist resolve/ignore unknown), `sort` (`recentes|antigas` fallback), `page/limit`.
- `backend/app/crud/jobs.py` — `list_published(..., q, city, sort)` over normalized `search_text` (title/company/activities/requirements, trigram/unaccent), AND semantics, DB-clock expiry filter.
- `frontend/components/board/BoardToolbar.tsx` — URL-driven client controls, 300ms debounce, immediate commit on Enter/clear/chip/sort, `router.replace(..., {scroll:false})`.

**Today:** no chatbot endpoint/UI, no embeddings/vector store.

## Recommended Stack

### Core Technologies (New capability: NL intent → structured search params)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Groq (reuse existing provider/models) | API, models via env (`GROQ_MODEL` default `openai/gpt-oss-20b`, fallback `openai/gpt-oss-120b`) | Extract user intent from pt-BR NL into validated JSON search params | **Best fit for this milestone:** already integrated, configured, and battle-tested in repo; zero new vendor/keys/billing; free tier aligns with "baixo custo"; low-latency inference fits chat UX; strict Structured Outputs supported (see `client.py`). Reuse infra (timeouts, retries, fallback, prompt-injection delimiting) instead of adding a second LLM stack. | 
| Pydantic v2 (existing) | 2.14.x line (current project baseline) | Define/validate `ChatIntent` schema (LLM output) and request/response contracts | Single source of truth for validation, defaults, and normalization; same pattern as `ExtractedJobRaw`/`ExtractionLLMOutput`; prevents invented/unsafe params from reaching search. |
| FastAPI + slowapi (existing) | project baseline | Public `chat-search` endpoint with rate limiting, timeouts, bounded payloads | Reuse proven public-surface protections (`limiter`, pt-BR errors, no contacts in public payload) and async request handling. |
| Next.js 16 + React 19 + Tailwind 4 (existing) | project baseline | Mobile-first chat drawer/modal UI | No new UI framework needed; compose from existing primitives/patterns (client component, URL/search integration where appropriate, modal/drawer behavior) to keep bundle and complexity minimal. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `groq` (Python SDK, existing) | 1.7.0 installed in env (PyPI latest observed: 1.7.0; npm `groq` 6.24.0 is unrelated JS pkg) | Chat completions with `response_format={"type":"json_schema","json_schema":{..., "strict": true}}` | Always for chat intent extraction when using Groq. Keep `temperature=0`, strict schema, and Pydantic re-validation. |
| `httpx` (existing) | 0.28.x baseline | Timeouts/HTTP plumbing (already used across stack) | Reuse for any verification/calls; ensure overall chat request budget is enforced (see Protections). |
| `slowapi` / existing limiter wiring (existing) | project baseline | Per-IP throttling of public chat endpoint | Required. Public, anonymous, LLM-backed endpoint is abuse/cost-amplification surface. |
| `zod` (existing, frontend) | 4.x baseline | Runtime-validate chat API response shape in client (optional but cheap) | Use if parsing/guarding response in TS client; not mandatory if types are simple and trusted-internal. |
| **No new frontend chat library** | n/a | Chat transcript/input UI | Build minimal custom drawer + message list + input (Tailwind). Avoid heavyweight chat kits for this scope. |
| **No embeddings/vector DB libs** | n/a | Retrieval | Out of scope: "LLM não recebe centenas de vagas; apenas extrai parâmetros" and reuse existing `search_text`/filters. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pytest + pytest-asyncio + httpx ASGI/TestClient (existing) | Unit/integration tests for intent parser, normalization, endpoint protections, and search mapping | Mock Groq client (inject fake client / patch call seam) as in extraction tests; never require real `GROQ_API_KEY`. Add cases for pt-BR phrasing, unknown cities, prompt injection, timeouts, 429/rate-limit. |
| Vitest / Playwright (existing) | Frontend chat drawer behavior and E2E search flows | Test mobile-first open/close, submit, "parâmetros entendidos" display, result rendering, empty/error states. |

## Installation

```bash
# Backend (NEW deps): none required for recommended path
# Reuse: fastapi, pydantic, groq, httpx, slowapi/limiter, sqlalchemy stack

# Frontend (NEW deps): none required for recommended path
# Reuse: next, react, react-dom, tailwindcss (and existing utils)

# Optional ONLY if an alternative provider is explicitly chosen later:
# pip install google-genai        # Gemini API (alternative)
# pip install ollama              # local Ollama client (dev/offline alternative)
# pip install openai              # if preferring OpenAI-compatible client for OpenRouter (httpx also works)
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **Groq reuse** (`openai/gpt-oss-20b`/`120b`, strict JSON schema) | **Google Gemini Flash via `google-genai`** (e.g. Flash-family models with `response_mime_type='application/json'` + `response_schema`/Pydantic) | If Groq free-tier limits/availability block MVP or quality is insufficient for pt-BR intent parsing. Tradeoff: adds dependency (`google-genai`), new API key/billing/quota management, and a second provider integration path. **Confidence: MEDIUM** (API pattern verified via docs; exact "free tier" quotas/models change). |
| **Groq reuse** | **OpenRouter (OpenAI-compatible)** with a free/low-cost model | If you need model variety/fallback marketplace. Tradeoff: extra account/key, variable model support for strict structured outputs, latency/availability depends on routed provider; can often be called with existing `httpx` but schema enforcement must be verified per model. **Confidence: MEDIUM**. |
| **Groq reuse** | **Ollama (local) + `ollama` Python client** (`format=model_json_schema()`) | Local/dev or offline experimentation; useful where no external API desired. **Not recommended for hosted MVP**: requires hosting the model/runtime (RAM/CPU/GPU), higher latency/ops cost on Railway/Render/Vercel-adjacent infra, and conflicts with "baixo custo operacional" for public traffic. **Confidence: HIGH** for local viability, **LOW/MEDIUM** for hosted free-tier fit. |
| **Rule-based heuristics only** (regex/keyword parsing, no LLM) | — | Only as deterministic fallback for trivial cases; NL salary/modality/contract phrasing in pt-BR is too variable for primary path. Can complement LLM (post-normalization), not replace it. |
| **Custom chat UI (Tailwind + React)** | Prebuilt chat UI libs (e.g. `react-chatbot-kit`, chat widget packages) | Only if you need rich chat features fast and accept bundle/style/lock-in cost. For MVP (single-turn or short guided search, params + results list), custom is simpler and matches existing dark minimal design. |
| **Query-param translation (LLM → call existing `GET /public/jobs`)** | Dedicated DB columns/FTS for salary/modality/contract now | Prefer incremental: map extractable hints to `q`/`city`/`sort` and apply **in-memory post-filter/ranking** over the returned page/candidate set for non-native fields when feasible; only extend schema/indexes if product needs demand it (keeps milestone small, avoids migration risk). |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Adding a **second LLM provider** by default (Gemini/OpenRouter/Ollama) | Duplicates config, secrets, failure modes, and cost/latency tuning when Groq is already integrated and sufficient for parameter extraction. | **Reuse Groq** via existing `services/extraction/client.py` patterns; abstract only if/when a second provider is truly needed. |
| **Embeddings/vector search / pgvector / external vector DB** | Overkill for 100–500 jobs/month and explicit constraint ("LLM não recebe centenas de vagas; apenas extrai parâmetros"). Adds infra, indexing, and cost. | LLM intent extraction + existing `search_text` trigram/unaccent + whitelist filters + lightweight post-filtering. |
| **Sending job listings/content blobs to the LLM** | Privacy/cost/latency/token risk; unnecessary when DB/search already exists. | Send only the user's NL query (sanitized/delimited) and return structured params + DB results. |
| **Unvalidated LLM output applied directly to DB/query** | Prompt injection/hallucination can produce invalid cities, extreme limits, or unsupported filters. | Strict JSON schema + Pydantic validation + whitelist normalization (`resolve_city`/`resolve_sort` semantics), caps on `q` length, page/limit bounds. |
| **Public chat endpoint without throttle/timeout/budget** | Anonymous LLM endpoint is trivially abusable (cost, rate exhaustion, hanging requests). | `@limiter.limit(...)` (env-tunable, e.g. new `CHAT_SEARCH_RATE_LIMIT`), strict request body size/max chars, `asyncio.timeout`/client timeout aligned with `GROQ_TIMEOUT_SECONDS`, bounded retries. |
| **Exposing contacts in chat-search response** | Breaks existing privacy/scraping posture (contacts revealed only via gated reveal flow). | Return `JobPublic`-shaped items (no contact fields) and reuse existing reveal flow for contact. |
| **Frontend global chat state library / heavy widget SDK** | Unneeded complexity for MVP drawer; harder to keep mobile-first and on-brand. | Local component state (or small hook) + existing design tokens/Tailwind. |

## Stack Patterns by Variant

**If intent maps cleanly to existing filters (city whitelist, keywords, sort):**
- LLM outputs `{ q?, city?, sort?, page?, limit?, interpreted: {...} }` (constrained).
- Normalize with existing helpers/semantics: `resolve_city` behavior (unknown → ignored/no 400), `resolve_sort` fallback, trim/cap `q` (<=80 like public API), clamp pagination.
- Call `crud.list_published` (or internal service) and return `{ interpretation, params_applied, results: JobPublic[], total }`.

**If user asks for non-native fields (salário/modalidade/contrato/senioridade) and schema is unchanged:**
- Extract hints in intent schema (e.g. `salary_min`, `modality`, `contract_type`, `seniority`, `keywords`).
- Translate to safe `q` expansions/keywords where helpful **and/or** post-filter/rank a bounded candidate set in Python (never scan unbounded rows).
- **Be explicit in response:** mark unsupported/partially-supported params in `interpretation` so UI can show "entendi X; filtro Y aplicado parcialmente/não disponível".
- Because: incremental delivery without DB migration; honest UX per milestone caveat.

**If Groq returns 429/model-unavailable/timeout:**
- Reuse existing retry/fallback/dead-model handling pattern from `extraction/client.py` (adapted to chat intent call).
- Return a fast, user-safe pt-BR fallback: suggest using manual search/filters (`BoardToolbar`) rather than hanging; never leak internals/keys.

**If abuse risk is observed in production:**
- Tighten `CHAT_SEARCH_RATE_LIMIT`, lower max input length, add cheap heuristics cache for identical normalized queries (in-memory, short TTL) before adding providers/infra.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `groq==1.7.0` (Python, installed) | `openai/gpt-oss-20b` / `openai/gpt-oss-120b` (configured) + `httpx 0.28.x` | Existing code already uses strict `json_schema` response_format; keep schema `additionalProperties:false` and required fields aligned with strict decoding. |
| FastAPI + Pydantic v2 (project baseline) | `groq` 1.7.0, slowapi limiter | Define intent models as Pydantic v2; reuse dependency injection patterns from `public.py`/`deps.py`. |
| Next.js 16.4.x + React 19.3.x + Tailwind 4.3.x | Existing component patterns (`"use client"`, `useTransition`, `router.replace`) | Chat drawer should be a client component; keep server/client boundary clear (no secrets in client). |
| `google-genai` (optional alternative) | Python 3.x (project), Gemini API | Only if adopted: verify pinned version at implementation time; different SDK/response shape than Groq—**do not mix** without an adapter. (Confidence: MEDIUM) |
| `ollama` Python client (optional alternative) | Local Ollama runtime | Only for local/dev; structured output via `format=<model_json_schema()>` differs from Groq's `response_format`. (Confidence: MEDIUM) |

## Integration Blueprint (What to Build, Minimal)

1. **Backend schema/service:** `app/services/chat_search/` (or similar) with `ChatIntent` Pydantic/JSON schema, `extract_intent(query, settings, client?)` reusing Groq call hardening patterns (delimiter-wrap user text, strict schema, timeout/retries/fallback), and deterministic `normalize_intent()` mapping to existing search params.
2. **Backend endpoint:** `POST /api/v1/public/jobs/chat-search` (name flexible) in `public.py` or a dedicated router: `@limiter.limit(chat_limit)`, input cap, LLM timeout budget, return interpretation + `JobListResponse`/`JobPublic` results; **no contact fields**.
3. **Config:** add env-tunable knobs in `config.py` only as needed (e.g. `CHAT_SEARCH_RATE_LIMIT`, `CHAT_MAX_QUERY_CHARS`, `CHAT_TIMEOUT_SECONDS`) with safe defaults; **do not hardcode models** (keep `GROQ_MODEL` chain).
4. **Frontend:** client component (e.g. `ChatSearchDrawer`) launched from board UI; calls backend, shows "entendi" params chips/summary, renders job cards/list reusing existing presentation where possible; mobile-first, accessible (focus trap/ESC), no history pollution required.
5. **Non-native fields:** start with text-mapping/post-filter strategy and explicit "parcial/não suportado" signaling; add DB/filter extensions only if required by accepted examples.

## Sources

- **Codebase (HIGH):** `backend/app/services/extraction/client.py`, `backend/app/services/extraction/schema.py`, `backend/app/core/config.py`, `backend/app/api/v1/public.py`, `backend/app/crud/jobs.py`, `frontend/components/board/BoardToolbar.tsx`, `.planning/PROJECT.md`
- **Context7 / library docs (HIGH for API patterns):** `/groq/groq-python` — `response_format` strict JSON schema / Structured Outputs for chat completions; `/websites/deepwiki_googleapis_python-genai` — Gemini structured output via `response_mime_type='application/json'` + `response_schema` (Pydantic) and `response.parsed`; `/ollama/ollama-python` — `chat(..., format=Model.model_json_schema(), options={"temperature":0})` structured outputs
- **Registry checks (HIGH for installed/latest observed):** `pip index versions groq` → installed/latest `1.7.0`; `npm view groq version` → `6.24.0` (JS package, not the Python SDK)
- **Project constraints (HIGH):** `.planning/PROJECT.md` v1.3 goal/constraints (public no-login, low cost, LLM only extracts params, reuse existing search)

---
*Stack research for: EmpregaNoix v1.3 Chatbot Inteligente de Busca de Vagas (NL chat search)*
*Researched: 2026-11-17*
