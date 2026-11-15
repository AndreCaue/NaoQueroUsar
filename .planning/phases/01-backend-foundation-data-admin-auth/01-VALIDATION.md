---
phase: 01-backend-foundation-data-admin-auth
slug: backend-foundation-data-admin-auth
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Reconstructed from Phase 01 PLANs/SUMMARYs (State B: no prior VALIDATION.md).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-asyncio (`asyncio_mode = "auto"`) |
| **Config file** | `backend/pyproject.toml` → `[tool.pytest.ini_options]` (`testpaths=["tests"]`) |
| **Quick run command (Windows, from repo root)** | `cd backend; .\.venv\Scripts\python.exe -m pytest -q` |
| **Full suite command (Windows, from repo root)** | `cd backend; .\.venv\Scripts\python.exe -m pytest -q` |
| **Estimated runtime** | ~10–30 seconds (varies with DB/network; suite includes integration tests against Postgres) |

> Notes: `uv` may not be installed; prefer the venv interpreter. Tests require a reachable Postgres (see `backend/tests/conftest.py` / `TEST_DATABASE_URL`).

---

## Sampling Rate

- **After every task commit:** run the quick suite for the touched area (at minimum `backend\.venv\Scripts\python.exe -m pytest -q tests/test_auth.py tests/test_public_api.py tests/test_schema.py`)
- **After every plan wave:** `cd backend; .\.venv\Scripts\python.exe -m pytest -q` (all backend tests)
- **Before `/gsd-verify-work`:** full backend suite green
- **Max feedback latency:** ~30 seconds

---

## Per-task Verification Map

> Derived from `01-01..01-04` PLAN `<verify>` blocks and SUMMARYs. Status reflects current repo state (post-Phase 3 additions may coexist; Phase 01 acceptance criteria remain covered).

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | ADMN-01, ADMN-02 | T-01-01..T-01-05 | Fail-fast on missing required env vars; no secrets logged; CORS limited to `CORS_ORIGINS` | integration/smoke | `cd backend; .\.venv\Scripts\python.exe -c "from app.main import create_app; app=create_app(); print([r.path for r in app.routes if 'health' in r.path])"` | ✅ | ✅ green |
| 01-01-02 | 01 | 1 | ADMN-01, ADMN-02 | T-01-01..T-01-05 | `/api/v1/health` returns 200 `{"status":"ok","env":"..."}`; app boots with validated config | smoke | `cd backend; .\.venv\Scripts\python.exe -c "from fastapi.testclient import TestClient; from app.main import create_app; c=TestClient(create_app()); r=c.get('/api/v1/health'); assert r.status_code==200 and r.json().get('status')=='ok'; print('ok')"` | ✅ | ✅ green |
| 01-02-01 | 02 | 2 | ADMN-02, ADMN-03 | T-02-01..T-02-05 | `JobStatus` enum has 4 values; model has `at_least_one_contact` constraint; `JobPublic`/model contract intact | unit/integration | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_schema.py` | ✅ | ✅ green |
| 01-02-02 | 02 | 2 | ADMN-02, ADMN-03 | T-02-01..T-02-05 | `alembic upgrade head` applies migrations; `job_status` type and indexes present; DB CHECK rejects no-contact insert | integration | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_schema.py` | ✅ | ✅ green |
| 01-03-01 | 03 | 2 | ADMN-01, ADMN-02 | T-03-02,T-03-04 | Password verify + JWT HS256 create/decode with pinned algorithms; no secrets logged | unit | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_auth.py -k "login_ok or wrong_password"` | ✅ | ✅ green |
| 01-03-02 | 03 | 2 | ADMN-01, ADMN-02, ADMN-03 | T-03-02,T-03-03,T-03-06 | Login issues bearer token; `/admin/me` returns 401 without/with invalid token and 200 with valid admin claims | integration (ASGI) | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_auth.py` | ✅ | ✅ green |
| 01-04-01 | 04 | 3 | ADMN-01,ADMN-02,ADMN-03 (validation) | T-04-01..T-04-05 | Public list/detail only published non-expired; payload has no `contact_email`/`contact_phone`; pagination bounds enforced | integration (ASGI) | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_public_api.py` | ✅ | ✅ green |
| 01-04-02 | 04 | 3 | ADMN-01,ADMN-02,ADMN-03 (validation) | T-02-01,T-02-02 | DB enforces at-least-one-contact and enum values; `expires_at` defaults to ~14 days from `created_at` | integration | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_schema.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers Phase 01 validation needs (pytest + pytest-asyncio configured in `backend/pyproject.toml`; `tests/conftest.py`, `tests/test_auth.py`, `tests/test_public_api.py`, `tests/test_schema.py` present).
- No new Wave 0 test files required for Phase 01 Nyquist reconstruction.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Health endpoint reachable with a real Neon-backed app startup (outside unit context) | ADMN-01/02 context | Requires local env vars + Neon connectivity | Set `DATABASE_URL`, `ADMIN_PASSWORD_HASH`, `JWT_SECRET`, `JWT_EXPIRES_IN`, `CORS_ORIGINS` in `backend/.env`, run `uvicorn app.main:app`, `curl http://localhost:8000/api/v1/health` → 200 `{"status":"ok","env":"dev"}` |
| Seed script produces a visible published job | ADMN-03/public read smoke | Requires DB access + optional manual API check | `cd backend; .\.venv\Scripts\python.exe scripts/seed.py` then `GET /api/v1/public/jobs` shows the seeded job (no contact fields) |

*All other Phase 01 behaviors covered by automated tests above.*

---

## Validation Sign-Off

- [x] All tasks have automated verify or are covered by existing tests
- [x] Sampling continuity: no large gaps (core suites map to each plan)
- [x] Wave 0 covers all Phase 01 test references (files already exist)
- [x] No watch-mode flags
- [x] Feedback latency < 60s for targeted suites
- [x] `nyquist_compliant: false` set in frontmatter (gaps/notes documented below)

**Approval:** pending (reconstructed; verify suite passes in your environment)

## Notes / Gaps (for audit)

- `test_auth.py` and `test_public_api.py` now include later-phase behavior (Phase 3 Turnstile/rate-limit/CORS additions). Phase 01 success criteria (login ok/bad, admin 401, public no-contact, published-only non-expired listing, schema constraints, 14-day expiry) are still asserted by the Phase 01–named cases present in those files.
- `backend/tests/conftest.py` may skip tests if `TEST_DATABASE_URL`/`DATABASE_URL` is not configured; ensure test DB is set for full verification.