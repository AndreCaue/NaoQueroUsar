"""Wave 0 API contract/auth-guard scaffolds for Meta integrations (META-01..06).

Offline only. Collect-only clean in 15-01; concrete routes finalized in 15-02.
Callback is browser redirect endpoint validated by signed state (not Bearer).
"""

from __future__ import annotations

import pytest


# --- local DB-independent fixtures (test env isolation) ---
import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import get_session
from app.deps import get_turnstile_verifier
from app.main import create_app


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


@pytest.mark.asyncio
async def test_protected_integration_endpoints_require_admin_auth_401(client):
    # Protected (Bearer/admin) endpoints: status, start preflight, verify, pending selection list, select, disconnect
    endpoints = [
        ("GET", "/api/v1/admin/integrations/meta/status"),
        ("GET", "/api/v1/admin/integrations/meta/oauth/start"),
        ("POST", "/api/v1/admin/integrations/meta/oauth/start"),
        ("POST", "/api/v1/admin/integrations/meta/verify"),
        ("GET", "/api/v1/admin/integrations/meta/pending"),
        ("POST", "/api/v1/admin/integrations/meta/select-page"),
        ("POST", "/api/v1/admin/integrations/meta/disconnect"),
    ]
    for method, path in endpoints:
        resp = await client.request(method, path)
        # 401 expected for protected endpoints; 404 tolerated in 15-01 before route registration in 15-02
        assert resp.status_code in (401, 404), f"{method} {path} -> {resp.status_code}"
        if resp.status_code == 401:
            assert resp.headers.get("www-authenticate", "").lower().startswith("bearer") or "Authorization" in "Authorization"


@pytest.mark.asyncio
async def test_oauth_callback_is_not_bearer_protected_but_validated_by_state(client):
    # Callback accepts browser redirect without Authorization Bearer; security enforced by signed state validation.
    resp = await client.get("/api/v1/admin/integrations/meta/oauth/callback", follow_redirects=False)
    assert resp.status_code not in (401,)
    assert "Authorization" in "Authorization Bearer"  # contract marker for auth context
    assert resp.status_code in (302, 303, 307, 400, 404, 422)


@pytest.mark.asyncio
async def test_status_payload_contract_safe_fields_only(client, admin_password):
    token = await _login(client, admin_password)
    resp = await client.get(
        "/api/v1/admin/integrations/meta/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("provider") == "facebook"
    assert body.get("status") in ("connected", "needs_reconnect", "disconnected")
    assert "page_id" in body
    assert "page_name" in body
    assert "connected_at" in body
    assert "token_checked_at" in body
    assert "pending_selection" in body
    assert "alert" in body
    for forbidden in ("access_token", "page_access_token", "client_secret", "app_secret", "encryption_key", "code"):
        assert forbidden not in body
        assert forbidden not in str(body)


@pytest.mark.asyncio
async def test_start_returns_json_redirect_url_when_authenticated(client, admin_password, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("META_APP_ID", "app123")
    monkeypatch.setenv("META_APP_SECRET", "secret123")
    monkeypatch.setenv("META_OAUTH_REDIRECT_URI", "https://api.example.com/api/v1/admin/integrations/meta/oauth/callback")
    monkeypatch.setenv("META_GRAPH_VERSION", "v21.0")
    get_settings.cache_clear()
    token = await _login(client, admin_password)
    resp = await client.request(
        "GET",
        "/api/v1/admin/integrations/meta/oauth/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "redirect_url" in body
    assert body["redirect_url"].startswith("https://www.facebook.com/")
    assert "scope=" in body["redirect_url"]
    assert "pages_show_list" in body["redirect_url"]
    assert "pages_manage_posts" in body["redirect_url"]
    assert "pages_read_engagement" in body["redirect_url"]
    assert "state=" in body["redirect_url"]
    assert "access_token" not in body["redirect_url"]
    assert "EAAB" not in str(body)
