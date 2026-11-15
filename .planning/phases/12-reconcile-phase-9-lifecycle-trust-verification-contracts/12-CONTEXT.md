# Phase 12: Reconcile Phase 9 Lifecycle/Trust Verification & Contracts - Context

**Gathered:** 2026-11-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Bring the Phase 9 planning artifacts — `09-VERIFICATION.md`, the ROADMAP `/admin/expire` contract text, and `REQUIREMENTS.md` traceability — in line with the lifecycle/trust/cron-secret-only behavior that is already implemented, tested and documented. This is an **evidence-and-contract reconciliation phase**: no product behavior, no backend/frontend feature code.

**In scope:** reconcile `09-VERIFICATION.md` with current repository state (fresh targeted test evidence, closed gaps, host caveat); confirm the ROADMAP Phase 9 criterion 2 contract already matches `X-Cron-Secret`-only enforcement (it does — commit `b9a38c6`); update `REQUIREMENTS.md` checkboxes/traceability for `LIFE-10..13`, `TRST-11` and the Phase 9 side of `SECR-12`; repair `09-04-SUMMARY.md` frontmatter to include `LIFE-13`; commit the uncommitted Phase 9 evidence that the verification report already cites.

**Out of scope:** canonical host / env / CORS / deploy execution alignment and BRND-04 production evidence (owned by **Phase 13**); Nyquist validation closure for Phase 9 (`/gsd-validate-phase 09`); any new lifecycle, trust, legal or ops capability; re-litigating T-06-01 (locked: `/admin/expire` is `X-Cron-Secret`-only, admin Bearer JWT is rejected).

</domain>

<decisions>
## Implementation Decisions

### Criterion 6 verdict (production deploy + green smoke gate)
- **D-01:** Mark ROADMAP Phase 9 criterion 6 as **VERIFIED with an explicit host caveat**. Evidence is the operator-approved `verify-deploy` pass recorded in `docs/DEPLOY.md` (`2026-11-15` row): health 200 `env=prod`, Turnstile `mode=live`, CORS allow/deny preflight, board/legal/API, cron rejected-then-idempotent, no secret leak. The caveat must state that the run was executed against `https://empreganoix-six.vercel.app` + `https://nqu-backend-x60n.onrender.com`, which differ from the roadmap's canonical `empreganoix.vercel.app` / `empreganoix.onrender.com`, and that canonical-host confirmation and any re-smoke belong to **Phase 13 (BRND-04)**. Do not re-run the smoke gate in Phase 12.
- **D-02:** **Verify only — do not rewrite ROADMAP criterion 2.** Commit `b9a38c6` already changed it to `protegido exclusivamente por header X-Cron-Secret (um Bearer JWT de admin NÃO é aceito — T-06-01)`. Phase 12 confirms it against `backend/app/api/v1/admin.py`, `backend/app/deps.py`, `backend/tests/test_admin_expire.py` and `docs/DEPLOY.md`, and records that confirmation as evidence. No further contract wording edits.
- **D-03:** Keep a **lean `human_verification` block** in the reconciled report recording the operator-run 2026-11-15 gate (command, hosts, result) plus the single remaining human/ops follow-up: canonical-host confirmation and re-smoke, owned by Phase 13. Do not delete it and do not downgrade the phase because of it.
- **D-04:** Keep a **one-line progression note** for the superseded 2026-11-12 failed smoke (`env=dev`, Turnstile `mode=test`, CORS preflight 400) → superseded by the 2026-11-15 pass after the 09-03/09-04 hardening. Do not reproduce the full failing detail.

