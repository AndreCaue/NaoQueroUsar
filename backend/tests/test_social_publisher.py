"""Contrato SocialPublisher/FacebookPublisher (Phase 17)."""

from __future__ import annotations

import asyncio
import inspect

from app.services.social import (
    FacebookPublisher,
    PublishFailureCategory,
    PublishResult,
    SocialPostPayload,
)


def test_publish_result_and_failure_categories_contract() -> None:
    ok = PublishResult(ok=True, external_post_id="ext-123")
    fail = PublishResult(
        ok=False,
        external_post_id=None,
        category=PublishFailureCategory.transient,
        error_message="falha temporária segura",
    )
    ambiguous = PublishResult(ok=False, category=PublishFailureCategory.ambiguous)

    assert ok.ok is True and ok.external_post_id == "ext-123"
    assert fail.ok is False and fail.category is PublishFailureCategory.transient
    assert fail.error_message == "falha temporária segura"
    assert PublishFailureCategory.permanent.value == "permanent"
    assert PublishFailureCategory.unknown.value == "unknown"
    assert ambiguous.category is PublishFailureCategory.ambiguous


def test_social_post_payload_minimal_typed_fields() -> None:
    payload = SocialPostPayload(job_id="job-1", provider="facebook", message="texto", link=None)
    assert payload.job_id == "job-1"
    assert payload.provider == "facebook"
    assert payload.message == "texto"
    assert payload.link is None


def test_facebook_publisher_async_contract_and_safe_failure_without_context() -> None:
    publisher = FacebookPublisher()
    assert hasattr(publisher, "publish") and callable(publisher.publish)
    assert inspect.iscoroutinefunction(FacebookPublisher.publish)
    sig = inspect.signature(FacebookPublisher.publish)
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
