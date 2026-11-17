# Project Research Summary

**Project:** EmpregaNoix
**Domain:** NL chatbot search (intent extraction → structured params → existing public job search) for a PT-BR public job board
**Researched:** 2026-11-17
**Confidence:** HIGH (core approach, grounded in codebase) / MEDIUM (free-tier thresholds, non-native filter heuristics)

## Executive Summary

EmpregaNoix v1.3 adds chat-based natural-language job search to an existing no-login public board (Next.js 16 + FastAPI + Neon + Groq). Experts build this kind of feature as **NL-to-search parameter extraction**, not as LLM-over-corpus retrieval: the model translates one PT-BR query into a strict, validated intent, the backend normalizes/whitelists it, and deterministic search primitives (`GET /api/v1/public/jobs` / `crud.list_published`, `resolve_city`, `resolve_sort`) return results. The current stack and codebase are already well-positioned for this — especially the hardened Groq structured-output patterns in `services/extraction/client.py` and the published/expiry-safe query path in `crud/jobs.py` — so the recommended approach is to **reuse Groq and existing search/UI contracts**, add a small `chat_search` service + public endpoint, and keep the board URL as the source of truth.

The recommended implementation is additive and constrained: LLM extracts **parameters only** (never receives job listings), outputs are schema-validated and allowlisted (city whitelist, sort enum, capped `q`/pagination), and chat responses return contact-free `JobPublic` items that preserve the existing protected reveal flow. For fields not natively modeled today (salary, modalidade, contract/seniority nuances), start with explicit capability mapping + bounded best-effort text/post-filtering and clearly label anything partial/unsupported rather than inventing filters or claiming accuracy.

Key risks are recall loss from hallucinated/over-constrained filters, public-endpoint abuse/cost/latency, prompt injection on untrusted input, and regressions to the core board/no-friction value. Mitigate with null-by-default intent extraction and relaxation/fallback behavior, layered protections (rate limit, input/timeout/token bounds, circuit-breaker/fallback to manual/keyword search), strict post-validation + allowlists, and regression-gated integration that keeps chat lazy-loaded and `crud.list_published` / `JobPublic` boundaries intact.

## Key Findings

### Recommended Stack

**Do not add a second LLM/retrieval stack by default.** The milestone is best served by reusing the existing, configured Groq integration (`openai/gpt-oss-20b` default, `120b` fallback, strict JSON schema, timeout/retry/fallback, prompt-injection delimiting) and the existing FastAPI/Next/Neon primitives. New dependencies are minimal-to-none for the recommended path.

**Core technologies:**
- **Groq (existing, `openai/gpt-oss-20b`/`120b` via env)**: NL → structured intent extraction — zero new vendor/keys, low latency/cost, strict structured outputs already proven in repo.
- **Pydantic v2 + strict JSON schema**: `ChatIntent`/response contracts — single source of truth for validation, defaults/nulls, and normalization before any query.
- **FastAPI + slowapi + existing public API patterns**: `POST /api/v1/public/chat-search` — per-IP throttling, bounded payloads, pt-BR errors, contact-free public payloads.
- **Next.js 16 / React 19 / Tailwind 4 (existing)**: mobile-first chat drawer/modal client component — additive, lazy-loadable, no new chat/widget framework.
- **SQLAlchemy async + `crud.list_published` + `services/cities` (reuse)**: deterministic, published/expiry-safe search — preserves visibility, parity, and ordering semantics.

**Critical stack choices:** no embeddings/vector DB/pgvector; never send job rows to the LLM; prefer query-param translation to existing `q/city/sort` + bounded in-memory post-filter for non-native fields (schema extension only if justified later). Alternatives (Gemini/OpenRouter/Ollama) are viable only as explicit fallbacks/experiments, not default.

### Expected Features

