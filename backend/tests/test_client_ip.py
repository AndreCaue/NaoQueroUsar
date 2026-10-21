"""Tests for the proxy-aware client IP resolver (Phase 3 — D-10).

The rate-limit bucket is keyed by the resolved client IP. Behind a proxy the
naive ``request.client.host`` is the proxy's own address, which would collapse
every visitor into a single bucket — so the resolution chain is fixed:

``X-Real-IP`` → right-most public entry of ``X-Forwarded-For`` →
``request.client.host`` → ``"unknown"``.

These tests are pure unit tests: no app import, no network, no database.
"""

from starlette.requests import Request

from app.core.client_ip import UNKNOWN_IP, resolve_client_ip


def make_request(headers=None, client_host="127.0.0.1") -> Request:
    """Build a minimal Starlette ``Request`` with an HTTP scope."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (key.lower().encode(), value.encode())
            for key, value in (headers or {}).items()
        ],
        "query_string": b"",
        "scheme": "http",
        "server": ("testserver", 80),
    }
    if client_host is not None:
        scope["client"] = (client_host, 1234)
    return Request(scope)


async def test_x_real_ip_wins_over_x_forwarded_for():
    """X-Real-IP has the highest priority (Railway overwrites it)."""
    request = make_request(
        {"x-real-ip": "203.0.113.10", "x-forwarded-for": "1.1.1.1"}
    )
    assert resolve_client_ip(request) == "203.0.113.10"


async def test_invalid_x_real_ip_is_ignored():
    """A non-IP X-Real-IP must not poison the bucket key."""
    request = make_request(
        {"x-real-ip": "nao-um-ip", "x-forwarded-for": "1.1.1.1"}
    )
    assert resolve_client_ip(request) == "1.1.1.1"


async def test_x_forwarded_for_uses_rightmost_entry():
    """The left-most XFF entry is spoofable — the right-most one is used."""
    request = make_request({"x-forwarded-for": "9.9.9.9, 2.2.2.2"})
    assert resolve_client_ip(request) == "2.2.2.2"


async def test_x_forwarded_for_skips_private_entries():
    """A private/loopback entry appended by an internal proxy is skipped."""
    request = make_request({"x-forwarded-for": "1.1.1.1, 10.0.0.5"})
    assert resolve_client_ip(request) == "1.1.1.1"


async def test_x_forwarded_for_all_private_falls_back_to_client_host():
    """When every XFF entry is private, the direct peer is used."""
    request = make_request({"x-forwarded-for": "192.168.0.1"}, client_host="203.0.113.55")
    assert resolve_client_ip(request) == "203.0.113.55"


async def test_no_headers_falls_back_to_client_host():
    """Without proxy headers the direct peer address is the key."""
    request = make_request(client_host="198.51.100.7")
    assert resolve_client_ip(request) == "198.51.100.7"


async def test_without_client_returns_unknown():
    """A request without a peer address resolves to the shared 'unknown' bucket."""
    request = make_request(client_host=None)
    assert resolve_client_ip(request) == UNKNOWN_IP
