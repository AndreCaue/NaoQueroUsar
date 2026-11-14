"""Production CORS contract (criterion 6 — T-09-13).

The app must echo the configured origin exactly, refuse to echo a
foreign origin, allow the report POST preflight, and refuse to boot
outside dev with an unsafe CORS_ORIGINS value.
"""

import uuid

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def _settings(**kwargs) -> Settings:
    base = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/nqu_test",
        "ADMIN_PASSWORD_HASH": "not-a-real-hash",
        "JWT_SECRET": "not-a-real-secret",
        "_env_file": None,
    }
    base.update(kwargs)
    return Settings(**base)


def _config_origin() -> str:
    """Return the origin the app was built with (from real .env)."""
    return get_settings().cors_origins_list[0]


async def test_configured_origin_is_echoed_exactly(client):
    resp = await client.get(
        "/api/v1/public/jobs",
        params={"limit": 1},
        headers={"Origin": _config_origin()},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == _config_origin()


async def test_foreign_origin_is_not_echoed(client):
    resp = await client.get(
        "/api/v1/public/jobs",
        params={"limit": 1},
        headers={"Origin": "https://evil.example"},
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers


async def test_preflight_allows_report_post(client):
    resp = await client.options(
        f"/api/v1/public/jobs/{uuid.uuid4()}/report",
        headers={
            "Origin": _config_origin(),
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == _config_origin()
    assert "POST" in resp.headers.get("access-control-allow-methods", "").upper()


@pytest.mark.parametrize(
    "origin",
    ["", "*", "https://empreganoix.vercel.app/", "empreganoix.vercel.app"],
)
def test_prod_rejects_unsafe_cors_origins(origin: str):
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        _settings(
            ENV="prod",
            CORS_ORIGINS=origin,
            TURNSTILE_SECRET_KEY="z" * 35,
        )


def test_prod_accepts_exact_https_origin_and_strips_spaces():
    settings = _settings(
        ENV="prod",
        CORS_ORIGINS=" https://empreganoix.vercel.app , https://admin.example ",
        TURNSTILE_SECRET_KEY="z" * 35,
    )
    assert settings.cors_origins_list == [
        "https://empreganoix.vercel.app",
        "https://admin.example",
    ]


def test_dev_still_accepts_localhost_default():
    settings = _settings(ENV="dev")
    assert settings.cors_origins_list == ["http://localhost:3000"]