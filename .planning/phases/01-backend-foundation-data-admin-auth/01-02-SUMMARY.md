---
phase: 01-backend-foundation-data-admin-auth
plan: 02
subsystem: database
tags: [sqlalchemy, alembic, postgres, neon, pg_trgm, unaccent, migration, uuid, enum, trigram-search]

# Dependency graph
requires:
  - phase: 01-backend-foundation-data-admin-auth
    provides: "Base (DeclarativeBase), async engine/session, Settings.DATABASE_URL, app factory (plan 01-01)"
provides:
  - "SQLAlchemy 2.x Job model + JobStatus enum (the jobs data contract)"
  - "at-least-one-contact + non-blank-title DB CHECK constraints"
  - "Async Alembic environment wired to Settings.DATABASE_URL + Base.metadata"
  - "Initial migration 0001_initial_jobs: pg_trgm/unaccent, job_status enum, jobs table, timestamptz + 14-day expires_at, search_text trigger, 7 indexes"
affects:
  - 01-backend-foundation-data-admin-auth/01-04
  - Phase 2 (admin paste/insert), Phase 3/4 (public read + search), Phase 6 (expiry hard delete)

# Tech tracking
tech-stack:
  added:
    - "alembic (async env) — already a dependency from 01-01; now wired up"
  patterns:
    - "Alembic async env: async_engine_from_config + connection.run_sync(do_run_migrations), statement_cache_size=0 for PgBouncer"
    - "URL injected into alembic at runtime from pydantic Settings (never hardcoded in alembic.ini)"
    - "IMMUTABLE SQL wrapper immutable_unaccent(text) to make unaccent() indexable/trigger-usable"
    - "search_text denormalized column kept in sync by a BEFORE INSERT OR UPDATE trigger"
    - "Partial indexes (WHERE status='published') scoped to the public read path"

key-files:
  created:
    - backend/app/models/__init__.py
    - backend/app/models/job.py
    - backend/alembic.ini
    - backend/alembic/env.py
    - backend/alembic/script.py.mako
    - backend/alembic/versions/0001_initial_jobs.py
  modified: []

key-decisions:
  - "D-06: UUID PK default gen_random_uuid() — opaque, non-enumerable ids"
  - "D-07: city is varchar(80) NOT NULL, validated in app (no DB enum/CHECK)"
  - "D-08: salary is free-text varchar(80) (pt-BR ranges, 'A combinar')"
  - "D-09: native job_status enum with pending/published/needs_review/invalid"
  - "D-10: at_least_one_contact CHECK after btrim() on email/phone"
  - "D-11: pg_trgm + unaccent + normalized search_text column + GIN trigram index (published-only)"
  - "D-12: created_at/updated_at/expires_at timestamptz; expires_at server default now() + 14 days"
  - "D-13: no soft delete (hard delete deferred to Phase 6)"
  - "kept base.py minimal; models imported in alembic/env.py instead (avoids circular import)"

patterns-established:
  - "Partial indexes for the public list (status='published') live only in the migration, not in model metadata (per plan)"
  - "updated_at maintained by a set_updated_at() trigger (T-02-04 repudiation mitigation)"

requirements-completed: [ADMN-02, ADMN-03]

# Metrics
duration: ~35min
completed: 2026-10-14
---

# Phase 01 Plan 02: Jobs Data Contract — Job Model + Initial Alembic Migration

**SQLAlchemy `Job` model and an async Alembic initial migration delivering the `jobs` contract: `job_status` enum, at-least-one-contact CHECK, timestamptz + 14-day `expires_at`, and accent-insensitive search (pg_trgm + unaccent + `search_text` GIN trigram index).**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-10-14
- **Completed:** 2026-10-14
- **Tasks:** 2 completed
- **Files modified:** 6 created, 0 modified

## Accomplishments
- `Job` model (SQLAlchemy 2.x `Mapped`/`mapped_column`) with UUID PK (`gen_random_uuid()`), `JobStatus` enum (4 values), and the `at_least_one_contact` + `title_not_blank` CHECK constraints.
- Async Alembic environment (`alembic/env.py`) wired to `Settings.DATABASE_URL` and `Base.metadata`, with `statement_cache_size=0` for Neon PgBouncer compatibility and `compare_type=True`.
- Initial migration `0001_initial_jobs`: `pg_trgm` + `unaccent` extensions, an `IMMUTABLE` `immutable_unaccent(text)` wrapper, the `job_status` enum type, the `jobs` table with timestamptz (`expires_at` default `now() + interval '14 days'`), the `search_text` sync trigger, the `updated_at` trigger, and 7 indexes (3 model-level + 4 public/lifecycle partial/composite).
- **Verified end-to-end** against a throwaway local PostgreSQL 17 instance: migration applies, schema matches, constraints reject invalid rows, the search trigger produces lowercased/unaccented text, trigram lookup matches accented data, and `downgrade base` → `upgrade head` re-creates the schema cleanly.

## Task Commits

Each task was committed atomically:

1. **task 1: Job model + JobStatus enum + at-least-one-contact constraint** - `13fcf70` (feat)
2. **task 2: Alembic setup + initial migration (extensions, enum, table, CHECK, search, indexes)** - `2e27f06` (feat)

**Plan metadata:** _(see final docs commit)_

