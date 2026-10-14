# Architecture Research: NQU (Não Quero Usar) — Job Board with LLM Extraction

**Domain:** Brazilian public job board (content aggregation + manual curation)
**Researched:** 2026-10-13
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    Client Layer                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Next.js 15 (App Router) — Vercel                                                      │  │
│  │ • Public: listing/grid, detail modal, search/city/filter/sort, "reveal contact"       │  │
│  │ • Admin: protected routes (login), paste+extract, review queue (pending), edit/delete  │  │
│  │ • Turnstile integration (client token)                                                │  │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                          │ HTTPS REST                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                    API Layer                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ FastAPI (Python) — Railway/Render (local first)                                       │  │
│  │ • Auth (admin), Jobs CRUD, Extraction (Groq), Turnstile verify, CORS, validation     │  │
│  │ • Background scheduler (APScheduler) for 14d expiry + HARD DELETE                      │  │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                          │ SQL + HTTP                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                  Data & External Services                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────────┐  │
│  │ Neon Postgres│  │ Groq API     │  │ Cloudflare   │  │ Observability/Config                 │  │
│  │ (serverless) │  │ (llama-3.1-8b│  │ Turnstile    │  │ .env (secrets), structured logging   │  │
│  │              │  │  -instant or │  │ (server-side)│  │ (uvicorn+fastapi)                    │  │
│  │              │  │  llama-3.3-70b)│  │             │  │                                      │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implementation Notes |
|-----------|----------------|---------------------|
| **Next.js 15 (App Router)** | Public UI (list/grid, modal, search/filter/sort), admin UI (paste+extract, review), client-side "reveal contact", Turnstile widget. | Server Components for read-heavy public pages; Client Components only where interactivity (modal, reveal, form state) needed. Route handlers optional if calling same-origin API; prefer typed fetch client. |
| **FastAPI (API)** | REST API, request validation (Pydantic v2), auth (admin JWT or env-based login), CORS, Turnstile server verification, Groq integration, DB access (SQLAlchemy 2.x/async or psycopg3), scheduler for lifecycle. | Keep thin routers, service layer for domain logic (extraction, lifecycle), repository/CRUD for jobs. Return pt-BR errors. Never expose secrets to frontend. |
| **Neon Postgres (serverless)** | Primary store for jobs + admin/auth metadata. Enforces constraints, indexes for search/filter/sort. | Use migrations (Alembic). Connection pooling tuned for serverless (pgbouncer-friendly). Soft-state not required; hard deletes on expiry. |
| **Groq (LLM)** | Extract structured array of jobs from raw pasted text per contract (schema + constraints). | Deterministic-ish via temperature=0 (or low), strict JSON schema in prompt, retry with correction prompt on malformed output. Cost/latency: 8b instant preferred for volume 100–500 jobs/month. |
| **Cloudflare Turnstile** | Anti-spam for public actions that reveal contact. Verification happens server-side. | Widget rendered on client; `cf-turnstile-response` token sent to backend; backend calls Turnstile verify endpoint with secret. Do not trust client-only checks. |
| **Scheduler (APScheduler)** | Runs 14-day expiry + HARD DELETE. | In-process APScheduler (BackgroundScheduler) with a lock/heartbeat (single-instance safe in typical Railway/Render single process; or use a scheduled job/cron if scaled). Must be idempotent and transactional. |
| **Config (.env)** | Secrets/keys: `ADMIN_PASSWORD` or JWT secret, `GROQ_API_KEY`, `TURNSTILE_SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `ENV`. | Never commit .env. Vercel/Railway/Render env vars. Validate on startup. |

## Recommended Project Structure

```
C:\Users\AndreC\Desktop\Teste\NaoQueroUsar\
├── frontend/                # Next.js 15 (App Router)
│   ├── app/
│   │   ├── (public)/        # list, [city?], job modal via parallel route or client
│   │   ├── admin/           # login + review (protected)
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/              # shadcn-like minimal (dark mode)
│   │   ├── job-card.tsx
│   │   ├── job-modal.tsx
│   │   ├── search-bar.tsx
│   │   ├── city-filter.tsx
│   │   ├── turnstile.tsx
│   │   └── admin/
│   ├── lib/
│   │   ├── api-client.ts    # typed fetch to backend
│   │   ├── types.ts         # shared types (Job)
│   │   └── utils.ts
│   └── package.json
├── backend/                 # FastAPI
│   ├── app/
│   │   ├── api/v1/          # routers: auth, jobs, admin, extract
│   │   ├── core/            # config, security, logging, cors
│   │   ├── schemas/         # Pydantic v2 (JobCreate/Update/Out, ExtractRequest/Response)
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # groq_extractor, lifecycle, turnstile
│   │   ├── crud/            # db ops
│   │   ├── deps.py          # dependencies (db, auth)
│   │   ├── tasks/           # scheduler (lifecycle)
│   │   └── main.py          # app factory + lifespan (start scheduler)
│   ├── alembic/             # migrations
│   ├── pyproject.toml (or requirements.txt)
│   └── Dockerfile (optional)
├── .planning/
│   └── research/            # research outputs
└── README.md
```

### Structure Rationale

- **Separation of concerns:** `frontend/` (UI) and `backend/` (API/domain) as separate apps — matches Vercel (frontend) + Railway/Render (backend). Clean deploy boundaries and CORS.
- **App Router (Next.js 15):** Colocation of routes, server actions not strictly needed (REST to FastAPI), but RSC for public read paths reduces JS. 
- **Layered FastAPI:** `api/routers` (transport), `services` (domain: extraction + lifecycle), `crud` (persistence), `schemas` (contracts), `models` (ORM). Prevents fat routers and eases testing.
- **Lifecycle in `tasks/` + lifespan:** Scheduler starts on app boot (single process). Idempotent hard-delete is critical (see PITFALLS later); keep in service with DB transactions.
- **Migrations first:** Alembic from day one (Neon schema evolution). 

## Architectural Patterns

### Pattern 1: Thin vertical slices with service layer
- **What:** Routers call services; services orchestrate CRUD + external calls (Groq, Turnstile). 
- **When:** API has mixed concerns (extraction + auth + lifecycle). 
- **Trade-offs:** +testable, -slightly more files. Worth it for extraction/error handling.
- **Example (extraction flow):**
```python
# api/v1/extract.py -> services/groq_extractor.extract_jobs(text) -> crud.jobs.bulk_create_pending(...)
```

### Pattern 2: Schema-first contracts (Pydantic v2 + shared TS types)
- **What:** Single source of truth for Job shape at API boundary; mirror in `frontend/lib/types.ts`. 
- **When:** Prevent drift between LLM output, DB model, API, UI.
- **Trade-offs:** +safety, -duplication small. 
- **Example:** `JobBase` (title/company/activities/requirements/salary/benefits/city/contact_email/contact_phone), `JobOut` includes `id, status, created_at, expires_at`.

### Pattern 3: Idempotent background jobs + transactional hard deletes
- **What:** Lifecycle job runs on interval (e.g. every 5–15 min) or hourly; finds jobs with `expires_at <= now()` and `status in (published, pending?)` and deletes in transaction (or with SELECT ... FOR UPDATE SKIP LOCKED). Track last run, use a guard (max rows). 
- **When:** 14d expiry + hard delete required; single-writer process typical. 
- **Trade-offs:** +deterministic, -needs care if scaled to multiple workers (use advisory lock or external cron). 
- **Example:** `DELETE FROM jobs WHERE id = ANY(:ids::uuid[]) AND expires_at <= NOW() RETURNING id;` inside transaction.

### Pattern 4: Server-side Turnstile verification
- **What:** Client gets token from widget; POST to `/api/v1/public/reveal-contact/verify` (or include in action) with `{ job_id, token }`; backend `POST https://challenges.cloudflare.com/turnstile/v0/siteverify` with secret+response+remoteip; allow reveal only if success. 
- **When:** Contact reveal is the scraping-sensitive surface. 
- **Trade-offs:** +prevents naive bots, -small latency/cost free. 

