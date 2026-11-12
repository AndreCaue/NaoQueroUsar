"""Tests for the public ``/health`` endpoint (Phase 3, D-14).

``/health`` is public, so it must report *whether* the Turnstile protection is
configured without ever revealing the secret (T-03-06).
"""

from __future__ import annotations

from app.core.config import DEV_TURNSTILE_SECRET
from app.deps import get_turnstile_verifier


async def test_health_reports_the_turnstile_status(client):
    resp = await client.get("/api/v1/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "env" in body
    assert body["turnstile"]["mode"] == "test"
    assert body["turnstile"]["configured"] is True
    assert body["turnstile"]["site_key_configured"] is False
    # Escape hatch: reports the flag, never the key. Default is off.
    assert body["turnstile"]["test_override"] is False


async def test_health_never_leaks_the_turnstile_secret(client):
    resp = await client.get("/api/v1/health")

    assert resp.status_code == 200
    assert DEV_TURNSTILE_SECRET not in resp.text
    assert "1x0000000000000000000000000000000AA" not in resp.text


async def test_the_harness_stubs_the_turnstile_verifier(app, fake_turnstile):
    """The suite must never reach Cloudflare — the verifier is overridden.

    The plans 03-03/03-04 rely on this seam: the real verifier is replaced
    through ``dependency_overrides``, so every protected route can be tested
    offline.
    """
    assert get_turnstile_verifier in app.dependency_overrides
    assert app.state.fake_turnstile is fake_turnstile
