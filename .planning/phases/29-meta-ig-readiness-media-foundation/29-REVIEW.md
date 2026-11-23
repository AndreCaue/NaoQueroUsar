---
phase: 29-meta-ig-readiness-media-foundation
reviewed: 2026-11-23T13:56:19Z
depth: standard
files_reviewed: 32
files_reviewed_list:
  - backend/.env.example
  - backend/alembic/env.py
  - backend/alembic/versions/0006_ig_readiness_media_foundation.py
  - backend/app/api/v1/admin.py
  - backend/app/api/v1/public.py
  - backend/app/core/config.py
  - backend/app/crud/social_media.py
  - backend/app/models/__init__.py
  - backend/app/models/social_account.py
  - backend/app/models/social_media_asset.py
  - backend/app/schemas/social_integrations.py
  - backend/app/schemas/social_media.py
  - backend/app/services/social/image_card.py
  - backend/app/services/social/image_media.py
  - backend/app/services/social/instagram_readiness.py
  - backend/app/services/social/meta_oauth.py
  - backend/assets/fonts/DejaVuSans.ttf
  - backend/assets/fonts/DejaVuSans-Bold.ttf
  - backend/assets/fonts/README.md
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/test_docs_meta_instagram.py
  - backend/tests/test_ig_media_card.py
  - backend/tests/test_ig_media_validation.py
  - backend/tests/test_integrations_instagram.py
  - backend/tests/test_meta_oauth_instagram.py
  - backend/tests/test_public_ig_media.py
  - backend/uv.lock
  - docs/META-INTEGRATION-TESTING.md
  - frontend/app/admin/integracoes/IntegrationsClient.tsx
  - frontend/app/admin/integracoes/page.tsx
  - frontend/lib/api.ts
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 29: Code Review Report

**Reviewed:** 2026-11-23T13:56:19Z
**Depth:** standard
**Files Reviewed:** 32
**Status:** issues_found

## Summary

Reviewed Phase 29 Meta/IG readiness and media foundation changes across backend models/migration, Meta OAuth/Instagram readiness services, IG media rendering/validation/public serving, admin/frontend integrations UI, and tests/docs. The implementation is largely aligned with the phase intent: additive IG readiness, safe pt-BR Graph error mapping, deterministic versioned media, and no secret exposure in API contracts.

No critical security or data-loss defects were found. Two warnings were identified: dead/confusing code containing a hardcoded key-shaped constant in Meta disconnect logic, and a race condition in IG media asset upsert that can cause public media 500s under concurrent cache-miss requests. Two low-severity maintainability items were also noted.

## Warnings

### WR-01: Dead disconnect code contains a hardcoded Fernet-key-shaped constant

**File:** `backend/app/services/social/meta_oauth.py:514-518`
**Issue:** `disconnect_meta` contains unreachable dead code (`if False ...`) that builds an encrypted token using a hardcoded base64 key-shaped literal, then immediately deletes the account. The code is never executed, but it is confusing, looks like a secret-handling path to scanners/readers, and obscures the actual disconnect behavior.
**Fix:**
```python
async def disconnect_meta(session: AsyncSession) -> MetaActionResponse:
    stmt = select(SocialAccount).where(SocialAccount.provider == "facebook")
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    if account is not None:
        # Safer: delete active record so no reusable secret remains; UI shows disconnected.
        await session.delete(account)
    await session.execute(
        delete(SocialOAuthPending).where(SocialOAuthPending.provider == "facebook")
    )
    await session.flush()
    return MetaActionResponse(
        status="disconnected",
        message="Integração com Facebook desconectada.",
        pending_selection=False,
        instagram=_instagram_readiness_not_connected(),
    )
```

### WR-02: IG media upsert is vulnerable to concurrent insert race

**File:** `backend/app/crud/social_media.py:60-90`, `backend/app/services/social/image_media.py:244-278`
**Issue:** `upsert_media_asset` performs check-then-insert/flush without conflict handling. The public endpoint `GET /api/v1/public/ig-media/{job_id}/{version}.jpg` calls `get_or_build_public_asset`, which can render and upsert on cache miss. Two concurrent requests for the same uncached `job_id + provider + version_hash` can both observe no row and attempt insert, hitting `uq_social_media_assets_job_provider_version` and causing an IntegrityError/500 response.
**Fix:**
```python
# backend/app/crud/social_media.py
from sqlalchemy.dialects.postgresql import insert

async def upsert_media_asset(... ) -> SocialMediaAsset:
    now = datetime.now(timezone.utc)
    stmt = insert(SocialMediaAsset).values(
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
    stmt = stmt.on_conflict_do_update(
        constraint="uq_social_media_assets_job_provider_version",
        set_={
            "template_version": template_version,
            "mime_type": mime_type,
            "width": width,
            "height": height,
            "byte_size": byte_size,
            "image_bytes": image_bytes,
            "provenance_json": provenance_json,
            "updated_at": now,
        },
    ).returning(SocialMediaAsset)
    return (await session.execute(stmt)).scalar_one()
```

Callers that need the write visible immediately (public serving path) should commit explicitly; keep transaction ownership consistent.

## Info

### IN-01: Inconsistent transaction commit ownership in IG media flow

**File:** `backend/app/services/social/image_media.py:277`, `backend/app/api/v1/admin.py:143-145`
**Issue:** `get_or_build_public_asset` commits the session internally, while `prepare_instagram_media` does not commit and the admin prepare endpoint commits after calling it. This mixed ownership makes transaction boundaries less predictable and can surprise future callers composing these services.
**Fix:**
```python
# Prefer caller-owned transactions for service functions.
# Option A: remove commit from get_or_build_public_asset and commit in public endpoint:
asset = await get_or_build_public_asset(session, job_id, version, settings)
if asset is None or not getattr(asset, "image_bytes", None):
    raise HTTPException(status_code=404, detail="Mídia não encontrada")
await session.commit()
return Response(...)
```

If service-level commit is retained intentionally for public rebuilds, document it clearly in the function contract.

### IN-02: Redundant job lookup in admin IG media prepare endpoint

**File:** `backend/app/api/v1/admin.py:139-143`
**Issue:** The endpoint loads the job to return 404, then `prepare_instagram_media` loads the same job again by ID. This is a small unnecessary query on an admin-only path.
**Fix:**
```python
job = await get_job(session, job_id)
if job is None:
    raise HTTPException(status_code=404, detail="Vaga não encontrada")

result = await prepare_instagram_media(session, job_id, settings, job=job)
await session.commit()
return result
```

Adjust `prepare_instagram_media` to accept an optional preloaded `job` to avoid duplicate reads.

---

_Reviewed: 2026-11-23T13:56:19Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
