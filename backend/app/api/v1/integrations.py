from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.deps import get_session, require_admin
from app.schemas.social_integrations import (
    MetaActionResponse,
    MetaIntegrationStatus,
    MetaOAuthStartResponse,
    MetaPendingSelectionResponse,
    MetaSelectPageRequest,
)
from app.services.social.meta_oauth import (
    MetaOAuthConfigError,
    MetaOAuthGraphError,
    MetaOAuthPendingError,
    complete_oauth_callback,
    confirm_pending_selection,
    disconnect_meta as disconnect_meta_service,
    get_current_meta_status,
    get_oauth_start_response,
    list_pending_pages,
    verify_current_connection,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/integrations", tags=["admin-integrations"])

AdminClaims = Annotated[dict, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]

MISSING_META_CONFIG_DETAIL = "Integração com Facebook não configurada"
META_OAUTH_SCOPES = "pages_show_list,pages_manage_posts,pages_read_engagement"


def _safe_redirect(result: str, *, reason: str | None = None, pending: str | None = None) -> RedirectResponse:
    # Never include tokens/secrets/code/provider internals in redirect URLs.
    url = f"/admin/integracoes?result={result}"
    if pending and result == "select_page":
        url += f"&pending={pending}"
    elif reason and result == "error":
        url += f"&reason={reason}"
    return RedirectResponse(url=url, status_code=302)


@router.get("/meta/oauth/start", response_model=MetaOAuthStartResponse)
@router.post("/meta/oauth/start", response_model=MetaOAuthStartResponse)
async def start_meta_oauth(
    claims: Annotated[dict, Depends(require_admin)],
    settings: AppSettings,
) -> MetaOAuthStartResponse:
    _ = claims
    try:
        return get_oauth_start_response(settings)
    except MetaOAuthConfigError as exc:
        raise HTTPException(status_code=503, detail=MISSING_META_CONFIG_DETAIL) from exc


@router.get("/meta/oauth/callback")
async def meta_oauth_callback(
    request: Request,
    session: DbSession,
    settings: AppSettings,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_reason: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
) -> RedirectResponse:
    # Browser redirect endpoint: no Bearer auth, protected by signed state validation in service.
    _ = (request, error_reason, error_description)
    try:
        outcome = await complete_oauth_callback(
            session,
            code=code,
            state=state,
            error=error,
            settings=settings,
        )
    except Exception:  # noqa: BLE001 - callback must fail safe with redirect
        await session.rollback()
        logger.warning("meta_oauth_callback_failed_safe")
        return _safe_redirect("error", reason="callback_failed")

    result = str(outcome.get("result") or "error")
    if result == "connected":
        await session.commit()
        return _safe_redirect("connected")
    if result == "select_page":
        pending_nonce = str(outcome.get("pending_nonce") or outcome.get("pending") or "")
        if not pending_nonce:
            await session.rollback()
            return _safe_redirect("error", reason="pending_selection")
        await session.commit()
        return _safe_redirect("select_page", pending=pending_nonce)
    if result == "cancelled":
        await session.rollback()
        return _safe_redirect("cancelled")

    await session.rollback()
    reason = str(outcome.get("reason") or "error")
    if reason in {"invalid_state", "needs_reconnect", "not_configured", "no_pages", "transient"}:
        safe_reason = "invalid_state" if reason == "invalid_state" else reason
    else:
        safe_reason = "oauth_error"
    if reason == "needs_reconnect":
        # Definitive validation failure during callback should not persist connected state.
        # Service may have marked needs_reconnect in specific flows; commit only safe state transitions it performed.
        try:
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()
        return _safe_redirect("error", reason="needs_reconnect")
    return _safe_redirect("error", reason=safe_reason)


@router.get("/meta/status", response_model=MetaIntegrationStatus)
async def get_meta_status(
    claims: Annotated[dict, Depends(require_admin)],
    session: DbSession,
) -> MetaIntegrationStatus:
    _ = claims
    return await get_current_meta_status(session)


@router.post("/meta/verify", response_model=MetaActionResponse)
async def verify_meta_connection(
    claims: Annotated[dict, Depends(require_admin)],
    session: DbSession,
    settings: AppSettings,
) -> MetaActionResponse:
    _ = claims
    try:
        response = await verify_current_connection(session, settings)
        await session.commit()
        return response
    except MetaOAuthConfigError as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail=MISSING_META_CONFIG_DETAIL) from exc
    except Exception as exc:  # noqa: BLE001
        await session.rollback()
        logger.warning("meta_oauth_verify_failed_safe", extra={"error_type": type(exc).__name__})
        raise HTTPException(status_code=503, detail="Não foi possível verificar a conexão agora. Tente novamente.") from exc


async def _pending_selection_response(
    session: AsyncSession,
    settings: Settings,
    pending: str | None,
) -> MetaPendingSelectionResponse:
    pending_nonce = (pending or "").strip()
    if not pending_nonce:
        raise HTTPException(status_code=422, detail="Seleção de página inválida ou expirada.")
    try:
        return await list_pending_pages(session, pending_nonce, settings)
    except MetaOAuthPendingError as exc:
        raise HTTPException(status_code=404, detail="Seleção de página expirada. Inicie a conexão novamente.") from exc


@router.get("/meta/pending-selection", response_model=MetaPendingSelectionResponse)
@router.get("/meta/pending", response_model=MetaPendingSelectionResponse)
async def get_pending_meta_pages(
    claims: Annotated[dict, Depends(require_admin)],
    session: DbSession,
    settings: AppSettings,
    pending: str | None = Query(default=None),
) -> MetaPendingSelectionResponse:
    _ = claims
    return await _pending_selection_response(session, settings, pending)


@router.post("/meta/select-page", response_model=MetaActionResponse)
async def select_meta_page(
    claims: Annotated[dict, Depends(require_admin)],
    payload: MetaSelectPageRequest,
    session: DbSession,
    settings: AppSettings,
) -> MetaActionResponse:
    _ = claims
    try:
        response = await confirm_pending_selection(
            session,
            payload.pending_nonce,
            payload.page_id,
            settings,
        )
        await session.commit()
        return response
    except MetaOAuthPendingError as exc:
        await session.rollback()
        message = str(exc)
        status_code = 404 if "expirada" in message.lower() or "inicie a conexão" in message.lower() else 422
        raise HTTPException(status_code=status_code, detail=message) from exc
    except MetaOAuthGraphError as exc:
        await session.rollback()
        message = str(exc)
        if "Reconecte" in message or "inválida" in message.lower():
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=503, detail=message) from exc
    except MetaOAuthConfigError as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail=MISSING_META_CONFIG_DETAIL) from exc


@router.post("/meta/disconnect", response_model=MetaActionResponse)
async def disconnect_meta(
    claims: Annotated[dict, Depends(require_admin)],
    session: DbSession,
) -> MetaActionResponse:
    _ = claims
    response = await disconnect_meta_service(session)
    await session.commit()
    return response
