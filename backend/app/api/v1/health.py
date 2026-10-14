from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()

settings = get_settings()


@router.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}
