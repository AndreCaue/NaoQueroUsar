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


@pytest.mark.asyncio
async def test_process_social_post_safe_targets_post_id(monkeypatch):
    from app.services.social import publish_pipeline as pipeline

    called = {}

    async def fake_cycle(*, post_id=None, limit=20):
        called["post_id"] = post_id
        called["limit"] = limit
        return {"claimed": 1}

    monkeypatch.setattr(pipeline, "run_social_publish_cycle", fake_cycle)
    target = uuid.uuid4()
    result = await pipeline.process_social_post_safe(target)
    assert result == {"claimed": 1}
    assert str(called["post_id"]) == str(target)
    assert called["limit"] == 1

    # Reexecução/direcionamento repetido para o mesmo post deve seguir pelo mesmo caminho idempotente do pipeline
    result = await pipeline.process_social_post_safe(target)
    assert result == {"claimed": 1}
    assert str(called["post_id"]) == str(target)
    assert called["limit"] == 1


class _Tx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _SessionCtx:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def begin(self):
        return _Tx()


@pytest.mark.asyncio
async def test_run_social_publish_cycle_recovers_post_claim_exception_without_leaving_publishing(monkeypatch):
    from app.crud.social_posts import compute_social_retry_state
    from app.services.social import publish_pipeline as pipeline
    from app.services.social.publish_pipeline import MSG_AMBIGUOUS

    post_id = uuid.uuid4()
    post = SimpleNamespace(
        id=post_id,
        job_id=uuid.uuid4(),
        provider="facebook",
        text="Texto",
        status=SocialPostStatus.publishing,
        attempts=0,
        next_retry_at=None,
        last_error=None,
        external_post_id=None,
        published_at=None,
    )

    class FakeClaimSession:
        def begin(self):
            return _Tx()

        async def flush(self):
            return None

    class FakeProcessingSession:
        def begin(self):
            return _Tx()

        async def get(self, model, ident):
            return None

        async def flush(self):
            return None

    class FakeRecoverySession:
        def begin(self):
            return _Tx()

        async def get(self, model, ident):
            return None

        async def flush(self):
            return None

    claim_session = FakeClaimSession()
    processing_session = FakeProcessingSession()
    recovery_session = FakeRecoverySession()
    sessions = [claim_session, processing_session, recovery_session]

    class FakeSessionFactory:
        def __call__(self):
            if not sessions:
                raise AssertionError("unexpected extra session")
            return _SessionCtx(sessions.pop(0))

    mark_calls = []
    log_calls = []

    async def fake_list_due_for_claim(session, **kwargs):
        return [post]

    async def fake_claim_for_publishing(session, claimed_post, *, now=None):
        claimed_post.status = SocialPostStatus.publishing
        return "claimed"

    async def fake_process_claimed_post(session, claimed_post, *, settings=None, publisher=None, now=None):
        raise RuntimeError("boom after claim")

    async def fake_get_social_post_by_id(session, pid):
        assert pid == post_id
        return post

    async def fake_mark_failed(session, failed_post, *, attempts, last_error, next_retry_at, final):
        failed_post.status = SocialPostStatus.failed
        failed_post.attempts = attempts
        failed_post.last_error = last_error
        failed_post.next_retry_at = next_retry_at
        mark_calls.append(
            {
                "attempts": attempts,
                "last_error": last_error,
                "next_retry_at": next_retry_at,
                "final": final,
            }
        )
        return failed_post

    async def fake_append_log(session, logged_post, *, attempt_number, result, **kwargs):
        log_calls.append({"attempt_number": attempt_number, "result": result, **kwargs})
        return None

    monkeypatch.setattr(pipeline, "async_session_factory", FakeSessionFactory())
    monkeypatch.setattr(pipeline, "list_due_for_claim", fake_list_due_for_claim)
    monkeypatch.setattr(pipeline, "claim_for_publishing", fake_claim_for_publishing)
    monkeypatch.setattr(pipeline, "process_claimed_post", fake_process_claimed_post)
    monkeypatch.setattr(pipeline, "get_social_post_by_id", fake_get_social_post_by_id)
    monkeypatch.setattr(pipeline, "mark_failed", fake_mark_failed)
    monkeypatch.setattr(pipeline, "_append_log", fake_append_log)

    result = await pipeline.run_social_publish_cycle(post_id=post_id, limit=1)

    assert result["processed"] == 1
    assert result["failed_final"] == 1
    assert post.status == SocialPostStatus.failed
    assert post.attempts == 1
    assert post.last_error == MSG_AMBIGUOUS
    assert post.next_retry_at is None
    assert mark_calls == [
        {
            "attempts": 1,
            "last_error": MSG_AMBIGUOUS,
            "next_retry_at": None,
            "final": True,
        }
    ]
    assert any(
        call["result"] == "ambiguous"
        and call["response_summary"] == "post_claim_processing_exception"
        for call in log_calls
    )

    can_retry, reason = compute_social_retry_state(post, SocialAccountStatus.connected)
    assert can_retry is False
    assert reason == "Verifique a publicação no Facebook antes de tentar novamente para evitar duplicidade."

