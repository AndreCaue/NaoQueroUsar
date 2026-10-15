from fastapi import APIRouter, Depends

from app.deps import require_admin

# Mounted by router.py without an extra prefix, so the route resolves to
# /api/v1/admin/me (ARCHITECTURE.md "Admin (protected)").
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me")
async def me(claims: dict = Depends(require_admin)) -> dict:
    """Return the decoded admin claims behind a valid Bearer token.

    Proof-of-guard for ADMN-03. The full admin review routes (list/approve/
    edit/delete) belong to Phase 5 — do NOT add them here.
    """
    return {
        "sub": claims["sub"],
        "role": claims["role"],
        "iat": claims.get("iat"),
        "exp": claims.get("exp"),
    }
