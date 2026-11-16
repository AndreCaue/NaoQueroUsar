# Phase 17: Publicação Assíncrona, Retry, Idempotência e Status - Pattern Map

**Mapped:** 2026-11-16
**Files analyzed:** 24
**Analogs found:** 23 / 24

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/app/api/v1/admin.py` | route/controller (admin API) | request-response + async dispatch trigger | `backend/app/api/v1/admin.py` (existing approve/expire/draft endpoints) | exact |
| `backend/app/crud/social_posts.py` | CRUD/repository | DB read/write (claim/status/retry queries) | `backend/app/crud/social_posts.py` (existing upsert/schedule) | exact |
| `backend/app/crud/social_accounts.py` | CRUD/repository (new) | DB read (active connected account lookup) | `backend/app/crud/social_posts.py` + `backend/app/models/social_account.py` usage patterns | role-match |
| `backend/app/services/social/publish_pipeline.py` | service/worker pipeline (new) | batch/claim -> external I/O -> DB state transitions | `backend/app/core/scheduler.py` (in-process async job/drain semantics) + `backend/app/api/v1/admin.py` (best-effort orchestration) | role-match |
| `backend/app/services/social/facebook.py` | service/provider integration | request-response (outbound HTTP to Graph API) | `backend/app/services/social/facebook.py` stub + `backend/app/services/social/meta_oauth.py`/project `httpx` usage | exact (stub to implement) |
| `backend/app/services/social/types.py` | types/contract | data transform (result/error categories) | `backend/app/services/social/types.py` | exact |
| `backend/app/services/social/publisher.py` | service contract/protocol | request-response | `backend/app/services/social/publisher.py` | exact |
| `backend/app/schemas/social_posts.py` | schema (Pydantic) | request/response transform | `backend/app/schemas/social_posts.py` + `backend/app/schemas/job.py` conventions | exact |
| `backend/app/models/social_post.py` | model/ORM (likely unchanged) | DB persistence/state | `backend/app/models/social_post.py` | exact |
| `backend/app/models/social_post_log.py` | model/ORM (use/possibly extend via writes) | DB append/logging | `backend/app/models/social_post_log.py` | exact |
| `backend/app/deps.py` | dependency/auth guard (reuse) | request-response guard | `backend/app/deps.py` (`require_admin`, `require_cron_secret`) | exact |
| `backend/app/core/config.py` | config (reuse) | config/transform | `backend/app/core/config.py` (`SOCIAL_MAX_ATTEMPTS`, `social_retry_delays_list`, `CRON_SECRET`) | exact |
| `frontend/lib/api.ts` | API client/types | request-response (fetch) + data transform | `frontend/lib/api.ts` (admin/meta/social draft functions) | exact |
| `frontend/app/admin/review/ReviewQueue.tsx` | UI component/page client logic | request-response state (fetch/mutate/toast/optimistic) | `frontend/app/admin/review/ReviewQueue.tsx` | exact |
| `frontend/app/admin/review/EditJobDialog.tsx` | UI component (dialog/form/state) | request-response + local form state | `frontend/app/admin/review/EditJobDialog.tsx` (social draft section/loading/errors/actions) | exact |
| `frontend/components/admin/ReviewRow.tsx` | UI component (row/card) | render/presentational + action callbacks | `frontend/components/admin/ReviewRow.tsx` | exact |
| `frontend/app/admin/social-posts/page.tsx` | UI page (new, server/client composition) | request-response/list view | `frontend/app/admin/integracoes/page.tsx` + `frontend/app/admin/review/page.tsx` admin page patterns | role-match |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` (or similar, discretionary name) | UI client component (new) | request-response (list/retry/refresh) | `frontend/app/admin/integracoes/IntegrationsClient.tsx` (status/alerts/actions/loading) | role-match |
| `backend/tests/test_facebook_publisher.py` | test (new) | unit/integration (mock outbound HTTP) | `backend/tests/test_social_publisher.py` + `backend/tests/test_admin_expire.py`/httpx mock patterns | role-match |
| `backend/tests/test_social_publish_pipeline.py` | test (new) | integration (DB + pipeline orchestration) | `backend/tests/test_admin_social_posts.py` + `backend/tests/conftest.py` fixtures | role-match |
| `backend/tests/test_social_retry_policy.py` | test (new) | unit/integration (time/backoff/classification) | `backend/tests/test_social_publisher.py` (unit) + DB-backed social tests | role-match |
| `backend/tests/test_social_worker_claim.py` | test (new) | integration/concurrency-oriented DB | `backend/tests/test_admin_expire.py` (protected endpoint) + social DB fixtures | role-match |
| `backend/tests/test_social_idempotency.py` | test (new) | integration/concurrency/idempotency | `backend/tests/test_admin_social_posts.py` + claim/idempotency scenarios | role-match |
| `backend/tests/test_admin_social_status_api.py` / `test_admin_social_retry_api.py` (or combined per implementation) | test (new) | integration/API (admin auth, safe payloads) | `backend/tests/test_admin_social_posts.py`, `backend/tests/test_admin_expire.py` | role-match |

