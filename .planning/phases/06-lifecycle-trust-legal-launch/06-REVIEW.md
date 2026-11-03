---
phase: 06-lifecycle-trust-legal-launch
reviewed: 2026-11-02T00:00:00Z
depth: standard
files_reviewed: 24
files_reviewed_list:
  - backend/app/core/scheduler.py
  - backend/tests/test_admin_expire.py
  - backend/tests/test_scheduler.py
  - backend/pyproject.toml
  - backend/app/core/config.py
  - backend/app/crud/jobs.py
  - backend/app/main.py
  - backend/app/deps.py
  - backend/app/api/v1/admin.py
  - backend/tests/test_report_api.py
  - frontend/components/board/ReportJobDialog.tsx
  - backend/app/api/v1/public.py
  - backend/app/schemas/job.py
  - frontend/lib/api.ts
  - frontend/components/board/JobCard.tsx
  - frontend/components/board/JobDetailDialog.tsx
  - frontend/app/(public)/privacidade/page.tsx
  - frontend/app/(public)/layout.tsx
  - render.yaml
  - .github/workflows/expire-cron.yml
  - frontend/vercel.json
  - docs/DEPLOY.md
  - scripts/verify-deploy.ps1
  - README.md
findings:
  critical: 2
  warning: 5
  info: 5
  total: 12
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-11-02
**Depth:** standard
**Files Reviewed:** 24 (plus cross-referenced `app/db/session.py` and `app/api/v1/health.py`)
**Status:** issues_found

## Summary

The phase delivers the expiry sweep (APScheduler in-process + `POST /api/v1/admin/expire` catch-up), the anonymous report flow, the legal page, and the deploy artifacts. The security posture of the new/changed code is mostly solid: the cron gate fails closed (503/401), secrets are compared with `secrets.compare_digest`, the report path is log-injection-safe (whitespace collapsed, 500-char cap, no persistence), the public payload remains contact-free, and no secrets are committed.

Two blockers remain before this can be called a trust/legal launch:

1. **The primary expiry mechanism is broken by construction** — the APScheduler worker thread runs `asyncio.run()` against the same asyncpg engine that serves the FastAPI event loop, so pooled connections cross event loops.
2. **The legal page for the launch is not shippable** — placeholder juridical redaction and an LGPD contact channel that does not exist anywhere.

Advisory risks (should fix, not ship-blocking on their own): no rate limit on the anonymous report endpoint, a deploy-verify gate whose failure mode contradicts the documented 503, and migrate-on-boot behind `autoDeploy: true`.

Immediate blockers vs advisory risks are labelled in each finding. Nothing here authorizes a production deploy; `scripts/verify-deploy.ps1` must be run by a human after the fixes below land.

---

## BLOCKER Issues

### CR-01: Expiry sweep runs on a throwaway event loop but shares the request-path asyncpg engine — cross-loop connection reuse

