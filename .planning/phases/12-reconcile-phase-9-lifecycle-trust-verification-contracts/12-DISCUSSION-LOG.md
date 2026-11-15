# Phase 12: Reconcile Phase 9 Lifecycle/Trust Verification & Contracts - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-15
**Phase:** 12-reconcile-phase-9-lifecycle-trust-verification-contracts
**Areas discussed:** Criterion 6 verdict, 09-VERIFICATION shape, Evidence depth & uncommitted code, Requirement closure semantics

---

## Criterion 6 verdict

| Option | Description | Selected |
|--------|-------------|----------|
| Verified with host caveat | Mark criterion 6 VERIFIED on the recorded 2026-11-15 passing smoke, with an explicit non-canonical-host caveat and Phase 13 hand-off; no re-run | ✓ |
| Stay human-gated until Phase 13 | Keep criterion 6 not-closed until Phase 13 aligns canonical hosts and re-runs the gate | |
| Re-run smoke on canonical hosts now | Attempt a fresh verify-deploy against `empreganoix.*` hosts inside Phase 12 | |

**User's choice:** Verified with host caveat
**Notes:** No re-run in Phase 12; canonical-host confirmation is Phase 13 (BRND-04).

### ROADMAP contract text handling

| Option | Description | Selected |
|--------|-------------|----------|
| Verify only, no rewrite | Criterion 2 already aligned by `b9a38c6`; confirm against code/tests/docs and record as evidence | ✓ |
| Strengthen criterion 2 text | Add fail-closed status codes, idempotent response shape and test pointer to the criterion | |
| You decide | Let planning decide the amount of contract wording | |

**User's choice:** Verify only, no rewrite

### Human-verification section

| Option | Description | Selected |
|--------|-------------|----------|
| Keep lean record + Phase 13 follow-up | Short `human_verification` block recording the operator-run 2026-11-15 gate and the canonical-host follow-up | ✓ |
| Remove it — gate closed | Drop the section because criterion 6 now passes | |
| Move to prose follow-ups | Replace the frontmatter block with a prose "Operational follow-ups" section | |

**User's choice:** Keep lean record + Phase 13 follow-up

### Superseded failed-run history

| Option | Description | Selected |
|--------|-------------|----------|
| Keep one-line progression note | Note the 2026-11-12 failure (`env=dev`, Turnstile test, CORS 400) superseded by the 2026-11-15 pass | ✓ |
| Keep full failed-run detail | Preserve exactly which checks failed and why | |
| Drop it | State only the current verified state | |

**User's choice:** Keep one-line progression note

---

## 09-VERIFICATION shape

| Option | Description | Selected |
|--------|-------------|----------|
| Rewrite in place + superseded table | One file stays authoritative; body refreshed and a compact superseded-findings table records the closed gaps | ✓ |
| Append addendum, keep original body | Leave the `gaps_found` body and append a dated reconciliation section | |
| Separate 09-REVERIFICATION.md | Freeze the original and write a new superseding report | |

**User's choice:** Rewrite in place + superseded table

### Frontmatter

| Option | Description | Selected |
|--------|-------------|----------|
| passed + caveats key | `status: passed`, `score: 6/6`, machine-readable `caveats:` entry, `reconciled:`/`initial_verified:` dates | ✓ |
| passed, caveat in body only | Keep frontmatter minimal; caveat only in prose | |
| New passed_with_caveats status | Introduce a new status value | |

**User's choice:** passed + caveats key

### Anti-patterns table

| Option | Description | Selected |
|--------|-------------|----------|
| Keep rows, mark CLOSED + commit | Three original rows stay, marked CLOSED with `b9a38c6` / `b3e6940` | ✓ |
| Drop resolved rows | Reserve the table for new findings only | |
| Move into superseded table | Collapse into the superseded-findings table | |

**User's choice:** Keep rows, mark CLOSED + commit

### Nyquist coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Note it as separate follow-up | Record that `09-VALIDATION.md` coverage is partial and closing it is `/gsd-validate-phase 09` | ✓ |
| Leave it out | Out of scope for a reconciliation report | |
| Fold validation into this phase | Close Nyquist validation inside Phase 12 | |

**User's choice:** Note it as separate follow-up

---

## Evidence depth & uncommitted code

