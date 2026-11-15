---
phase: 09-lifecycle-trust-legal-launch-completeness
plan: 04
subsystem: deploy
tags: [roadmap, smoke-gate, deploy, runbook, cron, cors, legal]
requires:
  - phase: 09-lifecycle-trust-legal-launch-completeness
    provides: Lifecycle/expire contract, legal pages, CORS hardening, and prior deploy artifacts (09-01/02/03)
provides:
  - ROADMAP criterion 2 aligned to X-Cron-Secret-only /admin/expire contract (T-06-01)
  - verify-deploy smoke gate tightened to assert exact intermediary notice on /termos-de-uso
  - DEPLOY runbook aligned to render.yaml boot (`uv run --no-sync`) with explicit criterion 6 human-gated evidence checklist and 2026-11-13 preparation log row
affects: [phase-9-verification, launch, deploy]
tech-stack:
  added: []
  patterns:
    - "Smoke gate asserts exact legal notice (accent-robust match) instead of weak substring"
    - "Launch criterion 6 documented as human-gated with explicit env/Turnstile/CORS/cron evidence requirements"
key-files:
  created: []
  modified:
    - .planning/ROADMAP.md
    - scripts/verify-deploy.ps1
    - docs/DEPLOY.md
key-decisions:
  - "None - followed plan as specified"
patterns-established:
  - "Repository artifacts may be prepared, but production criterion 6 closes only after operator-run deploy and recorded verify-deploy evidence"
requirements-completed:
  - LIFE-10
  - LIFE-11
  - LIFE-12
  - TRST-10
  - TRST-11
  - TRST-12
duration: 15min
completed: 2026-11-15
---

# Phase 9 Plan 04: Lifecycle/Trust/Legal Launch Gap Closure Summary

**ROADMAP and deploy gate/runbook now match the shipped X-Cron-Secret-only expire contract and exact intermediary notice, with criterion 6 explicitly documented as a pending human-gated production smoke verification.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-11-15T00:00:00Z
- **Completed:** 2026-11-15T00:00:00Z (paused at Task 3 human checkpoint)
- **Tasks:** 2/3 automated tasks completed (Task 3 pending human verification)
- **Files modified:** 3

## Accomplishments
- Aligned Phase 9 ROADMAP criterion 2 to the enforced contract: `/admin/expire` is protected exclusively by `X-Cron-Secret` and a Bearer JWT admin is not accepted (T-06-01).
- Tightened `scripts/verify-deploy.ps1` check 5 to require the exact intermediary notice `somos apenas meio de divulgação` (accent-robust `somos apenas meio de divulga`) and removed the weak `intermedi` assertion.
- Updated `docs/DEPLOY.md` to match `render.yaml` boot behavior (`uv run --no-sync`), added an explicit **Critério 6 (human-gated)** evidence checklist (env=prod, Turnstile mode, CORS allow/deny preflight, cron checks, recorded pass), and appended the `2026-11-13 | Preparação de deploy (Fase 9)` verification row while preserving prior history.

## Task Commits

Each task was committed atomically:

1. **Task 1: Align ROADMAP criterion 2 and tighten verify-deploy exact intermediary notice** - `b9a38c6` (docs)
2. **Task 2: Update DEPLOY.md with criterion 6 human-gated readiness, 2026-11-13 prep row, and uv run --no-sync alignment** - `b3e6940` (docs)
3. **Task 3: Execute production deploy and record passing criterion 6 smoke-gate evidence** - _pending human verification (checkpoint:human-verify, blocking)_

**Plan metadata:** pending (final metadata commit deferred until Task 3 evidence/resolution is recorded)

## Files Created/Modified
- `.planning/ROADMAP.md` - Phase 9 criterion 2 corrected to X-Cron-Secret-only auth and explicit rejection of admin Bearer JWT (T-06-01).
- `scripts/verify-deploy.ps1` - Smoke gate check 5 now asserts the exact intermediary notice on `/termos-de-uso`.
- `docs/DEPLOY.md` - Runbook documents `uv run --no-sync` boot/cold-start, explicit criterion 6 human-gated requirements/evidence, and 2026-11-13 preparation log entry.

## Decisions Made
None - followed plan as specified.

## Deviations from Plan

None - plan executed exactly as written for Tasks 1-2.

## Issues Encountered
- Verification commands using complex PowerShell quoting via the shell tool failed to parse; acceptance criteria were confirmed via direct file inspection/grep and the edits match the plan exactly.

## Authentication Gates
None.

## User Setup Required
**External operator action required for Task 3 (criterion 6).** Repository-side artifacts are prepared, but production deploy and smoke-gate evidence remain human-gated.

## Known Stubs
None.

## Threat Flags
None.

## Next Phase Readiness
- **Blocked (human-gated):** Task 3 requires a real production deploy and operator-run `scripts/verify-deploy.ps1` pass with recorded evidence in `docs/DEPLOY.md` (env=prod, Turnstile mode live or explicitly approved test_override, CORS allow/deny preflight, cron unauthorized rejected + authorized idempotent, cold-start).
- Once Task 3 evidence is recorded and approved, finalize this plan's metadata/state updates and close the remaining Phase 9 criterion 6 gap.

## Self-Check: PASSED

- FOUND: `.planning/ROADMAP.md`
- FOUND: `scripts/verify-deploy.ps1`
- FOUND: `docs/DEPLOY.md`
- FOUND: `b9a38c6`
- FOUND: `b3e6940`
- Task 3: checkpoint reached, awaiting human verification (not fabricated)

---
*Phase: 09-lifecycle-trust-legal-launch-completeness*
*Completed: 2026-11-15 (paused at Task 3 checkpoint)*
