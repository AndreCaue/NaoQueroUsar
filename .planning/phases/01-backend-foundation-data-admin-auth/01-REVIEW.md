---
phase: 01-backend-foundation-data-admin-auth
reviewed: 2026-10-15T03:18:56Z
depth: standard
files_reviewed: 48
files_reviewed_list:
  - backend/app/api/v1/admin.py
  - backend/app/api/v1/auth.py
  - backend/app/api/v1/health.py
  - backend/app/api/v1/public.py
  - backend/app/api/v1/router.py
  - backend/app/core/config.py
  - backend/app/core/logging.py
  - backend/app/core/security.py
  - backend/app/crud/jobs.py
  - backend/app/db/base.py
  - backend/app/db/session.py
  - backend/app/deps.py
  - backend/app/main.py
  - backend/app/models/job.py
  - backend/app/schemas/auth.py
  - backend/app/schemas/job.py
  - backend/scripts/seed.py
  - backend/tests/conftest.py
  - backend/tests/test_auth.py
  - backend/tests/test_public_api.py
  - backend/tests/test_schema.py
  - backend/alembic/env.py
  - backend/alembic/versions/0001_initial_jobs.py
  - backend/pyproject.toml
  - backend/.env.example
  - backend/alembic.ini
  - backend/alembic/script.py.mako
  - backend/app/__init__.py
  - backend/app/api/__init__.py
  - backend/app/api/v1/__init__.py
  - backend/app/core/__init__.py
  - backend/app/crud/__init__.py
  - backend/app/db/__init__.py
  - backend/app/models/__init__.py
  - backend/app/schemas/__init__.py
  - backend/scripts/__init__.py
  - backend/tests/__init__.py
  - frontend/app/layout.tsx
  - frontend/app/page.tsx
  - frontend/app/globals.css
  - frontend/next.config.mjs
  - frontend/package.json
  - frontend/tsconfig.json
  - frontend/.gitignore
  - .gitignore
  - README.md
  - backend/README.md
  - backend/.python-version
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-10-15T03:18:56Z
**Depth:** standard
**Files Reviewed:** 48
**Status:** issues_found

## Summary

Phase 1 delivers a FastAPI backend (config, JWT/bcrypt admin auth, `jobs`
model + Alembic migration, contact-free public read API, health/CORS/logging)
plus a minimal Next.js skeleton and a criteria test suite. Reviewed at
`standard` depth, all 48 in-scope files were read in full.

The security-critical surfaces requested for this review are **solid** and were
traced end-to-end:

- **Contact leakage (D-18):** `JobPublic` (`backend/app/schemas/job.py`) declares
  no `contact_email`/`contact_phone`, and `public.py` only ever returns
  `JobPublic.model_validate(...)`. There is no route (admin or public) that
  serializes the full `Job` ORM object, so the contact cannot reach a public
  payload. Verified, not a finding.
- **JWT verification:** `decode_access_token` pins `algorithms=["HS256"]`
  (blocks algorithm-confusion), PyJWT enforces `exp` by default, and
  `require_admin` additionally asserts `sub == "admin"` and `role == "admin"`.
  Missing/malformed/tampered tokens are mapped to a controlled 401 with
  `WWW-Authenticate: Bearer`. No bypass found.
- **CORS:** Origin allow-list comes from `CORS_ORIGINS` (no wildcard default),
  `allow_credentials=False`, so `allow_methods=["*"]`/`allow_headers=["*"]`
  cannot be combined with credentialed cross-origin reads.
- **SQL injection:** All job queries use bound SQLAlchemy parameters
  (`select(Job).where(Job.id == job_id, ...)`); `page`/`limit` are typed `int`
  with `Query(ge=..., le=50)`. The only raw SQL is static DDL in the migration.
  No injection vector found.

No **Critical (BLOCKER)** issues were found. Four **Warnings** and four **Info**
items follow; the most actionable are the un-imported `globals.css` (dead CSS),
the `bcrypt`/`passlib` dependency mismatch, the test suite's silent fallback to
`DATABASE_URL`, and non-deterministic pagination ordering.

## Warnings

### WR-01: `globals.css` is never imported — dark theme styles are dead code

**File:** `frontend/app/layout.tsx:1` (and `frontend/app/globals.css:1`)
**Issue:** `frontend/app/globals.css` defines the app's base dark styling
(`:root { color-scheme: dark; }`, `body { background: #0f0a1a; color: #fff; ... }`),
but no file imports it. In the Next.js App Router, global CSS is only applied
when imported from a layout/module. A repo-wide search finds zero `globals`
references outside the file itself, so the stylesheet never ships and the dark
base theme is not applied. This is a real wiring defect (not a style
preference): the file's only purpose is import-time activation.
**Fix:**
```tsx
// frontend/app/layout.tsx
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
```

### WR-02: `bcrypt` is imported directly but only declared transitively via `passlib[bcrypt]`

