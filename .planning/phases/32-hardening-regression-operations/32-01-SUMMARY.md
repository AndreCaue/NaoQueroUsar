---
phase: 32-hardening-regression-operations
plan: 01
subsystem: testing
tags: [pytest, instagram, facebook, hardening, regression, social-publish]

# Dependency graph
requires:
  - phase: 31-independent-publish-pipeline
    provides: Provider-aware IG/FB publish pipeline, reconciliation, rate-limit, retry/idempotency contracts
provides:
  - HARD-01 backend pytest coverage for IG draft generation/normalization and FB safe error contracts
  - Explicit HARD-01/FB regression gate command with green evidence
  - Traceable scenario mapping for IG draft/validation, idempotency, retry, ambiguity, rate limit, safe error mapping, and FB regression
affects: [32-02, phase-verification, social-publish]

# Tech tracking
tech-stack:
  added: []
  patterns: [behavioral pytest contracts, provider-aware regression gate selection, safe error-message assertions]

key-files:
  created: [.planning/phases/32-hardening-regression-operations/32-01-SUMMARY.md]
  modified:
    - backend/tests/test_facebook_publisher.py
    - backend/tests/test_social_post_generation.py
    - backend/tests/test_admin_social_publish.py

key-decisions:
  - "Extended existing pytest suites (no parallel snapshots) for HARD-01/FB gate per D-01/D-03/D-05."
  - "Recorded HARD-01 IG draft/validation boundary: backend-enforced rules covered by pytest; >30 hashtags warning and link-na-bio CTA remain Phase 30 D-09 UI-only contracts."
  - "Stabilized two existing PUBL01 approve tests with IG media validation stubs to keep the gate behavioral and green without product changes."

patterns-established:
  - "FB publisher error assertions must prove no access_token/page_access_token/token leakage."
  - "IG draft contract tests assert deterministic template, 2200 cap, link na bio, required hashtags, and no contact/confidential-company leakage."

requirements-completed: [HARD-01]

# Metrics
duration: 45min
completed: 2026-11-26
---

# Phase 32 Plan 01: Hardening, Regression & Operations Summary

**Backend pytest hardening for IG draft contracts and FB safe-error/regression gate coverage, with a green HARD-01/FB gate command**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-11-26T12:15:00Z
- **Completed:** 2026-11-26T13:00:00Z
- **Tasks:** 2
- **Files modified:** 3 test files (+ 1 summary)

## Accomplishments
- Added HARD-01 IG draft/generation backend contract tests covering deterministic template, `link na bio`, required hashtags, 2200-char cap, template_fallback draft contract, and no contact/confidential-company leakage.
- Strengthened Facebook publisher behavioral coverage to assert safe pt-BR errors and no `access_token`/`page_access_token`/`token=` leakage across transient, ambiguous, and permanent mappings.
- Executed the HARD-01/FB regression gate suite in normal pytest and confirmed green evidence (73 passed, 1 skipped, 3 warnings).

## Task Commits

Each task was committed atomically:

1. **Task 1: Estender testes HARD-01 para gaps de draft IG, erro seguro e gate FB** - `0d17e0c` (test)
2. **Task 2: Executar gate HARD-01/FB e registrar seleção de cenários rastreáveis** - `e0e028a` (test)

**Plan metadata:** `8759803` (docs: complete plan)

## Files Created/Modified
- `backend/tests/test_social_post_generation.py` - Added IG template/draft generation contract tests for HARD-01 draft/validation backend scope.
- `backend/tests/test_facebook_publisher.py` - Added FB safe error-message assertions and explicit token-leakage guard coverage.
- `backend/tests/test_admin_social_publish.py` - Added IG media-prep stubs in two PUBL01 approve tests to keep gate deterministic under current IG validation contract.
- `.planning/phases/32-hardening-regression-operations/32-01-SUMMARY.md` - Plan execution summary and gate evidence.

## HARD-01 / FB Gate Traceability

