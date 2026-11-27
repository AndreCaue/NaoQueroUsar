---
phase: 32
slug: hardening-regression-operations
status: audited
nyquist_compliant: false
wave_0_complete: true
created: 2026-11-26
updated: 2026-11-26
---

# Phase 32 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio (backend) |
| **Config file** | `backend/pyproject.toml` / existing pytest defaults |
| **Quick run command** | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_post_generation.py tests/test_ig_media_validation.py` |
| **Full suite command** | `cd backend && pytest -q` |
| **Estimated runtime** | ~60 seconds (targeted social suite) |

---

## Sampling Rate

- **After every task commit:** Run the narrowest affected pytest command for touched tests/files
- **After every plan wave:** Run `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_social_retry_policy.py tests/test_social_idempotency.py tests/test_admin_social_publish.py tests/test_admin_social_retry_api.py tests/test_admin_social_status_api.py tests/test_admin_instagram_social_posts.py`
- **Before `/gsd-verify-work`:** Targeted HARD-01 gate green; manual Meta items remain explicit handoff (not fabricated)
- **Max feedback latency:** 60 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 32-01-01 | 01 | 1 | HARD-01 | T-32-01 | IG draft/validation enforces backend rules (2200 cap, deterministic template/normalization, safe text/no contact leak, no invented confidential company) with safe pt-BR errors; `>30 hashtags`/link-na-bio remain Phase 30 D-09 UI-only (no fabricated backend enforcement) | unit/integration | `cd backend && pytest -q tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_admin_instagram_social_posts.py -k "instagram or 2200 or caption or media or draft"` | ✅ | ✅ green |
| 32-01-01 | 01 | 1 | HARD-01 | T-32-02 | IG/FB idempotency prevents duplicate publish on external_id/published/ambiguous reconciliation | unit/integration | `cd backend && pytest -q tests/test_social_idempotency.py tests/test_social_publish_pipeline.py -k "idempoten or ambiguous or reconcile"` | ✅ | ✅ green |
| 32-01-01 | 01 | 1 | HARD-01 | T-32-03 | Transient retry/backoff is bounded and safe; exhausted/final/manual retry semantics do not create blind retries | unit/integration | `cd backend && pytest -q tests/test_social_retry_policy.py tests/test_social_publish_pipeline.py tests/test_admin_social_retry_api.py -k "retry or backoff"` | ✅ | ✅ green |
| 32-01-01 | 01 | 1 | HARD-01 | T-32-04 | Ambiguous FB/IG outcomes do not trigger blind auto-retry; IG reconciliation required before publish retry | unit/integration | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "ambig"` | ✅ | ✅ green |
| 32-01-01 | 01 | 1 | HARD-01 | T-32-05 | IG 2207042/content_publishing_limit becomes blocked actionable state with no retry storm; FB rate/transient classification remains safe | unit/integration | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "rate or 2207042 or content_publishing_limit"` | ✅ | ✅ green |
| 32-01-01 | 01 | 1 | HARD-01 | T-32-06 | Error mapping remains transient/permanent/ambiguous/unknown with pt-BR safe messages and no secrets/tokens in logs/responses | unit | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "transient or permanent or ambiguous or unknown or safe"` | ✅ | ✅ green |
| 32-01-02 | 01 | 1 | HARD-01 | T-32-07 | Facebook Regression Gate covers full FB cycle (draft/generation, approval/site-first, async publish, status/logs seguros, retry/idempotency, reconnect/safe error) with no IG-induced regression; gate runs in normal pytest and is evidenced in 32-VERIFICATION | integration/contract | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_social_retry_policy.py tests/test_social_idempotency.py tests/test_admin_social_publish.py tests/test_admin_social_retry_api.py tests/test_admin_social_status_api.py tests/test_admin_instagram_social_posts.py tests/test_social_worker_claim.py tests/test_social_publisher.py` | ✅ | ✅ green |
| 32-02-01 | 02 | 2 | HARD-02 | N/A | Operational doc covers env vars, manual Meta checklist handoff, token expiry/reconnect/rotation, and IG publish troubleshooting states; .env.example aligned canonically | doc/manual verification | `cd backend && pytest -q tests/test_docs_meta_instagram.py` | ✅ | ✅ green |
| 32-02-02 | 02 | 2 | HARD-01,HARD-02 | N/A | 32-VERIFICATION.md records HARD-01 scenario matrix, explicit Facebook Regression Gate block, and manual Meta handoff marked not executed when applicable | doc/manual verification | `python -c "from pathlib import Path; t=Path('.planning/phases/32-hardening-regression-operations/32-VERIFICATION.md').read_text(encoding='utf-8'); assert 'HARD-01 Scenario Matrix' in t; assert 'Facebook Regression Gate' in t; assert 'Manual Meta Handoff' in t"` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/test_facebook_publisher.py` — extend for explicit FB regression/contract cases (D-01/D-02)
- [x] `backend/tests/test_social_publish_pipeline.py` — extend missing FB full-cycle/regression and HARD-01 traceability gaps
- [x] Existing FB/social admin tests selected for FB gate (`test_admin_social_publish.py`, `test_admin_social_status_api.py`, `test_admin_social_retry_api.py`, `test_social_idempotency.py` as applicable) — confirm/extend coverage per D-02
- [x] `docs/META-INTEGRATION-TESTING.md` — HARD-02 expansion (operational artifact)
- [x] `.planning/phases/32-hardening-regression-operations/32-VERIFICATION.md` — evidence matrix + FB gate block + handoff (D-13..D-16), created during execute/verify

*No new test framework install expected.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Meta/Instagram/Facebook publish with real credentials and Page/IG linkage | HARD-02 | Requires Meta app credentials, Page roles/tasks, IG Business/Creator linkage, and authorized environment | Follow `docs/META-INTEGRATION-TESTING.md` handoff checklist; record sanitized result as `handoff/manual` with "não executado/não evidenciado nesta sessão" when not run |
| App Review/Advanced Access/role/task confirmation in Meta dashboard | META-03/HARD-02 context | External platform UI and permissions outside local automated test control | Capture sanitized checklist evidence only when explicitly executed by authorized operator |

*All HARD-01 scenarios must have automated pytest/doc verification; manual items are handoff-only and must not be marked passed without execution.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** partial — automated coverage green; manual Meta handoff remains (2026-11-26)

## Validation Audit 2026-11-26

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Manual-only | 2 |

**Evidence reviewed:**
- `32-01-SUMMARY.md`, `32-02-SUMMARY.md`, `32-VERIFICATION.md`
- Existing test files present for all mapped scenarios (14 backend test files + docs test)
- Quick targeted run (2026-11-26): `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_post_generation.py tests/test_ig_media_validation.py` → **29 passed in 35.38s**
- Recorded HARD-01/FB gate (32-01-SUMMARY, commit `e0e028a`): 13-file gate → **73 passed, 1 skipped, 3 warnings**
- Recorded doc gate (32-02-SUMMARY): `pytest -q tests/test_docs_meta_instagram.py` → **1 passed**

**Notes:** All HARD-01/HARD-02 automated behaviors are covered by existing pytest/doc checks. Live Meta/App Review/IG smoke remains explicit handoff/manual and is not marked executed. `nyquist_compliant` remains `false` because manual-only handoff items remain; no automated coverage gaps were found.
