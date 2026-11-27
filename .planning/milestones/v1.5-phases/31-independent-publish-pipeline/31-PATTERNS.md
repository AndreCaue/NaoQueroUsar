# Phase 31: Independent Publish Pipeline - Pattern Map

**Mapped:** 2026-11-25
**Files analyzed:** 18
**Analogs found:** 16 / 18

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/models/social_post.py` | model | CRUD | `backend/app/models/social_post.py` (current) | exact |
| `backend/app/models/social_post_log.py` | model | CRUD | `backend/app/models/social_post_log.py` (current) | exact (likely no schema change; audit via summaries) |
| `backend/app/crud/social_posts.py` | crud | CRUD | `backend/app/crud/social_posts.py` (current) | exact |
| `backend/app/crud/social_accounts.py` | crud | request-response | `backend/app/crud/social_accounts.py::get_active_connected_facebook_account` | exact |
| `backend/app/schemas/social_posts.py` | schema | request-response | `backend/app/schemas/social_posts.py` (current) | exact |
| `backend/app/services/social/publish_pipeline.py` | service | event-driven/async stateful | `backend/app/services/social/publish_pipeline.py` (current) | exact |
| `backend/app/services/social/instagram.py` | service | request-response (2-step external) | `backend/app/services/social/facebook.py` | role-match (different data flow) |
| `backend/app/services/social/types.py` | utility/types | transform | `backend/app/services/social/types.py` (current) | exact |
| `backend/app/services/social/publisher.py` | utility/protocol | request-response | `backend/app/services/social/publisher.py` (current) | exact (likely unchanged) |
| `backend/app/services/social/__init__.py` | config/export | transform | `backend/app/services/social/__init__.py` (current) | exact |
| `backend/app/api/v1/admin.py` | route/controller | request-response | `backend/app/api/v1/admin.py` social endpoints (current) | exact |
| `backend/app/core/config.py` | config | config | `backend/app/core/config.py` (current) | exact |
| `backend/alembic/versions/0008_*_instagram_publish_pipeline.py` | migration | CRUD/schema | `backend/alembic/versions/0007_instagram_review_social_post_publish_enabled.py` | exact |
| `backend/tests/test_instagram_publisher.py` | test | request-response | `backend/tests/test_social_publisher.py` + `backend/tests/test_social_publish_pipeline.py` | role-match |
| `backend/tests/test_social_publish_pipeline.py` | test | async stateful | `backend/tests/test_social_publish_pipeline.py` (current) | exact |
| `backend/tests/test_admin_social_publish.py` | test | request-response | `backend/tests/test_admin_social_publish.py` (current) | exact |
| `frontend/lib/api.ts` | utility/client | request-response | `frontend/lib/api.ts` social section (current) | exact |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | component | request-response | `frontend/app/admin/social-posts/SocialPostsClient.tsx` (current) | exact |
| `frontend/app/admin/review/EditJobDialog.tsx` | component | request-response | `frontend/app/admin/review/EditJobDialog.tsx` (current) | exact |
| `frontend/app/admin/review/ReviewQueue.tsx` | component | request-response | `frontend/app/admin/review/ReviewQueue.tsx` (current) | partial (minimal/no social status today) |

## Pattern Assignments

### `backend/app/models/social_post.py` (model, CRUD)

**Analog:** `backend/app/models/social_post.py` (current, 83 lines - read whole file)

**Imports pattern** (lines 1-11):
```python
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
```

**Core model/field pattern** (lines 22-76):
```python
class SocialPost(Base):
    __tablename__ = "social_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sql_text("gen_random_uuid()"),
    )
    # ...
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sql_text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sql_text("now()"),
    )
```

**Table args/index pattern** (lines 77-83):
```python
    __table_args__ = (
        UniqueConstraint("job_id", "provider", name="uq_social_posts_job_provider"),
        Index("ix_social_posts_status", "status"),
        Index("ix_social_posts_scheduled_at", "scheduled_at"),
        Index("ix_social_posts_next_retry_at", "next_retry_at"),
        Index("ix_social_posts_job_id", "job_id"),
    )
```

**Phase 31 application (D-10, D-12, D-20):** Add explicit IG reconciliation columns on `SocialPost` (not logs). Keep `external_post_id` as final published media ID (A2). Candidate fields: `ig_container_id`, `ig_media_id`/reuse `external_post_id`, `ig_permalink`, `ig_reconciliation_state` (or blocked reason/code), `ig_last_checked_at`/`ig_reconciled_at`, `ig_publish_attempt_id`/step metadata only if needed - keep minimal and deterministic. Use nullable String/Text/TIMESTAMP with safe defaults; add indexes only if query patterns require them. Do **not** add enum status churn unless absolutely necessary (D-12 prefers `failed` + metadata).

---

### `backend/app/crud/social_posts.py` (crud, CRUD)

**Analog:** `backend/app/crud/social_posts.py` (current, 369 lines - read whole file)

**Imports/query pattern** (lines 1-18):
```python
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
```

**Claim eligibility pattern - MUST change for D-05** (lines 108-149):
```python
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
    stmt = select(SocialPost).where(SocialPost.provider == provider)
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
```

**Claim/idempotency pattern** (lines 152-166):
```python
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
```

**Retry-state computation pattern** (lines 219-258):
```python
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
    # ...
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
```

**Status item builder pattern** (lines 261-307):
```python
def build_social_status_item(
    *,
    job_id: uuid.UUID,
    job_title: str | None,
    post: SocialPost | None,
    account_status: SocialAccountStatus | None,
    now: datetime | None = None,
    provider: str = "facebook",
) -> SocialPostStatusItem:
    # ... maps model -> safe schema, includes can_retry/retry_block_reason
    return SocialPostStatusItem(
        ...
        published_url=_safe_published_url(post.external_post_id),
        external_post_id=post.external_post_id,
        attempts=int(post.attempts or 0),
        ...
        can_retry=can_retry,
        retry_block_reason=retry_block_reason,
    )
