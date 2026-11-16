# Phase 16: Geração, Revisão e Aprovação do Post Social - Pattern Map

**Mapped:** 2026-11-15
**Files analyzed:** 11
**Analogs found:** 11 / 11

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/crud/social_posts.py` | crud/repository | CRUD (upsert/read/transition by job+provider) | `backend/app/crud/jobs.py` | exact |
| `backend/app/schemas/social_posts.py` | schema (Pydantic request/response) | request-response/validation | `backend/app/schemas/social_integrations.py`, `backend/app/schemas/job.py` | exact |
| `backend/app/services/social/post_generation.py` | service (domain logic) | transform/generate (LLM+fallback+policy+schedule helpers) | `backend/app/services/extraction/client.py` (Groq seam) + `backend/app/services/social/meta_oauth.py` patterns | role-match |
| `backend/app/api/v1/admin.py` | route/controller (FastAPI) | request-response (admin-protected) | `backend/app/api/v1/admin.py` (self), `backend/app/api/v1/integrations.py` | exact |
| `backend/app/schemas/job.py` | schema (Pydantic) | request-response (approve contract evolution) | `backend/app/schemas/job.py` (self) | exact |
| `backend/app/core/config.py` | config (Settings/env validation) | config/load-validate | `backend/app/core/config.py` (self) | exact |
| `backend/.env.example` | config/docs | config template | `backend/.env.example` (self) | exact |
| `backend/app/services/social/__init__.py` | module exports | wiring | `backend/app/services/social/__init__.py`, `backend/app/crud/__init__.py` | exact |
| `frontend/lib/api.ts` | API client/types | request-response (fetch + typed contracts) | `frontend/lib/api.ts` Meta integration section (self) | exact |
| `frontend/app/admin/review/EditJobDialog.tsx` | UI component (client) | form/state + async actions | `frontend/app/admin/review/EditJobDialog.tsx` (self), `frontend/app/admin/integracoes/IntegrationsClient.tsx` | exact |
| `frontend/app/admin/review/ReviewQueue.tsx` | UI component (client, list/mutations) | request-response + optimistic UI | `frontend/app/admin/review/ReviewQueue.tsx` (self) | exact |

## Pattern Assignments

### `backend/app/crud/social_posts.py` (crud/repository, CRUD)

**Analog:** `backend/app/crud/jobs.py`

**Imports/module style** (lines 1-16):
```python
"""CRUD for jobs: public read queries (D-17) and extraction writes (D-03)."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus

PUBLISHED_TTL = timedelta(days=14)

__all__ = ["list_published", "get_published", "bulk_create_pending", "list_by_status", "get_job", "approve_job", "update_job", "delete_job", "delete_expired_jobs"]
```

**Core CRUD/query pattern** (get + filters, lines 130-135, 92-128 style):
```python
async def get_job(session: AsyncSession, job_id: uuid.UUID) -> Job | None:
    """Return a job by id, or ``None`` (no status filter — admin can edit any)."""
    stmt = select(Job).where(Job.id == job_id)
    return await session.scalar(stmt)
```

**Mutation/transaction boundary pattern** (flush only, caller commits) (lines 137-148, 163-167):
```python
async def approve_job(session: AsyncSession, job: Job) -> Job:
    """Publish a job and restart its 14-day TTL (caller owns transaction/commit)."""
    job.status = JobStatus.published
    job.expires_at = datetime.now(timezone.utc) + PUBLISHED_TTL
    await session.flush()
    return job


async def delete_job(session: AsyncSession, job: Job) -> None:
    """Delete job from session (caller owns transaction/commit)."""
    await session.delete(job)
```

**Apply to:** Implement `get_draft/get_by_job_provider`, `upsert_draft`, and `register/schedule_approved_draft`-style helpers using `select(SocialPost).where(job_id==..., provider=="facebook")` (model in `backend/app/models/social_post.py` lines 72-78 shows uniqueness/indexes). Keep `await session.flush()` in CRUD; let route own `commit`/best-effort separation (D-09). Enforce draft-only mutability checks consistent with D-02/D-12.

**Related model excerpt** (`backend/app/models/social_post.py`, lines 13-78):
```python
class SocialPostStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"
    cancelled = "cancelled"

class SocialPost(Base):
    __tablename__ = "social_posts"
    ...
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SocialPostStatus] = mapped_column(SAEnum(SocialPostStatus, name="social_post_status", native_enum=True), nullable=False, server_default=sql_text("'draft'"))
    scheduled_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    ...
    __table_args__ = (UniqueConstraint("job_id", "provider", name="uq_social_posts_job_provider"), ...)
```

---

### `backend/app/schemas/social_posts.py` (schema, request-response)

**Analogs:** `backend/app/schemas/social_integrations.py`, `backend/app/schemas/job.py`

**Imports and schema style** (`backend/app/schemas/social_integrations.py`, lines 1-47):
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

**ORM/from_attributes and admin response envelope style** (`backend/app/schemas/job.py`, lines 1-47, 105-132, 210-216):
```python
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.models.job import JobStatus

class JobAdmin(BaseModel):
    """Admin-facing job schema with contact + source_snippet exposure."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    ...
    status: JobStatus
    contact_email: str | None = None
    contact_phone: str | None = None
    source_snippet: str | None = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

