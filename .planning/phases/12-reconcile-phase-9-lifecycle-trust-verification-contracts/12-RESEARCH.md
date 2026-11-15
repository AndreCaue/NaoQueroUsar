# Phase 12: Reconcile Phase 9 Lifecycle/Trust Verification & Contracts - Research

**Researched:** 2026-11-15
**Domain:** Verification/traceability reconciliation for Phase 9 lifecycle, trust, and cron-secret-only security contracts (docs/evidence only)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Mark ROADMAP Phase 9 criterion 6 as **VERIFIED with an explicit host caveat**. Evidence is the operator-approved `verify-deploy` pass recorded in `docs/DEPLOY.md` (`2026-11-15` row): health 200 `env=prod`, Turnstile `mode=live`, CORS allow/deny preflight, board/legal/API, cron rejected-then-idempotent, no secret leak. The caveat must state that the run was executed against `https://empreganoix-six.vercel.app` + `https://nqu-backend-x60n.onrender.com`, which differ from the roadmap's canonical `empreganoix.vercel.app` / `empreganoix.onrender.com`, and that canonical-host confirmation and any re-smoke belong to **Phase 13 (BRND-04)**. Do not re-run the smoke gate in Phase 12.
- **D-02:** **Verify only — do not rewrite ROADMAP criterion 2.** Commit `b9a38c6` already changed it to `protegido exclusivamente por header X-Cron-Secret (um Bearer JWT de admin NÃO é aceito — T-06-01)`. Phase 12 confirms it against `backend/app/api/v1/admin.py`, `backend/app/deps.py`, `backend/tests/test_admin_expire.py` and `docs/DEPLOY.md`, and records that confirmation as evidence. No further contract wording edits.
- **D-03:** Keep a **lean `human_verification` block** in the reconciled report recording the operator-run 2026-11-15 gate (command, hosts, result) plus the single remaining human/ops follow-up: canonical-host confirmation and re-smoke, owned by Phase 13. Do not delete it and do not downgrade the phase because of it.
- **D-04:** Keep a **one-line progression note** for the superseded 2026-11-12 failed smoke (`env=dev`, Turnstile `mode=test`, CORS preflight 400) → superseded by the 2026-11-15 pass after the 09-03/09-04 hardening. Do not reproduce the full failing detail.
- **D-05:** **Rewrite `09-VERIFICATION.md` in place.** It stays the single source of truth: frontmatter refreshed, body updated to current state, and a compact **"Superseded findings"** table listing each of the originally reported gaps with the commit/artifact that closed it (`b9a38c6`, `b3e6940`, `docs/DEPLOY.md` rows, current tests). Do not create a separate `09-REVERIFICATION.md` and do not leave the original `gaps_found` body as a competing narrative.
- **D-06:** Reconciled frontmatter: `status: passed`, `score: 6/6 success criteria verified`, a machine-readable **`caveats:`** entry carrying the non-canonical-host production evidence + Phase 13 ownership, and both `initial_verified:` (2026-11-15, original run) and `reconciled:` (this phase) dates. Do not invent a `passed_with_caveats` status value.
- **D-07:** Keep the **Anti-Patterns** table with the three original rows (stale ROADMAP text, weak `intermedi` smoke assertion, incomplete `docs/DEPLOY.md`), each now marked **CLOSED** with the closing commit — `b9a38c6` for the ROADMAP contract and smoke-gate assertion, `b3e6940` for the runbook. Do not delete the rows; they are the audit trail of what was wrong.
- **D-08:** Add a short **Nyquist follow-up note**: `09-VALIDATION.md` exists but the milestone audit rates Phase 9 Nyquist coverage partial, and closing it is a separate `/gsd-validate-phase 09` task — not part of this phase.
- **D-09:** Generate **fresh targeted test evidence**: run `cd backend; .venv\Scripts\python.exe -m pytest <targets>` over `tests/test_schema.py`, `tests/test_admin_expire.py`, `tests/test_report_api.py`, `tests/test_cors.py`, and embed command, pass/fail counts and relevant snippets in the reconciled report. This follows the Phase 11 precedent (D-01/D-04: run tests now, do not restate summaries). Do not run the full suite for this phase.
- **D-10:** **Commit the pending Phase 9 evidence before reconciling**, as its own commit: `backend/app/core/config.py` (CORS fail-closed `_validate_cors_origins`), `backend/tests/test_admin_expire.py` (all-status expiry test), `backend/tests/test_report_api.py` (500-char + no-persistence tests). `09-VERIFICATION.md` already cites these as VERIFIED, so they are Phase 9 evidence that was never committed — they must exist at a known SHA before the reconciled report cites them. Do **not** mix this with the later docs-only reconciliation commit.
- **D-11:** Inspect root-level untracked `add_coldstart.py` and `add_scheduler.py`. If they are one-off patch scripts whose edits already landed in `docs/DEPLOY.md` / `render.yaml`, remove them in a **separate cleanup commit** — never inside the reconciliation commit. Leave `.gsd-temp/` untouched and out of scope.
- **D-12:** Add a **"How this was verified" / reproduce block** to the reconciled report: working directory (`backend/`), exact pytest command(s), the commit SHA at verification time, and the date, so the next auditor can re-run the same evidence.
- **D-13:** In `.planning/REQUIREMENTS.md`, **check all six** Phase 12 requirements: `LIFE-10`, `LIFE-11`, `LIFE-12`, `LIFE-13`, `TRST-11`, `SECR-12`. `LIFE-10/11/12` and `TRST-11` are pure Phase 9 code contracts (no residual). `LIFE-13` and `SECR-12` get an explicit **split-ownership note**: code/contract side verified here (`09-VERIFICATION.md`), residual canonical-host/deploy evidence owned by **Phase 13**, which keeps both IDs in its requirement list.
- **D-14:** **Repair `09-04-SUMMARY.md` frontmatter in place** by adding `LIFE-13` to `requirements-completed` — 09-04 performed the ROADMAP/REQUIREMENTS/DEPLOY cron-contract alignment. This mirrors Phase 11's in-place traceability repair on Phase 8 artifacts; keep `provides`/`key-files` consistent.
- **D-15:** Drift rule — fix **in-scope** drift in this phase (Phase 9 contract, traceability, verification/evidence alignment, stale statements about the cron gate). **Defer** anything touching canonical hosts, env vars, CORS values or deploy execution to Phase 13. Do not pull Phase 13 work forward.
- **D-16:** Record traceability in `REQUIREMENTS.md` the **Phase 11 way**: a parenthetical note on each requirement line pointing to the evidence in `09-VERIFICATION.md` (plus the Phase 13 residual ownership for `LIFE-13`/`SECR-12`), and update the footer `Last updated:` line. No consolidated-only section.

