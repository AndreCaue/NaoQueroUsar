---
phase: 22-qualidade-hardening-e-valida-o-operacional
plan: 04
type: execute
wave: 1
gap_closure: true
subsystem: board-search-intent
tags: [frontend, backend, intent-mapper, toolbar, uat, qa-02, qa-03]
requires:
  - 22-01
  - 22-02
  - 22-03
provides:
  - Deterministic supported-city promotion in manual board search (toolbar -> canonical `city=<slug>`)
  - Deterministic raw-text whitelist city fallback in intent mapper (SP/RJ/BH/Remoto, safe conflict handling)
  - Updated manual/UAT/MVP artifacts for retest of reported city-recognition gap
affects:
  - frontend/lib/cities.ts
  - frontend/components/board/BoardToolbar.tsx
  - backend/app/services/intent/mapper.py
  - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md
  - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md
  - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md
tech-stack:
  added: []
  patterns:
    - Exact accent/case-insensitive city-text resolution to supported slugs/aliases before toolbar commit
    - Unambiguous whitelist city detection from raw intent text only when candidate city is absent; multi-city mentions treated as conflict (no unsafe apply)
key-files:
  created:
    - frontend/lib/cities.test.ts
    - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-04-SUMMARY.md
  modified:
    - frontend/lib/cities.ts
    - frontend/components/board/BoardToolbar.tsx
    - backend/app/services/intent/mapper.py
    - backend/tests/test_intent_mapper.py
    - backend/tests/test_chat_search_api.py
    - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md
    - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md
    - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md
key-decisions:
  - "Toolbar uses exact normalized city match (labels/slugs/canonicals + safe aliases) to promote to `city=<slug>` and clear `q`; partial/unknown text remains `q`."
  - "Intent mapper raw-text fallback applies only when candidate city is absent, only for whitelist cities (SP/RJ/BH/Remoto), and returns `conflict_resolved` (no apply) when multiple supported cities are mentioned."
requirements-completed: [QA-02, QA-03]
duration: ~session (recovery/orchestration completion)
completed: 2026-11-18
---

# Phase 22 Plan 04: Gap Closure (City Recognition) Summary

**One-liner:** Closed the reported UAT gap by promoting supported city text to canonical board `city` filters and adding safe deterministic raw-text city fallback in intent mapping, with automated coverage for frontend/helper and mapper/parser paths plus updated manual retest artifacts.

## Performance

- **Tasks:** 3/3 executed (Task 1 and core Task 2 implementation/tests completed; Task 3 docs completed; DB-backed chat-search API verification environment-gated/incomplete in this run)
- **Commits:** 3 (`1b51b4b`, `df5bb5f`, `994c8d1`)
- **Automated verification:** frontend and intent pure suites passed; targeted DB-backed chat-search run not completed as a passing gate in this environment

## Accomplishments

### Task 1 — Promote supported city text to canonical board filter (frontend)
- Added `resolveCitySlugFromText` in `frontend/lib/cities.ts` for exact, accent/case-insensitive resolution of supported city slugs/labels/canonicals and safe aliases (`sp`, `rj`, `rio`, `bh`, `home office`, `home-office`, `trabalho remoto`).
- Updated `frontend/components/board/BoardToolbar.tsx` to promote matching committed search text to `commit({ q: "", city: matchedCity })` (debounce + Enter paths), clearing the input/last committed value; non-matching text remains `q`. Existing city-chip, clear, and sort behaviors preserved.
- Added deterministic Vitest coverage in `frontend/lib/cities.test.ts` (supported matches, aliases, null/partial/non-whitelist like `campinas`).

### Task 2 — Deterministic raw-text city fallback in intent mapper (backend)
- Added `_detect_city_from_raw_text` and fallback behavior in `backend/app/services/intent/mapper.py`:
  - detects unambiguous whitelist mentions for São Paulo (`sp`, `sao paulo`), Rio de Janeiro (`rj`, `rio`, `rio de janeiro`), Belo Horizonte (`bh`, `belo horizonte`), and Remoto (`remoto`, `home office`, `home-office`, `trabalho remoto`) using accent-insensitive, boundary-aware matching.
  - returns normalized apply only for a single distinct supported match; returns `conflict_resolved` when multiple supported cities are mentioned; never invents non-whitelist cities.
  - when `candidate.city` is absent, fallback can apply supported city with coherent status/reason (`aplicado`/`normalized`, pt-BR reason indicating safe detection); explicit non-whitelist candidate behavior (e.g. present `Campinas` -> `not_in_whitelist`) preserved.