> **No analog found (new capability area, use RESEARCH.md patterns):** shared claim+publish pipeline service coordinating DB claim, Graph call, retry/idempotency, and logging as a single reusable unit (`publish_pipeline.py` / worker service). Closest references are scheduler/job-entry patterns and existing best-effort approve orchestration, but not a queue worker implementation.

## Pattern Assignments

### `backend/app/api/v1/admin.py` (route/controller, request-response + async dispatch trigger)

**Analog:** `backend/app/api/v1/admin.py` (existing)

**Imports pattern** (lines 1-36):
```python
from fastapi import APIRouter, Depends, HTTPException, Query
import uuid
from typing import Literal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.crud.jobs import (
    approve_job,
    delete_expired_jobs,
    delete_job,
    get_job,
    list_by_status,
    update_job,
)
from app.crud.social_posts import get_by_job_provider, mark_scheduled, upsert_draft
from app.deps import get_session, require_admin, require_cron_secret
from app.models.job import JobStatus
from app.models.social_post import SocialPostStatus
from app.schemas.job import JobAdmin, JobAdminListResponse, JobApproveResponse, JobUpdate
from app.schemas.social_posts import (
    SocialApproveOutcome,
    SocialPostDraftRequest,
    SocialPostDraftResponse,
)
```

**Auth/guard patterns** (lines 41-49, 58-66, 422-446):
```python
@router.get("/me")
async def me(claims: dict = Depends(require_admin)) -> dict:
    """Return the decoded admin claims behind a valid Bearer token (ADMN-03)."""
    return {
        "sub": claims["sub"],
        "role": claims["role"],
        "iat": claims.get("iat"),
        "exp": claims.get("exp"),
    }

@router.get("/jobs", response_model=JobAdminListResponse)
async def list_jobs(
    status: str = Query("pending"),
    city: str | None = Query(None, max_length=40),
    page: int = Query(1, ge=1, le=10_000),
    limit: int = Query(24, ge=1, le=100),
    sort: Literal["recentes", "antigas"] = Query("recentes"),
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdminListResponse: ...

@router.post("/expire")
async def expire_jobs(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_cron_secret),
) -> dict:
    """Hard delete every expired job...
    Rate-limited per resolved IP (10/minute, IN-05) at the cron dependency (``require_cron_secret``) ...
    Idempotent: a second call with nothing expired answers ``deleted: 0``.
    """
    deleted = await delete_expired_jobs(session)
    await session.commit()
    return {"deleted": deleted, "status": "ok"}
```

**Core site-first + best-effort social orchestration pattern** (lines 121-185):
```python
@router.patch("/jobs/{job_id}/approve", response_model=JobApproveResponse)
async def approve(..., session: AsyncSession = Depends(get_session), claims: dict = Depends(require_admin),) -> JobApproveResponse:
    ...
    # Site-first: sucesso da vaga independe do registro social.
    await approve_job(session, job)
    await session.commit()
    await session.refresh(job)

    social_outcome = SocialApproveOutcome(status="skipped", code="no_draft", message="Nenhum rascunho social salvo")
    try:
        draft = await get_by_job_provider(session, job_id, provider="facebook")
        ...
        elif draft.status == SocialPostStatus.draft:
            final_scheduled_at = draft.scheduled_at if draft.scheduled_at is not None else now_utc()
            await mark_scheduled(session, draft, text=draft.text, scheduled_at=final_scheduled_at)
            await session.commit()
            social_outcome = SocialApproveOutcome(status="registered", code=None, message=None)
        else:
            social_outcome = SocialApproveOutcome(status="warning", code="social_registration_failed", message="Não foi possível registrar o post social agora")
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass
        social_outcome = SocialApproveOutcome(status="warning", code="social_registration_failed", message="Não foi possível registrar o post social agora")

    return JobApproveResponse(job=JobAdmin.model_validate(job), social=social_outcome)
```

**Error handling/validation pattern** (lines 76-82, 129-135, 210-223, 286-297):
```python
if status not in ("pending", "needs_review"):
    raise HTTPException(status_code=422, detail="Status inválido")
...
if job is None:
    raise HTTPException(status_code=404, detail="Vaga não encontrada")
if job.status not in (JobStatus.pending, JobStatus.needs_review):
    raise HTTPException(status_code=409, detail="Vaga não está na fila de revisão")
...
except IntegrityError as exc:
    await session.rollback()
    if "at_least_one_contact" in str(exc.orig):
        raise HTTPException(status_code=422, detail="Vaga precisa ter ao menos um contato (email ou telefone)") from exc
    raise HTTPException(status_code=422, detail="Dados inválidos para a vaga") from exc
```

