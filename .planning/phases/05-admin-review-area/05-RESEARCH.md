# Phase 05: Admin Review Area - Research

**Researched:** 2026-10-27
**Domain:** Admin review queue (pending → published), admin schema with contact exposure, Tailwind v4 migration of admin panel, toast + optimistic updates, client-side guard, source_snippet grounding display
**Confidence:** HIGH

## User Constraints (from CONTEXT.md)

### Locked Decisions
[Verbatim from 05-CONTEXT.md `## Decisions`]

- **D-01:** Fila principal exibe apenas vagas `pending`; `needs_review` em aba/seção separada "Precisam correção"; `invalid` não revisável.
- **D-02:** Ordenação padrão: mais recentes primeiro (`created_at DESC`), tie-break por `id DESC`.
- **D-03:** Filtro por cidade (chips SP, RJ, BH, Remoto), reusando padrão da home pública; sem busca por texto livre.
- **D-04:** Paginação offset (page/limit, limit 24, controles), mesmo padrão da home pública.
- **D-05:** Aprovação individual por vaga, via botão "Aprovar"; status → `published`, item sai da fila (atualização otimista); feedback por toast; sem aprovação em lote.
- **D-06:** Edição via modal com todos os campos editáveis (title, company, activities, requirements, salary, benefits, city, contact_email, contact_phone); city validado contra {São Paulo, Rio de Janeiro, Belo Horizonte, Remoto}; contato exige ao menos um (CHECK `at_least_one_contact`).
- **D-07:** Exclusão hard delete com confirmação (modal "Tem certeza?"); sem "Rejeitar" e sem reversão published→pending.
- **D-08:** Aprovação definitiva — `published` não volta para `pending`.
- **D-09:** Layout lado a lado em desktop (campos à esquerda, snippet à direita, sticky) e empilhado em mobile (snippet abaixo em accordion).
- **D-10:** Snippet somente leitura; sem destaque automático de termos; quando vazio/nulo, placeholder "Sem texto-fonte disponível" (itálico/cinza), sem mudar layout.
- **D-11:** Hub `/admin` com links para `/admin/paste` e `/admin/review`; header admin compartilhado com logout; ponto de entrada único.
- **D-12:** Painel admin adota Tailwind v4 (novo route group), migrando paste + fila juntos; `globals-admin.css` (CSS plano) substituído; paridade visual com o público.
- **D-13:** Feedback via toast próprio (componente React mínimo, sem lib externa) + atualização otimista (remove item ao aprovar/excluir e revalida); variantes success/error; auto-dismiss ~3s.
- **D-14:** Proteção de acesso no front é guard client-side com redirecionamento: sem token em `sessionStorage`, redireciona para login; backend continua bloqueando com 401 (`require_admin`).

### OpenCode's Discretion
- Estrutura de arquivos/componentes da fila e do modal de edição (`components/admin/` ou similar), nomes de helpers de fetch.
- Mecânica exata do toast (posicionamento, animação, z-index) e da atualização otimista (rollback em erro).
- Comportamento do hub `/admin` quando não autenticado.
- Paginação visual (controles vs "Ver mais") na fila admin — reusar padrão Phase 4.
- Empty state da fila (copy pt-BR) e estado de loading (skeleton).
- Validação client-side do form de edição (zod) e mensagens de erro (renderizar `body.detail` verbatim).
- Se a aba "Precisam correção" é rota separada ou tab client-side.

### Deferred Ideas (OUT OF SCOPE)
- Aprovação em lote, ação "Rejeitar", reversão published→pending, destaque automático de termos no snippet, soft delete, busca por texto livre na fila admin, middleware Next.js server-side, biblioteca de toast externa, PIX real, páginas legais, badge "Vaga revisada", report, ciclo de vida/expiração, chaves reais do Cloudflare + wiring de deploy.

## Summary

