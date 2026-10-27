---
phase: 05
slug: admin-review-area
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-27
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-asyncio 1.4.0 (backend); Vitest (frontend, optional) |
| **Config file** | `backend/pyproject.toml` (asyncio_mode=auto) |
| **Quick run command** | `cd backend; .venv\Scripts\python.exe -m pytest -q` |
| **Full suite command** | `cd backend; .venv\Scripts\python.exe -m pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend; .venv\Scripts\python.exe -m pytest -q`
- **After every plan wave:** Run `cd backend; .venv\Scripts\python.exe -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | REVW-01 | T-05-01 | require_admin on list route; 401 without token | integration | `pytest tests/test_admin_jobs.py::test_list_pending -x` | ❌ Wave 0 | ⬜ pending |
| 05-01-02 | 01 | 1 | REVW-01 | T-05-01 | needs_review tab listing | integration | `pytest tests/test_admin_jobs.py::test_list_needs_review -x` | ❌ Wave 0 | ⬜ pending |
| 05-02-01 | 02 | 2 | REVW-02 | T-05-02 | approve requires admin; 404 on missing | integration | `pytest tests/test_admin_jobs.py::test_approve -x` | ❌ Wave 0 | ⬜ pending |
| 05-02-02 | 02 | 2 | REVW-02 | T-05-02 | approve 404 path | integration | `pytest tests/test_admin_jobs.py::test_approve_404 -x` | ❌ Wave 0 | ⬜ pending |
| 05-03-01 | 03 | 2 | REVW-03 | T-05-03 | update validates city + at_least_one_contact | integration | `pytest tests/test_admin_jobs.py::test_update -x` | ❌ Wave 0 | ⬜ pending |
| 05-03-02 | 03 | 2 | REVW-03 | T-05-03 | clearing contacts -> 422 | integration | `pytest tests/test_admin_jobs.py::test_update_no_contact_422 -x` | ❌ Wave 0 | ⬜ pending |
| 05-03-03 | 03 | 2 | REVW-03 | T-05-03 | invalid city -> 422 | integration | `pytest tests/test_admin_jobs.py::test_update_bad_city_422 -x` | ❌ Wave 0 | ⬜ pending |
| 05-04-01 | 04 | 2 | REVW-04 | T-05-04 | hard delete requires admin; 404 on missing | integration | `pytest tests/test_admin_jobs.py::test_delete -x` | ❌ Wave 0 | ⬜ pending |
| 05-04-02 | 04 | 2 | REVW-04 | T-05-04 | delete 404 path | integration | `pytest tests/test_admin_jobs.py::test_delete_404 -x` | ❌ Wave 0 | ⬜ pending |
| 05-05-01 | 05 | 1 | REVW-05 | T-05-05 | JobAdmin exposes source_snippet + contact | integration | `pytest tests/test_admin_jobs.py::test_schema_includes_snippet_contact -x` | ❌ Wave 0 | ⬜ pending |
| 05-01-03 | 01 | 1 | (auth) | T-05-06 | all admin job routes reject unauthenticated (401) | integration | `pytest tests/test_admin_jobs.py::test_requires_auth -x` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_admin_jobs.py` — new test file covering REVW-01..05 + auth gate
- [ ] Reuse existing fixtures (client, db_session, admin_password, fake_turnstile) from conftest
- [ ] No new framework install needed
- [ ] Frontend: optional Vitest smoke for toast/guard; not required for phase gate (backend suite is authority)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tailwind v4 admin migration renders correctly | REVW-04 (UI) | Visual parity with public | Run `npm run dev`, open /admin/review, verify dark purple theme matches public board |
| Toast auto-dismiss + optimistic rollback | REVW-02/03/04 | UX timing | Approve a job, verify toast disappears ~3s and item removed; force 401, verify rollback |
| Client-side guard redirect | REVW-05 (access) | Browser navigation | Open /admin/review without token in sessionStorage, verify redirect to login |
| Source snippet side-by-side layout | REVW-05 | Responsive layout | Desktop: fields left, snippet right sticky; mobile: stacked accordion |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---

*Phase: 05-admin-review-area*
*Validation strategy created: 2026-10-27*
