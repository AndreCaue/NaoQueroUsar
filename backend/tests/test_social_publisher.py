"""SOC-05: contrato SocialPublisher e FacebookPublisher stub (sem DB/I-O externo)."""

from __future__ import annotations

import asyncio
import inspect
from pathlib import Path

from app.services.social import (
    FacebookPublisher,
    PublishFailureCategory,
    PublishResult,
    SocialPostPayload,
    SocialPublisher,
)
from app.services.social import facebook as facebook_module


def test_publish_result_and_failure_categories_contract() -> None:
    ok = PublishResult(ok=True, external_post_id="ext-123")
    fail = PublishResult(
        ok=False,
        external_post_id=None,
        category=PublishFailureCategory.transient,
        error_message="falha temporária segura",
    )

    assert ok.ok is True and ok.external_post_id == "ext-123"
    assert fail.ok is False and fail.category is PublishFailureCategory.transient
    assert fail.error_message == "falha temporária segura"
    assert PublishFailureCategory.permanent.value == "permanent"
    assert PublishFailureCategory.unknown.value == "unknown"


def test_social_post_payload_minimal_typed_fields() -> None:
    payload = SocialPostPayload(job_id="job-1", provider="facebook", message="texto", link=None)
    assert payload.job_id == "job-1"
    assert payload.provider == "facebook"
    assert payload.message == "texto"
    assert payload.link is None


def test_facebook_publisher_respects_async_contract_and_returns_controlled_stub_failure() -> None:
    publisher = FacebookPublisher()
    # Behavioral contract (SocialPublisher protocol is not runtime_checkable in impl): async publish -> PublishResult
    assert hasattr(publisher, "publish") and callable(publisher.publish)
    assert inspect.iscoroutinefunction(FacebookPublisher.publish)
    sig = inspect.signature(FacebookPublisher.publish)
    assert "post" in sig.parameters

    result = asyncio.run(publisher.publish(None))

    assert isinstance(result, PublishResult)
    assert result.ok is False
    assert result.external_post_id is None
    assert result.category is PublishFailureCategory.unknown
    assert result.error_message
    assert "stub" in result.error_message.lower() or "fase 14" in result.error_message.lower()


def test_facebook_publisher_stub_has_no_external_http_clients() -> None:
    social_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "social"
    for name in ("types.py", "publisher.py", "facebook.py"):
        text = (social_dir / name).read_text(encoding="utf-8")
        assert "httpx" not in text, f"{name} must not reference httpx"
        assert "requests" not in text, f"{name} must not reference requests"
    # sanity: module does not expose http client attributes
    assert not hasattr(facebook_module, "httpx")
    assert not hasattr(facebook_module, "requests")
