"""Schemas de draft/geração/aprovação social (Phase 16).

Contratos compartilhados entre serviço de geração, CRUD e endpoints admin.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SocialPublishMode = Literal["publish_now", "schedule"]


class SocialPostDraftRequest(BaseModel):
    """Entrada para gerar/salvar rascunho de post social."""

    text: str | None = None
    publish_mode: SocialPublishMode = "publish_now"
    scheduled_date: str | None = None
    scheduled_time: str | None = None


class SocialPostDraftResponse(BaseModel):
    """Rascunho/estado do post social para UI admin."""

    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    provider: Literal["facebook"] = "facebook"
    status: Literal["draft", "scheduled", "publishing", "published", "failed", "cancelled"]
    text: str
    publish_mode: Literal["publish_now", "schedule"] | None = None
    scheduled_at: datetime | None = None
    origin: Literal["llm", "template_fallback"]
    saved: bool
    frozen: bool
    warning: str | None = None


class SocialApproveOutcome(BaseModel):
    """Resultado do registro social no ato de aprovação da vaga."""

    status: Literal["registered", "skipped", "warning"]
    code: str | None = None
    message: str | None = None
