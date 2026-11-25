"""Contrato/comportamento do InstagramPublisher (Phase 31)."""

from __future__ import annotations

import asyncio
import inspect

import pytest

from app.services.social.instagram import InstagramPublisher
from app.services.social.types import PublishFailureCategory, PublishResult, SocialPostPayload


class FakeResponse:
    def __init__(self, status_code=200, body=None, json_exc=False):
        self.status_code = status_code
        self._body = body
        self._json_exc = json_exc

    def json(self):
        if self._json_exc:
            raise ValueError("bad json")
        return self._body


class FakeAsyncClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, data=None, **kwargs):
        self.calls.append(("POST", url, data))
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def get(self, url, params=None, **kwargs):
        self.calls.append(("GET", url, params))
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _ig_payload(**overrides):
    base = dict(
        job_id="job-1",
        provider="instagram",
        message="Legenda IG",
        image_url="https://media.example.com/ig.jpg",
        ig_user_id="1789",
        page_access_token="plain-token",
    )
    base.update(overrides)
    return SocialPostPayload(**base)


def test_instagram_publisher_async_contract_and_safe_failure_without_context() -> None:
    publisher = InstagramPublisher()
    assert hasattr(publisher, "publish") and callable(publisher.publish)
    assert inspect.iscoroutinefunction(InstagramPublisher.publish)
    sig = inspect.signature(InstagramPublisher.publish)
    assert "post" in sig.parameters

    result = asyncio.run(publisher.publish(None))

    assert isinstance(result, PublishResult)
    assert result.ok is False
    assert result.external_post_id is None
    assert result.category in {
        PublishFailureCategory.permanent,
        PublishFailureCategory.transient,
        PublishFailureCategory.unknown,
        PublishFailureCategory.ambiguous,
    }
    assert result.error_message
    assert "access_token" not in (result.error_message or "").lower()
    assert "token=" not in (result.error_message or "").lower()


def test_instagram_publisher_rejects_invalid_payload_contract() -> None:
    publisher = InstagramPublisher()
    payload = SocialPostPayload(job_id="job-1", provider="facebook", message="texto")
    result = asyncio.run(publisher.publish(payload))
    assert isinstance(result, PublishResult)
    assert result.ok is False
    assert result.category == PublishFailureCategory.permanent
    assert "access_token" not in (result.error_message or "").lower()


@pytest.mark.asyncio
async def test_instagram_publisher_two_step_publish_success_with_permalink(monkeypatch):
    from app.services.social import instagram as ig_mod

    responses = [
        FakeResponse(200, {"id": "container-1"}),  # create container
        FakeResponse(200, {"id": "container-1", "status_code": "FINISHED"}),  # status
        FakeResponse(200, {"id": "media-1"}),  # publish
        FakeResponse(200, {"id": "media-1", "permalink": "https://instagram.com/p/abc"}),  # permalink
    ]
    fake = FakeAsyncClient(responses)
    monkeypatch.setattr(ig_mod.httpx, "AsyncClient", lambda timeout=None: fake)
    monkeypatch.setattr(
        ig_mod,
        "get_settings",
        lambda: type(
            "S",
            (),
            {
                "META_GRAPH_VERSION": "v21.0",
                "IG_PUBLISH_HTTP_TIMEOUT_SECONDS": 20.0,
                "IG_STATUS_POLL_MAX_ATTEMPTS": 5,
                "IG_STATUS_POLL_DELAY_SECONDS": 0.0,
                "IG_PUBLISH_MAX_ATTEMPT_SECONDS": 45.0,
            },
        )(),
    )

    result = await InstagramPublisher().publish(_ig_payload())

    assert result.ok is True
    assert result.external_post_id == "media-1"
    assert result.container_id == "container-1"
    assert result.published_media_id == "media-1"
    assert result.permalink == "https://instagram.com/p/abc"
    assert any("media_publish" in str(c[1]) for c in fake.calls)
    assert any(c[0] == "GET" and "status_code" in str(c[2]) for c in fake.calls)


