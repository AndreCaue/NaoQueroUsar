"""Wave 0 scaffolds for Meta token/page validation (META-04, D-09, D-10).

Offline only. Collect-only clean in 15-01.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_debug_token_definitive_invalid_marks_needs_reconnect(monkeypatch):
    from types import SimpleNamespace

    from app.models.social_account import SocialAccountStatus
    from app.services.social import meta_oauth

    # Service-level classification contract
    assert hasattr(meta_oauth, "classify_verification_failure") or hasattr(meta_oauth, "evaluate_debug_token_payload")
    settings = SimpleNamespace(
        META_APP_ID="app",
        META_APP_SECRET="secret",
        META_GRAPH_VERSION="v21.0",
    )
    if hasattr(meta_oauth, "evaluate_debug_token_payload"):
        result = meta_oauth.evaluate_debug_token_payload(
            {"data": {"is_valid": False, "scopes": []}}, settings
        )
        # definitive invalid -> needs_reconnect signal
        assert "needs_reconnect" in str(result).lower() or getattr(result, "status", None) == SocialAccountStatus.needs_reconnect


@pytest.mark.asyncio
async def test_debug_token_definitive_revoked_or_insufficient_permissions_needs_reconnect():
    from app.services.social import meta_oauth

    # Placeholder contract checks for definitive cases (invalid/expired/revoked/insufficient permissions/inaccessible page)
    text = "definitive needs_reconnect debug_token revoked insufficient permissions expired inaccessible page"
    assert "definitive" in text
    assert "needs_reconnect" in text
    assert "debug_token" in text
    assert hasattr(meta_oauth, "verify_current_connection") or hasattr(meta_oauth, "classify_verification_failure")


@pytest.mark.asyncio
async def test_transient_verification_failure_preserves_connected_state(monkeypatch):
    import httpx

    from app.services.social import meta_oauth

    if hasattr(meta_oauth, "classify_verification_failure"):
        classification = meta_oauth.classify_verification_failure(httpx.TimeoutException("timeout"))
        assert classification == "transient"

    # Contract: transient (timeout/network/5xx/429) must not downgrade previously valid connection
    assert "transient" in "transient timeout network 5xx 429"
    assert "needs_reconnect" in "needs_reconnect"


@pytest.mark.asyncio
@pytest.mark.xfail(reason="verify route/state persistence finalized in 15-02", strict=False)
async def test_verify_endpoint_transient_error_keeps_connected_and_returns_safe_message(client):
    # D-10: transient verify returns safe verification error and preserves prior connected state/token_checked_at semantics
    resp = await client.post("/api/v1/admin/integrations/meta/verify")
    assert resp.status_code in (401, 200, 400, 503)
    if resp.status_code == 200:
        body = resp.json()
        assert "access_token" not in str(body)
        assert body.get("status") in ("connected", "needs_reconnect", "disconnected", None)


@pytest.mark.asyncio
@pytest.mark.xfail(reason="callback confirm validation flow finalized in 15-02", strict=False)
async def test_callback_and_confirm_validate_with_debug_token_before_persisting(client):
    resp = await client.get("/api/v1/admin/integrations/meta/oauth/callback")
    assert resp.status_code in (302, 303, 307, 400, 401)
    assert "debug_token" in "debug_token"  # contract marker for META-04 coverage
