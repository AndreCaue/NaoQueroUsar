---
phase: 22-qualidade-hardening-e-valida-o-operacional
plan: "03"
subsystem: testing
tags: [qa, mvp, intent, chat-search, pytest, manual-uat, hardening]
requires:
  - phase: 22-01
    provides: chat kill-switch/status contract, safe disabled/degraded behavior, structured no-PII logging and backend test baseline
  - phase: 22-02
    provides: frontend kill-switch/status gating and manual-search-safe chat UX behavior
provides:
  - Versioned QA-01 MVP examples matrix with expected/observed contracts, evidence refs, and explicit capability gaps
  - Guided manual/UAT runbook covering critical chat flow, degraded/disabled states, and manual board/reveal non-regression (no Playwright/RTL)
  - Deterministic MVP intent/chat-search test coverage extensions (LLM mocked) for mapping, equivalence, privacy, degradation context, and partial-support signaling
affects: [phase-22-verification, qa, chat-search, intent]
tech-stack:
  added: []
  patterns:
    - "MVP validation as matrix + deterministic mocked tests (seed textual only, whitelist-safe, no invented filters)"
    - "DB-backed chat-search contract tests remain environment-capable but explicitly evidenced when executed"
key-files:
  created:
    - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md
    - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md
    - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-03-SUMMARY.md
  modified:
    - backend/tests/test_intent_mapper.py
    - backend/tests/test_chat_search_api.py
key-decisions:
  - "Documented MVP behavior factually to current contracts: 'parecidas' is seed textual limitado in q only (no semantic/vector/link/ID), Campinas stays not_in_whitelist, and non-native fields are only understood/approximated/signaled."
  - "Recorded observed automated evidence from actual executions in this environment (intent pure suites and DB-backed chat/rate-limit suites passed) instead of leaving API evidence pending."
patterns-established:
  - "QA evidence pairs contrato esperado + resultado observado with traceable deterministic test names for each MVP example."
requirements-completed: [QA-01, QA-02, QA-03]
duration: ~45min
completed: 2026-11-18
---

# Phase 22 Plan 03: MVP Validation Matrix and Test Consolidation Summary

**Versioned MVP chat validation artifacts and deterministic intent/chat-search regressions covering the 5 target examples, explicit capability gaps, privacy-safe contracts, and manual UAT for disabled/degraded non-regression.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-11-18T08:20:00-03:00 (approx)
- **Completed:** 2026-11-18T08:42:00-03:00 (approx)
- **Tasks:** 3
- **Files modified:** 4 (+ this summary)

## Accomplishments
- Created `22-MVP-EXAMPLES.md` documenting all 5 MVP scenarios with entrada, interpretação/`applied_params`/`field_statuses`, resultados esperados, limitações/guidance, lacunas explícitas, **Contrato esperado + Resultado observado**, and traceable evidence refs.
- Created `22-MANUAL-UAT.md` as a guided manual runbook (no Playwright/RTL) covering enabled critical chat flow, degraded/no-results behavior, kill-switch disabled state (`CHAT_SEARCH_ENABLED`), and manual board/search/filter/pagination/detail/reveal non-regression with privacy checks.
- Extended deterministic intent/chat coverage: 5 MVP mapper cases in `backend/tests/test_intent_mapper.py` and 5 mocked MVP chat-search API cases in `backend/tests/test_chat_search_api.py`, validating whitelist/city handling, non-native unsupported/approximate fields, textual-seed-only "parecidas" limits, API equivalence to public jobs, and `JobPublic` privacy (no contacts).

## Task Commits

Each task was committed atomically (see note on Task 1/2 bundling):

1. **Task 1: Criar matriz QA-01 dos 5 exemplos MVP com contrato esperado, observado e lacunas explícitas** - `a3301eb` (docs)
2. **Task 2: Criar roteiro manual/UAT guiado viável cobrindo fluxo crítico, estados desativado/degradado e não-regressão** - `a3301eb` (docs, committed together with Task 1 due parallel git/index contention during execution)
3. **Task 3: Consolidar e estender testes determinísticos intent/chat para cenários MVP, contratos e lacunas** - `10ca96e` (test)

**Plan metadata:** committed in docs(22-03) summary commit (this plan).

