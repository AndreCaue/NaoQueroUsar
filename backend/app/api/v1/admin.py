from fastapi import APIRouter, Depends, HTTPException, Query
import uuid
from typing import Literal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.jobs import (
    approve_job,
    delete_expired_jobs,
    delete_job,
    get_job,
    list_by_status,
    update_job,
)
from app.deps import get_session, require_admin, require_cron_secret
from app.models.job import JobStatus
from app.schemas.job import JobAdmin, JobAdminListResponse, JobUpdate
from app.services.cities import resolve_city

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me")
async def me(claims: dict = Depends(require_admin)) -> dict:
    """Return the decoded admin claims behind a valid Bearer token (ADMN-03)."""
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
    city: str | None = Query(None, max_length=40),
    page: int = Query(1, ge=1, le=10_000),
    limit: int = Query(24, ge=1, le=100),
    sort: Literal["recentes", "antigas"] = Query("recentes"),
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdminListResponse:
    """List admin jobs filtered by status, city, pagination and sort.

    ``status`` default ``pending``; allowed ``pending`` / ``needs_review``.
    Unknown status or city → 422 (an admin filter must never fail open and
    silently return every city). Sort ``recentes`` (default) or ``antigas``
    with id tie-break. Returns ``JobAdminListResponse`` with contact +
    source_snippet.
    """
    if status not in ("pending", "needs_review"):
        raise HTTPException(status_code=422, detail="Status inválido")
    resolved_city = None
    if city:
        resolved_city = resolve_city(city)
        if resolved_city is None:
            raise HTTPException(status_code=422, detail="Cidade inválida")
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
    """Approve a reviewable job: status → ``published``, expiry refreshed.

    Only ``pending`` / ``needs_review`` rows can be approved (409 otherwise).
    Approving refreshes ``expires_at`` to now + 14 days so a job that waited
    in the queue is not published already-expired (and therefore invisible to
    the public board).
    """
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    if job.status not in (JobStatus.pending, JobStatus.needs_review):
        raise HTTPException(
            status_code=409, detail="Vaga não está na fila de revisão"
        )
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
    """Edit a job (partial update — only provided fields are applied).

    ``JobUpdate`` normalizes/validates title, city, email and phone before the
    DB. ``IntegrityError`` is the last-resort guard: only the contact CHECK
    maps to the contact message; anything else (NOT NULL, blank title) maps to
    a generic "Dados inválidos" instead of blaming the contact.
    """
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    try:
        await update_job(session, job, payload)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "at_least_one_contact" in str(exc.orig):
            raise HTTPException(
                status_code=422,
                detail="Vaga precisa ter ao menos um contato (email ou telefone)",
            ) from exc
        raise HTTPException(
            status_code=422, detail="Dados inválidos para a vaga"
        ) from exc
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


# ---------------------------------------------------------------------------
# LIFE-04: POST /admin/expire — manual / catch-up expiry sweep (D-02)
# ---------------------------------------------------------------------------


@router.post("/expire")
async def expire_jobs(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_cron_secret),
) -> dict:
    """Hard delete every expired job and return how many rows went away.

    This is the same sweep the APScheduler clock runs at 03:00 UTC, exposed so
    a free-tier host that spun down (or an external cron service) can trigger
    the catch-up on demand (LIFE-04). It is authenticated by ``X-Cron-Secret``
    instead of the admin Bearer token: a cron caller has no admin session, and
    the two credentials must not be interchangeable (T-06-01).

    Idempotent: a second call with nothing expired answers ``deleted: 0``.

    Rate-limited per resolved IP (10/minute, IN-05) at the cron dependency
    (``require_cron_secret``) — slowapi cannot wrap this route's handler for
    the probe vector because FastAPI resolves dependencies first and the
    401/503 short-circuit would bypass the limit. Under the limit the
    503 (unconfigured) and 401 (wrong secret) semantics are unchanged; over
    the limit the caller gets the shared 429 (pt-BR, ``Retry-After``).
    """
    deleted = await delete_expired_jobs(session)
    await session.commit()
    return {"deleted": deleted, "status": "ok"}
