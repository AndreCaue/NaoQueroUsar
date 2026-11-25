from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings

from .publisher import SocialPublisher
from .types import PublishFailureCategory, PublishResult, SocialPostPayload

_GENERIC_PERMANENT_ERROR = (
    "Não foi possível publicar no Instagram. Revise a integração ou o conteúdo e tente novamente."
)
_TRANSIENT_ERROR = "Falha temporária ao publicar no Instagram. Uma nova tentativa será feita automaticamente."
_AMBIGUOUS_ERROR = (
    "Não foi possível confirmar a publicação no Instagram. Verifique antes de tentar novamente para evitar duplicidade."
)
_RATE_LIMIT_ERROR = (
    "O Instagram bloqueou temporariamente novas publicações por limite da plataforma. "
    "Aguarde e tente novamente mais tarde."
)


def _safe_error_message(msg: str | None) -> str | None:
    if not msg:
        return None
    text = str(msg).strip()
    if not text:
        return None
    lower = text.lower()
    if "access_token" in lower or "token=" in lower:
        return _GENERIC_PERMANENT_ERROR
    return text[:500]


class InstagramPublisher(SocialPublisher):
    """Publisher Instagram via Graph API (2-step: container + publish)."""

    async def publish(self, post: SocialPostPayload | object | None = None) -> PublishResult:
        if not isinstance(post, SocialPostPayload):
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

        provider = str(getattr(post, "provider", "") or "").strip().lower()
        message = (post.message or "").strip()
        image_url = str(getattr(post, "image_url", "") or "").strip()
        ig_user_id = str(getattr(post, "ig_user_id", "") or "").strip()
        page_access_token = str(getattr(post, "page_access_token", "") or "")
        if provider != "instagram" or not message or not image_url or not ig_user_id or not page_access_token:
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

        # Task 2 implements full flow. This stub returns safe permanent failure.
        return PublishResult(
            ok=False,
            category=PublishFailureCategory.permanent,
            error_message=_GENERIC_PERMANENT_ERROR,
        )
