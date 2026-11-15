# Phase 15: OAuth Meta e Integrações no Admin - Pattern Map

**Mapped:** 2026-11-15
**Files analyzed:** 16 (10 new, 4 modified, 2 reused/reference)
**Analogs found:** 13 / 16

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/api/v1/integrations.py` (new) | route/controller | request-response (HTTP redirect + JSON, external OAuth callback) | `backend/app/api/v1/admin.py` | exact |
| `backend/app/api/v1/router.py` (modify) | config/route registration | config wiring | `backend/app/api/v1/router.py` (self) | exact |
| `backend/app/schemas/social_integrations.py` (new) | schema/validation | transform/validation (request/response DTOs) | `backend/app/schemas/job.py`, `backend/app/schemas/auth.py` | exact |
| `backend/app/services/social/meta_oauth.py` (new) | service (domain orchestration) | request-response + external API I/O + state transform | `backend/app/services/social/crypto.py`, `backend/app/services/social/types.py` | role-match |
| `backend/app/services/social/meta_graph.py` (optional new, discretion) | service/utility (HTTP client wrapper) | request-response (outbound Graph API) | `backend/app/services/social/meta_oauth.py` (if split) / existing `httpx` usage patterns | partial |
| `backend/app/models/social_account.py` (reuse/modify if needed) | model/persistence | CRUD/state persistence | `backend/app/models/social_account.py` (existing, Phase 14) | exact |
| `backend/app/core/config.py` (reuse; minor checks possible) | config | config/validation | `backend/app/core/config.py` (existing) | exact |
| `backend/app/deps.py` (reuse) | dependency/auth guard | request-response (dependency injection) | `backend/app/deps.py` (existing) | exact |
| `frontend/app/admin/layout.tsx` (modify) | layout/component | UI composition/navigation | `frontend/app/admin/layout.tsx` (self) | exact |
| `frontend/app/admin/page.tsx` (modify, optional) | page/component | UI composition | `frontend/app/admin/page.tsx` (self) | exact |
| `frontend/app/admin/integracoes/page.tsx` (new) | page (route entry) | UI composition | `frontend/app/admin/review/page.tsx` | exact |
| `frontend/app/admin/integracoes/IntegrationsClient.tsx` (new) | client component (stateful UI) | request-response (fetch) + UI state/events | `frontend/app/admin/review/page.tsx` + `frontend/components/admin/AdminGuard.tsx` + `frontend/lib/api.ts` consumers | role-match |
| `frontend/lib/api.ts` (modify) | client utility/API layer | request-response (HTTP fetch, typed contracts) | `frontend/lib/api.ts` (self) | exact |
| `backend/tests/test_meta_oauth_flow.py` (new, Wave 0) | test | request-response (mocked Graph/DB/session) | `backend/tests/test_admin_jobs.py` | exact |
| `backend/tests/test_meta_oauth_validation.py` (new, Wave 0) | test | transform/validation + HTTP-mocked outcomes | `backend/tests/test_social_crypto.py`, `backend/tests/test_admin_jobs.py` | role-match |
| `backend/tests/test_meta_oauth_security.py` (new, Wave 0) | test (security assertions) | request-response + sanitization checks | `backend/tests/test_social_crypto.py` | role-match |
| `backend/tests/test_integrations_api.py` (new, Wave 0) | test | request-response (auth guards/contracts) | `backend/tests/test_admin_jobs.py` | exact |

> **Note (D-08/open question):** If pending page selection is implemented with a DB-backed transient store, expect additional files (e.g. `backend/app/models/social_oauth_pending.py`, Alembic migration). No direct analog exists in current `social_*` persistence for expiring pending OAuth state; follow `SocialAccount` model conventions and existing Alembic/migration workflow if added.

## Pattern Assignments

### `backend/app/api/v1/integrations.py` (route/controller, request-response)

**Analogs:** `backend/app/api/v1/admin.py` (auth-guarded admin routes, error handling, pagination/response style) and `backend/app/api/v1/router.py` (registration). `backend/app/api/v1/auth.py` is a secondary analog for auth-adjacent endpoints.

**Imports pattern** (`backend/app/api/v1/admin.py:1-24`):
```python
from fastapi import APIRouter, Depends, HTTPException, Query
import uuid
from typing import Literal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.jobs import (
    approve_job,
    delete_expired_jobs,
    delete_job,
    get_job,
    list_by_status,
    update_job,
)
from app.deps import get_session, require_admin, require_cron_secret
from app.models.job import JobStatus
from app.schemas.job import JobAdmin, JobAdminListResponse, JobUpdate
from app.services.cities import resolve_city