**File:** `backend/pyproject.toml:15`
**Issue:** `backend/app/core/security.py:21` and `backend/tests/conftest.py:21`
both `import bcrypt`, but the project declares `passlib[bcrypt]>=1.7.4,<2.0.0`
and never declares `bcrypt` itself. The runtime import only works because
passlib's `bcrypt` extra happens to pull `bcrypt==5.0.0` (see `uv.lock`). The
code deliberately does **not** use passlib (the module docstring explains why);
therefore the declared dependency is misleading and the direct dependency is
implicit. Any repin/removal of passlib silently breaks password hashing at
import time. This is already noted in
`.planning/phases/01-backend-foundation-data-admin-auth/deferred-items.md`, but
it remains a latent break in the committed manifest and should be corrected
before further phases build on it.
**Fix:**
```toml
# replace the passlib line with a direct pin
-  "passlib[bcrypt]>=1.7.4,<2.0.0",
+  "bcrypt==5.0.0",
```
Then run `uv lock` to refresh `uv.lock`.

### WR-03: Test harness silently falls back to `DATABASE_URL` and issues `DELETE FROM jobs`

**File:** `backend/tests/conftest.py:31-37` and `backend/tests/conftest.py:111`
**Issue:** When `TEST_DATABASE_URL` is unset, `TEST_DATABASE_URL` is resolved
from `DATABASE_URL` (lines 31-36) and `HAS_DB` becomes `True`, so the suite runs
against whatever `DATABASE_URL` points to — i.e. the developer/dev Neon
database, not a dedicated test branch. The `db_session` fixture then executes
`DELETE FROM jobs` (line 111). The delete sits inside a transaction that is
rolled back at teardown, so it is not (today) a committed data loss; but it
violates plan 01-04's explicit constraint ("tests must never touch production
database", threat T-04-04) and leaves a live-DB `DELETE` one refactor away from
becoming destructive (e.g. any future test that commits, or an autocommit
misconfiguration). It also means assertions like `total == 1` are validated
against the wrong database.
**Fix:** Require a distinct test database; skip when it is absent instead of
falling back.
```python
TEST_DATABASE_URL = (
    os.environ.get("TEST_DATABASE_URL")
    or _FILE_ENV.get("TEST_DATABASE_URL")
)
HAS_DB = bool(TEST_DATABASE_URL)

# Keep a placeholder only so module-level get_settings() succeeds at collection
# when no test DB is configured; every test is skipped in that case.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL or (
    "postgresql+asyncpg://postgres@127.0.0.1:5432/nqu_placeholder"
)
```

### WR-04: Pagination has no deterministic tie-breaker (duplicate/missing rows)

**File:** `backend/app/crud/jobs.py:32`
**Issue:** `ORDER BY created_at DESC` is not a total order. Jobs created in the
same transaction/batch can share `created_at` (the migration's `now()` is the
transaction timestamp, and seeding/imports will create batches). With
offset-based paging (`D-14`), rows sharing a timestamp may be ordered
differently across the `items` and subsequent page queries, so a row can appear
on two pages or be skipped entirely. The count and the list can also disagree on
which rows are "on page N".
**Fix:** Add a stable secondary sort key.
```python
items_stmt = (
    select(Job)
    .where(*filters)
    .order_by(Job.created_at.desc(), Job.id.desc())
    .offset((page - 1) * limit)
    .limit(limit)
)
```

## Info

### IN-01: `/health` discloses the deployment environment name

**File:** `backend/app/api/v1/health.py:12`
**Issue:** The unauthenticated health endpoint returns `{"status": "ok", "env": settings.ENV}`,
publishing `dev`/`prod` to any caller. Minor information disclosure that
provides no operational value.
**Fix:** Return only `{"status": "ok"}`, or gate `env` behind a non-production
check if it is needed for local debugging.

### IN-02: `cors_origins_list` can yield an empty-string origin

**File:** `backend/app/core/config.py:23-25`
**Issue:** `self.CORS_ORIGINS.split(",")` on an empty or trailing-comma value
produces `[""]` entries (e.g. `CORS_ORIGINS=""` → `[""]`). An empty-string
origin is meaningless to `CORSMiddleware` and hides a misconfiguration.
**Fix:**
```python
@property
def cors_origins_list(self) -> List[str]:
    return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
```

### IN-03: `deps.py` imports `get_session`/`get_settings` solely to re-export them

**File:** `backend/app/deps.py:5-7,9`
**Issue:** `get_settings` and `get_session` are imported in `deps.py` but never
used in the module; they are only surfaced via `__all__`. This masks two
otherwise-unused imports and creates a second import path for the same symbols
(callers import `get_session` from `app.db.session` elsewhere). It invites
confusion about the canonical location.
**Fix:** Drop the re-exports from `__all__` and import these where they are
actually used, or add an explicit comment that the re-export is intentional for
backward compatibility.

### IN-04: Auth test hard-codes `expires_in == 43200` but the harness does not pin `JWT_EXPIRES_IN`

**File:** `backend/tests/test_auth.py:11` (harness: `backend/tests/conftest.py:44-53`)
**Issue:** `conftest.py` forces `DATABASE_URL`, `ADMIN_PASSWORD_HASH` and
`JWT_SECRET` via `os.environ`, but not `JWT_EXPIRES_IN`. The assertion
`body["expires_in"] == 43200` therefore depends on the local `backend/.env` not
overriding `JWT_EXPIRES_IN`; a developer with a non-default value in `.env`
gets a spurious failure. This affects test reliability.
**Fix:** Force the value in `conftest.py` alongside the other env vars:
```python
os.environ["JWT_EXPIRES_IN"] = "43200"
```

---

_Reviewed: 2026-10-15T03:18:56Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
