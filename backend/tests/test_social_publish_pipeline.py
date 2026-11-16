import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.social_account import SocialAccountStatus
from app.models.social_post import SocialPostStatus
from app.services.social.publish_pipeline import MSG_RECONNECT, MSG_TRANSIENT, process_claimed_post
from app.services.social.types import PublishFailureCategory, PublishResult


class FakeSession:
    def __init__(self, job=None):
        self._job = job
        self.added = []

    async def get(self, model, ident):
        return self._job

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_pipeline_blocks_when_integration_unavailable_without_auto_retry(monkeypatch):
    from app.services.social import publish_pipeline as pipeline

    job_id = uuid.uuid4()
    post = SimpleNamespace(
        id=uuid.uuid4(),
        job_id=job_id,
        provider="facebook",
        text="Texto",
        status=SocialPostStatus.publishing,
        attempts=0,
        next_retry_at=None,
        last_error=None,
        external_post_id=None,
        published_at=None,
    )
    settings = SimpleNamespace(
        SITE_PUBLIC_URL="https://site.exemplo/",
        SOCIAL_MAX_ATTEMPTS=5,
        social_retry_delays_list=[300, 900, 3600, 10800, 21600],
        SOCIAL_TOKEN_ENCRYPTION_KEY="k",
    )

    async def fake_get_account(session):
        return None

    async def fake_get_fb_account(session):
        return SimpleNamespace(status=SocialAccountStatus.needs_reconnect)

    monkeypatch.setattr(pipeline, "get_active_connected_facebook_account", fake_get_account)
    monkeypatch.setattr(pipeline, "get_facebook_account", fake_get_fb_account)
    monkeypatch.setattr(pipeline, "build_public_job_link", lambda jid, settings=None: f"https://site.exemplo/?vaga={jid}")

    async def noop_log(*args, **kwargs):
        return None

    monkeypatch.setattr(pipeline, "_append_log", noop_log)

    outcome = await process_claimed_post(
        FakeSession(job=SimpleNamespace(id=job_id)),
        post,
        settings=settings,
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert outcome == "failed_final"
    assert post.status == SocialPostStatus.failed
    assert post.next_retry_at is None
    assert post.last_error == MSG_RECONNECT


@pytest.mark.asyncio
async def test_pipeline_schedules_retry_for_transient_failure(monkeypatch):
    from app.services.social import publish_pipeline as pipeline

    job_id = uuid.uuid4()
    post = SimpleNamespace(
        id=uuid.uuid4(),
        job_id=job_id,
        provider="facebook",
        text="Texto",
        status=SocialPostStatus.publishing,
        attempts=0,
        next_retry_at=None,
        last_error=None,
        external_post_id=None,
        published_at=None,
    )
    account = SimpleNamespace(page_id="page1", page_access_token="cipher")
    settings = SimpleNamespace(
        SITE_PUBLIC_URL="https://site.exemplo/",
        SOCIAL_MAX_ATTEMPTS=5,
        social_retry_delays_list=[300, 900, 3600, 10800, 21600],
        SOCIAL_TOKEN_ENCRYPTION_KEY="k",
    )

    async def fake_get_account(session):
        return account

    monkeypatch.setattr(pipeline, "get_active_connected_facebook_account", fake_get_account)
    monkeypatch.setattr(pipeline, "decrypt_token", lambda ciphertext, key: "plain-token")
    monkeypatch.setattr(pipeline, "build_public_job_link", lambda jid, settings=None: f"https://site.exemplo/?vaga={jid}")

    class TransientPublisher:
        async def publish(self, payload):
            return PublishResult(ok=False, category=PublishFailureCategory.transient)

    async def noop_log(*args, **kwargs):
        return None

    monkeypatch.setattr(pipeline, "_append_log", noop_log)

    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    outcome = await process_claimed_post(
        FakeSession(job=SimpleNamespace(id=job_id)),
        post,
        settings=settings,
        publisher=TransientPublisher(),
        now=now,
    )
    assert outcome == "retried"
    assert post.status == SocialPostStatus.failed
    assert post.attempts == 1
    assert post.last_error == MSG_TRANSIENT
    assert post.next_retry_at == datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc)