```

**Phase 31 application:** D-05 - add `SocialPost.publish_enabled.is_(True)` to claim eligibility (both due and post_id-specific paths as appropriate; be careful not to claim disabled drafts). D-12/D-13/D-17/D-19/D-20 - add reconciliation-aware retry-state logic: if IG post is ambiguous/blocked-for-reconciliation, `can_retry` may be true but message must clearly indicate safe reconciliation before publish; do not allow blind retry. Expose provider-aware fields (permalink, IG IDs/audit metadata as safe schema allows). Preserve FB behavior and existing FB ambiguous message compatibility where tests depend on it.

---

### `backend/app/services/social/publish_pipeline.py` (service, async stateful)

**Analog:** `backend/app/services/social/publish_pipeline.py` (current, 407 lines - read whole file)

**Imports/core constants pattern** (lines 1-49):
```python
"""Pipeline único de claim/publicação/retry/idempotência para posts sociais (Phase 17).
...
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
```

**Retry/backoff pattern** (lines 66-79):
```python
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
```

**Failure classification pattern** (lines 82-97):
```python
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
```

**Safe log append pattern** (lines 100-122):
```python
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
```

**Claimed post processing skeleton** (lines 124-293, key excerpts):
```python
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
        return "skipped"

    attempt_number = int(post.attempts or 0) + 1
    publisher = publisher or FacebookPublisher()
    # ... resolve job/link/account/token, publish, classify, persist
```

**Ambiguous/no-auto-retry finalization** (lines 268-293):
```python
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
        session, post, attempts=attempt_number, last_error=safe_msg,
        next_retry_at=None, final=True,
    )
    await _append_log(
        session, post, attempt_number=attempt_number, result=log_result,
        error_message=safe_msg, response_summary=summary,
    )
    return "failed_final"
```

**Worker cycle FB-only pattern - MUST generalize for D-01/D-02/D-04/D-08** (lines 296-398):
```python
async def run_social_publish_cycle(
    *, post_id: uuid.UUID | str | None = None, limit: int = 20
) -> dict:
    """Executa um ciclo de claim/processamento e retorna contadores."""
    settings = get_settings()
    counters = {"claimed": 0, "processed": 0, "published": 0, "retried": 0,
                "failed_final": 0, "skipped": 0, "idempotent": 0}
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
                        # ... counters
            except Exception:
                logger.exception("social_publish_claim_failed")
                return counters
    except Exception:
        logger.exception("social_publish_cycle_open_session_failed")
        return counters
    # ... process claimed_ids with recovery on exception
    return counters
```

**Safe wrapper** (lines 401-407):
```python
async def process_social_post_safe(post_id: str | uuid.UUID) -> dict | None:
    """Wrapper seguro para dispatch imediato (BackgroundTasks/cron fast path)."""
    try:
        return await run_social_publish_cycle(post_id=post_id, limit=1)
    except Exception:
        logger.exception("social_publish_safe_wrapper_failed", extra={"post_id": str(post_id)})
        return None
```

**Phase 31 application:**
- D-01/D-02/D-08: `run_social_publish_cycle` iterates providers (`facebook`, `instagram`) in sequential isolated blocks. Each block has its own try/except, claim, and processing; aggregate totals + `by_provider` breakdown (D-04) while preserving existing top-level keys.
- D-03: extract provider handler/adapter. FB path keeps current behavior. IG handler resolves IG account/readiness/token, revalidates image via `prepare_instagram_media`/`validate_media_public_base_url` as needed (IMAG-01), builds payload, calls Instagram publisher, handles reconciliation.
- D-05 enforced in CRUD claim query.
- D-07: IG account not ready/invalid token/needs_reconnect => final failed, no auto-retry, safe pt-BR action message.
- D-09..D-20: persist container/status/permalink/reconciliation metadata in `social_posts`; ambiguous after critical step => `failed` + `next_retry_at=None` + reconciliation metadata + safe message. Manual retry on ambiguous IG reconciles known IDs before creating/publishing.
- D-18: append safe step logs (container_created, container_status, published, permalink_fetched, reconciled_*), never tokens/payloads.
- PUBL-05 (discretion): classify 2207042/content publishing limit/rate-limit as blocked actionable, no retry storm; no `next_retry_at` auto schedule unless explicitly safe.

---

### `backend/app/services/social/facebook.py` (service, request-response)

**Analog:** self (129 lines - read whole file). Use as closest analog for `instagram.py`.

**Publisher class contract pattern** (lines 51-77):
```python
class FacebookPublisher(SocialPublisher):
    """Publisher real do Facebook via Graph API (backend-only)."""

    async def publish(self, post: SocialPostPayload | object | None = None) -> PublishResult:
        if not isinstance(post, SocialPostPayload):
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

        message = (post.message or "").strip()
        page_id = (post.page_id or "").strip()
        page_access_token = post.page_access_token or ""
        if not message or not page_id or not page_access_token:
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

        settings = get_settings()
        url = f"https://graph.facebook.com/{settings.META_GRAPH_VERSION}/{page_id}/feed"
        data: dict[str, str] = {"message": post.message, "access_token": page_access_token}
        if post.link:
            data["link"] = post.link
```

**HTTP/timeout/ambiguity pattern** (lines 78-129):
```python
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, data=data)
        except httpx.TimeoutException:
            # Timeout antes/depois do envio é tratado como ambíguo por segurança (D-11).
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.ambiguous,
                error_message=_AMBIGUOUS_ERROR,
            )
        except httpx.RequestError:
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.transient,
                error_message=_TRANSIENT_ERROR,
            )

        try:
            body = response.json()
        except ValueError:
            body = None

        if response.status_code < 400 and isinstance(body, dict) and body.get("id"):
            return PublishResult(ok=True, external_post_id=str(body["id"]))

        if response.status_code == 429 or response.status_code >= 500:
            return PublishResult(ok=False, category=PublishFailureCategory.transient, error_message=_TRANSIENT_ERROR)

        if _is_definitive_graph_error(response.status_code, body):
            return PublishResult(ok=False, category=PublishFailureCategory.permanent, error_message=_GENERIC_PERMANENT_ERROR)
```

**Phase 31 application:** `instagram.py` should follow same contract (`SocialPublisher.publish` / `PublishResult`), same safe pt-BR messaging discipline, same httpx + `META_GRAPH_VERSION` usage, same no-token logging. Data flow differs (2-step IG): create container -> optional status poll -> publish container -> best-effort permalink fetch. Timeouts after critical steps must become ambiguous (D-09/D-14). 2207042/rate-limit must be classified safely and not as transient retry-storm (PUBL-05). May need a richer internal result or separate methods called by pipeline handler; keep public/persisted contract safe.

---

### `backend/app/services/social/types.py` (utility/types, transform)

**Analog:** self (29 lines - read whole file)

```python
class PublishFailureCategory(str, Enum):
    transient = "transient"
    permanent = "permanent"
    unknown = "unknown"
    ambiguous = "ambiguous"

@dataclass(frozen=True)
class PublishResult:
    ok: bool
    external_post_id: str | None = None
    category: PublishFailureCategory | None = None
    error_message: str | None = None

@dataclass(frozen=True)
class SocialPostPayload:
    job_id: str
    provider: str
    message: str
    link: str | None = None
    page_id: str | None = None
    page_access_token: str | None = None
```

**Phase 31 application:** Keep backward compatibility. IG may need additional fields (e.g., `image_url`, `ig_user_id`) on payload or a parallel IG-specific payload/type. `PublishResult` may need optional safe metadata fields (container_id, permalink, reconciliation hint, published_media_id) - be careful: dataclass is frozen and used widely; adding optional fields with defaults is backward-compatible. Alternatively keep `PublishResult` stable and return IG metadata through handler/pipeline-specific structures.

---

### `backend/app/api/v1/admin.py` (route/controller, request-response)

**Analog:** existing social endpoints in `admin.py` (read lines 130-299, 350-529, 530-709, 700-878)

**Approve dispatch pattern - currently FB-only, must become provider-independent (D-06, PUBL-01, A4)** (lines 210-289):
```python
    try:
        draft = await get_by_job_provider(
            session,
            job_id,
            provider="facebook",
        )

        if draft is None:
            social_outcome = SocialApproveOutcome(...)
        elif draft.status == SocialPostStatus.scheduled:
            social_outcome = SocialApproveOutcome(status="registered", ...)
            if draft.scheduled_at is not None and draft.scheduled_at <= now_utc():
                dispatch_post_id = draft.id
        elif draft.status == SocialPostStatus.draft:
            final_scheduled_at = draft.scheduled_at if draft.scheduled_at is not None else now_utc()
            await mark_scheduled(session, draft, text=draft.text, scheduled_at=final_scheduled_at)
            await session.commit()
            social_outcome = SocialApproveOutcome(status="registered", ...)
            if final_scheduled_at <= now_utc():
                dispatch_post_id = draft.id
        else:
            social_outcome = SocialApproveOutcome(status="warning", code="social_registration_failed", ...)
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass
        social_outcome = SocialApproveOutcome(status="warning", ...)
        dispatch_post_id = None

    if social_outcome.status == "registered" and dispatch_post_id is not None:
        try:
            background_tasks.add_task(process_social_post_safe, dispatch_post_id)
        except Exception:
            pass

    return JobApproveResponse(job=job_response, social=social_outcome)
```

**Worker endpoint pattern - currently FB-only counters** (lines 360-379):
```python
@router.post("/social/worker", response_model=SocialWorkerResponse)
async def social_worker(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_cron_secret),
) -> SocialWorkerResponse:
    """Processa lote de posts sociais elegíveis (cron Render, idempotente)."""
    # `session` injetada para consistência de dependências; pipeline usa sessões próprias.
    _ = session
    counters = await run_social_publish_cycle()
    defaults = {
        "claimed": 0, "processed": 0, "published": 0, "retried": 0,
        "failed_final": 0, "skipped": 0, "idempotent": 0,
    }
    defaults.update({k: int(v) for k, v in (counters or {}).items() if k in defaults})
    return SocialWorkerResponse(status="ok", **defaults)
```

**Retry endpoint pattern - currently FB-only, D-17 reuses retry with reconciliation semantics** (lines 418-476):
```python
@router.post("/jobs/{job_id}/social-post/retry", response_model=SocialRetryResponse)
async def retry_job_social_post(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialRetryResponse:
    """Retry manual idempotente para post social elegível da vaga."""
    _ = claims
    account = await get_facebook_account(session)
    account_status = _facebook_account_status_value(account)

    item, job_exists = await get_job_social_status_item(
        session, job_id, account_status=account_status, provider="facebook",
    )
    if not job_exists or item is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    post = await get_by_job_provider(session, job_id, provider="facebook")
    if post is None:
        return SocialRetryResponse(outcome="not_eligible", item=item,
                                   message="Nenhum post social registrado para esta vaga.")

    # Idempotência/no-op: estados não elegíveis não disparam duplicata
    if item.status in {"published", "publishing"} or not item.can_retry:
        outcome = "noop" if item.status in {"published", "publishing"} else "not_eligible"
        return SocialRetryResponse(outcome=outcome, item=item,
                                   message=item.retry_block_reason or "Nenhuma nova tentativa necessária.")

    counters = await run_social_publish_cycle(post_id=post.id, limit=1) or {}
    # Recarregar estado atualizado após processamento direcionado
    refreshed_item, _ = await get_job_social_status_item(...)
    ...
```

**Status endpoint pattern** (lines 398-415, 828-846):
```python
@router.get("/jobs/{job_id}/social-status", response_model=SocialPostStatusItem)
async def get_job_social_status(...):
    account = await get_facebook_account(session)
    item, job_exists = await get_job_social_status_item(
        session, job_id, account_status=_facebook_account_status_value(account), provider="facebook",
    )
    if not job_exists or item is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return item

@router.get("/jobs/{job_id}/instagram/social-status", response_model=SocialPostStatusItem)
async def get_job_instagram_social_status(...):
    item, job_exists = await get_job_social_status_item(
        session, job_id, account_status=None, provider="instagram",
    )
    ...
```

**Phase 31 application:**
- D-02/D-04: worker returns aggregated totals + `by_provider` breakdown; keep old top-level fields for compatibility.
- D-06/A4: approve should register/dispatch IG draft independently when eligible/enabled/due, in isolated try/except; FB dispatch/result must not be corrupted by IG failure and vice versa. Keep `JobApproveResponse.social` compatible or extend carefully.
- D-17: retry endpoint should infer provider from post (or support provider-aware path). For IG ambiguous posts, response/message should make reconciliation semantics clear. Reuse existing endpoint shape where possible.
- PUBL-03: status list/items expose safe audit info (IDs/permalink/timestamps/attempts/errors) per provider. Add provider-aware list or include provider in existing list; extend `GET /admin/social-posts` beyond FB-only.
- All admin endpoints keep `require_admin`; worker keeps `require_cron_secret`.

---

### `backend/app/schemas/social_posts.py` (schema, request-response)

**Analog:** self (107 lines - read whole file)

**Status item and response pattern** (lines 62-107):
```python
class SocialPostStatusItem(BaseModel):
    """Status operacional seguro do post social por vaga (UI/admin)."""

    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    job_title: str | None = None
    provider: Literal["facebook", "instagram"] = "facebook"
    status: SocialPostUiStatusLiteral
    status_label: str
    last_error: str | None = None
    published_url: str | None = None
    external_post_id: str | None = None
    attempts: int = 0
    next_retry_at: datetime | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    can_retry: bool = False
    retry_block_reason: str | None = None

class SocialWorkerResponse(BaseModel):
    """Resumo idempotente do ciclo do worker cron."""

    status: Literal["ok"] = "ok"
    claimed: int = 0
    processed: int = 0
    published: int = 0
    retried: int = 0
    failed_final: int = 0
    skipped: int = 0
    idempotent: int = 0
```

**Phase 31 application:** Add PUBL-03 safe audit fields (e.g., `permalink`, `ig_container_id`/`container_id`, `ig_media_id`? be careful not to expose sensitive internals; IDs/permalink are allowed by PUBL-03). Add reconciliation-safe metadata if needed (`reconciliation_state`, `reconciliation_required`, or encode in `retry_block_reason`/`last_error` + dedicated fields). Extend `SocialWorkerResponse` with `by_provider` while preserving existing top-level counters (D-04). Keep fields safe-only; no tokens/secrets/raw payloads.

---

### `backend/app/services/social/image_media.py` (service, request-response)

**Analog:** self (278 lines - read whole file, reused as dependency)

**Validation/prepare pattern to reuse before IG publish (IMAG-01)** (lines 91-109, 155-227):
```python
def validate_media_public_base_url(settings: Settings | Any) -> tuple[bool, str | None, str | None]:
    """Validate explicit public HTTPS media base URL.

    Returns (valid, code, message). Invalid/missing/localhost/private/non-https =>
    invalid_public_url with pt-BR message.
    """
    base = _text_or_empty(getattr(settings, "MEDIA_PUBLIC_BASE_URL", ""))
    if not base or not _is_public_https_base(base):
        return False, "invalid_public_url", MSG_INVALID_PUBLIC_URL
    return True, None, None

async def prepare_instagram_media(
    session: AsyncSession,
    job_id: uuid.UUID,
    settings: Settings | Any,
) -> InstagramMediaPrepareResponse:
    """Prepare/validate the exact intended Instagram image for a job (D-02/D-03/D-04)."""
    ...
```

**Phase 31 application:** IG publish handler must revalidate exact intended image/public URL before creating/publishing container (IMAG-01, Pitfall 5). On invalid/missing/unreachable-public-URL, fail only IG with safe pt-BR message; do not affect FB/site. Reuse `prepare_instagram_media` or `validate_media_public_base_url`+asset resolution; avoid ad-hoc URL checks.

---

### `backend/app/services/social/instagram_readiness.py` (service, request-response)

**Analog:** self (203 lines - read whole file, reused as dependency)

**Readiness result pattern** (lines 14-35, 96-203):
```python
InstagramReadinessState = Literal[
    "ready", "not_connected", "missing_linkage", "missing_permissions", "needs_reconnect", "unknown",
]

@dataclass
class InstagramReadinessResult:
    ready: bool
    ig_user_id: str | None
    ig_username: str | None
    state: InstagramReadinessState
    message: str
    error_code: str | None = None

async def resolve_instagram_readiness(
    *, page_id: str, page_access_token_plain: str, settings: Any
) -> InstagramReadinessResult:
    """Resolve IG readiness for a Facebook Page... safe actionable states; never raises raw provider errors across API boundary."""
```

**Phase 31 application (D-07):** Before IG publish, resolve account/readiness. If not ready / needs reconnect / missing linkage / missing permissions / invalid token, finalize IG post as failed final with actionable pt-BR message; no auto-retry. Reuse `instagram_readiness`/`meta_oauth`/account fields; do not block Facebook.

---

### `backend/app/crud/social_accounts.py` (crud, request-response)

**Analog:** existing Facebook helpers (38 lines - read whole file)

```python
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
    ...
```

**Phase 31 application:** Add IG-equivalent lookup helpers if needed. Note IG readiness is stored additively on the Facebook-linked `SocialAccount` (provider facebook has `ig_user_id`, `ig_readiness_state` per Phase 29 model) - confirm actual model before adding a separate "instagram provider account". Do not assume a separate provider=instagram row unless codebase already uses it.

---

### `backend/alembic/versions/0008_*_instagram_publish_pipeline.py` (migration, schema)

**Analog:** `0007_instagram_review_social_post_publish_enabled.py` (36 lines - read whole file), `0006_ig_readiness_media_foundation.py`

**Migration pattern** (0007):
```python
"""add publish_enabled to social_posts for Instagram review