### 09-VERIFICATION shape
- **D-05:** **Rewrite `09-VERIFICATION.md` in place.** It stays the single source of truth: frontmatter refreshed, body updated to current state, and a compact **"Superseded findings"** table listing each of the originally reported gaps with the commit/artifact that closed it (`b9a38c6`, `b3e6940`, `docs/DEPLOY.md` rows, current tests). Do not create a separate `09-REVERIFICATION.md` and do not leave the original `gaps_found` body as a competing narrative.
- **D-06:** Reconciled frontmatter: `status: passed`, `score: 6/6 success criteria verified`, a machine-readable **`caveats:`** entry carrying the non-canonical-host production evidence + Phase 13 ownership, and both `initial_verified:` (2026-11-15, original run) and `reconciled:` (this phase) dates. Do not invent a `passed_with_caveats` status value.
- **D-07:** Keep the **Anti-Patterns** table with the three original rows (stale ROADMAP text, weak `intermedi` smoke assertion, incomplete `docs/DEPLOY.md`), each now marked **CLOSED** with the closing commit — `b9a38c6` for the ROADMAP contract and smoke-gate assertion, `b3e6940` for the runbook. Do not delete the rows; they are the audit trail of what was wrong.
- **D-08:** Add a short **Nyquist follow-up note**: `09-VALIDATION.md` exists but the milestone audit rates Phase 9 Nyquist coverage partial, and closing it is a separate `/gsd-validate-phase 09` task — not part of this phase.

### Evidence depth & working tree
- **D-09:** Generate **fresh targeted test evidence**: run `cd backend; .venv\Scripts\python.exe -m pytest <targets>` over `tests/test_schema.py`, `tests/test_admin_expire.py`, `tests/test_report_api.py`, `tests/test_cors.py`, and embed command, pass/fail counts and relevant snippets in the reconciled report. This follows the Phase 11 precedent (D-01/D-04: run tests now, do not restate summaries). Do not run the full suite for this phase.
- **D-10:** **Commit the pending Phase 9 evidence before reconciling**, as its own commit: `backend/app/core/config.py` (CORS fail-closed `_validate_cors_origins`), `backend/tests/test_admin_expire.py` (all-status expiry test), `backend/tests/test_report_api.py` (500-char + no-persistence tests). `09-VERIFICATION.md` already cites these as VERIFIED, so they are Phase 9 evidence that was never committed — they must exist at a known SHA before the reconciled report cites them. Do **not** mix this with the later docs-only reconciliation commit.
- **D-11:** Inspect root-level untracked `add_coldstart.py` and `add_scheduler.py`. If they are one-off patch scripts whose edits already landed in `docs/DEPLOY.md` / `render.yaml`, remove them in a **separate cleanup commit** — never inside the reconciliation commit. Leave `.gsd-temp/` untouched and out of scope.
- **D-12:** Add a **"How this was verified" / reproduce block** to the reconciled report: working directory (`backend/`), exact pytest command(s), the commit SHA at verification time, and the date, so the next auditor can re-run the same evidence.

### Requirement closure semantics
- **D-13:** In `.planning/REQUIREMENTS.md`, **check all six** Phase 12 requirements: `LIFE-10`, `LIFE-11`, `LIFE-12`, `LIFE-13`, `TRST-11`, `SECR-12`. `LIFE-10/11/12` and `TRST-11` are pure Phase 9 code contracts (no residual). `LIFE-13` and `SECR-12` get an explicit **split-ownership note**: code/contract side verified here (`09-VERIFICATION.md`), residual canonical-host/deploy evidence owned by **Phase 13**, which keeps both IDs in its requirement list.
- **D-14:** **Repair `09-04-SUMMARY.md` frontmatter in place** by adding `LIFE-13` to `requirements-completed` — 09-04 performed the ROADMAP/REQUIREMENTS/DEPLOY cron-contract alignment. This mirrors Phase 11's in-place traceability repair on Phase 8 artifacts; keep `provides`/`key-files` consistent.
- **D-15:** Drift rule — fix **in-scope** drift in this phase (Phase 9 contract, traceability, verification/evidence alignment, stale statements about the cron gate). **Defer** anything touching canonical hosts, env vars, CORS values or deploy execution to Phase 13. Do not pull Phase 13 work forward.
- **D-16:** Record traceability in `REQUIREMENTS.md` the **Phase 11 way**: a parenthetical note on each requirement line pointing to the evidence in `09-VERIFICATION.md` (plus the Phase 13 residual ownership for `LIFE-13`/`SECR-12`), and update the footer `Last updated:` line. No consolidated-only section.