**Phase 17 application:** add cron-protected worker endpoint using `require_cron_secret` (D-02) returning summary counts; add admin-protected status/list and retry endpoints using `require_admin` and safe schemas; trigger immediate non-blocking dispatch after approval commit via `BackgroundTasks`/safe task calling the same pipeline (D-01/D-03/PUB-02) without changing site-first response semantics. Keep secrets/errors safe and idempotent.

---

### `backend/app/crud/social_posts.py` (CRUD/repository, DB read/write claim/status/retry)

**Analog:** `backend/app/crud/social_posts.py` (existing)

**Imports + access pattern** (lines 1-29):
```python
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
```

**Core state mutation pattern (flush-only, caller commits)** (lines 29-78):
```python
async def upsert_draft(..., *, text: str, scheduled_at, provider: str = "facebook") -> SocialPost:
    post = await get_by_job_provider(session, job_id, provider=provider)
    if post is None:
        post = SocialPost(job_id=job_id, provider=provider, text=text, status=SocialPostStatus.draft, scheduled_at=scheduled_at)
        session.add(post)
        await session.flush()
        return post

    if post.status != SocialPostStatus.draft:
        raise ValueError("frozen")

    post.text = text
    post.scheduled_at = scheduled_at
    await session.flush()
    return post


async def mark_scheduled(session: AsyncSession, social_post: SocialPost, *, text: str, scheduled_at) -> SocialPost:
    social_post.status = SocialPostStatus.scheduled
    social_post.text = text
    social_post.scheduled_at = scheduled_at
    # limpa estado transitório/retry anterior de forma segura
    social_post.next_retry_at = None
    social_post.last_error = None
    await session.flush()
    return social_post
```

**Phase 17 application:** extend with `claim_due_social_posts` / targeted claim helpers using `select(...).with_for_update(skip_locked=True)` and `and_/or_` eligibility (`scheduled` due, `failed` with `next_retry_at` due), defensive idempotent guards (`published`/`external_post_id`), status transitions to `publishing`, and helpers for published/failed-retry/final-failed/no-op reconciliation. Preserve flush-only convention.

---

### `backend/app/crud/social_accounts.py` (CRUD/repository, DB read) — **new**

**Analog:** `backend/app/crud/social_posts.py` (CRUD style) + `backend/app/models/social_account.py` (fields/status)

**Account model/state to query** (`backend/app/models/social_account.py`, lines 12-57):
```python
class SocialAccountStatus(str, Enum):
    connected = "connected"
    needs_reconnect = "needs_reconnect"
    disconnected = "disconnected"

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    ...
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    page_id: Mapped[str] = mapped_column(String(128), nullable=False)
    page_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_access_token: Mapped[str] = mapped_column(Text, nullable=False)  # encrypted at rest
    status: Mapped[SocialAccountStatus] = mapped_column(..., server_default=text("'connected'"))
    connected_at/token_checked_at/created_at/updated_at ...
    __table_args__ = (
        Index("ix_social_accounts_provider_status", "provider", "status"),
        Index("ix_social_accounts_page_id", "page_id"),
    )
```

**Phase 17 application:** add safe lookup for active connected Facebook account (and page/token fields for backend-only publish). Never expose token; integrate with D-06 (disconnected/needs_reconnect/missing/decrypt-fail => blocked, safe pt-BR error, no auto retry).

---

### `backend/app/services/social/facebook.py` (service/provider integration, outbound HTTP)

**Analog:** `backend/app/services/social/facebook.py` (stub) + contract in `publisher.py`/`types.py`

**Current stub to replace with real implementation** (`backend/app/services/social/facebook.py`, lines 1-19):
```python
from __future__ import annotations

from .publisher import SocialPublisher
from .types import PublishFailureCategory, PublishResult, SocialPostPayload


class FacebookPublisher(SocialPublisher):
    """Stub explícito do publisher do Facebook.

    Estrutura pronta para a Fase 17; nesta fase não realiza chamadas externas/HTTP.
    """

    async def publish(self, post: SocialPostPayload | object | None = None) -> PublishResult:
        return PublishResult(
            ok=False,
            external_post_id=None,
            category=PublishFailureCategory.unknown,
            error_message="publicação Facebook não implementada na Fase 14 (stub)",
        )
```

**Contract/types to preserve/extend safely** (`backend/app/services/social/publisher.py`, lines 1-9; `types.py`, lines 1-26):
```python
# publisher.py
class SocialPublisher(Protocol):
    async def publish(self, post: SocialPostPayload) -> PublishResult: ...

# types.py
class PublishFailureCategory(str, Enum):
    transient = "transient"
    permanent = "permanent"
    unknown = "unknown"

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
```

