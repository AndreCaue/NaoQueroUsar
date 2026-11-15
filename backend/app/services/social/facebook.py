from __future__ import annotations

from .publisher import SocialPublisher
from .types import PublishFailureCategory, PublishResult, SocialPostPayload


class FacebookPublisher(SocialPublisher):
    """Stub explícito do publisher do Facebook.

    Estrutura pronta para a Fase 17; nesta fase não realiza chamadas externas/HTTP.
    """

    async def publish(self, post: SocialPostPayload | object | None = None) -> PublishResult:
        return PublishResult(
            ok=False,
            external_post_id=None,
            category=PublishFailureCategory.unknown,
            error_message="publicação Facebook não implementada na Fase 14 (stub)",
        )
