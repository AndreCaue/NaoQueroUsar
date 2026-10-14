# Project Research Summary

**Project:** NQU — NaoQueroUsar
**Domain:** Brazilian no-signup public job board with LLM extraction + manual curation
**Researched:** 2026-10-13
**Confidence:** MEDIUM-HIGH

## Executive Summary

NQU is a public, no-signup job board for Brazil that ingests raw job posts from WhatsApp/Telegram groups, extracts structured listings with an LLM, and publishes them after a single master-admin review. The product's wedge is **not** "no signup" alone — several live Brazilian competitors (EmpregoDaqui, BrVagas, BuscarVagas) already claim that. The defensible edge is the **combination of zero-friction contact reveal + LLM-extracted human-reviewed curation quality + a hard 14-day expiry that guarantees zero ghost jobs.** The architecture is a well-understood two-app split: Next.js (App Router) on Vercel for the UI, FastAPI (async) on Railway/Render for the API, Neon Postgres for storage, Groq for extraction, and Cloudflare Turnstile for anti-spam. All four research files agree this stack is appropriate; the layering (router → service → CRUD), schema-first contracts (Pydantic v2), and migrations-from-day-one (Alembic) are the standard patterns.

The single most important finding is a **live blocker in the current PROJECT.md**: the fixed Groq models `llama-3.1-8b-instant` and `llama-3.3-70b-versatile` were **retired on 2026-08-16** and now return errors. STACK.md and ARCHITECTURE.md were written assuming those models; PITFALLS.md caught the retirement. The replacement (`openai/gpt-oss-20b` / `openai/gpt-oss-120b`, or `qwen/qwen3.8-27b`) is strictly better — it supports Groq **strict Structured Outputs** (`strict: true`), which the retired Llama models never did. Roadmap/planning must treat the model as a config value with a fallback chain, not a hardcoded constant, and update the PROJECT.md constraint.

The dominant risks cluster in three areas, each with a clear mitigation. (1) **Extraction reliability** — silent truncation of large pastes, hallucinated fields, Brazilian contact-format variance, prompt injection, and free-tier rate limits (a single 12–15K-token paste can exceed an 8K TPM limit by itself). Mitigate with chunking under TPM, strict schema + Pydantic validation, a grounding check (every extracted string must appear in the source), a pt-BR contact parser, input delimiters, and proactive throttling. (2) **Anti-scraping theater** — hiding contacts with CSS/JS while still shipping them in the JSON payload protects nothing. Mitigate by keeping contacts out of the SSR/list payload entirely and serving them only from a Turnstile-verified, rate-limited reveal endpoint. (3) **Infrastructure "$0" assumptions** — Render free web services spin down after 15 min, Railway's free tier only lasts ~30 days, Vercel Hobby cron is once-per-day/UTC/no-retry, and a persistent DB connection can burn Neon's 100 CU-hour free budget in ~16 days. Mitigate with an idempotent DB-statement expiry job triggered externally, pooled/small DB connections (or the Neon HTTP driver), and a realistic small monthly budget.

## Key Findings

### Recommended Stack

See [STACK.md](./STACK.md). The fixed stack (Next.js App Router, FastAPI, Neon Postgres, Groq, Turnstile, Vercel + Railway/Render) is validated and appropriate. Recommended supporting libraries: **SQLAlchemy 2.1.x async + asyncpg + Alembic** (with `Mapped`/`mapped_column` style), **Pydantic v2** for validation and as the extraction schema, the **Groq Python SDK** using strict JSON structured outputs, **PyJWT + passlib[bcrypt]** for single-master auth, **APScheduler** for the expiry job, and Tailwind v4 + Zod + `next-turnstile` on the frontend. Testing: pytest + pytest-asyncio, Vitest, Playwright.

**⚠️ Version correction (supersedes STACK.md):** STACK.md and ARCHITECTURE.md recommend `llama-3.1-8b-instant` / `llama-3.3-70b`. **These are retired (2026-08-16).** Use `openai/gpt-oss-20b` (fast/cheap default) with `openai/gpt-oss-120b` (quality) as fallback, via a `GROQ_MODEL` env var. These models also enable strict structured outputs. This is the highest-priority correction before planning.