Phase 5 completes the curation loop: the master pastes → extracts → reviews → approves. The backend already has the `Job` model with every field (`title`, `company`, `activities`, `requirements`, `salary`, `benefits`, `city`, `contact_email`, `contact_phone`, `source_snippet`, `status`), the `require_admin` guard, the extraction endpoint and a paginated/filtrada public read. What is missing is the **admin read surface** (list by status with city filter + offset pagination), the **approve/edit/delete mutations**, an **admin-facing schema that exposes contact** (different from contact-free `JobPublic`), and the **frontend review queue + edit modal + toast + Tailwind v4 admin shell**.

The right shape is to mirror the public board's read pattern (`list_published` → `list_by_status`) but for `pending`/`needs_review` statuses, add three mutations (approve → `published`, update with `at_least_one_contact` validation, hard delete), and expose a `JobAdmin` Pydantic schema (contact allowed, because the route is behind `require_admin`). On the frontend, reuse `JobGrid`/`Pagination`/`JobDetailDialog` idioms, migrate `/admin/paste` + new `/admin/review` to Tailwind v4 via a new `admin.css` (mirroring `public.css` tokens), implement a minimal toast context, and add a client-side guard that reads `nqu_admin_token` from `sessionStorage`.

**Primary recommendation:** Keep the backend thin (router → crud → schemas, single transaction per mutation, pt-BR `detail` errors rendered verbatim by the front), reuse the public board's pagination/filter conventions, and migrate the admin panel to Tailwind v4 in the same pass (D-12) so paste + review share one style.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| List review queue (pending/needs_review) | API / Backend | Frontend (render) | Status-filtered, city-filtered, paginated query must be server-side; frontend only renders |
| Approve (pending → published) | API / Backend | Frontend (optimistic) | State transition is server authority; frontend removes item optimistically and revalidates |
| Edit job fields | API / Backend | Frontend (modal + zod) | Validation + CHECK `at_least_one_contact` enforced server-side; client validates for UX |
| Hard delete | API / Backend | Frontend (confirm modal) | DB delete is server-side; frontend confirms via dialog |
| Contact exposure in admin | API / Backend | — | Contact is allowed only behind `require_admin`; public schema stays contact-free (D-18) |
| Source snippet display | Frontend (render) | Backend (persisted) | Read-only reference panel; data already persisted by extraction (D-08) |
| Admin auth guard (UX) | Browser / Client | API / Backend (401) | Token lives in `sessionStorage` (Bearer, no cookie); backend remains authoritative |
| Toast + optimistic updates | Browser / Client | — | Pure client UX; rollback on error |
| Tailwind v4 admin shell | Frontend (SSR/CSS) | — | CSS-only migration; no server logic |

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REVW-01 | Admin visualiza a fila de vagas com status `pending` | Backend `list_by_status(status, page, limit, city, sort)` + frontend `/admin/review` queue; city filter chips reuse Phase 4 pattern |
| REVW-02 | Admin aprova uma vaga (status → `published`) | `PATCH /admin/jobs/{id}/approve` (or `POST`); optimistic remove + toast; backend sets status published, updated_at trigger fires |
| REVW-03 | Admin edita os campos de uma vaga pelo ID | `PUT/PATCH /admin/jobs/{id}` with `JobUpdate` schema; validates `at_least_one_contact` + city whitelist server-side; modal with all fields |
| REVW-04 | Admin exclui uma vaga | `DELETE /admin/jobs/{id}` hard delete; confirm modal; optimistic remove + rollback |
| REVW-05 | Admin vê o trecho do texto-fonte ao lado dos campos | `source_snippet` already persisted (D-08 Phase 2); render read-only side panel (desktop) / accordion (mobile) with placeholder when empty |

## Standard Stack

Already fixed (from STACK.md, verified):