### OpenCode's Discretion
- Exact plan/wave split for the reconciliation work (documentation edit vs evidence commit vs REQUIREMENTS update), as long as D-10's evidence commit lands before the docs-only reconciliation commit.
- Exact selection/order of test files within the D-09 subset and how much pytest output to quote.
- Precise wording of the "Superseded findings" table, the `caveats:` key contents and the "How this was verified" block, provided the caveat names the actual hosts and the Phase 13 hand-off.
- Whether to mention the duplicate `07-contact-reveal-anti-spam-complefaces` directory or other unrelated repo noise in the report — optional, not required by the audit.

### Deferred Ideas (OUT OF SCOPE)
- Canonical host / env / CORS / API base alignment and any canonical-host production re-smoke — **Phase 13 (BRND-04 closeout)**.
- Nyquist validation closure for Phase 9 (`09-VALIDATION.md` partial) — separate `/gsd-validate-phase 09` task.
- Legacy internal identifiers spotted by the audit (`nqu-backend` service name, `nqu_admin_token` storage key) — not required by Phase 12.
- `.gsd-temp/` inspection and any repo-hygiene cleanup beyond the two stray root scripts.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (from REQUIREMENTS.md) | Research Support |
|----|------------------------------------|------------------|
| LIFE-10 | Vagas recebem `expires_at` = `created_at` + 14 dias - server_default no modelo e migration verificado | `backend/app/models/job.py` sets `server_default=text("now() + interval '14 days'")` on `TIMESTAMP(timezone=True)` with `ix_jobs_expires_at`; `backend/tests/test_schema.py` pins DDL/timestamptz/normalized interval/index (criterion 1 evidence). [VERIFIED: codebase] |
| LIFE-11 | Job agendado faz hard delete de vagas `published` expiradas, de forma idempotente e em UTC - APScheduler em processo FastAPI | `backend/app/crud/jobs.py::delete_expired_jobs` uses DB clock `expires_at < func.now()` (status-agnostic sweep, flush-only), invoked by `/admin/expire`; `backend/tests/test_admin_expire.py` covers idempotency/future preservation/503,401,JWT cases. [VERIFIED: codebase] |
| LIFE-12 | Vagas `pending` nao revisadas tambem expiram apos 14 dias - mesma regra de 14 dias aplicada | Same status-agnostic sweep; uncommitted but ready test `test_expire_deletes_expired_row_for_every_status` parametrized over all 4 statuses in `backend/tests/test_admin_expire.py` (D-10). [VERIFIED: working tree + codebase] |
| LIFE-13 | Expiraçao disparada por endpoint protegido por `CRON_SECRET`, com passe de recuperaçao (catch-up) - endpoint `/admin/expire` aceita somente `X-Cron-Secret` (Bearer JWT admin NAO é aceito - T-06-01) | `backend/app/api/v1/admin.py: POST /expire` depends on `require_cron_secret`; `backend/app/deps.py::require_cron_secret` is fail-closed (503 unconfigured, 401 missing/wrong, `secrets.compare_digest`, 10/min); tests prove JWT rejected; ROADMAP criterion 2 already aligned (b9a38c6) and docs/DEPLOY row 320 record cron rejected/idempotent. Split ownership: contract/evidence reconciled here, canonical-host residual Phase 13. [VERIFIED: codebase + git history + docs] |
| TRST-11 | Visitante pode denunciar uma vaga - endpoint `/jobs/{id}/report` aceita motivo opcional (máx 500 chars), emite logs estruturados sem persistir reports | `backend/app/api/v1/public.py::report_job` (log-only, cap/throttle/no-oracle) and `backend/tests/test_report_api.py` including uncommitted `test_report_reason_at_500_chars_is_accepted_and_logged` and `test_report_persists_nothing` (`to_regclass('public.reports') is None`) (D-10). [VERIFIED: working tree + prior report cites] |
| SECR-12 | Endpoint `/admin/expire` autenticado por header `X-Cron-Secret` - fail-closed: 503 quando header ausente/incorreto | Phase 9 side is the cron-secret-only contract (same implementation/tests/docs as LIFE-13). Phase 7 side was gap-closed in Phase 11 per REQUIREMENTS note; Phase 12 reconciles Phase 9 evidence/traceability. Keep split ownership with Phase 13 residual canonical-host evidence (D-13, D-15). [VERIFIED: codebase + REQUIREMENTS.md] |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- **GSD workflow enforcement:** “Before using Edit, Write, or other file-changing tools, start work through a GSD command…” (`AGENTS.md`, GSD:workflow block). Planning occurs under `/gsd-plan-phase`; execution must follow planned commits.
- **Stack/locale/product constraints (PROJECT.md via AGENTS context):** pt-BR, no-login public board, FastAPI backend + Next.js frontend, Neon Postgres, deploy Vercel/Render context. Phase 12 must not change product behavior.
- **Existing gitignore noise:** `.gsd-temp/` is untracked and must remain out of scope (D-11).