### Pattern 5: Strict LLM JSON extraction with repair
- **What:** Prompt returns a JSON array only (no prose). Validate against schema; if parse/validation fails, send correction prompt with error + raw text + required schema; retry once. Reject if still invalid. Enforce “at least one contact” per job. 
- **When:** Unstructured pt-BR text from groups. 
- **Trade-offs:** +robustness, +predictable, -extra call on failure (rare). 

## Data Flow

### Key End-to-End Flows

1. **Paste → Extraction → Pending**
```
Admin pastes text (UI)
  ↓ POST /api/v1/admin/extract { text }
FastAPI: validate size, call Groq with strict prompt -> parse JSON array
  ↓ validate each job (required fields, contact rule, lengths)
  ↓ bulk_insert_pending -> jobs with status='pending', created_at=now(), expires_at=now()+14d
  ↓ return list of created pending jobs (with ids)
UI shows review queue
```

2. **Review → Publish**
```
Admin reviews pending: approve/edit/delete
  ↓ PATCH /api/v1/admin/jobs/{id} { status: 'published' } or PUT update
DB update; published jobs appear on public list
```

3. **Public Browse**
```
Anon GET /api/v1/public/jobs?search=&city=&sort=desc&page=&limit=
DB query with ILIKE (search), city filter, ORDER BY created_at DESC
Return published jobs (contacts redacted in list; full redacted until reveal)
```

