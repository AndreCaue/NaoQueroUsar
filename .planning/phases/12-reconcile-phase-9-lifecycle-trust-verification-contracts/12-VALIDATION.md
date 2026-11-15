---
phase: 12
slug: reconcile-phase-9-lifecycle-trust-verification-contracts
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-15
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + pytest-asyncio (`asyncio_mode=auto`) |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py tests/test_cors.py -q` |
| **Full suite command** | `cd backend; .venv\Scripts\python.exe -m pytest -q` |
| **Estimated runtime** | ~60-180 seconds (targeted subset; depends on migrated test DB availability) |

---

## Sampling Rate

- **After every task commit:** Run the task's `<automated>` command (targeted pytest subset, diff/grep checks, or artifact/schema checks as specified in PLANs)
- **After every plan wave:** Run `cd backend; .venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py tests/test_cors.py -q` (once DB/migrations prerequisite is satisfied) and spot-check updated planning artifacts
- **Before `/gsd-verify-work`:** Targeted subset green with recorded counts/snippets; `09-VERIFICATION.md`, `09-04-SUMMARY.md`, and `REQUIREMENTS.md` reconciled per D-01..D-16
- **Max feedback latency:** 180 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-??-?? | TBD | 1 | LIFE-10 | T-06-01 / — | DB-owned 14-day `expires_at` (timestamptz, default, index) evidenced without behavior change | integration/DDL (DB-backed) | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_schema.py -q` | ✅ | ⬜ pending |
| 12-??-?? | TBD | 1 | LIFE-11, LIFE-12 | T-06-01 | Status-agnostic, idempotent, UTC/DB-clock expiry sweep evidenced (all statuses, future rows preserved) | integration | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_admin_expire.py -q` | ✅ | ⬜ pending |
| 12-??-?? | TBD | 1 | LIFE-13, SECR-12 | T-06-01 | `/admin/expire` remains `X-Cron-Secret`-only and fail-closed (503/401/JWT rejected); contract/evidence reconciled, ROADMAP criterion 2 verified-only | integration + static | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_admin_expire.py -q; Select-String -Path .planning/ROADMAP.md -Pattern "protegido exclusivamente por header ``X-Cron-Secret``"` | ✅ | ⬜ pending |
| 12-??-?? | TBD | 1 | TRST-11 | — | Report endpoint accept-and-log, 500-char inclusive cap, no persistence, throttled (evidence committed/reconciled) | integration | `cd backend; .venv\Scripts\python.exe -m pytest tests/test_report_api.py -q` | ✅ | ⬜ pending |
| 12-??-?? | TBD | 1 | — (D-10) | — | Pending Phase 9 evidence files committed as isolated commit before docs reconciliation | git/static | `git status --short -- backend/app/core/config.py backend/tests/test_admin_expire.py backend/tests/test_report_api.py` (expect clean after commit) | ✅ | ⬜ pending |
| 12-??-?? | TBD | 1 | — (D-11) | — | Obsolete root patch scripts removed in separate cleanup commit; `.gsd-temp/` untouched | static | `Test-Path add_coldstart.py,add_scheduler.py` (expect False after cleanup) | ✅ | ⬜ pending |
| 12-??-?? | TBD | 1 | LIFE-10..13, TRST-11, SECR-12 | — | `09-VERIFICATION.md` rewritten in place (passed 6/6, caveats, initial_verified/reconciled, superseded findings, closed anti-patterns, lean human block, Nyquist note, reproduce block) | artifact/static | `Select-String -Path .planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md -Pattern "status: passed|score: 6/6|caveats:|initial_verified:|reconciled:|Superseded findings|Nyquist"` | ✅ | ⬜ pending |
| 12-??-?? | TBD | 1 | LIFE-13 | — | `09-04-SUMMARY.md` frontmatter includes `LIFE-13` in `requirements-completed` | artifact/static | `Select-String -Path .planning/phases/09-lifecycle-trust-legal-launch-completeness/09-04-SUMMARY.md -Pattern "requirements-completed:.*LIFE-13"` | ✅ | ⬜ pending |
| 12-??-?? | TBD | 1 | LIFE-10..13, TRST-11, SECR-12 | — | `REQUIREMENTS.md` checkboxes/notes/footer updated with split ownership for LIFE-13/SECR-12 and Phase 13 residual | artifact/static | `Select-String -Path .planning/REQUIREMENTS.md -Pattern "^- \[x\] \*\*LIFE-10\*\*|^- \[x\] \*\*LIFE-11\*\*|^- \[x\] \*\*LIFE-12\*\*|^- \[x\] \*\*LIFE-13\*\*|^- \[x\] \*\*TRST-11\*\*|^- \[x\] \*\*SECR-12\*\*"` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements (tests and artifacts already exist).
- **Environment prerequisite:** migrated/local test database must be available for DB-backed pytest targets; a 2026-11-15 read-only run failed at setup with `asyncpg.exceptions.UndefinedTableError: relation "jobs" does not exist`. Resolve DB readiness before recording passing evidence.

*If none beyond prerequisite: "Existing infrastructure covers all phase requirements (DB readiness required)."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Canonical-host production smoke confirmation/re-smoke (`empreganoix.vercel.app` / `empreganoix.onrender.com`) | LIFE-13, SECR-12 (residual), BRND-04 handoff | Operator/deploy action on canonical hosts; explicitly deferred to Phase 13 (D-01, D-03, D-15) | Run operator smoke gate against canonical hosts in Phase 13 and record evidence; Phase 12 must only cite non-canonical 2026-11-15 pass and caveat |
| Operator-approved 2026-11-15 non-canonical smoke gate provenance | Phase 9 criterion 6 evidence | External execution recorded in `docs/DEPLOY.md:320` | Confirm row 320 details (hosts, `env=prod`, `turnstile.mode=live`, CORS allow/deny, cron rejected/idempotent, no secret leak) are accurately reflected in reconciled `09-VERIFICATION.md` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
