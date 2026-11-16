from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PublishFailureCategory(str, Enum):
    transient = "transient"
    permanent = "permanent"
    unknown = "unknown"
    ambiguous = "ambiguous"


@dataclass(frozen=True)
class PublishResult:
    ok: bool
    external_post_id: str | None = None
    category: PublishFailureCategory | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class SocialPostPayload:
    job_id: str
    provider: str
    message: str
    link: str | None = None
    page_id: str | None = None
    page_access_token: str | None = None