Revision ID: 0007_instagram_review_social_post_publish_enabled
Revises: 0006_ig_readiness_media_foundation
Create Date: 2026-11-25
...
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_instagram_review_social_post_publish_enabled"
down_revision: str | None = "0006_ig_readiness_media_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "social_posts",
        sa.Column(
            "publish_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("social_posts", "publish_enabled")
```

**Phase 31 application:** Create next revision after 0007. Add explicit IG/reconciliation columns to `social_posts` (D-10). Use nullable columns/defaults safe for existing rows. Keep downgrade symmetrical. Name clearly (e.g., `0008_instagram_publish_reconciliation.py` or as planned).

---

### `backend/tests/test_instagram_publisher.py` (test, request-response)

**Analog:** `backend/tests/test_social_publisher.py` (61 lines - read whole file)

**Contract/async test pattern** (lines 1-61):
```python
"""Contrato SocialPublisher/FacebookPublisher (Phase 17)."""

from __future__ import annotations

import asyncio
import inspect

from app.services.social import (
    FacebookPublisher,
    PublishFailureCategory,
    PublishResult,
    SocialPostPayload,
)


def test_publish_result_and_failure_categories_contract() -> None:
    ok = PublishResult(ok=True, external_post_id="ext-123")
    fail = PublishResult(
        ok=False,
        external_post_id=None,
        category=PublishFailureCategory.transient,
        error_message="falha temporária segura",
    )
    ambiguous = PublishResult(ok=False, category=PublishFailureCategory.ambiguous)
    assert ok.ok is True and ok.external_post_id == "ext-123"
    ...


def test_facebook_publisher_async_contract_and_safe_failure_without_context() -> None:
    publisher = FacebookPublisher()
    assert hasattr(publisher, "publish") and callable(publisher.publish)
    assert inspect.iscoroutinefunction(FacebookPublisher.publish)
    sig = inspect.signature(FacebookPublisher.publish)
    assert "post" in sig.parameters

    result = asyncio.run(publisher.publish(None))

    assert isinstance(result, PublishResult)
    assert result.ok is False
    assert result.external_post_id is None
    assert result.category in {PublishFailureCategory.permanent, PublishFailureCategory.transient, PublishFailureCategory.unknown, PublishFailureCategory.ambiguous}
    assert result.error_message
    assert "access_token" not in (result.error_message or "").lower()
```

**Phase 31 application:** New `test_instagram_publisher.py` should cover IG 2-step flow, timeout/ambiguous classification, 2207042/rate-limit safe classification (PUBL-05), permalink best-effort, no secrets/tokens in messages, configurable `META_GRAPH_VERSION` usage. Mock httpx responses; follow same contract assertions.

---

### `backend/tests/test_social_publish_pipeline.py` (test, async stateful)

**Analog:** self (308 lines - read whole file)

**Fake session / monkeypatch / SimpleNamespace pattern** (lines 1-76, 160-308):
```python
class FakeSession:
    def __init__(self, job=None):
        self._job = job
        self.added = []

    async def get(self, model, ident):
        return self._job

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None

@pytest.mark.asyncio
async def test_pipeline_blocks_when_integration_unavailable_without_auto_retry(monkeypatch):
    from app.services.social import publish_pipeline as pipeline

    job_id = uuid.uuid4()
    post = SimpleNamespace(
        id=uuid.uuid4(), job_id=job_id, provider="facebook", text="Texto",
        status=SocialPostStatus.publishing, attempts=0, next_retry_at=None,
        last_error=None, external_post_id=None, published_at=None,
    )
    settings = SimpleNamespace(
        SITE_PUBLIC_URL="https://site.exemplo/", SOCIAL_MAX_ATTEMPTS=5,
        social_retry_delays_list=[300, 900, 3600, 10800, 21600],
        SOCIAL_TOKEN_ENCRYPTION_KEY="k",
    )
    monkeypatch.setattr(pipeline, "get_active_connected_facebook_account", fake_get_account)
    monkeypatch.setattr(pipeline, "get_facebook_account", fake_get_fb_account)
    monkeypatch.setattr(pipeline, "build_public_job_link", lambda jid, settings=None: f"https://site.exemplo/?vaga={jid}")
    async def noop_log(*args, **kwargs): return None
    monkeypatch.setattr(pipeline, "_append_log", noop_log)

    outcome = await process_claimed_post(FakeSession(job=SimpleNamespace(id=job_id)), post, settings=settings, now=...)
    assert outcome == "failed_final"
```

**Recovery/ambiguous no-retry pattern** (lines 182-308): uses fake session factory with `begin()` tx context managers, monkeypatches CRUD/pipeline functions, asserts ambiguous final state, `next_retry_at is None`, and `compute_social_retry_state` blocks retry with duplicate-avoidance message.

**Phase 31 application:** Extend for D-01/D-05/D-09..D-20/PUBL-01/04/05: provider dispatch isolation, `publish_enabled` claim filter, IG ambiguous container/publish timeout -> blocked reconciliation, retry reconciles before publish, 2207042/rate limit no retry storm, idempotent already-published. Keep existing FB tests passing (HARD-01 regression signal).

---

### `backend/tests/test_admin_social_publish.py` (test, request-response)

**Analog:** self (139 lines - read whole file)

**Admin API test pattern** (lines 1-139):
```python
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import BackgroundTasks

from app.models.social_post import SocialPost, SocialPostStatus

VALID_CF_TOKEN = "token-de-teste"

async def _login(client, admin_password="test-password"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

async def _seed_pending_job(db_session):
    from app.models.job import Job, JobStatus

    job = Job(
        title="Vaga Dispatch", company="Empresa", activities="Atuar",
        city="São Paulo", contact_phone="+55 11 99999-1111",
        status=JobStatus.pending,
    )
    db_session.add(job)
    await db_session.flush()
    return job
```

**BackgroundTasks dispatch spy pattern** (lines 59-78):
```python
    calls = []
    original_add_task = BackgroundTasks.add_task

    def spy_add_task(self, func, *args, **kwargs):
        calls.append((getattr(func, "__name__", str(func)), args, kwargs))
        return original_add_task(self, func, *args, **kwargs)

    monkeypatch.setattr(BackgroundTasks, "add_task", spy_add_task)
    # ... approve
    assert any(name == "process_social_post_safe" and args and str(args[0]) == str(post.id) for name, args, _ in calls)
```

**Phase 31 application:** Extend for IG approve dispatch independence (D-06/PUBL-01), worker breakdown by provider (D-04), provider-aware retry/status/list, IG ambiguity/reconciliation admin semantics (D-17/PUBL-03/04). Preserve FB-only behavior assertions.

---

### `frontend/lib/api.ts` (utility/client, request-response)

**Analog:** social section in `api.ts` (read lines 409-460, 524-640, 800-899)

**Types pattern** (lines 409-437, 817-853):
```ts
export type SocialPublishMode = "publish_now" | "schedule";
export type SocialDraftOrigin = "llm" | "template_fallback";
export type SocialApproveStatus = "registered" | "skipped" | "warning";

export interface SocialPostDraft {
  job_id: string;
  provider: "facebook" | "instagram";
  status: "draft" | "scheduled" | "publishing" | "published" | "failed" | "cancelled";
  publish_mode: SocialPublishMode | null;
  text: string;
  origin: SocialDraftOrigin | null;
  saved: boolean;
  frozen: boolean;
  warning: string | null;
  publish_enabled: boolean;
}

export type SocialStatusValue =
  | "none" | "draft" | "scheduled" | "publishing" | "published" | "failed" | "cancelled";

export interface SocialPostStatusItem {
  job_id: string;
  job_title?: string | null;
  provider: "facebook" | "instagram";
  status: SocialStatusValue;
  status_label: string;
  last_error: string | null;
  published_url: string | null;
  external_post_id: string | null;
  attempts: number;
  next_retry_at: string | null;
  scheduled_at: string | null;
  published_at: string | null;
  can_retry: boolean;
  retry_block_reason: string | null;
}

export interface SocialRetryResponse {
  outcome?: "retried" | "noop" | "not_eligible" | "not_found";
  item?: SocialPostStatusItem | null;
  message?: string | null;
  status?: string;
}
```

**Fetch/error pattern** (lines 855-899):
```ts
export async function getSocialStatus(
  token: string,
  jobId: string,
): Promise<SocialPostStatusItem | null> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 404) { return null; }
  if (!res.ok) { throw new ApiError(await readError(res), res.status); }
  return (await res.json()) as SocialPostStatusItem;
}

