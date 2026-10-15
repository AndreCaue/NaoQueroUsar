---
phase: 01-backend-foundation-data-admin-auth
verified: 2026-10-15T00:30:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Apply the initial migration to the actual Neon database"
    expected: "`alembic upgrade head` exits 0; `job_status` enum exists; `jobs` table has the at_least_one_contact CHECK, timestamptz created_at/updated_at/expires_at (expires_at default now()+14d), and the 4 idx_jobs_* indexes; re-running is a no-op"
    why_human: "No live Neon database is reachable from the verifier environment (no DATABASE_URL / backend/.env). The migration was verified here only by offline SQL generation + model metadata, and by the executor against a throwaway local PostgreSQL 17. Applying to Neon is a documented human step in 01-USER-SETUP.md."
  - test: "Run the full pytest suite against a real DB (Neon test branch or local Postgres)"
    expected: "18 passed, exit 0 (login ok/bad, admin 401/200, public list published-only + non-expired, no contact keys, pending/expired/unknown 404, pagination total, limit cap 422, contact CHECK IntegrityError, 14-day expiry)"
    why_human: "The suite cleanly skips (18 skipped, exit 0) when no DB URL is configured — verified here. Actual DB execution requires TEST_DATABASE_URL/DATABASE_URL and a migrated schema, which need Neon access."
  - test: "Boot the backend locally against Neon and hit the health endpoint"
    expected: "`uv run uvicorn app.main:app` starts cleanly with env from Neon, and GET /api/v1/health returns 200 {\"status\":\"ok\"}"
    why_human: "App boot + env fail-fast + health + CORS + logging are verified programmatically; the 'against Neon' connection itself cannot be exercised without a Neon DATABASE_URL."
---

# Phase 01: Backend Foundation, Data & Admin Auth — Verification Report

**Phase Goal:** Um backend FastAPI rodando contra o Neon, com o contrato de dados de `jobs` e acesso seguro do master-admin — a base que todas as fases seguintes referenciam.
**Verified:** 2026-10-15T00:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Truths are taken from the ROADMAP.md Success Criteria (roadmap contract), merged with the PLAN frontmatter must-haves. All five roadmap criteria are represented.

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | Master authenticates with the env-defined password; admin routes without a valid token receive 401 (SC1, ADMN-01/03) | ✓ VERIFIED | Live TestClient: wrong password → 401; correct → 200 with `access_token`; `/api/v1/admin/me` no-header → 401; tampered token → 401; valid → 200 |
| 2 | Admin JWT session persists; each protected request validates the token; no password/token exposed (SC2, ADMN-02) | ✓ VERIFIED | `require_admin` (`backend/app/deps.py:24`) runs per request, pins `algorithms=["HS256"]`, checks `sub`/`role`; live valid-token `/me` → 200 `{sub:admin, role:admin}`; 401 body carries no token; no secret logged in `security.py`/`logging.py` |
| 3 | Initial migration creates `jobs` with the 4-value status enum, at-least-one-contact CHECK, `timestamptz` created_at/expires_at, and indexes (SC3) | ✓ VERIFIED | `alembic upgrade head --sql` emits exactly: `job_status` enum(pending/published/needs_review/invalid), `at_least_one_contact` CHECK, `TIMESTAMP WITH TIME ZONE` for created_at/updated_at/expires_at, `expires_at DEFAULT now() + interval '14 days'`, `idx_jobs_published_created_desc`, `idx_jobs_city_published`, `idx_jobs_search_trgm` (GIN `gin_trgm_ops`), `idx_jobs_status_expires` |
| 4 | Public read API (list/detail of `published`) responds without auth and without exposing email/phone (SC4) | ✓ VERIFIED | Routes registered (`/api/v1/public/jobs`, `/api/v1/public/jobs/{job_id}`) with no auth dependency; `JobPublic` declares no contact fields — validating an object carrying `contact_email`/`contact_phone` yields keys `['activities','benefits','city','company','created_at','expires_at','id','requirements','salary','status','title']` (LEAK-SAFE); `crud/jobs.py` filters `status='published' AND expires_at > now()` on both list and count |
| 5 | Backend boots locally with env-validated config (`pydantic-settings`), health endpoint, CORS and logging (SC5) | ✓ VERIFIED | `create_app()` boots; `GET /api/v1/health` → 200 `{"status":"ok","env":"dev"}`; `Settings()` fails fast with `ValidationError` when DATABASE_URL/ADMIN_PASSWORD_HASH/JWT_SECRET are unset; CORS from `CORS_ORIGINS` (`['http://localhost:3000','http://foo.com']`); `configure_logging` wired in `create_app` |