## Architectural Responsibility Map

| Tier | Files/Artifacts | Current state (relevant to Phase 12) | Reconciliation responsibility |
|------|------------------|--------------------------------------|------------------------------|
| Verification artifacts (Phase 9) | `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md` | `status: gaps_found`, `score: 4/6`, 4 gaps, 3 anti-patterns, 3 human checks, 2026-11-15 initial run [VERIFIED] | Rewrite in place to passed 6/6 with `caveats`, `initial_verified`, `reconciled`, Superseded findings, closed anti-patterns, lean human block, Nyquist note, reproduce block (D-03..D-08,D-12) |
| Phase 9 traceability | `09-04-SUMMARY.md` frontmatter | `requirements-completed: [LIFE-10, LIFE-11, LIFE-12, TRST-10, TRST-11, TRST-12]` (no `LIFE-13`) [VERIFIED] | In-place add `LIFE-13` only (D-14) |
| Roadmap contract | `.planning/ROADMAP.md` Phase 9 criterion 2 (line ~95) | Already states `X-Cron-Secret`-only and rejects admin Bearer JWT (T-06-01); aligned by `b9a38c6` [VERIFIED] | Verify-only, record confirmation evidence (D-02) |
| Milestone traceability | `.planning/REQUIREMENTS.md` | LIFE-10..13, TRST-11, SECR-12 currently unchecked with stale/split notes; footer dated 2026-11-15 Phase 11 sync [VERIFIED] | Check six IDs, add per-ID parenthetical evidence/ownership notes + footer update (D-13,D-16) |
| Deploy/ops evidence | `docs/DEPLOY.md` (rows 306-320, sections 65/94/182/191/214) | Contains 2026-11-12 failed smoke, 2026-11-13 prep, 2026-11-14 10-04 deploy, 2026-11-15 passing criterion 6 smoke on non-canonical hosts + `uv run --no-sync` + “Credencial única” + human-gated block [VERIFIED] | Cite as evidence only; no edits (D-01,D-03,D-04) |
| Backend evidence to commit (pre-req) | `backend/app/core/config.py`, `backend/tests/test_admin_expire.py`, `backend/tests/test_report_api.py` | Uncommitted working-tree changes implementing/covering CORS fail-closed, all-status expiry, 500-char/no-persistence report [VERIFIED: `git diff --shortstat`/diff] | Commit as isolated evidence commit before docs reconciliation (D-10) |
| Stray root scripts | `add_coldstart.py`, `add_scheduler.py` | One-off patch scripts; their target strings/blocks already present in `docs/DEPLOY.md` and `render.yaml` [VERIFIED: content comparison] | Remove in separate cleanup commit (D-11) |
| Out-of-scope handoff | Phase 13 artifacts/hosts | Canonical `empreganoix.vercel.app` / `empreganoix.onrender.com` and BRND-04 evidence [VERIFIED: ROADMAP/STATE/REQUIREMENTS] | Do not touch; only reference residual ownership |

## Summary

Phase 12 is a **docs/evidence/traceability reconciliation** phase, not a feature phase. The implementation is already in place and largely evidenced: lifecycle/expiry/report/CORS/cron contracts exist in code and tests; ROADMAP criterion 2 already says “X-Cron-Secret-only” (commit `b9a38c6`); `docs/DEPLOY.md` records the 2026-11-15 passing production smoke on non-canonical hosts; and `scripts/verify-deploy.ps1`/runbook were tightened in `b9a38c6`/`b3e6940`. The audit gap is that `09-VERIFICATION.md` is stale (`gaps_found`, 4/6), some cited backend evidence files are still uncommitted, `09-04-SUMMARY.md` omits `LIFE-13`, and REQUIREMENTS checkboxes/notes for LIFE-10..13/TRST-11/SECR-12 are not synced.

**Primary recommendation:** Plan a small, ordered sequence: (1) commit existing backend evidence files (D-10) and record SHA; (2) remove two proven-obsolete root patch scripts in a separate cleanup commit (D-11); (3) perform docs-only reconciliation — rewrite `09-VERIFICATION.md` in place with fresh targeted test evidence/caveats/superseded audit trail, repair `09-04-SUMMARY.md` frontmatter, and update `REQUIREMENTS.md` checkboxes/notes/footer — committed separately from evidence. Do not edit ROADMAP criterion 2 (verify-only), do not re-run production smoke, and do not pull Phase 13 host/deploy work forward.

