"""CRUD for jobs: public read queries (D-17) and extraction writes (D-03)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus

__all__ = ["list_published", "get_published", "bulk_create_pending"]


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


async def bulk_create_pending(session: AsyncSession, rows: list[dict]) -> list[Job]:
    """Insert extracted job rows in a single transaction (D-03).

    Each ``rows[i]`` is a dict of Job kwargs carrying a ``status`` key
    (``JobStatus.pending`` or ``JobStatus.needs_review``) and a
    ``source_snippet`` (D-08, review aid for REVW-05). Only ``flush()`` is
    called — the CALLER owns the transaction/commit, so a failure later in
    the request rolls back every insert ("nada foi gravado", D-03).
    """
    jobs: list[Job] = []
    for row in rows:
        job = Job(
            title=row["title"],
            company=row.get("company"),
            activities=row.get("activities"),
            requirements=row.get("requirements"),
            salary=row.get("salary"),
            benefits=row.get("benefits"),
            city=row["city"],
            contact_email=row.get("contact_email"),
            contact_phone=row.get("contact_phone"),
            status=row["status"],
            source_snippet=row["source_snippet"],
        )
        session.add(job)
        jobs.append(job)
    await session.flush()
    return jobs
