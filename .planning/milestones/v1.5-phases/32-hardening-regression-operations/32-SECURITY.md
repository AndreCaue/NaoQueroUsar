---
phase: 32
slug: hardening-regression-operations
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-26
---

# Phase 32 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Test doubles -> production service contracts | Mocks/fakes in social publish tests must assert safe behavior without bypassing production contract expectations. | Synthetic tokens/IDs, provider responses, publish payloads, error messages |
| Test output/logs -> operator evidence | Pytest output and verification evidence must not include tokens/secrets or encourage unsafe copy-paste. | Test logs, command output, verification artifacts |
| Docs/evidence -> operators | Operational docs and verification artifacts must guide safe action without exposing secrets or implying unperformed manual validation. | Env placeholders, runbook guidance, handoff status, sanitized evidence fields |
| Env config examples -> deployment | `.env.example` must document required/optional knobs without real secrets or unsafe defaults. | Env var names, placeholder values, operational budgets |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-32-01 | Information Disclosure | `backend/tests/*social*` assertions and fixtures | mitigate | FB publisher tests assert error messages do not leak `access_token`/`page_access_token`; fixtures use synthetic tokens/safe payloads. Evidence: `backend/tests/test_facebook_publisher.py`, `32-01-SUMMARY.md`, `32-VERIFICATION.md`. | closed |
| T-32-02 | Tampering | FB regression gate coverage | mitigate | Existing FB tests extended and explicit HARD-01/FB regression gate executed in normal pytest covering FB full cycle (draft/contract, approval/site-first, async publish/pipeline, status/logs safe, retry/idempotency, reconnect/safe errors). Evidence: `32-01-SUMMARY.md` (73 passed, 1 skipped, 3 warnings), `32-VERIFICATION.md` Facebook Regression Gate. | closed |
| T-32-03 | Repudiation / Audit gap | HARD-01 scenario traceability | mitigate | HARD-01 scenarios mapped to concrete test files/commands/results in `32-VERIFICATION.md` HARD-01 Scenario Matrix; no vague coverage claims. | closed |
| T-32-04 | Denial of Service | Rate-limit/retry regressions | mitigate | Behavioral tests cover IG 2207042/content_publishing_limit as actionable final block with no retry storm (`next_retry_at`/auto-retry guarded). Evidence: `backend/tests/test_instagram_publisher.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_admin_instagram_social_posts.py`, `32-VERIFICATION.md`. | closed |
| T-32-05 | Information Disclosure | `docs/META-INTEGRATION-TESTING.md`, `32-VERIFICATION.md`, `.env.example` | mitigate | Docs include explicit "never expose tokens/secrets/payloads" guidance; placeholders only; sanitized evidence fields required; no real credentials in artifacts. Evidence: `docs/META-INTEGRATION-TESTING.md`, `backend/.env.example`, `32-VERIFICATION.md`. | closed |
| T-32-06 | Repudiation | Manual Meta/App Review evidence | mitigate | Manual Meta handoff table marks items as `Não executado / não evidenciado nesta sessão` when not executed; no approval/pass claims fabricated. Evidence: `docs/META-INTEGRATION-TESTING.md` checklist, `32-VERIFICATION.md` Manual Meta Handoff. | closed |
| T-32-07 | Tampering | Env/config drift causing unsafe ops | mitigate | Canonical env/security table aligned to `backend/.env.example` and `backend/app/core/config.py`, including IG publish budgets and fail-closed/validation behavior. Evidence: `docs/META-INTEGRATION-TESTING.md` section 6, `backend/.env.example`, `backend/tests/test_docs_meta_instagram.py`. | closed |
| T-32-08 | Elevation of Privilege / Misuse | Unsafe retry/reconciliation guidance | mitigate | Troubleshooting states retry/reconcile preconditions explicitly; ambiguous/rate-limit rows forbid blind auto-retry/retry storm and direct operator to reconciliation/safe wait. Evidence: `docs/META-INTEGRATION-TESTING.md` section 7, `32-VERIFICATION.md`. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-26 | 8 | 8 | 0 | OpenCode (gsd-secure-phase) |

### 2026-11-26 — Phase 32 secure-phase verification (State B)

- **Input state:** No `*-SECURITY.md` existed; PLAN/SUMMARY artifacts present (`32-01-PLAN.md`, `32-02-PLAN.md`, summaries, verification).
- **Sources reviewed:** Plan threat registers, summaries, `32-VERIFICATION.md`, `docs/META-INTEGRATION-TESTING.md`, `backend/.env.example`, targeted test assertions in `backend/tests/test_facebook_publisher.py` and `backend/tests/test_social_post_generation.py`.
- **SUMMARY threat flags:** none found.
- **Result:** All 8 planned threats have mitigation evidence and are closed. `threats_open: 0`.

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-26