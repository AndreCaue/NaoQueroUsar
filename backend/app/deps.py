from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
import secrets

from app.core.config import get_settings
from app.core.ratelimit import limiter
from app.core.security import decode_access_token
from app.db.session import get_session
from app.services.turnstile import TurnstileVerifier

__all__ = [
    "get_session",
    "get_settings",
    "require_admin",
    "require_cron_secret",
    "bearer_scheme",
    "get_turnstile_verifier",
]

# auto_error=False so a missing header reaches our handler and yields a
# controlled 401 with a WWW-Authenticate challenge (T-03-03).
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """Validate the ``Authorization: Bearer <token>`` header.

    Returns the decoded JWT claims, or raises 401 when the header is
    missing/malformed, the token is invalid/expired/tampered, or the claims do
    not identify the master admin (T-03-02, T-03-03).
    """
    if creds is None or creds.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        claims = decode_access_token(creds.credentials)
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc

    if claims.get("sub") != "admin" or claims.get("role") != "admin":
        raise _unauthorized()

    return claims


def _cron_unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Não autorizado")


@limiter.limit("10/minute")
async def require_cron_secret(
    request: Request,
    x_cron_secret: str | None = Header(default=None, alias="X-Cron-Secret"),
) -> None:
    """Validate ``X-Cron-Secret`` against ``Settings.CRON_SECRET`` (T-06-01).

    Fails CLOSED in both directions:

    - no ``CRON_SECRET`` in the environment → 503, i.e. the manual trigger is
      disabled. A missing variable must never turn into an open hard-delete
      endpoint;
    - missing or wrong header → 401. The comparison uses
      ``secrets.compare_digest`` so the value cannot be recovered byte by byte
      from response timing.

    Rate-limited per resolved IP (10/minute, IN-05): the gate is a static
    bearer, so without a throttle an unauthenticated client could probe
    ``X-Cron-Secret`` at full speed. The limit lives on the dependency (not
    on the route handler) because FastAPI resolves dependencies first —
    decorating the handler would never see requests that short-circuit
    here with 401/503. Under the limit the 503/401 semantics are unchanged;
    over the limit the shared 429 (pt-BR, ``Retry-After``) is returned.
    """
    settings = get_settings()
    expected = settings.CRON_SECRET.strip()

    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Expiração manual não configurada",
        )

    provided = (x_cron_secret or "").strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise _cron_unauthorized()


async def get_turnstile_verifier() -> TurnstileVerifier:
    """Build the Turnstile verifier used by the protected routes.

    It is a dependency (and not a module-level singleton) so the tests can
    replace it through ``app.dependency_overrides`` and run completely
    offline — no request ever reaches Cloudflare from the test suite.

    Action binding is strictly enforced only in ``live`` mode. Cloudflare's
    public test keys do not echo the ``action`` in Siteverify responses, so
    we relax the check in ``test``/``dev`` to keep local/browser verification
    functional (D-12 already blocks test keys outside dev).
    """
    settings = get_settings()
    return TurnstileVerifier(
        secret=settings.effective_turnstile_secret,
        timeout_seconds=settings.TURNSTILE_TIMEOUT_SECONDS,
        enforce_action=(settings.turnstile_mode == "live"),
    )
