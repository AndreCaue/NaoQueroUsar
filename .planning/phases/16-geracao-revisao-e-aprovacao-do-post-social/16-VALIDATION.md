---
phase: 16
slug: geracao-revisao-e-aprovacao-do-post-social
status: audited
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-15
updated: 2026-11-17
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (backend, `asyncio_mode=auto`) + ESLint/Next.js frontend checks |
| **Config file** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`), `frontend/package.json` scripts |
| **Quick run command** | `cd backend && python -m pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py tests/test_admin_social_posts.py -x` |
| **Full suite command** | `cd backend && python -m pytest -q` (DB-backed suites require migrated test DB) and `cd frontend && npm run lint` (build smoke optional; 16-03 noted pre-existing unrelated prerender failure on `/admin/integracoes` in that environment) |
| **Estimated runtime** | ~90 seconds (targeted backend subset in current environment; DB/config dependent) |

---

## Sampling Rate

- **After every task commit:** Run targeted backend tests for touched social/admin modules (and quick frontend lint if UI/API contract files changed)
- **After every plan wave:** Targeted backend social/admin suites; frontend `npm run lint` smoke for admin review changes
- **Before `/gsd-verify-work`:** Relevant automated checks green; DB-backed/full-suite execution depends on migrated test DB environment
- **Max feedback latency:** 90 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-01-01 | 01 | 1 | POST-04, POST-06 | T-16-02, T-16-03 | Draft/schedule config and schemas support policy-safe defaults and BRT schedule inputs; approve envelope/contracts defined | unit/schema (backend) | `cd backend && python -m pytest -q tests/test_social_post_policy.py tests/test_admin_social_posts.py -x` | ✅ | ✅ green |
| 16-01-02 | 01 | 1 | POST-01, POST-02, POST-06 | T-16-01, T-16-02, T-16-04 | LLM generation uses allowed fields, applies policy scrub/link enforcement, and falls back deterministically without blocking review | unit (mocked Groq) | `cd backend && python -m pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py -x` | ✅ | ✅ green |
| 16-02-01 | 02 | 2 | POST-01, POST-02, POST-03, POST-04, POST-05, POST-06 | T-16-06, T-16-08, T-16-09, T-16-10 | Admin draft GET/generate/save endpoints enforce auth, validation, actionable SITE_PUBLIC_URL error, frozen 409, and persisted draft lifecycle | integration/API (DB-backed) | `cd backend && python -m pytest -q tests/test_admin_social_posts.py -x` | ✅ | ✅ green |
| 16-02-02 | 02 | 2 | POST-03, POST-04, POST-05, D-04, D-08..D-12 | T-16-07, T-16-08 | Approve is site-first with best-effort social registration (`registered`/`skipped`/`warning`), immutable scheduled text, and uses persisted/last-saved draft state | integration/API (DB-backed) | `cd backend && python -m pytest -q tests/test_admin_social_posts.py -x` | ✅ | ✅ green |
| 16-03-01 | 03 | 3 | POST-03, POST-04, POST-05, POST-06 | T-16-11 | Frontend API client exposes typed draft/approve contract (`/social-post`, `/social-post/generate`, approve envelope) | lint/static contract check | `cd frontend && npm run lint` | ✅ | ✅ green |
| 16-03-02 | 03 | 3 | POST-03, POST-04, POST-05, POST-06, D-05..D-12 | T-16-12, T-16-13, T-16-14 | Admin review UI wires generate/save/schedule/frozen/unsaved states and site-vs-social approve feedback per backend contract | lint/static contract check | `cd frontend && npm run lint` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/test_social_post_generation.py` — covers POST-01, POST-02 (LLM success, deterministic fallback, policy-safe output)
- [x] `backend/tests/test_social_post_policy.py` — covers POST-06, D-15, D-17 (link construction, actionable `SITE_PUBLIC_URL` error, company/contact stripping)
- [x] `backend/tests/test_admin_social_posts.py` — covers POST-03, POST-04, POST-05, D-04, D-08..D-12 (draft CRUD/upsert, schedule BRT persistence, frozen 409, approve best-effort outcomes)
- [x] `backend/tests/conftest.py` — adjusted to allow Phase 16 pure unit modules to run without configured test DB (DB-backed integration tests still require migrated DB fixtures/environment)
- [x] Frontend contract/state changes in `EditJobDialog.tsx` / `ReviewQueue.tsx` / `lib/api.ts` covered by automated lint (`npm run lint`, 0 errors; existing warnings only)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| UI states/copy/interactions in admin review dialog (loading, unsaved, frozen, BRT labels, preview/toasts) match 16-UI-SPEC | POST-03, POST-04, D-05..D-12 | Visual/interaction fidelity and browser behavior are best confirmed manually | Open `/admin/review`, exercise generate/regenerate/save/schedule/approve flows and compare to 16-UI-SPEC copy/states |

*All phase behaviors have automated verification targets where feasible; UI fidelity remains manual.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 90s (targeted automated checks)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (automated audit, 2026-11-17)

## Validation Audit 2026-11-17

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

- State A audit: existing `16-VALIDATION.md` updated to reflect implemented plans/tests and current automated results.
- Evidence (2026-11-17): `cd backend && python -m pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py tests/test_admin_social_posts.py -x` → 19 passed, 1 warning. `cd backend && python -m pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py -x` → 10 passed. `cd frontend && npm run lint` → 0 errors (11 pre-existing warnings).
- Manual-only retained: admin UI visual/interaction fidelity per 16-UI-SPEC.
