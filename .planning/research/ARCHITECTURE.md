# Architecture Research

**Domain:** NL chatbot search integration for an existing job board (EmpregaNoix v1.3)
**Researched:** 2026-11-17
**Confidence:** HIGH (grounded in current codebase) / MEDIUM (performance/rate-limit tuning specifics)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Next.js 16 App Router)                   │
│  ┌────────────────────────────── Public Board (existing) ──────────────────┐  │
│  │  (public)/page.tsx  [Server]  ← URL searchParams (q, city, sort, page) │  │
│  │     ├─ BoardToolbar (client)  ── updates URL / navigates               │  │
│  │     ├─ JobGrid / JobDetailDialog / RevealContact (client)              │  │
│  │     └─ ChatSearchLauncher + ChatDrawer/Modal (client)  [NEW]           │  │
│  └──────────────────────────────────────────────────────────────────────────────┘
│                 │ GET /api/v1/public/jobs?… (SSR fetchBoard)                 │
│                 │ POST /api/v1/public/chat-search  [NEW, client fetch]      │
├─────────────────┴────────────────────────────────────────────────────────────┤
│                            BACKEND (FastAPI, /api/v1)                        │
│  ┌────────────── Public API (existing, anonymous) ──────────────┐            │
│  │ GET  /public/jobs        → crud.list_published                │            │
│  │ GET  /public/jobs/{id}   → crud.get_published                 │            │
│  │ POST /public/jobs/{id}/reveal-contact (Turnstile+rate limit)  │            │
│  │ POST /public/jobs/{id}/report (rate limit, log-only)          │            │
│  │ POST /public/chat-search  [NEW] (rate limit + timeout)        │            │
│  └──────────────┬───────────────────────────────────────────────┘            │
│                 │                                                            │
│  ┌──────────────▼──────────────┐     ┌───────────────────────────────────┐  │
│  │ services/chat_search/ [NEW] │     │ services/cities.py (existing)     │  │
│  │  - schema.py (intent JSON)  │────▶│  resolve_city / resolve_sort      │  │
│  │  - prompt.py (NL→params)    │     └───────────────────────────────────┘  │
│  │  - extractor.py (Groq call) │     ┌───────────────────────────────────┐  │
│  │  - mapper.py (params→query) │────▶│ crud.jobs.list_published (reuse)  │  │
│  └──────────────┬──────────────┘     │  + optional in-memory post-filter │  │
│                 │                    └───────────────────────────────────┘  │
│                 │  async Groq chat completion (strict JSON)                  │
├─────────────────┴────────────────────────────────────────────────────────────┤
│  Groq API (existing config: GROQ_API_KEY/MODEL/FALLBACK/TIMEOUT_SECONDS)     │
│  Neon Postgres: jobs(status,published,expires_at,city,search_text,salary,…)  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation | Status |
|-----------|----------------|------------------------|--------|
| `frontend/app/(public)/page.tsx` | SSR public board from URL filters; renders board + chat entry point | Server Component, `fetchBoard`/`fetchJob`, `cache: "no-store"` | **Modify (small)**: mount chat launcher/drawer |
| `frontend/lib/filters.ts` | Single source of truth for URL↔filter parsing/serialization (`q,cit y,sort,page,vaga`) | Pure helpers (`normalizeFilters`, `toApiParams`, `buildBoardHref`) | **Modify (optional)**: add helpers to apply chat params to URL (no new persisted state) |
| `frontend/lib/jobs.ts` | Server-side board fetches against `/api/v1/public/jobs` | `request` + `BoardError`, timeout | **Extend**: add client-callable chat-search helper OR separate `lib/chat-search.ts` for browser `fetch` (avoid coupling to server-only env assumptions) |
| `frontend/components/board/Chat*` | Chat UI: open/close, message input, show interpreted params + result cards/links | Client Components (`"use client"`), drawer/modal, mobile-first, accessible focus trap | **New** |
| `backend/app/api/v1/public.py` | Anonymous public endpoints (list/detail/reveal/report) | FastAPI router, `slowapi` limits, Turnstile on reveal | **Modify**: add `POST /public/chat-search` with its own rate limit + request schema |
| `backend/app/crud/jobs.py` | Published query predicate/order/pagination (`list_published`, `_published_filters`) | SQLAlchemy async, shared predicate for items+total | **Reuse now; Extend later (controlled)** if native filters added (salary/modality/contract) |
| `backend/app/services/cities.py` | City/sort whitelist normalization | `resolve_city`, `resolve_sort` | **Reuse** (canonical DB city values) |
| `backend/app/services/chat_search/*` | NL message → validated intent → mapped query params → (optional) post-filter/ranking hints | Pydantic schema + prompt + Groq call seam mirroring `services/extraction/*` patterns | **New** |
| `backend/app/core/ratelimit.py` (or equivalent limiter config) | Per-IP throttles for anonymous endpoints | `slowapi` decorators (`@limiter.limit(...)`) as used by reveal/report | **Modify**: define chat-search limit key/policy |
| Groq client/config | Model chain, timeout, strict JSON response handling | Existing `settings.GROQ_*`, patterns in `services/extraction/client.py` | **Reuse** (do not duplicate key/model plumbing) |

