---
phase: 06-lifecycle-trust-legal-launch
plan: 01
subsystem: backend/lifecycle
tags: [apscheduler, cron, hard-delete, fastapi, sqlalchemy, expiry, cron-secret]

# Dependency graph
requires:
  - phase: 01-backend-foundation-data-admin-auth
    provides: Job model with expires_at = now() + 14 days (migration 0001) and the async session factory
  - phase: 04-public-board-frontend
    provides: public board filtering on expires_at > now() (the visibility rule the sweep mirrors)
provides:
  - Daily 03:00 UTC in-process expiry sweep (APScheduler BackgroundScheduler in the FastAPI lifespan)
  - delete_expired_jobs CRUD sweep (hard delete by DB clock, status-agnostic, idempotent)
  - POST /api/v1/admin/expire guarded by X-Cron-Secret for manual/catch-up triggers
  - CRON_SECRET and SCHEDULER_ENABLED settings (fail-closed defaults)
affects: [06-04-deploy-and-launch, phase-6-verification, any future background job]

# Tech tracking
tech-stack:
  added: [apscheduler==3.10.4 (+ pytz, tzlocal, tzdata, six as transitive deps)]
  patterns:
    - "BackgroundScheduler in the FastAPI lifespan: start on startup, shutdown(wait=False) before engine.dispose()"
    - "Async CRUD driven from a scheduler worker thread via asyncio.run() with a fresh async_session_factory session"
    - "Machine-to-machine auth as its own dependency (require_cron_secret) — never reuses the admin Bearer token"
    - "Fail-closed config: an empty secret disables the trigger (503) instead of opening the endpoint"

key-files:
  created:
    - backend/app/core/scheduler.py
    - backend/tests/test_admin_expire.py
    - backend/tests/test_scheduler.py
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/app/core/config.py
    - backend/app/crud/jobs.py
    - backend/app/main.py
    - backend/app/deps.py
    - backend/app/api/v1/admin.py

key-decisions:
  - "LIFE-01 needed no code: expires_at = now() + interval '14 days' is already the server_default in the model and in migration 0001 — verified, not re-implemented"
  - "The sweep compares against the DATABASE clock (func.now()), the same clock list_published uses, so a job is never invisible on the board yet alive in the table"
  - "delete_expired_jobs is status-agnostic (published, pending, needs_review, invalid) so an unreviewed row cannot escape expiry (LIFE-03/D-03/D-04)"
  - "X-Cron-Secret header (not Authorization: Bearer) keeps the machine credential structurally separate from the admin JWT; a valid admin token gets 401 on /admin/expire"
  - "Unconfigured CRON_SECRET answers 503 'Expiração manual não configurada' instead of 401 — a deploy that forgot the env var must look like a disabled trigger, not like a wrong password"
  - "secrets.compare_digest for the secret comparison (constant time, T-06-01); secrets are compared after .strip() on both sides"
  - "SCHEDULER_ENABLED=true|false lets an operator turn the in-process clock off on multi-worker boxes or when the host spins down, leaving the CRON_SECRET endpoint as the only (idempotent) trigger"
  - "APScheduler misfire_grace_time=3600 + coalesce=True + max_instances=1: a slept/restarted process runs one catch-up sweep instead of a burst"

patterns-established:
  - "Scheduler jobs never raise into the worker thread: expire_jobs_job logs the exception and returns 0 so the next cycle retries"
  - "Background job + manual trigger share ONE CRUD function (delete_expired_jobs); only the trigger path differs"
  - "Any new machine-to-machine secret gets its own require_* dependency in app/deps.py"

requirements-completed: [LIFE-01, LIFE-02, LIFE-03, LIFE-04]

# Metrics
duration: 14min
completed: 2026-11-02
---

# Phase 6 Plan 01: Expiry Lifecycle Summary

**APScheduler runs a daily 03:00 UTC hard delete of expired jobs inside the FastAPI process, with a CRON_SECRET-protected POST /admin/expire catch-up trigger sharing the same idempotent CRUD sweep**

## Performance

- **Duration:** 14 min
- **Started:** 2026-11-02T11:56:49Z
- **Completed:** 2026-11-02T12:10:21Z
- **Tasks:** 4
- **Files modified:** 10 (3 created, 7 modified)

## Accomplishments

- `delete_expired_jobs` hard deletes every row past `expires_at` using the database clock and returns the row count — status-agnostic, so `published`, `pending`, `needs_review` and `invalid` all expire on the same 14-day rule (LIFE-02/LIFE-03, D-03/D-04).
- `app/core/scheduler.py` starts a `BackgroundScheduler` in the FastAPI lifespan with `CronTrigger(hour=3, minute=0, timezone="UTC")`; the job opens its own `AsyncSession`, commits, and swallows/logs failures so one bad night cannot kill the worker thread.
- `POST /api/v1/admin/expire` authenticated by `X-Cron-Secret` (constant-time compare) runs the same sweep and answers `{"deleted": N, "status": "ok"}` — idempotent, and refuses everything when `CRON_SECRET` is unset (503) (LIFE-04, T-06-01/T-06-02).
- LIFE-01 confirmed already satisfied by the existing schema: `expires_at` has `server_default text("now() + interval '14 days'")` in both `backend/app/models/job.py` and `backend/alembic/versions/0001_initial_jobs.py` — nothing to change.
- New tests: 7 endpoint tests (gate fail-closed, published+pending deletion, idempotency, empty table, admin-token rejection) and 4 scheduler tests (03:00 UTC trigger, idempotent start, shutdown, disable flag). Full backend suite: **222 passed, 3 skipped**.

## Task Commits

Each task was committed atomically:

1. **Task 1: Adicionar APScheduler e CRON_SECRET às dependências/config** — `e1ec31a` (feat)
2. **Task 2: Criar CRUD para hard delete de jobs expirados** — `7b0d8b3` (feat)
3. **Task 3: Criar scheduler APScheduler e integrar ao lifespan** — `9a22848` (feat)
4. **Task 4: Adicionar endpoint /admin/expire protegido por CRON_SECRET** — `25af124` (feat)
5. **Scheduler trigger regression tests** — `d8aa9b8` (test)

**Plan metadata:** `docs(06-01): complete lifecycle expiry sweep plan` (last commit on this plan)

## Files Created/Modified

- `backend/app/core/scheduler.py` *(new)* — BackgroundScheduler factory, `expire_jobs_job`, start/shutdown, `SCHEDULER_ENABLED` handling
- `backend/app/crud/jobs.py` — `delete_expired_jobs(session) -> int` (SQLAlchemy 2.x `delete()` with `expires_at < func.now()`), exported in `__all__`
- `backend/app/deps.py` — `require_cron_secret` dependency (503 when unconfigured, 401 on missing/wrong `X-Cron-Secret`, `compare_digest`)
- `backend/app/api/v1/admin.py` — `POST /admin/expire` handler returning `{deleted, status}`
- `backend/app/core/config.py` — `CRON_SECRET: str = ""` and `SCHEDULER_ENABLED: bool = True`
- `backend/app/main.py` — lifespan starts the scheduler, stops it before `engine.dispose()`
- `backend/pyproject.toml` / `backend/uv.lock` — `apscheduler==3.10.4` pinned
- `backend/tests/test_admin_expire.py` *(new)* — endpoint/gate/idempotency coverage
- `backend/tests/test_scheduler.py` *(new)* — 03:00 UTC trigger and lifecycle coverage

## Decisions Made

- **Database clock over application clock:** the sweep uses `func.now()` (transaction start in Postgres), matching `list_published`'s `expires_at > func.now()`. Using Python's `datetime.now()` would let the two sides disagree by network/clock skew.
- **`X-Cron-Secret` header, own dependency:** the cron credential is not an admin session; reusing `Authorization: Bearer` would make the machine secret and the 12h JWT interchangeable. A test asserts an admin token alone gets 401.
- **503 when `CRON_SECRET` is unset:** the plan allowed 401/403; 503 is chosen so a missing env var reads as "trigger disabled" instead of "you typed the wrong secret", while still failing closed.
- **`SCHEDULER_ENABLED` knob:** not in the plan's action text, added because the phase targets free-tier hosts that spin down (the scheduler cannot run while asleep) and Render/Railway can start more than one worker. Duplicate sweeps are harmless (idempotent), but an operator needs a switch.
- **`shutdown(wait=False)`:** never block app shutdown on an in-flight sweep; the delete is idempotent so an interrupted run is simply repeated.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `backend/requirements.txt` does not exist — dependencies live in `pyproject.toml` + `uv.lock`**
- **Found during:** Task 1 (Adicionar APScheduler)
- **Issue:** The plan's `files_modified` and action name `backend/requirements.txt`, but the backend is a `uv` project: there is no `requirements.txt` anywhere in the repo, and `.venv` has no `pip`.
- **Fix:** `uv add apscheduler==3.10.4`, which pins it in `backend/pyproject.toml`, refreshes `backend/uv.lock` and installs into `backend/.venv`.
- **Files modified:** `backend/pyproject.toml`, `backend/uv.lock`
- **Verification:** `import apscheduler` → `3.10.4`; `uv add` resolved 54 packages and installed 5 (apscheduler, pytz, tzlocal, tzdata, six).
- **Committed in:** `e1ec31a` (task 1 commit)