**Core technologies:**
- **Next.js (App Router) + React 19 + TypeScript** — public + admin UI; Server Components for read-heavy public pages, client islands for modal/reveal/Turnstile.
- **FastAPI + Pydantic v2** — async API, validation, OpenAPI; thin routers + service layer.
- **SQLAlchemy 2.x (async) + asyncpg + Alembic** — ORM and migrations; pooled connection string for Neon.
- **Neon Postgres** — serverless Postgres; watch CU-hour budget, use `-pooler` host.
- **Groq (gpt-oss-20b/120b)** — LLM extraction with strict structured outputs.
- **Cloudflare Turnstile** — free anti-spam; **server-side Siteverify is mandatory**.
- **Tailwind CSS v4 + Zod + next-turnstile** — dark minimal-purple theme, schema validation, widget.

### Expected Features

See [FEATURES.md](./FEATURES.md). Market research shows "sem cadastro" is already a contested category, so NQU must lean on **curation × freshness × direct contact**.

**Must have (table stakes):**
- Public ungated published-jobs grid; job card + detail modal
- One-tap contact reveal + WhatsApp (`wa.me`) / `mailto:` apply links
- Accent- and case-insensitive keyword search (pt-BR: "sao paulo" == "São Paulo")
- City filter (São Paulo, Rio de Janeiro, Belo Horizonte, Remoto) + date sort (newest default)
- Auto-expiry + **hard delete** at 14 days (the freshness promise — must be reliable)
- Mobile-first responsive layout; salary shown when present ("A combinar" otherwise)
- "Vaga revisada" trust badge; report-a-job link
- Privacy/terms/disclaimer pages (LGPD + "apenas meio de divulgação")

**Should have (competitive):**
- WhatsApp-native apply format normalization (E.164)
- Guaranteed-freshness marketing ("no ghost jobs"); pt-BR informal tone; share-to-WhatsApp
- Discreet donation button + AD placeholders

**Defer (v2+):**
- Per-job URLs + `JobPosting` JSON-LD + Google Jobs (high value, high complexity; conflicts with modal-only detail)
- Swipe/browse mode, map/geo, multi-city selection, light facets, saved searches/alerts
- **Anti-features to never add:** user accounts/login, public submission, ATS/resume, in-platform chat, featured/paid listings, aggregation/scraping of other boards.

### Architecture Approach

See [ARCHITECTURE.md](./ARCHITECTURE.md). A two-app split — Next.js on Vercel, FastAPI on Railway/Render — with Neon Postgres, Groq, and Turnstile. Layered FastAPI (`api/v1` routers → `services` → `crud` → `models`, with `schemas` for contracts, `tasks/` for the scheduler wired into lifespan, `core/` for config/security). Migrations from day one. The `jobs` table carries a `status` enum (`pending`/`published`), `created_at`/`expires_at` as `timestamptz` (expires = created + 14 days, computed in DB), a CHECK enforcing at least one contact, and indexes for the public list (partial on `status='published'`), city, trigram search, and `expires_at`. Add an explicit `invalid`/`needs_review` state (see pitfalls).

**Major components:**
1. **Next.js UI** — public grid/modal/search/filter/sort + admin login/paste-review; RSC for reads, client islands for interactivity.
2. **FastAPI API** — auth, jobs CRUD, extraction service, Turnstile verify, lifecycle scheduler; pt-BR errors; secrets server-only.
3. **Extraction service (Groq)** — strict schema, chunking, validation, correction retry, grounding check, contact normalization.
4. **Lifecycle scheduler** — idempotent, transactional 14-day hard delete.
5. **Data + external services** — Neon, Groq, Turnstile, config via env.

### Critical Pitfalls

Top issues from [PITFALLS.md](./PITFALLS.md):

1. **Retired Groq models (BLOCKING)** — Llama models shut down 2026-08-16. Store model as `GROQ_MODEL` env + fallback chain; surface a clear admin error; never hardcode.
2. **Hidden contact is not protected contact** — if contacts ship in the list/JSON payload, scrapers harvest everything. Keep contacts server-side; expose only via a Turnstile-verified, rate-limited reveal endpoint (turnstile server-side Siteverify mandatory; handle single-use/300s expiry).
3. **Silent truncation + hallucination in extraction** — large pastes silently drop jobs; the model invents company/salary. Chunk under TPM, detect `finish_reason == "length"`, compare `total_jobs_detected` vs array length, and run a grounding check against the source text.
4. **Groq free-tier rate limits (429)** — a single 12–15K-token paste can exceed the ~8K TPM limit. Cap/chunk input (≤4–6K tokens/call), throttle proactively, honor `retry-after`, and track daily budget.
5. **14-day hard-delete silently fails** — Vercel Hobby cron is once/day/UTC/no-retry; Render free sleeps after 15 min; Neon loses advisory locks on suspend; timezone bugs delete wrong rows. Use a **pure idempotent DB statement** in UTC, triggered externally with a `CRON_SECRET`, plus a catch-up reconciliation pass and a lock that survives Neon suspend.

