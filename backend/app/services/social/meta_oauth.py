from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from urllib.parse import urlencode

import httpx
import jwt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_account import SocialAccount, SocialAccountStatus
from app.models.social_oauth_pending import SocialOAuthPending
from app.schemas.social_integrations import (
    MetaActionResponse,
    MetaIntegrationAlert,
    MetaIntegrationStatus,
    MetaOAuthStartResponse,
    MetaPendingPage,
    MetaPendingSelectionResponse,
)
from app.services.social.crypto import encrypt_token

logger = logging.getLogger(__name__)

META_OAUTH_SCOPES = "pages_show_list,pages_manage_posts,pages_read_engagement"
META_OAUTH_STATE_TTL_SECONDS = 600
PENDING_SELECTION_TTL_MINUTES = 15
_GRAPH_TIMEOUT_SECONDS = 10.0
_MISSING_CONFIG_MESSAGE = "Integração com Facebook não configurada"
_SAFE_CALLBACK_ERROR = "Não foi possível conectar ao Facebook."
_SAFE_TRANSIENT_VERIFY = "Não foi possível verificar a conexão agora. Tente novamente."
_SAFE_PENDING_EXPIRED = "Seleção de página expirada. Inicie a conexão novamente."
_REQUIRED_META_SCOPES = {"pages_show_list", "pages_manage_posts", "pages_read_engagement"}


class MetaOAuthError(Exception):
    """Base safe domain error for Meta OAuth flow."""


class MetaOAuthStateError(MetaOAuthError):
    """Invalid or expired OAuth state."""


class MetaOAuthConfigError(MetaOAuthError):
    """Missing/invalid Meta OAuth configuration."""


class MetaOAuthPendingError(MetaOAuthError):
    """Invalid/expired/consumed pending selection."""


class MetaOAuthGraphError(MetaOAuthError):
    """Safe Graph/OAuth operation failure."""


def _safe_error(message: str) -> MetaOAuthError:
    return MetaOAuthError(message)


def _require_meta_config(settings: Any) -> None:
    required = {
        "META_APP_ID": getattr(settings, "META_APP_ID", ""),
        "META_APP_SECRET": getattr(settings, "META_APP_SECRET", ""),
        "META_OAUTH_REDIRECT_URI": getattr(settings, "META_OAUTH_REDIRECT_URI", ""),
        "META_GRAPH_VERSION": getattr(settings, "META_GRAPH_VERSION", ""),
    }
    missing = [name for name, value in required.items() if not str(value or "").strip()]
    if missing:
        raise MetaOAuthConfigError(_MISSING_CONFIG_MESSAGE)


def build_meta_oauth_state(secret: str) -> str:
    """Build signed stateless OAuth state (HS256) with purpose, nonce and exp."""
    now = datetime.now(timezone.utc)
    claims = {
        "purpose": "meta_oauth",
        "nonce": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(seconds=META_OAUTH_STATE_TTL_SECONDS),
    }
    return jwt.encode(claims, secret, algorithm="HS256")


