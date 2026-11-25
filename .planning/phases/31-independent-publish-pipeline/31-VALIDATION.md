---
phase: 31
slug: independent-publish-pipeline
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-11-25
---

# Phase 31 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

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

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 31-01-01 | 01 | 1 | PUBL-01, PUBL-02, PUBL-03, PUBL-04, PUBL-05 | T-31-03, T-31-05 | Schema/contracts expose safe IG reconciliation/audit fields; claim eligibility respects `publish_enabled`; test scaffolds cover ambiguity/rate-limit/reconciliation | unit/contract | `cd backend && pytest -q tests/test_social_publisher.py tests/test_social_publish_pipeline.py tests/test_instagram_publisher.py -k "contract or publish_enabled or ambiguous or rate or reconcile or instagram"` | ❌ W0 | ⬜ pending |
| 31-01-02 | 01 | 1 | PUBL-01, PUBL-02, PUBL-03, PUBL-04, PUBL-05 | T-31-01, T-31-02, T-31-03, T-31-04, T-31-05, T-31-06 | IG 2-step publish is bounded/safe; ambiguity becomes reconciliation-required with no auto-retry/duplication; PUBL-05 runtime authority handled reactively from authoritative Graph limit/rate responses; no secrets in logs/errors | unit/integration | `cd backend && pytest -q tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_publisher.py -k "instagram or ambiguous or reconcile or rate or publish_enabled or provider or idempotent"` | ❌ W0 | ⬜ pending |
| 31-02-01 | 02 | 2 | PUBL-01, PUBL-03, PUBL-04, PUBL-05 | T-31-01, T-31-02, T-31-03, T-31-04, T-31-05 | Admin approve/worker/retry/status/log endpoints are provider-aware, auth-protected, reconciliation-safe, and expose only safe audit fields | integration/unit | `cd backend && pytest -q tests/test_admin_social_publish.py tests/test_admin_instagram_social_posts.py -k "approve or worker or retry or status or logs or instagram or provider"` | ✅ (extend) | ⬜ pending |
| 31-02-02 | 02 | 2 | PUBL-01, PUBL-03, PUBL-04, PUBL-05 | T-31-02, T-31-03, T-31-04, T-31-05 | Admin UI shows per-provider safe status/audit/retry states; IG reconciliation/rate-limit messaging is actionable pt-BR; no secret leakage | lint/manual | `cd frontend && npm run lint -- --file app/admin/social-posts/SocialPostsClient.tsx --file app/admin/review/EditJobDialog.tsx --file app/admin/review/ReviewQueue.tsx --file lib/api.ts` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_instagram_publisher.py` — covers PUBL-02, PUBL-05, timeout/error mapping, permalink best-effort, reactive runtime-authority classification.
- [ ] Extend `backend/tests/test_social_publish_pipeline.py` — covers provider dispatch, D-05 publish_enabled claim, IG ambiguity/reconciliation, no retry storm (PUBL-01/PUBL-04/PUBL-05).
- [ ] Extend `backend/tests/test_admin_social_publish.py` — covers worker breakdown, provider-aware retry/status/list, approve IG dispatch, safe audit logs (PUBL-01/PUBL-03).
- [ ] Extend `backend/tests/test_admin_instagram_social_posts.py` as needed for PUBL-03 status/audit/reconciliation semantics.

*Wave 0 is covered by Plan 31-01 Task 1 and Plan 31-02 Task 1 test scaffolds/extensions.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Admin sees actionable pt-BR IG status/retry/reconciliation/rate-limit state in UI | PUBL-03, PUBL-04, PUBL-05 | No frontend automated tests in this area; requires visual/interaction confirmation | Open admin review/social status UI, inspect IG provider states (failed ambiguous, rate-limit/content-publishing-limit blocked, published with permalink), confirm pt-BR safe messages, retry semantics, and no secret leakage. |
| Meta Graph live publish/reconcile/rate-limit behavior | PUBL-02, PUBL-04, PUBL-05 | Real Meta sandbox/live behavior and permissions can differ from mocks | With approved Meta test setup, run controlled publish/retry/rate-limit scenarios and record evidence separately; do not fabricate. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 45s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready
