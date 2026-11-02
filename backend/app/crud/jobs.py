"""CRUD for jobs: public read queries (D-17) and extraction writes (D-03)."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus

PUBLISHED_TTL = timedelta(days=14)

__all__ = ["list_published", "get_published", "bulk_create_pending", "list_by_status", "get_job", "approve_job", "update_job", "delete_job", "delete_expired_jobs"]


def _escape_like(term: str) -> str:
    """Escape LIKE metacharacters so ``q`` is matched literally (T-04-03).

    The backslash itself must be escaped first, otherwise the escapes added
    for ``%``/``_`` would be doubled by a later replace.
    """
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _published_filters(*, q: str | None, city: str | None) -> list:
    """The ONE predicate list shared by the page query and the total count.

    ``status = 'published'`` is always present literally: the search trigram
    index is partial on it, and ``total`` must describe exactly the same rows
    as ``items`` (D-17, 04-RESEARCH Pattern 3).
    """
    filters: list = [Job.status == JobStatus.published, Job.expires_at > func.now()]

    if city:
        filters.append(Job.city == city)

    if q:
        term = q.strip()
        if term:
            # ``search_text`` is stored as ``immutable_unaccent(lower(...))``
            # by the trigger, so the pattern is normalized identically. The
            # value stays a bound parameter — it is never interpolated into
            # SQL text (T-04-03).
            normalized = func.immutable_unaccent(func.lower(_escape_like(term)))
            pattern = func.concat("%", normalized, "%")
            filters.append(Job.search_text.like(pattern, escape="\\"))

    return filters


async def list_published(
    session: AsyncSession,
    page: int = 1,
    limit: int = 20,
    *,
    q: str | None = None,
    city: str | None = None,
    sort: str = "recentes",
) -> tuple[list[Job], int]:
    """Return ``(items, total)`` for published, non-expired jobs.

    Filters (all optional and combined with AND): ``q`` matches the normalized
    ``search_text`` (title + company + activities + requirements, D-03/D-04)
    and ``city`` compares to the canonical DB value (D-05). ``sort`` is
    ``recentes`` (default, ``created_at DESC``) or ``antigas`` (``ASC``).

    Both queries apply the SAME predicate list (D-17). The order always ends
    with the ``id`` tie-break: rows inserted in one transaction share
    ``created_at``, so without it ``limit``/``page`` could repeat or drop a row
    (D-06a). ``q``/``city``/``sort`` are keyword-only so every Phase 1–3 call
    keeps working unchanged.
    """
    filters = _published_filters(q=q, city=city)
    oldest_first = sort == "antigas"
    direction = Job.created_at.asc() if oldest_first else Job.created_at.desc()
    tie_break = Job.id.asc() if oldest_first else Job.id.desc()

    items_stmt = (
        select(Job)
        .where(*filters)
        .order_by(direction, tie_break)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    count_stmt = select(func.count()).select_from(Job).where(*filters)

    items = list((await session.scalars(items_stmt)).all())
    total = int((await session.scalar(count_stmt)) or 0)
    return items, total


async def list_by_status(
    session: AsyncSession,
    status: str,
    page: int = 1,
    limit: int = 24,
    *,
    city: str | None = None,
    sort: str = "recentes",
) -> tuple[list[Job], int]:
    """List jobs by status (no expires_at filter — admin sees all pending regardless of age).

    Mirrors ``list_published`` but filters ``Job.status == status`` only.
    City filter uses canonical DB value (resolved via ``resolve_city`` like public).
    Sort ``recentes`` (default, ``created_at DESC``) or ``antigas`` (``ASC``).
    Tie-break by ``id``.
    """
    filters = [Job.status == status]
    if city:
        filters.append(Job.city == city)
    oldest_first = sort == "antigas"
    direction = Job.created_at.asc() if oldest_first else Job.created_at.desc()
    tie_break = Job.id.asc() if oldest_first else Job.id.desc()

    items_stmt = (
        select(Job)
        .where(*filters)
        .order_by(direction, tie_break)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    count_stmt = select(func.count()).select_from(Job).where(*filters)

    items = list((await session.scalars(items_stmt)).all())
    total = int((await session.scalar(count_stmt)) or 0)
    return items, total


async def get_job(session: AsyncSession, job_id: uuid.UUID) -> Job | None:
    """Return a job by id, or ``None`` (no status filter — admin can edit any)."""
    stmt = select(Job).where(Job.id == job_id)
    return await session.scalar(stmt)


async def approve_job(session: AsyncSession, job: Job) -> Job:
    """Publish a job and restart its 14-day TTL (caller owns transaction/commit).

    A job can sit in the review queue for longer than 14 days; without this
    refresh it would be published with ``expires_at`` already in the past —
    ``GET /public/jobs`` filters on ``expires_at > now()``, so it would be
    invisible forever even though the admin saw "aprovada e publicada".
    """
    job.status = JobStatus.published
    job.expires_at = datetime.now(timezone.utc) + PUBLISHED_TTL
    await session.flush()
    return job


async def update_job(session: AsyncSession, job: Job, payload) -> Job:
    """Apply payload fields to existing job via ``JobUpdate`` model.

    Only fields present in the payload (``exclude_unset``) are updated.
    DB ``CHECK at_least_one_contact`` will raise ``IntegrityError`` if both
    contacts are cleared; the caller (router) should catch it.
    """
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(job, k, v)
    await session.flush()
    return job


async def delete_job(session: AsyncSession, job: Job) -> None:
    """Delete job from session (caller owns transaction/commit)."""
    await session.delete(job)


async def delete_expired_jobs(session: AsyncSession) -> int:
    """Hard delete every job past ``expires_at`` and return the row count (D-04).

    The sweep is deliberately status-agnostic: a row that sat in ``pending`` /
    ``needs_review`` for 14 days must not escape the clock just because nobody
    reviewed it (LIFE-03, D-03). ``invalid`` rows expire on the same rule.

    The comparison uses the DATABASE clock (``func.now()``) rather than the
    application clock, so the sweep is consistent with ``list_published``
    (``expires_at > now()``) — a job is never invisible to the board yet still
    alive in the table.

    Idempotent by construction: deleting nothing is a successful no-op, so the
    scheduler and the ``CRON_SECRET`` catch-up endpoint can both run at any
    time (T-06-02). Only ``flush()`` is called — the CALLER owns the
    transaction/commit.
    """
    stmt = delete(Job).where(Job.expires_at < func.now())
    result = await session.execute(stmt)
    await session.flush()
    return int(result.rowcount or 0)


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
