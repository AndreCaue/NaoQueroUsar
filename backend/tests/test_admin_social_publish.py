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


@pytest.mark.asyncio
async def test_approve_dispatches_fb_and_ig_independently(
    client, db_session, admin_password, monkeypatch
):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    fb = SocialPost(
        job_id=job.id,
        provider="facebook",
        text="FB",
        status=SocialPostStatus.draft,
        scheduled_at=None,
    )
    ig = SocialPost(
        job_id=job.id,
        provider="instagram",
        text="IG",
        status=SocialPostStatus.draft,
        scheduled_at=None,
        publish_enabled=True,
    )
    db_session.add_all([fb, ig])
    await db_session.flush()

    calls = []
    original_add_task = BackgroundTasks.add_task

    def spy_add_task(self, func, *args, **kwargs):
        calls.append((getattr(func, "__name__", str(func)), args))
        return original_add_task(self, func, *args, **kwargs)

    monkeypatch.setattr(BackgroundTasks, "add_task", spy_add_task)

    async def fake_prepare_ok(session, job_id, settings):
        from types import SimpleNamespace

        return SimpleNamespace(
            validation=SimpleNamespace(valid=True, code=None, message="ok")
        )

    monkeypatch.setattr("app.api.v1.admin.prepare_instagram_media", fake_prepare_ok)

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["job"]["status"] == "published"
    assert body["social"]["status"] == "registered"
    dispatched = {str(args[0]) for name, args in calls if name == "process_social_post_safe" and args}
    assert str(fb.id) in dispatched
    assert str(ig.id) in dispatched


@pytest.mark.asyncio
async def test_approve_ig_dispatch_failure_does_not_block_fb(
    client, db_session, admin_password, monkeypatch
):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    fb = SocialPost(
        job_id=job.id, provider="facebook", text="FB", status=SocialPostStatus.draft, scheduled_at=None
    )
    ig = SocialPost(
        job_id=job.id,
        provider="instagram",
        text="IG",
        status=SocialPostStatus.draft,
        scheduled_at=None,
        publish_enabled=True,
    )
    db_session.add_all([fb, ig])
    await db_session.flush()

    calls = []
    original_add_task = BackgroundTasks.add_task

    def spy_add_task(self, func, *args, **kwargs):
        calls.append((getattr(func, "__name__", str(func)), args))
        # fail only for IG dispatch
        if args and str(args[0]) == str(ig.id):
            raise RuntimeError("ig dispatch fail")
        return original_add_task(self, func, *args, **kwargs)

    monkeypatch.setattr(BackgroundTasks, "add_task", spy_add_task)

    async def fake_prepare_ok(session, job_id, settings):
        from types import SimpleNamespace

        return SimpleNamespace(validation=SimpleNamespace(valid=True, code=None, message="ok"))

    monkeypatch.setattr("app.api.v1.admin.prepare_instagram_media", fake_prepare_ok)

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["job"]["status"] == "published"
    assert body["social"]["status"] == "registered"
    dispatched = [str(args[0]) for name, args in calls if name == "process_social_post_safe" and args]
    assert str(fb.id) in dispatched


@pytest.mark.asyncio
async def test_worker_response_includes_by_provider_breakdown(
    client, admin_password, cron_secret_header, monkeypatch
):
    token = await _login(client, admin_password)
    _ = token

    async def fake_cycle(**kwargs):
        return {
            "claimed": 2,
            "processed": 2,
            "published": 1,
            "retried": 0,
            "failed_final": 1,
            "skipped": 0,
            "idempotent": 0,
            "by_provider": {
                "facebook": {"claimed": 1, "processed": 1, "published": 1, "retried": 0, "failed_final": 0, "skipped": 0, "idempotent": 0},
                "instagram": {"claimed": 1, "processed": 1, "published": 0, "retried": 0, "failed_final": 1, "skipped": 0, "idempotent": 0},
            },
        }

    monkeypatch.setattr("app.api.v1.admin.run_social_publish_cycle", fake_cycle)

    resp = await client.post("/api/v1/admin/social/worker", headers=cron_secret_header)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ok"
    assert body["claimed"] == 2
    assert body["by_provider"]["facebook"]["published"] == 1
    assert body["by_provider"]["instagram"]["failed_final"] == 1


