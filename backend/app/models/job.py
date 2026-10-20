import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobStatus(str, Enum):
    pending = "pending"
    published = "published"
    needs_review = "needs_review"
    invalid = "invalid"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str | None] = mapped_column(String(150), nullable=True)
    activities: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary: Mapped[str | None] = mapped_column(String(80), nullable=True)
    benefits: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status", native_enum=True),
        nullable=False,
        server_default=text("'pending'"),
    )
    search_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # trecho do texto-fonte da extração (D-08; REVW-05 review aid)
    source_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now() + interval '14 days'"),
    )

    __table_args__ = (
        CheckConstraint(
            "char_length(btrim(title)) > 0",
            name="title_not_blank",
        ),
        CheckConstraint(
            "(contact_email IS NOT NULL AND btrim(contact_email) <> '') "
            "OR (contact_phone IS NOT NULL AND btrim(contact_phone) <> '')",
            name="at_least_one_contact",
        ),
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_expires_at", "expires_at"),
        Index("ix_jobs_created_at", "created_at"),
    )
