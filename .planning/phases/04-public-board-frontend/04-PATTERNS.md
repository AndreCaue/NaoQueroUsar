# Phase 4: Public Board Frontend - Pattern Map

**Mapped:** 2026-10-22  
**Files analyzed:** 20 artifacts (backend + frontend)  
**Analogs found:** 11 / 20 (9 without analogs as expected - new Tailwind/route-group/frontend board components)  

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/crud/jobs.py` | service | CRUD | `backend/app/crud/jobs.py` (self - extend existing) | exact (modify) |
| `backend/app/api/v1/public.py` | route/controller | request-response | `backend/app/api/v1/public.py` (self - extend existing) | exact (modify) |
| `backend/app/schemas/job.py` | model/schema | N/A | `backend/app/schemas/job.py` (read) | reference (may need minimal change) |
| `backend/app/main.py` | config/app | N/A | `backend/app/main.py` | reference (add CORS expose_headers) |
| `backend/alembic/versions/0003_*.py` | migration | N/A | `backend/alembic/versions/0001_initial_jobs.py`, `0002_jobs_source_snippet.py` | role-match |
| `backend/scripts/seed_public_demo.py` | utility/script | N/A | `backend/scripts/seed.py` (exists but different pattern) | role-match with guard differences |
| `backend/tests/test_public_search.py` | test | N/A | `backend/tests/test_public_api.py`, `backend/tests/conftest.py` | role-match |
| `frontend/postcss.config.mjs` | config | N/A | **no analog** | — |
| `frontend/package.json` | config | N/A | `frontend/package.json` (modify) | exact (modify) |
| `frontend/tsconfig.json` | config | N/A | `frontend/tsconfig.json` (modify only if needed) | exact (may not need change) |
| `frontend/app/globals.css` | style/config | N/A | `frontend/app/globals.css` (orphaned, modify) | role-match (currently minimal) |
| `frontend/app/(public)/layout.tsx` | component/layout | N/A | **no analog** (route group) | — |
| `frontend/app/(public)/page.tsx` | component/page (RSC) | request-response | `frontend/app/page.tsx` (placeholder to replace) | role-match |
| `frontend/app/(public)/doacoes/page.tsx` | component/page (RSC) | N/A | **no analog** (static page) | — |
| `frontend/app/(public)/loading.tsx` | component/page (RSC) | N/A | **no analog** | — |
| `frontend/app/(public)/error.tsx` | component/client | error-boundary | **no analog** | — |
| `frontend/app/(public)/public.css` | style | N/A | **no analog** (Tailwind v4 route-scoped) | — |
| `frontend/components/board/*` (grid/card/toolbar/pagination/ad/dialog) | component | N/A | **no analog** (no components dir structure used yet) | — |
| `frontend/lib/api.ts` | utility/service | N/A | `frontend/lib/api.ts` (extend) | exact (extend) |
| `frontend/lib/cities.ts` | utility | N/A | **no analog** | — |
| `frontend/lib/contacts.ts` | utility | N/A | **no analog** | — |
| `frontend/lib/format.ts` | utility | N/A | **no analog** | — |

## Pattern Assignments

### Backend: Modify `backend/app/crud/jobs.py` (service, CRUD)
**Analog:** `backend/app/crud/jobs.py` (self, extend) — `lines 13-40` current implementation

**Current pattern (lines 13-40):**
```python
async def list_published(
    session: AsyncSession,
    page: int,
    limit: int,
) -> tuple[list[Job], int]:
    """Return ``(items, total)`` for published, non-expired jobs.
    Newest first (``created_at DESC``), offset-paginated (D-14). Both the
    page query and the total count apply the SAME filter (D-17):
    ``status = 'published' AND expires_at > now()``.
    """
    filters = (
        Job.status == JobStatus.published,
        Job.expires_at > func.now(),
    )

    items_stmt = (
        select(Job)
        .where(*filters)
        .order_by(Job.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    count_stmt = select(func.count()).select_from(Job).where(*filters)

    items = list((await session.scalars(items_stmt)).all())
    total = (await session.scalar(count_stmt)) or 0
    return items, total
```

**Conventions to copy:**
- **Imports:** `from sqlalchemy import func, select`, `from sqlalchemy.ext.asyncio import AsyncSession` (lines 5-6). Also may need `or_`/`and_` if composing complex predicates; for simple AND use tuple expansion as done.
- **Filter construction:** Build filters tuple/list once and reuse for both items query and count query (ensures `total` consistency). Apply `status='published' AND expires_at > now()` in both.
- **Ordering:** Use `.order_by()` with deterministic tie-breaker - **MUST add `Job.id`** (D-06a). Current is only `created_at.desc()`; must become `order_by(Job.created_at.desc(), Job.id.desc())` for `recentes`, and `order_by(Job.created_at.asc(), Job.id.asc())` for `antigas`.
- **Pagination:** Keep offset-based pagination with `(page-1)*limit`. 
- **Return shape:** Tuple of `(items: list[Job], total: int)`. Cast count with `or 0`.

**What must differ:**
- Add params `q: str | None = None, city: str | None = None, sort: str = "recentes"`. Make them keyword-only compatible with existing calls (existing code calls positionally; keep signature flexible or use defaults).
- Add helper `_published_filters(q=None, city=None)` returning list/tuple of filter expressions (reuse for items and count).
- For `q`: use `search_text.like(pattern, escape='\\')` where pattern is `f"%{escaped_normalized}%"` and normalized via `immutable_unaccent(lower(q))` (same expression as trigger). Need to import/use `func.immutable_unaccent`, `func.lower`. Also need `escape_like()` helper to escape `\`, `%`, `_`.
- For `city`: filter `Job.city == city` where `city` is the canonical value (no accent) as passed by API (API translates slug→canonical). No ILIKE, direct equality.
- For `sort`: map to asc/desc on `created_at` with id tie-breaker as above.
- Keep `status == JobStatus.published` and `expires_at > func.now()` always present (trigram index is partial on published).

---

### Backend: Modify `backend/app/api/v1/public.py` (route/controller, request-response)
**Analog:** `backend/app/api/v1/public.py` (self) — `lines 25-40` current

**Current pattern (lines 25-40):**
```python
@router.get("/jobs", response_model=JobListResponse)
async def list_public_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> JobListResponse:
    """List published, non-expired jobs (contact-free), newest first (D-14/D-17)."""
    # Phase boundary (D-16): search/city/sort are Phase 4 — do NOT add them here.
    items, total = await list_published(session, page=page, limit=limit)
    return JobListResponse(
        items=[JobPublic.model_validate(job) for job in items],
        page=page,
        limit=limit,
        total=total,
    )
```

**Conventions to copy:**
- **Imports:** `from fastapi import APIRouter, Depends, HTTPException, Query, Request` (line 3). Add imports as needed.
- **Router setup:** `router = APIRouter(prefix="/public", tags=["public"])` (line 22). No auth deps.
- **Query params:** Use `Query()` with validation (`ge=1` for page, `ge=1, le=50` for limit). Follow existing style.
- **Response model:** Always use Pydantic response models from `app.schemas.job` (`JobListResponse`, `JobPublic`).
- **Serialization:** `[JobPublic.model_validate(job) for job in items]` as done.
- **Error handling:** In detail/reveal endpoints, raise `HTTPException` with `status_code` and `detail` (pt-BR). For list endpoint, no errors expected beyond validation.

**What must differ:**
- Add `q: str | None = Query(None, max_length=80)`, `city: str | None = Query(None)`, `sort: str | None = Query(None)` (or `sort: str = Query("recentes")` with whitelist).
- Remove the "Phase boundary" comment on line 32.
- Translate city slug→canonical before passing to CRUD: use mapping `slug -> canonical` (e.g., `sao-paulo`→`"Sao Paulo"`, `rio-de-janeiro`→`"Rio de Janeiro"`, `belo-horizonte`→`"Belo Horizonte"`, `remoto`→`"Remoto"`). The canonical values are **without accents** per D-05 and extractor.py ALLOWED_CITIES.
- Validate/whitelist `sort` to `recentes|antigas`, default `recentes`. Validate/whitelist `city` slugs or canonical? API accepts slugs in URL per D-05; better to accept slugs and translate.
- Pass all params to `list_published(session, page=page, limit=limit, q=q, city=canonical_city, sort=sort)`.
- Ensure `JobListResponse` structure unchanged.

---

### Backend: New migration `backend/alembic/versions/0003_*.py`
**Analog:** `backend/alembic/versions/0001_initial_jobs.py` (trigger/function pattern) and `0002_jobs_source_snippet.py` (simple add column)

**From 0001 (lines 123-142):**
```python
op.execute(
    """
    CREATE OR REPLACE FUNCTION jobs_set_search_text()
    RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        NEW.search_text = immutable_unaccent(lower(
            coalesce(NEW.title, '') || ' ' ||
            coalesce(NEW.company, '') || ' ' ||
            coalesce(NEW.activities, '')
        ));
        RETURN NEW;
    END;
    $$;
    """
)
op.execute(
    "CREATE TRIGGER jobs_search_text_trg "
    "BEFORE INSERT OR UPDATE ON jobs "
    "FOR EACH ROW EXECUTE FUNCTION jobs_set_search_text();"
)
```

**Conventions to copy:**
- **Revision chain:** `down_revision = "0002_jobs_source_snippet"`. Follow naming pattern `000N_description.py`.
- **Use `op.execute()` for SQL functions/triggers** (not Alembic's high-level API for PL/pgSQL). 
- **Extensions already exist** - don't recreate them.
- **Immutable function `immutable_unaccent(text)` exists** (created in 0001).

**What must differ (per D-04/D-35):**
- **Replace trigger function** to include `requirements`: add `coalesce(NEW.requirements, '')` to concatenation.
- **Backfill existing rows:** Need to update `search_text` for all jobs. Must disable `jobs_updated_at` trigger during backfill (to avoid bumping `updated_at`), do UPDATE, re-enable trigger. As shown in research Pattern 4.
- **Use `CREATE OR REPLACE FUNCTION jobs_set_search_text()`** (same name) so existing trigger `jobs_search_text_trg` remains bound.
- **Downgrade:** Can restore previous function body without requirements (backfill not strictly necessary on downgrade per research note).

---

### Backend: New `backend/scripts/seed_public_demo.py` (utility/script)
**Analog:** `backend/scripts/seed.py` (exists in repo at `backend/scripts/` per CONTEXT line 127) - **read to match style**; research says seed.py has no env guard

**Conventions to copy from general script patterns:**
- **Location:** `backend/scripts/` (already exists with `__init__.py` and `seed.py`)
- **Use SQLAlchemy async session** like other scripts might do
- **Import settings/config** from `app.core.config`
- **Mark as dev-only with env guard** (critical - seed.py lacks this per research)

**What must differ (per D-02, research Pitfall 4):**
- **Env guard:** Require `settings.ENV == "dev"` AND explicit confirmation flag (e.g., `--yes`). Refuse if DB host doesn't look like dev/local. Print resolved host (not full URL) before inserting.
- **Never set `search_text` manually** - trigger owns it (migration 0003 ensures trigger includes requirements).
- **Idempotent:** Maybe delete previous demo rows by marker in `source_snippet` or some marker? Research suggests `MARKER = "SEED_PUBLIC_DEMO"` written into `source_snippet` for idempotent delete-then-insert.
- **Create published jobs only** with contacts fake, `expires_at` in future. Respect `at_least_one_contact` CHECK.
- **No HTTP endpoint** - script only.
- **Never run in production**.

---

### Backend: New `backend/tests/test_public_search.py` (test)
**Analog:** `backend/tests/test_public_api.py` and `backend/tests/conftest.py`

**From test_public_api.py patterns:**
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

**From conftest.py:**
- Use fixtures: `client`, `db_session`, `seed_*_job`. Tests run in rolled-back transaction.
- `db_session.execute(text("DELETE FROM jobs"))` done at start of transaction.
- `FakeTurnstileVerifier` installed via dependency overrides (not relevant for public GETs).
- Rate limiter reset per test.

**Conventions to copy:**
- **Async tests** - pytest-asyncio with `asyncio_mode = "auto"`.
- **Use fixtures** from conftest.
- **Make direct inserts** via `db_session.add()` and `await db_session.flush()` when creating test data (like seed fixtures do).
- **Assert response structure** matching `JobListResponse` schema.
- **Test against real Postgres** (DB-gated suite).

**What to test (per validation):**
- SRCH-01: accent/case-insensitive search in title/company/activities/**requirements**; wildcard escaping (`%`, `_` treated literally)
- SRCH-02: city filter by slug/canonical, AND with q, unknown city ignored (no 400)
- SRCH-03: sort `recentes`/`antigas`, default recentes, deterministic ordering with id tie-breaker (test 3 same-transaction rows, limit=1)
- Regression: list/detail still have no contact fields
- Total consistency

---

### Frontend: Config changes
**Analog:** `frontend/package.json` (modify), `frontend/tsconfig.json` (maybe)

**package.json current (lines 11-23):**
```json
"dependencies": {
  "next": "15.5.3",
  "next-turnstile": "1.0.7",
  "react": "19.1.1",
  "react-dom": "19.1.1"
},
"devDependencies": {
  "@types/node": "22.18.8",
  "@types/react": "19.1.13",
  "eslint": "8.57.1",
  "eslint-config-next": "15.5.3",
  "typescript": "5.9.2"
}
```

**Conventions to copy:**
- Keep exact versions as specified. Don't upgrade Next to 16.x.
- Follow existing style (JSON formatting).

**What must differ:**
- Add devDependencies: `tailwindcss@4.3.3`, `@tailwindcss/postcss@4.3.3` (per research). May need to add if not present.
- Create `postcss.config.mjs` with `@tailwindcss/postcss` plugin (new file).

**postcss.config.mjs (from research):**
```js
const config = { plugins: { "@tailwindcss/postcss": {} } };
export default config;
```

---

### Frontend: `frontend/app/layout.tsx` and `frontend/app/globals.css`
**Analog:** `frontend/app/layout.tsx` (modify), `frontend/app/globals.css` (modify - currently orphaned/minimal)

**Current layout.tsx:**
```tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
```

**Conventions to copy:**
- Keep `lang="pt-BR"` (already present).
- Simple functional component, no "use client".
- TypeScript with React types.

**What must differ:**
- Import `./globals.css` (currently not imported - UI-SPEC says "corrigir").
- Add `<meta name="theme-color" content="#0f0a1a" />` per UI-SPEC §G.
- Keep minimal.

**globals.css (UI-SPEC says):**
```css
/* app/globals.css */
:root { color-scheme: dark; }
body { background: var(--bg, #0f0a1a); color: #e2e8f0; }
```
But better to follow UI-SPEC exactly - it says "permanece mínimo (`:root { color-scheme: dark; }`, `body` background/color) e passa a ser importado pelo `app/layout.tsx`".

---

### Frontend: Route group `(public)` - new structure
**Analog:** None directly. Follow Next.js App Router conventions. Reference admin area structure for patterns.

**Admin patterns to observe:**
- `frontend/app/admin/paste/page.tsx` exists (not read but structure implied)
- `frontend/app/admin/paste/ExtractForm.tsx` is `"use client"` component with clear state management
- Uses CSS imports in components (`import "./globals-admin.css"`)
- Imports from `@/lib/api`

**Public layout pattern (new):**
- `app/(public)/layout.tsx` - RSC layout, imports `./public.css`, includes header/footer/skip link per UI-SPEC §F
- Header: wordmark "NaoQueroUsar" (accent on last char?), "Doações" button linking to `/doacoes`, slogan on desktop
- Footer with slogan and copyright
- Skip link to `#vagas`

**public.css (from UI-SPEC):**
```css
@import "tailwindcss";

@theme {
  --color-canvas: #0f0a1a;
  --color-surface: #1a1025;
  --color-line: #2a1f3d;
  --color-line-strong: #6d5a91;
  --color-fg: #e2e8f0;
  --color-fg-muted: #b8a9cc;
  --color-accent: #8b5cf6;
  --color-accent-soft: #a78bfa;
  --color-accent-strong: #7c3aed;
  --color-accent-strong-hover: #6d28d9;
  --color-donate: #facc15;
  --color-danger: #f87171;
  --color-danger-soft: #fecaca;
  --radius-card: 12px;
  --radius-dialog: 16px;
}
```
Must use `@import "tailwindcss"` (CSS-first v4). Import only in route group layout to isolate from admin.

---

### Frontend: `frontend/app/(public)/page.tsx` (RSC board)
**Analog:** `frontend/app/page.tsx` (placeholder to replace) - very minimal

**Patterns to follow from admin/RSC conventions:**
- RSC by default (no "use client" unless needed)
- Parse `searchParams` as Promise in Next 15: `searchParams: Promise<BoardSearchParams>`, `await searchParams`
- Fetch on server with `cache: "no-store"`, `AbortSignal.timeout(15000)`
- Use `NEXT_PUBLIC_API_URL` or server env var; research says prefer `BACKEND_API_URL` first, fallback to `NEXT_PUBLIC_API_URL`
- Normalize filters (whitelist, trim, clamp)
- Handle `?vaga=` deep link - fetch detail if not in current page items
- Render components with Suspense

**API call pattern from lib/api.ts:**
```ts
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
// ... fetch with headers, error handling extracting body.detail
```
For server-side in RSC, can use same env or different; need to be careful about build-time inlining.

---

### Frontend: Components in `frontend/components/board/`
**Analog:** None - new structure. Follow patterns from existing client components.

**From `frontend/app/admin/paste/ExtractForm.tsx`:**
- `"use client"` directive at top
- Named/default exports as appropriate
- State with `useState`, effects with `useEffect`
- Event handlers
- Conditional rendering
- Error handling extracting messages
- Turnstile usage: `import { Turnstile } from "next-turnstile"`, pass `siteKey`, `action`, `theme="dark"`, `onVerify`, `onExpire`, `onError`. Use `key` for reset (no reset API). For reveal use `appearance="interaction-only"`, `id="turnstile-reveal"`.
- SessionStorage usage with try/catch
- Class names for styling

**New patterns needed:**
- Native `<dialog>`: `useRef<HTMLDialogElement>`, `showModal()`, `close()`, handle `onClose`/`onCancel`, trap focus, restore focus on close, lock body scroll
- URL state sync: use `useRouter()`, `router.replace()` for filters (no history pollution), `history.replaceState()` for modal param
- Contact cache in module scope or context (D-10 forbids useRef in dialog host) - use module-level `Map` or React context
- Debounced search input (300ms), flush on Enter
- Date formatting with `Intl.DateTimeFormat` and `timeZone: "America/Sao_Paulo"`

---

### Frontend: `frontend/lib/api.ts` extensions
**Analog:** `frontend/lib/api.ts` (extend existing)

**Current pattern:**
```ts
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  // ...
}
```

**Conventions to copy:**
- Export interfaces/types for API responses
- Use `NEXT_PUBLIC_API_URL` fallback pattern
- Error handling: try to parse JSON, extract `body.detail` as string, fallback to status
- Return typed promises

**What to add:**
- `JobPublic` interface matching backend schema
- `JobListResponse` interface
- `ContactRevealResponse` interface  
- `listJobs(params)` for client-side if needed, or server-side helper in `lib/jobs.ts`
- `revealContact(jobId, cfToken)` - POST to `/api/v1/public/jobs/{id}/reveal-contact` with `{ cf_token: cfToken }`, handle 403/404/429/429 with Retry-After

---

### Frontend: `frontend/lib/cities.ts`, `frontend/lib/contacts.ts`, `frontend/lib/format.ts`
**Analog:** None - new utilities

**Patterns from codebase:**
- Simple TypeScript modules, named exports
- Pure functions
- Type definitions

**cities.ts pattern (from UI-SPEC/research):**
```ts
export type CitySlug = "sao-paulo" | "rio-de-janeiro" | "belo-horizonte" | "remoto";
export const CITIES: Array<{ slug: CitySlug; label: string; canonical: string }> = [
  { slug: "sao-paulo", label: "São Paulo", canonical: "Sao Paulo" },
  { slug: "rio-de-janeiro", label: "Rio de Janeiro", canonical: "Rio de Janeiro" },
  { slug: "belo-horizonte", label: "Belo Horizonte", canonical: "Belo Horizonte" },
  { slug: "remoto", label: "Remoto", canonical: "Remoto" },
];
export function slugToCanonical(slug: string): string | null { /* ... */ }
export function canonicalToLabel(canonical: string): string { /* ... */ }
```
Note: canonical values match ALLOWED_CITIES without accents as per D-05.

**contacts.ts:**
```ts
export function waHref(phone: string): string | null {
  const digits = phone.replace(/\D/g, "");
  return digits.length >= 10 ? `https://wa.me/${digits}` : null;
}
export function mailtoHref(email: string, title: string): string {
  const subject = encodeURIComponent(`Candidatura: ${title}`);
  return `mailto:${email.trim()}?subject=${subject}`;
}
```

**format.ts:**
```ts
const fmt = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit", month: "2-digit", year: "numeric",
  timeZone: "America/Sao_Paulo",
});
export const formatDateBR = (iso: string) => fmt.format(new Date(iso));
```

## "No Analog" List

| File/Area | Role | Why No Analog | Governing Spec Reference |
|-----------|------|---------------|--------------------------|
| `frontend/postcss.config.mjs` | config | Project has no PostCSS config; Tailwind v4 uses `@tailwindcss/postcss` plugin (new setup) | `04-RESEARCH.md` §Pattern 2, `04-UI-SPEC.md` §Design System |
| `frontend/app/(public)/` route group | routing/layout | No route groups exist; admin uses flat `app/admin/` structure. First route group in project. | `04-UI-SPEC.md` §Design System (Tailwind isolation), `04-CONTEXT.md` D-01 |
| `frontend/app/(public)/public.css` | style | No Tailwind usage anywhere; CSS is plain (`globals-admin.css`). Tailwind v4 CSS-first with `@theme`. | `04-UI-SPEC.md` §Design System lines 38-66, `04-RESEARCH.md` §Pattern 2 |
| `frontend/app/(public)/doacoes/page.tsx` | page (static RSC) | No static content pages exist outside admin; new route. | `04-CONTEXT.md` D-11, `04-UI-SPEC.md` §F |
| `frontend/app/(public)/loading.tsx`, `error.tsx` | RSC/loading/error boundaries | No loading/error.tsx files exist in app router. New pattern for this phase. | `04-UI-SPEC.md` §C states, `04-RESEARCH.md` §Pattern 1 |
| `frontend/components/board/*` (entire directory) | components | No `components/` directory exists in frontend root; only `lib/` exists. All UI is inline or in route files currently. | `04-UI-SPEC.md` §Component Inventory, `04-RESEARCH.md` §Recommended Project Structure |
| `frontend/lib/cities.ts`, `frontend/lib/contacts.ts`, `frontend/lib/format.ts` | utilities | No utility files beyond `api.ts`. New helpers needed. | `04-UI-SPEC.md` contracts, `04-RESEARCH.md` §Patterns 6,7 |
| Native `<dialog>` usage | component pattern | No dialog/modal components exist. Using native HTML dialog API. | `04-UI-SPEC.md` §D, `04-RESEARCH.md` §Pattern 4/Code Examples |
| Turnstile reveal flow (separate from login) | component pattern | Login uses Turnstile in admin; reveal has different requirements (mounted on click, `appearance="interaction-only"`, `id="turnstile-reveal"`, different state machine). | `04-UI-SPEC.md` §E, `04-RESEARCH.md` §Pattern 5 |
| ADS slots, pagination component | components | No pagination/ads exist anywhere. | `04-UI-SPEC.md` §ADS, §Pagination |

## Copy-Paste-Ready Convention Snippets

### Imports style (TypeScript/React)
**From:** `frontend/app/admin/paste/ExtractForm.tsx:1-6`
```tsx
"use client";

import { useEffect, useState } from "react";
import { Turnstile } from "next-turnstile";
import { loginAdmin, extractJobs, type ExtractSummary } from "@/lib/api";
import "./globals-admin.css";
```
**Notes:** Use `"use client"` only when needed (hooks, event handlers, browser APIs). Import types with `type` keyword. Use path alias `@/` for lib imports. CSS imports in client components are fine.

### API fetch with error extraction (TypeScript)
**From:** `frontend/lib/api.ts:21-46`
```ts
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

  const body = (await res.json()) as { access_token?: string };
  if (!body.access_token) {
    throw new Error("Token não recebido");
  }
  return body.access_token;
}
```
**Notes:** Always extract `body.detail` as string for error messages (rendered verbatim by UI). Try/catch JSON parse. Fallback to status code message.

### Error handling in client components
**From:** `frontend/app/admin/paste/ExtractForm.tsx:60-70, 80-86`
```tsx
} catch (err) {
  const msg = err instanceof Error ? err.message : "Erro ao autenticar";
  setError(msg);
  // The token was consumed by the backend (or refused) — a new one is needed
  resetTurnstile();
} finally {
  setLoading(false);
}
```
**Notes:** Extract message from Error instance or provide fallback. Handle side effects on error (like resetting Turnstile). Use finally for cleanup.

### CSS variable style (plain CSS)
**From:** `frontend/app/admin/paste/globals-admin.css:1-8, 27-41`
```css
:root {
  --bg: #0f0a1a;
  --panel: #1a1025;
  --accent: #8b5cf6;
  --accent-soft: #a78bfa;
  --warn: #facc15;
}

.admin-btn {
  background: var(--accent);
  color: #fff;
  border: 0;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
  margin-top: 1rem;
}

.admin-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```
**Notes:** Use CSS variables defined in :root. Keep admin CSS plain (no Tailwind). Public will use Tailwind v4 @theme with different token names.

### Tailwind v4 route-scoped setup
**From:** `04-UI-SPEC.md:43-63` and `04-RESEARCH.md:270-288`
```css
/* app/(public)/public.css */
@import "tailwindcss";

