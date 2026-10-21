"""Tests for the slowapi limiter, the pt-BR 429 handler and the DI seam.

The limiter is global (one instance per process, in-memory storage), so the
store is reset before and after every test — otherwise the buckets leak from
one test into the next (T-03-08).

No test touches the network: the rate limit is enforced by the middleware
inside the ASGI app.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from slowapi.errors import RateLimitExceeded

from app.core.client_ip import resolve_client_ip
from app.core.ratelimit import (
    RATE_LIMIT_MESSAGE,
    limiter,
    login_limit,
    rate_limit_exceeded_handler,
    reveal_limit,
)
from app.main import create_app

# The real application — the wiring under test (``app.state.limiter`` and the
# pt-BR exception handler) is the one installed by ``create_app()``.
#
# The limited route is declared ONCE at module level: the slowapi decorator
# *appends* the limit to a per-endpoint list, so re-declaring it per test
# would make a single request consume several hits.
test_app = create_app()


@test_app.get("/limited")
@limiter.limit("2/minute")
async def limited(request: Request):
    return {"ok": True}


@test_app.get("/dynamic")
@limiter.limit(reveal_limit)
async def dynamic(request: Request):
    return {"ok": True}


@pytest.fixture(autouse=True)
def _reset_limiter_store():
    """The limiter store is global — never let a bucket leak across tests."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
async def http_client():
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ---------------------------------------------------------------------------
# The limit itself
# ---------------------------------------------------------------------------


async def test_requests_below_the_limit_pass(http_client):
    for _ in range(2):
        resp = await http_client.get("/limited")
        assert resp.status_code == 200


async def test_request_over_the_limit_returns_429(http_client):
    await http_client.get("/limited")
    await http_client.get("/limited")

    resp = await http_client.get("/limited")

    assert resp.status_code == 429


async def test_429_body_uses_the_pt_br_detail_key(http_client):
    await http_client.get("/limited")
    await http_client.get("/limited")

    resp = await http_client.get("/limited")

    # The frontend reads ``body.detail`` — the slowapi default handler would
    # answer ``{"error": ...}`` in English and the client would show nothing.
    assert resp.json() == {"detail": RATE_LIMIT_MESSAGE}
    assert RATE_LIMIT_MESSAGE == (
        "Muitas tentativas. Aguarde alguns segundos e tente novamente."
    )


async def test_429_carries_a_retry_after_header(http_client):
    await http_client.get("/limited")
    await http_client.get("/limited")

    resp = await http_client.get("/limited")

    retry_after = resp.headers.get("Retry-After")
    assert retry_after is not None
    assert int(retry_after) > 0


async def test_a_different_ip_gets_its_own_bucket(http_client):
    for _ in range(2):
        resp = await http_client.get("/limited", headers={"X-Real-IP": "203.0.113.9"})
        assert resp.status_code == 200

    blocked = await http_client.get("/limited", headers={"X-Real-IP": "203.0.113.9"})
    assert blocked.status_code == 429

    other = await http_client.get("/limited", headers={"X-Real-IP": "198.51.100.7"})
    assert other.status_code == 200


# ---------------------------------------------------------------------------
# The key of the bucket — the resolved IP, never slowapi's default (D-10)
# ---------------------------------------------------------------------------


def test_limiter_is_keyed_by_the_resolved_client_ip():
    assert limiter._key_func is resolve_client_ip


# ---------------------------------------------------------------------------
# The limit is configuration, read per request — not frozen at import time
# ---------------------------------------------------------------------------


def test_reveal_and_login_limits_come_from_settings(monkeypatch):
    stub = SimpleNamespace(REVEAL_RATE_LIMIT="7/minute", LOGIN_RATE_LIMIT="3/minute")
    monkeypatch.setattr("app.core.ratelimit.get_settings", lambda: stub)

    assert reveal_limit() == "7/minute"
    assert login_limit() == "3/minute"


async def test_limit_is_resolved_on_every_request(http_client, monkeypatch):
    stub = SimpleNamespace(REVEAL_RATE_LIMIT="1/minute", LOGIN_RATE_LIMIT="1/minute")
    monkeypatch.setattr("app.core.ratelimit.get_settings", lambda: stub)

    assert (await http_client.get("/dynamic")).status_code == 200
    assert (await http_client.get("/dynamic")).status_code == 429


# ---------------------------------------------------------------------------
# Wiring — the app exposes the limiter and the custom handler
# ---------------------------------------------------------------------------


def test_create_app_registers_the_limiter_on_the_app_state():
    app = create_app()

    assert app.state.limiter is limiter


def test_create_app_registers_the_rate_limit_exceeded_handler():
    app = create_app()

    assert app.exception_handlers[RateLimitExceeded] is rate_limit_exceeded_handler
