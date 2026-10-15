---
phase: 01-backend-foundation-data-admin-auth
plan: 03
subsystem: auth
tags: [fastapi, jwt, pyjwt, hs256, bcrypt, bearer, admin-auth, dependencies]

# Dependency graph
requires:
  - phase: 01-backend-foundation-data-admin-auth
    provides: "Settings (ADMIN_PASSWORD_HASH, JWT_SECRET, JWT_EXPIRES_IN), create_app(), api_router + interface-first auth/admin routers, get_session/get_settings in deps.py (plan 01-01)"
provides:
  - "backend/app/core/security.py: bcrypt password verify + HS256 JWT create/decode"
  - "backend/app/schemas/auth.py: LoginRequest + TokenResponse"
  - "POST /api/v1/auth/login issuing a 12h Bearer JWT (ADMN-01, ADMN-02)"
  - "backend/app/deps.py require_admin guard returning 401 for missing/invalid/expired/wrong-claim tokens (ADMN-03)"
  - "GET /api/v1/admin/me — proof-of-guard returning the decoded admin claims"
affects:
  - "01-backend-foundation-data-admin-auth/01-04 (tests/test_auth.py exercises these endpoints/dependency)"
  - "Phase 2 (admin extract), Phase 5 (admin review routes reuse require_admin), Phase 6 (lifecycle)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bearer JWT guard: HTTPBearer(auto_error=False) + require_admin dependency raising a uniform 401 with WWW-Authenticate: Bearer"
    - "Routers declare their own APIRouter(prefix=...) so mounting stays a single include_router in router.py (01-03/01-04 never edit router.py)"
    - "JWT decode pins algorithms=['HS256'] (alg-confusion defense, T-03-02); claims sub/role both validated"
    - "bcrypt used directly for password hashing (passlib retained-but-unused; see deviation 1)"

key-files:
  created:
    - backend/app/core/security.py
    - backend/app/schemas/__init__.py
    - backend/app/schemas/auth.py
  modified:
    - backend/app/deps.py
    - backend/app/api/v1/auth.py
    - backend/app/api/v1/admin.py
    - .planning/phases/01-backend-foundation-data-admin-auth/01-USER-SETUP.md

key-decisions:
  - "D-01/Discretion realized: JWT claims sub=admin, role=admin, iat, exp; Bearer header (no cookie)"
  - "D-02 realized: single long-lived token, JWT_EXPIRES_IN seconds (default 43200 = 12h), no refresh token"
  - "D-03 realized: master password only as ADMIN_PASSWORD_HASH; verified with bcrypt (argon2 not available)"
  - "D-04 respected: no Turnstile/rate-limit in login (deferred to Phase 3); comment left in auth.py"
  - "Password hashing uses bcrypt directly instead of passlib (passlib 1.7.4 is incompatible with the locked bcrypt 5.0.0)"

patterns-established:
  - "Uniform 401 via a single _unauthorized() helper: missing header, non-Bearer scheme, PyJWTError, and non-admin claims all map to 401 + WWW-Authenticate: Bearer"
  - "require_admin returns decoded claims so future admin routes can read sub/role"

requirements-completed: [ADMN-01, ADMN-02, ADMN-03]

# Metrics
duration: ~4min
completed: 2026-10-14
---

# Phase 01 Plan 03: Master-Admin Auth — Login JWT + `require_admin` Guard

**Env-password login issuing a 12h HS256 Bearer JWT and a `require_admin` dependency that hard-blocks every admin request without a valid admin token (`GET /api/v1/admin/me` returns 401 / admin claims).**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-10-15T02:53:37Z
- **Completed:** 2026-10-15T02:57:00Z
- **Tasks:** 2 completed
- **Files modified:** 7 (3 created, 4 modified)

## Accomplishments
- `backend/app/core/security.py`: `verify_password`/`hash_password` (bcrypt), `authenticate_password` (against `settings.ADMIN_PASSWORD_HASH`), and `create_access_token`/`decode_access_token` (HS256 with `algorithms=["HS256"]` pinned).
- `POST /api/v1/auth/login` returns `{access_token, token_type:"bearer", expires_in:43200}` for the correct env password and `401 "Senha inválida"` otherwise.
- `backend/app/deps.py` `require_admin`: `HTTPBearer(auto_error=False)` → uniform `401 "Não autenticado"` (+`WWW-Authenticate: Bearer`) for a missing header, non-Bearer scheme, invalid/expired/tampered token, or claims that are not `sub=admin`/`role=admin`.
- `GET /api/v1/admin/me` (guarded) returns the decoded claims — proof of ADMN-03.
- Verified end-to-end with `TestClient`: wrong password → 401; correct password → 200 + token; `/me` no header → 401; tampered token → 401; expired token → 401; non-Bearer scheme → 401; valid token → 200 with `sub=admin`, `role=admin`, `iat`, `exp`.