@theme {
  --color-canvas: #0f0a1a;
  --color-surface: #1a1025;
  --color-line: #2a1f3d;
  --color-line-strong: #6d5a91;
  --color-fg: #e2e8f0;
  --color-fg-muted: #b8a9cc;
  --color-accent: #8b5cf6;
  --color-accent-soft: #a78bfa;
  --color-accent-strong: #7c3aed;
  --color-accent-strong-hover: #6d28d9;
  --color-donate: #facc15;
  --color-danger: #f87171;
  --color-danger-soft: #fecaca;
  --radius-card: 12px;
  --radius-dialog: 16px;
}
```
```js
// postcss.config.mjs
const config = { plugins: { "@tailwindcss/postcss": {} } };
export default config;
```
**Notes:** Import only in `app/(public)/layout.tsx`. Never import in root layout. Use `@theme` for design tokens. Rule: `#8b5cf6` never carries text (use `#7c3aed` for filled buttons with white text).

### Python CRUD pattern
**From:** `backend/app/crud/jobs.py:13-40`
```python
async def list_published(
    session: AsyncSession,
    page: int,
    limit: int,
) -> tuple[list[Job], int]:
    filters = (
        Job.status == JobStatus.published,
        Job.expires_at > func.now(),
    )

    items_stmt = (
        select(Job)
        .where(*filters)
        .order_by(Job.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    count_stmt = select(func.count()).select_from(Job).where(*filters)

    items = list((await session.scalars(items_stmt)).all())
    total = (await session.scalar(count_stmt)) or 0
    return items, total
```
**Notes:** Build filters once, reuse for items and count. Use `func.now()` for time comparisons. Return tuple. Cast count to int with `or 0`. Order with tie-breaker for pagination stability.

