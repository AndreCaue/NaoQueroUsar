"""SOC-01/02/03: modelos ORM, registro Alembic e migração 0004 (cobertura unitária sem DB migrado)."""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa

from app.models import SocialAccount, SocialAccountStatus, SocialPost, SocialPostLog, SocialPostStatus


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_PATH = BACKEND_DIR / "alembic" / "versions" / "0004_social_foundation.py"
ALEMBIC_ENV_PATH = BACKEND_DIR / "alembic" / "env.py"
MODELS_INIT_PATH = BACKEND_DIR / "app" / "models" / "__init__.py"


def _column(model, name: str) -> sa.Column:
    return model.__table__.c[name]


def test_social_account_model_and_enum_soc01() -> None:
    assert SocialAccount.__tablename__ == "social_accounts"
    assert set(SocialAccountStatus.__members__.keys()) == {"connected", "needs_reconnect", "disconnected"}

    required = [
        "id",
        "provider",
        "page_id",
        "page_name",
        "page_access_token",
        "status",
        "connected_at",
        "token_checked_at",
        "created_at",
        "updated_at",
    ]
    for col in required:
        assert col in SocialAccount.__table__.c, col

    assert isinstance(_column(SocialAccount, "page_access_token").type, sa.Text)
    status_col = _column(SocialAccount, "status")
    assert isinstance(status_col.type, sa.Enum)
    assert status_col.type.name == "social_account_status"

    index_names = {idx.name for idx in SocialAccount.__table__.indexes}
    assert "ix_social_accounts_provider_status" in index_names
    assert "ix_social_accounts_page_id" in index_names


def test_social_post_model_constraints_and_enum_soc02() -> None:
    assert SocialPost.__tablename__ == "social_posts"
    assert set(SocialPostStatus.__members__.keys()) == {
        "draft",
        "scheduled",
        "publishing",
        "published",
        "failed",
        "cancelled",
    }

    job_fk = list(SocialPost.__table__.c["job_id"].foreign_keys)[0]
    assert str(job_fk.column) == "jobs.id"
    assert job_fk.ondelete == "CASCADE"

    attempts_col = _column(SocialPost, "attempts")
    assert attempts_col.nullable is False
    assert attempts_col.server_default is not None
    assert "0" in str(attempts_col.server_default.arg)

    uq_names = {c.name for c in SocialPost.__table__.constraints if isinstance(c, sa.UniqueConstraint)}
    assert "uq_social_posts_job_provider" in uq_names

    index_names = {idx.name for idx in SocialPost.__table__.indexes}
    for expected in (
        "ix_social_posts_status",
        "ix_social_posts_scheduled_at",
        "ix_social_posts_next_retry_at",
        "ix_social_posts_job_id",
    ):
        assert expected in index_names


def test_social_post_log_model_soc03() -> None:
    assert SocialPostLog.__tablename__ == "social_post_logs"
    for col in ("attempt_number", "result", "http_status", "error_message", "response_summary", "external_post_id", "created_at"):
        assert col in SocialPostLog.__table__.c, col

    fk = list(SocialPostLog.__table__.c["social_post_id"].foreign_keys)[0]
    assert str(fk.column) == "social_posts.id"
    assert fk.ondelete == "CASCADE"

    index_names = {idx.name for idx in SocialPostLog.__table__.indexes}
    assert "ix_social_post_logs_social_post_id" in index_names
    assert "ix_social_post_logs_created_at" in index_names


def test_social_models_registered_in_init_and_alembic_env() -> None:
    init_text = MODELS_INIT_PATH.read_text(encoding="utf-8")
    env_text = ALEMBIC_ENV_PATH.read_text(encoding="utf-8")
    for name in ("SocialAccount", "SocialPost", "SocialPostLog"):
        assert name in init_text
        assert name in env_text


def test_migration_0004_covers_soc01_02_03_structure() -> None:
    assert MIGRATION_PATH.exists()
    text = MIGRATION_PATH.read_text(encoding="utf-8")

    assert 'revision: str = "0004_social_foundation"' in text
    assert 'down_revision: str | None = "0003_search_text_requirements"' in text
    assert "CREATE TYPE social_account_status AS ENUM ('connected','needs_reconnect','disconnected');" in text
    assert "CREATE TYPE social_post_status AS ENUM ('draft','scheduled','publishing','published','failed','cancelled');" in text
    assert "op.create_table(" in text
    assert '"social_accounts"' in text
    assert '"social_posts"' in text
    assert '"social_post_logs"' in text
    assert 'name="uq_social_posts_job_provider"' in text
    assert 'ondelete="CASCADE"' in text
    assert 'server_default=sa.text("0")' in text or "server_default=sa.text('0')" in text
    assert "def downgrade()" in text
    assert "DROP TYPE IF EXISTS social_post_status;" in text
    assert "DROP TYPE IF EXISTS social_account_status;" in text
    # FK to jobs and to social_posts
    assert '["job_id"], ["jobs.id"]' in text
    assert '["social_post_id"], ["social_posts.id"]' in text
