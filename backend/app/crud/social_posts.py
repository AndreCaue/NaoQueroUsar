"""CRUD de social_posts (draft/schedule/publish pipeline) — Phases 16/17.

Operações com flush apenas; o chamador controla commit/rollback.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_post import SocialPost, SocialPostStatus


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
) -> SocialPost:
    """Cria ou atualiza rascunho por (job_id, provider).

    Registros com status diferente de draft são imutáveis para edição.
    UniqueConstraint uq_social_posts_job_provider garante unicidade por par.
    """
    post = await get_by_job_provider(session, job_id, provider=provider)
    if post is None:
        post = SocialPost(
            job_id=job_id,
            provider=provider,
            text=text,
            status=SocialPostStatus.draft,
            scheduled_at=scheduled_at,
        )
        session.add(post)
        await session.flush()
        return post

    if post.status != SocialPostStatus.draft:
        raise ValueError("frozen")

    post.text = text
    post.scheduled_at = scheduled_at
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
    # limpa estado transitório/retry anterior de forma segura
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
    """Seleciona posts elegíveis para claim com lock (D-04)."""
    now = now or datetime.now(timezone.utc)
    stmt = select(SocialPost).where(SocialPost.provider == provider)
    if post_id is not None:
        stmt = stmt.where(SocialPost.id == _as_uuid(post_id))
    stmt = stmt.where(
        or_(
            (SocialPost.status == SocialPostStatus.scheduled)
            & (SocialPost.scheduled_at.is_not(None))
            & (SocialPost.scheduled_at <= now),
            (SocialPost.status == SocialPostStatus.failed)
            & (SocialPost.next_retry_at.is_not(None))
            & (SocialPost.next_retry_at <= now),
        )
    ).order_by(
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

