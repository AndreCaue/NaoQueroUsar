---
phase: 01-backend-foundation-data-admin-auth
plan: 04
subsystem: api
tags: [fastapi, pydantic, sqlalchemy, postgres, pytest, pytest-asyncio, httpx, public-api, pagination, contact-free]

# Dependency graph
requires:
  - phase: 01-backend-foundation-data-admin-auth
    provides: "Job model + JobStatus enum + jobs migration (plan 01-02); auth login + require_admin (plan 01-03); Settings/app factory/get_session (plan 01-01)"
provides:
  - "backend/app/schemas/job.py: JobPublic (contact-free) + JobListResponse envelope (D-15, D-18)"
  - "backend/app/crud/jobs.py: list_published + get_published filtering status='published' AND expires_at > now() (D-17)"
  - "GET /api/v1/public/jobs (offset pagination page/limit 1-50 default 20 + total) and GET /api/v1/public/jobs/{id} (404 otherwise) (D-14, D-16)"
  - "backend/scripts/seed.py: seeds one published job for manual checks (D-22)"
  - "backend/tests/: pytest + pytest-asyncio criteria suite (18 tests) + httpx ASGI client + rollback-isolated DB fixtures"
affects:
  - "Phase 3 (reveal/contact endpoint — JobPublic deliberately has no contact)", "Phase 4 (search/city/sort added to the public CRUD)", "Phase 5 (admin review reuses the crud/jobs layering pattern)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Contact-free public contract enforced at the schema layer (D-18): JobPublic declares no contact fields, so model_validate cannot leak them"
    - "A single `filters` tuple is applied to both the page SELECT and the total count (identical D-17 predicate on both)"
    - "Test isolation via a per-test outer connection transaction + session; the jobs table is cleared inside the transaction and everything is rolled back at teardown (no commits, no cross-test leakage)"
    - "FastAPI get_session dependency override to route the app at the test session; httpx ASGITransport (no live server)"
    - "conftest resolves the test DB from TEST_DATABASE_URL/DATABASE_URL before importing app modules, then forces deterministic ADMIN_PASSWORD_HASH/JWT_SECRET env"

key-files:
  created:
    - backend/app/schemas/job.py
    - backend/app/crud/__init__.py
    - backend/app/crud/jobs.py
    - backend/scripts/__init__.py
    - backend/scripts/seed.py
    - backend/tests/conftest.py
    - backend/tests/test_auth.py
    - backend/tests/test_public_api.py
    - backend/tests/test_schema.py
  modified:
    - backend/app/schemas/__init__.py
    - backend/app/api/v1/public.py

key-decisions:
  - "D-14 realized: offset pagination ?page=&limit= with limit bounded 1-50 (default 20) and a total count in the envelope"
  - "D-15 realized: JobPublic returns every field EXCEPT contact (title, company, activities, requirements, salary, benefits, city, status, created_at, expires_at)"
  - "D-16 respected: only GET /public/jobs and GET /public/jobs/{id}; search/filter/sort deferred to Phase 4"
  - "D-17 realized: every public query filters status='published' AND expires_at > now()"
  - "D-18 realized: no contact field on JobPublic; reveal endpoint deferred to Phase 3"
  - "D-22 realized: focused pytest + pytest-asyncio suite (18 tests) + seed script proving all Phase 1 criteria"

patterns-established:
  - "Public read surface is anonymous (no auth dependency) and structurally contact-free"
  - "Rollback-isolated async test fixtures sharing one session between test and app via dependency override"

requirements-completed: [ADMN-01, ADMN-02, ADMN-03]

# Metrics
duration: ~6min
completed: 2026-10-15
---

# Phase 01 Plan 04: Public Read Surface & Phase 1 Validation Suite

**Contact-free `JobPublic` schema, published/non-expired `GET /api/v1/public/jobs` (offset-paginated, no auth) + `{id}` detail (404 otherwise), a seed script, and a green 18-test pytest suite proving all five Phase 1 criteria.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-10-15T03:05:47Z
- **Completed:** 2026-10-15T03:11:44Z
- **Tasks:** 2 completed
- **Files modified:** 11 (9 created, 2 modified)