4. **Reveal Contact (behind Turnstile)**
```
User clicks "Mostrar contato" on modal -> client shows Turnstile, gets token
  ↓ POST /api/v1/public/jobs/{id}/reveal-contact { cf_token }
Backend: verify Turnstile (server) with remote IP
  if ok -> return { contact_email, contact_phone } (or masked logic if desired)
Client displays contacts (client-side only)
```

5. **Lifecycle: Expiry → Hard Delete (scheduled)**
```
APScheduler job runs every 5–10 min (or hourly). Query:
  SELECT id FROM jobs WHERE expires_at <= NOW() AND deleted_at IS NULL? 
  but hard delete required -> DELETE FROM jobs WHERE expires_at <= NOW() 
    AND (status='published' OR status='pending')  -- be explicit
  in transaction; log count; commit. Idempotent (no-op if none).
On next run same rows gone.
```

Notes: `expires_at = created_at + 14 days` (computed at insert). Do not rely on client time.

## Database Schema

### Tables

#### `jobs`
Core entity. Use UUID (or bigserial) PK. Status enum. Timestamps with timezone. 

```sql
CREATE TYPE job_status AS ENUM ('pending', 'published');

CREATE TABLE jobs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title             VARCHAR(200) NOT NULL CHECK (char_length(trim(title)) > 0),
  company           VARCHAR(150),
  activities        TEXT,                -- "início das activities (expansível)" in UI
  requirements      TEXT,
  salary            VARCHAR(80),         -- keep string (pt-BR ranges)
  benefits          VARCHAR(255),
  city              VARCHAR(80) NOT NULL,
  contact_email     VARCHAR(254),
  contact_phone     VARCHAR(30),
  status            job_status NOT NULL DEFAULT 'pending',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at        TIMESTAMPTZ NOT NULL, -- created_at + 14d
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT at_least_one_contact CHECK (
    (contact_email IS NOT NULL AND trim(contact_email) <> '') OR
    (contact_phone IS NOT NULL AND trim(contact_phone) <> '')
  )
);

-- updated_at trigger (optional but useful)
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER jobs_updated_at BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

Indexes (critical for 100–500 jobs/month + responsive UI):

```sql
-- Public list: recent published first, city filter, search
CREATE INDEX idx_jobs_published_created_desc ON jobs (created_at DESC) WHERE status = 'published';
CREATE INDEX idx_jobs_city_published ON jobs (city) WHERE status = 'published';
-- Trigram/ILIKE search on title+company+activities (pg_trgm)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_jobs_search_trgm ON jobs USING GIN (
  (coalesce(title,'') || ' ' || coalesce(company,'') || ' ' || coalesce(activities,'')) gin_trgm_ops
) WHERE status = 'published';