| Library | Version | Purpose |
|---------|---------|---------|
| Next.js (App Router) | 16.4.0 (codebase: 15.5.3) | Frontend |
| Tailwind CSS | 4.3.3 | Styling (admin migrates to v4 this phase) |
| FastAPI | 0.143.0 | Backend |
| SQLAlchemy (async) | 2.1.4 | ORM |
| asyncpg | 0.32.0 | Driver |
| Alembic | 1.20.0 | Migrations (none new expected) |
| Pydantic | 2.14.1 | Schemas (admin schema new) |
| PyJWT | 2.15.1 | Admin auth (existing) |
| zod | 4.6.7 (codebase: not installed yet) | Client-side edit form validation |
| next-turnstile | 1.0.7 | Login widget (existing) |

**No new backend dependencies required.** Admin mutations reuse existing stack. Frontend may add `zod` (not currently in `package.json`) for edit form validation; can also validate manually. [ASSUMED] zod is desirable but optional — manual validation acceptable given small form.

## Architecture Patterns

### Backend: admin review endpoints

Mount under existing `admin.router` (prefix `/admin`, already registered in `router.py`). Add to `backend/app/api/v1/admin.py` (or a new `admin_jobs.py` included similarly). Follow `extract.py` pattern: thin router → crud → schemas, `Depends(require_admin)`, `Depends(get_session)`, pt-BR `detail`, commit in router.

Proposed endpoints:

| Method | Path | Purpose | Status codes |
|--------|------|---------|--------------|
| GET | `/admin/jobs` | List by status (pending/needs_review), city filter, offset pagination | 200, 401 |
| PATCH | `/admin/jobs/{id}/approve` | pending/needs_review → published | 200, 401, 404 |
| PUT | `/admin/jobs/{id}` | Edit all fields | 200, 401, 404, 422 |
| DELETE | `/admin/jobs/{id}` | Hard delete | 204, 401, 404 |

Query params for GET: `status` (default `pending`, allowed `pending`/`needs_review`), `city` (slug/canonical/label, resolved like public), `page` (≥1), `limit` (default 24, ≤50 or 100), `sort` (default recentes). Coerce unknown status → 422 or clamp to pending. [ASSUMED] Recommend default `pending` and reject unknown status with 422 to keep contract clear; planner decides.

CRUD additions to `backend/app/crud/jobs.py`:

- `list_by_status(session, status, page, limit, *, city, sort)` → `(list[Job], int)` mirroring `list_published` but filtering `Job.status == status` (no expires_at filter — admin sees all pending regardless of age; Phase 6 may add expiry). City filter direct equality (canonical). Sort recentes/antigas with id tie-break.
- `get_by_id(session, job_id)` → `Job | None` (no status filter; admin can edit any).
- `approve(session, job)` → set `status = published`; commit in router. Optionally set `updated_at` via trigger (already exists).
- `update(session, job, data)` → setattr fields; flush; commit in router. Let DB CHECK raise → catch IntegrityError → 422 pt-BR "Vaga precisa ter ao menos um contato (email ou telefone)" / "Cidade inválida". Or validate in router before.
- `delete(session, job)` → `session.delete(job)`; flush; commit.

Schemas in `backend/app/schemas/job.py`:

- `JobAdmin(BaseModel)` with `model_config = ConfigDict(from_attributes=True)` and ALL fields including `contact_email`, `contact_phone`, `source_snippet`, `created_at`, `updated_at`, `expires_at`, `status`, `id`. This is the admin read surface. Contact exposure is safe because route is guarded.
- `JobUpdate(BaseModel)` with all editable fields optional? D-06 says edit all fields. Recommend required core fields (`title`, `city`) with min constraints, optional others, and `at_least_one_contact` validated via a model_validator or rely on DB CHECK. City validated against allowed set via a validator or Literal/Enum. [ASSUMED] Use `Literal["São Paulo","Rio de Janeiro","Belo Horizonte","Remoto"]` for city in `JobUpdate` to fail fast with 422 before DB.
- `JobAdminListResponse` = `{ items: list[JobAdmin], page, limit, total }`.

Approve endpoint: prefer `PATCH /admin/jobs/{id}/approve` returning `JobAdmin` (or 204). D-05 only needs status change; returning updated job lets frontend confirm. [ASSUMED] Return `JobAdmin` for consistency.

