"""Unit tests for the Cloudflare Turnstile Siteverify client (Phase 3).

Every test runs **offline**: the httpx client is built on ``httpx.MockTransport``,
so no request ever leaves the process. The suite proves the two properties the
whole phase depends on:

- the gate **fails closed** — any transport/HTTP/JSON error returns
  ``success=False`` and never lets the contact through (D-13);
- the ``action`` binding — a token minted for ``login`` cannot be replayed on
  ``reveal`` and vice-versa (T-03-03).
"""

from __future__ import annotations

import logging
from urllib.parse import parse_qs

import httpx
import pytest

from app.services.turnstile import (
    SITEVERIFY_URL,
    TURNSTILE_CHALLENGE_ERRORS,
    TURNSTILE_UNAVAILABLE_ERRORS,
    TurnstileResult,
    TurnstileVerifier,
    turnstile_error_detail,
)

SECRET = "0xTEST-secret-value-not-a-real-key"


def _json_handler(payload: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return handler


async def _verify(handler, **kwargs) -> tuple[TurnstileResult, list[httpx.Request]]:
    """Run ``verify`` against a mock transport; return the result and requests."""
    calls: list[httpx.Request] = []

    def recording_handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    transport = httpx.MockTransport(recording_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        verifier = TurnstileVerifier(secret=SECRET, client=client)
        result = await verifier.verify(**kwargs)
    return result, calls


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_verify_success_returns_action_and_no_error_codes():
    result, calls = await _verify(
        _json_handler({"success": True, "action": "reveal"}),
        token="token-abc",
        remoteip="203.0.113.9",
        expected_action="reveal",
    )

    assert result.success is True
    assert result.action == "reveal"
    assert result.error_codes == []
    assert len(calls) == 1


async def test_verify_failure_returns_siteverify_error_codes():
    result, _ = await _verify(
        _json_handler({"success": False, "error-codes": ["timeout-or-duplicate"]}),
        token="token-abc",
    )

    assert result.success is False
    assert result.error_codes == ["timeout-or-duplicate"]


# ---------------------------------------------------------------------------
# Action binding (T-03-03) — a token is bound to the flow that minted it
# ---------------------------------------------------------------------------


async def test_verify_rejects_token_minted_for_another_action():
    result, _ = await _verify(
        _json_handler({"success": True, "action": "login"}),
        token="token-abc",
        expected_action="reveal",
    )

    assert result.success is False
    assert result.error_codes == ["action-mismatch"]
    assert result.action == "login"


async def test_verify_accepts_token_when_action_matches():
    result, _ = await _verify(
        _json_handler({"success": True, "action": "login"}),
        token="token-abc",
        expected_action="login",
    )

    assert result.success is True
    assert result.action == "login"
    assert result.error_codes == []


# ---------------------------------------------------------------------------
# Fail closed (D-13) — the gate never opens because *we* broke
# ---------------------------------------------------------------------------


async def test_verify_network_error_fails_closed():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    result, _ = await _verify(handler, token="token-abc")

    assert result.success is False
    assert result.error_codes == ["internal-error"]


async def test_verify_timeout_fails_closed():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    result, _ = await _verify(handler, token="token-abc")

    assert result.success is False
    assert result.error_codes == ["internal-error"]


async def test_verify_http_500_fails_closed():
    result, _ = await _verify(
        lambda request: httpx.Response(500, text="boom"),
        token="token-abc",
    )

    assert result.success is False
    assert result.error_codes == ["internal-error"]


async def test_verify_invalid_json_body_fails_closed():
    result, _ = await _verify(
        lambda request: httpx.Response(200, text="<html>not json</html>"),
        token="token-abc",
    )

    assert result.success is False
    assert result.error_codes == ["internal-error"]


async def test_verify_non_object_json_fails_closed():
    result, _ = await _verify(
        lambda request: httpx.Response(200, json=["unexpected"]),
        token="token-abc",
    )

    assert result.success is False
    assert result.error_codes == ["internal-error"]


async def test_verify_requires_a_boolean_success_flag():
    """A truthy non-boolean ``success`` is not a Cloudflare success."""
    result, _ = await _verify(
        _json_handler({"success": "yes"}),
        token="token-abc",
    )

    assert result.success is False


# ---------------------------------------------------------------------------
# Short-circuit — an empty token never reaches the network
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("token", ["", "   "])
async def test_verify_empty_token_never_calls_siteverify(token):
    result, calls = await _verify(
        _json_handler({"success": True, "action": "reveal"}),
        token=token,
    )

    assert result.success is False
    assert result.error_codes == ["missing-input-response"]
    assert calls == []


# ---------------------------------------------------------------------------
# Request shape — the secret goes out, the site key never does
# ---------------------------------------------------------------------------


async def test_verify_posts_form_with_secret_and_never_sitekey():
    result, calls = await _verify(
        _json_handler({"success": True, "action": "reveal"}),
        token="token-abc",
        remoteip="203.0.113.9",
        expected_action="reveal",
        idempotency_key="idem-123",
    )

    assert result.success is True
    assert len(calls) == 1
    assert str(calls[0].url) == SITEVERIFY_URL
    assert calls[0].method == "POST"

    form = parse_qs(calls[0].content.decode())
    assert form["secret"] == [SECRET]
    assert form["response"] == ["token-abc"]
    assert form["remoteip"] == ["203.0.113.9"]
    assert form["idempotency_key"] == ["idem-123"]
    assert "sitekey" not in form


async def test_verify_omits_optional_fields_when_absent():
    _, calls = await _verify(
        _json_handler({"success": True, "action": "reveal"}),
        token="token-abc",
    )

    form = parse_qs(calls[0].content.decode())
    assert "remoteip" not in form
    assert "idempotency_key" not in form


# ---------------------------------------------------------------------------
# Log hygiene (T-03-05) — the token and the secret never reach the log
# ---------------------------------------------------------------------------


async def test_verify_logs_neither_token_nor_secret(caplog):
    caplog.set_level(logging.WARNING, logger="app.services.turnstile")

    await _verify(
        _json_handler({"success": False, "error-codes": ["timeout-or-duplicate"]}),
        token="super-secret-token",
    )

    assert caplog.records, "the rejection must be logged (D-14 layer b)"
    logged = "\n".join(
        [record.getMessage() for record in caplog.records]
        + [str(record.__dict__) for record in caplog.records]
    )
    assert "super-secret-token" not in logged
    assert SECRET not in logged


# ---------------------------------------------------------------------------
# Error-code taxonomy and pt-BR copy
# ---------------------------------------------------------------------------


def test_error_code_taxonomy_covers_the_documented_codes():
    assert "timeout-or-duplicate" in TURNSTILE_CHALLENGE_ERRORS
    assert "action-mismatch" in TURNSTILE_CHALLENGE_ERRORS
    assert "internal-error" in TURNSTILE_UNAVAILABLE_ERRORS
    assert "invalid-input-secret" in TURNSTILE_UNAVAILABLE_ERRORS
    assert not (TURNSTILE_CHALLENGE_ERRORS & TURNSTILE_UNAVAILABLE_ERRORS)


def test_turnstile_error_detail_uses_challenge_copy():
    for code in ("timeout-or-duplicate", "invalid-input-response", "bad-request"):
        assert turnstile_error_detail([code]) == (
            "Verificação anti-bot falhou — tente novamente"
        )


def test_turnstile_error_detail_uses_unavailable_copy():
    for code in ("internal-error", "invalid-input-secret", "missing-input-secret"):
        assert turnstile_error_detail([code]) == (
            "Verificação indisponível — tente novamente em instantes"
        )


def test_turnstile_error_detail_defaults_to_challenge_copy():
    assert turnstile_error_detail([]) == "Verificação anti-bot falhou — tente novamente"


def test_turnstile_result_defaults_to_no_error_codes():
    result = TurnstileResult(success=True)
    assert result.error_codes == []
    assert result.action is None
    assert result.hostname is None


def test_siteverify_url_is_the_official_cloudflare_endpoint():
    assert SITEVERIFY_URL == (
        "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    )


async def test_verify_parses_a_realistic_siteverify_payload():
    payload = {
        "success": True,
        "challenge_ts": "2026-10-21T22:00:00Z",
        "hostname": "nqu.app",
        "action": "reveal",
        "cdata": "job-123",
    }

    result, _ = await _verify(_json_handler(payload), token="token-abc")

    assert result.success is True
    assert result.action == "reveal"
    assert result.hostname == "nqu.app"


async def test_verify_keeps_error_codes_from_a_realistic_failure_payload():
    payload = {
        "success": False,
        "error-codes": ["invalid-input-response"],
        "hostname": "nqu.app",
    }

    result, _ = await _verify(_json_handler(payload), token="token-abc")

    assert result.success is False
    assert result.error_codes == ["invalid-input-response"]
    assert result.hostname == "nqu.app"