Also critical: **Neon free-tier CU-hour burn** (persistent connection ≈180 CU-h/month vs 100 free → suspension ~day 16; use pooling/HTTP driver, monitor the usage graph), **Render/Railway "free" mismatch** (spin-down and credit exhaustion), **LGPD/WhatsApp personal-data republishing** (privacy notice + takedown path + lawyer review before launch), **scams reaching users** (scam-signal checklist, warning banner, report button, blocklist), and **dark-mode contrast** (measured: `#8b5cf6` on `#1a1025` fails AA body at 4.33:1 — use `#a78bfa` for text).

## Implications for Roadmap

Suggested phase structure (coarse granularity). The order follows the architecture build order and front-loads the highest-risk, highest-uncertainty work (extraction + infra) before UI polish.

### Phase 1: Foundation & Data Layer
**Rationale:** Everything depends on the schema, migrations, and a fast-failing config layer. Establishing the data model early locks the `status`/`expires_at`/contact-invariant contract that all other phases rely on.
**Delivers:** Neon provisioned; SQLAlchemy models + Alembic initial migration (`jobs` with CHECK + indexes, optional `admin_users`); FastAPI skeleton with validated settings (`pydantic-settings`), health endpoint, CORS, logging.
**Addresses:** Data model behind every feature in FEATURES.md.
**Avoids:** Neon CU-hour burn (decide pooled/HTTP driver + small pool now); wrong `expires_at` semantics (`timestamptz`, computed in DB).

### Phase 2: API Core — Jobs CRUD, Public Read & Admin Auth
**Rationale:** The public read API and admin auth are prerequisites for both the extraction pipeline and any frontend. Auth must exist before admin routes.
**Delivers:** Jobs CRUD; public list/detail (contacts **redacted/excluded**); admin login (JWT, hashed password), `require_admin` dependency; Pydantic request/response schemas.
**Uses:** SQLAlchemy async, Pydantic v2, PyJWT.
**Implements:** API layer routers/services/crud; auth guard.
**Avoids:** Admin API exposed without auth on every route; contacts in SSR payload (baked in from the start).

### Phase 3: LLM Extraction Pipeline (HIGH RISK — needs research-phase)
**Rationale:** The most fragile and highest-uncertainty component; it is the core automation and the quality gate. Must be built with the corrected models and validated against real pt-BR samples.
**Delivers:** `/admin/extract`; Groq strict structured-output extraction with `GROQ_MODEL` env + fallback chain; chunking under TPM; Pydantic validation + correction retry; grounding check; pt-BR contact parser/normalizer (E.164); input delimiters anti-injection; `needs_review`/`invalid` states; caps on text size and job count.
**Addresses:** "Admin paste → LLM extract → pending cards" requirement.
**Avoids:** Pitfalls 1–6 and 10 (retired model, no schema guarantee, truncation, hallucination, contact mangling, prompt injection, rate limits).
**Research flag:** Confirm live Groq model IDs, strict-mode support, current TPM/TPD limits on `/settings/limits`, and best chunking strategy.

### Phase 4: Contact Reveal & Anti-Spam (HIGH RISK — needs research-phase)
**Rationale:** The reveal is the scrape-sensitive surface and the payoff moment; it must be server-side gated from the outset (retrofitting is a rewrite).
**Delivers:** `POST /public/jobs/{id}/reveal-contact`; server-side Turnstile Siteverify (fresh single-use token, `remoteip` via trusted proxy headers, `timeout-or-duplicate` handling); per-IP rate limiting; `next-turnstile` widget.
**Implements:** Turnstile pattern (server verify).
**Avoids:** Pitfall 7 (cosmetic hiding) and client-side-only validation; also protects admin login against credential stuffing (placement decision).