**Phase 17 application:** implement real async `publish` calling Graph `POST /{META_GRAPH_VERSION}/{page_id}/feed` with `message`+`link` and backend-only decrypted Page token (via `httpx.AsyncClient`, explicit timeout), parse `external_post_id` (`id`) on success, classify failures (network/5xx/429 transient, auth/permission/content permanent, ambiguous timeout-after-send per D-11) into safe `PublishResult` categories/messages (no raw payloads/secrets). Keep provider seam intact.

---

### `backend/app/services/social/publish_pipeline.py` (service/worker pipeline, batch+idempotent orchestration) — **new**

**Analog:** `backend/app/core/scheduler.py` (async job entry, bounded/non-raising orchestration, inflight awareness concepts) + approve best-effort orchestration in `admin.py`

**Async scheduler/job-entry pattern** (`backend/app/core/scheduler.py`, lines 73-106, 154-176):
```python
async def _run_expiry_sweep() -> int:
    """Open a session, hard delete expired jobs, commit, and return the count."""
    async with async_session_factory() as session:
        try:
            deleted = await delete_expired_jobs(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    return deleted


async def expire_jobs_job() -> int:
    """Scheduler entry point... Never raises: a transient database failure is logged and the next daily run ... retries ..."""
    task = asyncio.current_task()
    if task is not None:
        _inflight.add(task)
    try:
        deleted = await _run_expiry_sweep()
    except Exception:
        logger.exception("expiry sweep falhou; nova tentativa no proximo ciclo")
        return 0
    finally:
        if task is not None:
            _inflight.discard(task)
    logger.info("expiry sweep removeu %s vaga(s) expirada(s)", deleted)
    return deleted
```

**Phase 17 application (RESEARCH-aligned):** single shared pipeline for cron worker, immediate post-commit dispatch, and manual retry (D-03/D-12). Responsibilities: claim eligible rows (`FOR UPDATE SKIP LOCKED`, D-04/D-09), idempotent no-op on published/`external_post_id` (D-10), resolve connected account/token safely (D-06), call `FacebookPublisher`, classify/map safe pt-BR errors (D-05/D-06/D-08/D-11), compute attempts/`next_retry_at` from `settings.SOCIAL_MAX_ATTEMPTS` and `settings.social_retry_delays_list` with final-failed on exhaustion (D-07), persist `SocialPost` + `SocialPostLog`, never auto-republish ambiguous outcomes. Expose cycle/targeted processing and summary counts.

---

### `backend/app/schemas/social_posts.py` (schema, request/response transform)

**Analog:** `backend/app/schemas/social_posts.py` (existing)

**Schema pattern** (lines 1-49):
```python
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SocialPublishMode = Literal["publish_now", "schedule"]


class SocialPostDraftResponse(BaseModel):
    """Rascunho/estado do post social para UI admin."""

    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    provider: Literal["facebook"] = "facebook"
    status: Literal["draft", "scheduled", "publishing", "published", "failed", "cancelled"]
    text: str
    publish_mode: Literal["publish_now", "schedule"] | None = None
    scheduled_at: datetime | None = None
    origin: Literal["llm", "template_fallback"]
    saved: bool
    frozen: bool
    warning: str | None = None


class SocialApproveOutcome(BaseModel):
    status: Literal["registered", "skipped", "warning"]
    code: str | None = None
    message: str | None = None
```

**Phase 17 application:** add safe status/list item schema(s) for UI-01/D-13,D-14 (pt-BR label/badge inputs, safe `last_error`, `published_url`/`external_post_id` when available, attempts/next_retry/scheduled/published timestamps, `can_retry`, `retry_block_reason`) and worker/retry response schemas (summary counts / idempotent outcome) without exposing secrets or raw provider payloads.

---

### `backend/app/models/social_post.py` & `backend/app/models/social_post_log.py` (model/ORM, DB persistence) — **reuse/anchor**

**Operational fields/indexes** (`backend/app/models/social_post.py`, lines 13-78):
```python
class SocialPostStatus(str, Enum):
    draft = "draft"; scheduled = "scheduled"; publishing = "publishing"
    published = "published"; failed = "failed"; cancelled = "cancelled"

class SocialPost(Base):
    __tablename__ = "social_posts"
    ...
    status: Mapped[SocialPostStatus] = mapped_column(..., server_default=sql_text("'draft'"))
    scheduled_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sql_text("0"))
    next_retry_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    ...
    __table_args__ = (
        UniqueConstraint("job_id", "provider", name="uq_social_posts_job_provider"),
        Index("ix_social_posts_status", "status"),
        Index("ix_social_posts_scheduled_at", "scheduled_at"),
        Index("ix_social_posts_next_retry_at", "next_retry_at"),
        Index("ix_social_posts_job_id", "job_id"),
    )
```

