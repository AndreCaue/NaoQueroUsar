"""include requirements in jobs.search_text and backfill

Revision ID: 0003_search_text_requirements
Revises: 0002_jobs_source_snippet
Create Date: 2026-10-26

SRCH-01: ``q`` searches title + company + activities + requirements (D-03/D-04).
Migration ``0001`` built ``jobs_set_search_text()`` from the first three fields;
this revision replaces the function with the same body plus
``coalesce(NEW.requirements, '')`` and backfills every existing row.

``CREATE OR REPLACE FUNCTION`` keeps the same function name, so the existing
``jobs_search_text_trg`` trigger keeps binding — the trigger is never dropped.

The backfill disables **only** ``jobs_updated_at`` (a BEFORE UPDATE trigger) so
rewriting ``search_text`` does not fake an edit on every job. ``DISABLE
TRIGGER`` is transactional in Postgres: the trigger is re-enabled inside the
same migration transaction and a failed upgrade rolls everything back.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_search_text_requirements"
down_revision: str | None = "0002_jobs_source_snippet"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_FUNCTION_WITH_REQUIREMENTS = """
CREATE OR REPLACE FUNCTION jobs_set_search_text()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.search_text = immutable_unaccent(lower(
        coalesce(NEW.title, '') || ' ' ||
        coalesce(NEW.company, '') || ' ' ||
        coalesce(NEW.activities, '') || ' ' ||
        coalesce(NEW.requirements, '')
    ));
    RETURN NEW;
END;
$$;
"""

# Exact body created by 0001 — restored by downgrade.
_FUNCTION_WITHOUT_REQUIREMENTS = """
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

_BACKFILL = """
UPDATE jobs SET search_text = immutable_unaccent(lower(
    coalesce(title, '') || ' ' ||
    coalesce(company, '') || ' ' ||
    coalesce(activities, '') || ' ' ||
    coalesce(requirements, '')
));
"""


def upgrade() -> None:
    op.execute(_FUNCTION_WITH_REQUIREMENTS)
    op.execute("ALTER TABLE jobs DISABLE TRIGGER jobs_updated_at;")
    op.execute(_BACKFILL)
    op.execute("ALTER TABLE jobs ENABLE TRIGGER jobs_updated_at;")


def downgrade() -> None:
    op.execute(_FUNCTION_WITHOUT_REQUIREMENTS)
    # Requirements terms already written into ``search_text`` are left in
    # place: a superset is harmless for matching, and re-running the old
    # backfill would rewrite every row for no behavioural gain.
