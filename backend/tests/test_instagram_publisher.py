"""Contrato/comportamento do InstagramPublisher (Phase 31)."""

from __future__ import annotations

import asyncio
import inspect

from app.services.social.instagram import InstagramPublisher
from app.services.social.types import PublishFailureCategory, PublishResult, SocialPostPayload


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