Edit endpoint: `PUT /admin/jobs/{id}` with body `JobUpdate`. Apply only provided fields (partial update) OR full replace. D-06 modal sends all fields → full replace acceptable. Recommend partial (PATCH semantics) to be safe; but simpler full PUT. [ASSUMED] Use PUT with all fields; client always sends all.

Delete: `DELETE /admin/jobs/{id}` → 204.

City resolution in admin GET: reuse `_CITY_ALIASES` logic (move to shared helper or duplicate). Admin filter by city uses canonical DB value; accept slug/canonical/label like public. [ASSUMED] Duplicate small resolver in admin router (or extract to `app/core/cities.py`). Recommend extracting to avoid drift; but keep change minimal — duplicate is fine for now. Planner decides.

### Frontend: admin Tailwind v4 shell

Create `frontend/app/admin/admin.css` mirroring `public.css` tokens (copy `@theme` block) but imported only by admin layout. Replace `globals-admin.css` usage. Create `frontend/app/admin/layout.tsx` (if not exists) importing `admin.css`, rendering shared header with logout + nav links (hub). Route group: keep `/admin/paste` and `/admin/review` under `app/admin/`.

Hub `frontend/app/admin/page.tsx`: links to paste and review; client guard redirects to login if no token. [ASSUMED] Simplest: hub page is a client component that checks token and renders links or redirects to `/admin/login`? There is no separate login route — login is inline in ExtractForm. CONTEXT D-11 says hub with links; D-14 guard redirects to login. Since login lives inside paste page, guard on review page redirects to `/admin/paste` (which shows login). [ASSUMED] Redirect unauthenticated review access to `/admin/paste`. Planner can create `/admin/login` if preferred; recommend reusing paste page as login entry.

Migrate `ExtractForm.tsx` to Tailwind classes (remove `globals-admin.css` import), preserving Turnstile widget wrapper (no transform/scale on iframe — keep overflow hidden container).

### Frontend: review queue

New `frontend/app/admin/review/page.tsx` + client component `ReviewQueue.tsx` (or `components/admin/ReviewQueue.tsx`). Pattern: client-side fetch list on mount + on filter/page change (admin is dynamic, no SSR needed; but could be server component calling backend with token from... no, token is client-only in sessionStorage → must be client fetch). Use `useEffect` + state. City filter chips (reuse BoardToolbar styling subset), pagination controls (reuse Pagination but as client buttons calling fetch), tabs for pending vs needs_review.

Job row/card in queue: title, company, city, created_at, status badge, source snippet preview? Full snippet in edit modal. Actions: Aprovar, Editar, Excluir. Optimistic: remove item from list on approve/delete; on error rollback (re-insert at original index) + toast error.

