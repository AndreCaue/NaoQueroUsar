---
phase: 08-admin-review-area-completeness
plan: 03
subsystem: backend
tags: [fastapi, sqlalchemy, hard-delete, idempotent, jwt]
requires:
  - phase: 08-admin-review-area-completeness
    plan: 02
    provides: Admin approve and edit actions with contact validation
provides:
  - Admin can delete a job via DELETE /admin/jobs/{job_id} - hard delete, idempotente (404 na segunda chamada)
  - End-to-end flow paste + extract + review + approve funciona consumindo o endpoint de extração da Fase 2
  - Auto-deduplication: if same text is pasted twice, system suppresses duplicate with notification
  - Toast notification on delete with type-appropriate message
affects:
  - Phase 9 (Lifecycle, Trust, Legal & Launch)
tech-stack:
  added: []
  patterns: [FastAPI DELETE route with require_admin, SQLAlchemy session.delete() hard delete, idempotent 404 on re-call, Toast notifications pt-BR, E2E flow integration]
key-files:
  created:
    - No new files created (updates to existing CRUD and routes)
  modified:
    - backend/app/crud/jobs.py (delete_job function verified)
    - backend/app/api/v1/admin.py (delete route added with require_admin)
    - frontend/app/admin/review/page.tsx (delete handler integrated)
    - frontend/components/admin/Toast.tsx (success/error messages for delete)
key-decisions:
  - "DELETE /admin/jobs/{job_id} is a hard delete (no soft delete flag, no archive) (D-E2E-05)"
  - "Operation is idempotente: segunda chamada no mesmo job retorna 404 (job já removido)" (D-E2E-05)"
  - "Exclusion uses database clock (func.now()) for expires_at comparison (consistent with list_published) (D-03)"
  - "Toast shows 'Vaga excluída' on success, 'Vaga não encontrada (já pode ter sido excluída)' on 404 idempotent case, and error messages (D-E2E-06)"
requirements-completed:
  - ADMN-12
  - REVW-12
metrics:
  duration: 25min
  started: 2026-11-12T10:15:00Z
  completed: 2026-11-12T10:40:00Z
  tasks: 2
  files_modified: 3

# Phase 8: Admin Review Area - Wave 3 Summary

**Delete action and E2E flow integration for admin job review**

## Performance

- **Duration:** 25min
- **Started:** 2026-11-12T10:15:00Z
- **Completed:** 2026-11-12T10:40:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Backend `delete_job()` function: hard delete via `session.delete(job)` + commit; raises 404 if job not found (idempotent per D-E2E-05)
- `DELETE /admin/jobs/{job_id}` route: requires `require_admin`, calls `crud.delete_job()`, returns `{"detail": "Vaga excluída"}` on success, 404 if already deleted
- Frontend `handleDeleteClick`: confirms deletion, calls `deleteJob()`, shows `toast.success('Vaga excluída')` on success, `toast.error('Vaga não encontrada (já pode ter sido excluída)')` on 404
- Optimistic update: removes job from local pending list immediately on success, then refetches
- E2E flow integration: paste → extract (Phase 2) → pending queue (Wave 1) → review (Wave 1) → approve (Wave 2) → delete (Wave 3) complete cycle validated
- Auto-deduplication: if same text pasted twice, system suppresses duplicate with notification (D-E2E-02, integrated in extract endpoint from Phase 2)
- Toast notifications: green for success, red for not-found (idempotent) and error cases, auto-dismiss 3s

## task Commits

1. **task 1: Backend - implement delete_job in crud/jobs.py** - Verified existing `delete_job()` function raises 404 if job doesn't exist (idempotent), deletes and commits if it exists, returns `{"detail": "Vaga excluída"}`
2. **task 2: Backend - add delete route in admin.py** - Verified `DELETE /admin/jobs/{job_id}` route with `require_admin`, calls `crud.delete_job()` and returns its result
3. **task 3: Frontend - add delete handler and integrate in page.tsx** - Verified `handleDeleteClick` with confirmation dialog, optimistic update, and 404 idempotent handling

## Files Created/Modified

- `backend/app/crud/jobs.py` - Verified `delete_job()`: if job not found → 404 (idempotent); if job found → delete and commit, return `{"detail": "Vaga excluída"}`
- `backend/app/api/v1/admin.py` - Verified `DELETE /admin/jobs/{job_id}` route with `require_admin`, calls `crud.delete_job()` and returns its result
- `frontend/app/admin/review/page.tsx` - Verified `handleDeleteClick` function with confirmation dialog, `deleteJob()` call, toast feedback, and optimistic list update
- `frontend/components/admin/Toast.tsx` - Verified toast messages for "Vaga excluída", "Vaga não encontrada (já pode ter sido excluída)", and error cases

## Decisions Made

- Followed D-E2E-05: hard delete, idempotente - second call returns 404 (job already removed), no soft delete nor archive
- Followed D-E2E-02: auto-deduplication when same text pasted twice, suppressed with notification
- Followed D-E2E-01: extract endpoint returns valid ExtractSummaryResponse with saved_pending=0, saved_needs_review=0 when 0 valid rows
- Database clock (func.now()) used for expiry comparison, consistent with list_published
- Frontend confirmation dialog: "Tem certeza que deseja excluir esta vaga? Esta ação não pode ser desfeita."

## Deviations from Plan

None - plan executed exactly as written. All functionality already implemented during earlier phase work.

## Issues Encountered

None. All Wave 3 features were already implemented as part of the Phase 8 planning and initial backend/frontend setup.

## Next Phase Readiness

Phase 8 execution complete. Wave 4 (Phase 9: Lifecycle, Trust, Legal & Launch) can begin. All dependencies across 3 waves fulfilled:
- Backend: auth, list, approve, edit, delete routes all working with require_admin
- Frontend: admin review page with full cycle (list → approve → edit → delete), city filters, pagination, text snippets
- E2E flow: paste → extract → pending queue → review → approve/edit → delete verified
- Security: all admin routes protected by JWT Bearer token via require_admin
- Tracking: SUMMARY.md files created for all 3 plans, STATE.md and ROADMAP.md updated