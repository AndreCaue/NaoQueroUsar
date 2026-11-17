"""Schemas do chat-search público (Phase 20, API-01..03)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings
from app.schemas.job import JobPublic
from app.services.intent.schema import IntentContract


def _max_message_chars() -> int:
    """Return configured chat message max length with a safe fallback."""
    try:
        return int(get_settings().CHAT_SEARCH_MAX_MESSAGE_CHARS)
    except Exception:
        return 400


class ChatSearchRequest(BaseModel):
    """Entrada pública não confiável para busca por linguagem natural."""

    message: str = Field(min_length=1)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("message")
    @classmethod
    def _validate_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Mensagem é obrigatória")
        max_chars = _max_message_chars()
        if len(stripped) > max_chars:
            raise ValueError("Mensagem excede o tamanho máximo permitido")
        return stripped


class ChatSearchResults(BaseModel):
    """Resultados pagináveis determinísticos, sem contato."""

    items: list[JobPublic]
    page: int
    limit: int
    total: int


class ChatSearchResponse(BaseModel):
    """Envelope server-authoritative: interpretação + resultados."""

    interpretation: IntentContract
    results: ChatSearchResults
