"""Pipeline único de claim/publicação/retry/idempotência para posts sociais (Phase 17).

Responsável por:
- claim atômico de elegíveis (scheduled/failed retryable vencidos)
- transição segura para publishing antes do envio
- publicação via FacebookPublisher com token backend-only em memória
- classificação de falhas, backoff configurável e logging sanitizado
- idempotência/no-duplicate (inclui resultado ambíguo sem auto-retry)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

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
from app.services.social.post_generation import SocialPostLinkError, build_public_job_link
from app.services.social.types import PublishFailureCategory, PublishResult, SocialPostPayload

logger = logging.getLogger(__name__)

MSG_RECONNECT = "Conexão com o Facebook indisponível. Reconecte a integração para publicar."
MSG_TRANSIENT = "Falha temporária ao publicar. Uma nova tentativa será feita automaticamente."
MSG_AMBIGUOUS = (
    "Não foi possível confirmar a publicação. Verifique antes de tentar novamente para evitar duplicidade."
)
MSG_PERMANENT = "Não foi possível publicar este post. Revise a integração ou o conteúdo e tente novamente."
MSG_GENERIC_PROCESS = "Não foi possível processar a publicação deste post agora. Tente novamente."


def _now(now: datetime | None = None) -> datetime:
    return now or datetime.now(timezone.utc)


def _safe_text(value: str | None, max_len: int = 500) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
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
    publisher = publisher or FacebookPublisher()

    job = await session.get(Job, post.job_id)
    if job is None:
        msg = MSG_PERMANENT
        post.attempts = attempt_number
        await mark_failed(session, post, attempts=attempt_number, last_error=msg, next_retry_at=None, final=True)
        await _append_log(session, post, attempt_number=attempt_number, result="failed_permanent", error_message=msg)
        return "failed_final"

    try:
        link = build_public_job_link(job.id, settings=settings)
    except SocialPostLinkError:
        msg = MSG_PERMANENT
        post.attempts = attempt_number
        await mark_failed(session, post, attempts=attempt_number, last_error=msg, next_retry_at=None, final=True)
        await _append_log(session, post, attempt_number=attempt_number, result="failed_permanent", error_message=msg)
        return "failed_final"

    account = await get_active_connected_facebook_account(session)
    integration_blocked = False
    if account is None:
        # Diferencia estado para mensagem segura de reconexão (D-06) sem expor detalhes
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
        post.attempts = attempt_number
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
        # Nunca persistir/logar token em claro
        payload = None  # type: ignore[assignment]
        plain_token = None

    if result.ok and result.external_post_id:
        post.attempts = attempt_number
        await mark_published(
            session,
            post,
            external_post_id=str(result.external_post_id),
            published_at=now,
        )
        await _append_log(
            session,
            post,
            attempt_number=attempt_number,
            result="published",
            external_post_id=str(result.external_post_id),
            response_summary="published",
        )
        return "published"

    category = result.category or PublishFailureCategory.unknown
    safe_msg, retryable, ambiguous_or_blocked = _classify_failure(category, integration_blocked=False)
    post.attempts = attempt_number
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

    # permanente, ambíguo, desconhecido/bloqueado: sem auto-retry
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


async def run_social_publish_cycle(
    *, post_id: uuid.UUID | str | None = None, limit: int = 20
) -> dict:
    """Executa um ciclo de claim/processamento e retorna contadores."""
    settings = get_settings()
    counters = {
        "claimed": 0,
        "processed": 0,
        "published": 0,
        "retried": 0,
        "failed_final": 0,
        "skipped": 0,
        "idempotent": 0,
    }
    claimed_ids: list[uuid.UUID] = []
    try:
        async with async_session_factory() as session:
            try:
                async with session.begin():
                    due = await list_due_for_claim(
                        session, provider="facebook", limit=limit, now=_now(), post_id=post_id
                    )
                    for post in due:
                        claim_result = await claim_for_publishing(session, post)
                        if claim_result == "claimed":
                            counters["claimed"] += 1
                            claimed_ids.append(post.id)
                        elif claim_result == "noop":
                            counters["idempotent"] += 1
                        else:
                            counters["skipped"] += 1
            except Exception:
                logger.exception("social_publish_claim_failed")
                return counters
    except Exception:
        logger.exception("social_publish_cycle_open_session_failed")
        return counters

    for pid in claimed_ids:
        try:
            async with async_session_factory() as session:
                async with session.begin():
                    post = await get_social_post_by_id(session, pid)
                    if post is None:
                        counters["skipped"] += 1
                        continue
                    outcome = await process_claimed_post(session, post, settings=settings)
                    counters["processed"] += 1
                    if outcome == "published":
                        counters["published"] += 1
                    elif outcome == "retried":
                        counters["retried"] += 1
                    elif outcome == "idempotent":
                        counters["idempotent"] += 1
                    elif outcome == "skipped":
                        counters["skipped"] += 1
                    else:
                        counters["failed_final"] += 1
        except Exception:
            logger.exception("social_publish_item_failed", extra={"social_post_id": str(pid)})
            counters["failed_final"] += 1
            counters["processed"] += 1
    return counters


async def process_social_post_safe(post_id: str | uuid.UUID) -> dict | None:
    """Wrapper seguro para dispatch imediato (BackgroundTasks/cron fast path)."""
    try:
        return await run_social_publish_cycle(post_id=post_id, limit=1)
    except Exception:
        logger.exception("social_publish_safe_wrapper_failed", extra={"post_id": str(post_id)})
        return None
