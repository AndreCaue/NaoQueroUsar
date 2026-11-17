---
phase: 17
slug: publicacao-assincrona-retry-idempotencia-e-status
status: audited
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-16
updated: 2026-11-17
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution and post-execution Nyquist audit.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio + httpx/ASGI fixtures (backend). Frontend: Next.js ESLint (`npm run lint`) — no unit/E2E test framework configured. |
| **Config file** | `backend/pyproject.toml` (pytest config) and existing `backend/tests/conftest.py` fixtures/helpers. Frontend: `frontend/package.json` scripts (`lint`). |
| **Quick run command** | `cd backend && python -m pytest -q tests/test_facebook_publisher.py tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py tests/test_social_idempotency.py -x` |
| **Full suite command** | `cd backend && python -m pytest -q tests/test_facebook_publisher.py tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py tests/test_social_idempotency.py tests/test_social_worker_claim.py tests/test_admin_social_status_api.py tests/test_admin_social_retry_api.py tests/test_admin_social_publish.py tests/test_admin_social_posts.py -x` (DB-backed subset for phase social flows) and `cd frontend && npm run lint` |
| **Estimated runtime** | ~180 seconds for phase social backend subset in this environment (individual DB-backed files slower), ~30 seconds frontend lint |

---

## Sampling Rate

- **After every task commit:** Run the most targeted automated checks for touched scope (publisher/pipeline/retry/admin API/backend tests; frontend lint for admin UI/API client changes).
- **After every plan wave:** Run the phase social backend subset and frontend lint for modified surfaces.
- **Before `$gsd-verify-work`:** Phase social backend subset green (12 unit/core + 27 DB-backed/API/integration tests passed in this audit, 39 total across scoped runs), frontend lint exits 0 (warnings only), and manual checks below reviewed.
- **Max feedback latency:** 180 seconds (target); DB-backed API files may take longer individually in this environment.

---

## Per-task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | PUB-01 | T-17-01, T-17-03 | Facebook Graph feed publish uses backend-only page token in memory, trusted endpoint `{version}/{page_id}/feed` with `message`/`link`, returns `external_post_id` on success, and maps errors safely. | unit (mocked httpx) | `cd backend && python -m pytest -q tests/test_facebook_publisher.py -x` | ✅ | ✅ green |
| 17-01-02 | 01 | 1 | PUB-04, PUB-05, PUB-06, PUB-07 | T-17-01, T-17-02, T-17-04 | Shared pipeline claims eligible rows with `FOR UPDATE SKIP LOCKED`, marks `publishing`, computes bounded retry/backoff, classifies transient/permanent/ambiguous/blocked safely with pt-BR summaries, persists sanitized logs/state, and avoids duplicate/ambiguous republishes. | unit/integration (pipeline/CRUD behavior, mocked publisher/DB fixtures) | `cd backend && python -m pytest -q tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py tests/test_social_idempotency.py -x` | ✅ | ✅ green |
| 17-02-01 | 02 | 2 | PUB-03, PUB-04, PUB-07, UI-01, UI-02 | T-17-06, T-17-07, T-17-08, T-17-09 | Cron worker protected by `X-Cron-Secret`/`require_cron_secret`; admin status/list/retry endpoints require admin auth, expose only safe fields/labels/reasons, and reuse the same idempotent pipeline for claims/retries/no-ops. | integration/API | `cd backend && python -m pytest -q tests/test_social_worker_claim.py tests/test_admin_social_status_api.py tests/test_admin_social_retry_api.py -x` | ✅ | ✅ green |
| 17-02-02 | 02 | 2 | PUB-02, PUB-03, PUB-07, PUB-08 | T-17-08, T-17-09, T-17-10 | Approve flow remains site-first and returns success even when social dispatch/publish fails; immediate attempt dispatch is non-blocking and post-commit via shared pipeline; no Facebook update/delete side effects in job flows. | integration/API + regression | `cd backend && python -m pytest -q tests/test_admin_social_publish.py tests/test_admin_social_posts.py -x` | ✅ | ✅ green |
| 17-03-01 | 03 | 3 | UI-01, UI-02 | T-17-11, T-17-12, T-17-13, T-17-14 | Admin UI shows pt-BR social status/badges/safe errors/published link context and offers retry with single-flight/idempotent handling only for eligible cases, with safe navigation/orientation. | frontend static/contract checks + API contract coverage | `cd frontend && npm run lint` and backend contracts: `cd backend && python -m pytest -q tests/test_admin_social_status_api.py tests/test_admin_social_retry_api.py -x` | ✅ | ✅ green (automated scope: lint + API contracts); visual/UX flows remain manual |
| 17-03-02 | 03 | 3 | UI-01, UI-02 | T-17-11, T-17-12, T-17-13 | Dedicated `/admin/social-posts` operational view and navigation expose status/links/errors and eligible retry actions using safe authenticated contracts without secret leakage. | frontend static/contract checks + API contract coverage | `cd frontend && npm run lint` and `cd backend && python -m pytest -q tests/test_admin_social_status_api.py tests/test_admin_social_retry_api.py -x` | ✅ | ✅ green (automated scope: lint + API contracts); browser flow remains manual |
| 17-04-01 | 04 | 1 | PUB-04, PUB-06, PUB-07 | T-17-02, T-17-04 | Post-claim exception recovery prevents orphaned `publishing` rows: persists safe ambiguous failure/log, increments attempts coherently, blocks auto/manual unsafe retry, and preserves idempotency when already published/external id exists. | unit (pipeline recovery/idempotency) | `cd backend && python -m pytest -q tests/test_social_publish_pipeline.py tests/test_social_idempotency.py -x` | ✅ | ✅ green |
| 17-04-02 | 04 | 1 | PUB-04, PUB-06, PUB-07, UI-02 | T-17-02, T-17-11 | Automated regression proves crash/post-claim path exits `publishing` safely and ambiguous/manual-review state is not retry-eligible, aligning backend retry state with admin-safe behavior. | unit/regression | `cd backend && python -m pytest -q tests/test_social_publish_pipeline.py -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/test_facebook_publisher.py` — PUB-01 Graph request/response/error mapping (mocked HTTP)
- [x] `backend/tests/test_social_publish_pipeline.py` — shared pipeline flow, claim/process, status transitions, logs, recovery
- [x] `backend/tests/test_social_retry_policy.py` — PUB-05/PUB-06 backoff, exhaustion, transient/permanent/ambiguous/reconnect cases
- [x] `backend/tests/test_social_worker_claim.py` — PUB-04 eligibility and protected cron worker behavior
- [x] `backend/tests/test_social_idempotency.py` — PUB-07 no-op/duplicate prevention/ambiguous handling
- [x] `backend/tests/test_admin_social_publish.py` — PUB-02/PUB-03 approve non-blocking + dispatch/pipeline reuse
- [x] `backend/tests/test_admin_social_status_api.py` — UI-01 status contract (safe fields, badges/link/error/reasons)
- [x] `backend/tests/test_admin_social_retry_api.py` — UI-02 retry eligibility/idempotency
- [x] `backend/tests/conftest.py` (and existing fixtures/helpers) — connected social account, encrypted token, due/eligible social posts, cron/admin auth helpers
- [x] Frontend validation command available for modified admin surfaces — `frontend/package.json` provides `npm run lint` (no dedicated frontend unit/E2E suite configured for phase UI)