router = APIRouter(prefix="/admin", tags=["admin"])
```
*Apply for integrations:* use `APIRouter` with clear prefix/tags (discretion: e.g. `/admin/integrations` or keep under `/admin`), import `Depends`, `HTTPException`, `Query`/`Request`/`RedirectResponse` as needed, `AsyncSession`, `get_session`, `require_admin` from `app.deps`, integration schemas, and `services.social.meta_oauth` functions. Keep token/secret handling server-side only.

**Auth/guard pattern** (`backend/app/api/v1/admin.py:24-33,40-49,87-95` and `backend/app/deps.py:34-54`):
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
    ...
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdminListResponse:
    ...

# deps.py
async def require_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if creds is None or creds.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        claims = decode_access_token(creds.credentials)
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc
    if claims.get("sub") != "admin" or claims.get("role") != "admin":
        raise _unauthorized()
    return claims
```
*Apply (D-04):* `start`, `status`, `verify`, `select-page`, `disconnect` MUST depend on `require_admin` (+ `get_session` where DB needed). `callback` MUST NOT require Bearer but MUST fail closed on invalid/expired/forged signed `state` and perform all exchange/validation/persistence server-side.

**Core response/redirect + validation pattern** (`backend/app/api/v1/admin.py:58-78,118-127,136-166,180-186`):
```python
    if status not in ("pending", "needs_review"):
        raise HTTPException(status_code=422, detail="Status inválido")
    ...
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    if job.status not in (JobStatus.pending, JobStatus.needs_review):
        raise HTTPException(
            status_code=409, detail="Vaga não está na fila de revisão"
        )
    await approve_job(session, job)
    await session.commit()
    await session.refresh(job)
    return JobAdmin.model_validate(job)

    try:
        await update_job(session, job, payload)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "at_least_one_contact" in str(exc.orig):
            raise HTTPException(status_code=422, detail="Vaga precisa ter ao menos um contato (email ou telefone)") from exc
        raise HTTPException(status_code=422, detail="Dados inválidos para a vaga") from exc
```
*Apply:* return safe, typed payloads for status/pending actions; on mutating DB ops `commit`/`refresh` and rollback on integrity failures. For OAuth callback (D-02/D-03), prefer `RedirectResponse` to `/admin/integracoes?...` with **generic/safe result codes only** (no tokens/secrets/raw provider errors). Map definitive validation failures to `needs_reconnect` per D-10; transient verification failures must not downgrade a valid connection.

**Error handling pattern** (`backend/app/api/v1/admin.py:29-32,59-60,94-96,118-123,150-166,181-182` and `backend/app/deps.py:28-32,58-59,86-99`):
```python
def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
...
raise HTTPException(status_code=404, detail="Vaga não encontrada")
raise HTTPException(status_code=409, detail="Vaga não está na fila de revisão")
```
*Apply:* use pt-BR, user-safe `detail` strings; never leak tokens, app secret, raw Graph payloads, or sensitive query params in responses/logs. For missing Meta env/config, fail with safe operational message (see RESEARCH Open Question 3) without exposing values.

**Router registration** (`backend/app/api/v1/router.py:1-10`):
```python
from fastapi import APIRouter

from app.api.v1 import admin, auth, extract, health, public

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(extract.router)
api_router.include_router(public.router)
```
*Apply:* add integrations module import and `api_router.include_router(integrations.router)` (exact placement at discretion, keep consistent).

---

### `backend/app/schemas/social_integrations.py` (schema/validation, transform)

**Analogs:** `backend/app/schemas/job.py`, `backend/app/schemas/auth.py`

