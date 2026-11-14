# Phase 9 — Research: Lifecycle, Trust, Legal & Launch Completeness

**Researched:** 2026-11-13
**Phase:** 9 — Lifecycle, Trust, Legal & Launch Completeness
**Requirements:** LIFE-10, LIFE-11, LIFE-12, TRST-10, TRST-11, TRST-12
**Method:** direct codebase audit (no subagent — free-tier limit). Every claim below
was verified against source, not against SUMMARY.md.

---

## Executive summary

Phase 6 already shipped the *mechanisms* this phase's roadmap describes. What remains
is (a) **provable completeness** — tests and DDL assertions that pin the contract,
(b) **three real gaps**: the LGPD intermediary notice text is missing, the legal pages
duplicate the public shell and ignore the design tokens, and the deploy blueprint is
missing two operational knobs, and (c) **one documentation conflict** between the
ROADMAP success criterion 2 and the security decision T-06-01.

No architectural change is needed. Plans should be verification-heavy and surgical.

| Criterion | Verdict | Action |
|-----------|---------|--------|
| 1. `expires_at` = `created_at` + 14d, timestamptz/UTC | **DONE** (behavior) / **PARTIAL** (proof) | Add DDL-level assertion test |
| 2. `/admin/expire` hard delete, idempotent, future rows safe | **DONE** (code+tests) / **CONFLICT** (doc) | Fix ROADMAP wording: JWT is **not** accepted by design |
| 3. `pending` also expires | **DONE** | Extend tests to `needs_review` / `invalid` |
| 4. Legal pages + LGPD notice, 13/10 sections | **GAP** | Add notice phrase; restructure pages; footer links |
| 5. Report endpoint + "Vaga revisada" badge | **DONE** | Verification task only |
| 6. Vercel/Render deploy, CORS, secrets, cold-start | **PARTIAL / BLOCKED (human)** | Config knobs + CORS test + go-live gate |

---

## Criterion-by-criterion evidence

### Criterion 1 — 14-day expiry, `timestamptz`, DB clock

**DONE.** `backend/app/models/job.py:61-65` declares
`expires_at TIMESTAMP(timezone=True) NOT NULL server_default=text("now() + interval '14 days'")`.
The same default is in `backend/alembic/versions/0001_initial_jobs.py:103-105`, and an
index `ix_jobs_expires_at` exists (`models/job.py:78`, migration line 167).

Behavioral proof exists: `backend/tests/test_schema.py:44-57`
(`test_expires_at_defaults_to_14_days`) asserts the delta is within 13d23h–14d1h.
**Gap:** no test asserts the *DDL* contract (column type `timestamptz` and
`server_default` containing `interval '14 days'`). A migration edit that dropped the
server default would slip through behavior tests only if a client ever supplies
`expires_at` (it does not today) — the assertion is cheap and makes the criterion
explicit.

### Criterion 2 — `/admin/expire` hard delete, idempotent, future rows safe

**DONE in code and tests.**
- Route: `backend/app/api/v1/admin.py:193-217`, guarded by
  `Depends(require_cron_secret)` (`deps.py:62-…`).
- Sweep: `backend/app/crud/jobs.py:169-189` — `DELETE FROM jobs WHERE expires_at < func.now()`
  (database clock), `flush()` only, caller commits.
- Idempotency: `test_admin_expire.py:157-169` (second call → `{"deleted": 0, "status": "ok"}`).
- Future rows survive: `test_expiry_sweep_integration.py:34-…` seeds a future job and
  asserts it remains.
- Fail-closed: no `CRON_SECRET` → 503; missing/wrong header → 401
  (`test_admin_expire.py:66-107`); probing is rate-limited (10/min, `deps.py:77-83`).