### OpenCode's Discretion
- Exact plan/wave split for the reconciliation work (documentation edit vs evidence commit vs REQUIREMENTS update), as long as D-10's evidence commit lands before the docs-only reconciliation commit.
- Exact selection/order of test files within the D-09 subset and how much pytest output to quote.
- Precise wording of the "Superseded findings" table, the `caveats:` key contents and the "How this was verified" block, provided the caveat names the actual hosts and the Phase 13 hand-off.
- Whether to mention the duplicate `07-contact-reveal-anti-spam-complefaces` directory or other unrelated repo noise in the report — optional, not required by the audit.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope, audit and traceability
- `.planning/ROADMAP.md` — Phase 12 goal, requirements (`LIFE-10..13`, `TRST-11`, `SECR-12`), success criteria, and Phase 9 criterion 2 current wording (line 95, already `X-Cron-Secret`-only) and Phase 13 ownership.
- `.planning/REQUIREMENTS.md` — the six requirement lines to update (LIFE-10..13, TRST-11, SECR-12) plus `BRND-04` for the Phase 13 hand-off.
- `.planning/v1.1-MILESTONE-AUDIT.md` — authoritative gap list: stale `09-VERIFICATION.md`, ROADMAP contract drift, unchecked lifecycle/trust requirements, host canonicalization risk, Nyquist table.
- `.planning/PROJECT.md` — locked constraints (pt-BR, no-login public board, stack, deploy targets, development-staged launch policy).
- `.planning/STATE.md` — milestone position, accumulated Phase 9/deploy decisions (2026-11-12 failed smoke vs 2026-11-15 pass, legal gate, BRND caveats).

