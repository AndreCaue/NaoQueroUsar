"""CRUD for durable Instagram/social media assets (Phase 29)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_media_asset import SocialMediaAsset


async def get_media_asset_by_job_version(
    session: AsyncSession,
    job_id: uuid.UUID,
    version_hash: str,
    provider: str = "instagram",
) -> SocialMediaAsset | None:
    stmt = select(SocialMediaAsset).where(
        SocialMediaAsset.job_id == job_id,
        SocialMediaAsset.provider == provider,
        SocialMediaAsset.version_hash == version_hash,
    )
    return await session.scalar(stmt)


async def get_latest_media_asset_for_job(
    session: AsyncSession,
    job_id: uuid.UUID,
    provider: str = "instagram",
) -> SocialMediaAsset | None:
    stmt = (
        select(SocialMediaAsset)
        .where(
            SocialMediaAsset.job_id == job_id,
            SocialMediaAsset.provider == provider,
        )
        .order_by(SocialMediaAsset.updated_at.desc(), SocialMediaAsset.created_at.desc())
        .limit(1)
    )
    return await session.scalar(stmt)


async def upsert_media_asset(
    session: AsyncSession,
    *,
    job_id: uuid.UUID,
    provider: str,
    version_hash: str,
    template_version: str,
    mime_type: str,
    width: int,
    height: int,
    byte_size: int,
    image_bytes: bytes,
    provenance_json: str | None,
) -> SocialMediaAsset:
    """Create or update a durable media asset. Caller owns commit."""
    asset = await get_media_asset_by_job_version(
        session, job_id=job_id, version_hash=version_hash, provider=provider
    )
    now = datetime.now(timezone.utc)
    if asset is None:
        asset = SocialMediaAsset(
            job_id=job_id,
            provider=provider,
            version_hash=version_hash,
            template_version=template_version,
            mime_type=mime_type,
            width=width,
            height=height,
            byte_size=byte_size,
            image_bytes=image_bytes,
            provenance_json=provenance_json,
        )
        session.add(asset)
        await session.flush()
        return asset

    asset.template_version = template_version
    asset.mime_type = mime_type
    asset.width = width
    asset.height = height
    asset.byte_size = byte_size
    asset.image_bytes = image_bytes
    asset.provenance_json = provenance_json
    asset.updated_at = now
    await session.flush()
    return asset