from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MetaIntegrationAlert(BaseModel):
    code: str
    message: str


class MetaInstagramReadiness(BaseModel):
    ready: bool
    ig_user_id: str | None = None
    ig_username: str | None = None
    state: Literal[
        "ready",
        "not_connected",
        "missing_linkage",
        "missing_permissions",
        "needs_reconnect",
        "unknown",
    ]
    message: str | None = None
    checked_at: datetime | None = None


class MetaIntegrationStatus(BaseModel):
    provider: Literal["facebook"] = "facebook"
    status: Literal["connected", "needs_reconnect", "disconnected"]
    page_id: str | None = None
    page_name: str | None = None
    connected_at: datetime | None = None
    token_checked_at: datetime | None = None
    pending_selection: bool = False
    alert: MetaIntegrationAlert | None = None
    instagram: MetaInstagramReadiness | None = None


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
    instagram: MetaInstagramReadiness | None = None