## Files Created/Modified
- `backend/app/models/job.py` - `Job` model, `JobStatus` enum, CHECK constraints, model-level indexes
- `backend/app/models/__init__.py` - exports `Job`, `JobStatus`
- `backend/alembic.ini` - Alembic config; `script_location = alembic`, empty `sqlalchemy.url`
- `backend/alembic/env.py` - async env; injects `Settings.DATABASE_URL`, `target_metadata = Base.metadata`
- `backend/alembic/script.py.mako` - standard migration template
- `backend/alembic/versions/0001_initial_jobs.py` - the initial migration (upgrade/downgrade)

## Decisions Made
All decisions were fixed by `01-CONTEXT.md` (D-06..D-13); no new product decisions were required. Two implementation choices within the plan's latitude:
- `base.py` left minimal; `from app.models import Job, JobStatus` lives in `alembic/env.py` only (plan explicitly preferred this to avoid a circular import).
- The model's non-partial indexes (`ix_jobs_status/expires_at/created_at`) are also created in the migration to keep DB ⇄ metadata aligned; the partial/`WHERE status='published'` indexes exist only in the migration, per the plan.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `uv` is not installed on the executor machine**
- **Found during:** task 1 (and all verification steps)
- **Issue:** Every `<verify>`/`<automated>` command in the plan uses `uv run …`, but `uv` is not on `PATH` and no `uv` binary is present. Running the commands verbatim fails immediately.
- **Fix:** Ran the equivalent commands directly with the project virtualenv interpreter (`backend/.venv/Scripts/python.exe` and `.venv/Scripts/alembic.exe`). The `pyproject.toml`/`uv.lock` dependency set is unchanged, so `uv run` will work on a machine that has `uv`.
- **Files modified:** none (verification-only substitution)
- **Verification:** All plan verify commands produced their expected output via the venv.
- **Committed in:** n/a (no code change)

**2. [Rule 3 - Blocking] No `DATABASE_URL` / `.env` present; no Neon DB reachable**
- **Found during:** task 2
- **Issue:** Task 2's verification requires applying the migration against Neon, but there is no `backend/.env` and no `DATABASE_URL` in the environment. The plan lists Neon as a `user_setup` item, so the secret is expected to come from the human.
- **Fix:** Verified the migration end-to-end against a **throwaway local PostgreSQL 17 cluster** (`initdb` with trust auth on port 55432, same extensions) instead of failing the task. This exercised the real DDL, triggers, constraints, enum, and trigram search. The remaining Neon apply is documented in `01-USER-SETUP.md` as the human action.
- **Files modified:** none (verification-only substitution)
- **Verification:** `alembic upgrade head` exited 0; `job_status` enum present; all 4 `idx_jobs_*` indexes + 3 `ix_jobs_*` + `pk_jobs` present; `at_least_one_contact` & `title_not_blank` reject bad rows; invalid enum value rejected; `search_text` normalized (`São João` → `sao joao`); `expires_at - created_at = interval '14 days'`; `downgrade base` → `upgrade head` succeeded.
- **Committed in:** n/a (no code change)

---

**Total deviations:** 2 auto-fixed (both Rule 3 - Blocking, verification-environment substitutions; no production code affected).
**Impact on plan:** None on the delivered artifacts. All acceptance criteria that do not require the actual Neon instance were met against a real PostgreSQL 17. Applying `alembic upgrade head` to Neon remains a one-command human action (`01-USER-SETUP.md`).

## Issues Encountered
- The initial detached `postgres.exe` launch in the temporary cluster died once when the shell tool reaped the process tree; relaunching detached with `Start-Process` on a fresh `initdb` cluster worked. No impact on the migration itself.
- PowerShell's default encoding mangled accented literals passed inline to `psql`; verification SQL was run from UTF-8 files instead.

## Known Stubs
None — all code is functional. `search_text` is intentionally populated by a DB trigger (not a Python stub).

## User Setup Required

**External services require manual configuration.** See [01-USER-SETUP.md](./01-USER-SETUP.md) for:
- Environment variables to add (`DATABASE_URL`, `ADMIN_PASSWORD_HASH`, `JWT_SECRET`, `TEST_DATABASE_URL`)
- Neon dashboard configuration
- The `alembic upgrade head` apply step + verification commands

## Next Phase Readiness
- The `jobs` contract is fixed and migration-verified; plan **01-04** (public read API) can build its Pydantic schemas and repository against `app.models.job.Job` / `JobStatus` (D-18 requires contact fields be excluded from the public payload).
- Blocker/concern: the migration has **not yet been applied to Neon** — requires `DATABASE_URL` (see `01-USER-SETUP.md`). Plans 01-03 and 01-04 are designed to run without a live DB for their logic tests, so work can continue; the Neon apply should be done before the Phase 2 insert path is exercised.

---
*Phase: 01-backend-foundation-data-admin-auth*
*Completed: 2026-10-14*

## Self-Check

- [x] `backend/app/models/__init__.py` exists (FOUND)
- [x] `backend/app/models/job.py` exists (FOUND)
- [x] `backend/alembic.ini` exists (FOUND)
- [x] `backend/alembic/env.py` exists (FOUND)
- [x] `backend/alembic/script.py.mako` exists (FOUND)
- [x] `backend/alembic/versions/0001_initial_jobs.py` exists (FOUND)
- [x] Task commit `13fcf70` present (FOUND)
- [x] Task commit `2e27f06` present (FOUND)
- [x] Task 1 acceptance criteria re-verified (enum values, `at_least_one_contact`, timestamptz columns)
- [x] Task 2 SQL/migration verified end-to-end on real PostgreSQL 17 (offline SQL generation + live apply + downgrade/upgrade cycle)

## Self-Check: PASSED
