import uuid
from datetime import datetime, timezone

import pytest

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
async def test_retry_requires_admin(client, seed_published_job):
    resp = await client.post(f"/api/v1/admin/jobs/{seed_published_job.id}/social-post/retry")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_retry_eligible_failed_uses_pipeline(
    client,
    db_session,
    admin_password,
    seed_published_job,
    seed_connected_facebook_account,
    monkeypatch,
):
    token = await _login(client, admin_password)
    post = SocialPost(
        job_id=seed_published_job.id,
        provider="facebook",
        text="Texto",
        status=SocialPostStatus.failed,
        attempts=1,
        last_error="Falha",
        external_post_id=None,
        next_retry_at=None,
    )
    db_session.add(post)
    await db_session.flush()

    called = {}

    async def fake_cycle(*, post_id=None, limit=20):
        called["post_id"] = str(post_id)
        called["limit"] = limit
        return {"claimed": 1, "processed": 1, "published": 1, "retried": 0, "failed_final": 0, "skipped": 0, "idempotent": 0}

    monkeypatch.setattr("app.api.v1.admin.run_social_publish_cycle", fake_cycle)

    resp = await client.post(
        f"/api/v1/admin/jobs/{seed_published_job.id}/social-post/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["outcome"] in {"retried", "noop"}
    assert body["item"]["job_id"] == str(seed_published_job.id)
    assert called["post_id"] == str(post.id)
    assert called["limit"] == 1


@pytest.mark.asyncio
async def test_retry_ineligible_states_and_reconnect(
    client,
    db_session,
    admin_password,
    seed_published_job,
    seed_needs_reconnect_facebook_account,
):
    token = await _login(client, admin_password)

    # needs_reconnect => inelegível
    post = SocialPost(
        job_id=seed_published_job.id,
        provider="facebook",
        text="Texto",
        status=SocialPostStatus.failed,
        attempts=1,
        last_error="Falha",
        external_post_id=None,
    )
    db_session.add(post)
    await db_session.flush()

    resp = await client.post(
        f"/api/v1/admin/jobs/{seed_published_job.id}/social-post/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] == "not_eligible"
    assert body["item"]["can_retry"] is False
    assert "Reconexão" in (body["item"]["retry_block_reason"] or "")

    # published => noop/inelegível
    post.status = SocialPostStatus.published
    post.external_post_id = "123_456"
    await db_session.flush()
    resp = await client.post(
        f"/api/v1/admin/jobs/{seed_published_job.id}/social-post/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "noop"

    # publishing => noop
    post.status = SocialPostStatus.publishing
    post.external_post_id = None
    await db_session.flush()
    resp = await client.post(
        f"/api/v1/admin/jobs/{seed_published_job.id}/social-post/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "noop"


@pytest.mark.asyncio
async def test_retry_job_without_post_is_idempotent_not_eligible(
    client, admin_password, seed_published_job
):
    token = await _login(client, admin_password)
    resp = await client.post(
        f"/api/v1/admin/jobs/{seed_published_job.id}/social-post/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] == "not_eligible"
    assert body["item"]["status"] == "none"