### Phase 5: Lifecycle — 14-Day Expiry & Hard Delete
**Rationale:** The freshness promise is a differentiator; the failure modes (sleeping host, timezone, missed cron) are well understood but easy to get wrong. Design idempotency + external trigger together.
**Delivers:** Idempotent `DELETE ... WHERE status='published' AND expires_at <= now()` in UTC; `CRON_SECRET`-protected endpoint or external scheduler; catch-up/reconciliation pass; deterministic tests (future-dated job NOT deleted; duplicate invocation safe).
**Avoids:** Pitfall 11 (Vercel Hobby/Render/Neon lock/timezone traps).
**Research flag:** Choose the external scheduler (hosted cron pinger vs GitHub Actions with heartbeat) and decide whether `pending` jobs also expire.

### Phase 6: Public Frontend — Board, Modal, Search/Filter/Sort
**Rationale:** Depends on Phase 2 (public API) and Phase 4 (reveal). This is the user-facing core loop.
**Delivers:** Responsive mobile-first grid; job card + accessible detail modal (dvh/svh, scroll-lock, focus-trap, safe-area); accent-insensitive search; city chips + result count; date sort; one-tap reveal; WhatsApp/email CTAs; empty/loading/error states; dark minimal-purple theme with WCAG-AA-compliant contrast.
**Addresses:** P1 features from FEATURES.md and pt-BR/mobile UX specifics.
**Avoids:** Contrast failures (`#a78bfa` for text), filters resetting (URL-synced state), `100vh` modal bugs, fetch-all client filtering.

### Phase 7: Admin Frontend — Paste, Review & Edit
**Rationale:** Completes the ingestion loop after the API and extraction exist.
**Delivers:** Protected `/admin`; paste + extract UI (progress/partial states); review queue (pending); approve/edit-by-ID/delete; source-chunk shown beside parsed fields (grounding aid); contact editing; approval audit logging.
**Addresses:** "Admin reviews: approve, edit by ID, delete" + "approved → published".
**Avoids:** Auto-publishing, rubber-stamping (surface scam checklist + grounding side-by-side).

### Phase 8: Trust, Legal & Polish
**Rationale:** Trust and legal posture are product-critical, not cosmetic, but depend on the board existing. Must be complete before public launch.
**Delivers:** Scam-signal checklist at review; persistent per-listing warning banner; report-a-job (mailto/WhatsApp → Turnstile-protected later); blocklist enforcement; privacy notice + takedown path (LGPD); "somos apenas meio de divulgação" disclaimer; donation button (`#facc15`); AD placeholders.
**Avoids:** Pitfalls 8 & 9 (LGPD republishing liability, scams reaching users).

### Phase 9: Deployment & Infrastructure Wiring
**Rationale:** Cross-cutting finalization; validates the "near-zero cost" assumption which the research shows is only partially true.
**Delivers:** Vercel (frontend) + Railway/Render (backend) deploy; CORS locked to frontend origin; env/secrets on both platforms; Neon pooled connection; realistic cost plan; cold-start UX documented; public read path fast when backend asleep.
**Avoids:** Pitfall 12 & 13 (Neon suspension, free-host mismatch).

### Phase Ordering Rationale

- **Data model first** (Phase 1) because the contact-invariant, status enum, and `expires_at` semantics are referenced by every later phase.
- **Auth + public API before extraction/UI:** the extraction endpoint and both frontends depend on them.
- **Extraction and reveal are front-loaded as "risky"** (Phases 3–4) — they carry the most uncertainty (model churn, rate limits, anti-scraping correctness) and retrofitting them is expensive.
- **Lifecycle (Phase 5)** is isolated because its pitfalls are operational (scheduling/timezone/locks) and its tests are self-contained.
- **Frontends (Phases 6–7)** follow once stable APIs exist; public before admin so the core loop can be smoke-tested end-to-end.
- **Trust/legal (Phase 8) before launch** to avoid republishing-liability exposure on day one.
- This ordering directly mirrors the architecture build order and the pitfall-to-phase mapping.

### Research Flags

