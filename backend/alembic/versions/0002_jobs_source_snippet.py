"""add jobs.source_snippet (D-08)

Revision ID: 0002_jobs_source_snippet
Revises: 0001_initial_jobs
Create Date: 2026-10-19

Phase 2 stores the extraction snippet per job (D-08): the raw source text
surrounding each extracted candidate, persisted so the admin review flow
(REVW-05, Phase 5) can anchor an edited row to its origin.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_jobs_source_snippet"
down_revision: str | None = "0001_initial_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("source_snippet", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "source_snippet")