**Imports and base schema pattern** (`backend/app/schemas/job.py:19-48`, `backend/app/schemas/auth.py:1-19`):
```python
import re
import uuid
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.job import JobStatus
from app.services.cities import resolve_city


class JobPublic(BaseModel):
    """A published, non-expired job with NO contact fields (D-15, D-18)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    ...
    # NO contact_email / contact_phone (D-18).


class LoginRequest(BaseModel):
    password: str
    cf_token: str = Field(min_length=1, max_length=2048)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
```
*Apply:* define safe response/request models for Meta integration status (D-11), pending page list/selection, and action responses. Use `ConfigDict(from_attributes=True)` for ORM-backed responses if needed. **Never include** `page_access_token`, `META_APP_SECRET`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, or any OAuth token fields in schemas exposed to frontend.

**Validation/normalization pattern** (`backend/app/schemas/job.py:132-208`):
```python
class JobUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    ...

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Título é obrigatório")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Título é obrigatório")
        return stripped

    @model_validator(mode="after")
    def _at_least_one_contact(self) -> "JobUpdate":
        provided = self.model_fields_set
        if "contact_email" in provided and "contact_phone" in provided:
            if self.contact_email is None and self.contact_phone is None:
                raise ValueError(
                    "Vaga precisa ter ao menos um contato (email ou telefone)"
                )
        return self
```
*Apply:* validate selection payloads (e.g. selected `page_id` non-empty/belongs to pending context handled in service/route), normalize/strip inputs, and keep error messages safe and pt-BR where user-facing.

---

### `backend/app/services/social/meta_oauth.py` (service, request-response + external I/O)

**Analogs:** `backend/app/services/social/crypto.py` (domain service style, safe errors), `backend/app/services/social/types.py` and `facebook.py` (typed contracts/stub style), plus RESEARCH code patterns for state/token exchange/debug_token.

**Domain service + safe error pattern** (`backend/app/services/social/crypto.py:1-33`):
```python
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class SocialTokenDecryptError(Exception):
    """Falha segura de descriptografia de token social (sem expor segredo)."""


def validate_fernet_key(key: str | bytes) -> None:
    """Valida formato de chave Fernet sem ecoar o valor da chave."""
    try:
        key_bytes = key.encode() if isinstance(key, str) else key
        Fernet(key_bytes)
    except Exception as exc:
        raise ValueError("SOCIAL_TOKEN_ENCRYPTION_KEY inválida") from exc


def encrypt_token(plaintext: str, key: str | bytes) -> str:
    """Criptografa explicitamente um token social com Fernet e retorna texto."""
    key_bytes = key.encode() if isinstance(key, str) else key
    return Fernet(key_bytes).encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str, key: str | bytes) -> str:
    """Descriptografa explicitamente um token social com falha segura."""
    try:
        key_bytes = key.encode() if isinstance(key, str) else key
        return Fernet(key_bytes).decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError, TypeError) as exc:
        raise SocialTokenDecryptError(
            "token social inválido ou chave de criptografia incorreta"
        ) from exc
```
*Apply:* keep OAuth/Graph logic encapsulated in `services/social/`, reuse `encrypt_token`/`decrypt_token` for `page_access_token`, and define safe domain exceptions/results (no secrets in messages). Never store plaintext page tokens.

**Typed result/contract style** (`backend/app/services/social/types.py:1-26`, `facebook.py:1-19`):
```python
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
```
*Apply:* consider typed internal results for OAuth/verification outcomes (e.g. definitive vs transient classification D-10) and safe reason codes to drive redirects/status alerts without leaking provider details.