**Must have (table stakes):**
- **NL input (pt-BR) → strict validated intent JSON** — extract only stated/implied params (cargo, senioridade, cidade whitelist, modalidade, faixa salarial, tipo contrato, keywords, sort) with null-safe defaults.
- **Safe mapping to existing search** — apply `q/city/sort/pagination` via current public search logic; normalize/whitelist and ignore/relax unsupported values.
- **Transparent interpretation + results in chat** — show "entendi/apliquei/ignorei" params and return relevant `JobPublic` results with access to existing detail/reveal flow (no contacts in payload).
- **Combinations, empty states, and perceived performance** — handle multi-slot queries, useful zero-result guidance, loading/error states, and protected latency.

**Should have (competitive, P2 once validated):**
- **PT-BR-tolerant normalization/synonyms** and **light session refinement** (reuse last interpretation client-side) — better recall/UX without new infra.
- **"Vagas parecidas" via deterministic relaxation** (drop 1 constraint, label as approximation) and grounded "why these results" summaries — avoid dead-ends without embeddings/LLM-over-corpus.
- **Onboarding chips/examples** aligned to MVP queries.

**Defer (v2+ / anti-features for MVP):**
- **LLM ranking over job corpus, embeddings/vector search, long persistent memory, agentic apply flows, invented/normalized missing data, exposed contacts** — conflict with cost, constraints, privacy, or truthfulness. Promote salary/modality/contract to native schema/filters only if product signals justify.

### Architecture Approach

Integrate chat as an additive, bounded translation layer: a client-side chat island (drawer/modal) calls a new public endpoint that performs intent extraction → normalization/mapping → deterministic search, returning interpretation + contact-free results while delegating "apply to board" to canonical URL params/SSR flow. Keep boundaries clear: new `services/chat_search/*` (schema/prompt/extractor/mapper) separate from admin extraction, reuse `crud.list_published`/`services.cities`/Groq config, and treat non-native fields as explicit best-effort post-filters over bounded candidates until proven necessary.

**Major components:**
1. **`services/chat_search/` (new, backend)** — strict intent schema, pt-BR prompt, Groq extraction seam, and mapper/normalizer (whitelists, caps, capability-aware application/notes).
2. **`POST /api/v1/public/chat-search` (new, backend)** — rate-limited, timeout-bounded public endpoint composing extraction + `list_published`, returning interpretation + `JobPublic` results (no contacts).
3. **Chat UI client components + `lib/chat-search.ts` (new, frontend)** — mobile-first drawer/modal, parameter chips, preview results, and "apply to board" via existing `filters.ts`/URL contract.

### Critical Pitfalls

1. **Hallucinated/over-constrained filters kill recall** — null-by-default schema ("extract only stated/implied"), separate extracted vs applied filters, whitelist/relax unsupported or low-confidence constraints, and provide progressive fallback; validate with PT-BR golden queries.
2. **Public chat becomes a cost/latency/abuse magnet** — per-IP rate limits, request/`max_tokens` caps, strict timeouts/concurrency budget, short-TTL intent cache/dedup, circuit-breaker + fallback to keyword/manual search, and metrics/kill-switch.
3. **Prompt injection and untrusted input break safety** — harden prompt (intent-only, ignore conflicting instructions, JSON-only), strict parse+schema+allowlist validation, no secrets/admin context in prompt, no internal leakage in errors/logs.
4. **Extracted params mismatch real DB/search capabilities** — explicit capability matrix (supported now / safe text-mapped / unsupported), normalize to whitelist/canonical values, never claim unapplied filters, and report `applied` vs `ignored/approximate`.
5. **Integration regresses core board/no-friction value** — additive composition over `list_published`/`JobPublic` boundaries, lazy-loaded isolated UI, and regression tests/side-by-side checks for existing public search/detail/reveal flows.

## Implications for Roadmap

Based on combined research, use a dependency-driven, additive sequence: lock the intent/mapping contract before exposing a public LLM endpoint, harden the endpoint before broad UI reliance, then integrate/validate UX and operational readiness.

