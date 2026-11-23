"""Instagram image media preparation, validation, and public serving (Phase 29).

Implements IMAG-01/02/03 contracts: deterministic hash/versioning, explicit public
HTTPS base URL validation, on-demand generation + durable cache/rebuild, and safe
pt-BR validation messages.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import uuid
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.crud import social_media as social_media_crud
from app.crud.jobs import get_job
from app.models.job import Job
from app.models.social_media_asset import SocialMediaAsset
from app.schemas.social_media import (
    InstagramImageValidation,
    InstagramMediaPrepareResponse,
)
from app.services.social.image_card import (
    CARD_HEIGHT,
    CARD_TEMPLATE_VERSION,
    CARD_WIDTH,
    get_bundled_font_paths,
    render_ig_card,
)

VERSION_HASH_RE = re.compile(r"^[a-f0-9]{16}$")

MSG_MISSING = "Imagem ausente para Instagram. Gere o card da vaga antes de publicar no Instagram."
MSG_INVALID = "Imagem inválida para Instagram. Verifique o formato, tamanho ou disponibilidade pública antes de publicar."
MSG_INVALID_PUBLIC_URL = (
    "A imagem do Instagram não está acessível por uma URL pública HTTPS. Revise a configuração de mídia antes de publicar."
)
MSG_READY = "Imagem pronta para publicação no Instagram."
MSG_NOT_READY = "Imagem do Instagram ainda não está pronta. Gere o card antes de publicar."


def _text_or_empty(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _card_relevant_payload(job: Job) -> dict[str, str]:
    contract_type = _text_or_empty(
        getattr(job, "contract_type", None)
        or getattr(job, "employment", None)
        or getattr(job, "type", None)
    )
    return {
        "template": CARD_TEMPLATE_VERSION,
        "title": _text_or_empty(getattr(job, "title", None)),
        "company": _text_or_empty(getattr(job, "company", None)),
        "city": _text_or_empty(getattr(job, "city", None)),
        "contract_type": contract_type,
        "salary": _text_or_empty(getattr(job, "salary", None)),
    }


def compute_ig_card_hash(job: Job) -> str:
    """Deterministic 16-char SHA-256 hash over card-relevant job fields only."""
    payload = _card_relevant_payload(job)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _is_public_https_base(url: str) -> bool:
    parsed = urlparse((url or "").strip())
    host = (parsed.hostname or "").strip().lower()
    if parsed.scheme != "https" or not host:
        return False
    if host == "localhost" or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return True
    return not (ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local)


def validate_media_public_base_url(settings: Settings | Any) -> tuple[bool, str | None, str | None]:
    """Validate explicit public HTTPS media base URL.

    Returns (valid, code, message). Invalid/missing/localhost/private/non-https =>
    invalid_public_url with pt-BR message.
    """
    base = _text_or_empty(getattr(settings, "MEDIA_PUBLIC_BASE_URL", ""))
    if not base or not _is_public_https_base(base):
        return False, "invalid_public_url", MSG_INVALID_PUBLIC_URL
    return True, None, None


def build_public_ig_media_url(settings: Settings | Any, job_id: uuid.UUID, version_hash: str) -> str:
    base = _text_or_empty(getattr(settings, "MEDIA_PUBLIC_BASE_URL", "")).rstrip("/")
    return f"{base}/api/v1/public/ig-media/{job_id}/{version_hash}.jpg"


def _validation(valid: bool, code: str | None, message: str | None) -> InstagramImageValidation:
    return InstagramImageValidation(valid=valid, code=code, message=message)  # type: ignore[arg-type]


def _provenance(version_hash: str) -> dict[str, str | int | bool | None]:
    return {
        "template_version": CARD_TEMPLATE_VERSION,
        "version_hash": version_hash,
        "generated_from": "job",
        "width": CARD_WIDTH,
        "height": CARD_HEIGHT,
    }


def _response(
    *,
    job_id: uuid.UUID,
    version_hash: str,
    image_url: str | None,
    byte_size: int | None,
    validation: InstagramImageValidation,
    provenance: dict[str, str | int | bool | None] | None = None,
) -> InstagramMediaPrepareResponse:
    return InstagramMediaPrepareResponse(
        job_id=job_id,
        provider="instagram",
        version_hash=version_hash,
        template_version=CARD_TEMPLATE_VERSION,
        image_url=image_url,
        mime_type="image/jpeg",
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        byte_size=byte_size,
        validation=validation,
        provenance=provenance or {},
    )


async def _load_job(session: AsyncSession, job_id: uuid.UUID) -> Job | None:
    return await get_job(session, job_id)


async def _generate_asset_bytes(job: Job) -> bytes:
    regular, bold = get_bundled_font_paths()
    return render_ig_card(job, font_regular_path=regular, font_bold_path=bold)


async def prepare_instagram_media(
    session: AsyncSession,
    job_id: uuid.UUID,
    settings: Settings | Any,
) -> InstagramMediaPrepareResponse:
    """Prepare/validate the exact intended Instagram image for a job (D-02/D-03/D-04)."""
    job = await _load_job(session, job_id)
    if job is None:
        return _response(
            job_id=job_id,
            version_hash="0" * 16,
            image_url=None,
            byte_size=None,
            validation=_validation(False, "missing_image", MSG_MISSING),
            provenance={"template_version": CARD_TEMPLATE_VERSION, "generated_from": "job"},
        )

    version_hash = compute_ig_card_hash(job)
    base_ok, base_code, base_msg = validate_media_public_base_url(settings)
    image_url = build_public_ig_media_url(settings, job_id, version_hash) if base_ok else None

    asset = await social_media_crud.get_media_asset_by_job_version(
        session, job_id=job_id, version_hash=version_hash, provider="instagram"
    )
    if asset is None:
        try:
            image_bytes = await _generate_asset_bytes(job)
        except FileNotFoundError:
            return _response(
                job_id=job_id,
                version_hash=version_hash,
                image_url=image_url,
                byte_size=None,
                validation=_validation(False, "invalid_image", MSG_INVALID),
                provenance=_provenance(version_hash),
            )
        except Exception:
            return _response(
                job_id=job_id,
                version_hash=version_hash,
                image_url=image_url,
                byte_size=None,
                validation=_validation(False, "media_not_ready", MSG_NOT_READY),
                provenance=_provenance(version_hash),
            )

        provenance = _provenance(version_hash)
        asset = await social_media_crud.upsert_media_asset(
            session,
            job_id=job_id,
            provider="instagram",
            version_hash=version_hash,
            template_version=CARD_TEMPLATE_VERSION,
            mime_type="image/jpeg",
            width=CARD_WIDTH,
            height=CARD_HEIGHT,
            byte_size=len(image_bytes),
            image_bytes=image_bytes,
            provenance_json=json.dumps(provenance, ensure_ascii=False, sort_keys=True),
        )

    validation = _validation(True, None, MSG_READY)
    if not base_ok:
        validation = _validation(False, base_code, base_msg)

    return _response(
        job_id=job_id,
        version_hash=version_hash,
        image_url=image_url,
        byte_size=getattr(asset, "byte_size", None),
        validation=validation,
        provenance=_provenance(version_hash),
    )


async def get_or_build_public_asset(
    session: AsyncSession,
    job_id: uuid.UUID,
    version_hash: str,
    settings: Settings | Any,
) -> SocialMediaAsset | None:
    """Resolve public IG media asset by exact job+version.

    Only serves/builds when requested version matches current expected hash for the job,
    preventing arbitrary render abuse and keeping exactness.
    """
    if not VERSION_HASH_RE.fullmatch(version_hash or ""):
        return None

    asset = await social_media_crud.get_media_asset_by_job_version(
        session, job_id=job_id, version_hash=version_hash, provider="instagram"
    )
    if asset is not None and asset.image_bytes:
        return asset

    job = await _load_job(session, job_id)
    if job is None:
        return None

    current_hash = compute_ig_card_hash(job)
    if version_hash != current_hash:
        return None

    try:
        image_bytes = await _generate_asset_bytes(job)
    except Exception:
        return None

    provenance = _provenance(current_hash)
    asset = await social_media_crud.upsert_media_asset(
        session,
        job_id=job_id,
        provider="instagram",
        version_hash=current_hash,
        template_version=CARD_TEMPLATE_VERSION,
        mime_type="image/jpeg",
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        byte_size=len(image_bytes),
        image_bytes=image_bytes,
        provenance_json=json.dumps(provenance, ensure_ascii=False, sort_keys=True),
    )
    await session.commit()
    return asset