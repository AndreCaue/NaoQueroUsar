---
phase: 17
slug: publicacao-assincrona-retry-idempotencia-e-status
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-16
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio + httpx (backend, FastAPI/SQLAlchemy async stack) [ASSUMED from repo stack] |
| **Config file** | `backend/pyproject.toml` / existing `backend/tests` conventions [ASSUMED] |
| **Quick run command** | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py -x` [ASSUMED new phase test files] |
| **Full suite command** | `cd backend && pytest -q` [ASSUMED] |
| **Estimated runtime** | ~60-180 seconds [ASSUMED] |

Frontend UI work (UI-01/UI-02) should also use existing frontend validation commands (lint/type/build/tests if configured) per `frontend/package.json` when UI tasks land.

---

## Sampling Rate

- **After every task commit:** Run the most targeted automated checks for touched scope (publisher/pipeline/retry/admin API tests; frontend lint/type/build for admin UI/API client changes).
- **After every plan wave:** Run `cd backend && pytest -q` for relevant/new social/admin suites and frontend validation for modified UI surfaces.
- **Before `$gsd-verify-work`:** Full backend suite green for phase scope; frontend checks green for touched admin surfaces; manual checks below completed.
- **Max feedback latency:** 180 seconds [ASSUMED]

---

## Per-task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 17-??-?? | TBD | TBD | PUB-01 | V6 / Information Disclosure | Publish calls trusted Graph feed endpoint with decrypted backend-only token; no secrets leaked | unit/integration (mock Graph/httpx) | `cd backend && pytest -q tests/test_facebook_publisher.py -x` | ❌ W0 | ⬜ pending |
| 17-??-?? | TBD | TBD | PUB-02 | V4 Access Control | Job approval remains site-first and succeeds even if social dispatch/publish fails | integration/API | `cd backend && pytest -q tests/test_admin_social_publish.py -x` | ❌ W0 | ⬜ pending |
| 17-??-?? | TBD | TBD | PUB-03 | V4 / DoS (bounded) | Immediate attempt dispatched async after commit via same protected/shared pipeline; cron fallback compatible | integration | `cd backend && pytest -q tests/test_admin_social_publish.py -x` | ❌ W0 | ⬜ pending |
| 17-??-?? | TBD | TBD | PUB-04 | V2/V4 / Integrity | Cron worker protected by `CRON_SECRET`, claims due rows with `FOR UPDATE SKIP LOCKED` and safe transitions | integration/concurrency | `cd backend && pytest -q tests/test_social_worker_claim.py -x` | ❌ W0 | ⬜ pending |
| 17-??-?? | TBD | TBD | PUB-05 | DoS / Integrity | Backoff/attempt limits honor `SOCIAL_MAX_ATTEMPTS`/`SOCIAL_RETRY_DELAYS`; exhausted retries stop auto scheduling | unit/integration | `cd backend && pytest -q tests/test_social_retry_policy.py -x` | ❌ W0 | ⬜ pending |
| 17-??-?? | TBD | TBD | PUB-06 | V5 / Information Disclosure | Transient/permanent/ambiguous/reconnect-needed cases classified safely with pt-BR summarized errors and no secret leakage | unit | `cd backend && pytest -q tests/test_social_retry_policy.py -x` | ❌ W0 | ⬜ pending |
| 17-??-?? | TBD | TBD | PUB-07 | Integrity / Tampering | No duplicate publish on races/retries/double-click/ambiguous outcomes; `external_post_id`/published rows are no-op idempotent | integration/concurrency | `cd backend && pytest -q tests/test_social_idempotency.py -x` | ❌ W0 | ⬜ pending |
| 17-??-?? | TBD | TBD | PUB-08 | Integrity | Edit/close/expire job flows do not update/remove published Facebook post (fire-and-forget) | integration/regression | `cd backend && pytest -q tests/test_social_fire_and_forget.py -x` | ❌ W0 | ⬜ pending |
| 17-??-?? | TBD | TBD | UI-01 | V4 / Information Disclosure | Admin status views expose only safe fields (pt-BR badge/status, summarized error, published link/ID) | integration/API (+ frontend checks) | `cd backend && pytest -q tests/test_admin_social_status_api.py -x` | ❌ W0 | ⬜ pending |
| 17-??-?? | TBD | TBD | UI-02 | V2/V4 / Integrity | Manual retry is admin-protected, eligible-only, and uses the same idempotent claim/process pipeline | integration/API | `cd backend && pytest -q tests/test_admin_social_retry_api.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_facebook_publisher.py` — PUB-01 Graph request/response/error mapping (mocked HTTP)
- [ ] `backend/tests/test_social_publish_pipeline.py` — shared pipeline flow, claim/process, status transitions, logs
- [ ] `backend/tests/test_social_retry_policy.py` — PUB-05/PUB-06 backoff, exhaustion, transient/permanent/ambiguous/reconnect cases
- [ ] `backend/tests/test_social_worker_claim.py` — PUB-04 eligibility and `SKIP LOCKED`/concurrency behavior
- [ ] `backend/tests/test_social_idempotency.py` — PUB-07 no-op/duplicate prevention/manual retry races
- [ ] `backend/tests/test_admin_social_publish.py` — PUB-02/PUB-03 approve non-blocking + dispatch/cron reuse
- [ ] `backend/tests/test_admin_social_status_api.py` — UI-01 status contract (safe fields, badges/link/error)
- [ ] `backend/tests/test_admin_social_retry_api.py` — UI-02 retry eligibility/idempotency
- [ ] `backend/tests/conftest.py` (or equivalent fixtures module) — connected social account, encrypted token, due social posts, cron/admin auth helpers
- [ ] Frontend validation setup/check commands for modified admin surfaces (if not already covered by existing scripts)

*If none: "Existing infrastructure covers all phase requirements."* (Not expected; Wave 0 stubs/fixtures likely needed.)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Admin UI shows pt-BR badges/status, safe error text, published post link, and retry affordances in the intended review/edit + social posts views | UI-01, UI-02 | Visual placement/state rendering and copy/UX clarity require human/browser confirmation | In admin review/edit and the new social posts view, inspect states (rascunho/agendado/publicando/publicado/falhou/cancelado/sem rascunho), verify link visibility only when available, verify retry button only for eligible failed cases and disabled/hidden appropriately otherwise |
| Cron-triggered worker flow in deployment-like setup processes due posts without blocking admin actions | PUB-03, PUB-04 | Real scheduling cadence and operational secret wiring are environment-dependent | Configure `CRON_SECRET` and call protected worker endpoint on interval (or simulate cron) while approving/scheduling posts; confirm approvals return promptly and due posts progress |
| Ambiguous remote outcome handling avoids duplicate publish in realistic failure timing | PUB-07, D-11 | Precise timeout/remote-confirmation races are hard to fully reproduce deterministically in unit tests | Simulate timeout after provider send (or delayed persistence) and confirm system does not auto-republish; requires manual verification/retry path per safe rules |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
