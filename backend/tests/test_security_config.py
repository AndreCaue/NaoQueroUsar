"""Tests for the fail-closed security configuration (Phase 3 — D-11/D-12/D-06).

Covers:
- ``TURNSTILE_SECRET_KEY`` is mandatory outside ``ENV=dev`` (D-11).
- Cloudflare test keys (``1x``/``2x``/``3x``) are rejected outside ``ENV=dev``
  (D-12), unless the temporary escape hatch ``ALLOW_TEST_TURNSTILE=true`` is
  explicitly set (temporary deviation — see ``docs/DEPLOY.md``).
- In ``ENV=dev`` the empty secret falls back to Cloudflare's public
  always-pass key, and an explicitly provided key is used as-is.
- Rate-limit budgets are env-configurable with safe defaults (D-06).

No test touches the real ``.env`` file nor the database: every ``Settings``
instance is built with ``_env_file=None`` and explicit init kwargs (init
kwargs have the highest priority in pydantic-settings).
"""

import logging

import pytest
from pydantic import ValidationError

from app.core.config import DEV_TURNSTILE_SECRET, Settings

# Cloudflare's public test secrets (35 chars: prefix "Nx" + 31 chars + "AA").
KEY_ALWAYS_PASS = "1x0000000000000000000000000000000AA"
KEY_ALWAYS_FAIL = "2x0000000000000000000000000000000AA"
KEY_TIMEOUT = "3x0000000000000000000000000000000AA"


def _settings(**kwargs) -> Settings:
    """Build a ``Settings`` isolated from the local ``.env`` file."""
    base = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/nqu_test",
        "ADMIN_PASSWORD_HASH": "not-a-real-hash",
        "JWT_SECRET": "not-a-real-secret",
        "_env_file": None,
    }
    base.update(kwargs)
    return Settings(**base)


def test_dev_turnstile_secret_is_35_chars():
    """The always-pass key must have the real Cloudflare length (35 chars).

    A shorter key (e.g. ``{30}`` in the blocker regex) would let the
    always-pass key slip through the prod validator (D-12).
    """
    assert len(DEV_TURNSTILE_SECRET) == 35
    assert DEV_TURNSTILE_SECRET == KEY_ALWAYS_PASS


def test_prod_requires_turnstile_secret_key():
    """D-11: outside dev an empty secret must break the startup."""
    with pytest.raises(ValidationError, match="TURNSTILE_SECRET_KEY"):
        _settings(ENV="prod", TURNSTILE_SECRET_KEY="")


@pytest.mark.parametrize("test_key", [KEY_ALWAYS_PASS, KEY_ALWAYS_FAIL, KEY_TIMEOUT])
def test_prod_rejects_cloudflare_test_keys(test_key: str):
    """D-12: known Cloudflare test keys must break the startup outside dev."""
    with pytest.raises(ValidationError, match="TURNSTILE_SECRET_KEY|chave de teste"):
        _settings(ENV="prod", TURNSTILE_SECRET_KEY=test_key)


def test_prod_rejects_test_keys_when_override_is_off():
    """The escape hatch is opt-in: ``ALLOW_TEST_TURNSTILE=False`` keeps D-12."""
    with pytest.raises(ValidationError, match="chave de teste"):
        _settings(
            ENV="prod",
            TURNSTILE_SECRET_KEY=KEY_ALWAYS_PASS,
            ALLOW_TEST_TURNSTILE=False,
        )


def test_prod_accepts_test_key_with_explicit_override(caplog):
    """Desvio temporário: com ``ALLOW_TEST_TURNSTILE=True`` o boot prossegue.

    O modo continua ``test`` (o gate e o /health não escondem o desvio) e o
    boot emite um WARN explícito para o operador.
    """
    with caplog.at_level(logging.WARNING, logger="app.core.config"):
        settings = _settings(
            ENV="prod",
            TURNSTILE_SECRET_KEY=KEY_ALWAYS_PASS,
            ALLOW_TEST_TURNSTILE=True,
        )

    assert settings.effective_turnstile_secret == KEY_ALWAYS_PASS
    assert settings.turnstile_mode == "test"
    assert settings.ALLOW_TEST_TURNSTILE is True
    assert any("ALLOW_TEST_TURNSTILE" in record.message for record in caplog.records)


def test_prod_override_does_not_excuse_a_missing_secret():
    """D-11 is untouched: the override only relaxes the test-key check."""
    with pytest.raises(ValidationError, match="TURNSTILE_SECRET_KEY"):
        _settings(ENV="prod", TURNSTILE_SECRET_KEY="", ALLOW_TEST_TURNSTILE=True)


def test_prod_override_keeps_live_mode_for_a_real_secret():
    """A real secret is still classified as ``live`` even with the flag on."""
    settings = _settings(
        ENV="prod", TURNSTILE_SECRET_KEY="z" * 35, ALLOW_TEST_TURNSTILE=True
    )
    assert settings.turnstile_mode == "live"


def test_prod_accepts_non_test_secret():
    """A 35-char secret that is not a known test key is accepted."""
    settings = _settings(ENV="prod", TURNSTILE_SECRET_KEY="z" * 35)
    assert settings.TURNSTILE_SECRET_KEY == "z" * 35


def test_dev_falls_back_to_always_pass_secret():
    """D-12: in dev the empty secret falls back to the public always-pass key."""
    settings = _settings(ENV="dev", TURNSTILE_SECRET_KEY="")
    assert settings.effective_turnstile_secret == DEV_TURNSTILE_SECRET


def test_dev_uses_explicitly_configured_secret():
    """An explicitly configured dev secret wins over the always-pass default."""
    settings = _settings(ENV="dev", TURNSTILE_SECRET_KEY=KEY_ALWAYS_PASS)
    assert settings.effective_turnstile_secret == KEY_ALWAYS_PASS


def test_rate_limit_defaults():
    """D-06: the rate-limit budgets are configurable and default to the plan values."""
    settings = _settings()
    assert settings.REVEAL_RATE_LIMIT == "10/minute"
    assert settings.LOGIN_RATE_LIMIT == "5/minute"
