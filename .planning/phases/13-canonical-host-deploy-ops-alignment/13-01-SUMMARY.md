---
phase: 13-canonical-host-deploy-ops-alignment
plan: 01
subsystem: infra
tags: [deploy, ops, vercel, render, cors, turnstile, cron]

# Dependency graph
requires:
  - phase: 06-production-deploy-lifecycle
    provides: deploy artifacts, smoke gate script, expiry cron contract, and historical verification records
provides:
  - Canonical state-alvo and legacy-host mapping for EmpregaNoix production ops artifacts
  - D-10 alignment matrix covering health/CORS/expire endpoint and key public/admin surfaces with explicit status vocabulary
  - Canonical-first verify-deploy and frontend env/deploy guidance without runtime behavior changes
affects: [13-02, requirements-traceability, deploy-ops-evidence]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Canonical state-alvo documented separately from preserved historical verification evidence"
    - "Legacy host evidence mapped to canonical targets with explicit handoff/pending-execution statuses"

key-files:
  created:
    - .planning/phases/13-canonical-host-deploy-ops-alignment/13-01-SUMMARY.md
  modified:
    - docs/DEPLOY.md
    - scripts/verify-deploy.ps1
    - frontend/.env.example
    - frontend/.env.local.example
    - .github/workflows/expire-cron.yml

key-decisions:
  - "Document `https://empreganoix.vercel.app` and `https://empreganoix.onrender.com` as the canonical state-alvo while preserving all historical Registro de verificação rows verbatim as legacy evidence."
  - "Represent residual SECR-12/LIFE-13 ops evidence as mapped/handoff-tracked against the canonical contract without reopening T-06-01 or changing runtime behavior."

patterns-established:
  - "D-10 ops alignment matrix: record alvo canônico, host/evidência verificada, status, and referência for each required check."
  - "Canonical-first examples in runbook/scripts/env guidance with parameterization retained for reproducing legacy evidence."

requirements-completed: [BRND-04, SECR-12, LIFE-13]

# Metrics
duration: 12min
completed: 2026-11-15
---

# Phase 13 Plan 01: Canonical Host & Deploy Ops Alignment Summary

**Canonical EmpregaNoix deploy contract documented with legacy-host mapping, D-10 alignment matrix, and canonical-first ops guidance while preserving historical verification evidence.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-11-15T14:58:00Z
- **Completed:** 2026-11-15T15:09:38Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Reworked `docs/DEPLOY.md` to declare the canonical state-alvo (`empreganoix.vercel.app` / `empreganoix.onrender.com`), add canônico↔legado mapping, and provide a full D-10 alignment matrix for health/env/Turnstile, CORS preflight, `/admin/expire` fail-closed/idempotency, and key public/admin surfaces.
- Preserved the entire historical `## Registro de verificação` log (including 2026-11-12, 2026-11-14, and 2026-11-15 rows and pending entries) while adding explicit handoff sequence, rollback por reversão de env/config/domínio, and risk notes without reopening T-06-01.
- Aligned `scripts/verify-deploy.ps1`, frontend env examples, and expire-cron workflow guidance to canonical branded targets as primary state-alvo examples, keeping parameterization/local defaults/secret-free config and making no runtime behavior changes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Normalize DEPLOY runbook to canonical state-alvo and add legacy mapping + D-10 alignment matrix without rewriting history** - `11b74b6` (docs)
2. **Task 2: Align smoke-gate/examples and env/deploy config artifacts to canonical targets (conforme aplicável, no runtime changes)** - `a3341ac` (docs)

**Plan metadata:** `5f14022` (docs: complete plan)

## Files Created/Modified
- `docs/DEPLOY.md` - Canonical state-alvo, legacy mapping, D-10 matrix, handoff/risks, and preserved historical verification log.
- `scripts/verify-deploy.ps1` - Canonical branded hosts as primary smoke-gate example/help with legacy reproducibility note; executable logic unchanged.
- `frontend/.env.example` - Canonical production target guidance for API URLs/Turnstile origin while retaining local defaults.
- `frontend/.env.local.example` - Local-dev defaults retained with brief canonical production note.
- `.github/workflows/expire-cron.yml` - Canonical `API_BASE_URL` guidance in missing-variable error text; request/auth behavior unchanged.
- `render.yaml` - Reviewed (conforme aplicável); no changes required to preserve secret-free declarative config and behavior.
- `frontend/vercel.json` - Reviewed (conforme aplicável); remains minimal valid Next.js config.

## Decisions Made
- Treated historical deploy/smoke evidence on legacy hosts as mapped evidence (`verificado em host legado`) rather than rewriting records, keeping the branded hosts as contractual state-alvo.
- Kept SECR-12/LIFE-13 closure at contract/evidence-handoff level for this ops-alignment plan and explicitly preserved T-06-01 (`X-Cron-Secret` only, fail-closed/idempotent).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Shell tooling variance in this environment (`rg` unavailable, PowerShell quoting differences) required Python-based verification of required strings and preserved historical rows; acceptance content was confirmed present.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Repo-side canonical contract, legacy mapping, and D-10 alignment matrix are in place for Phase 13 Plan 02 traceability/closure work.
- Actual canonical-host provisioning/execution may remain `pendente de execução operacional`; follow the documented handoff sequence and record new evidence without altering historical rows.

## Self-Check: PASSED

- FOUND: docs/DEPLOY.md
- FOUND: scripts/verify-deploy.ps1
- FOUND: frontend/.env.example
- FOUND: frontend/.env.local.example
- FOUND: .github/workflows/expire-cron.yml
- FOUND: .planning/phases/13-canonical-host-deploy-ops-alignment/13-01-SUMMARY.md
- FOUND commit: 11b74b6
- FOUND commit: a3341ac
- Runtime scope check: no files modified under backend/app/, frontend/lib/, or frontend/app/

---
*Phase: 13-canonical-host-deploy-ops-alignment*
*Completed: 2026-11-15*