### Python API route pattern
**From:** `backend/app/api/v1/public.py:25-40`
```python
@router.get("/jobs", response_model=JobListResponse)
async def list_public_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> JobListResponse:
    items, total = await list_published(session, page=page, limit=limit)
    return JobListResponse(
        items=[JobPublic.model_validate(job) for job in items],
        page=page,
        limit=limit,
        total=total,
    )
```
**Notes:** Use FastAPI Query validation. No auth deps for public routes. Use response_model. Serialize with model_validate. Router mounted without extra prefix.

### Alembic migration pattern
**From:** `backend/alembic/versions/0001_initial_jobs.py:123-162`
```python
op.execute(
    """
    CREATE OR REPLACE FUNCTION jobs_set_search_text()
    RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        NEW.search_text = immutable_unaccent(lower(
            coalesce(NEW.title, '') || ' ' ||
            coalesce(NEW.company, '') || ' ' ||
            coalesce(NEW.activities, '')
        ));
        RETURN NEW;
    END;
    $$;
    """
)
op.execute(
    "CREATE TRIGGER jobs_search_text_trg "
    "BEFORE INSERT OR UPDATE ON jobs "
    "FOR EACH ROW EXECUTE FUNCTION jobs_set_search_text();"
)
```
**Notes:** Use `op.execute()` for PL/pgSQL. `CREATE OR REPLACE FUNCTION` to replace existing. Keep same function/trigger names when extending.