*All planned Wave 0 artifacts exist and are covered by automated checks for this phase.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Admin UI visual/interaction behavior in browser: pt-BR badges/status placement, safe error copy, published post link, retry affordances/disabled states across review/edit and `/admin/social-posts` | UI-01, UI-02 | Visual rendering, copy/UX clarity, and real interaction states require human/browser confirmation beyond lint/API contracts | In admin review/edit and the social posts view, inspect states (sem rascunho/rascunho/agendado/publicando/publicado/falhou/cancelado), verify link visibility only when available, verify retry only for eligible failed cases and blocked/ambiguous/reconnect guidance is shown correctly |
| Cron-triggered worker flow in deployment-like setup processes due posts without blocking admin actions | PUB-03, PUB-04 | Real scheduling cadence and operational secret wiring (`CRON_SECRET`, external cron/platform) are environment-dependent | Configure `CRON_SECRET` and invoke protected worker endpoint on interval (or real cron) while approving/scheduling posts; confirm approvals return promptly and due posts progress idempotently |
| Real Meta Graph publish outcomes and realistic ambiguous timeout/confirmation races avoid duplicate publish | PUB-01, PUB-06, PUB-07 | Depends on live Graph API behavior, credentials/page state, network timing, and remote confirmation semantics not fully reproducible deterministically | With valid Meta integration, validate immediate/scheduled publish records `external_post_id`/`published_at`; simulate timeout/ambiguous outcomes and confirm no auto-republish and safe manual verification path |
| Fire-and-forget in real job lifecycle operations (edit/close/expire) does not update/remove published Facebook post | PUB-08 | Requires observing real external Facebook side effects over time | After a post is published, edit/close/expire the job in integrated environment and confirm the Facebook post remains unchanged |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 180s (target; individual DB-backed API tests may exceed in slow env but phase checks complete)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (2026-11-17 audit, automated scope)

## Validation Audit 2026-11-17

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 4 (manual-only/environmental/UX) |

**Evidence (audit run):**
- `cd backend && python -m pytest -q tests/test_facebook_publisher.py tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py tests/test_social_idempotency.py -x` → 12 passed (0.25s)
- `cd backend && python -m pytest -q tests/test_social_worker_claim.py tests/test_admin_social_status_api.py tests/test_admin_social_retry_api.py tests/test_admin_social_publish.py tests/test_admin_social_posts.py -x` → 27 passed total (worker/status/retry/publish/posts ran green in this audit; a prior combined run timed out in harness but individual files passed)
- `cd frontend && npm run lint` → exit 0, 11 warnings (0 errors)
