"""Rate limiting (Phase 3, SECR-02).

The public board must survive a scraper without a Redis bill: the limiter
keeps its counters **in the memory of the process**, on a one-minute window,
keyed by the resolved client IP (D-05, D-10).

Three decisions shape this module:

- **No default limits.** ``default_limits=[]`` and no ``application_limits`` —
  only the two routes of this phase (the contact reveal and the admin login)
  are limited. Every other route of the project stays free (D-08).
- **The bucket key is the resolved IP**, never slowapi's ``get_remote_address``
  default, which behind a proxy would put every visitor in the same bucket
  (D-10).
- **The bucket is per route, not per URL.** slowapi's default ``key_style``
  (``"url"``) scopes the bucket by the *request path* — and the reveal route
  carries the job id in the path, so every job would get its own bucket and a
  scraper could walk through the ids without ever hitting the limit (and
  without ever paying for the Cloudflare verification it triggers). With
  ``key_style="endpoint"`` the bucket is ``(IP, route)``: one window per
  visitor per route, which is what D-05 and D-08 describe.
- **The 429 answer is ours.** slowapi's default handler replies
  ``{"error": "Rate limit exceeded: ..."}`` in English, while the frontend
  reads ``body.detail``. The custom handler answers ``{"detail": ...}`` in
  pt-BR plus a ``Retry-After`` header (T-03-07).
"""

from __future__ import annotations

import logging
import time

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.client_ip import resolve_client_ip
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Copy do 03-UI-SPEC — a mesma chave "detail" que o frontend extrai.
RATE_LIMIT_MESSAGE = "Muitas tentativas. Aguarde alguns segundos e tente novamente."

# Usado quando não dá para calcular o fim da janela (fallback conservador).
DEFAULT_RETRY_AFTER_SECONDS = 10

__all__ = [
    "RATE_LIMIT_MESSAGE",
    "RateLimitExceeded",
    "limiter",
    "login_limit",
    "rate_limit_exceeded_handler",
    "reveal_limit",
]


class SafeLimiter(Limiter):
    """slowapi's ``Limiter``, tolerant to endpoints without a ``response``.

    slowapi injects the ``X-RateLimit-*`` headers by calling
    ``_inject_headers(response, ...)`` with the ``response: Response``
    argument of the decorated endpoint. When the endpoint does not declare
    that argument — the common case for our routers — slowapi raises
    ``Exception("parameter `response` must be an instance of ...")`` and
    *every successful request becomes a 500*.

    Those headers are a nicety (the frontend only reads ``body.detail``, and
    our own 429 handler already sets ``Retry-After``), so the injection is
    simply skipped when there is no response object to decorate.
    """

    def _inject_headers(self, response, current_limit):
        if response is None:
            return response
        return super()._inject_headers(response, current_limit)


# One instance per process. The storage is in-memory (no Redis, no table, no
# migration) and the window is one minute — the format of the env knobs.
#
# ``key_style="endpoint"`` scopes the bucket by the endpoint instead of by
# the request path: the reveal route has the job id in its path, and a
# per-path bucket would give every job its own window (D-05/D-08).
limiter = SafeLimiter(
    key_func=resolve_client_ip,
    default_limits=[],
    headers_enabled=True,
    storage_uri="memory://",
    key_style="endpoint",
)


def reveal_limit() -> str:
    """Rate limit of the contact-reveal route (read from the env per request)."""
    return get_settings().REVEAL_RATE_LIMIT


def login_limit() -> str:
    """Rate limit of the admin login route (read from the env per request)."""
    return get_settings().LOGIN_RATE_LIMIT


def _retry_after_seconds(request: Request, exc: RateLimitExceeded) -> int:
    """How many seconds the client should wait before retrying.

    The window may already be half spent, so what the client really has to
    wait is the *remaining* time. ``get_expiry()`` (the whole window) is the
    fallback when the window stats are not available.
    """
    view_limit = getattr(request.state, "view_rate_limit", None)
    if view_limit is not None:
        try:
            window_stats = request.app.state.limiter.limiter.get_window_stats(
                view_limit[0], *view_limit[1]
            )
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            pass
        else:
            reset_in = 1 + window_stats[0]
            seconds = int(reset_in - time.time())
            if seconds > 0:
                return seconds

    try:
        return int(exc.limit.limit.get_expiry())
    except (AttributeError, TypeError, ValueError):
        return DEFAULT_RETRY_AFTER_SECONDS


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Answer 429 in pt-BR.

    The body uses the ``detail`` key (the one the frontend extracts) and the
    ``Retry-After`` header tells the client when it may try again.
    """
    logger.warning("rate_limit_exceeded", extra={"path": request.url.path})

    retry_after = _retry_after_seconds(request, exc)
    return JSONResponse(
        status_code=429,
        content={"detail": RATE_LIMIT_MESSAGE},
        headers={"Retry-After": str(retry_after)},
    )
