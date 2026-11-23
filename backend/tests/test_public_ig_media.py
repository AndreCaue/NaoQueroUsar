"""IMAG-03/IMAG-01: public IG media endpoint and admin prepare contract."""

from __future__ import annotations

import uuid

import pytest

from app.core.config import get_settings

VALID_CF_TOKEN = "token-de-teste"


async def _login(client, admin_password: str = "test-password") -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_public_ig_media_serves_versioned_jpeg_without_auth(
    client, db_session, seed_published_job, admin_password, monkeypatch
):
    monkeypatch.setattr(get_settings(), "MEDIA_PUBLIC_BASE_URL", "https://media.example.com")
    token = await _login(client, admin_password)

    prepare = await client.post(
        f"/api/v1/admin/jobs/{seed_published_job.id}/instagram/media/prepare",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert prepare.status_code == 200, prepare.text
    body = prepare.json()
    assert body["validation"]["valid"] is True
    version = body["version_hash"]
    assert len(version) == 16

    resp = await client.get(f"/api/v1/public/ig-media/{seed_published_job.id}/{version}.jpg")
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("image/jpeg")
    assert resp.headers.get("cache-control") == "public, max-age=31536000, immutable"
    assert resp.content.startswith(b"\xff\xd8\xff")
    assert len(resp.content) > 100

    # No auth/token leakage
    headers_text = " ".join([f"{k}:{v}" for k, v in resp.headers.items()]).lower()
    assert "authorization" not in headers_text
    assert "bearer" not in headers_text
    assert "set-cookie" not in headers_text
    assert b"access_token" not in resp.content.lower()
    assert b"secret" not in resp.content.lower()


@pytest.mark.asyncio
async def test_public_ig_media_returns_404_for_bad_or_unknown_version(client, seed_published_job):
    bad = await client.get(f"/api/v1/public/ig-media/{seed_published_job.id}/not-a-hash.jpg")
    assert bad.status_code == 404

    unknown = await client.get(f"/api/v1/public/ig-media/{seed_published_job.id}/0123456789abcdef.jpg")
    assert unknown.status_code == 404


@pytest.mark.asyncio
async def test_public_ig_media_unknown_job_returns_404(client):
    missing_job = uuid.uuid4()
    resp = await client.get(f"/api/v1/public/ig-media/{missing_job}/0123456789abcdef.jpg")
    assert resp.status_code == 404