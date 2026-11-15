from __future__ import annotations

from typing import Protocol

from .types import PublishResult, SocialPostPayload


class SocialPublisher(Protocol):
    async def publish(self, post: SocialPostPayload) -> PublishResult: ...
