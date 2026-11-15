"""SOC-06: Settings sociais e documentação .env.example (sem DB)."""

from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from app.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ENV_EXAMPLE = Path(__file__).resolve().parents[1] / ".env.example"

REQUIRED_SOCIAL_KEYS = [
    "META_APP_ID",
    "META_APP_SECRET",
    "META_GRAPH_VERSION",
    "META_OAUTH_REDIRECT_URI",
    "SOCIAL_TOKEN_ENCRYPTION_KEY",
    "SOCIAL_WORKER_SECRET",
    "SOCIAL_MAX_ATTEMPTS",
    "SOCIAL_RETRY_DELAYS",
    "SITE_PUBLIC_URL",
]


def _base_settings_kwargs(**overrides):
    data = {
        "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
        "ADMIN_PASSWORD_HASH": "x",
        "JWT_SECRET": "s",
    }
    data.update(overrides)
    return data


def test_settings_social_defaults_and_retry_delay_parser() -> None:
    s = Settings(**_base_settings_kwargs())
    assert s.META_APP_ID == ""
    assert s.META_APP_SECRET == ""
    assert s.META_GRAPH_VERSION == "v21.0"
    assert s.META_OAUTH_REDIRECT_URI == ""
    assert s.SOCIAL_TOKEN_ENCRYPTION_KEY == ""
    assert s.SOCIAL_WORKER_SECRET == ""
    assert s.SOCIAL_MAX_ATTEMPTS == 5
    assert s.SOCIAL_RETRY_DELAYS == "300,900,3600,10800,21600"
    assert s.SITE_PUBLIC_URL == ""
    assert s.social_retry_delays_list == [300, 900, 3600, 10800, 21600]

    s2 = Settings(**_base_settings_kwargs(SOCIAL_RETRY_DELAYS=" 300, 900 ,3600 "))
    assert s2.social_retry_delays_list == [300, 900, 3600]


@pytest.mark.parametrize(
    "overrides,expected_message",
    [
        ({"SITE_PUBLIC_URL": "ftp://example.com"}, "SITE_PUBLIC_URL deve ser uma URL http/https válida"),
        ({"META_OAUTH_REDIRECT_URI": "notaurl"}, "META_OAUTH_REDIRECT_URI deve ser uma URL http/https válida"),
        ({"SOCIAL_MAX_ATTEMPTS": 0}, "SOCIAL_MAX_ATTEMPTS deve ser um inteiro > 0"),
        ({"SOCIAL_RETRY_DELAYS": "300,,900"}, "SOCIAL_RETRY_DELAYS deve conter inteiros > 0 separados por vírgula"),
        ({"SOCIAL_RETRY_DELAYS": "300,-1"}, "SOCIAL_RETRY_DELAYS deve conter inteiros > 0 separados por vírgula"),
        ({"SOCIAL_RETRY_DELAYS": "abc"}, "SOCIAL_RETRY_DELAYS deve conter inteiros > 0 separados por vírgula"),
    ],
)
def test_settings_rejects_invalid_social_values_with_clear_errors(overrides, expected_message) -> None:
    with pytest.raises(Exception) as excinfo:
        Settings(**_base_settings_kwargs(**overrides))
    msg = str(excinfo.value)
    assert expected_message in msg


def test_settings_validates_social_token_encryption_key_format_without_echoing_secret() -> None:
    valid = Fernet.generate_key().decode()
    s = Settings(**_base_settings_kwargs(SOCIAL_TOKEN_ENCRYPTION_KEY=valid))
    assert s.SOCIAL_TOKEN_ENCRYPTION_KEY == valid

    bad = "chave-invalida"
    with pytest.raises(Exception) as excinfo:
        Settings(**_base_settings_kwargs(SOCIAL_TOKEN_ENCRYPTION_KEY=bad))
    err = excinfo.value
    # Our validator raises a clear, safe message (no key echo). Pydantic may wrap it in ValidationError.
    safe_message = "SOCIAL_TOKEN_ENCRYPTION_KEY inválida"
    messages = []
    if hasattr(err, "errors"):
        for e in err.errors():
            messages.append(str(e.get("msg", "")))
            # custom validator message should not include the raw key
            if safe_message in str(e.get("msg", "")):
                assert bad not in str(e.get("msg", ""))
    joined = " | ".join(messages) or str(err)
    assert safe_message in joined or safe_message in str(err)
    # ensure our explicit safe text (if present) does not leak the key
    for m in messages:
        if safe_message in m:
            assert bad not in m


def test_env_example_contains_exact_soc06_social_block_defaults_and_safe_placeholders() -> None:
    text = BACKEND_ENV_EXAMPLE.read_text(encoding="utf-8")
    for key in REQUIRED_SOCIAL_KEYS:
        assert key in text, f"missing {key} in .env.example"

    assert "META_GRAPH_VERSION=v21.0" in text
    assert "SOCIAL_MAX_ATTEMPTS=5" in text
    assert "SOCIAL_RETRY_DELAYS=300,900,3600,10800,21600" in text
    assert "Integração Social / Meta" in text or "Integra" in text
    # pt-BR guidance and backend-only note
    assert "backend" in text.lower()
    assert "SOCIAL_RETRY_DELAYS" in text and "CSV" in text

    # secrets must remain empty placeholders
    for key in ("META_APP_SECRET", "SOCIAL_TOKEN_ENCRYPTION_KEY", "SOCIAL_WORKER_SECRET"):
        assert f"{key}=" in text
        # no obvious filled value after '=' on same line
        for line in text.splitlines():
            if line.startswith(f"{key}="):
                assert line.strip() == f"{key}=", f"{key} must be an empty placeholder"
                break
        else:
            raise AssertionError(f"line for {key} not found")