**File:** `backend/app/core/scheduler.py:56-82`, `backend/app/db/session.py:14-24`, `backend/app/main.py:17-26`
**Severity:** BLOCKER (immediate — primary LIFE-02 mechanism fails; can poison the public board's connection pool)

**Issue:**
`expire_jobs_job()` (called by APScheduler's `BackgroundScheduler` worker thread) executes `asyncio.run(_run_expiry_sweep())`, which creates and then **closes a brand-new event loop** for every sweep. Meanwhile `app.db.session.engine` is a single module-level `AsyncEngine` (default `AsyncAdaptedQueuePool`) shared with the FastAPI lifespan/request path.

Two failure modes follow:

1. The sweep checks out (or creates) connections and returns them to the pool; that pool is then handed connections bound to a closed/`asyncio.run` loop. The next sweep — and crucially the next **HTTP request** — can receive a connection created on a dead loop, raising `RuntimeError: ... attached to a different loop` / asyncpg "connection was closed in another thread" style errors. `pool_pre_ping=True` does not save this: the ping itself executes on the caller's loop.
2. Because the sweep and requests both draw from one pool, after the first 03:00 UTC run the board/reveal endpoints can intermittently 500 until the process restarts (i.e. until the next Render deploy/wake).

The failure is silent to users: `expire_jobs_job()` swallows all exceptions into `logger.exception(...)` and returns `0` (`scheduler.py:75-82`), so the sweep can fail every single night and LIFE-02/LIFE-03 are unmet while the board still *displays* correctly (expired rows are filtered out by `expires_at > func.now()`). Hard delete never happens; the table grows forever.

`shutdown_scheduler()` compounds it: it uses `wait=False` and `lifespan` then immediately calls `await engine.dispose()` (`main.py:25-26`), so an in-flight sweep can still be using connections when disposal begins.

**Fix — pick one, in order of preference:**

```python
# Option A (preferred): run the sweep on the app's own loop, no thread + asyncio.run.
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler(timezone="UTC")
scheduler.add_job(_run_expiry_sweep, CronTrigger(...), id=EXPIRY_JOB_ID, ...)
# start/stop inside lifespan; no asyncio.run, no worker thread, same loop as the pool.
```

```python
# Option B: isolate the sweep's database access from the shared pool.
from sqlalchemy.pool import NullPool
sweep_engine = create_async_engine(url, poolclass=NullPool, ...)
sweep_factory = async_sessionmaker(sweep_engine, expire_on_commit=False)
# use sweep_factory in _run_expiry_sweep and dispose() it when done.
```

```python
# Option C (minimum): drop the pool for every checkout in the sweep path, and
# never return sweep-created connections to the shared pool.
```

Also add an integration test that actually executes `_run_expiry_sweep()` against the test database from a thread (or at minimum asserts the sweep path does not share pooled connections with the request path). Current tests (`test_scheduler.py`, `test_admin_expire.py`) only test the cron *endpoint* and scheduler *wiring* — they never run a sweep, which is exactly why this defect is invisible to the suite.

Additionally, make shutdown deterministic: stop the scheduler **and wait** for a running job before `engine.dispose()` (e.g. `shutdown(wait=True)` or a bounded drain), since the delete is idempotent a wait is cheap and safe.

---

### CR-02: `/privacidade` is not shippable — pending juridical redaction and no existing privacy/LGPD contact channel

**File:** `frontend/app/(public)/privacidade/page.tsx:96-102, 174-180, 245-262`, `frontend/app/(public)/layout.tsx:57-68`
**Severity:** BLOCKER (launch blocker — LGPD Art. 18/41; the phase itself is "trust-legal-launch")

**Issue:**
The page that is supposed to establish trust and legal compliance contains, verbatim:

- `[Redação jurídica detalhada pendente — sujeito a revisão por advogado antes do lançamento...]` (×3, lines 99, 175, 258)
- `[E-mail de contato para privacidade: pendente — definir endereço oficial antes do lançamento.]` (line 253)
- Copy that tells the reader to use "o canal de contato abaixo" / "o canal de contato indicado no rodapé deste site" (lines 93-94, 248-249) — **no such channel exists**: the footer (`layout.tsx`) only renders "© 2026 NaoQueroUsar", the slogan and a "Privacidade e termos" link. There is no e-mail, no form, no address anywhere on the site or in `README.md`/`docs/DEPLOY.md`.
- Internal inaccuracy: "os dados de contato ... são exibidos publicamente na página da vaga e tornam-se públicos quando revelados" (lines 68-72) — contacts are *not* publicly rendered; they are released only through the Turnstile-gated reveal. The wording misstates the actual data-flow to the titular.

Under LGPD, the controller must provide a reachable channel for data-subject requests; an unlaunched placeholder is not a channel. Publishing this page as-is fails exactly the trust/legal goal of the phase and invites both regulatory exposure and the appearance of a fake privacy policy.

**Fix:**
1. Define and publish a real, monitored privacy/contact address (e.g. `privacidade@<dominio>`) before go-live; render it on `/privacidade` and in the public footer.
2. Remove all three `[... pendente ...]` placeholders by completing lawyer review (or explicitly scope the page as interim and link a real contact).
3. Correct the "exibidos publicamente na página da vaga" wording to reflect the reveal flow ("os contatos só são exibidos ao visitante que clica em revelar, após verificação anti-bot").
4. Keep the "Redação jurídica pendente" notices out of the production build; a production page must not ship with unfinished legal text.

Both blockers must be resolved before the go-live checklist (`docs/DEPLOY.md` → "Checklist de go-live") can be honestly ticked.

---

## WARNING Issues

### WR-01: Anonymous report endpoint has no rate limiting — log flooding / disk exhaustion vector

**File:** `backend/app/api/v1/public.py:159-183`, `frontend/lib/api.ts:293-312`
**Severity:** WARNING (should fix before public launch)

**Issue:** `POST /public/jobs/{id}/report` is deliberately unauthenticated and unbounded. It writes one `logger.info("job_report ...")` line per request including the resolved client IP. The project's own limiter (`app.core.ratelimit`, `reveal_limit`) is applied to reveal and login but **not** here. An attacker can generate unlimited log lines on a free-tier Render instance (ephemeral but size-limited disk; log egress also costs), degrade log readability for the master, and rotate/hide real reports. Log injection itself is handled (`_log_safe` collapses whitespace and truncates to 500 — good), so this is purely an abuse/availability concern.

**Fix:** Apply `@limiter.limit("5/minute")` (and a `request: Request` parameter) keyed by resolved IP, mirroring `reveal_limit`; return a clean 429 with `Retry-After`. Optionally add a `Turnstile` check only if abuse is observed — do not break the anonymous-by-design flow unnecessarily. Frontend `reportJob` should also surface a friendly error on 429.

### WR-02: `verify-deploy.ps1` check 7 contradicts the documented 503 contract and reports it as "endpoint open"

**File:** `scripts/verify-deploy.ps1:176-181`, `docs/DEPLOY.md:138`, `backend/app/deps.py:74-85`
**Severity:** WARNING (should fix — gate misfires on a correctly-configured secure deploy)

**Issue:** Check 7 asserts the unauthenticated `POST /admin/expire` returns **401 or 403** and otherwise throws `"POST /admin/expire sem segredo retornou ... Endpoint destrutivo aberto!"`. But the backend, when `CRON_SECRET` is unset, returns **503** (`deps.py:77-82`) — the documented, fail-closed behavior (`docs/DEPLOY.md:138`). A deploy where the operator hasn't set `CRON_SECRET` therefore fails the gate with the message "Endpoint destrutivo aberto!", which is exactly backwards: the endpoint is closed, just unconfigured. The 403 branch is also dead (backend never returns 403 here). The gate will also fail (rather than warn) for an operator who deliberately runs with `SCHEDULER_ENABLED=true` and no cron secret and considers the manual trigger optional.

**Fix:** Accept `(401, 403, 503)` as "refused" and phrase the failure as "resposta inesperada; esperado 401/503 (fail-closed)"; or, better, treat 503 as a **warning** "manual trigger disabled — cron will rely on in-process scheduler only" and fail only on 2xx/5xx-other. Keep the assertion that 200 must never happen without the secret.

### WR-03: `autoDeploy: true` + `alembic upgrade head` on every boot ships schema migrations straight to production unreviewed

**File:** `render.yaml:24-26`, `docs/DEPLOY.md:88, 182-184`
**Severity:** WARNING (should fix — availability/data-risk configuration)

**Issue:** The Render blueprint sets `autoDeploy: true` and the start command runs `alembic upgrade head` before uvicorn, including on wake-ups from spin-down and on every push to the production branch. A broken or non-idempotent migration (or one with a locking `ALTER` on a live table) is applied automatically with no approval gate and **no schema rollback** (docs correctly note migrations are forward-only). Combined with free-tier restarts, a bad deploy can wedge every boot into upgrade-failure → crash loop, taking the public board down until a human intervenes. The runbook itself says rollback of code is trivial but schema is not, which makes the unattended schema step the risky one.

**Fix:** Set `autoDeploy: false` (or enable Render's manual deploy / CI-gated deploy), and/or move `alembic upgrade head` to a separate one-off deploy step rather than the boot path. If boot-migration is retained, alert on failure and keep a documented fast-forward migration to heal. At minimum, document that production deploys are manually approved and migration backups/snapshots are taken before merge.

### WR-04: Frontend API base silently falls back to `http://localhost:8000` — production misconfig fails opaque instead of loud

**File:** `frontend/lib/api.ts:105`, `frontend/vercel.json:1-4`
**Severity:** WARNING (should fix)

**Issue:** `const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"`. If `NEXT_PUBLIC_API_URL` is unset in a Vercel production build (typo, wrong scope — Preview only, or renamed var), the browser will issue every API call — login, extract, reveal, report, admin — to the *visitor's own* `localhost:8000`, which either fails with a confusing network error or, on a machine running an unrelated local service on 8000, sends requests (including the admin password and Turnstile tokens) to that local service. `vercel.json` pins only `framework`, so nothing catches this at build time.

**Fix:** Fail fast at build time in production: throw/return a build-time error when `NODE_ENV === "production"` and the variable is absent (or at minimum `console.warn` loudly and refuse localhost). Keep the localhost default only for `development`. Document the required env in `frontend/.env.example` and the Vercel checklist (already partially in `docs/DEPLOY.md` — make the build enforce it).

### WR-05: Shutdown can dispose the engine while a sweep is mid-query; interrupted deletes rely solely on idempotency

**File:** `backend/app/core/scheduler.py:127-141`, `backend/app/main.py:21-26`
**Severity:** WARNING (should fix together with CR-01)

**Issue:** `shutdown_scheduler()` calls `self._scheduler.shutdown(wait=False)` and `lifespan` immediately proceeds to `await engine.dispose()`. A sweep that is currently inside `DELETE FROM jobs ...` can have its connections invalidated/closed underneath it; the transaction aborts, the next boot re-sweeps (idempotent — acceptable) *silently*, and the log line telling the operator the nightly delete never happened may be the only trace. Worse, with CR-01 in place the mid-flight connection may belong to a loop that is already closed, producing an exception during interpreter/loop teardown that is easy to miss in Render logs.

**Fix:** After fixing CR-01, use `shutdown(wait=True)` (or a bounded wait with a timeout) so an in-flight delete completes before `engine.dispose()`. If you keep `wait=False`, at least check `scheduler.running` / job state and log a warning when a sweep is interrupted; never dispose the pool until the sweep thread has exited.

---

## INFO Issues

### IN-01: GitHub Actions workflow has no explicit `permissions:` block

**File:** `.github/workflows/expire-cron.yml:14-21`
**Issue:** The job inherits the repository default `GITHUB_TOKEN` permissions. It only calls an external HTTP endpoint and needs none, so least privilege says declare `permissions: {}` (or `contents: read`) at workflow top level.
**Fix:** Add `permissions: {}` under `on:` / top level of `expire-cron.yml`.

### IN-02: `curl --retry-all-errors` retries non-retryable responses (401/4xx)

**File:** `.github/workflows/expire-cron.yml:39-42`
**Issue:** With `--retry-all-errors`, a wrong/missing `CRON_SECRET` (401) is retried 3 times with 15 s delays before failing — wasteful and misleading in incident logs (implies a transient fault rather than a credential problem). Idempotency makes the retry harmless for 5xx/timeouts, but not for 4xx.
**Fix:** Drop `--retry-all-errors` and use `--retry 3 --retry-delay 15 --retry-connrefused` (retry only transport/5xx-ish), or add `--retry 3` with `--retry-max-time` and accept 4xx handling manually.

### IN-03: `reportJob` fetch has no timeout (unlike `revealContact`)

**File:** `frontend/lib/api.ts:293-312`
**Issue:** `revealContact` uses `AbortSignal.timeout(15_000)` with a typed timeout/network error path; `reportJob` uses a bare `fetch`. On a cold/half-open backend the report form's "Enviando..." state can hang far beyond the reveal budget with no recovery affordance.
**Fix:** Mirror the reveal pattern (`AbortSignal.timeout(10_000)`) and map abort to a retryable error state; keep the UI's "Tentar novamente" path.

### IN-04: No test executes the sweep itself — CR-01-class defects are untestable in the current suite

**File:** `backend/tests/test_scheduler.py`, `backend/tests/test_admin_expire.py`
**Issue:** Tests cover the cron endpoint (mocked session via ASGI transport) and scheduler *wiring* (job id/trigger/start/stop), never `_run_expiry_sweep`/`expire_jobs_job` against a real async connection. The cross-loop pool contamination therefore cannot fail CI. Add an integration test marked `asyncio` that builds a fresh loop, runs the sweep against `TEST_DATABASE_URL`, and asserts (a) rows are deleted, (b) no `RuntimeError` from the driver, (c) a subsequent request using the shared pool still works.
**Fix:** See CR-01; wire the test into `pytest` (skip cleanly when `TEST_DATABASE_URL` is absent, like the rest of the DB suite).

### IN-05: `POST /admin/expire` has no rate limit / brute-force throttle

**File:** `backend/app/api/v1/admin.py:193-210`, `backend/app/deps.py:60-85`
**Issue:** The cron gate is a static bearer compared in constant time (sound), but there is no slowapi limit, so an unauthenticated client can probe `X-Cron-Secret` at full speed indefinitely. With 32+ char secrets this is not practically exploitable, but it is free hardening consistent with `LOGIN_RATE_LIMIT`.
**Fix:** Add `@limiter.limit("10/minute")` keyed by resolved IP (and keep the 503/401 semantics unchanged).

---

## Notes for the go-live operator (not counted as findings)

- Deploy order per `docs/DEPLOY.md` remains valid; do not run `scripts/verify-deploy.ps1` until CR-01/CR-02 land and WR-02 is applied, or the gate will fail for the wrong reason.
- `render.yaml` does not set `SCHEDULER_ENABLED` (defaults `true`); on the free tier it is inert while asleep — documented and acceptable *only if* the GitHub cron catch-up is configured and monitored, or `SCHEDULER_ENABLED=false` is set explicitly.
- The `/privacidade` placeholders mean the "legal" checkbox in the go-live checklist cannot be ticked; see CR-02.
- No secrets are present in the reviewed tree (`render.yaml` uses `sync: false`, workflow uses `secrets.*`, docs carry placeholders only). `.env` not in scope.

## Verification commands (for the operator / after fixes)

```powershell
cd backend && uv run pytest -q
cd frontend && npm run build   # must fail if NEXT_PUBLIC_API_URL is unset in prod mode (WR-04)
powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 -FrontendUrl <url> -BackendUrl <url> -CronSecret <CRON_SECRET>
```

Do **not** treat any of the above as executed — none were run in this review (read-only, no network).

---

_Reviewed: 2026-11-02_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
