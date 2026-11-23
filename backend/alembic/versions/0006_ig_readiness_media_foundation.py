"""add instagram readiness fields and social media assets

Revision ID: 0006_ig_readiness_media_foundation
Revises: 0005_social_oauth_pending
Create Date: 2026-11-23

Phase 29: additive IG readiness on social_accounts and durable IG media assets.
IG readiness is additive; Facebook connection status remains authoritative for Facebook.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006_ig_readiness_media_foundation"
down_revision: str | None = "0005_social_oauth_pending"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("social_accounts", sa.Column("ig_user_id", sa.String(length=64), nullable=True))
    op.add_column("social_accounts", sa.Column("ig_username", sa.String(length=255), nullable=True))
    op.add_column("social_accounts", sa.Column("ig_readiness_state", sa.String(length=32), nullable=True))
    op.add_column(
        "social_accounts",
        sa.Column("ig_readiness_checked_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "social_accounts",
        sa.Column("ig_readiness_last_error_code", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "social_accounts",
        sa.Column("ig_readiness_last_error_message", sa.String(length=500), nullable=True),
    )

    op.create_table(
        "social_media_assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "provider",
            sa.String(length=32),
            server_default=sa.text("'instagram'"),
            nullable=False,
        ),
        sa.Column("version_hash", sa.String(length=64), nullable=False),
        sa.Column("template_version", sa.String(length=64), nullable=False),
        sa.Column(
            "mime_type",
            sa.String(length=64),
            server_default=sa.text("'image/jpeg'"),
            nullable=False,
        ),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("image_bytes", postgresql.BYTEA(), nullable=False),
        sa.Column("provenance_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "job_id",
            "provider",
            "version_hash",
            name="uq_social_media_assets_job_provider_version",
        ),
    )
    op.create_index(
        "ix_social_media_assets_job_provider",
        "social_media_assets",
        ["job_id", "provider"],
    )


def downgrade() -> None:
    op.drop_index("ix_social_media_assets_job_provider", table_name="social_media_assets")
    op.drop_table("social_media_assets")

    op.drop_column("social_accounts", "ig_readiness_last_error_message")
    op.drop_column("social_accounts", "ig_readiness_last_error_code")
    op.drop_column("social_accounts", "ig_readiness_checked_at")
    op.drop_column("social_accounts", "ig_readiness_state")
    op.drop_column("social_accounts", "ig_username")
    op.drop_column("social_accounts", "ig_user_id")
