"""META-01/META-02 API tests for Instagram readiness in integrations endpoints.

Offline only. Service calls are mocked; no real Meta network calls.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import get_session
from app.deps import get_turnstile_verifier
from app.main import create_app
from app.schemas.social_integrations import (
    MetaActionResponse,
    MetaInstagramReadiness,
    MetaIntegrationStatus,
)


class _DummyResult:
    def scalar_one_or_none(self):
        return None

    def scalars(self):
        return self

    def all(self):
        return []


class _DummySession:
    async def execute(self, *args, **kwargs):
        return _DummyResult()

    def add(self, *args, **kwargs):
        return None

    async def flush(self):
        return None

    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def refresh(self, *args, **kwargs):
        return None

    async def delete(self, *args, **kwargs):
        return None


class _FakeTurnstileVerifier:
    async def verify(self, token: str, remoteip: str | None = None, **kwargs):
        from types import SimpleNamespace

        return SimpleNamespace(success=True, error_codes=[], action=kwargs.get("expected_action"))


@pytest.fixture
async def db_session():
    return _DummySession()


@pytest.fixture
async def app(db_session):
    application = create_app()
    fake = _FakeTurnstileVerifier()

    async def _override_get_session():
        yield db_session

    async def _override_get_turnstile_verifier():
        return fake

    application.dependency_overrides[get_session] = _override_get_session
    application.dependency_overrides[get_turnstile_verifier] = _override_get_turnstile_verifier
    application.state.fake_turnstile = fake
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def admin_password() -> str:
    return "test-password"


VALID_CF_TOKEN = "token-de-teste"


async def _login(client, admin_password="test-password"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _ig_ready() -> MetaInstagramReadiness:
    return MetaInstagramReadiness(
        ready=True,
        ig_user_id="1789001",
        ig_username="empreganoix",
        state="ready",
        message="Conta Instagram vinculada: @empreganoix",
        checked_at=datetime(2026, 11, 23, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_meta_status_includes_additive_instagram_readiness(client, admin_password, monkeypatch):
    async def _fake_status(_session):
        return MetaIntegrationStatus(
            provider="facebook",
            status="connected",
            page_id="123",
            page_name="Page",
            connected_at=None,
            token_checked_at=None,
            pending_selection=False,
            alert=None,
            instagram=_ig_ready(),
        )

    monkeypatch.setattr("app.api.v1.integrations.get_current_meta_status", _fake_status)

    token = await _login(client, admin_password)
    resp = await client.get(
        "/api/v1/admin/integrations/meta/status",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "connected"
    assert body["instagram"]["state"] == "ready"
    assert body["instagram"]["ready"] is True
    assert body["instagram"]["ig_user_id"] == "1789001"
    # Security assertion: no token/secret leakage
    text = resp.text
    for forbidden in (
        "access_token",
        "page_access_token",
        "client_secret",
        "EAAB",
        "SOCIAL_TOKEN_ENCRYPTION_KEY",
    ):
        assert forbidden not in text


@pytest.mark.asyncio
async def test_meta_verify_includes_additive_instagram_readiness(client, admin_password, monkeypatch):
    async def _fake_verify(_session, _settings):
        return MetaActionResponse(
            status="connected",
            message="Conexão verificada com sucesso.",
            pending_selection=False,
            instagram=_ig_ready(),
        )

    monkeypatch.setattr("app.api.v1.integrations.verify_current_connection", _fake_verify)

    token = await _login(client, admin_password)
    resp = await client.post(
        "/api/v1/admin/integrations/meta/verify",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "connected"
    assert body["instagram"]["ready"] is True
    assert body["instagram"]["state"] == "ready"
    text = resp.text
    for forbidden in (
        "access_token",
        "page_access_token",
        "client_secret",
        "EAAB",
        "SOCIAL_TOKEN_ENCRYPTION_KEY",
    ):
        assert forbidden not in text
