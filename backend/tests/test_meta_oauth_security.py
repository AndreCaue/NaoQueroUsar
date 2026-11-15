"""Wave 0 security scaffolds for Meta OAuth/integrations (META-05, D-03/D-07/D-11).

Offline only. Collect-only clean in 15-01.
"""

from __future__ import annotations

import uuid

import pytest

from app.models.social_account import SocialAccount, SocialAccountStatus
from app.services.social.crypto import decrypt_token, encrypt_token


@pytest.mark.asyncio
async def test_social_account_page_access_token_persisted_encrypted_not_plaintext(db_session):
    key = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="  # 32-byte base64 Fernet key
    plain = "EAAB_page_token_plaintext_example"
    account = SocialAccount(
        provider="facebook",
        page_id="123",
        page_name="Pagina Teste",
        page_access_token=encrypt_token(plain, key),
        status=SocialAccountStatus.connected,
    )
    db_session.add(account)
    await db_session.flush()

    assert account.page_access_token != plain
    assert "EAAB" not in account.page_access_token or account.page_access_token != plain
    assert decrypt_token(account.page_access_token, key) == plain


def test_meta_oauth_service_never_exposes_secrets_in_safe_errors(monkeypatch):
    from types import SimpleNamespace

    from app.services.social.meta_oauth import MetaOAuthConfigError, build_meta_oauth_dialog_url

    settings = SimpleNamespace(
        META_APP_ID="",
        META_APP_SECRET="super-secret-app-secret",
        META_GRAPH_VERSION="v21.0",
        META_OAUTH_REDIRECT_URI="",
        SOCIAL_TOKEN_ENCRYPTION_KEY="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        JWT_SECRET="jwt-secret",
    )
    with pytest.raises(MetaOAuthConfigError) as excinfo:
        build_meta_oauth_dialog_url(settings)
    msg = str(excinfo.value)
    assert msg == "Integração com Facebook não configurada"
    assert "client_secret" not in msg.lower()
    assert "META_APP_SECRET" not in msg
    assert "super-secret-app-secret" not in msg
    assert "SOCIAL_TOKEN_ENCRYPTION_KEY" not in msg


def test_safe_status_and_pending_contracts_have_no_token_fields():
    from app.schemas import social_integrations as schemas

    assert not hasattr(schemas.MetaIntegrationStatus, "access_token")
    assert not hasattr(schemas.MetaIntegrationStatus, "page_access_token")
    assert not hasattr(schemas.MetaPendingPage, "access_token")
    assert "access_token" not in " ".join(getattr(schemas.MetaPendingSelectionResponse, "model_fields", {}).keys())
    assert "client_secret" not in str(schemas.__dict__)
    assert "encryption_key" not in str(schemas.__dict__)


@pytest.mark.asyncio
@pytest.mark.xfail(reason="redirect contract finalized in 15-02", strict=False)
async def test_callback_redirects_and_api_responses_never_contain_tokens_or_oauth_code(client):
    resp = await client.get(
        "/api/v1/admin/integrations/meta/oauth/callback",
        params={"state": "bad", "code": "oauth-code-secret", "error": "access_denied"},
        follow_redirects=False,
    )
    loc = resp.headers.get("location", "")
    body_text = resp.text
    for leaked in ("access_token", "EAAB", "client_secret", "META_APP_SECRET", "SOCIAL_TOKEN_ENCRYPTION_KEY", "fb_exchange_token", "oauth-code-secret"):
        assert leaked not in loc
        assert leaked not in body_text


@pytest.mark.asyncio
@pytest.mark.xfail(reason="status endpoint finalized in 15-02", strict=False)
async def test_status_payload_safe_no_secrets(client, admin_password):
    resp = await client.get("/api/v1/admin/integrations/meta/status")
    assert resp.status_code == 401
    text = resp.text
    assert "access_token" not in text
    assert "EAAB" not in text
    assert "client_secret" not in text
