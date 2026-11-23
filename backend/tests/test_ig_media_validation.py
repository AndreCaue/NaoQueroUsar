"""IMAG-01: Instagram image validation/preparation contract (pt-BR, IG-only blocking)."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.schemas.social_media import InstagramMediaPrepareResponse
from app.services.social import image_media
from app.services.social.image_media import (
    MSG_INVALID,
    MSG_INVALID_PUBLIC_URL,
    MSG_MISSING,
    prepare_instagram_media,
)


@pytest.mark.asyncio
async def test_prepare_returns_invalid_public_url_with_ptbr_message(db_session, seed_published_job, monkeypatch):
    settings = SimpleNamespace(MEDIA_PUBLIC_BASE_URL="http://localhost:8000")
    monkeypatch.setattr(image_media, "_generate_asset_bytes", lambda job: _async_bytes(b"fake"))

    resp = await prepare_instagram_media(db_session, seed_published_job.id, settings)

    assert isinstance(resp, InstagramMediaPrepareResponse)
    assert resp.validation.valid is False
    assert resp.validation.code == "invalid_public_url"
    assert resp.validation.message == MSG_INVALID_PUBLIC_URL
    assert resp.image_url is None
    assert resp.provenance.get("generated_from") == "job"
    assert "contact_email" not in resp.provenance
    assert "contact_phone" not in resp.provenance


async def _async_bytes(data: bytes):
    return data


@pytest.mark.asyncio
async def test_prepare_missing_job_returns_missing_image_message(db_session):
    settings = SimpleNamespace(MEDIA_PUBLIC_BASE_URL="https://media.example.com")
    missing_id = uuid.uuid4()

    resp = await prepare_instagram_media(db_session, missing_id, settings)

    assert resp.validation.valid is False
    assert resp.validation.code == "missing_image"
    assert resp.validation.message == MSG_MISSING
    assert resp.validation.message == "Imagem ausente para Instagram. Gere o card da vaga antes de publicar no Instagram."
    assert resp.job_id == missing_id


@pytest.mark.asyncio
async def test_prepare_invalid_image_maps_to_invalid_image(db_session, seed_published_job, monkeypatch):
    settings = SimpleNamespace(MEDIA_PUBLIC_BASE_URL="https://media.example.com")

    async def _boom(job):
        raise FileNotFoundError("Bundled IG card fonts missing; rendering requires repo-bundled fonts only: /x.ttf")

    monkeypatch.setattr(image_media, "_generate_asset_bytes", _boom)

    resp = await prepare_instagram_media(db_session, seed_published_job.id, settings)

    assert resp.validation.valid is False
    assert resp.validation.code == "invalid_image"
    assert resp.validation.message == MSG_INVALID
    assert resp.validation.message.startswith("Imagem inválida para Instagram")


@pytest.mark.asyncio
async def test_prepare_ready_image_has_valid_contract(db_session, seed_published_job):
    settings = SimpleNamespace(MEDIA_PUBLIC_BASE_URL="https://media.example.com")

    resp = await prepare_instagram_media(db_session, seed_published_job.id, settings)
    await db_session.commit()

    assert resp.validation.valid is True
    assert resp.validation.code is None
    assert resp.validation.message == "Imagem pronta para publicação no Instagram."
    assert resp.image_url is not None
    assert resp.image_url.startswith("https://media.example.com/api/v1/public/ig-media/")
    assert resp.version_hash
    assert len(resp.version_hash) == 16
    assert resp.byte_size is not None and resp.byte_size > 0
    assert resp.provenance["template_version"] == "ig-card-v1"
    assert "contact" not in str(resp.provenance).lower()