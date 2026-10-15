"""Pytest harness for the Phase 1 criteria suite (D-22).

Design:
- The suite runs against a dedicated test database. The URL is resolved from
  ``TEST_DATABASE_URL`` (env, then ``backend/.env``), falling back to
  ``DATABASE_URL``. If neither is configured the whole suite is skipped with a
  clear message so config-only runs do not hard-fail.
- Auth settings are forced to deterministic test values *before* any
  ``app`` module is imported (``app.core.security`` and ``app.db.session`` call
  ``get_settings()`` at import time).
- Each test runs inside an outer transaction that is rolled back at teardown,
  and the ``jobs`` table is cleared at the start of the transaction — tests are
  isolated from each other and from any pre-existing rows without ever
  committing.
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import pytest
from dotenv import dotenv_values

# ---------------------------------------------------------------------------
# Resolve the test DB URL BEFORE importing any app module.
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_FILE_ENV = dotenv_values(_BACKEND_DIR / ".env")

TEST_DATABASE_URL = (
    os.environ.get("TEST_DATABASE_URL")
    or _FILE_ENV.get("TEST_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or _FILE_ENV.get("DATABASE_URL")
)
HAS_DB = bool(TEST_DATABASE_URL)

# Force deterministic, isolated settings for the test run. Environment
# variables take precedence over any ``.env`` values in pydantic-settings.
# A placeholder URL is only used so module-level ``get_settings()`` calls
# succeed during collection when no DB is configured — every test is skipped
# in that case, so the engine is never connected.
TEST_ADMIN_PASSWORD = "test-password"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL or (
    "postgresql+asyncpg://postgres@127.0.0.1:5432/nqu_placeholder"
)
os.environ["ADMIN_PASSWORD_HASH"] = bcrypt.hashpw(
    TEST_ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
).decode("utf-8")
os.environ["JWT_SECRET"] = "test-secret-key-for-pytest-only-0123456789abcdef"
if TEST_DATABASE_URL:
    os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL

# ---------------------------------------------------------------------------
# App imports (safe now that the settings env is fixed).
# ---------------------------------------------------------------------------
from app.core.config import get_settings  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.job import Job, JobStatus  # noqa: E402

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

# Ensure the settings cache reflects the forced env values, not anything that
# may have been imported earlier.
get_settings.cache_clear()


def pytest_collection_modifyitems(config, items):
    """Skip the whole suite (cleanly, exit 0) when no test DB is configured."""
    if not HAS_DB:
        for item in items:
            item.add_marker(
                pytest.mark.skip(reason="TEST_DATABASE_URL/DATABASE_URL not set")
            )


@pytest.fixture
def admin_password() -> str:
    return TEST_ADMIN_PASSWORD


@pytest.fixture
async def engine():
    """A per-test async engine against the test database."""
    eng = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"statement_cache_size": 0},
        pool_pre_ping=True,
    )
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest.fixture
async def db_session(engine):
    """An isolated ``AsyncSession`` wrapped in a rolled-back transaction.

    The ``jobs`` table is cleared at the start of the transaction so tests see
    a deterministic empty table; the teardown rollback discards everything.
    """
    conn = await engine.connect()
    trans = await conn.begin()
    session = AsyncSession(bind=conn, expire_on_commit=False)
    try:
        await session.execute(text("DELETE FROM jobs"))
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await conn.close()


@pytest.fixture
async def client(db_session):
    """An ``httpx.AsyncClient`` over the ASGI app, hitting the test DB."""
    app = create_app()

    async def _override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def seed_published_job(db_session) -> Job:
    job = Job(
        title="Vaga Publicada — Teste",
        company="Empresa A",
        activities="Atividades de teste.",
        city="Remoto",
        salary="A combinar",
        contact_phone="+55 11 90000-0001",
        status=JobStatus.published,
    )
    db_session.add(job)
    await db_session.flush()
    return job


@pytest.fixture
async def seed_pending_job(db_session) -> Job:
    job = Job(
        title="Vaga Pendente — Teste",
        city="Remoto",
        contact_phone="+55 11 90000-0002",
        status=JobStatus.pending,
    )
    db_session.add(job)
    await db_session.flush()
    return job


@pytest.fixture
async def seed_expired_job(db_session) -> Job:
    job = Job(
        title="Vaga Expirada — Teste",
        city="Remoto",
        contact_phone="+55 11 90000-0003",
        status=JobStatus.published,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(job)
    await db_session.flush()
    return job