**State + OAuth/Graph flow pattern (RESEARCH guidance to implement concretely)** (`15-RESEARCH.md` excerpts, Architecture Pattern 1/2/4):
```python
# build/validate signed stateless state (PyJWT + TTL, purpose claim)
claims = {"purpose": "meta_oauth", "nonce": str(uuid.uuid4()), "iat": now, "exp": now + timedelta(seconds=META_OAUTH_STATE_TTL_SECONDS)}
state = jwt.encode(claims, secret, algorithm="HS256")
jwt.decode(state, secret, algorithms=["HS256"])  # reject invalid/expired

# chain: code -> short-lived user token -> long-lived user token (fb_exchange_token)
# -> /{META_GRAPH_VERSION}/me/accounts?fields=id,name,access_token,tasks (long-lived user token)
# -> /{META_GRAPH_VERSION}/debug_token?input_token={page_token}&access_token={app_id}|{app_secret}
```
*Apply:* always use `settings.META_GRAPH_VERSION`, `META_APP_ID`, `META_APP_SECRET`, `META_OAUTH_REDIRECT_URI` from `Settings`; enforce minimal scopes `pages_show_list,pages_manage_posts,pages_read_engagement`; classify definitive vs transient verification failures (D-10) conservatively; never log full URLs/bodies containing tokens/codes/secrets.

---

### `backend/app/models/social_account.py` (model/persistence, reuse)

**Analog:** existing `backend/app/models/social_account.py` (Phase 14 foundation)

**Model/enum/index pattern** (`backend/app/models/social_account.py:1-57`):
```python
class SocialAccountStatus(str, Enum):
    connected = "connected"
    needs_reconnect = "needs_reconnect"
    disconnected = "disconnected"


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
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
    connected_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    token_checked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at/updated_at ...

    __table_args__ = (
        Index("ix_social_accounts_provider_status", "provider", "status"),
        Index("ix_social_accounts_page_id", "page_id"),
    )
```
*Apply:* persist only one active Facebook page/connection (D-06), store `page_access_token` encrypted (crypto service), update `status`/`connected_at`/`token_checked_at` appropriately, and on disconnect remove/clear usable credentials and mark disconnected (D-07). Reuse existing enum values for UI-safe status payload.

---

### `frontend/app/admin/layout.tsx` and `frontend/app/admin/page.tsx` (layout/page, UI composition)

**Analogs:** existing files themselves

**Layout/nav shell pattern** (`frontend/app/admin/layout.tsx:1-51`):
```tsx
import Link from "next/link";
import "./admin.css";
import { LogoutButton } from "@/components/admin/LogoutButton";
import { ToastProvider } from "@/components/admin/ToastProvider";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <div className="flex min-h-screen flex-col bg-canvas text-fg">
        <header className="sticky top-0 z-40 border-b border-line bg-canvas">
          <div className="mx-auto flex h-16 w-full max-w-[1120px] items-center justify-between gap-4 px-4 md:px-6">
            <div className="flex items-center gap-4">
              <Link href="/" className="text-xl font-semibold text-fg">EmpregaNoix<span aria-hidden="true" className="text-accent-soft">.</span></Link>
              <span className="hidden text-sm font-normal text-fg-muted md:inline">Procurar um emprego, não deve dar trabalho</span>
            </div>
            <div className="flex items-center gap-2"><LogoutButton /></div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1120px] flex-1 px-4 py-8 md:px-6">{children}</main>
      </div>
    </ToastProvider>
  );
}
```
*Apply (D-13):* add clear "Integrações" navigation entry consistent with admin shell/tokens (and optionally preserve existing header simplicity). Keep all admin pages under shared layout/ToastProvider.

**Admin dashboard card pattern** (`frontend/app/admin/page.tsx:1-45`):
```tsx
"use client";

import Link from "next/link";
import { useAdminGuard } from "@/components/admin/AdminGuard";

const cardClass =
  "group rounded-[12px] border border-line bg-surface p-6 transition-colors hover:border-accent focus-visible:border-accent";

export default function AdminPage() {
  useAdminGuard();
  return (
    <div>
      <h1 className="mb-2 text-3xl font-semibold leading-tight tracking-tight">Painel admin</h1>
      <p className="mb-8 text-fg-muted">Curadoria de vagas: extraia, revise e publique.</p>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Link href="/admin/paste" className={cardClass}> ... </Link>
        <Link href="/admin/review" className={cardClass}> ... </Link>
      </div>
    </div>
  );
}
```
*Apply (optional):* add an Integrações card/link using same `cardClass`, typography, and accent-hover conventions from UI-SPEC/admin tokens.

---

### `frontend/app/admin/integracoes/page.tsx` (page, UI composition)