## Accomplishments
- `JobPublic` (no `contact_email`/`contact_phone`) + `JobListResponse` envelope — the contact-free public contract is enforced at the schema layer, so the ORM object can never leak contact into a response (D-15, D-18; T-04-01).
- `crud/jobs.py` `list_published` (page SELECT + total count sharing one `status='published' AND expires_at > now()` filter, newest first) and `get_published` (D-17; T-04-02).
- `GET /api/v1/public/jobs` (offset pagination `page`/`limit`, cap 1–50 default 20, total count) and `GET /api/v1/public/jobs/{id}` (404 for pending/expired/unknown), both anonymous (D-14/D-16).
- `scripts/seed.py` inserts one published job for manual verification (D-22).
- `tests/` — 18 tests, all passing against a real PostgreSQL 17: login ok/bad, admin 401 (missing/tampered) and 200 (sub/role=admin), public list is published-only non-expired with no contact keys (list+detail), pending/expired/unknown detail 404, pagination total, `limit` cap 422, at-least-one-contact `IntegrityError`, four enum values + DB-level rejection, and `expires_at = created_at + 14 days`.

## Task Commits

Each task was committed atomically:

1. **task 1: Public schemas + published/non-expired CRUD + public routes + seed script** - `54b2a69` (feat)
2. **task 2: pytest harness + criteria test suite** - `7c6158b` (test)

**Plan metadata:** _(see final docs commit)_

## Files Created/Modified
- `backend/app/schemas/job.py` - `JobPublic` (contact-free) + `JobListResponse`
- `backend/app/schemas/__init__.py` - exports the two new schemas (kept auth exports)
- `backend/app/crud/jobs.py` - `list_published` / `get_published` (D-17 predicate)
- `backend/app/crud/__init__.py` - exports the two CRUD functions
- `backend/app/api/v1/public.py` - `GET /public/jobs` + `GET /public/jobs/{id}` (no auth)
- `backend/scripts/seed.py` - seeds one published job (self-bootstraps `sys.path`)
- `backend/scripts/__init__.py` - package marker
- `backend/tests/conftest.py` - DB resolution, rollback-isolated session, ASGI client, seed fixtures, clean skip
- `backend/tests/test_auth.py` - login ok/bad + admin guard 401/200
- `backend/tests/test_public_api.py` - public list/detail, no-contact, 404s, pagination, limit cap
- `backend/tests/test_schema.py` - contact CHECK, enum values + DB rejection, 14-day expiry

