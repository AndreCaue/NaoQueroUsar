---
phase: 06-lifecycle-trust-legal-launch
reviewed: 2026-11-02T00:00:00Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - backend/app/core/scheduler.py
  - backend/app/main.py
  - backend/app/db/session.py
  - backend/app/api/v1/public.py
  - backend/app/api/v1/admin.py
  - backend/app/deps.py
  - backend/app/core/config.py
  - backend/tests/test_scheduler.py
  - backend/tests/test_admin_expire.py
  - backend/tests/test_report_api.py
  - backend/tests/test_expiry_sweep_integration.py
  - frontend/lib/api.ts
  - frontend/components/board/ReportJobDialog.tsx
  - frontend/.env.example
  - render.yaml
  - .github/workflows/expire-cron.yml
  - scripts/verify-deploy.ps1
  - docs/DEPLOY.md
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 6: Code Review Report (Re-review after fixes)

**Reviewed:** 2026-11-02
**Depth:** standard
**Files Reviewed:** 18 (plus cross-referenced `app/core/ratelimit.py`, `app/core/client_ip` usage, `tests/conftest.py`, the installed `apscheduler` executor source, and a grep of `frontend/app/(public)/privacidade/page.tsx`)
**Status:** issues_found (CR-02 remains)

## Summary

The fix pass is real, not cosmetic. Every previous finding except CR-02 was traced through the code that supposedly resolves it:

- **CR-01 (cross-loop pool) — RESOLVED.** The expiry sweep now runs as an `AsyncIOScheduler` coroutine job on the same event loop that serves FastAPI and owns the shared asyncpg pool; the thread + `asyncio.run()` path is gone. Shutdown is deterministic: the scheduler is paused, in-flight sweeps are awaited with a 30 s bounded drain (`_drain_inflight`), the scheduler is then stopped, and only then does the lifespan call `engine.dispose()`. The drain wiring is sound — I checked the installed `apscheduler` source: `AsyncIOExecutor` dispatches coroutine jobs via `eventloop.create_task(...)`, so `asyncio.current_task()` inside `expire_jobs_job()` registers the actual executor task in `_inflight`, and the shutdown test (`test_shutdown_waits_for_inflight_sweep`) blocks shutdown until the sweep releases. `test_shutdown_waits_for_inflight_sweep` and `test_expiry_sweep_integration` (executes the real sweep against `TEST_DATABASE_URL` and asserts the shared pool answers afterwards) are both present and wired into the suite.
- **WR-01 (report endpoint unlimited) — RESOLVED.** `@limiter.limit("5/minute")` with a `request: Request` parameter, keyed by resolved IP, `key_style="endpoint"`; over-limit answers the shared pt-BR 429 with `Retry-After`. `test_report_is_rate_limited_per_ip` pins the 6th call → 429, and `conftest.py` resets the limiter per test so the bucket cannot leak between tests. Frontend `reportJob` surfaces a 429-specific message and the dialog renders `RATE_LIMIT_COPY`.
- **WR-02 (verify-deploy gate contradicts 503) — RESOLVED.** Check 7 now accepts 401/403 as "recusado", treats 503 as a `WARN` ("gatilho manual desativado — fail-closed"), and only throws on anything else; the message no longer claims "endpoint aberto" for a correctly fail-closed deploy. `docs/DEPLOY.md` and the script header document the same contract.
- **WR-03 (autoDeploy + migrate-on-boot) — ACCEPTABLY DISPOSITIONED.** `autoDeploy: false`; production deploys are manual and gated on review; the boot-migration risk is explicitly documented in `render.yaml` and `docs/DEPLOY.md` as known-and-temporarily-accepted (forward-only migrations, Neon snapshot before schema merges, deploy manual gate). Separating the Alembic step into a pre-deploy job is documented as future work. This is not risk-free (a broken migration still crash-loops every boot/wake), but it is now a deliberate, documented operator decision rather than a silent default — the disposition requested in the finding.
- **WR-04 (silent localhost fallback) — RESOLVED.** `resolveApiBase()` throws at module scope when `NEXT_PUBLIC_API_URL` is absent and `NODE_ENV === "production"`; the localhost default exists only in development. `frontend/.env.example` and `docs/DEPLOY.md` document the build-fails-loudly behavior.
- **WR-05 (dispose under running DELETE) — RESOLVED.** Fixed with CR-01: drain-then-stop-then-dispose ordering in the lifespan, bounded 30 s wait, `wait=True` passed to `scheduler.shutdown()` (which the asyncio executor implements as cancel-pending — the drain is the real guarantee, and the code says so), warning logged if the drain times out, and a regression test proving shutdown blocks on an in-flight sweep.
- **IN-01 (no workflow permissions) — RESOLVED.** `permissions: {}` at workflow top level.
- **IN-02 (curl retry-all-errors) — RESOLVED.** `--retry 3 --retry-connrefused --retry-delay 15 --max-time 120`; 4xx is no longer retried; comment and `docs/DEPLOY.md` match.
- **IN-03 (reportJob no timeout) — RESOLVED.** `AbortSignal.timeout(10_000)`, Abort/Timeout mapped to a pt-BR retryable `ApiError(status 0)`, and the dialog keeps its "Tentar novamente" path; 429 yields the dedicated copy.
- **IN-04 (sweep never executed in tests) — RESOLVED.** `test_expiry_sweep_integration.py` runs `expire_jobs_job()` against `TEST_DATABASE_URL`, asserts expired rows are gone, live rows survive, and `engine.connect() → SELECT 1` works afterwards; skips cleanly when the test DB is absent (same rule as the rest of the suite). Caveat: CR-01 regression protection is only as strong as the environments that set `TEST_DATABASE_URL`.
- **IN-05 (cron gate brute-force) — RESOLVED.** `@limiter.limit("10/minute")` on the `require_cron_secret` dependency (deliberately on the dependency, not the handler, because FastAPI resolves dependencies first and the 401/503 short-circuit would bypass a handler-level limit). `test_expire_probing_is_rate_limited` pins the 11th probe → 429 with `Retry-After`; 503/401 semantics are unchanged under the limit.

