import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_published, list_published
from app.db.session import get_session
from app.schemas.job import JobListResponse, JobPublic

# Mounted by router.py without an extra prefix, so these resolve to
# /api/v1/public/jobs and /api/v1/public/jobs/{id}. NO auth dependency:
# the public read surface is anonymous by design (D-16).
router = APIRouter(prefix="/public", tags=["public"])


@router.get("/jobs", response_model=JobListResponse)
async def list_public_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> JobListResponse:
    """List published, non-expired jobs (contact-free), newest first (D-14/D-17)."""
    # Phase boundary (D-16): search/city/sort are Phase 4 — do NOT add them here.
    items, total = await list_published(session, page=page, limit=limit)
    return JobListResponse(
        items=[JobPublic.model_validate(job) for job in items],
        page=page,
        limit=limit,
        total=total,
    )


@router.get("/jobs/{job_id}", response_model=JobPublic)
async def get_public_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> JobPublic:
    """Return public detail for a published, non-expired job; 404 otherwise (D-17)."""
    # Phase boundary (D-18): no reveal/contact endpoint here — that is Phase 3.
    job = await get_published(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return JobPublic.model_validate(job)
