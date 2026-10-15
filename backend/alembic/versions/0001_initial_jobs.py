"""initial jobs schema: extensions, job_status enum, jobs table, search + indexes

Revision ID: 0001_initial_jobs
Revises:
Create Date: 2026-10-14

Creates the `jobs` data contract for NQU:
- pg_trgm + unaccent extensions and an IMMUTABLE unaccent wrapper
- the 4-value `job_status` enum type (D-09)
- the `jobs` table with the at-least-one-contact CHECK (D-10) and a
  non-empty title CHECK
- timestamptz timestamps with `expires_at = now() + 14 days` (D-12)
- a normalized `search_text` column kept in sync by trigger, with a GIN
  trigram index for accent-insensitive search (D-11)
- indexes for the public list, city filter, search and expiry

No advisory locks are used (Neon loses session context on suspend).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_jobs"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Required extensions (available on Neon Postgres by default).
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")

    # 2. unaccent() is STABLE, not IMMUTABLE, so it cannot be indexed directly.
    #    Wrap it in an IMMUTABLE SQL function we can use in the trigger.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION immutable_unaccent(text)
        RETURNS text
        LANGUAGE sql
        IMMUTABLE
        PARALLEL SAFE
        AS $$ SELECT public.unaccent('public.unaccent', $1) $$;
        """
    )

    # 3. Native enum type for job status (D-09).
    op.execute(
        "CREATE TYPE job_status AS ENUM "
        "('pending', 'published', 'needs_review', 'invalid');"
    )

    # 4. The jobs table.
    op.create_table(
        "jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("company", sa.String(length=150), nullable=True),
        sa.Column("activities", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("salary", sa.String(length=80), nullable=True),
        sa.Column("benefits", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("contact_email", sa.String(length=254), nullable=True),
        sa.Column("contact_phone", sa.String(length=30), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "published",
                "needs_review",
                "invalid",
                name="job_status",
                create_type=False,
            ),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("search_text", sa.Text(), nullable=True),
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
        sa.Column(
            "expires_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now() + interval '14 days'"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(btrim(title)) > 0",
            name="title_not_blank",
        ),
        sa.CheckConstraint(
            "(contact_email IS NOT NULL AND btrim(contact_email) <> '') "
            "OR (contact_phone IS NOT NULL AND btrim(contact_phone) <> '')",
            name="at_least_one_contact",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_jobs"),
    )

    # 5. Keep `search_text` normalized (accent-insensitive) on write (D-11).
    op.execute(
        """
        CREATE OR REPLACE FUNCTION jobs_set_search_text()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.search_text = immutable_unaccent(lower(
                coalesce(NEW.title, '') || ' ' ||
                coalesce(NEW.company, '') || ' ' ||
                coalesce(NEW.activities, '')
            ));
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        "CREATE TRIGGER jobs_search_text_trg "
        "BEFORE INSERT OR UPDATE ON jobs "
        "FOR EACH ROW EXECUTE FUNCTION jobs_set_search_text();"
    )

    # 6. Keep `updated_at` fresh on updates (audit trail, T-02-04).
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        "CREATE TRIGGER jobs_updated_at "
        "BEFORE UPDATE ON jobs "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )

    # 7. Indexes.
    # Non-partial indexes declared on the model metadata (kept in sync).
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_expires_at", "jobs", ["expires_at"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])
    # Partial / composite indexes for the public read paths.
    op.execute(
        "CREATE INDEX idx_jobs_published_created_desc "
        "ON jobs (created_at DESC) WHERE status = 'published';"
    )
    op.execute(
        "CREATE INDEX idx_jobs_city_published "
        "ON jobs (city) WHERE status = 'published';"
    )
    op.execute(
        "CREATE INDEX idx_jobs_search_trgm "
        "ON jobs USING GIN (search_text gin_trgm_ops) WHERE status = 'published';"
    )
    op.execute(
        "CREATE INDEX idx_jobs_status_expires ON jobs (status, expires_at);"
    )


def downgrade() -> None:
    # Reverse order of upgrade(). Extensions are intentionally left in place.
    op.execute("DROP INDEX IF EXISTS idx_jobs_status_expires;")
    op.execute("DROP INDEX IF EXISTS idx_jobs_search_trgm;")
    op.execute("DROP INDEX IF EXISTS idx_jobs_city_published;")
    op.execute("DROP INDEX IF EXISTS idx_jobs_published_created_desc;")
    op.drop_index("ix_jobs_created_at", table_name="jobs")
    op.drop_index("ix_jobs_expires_at", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")

    op.execute("DROP TRIGGER IF EXISTS jobs_updated_at ON jobs;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
    op.execute("DROP TRIGGER IF EXISTS jobs_search_text_trg ON jobs;")
    op.execute("DROP FUNCTION IF EXISTS jobs_set_search_text();")

    op.drop_table("jobs")
    op.execute("DROP TYPE IF EXISTS job_status;")
    op.execute("DROP FUNCTION IF EXISTS immutable_unaccent(text);")
