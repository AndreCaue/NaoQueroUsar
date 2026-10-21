"""Proxy-aware client IP resolution — the rate-limit key (Phase 3, D-10).

The rate-limit bucket is keyed by the resolved client IP. Behind a proxy the
naive ``request.client.host`` is the proxy's own address, so every visitor
lands in the same bucket and one noisy client locks everybody out. The
slowapi default (``get_remote_address``) has exactly the same problem, which
is why it is never used here.

The chain is fixed, in this order:

1. ``X-Real-IP`` — Railway *overwrites* this header with the real client
   address, so it is the most trustworthy signal when present. It is accepted
   as long as it parses as an IP address.
2. ``X-Forwarded-For`` — Render *appends* to this header, so the right-most
   entry is the one written by the closest proxy. Entries that are private,
   loopback, link-local, reserved or unspecified are skipped. The left-most
   entry is fully client-controlled (spoofable) and is therefore never used.
3. ``request.client.host`` — the direct peer, used when no proxy header
   applies (local dev, direct exposure).
4. ``"unknown"`` — last resort; all unidentified clients share one bucket.

Values that do not parse as an IP address are discarded instead of poisoning
the bucket key.
"""

from __future__ import annotations

import ipaddress

from fastapi import Request

UNKNOWN_IP = "unknown"


def _is_public_ip(value: str) -> bool:
    """True when ``value`` parses as an IP that is not private/reserved."""
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_unspecified
    )


def _rightmost_public_xff(request: Request) -> str | None:
    """The right-most public entry of ``X-Forwarded-For``, or ``None``."""
    raw = request.headers.get("x-forwarded-for", "")
    for candidate in reversed(raw.split(",")):
        candidate = candidate.strip()
        if candidate and _is_public_ip(candidate):
            return candidate
    return None


def resolve_client_ip(request: Request) -> str:
    """Resolve the client IP used as the rate-limit key (D-10)."""
    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        try:
            ipaddress.ip_address(real_ip)
        except ValueError:
            pass  # unparseable -> ignore the header, do not poison the key
        else:
            return real_ip

    xff_ip = _rightmost_public_xff(request)
    if xff_ip:
        return xff_ip

    client = request.client
    if client is not None and client.host:
        return client.host

    return UNKNOWN_IP
