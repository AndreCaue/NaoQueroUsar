---
phase: 31
slug: independent-publish-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-25
---

# Phase 31 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend) + frontend lint/manual checks (no frontend test harness in social area) |
| **Config file** | `backend/pyproject.toml` / pytest defaults; frontend eslint config |
| **Quick run command** | `cd backend && pytest -q tests/test_social_publish_pipeline.py tests/test_admin_social_publish.py tests/test_admin_instagram_social_posts.py` |
| **Full suite command** | `cd backend && pytest -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run targeted backend social tests for touched files.
- **After every plan wave:** `cd backend && pytest -q tests/test_social_publish_pipeline.py tests/test_social_publisher.py tests/test_admin_social_publish.py tests/test_admin_instagram_social_posts.py`
- **Before `/gsd-verify-work`:** Backend social suite green + FB characterization unchanged + frontend lint/manual checks for status/retry surfaces.
- **Max feedback latency:** 45 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 31-TBD-01 | TBD | 1 | PUBL-01 | T-31-01 | FB+IG dispatch/process independent; one provider failure does not block/corrupt other | integration/unit | `cd backend && pytest -q tests/test_admin_social_publish.py tests/test_social_publish_pipeline.py -k "instagram or provider or independent"` | ❌ W0 | ⬜ pending |
| 31-TBD-02 | TBD | 1 | PUBL-02 | T-31-02 | IG 2-step container/status/publish with safe timeout and configurable Graph version; no unsafe publish on timeout | unit | `cd backend && pytest -q tests/test_instagram_publisher.py` | ❌ W0 | ⬜ pending |
| 31-TBD-03 | TBD | 1 | PUBL-03 | T-31-03 | Status/audit fields persisted/exposed safely; no secrets/tokens; IDs/permalink/timestamps present when available | integration/unit | `cd backend && pytest -q tests/test_admin_social_publish.py tests/test_social_publish_pipeline.py -k "audit or status or permalink"` | ❌ W0 | ⬜ pending |
| 31-TBD-04 | TBD | 1 | PUBL-04 | T-31-04 | Ambiguous timeout does not auto-retry; retry reconciles known container before publish; no duplicate post | unit/integration | `cd backend && pytest -q tests/test_social_publish_pipeline.py -k "ambiguous or reconcile or idempotent"` | ❌ W0 | ⬜ pending |
| 31-TBD-05 | TBD | 1 | PUBL-05 | T-31-05 | 2207042/content_publishing_limit/rate limit classified safely; no retry storm; actionable admin state | unit | `cd backend && pytest -q tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "rate or 2207042 or limit"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_instagram_publisher.py` — covers PUBL-02, PUBL-05, timeout/error mapping, permalink best-effort.
- [ ] Extend `backend/tests/test_social_publish_pipeline.py` — covers provider dispatch, D-05 publish_enabled claim, IG ambiguity/reconciliation (PUBL-01/PUBL-04).
- [ ] Extend `backend/tests/test_admin_social_publish.py` — covers worker breakdown, provider-aware retry/status/list, approve IG dispatch (PUBL-01/PUBL-03).
- [ ] Extend `backend/tests/test_admin_instagram_social_posts.py` as needed for PUBL-03 status/audit/retry semantics.

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Admin sees actionable pt-BR IG status/retry/reconciliation state in UI | PUBL-03, PUBL-04, PUBL-05 | No frontend automated tests in this area; requires visual/interaction confirmation | Open admin review/social status UI, inspect IG provider states (failed ambiguous, rate-limit blocked, published with permalink), confirm pt-BR safe messages and no secret leakage. |
| Meta Graph live publish/reconcile behavior | PUBL-02, PUBL-04, PUBL-05 | Real Meta sandbox/live behavior and permissions can differ from mocks | With approved Meta test setup, run controlled publish/retry/rate-limit scenarios and record evidence separately; do not fabricate. |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
