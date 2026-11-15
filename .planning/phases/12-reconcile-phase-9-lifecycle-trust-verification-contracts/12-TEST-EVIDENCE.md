# Phase 12 Plan 01 - Targeted Test Evidence (D-09, D-12)

## Scope
Fresh targeted pytest evidence for Phase 9 lifecycle/trust verification reconciliation (LIFE-10/11/12/13, TRST-11, SECR-12 context), captured without changing product/runtime behavior.

## Run metadata
- **Working directory:** `backend/`
- **Run date/time:** `2026-11-15T10:17:46-03:00`
- **Exact command:** `.venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py tests/test_cors.py -q`
- **D-10 evidence commit SHA:** `261eae007933106be4c072f5256f642bdd26dba0` (`chore(12-01): commit Phase 9 backend evidence (D-10)`)
- **HEAD after Task 2:** `261eae007933106be4c072f5256f642bdd26dba0` (no cleanup commit created; obsolete root scripts `add_coldstart.py`/`add_scheduler.py` were untracked with edits already landed, removed from working tree only; `.gsd-temp/` untouched)
- **Exit code:** `1`

## Target files / contracts exercised
- `tests/test_schema.py` — JobStatus/enum/CHECK/14-day/DDL pin (timestamptz default/index)
- `tests/test_admin_expire.py` — 503/401/JWT-rejected, idempotency, future preserved, all-status sweep including `test_expire_deletes_expired_row_for_every_status`
- `tests/test_report_api.py` — cap/log-only/no persistence including `test_report_reason_at_500_chars_is_accepted_and_logged`, `test_report_persists_nothing`, throttle
- `tests/test_cors.py` — exact-origin echo, foreign-origin denial, preflight, prod rejection/acceptance

## Result summary (fresh run)
- **Counts:** `8 passed, 27 errors in 101.98s (0:01:41)`
- **Final summary line:** `8 passed, 27 errors in 101.98s (0:01:41)`
- **Status:** DB/schema not ready in this environment; targeted suite did **not** produce passing evidence.

## Honest blocker (no fabricated passing claims)
The run failed during test setup/fixture cleanup with a missing schema relation. No application/product code or migrations were modified to manufacture results.

Representative excerpt:
```text
..EEEEEEEEEEEEEEEEEEEEEEEEEEE......                                      [100%]
=================================== ERRORS ====================================
____________ ERROR at setup of test_db_rejects_invalid_enum_value _____________
...
>   ???
E   asyncpg.exceptions.UndefinedTableError: relation "jobs" does not exist

asyncpg/protocol/protocol.pyx:161: UndefinedTableError
...
E   sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) relation "jobs" does not exist
E   [SQL: DELETE FROM jobs]
E   (Background on this error at: https://sqlalche.me/e/21/f405)
```

Short test summary info (excerpt):
```text
ERROR tests/test_schema.py::test_db_rejects_invalid_enum_value - sqlalchemy.e...
ERROR tests/test_schema.py::test_job_requires_at_least_one_contact - sqlalche...
...
ERROR tests/test_admin_expire.py::test_expire_deletes_expired_row_for_every_status[pending]
ERROR tests/test_admin_expire.py::test_expire_deletes_expired_row_for_every_status[published]
ERROR tests/test_admin_expire.py::test_expire_deletes_expired_row_for_every_status[needs_review]
ERROR tests/test_admin_expire.py::test_expire_deletes_expired_row_for_every_status[invalid]
...
ERROR tests/test_report_api.py::test_report_reason_at_500_chars_is_accepted_and_logged
ERROR tests/test_report_api.py::test_report_persists_nothing - sqlalchemy.exc...
...
ERROR tests/test_cors.py::test_preflight_allows_report_post - sqlalchemy.exc....
8 passed, 27 errors in 101.98s (0:01:41)
```

## Environment / prerequisite note
DB-backed tests could not initialize because relation `"jobs"` does not exist in the configured test database/environment at run time. A migrated test database/schema is required to obtain green targeted evidence for these contracts.