**CONFLICT (must be resolved in this phase's docs, not code):**
ROADMAP success criterion 2 says the endpoint is protected by
"`X-Cron-Secret` header **(ou Bearer JWT admin)**". The implementation and tests
deliberately reject an admin JWT (`test_admin_expire.py:93-107`,
`test_admin_expire.py:5-6`, `STATE.md` decision T-06-01: "um Bearer JWT de admin NAO
autoriza /admin/expire"). Accepting the JWT would let a stolen browser token destroy
the board. **Recommendation:** keep the code; amend `ROADMAP.md` criterion 2 to
"protegido por `X-Cron-Secret` (um Bearer JWT de admin NÃO é aceito — T-06-01)" and
mirror the note in `docs/DEPLOY.md`. A plan task must make this explicit so a future
executor does not "fix" the code to match the stale roadmap text.

### Criterion 3 — `pending` (and every status) expires

**DONE.** `delete_expired_jobs` is status-agnostic by construction
(`crud/jobs.py:172-186`, docstring cites LIFE-03/D-03). `test_admin_expire.py:132-155`
deletes an expired `published` **and** an expired `pending` row in one call.

**Gap (proof only):** no test pins `needs_review` and `invalid`. Add a parametrized
case so "same 14-day rule for every status" cannot regress when a new status is added.

### Criterion 4 — Legal pages + LGPD notice

**PARTIAL — three concrete gaps.**

1. **Missing required notice (GAP).** Success criterion 4 and TRST-10 require the
   notice "somos apenas meio de divulgação". A full-text search of `frontend/` finds
   only "não intermediaria contratações" in
   `frontend/app/(public)/termos-de-uso/page.tsx:46`. The exact notice does not exist.
   Note `scripts/verify-deploy.ps1:199` checks only `/intermedi/`, so the smoke gate
   passes on the weaker sentence — the gate must be tightened to the real phrase.
2. **Nested public shell (GAP, REV-08).** Both pages live in the `(public)` route
   group, whose layout already renders `<main>` (`layout.tsx:53`), header (`:30`) and
   footer (`:57`). Each page renders **its own** `<main>` and `<header>`
   (`privacidade/page.tsx:6,8`; `termos-de-uso/page.tsx:6,8`) → duplicate landmarks and
   two headers on one document.
3. **Non-token styling + wrong heading levels (GAP).** Pages use `bg-gray-900`,
   `text-white`, `border-gray-700`, and a non-existent `hover:text-accent-strong`
   class; page titles are `<h2>` and sections `<h3>`. `09-UI-SPEC.md` requires tokens
   (`bg-canvas`, `text-fg`, `border-line`, `hover:text-accent-soft`), one `<h1>` and
   `<h2>` per section.
4. **Orphan page (GAP).** The footer links only `/privacidade`
   (`layout.tsx:61-66` labeled "Privacidade e termos"); `/termos-de-uso` has no public
   inbound link.
5. Sections count is **DONE**: 13 `<h3>` in privacidade, 10 in termos-de-uso.
   `/termos-de-uso` contains foro/legislation text and the LGPD reference lives in
   privacidade line 174. Neither page exports `metadata` (title/description) — add it.

**Content rule:** the legal copy is user-authored. Plans may re-tag headings and add
the required intermediary notice sentence, but must not rewrite or summarize the rest.

### Criterion 5 — Report endpoint + "Vaga revisada" badge

**DONE.**
- `POST /api/v1/public/jobs/{job_id}/report` — `backend/app/api/v1/public.py:159-189`;
  `ReportRequest.reason: str|None = Field(max_length=500)` with blank-stripping
  (`schemas/job.py:68-84`).
- Structured single-line log with `job_id`, sanitized/truncated `reason`, resolved IP;
  nothing persisted (`public.py:180-189`). Tests: `test_report_api.py` (no-body, log
  shape, 501 chars rejected, unknown job still 200, whitespace → absent, 6th request
  → 429).
- Badge: `JobCard.tsx:49-53` and `JobDetailDialog.tsx:121-125`, derived only from
  `job.status === "published"`.
- Report UI wired: `JobDetailDialog.tsx:174-178` renders `ReportJobDialog`.

No code change needed; include a verification task with explicit grep/test commands so
the criterion is proven in this phase's SUMMARY.

### Criterion 6 — Deploy, CORS, secrets, cold-start

**PARTIAL; production verification is BLOCKED on a human decision.**
Artifacts exist and are coherent:
- `render.yaml` — Render blueprint, `ENV=prod`, `autoDeploy: false`, secrets `sync: false`,
  `healthCheckPath: /api/v1/health`, build `uv sync --frozen --no-dev`,
  start `uv run alembic upgrade head && uv run uvicorn …`.
- `frontend/vercel.json` — Next.js framework config.
- `.github/workflows/expire-cron.yml` — daily 03:00 UTC + `workflow_dispatch`, calls
  `/api/v1/admin/expire` with `X-Cron-Secret`, least-privilege `permissions: {}`.
- `docs/DEPLOY.md` — runbook with CORS, cron, cold-start and a verification log.
- `scripts/verify-deploy.ps1` — 10-check production gate (health `env=prod`,
  Turnstile mode, CORS allow/deny, board no contact leak, legal pages, API envelope,
  cron 401/403/503 + idempotency, no secret leak, first-request latency).

**Observed production state (2026-11-12, `docs/DEPLOY.md` verification log):**
health 200 **but `env=dev`**; Turnstile `mode=test`; CORS preflight from the Vercel
origin **400 with no `Access-Control-Allow-Origin`**. Root causes are deployment
environment values, not code: `ENV`, `CORS_ORIGINS` (likely missing the Vercel origin
or carrying a trailing slash) and Turnstile live keys were not applied. The user
explicitly chose "option B" (stay local, no production deploy) on 2026-11-10, so
criterion 6 cannot be closed autonomously.

**Code/config gaps that are in scope:**
1. `render.yaml` does not declare `SCHEDULER_ENABLED` (REV-10). Add it explicitly
   (`value: "true"`) so the documented operational knob is visible in the blueprint.
2. `startCommand` uses `uv run`, which re-syncs the environment on every boot,
   including the dev dependency group (REV-09). Use `uv run --no-sync` (the build step
   already ran `uv sync --frozen --no-dev`) to cut cold-start.
3. No backend test pins the production CORS contract (exact configured origin allowed,
   foreign origin denied). Existing tests only cover `Retry-After` exposure and the
   reveal preflight (`test_public_api.py:88-124`).
4. CORS `allow_origins` comes from `CORS_ORIGINS` with `strip()` per item
   (`config.py:115-117`); there is no fail-closed validation that a production origin
   is non-empty or free of a trailing slash. Add a startup validator for `ENV != "dev"`
   (warn or fail) so a misconfigured deploy is caught at boot rather than in the
   browser.
5. `verify-deploy.ps1` check 5 must assert the exact intermediary notice phrase, not
   `/intermedi/`.

---

## Recommended plan breakdown (3 waves, mirrors Phase 6)

### Wave 1 — `09-01`: Lifecycle & trust proofs (backend)
Requirements: LIFE-10, LIFE-11, LIFE-12, TRST-11.
- DDL assertion test for `expires_at` (`timestamptz`, `server_default` contains
  `interval '14 days'`, `created_at`/`expires_at` both `timezone=True`).
- Parametrized expiry test across `pending`, `needs_review`, `invalid`, `published`
  plus a future row that survives.
- Keep `/admin/expire` JWT rejection pinned; add an explicit test name/marker so the
  decision is discoverable.
- Report endpoint verification task (grep + pytest `test_report_api.py`) — no code
  change expected.
- Docs: correct ROADMAP criterion 2 wording (JWT is not accepted).

### Wave 2 — `09-02`: Legal pages & trust surface (frontend)
Requirements: TRST-10, TRST-12.
- Restructure `privacidade/page.tsx` and `termos-de-uso/page.tsx`: remove nested
  `<main>`/`<header>`/`<nav>`, one `<h1>`, `<h2>` per section, tokens only,
  `max-w-3xl`, add `metadata` (title/description pt-BR), preserve all legal copy.
- Add the required notice sentence ("O NQU é apenas um meio de divulgação de vagas…")
  to `/termos-de-uso` (and reference it from `/privacidade` if the copy allows).
- Footer in `(public)/layout.tsx`: two links, "Privacidade" and "Termos de Uso".
- Verify badge in `JobCard`/`JobDetailDialog` and `ReportJobDialog` wiring; no changes
  unless a regression is found.

### Wave 3 — `09-03`: Launch readiness & deploy hardening
Requirements: none (criterion 6).
- `render.yaml`: add `SCHEDULER_ENABLED: "true"`, switch start command to
  `uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn …`.
- `config.py`: production CORS validation (non-empty, no trailing slash / wildcard;
  fail-closed outside `dev`).
- New `backend/tests/test_cors.py`: configured origin allowed with exact echo;
  foreign origin not echoed; preflight for reveal/report `POST` allowed.
- `scripts/verify-deploy.ps1`: exact intermediary-notice assertion.
- `docs/DEPLOY.md`: record the `uv run --no-sync` change, the CORS/ENV checklist and
  keep the production gate `autonomous: false` (human-only).

---

## Validation Architecture

**Backend (pytest, from `backend/`):**
```
cd backend; .venv\Scripts\python.exe -m pytest -q
```
Targeted files: `test_schema.py` (DDL/14d), `test_admin_expire.py` (auth/idempotency/
all statuses), `test_expiry_sweep_integration.py` (future survives, pool survives),
`test_report_api.py` (accept-and-log, 500-char cap, 429), new `test_cors.py`.
Baseline: suite is green today (Phase 6 close reported 247 passed / 3 skipped plus
post-review fixes); every new test must keep it green.

**Frontend:** `npm run lint` + `npx tsc --noEmit` + `next build` (`frontend/`).
Structural assertions for legal pages are grep-based (single `<main>` per rendered
route is enforced by removing the element from the page files; `h1` count, token
classes, notice phrase).

**E2E/Production (human gated):** `scripts/verify-deploy.ps1` after a real deploy.
Criterion 6 is only `passed` when the log shows `env=prod`, `turnstile.mode=live`,
CORS allow/deny correct and a measured first-request latency.

**Coverage targets for this phase:** every success criterion maps to at least one
automated assertion except criterion 6, which maps to a documented human gate.

---

## Risks & constraints

- **Do not "fix" the cron auth to accept JWT.** The roadmap text is stale; the code
  decision (T-06-01) is the secure one.
- **Do not rewrite legal copy.** Only markup, metadata, tokens and the required notice.
- **Production deploy remains a human decision** ("option B", 2026-11-10). Plans must
  not mark deploy complete; they may only prepare and document the gate.
- **Windows/PowerShell:** use `;` not `&&`; run pytest from `backend/`.
- **No new dependencies.** Everything above uses the existing stack.