export async function retrySocialPost(
  token: string,
  jobId: string,
): Promise<SocialRetryResponse> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-post/retry`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) { throw new ApiError(await readError(res), res.status); }
  return (await res.json()) as SocialRetryResponse;
}
```

**Phase 31 application:** Extend status item with safe PUBL-03 fields (permalink, container/media IDs if exposed, reconciliation flags/messages/timestamps). Extend worker/list/retry types for provider-aware responses/breakdowns as needed. Keep backward compatibility for existing consumers. Use `ApiError` and `readError` pattern.

---

### `frontend/app/admin/social-posts/SocialPostsClient.tsx` (component, request-response)

**Analog:** self (292 lines - read whole file)

**Client component/auth/error handling pattern** (lines 1-122):
```tsx
"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { useAdminGuard } from "@/components/admin/AdminGuard";
import { useToast } from "@/components/admin/ToastProvider";
import {
  ApiError,
  getAdminSocialPosts,
  retrySocialPost,
  type SocialPostStatusItem,
} from "@/lib/api";
import { buildAdminLoginHref } from "@/lib/adminReturnTo";
import { TOKEN_KEY } from "@/lib/auth";

function formatBrtDateTime(value: string | null | undefined): string | null { ... }

function badgeClass(status: SocialPostStatusItem["status"]): string { ... }

export function SocialPostsClient() {
  const token = useAdminGuard();
  const { toast } = useToast();
  const [items, setItems] = useState<SocialPostStatusItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState<Record<string, boolean>>({});
  const retryingRef = useRef<Record<string, boolean>>({});
  ...
  const handleAuthError = useCallback((err: unknown): boolean => {
    if (err instanceof ApiError && err.status === 401) {
      try { sessionStorage.removeItem(TOKEN_KEY); } catch {}
      window.location.replace(buildAdminLoginHref(`${window.location.pathname}${window.location.search}`));
      return true;
    }
    return false;
  }, []);
```