@pytest.mark.asyncio
async def test_instagram_publisher_status_polling_handles_in_progress_then_finished(monkeypatch):
    from app.services.social import instagram as ig_mod

    responses = [
        FakeResponse(200, {"id": "container-1"}),
        FakeResponse(200, {"id": "container-1", "status_code": "IN_PROGRESS"}),
        FakeResponse(200, {"id": "container-1", "status_code": "FINISHED"}),
        FakeResponse(200, {"id": "media-1"}),
        FakeResponse(200, {"id": "media-1", "permalink": "https://instagram.com/p/xyz"}),
    ]
    fake = FakeAsyncClient(responses)
    monkeypatch.setattr(ig_mod.httpx, "AsyncClient", lambda timeout=None: fake)
    orig_sleep = ig_mod.asyncio.sleep
    monkeypatch.setattr(ig_mod.asyncio, "sleep", lambda *_args, **_kwargs: orig_sleep(0))
    monkeypatch.setattr(
        ig_mod,
        "get_settings",
        lambda: type(
            "S",
            (),
            {
                "META_GRAPH_VERSION": "v21.0",
                "IG_PUBLISH_HTTP_TIMEOUT_SECONDS": 20.0,
                "IG_STATUS_POLL_MAX_ATTEMPTS": 5,
                "IG_STATUS_POLL_DELAY_SECONDS": 0.0,
                "IG_PUBLISH_MAX_ATTEMPT_SECONDS": 45.0,
            },
        )(),
    )

    result = await InstagramPublisher().publish(_ig_payload())
    assert result.ok is True
    assert result.external_post_id == "media-1"


@pytest.mark.asyncio
async def test_instagram_publisher_timeout_after_create_is_ambiguous(monkeypatch):
    import httpx as real_httpx
    from app.services.social import instagram as ig_mod

    responses = [
        FakeResponse(200, {"id": "container-1"}),
        real_httpx.TimeoutException("timeout"),
    ]
    fake = FakeAsyncClient(responses)
    monkeypatch.setattr(ig_mod.httpx, "AsyncClient", lambda timeout=None: fake)
    monkeypatch.setattr(
        ig_mod,
        "get_settings",
        lambda: type(
            "S",
            (),
            {
                "META_GRAPH_VERSION": "v21.0",
                "IG_PUBLISH_HTTP_TIMEOUT_SECONDS": 20.0,
                "IG_STATUS_POLL_MAX_ATTEMPTS": 2,
                "IG_STATUS_POLL_DELAY_SECONDS": 0.0,
                "IG_PUBLISH_MAX_ATTEMPT_SECONDS": 45.0,
            },
        )(),
    )

    result = await InstagramPublisher().publish(_ig_payload())
    assert result.ok is False
    assert result.category == PublishFailureCategory.ambiguous
    assert result.container_id == "container-1"
    assert "access_token" not in (result.error_message or "").lower()


@pytest.mark.asyncio
async def test_instagram_publisher_rate_limit_2207042_is_blocked_no_retry_storm(monkeypatch):
    from app.services.social import instagram as ig_mod

    responses = [
        FakeResponse(
            400,
            {
                "error": {
                    "message": "content publishing limit reached",
                    "code": 2207042,
                    "error_subcode": 2207042,
                }
            },
        )
    ]
    fake = FakeAsyncClient(responses)
    monkeypatch.setattr(ig_mod.httpx, "AsyncClient", lambda timeout=None: fake)
    monkeypatch.setattr(ig_mod, "get_settings", lambda: type("S", (), {"META_GRAPH_VERSION": "v21.0"})())

    result = await InstagramPublisher().publish(_ig_payload())
    assert result.ok is False
    assert result.category == PublishFailureCategory.permanent
    assert result.error_code in {"ig_rate_limit_blocked", "ig_content_publishing_limit"}
    assert "aguarde" in (result.error_message or "").lower()
    assert "access_token" not in (result.error_message or "").lower()


@pytest.mark.asyncio
async def test_instagram_publisher_permalink_failure_is_best_effort(monkeypatch):
    from app.services.social import instagram as ig_mod

    responses = [
        FakeResponse(200, {"id": "container-1"}),
        FakeResponse(200, {"id": "container-1", "status_code": "FINISHED"}),
        FakeResponse(200, {"id": "media-1"}),
        FakeResponse(500, {"error": {"message": "temporary"}}),
    ]
    fake = FakeAsyncClient(responses)
    monkeypatch.setattr(ig_mod.httpx, "AsyncClient", lambda timeout=None: fake)
    monkeypatch.setattr(ig_mod, "get_settings", lambda: type("S", (), {"META_GRAPH_VERSION": "v21.0", "IG_STATUS_POLL_MAX_ATTEMPTS": 2, "IG_STATUS_POLL_DELAY_SECONDS": 0.0, "IG_PUBLISH_MAX_ATTEMPT_SECONDS": 45.0, "IG_PUBLISH_HTTP_TIMEOUT_SECONDS": 20.0})())

    result = await InstagramPublisher().publish(_ig_payload())
    assert result.ok is True
    assert result.external_post_id == "media-1"
    assert result.permalink is None