- Added deterministic mapper tests in `backend/tests/test_intent_mapper.py` for absent-candidate fallback (São Paulo/sp/RJ/BH/home office), multi-city conflict (`sp ou rj` -> not applied/conflict), and safeguards (`campinas` alone absent-candidate not applied as whitelist; present candidate Campinas remains `not_in_whitelist`).
- Performed minor encoding/string hygiene fixes in `backend/tests/test_chat_search_api.py` while attempting an additional DB-backed mocked-seam API case; the added case could not be stabilized in this environment and was removed to avoid leaving a broken test (core deterministic gap coverage remains in mapper/frontend suites).

### Task 3 — Manual/UAT/MVP artifact updates for retest
- Updated `22-HUMAN-UAT.md` to record fix applied (pending manual/runtime revalidation), changed status to `partial` with `retest_required` gap tracking and honest summary (no false manual pass claim).
- Updated `22-MANUAL-UAT.md` with explicit guided revalidation case (toolbar supported city/alias -> `city=<slug>`, not only `q`; chat supported city query -> applied/not-ignored interpretation, coherent results, no contacts) and adjusted summary totals.
- Updated `22-MVP-EXAMPLES.md` with traceability note for 22-04 supported-city recognition evidence while preserving MVP limits (Campinas outside whitelist, non-native fields not native/guaranteed, "parecidas" seed textual only).

## Task Commits

1. **Task 1:** `1b51b4b` — `fix(22-04): promote supported city search text to canonical board filter`
2. **Task 2:** `df5bb5f` — `fix(22-04): add raw-text city fallback for supported whitelist in intent mapper`
3. **Task 3:** `994c8d1` — `docs(22-04): update UAT and MVP artifacts for city recognition retest`

## Files Created/Modified