class JobAdminListResponse(BaseModel):
    """Offset-paginated envelope for admin job list (D-14)."""
    items: list[JobAdmin]
    page: int
    limit: int
    total: int
```

**Apply to:** Define request/response models for draft get/generate/save and approve social outcome (e.g. draft payload with `text`, `mode` publish_now/schedule, BRT schedule fields or normalized `scheduled_at`, origin/status flags; approve envelope `{ job, social }` per RESEARCH A2/OQ1). Keep literal enums/strict fields, admin-only semantics, and avoid leaking secrets. Use `ConfigDict(from_attributes=True)` for ORM-backed responses where useful.

---

### `backend/app/services/social/post_generation.py` (service, transform/generate)

**Analogs:** `backend/app/services/extraction/client.py` (Groq config/call/error seam), `backend/app/services/social/types.py`/`publisher.py` (social domain types), `backend/app/core/config.py` (`settings` usage)

**Groq lazy client and config-driven call seam** (`backend/app/services/extraction/client.py`, lines 28-29, 155-156, 198-209, 212-241):
```python
from __future__ import annotations
...
# The SDK is imported lazily so tests inject a fake ``client`` and never need a
# real ``GROQ_API_KEY`` (or the ``AsyncGroq`` constructor) at all.
...
def model_chain(settings: Any) -> list[str]:
    """``[GROQ_MODEL, GROQ_MODEL_FALLBACK]`` deduplicated, never hardcoded."""
    chain: list[str] = []
    for name in (settings.GROQ_MODEL, settings.GROQ_MODEL_FALLBACK):
        if name and name not in chain:
            chain.append(name)
    return chain

def _build_real_client(settings: Any) -> Any:
    """Lazily construct ``AsyncGroq`` — tests inject ``client`` and never hit this."""
    if not str(getattr(settings, "GROQ_API_KEY", "") or "").strip():
        raise ExtractionAPIError(
            "GROQ_API_KEY não configurada — configure a variável no "
            "backend/.env (console.groq.com/keys)"
        )
    from groq import AsyncGroq
    return AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=settings.GROQ_TIMEOUT_SECONDS)

async def _create_with_retries(...):
    ...
    return await client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=strict_response_format(),
        temperature=0,
        timeout=settings.GROQ_TIMEOUT_SECONDS,
    )
```

**Service/exception/result shape hints** (`backend/app/services/extraction/client.py`, lines 66-82):
```python
class ExtractionAPIError(Exception):
    """Any Groq/extraction API failure surfaced to the admin in pt-BR."""
    def __init__(self, detail: str, *, model: str | None = None):
        super().__init__(detail)
        self.detail = detail
        self.model = model

