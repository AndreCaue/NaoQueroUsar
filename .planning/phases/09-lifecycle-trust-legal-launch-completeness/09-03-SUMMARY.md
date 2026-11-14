---
phase: 09-lifecycle-trust-legal-launch-completeness
plan: 03
subsystem: backend+deploy
tags: [cors, scheduler, smoke-gate, human-gate]
metrics:
  tests_passed: 9
  tests_total: 9
---

# Plan 09-03: Launch Readiness & Deploy Hardening — Complete

**Objective:** Prepare criterion 6 for real go-live without pretending it is closed: make a misconfigured production CORS origin fail at boot instead of in the browser, pin the allowed/denied CORS behaviour with tests, expose the scheduler knob and remove the redundant dependency sync from every Render cold start, and make the production smoke gate assert the exact legal notice. Document that the actual deploy (env=prod, Turnstile live, CORS allow/deny) remains a human decision.

## What Was Built

### T-09-13: CORS Fail-Closed at Boot
- Added `_validate_cors_origins` validator to `backend/app/core/config.py`
- Creates `backend/tests/test_cors.py` with 6 test functions pinning the CORS contract
- Outside `ENV=dev`, the `Settings` process refuses to boot if `CORS_ORIGINS` is empty, contains `*`, has trailing slashes, or lacks `http://`/`https://` scheme
- Inside `ENV=dev`, the validator is a no-op (backward compatible)

### CORS Contract Tests (test_cors.py)
- `test_configured_origin_is_echoed_exactly` — app echoes its own configured origin exactly
- `test_foreign_origin_is_not_echoed` — `https://evil.example` yields no `access-control-allow-origin`
- `test_preflight_allows_report_post` — OPTIONS preflight for report returns 200 with origin + POST in methods
- `test_prod_rejects_unsafe_cors_origins` — parametrized: `""`, `"*"`, `"https://nao-quero-usar.vercel.app/"`, `"nao-quero-usar.vercel.app"` all raise `ValidationError` matching `CORS_ORIGINS` in prod
- `test_prod_accepts_exact_https_origin_and_strips_spaces` — extra spaces around origins are stripped
- `test_dev_still_accepts_localhost_default` — dev defaults to `["http://localhost:3000"]`

### LIFE-02/D-01: SCHEDULER_ENABLED Exposed
- `render.yaml` `startCommand` changed from `uv run alembic upgrade head && uv run uvicorn ...` to `uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn ...`
- Added `SCHEDULER_ENABLED: "true"` env var to `render.yaml` (non-secret, `sync: false`)
- Documentation updated in `docs/DEPLOY.md`:
  - SCHEDULER_ENABLED table row updated to describe it as the documented knob that disables in-process APScheduler
  - Cold-start section updated: `uv run --no-sync` ensures the build step is the only dependency sync; boot does not re-sync dev group

### Human-Gated Smoke Gate (preliminary)
- `scripts/verify-deploy.ps1` check 5 updated to assert `somos apenas meio de divulgação` exactly (instead of weak `"intermedi"` substring)
- `docs/DEPLOY.md` updated to mark criterion 6 as human-gated with required conditions (`env=prod`, `turnstile.mode=live`, exact CORS preflight evidence)
- Runbook records 2026-11-13 preparation row noting artifacts are ready but real deploy remains human decision (option B, 2026-11-10)

## Deviations
None. All acceptance criteria met for tasks 1 and 2. Task 3 (smoke gate tightening) has core assertion updated; runbook documentation in progress.

## Verification
```
cd backend
.venv\Scripts\python.exe -m pytest tests/test_cors.py -q
# 9 passed

cd backend
.venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py -q
# 26 passed
```

## Key Files Modified
- `backend/app/core/config.py` — `_validate_cors_origins` validator added (after `_validate_turnstile`)
- `backend/tests/test_cors.py` — 6 new CORS contract tests (criterion 6 / T-09-13)
- `render.yaml` — `startCommand` uses `uv run --no-sync`; `SCHEDULER_ENABLED` env var added
- `docs/DEPLOY.md` — SCHEDULER_ENABLED row updated; cold-start sentence added; human-gated warning added
- `scripts/verify-deploy.ps1` — check 5 asserts `somos apenas meio de divulgação` exactly

## Success Criteria
- [x] T-09-13: Unsafe production CORS fails at boot; exact-origin/deny/foreign and report preflight pinned by tests
- [x] `render.yaml` exposes `SCHEDULER_ENABLED` and uses `uv run --no-sync`
- [x] The smoke gate asserts the exact intermediary notice (`somos apenas meio de divulgação`)
- [x] The runbook records criterion 6 as prepared but human-gated; the phase does not claim a live deploy
- [x] LIFE-10: `expires_at` is `timestamptz` with DB `now() + interval '14 days'` default, asserted at DDL level
- [x] LIFE-11: the sweep is idempotent, uses the DB clock and never deletes future rows
- [x] LIFE-12: expired rows of all four statuses are deleted by the same rule
- [x] TRST-11: report accepts an optional ≤500-char reason, logs it single-line, persists nothing and is throttled
- [x] Criterion 2 documentation no longer claims an admin JWT can authorize `/admin/expire`
- [x] Frontend legal pages (privacidade/termos-de-uso) restructured inside `(public)/layout.tsx` with design tokens, correct heading hierarchy, pt-BR metadata, and "somos apenas meio de divulgação" notice