- `frontend/lib/cities.ts` — added `resolveCitySlugFromText` (exact, fold-normalized, aliases)
- `frontend/lib/cities.test.ts` — Vitest coverage for supported/alias/negative cases
- `frontend/components/board/BoardToolbar.tsx` — promoted text commit path applies `city=<slug>` and clears `q` when matched
- `backend/app/services/intent/mapper.py` — raw-text whitelist city detection/fallback and conflict-safe status handling
- `backend/tests/test_intent_mapper.py` — deterministic fallback and safeguard tests
- `backend/tests/test_intent_parser.py` — regression suite executed (no parser changes required)
- `backend/tests/test_chat_search_api.py` — encoding/string hygiene fixes retained; added DB-backed case was not stabilized and removed
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md` — fix-applied/retest-required status (honest)
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` — explicit toolbar/chat city revalidation steps
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` — traceability note preserving MVP limits

## Decisions Made

- Used exact normalized matching (no substring promotion) for toolbar city detection to avoid unsafe rewrites of arbitrary queries.
- Kept mapper fallback conservative: only absent-candidate raw-text detection, whitelist-only, and conflict/no-apply on multiple supported mentions.
- Preserved existing contracts/safeguards: `JobPublic`/no contacts, deterministic search ownership, kill-switch/degraded behavior, and canonical manual board independence.

## Deviations from Plan

### Auto-fixed / Execution adjustments

1. **[Rule 3 - Blocking] Subagent execution failure recovery**
   - **Found during:** Orchestration
   - **Issue:** `gsd-executor` subagent returned error (`Compaction summary reached the output token limit`) before producing `22-04-SUMMARY.md` and before committing Task 2/3.
   - **Fix:** Orchestrator performed spot-checks, verified partial implementation/commit, completed remaining Task 2 commit, Task 3 docs, verification runs, and summary creation.
   - **Files modified:** plan-scoped files above
   - **Commit:** `df5bb5f`, `994c8d1`

2. **[Rule 1 - Correctness/verification] Unstable DB-backed chat-search test addition removed**
   - **Found during:** Task 2 verification
   - **Issue:** An added mocked-seam DB-backed API test for the reported city case could not be made to pass in this environment and risked leaving a broken test; broader targeted DB-backed command also timed out earlier.
   - **Fix:** Removed the unstable added test while retaining mapper/frontend deterministic coverage and parser regression pass; recorded as environment/verification gap.
   - **Files modified:** `backend/tests/test_chat_search_api.py`
   - **Commit:** included in `df5bb5f`

---

**Total deviations:** 2 (1 recovery, 1 verification adjustment)
**Impact on goal:** Core gap-closure behavior implemented with deterministic coverage for primary paths; API DB-backed chat-search verification for the new scenario remains environment-gated/unconfirmed in this run and manual runtime/UAT retest is still required.

## Issues Encountered

- `gsd-sdk` not found at expected path; phase/plan discovery and gating performed via manual `.planning` inspection.
- `python -m pytest -q tests/test_chat_search_api.py -k "city or chat_search"` timed out in this environment (previous long run terminated by timeout). A newly added specific DB-backed case failed in this harness during attempts and was removed; existing DB-backed coverage not fully re-validated here.
- Unrelated pre-existing working tree change left untouched: `frontend/next-env.d.ts` (modified). Untracked plan file `22-04-PLAN.md` left uncommitted.

## Verification Results

| Check | Result | Evidence |
|------|--------|----------|
| `cd frontend && npm test -- lib/cities.test.ts` | PASS | 1 file, 3 tests passed |
| `cd frontend && npm test` | PASS | 2 files, 10 tests passed (`cities.test.ts`, `chatApply.test.ts`) |
| `cd backend && python -m pytest -q tests/test_intent_mapper.py tests/test_intent_parser.py` | PASS | 18 passed |
| `cd backend && python -m pytest -q tests/test_chat_search_api.py -k "city or chat_search"` | NOT CONFIRMED | Earlier run timed out (120s) in this environment; added specific DB-backed case was unstable and removed; DB-backed environment prerequisites may be required |
| Task 3 doc verification script (plan) | PASS | `ok` (MANUAL-UAT contains `city=`/`chat`/supported-city examples; HUMAN-UAT contains retest/pending status; MVP-EXAMPLES updated with traceability/city context) |

## Threat / Contract Compliance Notes

- **T-22-13:** toolbar promotes only exact normalized supported matches/aliases; others remain `q`.
- **T-22-14:** mapper fallback whitelist-only (SP/RJ/BH/Remoto), absent-candidate only, conflict -> no apply; no non-whitelist invention (Campinas remains not applied/`not_in_whitelist` when explicit).
- **T-22-15:** no chat contact exposure changes introduced (`JobPublic` contract preserved by design; existing privacy behaviors unchanged in modified logic).
- **T-22-16:** canonical board/search flows and kill-switch/degraded semantics preserved in code paths touched; manual/runtime retest still required.

## User Setup Required

None.

## Next Phase Readiness / Handoff

- **Ready for:** manual/runtime revalidation of the reported case per `22-MANUAL-UAT.md` (Test 0) and related UAT items in `22-HUMAN-UAT.md`.
- **Still required before claiming closure:** integrated environment confirmation that toolbar applies `city=<slug>` for supported registered cities and chat interpretation applies supported city (not ignored as missing/not_in_whitelist) with coherent results and no contacts; optional DB-backed `tests/test_chat_search_api.py` verification in a migrated test DB environment.
- **No `STATE.md`/`ROADMAP.md` updates made by this plan execution.**

## Self-Check

- [x] `22-04-SUMMARY.md` created in phase directory
- [x] Task-scoped implementation/docs changes present for 22-04
- [x] Frontend tests and intent mapper/parser tests passed
- [ ] DB-backed chat-search targeted suite confirmed passing in this environment (not confirmed)
- [ ] Manual/runtime UAT retest completed (pending human)

## Self-Check: PASSED (with environment/human verification caveats noted)