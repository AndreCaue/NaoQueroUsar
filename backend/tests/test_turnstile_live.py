"""Opt-in smoke test against the **real** Cloudflare Siteverify API (Phase 3).

Why this file exists
--------------------
The whole suite of plans 03-01..03-04 runs 100% offline: the Turnstile
verifier is replaced by ``FakeTurnstileVerifier`` through
``dependency_overrides`` (see ``tests/conftest.py``). That is the right
default for CI — fast, deterministic, no quota — but it means **nothing in
the repo proves that the real round-trip works**. A fake that always answers
``success=True`` would look exactly like a working integration.

This file closes that gap: it talks to
``https://challenges.cloudflare.com/turnstile/v0/siteverify`` for real, using
Cloudflare's three public **testing** secret keys.

Opt-in by design (T-03-23)
---------------------------
The tests only run when ``TURNSTILE_LIVE=1`` is set; otherwise the whole file
is skipped. The regular suite must stay offline and must not depend on
outbound network access (or on the Cloudflare quota).

Run it explicitly::

    cd backend
    TURNSTILE_LIVE=1 .venv\\Scripts\\python.exe -m pytest tests/test_turnstile_live.py -q

The three secrets are the ones documented by Cloudflare
(https://developers.cloudflare.com/turnstile/troubleshooting/testing/):

===========================  ==========================================
Secret                       Behaviour
===========================  ==========================================
``1x000...AA``               always passes validation
``2x000...AA``               always fails validation
``3x000...AA``               always fails with "token already spent"
                             (``timeout-or-duplicate``)
===========================  ==========================================

They are public test values — not credentials — and they only work against
Cloudflare's own testing mode. The backend refuses them outside dev
(D-12, plan 03-01), so they can never reach production.

The file imports **only** ``app.services.turnstile``: it never builds the app,
never touches the database and never mutates global state.
"""

import os

import pytest

from app.services.turnstile import TurnstileVerifier

# Cloudflare's public testing secrets (see the module docstring).
ALWAYS_PASS_SECRET = "1x0000000000000000000000000000000AA"
ALWAYS_FAIL_SECRET = "2x0000000000000000000000000000000AA"
ALWAYS_ERROR_SECRET = "3x0000000000000000000000000000000AA"

# A token that is not a real Turnstile token. The testing secrets accept it
# (they never challenge, they answer from a fixed table).
DUMMY_TOKEN = "dummy-token-value"

# The live test is opt-in: without the env var the file is skipped, so the
# regular suite keeps running offline (T-03-23).
pytestmark = pytest.mark.skipif(
    os.environ.get("TURNSTILE_LIVE") != "1",
    reason="live Siteverify test disabled (set TURNSTILE_LIVE=1)",
)

# The verification talks to the internet — give it more room than the 10s
# default of the service, so a slow round-trip is not mistaken for a failure.
LIVE_TIMEOUT_SECONDS = 20.0


async def test_live_siteverify_always_pass_secret() -> None:
    """The always-pass secret must be accepted by the real Siteverify."""
    verifier = TurnstileVerifier(
        secret=ALWAYS_PASS_SECRET, timeout_seconds=LIVE_TIMEOUT_SECONDS
    )

    result = await verifier.verify(DUMMY_TOKEN)

    assert result.success is True, (
        "the always-pass testing secret was refused by Cloudflare: "
        f"error_codes={result.error_codes} action={result.action!r}"
    )
    assert result.error_codes == [], (
        f"a successful verification must carry no error code, got {result.error_codes}"
    )


async def test_live_siteverify_always_fail_secret() -> None:
    """The always-fail secret must be refused by the real Siteverify."""
    verifier = TurnstileVerifier(
        secret=ALWAYS_FAIL_SECRET, timeout_seconds=LIVE_TIMEOUT_SECONDS
    )

    result = await verifier.verify(DUMMY_TOKEN)

    assert result.success is False, (
        "the always-fail testing secret was accepted by Cloudflare — "
        "the gate would be open for a secret that must never pass"
    )


async def test_live_siteverify_error_secret_fails_closed() -> None:
    """The always-error secret must fail closed **and** be explainable.

    A failure that closes the gate but says nothing is a failure the operator
    cannot act on (D-13): ``error_codes`` has to be non-empty so the backend
    can tell "the challenge was refused" from "the verification broke".
    """
    verifier = TurnstileVerifier(
        secret=ALWAYS_ERROR_SECRET, timeout_seconds=LIVE_TIMEOUT_SECONDS
    )

    result = await verifier.verify(DUMMY_TOKEN)

    assert result.success is False, (
        "the always-error testing secret was accepted by Cloudflare — "
        "an unavailable verification must never look like a pass (D-13)"
    )
    assert result.error_codes, (
        "the failure must be explainable: error_codes was empty, so the "
        "backend could not tell a refused challenge from a broken verification"
    )