**Audit/log model** (`backend/app/models/social_post_log.py`, lines 11-43):
```python
class SocialPostLog(Base):
    __tablename__ = "social_post_logs"
    social_post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
```

**Phase 17 application:** drive claim/retry/idempotency using these fields and constraints (no schema changes expected/assumed unless required); persist sanitized attempt summaries only.

---

### `frontend/lib/api.ts` (API client/types, request-response)

**Analog:** `frontend/lib/api.ts` (existing)

**Imports/base/error helpers** (lines 1-164):
```ts
import type { CitySlug } from "./cities";

const API = resolveApiBase();

export class ApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readError(res: Response): Promise<string> { ... }
```

**Admin fetch/auth and social draft patterns** (lines 452-518, 550-674):
```ts
export async function approveJob(token: string, id: string): Promise<JobApproveResponse> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${id}/approve`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as JobApproveResponse;
}

export async function getSocialDraft(token: string, jobId: string): Promise<SocialPostDraft | null> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-post`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as SocialPostDraft;
}

export async function getMetaIntegrationStatus(token: string): Promise<MetaIntegrationStatus> {
  const res = await fetch(`${API}/api/v1/admin/integrations/meta/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as MetaIntegrationStatus;
}
```

**Existing social draft types** (lines 409-450):
```ts
export interface SocialPostDraft {
  job_id: string;
  provider: "facebook";
  status: "draft" | "scheduled" | "publishing" | "published" | "failed" | "cancelled";
  text: string;
  publish_mode: SocialPublishMode | null;
  scheduled_at: string | null;
  origin: SocialDraftOrigin | null;
  saved: boolean;
  frozen: boolean;
  warning: string | null;
}
```

**Phase 17 application:** extend types and add functions for social status/list view and manual retry endpoints (admin Bearer auth, `ApiError`/`readError` handling), exposing safe fields needed by UI-01/UI-02 (`status_label`/state, safe `last_error`, `published_url`/external id, `can_retry`, `retry_block_reason`, timestamps). Keep 404/nullable handling conventions where appropriate.

---

### `frontend/app/admin/review/ReviewQueue.tsx` (UI component/client state, request-response)

**Analog:** `frontend/app/admin/review/ReviewQueue.tsx` (existing)

**Client/data-fetch/toast/auth-error pattern** (lines 1-38, 74-119):
```tsx
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAdminGuard } from "@/components/admin/AdminGuard";
import { useToast } from "@/components/admin/ToastProvider";
import { ApiError, approveJob, deleteJob, listAdminJobs, type JobAdmin } from "@/lib/api";
import { TOKEN_KEY } from "@/lib/auth";

/** A 401 means the JWT expired: end the session instead of looping on retry. */
function handleAuthError(err: unknown): boolean {
  if (err instanceof ApiError && err.status === 401) {
    try { sessionStorage.removeItem(TOKEN_KEY); } catch {}
    window.location.replace("/admin/paste");
    return true;
  }
  return false;
}
...
  const token = useAdminGuard();
  const { toast } = useToast();
  const [items, setItems] = useState<JobAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const reload = useCallback(() => setRefreshKey((key) => key + 1), []);
```

**Mutation/optimistic + guarded in-flight pattern** (lines 79, 161-210, 212-253):
```tsx
  // Serializes mutations: a second approve/delete while one is in flight would apply an optimistic update on top of a snapshot that is already stale.
  const mutatingRef = useRef(false);
...
  const handleApprove = async (job: JobAdmin) => {
    if (!token) return;
    if (mutatingRef.current) { toast("Aguarde a operação anterior.", "error"); return; }
    mutatingRef.current = true;
    const snapshot = items; const previousTotal = total; const previousCounts = counts;
    ...
    try {
      const result = await approveJob(token, job.id);
      const socialStatus = result.social?.status;
      if (socialStatus === "skipped") toast("Vaga publicada no site. Nenhum rascunho social salvo — publicação no Facebook não foi registrada.", "error");
      else if (socialStatus === "warning") toast("Vaga publicada no site. Não foi possível registrar o post social agora.", "error");
      else toast("Vaga publicada no site. Post social registrado para envio.", "success");
      ...
    } catch (err) {
      setItems(snapshot); setTotal(previousTotal); setCounts(previousCounts);
      if (handleAuthError(err)) return;
      toast(`Erro: ${err instanceof Error ? err.message : "Falha ao aprovar"}`, "error");
    } finally {
      mutatingRef.current = false;
    }
  };