-- Lifecycle: expire/delete
CREATE INDEX idx_jobs_expires_at ON jobs (expires_at);
CREATE INDEX idx_jobs_status_expires ON jobs (status, expires_at);
```

Notes: 
- `city` constrained to initial set in app (São Paulo, Rio de Janeiro, Belo Horizonte, Remoto) but keep varchar to avoid premature enum churn.
- `activities` stored as TEXT (shown truncated then expandable). 
- `salary` string to support ranges (R$ X–Y, a combinar) per pt-BR reality. 
- Hard delete only (no `deleted_at` soft delete) per requirement.

#### `admin_users` (minimal, single-master friendly)
Keep minimal since “solo admin”. 

```sql
CREATE TABLE admin_users (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username   VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL, -- Argon2id or bcrypt
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_login TIMESTAMPTZ
);
-- Seed single user via migration or CLI (use ADMIN_USERNAME/PASSWORD only in bootstrap)
```

Or simpler: no DB user table if using single master password from `.env` + JWT (stateless). Both acceptable. Recommendation: **JWT stateless auth** (single password in `.env`) avoids DB user mgmt for solo admin — see API surface.

Rationale: out of scope multi-admin; stateless reduces surface. If you later add users, migrate to DB table.

### Data Constraints & Integrity
- At least one contact enforced by CHECK.
- `expires_at` always set on insert (never null). 
- Status transitions: `pending -> published` (and admin can delete pending). Do not auto-publish. 
- Trim inputs on write.

## REST API Surface

Base: `http://<backend>/api/v1` (prod https). All admin routes require auth. Public read-only except reveal-contact (needs Turnstile).

### Public
| Method | Path | Purpose | Notes |
|---|---|---|---|
| `GET` | `/public/jobs` | List published jobs | Query: `search` (string), `city` (string), `sort` (`asc\|desc`, default desc by created_at), `page` (int>=1), `limit` (int 1–50). Returns jobs with contacts omitted/redacted in list view; modal fetch full detail or include redacted. |
| `GET` | `/public/jobs/{id}` | Get published job details | Returns full job fields except maybe not needed if modal uses list+reveal; or include redacted contacts. Public can see non-contact fields. |
| `POST` | `/public/jobs/{id}/reveal-contact` | Reveal contact after Turnstile | Body: `{ "cf_token": "..." }`. Headers: `X-Forwarded-For`/`CF-Connecting-IP` passed to Turnstile. Returns `{ contact_email?, contact_phone? }`. 401/403 on fail. |

### Auth (Admin)
| Method | Path | Purpose | Notes |
|---|---|---|---|
| `POST` | `/auth/login` | Admin login | Body: `{ "password": "..." }` (or username+password). Verify against `ADMIN_PASSWORD` (env). Returns `{ access_token, token_type: "bearer", expires_in }`. Use httpOnly cookie alternative optional; bearer fine for SPA if stored securely (memory/localStorage tradeoffs). Recommend short-lived (e.g. 4–8h). |
| `POST` | `/auth/logout` | (optional) | If using httpOnly cookies; not necessary for bearer. |

Auth scheme: Bearer JWT signed with `JWT_SECRET`. Claims: `sub=admin`, `role=admin`, `exp`, `iat`.

### Admin (protected)
| Method | Path | Purpose | Notes |
|---|---|---|---|
| `POST` | `/admin/extract` | Extract jobs from text | Body: `{ "text": "..." }`. Max size (e.g. 256KB). Calls Groq, validates, bulk creates pending (expires_at=now+14d). Returns `{ jobs: [JobOut...] }` (pending). Idempotent by content+time not required; paste is explicit action. |
| `GET` | `/admin/jobs` | List jobs (any status) | Query: `status=pending\|published\|all`, `page`, `limit`. For review queue primary view is pending. |
| `GET` | `/admin/jobs/{id}` | Get single job | Full fields. |
| `PATCH` | `/admin/jobs/{id}` | Update job (approve/edit) | Body partial: can set `status='published'`, edit fields, etc. Validates contact rule. |
| `DELETE` | `/admin/jobs/{id}` | Delete job | Hard delete (admin manual). Also used for review rejections. |
| `POST` | `/admin/jobs/bulk-approve` | (optional) | `{ ids: [...] }` to approve multiple pending quickly. |

Notes: 
- All admin ops require `Authorization: Bearer <token>`. 
- `extract` is the main automation path; manual create optional but not needed. 
- Never expose internal fields beyond JobOut schema.