def validate_meta_oauth_state(state: str, secret: str) -> dict[str, Any]:
    """Validate signed stateless OAuth state and reject invalid/expired/wrong-purpose."""
    try:
        claims = jwt.decode(state, secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise MetaOAuthStateError("Estado OAuth inválido ou expirado.") from exc
    if claims.get("purpose") != "meta_oauth":
        raise MetaOAuthStateError("Estado OAuth inválido ou expirado.")
    if not claims.get("nonce"):
        raise MetaOAuthStateError("Estado OAuth inválido ou expirado.")
    return claims


def build_meta_oauth_dialog_url(settings: Any) -> str:
    """Build Meta OAuth dialog URL using META_GRAPH_VERSION and required scopes."""
    _require_meta_config(settings)
    state = build_meta_oauth_state(getattr(settings, "JWT_SECRET"))
    params = {
        "client_id": str(settings.META_APP_ID),
        "redirect_uri": str(settings.META_OAUTH_REDIRECT_URI),
        "state": state,
        "response_type": "code",
        "scope": META_OAUTH_SCOPES,
    }
    return f"https://www.facebook.com/{settings.META_GRAPH_VERSION}/dialog/oauth?{urlencode(params)}"


def get_oauth_start_response(settings: Any) -> MetaOAuthStartResponse:
    return MetaOAuthStartResponse(redirect_url=build_meta_oauth_dialog_url(settings))


def _graph_base(settings: Any) -> str:
    graph_version = str(getattr(settings, "META_GRAPH_VERSION", "") or "").strip()
    if not graph_version:
        raise MetaOAuthConfigError(_MISSING_CONFIG_MESSAGE)
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
        setattr(err, "_safe_body", data)
        raise err
    if not isinstance(data, dict):
        raise MetaOAuthGraphError("Resposta inválida da integração.")
    return data


async def exchange_code_for_short_lived_user_token(code: str, settings: Any) -> str:
    _require_meta_config(settings)
    url = f"{_graph_base(settings)}/oauth/access_token"
    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": settings.META_OAUTH_REDIRECT_URI,
        "client_secret": settings.META_APP_SECRET,
        "code": code,
    }
    try:
        data = await _graph_get_json(url, params)
    except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as exc:
        logger.warning("meta_oauth_short_token_exchange_failed", extra={"error_type": type(exc).__name__})
        raise MetaOAuthGraphError(_SAFE_CALLBACK_ERROR) from exc
    token = data.get("access_token")
    if not token or not isinstance(token, str):
        raise MetaOAuthGraphError(_SAFE_CALLBACK_ERROR)
    return token


async def exchange_for_long_lived_user_token(short_lived_user_token: str, settings: Any) -> str:
    _require_meta_config(settings)
    url = f"{_graph_base(settings)}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": settings.META_APP_ID,
        "client_secret": settings.META_APP_SECRET,
        "fb_exchange_token": short_lived_user_token,
    }
    try:
        data = await _graph_get_json(url, params)
    except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as exc:
        logger.warning("meta_oauth_long_token_exchange_failed", extra={"error_type": type(exc).__name__})
        raise MetaOAuthGraphError(_SAFE_CALLBACK_ERROR) from exc
    token = data.get("access_token")
    if not token or not isinstance(token, str):
        raise MetaOAuthGraphError(_SAFE_CALLBACK_ERROR)
    return token


async def list_user_pages(long_lived_user_token: str, settings: Any) -> list[dict[str, Any]]:
    _require_meta_config(settings)
    url = f"{_graph_base(settings)}/me/accounts"
    params = {
        "fields": "id,name,access_token,tasks",
        "access_token": long_lived_user_token,
    }
    try:
        data = await _graph_get_json(url, params)
    except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as exc:
        logger.warning("meta_oauth_list_pages_failed", extra={"error_type": type(exc).__name__})
        raise MetaOAuthGraphError(_SAFE_CALLBACK_ERROR) from exc
    pages = data.get("data") or []
    if not isinstance(pages, list):
        raise MetaOAuthGraphError(_SAFE_CALLBACK_ERROR)
    eligible: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_id = page.get("id")
        page_token = page.get("access_token")
        if page_id and page_token:
            eligible.append(
                {
                    "page_id": str(page_id),
                    "page_name": page.get("name") if isinstance(page.get("name"), str) else None,
                    "page_access_token": str(page_token),
                }
            )
    return eligible


async def debug_token(input_token: str, settings: Any) -> dict[str, Any]:
    _require_meta_config(settings)
    url = f"{_graph_base(settings)}/debug_token"
    params = {
        "input_token": input_token,
        "access_token": f"{settings.META_APP_ID}|{settings.META_APP_SECRET}",
    }
    return await _graph_get_json(url, params)


