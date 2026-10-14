<!-- GSD:project-start source:PROJECT.md -->
## Project

**NQU — NaoQueroUsar**

Plataforma pública de busca de emprego cujo diferencial é eliminar a burocracia de cadastro: qualquer pessoa vê as vagas e o contato **sem criar conta, sem login e sem etapas intermediárias**. Um board enxuto, dark mode e mobile-first, curado manualmente por um único administrador (o master), que transforma textos brutos de grupos de vagas em cards estruturados.

Slogan: "Procurar um emprego, não deve dar trabalho"

**Core Value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

### Constraints

- **Tech stack — Frontend:** Next.js 15 (App Router) + Tailwind CSS + dark mode — decisão fixada pelo usuário
- **Tech stack — Backend:** FastAPI (Python) — decisão fixada pelo usuário
- **Banco:** Neon (Postgres gratuito) — decisão fixada pelo usuário
- **LLM de extração:** Groq, modelo gratuito — `openai/gpt-oss-20b` (padrão) com `openai/gpt-oss-120b` como fallback, via env `GROQ_MODEL` — *corrigido pós-pesquisa: `llama-3.1-8b-instant`/`llama-3.3-70b` foram aposentados em 2026-08-16*
- **Anti-spam:** Cloudflare Turnstile (gratuito) — decisão fixada pelo usuário
- **Deploy:** Vercel (frontend) + local inicialmente; depois Railway/Render (backend) — decisão fixada pelo usuário
- **Idioma/Locale:** Português (Brasil), datas e textos em pt-BR
- **Design:** dark mode minimalista; roxo principal (#8b5cf6 / #a78bfa); fundos escuros (#0f0a1a / #1a1025); botão Doações amarelo (#facc15) discreto
- **Operação:** admin único (master); sem multiusuário
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Executive Summary
## Recommended Stack
### Core Technologies (Fixed - Validated)
| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Next.js (App Router) | 16.4.0 | Frontend framework | Fixed by user; v15+ App Router is current standard (v16.4.0 latest). Server Components fit public read-only pages well. | HIGH |
| Tailwind CSS | 4.3.3 | Styling | Fixed by user; v4 is current (CSS-first config, better performance). Pairs well with dark mode via CSS variables. | HIGH |
| FastAPI | 0.143.0 | Backend API | Fixed by user; current stable. Great for async, OpenAPI, Pydantic v2 integration. | HIGH |
| Neon (Postgres) | Managed (Free) | Database | Fixed by user; serverless Postgres with branching. Works with asyncpg/psycopg. | HIGH |
| Groq | API (Free tier) | LLM extraction | Fixed by user; llama-3.1-8b-instant/llama-3.3-70b appropriate for structured extraction at low cost. | HIGH |
| Cloudflare Turnstile | Free | Anti-spam | Fixed by user; simple widget + server verify; good for public forms (admin paste). | HIGH |
| Vercel + (Railway/Render) | Managed | Deploy | Fixed by user; split is sensible (Vercel for Next, backend on Railway/Render for long-running jobs like cleanup). | HIGH |
### Backend - Supporting Libraries (Python)
| Library | Version | Purpose | Why | Notes | Confidence |
|---------|---------|---------|-----|-------|------------|
| SQLAlchemy | 2.1.4 | ORM (async) | Industry standard for FastAPI; 2.1.x is current stable (2026). Full async support with `async_sessionmaker`. | Use 2.0+ style (declarative `Mapped[...]`, `mapped_column`). Avoid legacy 1.x patterns. | HIGH |
| Alembic | 1.20.0 | Migrations | Standard companion to SQLAlchemy; tracks schema changes. | Configure to work with async engine (use `alembic` env with `run_migrations_async` or sync wrapper). | HIGH |
| asyncpg | 0.32.0 | Async Postgres driver | Fast, widely used with SQLAlchemy 2.0 async + Neon (Postgres wire compatible). | Preferred for pure async stack; connection string from Neon (pooled). | HIGH |
| psycopg (v3) | 3.3.6 | Postgres driver (sync/alt) | Also fine; asyncpg is typically faster for high-throughput async. Not needed if using asyncpg. | Optional; include only if you need psycopg-specific features. | MEDIUM |
| Pydantic | 2.14.1 | Validation/serialization | Core to FastAPI; v2 is current. Use for request/response models + extraction schema. | Leverage `BaseModel`, `Field`, validators. For LLM output, use `model_validate_json` + structured schema. | HIGH |
| groq (Python SDK) | 1.7.0 | Groq API client | Official SDK; current. Supports chat completions, JSON mode/structured outputs. | Use with `response_format={"type":"json_object"}` or `structured_outputs` depending on model; test with chosen model. | HIGH |
| httpx | 0.28.1 | HTTP client | Used by groq SDK + general HTTP; 0.28.x is current. | For external calls (Turnstile verify). Also useful for testing. | HIGH |
| uvicorn | 0.54.0 | ASGI server | Standard for FastAPI; 0.54.x current. | Use `--reload` locally; gunicorn+uvicorn workers in prod if needed (Railway/Render). | HIGH |
| python-dotenv | 1.2.4 | Env loading | Simple for local dev (`.env`). | Never commit secrets; use platform env vars in Vercel/Railway/Render. | HIGH |
| PyJWT | 2.15.1 | JWT for admin auth | For single-master password-based login → JWT (or session). Secure, simple. | For "admin solo acessa área protegida por senha (via .env)/JWT" - generate JWT on login; httpOnly cookie or Authorization header. | HIGH |
| email-validator | 2.3.x (via FastAPI deps) | Email validation | Pydantic v2 can use email-validator. | If storing contact_email, validate format. | MEDIUM |
### Frontend - Supporting Libraries (TypeScript/Next.js)
| Library | Version | Purpose | Why | Notes | Confidence |
|---------|---------|---------|-----|-------|------------|
| react | 19.3.0 | Core | Bundled with Next 16; current stable. | Use Server Components by default; Client Components only where needed (modal, "mostrar contato", Turnstile widget). | HIGH |
| react-dom | 19.3.0 | DOM renderer | Matched to React 19.3.0. | Standard. | HIGH |
| TypeScript | 7.0.2 | Type safety | Current (v7). Next 16 works well with TS 5.x+; 7.x is latest. | Strict mode recommended. | HIGH |
| zod | 4.6.7 | Schema validation (client + shared types) | Excellent for form validation and runtime validation of API responses. | Can share extraction/job schemas between FE/BE conceptually; keep BE as source of truth. | HIGH |
| next-turnstile | 1.0.7 | Cloudflare Turnstile React component | Lightweight wrapper for Turnstile widget in Next.js App Router. | Works with "use client". Verify token server-side via `/siteverify`. | HIGH |
| @types/node | 26.6.5 | Node types | Current; matches Node runtime expectations. | For API routes/server code. | HIGH |
### Development & Testing Tools
| Tool | Version | Purpose | Why | Notes | Confidence |
|------|---------|---------|-----|-------|------------|
| pytest | 9.1.1 | Python testing | Standard for FastAPI; async support via pytest-asyncio. | Test extraction pipeline, admin endpoints, expiry logic. | HIGH |
| pytest-asyncio | (latest compatible) | Async test support | Needed for async DB tests. | Configure in pytest.ini; use `@pytest.mark.asyncio`. | HIGH |
| httpx (TestClient) | 0.28.1 | API testing | FastAPI TestClient uses httpx; for integration tests. | Use `TestClient(app)` for sync-like tests or `AsyncClient` with httpx.ASGITransport. | HIGH |
| Vitest | 5.0.4 | Unit/component tests (FE) | Fast, Vite-based; good for utils, hooks, schema validation. | Pair with @testing-library/react if testing components later. | HIGH |
| @playwright/test | 1.64.0 | E2E tests | Cross-browser, reliable; good for public flows (search/filter/modal/reveal contact) and admin flow. | Run in CI later; focus on critical user paths. | HIGH |
## Domain-Specific Recommendations
### 1) FastAPI Project Structure
- **Pattern:** Domain-driven (routers, schemas, services, models, core). Keep `app/` with `api/v1/`, `models/`, `schemas/`, `crud/` or `repositories/`, `services/` (LLM extraction), `core/` (config, security).
- **Async first:** Use `AsyncSession` from SQLAlchemy; `lifespan` for startup/shutdown.
- **Pydantic v2:** Split `schemas/` into request/response; use `ConfigDict(from_attributes=True)` for ORM mapping where needed.
- **Confidence:** HIGH (standard FastAPI best practice 2025).
### 2) Database: Neon + SQLAlchemy 2.x Async + Alembic
- **Engine:** `create_async_engine(url, echo=False, pool_pre_ping=True)` with `asyncpg` driver (`postgresql+asyncpg://...`).
- **Sessions:** `async_sessionmaker` with `expire_on_commit=False`.
- **Models:** Use `Mapped`, `mapped_column`, `DeclarativeBase`. Indexes: consider on `status`, `created_at`, `expires_at`, `city` (search/filter common).
- **Migrations:** Alembic autogenerate with proper `compare_type=True` if needed. Store migrations in `alembic/versions/`.
- **Neon:** Use pooled connection string for web (PgBouncer) to avoid connection limits on free tier; direct for migrations if preferred.
- **Confidence:** HIGH.
### 3) LLM Extraction (Groq) - Structured Output
- **Models:** `llama-3.1-8b-instant` (faster/cheaper) or `llama-3.3-70b` (better quality). Test with real WhatsApp/Telegram samples.
- **Approach:** Define Pydantic schema for extracted job (all required/conditional fields). Use Groq chat completions with `response_format` (JSON object mode) and strict instruction to return array of jobs. Validate with Pydantic after parse.
- **Prompting:** Include pt-BR context, rules (at least one contact required, dates, 14-day expiry semantics), handle multiple jobs per blob, normalize city names (map to allowed: São Paulo/Rio de Janeiro/Belo Horizonte/Remoto).
- **Error handling:** Retry with backoff on parse failures; fall back to smaller chunks if blob large.
- **Confidence:** HIGH (Groq SDK 1.7.0 supports JSON mode; structured extraction pattern is standard).
### 4) Next.js 15 Data Fetching
- **Public pages (home, cards, modal data):** Prefer Server Components for read-only data (fetch from backend API or if colocated, can call directly). Keep secrets server-side.
- **Client interactions:** Use Client Components for "Mostrar contato" (reveal), modal open/close, search/filter UI state, Turnstile widget.
- **Forms (admin paste/review/edit):** Can use Server Actions or client `fetch` to backend; both fine. With admin auth, POST to FastAPI with JWT.
- **Caching:** For public jobs (published, not expired), consider ISR or just dynamic fetch; volume 100–500 jobs/month means fresh data is easy (no heavy caching needed). If using Vercel, `fetch` with `cache: 'no-store'` for dynamic admin views.
- **Confidence:** HIGH.
### 5) Tailwind + Dark Mode (Dark Minimal Purple Theme)
- **Strategy:** Tailwind v4 uses CSS variables and `@theme`. Implement dark mode via `dark` class on `<html>` (class strategy). Define CSS variables for colors: purple primary `--color-primary-500: #8b5cf6`, `--color-primary-400: #a78bfa`, backgrounds `--bg-dark-900: #0f0a1a`, `--bg-dark-800: #1a1025`, accent yellow `--color-accent-yellow: #facc15` (discreet).
- **Doações button:** Yellow `#facc15`, subtle styling, hover state only (no focus ring overdone). Position top-right.
- **Mobile-first:** Use responsive grid for cards; modal mobile-friendly.
- **Confidence:** HIGH (Tailwind v4 docs current).
### 6) Turnstile Integration
- **Client:** `next-turnstile` component renders widget; get `token` on form submit (admin paste form).
- **Server (FastAPI):** Verify token against `https://challenges.cloudflare.com/turnstile/v0/siteverify` with `secret_key`, `response` (token), `remoteip` (optional). Return success/failure. Reject if invalid.
- **Env:** `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`. Frontend needs site key (public), backend secret (private).
- **Confidence:** HIGH.
### 7) Scheduling for 14-Day Expiry (Hard Delete)
- **Requirement:** "Vagas expiram automaticamente após 14 dias e são apagadas do banco (hard delete)". `expires_at = created_at + 14 days`. Job runs periodically to `DELETE FROM jobs WHERE status='expired' OR expires_at < now()` (or just check expires_at; also can mark expired first, then delete). Since hard delete, do both as needed.
- **Options given deploy split (Vercel + Railway/Render):**
- **Recommendation:** Use `APScheduler` with a daily (or hourly) job in the FastAPI process (BackgroundScheduler) when running on Railway/Render. For local dev, also fine. Avoid relying on Vercel cron for backend unless you expose a secured endpoint.
- **Library:** APScheduler (current: check via PyPI - add if needed; not in initial list; recommend adding). Also consider `python-crontab` unnecessary.
- **Confidence:** MEDIUM-HIGH.
### 8) Env/Secrets Across Vercel + Railway/Render
- **Frontend (Vercel):** Public vars: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`. Never put secrets here.
- **Backend (Railway/Render):** Private: `DATABASE_URL` (Neon pooled), `GROQ_API_KEY`, `TURNSTILE_SECRET_KEY`, `ADMIN_PASSWORD_HASH` (or plain in env per req? "password via .env"), `JWT_SECRET`, `ALLOWED_ORIGINS` (Vercel domain). 
- **Local:** `.env` files (gitignored). Use `python-dotenv` in dev only.
- **Security:** Hash admin password (bcrypt/argon2). Rotate JWT_SECRET if compromised. Validate ALLOWED_ORIGINS to prevent CORS abuse.
- **Libraries:** `passlib[bcrypt]` or `bcrypt` for password hashing (recommend passlib for flexibility).
- **Confidence:** HIGH.
## Installation (Concrete)
### Backend (requirements.txt)
### Frontend (package.json deps)
## Alternatives Considered
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Async driver | asyncpg 0.32.0 | psycopg (async) 3.3.6 | Both fine; asyncpg is very common with Neon/SQLAlchemy async and performs well. psycopg async is also solid; no strong reason to switch. |
| Migrations | Alembic 1.20.0 | yoyo-migrations | Alembic integrates better with SQLAlchemy metadata/autogenerate and is standard for FastAPI. |
| LLM structured | JSON mode + Pydantic | OpenAI-style function/tool calling | Groq models support JSON mode reliably; simpler than tool schema for this flat extraction. Function calling not strictly needed. |
| Scheduling | APScheduler (in-process) | Celery + Redis | Overkill for 100-500 jobs/month and single job (expiry). Celery adds infra (Redis) and complexity; not needed on free tiers. |
| Auth | PyJWT + password hash | FastAPI Users | FastAPI Users is heavy for single-master. Simple JWT + env password hash is sufficient and minimal. |
| FE validation | Zod 4.6.7 | Yup, Valibot | Zod v4 is current, TypeScript-first, good DX. Valibot is lighter but Zod fits well. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| SQLAlchemy 1.x (legacy API) | Incompatible with modern async patterns; 2.0+ style is the way forward and FastAPI docs emphasize 2.0. | SQLAlchemy 2.1.4 with `Mapped[...]` style. |
| Pydantic v1 | Deprecated; FastAPI 0.143+ works best with Pydantic v2. | Pydantic 2.14.1. |
| Using sync SQLAlchemy session in async endpoints | Blocks event loop; will hurt performance under load and is easy to misuse. | `AsyncSession` + `asyncpg`. |
| Storing plain admin password in code | Security risk. | Hash with passlib/bcrypt and store hash in env (or secret manager). |
| Client-side only contact reveal with no consideration | Already specified client-side (acceptable per requirements), but don't expose in HTML source beyond click handler. | Current approach is fine per spec ("revelado no clique client-side"). |
| Hardcoding cities beyond initial set | Keep to: São Paulo, Rio de Janeiro, Belo Horizonte, Remoto (as specified). Don't over-generalize early. | Enforce in validation/schema. |
## Version Compatibility Notes
| Pair | Compatibility | Notes |
|------|---------------|-------|
| FastAPI 0.143.0 + Pydantic 2.14.1 | OK | FastAPI 0.143 supports Pydantic v2; ensure no v1 remnants. |
| SQLAlchemy 2.1.4 + asyncpg 0.32.0 + Alembic 1.20.0 | OK | Verified compatible set for async stack. |
| Next.js 16.4.0 + React 19.3.0 + TypeScript 7.0.2 | OK | Next 16 supports React 19; TS 7.x is current. |
| Tailwind 4.3.3 + Next 16 | OK | Tailwind v4 works with Next.js (use @import "tailwindcss" and CSS-based config). |
| Groq SDK 1.7.0 + httpx 0.28.1 | OK | SDK uses httpx; 0.28.x is supported. |
## Implementation Checklist (Quick)
- [ ] Backend: `alembic init alembic`, configure async env, create Job model with required fields + indexes.
- [ ] Extraction: Pydantic schema for Job extraction; Groq JSON mode; validation + normalization (cities).
- [ ] Admin: password login → JWT; protected routes for paste/review/edit/delete.
- [ ] Public: responsive cards, modal, search, city filter, date sort; contact reveal on click.
- [ ] Expiry: APScheduler job for hard delete of expired (>14 days) records.
- [ ] Turnstile: widget + server verify on admin paste (and/or other sensitive actions).
- [ ] Deploy: set env vars on Vercel and Railway/Render; CORS configured.
- [ ] Tests: unit tests for extraction/validation, API tests, FE unit + E2E smoke.
## Sources
- [FastAPI](https://fastapi.tiangolo.com/) - Official docs (current). PyPI: fastapi 0.143.0 (verified 2026-10-13).
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/) - Official docs; 2.1.4 current (PyPI verified).
- [Alembic](https://alembic.sqlalchemy.org/) - Migrations; 1.20.0 current.
- [asyncpg](https://magicstack.github.io/asyncpg/) - Driver; 0.32.0 current.
- [Pydantic v2](https://docs.pydantic.dev/latest/) - 2.14.1 current.
- [Groq Python SDK](https://console.groq.com/docs/sdk) - 1.7.0 current.
- [Next.js](https://nextjs.org/docs) - 16.4.0 current (npm).
- [Tailwind CSS v4](https://tailwindcss.com/docs) - 4.3.3 current.
- [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/) - Official integration docs.
- [Neon Postgres](https://neon.tech/docs) - Serverless Postgres docs.
- [Vercel/Railway/Render](https://vercel.com/docs, https://docs.railway.com/, https://render.com/docs) - Deploy docs.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
