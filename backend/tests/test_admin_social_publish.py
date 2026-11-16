import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import BackgroundTasks

from app.models.social_post import SocialPost, SocialPostStatus


VALID_CF_TOKEN = "token-de-teste"


async def _login(client, admin_password="test-password"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _seed_pending_job(db_session):
    from app.models.job import Job, JobStatus

    job = Job(
        title="Vaga Dispatch",
        company="Empresa",
        activities="Atuar",
        city="São Paulo",
        contact_phone="+55 11 99999-1111",
        status=JobStatus.pending,
    )
    db_session.add(job)
    await db_session.flush()
    return job


@pytest.mark.asyncio
async def test_scaffold_phase17():
    assert True


@pytest.mark.asyncio
async def test_approve_enqueues_immediate_dispatch_for_due_registered_post(
    client, db_session, admin_password, monkeypatch
):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    post = SocialPost(
        job_id=job.id,
        provider="facebook",
        text="Texto para publicar agora",
        status=SocialPostStatus.draft,
        scheduled_at=None,  # publish_now => aprovado agenda para agora
    )
    db_session.add(post)
    await db_session.flush()

    calls = []
    original_add_task = BackgroundTasks.add_task

    def spy_add_task(self, func, *args, **kwargs):
        calls.append((getattr(func, "__name__", str(func)), args, kwargs))
        return original_add_task(self, func, *args, **kwargs)

    monkeypatch.setattr(BackgroundTasks, "add_task", spy_add_task)

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["job"]["status"] == "published"
    assert body["social"]["status"] == "registered"

    # dispatch não bloqueante enfileirado para o post correto
    assert any(name == "process_social_post_safe" and args and str(args[0]) == str(post.id) for name, args, _ in calls)


@pytest.mark.asyncio
async def test_approve_without_draft_does_not_enqueue_dispatch(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)

    calls = []
    original_add_task = BackgroundTasks.add_task

    def spy_add_task(self, func, *args, **kwargs):
        calls.append((func, args, kwargs))
        return original_add_task(self, func, *args, **kwargs)

    monkeypatch.setattr(BackgroundTasks, "add_task", spy_add_task)

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["job"]["status"] == "published"
    assert body["social"]["status"] == "skipped"
    assert calls == []


@pytest.mark.asyncio
async def test_approve_remains_site_first_even_if_dispatch_enqueue_fails(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    post = SocialPost(
        job_id=job.id,
        provider="facebook",
        text="Texto",
        status=SocialPostStatus.draft,
        scheduled_at=None,
    )
    db_session.add(post)
    await db_session.flush()

    def boom(self, func, *args, **kwargs):
        raise RuntimeError("dispatch fail")

    monkeypatch.setattr(BackgroundTasks, "add_task", boom)

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["job"]["status"] == "published"
    assert body["social"]["status"] == "registered"

    get_resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "published"
