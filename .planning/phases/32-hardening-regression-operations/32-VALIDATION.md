---
phase: 32
slug: hardening-regression-operations
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-26
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
| TBD | TBD | TBD | HARD-01 | T-32-01 | IG draft/validation rejects/normalizes invalid caption/media/URL with safe pt-BR errors; no secrets leaked | unit/integration | `cd backend && pytest -q tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_admin_instagram_social_posts.py -k "instagram or 2200 or caption or media or draft"` | ✅ (extend as gaps found) | ⬜ pending |
| TBD | TBD | TBD | HARD-01 | T-32-02 | IG/FB idempotency prevents duplicate publish on external_id/published/ambiguous reconciliation | unit/integration | `cd backend && pytest -q tests/test_social_idempotency.py tests/test_social_publish_pipeline.py -k "idempoten or ambiguous or reconcile"` | ✅ | ⬜ pending |
| TBD | TBD | TBD | HARD-01 | T-32-03 | Transient retry/backoff is bounded and safe; exhausted/final/manual retry semantics do not create blind retries | unit/integration | `cd backend && pytest -q tests/test_social_retry_policy.py tests/test_social_publish_pipeline.py tests/test_admin_social_retry_api.py -k "retry or backoff"` | ✅ | ⬜ pending |
| TBD | TBD | TBD | HARD-01 | T-32-04 | Ambiguous FB/IG outcomes do not trigger blind auto-retry; IG reconciliation required before publish retry | unit/integration | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "ambig"` | ✅ | ⬜ pending |
| TBD | TBD | TBD | HARD-01 | T-32-05 | IG 2207042/content_publishing_limit becomes blocked actionable state with no retry storm; FB rate/transient classification remains safe | unit/integration | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "rate or 2207042 or content_publishing_limit"` | ✅ | ⬜ pending |
| TBD | TBD | TBD | HARD-01 | T-32-06 | Error mapping remains transient/permanent/ambiguous/unknown with pt-BR safe messages and no secrets/tokens in logs/responses | unit | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "transient or permanent or ambiguous or unknown or safe"` | ✅ (extend for matrix) | ⬜ pending |
| TBD | TBD | TBD | HARD-01 | T-32-07 | Facebook Regression Gate covers full FB cycle (draft/generation, approval/site-first, async publish, status/logs seguros, retry/idempotency, reconnect/safe error) with no IG-induced regression | integration/contract | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_social_publish_pipeline.py tests/test_admin_social_publish.py tests/test_admin_social_status_api.py tests/test_admin_social_retry_api.py tests/test_social_idempotency.py -k "facebook or social"` | ✅ (extend/select explicit gate) | ⬜ pending |
| TBD | TBD | TBD | HARD-02 | N/A | Operational doc covers env vars, manual Meta checklist handoff, token expiry/reconnect/rotation, and IG publish troubleshooting states | doc/manual verification | `rg -n "Instagram|needs_reconnect|content_publishing_limit|ig_rate_limit_blocked|handoff|não executado|CRON_SECRET|MEDIA_PUBLIC_BASE_URL" docs/META-INTEGRATION-TESTING.md` | ✅ (doc exists; expand) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_facebook_publisher.py` — extend for explicit FB regression/contract cases (D-01/D-02)
- [ ] `backend/tests/test_social_publish_pipeline.py` — extend missing FB full-cycle/regression and HARD-01 traceability gaps
- [ ] Existing FB/social admin tests selected for FB gate (`test_admin_social_publish.py`, `test_admin_social_status_api.py`, `test_admin_social_retry_api.py`, `test_social_idempotency.py` as applicable) — confirm/extend coverage per D-02
- [ ] `docs/META-INTEGRATION-TESTING.md` — HARD-02 expansion (operational artifact)
- [ ] `.planning/phases/32-hardening-regression-operations/32-VERIFICATION.md` — evidence matrix + FB gate block + handoff (D-13..D-16), created during execute/verify

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

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
