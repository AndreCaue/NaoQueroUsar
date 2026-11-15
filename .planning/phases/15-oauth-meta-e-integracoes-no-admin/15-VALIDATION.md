---
phase: 15
slug: oauth-meta-e-integracoes-no-admin
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-15
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest 9.1.1 + pytest-asyncio (`asyncio_mode=auto`); Frontend: Vitest/Playwright (component/unit as needed) |
| **Config file** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd backend && pytest tests/test_meta_oauth_flow.py tests/test_meta_oauth_validation.py tests/test_meta_oauth_security.py tests/test_integrations_api.py -x` (or narrower `-k` target for touched area) |
| **Full suite command** | `cd backend && pytest` (plus relevant frontend suite if UI tests added/changed) |
| **Estimated runtime** | ~30 seconds (focused backend subset), higher for full suite |

---

## Sampling Rate

- **After every task commit:** Run the most focused automated command covering changed behavior (targeted Meta/integrations tests or single test node).
- **After every plan wave:** Run `cd backend && pytest` and relevant frontend tests for touched UI.
- **Before `/gsd-verify-work`:** Full suite must be green (record known inherited DB/browser gaps explicitly if applicable).
- **Max feedback latency:** 60 seconds for focused feedback loops where practical.

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 15-xx-01 | TBD | TBD | META-01 | V4/V5 (CSRF/state) | Start requires admin auth; callback rejects invalid/expired/forged `state`; code→token exchange and safe redirects only; no connected state persisted on failure/cancel | unit/integration (mock Graph + DB/session) | `cd backend && pytest tests/test_meta_oauth_flow.py -x` | ❌ W0 | ⬜ pending |
| 15-xx-02 | TBD | TBD | META-02 | V5 | OAuth requests use minimal scopes `pages_show_list,pages_manage_posts,pages_read_engagement` and `META_GRAPH_VERSION`-scoped URLs | unit | `cd backend && pytest tests/test_meta_oauth_flow.py -k scopes -x` | ❌ W0 | ⬜ pending |
| 15-xx-03 | TBD | TBD | META-03 | V4 | Single eligible page auto-completes; multiple pages require explicit authenticated selection; only one active connection persisted/replaced | unit/integration (mock) | `cd backend && pytest tests/test_meta_oauth_flow.py -k selection -x` | ❌ W0 | ⬜ pending |
| 15-xx-04 | TBD | TBD | META-04 | V2/V6 | `/debug_token` validation on callback/confirm and on-demand; definitive failures mark `needs_reconnect`; transient failures preserve valid connection with safe error | unit (HTTP mocked) | `cd backend && pytest tests/test_meta_oauth_validation.py -x` | ❌ W0 | ⬜ pending |
| 15-xx-05 | TBD | TBD | META-05 | V6 / info disclosure | App secret/tokens never returned to frontend, never in redirect params/logs; page token encrypted at rest | unit/security assertions | `cd backend && pytest tests/test_meta_oauth_security.py -x` | ❌ W0 | ⬜ pending |
| 15-xx-06 | TBD | TBD | META-06 | V4 | Admin Integrações UI shows safe status/states/CTAs, disconnect confirmation, and contextual banners from safe result codes; actions use authenticated API | frontend component/unit + manual smoke | `cd frontend && npx vitest run app/admin/integracoes` (if created) / manual browser check | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

> Note: task IDs/plans/waves will be finalized when PLAN.md files are created; this map is requirement-driven from 15-RESEARCH.md.

---

## Wave 0 Requirements

- [ ] `backend/tests/test_meta_oauth_flow.py` — start/callback/state/scopes/single-vs-multi page/redirects seguros (META-01/02/03)
- [ ] `backend/tests/test_meta_oauth_validation.py` — `/debug_token` parsing, definitive vs transient classification, `needs_reconnect` transitions (META-04)
- [ ] `backend/tests/test_meta_oauth_security.py` — no token/secret leakage in payloads/logs/redirects and encrypted persistence (META-05)
- [ ] `backend/tests/test_integrations_api.py` — `require_admin` guards for status/verify/select/disconnect and safe status contract (META-01/04/05/06)
- [ ] `frontend/app/admin/integracoes/*` test scaffolding (Vitest/RTL) if automated UI coverage adopted — states, CTAs, confirmation, banners (META-06)
- [ ] HTTP mock infrastructure for Graph API (`httpx` MockTransport/respx or repo-equivalent) — no real Meta calls in CI

*Automated Graph/OAuth tests must mock external calls.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real Meta app OAuth redirect/callback in browser with configured app credentials and approved redirect URI | META-01, META-02, META-03, META-04 | Requires real Meta app configuration, browser redirect flow, and live Graph responses/permissions | Configure `META_APP_ID/SECRET/REDIRECT_URI/GRAPH_VERSION` for a dev app; in `/admin/integracoes` click Conectar, complete Meta login/consent, verify return state (connected/select_page/error) and stored safe status |
| Visual/UX confirmation of admin Integrations states, banners, and confirmation dialogs across responsive layouts | META-06 | Visual/interaction fidelity and copy clarity are hard to fully assert headlessly | Load `/admin/integracoes` in disconnected, pending selection, connected, needs_reconnect, and error states; verify CTAs, alerts, disconnect confirmation modal, and banner behavior on callback return |

*All other listed behaviors should have automated verification where feasible.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