No new defects were found in the fix code. The one remaining launch blocker is CR-02, which is intentionally out of scope for this pass and remains open.

---

## Remaining findings

### CR-02: `/privacidade` is not shippable — pending juridical redaction and no existing privacy/LGPD contact channel

**File:** `frontend/app/(public)/privacidade/page.tsx:98, 175, 252, 258` (still present — verified by grep in this re-review), `frontend/app/(public)/layout.tsx`
**Severity:** BLOCKER (launch blocker — LGPD Art. 18/41; the phase is "trust-legal-launch")

**Issue:** The page that is supposed to establish trust and legal compliance still contains, or has been replaced with, non-launchable content. As of the latest remediation it contains clearly marked Lorem Ipsum/test copy, an unreachable `.invalid` placeholder address and a prominent warning that no legal text or LGPD channel is final. This is useful for visual development but does not authorize publication.

There is still no reachable privacy/LGPD contact channel anywhere on the site (the footer renders only the copyright line, slogan and the "Privacidade e termos" link). Under LGPD the controller must provide a reachable channel for data-subject requests; placeholder test content is not a channel. Publishing as-is fails the phase's trust/legal goal.

The contact reveal wording was corrected to accurately describe that no contacts appear in public HTML and are exposed only after the Turnstile-gated reveal.

**Status:** NOT FIXED — the explicit placeholders are now clearly labelled Lorem Ipsum/test content, and the page is `noindex`, but the launch blocker remains pending user/legal sign-off.

**Fix (unchanged):**
1. Define and publish a real, monitored privacy/contact address (e.g. `privacidade@<dominio>`) and render it on `/privacidade` and in the footer.
2. Remove all `[... pendente ...]` placeholders via lawyer review (or explicitly scope the page as interim and link a real contact).
3. Correct the "exibidos publicamente" wording to reflect the reveal flow.
4. Keep the placeholders out of the production build.