## Task Commits

Each task was committed atomically:

1. **task 1: Security utils (password hash verify + JWT) and auth schemas** - `f3f2b82` (feat)
2. **task 2: Login endpoint, require_admin dependency and protected admin route** - `9df4274` (feat)

**Plan metadata:** _(see final docs commit)_

## Files Created/Modified
- `backend/app/core/security.py` - bcrypt verify/hash + HS256 JWT create/decode; `settings.ADMIN_PASSWORD_HASH`/`JWT_SECRET`/`JWT_EXPIRES_IN`
- `backend/app/schemas/auth.py` - `LoginRequest`, `TokenResponse`
- `backend/app/schemas/__init__.py` - exports `LoginRequest`, `TokenResponse`
- `backend/app/deps.py` - added `bearer_scheme` + `require_admin` (kept `get_session`/`get_settings`)
- `backend/app/api/v1/auth.py` - `APIRouter(prefix="/auth")` + `POST /login`
- `backend/app/api/v1/admin.py` - `APIRouter(prefix="/admin")` + guarded `GET /me`
- `.planning/phases/01-backend-foundation-data-admin-auth/01-USER-SETUP.md` - hash-generation command now uses bcrypt directly

## Decisions Made
All decisions were fixed by `01-CONTEXT.md` (D-01..D-05). Two implementation choices within the plan's latitude:
- Password verification uses the `bcrypt` library directly (D-03 explicitly allows bcrypt or argon2; argon2-cffi is not installed and passlib is unusable — see deviation 1).
- Routers declare their own prefixes (`/auth`, `/admin`) rather than editing `router.py`, honoring 01-01's note that 01-03 never edits `router.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] passlib 1.7.4 is incompatible with the locked bcrypt 5.0.0**
- **Found during:** task 1 (and the plan's own verify commands, which generate a hash with passlib)
- **Issue:** The plan specifies `passlib.context.CryptContext(schemes=["bcrypt"])`, but `uv.lock` pins `bcrypt==5.0.0`. passlib 1.7.4's bcrypt backend probe (`detect_wrap_bug`) passes a >72-byte password, which bcrypt 5.x rejects with `ValueError: password cannot be longer than 72 bytes` — so `CryptContext` cannot even initialize its bcrypt backend (any `.hash`/`.verify` raises). No `pip`/`uv`/`argon2-cffi` is available in the execution environment to change the pin.
- **Fix:** Implemented `verify_password`/`hash_password` with the `bcrypt` library directly (DN-03 allows bcrypt or argon2; bcrypt 5.0.0 is already installed transitively via `passlib[bcrypt]`). Plaintext is truncated to bcrypt's 72-byte limit, and a malformed hash returns `False` rather than raising. Updated `01-USER-SETUP.md` hash-generation command to use bcrypt directly.
- **Files modified:** `backend/app/core/security.py`, `.planning/phases/01-backend-foundation-data-admin-auth/01-USER-SETUP.md`
- **Verification:** `authenticate_password('segredo')` → True, `'errado'` → False; JWT round-trip with `sub=admin`/`role=admin`/`expires_in==43200`.
- **Committed in:** `f3f2b82` (task 1) + `9df4274` (task 2, doc)

**2. [Rule 1 - Bug] Auth/admin routers were mounted without a prefix, so routes resolved to `/api/v1/login` and `/api/v1/me`**
- **Found during:** task 2 (first run of the verify command returned 404 for `/api/v1/auth/login`)
- **Issue:** Plan 01-01's `router.py` includes `auth.router`/`admin.router` with no prefix, but this plan's must_haves and ARCHITECTURE.md require `/api/v1/auth/login` and `/api/v1/admin/me`. 01-01 also explicitly states 01-03/01-04 must never edit `router.py`.
- **Fix:** Added `APIRouter(prefix="/auth")` in `auth.py` and `APIRouter(prefix="/admin")` in `admin.py` (routes stay a single unprefixed `include_router` in `router.py`).
- **Files modified:** `backend/app/api/v1/auth.py`, `backend/app/api/v1/admin.py`
- **Verification:** The task 2 verify command prints `login-guard-ok` against `/api/v1/auth/login` and `/api/v1/admin/me`.
- **Committed in:** `9df4274` (task 2)

**3. [Rule 3 - Blocking] `uv` is not installed on the executor machine**
- **Found during:** all verification steps
- **Issue:** Every `<verify>`/`<automated>` command uses `uv run …`, but `uv` is not on `PATH` (same as plan 01-02).
- **Fix:** Ran the equivalent commands directly with the project virtualenv interpreter (`backend/.venv/Scripts/python.exe`). The `pyproject.toml`/`uv.lock` dependency set is unchanged, so the commands run verbatim on a machine that has `uv`.
- **Files modified:** none (verification-only substitution)
- **Verification:** All plan verify commands produced their expected output (`auth-ok`, `login-guard-ok`).
- **Committed in:** n/a (no code change)

---

**Total deviations:** 3 auto-fixed (2 Rule 3 blocking, 1 Rule 1 bug).
**Impact on plan:** Deviation 1 is a necessary library substitution (passlib is unmaintained/broken with the locked bcrypt); deviation 2 is required to deliver the contracted route paths without violating 01-01's "never edit router.py" rule. No scope creep — all changes are within the auth surface.

## Issues Encountered
- `PyJWT` emits an `InsecureKeyLengthWarning` for the 11-byte `test-secret` used in verification — expected for a test key; the real `JWT_SECRET` is a 64-char random string per `.env.example`.
- `fastapi.testclient` emits a `StarletteDeprecationWarning` (httpx vs httpx2) — pre-existing, unrelated to this plan.

## Known Stubs
None — all code is functional; no hardcoded empty values, placeholders, or unwired data sources.

## Threat Flags
None — no new security-relevant surface beyond the plan's `<threat_model>`. Mitigations applied: T-03-02 (HS256 + pinned `algorithms`), T-03-03 (`require_admin` on the admin route), T-03-04 (bcrypt hash in env; no password/hash/secret logged; 401 carries no token), T-03-06 (12h expiry).

## User Setup Required

**External services require manual configuration.** See [01-USER-SETUP.md](./01-USER-SETUP.md) for:
- Environment variables (`ADMIN_PASSWORD_HASH` — now generated with bcrypt directly, `JWT_SECRET`, `DATABASE_URL`, `TEST_DATABASE_URL`)
- Neon dashboard configuration and the `alembic upgrade head` apply step

## Next Phase Readiness
- Plan **01-04** can build `tests/test_auth.py` directly against `POST /api/v1/auth/login`, `GET /api/v1/admin/me`, and `require_admin` (all contracts from the plan's `<interfaces>` are in place).
- `require_admin` is the reusable guard for Phase 2 (extract) and Phase 5 (admin review routes).
- Deferred dependency-hygiene item: replace the now-unused `passlib[bcrypt]` dependency with a direct `bcrypt` (or `argon2-cffi`) dependency and re-lock with `uv` — cannot be done in this environment (no `uv`/`pip`); tracked in `deferred-items.md`.

---
*Phase: 01-backend-foundation-data-admin-auth*
*Completed: 2026-10-14*

## Self-Check

- [x] `backend/app/core/security.py` exists (FOUND)
- [x] `backend/app/schemas/__init__.py` exists (FOUND)
- [x] `backend/app/schemas/auth.py` exists (FOUND)
- [x] `backend/app/deps.py` modified (FOUND)
- [x] `backend/app/api/v1/auth.py` modified (FOUND)
- [x] `backend/app/api/v1/admin.py` modified (FOUND)
- [x] Task 1 commit `f3f2b82` present (FOUND)
- [x] Task 2 commit `9df4274` present (FOUND)
- [x] Task 1 acceptance re-verified (`auth-ok`: verify ok/bad, JWT sub/role, expires_in=43200)
- [x] Task 2 acceptance re-verified (`login-guard-ok`: 401 wrong/no header/tampered/expired/non-bearer; 200 valid with sub=admin/role=admin)

## Self-Check: PASSED