### Phase 9 artifacts (reconciliation targets)
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md` — the report to rewrite in place (frontmatter gaps_found 4/6, three anti-patterns, human verification, gaps summary).
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-04-SUMMARY.md` — frontmatter repair target (add `LIFE-13`); records the 2026-11-15 approved criterion 6 evidence.
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-01-PLAN.md` — lifecycle/report contract scope (LIFE-10/11/12, TRST-11) and its T-06-01 alignment task.
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-01-SUMMARY.md`, `09-02-SUMMARY.md`, `09-03-SUMMARY.md` — claimed outcomes/evidence pointers.
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VALIDATION.md` — Nyquist baseline for the D-08 follow-up note.
- `.planning/phases/10-rebranding-launch-preparation-empreganoix/10-VERIFICATION.md` — recent verification-report pattern (passed phase with caveat).

### Deploy / ops evidence
- `docs/DEPLOY.md` — verification log table: 2026-11-12 failed smoke, 2026-11-13 preparation row, 2026-11-15 passing criterion 6 evidence (`:313-320`); Critério 6 human-gated block (`:214`); `uv run --no-sync` boot notes (`:65`, `:94`, `:191`); "Credencial única" cron note (`:182`).
- `scripts/verify-deploy.ps1` — smoke gate; check 5 asserts the exact intermediary notice (`:199`).
- `render.yaml` — blueprint (`SCHEDULER_ENABLED`, `uv run --no-sync` start command) referenced by the verification rows.
- `.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-CONTEXT.md` — Phase 11 precedent for run-now evidence (D-01/D-04), documented caveats (D-02), in-place traceability repair (D-07/D-08) and split ownership (D-10).

### Code and test evidence (targeted subset)
- `backend/app/models/job.py` — `expires_at` as `TIMESTAMP(timezone=True)` with `server_default=text("now() + interval '14 days'")` (LIFE-10).
- `backend/app/crud/jobs.py` — `delete_expired_jobs` status-agnostic sweep on the DB clock (LIFE-11/LIFE-12).
- `backend/app/api/v1/admin.py` — `/admin/expire` protected by `require_cron_secret` only (LIFE-13/SECR-12).
- `backend/app/deps.py` — `require_cron_secret` implementation (503 unconfigured, 401 missing/wrong).
- `backend/app/api/v1/public.py` — report endpoint accept-and-log, 500-char cap, throttle, no persistence (TRST-11).
- `backend/app/core/config.py` — CORS fail-closed validator (**currently uncommitted**, D-10) and Turnstile/rate-limit settings.
- `backend/tests/test_schema.py` — DDL pin for timestamptz + 14-day default + index.
- `backend/tests/test_admin_expire.py` — 503/401/missing/wrong/JWT-rejected, idempotency, future rows preserved, all-status sweep.
- `backend/tests/test_report_api.py` — cap, log-only, no `reports` table, 429 throttle.
- `backend/tests/test_cors.py` — exact-origin echo, foreign-origin denial, prod validator rejection.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `09-VERIFICATION.md` already has the full report skeleton (Observable Truths, Required Artifacts, Key Links, Data-Flow, Behavioral Spot-Checks, Requirements Coverage, Anti-Patterns, Human Verification, Gaps Summary) — the rewrite refreshes it rather than authoring a new structure.
- `10-VERIFICATION.md` is the nearest precedent for a `passed` phase report that still carries a caveat.
- `11-CONTEXT.md` supplies the run-now evidence pattern, caveat discipline, in-place traceability repair and split-ownership note style that Phase 12 reuses.
- `docs/DEPLOY.md` verification log already holds the authoritative production evidence rows — the report cites them instead of re-running the gate.

### Established Patterns
- Backend tests run from `backend/` (`cd backend; .venv\Scripts\python.exe -m pytest -q`); running pytest from the repo root loses `pyproject.toml` and `asyncio_mode=auto`.
- Verification artifacts are evidence-driven markdown with explicit requirement/status mapping and documented gaps/human checks.
- Requirement traceability lives inline per REQ-ID in `REQUIREMENTS.md`, written by `gsd-sdk query` handlers for ROADMAP/STATE mutations, with docs committed via `gsd-sdk query commit`.
- GSD artifacts use `{padded_phase}-{NN}-PLAN.md` / `-SUMMARY.md` naming; summaries carry YAML frontmatter with `requirements-completed`.

### Integration Points
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md` — rewritten in place (status/score/caveats/superseded table/reproduce block).
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-04-SUMMARY.md` — frontmatter gains `LIFE-13`.
- `.planning/REQUIREMENTS.md` — six checkbox flips + per-ID evidence notes + footer date.
- `.planning/ROADMAP.md` — no Phase 9 criterion edit expected (verify only); may need a progress/notes touch only if reconciliation surfaces an in-scope inconsistency.
- Backend working tree — evidence commit (D-10) must land before the report cites it; stray-script cleanup is a separate commit (D-11).

</code_context>

<specifics>
## Specific Ideas

- The ROADMAP contract is **already correct** (`ROADMAP.md:95`): "protegido exclusivamente por header `X-Cron-Secret` (um Bearer JWT de admin NÃO é aceito — T-06-01)". Phase 12 must not manufacture an edit just to satisfy the wording of its own success criterion; it verifies and records.
- The recorded production pass is real but was taken on non-canonical hosts (`empreganoix-six.vercel.app`, `nqu-backend-x60n.onrender.com`); the caveat must name both and hand the canonical-host confirmation to Phase 13, never silently imply `empreganoix.vercel.app` was verified.
- The uncommitted backend changes are the evidence base for LIFE-12 (all-status expiry), TRST-11 (500-char/no-persistence) and the CORS fail-closed claims — they must be committed before the report says "VERIFIED".
- `09-04-SUMMARY.md` frontmatter omits `LIFE-13` even though 09-04 did the cron-contract alignment; that omission is why the audit calls LIFE-13 "not explicitly in SUMMARY frontmatter".
- Keep the report's tone factual: what was wrong, what fixed it, what remains human-gated and who owns it.

</specifics>

<deferred>
## Deferred Ideas

- Canonical host / env / CORS / API base alignment and any canonical-host production re-smoke — **Phase 13 (BRND-04 closeout)**.
- Nyquist validation closure for Phase 9 (`09-VALIDATION.md` partial) — separate `/gsd-validate-phase 09` task.
- Legacy internal identifiers spotted by the audit (`nqu-backend` service name, `nqu_admin_token` storage key) — not required by Phase 12.
- `.gsd-temp/` inspection and any repo-hygiene cleanup beyond the two stray root scripts.

</deferred>

---

*Phase: 12-reconcile-phase-9-lifecycle-trust-verification-contracts*
*Context gathered: 2026-11-15*
