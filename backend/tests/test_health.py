"""Tests for the public ``/health`` endpoint (Phase 3, D-14).

``/health`` is public, so it must report *whether* the Turnstile protection is
configured without ever revealing the secret (T-03-06).
"""

from __future__ import annotations

from app.core.config import DEV_TURNSTILE_SECRET


async def test_health_reports_the_turnstile_status(client):
    resp = await client.get("/api/v1/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "env" in body
    assert body["turnstile"]["mode"] == "test"
    assert body["turnstile"]["configured"] is True
    assert body["turnstile"]["site_key_configured"] is False


async def test_health_never_leaks_the_turnstile_secret(client):
    resp = await client.get("/api/v1/health")

    assert resp.status_code == 200
    assert DEV_TURNSTILE_SECRET not in resp.text
    assert "1x0000000000000000000000000000000AA" not in resp.text