@dataclass
class RawExtraction:
    rows: list[ExtractedJobRaw]
    model_used: str
    finish_reasons: list[str] = field(default_factory=list)
```

**Apply to:** Create dedicated social generation service/module (not reusing extraction schema/prompt pipeline): reuse settings/model/timeout/client seam ideas, but with plain-text post prompt/output, deterministic template fallback (D-03/POST-02), central policy enforcement (no company/contact per D-15, configurable flag D-16), public link builder `f"{SITE_PUBLIC_URL.rstrip('/')}/?vaga={job_id}"` (D-13) with actionable error if missing/invalid (D-17), and BRT→aware datetime conversion helpers (`zoneinfo.ZoneInfo("America/Sao_Paulo")`). Do not call LLM from list endpoints.

---

### `backend/app/api/v1/admin.py` (route/controller, request-response)

**Analogs:** `backend/app/api/v1/admin.py` (self), `backend/app/api/v1/integrations.py`

**Router/dependency/error-handling pattern** (`backend/app/api/v1/admin.py`, lines 1-22, 40-78, 104-127):
```python
from fastapi import APIRouter, Depends, HTTPException, Query
import uuid
from typing import Literal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.jobs import approve_job, delete_job, get_job, list_by_status, update_job
from app.deps import get_session, require_admin, require_cron_secret
from app.models.job import JobStatus
from app.schemas.job import JobAdmin, JobAdminListResponse, JobUpdate
from app.services.cities import resolve_city

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/jobs", response_model=JobAdminListResponse)
async def list_jobs(..., session: AsyncSession = Depends(get_session), claims: dict = Depends(require_admin)) -> JobAdminListResponse:
    ...
    if status not in ("pending", "needs_review"):
        raise HTTPException(status_code=422, detail="Status inválido")
    ...
    return JobAdminListResponse(items=[JobAdmin.model_validate(j) for j in items], page=page, limit=limit, total=total)

@router.patch("/jobs/{job_id}/approve", response_model=JobAdmin)
async def approve(..., session: AsyncSession = Depends(get_session), claims: dict = Depends(require_admin)) -> JobAdmin:
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    if job.status not in (JobStatus.pending, JobStatus.needs_review):
        raise HTTPException(status_code=409, detail="Vaga não está na fila de revisão")
    await approve_job(session, job)
    await session.commit()
    await session.refresh(job)
    return JobAdmin.model_validate(job)
```

**Annotated deps and commit/rollback pattern** (`backend/app/api/v1/integrations.py`, lines 1-39, 136-151):
```python
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings, get_settings
from app.deps import get_session, require_admin

router = APIRouter(prefix="/admin/integrations", tags=["admin-integrations"])

AdminClaims = Annotated[dict, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]

@router.post("/meta/verify", response_model=MetaActionResponse)
async def verify_meta_connection(claims: Annotated[dict, Depends(require_admin)], session: DbSession, settings: AppSettings) -> MetaActionResponse:
    _ = claims
    try:
        response = await verify_current_connection(session, settings)
        await session.commit()
        return response
    except MetaOAuthConfigError as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail=MISSING_META_CONFIG_DETAIL) from exc
```

**Apply to:** Add admin-protected draft endpoints (recommended GET/POST generate/PUT save per RESEARCH OQ2) under `/admin/jobs/{job_id}/social-post...` and evolve `PATCH /admin/jobs/{job_id}/approve` to return `{job, social}` outcome (RESEARCH A2). Critical: commit job publish first (`approve_job`+commit+refresh) then do separate best-effort social registration with isolated try/except and no rollback of published job (D-09/D-11). Validate UUID/path, use pt-BR `HTTPException` details, and keep `require_admin` on all new mutating/read endpoints.

---

### `backend/app/schemas/job.py` (schema, request-response)

**Analog:** `backend/app/schemas/job.py` (self)

**Current response/model style** (lines 105-132, 210-216):
```python
class JobAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    ...
    status: JobStatus
    source_snippet: str | None = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