**2. [Rule 3 - Blocking] `backend/app/api/deps.py` in the plan is actually `backend/app/deps.py`**
- **Found during:** Task 4 (endpoint + CRON_SECRET dependency)
- **Issue:** The plan lists `backend/app/api/deps.py`; the real module (imported by every router as `from app.deps import ...`) is `backend/app/deps.py`. Creating the listed path would have added a dead duplicate module.
- **Fix:** `require_cron_secret` added to `backend/app/deps.py` next to `require_admin`, and exported in `__all__`.
- **Files modified:** `backend/app/deps.py`
- **Verification:** `test_admin_expire.py` exercises the dependency through the app's dependency graph (7/7 green).
- **Committed in:** `25af124` (task 4 commit)

**3. [Rule 2 - Missing Critical] `SCHEDULER_ENABLED` setting**
- **Found during:** Task 3 (scheduler + lifespan)
- **Issue:** The plan starts a `BackgroundScheduler` unconditionally. On a free-tier host that spins down, and on any multi-worker deployment, that is either useless (asleep) or duplicated (one scheduler per worker), with no way to opt out before the deploy plan (`06-04`) changes hosting.
- **Fix:** `SCHEDULER_ENABLED: bool = True` in `Settings`; `start_scheduler()` logs and returns `None` when false, leaving the `CRON_SECRET` endpoint as the trigger.
- **Files modified:** `backend/app/core/config.py`, `backend/app/core/scheduler.py`
- **Verification:** `test_scheduler_can_be_disabled` asserts `start_scheduler() is None`.
- **Committed in:** `9a22848` / `d8aa9b8`

**4. [Rule 2 - Missing Critical] Scheduler trigger regression tests**
- **Found during:** Task 4 (verification of the plan's "job agendado 03:00 UTC" checklist item)
- **Issue:** The plan's Task 3 automated check only proved the module imports; nothing pinned the cron hour/timezone, so a future edit could silently move the sweep.
- **Fix:** `backend/tests/test_scheduler.py` asserts `next_run_time.hour == 3`, minute 0, zero UTC offset, idempotent start, and clean shutdown.
- **Files modified:** `backend/tests/test_scheduler.py` (new)
- **Verification:** 4/4 green.
- **Committed in:** `d8aa9b8`

---

**Total deviations:** 4 auto-fixed (2 blocking, 2 missing critical)
**Impact on plan:** Task 1 was blocked by a nonexistent file and Task 4 pointed at a nonexistent module path — both resolved to the real project layout with no behavior change. The two additions (`SCHEDULER_ENABLED`, trigger tests) close an operational gap the deploy plan would otherwise hit and protect the 03:00 UTC contract. No scope creep: no new tables, no community schema or API changes.

## Issues Encountered

- While Task 4 was in progress the repository branch was renamed from `05-04-admin-review-wave2` to `main` by tooling outside this agent, and an external `first commit` swept the staged Task 4 files (plus the orchestrator's STATE.md edit) into one commit. Fixed with `git reset --soft HEAD~1` (no work lost), STATE.md unstaged back to the working tree, and Task 4 re-committed atomically as `25af124`.
- Pre-existing warning in `tests/test_extract_api.py::test_extract_commit_failure_rolls_back_no_rows` (`SAWarning: transaction already deassociated from connection`) — unrelated to this plan, left untouched.

## User Setup Required

None in code. The new environment variables belong to the deploy plan (`06-04`):

| Variable | Required | Behavior when absent |
|----------|----------|----------------------|
| `CRON_SECRET` | Only for the manual/catch-up trigger | `POST /admin/expire` answers 503; scheduler still runs |
| `SCHEDULER_ENABLED` | Optional (default `true`) | In-process 03:00 UTC sweep runs |

## Known Stubs

None — no placeholder values, mock data sources or unfinished UI paths were introduced by this plan.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: unauthenticated-endpoint-surface | backend/app/api/v1/admin.py | New externally reachable `POST /api/v1/admin/expire` that hard deletes rows; guarded by `X-Cron-Secret` (503 when unset, 401 otherwise) — registered in the plan's threat model as T-06-01/T-06-02, covered by tests |

## Next Phase Readiness

- LIFE-01..04 are implemented and covered; `06-02` (trust/report) and `06-03` (legal pages) can proceed without touching the scheduler.
- `06-04` (deploy) must set `CRON_SECRET` in the backend environment and decide `SCHEDULER_ENABLED` per host; the free-tier spin-down makes the endpoint the reliable catch-up path — document it in the cold-start notes.
- Recommendation for `06-04`: the single-process assumption behind D-01 is now explicit in code comments; if the host runs multiple workers, set `SCHEDULER_ENABLED=false` and drive the sweep from an external cron hitting `/admin/expire`.

## Self-Check: PASSED

- All 8 implementation files exist on disk (3 created, 5 modified).
- All 5 task commits are reachable: `e1ec31a`, `7b0d8b3`, `9a22848`, `25af124`, `d8aa9b8`.
- `backend` suite re-run after the last commit: 222 passed, 3 skipped (live Turnstile opt-in only).

---
*Phase: 06-lifecycle-trust-legal-launch*
*Completed: 2026-11-02*
