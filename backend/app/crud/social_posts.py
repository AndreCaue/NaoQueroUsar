"""CRUD de social_posts (draft/schedule/publish pipeline/status) - Phases 16/17.

Operações com flush apenas quando aplicável; o chamador controla commit/rollback.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.social_account import SocialAccountStatus
from app.models.social_post import SocialPost, SocialPostStatus
from app.schemas.social_posts import SocialPostStatusItem


async def get_by_job_provider(
    session: AsyncSession,
    job_id: uuid.UUID,
    provider: str = "facebook",
) -> SocialPost | None:
    stmt = select(SocialPost).where(
        SocialPost.job_id == job_id,
        SocialPost.provider == provider,
    )
    return await session.scalar(stmt)


async def upsert_draft(
    session: AsyncSession,
    job_id: uuid.UUID,
    *,
    text: str,
    scheduled_at,
    provider: str = "facebook",
    publish_enabled: bool | None = None,
) -> SocialPost:
    """Cria ou atualiza rascunho por (job_id, provider)."""
    post = await get_by_job_provider(session, job_id, provider=provider)
    if post is None:
        post = SocialPost(
            job_id=job_id,
            provider=provider,
            text=text,
            status=SocialPostStatus.draft,
            scheduled_at=scheduled_at,
            publish_enabled=True if publish_enabled is None else bool(publish_enabled),
        )
        session.add(post)
        await session.flush()
        return post

    if post.status != SocialPostStatus.draft:
        raise ValueError("frozen")

    post.text = text
    post.scheduled_at = scheduled_at
    if publish_enabled is not None:
        post.publish_enabled = bool(publish_enabled)
    await session.flush()
    return post


async def mark_scheduled(
    session: AsyncSession,
    social_post: SocialPost,
    *,
    text: str,
    scheduled_at,
) -> SocialPost:
    """Marca registro como agendado para envio (sem publicar)."""
    social_post.status = SocialPostStatus.scheduled
    social_post.text = text
    social_post.scheduled_at = scheduled_at
    social_post.next_retry_at = None
    social_post.last_error = None
    await session.flush()
    return social_post


def _as_uuid(value: uuid.UUID | str | None) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _as_job_uuid(value: uuid.UUID | str | None) -> uuid.UUID | None:
    try:
        return _as_uuid(value)
    except Exception:
        return None


async def get_social_post_by_id(
    session: AsyncSession, post_id: uuid.UUID | str
) -> SocialPost | None:
    post_uuid = _as_uuid(post_id)
    if post_uuid is None:
        return None
    return await session.get(SocialPost, post_uuid)


async def list_due_for_claim(
    session: AsyncSession,
    *,
    provider: str = "facebook",
    limit: int = 20,
    now: datetime | None = None,
    post_id: uuid.UUID | str | None = None,
) -> list[SocialPost]:
    """Seleciona posts elegíveis para claim com lock (D-04/D-12)."""
    now = now or datetime.now(timezone.utc)
    stmt = select(SocialPost).where(
        SocialPost.provider == provider,
        SocialPost.publish_enabled.is_(True),
    )
    if post_id is not None:
        stmt = stmt.where(SocialPost.id == _as_uuid(post_id))
        # Alvo específico: permitir claim do post em estado elegível/idempotente;
        # elegibilidade funcional (retry/manual) é validada no endpoint/pipeline.
        stmt = stmt.where(
            or_(
                SocialPost.status == SocialPostStatus.scheduled,
                SocialPost.status == SocialPostStatus.failed,
            )
        )
    else:
        stmt = stmt.where(
            or_(
                (SocialPost.status == SocialPostStatus.scheduled)
                & (SocialPost.scheduled_at.is_not(None))
                & (SocialPost.scheduled_at <= now),
                (SocialPost.status == SocialPostStatus.failed)
                & (SocialPost.next_retry_at.is_not(None))
                & (SocialPost.next_retry_at <= now),
            )
        )
    stmt = stmt.order_by(
        SocialPost.next_retry_at.asc().nulls_last(),
        SocialPost.scheduled_at.asc().nulls_last(),
        SocialPost.created_at.asc(),
    )
    if limit:
        stmt = stmt.limit(limit)
    stmt = stmt.with_for_update(skip_locked=True)
    result = await session.scalars(stmt)
    return list(result.all())


async def claim_for_publishing(
    session: AsyncSession, post: SocialPost, *, now: datetime | None = None
) -> str:
    """Marca elegível como publishing ou retorna no-op idempotente."""
    _ = now or datetime.now(timezone.utc)
    if post.status == SocialPostStatus.published or post.external_post_id:
        return "noop"
    if post.status not in {SocialPostStatus.scheduled, SocialPostStatus.failed}:
        return "skipped"
    post.status = SocialPostStatus.publishing
    post.next_retry_at = None
    post.last_error = None
    await session.flush()
    return "claimed"


async def mark_published(
    session: AsyncSession,
    post: SocialPost,
    *,
    external_post_id: str,
    published_at: datetime | None = None,
) -> SocialPost:
    post.status = SocialPostStatus.published
    post.external_post_id = external_post_id
    post.published_at = published_at or datetime.now(timezone.utc)
    post.last_error = None
    post.next_retry_at = None
    await session.flush()
    return post


async def mark_failed(
    session: AsyncSession,
    post: SocialPost,
    *,
    attempts: int,
    last_error: str,
    next_retry_at: datetime | None,
    final: bool,
) -> SocialPost:
    post.status = SocialPostStatus.failed
    post.attempts = attempts
    post.last_error = last_error
    post.next_retry_at = None if final else next_retry_at
    await session.flush()
    return post


_STATUS_LABELS_PT = {
    "none": "Sem rascunho",
    "draft": "Rascunho",
    "scheduled": "Agendado",
    "publishing": "Publicando",
    "published": "Publicado",
    "failed": "Falhou",
    "cancelled": "Cancelado",
}


def _safe_published_url(external_post_id: str | None) -> str | None:
    # Evita derivar permalink possivelmente incorreto; expõe external_post_id com segurança.
    _ = external_post_id
    return None


def compute_social_retry_state(
    post: SocialPost | None,
    account_status: SocialAccountStatus | None,
    *,
    now: datetime | None = None,
) -> tuple[bool, str | None]:
    """Retorna (can_retry, retry_block_reason) conforme D-15/UI-SPEC."""
    now = now or datetime.now(timezone.utc)
    if post is None:
        return False, None

    if post.status == SocialPostStatus.published or post.external_post_id:
        return False, "Post já publicado"
    if post.status == SocialPostStatus.publishing:
        return False, "Publicação em andamento"
    if post.status == SocialPostStatus.draft:
        return False, None
    if post.status == SocialPostStatus.cancelled:
        return False, "Post cancelado"
    if post.status == SocialPostStatus.scheduled:
        if post.scheduled_at and post.scheduled_at > now:
            return False, "Aguardando horário agendado"
        return False, "Publicação em andamento"

    if post.status != SocialPostStatus.failed:
        return False, "Tentativa automática indisponível. Verifique o erro antes de prosseguir."

    if (
        post.next_retry_at is None
        and post.last_error
        == "Não foi possível confirmar a publicação. Verifique antes de tentar novamente para evitar duplicidade."
    ):
        return (
            False,
            "Verifique a publicação no Facebook antes de tentar novamente para evitar duplicidade.",
        )

    if account_status != SocialAccountStatus.connected:
        return False, "Reconexão necessária"

    return True, None


def build_social_status_item(
    *,
    job_id: uuid.UUID,
    job_title: str | None,
    post: SocialPost | None,
    account_status: SocialAccountStatus | None,
    now: datetime | None = None,
    provider: str = "facebook",
) -> SocialPostStatusItem:
    now = now or datetime.now(timezone.utc)
    if post is None:
        return SocialPostStatusItem(
            job_id=job_id,
            job_title=job_title,
            provider=provider,
            status="none",
            status_label=_STATUS_LABELS_PT["none"],
            last_error=None,
            published_url=None,
            external_post_id=None,
            attempts=0,
            next_retry_at=None,
            scheduled_at=None,
            published_at=None,
            can_retry=False,
            retry_block_reason=None,
        )

    status_value = post.status.value if isinstance(post.status, SocialPostStatus) else str(post.status)
    status_label = _STATUS_LABELS_PT.get(status_value, status_value)
    can_retry, retry_block_reason = compute_social_retry_state(post, account_status, now=now)
    return SocialPostStatusItem(
        job_id=post.job_id,
        job_title=job_title,
        provider=post.provider or "facebook",
        status=status_value,  # type: ignore[arg-type]
        status_label=status_label,
        last_error=post.last_error,
        published_url=_safe_published_url(post.external_post_id),
        external_post_id=post.external_post_id,
        attempts=int(post.attempts or 0),
        next_retry_at=post.next_retry_at,
        scheduled_at=post.scheduled_at,
        published_at=post.published_at,
        can_retry=can_retry,
        retry_block_reason=retry_block_reason,
    )


async def get_job_social_status_item(
    session: AsyncSession,
    job_id: uuid.UUID | str,
    *,
    account_status: SocialAccountStatus | None = None,
    provider: str = "facebook",
    now: datetime | None = None,
) -> tuple[SocialPostStatusItem | None, bool]:
    """Retorna (item, job_exists)."""
    job_uuid = _as_job_uuid(job_id)
    if job_uuid is None:
        return None, False
    job = await session.get(Job, job_uuid)
    if job is None:
        return None, False
    post = await get_by_job_provider(session, job_uuid, provider=provider)
    return (
        build_social_status_item(
            job_id=job.id,
            job_title=getattr(job, "title", None),
            post=post,
            account_status=account_status,
            now=now,
            provider=provider,
        ),
        True,
    )


async def list_social_status_items(
    session: AsyncSession,
    *,
    account_status: SocialAccountStatus | None = None,
    provider: str = "facebook",
    limit: int = 200,
    now: datetime | None = None,
) -> list[SocialPostStatusItem]:
    """Lista visão operacional simples de posts/vagas sociais (D-13)."""
    now = now or datetime.now(timezone.utc)
    stmt = (
        select(SocialPost, Job)
        .join(Job, Job.id == SocialPost.job_id)
        .where(SocialPost.provider == provider)
        .order_by(SocialPost.updated_at.desc(), SocialPost.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    items: list[SocialPostStatusItem] = []
    for post, job in result.all():
        items.append(
            build_social_status_item(
                job_id=job.id,
                job_title=getattr(job, "title", None),
                post=post,
                account_status=account_status,
                now=now,
                provider=provider,
            )
        )
    return items