@pytest.mark.asyncio
async def test_list_due_for_claim_filters_publish_enabled_false(monkeypatch):
    from app.crud.social_posts import list_due_for_claim

    captured = {}

    class Result:
        def all(self):
            return []

    class FakeSession:
        async def scalars(self, stmt):
            captured["stmt"] = stmt
            return Result()

    await list_due_for_claim(FakeSession(), provider="instagram", limit=10)
    stmt = captured["stmt"]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
    assert "publish_enabled" in compiled

@pytest.mark.asyncio
async def test_pipeline_ig_ambiguous_persists_reconciliation_without_auto_retry(monkeypatch):
    from app.services.social import publish_pipeline as pipeline

    job_id = uuid.uuid4()
    post = SimpleNamespace(
        id=uuid.uuid4(),
        job_id=job_id,
        provider="instagram",
        text="Legenda",
        status=SocialPostStatus.publishing,
        attempts=0,
        next_retry_at="keep",
        last_error=None,
        external_post_id=None,
        published_at=None,
        ig_container_id=None,
        ig_media_id=None,
        ig_permalink=None,
        ig_reconciliation_required=False,
        ig_reconciliation_state=None,
        ig_last_reconciled_at=None,
        ig_last_publish_error_code=None,
    )
    account = SimpleNamespace(
        status=SocialAccountStatus.connected,
        ig_user_id="1789",
        ig_readiness_state="ready",
        page_access_token="cipher",
    )
    settings = SimpleNamespace(
        SITE_PUBLIC_URL="https://site.exemplo/",
        SOCIAL_MAX_ATTEMPTS=5,
        social_retry_delays_list=[300, 900, 3600, 10800, 21600],
        SOCIAL_TOKEN_ENCRYPTION_KEY="k",
        META_GRAPH_VERSION="v21.0",
    )

    async def fake_get_active(session):
        return account

    async def fake_get_fb(session):
        return account

    async def fake_prepare(session, jid, st):
        return SimpleNamespace(
            image_url="https://media.example.com/ig.jpg",
            validation=SimpleNamespace(valid=True, message="ok"),
        )

    class AmbiguousIGPublisher:
        async def publish(self, payload):
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.ambiguous,
                error_message="ambiguous",
                container_id="container-1",
                error_code="ig_publish_timeout_ambiguous",
            )

    async def noop_log(*args, **kwargs):
        return None

    monkeypatch.setattr(pipeline, "get_active_connected_facebook_account", fake_get_active)
    monkeypatch.setattr(pipeline, "get_facebook_account", fake_get_fb)
    monkeypatch.setattr(pipeline, "decrypt_token", lambda ciphertext, key: "plain-token")
    monkeypatch.setattr(pipeline, "prepare_instagram_media", fake_prepare)
    monkeypatch.setattr(pipeline, "validate_media_public_base_url", lambda s: (True, None, None))
    monkeypatch.setattr(pipeline, "_append_log", noop_log)

    outcome = await process_claimed_post(
        FakeSession(job=SimpleNamespace(id=job_id)),
        post,
        settings=settings,
        publisher=AmbiguousIGPublisher(),
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert outcome == "failed_final"
    assert post.status == SocialPostStatus.failed
    assert post.next_retry_at is None
    assert post.ig_reconciliation_required is True
    assert post.ig_reconciliation_state == "needs_reconciliation"
    assert post.ig_container_id == "container-1"


@pytest.mark.asyncio
async def test_pipeline_ig_rate_limit_is_blocked_no_retry_storm(monkeypatch):
    from app.services.social import publish_pipeline as pipeline

    job_id = uuid.uuid4()
    post = SimpleNamespace(
        id=uuid.uuid4(),
        job_id=job_id,
        provider="instagram",
        text="Legenda",
        status=SocialPostStatus.publishing,
        attempts=0,
        next_retry_at=None,
        last_error=None,
        external_post_id=None,
        published_at=None,
        ig_container_id=None,
        ig_media_id=None,
        ig_permalink=None,
        ig_reconciliation_required=False,
        ig_reconciliation_state=None,
        ig_last_reconciled_at=None,
        ig_last_publish_error_code=None,
    )
    account = SimpleNamespace(status=SocialAccountStatus.connected, ig_user_id="1789", ig_readiness_state="ready", page_access_token="cipher")
    settings = SimpleNamespace(SITE_PUBLIC_URL="https://site.exemplo/", SOCIAL_MAX_ATTEMPTS=5, social_retry_delays_list=[300], SOCIAL_TOKEN_ENCRYPTION_KEY="k")

    async def fake_prepare(session, jid, st):
        return SimpleNamespace(image_url="https://media.example.com/ig.jpg", validation=SimpleNamespace(valid=True, message="ok"))

    class RateLimitPublisher:
        async def publish(self, payload):
            return PublishResult(ok=False, category=PublishFailureCategory.permanent, error_message="rate", error_code="ig_content_publishing_limit")

    async def noop_log(*args, **kwargs):
        return None

    monkeypatch.setattr(pipeline, "get_active_connected_facebook_account", lambda s: _async_ret(account))
    monkeypatch.setattr(pipeline, "get_facebook_account", lambda s: _async_ret(account))
    monkeypatch.setattr(pipeline, "decrypt_token", lambda ciphertext, key: "plain-token")
    monkeypatch.setattr(pipeline, "prepare_instagram_media", fake_prepare)
    monkeypatch.setattr(pipeline, "validate_media_public_base_url", lambda s: (True, None, None))
    monkeypatch.setattr(pipeline, "_append_log", noop_log)

    outcome = await process_claimed_post(FakeSession(job=SimpleNamespace(id=job_id)), post, settings=settings, publisher=RateLimitPublisher())

    assert outcome == "failed_final"
    assert post.status == SocialPostStatus.failed
    assert post.next_retry_at is None
    assert post.ig_last_publish_error_code == "ig_content_publishing_limit"
    assert "limite" in (post.last_error or "").lower()


@pytest.mark.asyncio
async def test_pipeline_provider_isolation_ig_not_ready_does_not_block_facebook(monkeypatch):
    from app.crud.social_posts import compute_social_retry_state
    from app.services.social import publish_pipeline as pipeline

    # IG post fails preflight as not ready
    ig_job_id = uuid.uuid4()
    ig_post = SimpleNamespace(
        id=uuid.uuid4(), job_id=ig_job_id, provider="instagram", text="Legenda",
        status=SocialPostStatus.publishing, attempts=0, next_retry_at=None, last_error=None,
        external_post_id=None, published_at=None, ig_container_id=None, ig_media_id=None,
        ig_permalink=None, ig_reconciliation_required=False, ig_reconciliation_state=None,
        ig_last_reconciled_at=None, ig_last_publish_error_code=None,
    )
    # account missing/not ready for IG
    account = SimpleNamespace(status=SocialAccountStatus.connected, ig_user_id=None, ig_readiness_state="missing_linkage", page_access_token="cipher")
    settings = SimpleNamespace(SITE_PUBLIC_URL="https://site.exemplo/", SOCIAL_MAX_ATTEMPTS=5, social_retry_delays_list=[300], SOCIAL_TOKEN_ENCRYPTION_KEY="k")

    async def noop_log(*args, **kwargs):
        return None

    monkeypatch.setattr(pipeline, "get_active_connected_facebook_account", lambda s: _async_ret(account))
    monkeypatch.setattr(pipeline, "get_facebook_account", lambda s: _async_ret(account))
    monkeypatch.setattr(pipeline, "_append_log", noop_log)

    outcome = await process_claimed_post(FakeSession(job=SimpleNamespace(id=ig_job_id)), ig_post, settings=settings)
    assert outcome == "failed_final"
    assert ig_post.status == SocialPostStatus.failed
    assert ig_post.next_retry_at is None
    assert "Integra" in (ig_post.last_error or "") or "Instagram" in (ig_post.last_error or "")

    # FB post remains processable independently
    fb_job_id = uuid.uuid4()
    fb_post = SimpleNamespace(
        id=uuid.uuid4(), job_id=fb_job_id, provider="facebook", text="Texto FB",
        status=SocialPostStatus.publishing, attempts=0, next_retry_at=None, last_error=None,
        external_post_id=None, published_at=None,
    )
    fb_account = SimpleNamespace(status=SocialAccountStatus.connected, page_id="page1", page_access_token="cipher")
    monkeypatch.setattr(pipeline, "get_active_connected_facebook_account", lambda s: _async_ret(fb_account))
    monkeypatch.setattr(pipeline, "get_facebook_account", lambda s: _async_ret(fb_account))
    monkeypatch.setattr(pipeline, "decrypt_token", lambda c, k: "plain")
    monkeypatch.setattr(pipeline, "build_public_job_link", lambda jid, settings=None: f"https://site.exemplo/?vaga={jid}")

    class OkFB:
        async def publish(self, payload):
            return PublishResult(ok=True, external_post_id="fb-1")

    fb_outcome = await process_claimed_post(FakeSession(job=SimpleNamespace(id=fb_job_id)), fb_post, settings=settings, publisher=OkFB())
    assert fb_outcome == "published"
    assert fb_post.status == SocialPostStatus.published


async def _async_ret(val):
    return val

@pytest.mark.asyncio
async def test_pipeline_ig_reconciliation_published_marks_post_published(monkeypatch):
    from app.services.social import publish_pipeline as pipeline

    job_id = uuid.uuid4()
    post = SimpleNamespace(
        id=uuid.uuid4(), job_id=job_id, provider="instagram", text="Legenda",
        status=SocialPostStatus.publishing, attempts=1, next_retry_at=None,
        last_error="Não foi possível confirmar a publicação no Instagram. A reconciliação será verificada antes de qualquer nova tentativa.",
        external_post_id=None, published_at=None,
        ig_container_id="container-1", ig_media_id="media-1", ig_permalink=None,
        ig_reconciliation_required=True, ig_reconciliation_state="needs_reconciliation",
        ig_last_reconciled_at=None, ig_last_publish_error_code="ig_publish_timeout_ambiguous",
    )
    account = SimpleNamespace(status=SocialAccountStatus.connected, ig_user_id="1789", ig_readiness_state="ready", page_access_token="cipher")
    settings = SimpleNamespace(SITE_PUBLIC_URL="https://site.exemplo/", SOCIAL_MAX_ATTEMPTS=5, social_retry_delays_list=[300], SOCIAL_TOKEN_ENCRYPTION_KEY="k", META_GRAPH_VERSION="v21.0", IG_PUBLISH_HTTP_TIMEOUT_SECONDS=20.0, IG_STATUS_POLL_MAX_ATTEMPTS=2, IG_STATUS_POLL_DELAY_SECONDS=0.0, IG_PUBLISH_MAX_ATTEMPT_SECONDS=45.0)

    class FakeResponse:
        def __init__(self, status_code=200, body=None):
            self.status_code = status_code
            self._body = body
        def json(self):
            return self._body

    class FakeClient:
        def __init__(self, timeout=None):
            self.calls = []
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url, params=None, **kwargs):
            self.calls.append((url, params))
            # return published media info
            if "/media-1" in url or params and params.get("fields"):
                return FakeResponse(200, {"id": "media-1", "permalink": "https://instagram.com/p/reconciled"})
            return FakeResponse(404, {"error": {"message": "not found"}})
        async def post(self, url, data=None, **kwargs):
            self.calls.append((url, data))
            return FakeResponse(500, {})

    async def noop_log(*args, **kwargs):
        return None

    monkeypatch.setattr(pipeline, "get_active_connected_facebook_account", lambda s: _async_ret(account))
    monkeypatch.setattr(pipeline, "get_facebook_account", lambda s: _async_ret(account))
    monkeypatch.setattr(pipeline, "decrypt_token", lambda c, k: "plain-token")
    monkeypatch.setattr(pipeline, "_append_log", noop_log)
    monkeypatch.setattr(pipeline.httpx, "AsyncClient", FakeClient)

    outcome = await process_claimed_post(FakeSession(job=SimpleNamespace(id=job_id)), post, settings=settings)

    assert outcome == "published"
    assert post.status == SocialPostStatus.published
    assert post.external_post_id == "media-1"
    assert post.ig_reconciliation_required is False