### Phase 1: Intent Contract, Capability Matrix & Safe Mapping
**Rationale:** Every downstream component depends on a trustworthy, recall-preserving translation from NL to existing search primitives; this is where hallucination, capability mismatch, and whitelist/normalization errors must be eliminated first.
**Delivers:** `ChatIntent` schema + prompt, normalization/mapper (to `q/city/sort` with caps), explicit capability matrix (supported/mapped/unsupported incl. salary/modality/contract), and deterministic/unit-tested behavior (mocked Groq, no real key).
**Addresses:** NL extraction → validated JSON, safe application to existing search, PT-BR normalization groundwork, truthful handling of non-native fields.
**Avoids:** Hallucinated/over-constrained filters, param/DB capability mismatch, unsafe unvalidated model output.

### Phase 2: Public Chat-Search API, Protections & Resilience
**Rationale:** The public anonymous LLM endpoint is the main cost/abuse/risk surface and must be production-safe before chat becomes a primary entry point.
**Delivers:** `POST /api/v1/public/chat-search` composing extractor → mapper → `crud.list_published` (bounded candidate set, best-effort post-filter where defined) returning interpretation + `JobPublic` results; env-tunable rate limit/timeout/input/`max_tokens` guards, strict validation, pt-BR errors, and Groq failure fallback (keyword/manual-search guidance).
**Uses:** Existing Groq config/client patterns, FastAPI/slowapi, Pydantic v2, `services/cities`, SQLAlchemy async search path.
**Implements:** Bounded translation + map-to-existing-query backend flow with defense-in-depth.
**Avoids:** Cost/latency/abuse magnet, prompt-injection exposure via weak handling, secret/internal leakage, contact-boundary violations.

### Phase 3: Chat UI Integration & Transparent Search UX
**Rationale:** Once the contract/API is stable and protected, ship the user-facing flow that preserves the core "find a job in seconds, no login" value and makes interpretation/applicability explicit.
**Delivers:** Lazy-loaded mobile-first chat drawer/modal with input/loading/error/empty states, "entendi/apliquei/ignorado/aproximado" parameter chips, preview results reusing existing presentation/detail access, and "apply to board" via canonical URL (`filters.ts`/SSR board).
**Addresses:** NL entry, visible interpretation, results access, multi-filter combinations (including clearly-labeled partial support), zero-result recovery, examples/chips.
**Avoids:** Poor zero-result UX, hidden/false filter application, chat becoming a second source of truth, contact-flow bypass, frontend perf regressions.

### Phase 4: Hardening, Regression Gate & Measured Tuning (post-MVP hooks)
**Rationale:** Behavior under real PT-BR phrasing, traffic, and dataset sparsity determines whether heuristics/limits hold; regressions to existing flows are highest-risk at launch.
**Delivers:** Golden/injection/regression test coverage (backend + E2E), side-by-side parity checks vs manual search, observability (latency/errors/429/zero-result signals) and kill-switch, tuning of limits/timeouts/candidate window/cache TTL, and explicit decisions on v1.x items (light refinement, deterministic "parecidas") or schema promotion if justified.
**Addresses:** MVP example validation, reliability/privacy/operability, and data-driven follow-ups.
**Avoids:** Silent regressions, unobservable abuse/cost issues, premature embeddings/native-schema complexity.

### Phase Ordering Rationale