## Recommended Project Structure

```
backend/app/
├── api/v1/
│   └── public.py                 # MODIFY: add POST /public/chat-search
├── crud/
│   └── jobs.py                   # REUSE; MODIFY only if adding native filter columns later
├── schemas/
│   ├── job.py                    # REUSE: JobPublic/JobListResponse
│   └── chat_search.py            # NEW: ChatSearchRequest/Response, InterpretedParams
├── services/
│   ├── cities.py                 # REUSE: resolve_city/resolve_sort
│   ├── extraction/               # REUSE patterns (client seam, strict schema, sanitization)
│   └── chat_search/              # NEW
│       ├── schema.py             # intent JSON schema + Pydantic models (strict, bounded)
│       ├── prompt.py             # pt-BR system/user prompt, delimiters, "no inventing"
│       ├── extractor.py          # call Groq once per request (timeout-bounded), parse/validate
│       └── mapper.py             # intent → {q, city, sort} + post-filter directives + notes
└── core/
    └── ratelimit.py              # MODIFY if needed: chat limit constant/policy

frontend/
├── app/(public)/
│   └── page.tsx                  # MODIFY: include Chat entry component
├── components/board/
│   ├── ChatSearchButton.tsx      # NEW (client): launcher (FAB/toolbar action)
│   ├── ChatSearchDrawer.tsx      # NEW (client): drawer/modal, messages, results
│   └── ...existing board comps   # REUSE (JobCard/list rendering patterns or lightweight result rows)
├── lib/
│   ├── filters.ts                # REUSE/MODIFY: map interpreted params → Filters/URL
│   ├── jobs.ts                   # REUSE for board SSR; keep server fetch semantics
│   ├── chat-search.ts            # NEW: browser fetch to POST /public/chat-search
│   └── api.ts                    # EXTEND types if shared
```

### Structure Rationale

- **`services/chat_search/` separate from `extraction/`:** extraction writes/admin flow and parses many jobs from pasted blobs; chat-search is a public, read-only, single-intent parse. Share *patterns* (strict JSON, sanitization, model-chain/error mapping) but not orchestration/storage code.
- **Keep `crud.list_published` as the search engine:** avoids duplicating visibility rules (`status=published AND expires_at>now()`), predicate parity, and ordering/tie-break semantics already fixed in D-17/04 patterns.
- **Chat as client-side island on SSR board:** preserves SEO/fast first paint of existing server-rendered board; chat is progressive enhancement and must not block initial HTML.

## Architectural Patterns

### Pattern 1: Intent Extraction as a Pure, Bounded Translation Step

**What:** Convert one NL message into a strict, validated `InterpretedParams` object (no DB access, no side effects). LLM extracts *parameters only*; it never receives job rows and never invents results.
**When to use:** Every chat request.
**Trade-offs:** Deterministic validation prevents prompt drift, but requires clear handling for unsupported/ambiguous fields (return them as notes, not fabricated filters).

**Example (shape, illustrative):**
```python
class InterpretedParams(BaseModel):
    q: str | None = None                 # keywords/role text for existing search_text match
    city: str | None = None             # canonical: São Paulo|Rio de Janeiro|Belo Horizonte|Remoto|None
    sort: Literal["recentes", "antigas"] = "recentes"
    salary_min: int | None = None        # BRL/month intent, if confidently stated
    salary_max: int | None = None
    modality: Literal["remoto","presencial","hibrido"] | None = None
    contract: str | None = None          # e.g. CLT/PJ/estágio (normalized enum subset)
    keywords: list[str] = []             # extracted tokens (merged into q strategy)
    confidence_notes: list[str] = []     # "salário não filtrado nativamente", etc.
```

