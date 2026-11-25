"""add instagram publish reconciliation fields to social_posts

Revision ID: 0008_instagram_publish_reconciliation
Revises: 0007_instagram_review_social_post_publish_enabled
Create Date: 2026-11-25

Phase 31 (PUBL-03/PUBL-04): explicit IG container/publish/reconciliation metadata.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_instagram_publish_reconciliation"
down_revision: str | None = "0007_instagram_review_social_post_publish_enabled"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("social_posts", sa.Column("ig_container_id", sa.String(length=255), nullable=True))
    op.add_column("social_posts", sa.Column("ig_media_id", sa.String(length=255), nullable=True))
    op.add_column("social_posts", sa.Column("ig_permalink", sa.String(length=500), nullable=True))
    op.add_column(
        "social_posts",
        sa.Column(
            "ig_reconciliation_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column("social_posts", sa.Column("ig_reconciliation_state", sa.String(length=64), nullable=True))
    op.add_column(
        "social_posts",
        sa.Column("ig_last_reconciled_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column("social_posts", sa.Column("ig_last_publish_error_code", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("social_posts", "ig_last_publish_error_code")
    op.drop_column("social_posts", "ig_last_reconciled_at")
    op.drop_column("social_posts", "ig_reconciliation_state")
    op.drop_column("social_posts", "ig_reconciliation_required")
    op.drop_column("social_posts", "ig_permalink")
    op.drop_column("social_posts", "ig_media_id")
    op.drop_column("social_posts", "ig_container_id")