class JobAdminListResponse(BaseModel):
    items: list[JobAdmin]
    page: int
    limit: int
    total: int
```

**Apply to:** Preserve existing `JobAdmin` fields; if approve contract becomes envelope, add/adjust response schema(s) (e.g. `JobApproveResponse` with `job: JobAdmin` and `social: ...`) rather than breaking `JobAdmin` shape used elsewhere. Keep admin-only contact exposure unchanged.

---

### `backend/app/core/config.py` (config, load/validate)

**Analog:** `backend/app/core/config.py` (self)

**Settings fields and model validators** (lines 22-148, 220-246):
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    ...
    # --- Integração Social / Meta (Phase 14 - Fundação) ---
    META_APP_ID: str = ""
    META_GRAPH_VERSION: str = "v21.0"
    META_OAUTH_REDIRECT_URI: str = ""
    SOCIAL_TOKEN_ENCRYPTION_KEY: str = ""
    SOCIAL_WORKER_SECRET: str = ""
    SOCIAL_MAX_ATTEMPTS: int = 5
    SOCIAL_RETRY_DELAYS: str = "300,900,3600,10800,21600"
    SITE_PUBLIC_URL: str = ""

    @model_validator(mode="after")
    def _validate_social_foundation(self) -> "Settings":
        site_url = self.SITE_PUBLIC_URL.strip()
        if site_url:
            parsed = urlparse(site_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("SITE_PUBLIC_URL deve ser uma URL http/https válida")
        ...
        return self

    @property
    def social_retry_delays_list(self) -> list[int]:
        return self._parse_social_retry_delays(self.SOCIAL_RETRY_DELAYS)

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Apply to:** Add backend policy flag env for D-16 (default disabled/no contact), documented name at discretion (e.g. boolean `SOCIAL_POST_INCLUDE_CONTACT` style) with parsing/validation consistent with existing patterns. Reuse `SITE_PUBLIC_URL` validation; generation service should treat missing/invalid site URL as actionable draft-generation error (D-17) even if config allows empty in some envs.

---

### `backend/.env.example` (config/docs)

**Analog:** `backend/.env.example` (self)

**Section/comment style** (lines 34-48):
```env
# --- Integração Social / Meta (Phase 14 - Fundação) ---
# Variáveis para a fundação da integração com Meta/Facebook (SOC-06).
# Segredos, chaves e tokens ficam apenas no backend e nunca devem ser expostos ao frontend ou logs.
# Preencha os segredos somente no ambiente real (.env/deploy), sem versionar valores reais.
# SOCIAL_TOKEN_ENCRYPTION_KEY deve ser uma chave Fernet válida (32 bytes url-safe base64) quando preenchida.
# SOCIAL_RETRY_DELAYS é uma lista CSV de inteiros em segundos.
META_APP_ID=
...
SITE_PUBLIC_URL=
```

**Apply to:** Add Phase 16/social-post policy flag with pt-BR comment explaining default (sem contato/empresa) and configurability per POST-06/D-16. Keep secrets-only-in-backend guidance; do not add frontend-exposed vars.

---

### `backend/app/services/social/__init__.py` (module exports, wiring)

**Analogs:** `backend/app/services/social/__init__.py`, `backend/app/crud/__init__.py`

**Explicit export pattern** (`backend/app/services/social/__init__.py`, lines 1-21):
```python
from .crypto import SocialTokenDecryptError, decrypt_token, encrypt_token, validate_fernet_key
from .facebook import FacebookPublisher
from .publisher import SocialPublisher
from .types import PublishFailureCategory, PublishResult, SocialPostPayload

