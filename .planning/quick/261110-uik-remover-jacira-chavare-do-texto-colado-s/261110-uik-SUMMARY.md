---
phase: 261110-uik
plan: 01
subsystem: extraction
tags: [fastapi, nextjs, admin-paste, groq-extraction, term-removal]

# Dependency graph
requires:
  - phase: 261110-u28
    provides: the original blocking rule (is_blocked_text / BLOCKED_TERM_ERROR) that this task replaces
provides:
  - strip_blocked_terms(text) backend rule + TERM_REMOVED_ALERT / REMOVED_TERM constants
  - stripBlockedTerms(text) frontend mirror + TERM_REMOVED_NOTICE
  - POST /api/v1/admin/extract extracts from cleaned text and reports the removal in alerts
  - paste handler that inserts the cleaned text at the caret and shows a role=status notice
affects: [admin-paste, extraction, frontend-blocklist]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single regex compiled from a constant (accent char classes + \\s+ between words), never from user input"
    - "Server is the authority; client strip is convenience only"

key-files:
  created: []
  modified:
    - backend/app/services/extraction/blocklist.py
    - backend/tests/test_blocklist.py
    - backend/app/api/v1/extract.py
    - backend/tests/test_extract_api.py
    - frontend/lib/blocklist.ts
    - frontend/app/admin/paste/ExtractForm.tsx

key-decisions:
  - "The term is REMOVED, never blocked: each occurrence becomes one space and the surrounding text is preserved byte for byte (no global normalization)"
  - "413 (byte size of the original text) keeps precedence over removal; term-only text yields 422 'apenas o termo removido' without calling Groq"
  - "Removal is announced, not silent: TERM_REMOVED_ALERT in the summary alerts and TERM_REMOVED_NOTICE in a role=status block"
  - "Frontend paste handler writes the cleaned text at the caret and notifies; it never discards the paste"

patterns-established:
  - "One rule, two mirrors: backend/app/services/extraction/blocklist.py and frontend/lib/blocklist.ts share REMOVED_TERM and identical semantics"

requirements-completed: []

# Metrics
duration: 12min
completed: 2026-11-10
---

# Quick Task 261110-uik: remover "JACIRA CHAVARE" do texto colado Summary

**The pasted term is stripped from every occurrence (any case/accent/spacing) instead of being refused, so extraction proceeds on the cleaned text and the admin is informed via a summary alert and an inline notice**

## Performance

- **Duration:** 12 min
- **Started:** 2026-11-10T22:03:45Z
- **Completed:** 2026-11-10T22:15:58Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- `strip_blocked_terms` (backend) and `stripBlockedTerms` (frontend) replace the blocklist check: every occurrence is replaced by a single space, surrounding text untouched.
- `POST /api/v1/admin/extract` now calls `extract_jobs` with the cleaned text, returns 200 and appends `TERM_REMOVED_ALERT` to `alerts`; text that is only the term returns 422 with "O texto continha apenas o termo removido — cole o conteúdo da vaga." and never reaches Groq.
- The 413 byte-size gate still measures the original `payload.text`, so size precedence is preserved (renamed test `test_extract_413_wins_over_term_removal`).
- The admin paste form inserts the cleaned text at the caret (respecting selection), shows an informational `role="status"` notice, and no longer disables the button or marks the textarea `aria-invalid` because of the term.
- No blocking symbols remain: `is_blocked_text`, `isBlockedText`, `BLOCKED_TERM`, `BLOCKED_TERM_ERROR`, `blockedNotice`, `blocked` state and `aria-invalid` are gone from the codebase.

## Task Commits

Each task was committed atomically:

1. **task 1: strip_blocked_terms no backend + unit tests de remoção** - `04a468e` (feat)
2. **task 2: endpoint extrai do texto limpo + alerta TERM_REMOVED_ALERT + testes de API** - `a8f35cf` (feat)
3. **task 3: frontend — paste limpo no cursor, aviso informativo e submit sem gate** - `75c19ef` (feat)

## Files Created/Modified

