import uuid

import pytest

from app.core.config import get_settings
from app.models.social_post import SocialPost, SocialPostStatus


VALID_CF_TOKEN = "token-de-teste"


async def _login(client, admin_password="test-password"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_scaffold_phase17():
    assert True


@pytest.mark.asyncio
async def test_social_status_endpoints_require_admin(client, seed_published_job):
    resp = await client.get("/api/v1/admin/social-posts")
    assert resp.status_code == 401
    resp = await client.get(f"/api/v1/admin/jobs/{seed_published_job.id}/social-status")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_social_status_by_job_safe_contract_and_labels(
    client,
    db_session,
    admin_password,
    seed_published_job,
    seed_connected_facebook_account,
):
    token = await _login(client, admin_password)

    # Sem rascunho
    resp = await client.get(
        f"/api/v1/admin/jobs/{seed_published_job.id}/social-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["job_id"] == str(seed_published_job.id)
    assert body["status"] == "none"
    assert body["status_label"] == "Sem rascunho"
    assert body["can_retry"] is False

    # Falhou elegível (com conexão)
    post = SocialPost(
        job_id=seed_published_job.id,
        provider="facebook",
        text="Texto",
        status=SocialPostStatus.failed,
        attempts=2,
        last_error="Falha temporária segura",
        external_post_id=None,
        next_retry_at=None,
    )
    db_session.add(post)
    await db_session.flush()

    resp = await client.get(
        f"/api/v1/admin/jobs/{seed_published_job.id}/social-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert body["status_label"] == "Falhou"
    assert body["last_error"] == "Falha temporária segura"
    assert body["can_retry"] is True
    assert body["retry_block_reason"] is None
    assert "access_token" not in str(body).lower()
    assert "page_access_token" not in str(body).lower()
    assert "secret" not in str(body).lower()


@pytest.mark.asyncio
async def test_social_posts_list_safe_fields(
    client,
    db_session,
    admin_password,
    seed_published_job,
    seed_connected_facebook_account,
):
    token = await _login(client, admin_password)
    post = SocialPost(
        job_id=seed_published_job.id,
        provider="facebook",
        text="Texto",
        status=SocialPostStatus.published,
        attempts=1,
        external_post_id="123_456",
        last_error=None,
    )
    db_session.add(post)
    await db_session.flush()

    resp = await client.get(
        "/api/v1/admin/social-posts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["job_id"] == str(seed_published_job.id)
    assert item["status"] == "published"
    assert item["status_label"] == "Publicado"
    assert item["external_post_id"] == "123_456"
    assert item["can_retry"] is False
    assert "access_token" not in str(body).lower()
    assert "page_access_token" not in str(body).lower()


@pytest.mark.asyncio
async def test_social_status_job_not_found(client, admin_password):
    token = await _login(client, admin_password)
    resp = await client.get(
        f"/api/v1/admin/jobs/{uuid.uuid4()}/social-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
