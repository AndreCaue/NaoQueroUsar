from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MetaIntegrationAlert(BaseModel):
    code: str
    message: str


class MetaIntegrationStatus(BaseModel):
    provider: Literal["facebook"] = "facebook"
    status: Literal["connected", "needs_reconnect", "disconnected"]
    page_id: str | None = None
    page_name: str | None = None
    connected_at: datetime | None = None
    token_checked_at: datetime | None = None
    pending_selection: bool = False
    alert: MetaIntegrationAlert | None = None


class MetaPendingPage(BaseModel):
    page_id: str
    page_name: str | None = None


class MetaPendingSelectionResponse(BaseModel):
    pending: bool
    pages: list[MetaPendingPage] = Field(default_factory=list)


class MetaSelectPageRequest(BaseModel):
    pending_nonce: str = Field(min_length=1)
    page_id: str = Field(min_length=1)


class MetaOAuthStartResponse(BaseModel):
    redirect_url: str


class MetaActionResponse(BaseModel):
    status: Literal["connected", "needs_reconnect", "disconnected"]
    message: str | None = None
    pending_selection: bool | None = None