```

**Phase 17 application:** extend row/dialog props/data flow to surface compact social status per job (and refresh) per D-13/D-14; if row-level retry is added, reuse `mutatingRef`/single-flight, toast, reload and backend idempotent outcomes. Preserve 401 handling and existing approve semantics.

---

### `frontend/app/admin/review/EditJobDialog.tsx` (UI dialog/component, request-response + form state)

**Analog:** `frontend/app/admin/review/EditJobDialog.tsx` (existing)

**Social draft loading/state/error/action pattern** (lines 230-324, 356-365, 472-557):
```tsx
  const [socialDraft, setSocialDraft] = useState<SocialPostDraft | null>(null);
  const [socialAction, setSocialAction] = useState<SocialAction>(null);
  const [socialLoadError, setSocialLoadError] = useState<string | null>(null);
  const [socialActionError, setSocialActionError] = useState<string | null>(null);
...
  useEffect(() => {
    if (!open || !job || !token) return;
    let cancelled = false;
    setSocialAction("load");
    setSocialLoadError(null);
    getSocialDraft(token, job.id)
      .then((draft) => { if (cancelled) return; applyDraft(draft); })
      .catch((err) => {
        if (cancelled) return;
        const message = err instanceof ApiError ? err.message : "Não foi possível carregar o rascunho social.";
        setSocialLoadError(message);
      })
      .finally(() => { if (!cancelled) setSocialAction(null); });
    return () => { cancelled = true; };
  }, [open, job?.id, token]);
...
  const frozen = Boolean(socialDraft?.frozen || (socialDraft && socialDraft.status !== "draft"));
  const busy = socialAction !== null;
...
  const handleGenerate = async (isRegenerate: boolean) => {
    if (!token || !job || frozen || busy) return;
    ...
    setSocialAction("generate"); setSocialActionError(null); setSocialFallbackWarning(false);
    try { const draft = await generateSocialDraft(token, job.id, buildSocialPayload()); applyDraft(draft); ... }
    catch (err) { ... setSocialActionError(message); if (!/SITE_PUBLIC_URL|Link público indisponível/i.test(message)) toast(`Erro: ${message}`, "error"); }
    finally { setSocialAction(null); }
  };
```

**Section rendering / status chips / disabled controls pattern** (lines 729-967 excerpts):
```tsx
<section className="mt-6 border-t border-line pt-6">
  <h3 className="text-[20px] font-semibold leading-tight text-fg">Post para Facebook</h3>
  {socialAction === "load" ? (<p className="mt-3 text-[14px] text-fg-muted">Carregando rascunho...</p>) : null}
  {socialLoadError ? (<p role="alert" className="mt-3 text-[14px] text-danger-soft">{socialLoadError}</p>) : null}
  ...
  <div className="flex flex-wrap gap-2">
    {originChip ? <span className="rounded-full border border-line bg-canvas px-3 py-1 text-[14px] text-fg-muted">{originChip}</span> : null}
    {frozen ? <span className="rounded-full border border-line bg-canvas px-3 py-1 text-[14px] text-fg-muted">Texto bloqueado após aprovação</span> : null}
  </div>
  ...
  <button ... disabled={controlsDisabled || !token} className="min-h-11 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white ... disabled:opacity-50">...</button>
</section>
```

**Phase 17 application:** add `Status da publicação no Facebook` block (D-13/UI-SPEC) showing badge/helper/safe error, scheduled/published context, `Ver post no Facebook` external link when available, and `Tentar novamente` only when eligible (D-15) with single-flight loading/idempotent feedback. Do not alter draft immutability semantics (Phase 16/PUB-08).

---

### `frontend/components/admin/ReviewRow.tsx` (UI component, presentational + actions)

**Analog:** `frontend/components/admin/ReviewRow.tsx` (existing)

**Card/action/badge pattern** (lines 30-155):
```tsx
const STATUS_LABELS: Record<JobAdmin["status"], string> = {
  pending: "Pendente", published: "Publicada", needs_review: "Necessita revisão", invalid: "Inválida",
};