### Pattern 2: Map-to-Existing-Query First, Controlled Degrade for Non-Native Fields

**What:** Drive results through the current public search primitives whenever possible (`q` → `crud.list_published(q=...)`, `city` → `resolve_city`, `sort` → `resolve_sort`). For fields not modeled natively today (`salary` text, no explicit `modality`/`contract` columns), apply **incremental, explicit strategies**:
- **Phase 1 (MVP, no schema change):** fetch a bounded candidate page/window using mapped `q/city/sort` (e.g. larger `limit` up to a safe cap, or first N pages capped) and apply best-effort in-memory post-filters/ranking (regex/number parse over `salary`, keyword heuristics over `title/activities/requirements/city` for modalidade/contrato). Return `unsupported_or_approximate` notes in interpretation.
- **Phase 2 (only if needed):** extend DB/CRUD with indexed/normalized columns or structured filters (e.g. `salary_min/max` numeric, `modality`, `contract_type`) behind the same endpoint contract.
**When to use:** Always prefer reuse; escalate to schema extension only with measured need.
**Trade-offs:** Post-filtering is fast to ship and zero-migration but can reduce recall/pagination accuracy; native filters are correct/performant but add migration + backfill + extraction alignment work.

### Pattern 3: Public Chat Endpoint with Defense-in-Depth (Rate Limit + Timeout + Validation)

**What:** Treat chat-search as an abuse/cost-sensitive public endpoint (LLM call per request). Enforce per-IP rate limit, strict request size, server-side timeout budget around Groq, and fail closed to a safe message (no stack traces, no prompt echo).
**When to use:** The new `POST /public/chat-search`.
**Trade-offs:** Protects free-tier cost/availability; aggressive limits can frustrate users—start conservative and observable.

## Data Flow

### Request Flow (Chat Search)

```
[User types NL query in ChatDrawer]
    ↓ (client)  POST /api/v1/public/chat-search { message }
[FastAPI public.chat-search]
    ↓ @limiter (per-IP) + input validation (max length, trim, empty → 422/400-ptBR)
[services.chat_search.extractor]  (asyncio.timeout / overall budget)
    ↓ Groq strict JSON (model chain, retry-on-429 bounded) — NO job rows sent
[InterpretedParams validated & normalized]
    ↓ mapper: resolve_city/resolve_sort, build q, derive post-filter directives
[crud.list_published(session, q, city, sort, page=1, limit=bounded)]
    ↓ (optional) in-memory post-filter/rank for salary/modality/contract (best-effort)
[Response: interpretation + results(JobPublic[]) + total/applied + notes]
    ↓
[ChatDrawer renders "entendi: …" + result list + "Aplicar no board" (buildBoardHref)]
```

### "Apply to Board" Flow (recommended UX integration)

```
[User clicks "Aplicar filtros"]
    ↓ map interpreted params → Filters (q, city slug, sort; drop vaga/page=1)
[router.push(buildBoardHref(...)) or Link href]
    ↓ URL change
[(public)/page.tsx re-renders via searchParams] → existing SSR fetchBoard path (source of truth)
```

*Key point:* the **board URL/listing remains canonical**. Chat can show a preview result set, but applying filters should delegate to the existing board pipeline for consistency, shareable links, and pagination/SEO behavior.

### Key Data Flows

1. **NL → params:** untrusted user text is delimited/sanitized in prompt (same injection posture as extraction), parsed to strict schema, then clamped/whitelisted server-side (`resolve_city/resolve_sort`, length caps). Never trust model output without normalization.
2. **Params → jobs:** reuse `list_published` visibility predicates; only augment with post-filters that cannot contradict published/non-expired guarantees.
3. **Results → user:** return `JobPublic` (contact-free) items only, mirroring existing public list contract; detail/reveal continues through existing endpoints.

## Integration Points & Boundaries

### New vs Modified (explicit)

