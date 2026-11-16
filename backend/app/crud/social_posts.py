"""CRUD de social_posts (draft/schedule) — Phase 16.

Operações com flush apenas; o chamador controla commit/rollback.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
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
