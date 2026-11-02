"""Manual expiry sweep tests (LIFE-04, T-06-01/T-06-02).

Covers ``POST /api/v1/admin/expire``:

- the ``X-Cron-Secret`` gate fails CLOSED (no secret configured → 503, missing
  or wrong header → 401, admin JWT is NOT interchangeable with the cron secret);
- the sweep hard deletes expired ``published`` and ``pending`` rows, keeps the
  live ones, and is idempotent (a second call answers ``deleted: 0``).
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.core.config import get_settings
from app.models.job import Job, JobStatus

CRON_SECRET = "cron-secret-de-teste-0123456789"
VALID_CF_TOKEN = "token-de-teste"
ENDPOINT = "/api/v1/admin/expire"


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_job(**kwargs) -> Job:
    """A minimal valid job (title + one contact are the DB CHECKs)."""
    defaults = {
        "title": "Vaga de teste",
        "city": "Remoto",
        "contact_phone": "+55 11 90000-0000",
        "status": JobStatus.published,
    }
    defaults.update(kwargs)
    return Job(**defaults)


def _expired(**kwargs) -> Job:
    return _make_job(expires_at=datetime.now(timezone.utc) - timedelta(days=1), **kwargs)


def _live(**kwargs) -> Job:
    return _make_job(expires_at=datetime.now(timezone.utc) + timedelta(days=13), **kwargs)


@pytest.fixture
def cron_secret(monkeypatch) -> str:
    """Configure the endpoint secret for the current test (settings are cached)."""
    monkeypatch.setattr(get_settings(), "CRON_SECRET", CRON_SECRET)
    return CRON_SECRET


async def _count_jobs(db_session) -> int:
    return int((await db_session.scalar(select(func.count()).select_from(Job))) or 0)


# ---------------------------------------------------------------------------
# T-06-01: the gate fails closed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expire_without_secret_configured_returns_503(client, monkeypatch):
    """No CRON_SECRET in the environment → the trigger is disabled, not open."""
    monkeypatch.setattr(get_settings(), "CRON_SECRET", "")

    resp = await client.post(ENDPOINT, headers={"X-Cron-Secret": "qualquer-coisa"})

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Expiração manual não configurada"


@pytest.mark.asyncio
async def test_expire_missing_header_returns_401(client, cron_secret):
    resp = await client.post(ENDPOINT)

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Não autorizado"


@pytest.mark.asyncio
async def test_expire_wrong_secret_returns_401(client, cron_secret):
    resp = await client.post(ENDPOINT, headers={"X-Cron-Secret": "segredo-errado"})

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Não autorizado"


@pytest.mark.asyncio
async def test_admin_bearer_token_is_not_a_cron_secret(client, cron_secret, admin_password):
    """A valid admin JWT must not authorize the sweep — credentials differ."""
    login = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    resp = await client.post(
        ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# T-06-02 / LIFE-02 / LIFE-03: the sweep itself
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expire_deletes_expired_published_and_pending(
    client, db_session, cron_secret
):
    """Expired published + pending rows go away; live rows stay (D-04)."""
    db_session.add_all(
        [
            _expired(title="Publicada expirada", status=JobStatus.published),
            _expired(title="Pending expirada", status=JobStatus.pending),
            _live(title="Publicada viva", status=JobStatus.published),
            _live(title="Pending viva", status=JobStatus.pending),
        ]
    )
    await db_session.flush()
    assert await _count_jobs(db_session) == 4

    resp = await client.post(ENDPOINT, headers={"X-Cron-Secret": cron_secret})

    assert resp.status_code == 200
    assert resp.json() == {"deleted": 2, "status": "ok"}

    remaining = list((await db_session.scalars(select(Job.title))).all())
    assert sorted(remaining) == ["Pending viva", "Publicada viva"]


@pytest.mark.asyncio
async def test_expire_is_idempotent(client, db_session, cron_secret):
    """Running the sweep twice is safe: the second run deletes nothing."""
    db_session.add(_expired(title="Expirada"))
    await db_session.flush()

    first = await client.post(ENDPOINT, headers={"X-Cron-Secret": cron_secret})
    second = await client.post(ENDPOINT, headers={"X-Cron-Secret": cron_secret})

    assert first.status_code == 200
    assert first.json()["deleted"] == 1
    assert second.status_code == 200
    assert second.json() == {"deleted": 0, "status": "ok"}


@pytest.mark.asyncio
async def test_expire_with_empty_table_returns_zero(client, db_session, cron_secret):
    resp = await client.post(ENDPOINT, headers={"X-Cron-Secret": cron_secret})

    assert resp.status_code == 200
    assert resp.json() == {"deleted": 0, "status": "ok"}
