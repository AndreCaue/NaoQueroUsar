import uuid
from datetime import datetime

from sqlalchemy import Index, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SocialOAuthPending(Base):
    __tablename__ = "social_oauth_pending"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'facebook'"),
    )
    nonce: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    pages_payload_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_social_oauth_pending_nonce", "nonce", unique=True),
        Index("ix_social_oauth_pending_expires_at", "expires_at"),
        Index("ix_social_oauth_pending_provider", "provider"),
    )