## Decisions Made
All decisions were fixed by `01-CONTEXT.md` (D-14..D-18, D-22). One implementation choice within latitude: the public router declares `APIRouter(prefix="/public")` (mounted unprefixed by `router.py`, consistent with 01-03's auth/admin routers), so routes resolve to `/api/v1/public/jobs[...]`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `uv` is not installed on the executor machine**
- **Found during:** all verification steps
- **Issue:** Every `<verify>`/`<automated>` command uses `uv run …`, but `uv` is not on `PATH` (same as plans 01-02/01-03).
- **Fix:** Ran the equivalent commands directly with the project virtualenv interpreter (`backend/.venv/Scripts/python.exe`, `.venv/Scripts/alembic.exe`). `pyproject.toml`/`uv.lock` are unchanged, so the commands run verbatim where `uv` exists.
- **Files modified:** none (verification-only substitution)
- **Verification:** All plan verify commands produced their expected output (`public-api-ok`, `18 passed`, `E2E-OK`).
- **Committed in:** n/a (no code change)

**2. [Rule 3 - Blocking] No live Neon test branch; no `DATABASE_URL`/`.env`**
- **Found during:** task 2 (running the suite)
- **Issue:** The plan targets a dedicated Neon test branch (`TEST_DATABASE_URL`), but no live Neon DB is reachable and no `backend/.env` exists.
- **Fix:** Ran the full suite against a **throwaway local PostgreSQL 17 cluster** (`initdb` trust-auth on port 55432 — the same approach 01-02 used), applied `alembic upgrade head`, then ran `pytest`. Applied the plan's `<verify>` accordingly. This exercises the real DDL (enum, CHECK, timestamptz defaults, triggers) and the real query predicates. The Neon test branch remains a human setup step in `01-USER-SETUP.md`.
- **Files modified:** none (verification-only substitution)
- **Verification:** `pytest -q` → `18 passed`; seed + `GET /api/v1/public/jobs` → `total=1`, detail returns no contact keys, unknown id → 404.
- **Committed in:** n/a (no code change)

**3. [Rule 1 - Bug] The plan's prescribed module-level `pytest.skip(..., allow_module_level=True)` in conftest.py is not a clean skip**
- **Found during:** task 2 (verifying the "skip when no DB" behavior)
- **Issue:** `pytest.skip(..., allow_module_level=True)` executed inside `conftest.py` is treated as a conftest import error — pytest exits **1** with a traceback, not the intended clean skip (`--` the explicit goal "so config-only runs don't hard-fail"). Additionally, resolving the URL via `get_settings().DATABASE_URL` raises `ValidationError` when required secrets are unset, which also breaks config-only runs.
- **Fix:** (a) Resolve the DB URL directly from `os.environ` / `backend/.env` (`dotenv_values`) before importing app modules — no Settings construction; (b) skip the entire suite via a `pytest_collection_modifyitems` hook that marks every collected item skipped when no DB is configured. Result: no DB → `18 skipped`, **exit 0**; DB present → `18 passed`, exit 0. The forced test env (`ADMIN_PASSWORD_HASH`/`JWT_SECRET`) is set before any app import so auth is deterministic.
- **Files modified:** `backend/tests/conftest.py`
- **Verification:** With `TEST_DATABASE_URL` unset → `18 skipped in 0.03s`, exit 0; with it set → `18 passed`, exit 0.
- **Committed in:** `7c6158b` (task 2)

**4. [Rule 3 - Blocking] `python scripts/seed.py` could not import `app`**
- **Found during:** task 1 (running the seed script as documented)
- **Issue:** Running a file as a script puts its own directory (`scripts/`) — not `backend/` — on `sys.path`, so `from app.db.session import …` raised `ModuleNotFoundError: No module named 'app'` for the documented `python scripts/seed.py` invocation.
- **Fix:** Added a small `sys.path` bootstrap (insert the parent `backend/` dir) at the top of `seed.py`.
- **Files modified:** `backend/scripts/seed.py`
- **Verification:** `python scripts/seed.py` → `Seeded published job id=…`.
- **Committed in:** `54b2a69` (task 1)

---

**Total deviations:** 4 auto-fixed (3 Rule 3 blocking, 1 Rule 1 bug — all verification/test-harness robustness; no product behaviour changed).
**Impact on plan:** None on the delivered artifacts. The public API and the criteria suite are exactly as planned; deviations are environment substitutions and two robustness fixes to the test harness/seed script.

## Issues Encountered
- `PyJWT` `InsecureKeyLengthWarning` for the initial 31-byte test secret — lengthened the test `JWT_SECRET` to ≥32 bytes; the warning is gone. Unrelated to production (real `JWT_SECRET` is a 64-char random string).

## Known Stubs
None — all code is functional; no hardcoded empty values, placeholders, or unwired data sources (seed data is intentional synthetic test data).

## Threat Flags
None beyond the plan's `<threat_model>`. Mitigations applied: T-04-01 (`JobPublic` has no contact fields; tests assert keys absent on list + detail), T-04-02 (published-only + non-expired filter on query and count; tests seed pending/expired and assert exclusion/404), T-04-03 (`limit` capped at 50 via `Query(le=50)`; test asserts 422 above the cap), T-04-04 (synthetic seed/test data only; suite targets `TEST_DATABASE_URL`), T-04-05 (SQLAlchemy parameterised queries; `page`/`limit` typed `int` with bounds).

## User Setup Required

**External services require manual configuration.** See [01-USER-SETUP.md](./01-USER-SETUP.md) for:
- Environment variables (`DATABASE_URL`, `ADMIN_PASSWORD_HASH`, `JWT_SECRET`, `TEST_DATABASE_URL`)
- Neon dashboard configuration + the `alembic upgrade head` apply step
- The Neon test branch required by this plan's `pytest` suite

## Next Phase Readiness
- Phase 1 is functionally complete: the public read API responds without auth and without exposing contact, and the criteria suite has automated proof for all five Phase 1 success criteria.
- Ready for `/gsd-verify-work` on Phase 1 and for Phase 2 (LLM extraction) — the admin `require_admin` guard and the `crud/` layering are reusable.
- Blocker/concern: the suite and `01-USER-SETUP.md` steps require a live Neon (dev + test branch) to reproduce outside CI; verified here against a real local PostgreSQL 17.

---

*Phase: 01-backend-foundation-data-admin-auth*
*Completed: 2026-10-15*

## Self-Check

- [x] `backend/app/schemas/job.py` exists (FOUND)
- [x] `backend/app/crud/jobs.py` exists (FOUND)
- [x] `backend/app/crud/__init__.py` exists (FOUND)
- [x] `backend/app/api/v1/public.py` modified (FOUND)
- [x] `backend/scripts/seed.py` exists (FOUND)
- [x] `backend/tests/conftest.py`, `test_auth.py`, `test_public_api.py`, `test_schema.py` exist (FOUND)
- [x] Task 1 commit `54b2a69` present (FOUND)
- [x] Task 2 commit `7c6158b` present (FOUND)
- [x] Task 1 acceptance re-verified (`public-api-ok`, both route paths, no contact fields)
- [x] Task 2 acceptance re-verified (`pytest -q` → 18 passed, exit 0; no-DB → 18 skipped, exit 0)

## Self-Check: PASSED
