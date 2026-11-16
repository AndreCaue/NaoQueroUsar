---
phase: 16-geracao-revisao-e-aprovacao-do-post-social
plan: 02
subsystem: backend-admin-social
tags: [fastapi, sqlalchemy, pydantic, social-posts, admin-api, pytest]
requires:
  - phase: 16-geracao-revisao-e-aprovacao-do-post-social
    provides: Social draft generation/policy/schemas/CRUD foundation from plan 16-01
  - phase: 14-fundacao-social-dados-e-configuracao
    provides: SocialPost model, status enum, and (job_id, provider) uniqueness
provides:
  - Admin endpoints to consultar/gerar/salvar rascunho social por vaga (facebook) com validação, política e bloqueio de mutação quando congelado
  - Approve site-first com envelope `{job,social}` e registro social best-effort (registered/skipped/warning)
  - Cobertura de integração/API para lifecycle de draft, agendamento BRT, imutabilidade e falhas sociais sem bloquear publicação da vaga
affects: [16-03-ui-review, admin-review-flow, social-publishing]
tech-stack:
  added: []
  patterns: [site-first approve with isolated best-effort side effect, explicit draft save/regenerate, frozen scheduled draft immutability, BRT wall-time validation to UTC]
key-files:
  created:
    - backend/tests/test_admin_social_posts.py
  modified:
    - backend/app/api/v1/admin.py
    - backend/tests/test_admin_jobs.py
key-decisions:
  - "GET /admin/jobs/{id}/social-post retorna 404 claro quando não há draft salvo; generate/save retornam SocialPostDraftResponse persistido com frozen/origin/warning conforme contexto."
  - "Aprovação mantém publicação da vaga como fronteira crítica (commit antes do social) e registra social em etapa isolada com outcomes skipped/no_draft, registered ou warning/social_registration_failed sem rollback do job."
  - "Mutação de draft (generate/save) rejeita status não-draft com 409 'Texto aprovado e bloqueado para envio.'; save sanitiza política/link via serviço antes de persistir."
patterns-established:
  - "Rotas sociais admin reutilizam require_admin/get_session e HTTPException pt-BR, propagando erro acionável de SITE_PUBLIC_URL no fluxo de geração/salvamento."
  - "Registro social no approve trata draft ausente como skipped, draft scheduled como registered idempotente e falhas como warning após rollback isolado."
requirements-completed: [POST-01, POST-02, POST-03, POST-04, POST-05, POST-06]
duration: short
completed: 2026-11-15
---

# Phase 16 Plan 02: Geração/Revisão/Aprovação do Post Social Summary

**Admin social draft APIs and site-first approve envelope that registers scheduled Facebook posts best-effort while preserving immutable, policy-safe draft handling.**

## Performance

- **Duration:** short
- **Started:** 2026-11-15T22:52:00Z
- **Completed:** 2026-11-15T22:58:31-03:00
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Implemented admin-protected draft endpoints `GET/POST generate/PUT` for `/admin/jobs/{job_id}/social-post` with persisted Job lookup, explicit save validation, BRT schedule conversion, policy sanitization, and frozen-draft rejection.
- Evolved `PATCH /admin/jobs/{job_id}/approve` to return `JobApproveResponse` (`job` + `social`), committing job publication first and registering social draft as scheduled in a separate best-effort step with `registered|skipped|warning` outcomes.
- Added integration/API test coverage for draft lifecycle and approve invariants (including actionable SITE_PUBLIC_URL error, frozen mutations, D-04 persisted-job regeneration, skipped/warning paths) and aligned existing approve assertions to the new envelope.

## Task Commits

Each task was committed atomically (git lock contention required splitting implementation/tests into separate commits):

1. **Task 1: Endpoints admin de draft social (GET/POST generate/PUT save) com política e imutabilidade** - `2c0802e` (feat)
2. **Task 2: Evoluir approve para site-first + registro social best-effort e criar testes de integração** - `fcfa903` (test)

**Plan metadata:** see final docs commit for this plan.

## Files Created/Modified
- `backend/app/api/v1/admin.py` - Adds social draft routes/helpers and site-first approve flow returning `JobApproveResponse` with best-effort social outcome handling.
- `backend/tests/test_admin_social_posts.py` - New integration/API tests covering POST-03/04/05/06 and D-04/D-08..D-12/D-17 behaviors.
- `backend/tests/test_admin_jobs.py` - Updates approve expectations to the new `{job, social}` response envelope (directly impacted by Task 2 contract change).

## Decisions Made
- Treated missing draft on GET as `404 Rascunho social não encontrado` for a clear, consistent contract; generate/save always persist and return draft state.
- Derived draft `publish_mode` from persisted `scheduled_at` (`schedule` when present, else `publish_now`) and, on approve, used stored `scheduled_at` for schedule intent or `now_utc()` for publish-now registration.
- Classified non-registrable post-approve social states defensively as warning while never failing the already-committed job publication.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Aligned existing approve tests to new API envelope**
- **Found during:** Task 2 (approve contract evolution)
- **Issue:** `PATCH /admin/jobs/{id}/approve` now returns `JobApproveResponse` (`job` + `social`), which would break existing approve assertions in `test_admin_jobs.py`.
- **Fix:** Updated affected approve assertions to read `body["job"]` (and accept `social`) while preserving job publication checks.
- **Files modified:** `backend/tests/test_admin_jobs.py`
- **Verification:** Code updated to match implemented contract; DB-backed suite execution blocked by environment (see below).
- **Committed in:** `fcfa903`

**2. [Execution environment] DB-backed integration tests could not run (unmigrated/missing relations in test DB)**
- **Found during:** Task 2 verification
- **Issue:** `cd backend && python -m pytest -q tests/test_admin_social_posts.py tests/test_social_post_generation.py tests/test_social_post_policy.py -x` errored during setup with `relation "jobs" does not exist` when running DB-backed tests.
- **Fix:** Verified non-DB unit targets successfully (`tests/test_social_post_generation.py tests/test_social_post_policy.py` → 10 passed). Integration tests were added as specified but require a migrated test database to execute.
- **Files modified:** None
- **Verification:** `cd backend && python -m pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py -x` (10 passed)
- **Committed in:** N/A (environment constraint)

---

**Total deviations:** 2 (1 blocking contract-alignment fix, 1 environment constraint)
**Impact on plan:** Scope unchanged; API/tests implemented per plan. Full DB-backed verification pending migrated test DB.

## Issues Encountered
- Parallel git/index contention caused commit ordering/lock errors; resolved by committing sequentially after clearing lock, resulting in implementation and test commits split across `2c0802e` and `fcfa903`.
- `frontend/next-env.d.ts` was pre-modified in worktree and intentionally left unstaged/uncommitted as unrelated to this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backend draft/approve contracts and site-first best-effort behavior are in place for Phase 16 Plan 03 admin review UI integration.
- Integration tests for admin social flows are authored but need a migrated DB environment to run end-to-end.

## Self-Check

### Created files exist
- FOUND: `.planning/phases/16-geracao-revisao-e-aprovacao-do-post-social/16-02-SUMMARY.md`
- FOUND: `backend/tests/test_admin_social_posts.py`

### Commits exist
- FOUND: `2c0802e`
- FOUND: `fcfa903`

### Task-level verification
- PASSED (unit subset): `cd backend && python -m pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py -x` (10 passed)
- BLOCKED (environment): full plan verify including `tests/test_admin_social_posts.py` requires migrated test DB (`relation "jobs" does not exist`)

## Self-Check: PASSED

---
*Phase: 16-geracao-revisao-e-aprovacao-do-post-social*
*Completed: 2026-11-15*
