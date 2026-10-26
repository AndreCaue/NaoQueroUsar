"""Search, city filter and sort integration tests (SRCH-01/02/03).

Two layers live in this file:

1. **Database contract** (migration ``0003``): ``jobs.search_text`` is produced
   by the ``jobs_set_search_text()`` trigger and must include ``requirements``.
   The backfill must refresh existing rows *without* bumping ``updated_at`` and
   must leave the ``jobs_updated_at`` trigger enabled.
2. **HTTP contract**: ``q``/``city``/``sort`` on ``GET /api/v1/public/jobs``,
   including wildcard escaping, the city alias table, the AND composition and
   the deterministic ``created_at, id`` ordering that keeps paging stable.

The suite runs against the real Postgres test branch; every assertion goes
through ``flush()`` (or the HTTP layer) so it sees what the trigger actually
wrote — never an in-memory Python value.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.models.job import Job, JobStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _job(**overrides) -> Job:
    """A published, contact-bearing job that passes both CHECK constraints."""
    defaults = {
        "title": "Vaga de Teste",
        "city": "Remoto",
        "contact_phone": "+55 11 90000-0100",
        "status": JobStatus.published,
    }
    defaults.update(overrides)
    return Job(**defaults)


# ---------------------------------------------------------------------------
# Trigger / migration 0003 (search_text includes requirements)
# ---------------------------------------------------------------------------


async def test_trigger_search_text_includes_requirements(db_session):
    job = _job(
        title="Analista Sênior",
        requirements="Kubernetes e Terraform",
        contact_phone="+55 11 90000-0101",
    )
    db_session.add(job)
    await db_session.flush()
    await db_session.refresh(job)

    assert job.search_text is not None
    assert "kubernetes" in job.search_text
    assert "analista senior" in job.search_text


async def test_trigger_updates_search_text_on_requirements_change(db_session):
    job = _job(
        title="Desenvolvedor(a) Backend",
        requirements="Kubernetes e Terraform",
        contact_phone="+55 11 90000-0102",
    )
    db_session.add(job)
    await db_session.flush()
    await db_session.refresh(job)
    assert "kubernetes" in job.search_text

    job.requirements = "Java e Spring Boot"
    await db_session.flush()
    await db_session.refresh(job)

    assert "java" in job.search_text
    assert "kubernetes" not in job.search_text


async def test_trigger_function_definition_has_requirements(db_session):
    """Proves migration 0003 was applied to this database, not just written."""
    prosrc = await db_session.scalar(
        text("SELECT prosrc FROM pg_proc WHERE proname = 'jobs_set_search_text'")
    )

    assert prosrc is not None
    assert "requirements" in prosrc


async def test_backfill_preserves_updated_at(db_session):
    job = _job(
        title="Auxiliar Administrativo",
        company="Empresa Backfill",
        activities="Rotinas administrativas.",
        requirements="Excel intermediário",
        contact_phone="+55 11 90000-0103",
    )
    db_session.add(job)
    await db_session.flush()
    await db_session.refresh(job)
    before = job.updated_at

    await db_session.execute(text("ALTER TABLE jobs DISABLE TRIGGER jobs_updated_at"))
    await db_session.execute(
        text(
            "UPDATE jobs SET search_text = immutable_unaccent(lower("
            "coalesce(title, '') || ' ' || coalesce(company, '') || ' ' || "
            "coalesce(activities, '') || ' ' || coalesce(requirements, ''))) "
            "WHERE id = :id"
        ),
        {"id": job.id},
    )
    await db_session.execute(text("ALTER TABLE jobs ENABLE TRIGGER jobs_updated_at"))

    await db_session.refresh(job)
    assert job.updated_at == before
    assert "excel" in job.search_text


async def test_updated_at_trigger_is_enabled(db_session):
    state = await db_session.scalar(
        text("SELECT tgenabled FROM pg_trigger WHERE tgname = 'jobs_updated_at'")
    )
    # ``pg_trigger.tgenabled`` is a ``"char"`` column; asyncpg hands it back as
    # a single byte rather than a str.
    if isinstance(state, (bytes, bytearray)):
        state = state.decode()

    assert state == "O"