**Analog:** `frontend/app/admin/review/page.tsx`

**Admin page wrapper pattern** (`frontend/app/admin/review/page.tsx:1-17`):
```tsx
"use client";

import { ReviewQueue } from "@/app/admin/review/ReviewQueue";

export default function Page() {
  return (
    <div>
      <h1 className="text-[20px] font-semibold leading-tight [overflow-wrap:anywhere] [text-wrap:balance]">
        Revisão de vagas
      </h1>
      <p className="mt-1 text-[14px] text-fg-muted">
        Confira o texto-fonte ao lado e aprove para publicar.
      </p>
      <ReviewQueue />
    </div>
  );
}
```
*Apply (D-13/D-14, UI-SPEC):* create `page.tsx` as route entry rendering title/subtitle per copy contract (`Integrações`, helper subtitle) and mount `IntegrationsClient` (or equivalent). Follow existing admin spacing/typography tokens; prefer contract sizes (Display/Heading/Body) consistently.

---

### `frontend/app/admin/integracoes/IntegrationsClient.tsx` (client component, stateful UI)

**Analogs:** `frontend/components/admin/AdminGuard.tsx`, `frontend/components/admin/ToastProvider.tsx`, `frontend/lib/api.ts`, and admin page/client composition (`review/page.tsx`).

**Auth guard + session token pattern** (`frontend/components/admin/AdminGuard.tsx:1-33`, `frontend/lib/auth.ts:1-2`):
```tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { TOKEN_KEY } from "@/lib/auth";

export function useAdminGuard(): string | null {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = sessionStorage.getItem(TOKEN_KEY);
    } catch {
      // ignore storage errors
    }
    setToken(stored);
    if (!stored) {
      router.replace("/admin/paste");
    }
  }, [router]);

  return token;
}
```
*Apply:* protect integrations UI via `useAdminGuard()` and use Bearer token from `sessionStorage`/`TOKEN_KEY` for authenticated API calls (status/verify/select/disconnect/start-preflight as designed). Handle loading/unauthenticated states gracefully.

**Toast/feedback pattern** (`frontend/components/admin/ToastProvider.tsx:1-157`):
```tsx
export type ToastVariant = "success" | "error";
...
const ToastContext = createContext<ToastContextValue | undefined>(undefined);
...
export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return ctx;
}
```
*Apply (D-16/UI-SPEC):* reuse `useToast()` and/or contextual banners for action results and callback outcomes (`connected/error/cancelled/select_page`) with safe pt-BR copy. Do not render secrets/tokens/provider internals.

**Client fetch + error handling integration** (`frontend/lib/api.ts` usage pattern, see API section below): use typed helpers, catch `ApiError` for status-aware UI messaging/retry affordances, and enforce UI states/CTAs per D-14 (disconnected, pending selection, connected, needs_reconnect, loading/errors). For destructive disconnect, require explicit confirmation dialog before API call (D-15).

---

### `frontend/lib/api.ts` (utility/client, request-response)

**Analog:** `frontend/lib/api.ts` (self)

**API base, ApiError, request helper pattern** (`frontend/lib/api.ts:111-210`):
```ts
function resolveApiBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (fromEnv) return fromEnv;
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not set. Configure it in the Vercel project env (Production scope) — production builds cannot fall back to http://localhost:8000.",
    );
  }
  return "http://localhost:8000";
}

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

export async function extractJobs(token: string, text: string): Promise<ExtractSummary> {
  const res = await fetch(`${API}/api/v1/admin/extract`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as ExtractSummary;
}
```
*Apply:* add typed interfaces for safe Meta integration status/pending pages and helpers (e.g. `getMetaIntegrationStatus`, `startMetaOAuth` preflight/URL fetch if chosen, `verifyMetaIntegration`, `disconnectMetaIntegration`, `listPendingMetaPages`, `confirmMetaPageSelection`) following same `fetch` + `Authorization: Bearer ${token}` + `readError`/`ApiError` conventions. Preserve `NEXT_PUBLIC_API_URL` resolution and never send/store secrets on client.

