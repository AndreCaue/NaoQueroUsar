"""Password hashing and JWT utilities for master-admin auth.

Auth model (Phase 1, decisions D-01..D-03):
- Single master password, stored only as a hash in ``ADMIN_PASSWORD_HASH``.
- JWT (HS256) issued on login and validated once per protected request.
- Turnstile + rate limiting on login are deferred to Phase 3 (D-04).

Implementation note (deviation from the plan's "via passlib"): password
verification uses the ``bcrypt`` library directly instead of ``passlib``.
passlib 1.7.4 is unmaintained and its bcrypt backend probe is incompatible
with bcrypt >= 4.1, which the project's lockfile pins as bcrypt 5.0.0
(the probe passes a >72-byte password that bcrypt 5.x rejects with
``ValueError``, breaking ``CryptContext`` entirely). D-03 allows bcrypt or
argon2; bcrypt is used directly here.

Never log the password, the password hash, or the JWT secret.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()

_ALGORITHM = "HS256"
# bcrypt only considers the first 72 bytes of a password.
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(value: str) -> bytes:
    """UTF-8 encode a password, truncated to bcrypt's 72-byte limit."""
    return value.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` if ``plain`` matches the bcrypt ``hashed`` value."""
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # A malformed/unknown hash must never authenticate anyone.
        return False


def hash_password(plain: str) -> str:
    """Hash a password with bcrypt (used to produce ``ADMIN_PASSWORD_HASH``)."""
    return bcrypt.hashpw(_to_bcrypt_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def authenticate_password(plain: str) -> bool:
    """Verify a plaintext password against the configured ``ADMIN_PASSWORD_HASH``."""
    return verify_password(plain, settings.ADMIN_PASSWORD_HASH)


def create_access_token(subject: str = "admin", role: str = "admin") -> tuple[str, int]:
    """Create a signed HS256 JWT for the master admin.

    Returns ``(token, expires_in_seconds)``. Claims: ``sub``, ``role``, ``iat``,
    ``exp`` (D-01 / OpenCode's Discretion). Uses timezone-aware UTC datetimes.
    """
    now = datetime.now(timezone.utc)
    expires_in = settings.JWT_EXPIRES_IN
    claims = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(claims, settings.JWT_SECRET, algorithm=_ALGORITHM)
    return token, expires_in


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT.

    Pins ``algorithms=["HS256"]`` to prevent algorithm-confusion attacks
    (T-03-02). Raises ``jwt.PyJWTError`` (e.g. ``ExpiredSignatureError``,
    ``InvalidTokenError``) on an invalid/expired/tampered token; callers map
    this to a 401.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM])
