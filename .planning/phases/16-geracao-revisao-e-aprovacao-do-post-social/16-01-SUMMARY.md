---
phase: 16-geracao-revisao-e-aprovacao-do-post-social
plan: 01
subsystem: backend-social
tags: [fastapi, groq, social-posts, pydantic, sqlalchemy]
requires:
  - phase: 14-fundacao-social-dados-e-configuracao
    provides: SocialPost model/constraints and social service foundations
provides:
  - Social post draft generation service (Groq + deterministic template fallback)
  - Policy/link/sanitization and BRT schedule helpers for social drafts
  - Social post CRUD/schemas/config foundation for admin draft/approval flows
affects: [16-02-api-admin, 16-03-ui-review, social-publishing]
tech-stack:
  added: []
  patterns: [policy-safe draft generation, deterministic fallback, flush-only CRUD, timezone-aware BRT conversion]
key-files:
  created:
    - backend/app/services/social/post_generation.py
    - backend/app/crud/social_posts.py
    - backend/app/schemas/social_posts.py
    - backend/tests/test_social_post_generation.py
    - backend/tests/test_social_post_policy.py
  modified:
    - backend/app/core/config.py
    - backend/.env.example
    - backend/app/schemas/job.py
    - backend/app/services/social/__init__.py
    - backend/tests/conftest.py
key-decisions:
  - "Centralized social post policy in service layer: strip company/contact patterns and never include contacts by default (flag off)."
  - "Build public draft links only from validated SITE_PUBLIC_URL as {base}/?vaga={job_id}; missing/invalid config raises actionable pt-BR error."
  - "LLM failures fall back to deterministic template draft with warning so review flow is never blocked; BRT wall time converts to timezone-aware UTC."
patterns-established:
  - "Generation service returns origin/warning metadata and enforces sanitization on all output paths."
  - "social_posts CRUD uses flush-only upsert/transition helpers with draft-freeze guard for immutable approved text."
requirements-completed: [POST-01, POST-02, POST-04, POST-06]
duration: short
completed: 2026-11-15
---

# Phase 16 Plan 01: Geração/Revisão/Aprovação do Post Social Summary

**Backend foundation for policy-safe social post drafts with Groq-or-template generation, actionable public link validation, BRT scheduling helpers, and draft/schedule persistence contracts.**

## Performance

- **Duration:** short
- **Started:** 2026-11-15T22:46:00Z
- **Completed:** 2026-11-15T22:52:00Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Added `SOCIAL_POST_INCLUDE_CONTACT` default-off config and documented it in `.env.example` to enforce no company/contact in posts by default.
- Implemented `post_generation` service with `build_public_job_link`, policy sanitization, deterministic template fallback, Groq-based draft generation, and BRT (`America/Sao_Paulo`) to UTC helpers.
- Added social draft/schedule schemas, `JobApproveResponse` envelope, and `social_posts` CRUD helpers for draft upsert and scheduled transition with immutability guard.
- Added focused unit tests for generation fallback/LLM path safety and link/policy enforcement; made Phase 16 unit tests runnable without DB via `conftest` adjustment.

## Task Commits

Each task was committed atomically:

1. **Task 1: Config/política e schemas/CRUD de social_post (draft foundation)** - `5c8379f` (feat)
2. **Task 2: Serviço de geração (LLM+fallback), política/link/sanitização e agendamento BRT + testes unitários** - `dd4c093` (feat)

**Plan metadata:** see final docs commit for this plan.

## Files Created/Modified
- `backend/app/core/config.py` - Adds `SOCIAL_POST_INCLUDE_CONTACT` default-false policy flag.
- `backend/.env.example` - Documents social post content policy flag (no company/contact by default).
- `backend/app/schemas/social_posts.py` - Draft request/response and social approval outcome schemas.
- `backend/app/schemas/job.py` - Adds `JobApproveResponse` (`job` + `social`) envelope.
- `backend/app/crud/social_posts.py` - Flush-only helpers to fetch, upsert draft, and mark scheduled with freeze guard.
- `backend/app/services/social/post_generation.py` - Link builder, policy sanitization, template fallback, LLM generation, and BRT scheduling utilities.
- `backend/app/services/social/__init__.py` - Exports post generation utilities.
- `backend/tests/conftest.py` - Allows Phase 16 pure unit test modules to run without configured test DB.
- `backend/tests/test_social_post_generation.py` - Covers LLM success/fallback behavior and policy-safe output (POST-01/POST-02).
- `backend/tests/test_social_post_policy.py` - Covers link construction/actionable error and contact/company stripping (POST-06).

## Decisions Made
- Enforced policy in a central sanitizer applied to both LLM and template outputs, scrubbing company/contact values and common contact patterns when flag is off.
- Kept `SITE_PUBLIC_URL` boot validation behavior unchanged and raised a domain-specific actionable error at draft link generation time when missing/invalid.
- Used `zoneinfo.ZoneInfo("America/Sao_Paulo")` for wall-time conversion and returned timezone-aware UTC datetimes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Allowed Phase 16 unit tests to run without DB-configured environment**
- **Found during:** Task 2 (test execution)
- **Issue:** Global pytest collection skip in `conftest.py` would skip all tests when no test DB configured, blocking required unit verification.
- **Fix:** Narrowed skip behavior to exempt `test_social_post_generation.py` and `test_social_post_policy.py` so pure unit tests execute.
- **Files modified:** `backend/tests/conftest.py`
- **Verification:** `cd backend && python -m pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py -x` passes.
- **Committed in:** `5c8379f` (Task 1 commit)

**2. [Rule 1 - Bug] Prevented duplicate/malformed CTA link injection in sanitizer**
- **Found during:** Task 2 (test execution)
- **Issue:** Initial sanitizer could append CTA twice in edge cases, producing duplicated/malformed link text.
- **Fix:** Ensured single CTA/link append path and preserved link after defensive scrub.
- **Files modified:** `backend/app/services/social/post_generation.py`
- **Verification:** Targeted unit tests pass, including policy-safe LLM output case.
- **Committed in:** `dd4c093` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for correctness and verifiability; no scope creep.

## Issues Encountered
- Parallel git index contention caused commit retries; resolved with sequential commits and confirmed final task commits are correct (`5c8379f`, `dd4c093`).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Draft generation, policy/link, BRT helpers, schemas, and CRUD primitives are ready for Phase 16 Plan 02 API/admin wiring.
- No blockers identified for endpoint integration and approval registration flow.

## Self-Check: PASSED

- FOUND: `.planning/phases/16-geracao-revisao-e-aprovacao-do-post-social/16-01-SUMMARY.md`
- FOUND commit: `5c8379f`
- FOUND commit: `dd4c093`
- Verified: `cd backend && python -m pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py -x` (10 passed)

---
*Phase: 16-geracao-revisao-e-aprovacao-do-post-social*
*Completed: 2026-11-15*
