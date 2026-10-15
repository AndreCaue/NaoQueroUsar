"""Published-only, non-expired read queries for the public surface (D-17)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus

__all__ = ["list_published", "get_published"]


async def list_published(
    session: AsyncSession,
    page: int,
    limit: int,
) -> tuple[list[Job], int]:
    """Return ``(items, total)`` for published, non-expired jobs.

    Newest first (``created_at DESC``), offset-paginated (D-14). Both the
    page query and the total count apply the SAME filter (D-17):
    ``status = 'published' AND expires_at > now()``.
    """
    filters = (
        Job.status == JobStatus.published,
        Job.expires_at > func.now(),
    )

    items_stmt = (
        select(Job)
        .where(*filters)
        .order_by(Job.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    count_stmt = select(func.count()).select_from(Job).where(*filters)

    items = list((await session.scalars(items_stmt)).all())
    total = (await session.scalar(count_stmt)) or 0
    return items, total


async def get_published(session: AsyncSession, job_id: uuid.UUID) -> Job | None:
    """Return a published, non-expired job by id, or ``None`` (D-17)."""
    stmt = select(Job).where(
        Job.id == job_id,
        Job.status == JobStatus.published,
        Job.expires_at > func.now(),
    )
    return await session.scalar(stmt)