**Provider-specific rendering to generalize** (lines 214-234, 260-267):
```tsx
{item.status === "published" ? (
  <div className="space-y-1">
    <p className="text-fg">Publicado no Facebook.</p>
    {published ? <p className="text-fg-muted">Publicado em {published} (America/Sao_Paulo).</p> : null}
    {item.published_url ? (
      <a href={item.published_url} target="_blank" rel="noopener noreferrer" ...>
        Ver post no Facebook
      </a>
    ) : (
      <p className="text-fg-muted">Publicado no Facebook. Link indisponível.</p>
    )}
  </div>
) : null}

{reconnectNeeded ? (
  <a href="/admin/integracoes" ...>Abrir Integrações</a>
) : null}
```

**Phase 31 application (PUBL-03, D-17):** Make provider-aware (Facebook/Instagram labels, permalink/ID display). Show safe audit info (attempts, timestamps, last error, IDs/permalink when available). For ambiguous IG blocked state, show actionable reconciliation message and keep retry action clear/safe. Do not expose tokens/secrets. Reuse existing badge/loading/auth/toast patterns.

---

### `frontend/app/admin/review/EditJobDialog.tsx` (component, request-response)

**Analog:** self (large file; read 1-260, grepped key sections)

**Imports/state pattern** (lines 1-38, 245-286):
```tsx
import {
  ApiError, generateInstagramSocialDraft, generateSocialDraft, getInstagramSocialDraft,
  getInstagramSocialStatus, getMetaIntegrationStatus, getSocialDraft, getSocialStatus,
  prepareInstagramMedia, retrySocialPost, saveInstagramSocialDraft, saveSocialDraft,
  updateJob, type InstagramMediaPrepareResponse, type JobAdmin, type JobUpdate,
  type MetaInstagramReadiness, type SocialPostDraft, type SocialPostStatusItem, type SocialPublishMode,
} from "@/lib/api";
// ...
const [retryingSocial, setRetryingSocial] = useState(false);
const retryInFlightRef = useRef(false);
```

