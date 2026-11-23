import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SAEnum, Index, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SocialAccountStatus(str, Enum):
    connected = "connected"
    needs_reconnect = "needs_reconnect"
    disconnected = "disconnected"


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    page_id: Mapped[str] = mapped_column(String(128), nullable=False)
    page_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SocialAccountStatus] = mapped_column(
        SAEnum(SocialAccountStatus, name="social_account_status", native_enum=True),
        nullable=False,
        server_default=text("'connected'"),
    )
    connected_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    token_checked_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    # IG readiness is additive; Facebook connection status remains authoritative for Facebook.
    ig_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ig_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ig_readiness_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ig_readiness_checked_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    ig_readiness_last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ig_readiness_last_error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_social_accounts_provider_status", "provider", "status"),
        Index("ix_social_accounts_page_id", "page_id"),
    )
