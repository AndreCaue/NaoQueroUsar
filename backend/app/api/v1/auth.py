from fastapi import APIRouter, HTTPException

from app.core.security import authenticate_password, create_access_token
from app.schemas.auth import LoginRequest, TokenResponse

# Mounted by router.py without an extra prefix, so the route resolves to
# /api/v1/auth/login (ARCHITECTURE.md "Auth (Admin)").
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    """Authenticate the master admin against ``ADMIN_PASSWORD_HASH``.

    Returns a Bearer JWT on success (ADMN-01/ADMN-02); 401 otherwise. The 401
    body carries no token (T-03-04).
    """
    # Turnstile + rate limiting added in Phase 3 (SECR-03). Phase 1 verifies
    # only the password hash (D-04) — do not add them here.
    if not authenticate_password(payload.password):
        raise HTTPException(status_code=401, detail="Senha inválida")

    token, expires_in = create_access_token()
    return TokenResponse(access_token=token, expires_in=expires_in)
