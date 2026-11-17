"""Intent parsing/orchestration: LLM candidate -> deterministic safe contract.

Pure service layer (no FastAPI/DB). User text is untrusted data handled by the
intent client; final contract is server-authoritative via mapper.
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from pydantic import ValidationError

from app.services.intent.client import IntentExtractionError, call_intent_llm
from app.services.intent.mapper import build_empty_intent, map_intent
from app.services.intent.schema import IntentContract, IntentLLMOutput


def _is_empty_input(text: str | None) -> bool:
    return text is None or not str(text).strip()


async def parse_intent(
    text: str | None,
    settings: Any,
    *,
    client: Any | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    timeout_seconds: float | int | None = None,
) -> IntentLLMOutput:
    """Return LLM-validated intent candidate; empty input yields null candidate without LLM."""
    if _is_empty_input(text):
        return IntentLLMOutput()
    return await call_intent_llm(
        str(text).strip(), settings, client=client, sleep=sleep, timeout_seconds=timeout_seconds
    )


def _is_effectively_empty(contract: IntentContract) -> bool:
    applied = contract.applied_params
    if applied.q is not None or applied.city is not None or applied.sort is not None:
        return False
    for fs in contract.field_statuses:
        status = getattr(fs.status, "value", fs.status)
        if status in {"aplicado", "aproximado"}:
            return False
    return True


async def extract_and_map_intent(
    text: str | None,
    settings: Any,
    *,
    client: Any | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    timeout_seconds: float | int | None = None,
) -> IntentContract:
    """Produce final deterministic IntentContract.

    Empty input degrades to a safe empty contract. Extraction/provider failures
    propagate so the caller (API layer) can classify timeout vs LLM unavailability
    and return the appropriate user-facing degradation.
    """
    raw_text = "" if text is None else str(text)
    if _is_empty_input(text):
        return build_empty_intent(text, reason_code="empty_input")

    candidate = await parse_intent(
        text, settings, client=client, sleep=sleep, timeout_seconds=timeout_seconds
    )

    contract = map_intent(candidate, raw_text=raw_text)
    if _is_effectively_empty(contract):
        return build_empty_intent(text, reason_code="no_extractable_params")
    return contract