| HARD-01 Scenario / Gate | Automated Evidence | Command | Result |
|---|---|---|---|
| Draft/validação IG (backend-enforced) | `backend/tests/test_social_post_generation.py`, `backend/tests/test_ig_media_validation.py`, `backend/tests/test_admin_instagram_social_posts.py` | `cd backend && pytest -q tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_admin_instagram_social_posts.py` | Covered by gate (see full gate) |
| Idempotência | `backend/tests/test_social_idempotency.py`, `backend/tests/test_social_publish_pipeline.py` | included in HARD-01/FB gate | Covered |
| Retry/backoff | `backend/tests/test_social_retry_policy.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_admin_social_retry_api.py` | included in HARD-01/FB gate | Covered |
| Ambiguidade/reconciliação | `backend/tests/test_facebook_publisher.py`, `backend/tests/test_instagram_publisher.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_admin_instagram_social_posts.py` | included in HARD-01/FB gate | Covered |
| Rate limit / bloqueio acionável | `backend/tests/test_instagram_publisher.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_admin_instagram_social_posts.py` | included in HARD-01/FB gate | Covered |
| Mapeamento de erros seguro | `backend/tests/test_facebook_publisher.py`, `backend/tests/test_instagram_publisher.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_admin_social_status_api.py` | included in HARD-01/FB gate | Covered |
| Facebook Regression Gate (full cycle) | `test_facebook_publisher.py`, `test_social_publish_pipeline.py`, `test_admin_social_publish.py`, `test_admin_social_status_api.py`, `test_admin_social_retry_api.py`, `test_social_idempotency.py`, `test_social_retry_policy.py`, `test_social_worker_claim.py`, `test_social_publisher.py` | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_social_retry_policy.py tests/test_social_idempotency.py tests/test_admin_social_publish.py tests/test_admin_social_retry_api.py tests/test_admin_social_status_api.py tests/test_admin_instagram_social_posts.py tests/test_social_worker_claim.py tests/test_social_publisher.py` | PASS (73 passed, 1 skipped, 3 warnings) |

**Boundary (HARD-01/D-06, Phase 30 D-09):** Backend-enforced rules have automated pytest evidence: IG caption 2200 cap, deterministic template/normalization, safe text without contact email/phone leakage, no invented confidential/absent company in template contract, and existing IG media/validation contracts referenced by gate tests. `>30 hashtags` warning and "link na bio" CTA/copy orientation remain Phase 30 D-09 UI-only contracts; no backend hard-block was fabricated for `>30 hashtags`.

## Decisions Made
- Followed plan as specified for HARD-01/FB gate scope (D-01..D-08, D-15, D-16).
- Kept Facebook regression gate in normal pytest and documented it as an explicit evidence block in this summary for Plan 32-02 verification rollup.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Stabilized two PUBL01 approve gate tests for current IG media validation contract**
- **Found during:** Task 2 (HARD-01/FB gate execution)
- **Issue:** `test_approve_dispatches_fb_and_ig_independently_publ01` and `test_approve_ig_dispatch_failure_does_not_block_fb_or_site` failed with 422 because they enabled IG publish without stubbing `prepare_instagram_media`, and the approval path now enforces valid IG media.
- **Fix:** Added `fake_prepare_ok` monkeypatch in both tests, matching the existing pattern in the same file.
- **Files modified:** `backend/tests/test_admin_social_publish.py`
- **Verification:** `cd backend && pytest -q tests/test_admin_social_publish.py::test_approve_dispatches_fb_and_ig_independently_publ01 tests/test_admin_social_publish.py::test_approve_ig_dispatch_failure_does_not_block_fb_or_site tests/test_admin_social_posts_provider_filter_and_all tests/test_admin_social_retry_resolution_mismatch_and_omitted_ambiguity` passed (4 passed); full gate command passed.
- **Committed in:** `e0e028a` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking test-environment/gate stabilization)
**Impact on plan:** No product behavior change. Fix aligned tests with already-contracted IG media validation so the HARD-01/FB gate could be executed reliably.

## Issues Encountered
- Test DB schema was behind for `social_posts` IG reconciliation columns, causing admin DB tests to fail with `UndefinedColumnError: ig_container_id`. Resolved by applying existing Alembic migration to `TEST_DATABASE_URL` (`0007 -> 0008`), no code or migration-file changes.
- Full gate suite is slow in this environment (~5 min). Used `python -u -m pytest -q ...` with output capture to obtain complete evidence.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- HARD-01 automated coverage and FB regression gate command are green and traceable for Plan 32-02 to consolidate into `32-VERIFICATION.md`.
- Manual Meta live handoff items remain explicitly out of scope for this plan (D-12/D-14); do not mark executed without real credentials/evidence.

## Self-Check: PASSED

- FOUND: `.planning/phases/32-hardening-regression-operations/32-01-SUMMARY.md`
- FOUND: `0d17e0c`
- FOUND: `e0e028a`
- FOUND: `backend/tests/test_facebook_publisher.py`
- FOUND: `backend/tests/test_social_post_generation.py`
- FOUND: `backend/tests/test_admin_social_publish.py`

---
*Phase: 32-hardening-regression-operations*
*Completed: 2026-11-26*
