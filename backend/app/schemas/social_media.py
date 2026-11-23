from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

InstagramImageValidationCode = Literal[
    "missing_image", "invalid_image", "invalid_public_url", "media_not_ready"
]


class InstagramImageValidation(BaseModel):
    valid: bool
    code: InstagramImageValidationCode | None = None
    message: str | None = None


class InstagramMediaPrepareResponse(BaseModel):
    job_id: uuid.UUID
    provider: Literal["instagram"] = "instagram"
    version_hash: str
    template_version: str
    image_url: str | None = None
    mime_type: str = "image/jpeg"
    width: int = 1080
    height: int = 1350
    byte_size: int | None = None
    validation: InstagramImageValidation
    provenance: dict[str, str | int | bool | None] = Field(default_factory=dict)