## Research Answers (Critical Questions)

### 1) Current `09-VERIFICATION.md` shape and required rewrite
- **Current frontmatter (lines 1-39):** `phase: 09-lifecycle-trust-legal-launch-completeness`, `verified: 2026-11-15T00:00:00Z`, `status: gaps_found`, `score: 4/6 success criteria verified`, `gaps:` with 4 items (truth/status/reason/artifacts/missing), `human_verification:` with 3 items. [VERIFIED: `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md:1-107`]
- **Body sections present:** `# Phase 9... Verification Report`, Goal/Verified/Status/Re-verification header, `## Goal Achievement` → `### Observable Truths (ROADMAP Success Criteria)` (6 rows), `### Required Artifacts`, `### Key Link Verification`, `### Data-Flow Trace (Level 4)`, `### Behavioral Spot-Checks`, `### Requirements Coverage`, `### Anti-Patterns Found` (3 rows), `### Human Verification Required` (3 subsections), `### Gaps Summary`, footer. [VERIFIED: same file]
- **Three anti-pattern rows to preserve as CLOSED (D-07):** `.planning/ROADMAP.md:89` stale `(ou Bearer JWT admin)` blocker (closed by `b9a38c6` ROADMAP alignment evidence/confirmation), `scripts/verify-deploy.ps1:199` weak `imatch 'intermedi'` warning (closed by `b9a38c6`), `docs/DEPLOY.md` missing human-gated/prep row/`--no-sync` docs warning (closed by `b3e6940`). [VERIFIED: 09-VERIFICATION.md anti-pattern table + git log]
- **Rewrite target (D-05/D-06):** keep single file, `status: passed`, `score: 6/6 success criteria verified`, add machine-readable `caveats:` (non-canonical hosts `https://empreganoix-six.vercel.app` + `https://nqu-backend-x60n.onrender.com`, Phase 13/BRND-04 ownership), keep `initial_verified` (2026-11-15 original) and add `reconciled` date, add compact “Superseded findings” table mapping each original gap to closing commit/artifact, keep anti-pattern rows marked CLOSED, lean `human_verification` (D-03), Nyquist note (D-08), reproduce block (D-12), one-line progression note (D-04).

### 2) ROADMAP Phase 9 criterion 2 (verify-only, D-02)
- **Exact current line (ROADMAP):** `.planning/ROADMAP.md:95` → `2. Vagas expiradas são hard-deleted do banco por sweep protegido exclusivamente por header \`X-Cron-Secret\` (um Bearer JWT de admin NÃO é aceito — T-06-01); o job roda de forma idempotente em UTC e nunca apaga vagas com \`expires_at\` no futuro.` [VERIFIED: `gsd-sdk query roadmap.get-phase 12/9 context` + file]
- **Aligned by:** commit `b9a38c6` (“Align ROADMAP criterion 2…” per `09-04-SUMMARY.md`). [VERIFIED: git log]
- **Matches implementation/tests/docs:** `backend/app/api/v1/admin.py` `POST /expire` uses `Depends(require_cron_secret)` only; `backend/app/deps.py` enforces 503 unconfigured / 401 missing-wrong via `compare_digest`; `backend/tests/test_admin_expire.py::test_admin_bearer_token_is_not_a_cron_secret`; `docs/DEPLOY.md:182` “Credencial única… aceita **somente** `X-Cron-Secret`”. [VERIFIED: codebase/tests/docs] **Conclusion:** verify-only, no ROADMAP edit.

### 3) Targeted backend tests: assertions, invocation, prerequisites, read-only run
- **`tests/test_schema.py`:** asserts `JobStatus` 4 values/rejects bogus, DB rejects invalid enum, `at_least_one_contact` CHECK, behavioural 14-day delta, and DDL pin `test_expires_at_column_is_timestamptz_with_14_day_default` (timestamptz for created/expires, normalized default contains `now()` + `'14 days'::interval`, index `ix_jobs_expires_at`). [VERIFIED]
- **`tests/test_admin_expire.py`:** 503 unconfigured, 401 missing/wrong, 401 wrong CRON_SECRET, `test_admin_bearer_token_is_not_a_cron_secret` (401), deletes expired published+pending, preserves future, idempotent, **uncommitted** `test_expire_deletes_expired_row_for_every_status` for all 4 statuses, empty-table zero. [VERIFIED]
- **`tests/test_report_api.py`:** no-body ok, reason logged, >500 rejected 422, unknown job ok, whitespace-only, **uncommitted** 500-char accepted/logged, **uncommitted** `test_report_persists_nothing` (`to_regclass('public.reports') is None`), 6th request 429. [VERIFIED]
- **`tests/test_cors.py`:** exact-origin echo, foreign-origin denied, report preflight allowed, unsafe prod origins rejected (empty/wildcard/trailing-slash/scheme-less), spaces stripped, dev permissive (relies on `Settings._validate_cors_origins` in `backend/app/core/config.py`). [VERIFIED]
- **Exact invocation/prereqs:** run from `backend/` with venv interpreter: `cd backend; .venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py tests/test_cors.py -q` (from repo root loses `pyproject.toml`/`asyncio_mode=auto`, per STATE/09 plan context). `backend/pyproject.toml` sets pytest config (asyncio_mode auto implied by project conventions/tests). [VERIFIED: existing project pattern]
- **Read-only run (2026-11-15, this session):** `..EEEEEEEEEEEEEEEEEEEEEEEEEEE...... [100%]` then **ERRORs at setup** for DB-backed tests with `asyncpg.exceptions.UndefinedTableError: relation "jobs" does not exist` during fixture cleanup (`DELETE FROM jobs`). This indicates the local test database/schema is not migrated/available in this environment (not an assertion failure in the contracts themselves). Planner must account for this when defining “fresh evidence”: either run against a migrated test DB or capture the environment blocker honestly; do not claim green passes without a successful run. [VERIFIED: command executed in `backend/`]