- `backend/app/services/extraction/blocklist.py` — `REMOVED_TERM`, `TERM_REMOVED_ALERT`, `strip_blocked_terms`; regex built from the constant with accent variants + `\s+`.
- `backend/tests/test_blocklist.py` — removal tests: case/accent/whitespace variants, multiple occurrences, preserved surroundings, untouched text (`"JACIRA"`/`"CHAVARE"` alone), term-only input, alert copy.
- `backend/app/api/v1/extract.py` — strip between the 413 gate and `extract_jobs`, 422 for empty-after-strip text, `TERM_REMOVED_ALERT` appended to `alerts`.
- `backend/tests/test_extract_api.py` — new 200 strip test (asserts Groq receives `strip_blocked_terms(pasted)`, no echo of pasted text), new 422 term-only test, renamed 413 precedence test.
- `frontend/lib/blocklist.ts` — `REMOVED_TERM`, `TERM_REMOVED_NOTICE`, `stripBlockedTerms`; fresh `RegExp` per call, ES2017-safe.
- `frontend/app/admin/paste/ExtractForm.tsx` — `notice` state, caret-aware paste handler, cleaned-text submit, `isSubmitDisabled` without the term gate.

## Decisions Made

- Message for term-only text follows the plan's task 2 code block verbatim (no term name in the string); see deviation 1.
- `stripBlockedTerms` returns `""` for whitespace-only results so the submit guard and the disabled state stay consistent with the backend's 422 path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan-internal inconsistency in the term-only assertion**
- **Found during:** task 2 (API tests)
- **Issue:** Task 2 (a) prescribes the exact 422 message `"O texto continha apenas o termo removido — cole o conteúdo da vaga."`, which does not contain `"JACIRA CHAVARE"`, while task 2 (b) instructs `assert "JACIRA CHAVARE" in detail` — the two cannot both hold.
- **Fix:** Kept the plan's prescribed message verbatim (implementation code block wins; success criteria only require "apenas o termo removido") and asserted the actual copy instead: `"apenas o termo removido" in detail` and `"cole o conteúdo da vaga" in detail`.
- **Files modified:** backend/tests/test_extract_api.py
- **Verification:** `tests/test_extract_api.py` green (31 tests together with `test_blocklist.py`).
- **Committed in:** `a8f35cf` (task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test assertion adjusted to the message the plan itself mandates; runtime behavior, status codes and copy are exactly as specified. No scope creep.

## Verification

| Command | Result |
|---------|--------|
| `backend> .venv\Scripts\python.exe -m pytest -q tests/test_blocklist.py tests/test_extract_api.py` | 31 passed, 1 warning (57.43s) |
| `backend> .venv\Scripts\python.exe -m pytest -q` | 267 passed, 3 skipped, 1 warning (489.30s) |
| `frontend> npx tsc --noEmit` | clean (no output) |
| `frontend> npm run lint` | No ESLint warnings or errors |
| `frontend> npm run build` (with dev `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_TURNSTILE_SITE_KEY`) | Compiled successfully; 10 static pages generated |

Covered removal variations (unit tests): `JACIRA CHAVARE`, `jacira chavare`, `Jacira Chavare`, `JACIRA   CHAVARE`, `JACIRA\nCHAVARE`, `JACIRA\tCHAVARE`, `JACIRA CHAVÁRE`, `  jacira chavare  ` → all `""`; multiple occurrences in one blob; realistic blob with neighbouring lines preserved (`startswith`/`endswith`/email intact); partials `JACIRA` and `CHAVARE` untouched; accented/whitespace text returned byte-identical.

Replacement confirmation: this task supersedes quick task 261110-u28 (commit `fd281dd`, 422 rejection). No blocking behavior for the term remains in `blocklist.py`, `lib/blocklist.ts`, `extract.py` or `ExtractForm.tsx`.

## Issues Encountered

- Task 1's focused pytest could not run in isolation: `tests/conftest.py` imports `app.main`, which imports `extract.py` and therefore the renamed symbols. Logic was pre-verified with a direct module import, then the focused suite ran green after task 2's import change. The two commits were made back to back.

## User Setup Required

None - no external service configuration required.

## Threat Flags

None — no new network endpoints, auth paths or trust boundaries. T-261110-11..16 mitigations from the plan are implemented (server-side strip before Groq, constant-derived regex, non-echoing pt-BR copy, announced removal) and T-261110-16 remains an accepted cosmetic false positive.

## Self-Check: PASSED

- Files exist: `backend/app/services/extraction/blocklist.py`, `backend/tests/test_blocklist.py`, `backend/app/api/v1/extract.py`, `backend/tests/test_extract_api.py`, `frontend/lib/blocklist.ts`, `frontend/app/admin/paste/ExtractForm.tsx`.
- Commits exist: `04a468e`, `a8f35cf`, `75c19ef`.

---

*Quick task: 261110-uik-remover-jacira-chavare-do-texto-colado-s*
*Completed: 2026-11-10*