**Score:** 5/5 truths verified

The five success criteria are all met at the code/contract level. The only unverified dimension is the live Neon connection and a full DB-backed test run — both are documented human steps (see Human Verification Required).

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/app/core/config.py` | Pydantic Settings, D-05 env vars + CORS parsing | ✓ VERIFIED | `Settings` (6 fields + `TEST_DATABASE_URL`), `cors_origins_list`, `get_settings` (`@lru_cache`) |
| `backend/app/main.py` | `create_app()` + lifespan + CORS + logging | ✓ VERIFIED | 38 lines; `create_app`, `CORSMiddleware`, `/api/v1` prefix, `engine.dispose()` in lifespan |
| `backend/app/db/session.py` | async engine + async_sessionmaker | ✓ VERIFIED | `create_async_engine(..., pool_pre_ping=True, connect_args={"statement_cache_size": 0})`, `expire_on_commit=False` |
| `backend/app/api/v1/health.py` | health endpoint | ✓ VERIFIED | `GET /health` → `{status, env}`; live 200 |
| `backend/pyproject.toml` | uv/Python manifest with pinned deps | ✓ VERIFIED | fastapi 0.143.0, sqlalchemy 2.1.4, PyJWT 2.15.1, `[tool.pytest.ini_options]` present |
| `backend/.env.example` | documented env template | ✓ VERIFIED | DATABASE_URL/ADMIN_PASSWORD_HASH/JWT_SECRET/JWT_EXPIRES_IN/CORS_ORIGINS/TEST_DATABASE_URL; placeholders only |
| `frontend/package.json` | Next.js App Router skeleton manifest | ✓ VERIFIED | next 15.5.3, react 19.1.1, dev/build/start/lint scripts |
| `backend/app/models/job.py` | `Job` model + `JobStatus` + contact constraint | ✓ VERIFIED | enum 4 values; constraints `at_least_one_contact`, `title_not_blank`; timestamptz + `interval '14 days'` |
| `backend/alembic/env.py` | async Alembic env → Settings.DATABASE_URL + Base.metadata | ✓ VERIFIED | `run_migrations_online`, injects `settings.DATABASE_URL`, `connect_args={"statement_cache_size": 0}` |
| `backend/alembic/versions/0001_initial_jobs.py` | initial migration | ✓ VERIFIED | Compiles offline; full DDL as contracted |
| `backend/alembic.ini` | Alembic config | ✓ VERIFIED | `script_location = alembic`, empty `sqlalchemy.url` |
| `backend/app/schemas/job.py` | `JobPublic` (contact-free) + `JobListResponse` | ✓ VERIFIED | No contact fields (LEAK-SAFE) |
| `backend/app/crud/jobs.py` | published-only, non-expired queries | ✓ VERIFIED | shared `filters` tuple on items + count |
| `backend/app/api/v1/public.py` | `GET /jobs` + `GET /jobs/{id}` | ✓ VERIFIED | anonymous, paginated, 404 handling |
| `backend/tests/test_public_api.py` | criteria tests | ✓ VERIFIED | 85 lines; asserts contact keys absent on list+detail |
| `backend/scripts/seed.py` | seed one published job | ✓ VERIFIED | `status=JobStatus.published`, phone contact set |

Frontend skeleton (`layout.tsx`, `page.tsx`, `globals.css`, `tsconfig.json`, `next.config.mjs`, `.gitignore`) all present.

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `main.py` | `core/config.py` | `get_settings` | ✓ WIRED | imported and used at module scope |
| `db/session.py` | `core/config.py` | `settings.DATABASE_URL` | ✓ WIRED | engine built from settings |
| `api/v1/router.py` | `health.py` | `include_router` | ✓ WIRED | includes health/auth/admin/public |
| `alembic/env.py` | `db/base.py` | `target_metadata` | ✓ WIRED | `target_metadata = Base.metadata`; models imported |
| `models/job.py` | `db/base.py` | `Base` | ✓ WIRED | `class Job(Base)` |
| `0001_initial_jobs.py` | search_text GIN | `gin_trgm_ops` | ✓ WIRED | emitted in offline SQL |
| `deps.py` | `core/security.py` | `decode_access_token` | ✓ WIRED | imported and called in `require_admin` |
| `api/v1/auth.py` | `core/config.py` | `ADMIN_PASSWORD_HASH` | ✓ WIRED | via `authenticate_password` → `settings.ADMIN_PASSWORD_HASH` |
| `api/v1/admin.py` | `deps.py` | `Depends(require_admin)` | ✓ WIRED | guard on `/me` |
| `api/v1/public.py` | `schemas/job.py` | `JobPublic`/`JobListResponse` | ✓ WIRED | `response_model` + `model_validate` |
| `crud/jobs.py` | `expires_at` filter | `Job.expires_at > func.now()` | ✓ WIRED | applied to items and count |
| `tests/test_public_api.py` | `api/v1/public.py` | asserts `contact_` absent | ✓ WIRED | keys asserted on list + detail |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `api/v1/public.py` (list/detail) | `items`/`job` | `crud/jobs.py` → `select(Job).where(status='published', expires_at > now())` over the real `jobs` table | Yes (real SQLAlchemy query, no static/empty returns) | ✓ FLOWING (query verified statically; executed against a real PostgreSQL 17 by the executor) |
| `api/v1/health.py` | `settings.ENV` | `Settings` (env) | Yes (config value) | ✓ FLOWING |

No static/empty fallbacks, no hardcoded-empty props, no disconnected data sources found in the phase's dynamic-data paths.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Health returns ok | `TestClient.get('/api/v1/health')` | `200 {'status':'ok','env':'dev'}` | ✓ PASS |
| Login ok/bad | `POST /api/v1/auth/login` (correct/wrong) | `200` + token / `401` | ✓ PASS |
| Admin guard | `GET /api/v1/admin/me` (none/tampered/valid) | `401` / `401` / `200 {sub:admin,role:admin}` | ✓ PASS |
| Fail-fast config | `Settings()` with 3 vars unset | `ValidationError` (DATABASE_URL, ADMIN_PASSWORD_HASH, JWT_SECRET) | ✓ PASS |
| Contact-free schema | `JobPublic.model_validate(obj_with_contacts)` | keys exclude contact_email/contact_phone | ✓ PASS |
| Route registration | `app.openapi()['paths']` | `/api/v1/{admin/me,auth/login,health,public/jobs,public/jobs/{job_id}}` | ✓ PASS |
| Migration SQL compiles | `alembic upgrade head --sql` | exit 0, full contracted DDL | ✓ PASS |
| CORS parsing | `Settings(CORS_ORIGINS='a, b')` | `['a','b']` | ✓ PASS |
| pytest (no DB) | `python -m pytest -q` | `18 skipped`, exit 0 | ✓ PASS (skip path) |
| pytest (with DB) | requires migrated DB | not runnable here | SKIP → human |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| ADMN-01 | 01-01, 01-03, 01-04 | Master faz login na área admin com senha definida via variável de ambiente | ✓ SATISFIED | `POST /api/v1/auth/login` verifies bcrypt hash of `ADMIN_PASSWORD_HASH`; live 200/401 |
| ADMN-02 | 01-01, 01-02, 01-03, 01-04 | Sessão admin autenticada por JWT persiste durante o uso | ✓ SATISFIED | `create_access_token` (12h, HS256); `require_admin` validates each request; live round-trip |
| ADMN-03 | 01-02, 01-03, 01-04 | Rotas administrativas bloqueiam acesso não autenticado | ✓ SATISFIED | `Depends(require_admin)` on `/admin/me`; live 401 for missing/tampered, 200 for valid |

No orphaned requirements: REQUIREMENTS.md maps only ADMN-01/02/03 to Phase 1, and all three appear in plan frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `frontend/app/globals.css` | 1 | Orphaned artifact — never imported (no `import "./globals.css"` in `layout.tsx`; repo-wide grep finds zero references) | ⚠️ Warning | The skeleton's dark theme (`color-scheme: dark`, `#0f0a1a`) never applies. Skeleton still runs; full UI/Tailwind is Phase 4. (REVIEW WR-01) |
| `backend/pyproject.toml` | 15 | `bcrypt` imported directly but only declared transitively via `passlib[bcrypt]` | ⚠️ Warning | Latent break in the committed manifest; already tracked in `deferred-items.md`. passlib is deliberately unused. (REVIEW WR-02) |
| `backend/tests/conftest.py` | 31-37, 111 | Test harness falls back to `DATABASE_URL` and runs `DELETE FROM jobs` | ⚠️ Warning | Falls back to the dev DB when `TEST_DATABASE_URL` is absent; the DELETE is inside a rolled-back transaction today, but violates the "tests never touch dev/prod DB" constraint (T-04-04). (REVIEW WR-03) |
| `backend/app/crud/jobs.py` | 32 | `ORDER BY created_at DESC` with no tie-breaker under offset pagination | ⚠️ Warning | Rows sharing a timestamp can duplicate/miss across pages. Page 4 concern. (REVIEW WR-04) |
| `backend/app/api/v1/health.py` | 12 | Unauthenticated `/health` discloses `env` (dev/prod) | ℹ️ Info | Minor info disclosure. (REVIEW IN-01) |
| `backend/app/core/config.py` | 24 | `cors_origins_list` can yield `['']` on empty/trailing-comma value | ℹ️ Info | Confirmed: `CORS_ORIGINS=''` → `['']`. (REVIEW IN-02) |
| `backend/app/deps.py` | 5-9 | `get_session`/`get_settings` imported only to re-export | ℹ️ Info | Two import paths for the same symbols. (REVIEW IN-03) |
| `backend/tests/test_auth.py` | 11 | Hardcodes `expires_in == 43200`; `JWT_EXPIRES_IN` not pinned in conftest | ℹ️ Info | Flaky if a local `.env` overrides the value. (REVIEW IN-04) |

