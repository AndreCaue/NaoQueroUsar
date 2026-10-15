---
status: partial
phase: 01-backend-foundation-data-admin-auth
source: [01-VERIFICATION.md]
started: 2026-10-15T00:25:05Z
updated: 2026-10-15T00:25:05Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Apply the migration to Neon
expected: From `backend/` with `DATABASE_URL` set (pooled, `?ssl=require`), `alembic upgrade head` exits 0 and `alembic current` reports `0001_initial_jobs (head)`; re-running is a no-op. Spot-check: `job_status` enum exists, the 4 `idx_jobs_*` indexes exist, and `at_least_one_contact` constraint exists.
result: [pending]

### 2. Run the full test suite against a real database
expected: Create a Neon branch (or local Postgres), set `DATABASE_URL`/`TEST_DATABASE_URL`, apply the schema, run `uv run pytest -q` → `18 passed`, exit 0.
result: [pending]

### 3. Boot the backend locally against Neon
expected: With `backend/.env` populated, `uv run uvicorn app.main:app --reload` starts; `GET /api/v1/health` → 200 `{"status":"ok"}`; login returns a JWT; `/api/v1/admin/me` → 401 without token / 200 with token.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