### Pytest test pattern
**From:** `backend/tests/test_public_api.py:13-33` and `backend/tests/conftest.py:192-198`
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
**Notes:** Use fixtures from conftest. Tests run in rolled-back transactions. Use AsyncClient. Assert on response structure.

### Test fixture usage
**From:** `backend/tests/conftest.py:251-263, 292-298`
```python
@pytest.fixture
async def seed_published_job(db_session) -> Job:
    job = Job(
        title="Vaga Publicada — Teste",
        company="Empresa A",
        activities="Atividades de teste.",
        city="Remoto",
        salary="A combinar",
        contact_phone="+55 11 90000-0001",
        status=JobStatus.published,
    )
    db_session.add(job)
    await db_session.flush()
    return job
```
**Notes:** Add to db_session, flush to get IDs. Transaction rolled back after test. Don't commit.

## Naming/Commit Conventions Observed from `git log --oneline -20`

**Commit style (from recent commits):**
- Conventional commits with scope: `docs(04): ...`, `refactor(03): ...`, `fix(03-05): ...`, `feat(03-04): ...`, `test(03-04): ...`
- Scope includes phase/plan: `(04)`, `(03)`, `(03-05)`, `(03-04)`, `(03-03)`
- Types: `docs`, `refactor`, `fix`, `feat`, `test`
- Descriptive messages in Portuguese or English as appropriate
- Granular commits per change