**Retry handler pattern** (lines ~579-605 from grep): uses `retryInFlightRef` guard, calls `retrySocialPost(token, job.id)`, handles outcome `noop/not_eligible`, toasts, refreshes status.

**Phase 31 application:** IG retry/status surfaces must reflect reconciliation semantics (D-17/PUBL-03). Show safe IDs/permalink/timestamps/audit hints where useful. Keep Facebook section behavior unchanged. Reuse existing per-provider status state and retry controls.

---

## Shared Patterns

### 1. Safe pt-BR error messages (no secrets/tokens)
**Source:** `backend/app/services/social/publish_pipeline.py:41-48`, `backend/app/services/social/facebook.py:12-19`
```python
MSG_RECONNECT = "Conexão com o Facebook indisponível. Reconecte a integração para publicar."
MSG_TRANSIENT = "Falha temporária ao publicar. Uma nova tentativa será feita automaticamente."
MSG_AMBIGUOUS = (
    "Não foi possível confirmar a publicação. Verifique antes de tentar novamente para evitar duplicidade."
)
MSG_PERMANENT = "Não foi possível publicar este post. Revise a integração ou o conteúdo e tente novamente."
```
**Apply to:** All new IG pipeline/publisher/admin messages. Add IG-specific safe messages for: not ready/needs reconnect, ambiguous container/publish requiring reconciliation, rate limit/content publishing limit blocked, invalid/expired container. Never include access tokens, raw Graph payloads, or secrets.

