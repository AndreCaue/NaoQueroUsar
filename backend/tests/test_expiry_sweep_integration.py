"""Expiry sweep integration test against the real test database (IN-04).

Every other test fakes the database round-trip of the sweep (or never runs
one), which is exactly how the CR-01 cross-loop pool defect stayed invisible
to the suite. This test executes ``expire_jobs_job()`` — the same entry point
the scheduler and the cron endpoint use — against ``TEST_DATABASE_URL`` and
asserts both effects and pool survival.

It is skipped cleanly when no test database is configured (same rule as the
rest of the suite, enforced in ``conftest.py``).

The sweep commits by design, so the seeded rows are cleaned up in ``finally``
instead of being rolled back like the transactional fixture tests.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, func, select, text

from app.core import scheduler as scheduler_module
from app.db.session import async_session_factory, engine
from app.models.job import Job, JobStatus


async def _cleanup(marker: str) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(Job).where(Job.title.like(f"{marker}%")))
        await session.commit()


@pytest.mark.asyncio
async def test_sweep_executes_against_test_db_and_pool_survives():
    marker = f"sweep-itest-{uuid.uuid4().hex[:12]}"
    past = datetime.now(timezone.utc) - timedelta(days=1)
    future = datetime.now(timezone.utc) + timedelta(days=13)

    expired_title = f"{marker} expirada"
    live_title = f"{marker} viva"

    # Seed with the shared pool the same way the app does, then commit —
    # the sweep runs on its own session and must see these rows.
    async with async_session_factory() as session:
        session.add_all(
            [
                Job(
                    title=expired_title,
                    city="Remoto",
                    contact_phone="+55 11 90000-0000",
                    status=JobStatus.published,
                    expires_at=past,
                ),
                Job(
                    title=live_title,
                    city="Remoto",
                    contact_phone="+55 11 90000-0001",
                    status=JobStatus.published,
                    expires_at=future,
                ),
            ]
        )
        await session.commit()

    try:
        deleted = await scheduler_module.expire_jobs_job()

        assert deleted >= 1
        async with async_session_factory() as session:
            expired_left = await session.scalar(
                select(func.count()).select_from(Job).where(Job.title == expired_title)
            )
            live_left = await session.scalar(
                select(func.count()).select_from(Job).where(Job.title == live_title)
            )
        assert int(expired_left or 0) == 0
        assert int(live_left or 0) == 1

        # The shared pool is still usable afterwards — no cross-loop or
        # closed-connection fallout from the sweep (CR-01 regression guard).
        async with engine.connect() as conn:
            assert (await conn.execute(text("SELECT 1"))).scalar_one() == 1
    finally:
        await _cleanup(marker)