**File naming conventions:**
- **Backend:** snake_case for modules (`jobs.py`, `public.py`, `turnstile.py`), kebab-case not used; classes PascalCase
- **Migrations:** numbered with description `0001_initial_jobs.py`, `0002_jobs_source_snippet.py`
- **Frontend:** kebab-case for files in some places? Components use PascalCase (`ExtractForm.tsx`), routes use lowercase/page.tsx conventions
- **Scripts:** snake_case in `backend/scripts/` (`seed.py`)

**Project structure patterns:**
- Backend follows `app/` package: `api/v1/`, `crud/`, `models/`, `schemas/`, `services/`, `core/`, `db/`, `deps.py`, `main.py`
- Frontend uses App Router: `app/` directory, route groups with `()`, client components marked `"use client"`
- Phase docs in `.planning/phases/XX-name/` with numbered files

## 5-Line Summary of Most Load-Bearing Conventions

1. **Single source of truth for filters**: Build filter predicates once in CRUD and reuse for both items query and count query (ensures `total` consistency); always include `status='published' AND expires_at > now()`.
2. **Deterministic pagination**: Order by `created_at` with `id` as tie-breaker (`ORDER BY created_at DESC, id DESC`) because same-transaction inserts share timestamps.
3. **Accent-insensitive search via DB**: Use existing `search_text` column maintained by trigger with `immutable_unaccent(lower(...))`, query with `search_text LIKE pattern ESCAPE '\'` where pattern is escaped and normalized the same way; extend trigger to include `requirements` in migration `0003` with backfill.
4. **Route-scoped styling isolation**: Tailwind v4 lives only in `app/(public)/` route group (imported in `(public)/layout.tsx`) to avoid Preflight leaking into `/admin/*` which uses plain CSS; never `#8b5cf6` for text (use `#7c3aed` for filled buttons with white text per AA).
5. **Contact-free by design + gated reveal**: `JobPublic` never includes contacts (PUBL-05); reveal is only via `POST /api/v1/public/jobs/{id}/reveal-contact` with Turnstile verification, widget mounted on click with different id/appearance from login, contact cached in module scope per tab (not in dialog ref).
