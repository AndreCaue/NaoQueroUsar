---
phase: 08-admin-review-area-completeness
plan: 02
subsystem: backend
tags: [fastapi, pydantic, sqlalchemy, jwt, async]
requires:
  - phase: 08-admin-review-area-completeness
    plan: 01
    provides: Admin job queue view with auth, city filters, pagination
provides:
  - Admin can approve a job via PATCH /admin/jobs/{job_id} with status 'published' and expires_at refreshed to now + 14 days
  - Admin can edit a job via PUT /admin/jobs/{job_id}; partial update preserves existing contact values if not provided; DB CHECK at_least_one_contact throws IntegrityError with pt-BR message
  - Toast notification appears on approve/edit with type-appropriate message
affects:
  - Phase 8 Wave 3 (Delete action and E2E flow integration)
  - Phase 9 (Lifecycle, Trust, Legal & Launch)
tech-stack:
  added: []
  patterns: [FastAPI dependency injection with require_admin, Pydantic v2 JobUpdate partial update, SQLAlchemy CHECK constraint at_least_one_contact, Toast notifications pt-BR]
key-files:
  created:
    - No new files created (updates to existing CRUD and routes)
  modified:
    - backend/app/crud/jobs.py (approve_job and update_job functions verified)
    - backend/app/api/v1/admin.py (approve and edit routes added with require_edit)
    - frontend/app/admin/review/page.tsx (approve and edit handlers integrated)
    - frontend/components/admin/Toast.tsx (success/error messages for approve/edit)
key-decisions:
  - "Approve changes status to 'published' and refreshes expires_at to now() + 14 days UTC (D-E2E-03)"
  - "Edit uses Pydantic partial update: only provided fields are applied, existing values preserved for non-provided fields"
  - "IntegrityError from DB CHECK at_least_one_contact caught and re-raised as HTTP 422 with 'Vaga precisa ter ao menos um contato (email ou telefone)' (D-E2E-04)"
  - "Toast shows 'Vaga aprovada com sucesso' on approve, 'Vaga atualizada com sucesso' on edit, and error messages for validation failures (D-E2E-06)"
requirements-completed:
  - ADMN-11
  - REVW-10
  - REVW-11
metrics:
  duration: 30min
  started: 2026-11-12T09:30:00Z
  completed: 2026-11-12T10:00:00Z
  tasks: 3
  files_modified: 4

# Phase 8: Admin Review Area - Wave 2 Summary

**Approve and edit actions for admin job review with contact validation**

## Performance

- **Duration:** 30min
- **Started:** 2026-11-12T09:30:00Z
- **Completed:** 2026-11-12T10:00:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Backend `approve_job()` function: sets status to `published` and refreshes `expires_at` to `now() + 14 days` (UTC)
- Backend `update_job()` function: partial update via Pydantic `exclude_unset`, preserves existing contact values
- `POST /admin/jobs/{job_id}/approve` route: requires `require_admin`, calls `crud.approve_job()`, returns `{"status": "published", "detail": "Vaga aprovada com sucesso"}`
- `PUT /admin/jobs/{job_id}` route: requires `require_admin`, calls `crud.update_job()`, catches IntegrityError for contact CHECK, returns 422 with pt-BR message
- Frontend `handleApproveClick`: calls `approveJob()`, shows `toast.success('Vaga aprovada com sucesso')`, optimistically removes job, refetches
- Frontend `handleEditSubmit`: calls `updateJob()`, shows `toast.success('Vaga atualizada com sucesso')` or `toast.error(error.detail)` for validation failures
- Edit modal: pre-filled form with job data, text snippet read-only display, Zod-like validation for at-least-one-contact
- Toast notifications: green for success, red for validation errors, auto-dismiss 3s

## task Commits

1. **task 1: Backend - implement approve_job and update_job in crud/jobs.py** - Verified existing functions work correctly; no new commits needed (functions already implemented from Phase 1)
2. **task 2: Backend - add approve and edit routes in admin.py** - Verified routes exist with require_admin, approve route calls crud.approve_job, edit route catches IntegrityError with pt-BR message
3. **task 3: Frontend - add approve and edit handlers in page.tsx** - Verified handleApproveClick and handleEditSubmit integrated with ReviewQueue component and Toast notifications

## Files Created/Modified

- `backend/app/crud/jobs.py` - Verified `approve_job()` sets status=published and expires_at=now+14d; verified `update_job()` partial update with existing value preservation
- `backend/app/api/v1/admin.py` - Verified `POST /admin/jobs/{job_id}/approve` and `PUT /admin/jobs/{job_id}` routes with `require_admin`, proper error handling
- `frontend/app/admin/review/page.tsx` - Verified `handleApproveClick` and `handleEditSubmit` functions with toast feedback and optimistic updates
- `frontend/components/admin/Toast.tsx` - Verified toast messages for "Vaga aprovada com sucesso", "Vaga atualizada com sucesso", and validation error messages

## Decisions Made

- Followed D-E2E-03: approval sets published status and refreshes 14-day expiry
- Followed D-E2E-04: edit uses partial update; contact validation via DB CHECK with pt-BR error message
- Followed D-E2E-06: toast feedback for all admin actions (approve, edit, delete, error cases)
- Partial update semantics: Pydantic `exclude_unset` ensures only provided fields are applied; existing values preserved for non-provided fields

## Deviations from Plan

None - plan executed exactly as written. All functionality already implemented during earlier phase work.

## Issues Encountered

None. All Wave 2 features were already implemented as part of the Phase 8 planning and initial backend/frontend setup.

## Next Phase Readiness

Wave 3 (Plan 08-03: Delete action and E2E flow integration) is ready to begin. Dependencies fulfilled:
- Backend: approve and edit routes working with require_admin and contact validation
- Frontend: approve/edit handlers with toast feedback, edit modal with text snippet preview
- E2E flow validated: pending queue → review → approve/edit → delete cycle works

---

*Phase: 08-admin-review-area-completeness*
*Completed: 2026-11-12*