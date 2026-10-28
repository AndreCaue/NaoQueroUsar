from fastapi import APIRouter, Depends, HTTPException, Query
import uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.jobs import delete_job, get_job, list_by_status, update_job, approve_job
from app.deps import require_admin, get_session
from app.models.job import JobStatus
from app.schemas.job import JobAdmin, JobAdminListResponse, JobUpdate
from app.api.v1.public import _CITY_ALIASES, _resolve_city

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me")
async def me(claims: dict = Depends(require_admin)) -> dict:
    """Return the decoded admin claims behind a valid Bearer token.

    Proof-of-guard for ADMN-03. The full admin review routes (list/approve/
    edit/delete) belong to Phase 5 — do NOT add them here.
    """
    return {
        "sub": claims["sub"],
        "role": claims["role"],
        "iat": claims.get("iat"),
        "exp": claims.get("exp"),
    }


# ---------------------------------------------------------------------------
# REVW-01: GET /admin/jobs — list by status, city filter, pagination
# ---------------------------------------------------------------------------


@router.get("/jobs", response_model=JobAdminListResponse)
async def list_jobs(
    status: str = Query("pending"),
    city: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    sort: str = Query("recentes", max_length=20),
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdminListResponse:
    """List admin jobs filtered by status, city, pagination and sort.

    ``status`` default ``pending``; allowed ``pending`` / ``needs_review``.
    Unknown status → 422. City resolved via alias map (slug/canonical/label →
    canonical DB value). Sort ``recentes`` (default) or ``antigas`` with id
    tie-break. Returns ``JobAdminListResponse`` with contact + source_snippet.
    """
    if status not in ("pending", "needs_review"):
        raise HTTPException(status_code=422, detail="Status inválido")
    resolved_city = _resolve_city(city)
    items, total = await list_by_status(
        session,
        JobStatus(status),
        page=page,
        limit=limit,
        city=resolved_city,
        sort=sort,
    )
    return JobAdminListResponse(
        items=[JobAdmin.model_validate(j) for j in items],
        page=page,
        limit=limit,
        total=total,
    )


# ---------------------------------------------------------------------------
# REVW-05: GET /admin/jobs/{job_id} — retrieve a job by ID
# ---------------------------------------------------------------------------


@router.get("/jobs/{job_id}", response_model=JobAdmin)
async def get_job_detail(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdmin:
    """Retrieve a job by ID (admin only, contact + source_snippet exposed)."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return JobAdmin.model_validate(job)


# ---------------------------------------------------------------------------
# REVW-02: PATCH /admin/jobs/{id}/approve — pending/needs_review → published
# ---------------------------------------------------------------------------


@router.patch("/jobs/{job_id}/approve", response_model=JobAdmin)
async def approve(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdmin:
    """Approve a job: status changes to ``published``."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    await approve_job(session, job)
    await session.commit()
    await session.refresh(job)
    return JobAdmin.model_validate(job)


# ---------------------------------------------------------------------------
# REVW-03: PUT /admin/jobs/{id} — edit all fields
# ---------------------------------------------------------------------------


@router.put("/jobs/{job_id}", response_model=JobAdmin)
async def update(
    job_id: uuid.UUID,
    payload: JobUpdate,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdmin:
    """Edit a job (partial update — only provided fields are applied)."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    # Resolve city if provided
    if payload.city is not None:
        resolved = _resolve_city(payload.city)
        if resolved is None:
            raise HTTPException(status_code=422, detail="Cidade invalida")
        payload.city = resolved
    try:
        await update_job(session, job, payload)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=422,
            detail="Vaga precisa ter ao menos um contato (email ou telefone)",
        )
    await session.refresh(job)
    return JobAdmin.model_validate(job)


# ---------------------------------------------------------------------------
# REVW-04: DELETE /admin/jobs/{id} — hard delete
# ---------------------------------------------------------------------------


@router.delete("/jobs/{job_id}", status_code=204)
async def delete(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> None:
    """Hard delete a job."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    await delete_job(session, job)
    await session.commit()
