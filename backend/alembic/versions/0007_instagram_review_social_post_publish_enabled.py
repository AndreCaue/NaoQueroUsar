"""add publish_enabled to social_posts for Instagram review

Revision ID: 0007_instagram_review_social_post_publish_enabled
Revises: 0006_ig_readiness_media_foundation
Create Date: 2026-11-25

Phase 30: per-job Instagram publish toggle persistence (D-04).
Existing rows default to enabled for backward-compatible Facebook behavior.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_instagram_review_social_post_publish_enabled"
down_revision: str | None = "0006_ig_readiness_media_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "social_posts",
        sa.Column(
            "publish_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("social_posts", "publish_enabled")
