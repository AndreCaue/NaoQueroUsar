"""Schemas de draft/status/retry/worker social (Phases 16/17).

Contratos compartilhados entre geração, CRUD e endpoints admin.
Campos seguros apenas (sem tokens/segredos/payload bruto).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


SocialPublishMode = Literal["publish_now", "schedule"]
SocialPostStatusLiteral = Literal[
    "draft", "scheduled", "publishing", "published", "failed", "cancelled"
]
SocialPostUiStatusLiteral = Literal[
    "none", "draft", "scheduled", "publishing", "published", "failed", "cancelled"
]


class SocialPostDraftRequest(BaseModel):
    """Entrada para gerar/salvar rascunho de post social."""

    text: str | None = None
    publish_mode: SocialPublishMode = "publish_now"
    scheduled_date: str | None = None
    scheduled_time: str | None = None


class SocialPostDraftResponse(BaseModel):
    """Rascunho/estado do post social para UI admin (Phase 16)."""

    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    provider: Literal["facebook"] = "facebook"
    status: SocialPostStatusLiteral
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


class SocialPostStatusItem(BaseModel):
    """Status operacional seguro do post social por vaga (UI/admin)."""

    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    job_title: str | None = None
    provider: Literal["facebook"] = "facebook"
    status: SocialPostUiStatusLiteral
    status_label: str
    last_error: str | None = None
    published_url: str | None = None
    external_post_id: str | None = None
    attempts: int = 0
    next_retry_at: datetime | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    can_retry: bool = False
    retry_block_reason: str | None = None


class SocialPostStatusListResponse(BaseModel):
    """Listagem simples de status sociais para visão admin."""

    items: list[SocialPostStatusItem]
    total: int


class SocialRetryResponse(BaseModel):
    """Resposta idempotente/segura de retry manual."""

    outcome: Literal["retried", "noop", "not_eligible", "not_found"]
    item: SocialPostStatusItem | None = None
    message: str | None = None


class SocialWorkerResponse(BaseModel):
    """Resumo idempotente do ciclo do worker cron."""

    status: Literal["ok"] = "ok"
    claimed: int = 0
    processed: int = 0
    published: int = 0
    retried: int = 0
    failed_final: int = 0
    skipped: int = 0
    idempotent: int = 0