| Area | New | Modified | Rationale |
|------|-----|----------|-----------|
| Backend endpoint | `POST /api/v1/public/chat-search` handler + Pydantic request/response schemas | `backend/app/api/v1/public.py` to register route | Public, anonymous capability aligned with existing `/public/*` surface |
| Intent service | `backend/app/services/chat_search/{schema,prompt,extractor,mapper}.py` | — (reuse `services/cities`, Groq config; optionally factor tiny shared Groq helpers only if duplication becomes harmful) | Isolates NL logic; avoids entangling admin extraction pipeline |
| Search core | — | **None initially** to `crud.list_published`/`_published_filters` | Preserve behavior; chat adapts to current capabilities |
| Rate limiting | chat-specific limit value/policy | limiter config/decorator usage | Separate cost profile from report/reveal |
| Frontend UI | `ChatSearchButton`, `ChatSearchDrawer/Modal`, `lib/chat-search.ts` | `app/(public)/page.tsx` to mount entry; minor `BoardToolbar`/layout hook if entry placed there | Additive, mobile-first, no login/friction |
| URL/filter contract | — | `lib/filters.ts` only if helper(s) needed to translate interpreted params → board href | Keep URL contract centralized |

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Groq (LLM) | Async chat completion, strict JSON schema, model chain + bounded retries/timeout (reuse existing env/settings) | **Do not** send hundreds of jobs; only the user message (+ tiny fixed instructions). Map provider errors to pt-BR, never leak raw upstream details/keys. Cost/latency dominate UX. |
| Neon/Postgres | Existing SQLAlchemy async session via `get_session` | No new tables required for MVP; consider no chat logging persistence (privacy/cost) unless product asks. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `api.v1.public` ↔ `services.chat_search` | Direct async call | Service returns typed interpretation + query plan; route owns HTTP concerns (limits, status codes) |
| `services.chat_search` ↔ `crud.jobs` | Direct call with `AsyncSession` | Reuse published-only predicates; keep total/items consistency if returning paged preview |
| `chat UI` ↔ `board page state` | URL navigation (`buildBoardHref`) and/or local preview state | Prefer URL as source of truth for "applied" filters; drawer state is ephemeral UI state |

## Suggested Build Order (dependency-aware)

1. **Contract & schema (backend, no network side effects):** define `ChatSearchRequest/Response`, `InterpretedParams` (strict, bounded enums/lengths), and mapper rules to existing `q/city/sort`. *Deps:* understand `resolve_city`, `list_published` signature.
2. **Intent extractor service (backend):** prompt + Groq call (timeout-bounded, reuse `GROQ_*` settings/model-chain posture) with deterministic normalization/whitelisting and safe fallbacks when Groq unavailable. *Deps:* (1).
3. **Public endpoint + protections (backend):** `POST /public/chat-search` wiring service → `crud.list_published` (+ best-effort post-filter for salary/modalidade/contrato with explicit notes), per-IP rate limit, input/timeout guards, pt-BR errors. *Deps:* (1),(2).
4. **Frontend client integration (minimal):** `lib/chat-search.ts`, chat launcher + drawer/modal rendering interpretation and preview results (contact-free), "apply to board" via `buildBoardHref`. *Deps:* (3) for real responses; can stub types earlier.
5. **Fit-and-finish & hardening:** mobile UX/a11y, empty/ambiguous states, copy for unsupported params, observability (timings/error classes), and tuning rate limit/timeout/candidate window from real usage. *Deps:* (4).
6. **Optional evolution (post-MVP, only if justified):** native DB-backed filters for salary/modality/contract, caching of identical intents, conversation follow-ups — each behind explicit requirements/migrations.

*Rationale:* backend contract first de-risks mapping/validation; endpoint protections before public exposure; UI last but can parallelize against a stable mocked contract.

## Rate Limiting, Caching, and Performance Considerations