No 🛑 Blocker anti-patterns. No TODO/FIXME/placeholder stubs, no empty implementations, and no hardcoded-empty data flowing to rendering were found in the phase's must-have paths. `search_text` is intentionally populated by a DB trigger (not a stub).

### Human Verification Required

#### 1. Apply the migration to Neon

**Test:** From `backend/` with `DATABASE_URL` set (pooled, `?ssl=require`), run `alembic upgrade head`, then `alembic current`.
**Expected:** Exits 0 and reports `0001_initial_jobs (head)`; re-running is a no-op. Spot-check: `select exists(select 1 from pg_type where typname='job_status')` → `t`; `select indexname from pg_indexes where tablename='jobs'` lists the 4 `idx_jobs_*`; `select conname from pg_constraint where conrelid='jobs'::regclass` includes `at_least_one_contact`.
**Why human:** No live Neon connection is available here. Migration correctness was verified via offline SQL generation and the executor's local PostgreSQL 17 run, not against Neon.

#### 2. Run the full test suite against a real database

**Test:** Create a Neon branch (or local Postgres), set `DATABASE_URL`/`TEST_DATABASE_URL`, apply the schema, run `uv run pytest -q`.
**Expected:** `18 passed`, exit 0.
**Why human:** The suite cleanly skips without a DB (verified: `18 skipped`, exit 0). Real execution needs a migrated DB URL.

#### 3. Boot the backend locally against Neon

**Test:** With `backend/.env` populated, `uv run uvicorn app.main:app --reload`; then `curl http://localhost:8000/api/v1/health` and a login round-trip.
**Expected:** Server starts, health returns 200 `{"status":"ok"}`; login returns a JWT; `/api/v1/admin/me` 401 without / 200 with the token.
**Why human:** App boot, env fail-fast, health, CORS and logging are verified programmatically; the live Neon connection is not.

### Gaps Summary

No gaps. All five roadmap success criteria and all sixteen must-have artifacts in the plan frontmatter are present, substantive, wired, and — for the dynamic-data public read path — backed by real queries. All three phase requirements (ADMN-01/02/03) are satisfied with live evidence. The remaining work is the operator-owned Neon connection + migration apply + DB-backed test run (documented in `01-USER-SETUP.md`). The eight REVIEW findings are non-blocking warnings/info; none prevents the phase goal. No items were deferred to later phases.

---

_Verified: 2026-10-15T00:30:00Z_
_Verifier: OpenCode (gsd-verifier)_
