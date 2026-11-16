import httpx
import pytest

from app.services.social.facebook import FacebookPublisher
from app.services.social.types import PublishFailureCategory, SocialPostPayload


@pytest.mark.asyncio
async def test_facebook_publisher_posts_message_link_and_returns_external_id(monkeypatch):
    calls = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"id": "123_456"}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            calls["init_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, data=None):
            calls["url"] = url
            calls["data"] = data
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        "app.services.social.facebook.get_settings",
        lambda: type("S", (), {"META_GRAPH_VERSION": "v21.0"})(),
    )

    publisher = FacebookPublisher()
    result = await publisher.publish(
        SocialPostPayload(
            job_id="job-1",
            provider="facebook",
            message="Olá vaga",
            link="https://site.exemplo/?vaga=job-1",
            page_id="page-1",
            page_access_token="page-token",
        )
    )

    assert result.ok is True
    assert result.external_post_id == "123_456"
    assert calls["url"] == "https://graph.facebook.com/v21.0/page-1/feed"
    assert calls["data"]["message"] == "Olá vaga"
    assert calls["data"]["link"] == "https://site.exemplo/?vaga=job-1"
    assert calls["data"]["access_token"] == "page-token"


@pytest.mark.asyncio
async def test_facebook_publisher_classifies_transient_and_ambiguous_errors(monkeypatch):
    class TransientResponse:
        status_code = 503

        def json(self):
            return {"error": {"message": "temp"}}

    class TransientClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, data=None):
            return TransientResponse()

    monkeypatch.setattr(httpx, "AsyncClient", TransientClient)
    monkeypatch.setattr(
        "app.services.social.facebook.get_settings",
        lambda: type("S", (), {"META_GRAPH_VERSION": "v21.0"})(),
    )
    publisher = FacebookPublisher()
    payload = SocialPostPayload(
        job_id="job-1",
        provider="facebook",
        message="msg",
        link=None,
        page_id="p",
        page_access_token="t",
    )
    result = await publisher.publish(payload)
    assert result.ok is False
    assert result.category == PublishFailureCategory.transient
    assert "automática" in (result.error_message or "").lower() or "tempor" in (result.error_message or "").lower()

    class RateLimitResponse:
        status_code = 429

        def json(self):
            return {"error": {"message": "rate limit"}}

    class RateLimitClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, data=None):
            return RateLimitResponse()

    monkeypatch.setattr(httpx, "AsyncClient", RateLimitClient)
    result = await publisher.publish(payload)
    assert result.ok is False
    assert result.category == PublishFailureCategory.transient

    class TimeoutClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, data=None):
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "AsyncClient", TimeoutClient)
    result = await publisher.publish(payload)
    assert result.ok is False
    assert result.category == PublishFailureCategory.ambiguous
    assert "duplic" in (result.error_message or "").lower() or "confirmar" in (result.error_message or "").lower()

    class PermanentResponse:
        status_code = 401

        def json(self):
            return {"error": {"message": "invalid token", "type": "OAuthException", "code": 190}}

    class PermanentClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, data=None):
            return PermanentResponse()

    monkeypatch.setattr(httpx, "AsyncClient", PermanentClient)
    result = await publisher.publish(payload)
    assert result.ok is False
    assert result.category == PublishFailureCategory.permanent
    assert "não foi possível publicar" in (result.error_message or "").lower() or "revise" in (result.error_message or "").lower()
