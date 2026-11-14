"""Schema criteria tests (criterion 3): contact CHECK, enum, 14-day expiry."""

from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.models.job import Job, JobStatus


def test_job_status_has_four_values():
    assert {status.value for status in JobStatus} == {
        "pending",
        "published",
        "needs_review",
        "invalid",
    }


def test_job_status_rejects_out_of_set_value():
    with pytest.raises(ValueError):
        JobStatus("bogus")


async def test_db_rejects_invalid_enum_value(db_session):
    with pytest.raises(DBAPIError):
        async with db_session.begin_nested():
            await db_session.execute(
                text(
                    "INSERT INTO jobs (title, city, contact_phone, status) "
                    "VALUES ('X', 'Remoto', '+55 11 90000-0005', 'bogus')"
                )
            )


async def test_job_requires_at_least_one_contact(db_session):
    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(Job(title="Sem Contato", city="São Paulo"))
            await db_session.flush()


async def test_expires_at_defaults_to_14_days(db_session):
    job = Job(
        title="Default Expira — Teste",
        city="Remoto",
        contact_phone="+55 11 90000-0004",
    )
    db_session.add(job)
    await db_session.flush()
    await db_session.refresh(job)

    assert job.created_at is not None
    assert job.expires_at is not None
    delta = job.expires_at - job.created_at
    assert timedelta(days=13, hours=23) <= delta <= timedelta(days=14, hours=1)


async def test_expires_at_column_is_timestamptz_with_14_day_default(db_session):
    """LIFE-10: the DDL — not Python — owns the 14-day expiry.

    A migration edit that dropped the server default or changed the column
    to a naive timestamp would still pass the behavioural test above
    whenever a client supplies expires_at (nothing does today), so pin the
    live schema explicitly.
    """
    columns = (
        await db_session.execute(
            text(
                "SELECT column_name, data_type, column_default "
                "FROM information_schema.columns "
                "WHERE table_name = 'jobs' "
                "AND column_name IN ('created_at', 'expires_at') "
                "ORDER BY column_name"
            )
        )
    ).all()
    by_name = {row.column_name: row for row in columns}

    assert by_name["created_at"].data_type == "timestamp with time zone"
    assert by_name["expires_at"].data_type == "timestamp with time zone"

    expires_default = (by_name["expires_at"].column_default or "").lower()
    # Postgres normalizes the expression: (now() + '14 days'::interval)
    assert "now()" in expires_default
    assert "'14 days'::interval" in expires_default

    index_name = await db_session.scalar(
        text(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'jobs' AND indexname = 'ix_jobs_expires_at'"
        )
    )
    assert index_name == "ix_jobs_expires_at"
