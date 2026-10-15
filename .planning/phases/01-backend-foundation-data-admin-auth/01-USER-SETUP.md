# Phase 1: User Setup Required

**Generated:** 2026-10-14
**Phase:** 01-backend-foundation-data-admin-auth
**Status:** Incomplete

Complete these items for the integration to function. OpenCode automated everything
possible; these items require human access to external dashboards/accounts.

## Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `DATABASE_URL` | Neon Console → Project → Connection Details → **Pooled** connection string (host contains `-pooler`), append `?ssl=require` | `backend/.env` |
| [ ] | `ADMIN_PASSWORD_HASH` | Generate locally (bcrypt directly — passlib 1.7.4 is incompatible with the locked bcrypt 5.0.0): `.venv\Scripts\python -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_MASTER_PASSWORD', bcrypt.gensalt()).decode())"` | `backend/.env` |
| [ ] | `JWT_SECRET` | Generate: 64-char random string (e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"`) | `backend/.env` |
| [ ] | `TEST_DATABASE_URL` | Neon Console → Branches → create a branch of the dev DB → copy its **pooled** connection string with `?ssl=require` (required by plan 01-04) | `backend/.env` |

`backend/.env.example` already documents all of these (created in plan 01-01).

## Account Setup

- [ ] **Create/confirm a Neon account and project**
  - URL: https://console.neon.tech
  - Skip if: a Neon project already exists for NQU

## Dashboard Configuration

- [ ] **Apply the initial migration against Neon**
  - Location: local terminal, `backend/` directory
  - Command: `alembic upgrade head` (with `DATABASE_URL` set in `backend/.env` or the shell)
  - Notes: The migration creates `pg_trgm`/`unaccent` extensions, the `job_status`
    enum, the `jobs` table, the `at_least_one_contact` CHECK, the `search_text`
    trigger and indexes. These extensions are supported on Neon Postgres and can be
    created by the project owner role by default.

## Verification

After completing setup, verify with:

```powershell
# from backend/
alembic upgrade head
python -c "import asyncio, asyncpg, os; from app.core.config import get_settings; url=get_settings().DATABASE_URL.replace('postgresql+asyncpg://','postgresql://'); print(url)"
```

Expected results:
- `alembic upgrade head` exits 0 and reports `Running upgrade -> 0001_initial_jobs`.
- Re-running `alembic upgrade head` is a no-op (already at head).
- `alembic current` reports `0001_initial_jobs (head)`.

Quick schema spot-check (psql or Neon SQL editor):

```sql
select exists(select 1 from pg_type where typname = 'job_status');           -- t
select indexname from pg_indexes where tablename = 'jobs' order by 1;        -- 8 rows incl. idx_jobs_*
select conname from pg_constraint where conrelid = 'jobs'::regclass;         -- at_least_one_contact
```

---

**Once all items complete:** Mark status as "Complete" at top of file.

> **Note:** This migration was verified end-to-end by the executor against a throwaway
> local PostgreSQL 17 instance (same extensions, `gen_random_uuid()`, trigram search,
> CHECK/enum enforcement, downgrade→upgrade cycle). The only remaining step is applying
> it to the actual Neon database once `DATABASE_URL` is available.