export function ReviewRow({ job, onApprove, onEdit, onDelete, loading = false }: ReviewRowProps) {
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const busy = loading || pendingAction !== null;
  ...
  return (
    <article className={`flex h-full flex-col gap-3 rounded-[12px] border border-line bg-surface p-4 ... ${busy ? "pointer-events-none opacity-60" : ""}`} aria-busy={busy}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h2 className="min-w-0 text-[20px] font-semibold leading-tight [overflow-wrap:anywhere] [text-wrap:balance]">{job.title}</h2>
        <span className="shrink-0 rounded-full bg-[rgba(139,92,246,0.12)] px-3 py-1 text-[14px] text-accent-soft">{statusLabel}</span>
      </div>
      ...
      <div className="mt-auto flex flex-wrap gap-2 pt-1">
        <button ... className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white ...">
          {pendingAction === "approve" ? <Spinner size={16} /> : <Check size={16} />}
          {pendingAction === "approve" ? "Aprovando..." : "Aprovar"}
        </button>
        <button ... className={secondaryButton}><Pencil size={16} />Editar</button>
        <button ... className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-danger px-4 text-sm text-danger ..."><Trash size={16} />Excluir</button>
      </div>
    </article>
  );
}
```

**Phase 17 application:** add compact social status badge/hint per D-13/D-14 without relying on color alone; keep 44px actions and busy/disabled semantics if row-level retry is included (prefer dialog/list for action unless trivial and idempotent).

---

### `frontend/app/admin/integracoes/IntegrationsClient.tsx` (UI client, status/actions/alerts — analog for new social-posts view)

**Analog:** `frontend/app/admin/integracoes/IntegrationsClient.tsx` (existing)

**Client state, fetch, banner/error/toast, action loading pattern** (lines 46-74, 111-147, 169-188, 294-321):
```tsx
export function IntegrationsClient() {
  const token = useAdminGuard();
  const { toast } = useToast();
  const [status, setStatus] = useState<MetaIntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<"start" | "verify" | "confirm" | "disconnect" | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [banner, setBanner] = useState<{ kind: BannerKind; text: string } | null>(null);
...
  const refresh = useCallback(async (opts?: { keepLoading?: boolean }) => {
    if (!token) return;
    if (!opts?.keepLoading) setLoading(true);
    setPageError(null);
    try {
      const nextStatus = await getMetaIntegrationStatus(token);
      setStatus(nextStatus);
      ...
    } catch (err) {
      setPageError(err instanceof ApiError ? (err.message || "Não foi possível concluir a ação...") : "Não foi possível concluir a ação...");
    } finally {
      setLoading(false);
    }
  }, [token, result, pendingNonce]);

  useEffect(() => { if (!token) return; void refresh(); }, [token, refresh]);
...
  return (
    <div className="mt-6 space-y-4">
      {banner && (<div className={`rounded-[12px] border px-4 py-3 text-sm ${bannerClass}`}>{banner.text}</div>)}
      {pageError && (<div className="rounded-[12px] border border-danger bg-[rgba(248,113,113,0.12)] px-4 py-3 text-sm text-danger-soft">{pageError}</div>)}
      <section className="rounded-[12px] border border-line bg-surface p-6">
        {loading ? (<p className="text-fg-muted">Carregando integrações...</p>) : (/* state-driven UI */)}
      </section>
    </div>
  );
}
```

**Phase 17 application (for `admin/social-posts` view):** copy this pattern for list loading/empty/error states, banners/toasts, per-item/per-action loading, safe pt-BR messages, and action buttons/links (including `Abrir Integrações` to `/admin/integracoes` and `Ir para a fila de revisão`) per UI-SPEC/D-13.

---

### `backend/app/deps.py` & `backend/app/core/config.py` (guards/config — reuse)

**Cron/admin guards** (`backend/app/deps.py`, lines 23-96):
```python
bearer_scheme = HTTPBearer(auto_error=False)

