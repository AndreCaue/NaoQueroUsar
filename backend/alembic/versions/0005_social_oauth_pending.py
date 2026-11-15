"""add social oauth pending selection table

Revision ID: 0005_social_oauth_pending
Revises: 0004_social_foundation
Create Date: 2026-11-15

Transient backend-mediated pending page selection for Meta OAuth (D-08).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_social_oauth_pending"
down_revision: str | None = "0004_social_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "social_oauth_pending",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(length=32),
            server_default=sa.text("'facebook'"),
            nullable=False,
        ),
        sa.Column("nonce", sa.String(length=64), nullable=False),
        sa.Column("pages_payload_encrypted", sa.Text(), nullable=False),
        sa.Column("expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("consumed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_social_oauth_pending_nonce",
        "social_oauth_pending",
        ["nonce"],
        unique=True,
    )
    op.create_index(
        "ix_social_oauth_pending_expires_at",
        "social_oauth_pending",
        ["expires_at"],
    )
    op.create_index(
        "ix_social_oauth_pending_provider",
        "social_oauth_pending",
        ["provider"],
    )


def downgrade() -> None:
    op.drop_index("ix_social_oauth_pending_provider", table_name="social_oauth_pending")
    op.drop_index("ix_social_oauth_pending_expires_at", table_name="social_oauth_pending")
    op.drop_index("ix_social_oauth_pending_nonce", table_name="social_oauth_pending")
    op.drop_table("social_oauth_pending")