## Files Created/Modified
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` - QA-01 matrix for the 5 MVP examples with expected/observed evidence and explicit gaps
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` - Guided manual/UAT runbook for QA-02/QA-03 viable validation
- `backend/tests/test_intent_mapper.py` - Deterministic MVP mapping cases (SP/Remoto whitelist, salary unsupported, textual approximations, Campinas `not_in_whitelist`, textual-seed-only "parecidas")
- `backend/tests/test_chat_search_api.py` - Mocked MVP chat-search API cases asserting interpretation preservation, equivalence to `GET /api/v1/public/jobs`, and no contact leakage
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-03-SUMMARY.md` - Execution summary and self-check

## Decisions Made
- Kept "parecidas com uma vaga" strictly as **seed textual limitado** in `q` with explicit denial of semantic/vector/link-ID support in evidence/tests/docs; no new capability claims added.
- Treated Campinas/remote+salary combo per deterministic current behavior (candidate non-whitelisted city not applied; alternative remoto not auto-promoted in tested candidate shape) and documented limitations per field.
- Updated MVP matrix observed results to reflect actual passing executions (including DB-backed chat/rate-limit suites available in this environment) for accurate QA evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected MVP "parecidas" API test assertion to allow explicit limitation denial text**
- **Found during:** Task 3 (chat-search MVP API test execution)
- **Issue:** Initial assertion forbade "semântica/vetorial" substrings globally, conflicting with the safe guidance that explicitly states the limitation (no semantic/vector support).
- **Fix:** Replaced over-broad string bans with checks for explicit seed-textual limitation guidance and absence of semantic/vector/link-ID capability keys/metadata in structured response fields.
- **Files modified:** `backend/tests/test_chat_search_api.py`
- **Verification:** `python -m pytest -q tests/test_chat_search_api.py tests/test_ratelimit.py` passed (33 passed)
- **Committed in:** `10ca96e` (part of Task 3 commit)

**2. [Rule 3 - Blocking] Bundled Task 1 and Task 2 doc commits due parallel git index contention**
- **Found during:** Task 1/Task 2 commit steps
- **Issue:** Parallel commit operations contended on `.git/index.lock`; the resulting commit included both planned doc artifacts.
- **Fix:** Preserved both task outputs in `a3301eb` and kept Task 3 as a separate atomic commit; documented the bundling transparently.
- **Files modified:** `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md`, `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md`
- **Verification:** Commit contents verified via `git log/show` and files present with required content
- **Committed in:** `a3301eb`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking process issue)
**Impact on plan:** No scope creep; MVP coverage/evidence requirements satisfied. Task 1/2 artifacts are committed (bundled) and Task 3 is isolated.

## Issues Encountered
- `git merge-base` could not validate the provided worktree base hash in this environment (`17803cfb204c4284f38d3401e9b0e778ba706964` not found), but `HEAD` was already at `17803cf` (expected base context); execution proceeded without reset.
- Parallel commit attempts caused temporary `.git/index.lock` contention; resolved by retrying after lock cleared (resulted in Task 1/2 bundle noted above).

## User Setup Required
None - no external service configuration required.

## Verification

Executed (backend):
- `cd backend && python -m pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py` → **30 passed**
- `cd backend && python -m pytest -q tests/test_chat_search_api.py tests/test_ratelimit.py` → **33 passed** (DB-backed, LLM mocked)

Automated verification highlights:
- Mapper contains MVP cases including `Campinas`, `not_in_whitelist`, and `unsupported_structured_filter`.
- Chat-search API MVP cases mock `extract_and_map_intent`, assert equivalence to public jobs, and enforce `_assert_no_contacts`.
- Manual/UAT artifact documents `CHAT_SEARCH_ENABLED`, `busca manual`, `sem login`, `carregar mais`, contatos/revelação, and disabled-state checks.

## Self-Check: PASSED

- FOUND: `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md`
- FOUND: `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md`
- FOUND: `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-03-SUMMARY.md`
- FOUND: `backend/tests/test_intent_mapper.py` (MVP extensions)
- FOUND: `backend/tests/test_chat_search_api.py` (MVP extensions)
- FOUND commit: `a3301eb` (Task 1/2 docs)
- FOUND commit: `10ca96e` (Task 3 tests + evidence update)
- Verified commands: intent pure suites PASS (30), chat-search+ratelimit DB-backed PASS (33)

## Threat Flags

None - no new network endpoints, auth paths, file access patterns, or schema/trust-boundary changes introduced; changes are documentation and deterministic tests against existing contracts.

---
*Phase: 22-qualidade-hardening-e-valida-o-operacional*
*Completed: 2026-11-18*
