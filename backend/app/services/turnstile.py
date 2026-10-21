"""Cloudflare Turnstile Siteverify client (Phase 3, SECR-01).

The public job board never exposes a contact without a Turnstile token, and a
client-side-only check would be trivially bypassed by a scraper. So the token
travels to the backend, the backend asks Cloudflare whether the token is real,
and **only then** the contact is released.

Two properties are non-negotiable here:

- **Fail closed (D-13).** Every failure of *our* side — the network is down,
  Cloudflare answers 5xx, the body is not JSON, the token is empty — resolves
  to ``success=False``. There is no degraded mode and no fail-open path: a
  broken backend never turns into a public contact list.
- **Action binding (T-03-03).** The Siteverify response carries the ``action``
  the token was minted for. A token minted for ``login`` is rejected on the
  ``reveal`` flow (and vice-versa), so a token cannot be harvested in one flow
  and replayed in the other.

The secret only ever travels from the backend to Cloudflare, and neither the
secret nor the token is ever logged (T-03-05).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# The challenge itself was refused: the token is missing, expired, replayed or
# was minted for another action. The user can simply try again.
TURNSTILE_CHALLENGE_ERRORS: frozenset[str] = frozenset(
    {
        "invalid-input-response",
        "missing-input-response",
        "timeout-or-duplicate",
        "bad-request",
        "action-mismatch",
    }
)

# The verification itself could not be performed: our side or Cloudflare's is
# broken (network, 5xx, invalid secret). Retrying later may work — saying
# "anti-bot failed" here would send the user down the wrong path.
TURNSTILE_UNAVAILABLE_ERRORS: frozenset[str] = frozenset(
    {
        "internal-error",
        "missing-input-secret",
        "invalid-input-secret",
    }
)

CHALLENGE_MESSAGE = "Verificação anti-bot falhou — tente novamente"
UNAVAILABLE_MESSAGE = "Verificação indisponível — tente novamente em instantes"


@dataclass(frozen=True)
class TurnstileResult:
    """Outcome of a Siteverify call.

    ``error_codes`` mirrors Cloudflare's ``error-codes`` array; the local
    failures that never reached Cloudflare use ``internal-error``.
    """

    success: bool
    error_codes: list[str] = field(default_factory=list)
    action: str | None = None
    hostname: str | None = None


def turnstile_error_detail(error_codes: list[str]) -> str:
    """Map Siteverify error codes to the pt-BR message shown to the user.

    The copy is shared by every flow (reveal, login) so the wording lives in a
    single place — the routers import this function instead of duplicating it.
    """
    if any(code in TURNSTILE_UNAVAILABLE_ERRORS for code in error_codes):
        return UNAVAILABLE_MESSAGE
    return CHALLENGE_MESSAGE


class TurnstileVerifier:
    """Async client for the Cloudflare Siteverify endpoint."""

    def __init__(
        self,
        secret: str,
        *,
        timeout_seconds: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._secret = secret
        self._timeout = timeout_seconds
        self._client = client

    async def verify(
        self,
        token: str,
        remoteip: str | None = None,
        *,
        expected_action: str | None = None,
        idempotency_key: str | None = None,
    ) -> TurnstileResult:
        """Verify a Turnstile token against Cloudflare.

        Returns a :class:`TurnstileResult`; it never raises for an operational
        failure, because every failure must close the gate (D-13).
        """
        if not token or not token.strip():
            logger.warning(
                "turnstile_rejected",
                extra={"turnstile_error_codes": "missing-input-response"},
            )
            return TurnstileResult(
                success=False, error_codes=["missing-input-response"]
            )

        data = {"secret": self._secret, "response": token}
        if remoteip:
            data["remoteip"] = remoteip
        if idempotency_key:
            data["idempotency_key"] = idempotency_key

        try:
            payload = await self._post(data)
        except httpx.HTTPError:
            # Transport error, timeout or 5xx — our side (or Cloudflare's) is
            # broken. Fail closed.
            logger.warning(
                "turnstile_rejected",
                extra={"turnstile_error_codes": "internal-error"},
            )
            return TurnstileResult(success=False, error_codes=["internal-error"])
        except ValueError:
            # Body is not valid JSON (or not a JSON object).
            logger.warning(
                "turnstile_rejected",
                extra={"turnstile_error_codes": "internal-error"},
            )
            return TurnstileResult(success=False, error_codes=["internal-error"])

        error_codes = [
            str(code) for code in (payload.get("error-codes") or [])
        ]
        action = payload.get("action")
        hostname = payload.get("hostname")
        success = payload.get("success") is True

        if not success:
            logger.warning(
                "turnstile_rejected",
                extra={"turnstile_error_codes": ",".join(error_codes)},
            )
            return TurnstileResult(
                success=False,
                error_codes=error_codes,
                action=action,
                hostname=hostname,
            )

        if expected_action and action != expected_action:
            # The token is valid but was minted for another flow — reject it
            # instead of accepting a cross-flow replay (T-03-03).
            logger.warning(
                "turnstile_action_mismatch",
                extra={"turnstile_action": str(action)},
            )
            return TurnstileResult(
                success=False,
                error_codes=["action-mismatch"],
                action=action,
                hostname=hostname,
            )

        return TurnstileResult(
            success=True,
            error_codes=[],
            action=action,
            hostname=hostname,
        )

    async def _post(self, data: dict[str, str]) -> dict:
        """POST the verification form to Cloudflare and return the JSON body."""
        if self._client is not None:
            return await self._post_with(self._client, data)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await self._post_with(client, data)

    async def _post_with(
        self, client: httpx.AsyncClient, data: dict[str, str]
    ) -> dict:
        response = await client.post(
            SITEVERIFY_URL, data=data, timeout=self._timeout
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Siteverify response is not a JSON object")
        return payload