**Admin-authenticated endpoint pattern** (`frontend/lib/api.ts:380-450`):
```ts
export async function listAdminJobs(token: string, params?: { ... }): Promise<JobAdminListResponse> {
  const url = new URL(`${API}/api/v1/admin/jobs`);
  ...
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as JobAdminListResponse;
}

export async function approveJob(token: string, id: string): Promise<JobAdmin> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${id}/approve`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as JobAdmin;
}
```
*Apply:* for same-tab connect flow (D-02), if backend returns a JSON `{ redirect_url }` from authenticated start endpoint, fetch it with Bearer then `window.location.assign(redirect_url)`; do not attach tokens to Meta URLs.

---

### Backend tests (Wave 0) — `test_meta_oauth_*`, `test_integrations_api.py`

**Analogs:** `backend/tests/test_admin_jobs.py`, `backend/tests/test_social_crypto.py`, `backend/tests/conftest.py`

**Integration test/auth + request pattern** (`backend/tests/test_admin_jobs.py:1-95,255-318,540-582`):
```python
"""Admin job review integration tests ..."""

VALID_CF_TOKEN = "token-de-teste"


async def _login(client, admin_password="test-password"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    body = resp.json()
    assert body["token_type"] == "bearer"
    return body["access_token"]


@pytest.mark.asyncio
async def test_list_pending(client, db_session, admin_password):
    token = await _login(client, admin_password)
    ...
    resp = await client.get(
        "/api/v1/admin/jobs",
        headers={"Authorization": f"Bearer {token}"},
        params={"status": "pending"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2


@pytest.mark.asyncio
async def test_requires_auth(client, db_session, admin_password):
    resp = await client.get("/api/v1/admin/jobs")
    assert resp.status_code == 401
```
*Apply:* test `require_admin` guards for status/verify/select/disconnect (and start preflight endpoint as implemented), safe response contracts, and 401 behavior. Mock Graph HTTP calls (never real Meta). For callback, test browser-like GET without Bearer but with valid/invalid/expired state and safe redirect outcomes.

**Security/domain assertion pattern** (`backend/tests/test_social_crypto.py:1-63`):
```python
def test_decrypt_with_wrong_key_raises_safe_domain_error() -> None:
    ...
    with pytest.raises(SocialTokenDecryptError) as excinfo:
        decrypt_token(ciphertext, other_key)

    msg = str(excinfo.value)
    assert msg == "token social inválido ou chave de criptografia incorreta"
    assert "segredo" not in msg
    assert key not in msg
    assert other_key not in msg
    assert ciphertext not in msg
```
*Apply (META-05):* assert no `access_token`, `EAAB`, `client_secret`, `META_APP_SECRET`, encryption key, or OAuth `code` appears in JSON payloads, redirect URLs returned to UI, or logged/sanitized error surfaces. Assert persisted page token is encrypted (not plaintext).

**Test harness and dependency override pattern** (`backend/tests/conftest.py:1-120,200-248` conceptually and structure):
```python
# deterministic settings/env before app imports; skip suite cleanly if no DB configured
TEST_ADMIN_PASSWORD = "test-password"
...
get_settings.cache_clear()

class FakeTurnstileVerifier:
    ...

@pytest.fixture
async def app(db_session):
    application = create_app()
    async def _override_get_session():
        yield db_session
    application.dependency_overrides[get_session] = _override_get_session
    application.dependency_overrides[get_turnstile_verifier] = _override_get_turnstile_verifier
    yield application
    application.dependency_overrides.clear()

@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
```
*Apply:* follow existing `conftest.py` fixtures (`client`, `db_session`, `admin_password`, `fake_turnstile` where relevant), use `dependency_overrides` for stubbing external/meta clients or inject mock transports, and keep tests offline/deterministic.

## Shared Patterns

### Admin authentication and protected endpoints
**Source:** `backend/app/deps.py:22-54`, `backend/app/api/v1/admin.py:40-49,87-95`
**Apply to:** `backend/app/api/v1/integrations.py` (all sensitive routes except callback, per D-04), `frontend/lib/api.ts` integration helpers, `frontend/app/admin/integracoes/*` (via `useAdminGuard`).
```python
bearer_scheme = HTTPBearer(auto_error=False)

async def require_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if creds is None or creds.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        claims = decode_access_token(creds.credentials)
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc
    if claims.get("sub") != "admin" or claims.get("role") != "admin":
        raise _unauthorized()
    return claims
```

### Safe secret handling and token encryption at rest
**Source:** `backend/app/services/social/crypto.py:6-33`, `backend/app/core/config.py:80-120` (social/Meta env validation)
**Apply to:** `meta_oauth.py`, any persistence/update of `social_accounts.page_access_token`, disconnect flow (D-07), status payloads (D-11/META-05).
```python
class SocialTokenDecryptError(Exception):
    """Falha segura de descriptografia de token social (sem expor segredo)."""

def encrypt_token(plaintext: str, key: str | bytes) -> str:
    key_bytes = key.encode() if isinstance(key, str) else key
    return Fernet(key_bytes).encrypt(plaintext.encode()).decode()
```
*Rule:* secrets/tokens only server-side; never in frontend, redirect query params, logs, or API responses.

### DB transaction/error discipline for mutations
**Source:** `backend/app/api/v1/admin.py:124-166`
**Apply to:** integrations routes/services performing connect/select/verify-state updates/disconnect.
```python
try:
    await update_job(session, job, payload)
    await session.commit()
except IntegrityError as exc:
    await session.rollback()
    raise HTTPException(status_code=422, detail="Dados inválidos para a vaga") from exc
await session.refresh(job)
```

### Frontend admin shell, guard, and feedback
**Source:** `frontend/app/admin/layout.tsx:17-50`, `frontend/components/admin/AdminGuard.tsx:15-33`, `frontend/components/admin/ToastProvider.tsx:43-157`
**Apply to:** `/admin/integracoes` page/client, nav entry, callback banners, action feedback.
```tsx
<ToastProvider>
  <div className="flex min-h-screen flex-col bg-canvas text-fg"> ... <main className="mx-auto w-full max-w-[1120px] flex-1 px-4 py-8 md:px-6">{children}</main> ... </div>
</ToastProvider>

// AdminGuard
const stored = sessionStorage.getItem(TOKEN_KEY);
if (!stored) router.replace("/admin/paste");
```

### Typed fetch client with `ApiError` and Bearer auth
**Source:** `frontend/lib/api.ts:111-170,192-210,380-450`
**Apply to:** new Meta integration API functions in `frontend/lib/api.ts` and UI state/error handling.
```ts
const res = await fetch(`${API}/api/v1/admin/extract`, {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({ text }),
});
if (!res.ok) throw new ApiError(await readError(res), res.status);
return (await res.json()) as ExtractSummary;
```

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns and locked decisions as primary guidance):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/app/services/social/meta_oauth.py` (OAuth state/exchange/debug orchestration specifics) | service | external OAuth/Graph request-response + security state machine | No existing Meta OAuth flow, signed stateless `state`, token exchange chain, `/debug_token` validation, or pending-page selection orchestration in repo; closest are `crypto.py`/social stubs for domain placement only. |
| `backend/app/api/v1/integrations.py` callback handler (unauthenticated browser redirect validated by signed state) | route/controller | redirect/callback request-response | Existing admin routes are Bearer-protected APIs; no prior external-provider callback endpoint with "auth via state, not JWT header" pattern (D-04). |
| Pending selection transient storage mechanism (if implemented as new model/table/store) | model/persistence or service store | ephemeral state + CRUD/expiry | D-08 requires secure, expiring, backend-mediated pending selection without token exposure; no existing transient OAuth-pending persistence pattern identified. Follow `SocialAccount`/SQLAlchemy conventions or a clearly bounded server-side store per research discretion. |

## Metadata

**Analog search scope:** `backend/app/api/v1`, `backend/app/core`, `backend/app/deps.py`, `backend/app/models`, `backend/app/schemas`, `backend/app/services/social`, `backend/tests`, `frontend/app/admin`, `frontend/components/admin`, `frontend/lib`
**Files scanned:** 24 (source/test files read directly) + directory listings for api/services/admin/lib/tests
**Pattern extraction date:** 2026-11-15