## LLM Extraction Contract

### Goal
Return an **array** of structured job objects from raw unstructured pt-BR text (WhatsApp/Telegram: line breaks, bullets, emojis, multiple jobs).

### Required output schema (strict)
Each job must match:
- `title` (string, required, non-empty after trim). e.g. "Analista de Suporte"
- `company` (string, optional)
- `activities` (string, optional) — responsibilities/atividades
- `requirements` (string, optional) — requisitos
- `salary` (string, optional) — keep ranges/text as is
- `benefits` (string, optional)
- `city` (string, required) — must be one of: `"São Paulo"`, `"Rio de Janeiro"`, `"Belo Horizonte"`, `"Remoto"`. If ambiguous, infer or ask? Prefer best inference; if cannot infer -> skip or set to one of allowed? Recommendation: if clearly not in list, map to nearest or set `city="Remoto"` only if stated; otherwise include but UI can filter? Project states initial cities fixed — enforce allowed set; if unknown, do not hallucinate wildly — better to include with best guess but validation can reject? Or instruct LLM to pick from allowed set. 
- `contact_email` (string, optional, valid email if present)
- `contact_phone` (string, optional, pt-BR style acceptable)

**Validation rule:** `contact_email OR contact_phone` must be non-empty after trim for every job.

### Prompt design (opinionated)
Use system+user with explicit constraints:

```text
SYSTEM:
You are an extractor that converts Brazilian job posts (pt-BR) from unstructured text into a JSON array.
Output ONLY valid JSON (no markdown, no prose, no code fences).
Do not invent facts. Use null/omit empty optional fields.
For each job return exactly these keys: title, company, activities, requirements, salary, benefits, city, contact_email, contact_phone.
city MUST be one of: "São Paulo", "Rio de Janeiro", "Belo Horizonte", "Remoto".
Each job MUST have at least one contact: contact_email OR contact_phone (non-empty).
If multiple jobs in text, split them. Do not merge unrelated posts.
Preserve original intent; keep short strings for salary/benefits if ranges given.
```

```text
USER:
{text}
```

### Parameters
- Model: `llama-3.1-8b-instant` (default, cheaper/faster) or `llama-3.3-70b` (higher accuracy). Start with 8b-instant.
- Temperature: `0` (max determinism)
- Max tokens: sufficient for array (e.g. 4096) 
- Response format: JSON (if Groq supports json_object/response_format) — prefer strict JSON mode.

### Parsing, validation, error handling
1. **Parse:** `json.loads(raw)` — if fails, try to strip code fences.
2. **Type check:** result is `list` of dicts.
3. **Per-job validation (Pydantic):** 
- title required non-empty
- city in allowed set
- contact rule satisfied
- email format basic if present (e.g. `r"^[^@\s]+@[^@\s]+\.[^@\s]+$"`)
- phone basic non-empty if present
- lengths (title<=200, company<=150 etc.) to avoid abuse
4. **Filter/repair:** drop jobs failing validation? Or reject whole batch? **Reject whole batch** on critical parse failure (return 422 with details) and suggest reformatting; for individual field issues, prefer to **not insert** that job unless fixable — but better fail with correction prompt to avoid losing data silently. 
5. **Correction retry (once):**
```text
SYSTEM: ... Output ONLY JSON array matching schema. Fix these errors: {errors}. 
Do not add new jobs.
```
User includes original text + errors. Parse again.
6. **At-least-one-contact enforcement:** hard fail if any job violates (prevents publishing garbage). 
7. **Safety:** cap max jobs per extract (e.g. 50) to prevent abuse/overspend; cap text size.

### Idempotency
- `extract` is not globally idempotent by key (pasting same text again creates new pending jobs) — this is correct for manual curation (admin explicitly pasted). 
- Do **not** dedupe against published jobs in MVP (stated out of scope). 
- If needed later, dedupe by (normalized title+company+contact_signature+city) but avoid false positives.

## Build Order (Dependencies)

Implement in order to minimize blockers:

1. **DB + models/migrations (foundation)**
- Neon DB provisioned, `DATABASE_URL`. 
- SQLAlchemy models + Alembic init + initial migration (jobs + admin_users or skip). 
- Config/.env validation.

