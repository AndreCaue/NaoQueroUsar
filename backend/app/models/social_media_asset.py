import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SocialMediaAsset(Base):
    """Durable, rebuildable IG media asset keyed by job/provider/version hash.

    D-09: Postgres durable bytes are acceptable at v1.5 scale; the backend public
    endpoint is the primary serving surface, not external R2/S3/CDN blob infra.
    """

    __tablename__ = "social_media_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sql_text("gen_random_uuid()"),
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=sql_text("'instagram'"),
    )
    version_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    template_version: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        server_default=sql_text("'image/jpeg'"),
    )
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    image_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    provenance_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sql_text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sql_text("now()"),
    )

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "provider",
            "version_hash",
            name="uq_social_media_assets_job_provider_version",
        ),
        Index("ix_social_media_assets_job_provider", "job_id", "provider"),
    )
