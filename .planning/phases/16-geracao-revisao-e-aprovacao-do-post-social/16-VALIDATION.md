---
phase: 16
slug: geracao-revisao-e-aprovacao-do-post-social
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-15
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend) + frontend lint/type/build checks (existing) |
| **Config file** | `backend/pyproject.toml` / `backend/tests/*` (existing); `frontend/package.json` scripts |
| **Quick run command** | `cd backend && pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py tests/test_admin_social_posts.py -x` |
| **Full suite command** | `cd backend && pytest -q` and frontend checks as applicable (e.g. `cd frontend && npm run lint` / `npm run build`) |
| **Estimated runtime** | ~60 seconds (targeted; full varies) |

---

## Sampling Rate

- **After every task commit:** Run targeted backend tests for touched social/admin modules (and quick frontend type/lint if UI/API contract files changed)
- **After every plan wave:** `cd backend && pytest -q` for relevant suites; frontend `lint`/`build` smoke for admin review changes
- **Before `/gsd-verify-work`:** Full suite must be green (per project/phase gates)
- **Max feedback latency:** 60 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-??-?? | — | — | POST-01 | — | No company/contact leakage in generated output; server-side policy enforcement | unit/integration (mock Groq) | `cd backend && pytest tests/test_social_post_generation.py -x` | ❌ W0 | ⬜ pending |
| 16-??-?? | — | — | POST-02 | — | LLM failure/unavailable falls back deterministically; review not blocked | unit/integration | `cd backend && pytest tests/test_social_post_generation.py -x` | ❌ W0 | ⬜ pending |
| 16-??-?? | — | — | POST-03 | — | Draft edit/save/regenerate respects persisted state and draft-only mutability rules | integration/API | `cd backend && pytest tests/test_admin_social_posts.py -x` | ❌ W0 | ⬜ pending |
| 16-??-?? | — | — | POST-04 | — | BRT schedule parsed/converted unambiguously; publish-now vs schedule persisted correctly | unit/integration | `cd backend && pytest tests/test_admin_social_posts.py -x` | ❌ W0 | ⬜ pending |
| 16-??-?? | — | — | POST-05 | — | Approved/scheduled text immutable server-side; edits/regenerate rejected | integration/API | `cd backend && pytest tests/test_admin_social_posts.py -x` | ❌ W0 | ⬜ pending |
| 16-??-?? | — | — | POST-06 | — | Default no-contact/no-company policy; link from `SITE_PUBLIC_URL/?vaga=<id>`; configurable flag; actionable error on missing/invalid URL | unit/integration | `cd backend && pytest tests/test_social_post_policy.py tests/test_admin_social_posts.py -x` | ❌ W0 | ⬜ pending |
| 16-??-?? | — | — | D-09/D-11 | — | Job publish succeeds independently of social registration failures/missing draft | integration/API | `cd backend && pytest tests/test_admin_social_posts.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_social_post_generation.py` — stubs/tests for POST-01, POST-02 (prompt/template/fallback/policy-safe output, mocked Groq)
- [ ] `backend/tests/test_social_post_policy.py` — stubs/tests for POST-06, D-15, D-17 (no company/contact, link construction, SITE_PUBLIC_URL validation, config flag behavior)
- [ ] `backend/tests/test_admin_social_posts.py` — stubs/tests for POST-03, POST-04, POST-05, D-08..D-12 (draft CRUD/upsert, approve best-effort contract, immutability, schedule conversion/persistence expectations)
- [ ] `backend/tests/conftest.py` (extend as needed) — fixtures/helpers for admin-auth requests, job fixtures, social post assertions
- [ ] Frontend validation via existing commands for `EditJobDialog.tsx`/`ReviewQueue.tsx`/`lib/api.ts` contract changes (lint/build/typecheck as configured)

*Planner should map concrete task IDs/waves and refine commands per plan scope.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| UI states/copy/interactions in admin review dialog (loading, unsaved, frozen, BRT labels, toasts) match 16-UI-SPEC | POST-03, POST-04, D-06..D-12 | Visual/interaction fidelity best confirmed in browser | Open `/admin/review`, exercise generate/regenerate/save/schedule/approve flows and compare to 16-UI-SPEC copy/states |

*All phase behaviors have automated verification targets where feasible; UI fidelity remains partially manual.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