### 4) `docs/DEPLOY.md` cited evidence (criterion 6, D-01/D-03/D-04)
- **2026-11-12 failed smoke (superseded context):** rows 308 (`env=dev`, `turnstile.mode=test`), 310 (CORS preflight 400), 316 (`verify-deploy.ps1` failed on check 1). [VERIFIED: `docs/DEPLOY.md:308,310,316`]
- **2026-11-13 preparation:** row 318 records artifacts prepared/aligned and criterion 6 remains human-gated/not executed. [VERIFIED: `docs/DEPLOY.md:318`]
- **2026-11-15 passing criterion 6 evidence:** row 320 — Frontend `https://empreganoix-six.vercel.app`, Backend `https://nqu-backend-x60n.onrender.com`, **PASS `verify-deploy: all checks passed`** (health 200 `env=prod`, `turnstile.mode=live`; CORS allow canonical Vercel / deny `https://evil.example`; board/legal/API OK; cron unauthorized rejected and authorized idempotent; no secret leak), cold-start `0.2s`, “Evidência humana aprovada (2026-11-15)”. [VERIFIED: `docs/DEPLOY.md:320`]
- **Supporting runbook facts:** `uv run --no-sync` at :65/:94/:191, “Credencial única” cron note :182, “Critério 6 (human-gated)” block :214. [VERIFIED]
- **Caveat required (D-01):** run used non-canonical hosts differing from roadmap’s canonical `empreganoix.vercel.app` / `empreganoix.onrender.com`; canonical-host confirmation/re-smoke owned by Phase 13 (BRND-04).

### 5) `09-04-SUMMARY.md` frontmatter and minimal `LIFE-13` repair (D-14)
- **Current:** frontmatter includes `requirements-completed: [LIFE-10, LIFE-11, LIFE-12, TRST-10, TRST-11, TRST-12]` and `duration/completed 2026-11-15`; body states it aligned ROADMAP criterion 2 to X-Cron-Secret-only/T-06-01 and recorded criterion 6 evidence. [VERIFIED: `09-04-SUMMARY.md`]
- **Minimal in-place edit:** add `LIFE-13` to `requirements-completed` (list becomes `[..., TRST-11, TRST-12, LIFE-13]` or equivalent) because 09-04 performed cron-contract alignment; keep `provides`, `key-files`, accomplishments, decisions, and other frontmatter/body consistent/unchanged except any necessary cross-reference text if present. [CITED: D-14, Phase 11 traceability-repair precedent in 11-CONTEXT]

### 6) `09-VALIDATION.md` Nyquist ratings and D-08 follow-up note
- **Frontmatter/state:** `status: approved`, `nyquist_compliant: true`, `wave_0_complete: true` (planning-time approval). Per-task map statuses are all `⏳ pending` in the table, but `backend/tests/test_cors.py` and other referenced artifacts now exist in repo/working tree context. [VERIFIED: `09-VALIDATION.md`]
- **Milestone audit context:** v1.1 audit rates Phase 9 Nyquist coverage **partial** (`.planning/v1.1-MILESTONE-AUDIT.md` Nyquist section). [VERIFIED: audit]
- **D-08 required note (substance):** state that `09-VALIDATION.md` exists but milestone audit rates Phase 9 Nyquist coverage partial, and closing it is a separate `/gsd-validate-phase 09` task — not part of Phase 12.

### 7) Stray root scripts `add_coldstart.py` / `add_scheduler.py` (D-11)
- **`add_coldstart.py`:** Python one-off that replaces a hardcoded cold-start paragraph in `docs/DEPLOY.md` to mention `uv run --no-sync`. The target text (`uv run --no-sync` in boot/cold-start, lines 94/191 and related) is already present in `docs/DEPLOY.md`. [VERIFIED: script content + `docs/DEPLOY.md` matches]
- **`add_scheduler.py`:** Python one-off that inserts `SCHEDULER_ENABLED: "true"` into `render.yaml` after `JWT_EXPIRES_IN`. `render.yaml:56` already contains `- key: SCHEDULER_ENABLED` with value `"true"` and start command uses `uv run --no-sync`. [VERIFIED: script content + `render.yaml`]
- **Conclusion:** both are obsolete patch scripts whose edits have landed; safe to remove in a separate cleanup commit (never mixed with reconciliation). `.gsd-temp/` remains untouched.

