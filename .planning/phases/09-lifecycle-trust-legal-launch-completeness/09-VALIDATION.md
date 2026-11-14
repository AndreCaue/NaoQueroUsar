---
phase: 9
slug: lifecycle-trust-legal-launch-completeness
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-13
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + pytest-asyncio (backend, `asyncio_mode=auto`); ESLint 9 + `tsc --noEmit` + `next build` (frontend) |
| **Config file** | `backend/pyproject.toml`, `frontend/eslint.config.mjs`, `frontend/tsconfig.json` |
| **Quick run command** | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py -q` |
| **Full suite command** | `cd backend; .venv\Scripts\python.exe -m pytest -q` |
| **Frontend gate** | `cd frontend; npm run lint; npx tsc --noEmit; npm run build` |
| **Estimated runtime** | backend suite ~90–150 s; frontend gate ~120–180 s |

---

## Sampling Rate

- **After every task commit:** run the task's `<automated>` command (targeted pytest file or frontend gate)
- **After every plan wave:** run the full backend suite + frontend gate
- **Before `/gsd-verify-work`:** full suite and frontend build must be green
- **Max feedback latency:** 180 s

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | LIFE-10 | T-09-01 | `expires_at` DDL pinned as `timestamptz` + 14-day server default (stored as `'14 days'::interval`) + index | unit (DDL) | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_schema.py -q` | ✅ | ⬜ pending |
| 09-01-02 | 01 | 1 | LIFE-11, LIFE-12 | T-09-03, T-09-06 | Sweep deletes expired rows of all four statuses; future rows survive; idempotent | unit/integration | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_admin_expire.py -q` | ✅ | ⬜ pending |
| 09-01-03 | 01 | 1 | TRST-11 | T-09-04, T-09-05 | Report accept-and-log, 500-char inclusive cap, single-line log, no persistence, 429 throttle | unit | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_report_api.py -q` | ✅ | ⬜ pending |
| 09-01-04 | 01 | 1 | — (criterion 2 docs) | T-09-02 | ROADMAP/REQUIREMENTS/DEPLOY no longer claim an admin JWT authorizes `/admin/expire`; T-06-01 test untouched | static/grep + full suite | `Select-String -Path .planning\ROADMAP.md -Pattern "Bearer JWT de admin NÃO é aceito" -Quiet; cd backend; .venv\Scripts\python.exe -m pytest -q` | ✅ | ⬜ pending |
| 09-02-01 | 02 | 2 | TRST-10 | T-09-08, T-09-09 | `/privacidade` renders inside the single shell: one `<h1>`, 13 `<h2>`, tokens only, copy preserved | static/grep + tsc + build | `cd frontend; npx tsc --noEmit; npm run build` | ✅ | ⬜ pending |
| 09-02-02 | 02 | 2 | TRST-10 | T-09-07, T-09-08 | `/termos-de-uso` has 10 sections and the verbatim intermediary notice | static/grep + tsc | `Select-String -Path "frontend/app/(public)/termos-de-uso/page.tsx" -Pattern "Somos apenas meio de divulgação de vagas"` | ✅ | ⬜ pending |
| 09-02-03 | 02 | 2 | TRST-10 | T-09-10 | Footer links both `/privacidade` and `/termos-de-uso`; no orphan page | static/grep + tsc | `Select-String -Path "frontend/app/(public)/layout.tsx" -Pattern '/termos-de-uso'` | ✅ | ⬜ pending |
| 09-02-04 | 02 | 2 | TRST-12 | T-09-11, T-09-12 | Badge derives only from `status === "published"`; report dialog wired with `aria-live` | static/grep | `Select-String -Path frontend/components/board/JobCard.tsx,frontend/components/board/JobDetailDialog.tsx -Pattern "Vaga revisada"` | ✅ | ⬜ pending |
| 09-03-01 | 03 | 3 | — (criterion 6) | T-09-13 | Prod CORS fails closed on empty/`*`/trailing-slash/scheme-less; exact echo, foreign denied, report preflight OK | unit | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_cors.py tests/test_public_api.py tests/test_security_config.py -q` | ❌ W0 | ⬜ pending |
| 09-03-02 | 03 | 3 | — (criterion 6) | T-09-14, T-09-15, T-09-18 | Blueprint exposes `SCHEDULER_ENABLED`; `uv run --no-sync` boot; secrets stay `sync: false` | static + YAML parse | `Select-String -Path render.yaml -Pattern "SCHEDULER_ENABLED"; Select-String -Path render.yaml -Pattern "uv run --no-sync"` | ✅ | ⬜ pending |
| 09-03-03 | 03 | 3 | — (criterion 6) | T-09-16, T-09-17 | Smoke gate asserts the exact notice; no row pre-marked OK for production | static + PS parse | `Select-String -Path scripts/verify-deploy.ps1 -Pattern "somos apenas meio de divulga"` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/conftest.py` — shared client/session/seed fixtures already exist
- [x] pytest + pytest-asyncio already installed and configured
- [ ] `backend/tests/test_cors.py` — new file created in plan 09-03 task 1
- [ ] Intermediary-notice sentence added to `frontend/app/(public)/termos-de-uso/page.tsx` (plan 09-02 task 2) and asserted by the smoke gate (plan 09-03 task 3)

*Existing infrastructure covers everything except the new CORS test file and the new notice assertion.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Production deploy is live with `env=prod`, Turnstile `live`, CORS allow/deny correct and measured cold-start | Criterion 6 | Requires real Vercel/Render/Neon/Turnstile credentials and a human go-live decision ("option B", 2026-11-10) | Run `scripts/verify-deploy.ps1 -FrontendUrl <vercel> -BackendUrl <render>` as the first request after ~20 min idle; record in `docs/DEPLOY.md` |
| Legal copy approval | TRST-10 | Legal text is user-authored; not a software decision | Human reads `/privacidade` and `/termos-de-uso`; notices are structurally verified by tests/grep |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (`test_cors.py`, intermediary-notice assertion)
- [x] No watch-mode flags
- [x] Feedback latency < 180 s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-11-13 (planning)
