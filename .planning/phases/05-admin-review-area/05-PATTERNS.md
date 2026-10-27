# Phase 05: Admin Review Area - Pattern Map

**Mapped:** 2026-10-27  
**Files analyzed:** 24 artifacts (backend + frontend, new + modified)  
**Analogs found:** 22 / 24 (2 with no close analog: `frontend/app/admin/admin.css` Tailwind v4 route-scoped shell — copied from `public.css`, and `frontend/components/admin/ToastProvider.tsx` — new pattern)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/crud/jobs.py` (modify) | service (CRUD) | CRUD | `backend/app/crud/jobs.py` (self — `list_published`) | exact (extend) |
| `backend/app/api/v1/admin.py` (modify) | route/controller | request-response | `backend/app/api/v1/extract.py` + `public.py` | exact (extend) |
| `backend/app/schemas/job.py` (modify) | model/schema | N/A | `backend/app/schemas/job.py` (`JobPublic`) | exact (extend) |
| `backend/tests/test_admin_jobs.py` (new) | test | N/A | `backend/tests/test_public_api.py` + `conftest.py` | role-match |
| `frontend/app/admin/admin.css` (new) | style/config | N/A | `frontend/app/(public)/public.css` | exact (copy tokens) |
| `frontend/app/admin/layout.tsx` (new) | layout/RSC | N/A | `frontend/app/(public)/layout.tsx` | exact (adapt) |
| `frontend/app/admin/page.tsx` (new) | page (hub) | request-response (client) | `frontend/app/admin/paste/page.tsx` | role-match |
| `frontend/app/admin/review/page.tsx` (new) | page (client) | request-response | `frontend/app/admin/paste/page.tsx` | role-match |
| `frontend/app/admin/review/ReviewQueue.tsx` (new) | component/client | request-response | `frontend/components/board/JobGrid.tsx` + `BoardToolbar.tsx` | role-match |
| `frontend/app/admin/review/EditJobDialog.tsx` (new) | component/client | request-response | `frontend/components/board/JobDetailDialog.tsx` | exact (adapt) |
| `frontend/app/admin/review/DeleteConfirmDialog.tsx` (new) | component/client | request-response | `frontend/components/board/JobDetailDialog.tsx` (native `<dialog>`) | role-match |
| `frontend/app/admin/paste/page.tsx` (modify) | page/RSC | N/A | self (modify) | exact (modify) |
| `frontend/app/admin/paste/ExtractForm.tsx` (modify) | component/client | request-response | self (migrate to Tailwind) | exact (modify) |
| `frontend/app/admin/paste/globals-admin.css` (remove) | style | N/A | — | removed |
| `frontend/components/admin/ToastProvider.tsx` (new) | component/client (provider) | event-driven (context) | **no analog** | — |
| `frontend/components/admin/AdminGuard.tsx` (new) | hook/component | request-response | `frontend/app/admin/paste/ExtractForm.tsx` (sessionStorage read) | role-match |
| `frontend/components/admin/ReviewRow.tsx` (new) | component/client | request-response | `frontend/components/board/JobCard.tsx` | role-match |
| `frontend/components/admin/CityChips.tsx` (new) | component/client | request-response | `frontend/components/board/BoardToolbar.tsx` (city chips) | exact (reuse) |
| `frontend/components/admin/icons.tsx` (new) | component (icons) | N/A | `frontend/components/board/icons.tsx` | exact (extend style) |
| `frontend/lib/api.ts` (modify) | utility/service | request-response | self (extend) | exact (extend) |
| `frontend/lib/cities.ts` (reuse) | utility | N/A | self | reference |
| `frontend/lib/format.ts` (reuse) | utility | N/A | self | reference |

## Pattern Assignments

### Backend: Modify `backend/app/crud/jobs.py` (service, CRUD)

**Analog:** `backend/app/crud/jobs.py` — `list_published` (lines 48-86), `_published_filters` (lines 22-45)

**Imports pattern** (lines 1-8):
```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
```

**Core CRUD pattern** (lines 48-86) — mirror for `list_by_status`:
```python
async def list_published(
    session: AsyncSession,
    page: int = 1,
    limit: int = 20,
    *,
    q: str | None = None,
    city: str | None = None,
    sort: str = "recentes",
) -> tuple[list[Job], int]:
    filters = _published_filters(q=q, city=city)
    oldest_first = sort == "antigas"
    direction = Job.created_at.asc() if oldest_first else Job.created_at.desc()
    tie_break = Job.id.asc() if oldest_first else Job.id.desc()

    items_stmt = (
        select(Job)
        .where(*filters)
        .order_by(direction, tie_break)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    count_stmt = select(func.count()).select_from(Job).where(*filters)

    items = list((await session.scalars(items_stmt)).all())
    total = int((await session.scalar(count_stmt)) or 0)
    return items, total
```

**Conventions to copy:**
- Build filter list once and reuse for both items query and count query (ensures `total` consistency).
- Order by `created_at` with `id` tie-breaker (D-06a) — rows inserted in one transaction share `created_at`.
- Return `(items: list[Job], total: int)`; cast count with `or 0` then `int()`.
- `get_published` (lines 89-96) pattern for single-row lookup:
```python
async def get_published(session: AsyncSession, job_id: uuid.UUID) -> Job | None:
    stmt = select(Job).where(
        Job.id == job_id,
        Job.status == JobStatus.published,
        Job.expires_at > func.now(),
    )
    return await session.scalar(stmt)
```
- `bulk_create_pending` (lines 99-126) pattern for write helpers: only `flush()` (caller owns transaction/commit); add to `session`, flush, return.

**What must differ for Phase 5:**
- Add `list_by_status(session, status, page, limit, *, city, sort)` filtering `Job.status == status` (NO `expires_at` filter — admin sees all pending regardless of age; A6).
- Add `get_job(session, job_id)` → `Job | None` (no status filter; admin can edit any).
- Add `approve_job(session, job)` → set `status = JobStatus.published`; flush.
- Add `update_job(session, job, data)` → setattr fields from `JobUpdate`; flush; let DB CHECK raise `IntegrityError` (caught in router).
- Add `delete_job(session, job)` → `session.delete(job)`; flush.
- Update `__all__` to include new helpers.

---

### Backend: Modify `backend/app/api/v1/admin.py` (route/controller, request-response)

**Analog:** `backend/app/api/v1/extract.py` (lines 15-60) for router skeleton + auth deps + pt-BR errors; `backend/app/api/v1/public.py` (lines 24-45) for `_CITY_ALIASES` / `_resolve_city` / `_resolve_sort`.

**Imports pattern** (extract.py lines 15-36):
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.crud.jobs import bulk_create_pending
from app.db.session import get_session
from app.deps import require_admin
from app.models.job import JobStatus
from app.schemas.extract import ExtractRequest, ExtractSummaryResponse
```

**Auth/guard pattern** (extract.py lines 49-53):
```python
@router.post("/extract", response_model=ExtractSummaryResponse)
async def extract_admin(
    payload: ExtractRequest,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> ExtractSummaryResponse:
```

**Router setup** (admin.py lines 5-7, extract.py line 37):
```python
router = APIRouter(prefix="/admin", tags=["admin"])
```

**Error handling pattern** (extract.py lines 56-84) — pt-BR `detail`, HTTPException with status_code:
```python
if not settings.GROQ_API_KEY:
    raise HTTPException(
        status_code=503,
        detail="Serviço de extração indisponível — GROQ_API_KEY não configurado.",
    )
```

**City alias resolution** (public.py lines 28-49) — reuse for admin GET filter and JobUpdate normalization:
```python
_CITY_ALIASES: dict[str, str] = {
    "sao-paulo": "São Paulo",
    "sao paulo": "São Paulo",
    "são paulo": "São Paulo",
    "rio-de-janeiro": "Rio de Janeiro",
    "rio de janeiro": "Rio de Janeiro",
    "belo-horizonte": "Belo Horizonte",
    "belo horizonte": "Belo Horizonte",
    "remoto": "Remoto",
}

def _resolve_city(value: str | None) -> str | None:
    if not value:
        return None
    return _CITY_ALIASES.get(value.strip().lower())
```

**CRUD call + commit pattern** (extract.py lines 103-112) — single transaction per mutation:
```python
if rows:
    try:
        await bulk_create_pending(session, rows)
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Falha ao salvar — nada foi gravado, tente novamente",
        ) from exc
```

**Conventions to copy for new review routes:**
- Mount under existing `admin.router` (prefix `/admin`, already registered in `router.py` — no router.py change needed).
- Thin router → crud → schemas; `Depends(require_admin)`, `Depends(get_session)`; pt-BR `detail`; commit in router.
- Status validation: `if status not in ("pending", "needs_review"): raise HTTPException(422, detail="Status inválido")`.
- IntegrityError handling for edit (Pitfall 6):
```python
from sqlalchemy.exc import IntegrityError
try:
    await update_job(session, job, payload)
    await session.commit()
except IntegrityError:
    await session.rollback()
    raise HTTPException(status_code=422, detail="Vaga precisa ter ao menos um contato (email ou telefone)")
```
- 404 pattern: `if job is None: raise HTTPException(status_code=404, detail="Vaga não encontrada")`.
- Return `JobAdmin.model_validate(job)`; approve returns updated job.

**Proposed endpoints (research §Architecture):**
- `GET /admin/jobs` (status default pending, city, page, limit default 24, sort)
- `PATCH /admin/jobs/{id}/approve` → `JobAdmin`
- `PUT /admin/jobs/{id}` with `JobUpdate` → `JobAdmin`
- `DELETE /admin/jobs/{id}` → 204

---

### Backend: Modify `backend/app/schemas/job.py` (model/schema, N/A)

**Analog:** `backend/app/schemas/job.py` — `JobPublic` (lines 24-40), `JobListResponse` (lines 43-49), `ContactRevealResponse` (lines 63-78)

**Imports pattern** (lines 16-22):
```python
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus
```

**Schema pattern with from_attributes** (lines 24-40):
```python
class JobPublic(BaseModel):
    """A published, non-expired job with NO contact fields (D-15, D-18)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str | None = None
    activities: str | None = None
    requirements: str | None = None
    salary: str | None = None
    benefits: str | None = None
    city: str
    status: JobStatus
    created_at: datetime
    expires_at: datetime
    # NO contact_email / contact_phone (D-18).
```

**Conventions to copy:**
- `model_config = ConfigDict(from_attributes=True)` for ORM mapping.
- Field defaults with `= None` for optional text fields.
- `Field(min_length=1, max_length=...)` for constrained strings (see `RevealRequest`, lines 52-58).

**What must differ for Phase 5:**
- Add `JobAdmin(BaseModel)` exposing ALL fields including `contact_email`, `contact_phone`, `source_snippet`, `updated_at`, `expires_at` (contact allowed only behind `require_admin` — Pitfall 1).
- Add `JobUpdate(BaseModel)` with editable fields; `title`/`city` required; city validated via `Literal["São Paulo","Rio de Janeiro","Belo Horizonte","Remoto"]` (or model_validator normalizing slug/label → canonical, Pitfall 2); `at_least_one_contact` via model_validator (or rely on DB CHECK + router catch).
- Add `JobAdminListResponse = { items: list[JobAdmin], page, limit, total }` (mirror `JobListResponse`).

---

### Backend: New `backend/tests/test_admin_jobs.py` (test)

**Analog:** `backend/tests/test_public_api.py` (read for test shape) + `backend/tests/conftest.py` fixtures.

**From conftest.py — fixtures to reuse** (lines 162-290):
```python
@pytest.fixture
def admin_password() -> str:
    return TEST_ADMIN_PASSWORD

@pytest.fixture
async def client(app): ...  # AsyncClient over ASGI

@pytest.fixture
async def db_session(engine): ...  # rolled-back transaction, jobs cleared

@pytest.fixture
async def seed_pending_job(db_session) -> Job: ...  # status=pending
```

**Test pattern** (from 04-PATTERNS test section):
```python
async def test_list_returns_only_published_non_expired(
    client, seed_published_job, seed_pending_job, seed_expired_job
):
    resp = await client.get("/api/v1/public/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(seed_published_job.id)
```

**Auth header pattern** (Phase 1/3 — login to get token):
```python
# Login: POST /api/v1/auth/login with {password, cf_token}
# Then Authorization: Bearer <token>
```

**Conventions to copy:**
- Async tests with `asyncio_mode = "auto"` (pyproject.toml).
- Use fixtures from conftest; tests run in rolled-back transactions (no commit).
- Assert on response structure matching `JobAdminListResponse`.
- Render `body.detail` verbatim expectation for error cases.
- Test 401 for unauthenticated access to all admin job routes.

**What to test (research §Validation Architecture):**
- `test_list_pending`, `test_list_needs_review` (status filter)
- city filter + pagination
- `test_approve` (→ published), `test_approve_404`
- `test_update` (fields), `test_update_no_contact_422`, `test_update_bad_city_422`
- `test_delete`, `test_delete_404`
- `test_schema_includes_snippet_contact` (JobAdmin includes source_snippet + contact)
- `test_requires_auth` (401 on all routes)

---

### Frontend: New `frontend/app/admin/admin.css` (style/config)

**Analog:** `frontend/app/(public)/public.css` (lines 1-107) — copy `@theme` block verbatim.

**Pattern** (public.css lines 1-24):
```css
@import "tailwindcss";

@theme {
  --color-canvas: #0f0a1a; /* 60% — page background */
  --color-surface: #1a1025; /* 30% — cards, dialog */
  --color-line: #2a1f3d; /* decorative card/dialog border */
  --color-line-strong: #6d5a91; /* control border (input, secondary button, chip) — 3.26:1 */
  --color-fg: #e2e8f0;
  --color-fg-muted: #b8a9cc;
  --color-accent: #8b5cf6; /* brand: borders/hover/indicator */
  --color-accent-soft: #a78bfa; /* accent TEXT + focus ring */
  --color-accent-strong: #7c3aed; /* filled CTA with white text (5.70:1) */
  --color-accent-strong-hover: #6d28d9;
  --color-donate: #facc15;
  --color-danger: #f87171;
  --color-danger-soft: #fecaca;
  --radius-card: 12px;
  --radius-dialog: 16px;
}
```

**Conventions to copy:**
- `@import "tailwindcss";` first (CSS-first v4).
- `@theme` for design tokens.
- `@layer base` for `html { color-scheme: dark; }`, body background/color, focus-visible ring, reduced-motion.
- `@layer components` for dialog::backdrop, dialog radius, job-card hover (as in public.css lines 64-107).
- Import ONLY in `app/admin/layout.tsx` (Pitfall 4 — Preflight isolation).

**What must differ:** Drop `--color-donate` usage in admin (donations button not shown); keep token for parity. Add admin-specific component classes if needed (toast, etc.) but prefer Tailwind utilities.

---

### Frontend: New `frontend/app/admin/layout.tsx` (layout/RSC)

**Analog:** `frontend/app/(public)/layout.tsx` (lines 1-66).

**Imports pattern** (public layout lines 1-4):
```tsx
import type { Metadata, Viewport } from "next";
import Link from "next/link";

import "./public.css";
```

**Layout shell pattern** (public layout lines 16-65):
```tsx
export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas text-fg">
      <header className="sticky top-0 z-40 border-b border-line bg-canvas">
        <div className="mx-auto flex h-16 w-full max-w-[1120px] items-center justify-between gap-4 px-4 md:px-6">
          ...
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1120px] flex-1 px-4 py-8 md:px-6">
        {children}
      </main>
    </div>
  );
}
```

**Conventions to copy:**
- Import `./admin.css` (not public.css).
- Header admin: wordmark `NaoQueroUsar · Painel admin` (Heading 20/600) + `Sair` ghost button (h44) on right (UI-SPEC §H).
- No "Doações" button, no ADS (admin is not vitrine).
- Wrap children with `ToastProvider` (client) — needs a client wrapper component or `"use client"` boundary. Since layout is RSC, wrap `{children}` in a client `ToastProvider` component.
- Metadata: title `NaoQueroUsar — Painel admin`, description `Área restrita de curadoria de vagas.`

**What must differ:**
- Add guard is applied per-page (hub + review), not in layout (paste is login entry).
- `ToastProvider` must be a client component imported into RSC layout (allowed: RSC can render client components).

---

### Frontend: New `frontend/app/admin/page.tsx` (hub, client guard)

**Analog:** `frontend/app/admin/paste/page.tsx` (lines 1-9) for minimal RSC shape; guard pattern from `ExtractForm.tsx` (lines 29-38) for sessionStorage read.

**Page pattern** (paste/page.tsx):
```tsx
export default async function Page() {
  const { default: ExtractForm } = await import("./ExtractForm");
  return (
    <main>
      <h1>Admin — Colar vagas</h1>
      <ExtractForm />
    </main>
  );
}
```

**Guard pattern** (ExtractForm.tsx lines 29-38):
```tsx
useEffect(() => {
  try {
    const stored = window.sessionStorage.getItem(TOKEN_KEY);
    if (stored) {
      setToken(stored);
    }
  } catch {
    // ignore storage errors
  }
}, []);
```

**Conventions to copy:**
- Hub cards are `<Link>` to `/admin/paste` and `/admin/review` with descriptive aria-label (UI-SPEC §A).
- `useAdminGuard()` hook: reads `nqu_admin_token`; if missing, `router.replace("/admin/paste")`.
- Logout: remove `nqu_admin_token` from sessionStorage, redirect to `/admin/paste`.

---

### Frontend: New `frontend/app/admin/review/page.tsx` + `ReviewQueue.tsx`

**Analog:** `frontend/app/admin/paste/page.tsx` (RSC shell) + `frontend/components/board/JobGrid.tsx` (client state/dialog ownership) + `BoardToolbar.tsx` (city chips, pagination).

**Client component pattern** (JobGrid.tsx lines 44-64):
```tsx
export function JobGrid({ jobs, initialJob }: JobGridProps) {
  const [selected, setSelected] = useState<JobPublic | null>(
    initialJob ?? null,
  );
  const triggerRef = useRef<HTMLElement | null>(null);

  const handleOpen = (job: JobPublic, trigger: HTMLElement | null) => {
    triggerRef.current = trigger;
    setSelected(job);
    syncVagaParam(job.id);
  };
  ...
}
```

**City chips pattern** (BoardToolbar.tsx lines 151-186):
```tsx
<div role="group" aria-label="Filtrar por cidade" className="-mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] sm:mx-0 sm:flex-wrap sm:overflow-visible">
  <button type="button" aria-pressed={filters.city === null} onClick={() => commit({ city: null })}
    className={filters.city === null ? "min-h-11 shrink-0 rounded-full bg-accent-strong px-4 text-sm font-semibold text-white" : "min-h-11 shrink-0 rounded-full border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft"}>
    Todas
  </button>
  {CITY_OPTIONS.map((option) => {
    const active = filters.city === option.slug;
    return (
      <button key={option.slug} type="button" aria-pressed={active} onClick={() => commit({ city: option.slug })}
        className={active ? "min-h-11 shrink-0 rounded-full bg-accent-strong px-4 text-sm font-semibold text-white" : "min-h-11 shrink-0 rounded-full border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft"}>
        {option.label}
      </button>
    );
  })}
</div>
```

**Pagination pattern** (Pagination.tsx lines 20-67) — adapt to client buttons (onClick, not Link):
```tsx
<nav aria-label="Paginação" className="mt-8 flex items-center justify-between gap-4">
  {prevHref ? (<Link href={prevHref} aria-label="Página anterior" className={...}>Anterior</Link>) : (<span aria-disabled="true" className={...}>Anterior</span>)}
  <span className="text-sm text-fg-muted">Página {page} de {totalPages}</span>
  ...
</nav>
```

**Conventions to copy:**
- Admin is client-fetched (token in sessionStorage) → `useEffect` + state, no RSC fetch.
- Tabs client-side for pending vs needs_review (UI-SPEC §B): `role="tablist"`/`role="tab"`/`aria-selected`.
- City filter chips reuse BoardToolbar pattern (single-select + `Todas`).
- Pagination controls with onClick (not Link) since admin is client-fetched (UI-SPEC §Interaction Contract D4).
- Skeleton: 6 placeholder rows with `animate-pulse` (disabled under reduced-motion), `aria-busy="true"` + sr-only "Carregando fila".
- Optimistic remove + rollback + refetch (Pitfalls 3, 8).
- Empty states + error panel copy from UI-SPEC §Copywriting.

---

### Frontend: New `frontend/app/admin/review/EditJobDialog.tsx`

**Analog:** `frontend/components/board/JobDetailDialog.tsx` (lines 42-156) — native `<dialog>` + `showModal()` + focus trap + scroll lock + backdrop close.

**Native dialog pattern** (JobDetailDialog.tsx lines 42-97):
```tsx
export function JobDetailDialog({ job, open, onClose }: JobDetailDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const close = () => dialogRef.current?.close();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      dialog.focus();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const root = document.documentElement;
    const previous = root.style.overflow;
    root.style.overflow = "hidden";
    return () => { root.style.overflow = previous; };
  }, [open]);

  return (
    <dialog ref={dialogRef} tabIndex={-1} aria-labelledby={titleId} onClose={onClose}
      onClick={(event) => { if (event.target === dialogRef.current) dialogRef.current?.close(); }}
      className="mb-0 mt-auto max-h-[92dvh] w-full max-w-none flex-col overflow-hidden rounded-t-[16px] border-0 bg-surface p-0 ...">
      ...
    </dialog>
  );
}
```

**Conventions to copy:**
- `useRef<HTMLDialogElement>`, `showModal()`, `close()`.
- `onClose` callback for ESC/backdrop.
- Scroll lock on document root.
- Focus restoration to trigger element after close (requestAnimationFrame).
- Mobile bottom sheet (mb-0 mt-auto, rounded-t) vs desktop centered (sm:mb-auto sm:rounded).

**What must differ for Phase 5:**
- Form with all editable fields (title, company, activities, requirements, salary, benefits, city select, contact_email, contact_phone).
- City select with 4 options (São Paulo, Rio de Janeiro, Belo Horizonte, Remoto).
- Source snippet read-only side panel: desktop grid 2 cols (form left, snippet right sticky 320px); mobile accordion (`<details>` below form, closed by default, summary "Texto-fonte").
- Snippet placeholder "Sem texto-fonte disponível" (italic, muted) when null/empty (Pitfall 5).
- Validation manual (no zod): title required, city in set, at least one contact, email valid if filled, phone digits if filled; inline errors `#f87171` Label 14.
- Reset form state when `job.id` changes (Pitfall 9).
- Block close while saving (disable X/ESC/backdrop).
- Submit → PUT → toast success + update item in place + close; 422 → toast error with body.detail, modal stays open.

---

### Frontend: New `frontend/app/admin/review/DeleteConfirmDialog.tsx`

**Analog:** `frontend/components/board/JobDetailDialog.tsx` (native `<dialog>` pattern, lines 47-97) — reuse showModal/close/scroll-lock.

**Conventions to copy:**
- Native `<dialog>`, `max-width: 480px`, centered all breakpoints (not bottom sheet).
- Title `Excluir esta vaga?` (Heading 20/600) + body + footer `Cancelar` (secondary) + `Excluir vaga` (destructive).
- During delete: destructive button shows `Excluindo...` and disabled; Cancelar disabled; ESC/backdrop close only if not deleting.

---

### Frontend: Modify `frontend/app/admin/paste/page.tsx` + `ExtractForm.tsx`

**Analog:** self (modify). New layout provides header/shell.

**Current ExtractForm imports** (lines 1-6):
```tsx
"use client";

import { useEffect, useState } from "react";
import { Turnstile } from "next-turnstile";
import { loginAdmin, extractJobs, type ExtractSummary } from "@/lib/api";
import "./globals-admin.css";
```

**Conventions to copy (keep):**
- `"use client"` directive.
- `TOKEN_KEY = "nqu_admin_token"` in sessionStorage (lines 8, 29-38).
- Turnstile reset by remount with key (lines 43-46) — `key={turnstileKey}`.
- Error handling extracting message from Error instance (lines 60-70, 80-86).
- Turnstile wrapper `overflow: hidden; max-width: 100%` (globals-admin.css lines 60-66) — keep as Tailwind `overflow-hidden max-w-full` (Pitfall: never transform/scale iframe).

**What must differ:**
- Remove `import "./globals-admin.css";` → use Tailwind classes with admin.css tokens.
- Migrate all `.admin-*` class usages to Tailwind utilities (container max-w-[720px], bg-surface, border-line, etc.).
- Keep behavior: login with Turnstile `interaction-only`, `action="login"`, token in sessionStorage, extraction, alerts/discards.

---

### Frontend: New `frontend/components/admin/ToastProvider.tsx`

**Analog:** **no analog** — new pattern (research §Code Examples).

**Pattern (research lines 342-371):**
```tsx
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

**Conventions to copy (UI-SPEC §E):**
- Container: `bottom-16 right-4` (desktop ≥640) / `bottom-4 left-4 right-4` (mobile <640), `z-50`, `flex flex-col gap-2`, max-width 360px.
- Toast: `bg-surface`, border 1px line, radius 8px, padding 12px 16px, shadow `0 8px 24px rgba(0,0,0,.4)`. Left border 4px colored by variant (success `#7c3aed`, error `#f87171`).
- Icon 16px left, message Body 14/400, close button `×` ghost right (aria-label `Fechar notificação`).
- Auto-dismiss 3000ms; hover pauses timer; multiple toasts stack (max 3 visible, oldest removed).
- Slide-in from bottom + fade 150ms ease-out; respect reduced-motion.
- Wrap in `app/admin/layout.tsx` (RSC renders client provider).

---

### Frontend: New `frontend/components/admin/AdminGuard.tsx` (or hook `useAdminGuard`)

**Analog:** `frontend/app/admin/paste/ExtractForm.tsx` lines 29-38 (sessionStorage read) + research §Code Examples (lines 373-387).

**Guard pattern** (research):
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

**Conventions to copy:**
- Applied in `/admin` (hub) and `/admin/review`. NOT in `/admin/paste` (login entry).
- Silent redirect (no "acesso negado" copy).
- Backend remains authoritative (`require_admin` → 401).

---

### Frontend: New `frontend/components/admin/ReviewRow.tsx`

**Analog:** `frontend/components/board/JobCard.tsx` (lines 26-101) — card with title, company, city, salary, date, action button.

**Card pattern** (JobCard.tsx lines 37-101):
```tsx
<article className="flex h-full flex-col gap-3 rounded-[12px] border border-line bg-surface p-4 transition-colors hover:border-accent focus-within:border-accent">
  {company ? (<p className="text-sm text-fg-muted [overflow-wrap:anywhere]">{company}</p>) : null}
  <h2 className="line-clamp-2 text-xl font-semibold leading-tight [overflow-wrap:anywhere] [text-wrap:balance]">{job.title}</h2>
  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-fg-muted">
    <span className="inline-flex items-center gap-1"><MapPin size={16} />{cityLabel(job.city)}</span>
    {salary ? (<span>Salário: <span className="font-semibold text-fg">{salary}</span></span>) : null}
  </div>
  <p className="text-sm text-fg-muted">Publicada em {formatDateBR(job.created_at)}</p>
  <div className="mt-auto pt-1">
    <button type="button" onClick={(event) => onOpen(job, event.currentTarget)} aria-label={`Ver a vaga: ${job.title}`} className="...">
      Ver a vaga
    </button>
  </div>
</article>
```

**Conventions to copy:**
- Tailwind classes with tokens (`bg-surface`, `border-line`, `text-fg`, `text-fg-muted`, `text-accent-soft`).
- `cityLabel` from `@/lib/cities`, `formatDateBR` from `@/lib/format`.
- Action buttons h44 min touch target.

**What must differ for Phase 5:**
- Status badge pill: `#a78bfa` text on `rgba(139,92,246,.12)`, radius 999px, Label 14/400.
- Actions: `Aprovar` (primary filled `#7c3aed`), `Editar` (secondary outline), `Excluir` (destructive outline `#f87171`).
- Loading state: row `opacity: .6; pointer-events: none` + spinner 16px in triggered button; button text `Aprovando...`/`Excluindo...`.
- Optimistic remove on approve/delete; rollback + toast on error.

---

### Frontend: New `frontend/components/admin/CityChips.tsx`

**Analog:** `frontend/components/board/BoardToolbar.tsx` lines 151-186 (city chips) — copy pattern verbatim (single-select + `Todas`, `aria-pressed`, horizontal scroll mobile).

---

### Frontend: New `frontend/components/admin/icons.tsx`

**Analog:** `frontend/components/board/icons.tsx` — reuse existing icons (MapPin, X) and add admin icons (check, pencil, trash, logout, plus, x, chevron-down) as inline SVGs 20px (16px inline), `stroke-width: 1.75`, `currentColor` (UI-SPEC §Design System).

---

### Frontend: Modify `frontend/lib/api.ts`

**Analog:** self (extend). Follow existing `loginAdmin`/`extractJobs` patterns (lines 95-146).

**Imports/API base pattern** (lines 93-94):
```ts
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
```

**Fetch + error extraction pattern** (lines 95-113):
```ts
export async function loginAdmin(password: string, cfToken: string): Promise<string> {
  const res = await fetch(`${API}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password, cf_token: cfToken }),
  });

  if (!res.ok) {
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }
  ...
}
```

**Auth header pattern** (extractJobs lines 122-130):
```ts
const res = await fetch(`${API}/api/v1/admin/extract`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  },
  body: JSON.stringify({ text }),
});
```

**Conventions to copy:**
- Export interfaces/types for API responses (`JobPublic`, `JobListResponse` already).
- Use `NEXT_PUBLIC_API_URL` fallback.
- Error handling: try parse JSON, extract `body.detail` as string, fallback to status.
- Return typed promises.

**What to add (research §Frontend api helpers):**
- `JobAdmin` interface (all fields incl. contact + source_snippet + timestamps).
- `JobAdminListResponse` interface.
- `JobUpdate` interface (editable fields).
- `listAdminJobs(token, { status, city, page, limit })` → `JobAdminListResponse`.
- `approveJob(token, id)` → `JobAdmin` (PATCH `/admin/jobs/{id}/approve`).
- `updateJob(token, id, data)` → `JobAdmin` (PUT `/admin/jobs/{id}`).
- `deleteJob(token, id)` → void (DELETE, 204).

---

## Shared Patterns

### Authentication (Bearer JWT)
**Source:** `backend/app/deps.py` (lines 31-51) + `frontend/app/admin/paste/ExtractForm.tsx` (lines 8, 29-38, 54-60)
**Apply to:** All new admin review routes (backend) and guarded pages (frontend).
```python
# Backend
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
```
```ts
// Frontend: token in sessionStorage
const TOKEN_KEY = "nqu_admin_token";
const stored = window.sessionStorage.getItem(TOKEN_KEY);
// requests: Authorization: `Bearer ${token}`
```

### Error Handling (pt-BR verbatim)
**Source:** `frontend/lib/api.ts` (lines 102-113) + `backend/app/api/v1/extract.py` (lines 56-84)
**Apply to:** All admin mutations and fetches.
- Backend raises `HTTPException(status_code=..., detail="pt-BR message")`.
- Frontend extracts `body.detail` as string and renders verbatim (never translates).

### Validation (at_least_one_contact + city whitelist)
**Source:** `backend/app/models/job.py` (lines 67-76) CHECK constraints + `backend/app/api/v1/public.py` `_CITY_ALIASES` (lines 28-45)
**Apply to:** `JobUpdate` schema + edit mutation.
- DB CHECK `at_least_one_contact`: `(contact_email IS NOT NULL AND btrim(contact_email) <> '') OR (contact_phone IS NOT NULL AND btrim(contact_phone) <> '')`.
- City validated against accented canonical set {São Paulo, Rio de Janeiro, Belo Horizonte, Remoto}; normalize slug/label → canonical before persisting (Pitfall 2).

### Response Serialization (Pydantic from_attributes)
**Source:** `backend/app/schemas/job.py` (lines 24-40) `model_config = ConfigDict(from_attributes=True)`
**Apply to:** `JobAdmin`, `JobUpdate`, `JobAdminListResponse`.

### Native `<dialog>` Modal
**Source:** `frontend/components/board/JobDetailDialog.tsx` (lines 47-97)
**Apply to:** `EditJobDialog.tsx`, `DeleteConfirmDialog.tsx`.
- `useRef<HTMLDialogElement>`, `showModal()`, `close()`, `onClose` for ESC/backdrop, scroll lock, focus restoration via requestAnimationFrame.

### City Chips Filter
**Source:** `frontend/components/board/BoardToolbar.tsx` (lines 151-186)
**Apply to:** `CityChips.tsx` / review queue.

### Tailwind v4 Route-Scoped CSS
**Source:** `frontend/app/(public)/public.css` (lines 1-24) + `frontend/app/(public)/layout.tsx` (line 4)
**Apply to:** `frontend/app/admin/admin.css` + `frontend/app/admin/layout.tsx`.
- `@import "tailwindcss";` + `@theme { ... }` tokens; import only in admin layout (Preflight isolation, Pitfall 4).

### Optimistic Update + Rollback
**Source:** Research §Architecture (Pitfalls 3, 8) — new pattern for this phase (no direct analog in codebase; closest is `JobGrid` client state).
**Apply to:** Review queue approve/delete/edit.
- Snapshot previous list; remove/update immediately; on error restore + toast error; refetch after success; decrement page if empty.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `frontend/components/admin/ToastProvider.tsx` | component (provider) | event-driven (context) | No toast/context provider exists in codebase; new pattern (D-13, no external lib) |
| `frontend/app/admin/admin.css` | style/config | N/A | No Tailwind in admin today (plain CSS `globals-admin.css`); new route-scoped Tailwind v4 shell (D-12). Closest is `public.css` (copy tokens). |
| `frontend/components/admin/icons.tsx` | component (icons) | N/A | Admin icons don't exist yet; follows `board/icons.tsx` inline SVG style (20px, stroke-width 1.75, currentColor). |

## Metadata

**Analog search scope:** `backend/app/` (api/v1, crud, models, schemas, deps), `backend/tests/`, `frontend/app/`, `frontend/components/`, `frontend/lib/`  
**Files scanned:** 40+  
**Pattern extraction date:** 2026-10-27