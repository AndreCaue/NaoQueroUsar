"""add social foundation tables for accounts, posts and logs

Revision ID: 0004_social_foundation
Revises: 0003_search_text_requirements
Create Date: 2026-11-15

SOC-01/02/03: foundation schema for Meta/Facebook social integration.
Creates social_accounts, social_posts, social_post_logs with native enums,
integrity constraints, and operational indexes.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004_social_foundation"
down_revision: str | None = "0003_search_text_requirements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE social_account_status AS ENUM ('connected','needs_reconnect','disconnected');"
    )
    op.execute(
        "CREATE TYPE social_post_status AS ENUM ('draft','scheduled','publishing','published','failed','cancelled');"
    )

    op.create_table(
        "social_accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("page_id", sa.String(length=128), nullable=False),
        sa.Column("page_name", sa.String(length=255), nullable=True),
        sa.Column("page_access_token", sa.Text(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "connected",
                "needs_reconnect",
                "disconnected",
                name="social_account_status",
                create_type=False,
            ),
            server_default=sa.text("'connected'"),
            nullable=False,
        ),
        sa.Column("connected_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("token_checked_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "social_posts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft",
                "scheduled",
                "publishing",
                "published",
                "failed",
                "cancelled",
                name="social_post_status",
                create_type=False,
            ),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column("scheduled_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "attempts",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("next_retry_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("external_post_id", sa.String(length=255), nullable=True),
        sa.Column("published_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
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
        sa.UniqueConstraint("job_id", "provider", name="uq_social_posts_job_provider"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "social_post_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("social_post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "attempt_number",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("external_post_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["social_post_id"], ["social_posts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_social_accounts_provider_status",
        "social_accounts",
        ["provider", "status"],
    )
    op.create_index("ix_social_accounts_page_id", "social_accounts", ["page_id"])
    op.create_index("ix_social_posts_status", "social_posts", ["status"])
    op.create_index("ix_social_posts_scheduled_at", "social_posts", ["scheduled_at"])
    op.create_index("ix_social_posts_next_retry_at", "social_posts", ["next_retry_at"])
    op.create_index("ix_social_posts_job_id", "social_posts", ["job_id"])
    op.create_index(
        "ix_social_post_logs_social_post_id",
        "social_post_logs",
        ["social_post_id"],
    )
    op.create_index(
        "ix_social_post_logs_created_at",
        "social_post_logs",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_social_post_logs_created_at", table_name="social_post_logs")
    op.drop_index("ix_social_post_logs_social_post_id", table_name="social_post_logs")
    op.drop_index("ix_social_posts_job_id", table_name="social_posts")
    op.drop_index("ix_social_posts_next_retry_at", table_name="social_posts")
    op.drop_index("ix_social_posts_scheduled_at", table_name="social_posts")
    op.drop_index("ix_social_posts_status", table_name="social_posts")
    op.drop_index("ix_social_accounts_page_id", table_name="social_accounts")
    op.drop_index("ix_social_accounts_provider_status", table_name="social_accounts")

    op.drop_table("social_post_logs")
    op.drop_table("social_posts")
    op.drop_table("social_accounts")

    op.execute("DROP TYPE IF EXISTS social_post_status;")
    op.execute("DROP TYPE IF EXISTS social_account_status;")