__all__ = [
    "SocialTokenDecryptError",
    "decrypt_token",
    "encrypt_token",
    "validate_fernet_key",
    "PublishFailureCategory",
    "PublishResult",
    "SocialPostPayload",
    "SocialPublisher",
    "FacebookPublisher",
]
```

**Apply to:** Export new generation service/types/helpers only if needed by other modules; keep `__all__` explicit and avoid coupling publishing (Phase 17 stub in `facebook.py`) with generation concerns.

---

### `frontend/lib/api.ts` (API client/types, request-response)

**Analog:** `frontend/lib/api.ts` (self)

**Imports, base/types, error handling, auth fetch pattern** (lines 1-7, 111-168, 370-450):
```ts
import type { CitySlug } from "./cities";

export type JobStatus = "pending" | "published" | "needs_review" | "invalid";

export interface JobAdmin { ... id: string; ... status: JobStatus; contact_email: string | null; contact_phone: string | null; source_snippet: string | null; created_at: string; updated_at: string; expires_at: string; }
export interface JobUpdate { title?: string; ... city?: string; contact_email?: string | null; contact_phone?: string | null; }

const API = resolveApiBase();

export class ApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) { super(message); this.name = "ApiError"; this.status = status; }
}

async function readError(res: Response): Promise<string> { /* handles detail string/array */ }

export async function approveJob(token: string, id: string): Promise<JobAdmin> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${id}/approve`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as JobAdmin;
}
```

**Typed admin integration calls (good analog for new social draft calls)** (lines 452-576):
```ts
export interface MetaIntegrationStatus { provider: "facebook"; status: "connected" | "needs_reconnect" | "disconnected"; ... pending_selection: boolean; alert: MetaIntegrationAlert | null; }

export async function getMetaIntegrationStatus(token: string): Promise<MetaIntegrationStatus> {
  const res = await fetch(`${API}/api/v1/admin/integrations/meta/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as MetaIntegrationStatus;
}
```

**Apply to:** Add types/functions for draft get/generate/save and update `approveJob` return type to new envelope (e.g. `{ job: JobAdmin; social: { status: "registered"|"skipped"|"warning"; code?: string; message?: string } }`) in sync with backend schema/route and `ReviewQueue.tsx`. Reuse `ApiError`/`readError`, `Authorization: Bearer ${token}`, and JSON content-type for POST/PUT bodies.

---

### `frontend/app/admin/review/EditJobDialog.tsx` (UI component, form/state + async actions)

**Analogs:** `frontend/app/admin/review/EditJobDialog.tsx` (self), `frontend/app/admin/integracoes/IntegrationsClient.tsx`

**Dialog/form structure and hooks** (`EditJobDialog.tsx`, lines 1-20, 164-211, 285-309, 330-482):
```tsx
"use client";

import { useEffect, useRef, useState, type FormEvent, type RefObject } from "react";
import { useToast } from "@/components/admin/ToastProvider";
import { X } from "@/components/admin/icons";
import { updateJob, type JobAdmin, type JobUpdate } from "@/lib/api";
import { CITY_OPTIONS, type CitySlug } from "@/lib/cities";

export interface EditJobDialogProps {
  job: JobAdmin | null;
  token: string | null;
  open: boolean;
  onClose: () => void;
  onSaved: (job: JobAdmin) => void;
}

export function EditJobDialog({ job, token, open, onClose, onSaved }: EditJobDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const [form, setForm] = useState<FormState>(() => toFormState(job));
  const [errors, setErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setForm(toFormState(job));
    setErrors({});
  }, [job, open]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      titleRef.current?.focus();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);
  ...
  return (
    <dialog
      ref={dialogRef}
      aria-labelledby="edit-job-title"
      onClose={onClose}
      onCancel={(event) => { if (saving) event.preventDefault(); }}
      className="mb-0 mt-auto max-h-[92dvh] w-full max-w-none flex-col overflow-hidden rounded-t-[16px] border-0 bg-surface p-0 ... backdrop:bg-[rgba(5,2,12,.72)] open:flex ..."
    >
      ...
      <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
        <div className="grid min-h-0 flex-1 gap-6 overflow-y-auto ... md:grid-cols-[minmax(0,1fr)_320px]">...</div>
        <footer className="flex shrink-0 items-center justify-end gap-3 border-t border-line p-4">...</footer>
      </form>
    </dialog>
  );
}
```

**Async action/loading/confirmation/banner patterns** (`frontend/app/admin/integracoes/IntegrationsClient.tsx`, lines 56-68, 169-221, 484-521):
```tsx
const [actionLoading, setActionLoading] = useState<"start" | "verify" | "confirm" | "disconnect" | null>(null);
const [banner, setBanner] = useState<{ kind: BannerKind; text: string } | null>(null);
const dialogRef = useRef<HTMLDialogElement | null>(null);