### 8) House style precedents (`10-VERIFICATION.md`, Phase 11)
- **`10-VERIFICATION.md` (passed with caveat):** frontmatter `status: passed`, numeric score (`11/11 must-haves verified`), `overrides_applied: 0`; body includes Observable Truths table, Required Artifacts, Key Links, Behavioral Spot-Checks, Requirements Coverage, Anti-Patterns (info-level acceptable), Human Verification Required (can state “None” when checkpoint approved), Gaps Summary. [VERIFIED: `10-VERIFICATION.md`]
- **Phase 11 style (11-CONTEXT/precedent):** run-now targeted evidence with command/results/snippets (D-01/D-04 style), explicit caveats documented (not hidden), in-place traceability repair on existing artifacts, split-ownership notes for cross-phase requirements (e.g. SECR-12), per-ID parenthetical notes in REQUIREMENTS pointing to verification artifacts + footer update. Phase 12 reuses these patterns per D-06/D-09/D-12/D-13/D-16. [VERIFIED: 11-CONTEXT excerpt + current REQUIREMENTS Phase 11 notes]

### 9) Exact `REQUIREMENTS.md` edits required (D-13/D-16)
- **Lines to update (current):**
  - `46`: `- [ ] **SECR-12**: ... *(Phase 11 gap closure - split ownership... reconciliação/evidência do contrato /admin/expire (lado Phase 9, X-Cron-Secret-only, T-06-01) — owned by **Phase 12**. No full SECR-12 closure claimed in Phase 11.)*` → check `[x]` and append/update parenthetical to record Phase 12 evidence in `09-VERIFICATION.md` (Phase 9 contract) while keeping residual canonical-host/deploy evidence owned by **Phase 13**.
  - `50-53`: `LIFE-10..13` unchecked → `[x]` with per-ID evidence notes pointing to `09-VERIFICATION.md`; `LIFE-13` must carry split-ownership residual to Phase 13.
  - `64`: `TRST-11` unchecked → `[x]` with evidence note to `09-VERIFICATION.md`.
  - `72`: `BRND-04` remains Phase 13-owned (leave consistent with deferral; do not claim here).
  - Traceability bullets `87-88` may need wording sync to reflect Phase 12 completed reconciliation vs pending (planner should inspect exact current text).
  - `95`: footer `*Last updated: 2026-11-15 after Phase 11 gap-closure traceability sync...*` → update to Phase 12 reconciliation date/note. [VERIFIED: `REQUIREMENTS.md`]
- **Style:** inline per-REQ-ID parenthetical notes (Phase 11 way), no consolidated-only section.

### 10) Verification-artifact/schema risks
- **Observed consumer patterns:** Phase reports are markdown with YAML frontmatter; later audits and planning read them as evidence documents (e.g. 10-VERIFICATION used `status: passed` + `score` + `caveats`-like info in text; 09 currently uses `status/gaps/human_verification`). D-06 explicitly constrains keys: `status: passed`, `score: 6/6 success criteria verified`, `caveats:` machine-readable, `initial_verified`, `reconciled` — do not invent `passed_with_caveats`. [VERIFIED: 09/10 files + D-06]
- **`gsd-sdk` sensitivity:** `state.planned-phase` and roadmap/requirements helpers mutate ROADMAP/STATE/REQUIREMENTS via their own formats; rewriting `09-VERIFICATION.md` content is local to that phase dir and not a known structured input to those handlers. Preserve recognizable frontmatter delimiters and standard fields; avoid removing required sections used by humans/audits (Observable Truths/Artifacts/Requirements/Human Verification). [CITED: repo conventions; no handler was found to parse 09-VERIFICATION internals during this research]
- **ROADMAP/STATE:** D-02/D-15 mean no ROADMAP criterion text change expected; STATE updates, if any, should follow existing gsd-sdk flow during execution/plan metadata, not ad-hoc schema invention.

## Standard Stack

### Core (this phase)
| Library/Tool | Version/Source | Purpose | Why Standard |
|--------------|----------------|---------|--------------|
| pytest + pytest-asyncio | Backend test stack (`backend/pyproject.toml`, `asyncio_mode=auto`) | Generate/record targeted evidence for schema/expire/report/cors contracts | Project’s established executable evidence mechanism (Phase 9/11 pattern) [VERIFIED] |
| Git (`git diff`, `git log`, `git add/commit` via gsd-sdk flow) | Repo tooling | Isolate evidence vs cleanup vs docs commits (D-10/D-11 ordering) | Required for auditable SHAs cited in reconciled report [VERIFIED] |
| Markdown planning artifacts | `.planning/**` | Verification report, summary frontmatter repair, requirements traceability | Canonical GSD evidence/audit surface [VERIFIED] |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `rg`/`Select-String`/`gsd-sdk query` | Confirm lines, requirement IDs, roadmap text | Before editing to avoid drift and to quote exact evidence [VERIFIED] |
| `docs/DEPLOY.md` verification log | Production smoke evidence source | Cite 2026-11-15 row 320 and 2026-11-12 progression (no re-run) [VERIFIED] |

**Installation:** None required (no new dependencies).

## Architecture Patterns

### Recommended Plan/Commit Structure
```
Commit A (evidence, D-10): backend/app/core/config.py, backend/tests/test_admin_expire.py, backend/tests/test_report_api.py
Commit B (cleanup, D-11, separate): remove add_coldstart.py, add_scheduler.py (only if confirmed landed)
Commit C (docs-only reconciliation): 09-VERIFICATION.md rewrite, 09-04-SUMMARY.md LIFE-13 frontmatter, REQUIREMENTS.md checkboxes/notes/footer (+ STATE/ROADMAP touches only if strictly in-scope/needed)
```

