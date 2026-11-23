"""META-01/META-02 backend tests for Instagram readiness (Phase 29).

Offline only: Graph calls are mocked; no real Meta network calls.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest

from app.models.social_account import SocialAccount, SocialAccountStatus
from app.schemas.social_integrations import MetaInstagramReadiness
from app.services.social import meta_oauth
from app.services.social.instagram_readiness import resolve_instagram_readiness


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return self

    def all(self):
        return [] if self._value is None else [self._value]


class _FakeSession:
    def __init__(self, account: SocialAccount | None = None, pending: bool = False):
        self.account = account
        self.pending = pending
        self.added = []

    async def execute(self, stmt, *args, **kwargs):
        sql = str(stmt)
        if "social_oauth_pending" in sql:
            return _ScalarResult(object() if self.pending else None)
        return _ScalarResult(self.account)

    def add(self, obj):
        self.added.append(obj)
        if isinstance(obj, SocialAccount):
            self.account = obj

    async def flush(self):
        return None

    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def delete(self, obj):
        if self.account is obj:
            self.account = None

    async def scalar(self, *args, **kwargs):
        return self.account


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        META_APP_ID="app123",
        META_APP_SECRET="secret123",
        META_GRAPH_VERSION="v21.0",
        META_OAUTH_REDIRECT_URI="https://api.example.com/api/v1/admin/integrations/meta/oauth/callback",
        SOCIAL_TOKEN_ENCRYPTION_KEY="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        JWT_SECRET="jwt-secret",
    )


def _connected_account(**overrides) -> SocialAccount:
    data = dict(
        provider="facebook",
        page_id="12345",
        page_name="Page",
        page_access_token="encrypted-token",
        status=SocialAccountStatus.connected,
        connected_at=datetime(2026, 11, 20, tzinfo=timezone.utc),
        token_checked_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        ig_user_id=None,
        ig_username=None,
        ig_readiness_state=None,
        ig_readiness_checked_at=None,
        ig_readiness_last_error_code=None,
        ig_readiness_last_error_message=None,
    )
    data.update(overrides)
    return SocialAccount(**data)


@pytest.mark.asyncio
async def test_status_includes_additive_instagram_ready_payload(monkeypatch):
    account = _connected_account(
        ig_user_id="1789001",
        ig_username="empreganoix",
        ig_readiness_state="ready",
        ig_readiness_checked_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
    )
    session = _FakeSession(account)

    status = await meta_oauth.get_current_meta_status(session)

    assert status.status == "connected"
    assert status.instagram is not None
    assert status.instagram.ready is True
    assert status.instagram.state == "ready"
    assert status.instagram.ig_user_id == "1789001"
    assert status.instagram.ig_username == "empreganoix"
    assert "Conta Instagram vinculada" in (status.instagram.message or "")


@pytest.mark.asyncio
async def test_resolve_instagram_readiness_maps_graph_outcomes(monkeypatch):
    settings = _settings()

    async def _ok(_url, _params):
        return {"instagram_business_account": {"id": "1789", "username": "nqu"}}

    monkeypatch.setattr("app.services.social.instagram_readiness._graph_get_json", _ok)
    ready = await resolve_instagram_readiness(
        page_id="123", page_access_token_plain="plain", settings=settings
    )
    assert ready.state == "ready"
    assert ready.ready is True
    assert ready.ig_user_id == "1789"

    async def _missing(_url, _params):
        return {"id": "123"}

    monkeypatch.setattr("app.services.social.instagram_readiness._graph_get_json", _missing)
    missing = await resolve_instagram_readiness(
        page_id="123", page_access_token_plain="plain", settings=settings
    )
    assert missing.state == "missing_linkage"
    assert missing.ready is False
    assert "Nenhuma conta Instagram Business/Creator vinculada" in missing.message

    request = httpx.Request("GET", "https://graph.facebook.com/v21.0/123")
    response = httpx.Response(403, request=request, json={"error": {"code": 10, "message": "perm"}})
    err = httpx.HTTPStatusError("bad", request=request, response=response)
    setattr(err, "_safe_body", response.json())

    async def _perm(_url, _params):
        raise err

    monkeypatch.setattr("app.services.social.instagram_readiness._graph_get_json", _perm)
    denied = await resolve_instagram_readiness(
        page_id="123", page_access_token_plain="plain", settings=settings
    )
    assert denied.state in {"missing_permissions", "needs_reconnect"}
    assert denied.ready is False
    assert "Reconecte" in denied.message or "permiss" in denied.message.lower()


@pytest.mark.asyncio
async def test_verify_refreshes_instagram_readiness_without_exposing_tokens(monkeypatch):
    account = _connected_account()
    session = _FakeSession(account)
    settings = _settings()

    monkeypatch.setattr("app.services.social.crypto.decrypt_token", lambda *_args, **_kwargs: "plain-token")

    async def _classify(_token, _settings):
        return "definitive", True

    monkeypatch.setattr(meta_oauth, "_classify_current_token", _classify)

    async def _resolve(**_kwargs):
        return SimpleNamespace(
            ready=True,
            ig_user_id="1789001",
            ig_username="empreganoix",
            state="ready",
            message="Conta Instagram vinculada: @empreganoix",
            error_code=None,
        )

    monkeypatch.setattr(meta_oauth, "resolve_instagram_readiness", _resolve)

    resp = await meta_oauth.verify_current_connection(session, settings)

    assert resp.status == "connected"
    assert resp.instagram is not None
    assert resp.instagram.ig_user_id == "1789001"
    assert account.ig_user_id == "1789001"
    assert account.status == SocialAccountStatus.connected
    payload = resp.model_dump_json()
    for forbidden in ("access_token", "page_access_token", "client_secret", "EAAB", "SOCIAL_TOKEN_ENCRYPTION_KEY"):
        assert forbidden not in payload


@pytest.mark.asyncio
async def test_missing_ig_permissions_do_not_break_facebook_connection_d15(monkeypatch):
    account = _connected_account()
    session = _FakeSession(account)
    settings = _settings()

    monkeypatch.setattr("app.services.social.crypto.decrypt_token", lambda *_args, **_kwargs: "plain-token")

    async def _classify(_token, _settings):
        return "definitive", True

    monkeypatch.setattr(meta_oauth, "_classify_current_token", _classify)

    async def _resolve(**_kwargs):
        return SimpleNamespace(
            ready=False,
            ig_user_id=None,
            ig_username=None,
            state="missing_permissions",
            message="Permissões do Instagram ausentes. Reconecte para autorizar o Instagram.",
            error_code="missing_permissions",
        )

    monkeypatch.setattr(meta_oauth, "resolve_instagram_readiness", _resolve)

    resp = await meta_oauth.verify_current_connection(session, settings)

    # D-15: Facebook remains authoritative and connected when FB token is valid.
    assert resp.status == "connected"
    assert account.status == SocialAccountStatus.connected
    assert resp.instagram is not None
    assert resp.instagram.state == "missing_permissions"
    assert resp.instagram.ready is False