- **Contract before endpoint, endpoint before UI:** mapping/validation correctness is a prerequisite for safe querying; protections must exist before exposing public LLM usage; UI depends on a stable, truthful response contract.
- **Reuse-first, extend-later:** compose `crud.list_published`/`services/cities` and bounded post-filters before any DB/index changes to avoid duplicating visibility logic and migration risk at low volume.
- **Additive boundaries preserve core value:** keeping chat as a client island + URL-canonical "apply" path and `JobPublic`/reveal boundaries prevents regressions to the no-login, no-friction board.
- **Pitfall-driven gates:** recall/capability safety (P1) and abuse/injection defenses (P2) are verified before broad rollout; regressions/operability are explicitly gated (P4).

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** PT-BR salary/modality/contract/seniority normalization heuristics and a precise capability matrix vs. current `jobs` fields/text quality — dataset-dependent and easy to over-promise.
- **Phase 2:** Production-safe rate/timeout/token/concurrency thresholds on Groq + hosting free tiers and fallback/circuit-breaker behavior — needs measurement/tuning (MEDIUM confidence).

Phases with standard patterns (skip research-phase):
- **Phase 3:** Standard Next.js client drawer/modal + existing fetch/URL/filter patterns (`BoardToolbar`/`filters.ts`) — well-understood in codebase.
- **Phase 4:** Conventional testing/observability/regression-hardening workflows (pytest/Vitest/Playwright, structured logging/metrics) — established patterns, apply to new surface.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Grounded in current repo/config and verified library patterns; alternative-provider specifics remain MEDIUM. |
| Features | MEDIUM | Clear project constraints and domain patterns, but external competitor/web validation was unavailable in-repo; MVP field support must be proven against real data. |
| Architecture | HIGH | Derived directly from existing components/contracts (`public.py`, `crud.jobs`, `services/cities`, extraction patterns, frontend board/filters). |
| Pitfalls | HIGH | Strong alignment with project constraints and well-known LLM/public-endpoint risks; exact operational thresholds are MEDIUM pending production metrics. |

**Overall confidence:** HIGH (approach/integration) / MEDIUM (tuning and non-native field coverage)

### Gaps to Address

- **Non-native filter fidelity (salary/modalidade/contrato/senioridade):** sparse/unstructured PT-BR data may limit reliable filtering — define capability matrix early, implement as explicit best-effort/labelled, and validate with MVP examples before claiming support.
- **Groq free-tier and latency behavior under public traffic:** tune rate limits, timeouts, retries, caching TTL, and fallback thresholds from observed metrics; keep a kill-switch.
- **PT-BR intent phrasing coverage and recall:** build golden/adversarial query sets (ambiguity, synonyms, injection) and iterate prompt/relaxation rules; monitor zero-result rate vs manual search.
- **Pagination consistency with post-filtering:** bounded in-memory filtering can skew totals/pages — document semantics (preview vs applied) or constrain to first bounded window until native filters exist.

## Sources

### Primary (HIGH confidence)
- **Codebase:** `backend/app/services/extraction/client.py`, `backend/app/services/extraction/schema.py`, `backend/app/core/config.py`, `backend/app/api/v1/public.py`, `backend/app/crud/jobs.py`, `backend/app/models/job.py`, `backend/app/services/cities.py`, `frontend/app/(public)/page.tsx`, `frontend/components/board/BoardToolbar.tsx`, `frontend/lib/jobs.ts`, `frontend/lib/filters.ts`
- **Project context:** `.planning/PROJECT.md`, `AGENTS.md`
- **Prior project research (inputs):** `.planning/research/STACK.md`, `.planning/research/FEATURES.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md`
- **Library/registry checks (as cited in STACK):** `/groq/groq-python` (strict JSON schema/structured outputs), `/websites/deepwiki_googleapis_python-genai` and `/ollama/ollama-python` (alternative patterns), `pip index versions groq` (1.7.0)

### Secondary (MEDIUM confidence)
- Established NL intent-extraction / slot-filling and public LLM endpoint hardening patterns (schema validation, allowlists, prompt-injection resistance, null-over-guessing, rate/timeout/fallback/caching) — domain best practices reflected in research files.

### Tertiary (LOW confidence)
- None. (Alternative-provider free-tier quotas, exact performance/rate thresholds, and live competitor behavior require validation during planning/implementation.)

---
*Research completed: 2026-11-17*
*Ready for roadmap: yes*