| Option | Description | Selected |
|--------|-------------|----------|
| Targeted subset, fresh results | Run `test_schema`, `test_admin_expire`, `test_report_api`, `test_cors` now and embed command/counts/snippets | ✓ |
| Full backend suite | Run everything for maximal confidence | |
| Cite, don't run | Documentation-only, cite existing test definitions | |

**User's choice:** Targeted subset, fresh results
**Notes:** Follows the Phase 11 precedent of run-now evidence.

### Uncommitted working-tree evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Commit as Phase 9 evidence first | Commit `config.py` CORS validator + the two test additions before reconciling so the report cites committed code | ✓ |
| Leave uncommitted, flag it | Cite working-tree state and flag it as uncommitted | |
| Review them one by one | Decide per file with the user first | |

**User's choice:** Commit as Phase 9 evidence first

### Stray root scripts

| Option | Description | Selected |
|--------|-------------|----------|
| Inspect, then clean up separately | Inspect `add_coldstart.py` / `add_scheduler.py`; remove in a separate commit if their edits already landed; leave `.gsd-temp/` alone | ✓ |
| Leave untouched | Out of Phase 12 scope entirely | |
| Commit as tooling | Keep them under `scripts/` if reusable | |

**User's choice:** Inspect, then clean up separately

### Reproducibility

| Option | Description | Selected |
|--------|-------------|----------|
| Add reproduce block | Working directory, exact pytest command, commit SHA, date | ✓ |
| Prose only | Describe evidence without commands/SHA | |
| Separate evidence log | Keep commands in a separate file | |

**User's choice:** Add reproduce block

---

## Requirement closure semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Check all six, split-note on LIFE-13/SECR-12 | Check LIFE-10/11/12/13, TRST-11, SECR-12; residual host/deploy evidence stays with Phase 13 | ✓ |
| Check four, leave two for Phase 13 | Only LIFE-10/11/12 + TRST-11 checked | |
| Check all six, no caveat | Treat the 2026-11-15 smoke as final closure with no residual ownership | |

**User's choice:** Check all six, split-note on LIFE-13/SECR-12

### 09-04 frontmatter repair

| Option | Description | Selected |
|--------|-------------|----------|
| Repair 09-04 frontmatter in place | Add `LIFE-13` to `requirements-completed` (09-04 did the cron-contract alignment) | ✓ |
| Leave 09-04 untouched | Record LIFE-13 ownership only in Phase 12 artifacts | |
| Add a side note file | Separate traceability note in the Phase 9 directory | |

**User's choice:** Repair 09-04 frontmatter in place

### New drift rule

| Option | Description | Selected |
|--------|-------------|----------|
| Fix in-scope drift, defer ops drift | Fix Phase 9 contract/traceability/evidence drift; defer hosts/env/CORS/deploy to Phase 13 | ✓ |
| Fix everything found | Pull Phase 13 work forward as needed | |
| Audit list only | Fix exactly the audit items and note the rest | |

**User's choice:** Fix in-scope drift, defer ops drift

### REQUIREMENTS.md traceability format

| Option | Description | Selected |
|--------|-------------|----------|
| Per-ID notes, Phase 11 style | Parenthetical evidence note per requirement line + footer `Last updated:` refresh | ✓ |
| One consolidated section | Single traceability section at the end of the file | |
| Boxes only | Check the boxes, narrative only in the verification report | |

**User's choice:** Per-ID notes, Phase 11 style

---

## OpenCode's Discretion

- Plan/wave split for the reconciliation work, provided the evidence commit lands before the docs-only reconciliation commit.
- Exact test ordering inside the targeted subset and how much pytest output to quote.
- Exact wording of the superseded-findings table, `caveats:` values and the reproduce block.
- Whether to mention unrelated repo noise (e.g. the duplicate `07-...-complefaces` directory) — optional.

## Deferred Ideas

- Canonical host / env / CORS / API base alignment and canonical-host production re-smoke — Phase 13 (BRND-04 closeout).
- Nyquist validation closure for Phase 9 (`09-VALIDATION.md` partial) — `/gsd-validate-phase 09`.
- Legacy internal identifiers (`nqu-backend` service name, `nqu_admin_token` key) — not required by Phase 12.
- `.gsd-temp/` inspection and broader repo hygiene beyond the two stray root scripts.
