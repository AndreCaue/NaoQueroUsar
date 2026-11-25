"""Integration/API tests for admin Instagram social draft/review flow (Phase 30, REVW-01..04).

Covers IG draft CRUD isolation, caption limit, D-07 image validation guard, and
approve guard behavior while preserving Facebook/site independence.
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.job import Job, JobStatus
from app.models.social_post import SocialPost, SocialPostStatus

VALID_CF_TOKEN = "token-de-teste"


async def _login(client, admin_password="test-password"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _seed_job(db_session, **overrides) -> Job:
    data = dict(
        title="Vaga Instagram",
        company="Empresa Confidencial",
        activities="Atuar no atendimento",
        requirements=None,
        salary="R$ 2.000",
        benefits="VT",
        city="São Paulo",
        contact_email="rh@empresa.com",
        contact_phone="+55 11 99999-0000",
        status=JobStatus.pending,
        source_snippet="fonte",
    )
    data.update(overrides)
    job = Job(**data)
    db_session.add(job)
    await db_session.flush()
    return job


async def _get_social_post(db_session, job_id: uuid.UUID, provider: str) -> SocialPost | None:
    stmt = select(SocialPost).where(
        SocialPost.job_id == job_id, SocialPost.provider == provider
    )
    return await db_session.scalar(stmt)


def _valid_media_result():
    return SimpleNamespace(
        validation=SimpleNamespace(
            valid=True,
            code=None,
            message="Imagem pronta para publicação no Instagram.",
        )
    )


def _invalid_media_result(message="Imagem inválida para Instagram"):
    return SimpleNamespace(
        validation=SimpleNamespace(
            valid=False,
            code="invalid_image",
            message=message,
        )
    )


@pytest.mark.asyncio
async def test_instagram_social_post_get_generate_save_isolated_from_facebook(
    client, db_session, admin_password, monkeypatch
):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()

    async def fake_prepare_ok(session, job_id, settings):
        return _valid_media_result()

    monkeypatch.setattr("app.api.v1.admin.prepare_instagram_media", fake_prepare_ok)

    resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}/instagram/social-post",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404

    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/instagram/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "instagram"
    assert body["publish_enabled"] is False
    assert "link na bio" in body["text"]
    assert "#vagas" in body["text"]
    assert "#emprego" in body["text"]
    assert "#oportunidade" in body["text"]

    caption = "  Legenda IG manual sem link  "
    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}/instagram/social-post",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": caption,
            "publish_mode": "publish_now",
            "publish_enabled": True,
        },
    )
    assert resp.status_code == 200, resp.text
    saved = resp.json()
    assert saved["provider"] == "instagram"
    assert saved["publish_enabled"] is True
    assert saved["text"] == caption.strip()
    assert "http://" not in saved["text"]
    assert "https://" not in saved["text"]

    async def fake_generate_fb(job_arg, settings=None, client=None):
        return SimpleNamespace(
            text="Rascunho Facebook original",
            origin="llm",
            warning=None,
        )

    monkeypatch.setattr("app.api.v1.admin.generate_draft_for_job", fake_generate_fb)
    fb_resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert fb_resp.status_code == 200, fb_resp.text
    fb_body = fb_resp.json()
    assert fb_body["provider"] == "facebook"
    assert fb_body["text"] == "Rascunho Facebook original"

    ig_post = await _get_social_post(db_session, job.id, "instagram")
    fb_post = await _get_social_post(db_session, job.id, "facebook")
    assert ig_post is not None
    assert fb_post is not None
    assert ig_post.text == caption.strip()
    assert fb_post.text == "Rascunho Facebook original"


@pytest.mark.asyncio
async def test_instagram_caption_over_2200_rejected(client, db_session, admin_password):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)

    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}/instagram/social-post",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "x" * 2201,
            "publish_mode": "publish_now",
            "publish_enabled": False,
        },
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Legenda do Instagram deve ter no máximo 2200 caracteres."


@pytest.mark.asyncio
async def test_instagram_enabled_requires_valid_image_on_save(
    client, db_session, admin_password, monkeypatch
):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()

    async def fake_prepare_invalid(session, job_id, settings):
        return _invalid_media_result("Imagem inválida para Instagram")

    monkeypatch.setattr("app.api.v1.admin.prepare_instagram_media", fake_prepare_invalid)

    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}/instagram/social-post",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "Legenda curta",
            "publish_mode": "publish_now",
            "publish_enabled": True,
        },
    )
    assert resp.status_code == 422
    assert "Imagem inválida para Instagram" in resp.json()["detail"]

    async def fake_generate_fb(job_arg, settings=None, client=None):
        return SimpleNamespace(text="FB segue ok", origin="llm", warning=None)

    monkeypatch.setattr("app.api.v1.admin.generate_draft_for_job", fake_generate_fb)
    fb_resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert fb_resp.status_code == 200
    assert fb_resp.json()["provider"] == "facebook"


@pytest.mark.asyncio
async def test_approve_blocked_by_invalid_instagram_then_allowed_when_disabled(
    client, db_session, admin_password, monkeypatch
):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()

    async def fake_generate_fb(job_arg, settings=None, client=None):
        return SimpleNamespace(text="Rascunho FB", origin="llm", warning=None)

    monkeypatch.setattr("app.api.v1.admin.generate_draft_for_job", fake_generate_fb)
    fb_resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert fb_resp.status_code == 200

    async def fake_prepare_invalid(session, job_id, settings):
        return _invalid_media_result("Imagem inválida para Instagram")

    monkeypatch.setattr("app.api.v1.admin.prepare_instagram_media", fake_prepare_invalid)

    ig_resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}/instagram/social-post",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "Legenda IG",
            "publish_mode": "publish_now",
            "publish_enabled": False,
        },
    )
    assert ig_resp.status_code == 200, ig_resp.text

    # Force enabled state directly in DB to simulate stale/enabled invalid state
    ig_post = await _get_social_post(db_session, job.id, "instagram")
    assert ig_post is not None
    ig_post.publish_enabled = True
    await db_session.flush()

    approve_resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve_resp.status_code == 422
    detail = approve_resp.json()["detail"]
    assert "Instagram" in detail
    assert "desative a publicação no Instagram" in detail

    disable_resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}/instagram/social-post",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "Legenda IG",
            "publish_mode": "publish_now",
            "publish_enabled": False,
        },
    )
    assert disable_resp.status_code == 200

    approve_resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve_resp.status_code == 200, approve_resp.text
    body = approve_resp.json()
    assert body["job"]["status"] == "published"
    assert body["social"]["status"] in {"registered", "warning", "skipped"}


@pytest.mark.asyncio
async def test_instagram_status_and_logs_expose_safe_reconciliation_fields(
    client, db_session, admin_password
):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    ig = SocialPost(
        job_id=job.id,
        provider="instagram",
        text="IG",
        status=SocialPostStatus.failed,
        attempts=1,
        last_error="Não foi possível confirmar a publicação no Instagram. A reconciliação será verificada antes de qualquer nova tentativa.",
        ig_container_id="container_1",
        ig_media_id="media_1",
        ig_permalink="https://instagram.com/p/safe",
        ig_reconciliation_required=True,
        ig_reconciliation_state="needs_reconciliation",
        ig_last_reconciled_at=datetime.now(timezone.utc),
    )
    db_session.add(ig)
    await db_session.flush()

    from app.models.social_post_log import SocialPostLog

    db_session.add(
        SocialPostLog(
            social_post_id=ig.id,
            attempt_number=1,
            result="ambiguous",
            http_status=200,
            error_message="Erro seguro",
            response_summary="ig_ambiguous_needs_reconciliation",
            external_post_id="container_1",
        )
    )
    await db_session.flush()

    status_resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}/instagram/social-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_resp.status_code == 200, status_resp.text
    item = status_resp.json()
    assert item["provider"] == "instagram"
    assert item["reconciliation_required"] is True
    assert item["published_permalink"] == "https://instagram.com/p/safe"
    assert item["can_retry"] is True
    assert "reconcil" in (item["retry_block_reason"] or "").lower()
    assert "access_token" not in str(item).lower()

    logs_resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}/social-post/logs?provider=instagram",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logs_resp.status_code == 200, logs_resp.text
    logs = logs_resp.json()
    assert logs["total"] == 1
    assert logs["items"][0]["external_post_id"] == "container_1"
    assert "access_token" not in str(logs).lower()


@pytest.mark.asyncio
async def test_instagram_retry_uses_reconciliation_aware_pipeline(
    client, db_session, admin_password, monkeypatch
):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    ig = SocialPost(
        job_id=job.id,
        provider="instagram",
        text="IG",
        status=SocialPostStatus.failed,
        attempts=1,
        last_error="Não foi possível confirmar a publicação no Instagram. A reconciliação será verificada antes de qualquer nova tentativa.",
        ig_container_id="container_1",
        ig_reconciliation_required=True,
        ig_reconciliation_state="needs_reconciliation",
    )
    db_session.add(ig)
    await db_session.flush()

    called = {}

    async def fake_cycle(*, post_id=None, limit=20):
        called["post_id"] = str(post_id) if post_id is not None else None
        called["limit"] = limit
        return {
            "claimed": 1,
            "processed": 1,
            "published": 0,
            "retried": 1,
            "failed_final": 0,
            "skipped": 0,
            "idempotent": 0,
            "by_provider": {},
        }

    monkeypatch.setattr("app.api.v1.admin.run_social_publish_cycle", fake_cycle)

    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/retry?provider=instagram",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["item"]["provider"] == "instagram"
    assert called["post_id"] == str(ig.id)
    assert called["limit"] == 1


@pytest.mark.asyncio
async def test_instagram_social_status_exposes_safe_reconciliation_fields(
    client, db_session, admin_password
):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    post = SocialPost(
        job_id=job.id,
        provider="instagram",
        text="Legenda IG",
        status=SocialPostStatus.failed,
        attempts=1,
        last_error="Não foi possível confirmar a publicação no Instagram. A reconciliação será verificada antes de qualquer nova tentativa.",
        ig_reconciliation_required=True,
        ig_reconciliation_state="needs_reconciliation",
        ig_container_id="container-1",
        ig_media_id=None,
        ig_permalink=None,
    )
    db_session.add(post)
    await db_session.flush()

    resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}/instagram/social-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "instagram"
    assert body["reconciliation_required"] is True
    assert body["ig_container_id"] == "container-1"
    assert body["can_retry"] is True
    assert "access_token" not in str(body).lower()
    assert "page_access_token" not in str(body).lower()


@pytest.mark.asyncio
async def test_social_post_logs_endpoint_returns_safe_audit_history(
    client, db_session, admin_password
):
    from app.models.social_post_log import SocialPostLog

    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    post = SocialPost(
        job_id=job.id,
        provider="instagram",
        text="Legenda IG",
        status=SocialPostStatus.failed,
        attempts=1,
    )
    db_session.add(post)
    await db_session.flush()
    db_session.add(
        SocialPostLog(
            social_post_id=post.id,
            attempt_number=1,
            result="ambiguous",
            http_status=200,
            error_message="mensagem segura",
            response_summary="ig_publish_ambiguous",
            external_post_id=None,
        )
    )
    await db_session.flush()

    resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}/social-post/logs?provider=instagram",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "instagram"
    assert body["total"] == 1
    item = body["items"][0]
    assert item["attempt_number"] == 1
    assert item["result"] == "ambiguous"
    assert "access_token" not in str(body).lower()