def classify_verification_failure(exc_or_response: Any) -> Literal["definitive", "transient"]:
    """Classify verification outcome as definitive or transient (D-10)."""
    if isinstance(exc_or_response, (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError)):
        return "transient"
    if isinstance(exc_or_response, httpx.HTTPStatusError):
        status = exc_or_response.response.status_code if exc_or_response.response else 0
        if status >= 500 or status == 429:
            return "transient"
        if status in (400, 401, 403):
            return "definitive"
        return "transient"
    # Unknown/indeterminate => conservative transient to preserve valid connection.
    return "transient"


def evaluate_debug_token_payload(payload: dict[str, Any], settings: Any | None = None) -> dict[str, Any]:
    """Evaluate /debug_token payload and return safe validity/classification summary."""
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return {"valid": False, "classification": "transient", "status": "unknown"}

    is_valid = bool(data.get("is_valid"))
    scopes = set()
    for key in ("scopes", "granular_scopes"):
        value = data.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    scopes.add(item)
                elif isinstance(item, dict):
                    scope = item.get("scope")
                    if isinstance(scope, str):
                        scopes.add(scope)
    has_required_scopes = _REQUIRED_META_SCOPES.issubset(scopes) if scopes else False

    expires_at = data.get("expires_at")
    expired = False
    if isinstance(expires_at, (int, float)) and expires_at > 0:
        expired = datetime.fromtimestamp(expires_at, tz=timezone.utc) <= datetime.now(timezone.utc)

    if not is_valid or expired:
        return {"valid": False, "classification": "definitive", "status": SocialAccountStatus.needs_reconnect.value}
    if scopes and not has_required_scopes:
        return {"valid": False, "classification": "definitive", "status": SocialAccountStatus.needs_reconnect.value}
    # Valid token (and scopes ok/unknown in conservative-compatible form)
    return {"valid": True, "classification": "definitive", "status": SocialAccountStatus.connected.value}


async def _classify_current_token(input_token: str, settings: Any) -> tuple[Literal["definitive", "transient"], bool]:
    try:
        payload = await debug_token(input_token, settings)
    except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as exc:
        return classify_verification_failure(exc), False
    except Exception:
        return "transient", False
    evaluated = evaluate_debug_token_payload(payload, settings)
    classification = evaluated.get("classification", "transient")
    if classification not in ("definitive", "transient"):
        classification = "transient"
    return classification, bool(evaluated.get("valid"))


