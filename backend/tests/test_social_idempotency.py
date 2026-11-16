import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.social_post import SocialPostStatus
from app.services.social.publish_pipeline import process_claimed_post
from app.services.social.types import PublishFailureCategory, PublishResult


class FakeSession:
    async def get(self, model, ident):
        return None

    def add(self, obj):
        return None

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_idempotency_noop_when_already_published_or_external_id():
    session = FakeSession()
    settings = SimpleNamespace(
        SITE_PUBLIC_URL="https://site.exemplo/",
        SOCIAL_MAX_ATTEMPTS=5,
        social_retry_delays_list=[300, 900, 3600, 10800, 21600],
        SOCIAL_TOKEN_ENCRYPTION_KEY="",
    )
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    post_published = SimpleNamespace(
        id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        provider="facebook",
        text="t",
        status=SocialPostStatus.published,
        attempts=1,
        next_retry_at=None,
        last_error=None,
        external_post_id="123_456",
        published_at=now,
    )
    outcome = await process_claimed_post(session, post_published, settings=settings, now=now)
    assert outcome == "idempotent"

    post_with_external = SimpleNamespace(
        id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        provider="facebook",
        text="t",
        status=SocialPostStatus.failed,
        attempts=1,
        next_retry_at=None,
        last_error="x",
        external_post_id="123_456",
        published_at=None,
    )
    outcome = await process_claimed_post(session, post_with_external, settings=settings, now=now)
    assert outcome == "idempotent"


@pytest.mark.asyncio
async def test_ambiguous_failure_does_not_schedule_auto_retry(monkeypatch):
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
    job = SimpleNamespace(id=job_id)
    account = SimpleNamespace(page_id="page1", page_access_token="cipher")
    settings = SimpleNamespace(
        SITE_PUBLIC_URL="https://site.exemplo/",
        SOCIAL_MAX_ATTEMPTS=5,
        social_retry_delays_list=[300, 900, 3600, 10800, 21600],
        SOCIAL_TOKEN_ENCRYPTION_KEY="k",
        META_GRAPH_VERSION="v21.0",
    )

    class Sess(FakeSession):
        async def get(self, model, ident):
            return job

    async def fake_get_account(session):
        return account

    monkeypatch.setattr(pipeline, "get_active_connected_facebook_account", fake_get_account)
    monkeypatch.setattr(pipeline, "decrypt_token", lambda ciphertext, key: "plain-token")
    monkeypatch.setattr(pipeline, "build_public_job_link", lambda jid, settings=None: f"https://site.exemplo/?vaga={jid}")

    class AmbiguousPublisher:
        async def publish(self, payload):
            assert payload.page_access_token == "plain-token"
            return PublishResult(ok=False, category=PublishFailureCategory.ambiguous, error_message="amb")

    async def noop_log(*args, **kwargs):
        return None

    monkeypatch.setattr(pipeline, "_append_log", noop_log)

    outcome = await process_claimed_post(
        Sess(), post, settings=settings, publisher=AmbiguousPublisher(), now=datetime(2026, 1, 1, tzinfo=timezone.utc)
    )

    assert outcome == "failed_final"
    assert post.status == SocialPostStatus.failed
    assert post.attempts == 1
    assert post.next_retry_at is None
    assert "duplic" in (post.last_error or "").lower() or "confirmar" in (post.last_error or "").lower()