Both items are prerequisites for honestly ticking the "legal" checkbox in the go-live checklist (`docs/DEPLOY.md`), and for `scripts/verify-deploy.ps1` check 5 to gate anything meaningful.

---

## Notes for the go-live operator (not counted as findings)

- **Do not run `scripts/verify-deploy.ps1` yet.** CR-02 is open; `/privacidade` still ships clearly labelled non-legal test content and no real LGPD channel. The gate must not be used to bless a launch.
- **Residual risk accepted and documented (WR-03 disposition):** `alembic upgrade head` still runs on every boot, including free-tier wake-ups. A broken/non-idempotent migration will crash-loop the service and take the public board down; there is no schema rollback. Mitigations are procedural only (manual deploys, forward-only migrations, Neon snapshot before schema merges). The pre-deploy migration step remains future work.
- **Residual risk accepted and documented (WR-05):** if a sweep outlives the 30 s drain, shutdown proceeds to `engine.dispose()` anyway — the in-flight `DELETE` aborts and is retried by the next cycle (idempotent). This is a deliberate bounded trade-off, logged via `logger.warning`.
- **CR-01 regression coverage depends on `TEST_DATABASE_URL`:** environments without a test database skip `test_expiry_sweep_integration.py`, so the cross-loop defect class is only guarded where the integration suite actually runs.
- `render.yaml` does not set `SCHEDULER_ENABLED` (defaults `true`); on the free tier it is inert while asleep — acceptable **only if** the GitHub cron catch-up is configured and monitored, or `SCHEDULER_ENABLED=false` is set explicitly.
- No secrets are present in the reviewed tree (`render.yaml` uses `sync: false`, the workflow uses `secrets.*`/`vars.*` and now `permissions: {}`, docs carry placeholders only). `.env` not in scope.
- `verify-deploy.ps1` check 7 was NOT executed; its fix was reviewed statically only.

## Verification commands (for the operator / after CR-02 lands)

```powershell
cd backend && uv run pytest -q        # includes the sweep integration test when TEST_DATABASE_URL is set
cd frontend && npm run build          # fails in prod mode if NEXT_PUBLIC_API_URL is unset (WR-04)
powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 -FrontendUrl <url> -BackendUrl <url> -CronSecret <CRON_SECRET>
```

Do **not** treat any of the above as executed — none were run in this review (read-only, no network, no deploy).

## Disposition of previous findings

| ID | Title | Disposition |
|----|-------|-------------|
| CR-01 | Cross-loop pool contamination | Resolved — AsyncIOScheduler on the app loop + bounded drain + integration test |
| CR-02 | `/privacidade` not shippable | **Open — Lorem/noindex test copy only (out of scope; pending user/legal sign-off)** |
| WR-01 | No rate limit on report endpoint | Resolved — 5/min per-IP limiter + 429 handling + test |
| WR-02 | Deploy gate contradicts 503 | Resolved — 401/403 pass, 503 warns, other values fail |
| WR-03 | autoDeploy + migrate-on-boot | Acceptably dispositioned — manual deploys + documented accepted risk |
| WR-04 | Silent localhost API fallback | Resolved — build-time throw in production |
| WR-05 | Dispose under running DELETE | Resolved — pause/drain/wait/dispose ordering + regression test |
| IN-01 | No workflow `permissions:` | Resolved — `permissions: {}` |
| IN-02 | curl `--retry-all-errors` | Resolved — transport/connrefused-only retries |
| IN-03 | reportJob no timeout | Resolved — 10 s `AbortSignal.timeout` + retryable error path |
| IN-04 | Sweep never tested | Resolved — integration test (skips without `TEST_DATABASE_URL`) |
| IN-05 | Cron gate brute-force | Resolved — 10/min limiter on the dependency + 429 test |

---

_Reviewed: 2026-11-02_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
