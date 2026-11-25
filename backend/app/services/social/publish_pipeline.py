"""Pipeline único de claim/publicação/retry/idempotência para posts sociais (Phases 17/31).

Responsável por:
- claim atômico de elegíveis (scheduled/failed retryable vencidos)
- transição segura para publishing antes do envio
- publicação via FacebookPublisher/InstagramPublisher com token backend-only em memória
- classificação de falhas, backoff configurável e logging sanitizado
- idempotência/no-duplicate (inclui resultado ambíguo sem auto-retry)
- reconciliação IG segura antes de republicar (PUBL-04)
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.crud.social_accounts import get_active_connected_facebook_account, get_facebook_account
from app.crud.social_posts import (
    claim_for_publishing,
    get_social_post_by_id,
    list_due_for_claim,
    mark_failed,
    mark_published,
)
from app.db.session import async_session_factory
from app.models.job import Job
from app.models.social_account import SocialAccountStatus
from app.models.social_post import SocialPost, SocialPostStatus
from app.models.social_post_log import SocialPostLog
from app.services.social.crypto import SocialTokenDecryptError, decrypt_token
from app.services.social.facebook import FacebookPublisher
from app.services.social.image_media import prepare_instagram_media, validate_media_public_base_url
from app.services.social.instagram import InstagramPublisher
from app.services.social.post_generation import SocialPostLinkError, build_public_job_link
from app.services.social.types import PublishFailureCategory, PublishResult, SocialPostPayload

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS: tuple[str, ...] = ("facebook", "instagram")

MSG_RECONNECT = "Conexão com o Facebook indisponível. Reconecte a integração para publicar."
MSG_TRANSIENT = "Falha temporária ao publicar. Uma nova tentativa será feita automaticamente."
MSG_AMBIGUOUS = (
    "Não foi possível confirmar a publicação. Verifique antes de tentar novamente para evitar duplicidade."
)
MSG_PERMANENT = "Não foi possível publicar este post. Revise a integração ou o conteúdo e tente novamente."
MSG_GENERIC_PROCESS = "Não foi possível processar a publicação deste post agora. Tente novamente."

MSG_IG_RECONNECT = (
    "Conexão com o Instagram indisponível ou não pronta. Reconecte/verifique a integração em Integrações antes de publicar."
)
MSG_IG_AMBIGUOUS = (
    "Não foi possível confirmar a publicação no Instagram. A reconciliação será verificada antes de qualquer nova tentativa."
)
MSG_IG_PERMANENT = "Não foi possível publicar no Instagram. Revise a integração, a imagem ou o conteúdo e tente novamente."
MSG_IG_IMAGE_INVALID = (
    "A imagem do Instagram não está válida ou acessível publicamente. Revise a mídia antes de publicar no Instagram."
)
MSG_IG_RATE_LIMIT = (
    "O Instagram bloqueou temporariamente novas publicações por limite da plataforma. "
    "Aguarde e tente novamente mais tarde."
)
MSG_IG_CONTENT_LIMIT = (
    "O limite diário de publicação do Instagram foi atingido. "
    "Aguarde a janela da plataforma antes de tentar novamente."
)


def _now(now: datetime | None = None) -> datetime:
    return now or datetime.now(timezone.utc)


def _safe_text(value: str | None, max_len: int = 500) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lower = text.lower()
    if "access_token" in lower or "token=" in lower or "bearer " in lower:
        return "[redacted]"
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def compute_next_retry(attempts: int, settings: Settings | None = None, *, now: datetime | None = None) -> datetime | None:
    """Calcula próximo retry automático para falha retryable.

    `attempts` representa o número da tentativa recém-falha (1-based após incremento).
    """
    settings = settings or get_settings()
    now = _now(now)
    max_attempts = int(getattr(settings, "SOCIAL_MAX_ATTEMPTS", 5) or 5)
    if attempts >= max_attempts:
        return None
    delays = list(getattr(settings, "social_retry_delays_list", []) or [300, 900, 3600, 10800, 21600])
    if not delays:
        delays = [300]
    idx = min(max(attempts - 1, 0), len(delays) - 1)
    return now + timedelta(seconds=int(delays[idx]))


def _classify_failure(
    category: PublishFailureCategory | None,
    *,
    integration_blocked: bool = False,
) -> tuple[str, bool, bool]:
    """Retorna (mensagem_segura, retryable_auto, final_sem_auto_retry_ambíguo_ou_bloqueado)."""
    if integration_blocked:
        return MSG_RECONNECT, False, True
    if category == PublishFailureCategory.transient:
        return MSG_TRANSIENT, True, False
    if category == PublishFailureCategory.ambiguous:
        return MSG_AMBIGUOUS, False, True
    if category == PublishFailureCategory.permanent:
        return MSG_PERMANENT, False, True
    # unknown -> tratar como permanente seguro (não entrar em loop cego)
    return MSG_PERMANENT, False, True


async def _append_log(
    session,
    post: SocialPost,
    *,
    attempt_number: int,
    result: str,
    http_status: int | None = None,
    error_message: str | None = None,
    response_summary: str | None = None,
    external_post_id: str | None = None,
) -> None:
    log = SocialPostLog(
        social_post_id=post.id,
        attempt_number=attempt_number,
        result=_safe_text(result, 32) or "failed",
        http_status=http_status,
        error_message=_safe_text(error_message),
        response_summary=_safe_text(response_summary),
        external_post_id=_safe_text(external_post_id, 255),
    )
    session.add(log)
    await session.flush()


def _is_ig_rate_limit_code(code: str | None) -> bool:
    return str(code or "").strip().lower() in {"ig_rate_limit_blocked", "ig_content_publishing_limit"}


def _ig_safe_rate_limit_message(code: str | None) -> str:
    if str(code or "").strip().lower() == "ig_content_publishing_limit":
        return MSG_IG_CONTENT_LIMIT
    return MSG_IG_RATE_LIMIT


def _clear_ig_reconciliation(post: SocialPost) -> None:
    post.ig_reconciliation_required = False
    post.ig_reconciliation_state = "reconciled_published" if post.status == SocialPostStatus.published else None


async def _finalize_failed(
    session,
    post: SocialPost,
    *,
    attempt_number: int,
    safe_msg: str,
    result: str,
    summary: str,
    next_retry_at: datetime | None = None,
    final: bool = True,
    category: PublishFailureCategory | None = None,
    external_post_id: str | None = None,
    ig_container_id: str | None = None,
    ig_media_id: str | None = None,
    ig_permalink: str | None = None,
    ig_reconciliation_required: bool | None = None,
    ig_reconciliation_state: str | None = None,
    ig_last_reconciled_at: datetime | None = None,
    ig_last_publish_error_code: str | None = None,
) -> str:
    post.attempts = attempt_number
    if ig_container_id is not None or hasattr(post, "ig_container_id"):
        if ig_container_id is not None:
            post.ig_container_id = ig_container_id
    if ig_media_id is not None:
        post.ig_media_id = ig_media_id
    if ig_permalink is not None:
        post.ig_permalink = ig_permalink
    if ig_reconciliation_required is not None:
        post.ig_reconciliation_required = bool(ig_reconciliation_required)
    if ig_reconciliation_state is not None or (ig_reconciliation_required is False):
        post.ig_reconciliation_state = ig_reconciliation_state
    if ig_last_reconciled_at is not None:
        post.ig_last_reconciled_at = ig_last_reconciled_at
    if ig_last_publish_error_code is not None:
        post.ig_last_publish_error_code = ig_last_publish_error_code
    await mark_failed(
        session,
        post,
        attempts=attempt_number,
        last_error=safe_msg,
        next_retry_at=None if final else next_retry_at,
        final=final,
    )
    await _append_log(
        session,
        post,
        attempt_number=attempt_number,
        result=result,
        error_message=safe_msg,
        response_summary=summary,
        external_post_id=external_post_id,
    )
    if final:
        return "failed_final"
    return "retried"


async def _finalize_published(
    session,
    post: SocialPost,
    *,
    attempt_number: int,
    external_post_id: str,
    now: datetime,
    summary: str = "published",
    log_result: str = "published",
    ig_container_id: str | None = None,
    ig_media_id: str | None = None,
    ig_permalink: str | None = None,
    ig_last_reconciled_at: datetime | None = None,
) -> str:
    post.attempts = attempt_number
    if ig_container_id is not None:
        post.ig_container_id = ig_container_id
    if ig_media_id is not None:
        post.ig_media_id = ig_media_id
    if ig_permalink is not None:
        post.ig_permalink = ig_permalink
    post.ig_reconciliation_required = False
    post.ig_reconciliation_state = "reconciled_published" if summary.startswith("reconciled") else None
    post.ig_last_publish_error_code = None
    if ig_last_reconciled_at is not None:
        post.ig_last_reconciled_at = ig_last_reconciled_at
    await mark_published(session, post, external_post_id=str(external_post_id), published_at=now)
    await _append_log(
        session,
        post,
        attempt_number=attempt_number,
        result=log_result,
        external_post_id=str(external_post_id),
        response_summary=summary,
    )
    return "published"


def _ig_account_is_ready(account: Any | None) -> tuple[bool, str]:
    if account is None:
        return False, MSG_IG_RECONNECT
    if getattr(account, "status", None) != SocialAccountStatus.connected:
        return False, MSG_IG_RECONNECT
    state = str(getattr(account, "ig_readiness_state", "") or "").strip().lower()
    if state and state != "ready":
        return False, MSG_IG_RECONNECT
    ig_user_id = str(getattr(account, "ig_user_id", "") or "").strip()
    if not ig_user_id:
        return False, MSG_IG_RECONNECT
    token = getattr(account, "page_access_token", None)
    if not token:
        return False, MSG_IG_RECONNECT
    return True, ""


async def _ig_fetch_status(
    client: httpx.AsyncClient,
    *,
    base: str,
    container_id: str,
    access_token: str,
) -> dict[str, Any]:
    try:
        resp = await client.get(
            f"{base}/{container_id}",
            params={"fields": "status_code,status,id", "access_token": access_token},
        )
    except httpx.TimeoutException:
        return {"kind": "ambiguous", "status_code": None, "body": None}
    except httpx.RequestError:
        return {"kind": "ambiguous", "status_code": None, "body": None}
    try:
        body = resp.json()
    except ValueError:
        body = None
    if resp.status_code >= 500 or resp.status_code == 429:
        # ambiguous/blocked at status check; caller decides rate-limit vs ambiguous
        return {"kind": "ambiguous_http", "status_code": resp.status_code, "body": body}
    if resp.status_code >= 400:
        return {"kind": "http_error", "status_code": resp.status_code, "body": body}
    status = ""
    if isinstance(body, dict):
        status = str(body.get("status_code") or body.get("status") or "").upper().strip()
    return {"kind": "ok", "status": status, "status_code": resp.status_code, "body": body}


async def _ig_fetch_media_permalink(
    client: httpx.AsyncClient,
    *,
    base: str,
    media_id: str,
    access_token: str,
) -> str | None:
    try:
        resp = await client.get(
            f"{base}/{media_id}",
            params={"fields": "id,permalink", "access_token": access_token},
        )
    except Exception:
        return None
    try:
        body = resp.json()
    except ValueError:
        body = None
    if resp.status_code < 400 and isinstance(body, dict):
        permalink = body.get("permalink")
        if isinstance(permalink, str) and permalink.strip():
            return _safe_text(permalink.strip(), 500)
    return None


async def _ig_publish_container(
    client: httpx.AsyncClient,
    *,
    base: str,
    ig_user_id: str,
    container_id: str,
    access_token: str,
) -> PublishResult:
    try:
        resp = await client.post(
            f"{base}/{ig_user_id}/media_publish",
            data={"creation_id": container_id, "access_token": access_token},
        )
    except httpx.TimeoutException:
        return PublishResult(ok=False, category=PublishFailureCategory.ambiguous, error_message=MSG_IG_AMBIGUOUS, container_id=container_id, error_code="ig_publish_timeout_ambiguous")
    except httpx.RequestError:
        return PublishResult(ok=False, category=PublishFailureCategory.ambiguous, error_message=MSG_IG_AMBIGUOUS, container_id=container_id, error_code="ig_publish_request_ambiguous")
    try:
        body = resp.json()
    except ValueError:
        body = None
    # rate-limit detection
    err = body.get("error") if isinstance(body, dict) else None
    err = err if isinstance(err, dict) else {}
    code = err.get("code")
    subcode = err.get("error_subcode")
    blob = " ".join(
        [
            str(err.get("message") or "").lower(),
            str(err.get("error_user_title") or "").lower(),
            str(err.get("error_user_msg") or "").lower(),
        ]
    )
    if code == 2207042 or subcode == 2207042 or "2207042" in blob or "content_publishing_limit" in blob:
        return PublishResult(ok=False, category=PublishFailureCategory.permanent, error_message=MSG_IG_CONTENT_LIMIT, container_id=container_id, error_code="ig_content_publishing_limit")
    if resp.status_code == 429 or (code in {4, 17, 32, 613} and ("limit" in blob or "too many" in blob or "rate" in blob)):
        return PublishResult(ok=False, category=PublishFailureCategory.permanent, error_message=MSG_IG_RATE_LIMIT, container_id=container_id, error_code="ig_rate_limit_blocked")

    if resp.status_code < 400 and isinstance(body, dict) and body.get("id"):
        return PublishResult(ok=True, external_post_id=str(body["id"]), container_id=container_id, published_media_id=str(body["id"]))
    if resp.status_code >= 500 or resp.status_code == 429:
        return PublishResult(ok=False, category=PublishFailureCategory.ambiguous, error_message=MSG_IG_AMBIGUOUS, container_id=container_id, error_code="ig_publish_http_ambiguous")
    if resp.status_code >= 400:
        return PublishResult(ok=False, category=PublishFailureCategory.permanent, error_message=MSG_IG_PERMANENT, container_id=container_id, error_code="ig_publish_failed")
    return PublishResult(ok=False, category=PublishFailureCategory.ambiguous, error_message=MSG_IG_AMBIGUOUS, container_id=container_id, error_code="ig_publish_ambiguous")


async def _ig_reconcile_before_publish(
    session,
    post: SocialPost,
    *,
    settings: Settings,
    account: Any,
    plain_token: str,
    attempt_number: int,
    now: datetime,
) -> tuple[str | None, PublishResult | None]:
    """Returns (pipeline_outcome, None) if reconciliation finalized, else (None, None) to continue."""
    container_id = str(getattr(post, "ig_container_id", "") or "").strip() or None
    ig_media_id = str(getattr(post, "ig_media_id", "") or "").strip() or None
    external_id = str(getattr(post, "external_post_id", "") or "").strip() or None
    if not container_id and not ig_media_id and not external_id:
        # No known IDs to reconcile - allow normal flow (no blind new container concern here)
        post.ig_reconciliation_required = False
        post.ig_reconciliation_state = None
        return None, None

    graph_version = str(getattr(settings, "META_GRAPH_VERSION", "v21.0") or "v21.0").strip() or "v21.0"
    base = f"https://graph.facebook.com/{graph_version}"
    timeout = float(getattr(settings, "IG_PUBLISH_HTTP_TIMEOUT_SECONDS", 20.0) or 20.0)
    max_poll_attempts = max(1, int(getattr(settings, "IG_STATUS_POLL_MAX_ATTEMPTS", 5) or 5))
    poll_delay = max(0.0, float(getattr(settings, "IG_STATUS_POLL_DELAY_SECONDS", 2.0) or 2.0))
    deadline = time.monotonic() + float(getattr(settings, "IG_PUBLISH_MAX_ATTEMPT_SECONDS", 45.0) or 45.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        # If we have a published media ID/external ID, confirm and mark published
        for media_id in [external_id, ig_media_id]:
            if not media_id:
                continue
            permalink = await _ig_fetch_media_permalink(client, base=base, media_id=media_id, access_token=plain_token)
            # If we can fetch media object, treat as published/reconciled
            try:
                resp = await client.get(f"{base}/{media_id}", params={"fields": "id,permalink", "access_token": plain_token})
                body = resp.json() if resp.status_code < 500 else None
            except Exception:
                resp = None
                body = None
            if resp is not None and resp.status_code < 400 and isinstance(body, dict) and body.get("id"):
                permalink = str(body.get("permalink") or permalink or "") or None
                post.ig_last_reconciled_at = now
                return await _finalize_published(
                    session,
                    post,
                    attempt_number=attempt_number,
                    external_post_id=str(body["id"]),
                    now=now,
                    summary="reconciled_published",
                    log_result="reconciled_published",
                    ig_container_id=container_id,
                    ig_media_id=str(body["id"]),
                    ig_permalink=permalink,
                    ig_last_reconciled_at=now,
                ), None

        if not container_id:
            # No container to reconcile; keep blocked ambiguity safe
            post.ig_last_reconciled_at = now
            return await _finalize_failed(
                session,
                post,
                attempt_number=attempt_number,
                safe_msg=MSG_IG_AMBIGUOUS,
                result="ambiguous",
                summary="ig_reconciliation_no_container",
                final=True,
                category=PublishFailureCategory.ambiguous,
                ig_reconciliation_required=True,
                ig_reconciliation_state="needs_reconciliation",
                ig_last_reconciled_at=now,
            ), None

        # Poll/check container status
        attempts = 0
        status = "IN_PROGRESS"
        while True:
            if time.monotonic() >= deadline:
                post.ig_last_reconciled_at = now
                return await _finalize_failed(
                    session,
                    post,
                    attempt_number=attempt_number,
                    safe_msg=MSG_IG_AMBIGUOUS,
                    result="ambiguous",
                    summary="ig_reconciliation_budget_ambiguous",
                    final=True,
                    category=PublishFailureCategory.ambiguous,
                    ig_container_id=container_id,
                    ig_reconciliation_required=True,
                    ig_reconciliation_state="needs_reconciliation",
                    ig_last_reconciled_at=now,
                ), None
            attempts += 1
            info = await _ig_fetch_status(client, base=base, container_id=container_id, access_token=plain_token)
            if info["kind"] == "ok":
                status = str(info.get("status") or "").upper().strip() or "IN_PROGRESS"
            elif info["kind"] in {"ambiguous", "ambiguous_http"}:
                # rate limit on status check - treat as blocked rate limit if detectable? Be conservative ambiguous.
                body = info.get("body")
                err = body.get("error") if isinstance(body, dict) else None
                err = err if isinstance(err, dict) else {}
                code = err.get("code")
                subcode = err.get("error_subcode")
                blob = str(err.get("message") or "").lower()
                if code == 2207042 or subcode == 2207042 or "content_publishing_limit" in blob:
                    post.ig_last_reconciled_at = now
                    post.ig_last_publish_error_code = "ig_content_publishing_limit"
                    return await _finalize_failed(
                        session,
                        post,
                        attempt_number=attempt_number,
                        safe_msg=MSG_IG_CONTENT_LIMIT,
                        result="failed_permanent",
                        summary="ig_content_publishing_limit",
                        final=True,
                        category=PublishFailureCategory.permanent,
                        ig_container_id=container_id,
                        ig_reconciliation_required=False,
                        ig_reconciliation_state="reconciled_failed",
                        ig_last_reconciled_at=now,
                        ig_last_publish_error_code="ig_content_publishing_limit",
                    ), None
                status = "IN_PROGRESS"
            elif info["kind"] == "http_error":
                status = "ERROR"
            else:
                status = "IN_PROGRESS"

            if status == "FINISHED":
                # publish same container, no new container
                publish_result = await _ig_publish_container(
                    client,
                    base=base,
                    ig_user_id=str(getattr(account, "ig_user_id", "") or "").strip(),
                    container_id=container_id,
                    access_token=plain_token,
                )
                if publish_result.ok and publish_result.external_post_id:
                    permalink = publish_result.permalink
                    if not permalink:
                        permalink = await _ig_fetch_media_permalink(
                            client, base=base, media_id=publish_result.external_post_id, access_token=plain_token
                        )
                    post.ig_last_reconciled_at = now
                    return await _finalize_published(
                        session,
                        post,
                        attempt_number=attempt_number,
                        external_post_id=publish_result.external_post_id,
                        now=now,
                        summary="reconciled_published",
                        log_result="reconciled_published",
                        ig_container_id=container_id,
                        ig_media_id=publish_result.external_post_id,
                        ig_permalink=permalink,
                        ig_last_reconciled_at=now,
                    ), None
                if publish_result.category == PublishFailureCategory.ambiguous:
                    post.ig_last_reconciled_at = now
                    return await _finalize_failed(
                        session,
                        post,
                        attempt_number=attempt_number,
                        safe_msg=MSG_IG_AMBIGUOUS,
                        result="ambiguous",
                        summary="ig_reconciliation_publish_ambiguous",
                        final=True,
                        category=PublishFailureCategory.ambiguous,
                        ig_container_id=container_id,
                        ig_media_id=publish_result.published_media_id,
                        ig_reconciliation_required=True,
                        ig_reconciliation_state="needs_reconciliation",
                        ig_last_reconciled_at=now,
                        ig_last_publish_error_code=publish_result.error_code,
                    ), None
                # conclusive failure from publish
                post.ig_last_reconciled_at = now
                is_rl = _is_ig_rate_limit_code(publish_result.error_code)
                safe_msg = _ig_safe_rate_limit_message(publish_result.error_code) if is_rl else MSG_IG_PERMANENT
                return await _finalize_failed(
                    session,
                    post,
                    attempt_number=attempt_number,
                    safe_msg=safe_msg,
                    result="failed_permanent",
                    summary=_safe_text(publish_result.error_code or "ig_reconciliation_publish_failed", 64) or "ig_reconciliation_publish_failed",
                    final=True,
                    category=PublishFailureCategory.permanent,
                    ig_container_id=container_id,
                    ig_reconciliation_required=False,
                    ig_reconciliation_state="reconciled_failed",
                    ig_last_reconciled_at=now,
                    ig_last_publish_error_code=publish_result.error_code,
                ), None
            if status == "PUBLISHED":
                media_id = ig_media_id or external_id
                permalink = None
                if media_id:
                    permalink = await _ig_fetch_media_permalink(client, base=base, media_id=media_id, access_token=plain_token)
                post.ig_last_reconciled_at = now
                if media_id:
                    return await _finalize_published(
                        session,
                        post,
                        attempt_number=attempt_number,
                        external_post_id=media_id,
                        now=now,
                        summary="reconciled_published",
                        log_result="reconciled_published",
                        ig_container_id=container_id,
                        ig_media_id=media_id,
                        ig_permalink=permalink,
                        ig_last_reconciled_at=now,
                    ), None
                return await _finalize_failed(
                    session,
                    post,
                    attempt_number=attempt_number,
                    safe_msg=MSG_IG_AMBIGUOUS,
                    result="ambiguous",
                    summary="ig_reconciliation_published_missing_id",
                    final=True,
                    category=PublishFailureCategory.ambiguous,
                    ig_container_id=container_id,
                    ig_reconciliation_required=True,
                    ig_reconciliation_state="needs_reconciliation",
                    ig_last_reconciled_at=now,
                ), None
            if status in {"ERROR", "EXPIRED"}:
                post.ig_last_reconciled_at = now
                return await _finalize_failed(
                    session,
                    post,
                    attempt_number=attempt_number,
                    safe_msg=MSG_IG_PERMANENT,
                    result="failed_permanent",
                    summary=f"ig_container_{status.lower()}",
                    final=True,
                    category=PublishFailureCategory.permanent,
                    ig_container_id=container_id,
                    ig_reconciliation_required=False,
                    ig_reconciliation_state="reconciled_failed",
                    ig_last_reconciled_at=now,
                    ig_last_publish_error_code=f"ig_container_{status.lower()}",
                ), None
            # IN_PROGRESS / unknown
            if attempts >= max_poll_attempts or time.monotonic() >= deadline:
                post.ig_last_reconciled_at = now
                return await _finalize_failed(
                    session,
                    post,
                    attempt_number=attempt_number,
                    safe_msg=MSG_IG_AMBIGUOUS,
                    result="ambiguous",
                    summary="ig_reconciliation_inconclusive",
                    final=True,
                    category=PublishFailureCategory.ambiguous,
                    ig_container_id=container_id,
                    ig_reconciliation_required=True,
                    ig_reconciliation_state="needs_reconciliation",
                    ig_last_reconciled_at=now,
                ), None
            await asyncio.sleep(min(poll_delay, max(0.0, deadline - time.monotonic())))


async def process_claimed_post(
    session,
    post: SocialPost,
    *,
    settings: Settings | None = None,
    publisher: Any | None = None,
    now: datetime | None = None,
) -> str:
    """Processa um post já claimado (status publishing) e persiste resultado seguro."""
    settings = settings or get_settings()
    now = _now(now)

    # Idempotência: nunca republicar item já publicado/com external_post_id
    if post.status == SocialPostStatus.published or post.external_post_id:
        return "idempotent"

    if post.status != SocialPostStatus.publishing:
        # Defesa defensiva: só processa se estiver em publishing
        return "skipped"

    attempt_number = int(post.attempts or 0) + 1
    provider = (post.provider or "facebook").strip().lower()

    if provider == "instagram":
        return await _process_instagram_claimed_post(
            session,
            post,
            attempt_number=attempt_number,
            settings=settings,
            publisher=publisher,
            now=now,
        )

    # Facebook/default (backward-compatible)
    return await _process_facebook_claimed_post(
        session,
        post,
        attempt_number=attempt_number,
        settings=settings,
        publisher=publisher,
        now=now,
    )


async def _process_facebook_claimed_post(
    session,
    post: SocialPost,
    *,
    attempt_number: int,
    settings: Settings,
    publisher: Any | None,
    now: datetime,
) -> str:
    publisher = publisher or FacebookPublisher()

    job = await session.get(Job, post.job_id)
    if job is None:
        msg = MSG_PERMANENT
        await mark_failed(session, post, attempts=attempt_number, last_error=msg, next_retry_at=None, final=True)
        await _append_log(session, post, attempt_number=attempt_number, result="failed_permanent", error_message=msg)
        return "failed_final"

    try:
        link = build_public_job_link(job.id, settings=settings)
    except SocialPostLinkError:
        msg = MSG_PERMANENT
        await mark_failed(session, post, attempts=attempt_number, last_error=msg, next_retry_at=None, final=True)
        await _append_log(session, post, attempt_number=attempt_number, result="failed_permanent", error_message=msg)
        return "failed_final"

    account = await get_active_connected_facebook_account(session)
    integration_blocked = False
    if account is None:
        existing = await get_facebook_account(session)
        if existing is None or existing.status in {
            SocialAccountStatus.disconnected,
            SocialAccountStatus.needs_reconnect,
        }:
            integration_blocked = True
        else:
            integration_blocked = True

    plain_token: str | None = None
    page_id: str | None = None
    if not integration_blocked and account is not None:
        page_id = account.page_id
        try:
            key = getattr(settings, "SOCIAL_TOKEN_ENCRYPTION_KEY", "")
            plain_token = decrypt_token(account.page_access_token, key)
        except (SocialTokenDecryptError, Exception):
            integration_blocked = True

    if integration_blocked or not plain_token or not page_id:
        msg = MSG_RECONNECT
        await mark_failed(session, post, attempts=attempt_number, last_error=msg, next_retry_at=None, final=True)
        await _append_log(
            session,
            post,
            attempt_number=attempt_number,
            result="blocked",
            error_message=msg,
            response_summary="integration_unavailable",
        )
        return "failed_final"

    payload = SocialPostPayload(
        job_id=str(post.job_id),
        provider=post.provider,
        message=post.text,
        link=link,
        page_id=page_id,
        page_access_token=plain_token,
    )

    try:
        result: PublishResult = await publisher.publish(payload)
    except Exception:
        result = PublishResult(
            ok=False,
            category=PublishFailureCategory.ambiguous,
            error_message=MSG_AMBIGUOUS,
        )
    finally:
        payload = None  # type: ignore[assignment]
        plain_token = None

    if result.ok and result.external_post_id:
        await _finalize_published(
            session,
            post,
            attempt_number=attempt_number,
            external_post_id=str(result.external_post_id),
            now=now,
        )
        return "published"

    category = result.category or PublishFailureCategory.unknown
    safe_msg, retryable, _ambiguous_or_blocked = _classify_failure(category, integration_blocked=False)
    if retryable and category == PublishFailureCategory.transient:
        next_retry_at = compute_next_retry(attempt_number, settings, now=now)
        final = next_retry_at is None
        if final:
            safe_msg = MSG_PERMANENT
        await mark_failed(
            session,
            post,
            attempts=attempt_number,
            last_error=safe_msg,
            next_retry_at=next_retry_at,
            final=final,
        )
        await _append_log(
            session,
            post,
            attempt_number=attempt_number,
            result="failed_transient" if not final else "failed_permanent",
            error_message=safe_msg,
            response_summary="transient" if not final else "exhausted",
        )
        return "retried" if not final else "failed_final"

    if category == PublishFailureCategory.ambiguous:
        log_result = "ambiguous"
        summary = "ambiguous_no_auto_retry"
    elif category == PublishFailureCategory.permanent:
        log_result = "failed_permanent"
        summary = "permanent"
    else:
        log_result = "failed_permanent"
        summary = "unknown"
    await mark_failed(
        session,
        post,
        attempts=attempt_number,
        last_error=safe_msg,
        next_retry_at=None,
        final=True,
    )
    await _append_log(
        session,
        post,
        attempt_number=attempt_number,
        result=log_result,
        error_message=safe_msg,
        response_summary=summary,
    )
    return "failed_final"


async def _process_instagram_claimed_post(
    session,
    post: SocialPost,
    *,
    attempt_number: int,
    settings: Settings,
    publisher: Any | None,
    now: datetime,
) -> str:
    publisher = publisher or InstagramPublisher()

    # Resolve FB-linked account that carries IG readiness fields (Phase 29)
    account = await get_active_connected_facebook_account(session)
    if account is None:
        account = await get_facebook_account(session)

    ready, readiness_msg = _ig_account_is_ready(account)
    if not ready or account is None:
        post.ig_last_publish_error_code = "ig_not_ready"
        return await _finalize_failed(
            session,
            post,
            attempt_number=attempt_number,
            safe_msg=readiness_msg or MSG_IG_RECONNECT,
            result="failed_permanent",
            summary="ig_not_ready",
            final=True,
            category=PublishFailureCategory.permanent,
            ig_reconciliation_required=False,
            ig_reconciliation_state="reconciled_failed",
            ig_last_publish_error_code="ig_not_ready",
        )

    plain_token: str | None = None
    try:
        key = getattr(settings, "SOCIAL_TOKEN_ENCRYPTION_KEY", "")
        plain_token = decrypt_token(account.page_access_token, key)
    except (SocialTokenDecryptError, Exception):
        post.ig_last_publish_error_code = "ig_not_ready"
        return await _finalize_failed(
            session,
            post,
            attempt_number=attempt_number,
            safe_msg=MSG_IG_RECONNECT,
            result="failed_permanent",
            summary="ig_token_decrypt_failed",
            final=True,
            category=PublishFailureCategory.permanent,
            ig_reconciliation_required=False,
            ig_reconciliation_state="reconciled_failed",
            ig_last_publish_error_code="ig_not_ready",
        )

    ig_user_id = str(getattr(account, "ig_user_id", "") or "").strip()

    # D-13/D-19: reconcile before any new publish when ambiguity/reconciliation is present
    needs_recon = bool(getattr(post, "ig_reconciliation_required", False)) or (
        str(getattr(post, "ig_reconciliation_state", "") or "").strip().lower() == "needs_reconciliation"
    )
    if needs_recon:
        outcome, _ = await _ig_reconcile_before_publish(
            session,
            post,
            settings=settings,
            account=account,
            plain_token=plain_token,
            attempt_number=attempt_number,
            now=now,
        )
        if outcome is not None:
            return outcome
        # If reconciliation cleared state and says safe to continue, fall through to normal publish

    # Revalidate image before publish (IMAG-01)
    try:
        prepared = await prepare_instagram_media(session, post.job_id, settings)
    except Exception:
        prepared = None
    if prepared is None or not getattr(getattr(prepared, "validation", None), "valid", False):
        msg = MSG_IG_IMAGE_INVALID
        if prepared is not None:
            vmsg = str(getattr(getattr(prepared, "validation", None), "message", "") or "").strip()
            if vmsg:
                msg = _safe_text(vmsg, 500) or MSG_IG_IMAGE_INVALID
        post.ig_last_publish_error_code = "ig_invalid_media"
        return await _finalize_failed(
            session,
            post,
            attempt_number=attempt_number,
            safe_msg=msg,
            result="failed_permanent",
            summary="ig_invalid_media",
            final=True,
            category=PublishFailureCategory.permanent,
            ig_reconciliation_required=False,
            ig_reconciliation_state="reconciled_failed",
            ig_last_publish_error_code="ig_invalid_media",
        )

    image_url = str(getattr(prepared, "image_url", "") or "").strip()
    base_ok, _, _ = validate_media_public_base_url(settings)
    if not base_ok or not image_url.startswith("https://"):
        post.ig_last_publish_error_code = "ig_invalid_media"
        return await _finalize_failed(
            session,
            post,
            attempt_number=attempt_number,
            safe_msg=MSG_IG_IMAGE_INVALID,
            result="failed_permanent",
            summary="ig_invalid_media",
            final=True,
            category=PublishFailureCategory.permanent,
            ig_reconciliation_required=False,
            ig_reconciliation_state="reconciled_failed",
            ig_last_publish_error_code="ig_invalid_media",
        )

    payload = SocialPostPayload(
        job_id=str(post.job_id),
        provider="instagram",
        message=post.text,
        image_url=image_url,
        ig_user_id=ig_user_id,
        page_access_token=plain_token,
    )

    await _append_log(
        session,
        post,
        attempt_number=attempt_number,
        result="attempt",
        response_summary="ig_publish_attempt",
    )

    try:
        result: PublishResult = await publisher.publish(payload)
    except Exception:
        result = PublishResult(
            ok=False,
            category=PublishFailureCategory.ambiguous,
            error_message=MSG_IG_AMBIGUOUS,
            container_id=getattr(post, "ig_container_id", None),
            error_code="ig_unexpected_ambiguous",
        )
    finally:
        payload = None  # type: ignore[assignment]
        plain_token = None

    if result.ok and result.external_post_id:
        return await _finalize_published(
            session,
            post,
            attempt_number=attempt_number,
            external_post_id=str(result.external_post_id),
            now=now,
            summary="published",
            ig_container_id=result.container_id or getattr(post, "ig_container_id", None),
            ig_media_id=result.published_media_id or str(result.external_post_id),
            ig_permalink=result.permalink,
        )

    category = result.category or PublishFailureCategory.unknown
    error_code = str(getattr(result, "error_code", "") or "").strip().lower() or None
    container_id = result.container_id or getattr(post, "ig_container_id", None)
    published_media_id = result.published_media_id or getattr(post, "ig_media_id", None)

    # PUBL-05: rate-limit/content_publishing_limit - no retry storm, actionable blocked
    if _is_ig_rate_limit_code(error_code):
        post.ig_last_publish_error_code = error_code
        return await _finalize_failed(
            session,
            post,
            attempt_number=attempt_number,
            safe_msg=_ig_safe_rate_limit_message(error_code),
            result="failed_permanent",
            summary=error_code or "ig_rate_limit_blocked",
            final=True,
            category=PublishFailureCategory.permanent,
            ig_container_id=container_id,
            ig_media_id=published_media_id,
            ig_reconciliation_required=False,
            ig_reconciliation_state="reconciled_failed",
            ig_last_publish_error_code=error_code,
        )

    # PUBL-04/D-09/D-12: ambiguous -> failed + reconciliation required, no auto-retry
    if category == PublishFailureCategory.ambiguous or bool(container_id):
        # any ambiguity or critical-step result with known container must be reconciliation-safe
        if category == PublishFailureCategory.ambiguous or error_code and "ambiguous" in error_code:
            post.ig_last_reconciled_at = now
            post.ig_last_publish_error_code = error_code
            return await _finalize_failed(
                session,
                post,
                attempt_number=attempt_number,
                safe_msg=MSG_IG_AMBIGUOUS,
                result="ambiguous",
                summary="ig_ambiguous_needs_reconciliation",
                final=True,
                category=PublishFailureCategory.ambiguous,
                ig_container_id=container_id,
                ig_media_id=published_media_id,
                ig_reconciliation_required=True,
                ig_reconciliation_state="needs_reconciliation",
                ig_last_reconciled_at=now,
                ig_last_publish_error_code=error_code,
            )

    # transient auto-retry only when no ambiguity/critical container concern
    if category == PublishFailureCategory.transient and not container_id:
        next_retry_at = compute_next_retry(attempt_number, settings, now=now)
        final = next_retry_at is None
        safe_msg = MSG_TRANSIENT if not final else MSG_IG_PERMANENT
        return await _finalize_failed(
            session,
            post,
            attempt_number=attempt_number,
            safe_msg=safe_msg,
            result="failed_transient" if not final else "failed_permanent",
            summary="transient" if not final else "exhausted",
            next_retry_at=next_retry_at,
            final=final,
            category=PublishFailureCategory.transient,
            ig_container_id=container_id,
            ig_media_id=published_media_id,
            ig_reconciliation_required=False,
            ig_reconciliation_state="reconciled_failed",
            ig_last_publish_error_code=error_code,
        )

    # Permanent/unknown/conclusive
    post.ig_last_publish_error_code = error_code
    return await _finalize_failed(
        session,
        post,
        attempt_number=attempt_number,
        safe_msg=_safe_text(result.error_message, 500) or MSG_IG_PERMANENT,
        result="failed_permanent",
        summary=_safe_text(error_code or category.value, 64) or "permanent",
        final=True,
        category=category if category in {PublishFailureCategory.permanent, PublishFailureCategory.unknown} else PublishFailureCategory.permanent,
        ig_container_id=container_id,
        ig_media_id=published_media_id,
        ig_reconciliation_required=False,
        ig_reconciliation_state="reconciled_failed",
        ig_last_publish_error_code=error_code,
    )


def _new_provider_counters() -> dict[str, int]:
    return {
        "claimed": 0,
        "processed": 0,
        "published": 0,
        "retried": 0,
        "failed_final": 0,
        "skipped": 0,
        "idempotent": 0,
    }


async def run_social_publish_cycle(
    *, post_id: uuid.UUID | str | None = None, limit: int = 20
) -> dict:
    """Executa um ciclo de claim/processamento e retorna contadores."""
    settings = get_settings()
    counters = _new_provider_counters()
    by_provider: dict[str, dict[str, int]] = {p: _new_provider_counters() for p in SUPPORTED_PROVIDERS}
    claimed_by_provider: dict[str, list[uuid.UUID]] = {p: [] for p in SUPPORTED_PROVIDERS}

    providers = list(SUPPORTED_PROVIDERS)

    for provider in providers:
        if provider not in by_provider:
            by_provider[provider] = _new_provider_counters()
            claimed_by_provider[provider] = []
        pcounts = by_provider[provider]
        found_due = False
        try:
            async with async_session_factory() as session:
                try:
                    async with session.begin():
                        due = await list_due_for_claim(
                            session, provider=provider, limit=limit, now=_now(), post_id=post_id
                        )
                        found_due = bool(due)
                        for post in due:
                            claim_result = await claim_for_publishing(session, post)
                            if claim_result == "claimed":
                                pcounts["claimed"] += 1
                                counters["claimed"] += 1
                                claimed_by_provider[provider].append(post.id)
                            elif claim_result == "noop":
                                pcounts["idempotent"] += 1
                                counters["idempotent"] += 1
                            else:
                                pcounts["skipped"] += 1
                                counters["skipped"] += 1
                except Exception:
                    logger.exception("social_publish_claim_failed", extra={"provider": provider})
                    if post_id is not None:
                        break
                    continue
        except Exception:
            logger.exception("social_publish_cycle_open_session_failed", extra={"provider": provider})
            if post_id is not None:
                break
            continue
        # For targeted post_id, only the owning provider will match; avoid extra session opens.
        if post_id is not None and found_due:
            break

    for provider, ids in claimed_by_provider.items():
        pcounts = by_provider.setdefault(provider, _new_provider_counters())
        for pid in ids:
            try:
                async with async_session_factory() as session:
                    async with session.begin():
                        post = await get_social_post_by_id(session, pid)
                        if post is None:
                            counters["skipped"] += 1
                            pcounts["skipped"] += 1
                            continue
                        outcome = await process_claimed_post(session, post, settings=settings)
                        counters["processed"] += 1
                        pcounts["processed"] += 1
                        if outcome == "published":
                            counters["published"] += 1
                            pcounts["published"] += 1
                        elif outcome == "retried":
                            counters["retried"] += 1
                            pcounts["retried"] += 1
                        elif outcome == "idempotent":
                            counters["idempotent"] += 1
                            pcounts["idempotent"] += 1
                        elif outcome == "skipped":
                            counters["skipped"] += 1
                            pcounts["skipped"] += 1
                        else:
                            counters["failed_final"] += 1
                            pcounts["failed_final"] += 1
            except Exception:
                logger.exception("social_publish_item_failed", extra={"social_post_id": str(pid), "provider": provider})
                recovery_outcome = "failed_final"
                try:
                    async with async_session_factory() as session:
                        async with session.begin():
                            post = await get_social_post_by_id(session, pid)
                            if post is not None and post.status == SocialPostStatus.publishing and not post.external_post_id:
                                attempt_number = int(post.attempts or 0) + 1
                                ambiguous_msg = MSG_IG_AMBIGUOUS if (post.provider or "") == "instagram" else MSG_AMBIGUOUS
                                # if IG has known container, mark reconciliation required
                                ig_container = str(getattr(post, "ig_container_id", "") or "").strip() or None
                                is_ig = (post.provider or "").strip().lower() == "instagram"
                                await mark_failed(
                                    session,
                                    post,
                                    attempts=attempt_number,
                                    last_error=ambiguous_msg,
                                    next_retry_at=None,
                                    final=True,
                                )
                                if is_ig and ig_container:
                                    post.ig_reconciliation_required = True
                                    post.ig_reconciliation_state = "needs_reconciliation"
                                    post.ig_last_reconciled_at = _now()
                                await _append_log(
                                    session,
                                    post,
                                    attempt_number=attempt_number,
                                    result="ambiguous",
                                    error_message=ambiguous_msg,
                                    response_summary="post_claim_processing_exception",
                                    external_post_id=getattr(post, "external_post_id", None),
                                )
                                recovery_outcome = "failed_final"
                            elif post is not None and (
                                post.status == SocialPostStatus.published or post.external_post_id
                            ):
                                recovery_outcome = "idempotent"
                            else:
                                recovery_outcome = "failed_final"
                except Exception:
                    logger.exception(
                        "social_publish_item_recovery_failed",
                        extra={"social_post_id": str(pid)},
                    )
                    recovery_outcome = "failed_final"

                counters["processed"] += 1
                pcounts["processed"] += 1
                if recovery_outcome == "idempotent":
                    counters["idempotent"] += 1
                    pcounts["idempotent"] += 1
                else:
                    counters["failed_final"] += 1
                    pcounts["failed_final"] += 1

    counters["by_provider"] = by_provider
    return counters


async def process_social_post_safe(post_id: str | uuid.UUID) -> dict | None:
    """Wrapper seguro para dispatch imediato (BackgroundTasks/cron fast path)."""
    try:
        return await run_social_publish_cycle(post_id=post_id, limit=1)
    except Exception:
        logger.exception("social_publish_safe_wrapper_failed", extra={"post_id": str(post_id)})
        return None
