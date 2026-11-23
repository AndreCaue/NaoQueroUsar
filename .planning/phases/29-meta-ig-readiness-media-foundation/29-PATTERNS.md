# Phase 29: Meta/IG Readiness & Media Foundation - Pattern Map

**Mapped:** 2026-11-23
**Files analyzed:** 25
**Analogs found:** 22 / 25

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/models/social_account.py` | model | CRUD/schema extension | `backend/app/models/social_account.py` (self) + `backend/app/models/social_oauth_pending.py` | exact |
| `backend/app/schemas/social_integrations.py` | schema | request-response | `backend/app/schemas/social_integrations.py` (self) | exact |
| `backend/app/api/v1/integrations.py` | route | request-response | `backend/app/api/v1/integrations.py` (self) | exact |
| `backend/app/services/social/meta_oauth.py` | service | external API / request-response | `backend/app/services/social/meta_oauth.py` (self) | exact |
| `backend/app/crud/social_accounts.py` | crud | CRUD | `backend/app/crud/social_accounts.py` (self) + `backend/app/crud/social_posts.py` | exact |
| `backend/app/core/config.py` | config | config/validation | `backend/app/core/config.py` (self) | exact |
| `backend/.env.example` | config | config/docs | `backend/.env.example` (self) | exact |
| `backend/pyproject.toml` | config | dependency manifest | `backend/pyproject.toml` (self) | exact |
| `backend/app/models/__init__.py` | model registry | import wiring | `backend/app/models/__init__.py` (self) | exact |
| `backend/alembic/env.py` | migration config | import wiring | `backend/alembic/env.py` (self) | exact |
| `backend/app/models/social_media_asset.py` | model | CRUD | `backend/app/models/social_post.py` | role-match |
| `backend/app/schemas/social_media.py` | schema | request-response | `backend/app/schemas/social_posts.py` | role-match |
| `backend/app/crud/social_media.py` | crud | CRUD | `backend/app/crud/social_posts.py` | role-match |
| `backend/app/services/social/instagram_readiness.py` | service | external API / readiness | `backend/app/services/social/meta_oauth.py` | role-match |
| `backend/app/services/social/image_card.py` | service | transform/render | `backend/app/services/social/post_generation.py` | partial |
| `backend/app/services/social/image_media.py` | service | CRUD + cache/file/URL | `backend/app/services/social/post_generation.py` + `backend/app/services/social/crypto.py` | partial |
| `backend/app/api/v1/public.py` (extend) | route | request-response / public read | `backend/app/api/v1/public.py` (self) | exact |
| `backend/app/api/v1/admin.py` (extend) | route | request-response / admin | `backend/app/api/v1/admin.py` (self) | exact |
| `backend/alembic/versions/0006_*_ig_readiness_media.py` | migration | schema migration | `backend/alembic/versions/0004_social_foundation.py`, `0005_social_oauth_pending.py` | exact |
| `frontend/app/admin/integracoes/IntegrationsClient.tsx` | component | UI state / request-response | `frontend/app/admin/integracoes/IntegrationsClient.tsx` (self) | exact |
| `frontend/app/admin/integracoes/page.tsx` | page component | render | `frontend/app/admin/integracoes/page.tsx` (self) | exact |
| `frontend/lib/api.ts` | client utility | request-response | `frontend/lib/api.ts` (self) | exact |
| `docs/META-INTEGRATION-TESTING.md` | docs | operational checklist | `docs/META-INTEGRATION-TESTING.md` (self) | exact |
| `backend/assets/fonts/*` | static asset | build/runtime asset | No code analog (new asset dir) | none |
| `backend/tests/test_*instagram* / test_*ig_media*` | test | verification | `backend/tests/test_meta_oauth_flow.py`, `test_meta_oauth_security.py`, `test_social_models.py` | exact |

## Pattern Assignments

### `backend/app/models/social_account.py` (model, CRUD/schema extension)

**Analog:** self; style reference `backend/app/models/social_oauth_pending.py` for simple timestamped model fields.

**Imports / enum / column style** (`backend/app/models/social_account.py:1-18`):
```python
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SAEnum, Index, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SocialAccountStatus(str, Enum):
    connected = "connected"
    needs_reconnect = "needs_reconnect"
    disconnected = "disconnected"
```

**Column declaration pattern** (`backend/app/models/social_account.py:19-57`):
```python
class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    page_id: Mapped[str] = mapped_column(String(128), nullable=False)
    page_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SocialAccountStatus] = mapped_column(
        SAEnum(SocialAccountStatus, name="social_account_status", native_enum=True),
        nullable=False,
        server_default=text("'connected'"),
    )
    connected_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    token_checked_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_social_accounts_provider_status", "provider", "status"),
        Index("ix_social_accounts_page_id", "page_id"),
    )
```

**Apply for Phase 29:** Add additive IG fields per D-13 (e.g. `ig_user_id`, `ig_username`, IG readiness state, timestamps/safe error fields as decided). Keep FB `status` semantics intact (D-15). Do not store plaintext tokens/secrets; any sensitive data must follow `crypto.py` encryption pattern.

---

### `backend/app/schemas/social_integrations.py` (schema, request-response)

**Analog:** self.

**Schema style** (`backend/app/schemas/social_integrations.py:1-47`):
```python
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MetaIntegrationAlert(BaseModel):
    code: str
    message: str


class MetaIntegrationStatus(BaseModel):
    provider: Literal["facebook"] = "facebook"
    status: Literal["connected", "needs_reconnect", "disconnected"]
    page_id: str | None = None
    page_name: str | None = None
    connected_at: datetime | None = None
    token_checked_at: datetime | None = None
    pending_selection: bool = False
    alert: MetaIntegrationAlert | None = None


class MetaActionResponse(BaseModel):
    status: Literal["connected", "needs_reconnect", "disconnected"]
    message: str | None = None
    pending_selection: bool | None = None
```

**Apply for Phase 29:** Extend with additive `instagram` readiness payload (RESEARCH example `MetaInstagramReadiness`) without removing existing FB fields. Keep fields safe/no-secret. Use Literal states for actionable IG readiness; include safe pt-BR message.

---

### `backend/app/api/v1/integrations.py` (route, request-response)

**Analog:** self.

**Router/dependency/error pattern** (`backend/app/api/v1/integrations.py:1-67`):
```python
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.deps import get_session, require_admin
from app.schemas.social_integrations import (
    MetaActionResponse,
    MetaIntegrationStatus,
    MetaOAuthStartResponse,
    MetaPendingSelectionResponse,
    MetaSelectPageRequest,
)
from app.services.social.meta_oauth import (
    MetaOAuthConfigError,
    MetaOAuthGraphError,
    MetaOAuthPendingError,
    complete_oauth_callback,
    confirm_pending_selection,
    disconnect_meta as disconnect_meta_service,
    get_current_meta_status,
    get_oauth_start_response,
    list_pending_pages,
    verify_current_connection,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/integrations", tags=["admin-integrations"])

AdminClaims = Annotated[dict, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]

MISSING_META_CONFIG_DETAIL = "Integração com Facebook não configurada"
```

**Endpoint commit/rollback pattern** (`backend/app/api/v1/integrations.py:134-151`):
```python
@router.post("/meta/verify", response_model=MetaActionResponse)
async def verify_meta_connection(
    claims: Annotated[dict, Depends(require_admin)],
    session: DbSession,
    settings: AppSettings,
) -> MetaActionResponse:
    _ = claims
    try:
        response = await verify_current_connection(session, settings)
        await session.commit()
        return response
    except MetaOAuthConfigError as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail=MISSING_META_CONFIG_DETAIL) from exc
    except Exception as exc:  # noqa: BLE001
        await session.rollback()
        logger.warning("meta_oauth_verify_failed_safe", extra={"error_type": type(exc).__name__})
        raise HTTPException(status_code=503, detail="Não foi possível verificar a conexão agora. Tente novamente.") from exc
```

**Apply for Phase 29:** Keep endpoints admin-only. Extend `/meta/status` and `/meta/verify` responses to include IG readiness. If adding an explicit IG prepare/check endpoint, follow same dependency typing, safe error mapping, commit/rollback, and no-secrets logging.

---

### `backend/app/services/social/meta_oauth.py` (service, external API / request-response)

**Analog:** self. This is the primary Meta integration analog.

**Module constants/error classes pattern** (`backend/app/services/social/meta_oauth.py:27-58`):
```python
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


class MetaOAuthConfigError(MetaOAuthError):
    """Missing/invalid Meta OAuth configuration."""
```

**Graph GET helper / safe failure** (`backend/app/services/social/meta_oauth.py:119-142`):
```python
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
```

**Connection status construction / alert pattern** (`backend/app/services/social/meta_oauth.py:289-344`):
```python
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
```

**Verify pattern (definitive vs transient)** (`backend/app/services/social/meta_oauth.py:603-635`):
```python
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
```

**Apply for Phase 29:** Extend scopes in `META_OAUTH_SCOPES` carefully (D-15, META-02); include IG scopes (`instagram_basic`, `instagram_content_publish` per RESEARCH, confirm exact set). Resolve IG via Graph `/{page-id}?fields=instagram_business_account{id,username}` using stored Page token. Evaluate readiness without breaking FB status: IG missing scopes/linkage should be actionable IG state, not FB disconnect (D-15). Do not query Graph on every status GET (D-14) - status reads persisted readiness; connect/verify/confirm refresh. Keep safe logging (no token, no raw body).

---

### `backend/app/crud/social_accounts.py` (crud, CRUD)

**Analog:** self; pattern reference `backend/app/crud/social_posts.py`.

**CRUD style** (`backend/app/crud/social_accounts.py:1-38`):
```python
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
```

**Apply for Phase 29:** Add helpers only if needed for IG readiness lookups/updates; avoid duplicating logic already in `meta_oauth.py`. Keep `session.flush()` only, caller commits.

---

### `backend/app/core/config.py` (config, validation)

**Analog:** self.

**Settings field + validator pattern** (`backend/app/core/config.py:82-129`):
```python
    # --- Integração Social / Meta (Phase 14 - Fundação) ---
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_GRAPH_VERSION: str = "v21.0"
    META_OAUTH_REDIRECT_URI: str = ""
    SOCIAL_TOKEN_ENCRYPTION_KEY: str = ""
    SOCIAL_WORKER_SECRET: str = ""
    SOCIAL_MAX_ATTEMPTS: int = 5
    SOCIAL_RETRY_DELAYS: str = "300,900,3600,10800,21600"
    SITE_PUBLIC_URL: str = ""
    # Política de conteúdo do post social (Phase 16): por padrão sem empresa/contatos.
    SOCIAL_POST_INCLUDE_CONTACT: bool = False

    @model_validator(mode="after")
    def _validate_social_foundation(self) -> "Settings":
        site_url = self.SITE_PUBLIC_URL.strip()
        if site_url:
            parsed = urlparse(site_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("SITE_PUBLIC_URL deve ser uma URL http/https válida")
```

**Apply for Phase 29:** Add explicit public media base env (D-12). Name is OpenCode's Discretion; RESEARCH recommends validating HTTPS/public/non-localhost. Suggested: `MEDIA_PUBLIC_BASE_URL` or `BACKEND_PUBLIC_URL` - pick one, document in `.env.example`, validate with `urlparse` + private/localhost rejection. Add any IG/media cache settings only if needed.

---

### `backend/app/models/social_media_asset.py` (model, CRUD) — NEW

**Analog:** `backend/app/models/social_post.py` and `backend/app/models/social_oauth_pending.py`.

**Model/table pattern** (`backend/app/models/social_post.py:1-78`):
```python
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SAEnum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SocialPost(Base):
    __tablename__ = "social_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sql_text("gen_random_uuid()"),
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    ...
    __table_args__ = (
        UniqueConstraint("job_id", "provider", name="uq_social_posts_job_provider"),
        Index("ix_social_posts_status", "status"),
        ...
    )
```

**Apply for Phase 29:** If persisting media asset/bytes (RESEARCH A3 recommendation), model should key by job+version/hash, store content type/size/bytes or path metadata, provenance (template version, hash, generated_at), and be rebuildable. Keep no PII beyond job card content; no secrets. Include indexes for `(job_id, version_hash)` lookup.

---

### `backend/app/schemas/social_media.py` (schema, request-response) — NEW

**Analog:** `backend/app/schemas/social_posts.py`.

**Schema pattern** (`backend/app/schemas/social_posts.py:1-49`):
```python
"""Schemas de draft/status/retry/worker social (Phases 16/17).

Contratos compartilhados entre geração, CRUD e endpoints admin.
Campos seguros apenas (sem tokens/segredos/payload bruto).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SocialPostDraftResponse(BaseModel):
    """Rascunho/estado do post social para UI admin (Phase 16)."""

    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    provider: Literal["facebook"] = "facebook"
    status: SocialPostStatusLiteral
    text: str
    ...
```

**Apply for Phase 29:** Define admin prepare/validate response (job_id, image_url, version_hash, valid, validation_errors/reason_code, provenance, mime/size/width/height as needed) and public/internal contracts. Keep safe fields only. IMAG-01 feedback codes must be clear pt-BR.

---

### `backend/app/crud/social_media.py` (crud, CRUD) — NEW

**Analog:** `backend/app/crud/social_posts.py`.

**CRUD upsert/get pattern** (`backend/app/crud/social_posts.py:20-60`):
```python
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
    """Cria ou atualiza rascunho por (job_id, provider)."""
    post = await get_by_job_provider(session, job_id, provider=provider)
    if post is None:
        post = SocialPost(...)
        session.add(post)
        await session.flush()
        return post
    ...
    await session.flush()
    return post
```

**Apply for Phase 29:** Implement `get_by_job_and_version` / `upsert_media_asset` / `get_latest_for_job` as needed. Flush only; caller commits. Use deterministic version hash as key.

---

### `backend/app/services/social/instagram_readiness.py` (service, external API/readiness) — NEW

**Analog:** `backend/app/services/social/meta_oauth.py` (same domain, split by responsibility per RESEARCH).

**Safe graph call + classification patterns** (`backend/app/services/social/meta_oauth.py:126-142, 227-287`):
```python
async def _graph_get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=_GRAPH_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, params=params)
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        raise exc
    ...
    if not isinstance(data, dict):
        raise MetaOAuthGraphError("Resposta inválida da integração.")
    return data


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
    return "transient"
```

**Apply for Phase 29:** Isolate IG Graph/readiness rules here. Probe `/{page-id}?fields=instagram_business_account{id,username}`. Map outcomes to safe actionable states: `ready`, `missing_linkage`, `missing_permissions`, `needs_reconnect`, `unknown`. Never log token; reuse token decrypt/graph helpers or carefully import shared patterns.

---

### `backend/app/services/social/image_card.py` (service, transform/render) — NEW

**Analog:** `backend/app/services/social/post_generation.py` for service structure/settings injection; rendering itself has no code analog.

**Service module shape** (`backend/app/services/social/post_generation.py:1-21` excerpted pattern):
```python
import uuid
from types import SimpleNamespace

import pytest  # (test analog; service uses normal imports)

from app.services.social.post_generation import (
    FALLBACK_WARNING,
    build_public_job_link,
    generate_draft_for_job,
)
```
(Use actual service file style: typed functions, settings passed explicitly, pure deterministic output.)

**Card rendering contract (from RESEARCH, implement with Pillow)** (`.planning/phases/29-meta-ig-readiness-media-foundation/29-RESEARCH.md:416-441`):
```python
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350  # D-05
BG = "#0f0a1a"
PURPLE = "#8b5cf6"

def render_ig_card(job, font_regular, font_bold) -> bytes:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # layout omitted: deterministic text wrapping, no contacts, CTA "link na bio"
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90, optimize=True, progressive=True, subsampling="4:2:0")
    data = buf.getvalue()
    quality = 90
    while len(data) > 8 * 1024 * 1024 and quality >= 70:
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        data = buf.getvalue()
        quality -= 5
    return data
```

**Apply for Phase 29:** D-01/05/06/07/08. Deterministic only: bundled fonts from `backend/assets/fonts/`, fixed layout, no timestamp/random, RGB JPEG sRGB-compatible output, <8MB. No contact fields. Include template version in hash input.

---

### `backend/app/services/social/image_media.py` (service, CRUD+cache/URL/validation) — NEW

**Analog:** `post_generation.py` for job-driven generation; `crypto.py` for small focused helpers; config validators for URL validation.

**Deterministic hash pattern** (`.planning/phases/29-meta-ig-readiness-media-foundation/29-RESEARCH.md:255-274`):
```python
import hashlib, json

CARD_TEMPLATE_VERSION = "ig-card-v1"

def compute_ig_card_hash(job) -> str:
    payload = {
        "template": CARD_TEMPLATE_VERSION,
        "title": job.title or "",
        "company": job.company or "",
        "city": job.city or "",
        "contract_type": getattr(job, "contract_type", None) or getattr(job, "employment_type", None) or "",
        "salary": job.salary or "",
        # D-07: no contacts in card; do not include contact fields
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
```

**Public base URL validation pattern** (`.planning/phases/29-meta-ig-readiness-media-foundation/29-RESEARCH.md:392-414`):
```python
from urllib.parse import urlparse
import ipaddress

def validate_public_https_base(url: str, field_name: str) -> str:
    value = (url or "").strip()
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        raise ValueError(f"{field_name} deve ser uma URL HTTPS pública válida")
    if host in {"localhost"} or host.endswith(".local"):
        raise ValueError(f"{field_name} não pode apontar para host local")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            raise ValueError(f"{field_name} não pode apontar para IP privado/local")
    except ValueError:
        # hostname (non-IP) is acceptable if HTTPS/public
        pass
    return value.rstrip("/")
```

**Apply for Phase 29:** D-02/03/10/11/12/IMAG-01/03. Compute version hash from card-relevant fields only. Build public URL from explicit env base; validate HTTPS/public/non-localhost. On-demand generate + cache; rebuild from Job if missing. Return validation/provenance metadata for admin and publish guard.

---

### `backend/app/api/v1/public.py` (route, public read) — EXTEND

**Analog:** self.

**Public router / no-auth endpoint pattern** (`backend/app/api/v1/public.py:31-35, 196-207`):
```python
# Mounted by router.py without an extra prefix, so these resolve to
# /api/v1/public/jobs and /api/v1/public/jobs/{id}. NO auth dependency:
# the public read surface is anonymous by design (D-16).
router = APIRouter(prefix="/public", tags=["public"])

...

@router.get("/jobs/{job_id}", response_model=JobPublic)
async def get_public_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> JobPublic:
    """Return public detail for a published, non-expired job; 404 otherwise (D-17)."""
    # Phase boundary (D-18): no reveal/contact endpoint here — that is Phase 3.
    job = await get_published(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return JobPublic.model_validate(job)
```

**Apply for Phase 29:** Add unauthenticated media endpoint (D-09/D-12) such as `GET /public/ig-media/{job_id}/{version}.jpg` returning `Response(content=bytes, media_type="image/jpeg")` with cache headers. No auth dependency. Must not leak internal errors/secrets; 404 on missing/unbuildable asset. Validate version/hash format to avoid path abuse.

---

### `backend/app/api/v1/admin.py` (route, admin) — EXTEND

**Analog:** self, especially social post endpoints.

**Admin job-scoped endpoint pattern** (`backend/app/api/v1/admin.py:490-553`):
```python
@router.get("/jobs/{job_id}/social-post", response_model=SocialPostDraftResponse)
async def get_job_social_post(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialPostDraftResponse:
    """Consulta rascunho social salvo por vaga/provider (facebook)."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    post = await get_by_job_provider(session, job_id, provider="facebook")
    if post is None:
        raise HTTPException(status_code=404, detail="Rascunho social não encontrado")
    return _draft_response(post)
```

**Apply for Phase 29:** Add idempotent admin prepare endpoint (RESEARCH open question 4 recommends `POST /api/v1/admin/jobs/{id}/instagram/media/prepare`) returning image URL, version_hash, valid, validation_errors, provenance. Require admin. Use `get_job`/404 pattern; return safe pt-BR validation messages.

---

### `backend/alembic/versions/0006_*_ig_readiness_media.py` (migration, schema migration) — NEW

**Analog:** `0004_social_foundation.py`, `0005_social_oauth_pending.py`.

**Migration header/structure pattern** (`backend/alembic/versions/0005_social_oauth_pending.py:1-72`):
```python
"""add social oauth pending selection table

Revision ID: 0005_social_oauth_pending
Revises: 0004_social_foundation
Create Date: 2026-11-15

Transient backend-mediated pending page selection for Meta OAuth (D-08).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_social_oauth_pending"
down_revision: str | None = "0004_social_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(...)

def downgrade() -> None:
    op.drop_index(...)
    op.drop_table(...)
```

**Apply for Phase 29:** New revision down_revision `0005_social_oauth_pending` (confirm latest at plan time). Add IG readiness columns to `social_accounts` via `op.add_column`/`op.drop_column`, and/or create `social_media_assets` table if durable storage chosen. For enum/status fields prefer String or constrained SAEnum consistent with model; adding native enum values in Postgres requires care - prefer String/Text or follow existing enum pattern cautiously. Include indexes for lookup by job/version.

---

### `frontend/app/admin/integracoes/IntegrationsClient.tsx` (component, UI state / request-response)

**Analog:** self.

**Client component state/action pattern** (`frontend/app/admin/integracoes/IntegrationsClient.tsx:1-23, 46-67`):
```tsx
"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useAdminGuard } from "@/components/admin/AdminGuard";
import { useToast } from "@/components/admin/ToastProvider";
import {
  ApiError,
  confirmMetaPageSelection,
  disconnectMetaIntegration,
  getMetaIntegrationStatus,
  getMetaPendingSelection,
  startMetaOAuth,
  verifyMetaIntegration,
  type MetaIntegrationStatus,
  type MetaPendingPage,
} from "@/lib/api";

...

export function IntegrationsClient() {
  const token = useAdminGuard();
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const router = useRouter();

  const [status, setStatus] = useState<MetaIntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<
    "start" | "verify" | "confirm" | "disconnect" | null
  >(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [banner, setBanner] = useState<{ kind: BannerKind; text: string } | null>(null);
```

**Connected status card / actions pattern** (`frontend/app/admin/integracoes/IntegrationsClient.tsx:374-428`):
```tsx
) : effectiveStatus === "connected" ? (
  <div className="space-y-4">
    <div>
      <h2 className="text-xl font-semibold">Página do Facebook conectada</h2>
      <p className="mt-1 text-base text-fg-muted">
        A integração está ativa para a página exibida abaixo. Você pode verificar a conexão agora ou desconectar quando quiser.
      </p>
    </div>
    <dl className="grid gap-2 text-sm text-fg-muted sm:grid-cols-2">...
    </dl>
    {status?.alert?.message && (
      <div className="rounded-[12px] border border-line bg-canvas px-4 py-3 text-sm text-fg">
        {status.alert.message}
      </div>
    )}
    <div className="flex flex-wrap gap-2">
      <button ... className="inline-flex min-h-[44px] ... bg-accent ...">Verificar agora</button>
      <button ... className="inline-flex min-h-[44px] ... border-danger ...">Desconectar</button>
    </div>
  </div>
```

**Apply for Phase 29:** Add additive IG readiness panel inside connected/needs_reconnect states per UI-SPEC. Do not regress FB flow. Keep pt-BR actionable copy, 44px min-h controls, banner classes, dialog pattern. IG not ready must not render as FB disconnected (D-15). Use `status.instagram` (or decided field) additive payload.

---

### `frontend/lib/api.ts` (client utility, request-response)

**Analog:** self.

**Type + fetch helper pattern** (`frontend/lib/api.ts:558-604`):
```ts
export interface MetaIntegrationStatus {
  provider: "facebook";
  status: "connected" | "needs_reconnect" | "disconnected";
  page_id: string | null;
  page_name: string | null;
  connected_at: string | null;
  token_checked_at: string | null;
  pending_selection: boolean;
  alert: MetaIntegrationAlert | null;
}

export async function getMetaIntegrationStatus(
  token: string,
): Promise<MetaIntegrationStatus> {
  const res = await fetch(`${API}/api/v1/admin/integrations/meta/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as MetaIntegrationStatus;
}
```

**Apply for Phase 29:** Extend `MetaIntegrationStatus` with additive `instagram` readiness type (UI-SPEC states: ready, missing_linkage, missing_permissions, needs_reconnect, unknown). Add any new admin media prepare/validate function following same auth header + `ApiError` pattern.

---

### `docs/META-INTEGRATION-TESTING.md` (docs, operational checklist)

**Analog:** self.

**Doc structure pattern** (`docs/META-INTEGRATION-TESTING.md:1-45`):
```md
# Integração Meta/Facebook — roteiro de teste manual e operação (TEST-04, DOC-01)

Este documento descreve como configurar e validar a integração social (Facebook Pages) em **modo desenvolvimento**, além de checklists operacionais para cron/Render e App Review/modo Live. Não contém segredos reais.

## 1) Setup do app Meta e Página em modo desenvolvimento

### Pré-requisitos
...
### Permissões mínimas
...
### Variáveis de ambiente relacionadas (backend, placeholders)
...
```

**Apply for Phase 29 (META-03):** Add IG scopes, Page↔IG Business/Creator linkage prerequisites, `instagram_business_account` readiness checks, explicit env vars for media base URL, App Review/Advanced Access/roles/tasks assumptions, and manual checklist. Clearly mark manual/live verification as handoff - no fabricated pass.

---

### `backend/app/models/__init__.py` and `backend/alembic/env.py` (registry wiring)

**Analogs:** self.

**Model export pattern** (`backend/app/models/__init__.py:1-16`):
```python
from app.models.job import Job, JobStatus
from app.models.social_account import SocialAccount, SocialAccountStatus
from app.models.social_oauth_pending import SocialOAuthPending
from app.models.social_post import SocialPost, SocialPostStatus
from app.models.social_post_log import SocialPostLog

__all__ = [
    "Job",
    "JobStatus",
    "SocialAccount",
    "SocialAccountStatus",
    "SocialOAuthPending",
    "SocialPost",
    "SocialPostStatus",
    "SocialPostLog",
]
```

**Alembic env import pattern** (`backend/alembic/env.py:15-24`):
```python
# Import models so their tables are registered on Base.metadata before
# Alembic reads target_metadata (autogenerate support).
from app.models import (  # noqa: F401
    Job,
    JobStatus,
    SocialAccount,
    SocialAccountStatus,
    SocialPost,
    SocialPostLog,
    SocialPostStatus,
)
```

**Apply for Phase 29:** If new model `SocialMediaAsset` is added, register it in both files; if only extending `SocialAccount`, no new model registration needed but migration still required.

---

## Shared Patterns

### Safe external integration errors (no token/secret leaks)
**Source:** `backend/app/services/social/meta_oauth.py:27-58,126-142`; `backend/app/api/v1/integrations.py:134-151`
**Apply to:** `instagram_readiness.py`, integrations endpoints, media prepare endpoints, public media endpoint.

```python
_SAFE_TRANSIENT_VERIFY = "Não foi possível verificar a conexão agora. Tente novamente."

class MetaOAuthGraphError(MetaOAuthError):
    """Safe Graph/OAuth operation failure."""

logger.warning("meta_oauth_verify_failed_safe", extra={"error_type": type(exc).__name__})
raise HTTPException(status_code=503, detail="Não foi possível verificar a conexão agora. Tente novamente.") from exc
```

**Rule:** Never log or return `access_token`, `page_access_token`, `client_secret`, encrypted blobs, raw Graph response bodies. Map to safe pt-BR messages.

### Admin-only endpoint dependency + commit/rollback
**Source:** `backend/app/api/v1/integrations.py:37-39,134-151`; `backend/app/api/v1/admin.py:490-505`
**Apply to:** any new admin IG/media endpoints.

```python
AdminClaims = Annotated[dict, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]

_ = claims
try:
    response = await service_call(session, settings)
    await session.commit()
    return response
except KnownSafeError as exc:
    await session.rollback()
    raise HTTPException(status_code=..., detail="...") from exc
```

### SQLAlchemy 2.0 async model/CRUD style
**Source:** `backend/app/models/social_post.py:1-78`, `backend/app/crud/social_posts.py:20-60`
**Apply to:** `social_media_asset.py`, `crud/social_media.py`, SocialAccount IG fields.

```python
id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()"))
...
stmt = select(Model).where(...)
return await session.scalar(stmt)
...
session.add(obj)
await session.flush()
```

### Frontend admin token + ApiError + 44px controls
**Source:** `frontend/lib/api.ts:594-604`, `frontend/app/admin/integracoes/IntegrationsClient.tsx:411-426`
**Apply to:** IntegrationsClient IG readiness UI, any new admin media API calls.

```ts
const res = await fetch(`${API}/api/v1/admin/integrations/meta/status`, {
  headers: { Authorization: `Bearer ${token}` },
});
if (!res.ok) {
  throw new ApiError(await readError(res), res.status);
}
return (await res.json()) as MetaIntegrationStatus;
```

```tsx
<button
  type="button"
  onClick={handleVerify}
  disabled={actionLoading !== null}
  className="inline-flex min-h-[44px] items-center justify-center rounded-[12px] bg-accent px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
>
  {actionLoading === "verify" ? "Verificando conexão..." : "Verificar agora"}
</button>
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/assets/fonts/*` | static asset | build/runtime asset | No existing bundled font assets for deterministic Pillow rendering. Need to add licensed font files (OFL/Apache) and load by explicit path. |
| `backend/app/services/social/image_card.py` (render internals) | service | transform/render | No existing Pillow/image-rendering service in codebase; `post_generation.py` gives service shape, but canvas/text-wrap/JPEG layout is new. Use RESEARCH code sketch as starting contract. |
| `backend/app/api/v1/public.py` binary image response | route | public file/bytes read | No existing endpoint returns image bytes/`Response(media_type="image/jpeg")`; public.py has JSON patterns only. Use FastAPI `Response` pattern from RESEARCH. |

## Metadata

**Analog search scope:** `backend/app/models`, `backend/app/schemas`, `backend/app/api/v1`, `backend/app/services/social`, `backend/app/crud`, `backend/tests`, `backend/alembic/versions`, `frontend/app/admin/integracoes`, `frontend/lib`, `docs`, `backend/core`
**Files scanned:** 35+ files (globs + targeted reads)
**Pattern extraction date:** 2026-11-23
**Key constraints observed:** D-01..D-16, META-01..03, IMAG-01..03; additive IG readiness must not break FB; no token/secret leaks; public media endpoint unauthenticated but safe; deterministic Pillow 1080x1350 JPEG <8MB; explicit HTTPS public media base URL.