async def require_admin(creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
    if creds is None or creds.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        claims = decode_access_token(creds.credentials)
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc
    if claims.get("sub") != "admin" or claims.get("role") != "admin":
        raise _unauthorized()
    return claims

@limiter.limit("10/minute")
async def require_cron_secret(request: Request, x_cron_secret: str | None = Header(default=None, alias="X-Cron-Secret")) -> None:
    settings = get_settings()
    expected = settings.CRON_SECRET.strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Expiração manual não configurada")
    provided = (x_cron_secret or "").strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise _cron_unauthorized()
```

**Social retry/config** (`backend/app/core/config.py`, lines 69-87, 105-149):
```python
CRON_SECRET: str = ""
SOCIAL_MAX_ATTEMPTS: int = 5
SOCIAL_RETRY_DELAYS: str = "300,900,3600,10800,21600"
...
@staticmethod
def _parse_social_retry_delays(raw: str) -> list[int]: ... # CSV ints > 0
@property
def social_retry_delays_list(self) -> list[int]:
    return self._parse_social_retry_delays(self.SOCIAL_RETRY_DELAYS)
```

**Phase 17 application:** D-02 requires worker endpoint protected by `require_cron_secret`/`CRON_SECRET` (same pattern as `/admin/expire`), not `SOCIAL_WORKER_SECRET`. Retry policy must use `SOCIAL_MAX_ATTEMPTS` and `social_retry_delays_list`.

## Shared Patterns

### 1) Admin/Cron protection and endpoint style
**Source:** `backend/app/deps.py` lines 23-96, `backend/app/api/v1/admin.py` lines 41-66, 422-446
**Apply to:** all Phase 17 admin status/retry endpoints (`require_admin`, `get_session`, typed responses, 401/404/409/422 semantics) and worker cron endpoint (`require_cron_secret`, idempotent JSON summary).
```python
async def handler(..., session: AsyncSession = Depends(get_session), claims: dict = Depends(require_admin)): ...
@router.post("/social/worker")  # example path discretionary
async def social_worker(session: AsyncSession = Depends(get_session), _: None = Depends(require_cron_secret)) -> dict:
    # process due batch via shared pipeline
    return {"status": "ok", "claimed": n, "processed": n, "published": n, "retried": n, "failed_final": n, "skipped": n}
```

### 2) Site-first, failure-isolated social side effects (no regressions to approve/publish-site)
**Source:** `backend/app/api/v1/admin.py` lines 121-185
**Apply to:** approve-triggered immediate dispatch and any social status/retry actions (never block/break job publish flow; catch/log safe; cron fallback).
```python
# commit site change first
await approve_job(session, job)
await session.commit()
await session.refresh(job)
# best-effort / non-blocking social handling after commit
try: ...
except Exception:
    try: await session.rollback()
    except Exception: pass
    # safe warning outcome, site already published
```

### 3) CRUD/session transaction discipline (flush in CRUD, commit in caller/transaction boundary)
**Source:** `backend/app/crud/social_posts.py` lines 1-78
**Apply to:** new claim/status/retry/log CRUD helpers and pipeline steps that require explicit transactional boundaries for `FOR UPDATE SKIP LOCKED`.
```python
# CRUD mutates and flushes; caller commits/rolls back
post.status = ...
await session.flush()
return post
```

### 4) Safe error mapping and no-secrets policy (pt-BR, summarized)
**Source:** `backend/app/core/config.py` (secret handling/validation posture), `backend/app/models/social_post_log.py` (response_summary/error fields), CONTEXT/RESEARCH D-05..D-08,D-11
**Apply to:** `FacebookPublisher` results, pipeline persistence (`last_error`, logs), and admin/API/UI payloads.
```python
# Persist/UI only safe summaries (no tokens, no raw Graph payloads)
post.last_error = "Falha temporária ao publicar. Uma nova tentativa será feita automaticamente."
# or reconnect/ambiguous/final messages per mapping; log sanitized summaries only
```

### 5) Frontend admin API + UI resilience (ApiError/401, loading, single-flight, toasts)
**Source:** `frontend/lib/api.ts` lines 132-164,452-518; `frontend/app/admin/review/ReviewQueue.tsx` lines 24-38,79,161-210,372-385; `frontend/app/admin/integracoes/IntegrationsClient.tsx` lines 111-147,294-321
**Apply to:** social status fetch/list, retry action, and new `admin/social-posts` view.
```ts
if (err instanceof ApiError && err.status === 401) { sessionStorage.removeItem(TOKEN_KEY); window.location.replace("/admin/paste"); return true; }
if (mutatingRef.current) { toast("Aguarde a operação anterior.", "error"); return; }
mutatingRef.current = true;
try { /* call */ toast("Nova tentativa iniciada.", "success"); reload(); }
catch (err) { /* restore if optimistic; safe toast */ }
finally { mutatingRef.current = false; }
```

### 6) Test harness and auth/cron test style
**Source:** `backend/tests/conftest.py` lines 1-301, `backend/tests/test_admin_expire.py` lines 1-207, `backend/tests/test_admin_social_posts.py` lines 1-391
**Apply to:** all Wave 0 Phase 17 backend tests (DB isolation/fixtures, admin login helper, cron `X-Cron-Secret` monkeypatching, monkeypatch generation/pipeline seams, safe 503/401/idempotent assertions).
```python
@pytest.fixture
def cron_secret(monkeypatch) -> str:
    monkeypatch.setattr(get_settings(), "CRON_SECRET", CRON_SECRET)
    return CRON_SECRET

async def _login(client, admin_password="test-password"):
    resp = await client.post("/api/v1/auth/login", json={"password": admin_password, "cf_token": VALID_CF_TOKEN})
    assert resp.status_code == 200
    return resp.json()["access_token"]
# DB-backed tests use db_session fixtures; generation/Graph calls mocked
```

## No Analog Found

Files with no close in-repo match (planner should use RESEARCH.md + CONTEXT.md patterns and locked decisions as primary guide):

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `backend/app/services/social/publish_pipeline.py` (or equivalent worker service module) | service/pipeline (queue worker) | claim (DB lock) -> external publish -> state/log persistence | No existing queue/worker pipeline with `FOR UPDATE SKIP LOCKED`, retry/backoff/idempotency, and Graph publish orchestration in codebase; nearest are scheduler entrypoints and best-effort approve hooks. |

## Metadata

**Analog search scope:** `.planning/phases/17-*`, `.planning/{STATE,ROADMAP,REQUIREMENTS}.md`, `backend/app/{api/v1,crud,services/social,models,schemas,deps.py,core}`, `frontend/{lib/api.ts,app/admin,components/admin}`, `backend/tests`
**Files scanned:** ~25 (targeted reads of all referenced core analogs + existing social/admin/cron tests)
**Pattern extraction date:** 2026-11-16