### Pattern 1: Evidence-first reconciliation (Phase 11 precedent)
**What:** Run targeted tests now, capture command/cwd/SHA/date and relevant snippets, then write verification claims against that evidence.
**When to use:** Any verification backfill where artifacts claim behavior.
**Risk noted:** Local DB schema unavailable in current environment produced setup ERRORs (`relation "jobs" does not exist`) — plans must include a deterministic path to obtain green targeted evidence or explicitly document/handle the environment prerequisite. [VERIFIED: test run]

### Pattern 2: In-place canonical report with audit trail
**What:** Replace stale narrative but preserve closure trace (Superseded findings table, anti-pattern rows marked CLOSED) so history remains auditable.
**When to use:** `09-VERIFICATION.md` rewrite (D-05/D-07).

### Anti-Patterns to Avoid
- **Mixing commits:** never combine D-10 evidence with docs reconciliation or D-11 cleanup.
- **Rewriting ROADMAP criterion 2:** it is already correct; verify and cite only (D-02).
- **Claiming green tests without a successful run:** current environment lacks migrated `jobs` table; report must reflect actual evidence obtained.
- **Phase 13 scope pull-forward:** no canonical-host edits, no re-smoke, no deploy/env/CORS changes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Requirement/roadmap/state mutations | Manual ad-hoc field surgery beyond specified in-place docs | Existing `gsd-sdk query` handlers where applicable; careful targeted markdown edits for verification/summary/requirements lines per spec | Preserves project conventions and reduces accidental schema drift [CITED] |
| Production proof | Re-running smoke gate | `docs/DEPLOY.md` row 320 + caveat (D-01) | Locked decision; operator evidence already approved |
| New tests/features | Adding behavior/code fixes | Existing/ready evidence tests and docs reconciliation | Phase boundary forbids product behavior changes |

## Common Pitfalls

### Pitfall 1: Citing uncommitted evidence
**What goes wrong:** `09-VERIFICATION.md` claims “VERIFIED” but referenced files/lines aren’t at a stable SHA.
**How to avoid:** Execute D-10 commit first; record resulting SHA in D-12 reproduce block.

### Pitfall 2: Test environment not ready (DB schema missing)
**What goes wrong:** Targeted pytest run errors at setup (`relation "jobs" does not exist`) and planner assumes passes.
**How to avoid:** Make DB/migration readiness an explicit precondition or task step for D-09 evidence; capture actual pass counts/snippets only after successful execution. [VERIFIED: observed run]

### Pitfall 3: Overstating criterion 6 / host scope
**What goes wrong:** Report implies canonical hosts verified.
**How to avoid:** Machine-readable `caveats` naming actual hosts and stating Phase 13 ownership (D-01/D-03/D-06).

### Pitfall 4: Traceability inconsistency
**What goes wrong:** `09-04-SUMMARY.md`, `REQUIREMENTS.md`, and `09-VERIFICATION.md` disagree on LIFE-13/SECR-12 ownership.
**How to avoid:** Apply D-13/D-14/D-16 together in docs reconciliation; mirror Phase 11 split-note phrasing.

## Validation Architecture