### 2. Ambiguous/critical failure = no auto-retry
**Source:** `backend/app/services/social/publish_pipeline.py:268-293`, `backend/app/services/social/facebook.py:82-87`
```python
except httpx.TimeoutException:
    # Timeout antes/depois do envio é tratado como ambíguo por segurança (D-11).
    return PublishResult(ok=False, category=PublishFailureCategory.ambiguous, error_message=_AMBIGUOUS_ERROR)
# ...
if category == PublishFailureCategory.ambiguous:
    log_result = "ambiguous"
    summary = "ambiguous_no_auto_retry"
...
await mark_failed(session, post, attempts=attempt_number, last_error=safe_msg, next_retry_at=None, final=True)
```
**Apply to:** IG container creation timeout, publish timeout, inconclusive status polling, and any post-critical unknown result. Persist known IDs/metadata; do not schedule `next_retry_at`.

### 3. Safe attempt logging (sanitized, no payloads/tokens)
**Source:** `backend/app/services/social/publish_pipeline.py:53-122`
```python
def _safe_text(value: str | None, max_len: int = 500) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text

async def _append_log(..., result=..., http_status=None, error_message=None, response_summary=None, external_post_id=None):
    log = SocialPostLog(..., result=_safe_text(result, 32) or "failed", ...)
    session.add(log)
    await session.flush()
```
**Apply to:** All IG pipeline steps (container create/status check/publish/permalink/reconcile). Log safe summaries like `ig_container_created`, `ig_status_in_progress`, `ig_publish_ambiguous`, `ig_reconciled_published`, `ig_rate_limit_blocked`.

