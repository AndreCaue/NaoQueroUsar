---
phase: 31
slug: independent-publish-pipeline
status: reconciled
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-25
reconciled_at: 2026-11-26
reconciled_by: phase-33-audit-reconciliation
phase_level_evidence: ".planning/phases/31-independent-publish-pipeline/31-VERIFICATION.md (passed, 5/5 must-haves verified, 2026-11-25T00:00:00Z)"
task_level_nyquist_evidence: "not reconciled / not executed as Nyquist per-task sign-off in this artifact"
---

# Phase 31 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

## Phase 33 Reconciliation (2026-11-26)

This artifact had internal contradiction (frontmatter reported nyquist compliant as true while `wave_0_complete: false` and tasks were pending). Phase 33 normalized it for audit clarity without fabricating task/Wave 0 execution. Per-task map and Wave 0 remain historical/stale/not Nyquist-executed unless backed by separate evidence. Phase-level implementation evidence exists in `31-VERIFICATION.md` (5/5 passed) and Phase 31 plans/summaries/tests referenced there; that is phase-level evidence, not Nyquist per-task execution.

Phase-level evidence references (reference only, not per-task Nyquist execution claims): `31-VERIFICATION.md` (passed 5/5), `31-01-SUMMARY.md`, `31-02-SUMMARY.md`, and test files named in this artifact (`backend/tests/test_instagram_publisher.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_social_publisher.py`, `backend/tests/test_admin_social_publish.py`, `backend/tests/test_admin_instagram_social_posts.py`).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend) + frontend ESLint/manual checks (no frontend test harness in social admin area) |
| **Config file** | `backend/pyproject.toml` / pytest defaults; `frontend/eslint.config.mjs` |
| **Quick run command** | `cd backend && pytest -q tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_publisher.py -k "instagram or ambiguous or reconcile or rate or publish_enabled or provider or idempotent"` |
| **Full suite command** | `cd backend && pytest -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task's `<automated>` verify command (or narrowest touched-file pytest/lint command).
- **After every plan wave:** `cd backend && pytest -q tests/test_social_publish_pipeline.py tests/test_social_publisher.py tests/test_admin_social_publish.py tests/test_admin_instagram_social_posts.py tests/test_instagram_publisher.py`
- **Before `/gsd-verify-work`:** Backend social suite green + FB characterization unchanged + frontend lint/manual checks for status/retry/audit surfaces.
- **Max feedback latency:** 45 seconds

---

## Per-task Verification Map

> Historical/stale task map — statuses not reconciled as Nyquist per-task execution by Phase 33.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 31-01-01 | 01 | 1 | PUBL-01, PUBL-02, PUBL-03, PUBL-04, PUBL-05 | T-31-03, T-31-05 | Schema/contracts expose safe IG reconciliation/audit fields; claim eligibility respects `publish_enabled`; test scaffolds cover ambiguity/rate-limit/reconciliation | unit/contract | `cd backend && pytest -q tests/test_social_publisher.py tests/test_social_publish_pipeline.py tests/test_instagram_publisher.py -k "contract or publish_enabled or ambiguous or rate or reconcile or instagram"` | ❌ W0 | ⬜ pending |
| 31-01-02 | 01 | 1 | PUBL-02, PUBL-04, PUBL-05 | T-31-01, T-31-02, T-31-03, T-31-05 | InstagramPublisher performs bounded 2-step flow; ambiguous/rate-limit outcomes classified safely with no secrets and no retry storm | unit | `cd backend && pytest -q tests/test_instagram_publisher.py tests/test_social_publisher.py -k "instagram or contract or rate or ambiguous or permalink or status"` | ❌ W0 | ⬜ pending |
| 31-01-03 | 01 | 1 | PUBL-01, PUBL-03, PUBL-04, PUBL-05 | T-31-01, T-31-03, T-31-04, T-31-05, T-31-06 | Pipeline/CRUD provider dispatch is isolated; ambiguity persists reconciliation-required with no auto-retry; claim excludes publish_enabled=false; retry-state/rate-limit blocks are safe | unit/integration | `cd backend && pytest -q tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_publisher.py -k "instagram or ambiguous or reconcile or rate or publish_enabled or provider or idempotent"` | ❌ W0 | ⬜ pending |
| 31-02-01 | 02 | 2 | PUBL-01, PUBL-03, PUBL-04, PUBL-05 | T-31-01, T-31-02, T-31-03, T-31-04, T-31-05 | Admin approve/worker/retry/status/log endpoints are provider-aware, auth-protected, reconciliation-safe, and expose only safe audit fields | integration/unit | `cd backend && pytest -q tests/test_admin_social_publish.py tests/test_admin_instagram_social_posts.py -k "approve or worker or retry or status or logs or instagram or provider"` | ✅ (extend) | ⬜ pending |
| 31-02-02 | 02 | 2 | PUBL-01, PUBL-03, PUBL-04, PUBL-05 | T-31-02, T-31-03, T-31-04, T-31-05 | Admin UI shows per-provider safe status/audit/retry states; IG reconciliation/rate-limit messaging is actionable pt-BR; no secret leakage | lint/manual | `cd frontend && npm run lint -- --file app/admin/social-posts/SocialPostsClient.tsx --file app/admin/review/EditJobDialog.tsx --file app/admin/review/ReviewQueue.tsx --file lib/api.ts` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

> Historical/stale task map — statuses not reconciled as Nyquist per-task execution by Phase 33.

- [ ] `backend/tests/test_instagram_publisher.py` — covers PUBL-02, PUBL-05, timeout/error mapping, permalink best-effort, reactive runtime-authority classification.
- [ ] Extend `backend/tests/test_social_publish_pipeline.py` — covers provider dispatch, D-05 publish_enabled claim, IG ambiguity/reconciliation, no retry storm (PUBL-01/PUBL-04/PUBL-05).
- [ ] Extend `backend/tests/test_admin_social_publish.py` — covers worker breakdown, provider-aware retry/status/list, approve IG dispatch, safe audit logs (PUBL-01/PUBL-03).
- [ ] Extend `backend/tests/test_admin_instagram_social_posts.py` as needed for PUBL-03 status/audit/reconciliation semantics.

*Wave 0 is covered by Plan 31-01 Task 1 and Plan 31-02 Task 1 test scaffolds/extensions (historical plan intent; not reconciled as executed Nyquist evidence by Phase 33).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Admin sees actionable pt-BR IG status/retry/reconciliation/rate-limit state in UI | PUBL-03, PUBL-04, PUBL-05 | No frontend automated tests in this area; requires visual/interaction confirmation | Open admin review/social status UI, inspect IG provider states (failed ambiguous, rate-limit/content-publishing-limit blocked, published with permalink), confirm pt-BR safe messages, retry semantics, and no secret leakage. |
| Meta Graph live publish/reconcile/rate-limit behavior | PUBL-02, PUBL-04, PUBL-05 | Real Meta sandbox/live behavior and permissions can differ from mocks | With approved Meta test setup, run controlled publish/retry/rate-limit scenarios and record evidence separately; do not fabricate. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies (historical plan intent; not Nyquist per-task executed evidence)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify (historical plan intent; not Nyquist per-task executed evidence)
- [ ] Wave 0 covers all MISSING references (historical plan intent; not Nyquist per-task executed evidence)
- [x] No watch-mode flags
- [x] Feedback latency < 45s
- [ ] Frontmatter Nyquist flag reconciled to `nyquist_compliant: false` for audit clarity (phase-level evidence only; no per-task execution claim)

**Approval:** reconciled for audit traceability (phase-level evidence only; Nyquist per-task execution not claimed)