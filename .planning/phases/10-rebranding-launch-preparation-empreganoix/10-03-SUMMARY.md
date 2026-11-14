---
phase: 10-rebranding-launch-preparation-empreganoix
plan: 03
subsystem: docs-infra-tests
tags: [rebrand, docs, infra, cors, pytest, guard]

# Dependency graph
requires:
  - phase: 10-rebranding-launch-preparation-empreganoix
    provides: frontend and backend source rebranding from 10-01/10-02
provides:
  - EmpregaNoix branding and hosts in root docs, deploy runbook, infra config, and smoke gate script
  - CORS test examples aligned to empreganoix.vercel.app and automated brand-leftover guard in backend tests
  - Planning artifacts refreshed to EmpregaNoix naming while preserving historical/factual context
affects: [10-04, deploy, launch, brand-consistency]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pytest guard scanning frontend/backend for legacy brand tokens with explicit directory/file exclusions"

key-files:
  created:
    - backend/tests/test_brand_rename.py
  modified:
    - README.md
    - AGENTS.md
    - docs/DEPLOY.md
    - render.yaml
    - scripts/verify-deploy.ps1
    - backend/tests/test_cors.py
    - .planning/PROJECT.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md

key-decisions:
  - "Rewrote docs/DEPLOY.md with EmpregaNoix hosts and fixed pre-existing garbled command snippets encountered in the working copy while applying plan-required replacements (Rule 1)."
  - "Kept historical requirement text describing rename-from-NaoQueroUsar facts, while removing brand-token leftovers from titles/labels in planning docs."

patterns-established:
  - "Brand rename verification via backend/tests/test_brand_rename.py excludes .planning/node_modules/.next/__pycache__/.venv/uv.lock to avoid false positives."

requirements-completed: [BRND-01, BRND-04]

# Metrics
duration: 20min
completed: 2026-11-14
---

# Phase 10 Plan 03: Docs/Infra Rebranding & Guard Summary

**EmpregaNoix naming and production host references propagated across docs/infra/tests with a pytest brand-leftover guard and full backend suite green**

## Performance

- **Duration:** ~20 min (including full pytest suite)
- **Started:** 2026-11-14T21:07:00Z
- **Completed:** 2026-11-14T21:27:38Z
- **Tasks:** 2
- **Files modified:** 11 (1 created)

## Accomplishments
- Rebranded root README/AGENTS, deploy runbook, Render blueprint comment, and verify-deploy smoke gate script to EmpregaNoix and updated host examples to `empreganoix.vercel.app` / `empreganoix.onrender.com`.
- Updated `backend/tests/test_cors.py` host examples to the new domain and added `backend/tests/test_brand_rename.py` guard to fail on leftover `NaoQueroUsar`/`NQU`/`suportenqs` tokens in frontend/backend source.
- Refreshed planning artifacts (PROJECT/REQUIREMENTS/ROADMAP/STATE) brand naming for v1.1 context and marked BRND-04 complete in requirements tracking.

## Task Commits

Each task was committed atomically:

1. **Task 1: Renomear docs/infra e hosts** - `96af491` (docs)
2. **Task 2: Atualizar test_cors.py e artefatos de planning + grep guard** - `b47654d` (test)

## Files Created/Modified
- `README.md` - Root project title rebranded to EmpregaNoix.
- `AGENTS.md` - Project header rebranded to EmpregaNoix.
- `docs/DEPLOY.md` - Runbook rebranded with EmpregaNoix hosts and cleaned command examples.
- `render.yaml` - Blueprint header comment rebranded to EmpregaNoix backend.
- `scripts/verify-deploy.ps1` - Smoke gate description rebranded to EmpregaNoix.
- `backend/tests/test_cors.py` - CORS origin examples updated to `empreganoix.vercel.app`.
- `backend/tests/test_brand_rename.py` - Guard test preventing legacy brand token leftovers in frontend/backend.
- `.planning/PROJECT.md` - Project title/brand references updated for EmpregaNoix.
- `.planning/REQUIREMENTS.md` - v1.1 title and BRND-04 requirement marked complete.
- `.planning/ROADMAP.md` - v1.1 title/intro updated and Phase 10 progress advanced.
- `.planning/STATE.md` - Position, progress, and session continuity updated for 10-03 completion.

## Decisions Made
- Treated pre-existing garbled deploy command snippets in `docs/DEPLOY.md` as a correctness issue and restored valid commands while applying required host/brand substitutions.
- Preserved factual historical references to the prior brand where required for context, while removing actionable legacy brand tokens from code/docs/infra/planning titles.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed garbled command snippets in deploy runbook**
- **Found during:** Task 1 (Renomear docs/infra e hosts)
- **Issue:** `docs/DEPLOY.md` working copy contained corrupted repeated fragments in bcrypt and smoke-gate command examples, breaking copy/paste correctness.
- **Fix:** Restored valid PowerShell commands and kept the plan-required EmpregaNoix/host substitutions.
- **Files modified:** `docs/DEPLOY.md`
- **Verification:** `docs/DEPLOY.md` contains `# Deploy — EmpregaNoix`, `empreganoix.vercel.app`, valid command examples, and no legacy brand tokens.
- **Committed in:** `96af491` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary correctness fix to deploy documentation; no scope creep.

## Issues Encountered
- `git commit` failed once with a stale `.git/index.lock`; removed the lock and retried successfully.
- Full backend suite initially ran beyond the default 120s shell timeout in an earlier invocation; reran with extended timeout and completed successfully.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- BRND-01 and BRND-04 repo-side rename/host updates and automated guard coverage are complete.
- Phase 10 plan 10-04 (launch/deploy execution and smoke gate) can proceed on the rebranded codebase.

## Self-Check: PASSED

- FOUND: README.md
- FOUND: AGENTS.md
- FOUND: docs/DEPLOY.md
- FOUND: render.yaml
- FOUND: scripts/verify-deploy.ps1
- FOUND: backend/tests/test_cors.py
- FOUND: backend/tests/test_brand_rename.py
- FOUND: .planning/PROJECT.md
- FOUND: .planning/REQUIREMENTS.md
- FOUND: .planning/ROADMAP.md
- FOUND: .planning/STATE.md
- FOUND: .planning/phases/10-rebranding-launch-preparation-empreganoix/10-03-SUMMARY.md
- FOUND commit: 96af491
- FOUND commit: b47654d
- Verified: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_cors.py tests/test_brand_rename.py -q` → 10 passed
- Verified: `cd backend; .\.venv\Scripts\python.exe -m pytest -q` → 288 passed, 3 skipped, 1 warning
- Verified: no leftover `NaoQueroUsar`/`NQU`/`suportenqs` in frontend/backend (excluding .planning, uv.lock, test_brand_rename.py, node_modules, .next, __pycache__, .venv)

---
*Phase: 10-rebranding-launch-preparation-empreganoix*
*Completed: 2026-11-14*
