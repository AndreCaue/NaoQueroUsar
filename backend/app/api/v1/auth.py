import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.client_ip import UNKNOWN_IP, resolve_client_ip
from app.core.ratelimit import limiter, login_limit
from app.core.security import authenticate_password, create_access_token
from app.deps import get_turnstile_verifier
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.turnstile import TurnstileVerifier, turnstile_error_detail

# Mounted by router.py without an extra prefix, so the route resolves to
# /api/v1/auth/login (ARCHITECTURE.md "Auth (Admin)").
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit(login_limit)
async def login(
    request: Request,
    payload: LoginRequest,
    verifier: TurnstileVerifier = Depends(get_turnstile_verifier),
) -> TokenResponse:
    """Authenticate the master admin against ``ADMIN_PASSWORD_HASH``.

    Returns a Bearer JWT on success (ADMN-01/ADMN-02); 401 otherwise. The 401
    body carries no token (T-03-04).

    The order of the checks is the contract (D-15/D-17):

    1. **rate limit** — applied by the decorator, per resolved IP (D-06/D-08);
    2. **Siteverify** — the Turnstile token is checked server-side, with the
       ``login`` action binding (a token minted for ``reveal`` is refused);
    3. **password** — only now is ``ADMIN_PASSWORD_HASH`` compared. Without a
       valid token the password is never even looked at;
    4. **200** — the JWT.

    A failed verification is **always** a 403, never a degraded 200 and never
    a 401 (D-18): the copy distinguishes "the challenge was refused" from
    "the verification itself is unavailable" (``turnstile_error_detail``).
    """
    ip = resolve_client_ip(request)
    result = await verifier.verify(
        payload.cf_token,
        None if ip == UNKNOWN_IP else ip,
        expected_action="login",
        idempotency_key=str(uuid.uuid4()),
    )
    if not result.success:
        raise HTTPException(
            status_code=403, detail=turnstile_error_detail(result.error_codes)
        )

    if not authenticate_password(payload.password):
        raise HTTPException(status_code=401, detail="Senha inválida")

    token, expires_in = create_access_token()
    return TokenResponse(access_token=token, expires_in=expires_in)