async def get_current_meta_status(session: AsyncSession) -> MetaIntegrationStatus:
    # Pending selection (valid/unconsumed/unexpired) flag
    now = datetime.now(timezone.utc)
    pending_stmt = (
        select(SocialOAuthPending.id)
        .where(
            SocialOAuthPending.provider == "facebook",
            SocialOAuthPending.consumed_at.is_(None),
            SocialOAuthPending.expires_at > now,
        )
        .limit(1)
    )
    pending_res = await session.execute(pending_stmt)
    pending_selection = pending_res.scalar_one_or_none() is not None

    stmt = (
        select(SocialAccount)
        .where(SocialAccount.provider == "facebook")
        .order_by(SocialAccount.updated_at.desc(), SocialAccount.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    if account is None:
        return MetaIntegrationStatus(
            provider="facebook",
            status="disconnected",
            page_id=None,
            page_name=None,
            connected_at=None,
            token_checked_at=None,
            pending_selection=pending_selection,
            alert=None,
        )

    alert = None
    if account.status == SocialAccountStatus.needs_reconnect:
        alert = MetaIntegrationAlert(code="needs_reconnect", message="Reconexão necessária com o Facebook.")
    elif account.status == SocialAccountStatus.disconnected:
        alert = MetaIntegrationAlert(code="disconnected", message="Integração com Facebook desconectada.")

    status_value = (
        account.status.value if isinstance(account.status, SocialAccountStatus) else str(account.status)
    )
    if status_value not in {"connected", "needs_reconnect", "disconnected"}:
        status_value = "disconnected"
    return MetaIntegrationStatus(
        provider="facebook",
        status=status_value,  # type: ignore[arg-type]
        page_id=account.page_id if account.status != SocialAccountStatus.disconnected else None,
        page_name=account.page_name if account.status != SocialAccountStatus.disconnected else None,
        connected_at=account.connected_at,
        token_checked_at=account.token_checked_at,
        pending_selection=pending_selection,
        alert=alert,
    )


async def _cleanup_facebook_connections(session: AsyncSession) -> None:
    await session.execute(delete(SocialAccount).where(SocialAccount.provider == "facebook"))


async def replace_active_connection(
    session: AsyncSession,
    provider: str = "facebook",
    *,
    page_id: str,
    page_name: str | None,
    page_access_token_plain: str,
    settings: Any,
    connected_now: bool = True,
) -> SocialAccount:
    key = getattr(settings, "SOCIAL_TOKEN_ENCRYPTION_KEY", "")
    if not str(key or "").strip():
        raise MetaOAuthConfigError(_MISSING_CONFIG_MESSAGE)
    encrypted = encrypt_token(page_access_token_plain, key)
    await session.execute(delete(SocialAccount).where(SocialAccount.provider == provider))
    now = datetime.now(timezone.utc)
    account = SocialAccount(
        provider=provider,
        page_id=str(page_id),
        page_name=page_name,
        page_access_token=encrypted,
        status=SocialAccountStatus.connected,
        connected_at=now if connected_now else None,
        token_checked_at=now,
    )
    session.add(account)
    await session.flush()
    return account


async def mark_needs_reconnect(
    session: AsyncSession,
    reason_code: str = "needs_reconnect",
    message_safe: str = "Reconexão necessária com o Facebook.",
) -> MetaIntegrationStatus:
    stmt = select(SocialAccount).where(SocialAccount.provider == "facebook")
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    if account is None:
        return await get_current_meta_status(session)
    account.status = SocialAccountStatus.needs_reconnect
    account.token_checked_at = datetime.now(timezone.utc)
    await session.flush()
    _ = (reason_code, message_safe)  # reason tracked via safe status alert
    return await get_current_meta_status(session)


async def disconnect_meta(session: AsyncSession) -> MetaActionResponse:
    # Remove usable credential/record and mark disconnected state (D-07)
    stmt = select(SocialAccount).where(SocialAccount.provider == "facebook")
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    if account is not None:
        # Keep a non-reusable disconnected marker without storing real token
        account.page_access_token = encrypt_token("disconnected", getattr(getattr(session, "info", {}), "get", lambda *_: "")("social_token_key") or "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=") if False else account.page_access_token
        # Safer: delete active record so no reusable secret remains; UI shows disconnected.
        await session.delete(account)
    await session.execute(
        delete(SocialOAuthPending).where(SocialOAuthPending.provider == "facebook")
    )
    await session.flush()
    return MetaActionResponse(status="disconnected", message="Integração com Facebook desconectada.", pending_selection=False)


async def create_pending_selection(
    session: AsyncSession,
    pages_with_tokens: list[dict[str, Any]],
    settings: Any,
    ttl_minutes: int = PENDING_SELECTION_TTL_MINUTES,
) -> str:
    """Create DB-backed pending selection and return opaque pending_nonce for redirect contract."""
    key = getattr(settings, "SOCIAL_TOKEN_ENCRYPTION_KEY", "")
    if not str(key or "").strip():
        raise MetaOAuthConfigError(_MISSING_CONFIG_MESSAGE)
    nonce = uuid.uuid4().hex  # opaque nonce used as pending=<opaque_nonce>
    payload = {
        "provider": "facebook",
        "pages": [
            {
                "page_id": str(p.get("page_id")),
                "page_name": p.get("page_name"),
                "page_access_token": p.get("page_access_token"),
            }
            for p in pages_with_tokens
            if p.get("page_id") and p.get("page_access_token")
        ],
    }
    encrypted_payload = encrypt_token(json.dumps(payload, ensure_ascii=False), key)
    pending = SocialOAuthPending(
        provider="facebook",
        nonce=nonce,
        pages_payload_encrypted=encrypted_payload,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
        consumed_at=None,
    )
    session.add(pending)
    await session.flush()
    return nonce  # pending_nonce


async def _get_valid_pending(session: AsyncSession, pending_nonce: str) -> SocialOAuthPending | None:
    stmt = select(SocialOAuthPending).where(
        SocialOAuthPending.provider == "facebook",
        SocialOAuthPending.nonce == pending_nonce,
        SocialOAuthPending.consumed_at.is_(None),
        SocialOAuthPending.expires_at > datetime.now(timezone.utc),
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _decrypt_pending_payload(pending: SocialOAuthPending, settings: Any) -> dict[str, Any]:
    from app.services.social.crypto import SocialTokenDecryptError, decrypt_token

    key = getattr(settings, "SOCIAL_TOKEN_ENCRYPTION_KEY", "")
    try:
        raw = decrypt_token(pending.pages_payload_encrypted, key)
        data = json.loads(raw)
    except (SocialTokenDecryptError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise MetaOAuthPendingError(_SAFE_PENDING_EXPIRED) from exc
    if not isinstance(data, dict):
        raise MetaOAuthPendingError(_SAFE_PENDING_EXPIRED)
    return data


async def list_pending_pages(session: AsyncSession, pending_nonce: str, settings: Any | None = None) -> MetaPendingSelectionResponse:
    """Return safe pending page list (no nonce/token fields) for GET ?pending=<opaque_nonce>."""
    pending = await _get_valid_pending(session, pending_nonce)
    if pending is None:
        raise MetaOAuthPendingError(_SAFE_PENDING_EXPIRED)
    pages: list[MetaPendingPage] = []
    payload = _decrypt_pending_payload(pending, settings) if settings is not None else {"pages": []}
    for page in payload.get("pages") or []:
        if isinstance(page, dict) and page.get("page_id"):
            pages.append(
                MetaPendingPage(
                    page_id=str(page.get("page_id")),
                    page_name=page.get("page_name") if isinstance(page.get("page_name"), str) else None,
                )
            )
    return MetaPendingSelectionResponse(pending=True, pages=pages)


async def confirm_pending_selection(
    session: AsyncSession,
    pending_nonce: str,
    page_id: str,
    settings: Any,
) -> MetaActionResponse:
    """Confirm selected pending page (by pending_nonce) and persist active connection."""
    pending = await _get_valid_pending(session, pending_nonce)
    if pending is None:
        raise MetaOAuthPendingError(_SAFE_PENDING_EXPIRED)
    payload = _decrypt_pending_payload(pending, settings)
    selected = None
    for page in payload.get("pages") or []:
        if isinstance(page, dict) and str(page.get("page_id")) == str(page_id):
            selected = page
            break
    if selected is None:
        raise MetaOAuthPendingError("Página inválida para esta seleção.")

    token_plain = str(selected.get("page_access_token") or "")
    classification, valid = await _classify_current_token(token_plain, settings)
    if not valid:
        if classification == "definitive":
            pending.consumed_at = datetime.now(timezone.utc)
            await session.flush()
            raise MetaOAuthGraphError("Conexão com o Facebook inválida. Reconecte para continuar.")
        raise MetaOAuthGraphError(_SAFE_TRANSIENT_VERIFY)

    await replace_active_connection(
        session,
        provider="facebook",
        page_id=str(selected.get("page_id")),
        page_name=selected.get("page_name") if isinstance(selected.get("page_name"), str) else None,
        page_access_token_plain=token_plain,
        settings=settings,
        connected_now=True,
    )
    pending.consumed_at = datetime.now(timezone.utc)
    await session.flush()
    return MetaActionResponse(status="connected", message="Página conectada com sucesso.", pending_selection=False)


async def process_callback(
    session: AsyncSession,
    *,
    code: str | None,
    state: str | None,
    error: str | None,
    settings: Any,
) -> dict[str, Any]:
    """Complete OAuth callback with signed state validation and safe result (D-02..D-10)."""
    try:
        validate_meta_oauth_state(state or "", getattr(settings, "JWT_SECRET"))
    except MetaOAuthStateError:
        return {"result": "error", "reason": "invalid_state"}

    if error:
        return {"result": "cancelled" if error == "access_denied" else "error", "reason": "provider_error"}

    if not code:
        return {"result": "error", "reason": "missing_code"}

    try:
        short_token = await exchange_code_for_short_lived_user_token(code, settings)
        long_token = await exchange_for_long_lived_user_token(short_token, settings)
        pages = await list_user_pages(long_token, settings)
    except MetaOAuthConfigError:
        return {"result": "error", "reason": "not_configured"}
    except MetaOAuthGraphError:
        return {"result": "error", "reason": "graph_error"}

    if not pages:
        return {"result": "error", "reason": "no_pages"}

    if len(pages) == 1:
        page = pages[0]
        classification, valid = await _classify_current_token(str(page["page_access_token"]), settings)
        if not valid:
            if classification == "definitive":
                await mark_needs_reconnect(session)
                return {"result": "error", "reason": "needs_reconnect"}
            return {"result": "error", "reason": "transient"}
        await replace_active_connection(
            session,
            provider="facebook",
            page_id=str(page["page_id"]),
            page_name=page.get("page_name") if isinstance(page.get("page_name"), str) else None,
            page_access_token_plain=str(page["page_access_token"]),
            settings=settings,
            connected_now=True,
        )
        return {"result": "connected"}

    # Multi-page: backend-mediated pending selection with pending_nonce
    pending_nonce = await create_pending_selection(session, pages, settings, ttl_minutes=PENDING_SELECTION_TTL_MINUTES)
    return {"result": "select_page", "pending_nonce": pending_nonce, "pending": pending_nonce}


async def complete_oauth_callback(
    session: AsyncSession,
    *,
    code: str | None,
    state: str | None,
    error: str | None,
    settings: Any,
) -> dict[str, Any]:
    return await process_callback(session, code=code, state=state, error=error, settings=settings)


async def verify_current_connection(session: AsyncSession, settings: Any) -> MetaActionResponse:
    """On-demand verification (D-09/D-10): definitive -> needs_reconnect, transient preserves state."""
    stmt = select(SocialAccount).where(SocialAccount.provider == "facebook")
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    if account is None or account.status == SocialAccountStatus.disconnected:
        return MetaActionResponse(status="disconnected", message="Integração com Facebook desconectada.", pending_selection=False)

    from app.services.social.crypto import SocialTokenDecryptError, decrypt_token

    try:
        key = getattr(settings, "SOCIAL_TOKEN_ENCRYPTION_KEY", "")
        token_plain = decrypt_token(account.page_access_token, key)
    except (SocialTokenDecryptError, MetaOAuthConfigError):
        await mark_needs_reconnect(session)
        return MetaActionResponse(status="needs_reconnect", message="Reconexão necessária com o Facebook.")

    classification, valid = await _classify_current_token(token_plain, settings)
    now = datetime.now(timezone.utc)
    if valid:
        account.status = SocialAccountStatus.connected
        account.token_checked_at = now
        await session.flush()
        return MetaActionResponse(status="connected", message="Conexão verificada com sucesso.")
    if classification == "definitive":
        account.status = SocialAccountStatus.needs_reconnect
        account.token_checked_at = now
        await session.flush()
        return MetaActionResponse(status="needs_reconnect", message="Reconexão necessária com o Facebook.")
    # transient: preserve previously valid connected state
    account.token_checked_at = account.token_checked_at or now
    await session.flush()
    return MetaActionResponse(status=account.status.value, message=_SAFE_TRANSIENT_VERIFY)