### 4. Idempotency guard before publish
**Source:** `backend/app/services/social/publish_pipeline.py:137-143`
```python
# Idempotência: nunca republicar item já publicado/com external_post_id
if post.status == SocialPostStatus.published or post.external_post_id:
    return "idempotent"

if post.status != SocialPostStatus.publishing:
    # Defesa defensiva: só processa se estiver em publishing
    return "skipped"
```
**Apply to:** IG handler and reconciliation flow. Before any IG publish/create action, check published/external_post_id and reconciliation state. If reconciliation finds already-published media, mark local published (D-20).

### 5. Provider-isolated dispatch and error containment
**Source:** `backend/app/api/v1/admin.py:210-289`
```python
try:
    # provider registration/dispatch
    ...
except Exception:
    try:
        await session.rollback()
    except Exception:
        pass
    social_outcome = SocialApproveOutcome(status="warning", code="social_registration_failed", ...)
    dispatch_post_id = None

if social_outcome.status == "registered" and dispatch_post_id is not None:
    try:
        background_tasks.add_task(process_social_post_safe, dispatch_post_id)
    except Exception:
        pass
```
**Apply to:** FB and IG approve/dispatch blocks independently (D-06/PUBL-01). One provider's failure must not corrupt or block the other. Worker provider blocks isolated (D-08).

### 6. Admin auth / cron secret guards
**Source:** `backend/app/api/v1/admin.py:360-366, 398-405`
```python
@router.post("/social/worker", response_model=SocialWorkerResponse)
async def social_worker(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_cron_secret),
) -> SocialWorkerResponse:

@router.get("/jobs/{job_id}/social-status", response_model=SocialPostStatusItem)
async def get_job_social_status(
    ...
    claims: dict = Depends(require_admin),
) -> SocialPostStatusItem:
```
**Apply to:** Any new/modified admin or worker endpoint. Keep existing auth model; no public publish endpoints.

### 7. Frontend admin fetch/auth/toast pattern
**Source:** `frontend/lib/api.ts:855-899`, `frontend/app/admin/social-posts/SocialPostsClient.tsx:54-122`
```ts
const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-post/retry`, {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` },
});
if (!res.ok) { throw new ApiError(await readError(res), res.status); }
return (await res.json()) as SocialRetryResponse;
```
```tsx
const handleAuthError = useCallback((err: unknown): boolean => {
  if (err instanceof ApiError && err.status === 401) {
    try { sessionStorage.removeItem(TOKEN_KEY); } catch {}
    window.location.replace(buildAdminLoginHref(`${window.location.pathname}${window.location.search}`));
    return true;
  }
  return false;
}, []);
```
**Apply to:** Any new social status/retry/audit UI behavior. Use `ApiError`, 401 redirect, toast feedback, in-flight guards.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/app/services/social/instagram.py` | service | request-response (2-step external) | No existing IG content publishing service. `facebook.py` is closest role-match but IG requires 2-step container/status/publish + reconciliation/permalink; data flow is stateful/ambiguous. Use FacebookPublisher as contract/structure analog; follow D-09..D-16/PUBL-02/PUBL-04/PUBL-05. |
| `backend/tests/test_instagram_publisher.py` | test | request-response/mocked HTTP | No existing IG publisher tests. Use `test_social_publisher.py` contract style + pipeline test mocking style. |

## Metadata

**Analog search scope:** `backend/app/services/social`, `backend/app/models`, `backend/app/crud`, `backend/app/schemas`, `backend/app/api/v1/admin.py`, `backend/app/core/config.py`, `backend/alembic/versions`, `backend/tests`, `frontend/lib/api.ts`, `frontend/app/admin/review`, `frontend/app/admin/social-posts`
**Files scanned:** ~30 targeted files
**Pattern extraction date:** 2026-11-25