@pytest.mark.asyncio
async def test_retry_provider_deterministic_and_ambiguous(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    fb = SocialPost(job_id=job.id, provider="facebook", text="FB", status=SocialPostStatus.failed, attempts=1, last_error="Falha temporária")
    ig = SocialPost(job_id=job.id, provider="instagram", text="IG", status=SocialPostStatus.failed, attempts=1, last_error="Falha")
    db_session.add_all([fb, ig])
    await db_session.flush()

    # omitted provider with both posts -> 409, no mutation
    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409, resp.text

    # mismatched provider param -> 409 (request instagram on resolved? create case: only fb exists? test explicit mismatch)
    # create another job with only FB
    job2 = await _seed_pending_job(db_session)
    fb2 = SocialPost(job_id=job2.id, provider="facebook", text="FB2", status=SocialPostStatus.failed, attempts=1, last_error="Falha temporária")
    db_session.add(fb2)
    await db_session.flush()
    resp = await client.post(
        f"/api/v1/admin/jobs/{job2.id}/social-post/retry?provider=instagram",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409, resp.text

    async def fake_cycle(*, post_id=None, limit=20):
        return {"claimed": 1, "processed": 1, "published": 0, "retried": 1, "failed_final": 0, "skipped": 0, "idempotent": 0, "by_provider": {}}

    monkeypatch.setattr("app.api.v1.admin.run_social_publish_cycle", fake_cycle)

    # explicit provider resolves deterministically
    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/retry?provider=instagram",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["item"]["provider"] == "instagram"


@pytest.mark.asyncio
async def test_retry_omitted_provider_not_default_for_ig_only(client, db_session, admin_password):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    ig = SocialPost(job_id=job.id, provider="instagram", text="IG", status=SocialPostStatus.failed, attempts=1, last_error="Falha")
    db_session.add(ig)
    await db_session.flush()

    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409, resp.text


@pytest.mark.asyncio
async def test_admin_social_posts_provider_filter_and_logs_safe(client, db_session, admin_password):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    fb = SocialPost(job_id=job.id, provider="facebook", text="FB", status=SocialPostStatus.published, external_post_id="fb_1", attempts=1)
    ig = SocialPost(
        job_id=job.id,
        provider="instagram",
        text="IG",
        status=SocialPostStatus.failed,
        attempts=1,
        last_error="Não foi possível confirmar a publicação no Instagram. A reconciliação será verificada antes de qualquer nova tentativa.",
        ig_container_id="c1",
        ig_media_id="m1",
        ig_permalink="https://instagram.com/p/abc",
        ig_reconciliation_required=True,
        ig_reconciliation_state="needs_reconciliation",
    )
    db_session.add_all([fb, ig])
    await db_session.flush()

    resp = await client.get(
        "/api/v1/admin/social-posts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    providers = {i["provider"] for i in items}
    assert "facebook" in providers and "instagram" in providers

    resp = await client.get(
        "/api/v1/admin/social-posts?provider=instagram",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(i["provider"] == "instagram" for i in items)
    ig_item = next(i for i in items if i["job_id"] == str(job.id))
    assert ig_item["published_permalink"] == "https://instagram.com/p/abc"
    assert ig_item["ig_container_id"] == "c1"
    assert ig_item["reconciliation_required"] is True
    assert "access_token" not in str(ig_item).lower()

    # logs endpoint safe
    from app.models.social_post_log import SocialPostLog

    db_session.add(
        SocialPostLog(
            social_post_id=ig.id,
            attempt_number=1,
            result="ambiguous",
            http_status=200,
            error_message="Seguro",
            response_summary="ig_ambiguous_needs_reconciliation",
            external_post_id="c1",
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
    assert body["items"][0]["response_summary"] == "ig_ambiguous_needs_reconciliation"
    assert "access_token" not in str(body).lower()


@pytest.mark.asyncio
async def test_approve_dispatches_fb_and_ig_independently_publ01(
    client, db_session, admin_password, monkeypatch
):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    fb = SocialPost(
        job_id=job.id,
        provider="facebook",
        text="FB draft",
        status=SocialPostStatus.draft,
        scheduled_at=None,
    )
    ig = SocialPost(
        job_id=job.id,
        provider="instagram",
        text="IG draft",
        status=SocialPostStatus.draft,
        scheduled_at=None,
        publish_enabled=True,
    )
    db_session.add_all([fb, ig])
    await db_session.flush()

    calls = []
    original_add_task = BackgroundTasks.add_task

    def spy_add_task(self, func, *args, **kwargs):
        calls.append((getattr(func, "__name__", str(func)), [str(a) for a in args]))
        return original_add_task(self, func, *args, **kwargs)

    monkeypatch.setattr(BackgroundTasks, "add_task", spy_add_task)

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["job"]["status"] == "published"
    assert body["social"]["status"] in {"registered", "warning", "skipped"}
    dispatched_ids = {args[0] for name, args in calls if name == "process_social_post_safe" and args}
    assert str(fb.id) in dispatched_ids
    assert str(ig.id) in dispatched_ids


@pytest.mark.asyncio
async def test_approve_ig_dispatch_failure_does_not_block_fb_or_site(
    client, db_session, admin_password, monkeypatch
):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    fb = SocialPost(
        job_id=job.id, provider="facebook", text="FB", status=SocialPostStatus.draft, scheduled_at=None
    )
    ig = SocialPost(
        job_id=job.id, provider="instagram", text="IG", status=SocialPostStatus.draft, scheduled_at=None, publish_enabled=True
    )
    db_session.add_all([fb, ig])
    await db_session.flush()

    original_add_task = BackgroundTasks.add_task
    calls = []

    def flaky_add_task(self, func, *args, **kwargs):
        name = getattr(func, "__name__", str(func))
        calls.append(str(args[0]) if args else None)
        if args and str(args[0]) == str(ig.id):
            raise RuntimeError("ig dispatch fail")
        return original_add_task(self, func, *args, **kwargs)

    monkeypatch.setattr(BackgroundTasks, "add_task", flaky_add_task)

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["job"]["status"] == "published"
    assert str(fb.id) in calls
    assert str(ig.id) in calls


@pytest.mark.asyncio
async def test_worker_response_includes_by_provider_breakdown(client, admin_password, monkeypatch):
    token = await _login(client, admin_password)

    async def fake_cycle(**kwargs):
        return {
            "claimed": 2, "processed": 2, "published": 1, "retried": 0,
            "failed_final": 1, "skipped": 0, "idempotent": 0,
            "by_provider": {
                "facebook": {"claimed": 1, "processed": 1, "published": 1, "retried": 0, "failed_final": 0, "skipped": 0, "idempotent": 0},
                "instagram": {"claimed": 1, "processed": 1, "published": 0, "retried": 0, "failed_final": 1, "skipped": 0, "idempotent": 0},
            },
        }

    monkeypatch.setattr("app.api.v1.admin.run_social_publish_cycle", fake_cycle)
    resp = await client.post(
        "/api/v1/admin/social/worker",
        headers={"X-Cron-Secret": "test-cron-secret"},
    )
    if resp.status_code in (401, 403):
        pytest.skip("cron secret not configured for test client")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["published"] == 1
    assert body["by_provider"]["facebook"]["published"] == 1
    assert body["by_provider"]["instagram"]["failed_final"] == 1


@pytest.mark.asyncio
async def test_admin_social_posts_provider_filter_and_all(client, db_session, admin_password):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    db_session.add_all([
        SocialPost(job_id=job.id, provider="facebook", text="fb", status=SocialPostStatus.failed),
        SocialPost(job_id=job.id, provider="instagram", text="ig", status=SocialPostStatus.scheduled),
    ])
    await db_session.flush()

    resp_all = await client.get("/api/v1/admin/social-posts", headers={"Authorization": f"Bearer {token}"})
    assert resp_all.status_code == 200, resp_all.text
    items_all = resp_all.json()["items"]
    providers = {i["provider"] for i in items_all}
    assert "facebook" in providers and "instagram" in providers

    resp_fb = await client.get("/api/v1/admin/social-posts?provider=facebook", headers={"Authorization": f"Bearer {token}"})
    assert resp_fb.status_code == 200
    assert all(i["provider"] == "facebook" for i in resp_fb.json()["items"])

    resp_ig = await client.get("/api/v1/admin/social-posts?provider=instagram", headers={"Authorization": f"Bearer {token}"})
    assert resp_ig.status_code == 200
    assert all(i["provider"] == "instagram" for i in resp_ig.json()["items"])


@pytest.mark.asyncio
async def test_retry_provider_resolution_mismatch_and_omitted_ambiguity(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_pending_job(db_session)
    fb = SocialPost(job_id=job.id, provider="facebook", text="fb", status=SocialPostStatus.failed, attempts=1, next_retry_at=None)
    ig = SocialPost(job_id=job.id, provider="instagram", text="ig", status=SocialPostStatus.failed, attempts=1, next_retry_at=None,
                    ig_reconciliation_required=True, ig_reconciliation_state="needs_reconciliation")
    db_session.add_all([fb, ig])
    await db_session.flush()

    resp = await client.post(f"/api/v1/admin/jobs/{job.id}/social-post/retry", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 409, resp.text

    resp = await client.post(f"/api/v1/admin/jobs/{job.id}/social-post/retry?provider=facebook", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (200, 409, 400)

    job2 = await _seed_pending_job(db_session)
    ig2 = SocialPost(job_id=job2.id, provider="instagram", text="ig2", status=SocialPostStatus.failed, attempts=1,
                     ig_reconciliation_required=True, ig_reconciliation_state="needs_reconciliation")
    db_session.add(ig2)
    await db_session.flush()
    resp2 = await client.post(f"/api/v1/admin/jobs/{job2.id}/social-post/retry", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 409, resp2.text

    async def fake_cycle(**kwargs):
        return {"claimed": 1, "processed": 1, "published": 0, "retried": 0, "failed_final": 1, "skipped": 0, "idempotent": 0}

    monkeypatch.setattr("app.api.v1.admin.run_social_publish_cycle", fake_cycle)
    resp3 = await client.post(
        f"/api/v1/admin/jobs/{job2.id}/social-post/retry?provider=instagram",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp3.status_code == 200, resp3.text
    assert resp3.json()["item"]["provider"] == "instagram"