const handleVerify = useCallback(async () => {
  if (!token) return;
  setActionLoading("verify");
  setTransientVerifyMessage(null);
  setPageError(null);
  try {
    const data = await verifyMetaIntegration(token);
    ...
    toast("Verificação concluída.", "success");
  } catch (err) {
    const message = err instanceof ApiError ? err.message : "Não foi possível concluir a ação...";
    setBanner({ kind: "error", text: message });
    toast(message, "error");
  } finally {
    setActionLoading(null);
  }
}, [token, ...]);

<dialog ref={dialogRef} onCancel={(e) => { e.preventDefault(); if (actionLoading !== "disconnect") setShowDisconnectDialog(false); }} ...>
  <form method="dialog" className="space-y-4 p-6" onSubmit={(e) => e.preventDefault()}>...</form>
</dialog>
```

**Apply to:** Embed `Post para Facebook` section per UI-SPEC/CONTEXT D-05/D-06 (textarea, counter `{n}/700`, generate/regenerate/save, publish-now/schedule toggle with BRT label, preview, origin/status chips, fallback/missing-URL notices, frozen state). Reuse `min-h-11`, token classes (`bg-canvas`, `border-line`, `text-fg-muted`, `bg-accent-strong`), native `<dialog>` for regenerate confirmation, `useToast`, and `ApiError`-aware messages. Load draft on open (recommended), track unsaved changes, disable edits when approved/scheduled (D-12).

---

### `frontend/app/admin/review/ReviewQueue.tsx` (UI component, request-response + optimistic UI)

**Analog:** `frontend/app/admin/review/ReviewQueue.tsx` (self)

**Auth/error helper, state, optimistic mutation and toast patterns** (lines 24-37, 53-80, 161-197):
```tsx
function handleAuthError(err: unknown): boolean {
  if (err instanceof ApiError && err.status === 401) {
    try { sessionStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
    window.location.replace("/admin/paste");
    return true;
  }
  return false;
}

const mutatingRef = useRef(false);

const handleApprove = async (job: JobAdmin) => {
  if (!token) return;
  if (mutatingRef.current) {
    toast("Aguarde a operação anterior.", "error");
    return;
  }
  mutatingRef.current = true;
  const snapshot = items;
  const previousTotal = total;
  const previousCounts = counts;

  setItems((prev) => prev.filter((item) => item.id !== job.id));
  setTotal((prev) => Math.max(0, prev - 1));
  setCounts((prev) => ({ ...prev, [tab]: Math.max(0, (prev[tab] ?? 1) - 1) }));

  try {
    await approveJob(token, job.id);
    toast("Vaga aprovada e publicada.", "success");
    ...
  } catch (err) {
    setItems(snapshot);
    setTotal(previousTotal);
    setCounts(previousCounts);
    if (handleAuthError(err)) return;
    const message = err instanceof Error ? err.message : "Falha ao aprovar";
    toast(`Erro: ${message}`, "error");
  } finally {
    mutatingRef.current = false;
  }
};
```

**Apply to:** Adapt `approveJob` handling to new envelope result (`{ job, social }`) without losing optimistic/site-first behavior: always communicate site published, then branch toast for `social.status` (`registered`/`skipped`/`warning`) per UI-SPEC copy (D-09/D-10/D-11). Keep snapshot rollback only for actual approve request failure that means job not published as before.

## Shared Patterns

### Admin route protection and deps (FastAPI)
**Source:** `backend/app/api/v1/admin.py` (lines 16, 24-33, 41-49), `backend/app/api/v1/integrations.py` (lines 11, 36-38)
**Apply to:** All new backend admin social endpoints (draft CRUD, generate, approve evolution)
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.deps import get_session, require_admin

router = APIRouter(prefix="/admin", tags=["admin"])
# or Annotated deps style:
# DbSession = Annotated[AsyncSession, Depends(get_session)]
# claims via Depends(require_admin)
```

### Transaction ownership and best-effort separation
**Source:** `backend/app/crud/jobs.py` (lines 137-148 flush-only), `backend/app/api/v1/admin.py` (lines 124-127), `backend/app/api/v1/integrations.py` (lines 140-151)
**Apply to:** `crud/social_posts.py`, approve flow in `admin.py`
```python
await approve_job(session, job)
await session.commit()
await session.refresh(job)
# CRUD helpers use await session.flush(); routes commit/rollback.
# For D-09: commit job first, then try social registration in separate try/except without rolling back job.
```

### pt-BR HTTP errors and validation
**Source:** `backend/app/api/v1/admin.py` (lines 59-64, 94-96, 121-123, 158-167), `backend/app/core/config.py` (ValueError messages in pt-BR)
**Apply to:** New draft/schedule/policy/link validation errors and 404/409/422/503 responses
```python
raise HTTPException(status_code=422, detail="Status inválido")
raise HTTPException(status_code=404, detail="Vaga não encontrada")
raise HTTPException(status_code=409, detail="Vaga não está na fila de revisão")
```

### Frontend admin fetch/auth/toast conventions
**Source:** `frontend/lib/api.ts` (lines 132-168, 409-450), `frontend/app/admin/review/ReviewQueue.tsx` (lines 24-37, 191-196), `frontend/app/admin/integracoes/IntegrationsClient.tsx` (lines 7-18, 135-141, 210-216)
**Apply to:** New social draft API calls and UI actions in EditJobDialog/ReviewQueue
```ts
export class ApiError extends Error { readonly status: number; ... }
if (!res.ok) throw new ApiError(await readError(res), res.status);
// 401 => clear TOKEN_KEY and redirect to /admin/paste
// UI: try/catch -> toast success or `Erro: ${message}` / warning as specified
```

### Admin UI tokens and controls (dark admin system)
**Source:** `frontend/app/admin/review/EditJobDialog.tsx` (classes throughout, e.g. lines 100-108, 299-327, 463-479), `frontend/app/admin/integracoes/IntegrationsClient.tsx` (lines 296-307, 360-371, 484-521)
**Apply to:** New Post para Facebook section, toggle, preview, banners, confirm dialog
```tsx
className="min-h-11 w-full rounded-lg border border-line-strong bg-canvas px-3 text-base text-fg placeholder:text-fg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
className="min-h-11 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover disabled:opacity-50"
<dialog ... className="... bg-surface ... backdrop:bg-[rgba(5,2,12,.72)] open:flex ..." onCancel={(e)=>{ if(loading) e.preventDefault(); }}>
```

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md/UI-SPEC patterns and locked decisions):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/app/services/social/post_generation.py` (social-specific prompt/template/policy/sanitize + BRT schedule conversion parts) | service | transform/generate | No existing "social post copy generation" service; Groq seam exists in extraction but extraction is schema-parsing/grounding-oriented (different prompt/output/guards). Follow D-03/D-14-D-17 and RESEARCH patterns for template fallback, policy scrub, and `zoneinfo` schedule conversion. |

## Metadata

**Analog search scope:** `backend/app/` (api, crud, schemas, services, models, core), `backend/.env.example`, `frontend/app/admin/review/`, `frontend/app/admin/integracoes/`, `frontend/lib/api.ts`, `frontend/app/(public)/page.tsx`
**Files scanned:** 18 (targeted reads/inspections) + directory listings
**Pattern extraction date:** 2026-11-15