> `workflow.nyquist_validation` is enabled in `.planning/config.json` (key present/true) — this section is required.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x + pytest-asyncio (`asyncio_mode=auto`), backend venv interpreter |
| Config file | `backend/pyproject.toml` |
| Quick run command | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py tests/test_cors.py -q` |
| Full suite command | `cd backend; .venv\Scripts\python.exe -m pytest -q` (out of scope for this phase) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LIFE-10 | `expires_at` timestamptz + DB-owned 14-day default + index | integration/DDL (DB-backed) | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_schema.py -q` | ✅ |
| LIFE-11 | Expired published rows hard-deleted idempotently in UTC; future preserved | integration (DB-backed) | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_admin_expire.py -q` | ✅ |
| LIFE-12 | Same expiry sweep applies to all statuses incl. `pending` | integration (DB-backed) | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_admin_expire.py -k every_status -q` | ✅ (uncommitted in working tree) |
| LIFE-13 | `/admin/expire` accepts only `X-Cron-Secret` (503/401/JWT rejected), idempotent | integration/API | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_admin_expire.py -q` | ✅ |
| TRST-11 | Report endpoint: optional reason ≤500, log-only, no persistence, throttled | integration/API | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_report_api.py -q` | ✅ (2 cases uncommitted) |
| SECR-12 (Phase 9 side) | Cron-secret-only fail-closed contract for expire endpoint | integration/API | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_admin_expire.py -q` | ✅ |

### Sampling Rate
- **Per task commit:** Run the smallest relevant targeted subset for files touched/claimed (and always re-run full D-09 subset before finalizing `09-VERIFICATION.md` evidence).
- **Per wave merge:** `cd backend; .venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py tests/test_cors.py -q`
- **Phase gate:** Targeted subset green with recorded counts/snippets + docs/traceability consistency checks before `/gsd-verify-work` (or phase completion).

### Wave 0 Gaps
- None new to create — test files exist. **Environment prerequisite:** migrated/local test database must be available; current read-only run failed at setup with missing `jobs` relation. Plans should include ensuring DB readiness (e.g. apply migrations / use configured test DB) as part of evidence generation, without changing product behavior.

## State of the Art

| Old Approach (stale 09-VERIFICATION) | Current Approach (reconciled target) | When Changed | Impact |
|--------------------------------------|--------------------------------------|--------------|--------|
| ROADMAP criterion 2 text implied admin Bearer JWT acceptable | X-Cron-Secret-only, Bearer JWT rejected (T-06-01) | `b9a38c6` (09-04) | Contract aligned in roadmap/docs; verification must confirm, not rewrite [VERIFIED] |
| Weak smoke assertion `intermedi` and incomplete runbook notes | Exact intermediary notice asserted; `uv run --no-sync` + human-gated criterion 6 documented | `b9a38c6`, `b3e6940` | Anti-patterns closable with commit evidence [VERIFIED] |
| No passing production smoke evidence | Operator-approved 2026-11-15 `verify-deploy` pass recorded (non-canonical hosts) | 2026-11-15 (docs/DEPLOY row 320) | Criterion 6 verifiable with explicit caveat + Phase 13 handoff [VERIFIED] |
| Phase 9 report `gaps_found` 4/6 | Single reconciled `passed` 6/6 report with superseded audit trail | Phase 12 (planned) | Removes audit blockers for lifecycle/trust contract verification |

**Deprecated/outdated in this context:**
- Treating `09-VERIFICATION.md` `gaps_found` body as current truth: superseded once evidence/commits are reconciled per D-04/D-05.
- Treating root `add_coldstart.py`/`add_scheduler.py` as needed: obsolete after their edits landed (D-11).

## Open Questions

1. **How to obtain green targeted pytest evidence in this environment?**
   - What we know: running the D-09 subset from `backend/` with `.venv\Scripts\python.exe -m pytest ...` errored at setup because relation `jobs` does not exist (`asyncpg.exceptions.UndefinedTableError`). [VERIFIED]
   - What's unclear: whether a migrated test database is available/configured locally for this workspace right now.
   - Recommendation: plan an explicit step to prepare the test DB/schema (per project test setup) before capturing pass/fail counts/snippets for D-09/D-12; if unavailable, record the blocker accurately rather than fabricating results.

2. **Exact `caveats:` frontmatter structure**
   - What we know: must be machine-readable and carry non-canonical-host evidence + Phase 13 ownership (D-06).
   - What's unclear: preferred YAML shape (list vs map) in this repo.
   - Recommendation: follow simple, parseable YAML (e.g. list of objects or keyed fields naming `hosts_actual`, `hosts_canonical`, `owner: Phase 13 (BRND-04)`), consistent with “machine-readable” intent; planner to choose minimal unambiguous form.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python venv + pytest | D-09 targeted evidence | ✅ interpreter/tests present; ⚠️ DB schema not ready | `.venv\Scripts\python.exe`, pytest 9.x (project) | Prepare/migrate test DB; otherwise cannot claim green evidence [VERIFIED] |
| Git | D-10/D-11/commit SHAs | ✅ | repo present | — |
| Node/frontend toolchain | — | Not required | — | N/A (no frontend changes) |
| Deployed prod hosts | Criterion 6 proof | Evidence exists in docs only | — | Cite `docs/DEPLOY.md` row 320; do not re-run (D-01) |

**Missing dependencies with no fallback:** None that block planning; test DB readiness is required to fulfill D-09 “fresh targeted test evidence” with passing results.
**Missing dependencies with fallback:** None.

## Sources

### Primary (HIGH confidence)
- `.planning/phases/12-reconcile-phase-9-lifecycle-trust-verification-contracts/12-CONTEXT.md` — locked decisions D-01..D-16 [VERIFIED]
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md`, `09-04-SUMMARY.md`, `09-VALIDATION.md`, `09-01..03-SUMMARY.md` (queried) — current gap report, completion claims, Nyquist state [VERIFIED]
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/v1.1-MILESTONE-AUDIT.md`, `.planning/PROJECT.md` — scope, traceability, audit gaps, constraints [VERIFIED]
- `docs/DEPLOY.md` (rows/sections cited), `render.yaml`, `scripts/verify-deploy.ps1` context from summaries — deploy evidence and boot config [VERIFIED]
- `backend/app/models/job.py`, `backend/app/crud/jobs.py`, `backend/app/api/v1/admin.py`, `backend/app/api/v1/public.py`, `backend/app/deps.py`, `backend/app/core/config.py` (incl. working tree) — implementation contracts [VERIFIED]
- `backend/tests/test_schema.py`, `test_admin_expire.py`, `test_report_api.py`, `test_cors.py` (+ working-tree diffs) — executable evidence definitions [VERIFIED]
- `git log` (`b9a38c6`, `b3e6940`, recent docs commits), `git status`, `git diff` — closure SHAs and pending evidence [VERIFIED]
- `10-VERIFICATION.md`, `11-CONTEXT.md` — house-style precedents [VERIFIED]
- Read-only pytest run in `backend/` (`.venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py tests/test_cors.py -q`) — environment result (setup ERROR: missing `jobs` relation) [VERIFIED]

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - repo-native tools/tests/artifacts only.
- Architecture/patterns: HIGH - directly grounded in existing phase artifacts, commits, and locked decisions.
- Pitfalls: HIGH - key risk (DB-not-ready test run) empirically observed; others derived from explicit decisions/audit.

**Research date:** 2026-11-15
**Valid until:** 2026-11-29 (stable reconciliation scope; recheck if Phase 9 artifacts or backend evidence files change)

## RESEARCH COMPLETE