2. **Backend core (API skeleton)**
- FastAPI app, CORS, logging, Pydantic schemas, deps (DB session, auth). 
- Health endpoint (`/health`).

3. **Auth + Admin guards**
- JWT issuance/verification; login endpoint; dependency `require_admin`. 
- Protect admin routers.

4. **Jobs CRUD + Public read**
- CRUD for jobs, public list/detail (redacted), admin CRUD. 
- Validation (contact rule). 

5. **LLM extraction (Groq)**
- Service + router `/admin/extract`, prompt + parsing + validation + retry. 
- Bulk create pending with expires_at=now()+14d. 

6. **Turnstile verify (reveal contact)**
- Service to call Turnstile API (server-side), `/public/jobs/{id}/reveal-contact`. 
- IP extraction behind proxy (Railway/Render + Vercel). 

7. **Lifecycle scheduler (14d expiry + hard delete)**
- APScheduler in lifespan; job `expire_and_hard_delete()` runs periodically; transactional; logging. 
- Indexes for expires_at.

8. **Frontend (Next.js 15)**
- Public pages (grid, modal, search/filter/sort). 
- Admin pages (login, paste+extract, review queue). 
- Turnstile widget + reveal contact. 
- API client typed to backend.

9. **Integration + deployment wiring**
- CORS origins (Vercel frontend + local), env vars both sides. 
- Deploy backend (Railway/Render), frontend (Vercel). Connect Neon.

## Deployment Topology

| Component | Platform | Notes |
|---|---|---|
| **Frontend (Next.js 15)** | Vercel | App Router, Node runtime. Env: `NEXT_PUBLIC_API_BASE_URL` (backend URL). No secrets. Dark mode Tailwind. |
| **Backend (FastAPI)** | Railway or Render | Python 3.11+. Uvicorn/Gunicorn. Single process typical (sufficient for 100–500 jobs/month). If you later scale to multiple instances, scheduler must be singleton (advisory lock or external cron). |
| **DB (Postgres)** | Neon (serverless) | Connection string with pooling. Use `sslmode=require`. Migrations run from backend CI/CLI (alembic upgrade head). |
| **Turnstile** | Cloudflare | Free. Add site key to frontend, secret to backend. |
| **LLM** | Groq | API key server-side only. Models: `llama-3.1-8b-instant` or `llama-3.3-70b`. |

### Network & CORS

- CORS: allow only frontend origin(s). 
  - Dev: `http://localhost:3000`
  - Prod: `https://<your-vercel-app>.vercel.app`
- Backend behind HTTPS. Trust proxy headers for client IP (X-Forwarded-For, CF-Connecting-IP) when verifying Turnstile and for logging.
- No direct DB access from frontend.

### Environment variables

**Backend (.env):**
```env
ENV=dev|prod
DATABASE_URL=postgresql+psycopg://...@ep-...us-east-1.aws.neon.tech/dbname?sslmode=require
GROQ_API_KEY=...
GROQ_MODEL=llama-3.1-8b-instant  # or llama-3.3-70b
ADMIN_PASSWORD=...  # single master
JWT_SECRET=...      # strong random
JWT_EXPIRES_IN=28800  # 8h
TURNSTILE_SECRET_KEY=...
CORS_ORIGINS=http://localhost:3000,https://<vercel>.vercel.app
MAX_EXTRACT_TEXT_KB=256
EXPIRE_CHECK_INTERVAL_MIN=10  # scheduler frequency
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1  # dev
# prod: https://<backend>.railway.app/api/v1
NEXT_PUBLIC_TURNSTILE_SITE_KEY=...
```

Validate on backend startup (pydantic-settings) — fail fast if missing.

## Where Turnstile Happens (server-side) — explicitly

