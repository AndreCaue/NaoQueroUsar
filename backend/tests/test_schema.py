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