Phases likely needing deeper research during planning (`/gsd-research-phase`):
- **Phase 3 (LLM Extraction):** Verify live Groq model IDs, strict structured-output support, exact TPM/TPD limits, chunking strategy, and pt-BR contact parsing edge cases.
- **Phase 4 (Contact Reveal/Anti-Spam):** Turnstile Siteverify details (token lifetime/single-use, `timeout-or-duplicate`, proxy IP extraction, test keys), rate-limiting approach.
- **Phase 5 (Lifecycle/Infra):** Choose external scheduler and confirm idempotency/lock approach under Neon suspend.
- **Phase 9 (Infrastructure):** Confirm current Neon CU-hour/pooling behavior and Render/Railway free-tier mechanics empirically.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation/Data):** Well-documented SQLAlchemy/Alembic/FastAPI patterns.
- **Phase 2 (API Core/Auth):** JWT + CRUD are established patterns.
- **Phase 6 (Public Frontend):** Standard Next.js App Router + Tailwind patterns (though a UI-phase/design pass is warranted for the theme).
- **Phase 7 (Admin Frontend):** Standard forms/tables.
- **Phase 8 (Trust/Legal):** Content/policy work; legal review is a human task, not code research.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified against official registries; **but STACK.md's LLM model choice is invalidated by PITFALLS.md** (retired 2026-08-16). Libraries and structure are solid. |
| Features | MEDIUM | Domain patterns well-evidenced from live competitor analysis; NQU-specific tradeoffs reasoned, not field-tested. Strong on table-stakes; differentiator durability unproven. |
| Architecture | HIGH | Standard, well-understood two-app split with verified patterns (layering, migrations, indexes, server-side verify). |
| Pitfalls | MEDIUM-HIGH | Core platform facts verified against official docs; some project-specific claims (Neon idle-connection behavior, exact free limits) flagged for empirical verification. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Groq model decision:** PROJECT.md still fixes retired Llama models. Update the constraint to `openai/gpt-oss-20b`/`120b` (or `qwen/qwen3.8-27b`) and adopt `GROQ_MODEL` + fallback. Resolve before Phase 3 planning.
- **Turnstile placement:** FEATURES.md flags an open question — with no public write form in MVP, Turnstile is best placed on the **admin login** and/or the **report-a-job** endpoint, in addition to contact reveal. Decide at Phase 4.
- **SEO vs modal-only detail:** Deferred to v1.x, but the modal architecture conflicts with `JobPosting` JSON-LD (requires a dedicated single-job URL). Decide explicitly whether SEO is MVP or v1.x; if later, plan Next.js intercepting/parallel routes early.
- **Exact Groq rate limits & Neon CU-hour behavior:** Limits change and Neon idle-connection behavior is only MEDIUM confidence — verify empirically before/at launch.
- **LGPD legal basis:** Requires an actual Brazilian lawyer's review before launch; the hard-14-day-delete retention is the friendly narrative but does not by itself establish a legal basis.
- **`pending` job expiry policy:** Undecided — must specify whether unapproved jobs also hard-delete (otherwise the table grows unbounded).
- **Admin auth model:** Decide stateless single-password JWT (recommended for solo master) vs a DB `admin_users` table.

## Sources

Aggregated from the four research files. See individual files for full citations.

### Primary (HIGH confidence)
- FastAPI, SQLAlchemy 2.0, Alembic, asyncpg, Pydantic v2, Groq Python SDK, Next.js, Tailwind v4, Cloudflare Turnstile, Neon Postgres, Vercel/Railway/Render official docs (STACK.md)
- Google Search Central — `JobPosting` structured data (single-page rule, `validThrough`) (FEATURES.md)
- Live competitor sites: EmpregoDaqui, BrVagas, Meu Emprego, BuscarVagas, Chance na Vaga; InfoJobs/Trabalha Brasil (FEATURES.md)
- Groq Model Deprecation, Structured Outputs, and Rate Limits docs; Neon compute-lifecycle/pooling/free-plan docs; Vercel Cron docs; Render free docs; Railway free-trial docs; Turnstile server-side validation docs (PITFALLS.md)
- FBI/Europol/IC3 job-scam advisories; Febraban false-job-scam alert; gov.br LGPD data types (FEATURES.md, PITFALLS.md)
- WebAIM / MDN WCAG contrast thresholds (PITFALLS.md)

### Secondary (MEDIUM confidence)
- Cavuno / Job Boardly feature taxonomy; LogRocket/Algolia/Pencil & Paper mobile filter UX; UX case studies on verified badges (FEATURES.md)
- Microsoft Partner Solutions structured-output extraction best practices; arXiv SafePassage grounding-check research (PITFALLS.md)
- Jusbrasil/STJ jurisprudence on WhatsApp communication secrecy (PITFALLS.md)

### Tertiary (LOW confidence — verify)
- Neon idle-in-transaction compute behavior (MEDIUM, flagged to verify empirically)
- Exact current Groq TPM/TPD/RPD figures (limits change; verify live)

---
*Research completed: 2026-10-13*
*Ready for roadmap: yes*