| Concern | Recommendation | Notes |
|---------|----------------|-------|
| Rate limiting | Apply strict per-IP limit on `/public/chat-search` (stricter than report; reveal already limited) via existing `slowapi` limiter; return shared pt-BR 429 + `Retry-After` | Protects Groq quota and cost; consider separate bucket from reveal to avoid cross-flow starvation. |
| Timeouts | Enforce overall request budget (e.g. asyncio timeout wrapping Groq + search) below platform/proxy limits; keep Groq call bounded by `GROQ_TIMEOUT_SECONDS` semantics | Fail fast with actionable pt-BR message ("não consegui entender agora, tente termos como cargo e cidade"). |
| Payload/abuse bounds | Cap message length (chars) and reject/trim control noise; single-turn MVP (no long history) to cap tokens/cost | Public, anonymous endpoint. |
| Caching | **Default: no response cache** (or very short, e.g. 30–60s in-process) keyed by normalized message; rely on `cache: "no-store"` semantics already used for board freshness | Job board changes (expiry/publish) make correctness more important than micro-optimization at 100–500 jobs/month. |
| Search cost | `list_published` already indexed/optimized for status/expiry/search_text; post-filter only over a bounded candidate set (cap limit/pages) | Never scan unbounded rows in Python for a public request. |
| Frontend perf | Lazy-mount drawer contents; keep chat JS off critical SSR path; reuse existing card/result presentation primitives where practical | Mobile-first; avoid large client bundles. |

## Anti-Patterns

### Anti-Pattern 1: Sending Job Listings to the LLM
**What people do:** Stuff current jobs/results into the prompt to "let the model search."
**Why it's wrong:** Blows token/cost/latency budgets, leaks data patterns, non-deterministic, and explicitly disallowed by project constraints.
**Do this instead:** LLM extracts **parameters only**; database/query layer returns results.

### Anti-Pattern 2: Bypassing Existing Search/Visibility Rules
**What people do:** Implement a parallel raw SQL/query for chat results.
**Why it's wrong:** Risks diverging from `published && not expired`, predicate parity, ordering, and future fixes.
**Do this instead:** Reuse `crud.list_published` and `services.cities` normalization; only layer safe post-filters.

### Anti-Pattern 3: Trusting Model Output as Already-Valid Filters
**What people do:** Pass LLM city/sort/filters straight to the DB or URL.
**Why it's wrong:** Hallucinated/unknown values can break UX or, if schema changes later, create unsafe queries; city must match whitelist semantics.
**Do this instead:** Strict schema + server-side whitelist (`resolve_city/resolve_sort`), clamp ranges, and surface "não entendido/ignorado" notes.

### Anti-Pattern 4: Making Chat the New Source of Truth for the Board
**What people do:** Keep results only in chat local state with no URL/apply path.
**Why it's wrong:** Breaks shareability, back/forward navigation, and consistency with existing SEO/SSR board behavior.
**Do this instead:** Provide "aplicar no board" mapping to canonical URL params for supported fields.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k users (current target: 100–500 jobs/mo) | Current approach is sufficient: per-request Groq call, reuse `list_published`, bounded post-filter, simple rate limit. Keep synchronous request/response. |
| 1k-100k users | Add short-TTL intent/result caching for hot queries, tighter abuse controls, metrics/alerting on Groq latency/errors and 429s, consider queueing only if timeouts persist (not default). |
| 100k+ users | Move to dedicated search/index (or materialized structured fields) for native multi-filter queries; revisit conversational state storage and cost controls; out of scope for v1.3. |

### Scaling Priorities

1. **First bottleneck:** Groq latency/rate limits and per-request cost — mitigate with strict rate limits, tight timeouts, minimal prompts, and optional tiny cache.
2. **Second bottleneck:** Post-filter pagination/recall mismatch for non-native fields — mitigate by promoting those fields to native indexed filters when product demands it.

## Sources

- Codebase (HIGH): `backend/app/api/v1/public.py`, `backend/app/crud/jobs.py`, `backend/app/services/cities.py`, `backend/app/services/extraction/client.py`, `backend/app/services/extraction/schema.py`, `backend/app/models/job.py`, `frontend/app/(public)/page.tsx`, `frontend/lib/jobs.ts`, `frontend/lib/filters.ts`
- Project constraints (HIGH): `.planning/PROJECT.md`, `AGENTS.md`
- Prior research (context, partially superseded on specifics): `.planning/research/ARCHITECTURE.md` (pre-v1.3), `.planning/research/STACK.md`, `.planning/research/PITFALLS.md`

---
*Architecture research for: v1.3 Chatbot Inteligente de Busca de Vagas (integration into EmpregaNoix)*
*Researched: 2026-11-17*