- **Client:** Render `<Turnstile />` widget on "Mostrar contato" action (modal). On success receive `token`. 
- **Client → API:** `POST /public/jobs/{id}/reveal-contact` with `{ cf_token: token }` and include job context. 
- **Server:** Extract client IP (`request.headers.get("CF-Connecting-IP") or "X-Forwarded-For" first IP`). Call `https://challenges.cloudflare.com/turnstile/v0/siteverify` with `secret`, `response=cf_token`, `remoteip`, `sitekey` (optional). 
- **Decision:** If `success` true and not expired/duplicate — return contacts. Otherwise 403. 
- **Never:** Trust client-side flags; never embed contacts in public list; never skip server verify.

## Scaling & Performance Considerations

| Scale | Approach |
|---|---|
| **0–1k users/month** (expected 100–500 jobs) | Monolith FastAPI + single worker. APScheduler in-process. Neon serverless fine with pool. 8b-instant Groq cheap. |
| **1k–10k users/month** | Add DB indexes if search slow (trigram already included). Consider HTTP caching for public list (ETag, CDN) but jobs change on publish/delete. Avoid over-caching. |
| **>10k** | Split: extract as background job queue (Celery/RQ) to avoid blocking request; multiple API replicas -> replace in-process scheduler with external cron (e.g. Render cron, GitHub Actions + HTTP trigger) or DB-backed lock. But premature now. |

Key priorities: 
1. Correct indexes (published_created_desc, city, trigram) — biggest win for list/search.
2. Pydantic validation + size caps (abuse prevention).
3. Transactional hard deletes with `expires_at` index.

## Anti-Patterns to Avoid

| Anti-Pattern | Why wrong | Do instead |
|---|---|---|
| **Client-side contact reveal** | Trivial to scrape by inspecting network/js. | Server-side Turnstile verify before returning contacts (as above). |
| **Soft delete on expiry** | Violates “apagadas do banco (hard delete)”. Bloats table, keeps PII longer than needed. | Hard `DELETE` in scheduled job with transaction + WHERE expires_at <= NOW(). |
| **Trusting LLM output blindly** | Malformed JSON, missing contacts, hallucinated cities. | Strict schema + parse+validate + correction retry + enforce contact CHECK + app validation. |
| **Auto-publishing extracted jobs** | Quality gate required (curadoria manual). | Always insert as `status='pending'`; only admin can set `published`. |
| **Scheduler in multi-replica without lock** | Double-deletes, race conditions. | Use advisory lock (Postgres `pg_try_advisory_lock`) or run single instance; or external cron hitting secured endpoint. |
| **Exposing DB/LLM from frontend** | Secrets leak. | All external calls server-side; frontend uses API only. |
| **Using client time for expires_at** | Clock skew -> wrong expiry. | Compute `expires_at = NOW() + interval '14 days'` in DB/service (server time). |
| **ILIKE only without trigram** | Slow on larger datasets/text search. | Add `pg_trgm` GIN index on title+company+activities (with status filter). |

## Integration Points

| Boundary | Communication | Notes |
|---|---|---|
| **Next.js → FastAPI** | REST HTTPS (JSON) | CORS restricted. Typed client. Handle 401/403/422. |
| **FastAPI → Postgres (Neon)** | TCP + SSL (asyncpg/psycopg3) | Connection pooling. Migrations via Alembic. |
| **FastAPI → Groq** | HTTPS JSON | API key header. Timeout + retry on network errors (not on validation). |
| **FastAPI → Turnstile** | HTTPS form/urlencode | `siteverify` endpoint. Idempotent verification. |
| **Scheduler → DB** | Same connection pool | Transactional deletes; index scan on expires_at. |

## Sources (current, verified approach)

- Next.js 15 App Router: official docs (routing, RSC, env). 
- FastAPI: Pydantic v2, dependencies, lifespan (for scheduler), CORS, background tasks. 
- Neon Postgres: serverless + pooling, pg_trgm. 
- Groq: JSON mode/structured output guidance; model choices (llama-3.1-8b-instant, llama-3.3-70b). 
- Cloudflare Turnstile: server-side siteverify. 
- APScheduler: BackgroundScheduler in-process with proper shutdown in lifespan. 
- PostgreSQL: CHECK constraints, partial indexes, trigram search. 

---

*Architecture research for: NQU (NaoQueroUsar)*  
*Researched: 2026-10-13 | Confidence: HIGH | Domain: pt-BR job board + LLM extraction + 14d hard-delete lifecycle*