Edit modal: reuse native `<dialog>` pattern from `JobDetailDialog`. Form fields all editable. City select with 4 options. Contact at least one validation (client zod or manual). Source snippet read-only side panel (desktop: grid 2 cols sticky; mobile: accordion/details below). Submit → PUT → toast success + update item in list (or remove if status changed? edit doesn't change status). Close modal.

Toast: minimal context provider `ToastProvider` + `useToast()` hook; portal-like fixed container bottom-right; variants success/error; auto-dismiss 3s; manual close. No external lib.

Client guard: `useEffect` reads `sessionStorage.getItem("nqu_admin_token")`; if missing, `router.replace("/admin/paste")` (or login). Wrap review page and hub.

### Frontend: api helpers

Extend `frontend/lib/api.ts` with:
- `listAdminJobs(token, { status, city, page, limit })` → `{ items: JobAdmin[], page, limit, total }`
- `approveJob(token, id)` → `JobAdmin`
- `updateJob(token, id, data)` → `JobAdmin`
- `deleteJob(token, id)` → void

`JobAdmin` TS interface mirroring backend (with contact + source_snippet + timestamps). Error handling: extract `body.detail` verbatim (existing pattern).

### Optimistic updates + revalidation

Admin queue is client-fetched (no RSC). "Revalidate" = refetch current page after mutation, adjusting page if empty. Optimistic remove immediately; on error revert list + toast. For approve: remove item; if list becomes empty and page>1, go to page-1. For delete: same. For edit: update item in place (no remove). After any mutation, optionally refetch to sync totals. [ASSUMED] Refetch after success to keep total count accurate; optimistic for instant feedback.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pagination math / URL state | Custom | Reuse `Pagination` component + page/limit state | Already tested pattern |
| City alias resolution | New map | Reuse `_CITY_ALIASES` (extract to shared helper or duplicate) | Avoid drift with public |
| Auth guard | Custom middleware | `require_admin` (backend) + sessionStorage check (front) | Phase 1 decision (Bearer, no cookie) |
| Modal focus trap | Custom | Native `<dialog>` + `showModal()` (Phase 4 pattern) | Free a11y |
| Toast library | sonner/react-hot-toast | Minimal own component (D-13) | Bundle small, no dep |
| Contact validation | Custom regex | DB CHECK + Pydantic Literal city + model_validator | Single source of truth |
| Error messages | Translate | Render `body.detail` verbatim (Phase 4 rule) | Consistency |

## Runtime State Inventory

Not applicable — this is a feature phase, not a rename/refactor/migration. No runtime state to inventory. (No migrations expected; model already has all fields.)

## Common Pitfalls

### Pitfall 1: Contact leaks into public payload
**What goes wrong:** Reusing `JobPublic` (contact-free) for admin read, or accidentally serializing contact in public endpoint.
**How to avoid:** Separate `JobAdmin` schema (contact allowed) used only in admin routes; public routes keep `JobPublic`. Add test asserting `/public/jobs` has no contact fields (already exists).

### Pitfall 2: City validation mismatch (accented canonical)
**What goes wrong:** Admin edit accepts "Sao Paulo" (unaccented) and stores it; public filter uses accented canonical → zero matches.
**How to avoid:** Validate city against allowed set (accented) in `JobUpdate` via Literal or validator normalizing to canonical; reuse `_CITY_ALIASES` resolution so slug/label → canonical before persisting.

### Pitfall 3: Optimistic update without rollback
**What goes wrong:** Item removed on approve, but request fails → queue out of sync, user confused.
**How to avoid:** Keep previous list snapshot; on error restore + toast error; refetch after success.

### Pitfall 4: Tailwind Preflight leaking into admin or vice versa
**What goes wrong:** Importing `public.css` (Tailwind) in admin layout causes Preflight reset on admin; or admin keeps plain CSS and looks inconsistent.
**How to avoid:** Create separate `admin.css` with `@import "tailwindcss"` + `@theme` tokens (copy from public.css), imported only by `app/admin/layout.tsx`. Remove `globals-admin.css` import. Proven pattern from Phase 4 (Preflight isolated per route group).

### Pitfall 5: Snippet empty/null handling
**What goes wrong:** Layout breaks or shows "undefined" when source_snippet is null (older rows / discarded).
**How to avoid:** Render placeholder "Sem texto-fonte disponível" (italic/muted) in the same panel slot; don't conditionally hide panel.

### Pitfall 6: at_least_one_contact DB CHECK vs Pydantic
**What goes wrong:** Edit clears both contacts → DB raises IntegrityError → 500 instead of 422.
**How to avoid:** Catch `IntegrityError` in router and return 422 pt-BR; also add Pydantic model_validator for early 422.

### Pitfall 7: Client guard only UX, not security
**What goes wrong:** Relying on frontend redirect as security; backend still must enforce 401.
**How to avoid:** Keep `require_admin` on every admin route (already pattern); frontend guard improves UX only.

### Pitfall 8: Pagination out-of-range after deletion
**What goes wrong:** Delete last item on page 2 → page 2 empty, confusing.
**How to avoid:** After mutation, if current page has no items and page>1, decrement page and refetch.

### Pitfall 9: Edit modal not resetting on reopen
**What goes wrong:** Stale form values from previous job.
**How to avoid:** Reset form state when `job` prop changes (useEffect on job.id) or remount modal with key.

## Code Examples

### Backend: list_by_status (mirror list_published)

```python
# backend/app/crud/jobs.py
async def list_by_status(
    session: AsyncSession,
    status: JobStatus,
    page: int = 1,
    limit: int = 24,
    *,
    city: str | None = None,
    sort: str = "recentes",
) -> tuple[list[Job], int]:
    filters = [Job.status == status]
    if city:
        filters.append(Job.city == city)
    oldest_first = sort == "antigas"
    direction = Job.created_at.asc() if oldest_first else Job.created_at.desc()
    tie_break = Job.id.asc() if oldest_first else Job.id.desc()
    items_stmt = (
        select(Job).where(*filters)
        .order_by(direction, tie_break)
        .offset((page - 1) * limit).limit(limit)
    )
    count_stmt = select(func.count()).select_from(Job).where(*filters)
    items = list((await session.scalars(items_stmt)).all())
    total = int((await session.scalar(count_stmt)) or 0)
    return items, total
```

### Backend: admin router skeleton

```python
# backend/app/api/v1/admin.py (extend)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.jobs import delete_job, get_job, list_by_status, update_job, approve_job
from app.deps import require_admin, get_session
from app.models.job import JobStatus
from app.schemas.job import JobAdmin, JobAdminListResponse, JobUpdate

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/jobs", response_model=JobAdminListResponse)
async def list_jobs(
    status: str = Query("pending"),
    city: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    sort: str = Query("recentes"),
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdminListResponse:
    if status not in ("pending", "needs_review"):
        raise HTTPException(status_code=422, detail="Status inválido")
    resolved_city = _resolve_city(city)  # reuse alias map
    items, total = await list_by_status(session, JobStatus(status), page, limit, city=resolved_city, sort=sort)
    return JobAdminListResponse(items=[JobAdmin.model_validate(j) for j in items], page=page, limit=limit, total=total)

@router.patch("/jobs/{job_id}/approve", response_model=JobAdmin)
async def approve(job_id: uuid.UUID, session=Depends(get_session), claims=Depends(require_admin)):
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    await approve_job(session, job)
    await session.commit()
    await session.refresh(job)
    return JobAdmin.model_validate(job)

@router.put("/jobs/{job_id}", response_model=JobAdmin)
async def update(job_id: uuid.UUID, payload: JobUpdate, session=Depends(get_session), claims=Depends(require_admin)):
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    try:
        await update_job(session, job, payload)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=422, detail="Vaga precisa ter ao menos um contato (email ou telefone)")
    await session.refresh(job)
    return JobAdmin.model_validate(job)

@router.delete("/jobs/{job_id}", status_code=204)
async def delete(job_id: uuid.UUID, session=Depends(get_session), claims=Depends(require_admin)):
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    await delete_job(session, job)
    await session.commit()
```

### Frontend: JobAdmin type + api helpers

```typescript
// frontend/lib/api.ts (add)
export interface JobAdmin {
  id: string;
  title: string;
  company: string | null;
  activities: string | null;
  requirements: string | null;
  salary: string | null;
  benefits: string | null;
  city: string;
  status: JobStatus;
  contact_email: string | null;
  contact_phone: string | null;
  source_snippet: string | null;
  created_at: string;
  updated_at: string;
  expires_at: string;
}
export interface JobAdminListResponse { items: JobAdmin[]; page: number; limit: number; total: number; }

export async function listAdminJobs(token, params) { ... }
export async function approveJob(token, id) { ... }
export async function updateJob(token, id, data) { ... }
export async function deleteJob(token, id) { ... }
```

### Frontend: toast (minimal)

```tsx
// components/admin/ToastProvider.tsx
"use client";
import { createContext, useCallback, useContext, useState } from "react";

type Toast = { id: number; message: string; variant: "success" | "error" };
const ToastCtx = createContext<{ toast: (msg: string, variant?: "success"|"error") => void } | null>(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toast = useCallback((message, variant = "success") => {
    const id = Date.now();
    setToasts((t) => [...t, { id, message, variant }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3000);
  }, []);
  return (
    <ToastCtx.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <div key={t.id} className={t.variant === "success" ? "..." : "..."}>{t.message}</div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
export const useToast = () => useContext(ToastCtx)!;
```

### Frontend: client guard

```tsx
"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export function useAdminGuard() {
  const router = useRouter();
  useEffect(() => {
    const t = window.sessionStorage.getItem("nqu_admin_token");
    if (!t) router.replace("/admin/paste");
  }, [router]);
}
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-asyncio 1.4.0 (backend); Vitest (frontend, optional) |
| Config file | `backend/pyproject.toml` (asyncio_mode=auto) |
| Quick run command | `cd backend; .venv\Scripts\python.exe -m pytest -q` |
| Full suite command | `cd backend; .venv\Scripts\python.exe -m pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REVW-01 | GET /admin/jobs lists pending, city filter, pagination | integration | `pytest tests/test_admin_jobs.py::test_list_pending -x` | ❌ Wave 0 |
| REVW-01 | GET /admin/jobs?status=needs_review | integration | `pytest tests/test_admin_jobs.py::test_list_needs_review -x` | ❌ Wave 0 |
| REVW-02 | PATCH /admin/jobs/{id}/approve → published | integration | `pytest tests/test_admin_jobs.py::test_approve -x` | ❌ Wave 0 |
| REVW-02 | Approve non-existent → 404 | integration | `pytest tests/test_admin_jobs.py::test_approve_404 -x` | ❌ Wave 0 |
| REVW-03 | PUT /admin/jobs/{id} updates fields | integration | `pytest tests/test_admin_jobs.py::test_update -x` | ❌ Wave 0 |
| REVW-03 | Update clearing contacts → 422 | integration | `pytest tests/test_admin_jobs.py::test_update_no_contact_422 -x` | ❌ Wave 0 |
| REVW-03 | Update invalid city → 422 | integration | `pytest tests/test_admin_jobs.py::test_update_bad_city_422 -x` | ❌ Wave 0 |
| REVW-04 | DELETE /admin/jobs/{id} hard delete | integration | `pytest tests/test_admin_jobs.py::test_delete -x` | ❌ Wave 0 |
| REVW-04 | Delete non-existent → 404 | integration | `pytest tests/test_admin_jobs.py::test_delete_404 -x` | ❌ Wave 0 |
| REVW-05 | JobAdmin includes source_snippet + contact | integration | `pytest tests/test_admin_jobs.py::test_schema_includes_snippet_contact -x` | ❌ Wave 0 |
| (auth) | All admin job routes reject unauthenticated (401) | integration | `pytest tests/test_admin_jobs.py::test_requires_auth -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend; .venv\Scripts\python.exe -m pytest -q`
- **Per wave merge:** `cd backend; .venv\Scripts\python.exe -m pytest -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_admin_jobs.py` — new test file covering REVW-01..05 + auth gate
- [ ] Reuse existing fixtures (client, db_session, admin_password, fake_turnstile) from conftest
- [ ] No new framework install needed
- [ ] Frontend: optional Vitest smoke for toast/guard; not required for phase gate (backend suite is authority)

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PostgreSQL (Neon test branch) | Backend tests | ✓ | managed | skip suite if no DB |
| Python venv | Backend | ✓ | 3.11/3.13 | — |
| Node.js | Frontend build | ✓ | 18+ | — |
| Cloudflare Turnstile (test keys) | Login flow | ✓ (dev) | public test keys | empty → dev mode |

No new external dependencies for this phase.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | `require_admin` Bearer JWT on every admin route (existing) |
| V3 Session Management | yes | JWT 12h, no refresh, sessionStorage on client (Phase 1) |
| V4 Access Control | yes | Admin-only mutations behind `require_admin`; unauthenticated → 401 |
| V5 Input Validation | yes | Pydantic `JobUpdate` + Literal city + model_validator at_least_one_contact; DB CHECK backstop |
| V6 Cryptography | no new | Reuse existing bcrypt/JWT |

### Known Threat Patterns for FastAPI/Next.js Admin Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Contact leak via admin schema in public route | Information disclosure | Separate `JobAdmin` vs `JobPublic`; public routes only `JobPublic` |
| Unauthenticated mutation | Elevation of privilege | `require_admin` on every route; test 401 |
| City injection / SQL injection | Tampering | Parameterized queries (SQLAlchemy); Literal validation |
| Stale token / session fixation | Spoofing | JWT exp; sessionStorage cleared on logout |
| Optimistic UI desync | Tampering (integrity) | Rollback + refetch |

## Open Questions

1. **Approve endpoint shape** — PATCH vs POST vs dedicated `/approve`. Recommendation: PATCH `/admin/jobs/{id}/approve`. Planner decides; keep consistent with REST conventions in codebase (POST used for extract/login).
2. **Edit semantics** — full PUT vs partial PATCH. Recommendation: PUT with all fields (modal always sends all). Planner decides.
3. **needs_review tab** — separate route `/admin/review/needs-review` vs client tab. CONTEXT allows discretion; recommendation: client-side tab on `/admin/review` (simpler, single fetch state). 
4. **Admin layout location** — `app/admin/layout.tsx` vs `app/(admin)/`. Recommendation: `app/admin/layout.tsx` (preserves existing `/admin/paste` URL).
5. **zod on frontend** — add dependency or manual validation. Recommendation: manual (small form) to avoid new dep; zod if planner prefers.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | No new backend dependencies needed | Standard Stack | Low — all mutations use existing libs |
| A2 | No Alembic migration needed (model complete) | Standard Stack | Low — verified model has all fields + source_snippet |
| A3 | Admin edit uses PUT with all fields | Architecture | Medium — partial PATCH would be safer; modal sends all anyway |
| A4 | Redirect unauthenticated review to `/admin/paste` | Architecture | Low — login lives there; could create dedicated login route |
| A5 | zod optional on frontend | Standard Stack | Low — manual validation acceptable |
| A6 | `list_by_status` does not filter expires_at | Architecture | Medium — Phase 6 may require expiry for pending; revisit then |

## Sources

### Primary (HIGH confidence)
- Codebase: `backend/app/api/v1/admin.py`, `extract.py`, `public.py`, `crud/jobs.py`, `models/job.py`, `schemas/job.py`, `deps.py`, `main.py`, `router.py`
- Codebase: `frontend/app/admin/paste/ExtractForm.tsx`, `frontend/lib/api.ts`, `frontend/components/board/*`, `frontend/app/(public)/public.css`, `frontend/app/(public)/page.tsx`
- `.planning/phases/05-admin-review-area/05-CONTEXT.md` (locked decisions D-01..D-14)
- `.planning/REQUIREMENTS.md` (REVW-01..05)
- `.planning/research/STACK.md` (versions)
- `.planning/research/PITFALLS.md` (Pitfall 3 grounding, Pitfall 7 contact protection)

### Secondary (MEDIUM confidence)
- Phase 4 patterns (Tailwind v4 route-group isolation, native dialog, Pagination, BoardToolbar city chips)

### Tertiary (LOW confidence)
- None — all claims verified against codebase or prior phase research.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — reuse existing, no new deps
- Architecture: HIGH — mirrors established public-board + extract patterns
- Pitfalls: HIGH — derived from codebase constraints + prior phase decisions

**Research date:** 2026-10-27
**Valid until:** 2026-11-27 (30 days; stack stable)

## RESEARCH COMPLETE