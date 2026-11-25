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
    publish_enabled: bool | None = None
    scheduled_date: str | None = None
    scheduled_time: str | None = None


class SocialPostDraftResponse(BaseModel):
    """Rascunho/estado do post social para UI admin (Phase 16)."""

    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    provider: Literal["facebook", "instagram"] = "facebook"
    status: SocialPostStatusLiteral
    text: str
    publish_mode: Literal["publish_now", "schedule"] | None = None
    publish_enabled: bool = True
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
    provider: Literal["facebook", "instagram"] = "facebook"
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
    published_permalink: str | None = None
    ig_container_id: str | None = None
    ig_media_id: str | None = None
    reconciliation_required: bool = False
    reconciliation_state: str | None = None
    ig_last_reconciled_at: datetime | None = None


class SocialPostStatusListResponse(BaseModel):
    """Listagem simples de status sociais para visão admin."""

    items: list[SocialPostStatusItem]
    total: int


class SocialPostLogItem(BaseModel):
    """Item seguro de auditoria do post social (sem tokens/payload bruto)."""

    attempt_number: int = 0
    result: str
    http_status: int | None = None
    error_message: str | None = None
    response_summary: str | None = None
    external_post_id: str | None = None
    created_at: datetime


class SocialPostLogsResponse(BaseModel):
    """Histórico seguro de tentativas/publicação por vaga+provider."""

    job_id: uuid.UUID
    provider: Literal["facebook", "instagram"]
    items: list[SocialPostLogItem]
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
    by_provider: dict[str, dict[str, int]] | None = None
