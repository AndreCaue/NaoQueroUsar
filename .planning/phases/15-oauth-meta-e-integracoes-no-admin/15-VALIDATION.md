---
phase: 15
slug: oauth-meta-e-integracoes-no-admin
status: audited
nyquist_compliant: false
wave_0_complete: true
created: 2026-11-15
updated: 2026-11-15
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest 9.1.1 + pytest-asyncio (`asyncio_mode=auto`); Frontend: no automated test framework/scaffolding present for `/admin/integracoes` |
| **Config file** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd backend && pytest tests/test_meta_oauth_flow.py tests/test_meta_oauth_validation.py tests/test_meta_oauth_security.py tests/test_integrations_api.py -x` |
| **Full suite command** | `cd backend && pytest` (frontend Meta integrations UI currently manual-only) |
| **Estimated runtime** | ~2 seconds (focused backend subset, 23 tests on 2026-11-15 audit) |

---

## Sampling Rate

- **After every task commit:** Run the most focused automated command covering changed behavior (targeted Meta/integrations tests or single test node).
- **After every plan wave:** Run `cd backend && pytest` and relevant frontend checks for touched UI.
- **Before `/gsd-verify-work`:** Full suite should be green (record known inherited DB/browser gaps explicitly if applicable).
- **Max feedback latency:** 60 seconds for focused feedback loops where practical.

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | META-01/02/03/04/05 | V4/V5/V6 | Wave 0 scaffolds encode start/callback/state, scopes, selection, validation, security, and API guard expectations (offline, mocked) | unit/integration scaffolds | `cd backend && pytest --collect-only tests/test_meta_oauth_flow.py tests/test_meta_oauth_validation.py tests/test_meta_oauth_security.py tests/test_integrations_api.py` | ✅ | ✅ green (collected; implemented/covered by later plans) |
| 15-01-02 | 01 | 1 | META-03/05 | V4/V6 | Pending selection persisted server-side (encrypted/expiring nonce contract) and safe schemas avoid token/secret exposure | model/schema/migration verification | `cd backend && python -m compileall app/models/social_oauth_pending.py app/schemas/social_integrations.py` | ✅ | ✅ green (artifacts present) |
| 15-01-03 | 01 | 1 | META-01/02/03/04/05 | V2/V4/V5/V6 | Meta OAuth service implements signed state, Graph flow, definitive-vs-transient validation, encrypted single-connection persistence | unit/service + security assertions | `cd backend && pytest tests/test_meta_oauth_security.py -x` | ✅ | ✅ green |
| 15-02-01 | 02 | 2 | META-01/02/03/04/05 | V4/V5/V6 | Authenticated integrations routes + state-protected callback expose safe redirect/status/selection/disconnect contracts | integration (mocked) | `cd backend && pytest tests/test_integrations_api.py -x` | ✅ | ✅ green |
| 15-02-02 | 02 | 2 | META-01/02/03/04/05 | V2/V4/V5/V6 | End-to-end backend flow/validation/security behavior passes offline for pinned contracts | unit/integration (mocked Graph) | `cd backend && pytest tests/test_meta_oauth_flow.py tests/test_meta_oauth_validation.py tests/test_meta_oauth_security.py tests/test_integrations_api.py -x` | ✅ | ✅ green (23 passed, 2026-11-15) |
| 15-03-01 | 03 | 3 | META-06 | V4 | Typed safe frontend API helpers and admin navigation entry to Integrações | typecheck/contract markers | `cd frontend && npx tsc --noEmit --pretty false --project tsconfig.json` | ✅ | ✅ green (artifacts present; manual UX approved) |
| 15-03-02 | 03 | 3 | META-06 | V4/V6/info disclosure | Integrações UI renders safe states/CTAs/banners, pending selection, and disconnect confirmation without token exposure | manual browser + contract review | Manual: open `/admin/integracoes`, exercise states/banners/actions per 15-UI-SPEC.md | ✅ | ⚠️ manual-only (human-approved 2026-11-15) |
| 15-03-03 | 03 | 3 | META-06 | V4 | Human verification of redirect UX, visual/state fidelity, confirmations | manual checkpoint | 15-03 Task 3 human-verify checkpoint | ✅ | ⚠️ manual-only (approved) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky · manual-only*

---

## Wave 0 Requirements

- [x] `backend/tests/test_meta_oauth_flow.py` — start/callback/state/scopes/single-vs-multi page/redirects seguros (META-01/02/03)
- [x] `backend/tests/test_meta_oauth_validation.py` — `/debug_token` parsing, definitive vs transient classification, `needs_reconnect` transitions (META-04)
- [x] `backend/tests/test_meta_oauth_security.py` — no token/secret leakage in payloads/logs/redirects and encrypted persistence (META-05)
- [x] `backend/tests/test_integrations_api.py` — `require_admin` guards for status/verify/select/disconnect and safe status contract (META-01/04/05/06 backend contract)
- [ ] `frontend/app/admin/integracoes/*` automated test scaffolding (Vitest/RTL/Playwright) — **gap accepted as manual-only** (no frontend test infra/tests added; human checkpoint approved)
- [x] HTTP mock infrastructure for Graph API in tests (`httpx` mocking/stubs) — no real Meta calls in CI

*Automated Graph/OAuth tests must mock external calls.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real Meta app OAuth redirect/callback in browser with configured app credentials and approved redirect URI | META-01, META-02, META-03, META-04 | Requires real Meta app configuration, browser redirect flow, and live Graph responses/permissions | Configure `META_APP_ID/SECRET/REDIRECT_URI/GRAPH_VERSION` for a dev app; in `/admin/integracoes` click Conectar, complete Meta login/consent, verify return state (connected/select_page/error) and stored safe status |
| Admin Integrações UI states, banners, pending selection, CTAs, disconnect confirmation, and responsive/interaction fidelity | META-06 | No automated frontend tests/scaffolding for `/admin/integracoes` in repo; visual/interaction and redirect UX require browser verification (human-approved in 15-03) | Open `/admin/integracoes`; verify disconnected/pending_selection/connected/needs_reconnect/loading/error states, callback banners (`connected/cancelled/error/select_page`), selection confirmation, verify/reconnect/disconnect flows, and confirmation dialog; confirm no tokens/secrets in UI/URLs/responses |

*All other listed behaviors should have automated verification where feasible.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or accepted manual-only verification
- [x] Sampling continuity: no 3 consecutive tasks without automated/manual verification evidence
- [x] Wave 0 covers required backend MISSING references; frontend automation gap explicitly accepted as manual-only
- [x] No watch-mode flags
- [x] Feedback latency < 60s for backend automated subset
- [ ] `nyquist_compliant: true` set in frontmatter (false: META-06 automation gap remains manual-only)

**Approval:** audited (partial automation)

## Validation Audit 2026-11-15

| Metric | Count |
|--------|-------|
| Gaps found | 1 |
| Resolved | 0 |
| Escalated | 1 (manual-only, user-approved) |

**Findings:**
- META-01..META-05: COVERED by existing backend automated tests (	ests/test_meta_oauth_flow.py, 	ests/test_meta_oauth_validation.py, 	ests/test_meta_oauth_security.py, 	ests/test_integrations_api.py). Focused run: 23 passed, 1 warning in 1.60s.
- META-06: PARTIAL for automation (no automated frontend tests for /admin/integracoes found). UI artifacts exist and 15-03 human verification checkpoint was approved; accepted as manual-only per audit decision.
- No new tests generated in this audit.

