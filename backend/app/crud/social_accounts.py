"""CRUD de contas sociais para publicação (Phase 17).

Operações com flush apenas quando aplicável; o chamador controla commit/rollback.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_account import SocialAccount, SocialAccountStatus


async def get_active_connected_facebook_account(
    session: AsyncSession,
) -> SocialAccount | None:
    """Retorna a conta Facebook conectada/ativa (admin único), sem expor token."""
    stmt = (
        select(SocialAccount)
        .where(
            SocialAccount.provider == "facebook",
            SocialAccount.status == SocialAccountStatus.connected,
        )
        .order_by(SocialAccount.updated_at.desc(), SocialAccount.created_at.desc())
        .limit(1)
    )
    return await session.scalar(stmt)


async def get_facebook_account(session: AsyncSession) -> SocialAccount | None:
    """Retorna a conta Facebook mais recente para diferenciar estados (D-06)."""
    stmt = (
        select(SocialAccount)
        .where(SocialAccount.provider == "facebook")
        .order_by(SocialAccount.updated_at.desc(), SocialAccount.created_at.desc())
        .limit(1)
    )
    return await session.scalar(stmt)
