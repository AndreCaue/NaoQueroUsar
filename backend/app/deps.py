from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_session
from app.services.turnstile import TurnstileVerifier

__all__ = [
    "get_session",
    "get_settings",
    "require_admin",
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


async def get_turnstile_verifier() -> TurnstileVerifier:
    """Build the Turnstile verifier used by the protected routes.

    It is a dependency (and not a module-level singleton) so the tests can
    replace it through ``app.dependency_overrides`` and run completely
    offline — no request ever reaches Cloudflare from the test suite.
    """
    settings = get_settings()
    return TurnstileVerifier(
        secret=settings.effective_turnstile_secret,
        timeout_seconds=settings.TURNSTILE_TIMEOUT_SECONDS,
    )
