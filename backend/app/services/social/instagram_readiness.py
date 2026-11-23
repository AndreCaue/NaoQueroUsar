from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

import httpx

logger = logging.getLogger(__name__)

_GRAPH_TIMEOUT_SECONDS = 10.0

InstagramReadinessState = Literal[
    "ready",
    "not_connected",
    "missing_linkage",
    "missing_permissions",
    "needs_reconnect",
    "unknown",
]


@dataclass
class InstagramReadinessResult:
    ready: bool
    ig_user_id: str | None
    ig_username: str | None
    state: InstagramReadinessState
    message: str
    error_code: str | None = None


def _graph_base(settings: Any) -> str:
    graph_version = str(getattr(settings, "META_GRAPH_VERSION", "") or "").strip()
    if not graph_version:
        raise ValueError("META_GRAPH_VERSION ausente")
    return f"https://graph.facebook.com/{graph_version}"


async def _graph_get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=_GRAPH_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, params=params)
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        raise exc

    try:
        data = resp.json()
    except ValueError:
        data = {}

    if resp.status_code >= 400:
        err = httpx.HTTPStatusError("graph_error", request=resp.request, response=resp)
        setattr(err, "_safe_body", data if isinstance(data, dict) else {})
        raise err

    if not isinstance(data, dict):
        raise ValueError("invalid_graph_payload")
    return data


def _message_for_ready(ig_user_id: str | None, ig_username: str | None) -> str:
    if ig_username:
        return f"Conta Instagram vinculada: @{ig_username}"
    if ig_user_id:
        return f"Conta Instagram vinculada (ID: {ig_user_id})."
    return "Conta Instagram vinculada."


def _safe_error_code(body: Any) -> int | None:
    if not isinstance(body, dict):
        return None
    err = body.get("error")
    if isinstance(err, dict):
        code = err.get("code")
        if isinstance(code, int):
            return code
        if isinstance(code, str) and code.isdigit():
            return int(code)
    return None


def _is_permission_or_scope_error(exc: httpx.HTTPStatusError) -> bool:
    status = exc.response.status_code if exc.response is not None else 0
    if status not in (400, 401, 403):
        return False
    body = getattr(exc, "_safe_body", None)
    code = _safe_error_code(body)
    # Conservative: auth/permission Graph errors on IG probe are actionable reconnect.
    if status in (401, 403):
        return True
    # Common Meta permission/code shapes: 10/200/190 etc. Treat 400 with code as actionable.
    return code is not None


async def resolve_instagram_readiness(
    *, page_id: str, page_access_token_plain: str, settings: Any
) -> InstagramReadinessResult:
    """Resolve IG readiness for a Facebook Page.

    Uses the existing encrypted/stored Page token (plain value provided by caller).
    Returns safe actionable states; never raises raw provider errors across API boundary.
    IG readiness is additive; Facebook connection status remains authoritative for Facebook.
    """
    try:
        url = f"{_graph_base(settings)}/{page_id}"
        data = await _graph_get_json(
            url,
            {
                "fields": "instagram_business_account{id,username}",
                "access_token": page_access_token_plain,
            },
        )
    except (httpx.TimeoutException, httpx.RequestError):
        logger.warning(
            "instagram_readiness_transient_failure",
            extra={"error_type": "transient"},
        )
        return InstagramReadinessResult(
            ready=False,
            ig_user_id=None,
            ig_username=None,
            state="unknown",
            message="Não foi possível confirmar a prontidão do Instagram agora.",
            error_code="transient",
        )
    except httpx.HTTPStatusError as exc:
        if _is_permission_or_scope_error(exc):
            logger.warning(
                "instagram_readiness_permission_failure",
                extra={"error_type": "missing_permissions"},
            )
            return InstagramReadinessResult(
                ready=False,
                ig_user_id=None,
                ig_username=None,
                state="missing_permissions",
                message="Permissões do Instagram ausentes. Reconecte para autorizar o Instagram.",
                error_code="missing_permissions",
            )
        status = exc.response.status_code if exc.response is not None else 0
        if status >= 500 or status == 429:
            logger.warning(
                "instagram_readiness_transient_failure",
                extra={"error_type": "transient"},
            )
            return InstagramReadinessResult(
                ready=False,
                ig_user_id=None,
                ig_username=None,
                state="unknown",
                message="Não foi possível confirmar a prontidão do Instagram agora.",
                error_code="transient",
            )
        logger.warning(
            "instagram_readiness_graph_failure",
            extra={"error_type": "unknown"},
        )
        return InstagramReadinessResult(
            ready=False,
            ig_user_id=None,
            ig_username=None,
            state="unknown",
            message="Não foi possível confirmar a prontidão do Instagram agora.",
            error_code="graph_error",
        )
    except Exception:
        logger.warning(
            "instagram_readiness_unexpected_failure",
            extra={"error_type": "unknown"},
        )
        return InstagramReadinessResult(
            ready=False,
            ig_user_id=None,
            ig_username=None,
            state="unknown",
            message="Não foi possível confirmar a prontidão do Instagram agora.",
            error_code="unknown",
        )

    ig_raw = data.get("instagram_business_account") if isinstance(data, dict) else None
    ig = ig_raw if isinstance(ig_raw, dict) else {}
    ig_user_id = str(ig.get("id")) if ig.get("id") else None
    ig_username = ig.get("username") if isinstance(ig.get("username"), str) and ig.get("username") else None

    if ig_user_id:
        return InstagramReadinessResult(
            ready=True,
            ig_user_id=ig_user_id,
            ig_username=ig_username,
            state="ready",
            message=_message_for_ready(ig_user_id, ig_username),
            error_code=None,
        )

    return InstagramReadinessResult(
        ready=False,
        ig_user_id=None,
        ig_username=None,
        state="missing_linkage",
        message="Nenhuma conta Instagram Business/Creator vinculada a esta Página.",
        error_code="missing_linkage",
    )
