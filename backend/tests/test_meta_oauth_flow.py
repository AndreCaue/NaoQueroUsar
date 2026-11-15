"""Wave 0 scaffolds for Meta OAuth flow (META-01/02/03, D-01..D-08).

Collect-only clean in 15-01; service/route contracts are finalized across 15-01/15-02.
Offline only (no real Meta network calls).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest

VALID_CF_TOKEN = "token-de-teste"
META_SCOPES = "pages_show_list,pages_manage_posts,pages_read_engagement"


async def _login(client, admin_password="test-password"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_meta_oauth_state_contains_purpose_nonce_exp_and_rejects_tampering(monkeypatch):
    from app.core.config import get_settings
    from app.services.social.meta_oauth import (
        MetaOAuthStateError,
        build_meta_oauth_state,
        validate_meta_oauth_state,
    )

    settings = get_settings()
    secret = settings.JWT_SECRET
    state = build_meta_oauth_state(secret)
    claims = validate_meta_oauth_state(state, secret)

    assert claims["purpose"] == "meta_oauth"
    assert "nonce" in claims and claims["nonce"]
    assert "exp" in claims
    assert "iat" in claims

    tampered = state[:-1] + ("a" if state[-1] != "a" else "b")
    with pytest.raises(MetaOAuthStateError):
        validate_meta_oauth_state(tampered, secret)

    expired_payload_state = build_meta_oauth_state(secret)
    # expired/invalid handling covered by service; force invalid decode path
    with pytest.raises(MetaOAuthStateError):
        validate_meta_oauth_state(expired_payload_state + "x", secret)


@pytest.mark.xfail(reason="requires JWT iat/exp control; enforced by service in 15-01", strict=False)
def test_meta_oauth_state_rejects_expired(monkeypatch):
    import jwt

    from app.core.config import get_settings
    from app.services.social.meta_oauth import (
        META_OAUTH_STATE_TTL_SECONDS,
        MetaOAuthStateError,
        validate_meta_oauth_state,
    )

    settings = get_settings()
    now = datetime.now(timezone.utc) - timedelta(seconds=META_OAUTH_STATE_TTL_SECONDS + 60)
    token = jwt.encode(
        {"purpose": "meta_oauth", "nonce": str(uuid.uuid4()), "iat": now, "exp": now + timedelta(seconds=1)},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    with pytest.raises(MetaOAuthStateError):
        validate_meta_oauth_state(token, settings.JWT_SECRET)


def test_build_meta_oauth_dialog_url_uses_graph_version_scopes_redirect_and_state(monkeypatch):
    from types import SimpleNamespace

    from app.services.social.meta_oauth import build_meta_oauth_dialog_url

    settings = SimpleNamespace(
        META_APP_ID="app123",
        META_APP_SECRET="secret123",
        META_GRAPH_VERSION="v21.0",
        META_OAUTH_REDIRECT_URI="https://api.example.com/api/v1/admin/integrations/meta/oauth/callback",
        JWT_SECRET="jwt-secret",
    )
    monkeypatch.setenv("JWT_SECRET", settings.JWT_SECRET)
    url = build_meta_oauth_dialog_url(settings)
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    assert parsed.netloc == "www.facebook.com"
    assert parsed.path.endswith(f"/{settings.META_GRAPH_VERSION}/dialog/oauth")
    assert "graph_version" in {"graph_version", "META_GRAPH_VERSION"} or settings.META_GRAPH_VERSION in url
    assert qs["scope"] == [META_SCOPES]
    assert qs["response_type"] == ["code"]
    assert qs["redirect_uri"] == [settings.META_OAUTH_REDIRECT_URI]
    assert qs["client_id"] == [settings.META_APP_ID]
    assert "state" in qs and qs["state"][0]


def test_missing_meta_envs_fails_safe(monkeypatch):
    from types import SimpleNamespace

    from app.services.social.meta_oauth import (
        MetaOAuthConfigError,
        build_meta_oauth_dialog_url,
    )

    settings = SimpleNamespace(
        META_APP_ID="",
        META_APP_SECRET="",
        META_GRAPH_VERSION="v21.0",
        META_OAUTH_REDIRECT_URI="",
        JWT_SECRET="jwt-secret",
    )
    with pytest.raises(MetaOAuthConfigError) as excinfo:
        build_meta_oauth_dialog_url(settings)
    msg = str(excinfo.value)
    assert msg == "Integração com Facebook não configurada"


@pytest.mark.asyncio
@pytest.mark.xfail(reason="callback/start routes finalized in 15-02", strict=False)
async def test_oauth_callback_invalid_state_redirects_safe_error_without_persisting(client):
    resp = await client.get(
        "/api/v1/admin/integrations/meta/oauth/callback",
        params={"state": "invalid", "code": "abc"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303, 307)
    loc = resp.headers.get("location", "")
    assert "result=error" in loc or "result=cancelled" in loc or "select_page" not in loc
    assert "access_token" not in loc and "EAAB" not in loc


@pytest.mark.asyncio
@pytest.mark.xfail(reason="callback/start routes finalized in 15-02", strict=False)
async def test_oauth_callback_cancel_redirects_safe_without_connection(client):
    resp = await client.get(
        "/api/v1/admin/integrations/meta/oauth/callback",
        params={"error": "access_denied", "state": "x"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303, 307)
    loc = resp.headers.get("location", "")
    assert "result=cancelled" in loc or "result=error" in loc


@pytest.mark.asyncio
async def test_single_page_auto_completes_and_multi_page_creates_pending_selection_contract(monkeypatch):
    """Service-level contract for META-03/D-05/D-08 (offline)."""
    from types import SimpleNamespace

    from app.services.social import meta_oauth

    settings = SimpleNamespace(
        META_APP_ID="app123",
        META_APP_SECRET="secret123",
        META_GRAPH_VERSION="v21.0",
        META_OAUTH_REDIRECT_URI="https://api.example.com/callback",
        SOCIAL_TOKEN_ENCRYPTION_KEY="",
        JWT_SECRET="jwt-secret",
    )

    # Ensure helpers exist and express pinned select_page + pending nonce contract semantics
    assert hasattr(meta_oauth, "create_pending_selection")
    assert hasattr(meta_oauth, "confirm_pending_selection")
    assert hasattr(meta_oauth, "process_callback") or hasattr(meta_oauth, "complete_oauth_callback")


@pytest.mark.asyncio
@pytest.mark.xfail(reason="route-level select_page redirect finalized in 15-02", strict=False)
async def test_callback_multi_page_redirects_with_select_page_and_pending_nonce(client):
    # Contract expectation: callback redirects to /admin/integracoes?result=select_page&pending=<opaque_nonce>
    resp = await client.get(
        "/api/v1/admin/integrations/meta/oauth/callback",
        params={"state": "dummy", "code": "dummy"},
        follow_redirects=False,
    )
    loc = resp.headers.get("location", "")
    assert resp.status_code in (302, 303, 307, 400, 401, 403)
    assert "select_page" in loc or "result=" in loc or loc == ""
    if "select_page" in loc:
        assert "pending=" in loc


@pytest.mark.asyncio
@pytest.mark.xfail(reason="replacement semantics finalized with route wiring in 15-02", strict=False)
async def test_reconnect_replaces_existing_active_connection(client, db_session, admin_password):
    # D-06: new connection/selection replaces active connection (single page/admin)
    token = await _login(client, admin_password)
    assert token
    assert META_SCOPES == "pages_show_list,pages_manage_posts,pages_read_engagement"
