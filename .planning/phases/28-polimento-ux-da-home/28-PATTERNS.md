# Phase 28: Polimento UX da Home - Pattern Map

**Mapped:** 2026-11-22
**Files analyzed:** 14
**Analogs found:** 13 / 14

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/schemas/job.py` | schema/model | request-response | self (`JobListResponse`, lines 48-54) | exact |
| `backend/app/api/v1/public.py` | route/controller | request-response | self (`list_public_jobs`, lines 155-191) | exact |
| `backend/app/crud/jobs.py` | service/CRUD | CRUD/read | self (`_published_filters`, `list_published`, lines 27-91) | exact |
| `backend/app/services/cities.py` | utility/service | transform | self (`CITY_ALIASES`, `resolve_city`, lines 11-28) | exact |
| `frontend/lib/api.ts` | type/contract | request-response | self (`JobListResponse`, lines 78-83) | exact |
| `frontend/lib/jobs.ts` | service/fetch | request-response | self (`fetchBoard`, lines 66-75) | exact |
| `frontend/lib/cities.ts` | utility | transform | self (`CITY_OPTIONS`, `cityBySlug`, lines 11-86) | exact |
| `frontend/lib/filters.ts` | utility/state | transform | self (`buildBoardHref`, `normalizeFilters`, lines 31-95) | exact |
| `frontend/app/(public)/page.tsx` | page/RSC | request-response | self (lines 33-177) | exact |
| `frontend/components/board/BoardToolbar.tsx` | component | event-driven/UI state | self (lines 24-241) | exact |
| `frontend/components/board/SortDropdown.tsx` | component (new, recommended by UI-SPEC) | event-driven/UI state | `frontend/components/board/BoardToolbar.tsx` + `frontend/components/board/JobCard.tsx` | partial (no listbox analog in repo) |
| `frontend/components/board/JobCard.tsx` | component | event-driven/UI state | self (lines 26-108) | exact |
| `frontend/components/board/JobGrid.tsx` | component | event-driven/UI state | self (lines 44-84) | exact (likely no behavior change) |
| `frontend/app/(public)/public.css` | config/style | transform | self (lines 8-107) | exact |

## Pattern Assignments

### `backend/app/schemas/job.py` (schema, request-response)

**Analog:** `backend/app/schemas/job.py` (self)

**Imports pattern** (lines 19-27):
```python
import re
import uuid
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.job import JobStatus
from app.services.cities import resolve_city
```

**Public contract pattern** (lines 29-54):
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


class JobListResponse(BaseModel):
    """Offset-paginated envelope with a total count (D-14)."""

    items: list[JobPublic]
    page: int
    limit: int
    total: int
```

**Phase 28 application (D-04, UI-SPEC data contract):** Add `available_cities: list[str] = Field(default_factory=list)` to `JobListResponse` only. Keep `JobPublic` contact-free. Do not expose contact fields. Values are supported city slugs in stable `CITY_OPTIONS` order.

---

### `backend/app/api/v1/public.py` (route/controller, request-response)

**Analog:** `backend/app/api/v1/public.py` (self)

**Imports / router pattern** (lines 1-36):
```python
import asyncio
import logging
import time
import uuid
from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.client_ip import UNKNOWN_IP, resolve_client_ip
from app.core.config import get_settings
from app.core.ratelimit import chat_search_limit, limiter, reveal_limit
from app.crud import get_published, list_published
from app.db.session import get_session
from app.deps import get_turnstile_verifier
from app.schemas.chat import ChatSearchRequest, ChatSearchResponse, ChatSearchResults
from app.schemas.job import (
    ContactRevealResponse,
    JobListResponse,
    JobPublic,
    ReportRequest,
    RevealRequest,
)
from app.services.cities import resolve_city, resolve_sort
# ...
router = APIRouter(prefix="/public", tags=["public"])
```

**Public board endpoint pattern** (lines 155-191):
```python
@router.get("/jobs", response_model=JobListResponse)
async def list_public_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    q: str | None = Query(None, max_length=80),
    city: str | None = Query(None, max_length=40),
    sort: str = Query("recentes", max_length=20),
    session: AsyncSession = Depends(get_session),
) -> JobListResponse:
    """List published, non-expired jobs (contact-free), filtered and sorted.

    ``q`` searches title + company + activities + requirements, accent- and
    case-insensitively (SRCH-01/D-03). ``city`` is an independent filter
    combined with AND — it never replaces ``q`` (SRCH-02/D-05). ``sort`` is
    ``recentes`` (default) or ``antigas`` (SRCH-03/D-06). Unknown ``city``
    values are ignored and unknown ``sort`` values fall back to ``recentes`` —
    a bad URL never produces a 400. Items and ``total`` share one predicate
    list (04-RESEARCH Pattern 3).
    """
    term = q.strip() if q else None
    if not term:
        term = None

    items, total = await list_published(
        session,
        page=page,
        limit=limit,
        q=term,
        city=resolve_city(city),
        sort=resolve_sort(sort),
    )
    return JobListResponse(
        items=[JobPublic.model_validate(job) for job in items],
        page=page,
        limit=limit,
        total=total,
    )
```

**Phase 28 application (D-01/D-04):** Add `available_cities` to the same response. Compute it via a dedicated CRUD call/query that uses only published+non-expired semantics, independent of `q/city/sort`. Do not create a separate endpoint. Keep response contact-free.

---

### `backend/app/crud/jobs.py` (CRUD/service, read)

**Analog:** `backend/app/crud/jobs.py` (self)

**Imports / module pattern** (lines 1-16):
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

**Published filter reuse pattern** (lines 27-50):
```python
def _published_filters(*, q: str | None, city: str | None) -> list:
    """The ONE predicate list shared by the page query and the total count.

    ``status = 'published'`` is always present literally: the search trigram
    index is partial on it, and ``total`` must describe exactly the same rows
    as ``items`` (D-17, 04-RESEARCH Pattern 3).
    """
    filters: list = [Job.status == JobStatus.published, Job.expires_at > func.now()]

    if city:
        filters.append(Job.city == city)

    if q:
        term = q.strip()
        if term:
            # ``search_text`` is stored as ``immutable_unaccent(lower(...))``
            # by the trigger, so the pattern is normalized identically. The
            # value stays a bound parameter — it is never interpolated into
            # SQL text (T-04-03).
            normalized = func.immutable_unaccent(func.lower(_escape_like(term)))
            pattern = func.concat("%", normalized, "%")
            filters.append(Job.search_text.like(pattern, escape="\\"))
    
    return filters
```

**Phase 28 application (D-01/D-02):** Add a dedicated active-cities query (e.g. `list_active_cities`) using only `Job.status == JobStatus.published, Job.expires_at > func.now()` and `select(Job.city).distinct()`. Do **not** apply `q`, `city`, or `sort`. Map canonical DB values to supported slugs and return in stable `CITY_OPTIONS` order (UI-SPEC/Research A3). Update `__all__` if a new public function is added.

---

### `backend/app/services/cities.py` (utility/service, transform)

**Analog:** `backend/app/services/cities.py` (self)

**Canonical mapping pattern** (lines 1-32):
```python
"""City / sort whitelists shared by the public and admin routes (D-05/D-06b).

The URL and the API speak slugs (``sao-paulo``), the DB stores the accented
canonical form (``São Paulo``) and the UI renders the label. Both routers must
resolve the three spellings identically, so the table lives here instead of in
one router importing another router's private helper.
"""

from typing import Final

CITY_ALIASES: Final[dict[str, str]] = {
    "sao-paulo": "São Paulo",
    "sao paulo": "São Paulo",
    "são paulo": "São Paulo",
    "rio-de-janeiro": "Rio de Janeiro",
    "rio de janeiro": "Rio de Janeiro",
    "belo-horizonte": "Belo Horizonte",
    "belo horizonte": "Belo Horizonte",
    "remoto": "Remoto",
}


def resolve_city(value: str | None) -> str | None:
    """Whitelist the city (slug/canonical/label); anything else is ``None``."""
    if not value:
        return None
    return CITY_ALIASES.get(value.strip().lower())


def resolve_sort(value: str) -> str:
    """Only ``antigas`` changes the order; everything else is ``recentes``."""
    return "antigas" if value.strip().lower() == "antigas" else "recentes"
```

**Phase 28 application (A3, D-04):** Add an explicit canonical->slug mapping/helper for `available_cities` (backend returns slugs). Keep slug whitelist aligned with frontend `CITY_OPTIONS`. Avoid ad-hoc string mapping in routes.

---

### `frontend/lib/api.ts` (type/contract, request-response)

**Analog:** `frontend/lib/api.ts` (self)

**Public board types pattern** (lines 1-83):
```ts
import type { CitySlug } from "./cities";

export type JobStatus = "pending" | "published" | "needs_review" | "invalid";

/**
 * Public job payload (contact-free by design — PUBL-05/D-18).
 *
 * These are exactly the fields the board is allowed to render. The backend
 * guarantees `contact_email`/`contact_phone` never appear in the list/detail
 * response, so the board cannot leak a contact even by accident.
 */
export interface JobPublic {
  id: string;
  title: string;
  company: string | null;
  activities: string | null;
  requirements: string | null;
  salary: string | null;
  benefits: string | null;
  city: string;
  status: JobStatus;
  created_at: string; // ISO 8601
  expires_at: string; // ISO 8601
}

/** Response from list public jobs — paginated public list. */
export interface JobListResponse {
  items: JobPublic[];
  page: number;
  limit: number;
  total: number;
}
```

**Phase 28 application (D-04):** Extend `JobListResponse` with `available_cities: string[]` (or `CitySlug[]` if planner keeps type tighter; UI-SPEC says supported city slugs). Do not add contact fields.

---

### `frontend/lib/jobs.ts` (service/fetch, request-response)

**Analog:** `frontend/lib/jobs.ts` (self)

**Server fetch pattern** (lines 16-75):
```ts
const API =
  process.env.BACKEND_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

const TIMEOUT_MS = 15_000;

export type BoardErrorKind = "timeout" | "http" | "network";

/**
 * Board fetch failure. `message` is the kind so the client error boundary can
 * pick the cold-start copy without importing this server module.
 */
export class BoardError extends Error {
  readonly kind: BoardErrorKind;
  readonly status?: number;

  constructor(kind: BoardErrorKind, status?: number) {
    super(kind);
    this.name = "BoardError";
    this.kind = kind;
    this.status = status;
  }
}

async function request(path: string): Promise<Response> {
  try {
    return await fetch(`${API}${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch (error) {
    if (
      error instanceof Error &&
      (error.name === "TimeoutError" || error.name === "AbortError")
    ) {
      throw new BoardError("timeout");
    }
    throw new BoardError("network");
  }
}

export async function fetchBoard(filters: Filters): Promise<JobListResponse> {
  const params = new URLSearchParams(toApiParams(filters));
  params.set("limit", String(PAGE_SIZE));

  const response = await request(`/api/v1/public/jobs?${params.toString()}`);
  if (!response.ok) {
    throw new BoardError("http", response.status);
  }
  return parseJson<JobListResponse>(response);
}
```

**Phase 28 application (D-04):** No new fetch path. `fetchBoard` already returns `JobListResponse`; extending the type propagates `available_cities` through RSC. Keep `cache: "no-store"` and timeout behavior.

---

### `frontend/lib/cities.ts` (utility, transform)

**Analog:** `frontend/lib/cities.ts` (self)

**City option/order pattern** (lines 10-30):
```ts
export type CitySlug =
  | "sao-paulo"
  | "rio-de-janeiro"
  | "belo-horizonte"
  | "remoto";

export interface CityOption {
  slug: CitySlug;
  label: string;
  canonical: string;
}

export const CITY_OPTIONS: readonly CityOption[] = [
  { slug: "sao-paulo", label: "São Paulo", canonical: "São Paulo" },
  { slug: "rio-de-janeiro", label: "Rio de Janeiro", canonical: "Rio de Janeiro" },
  { slug: "belo-horizonte", label: "Belo Horizonte", canonical: "Belo Horizonte" },
  { slug: "remoto", label: "Remoto", canonical: "Remoto" },
];
```

**Lookup helper pattern** (lines 79-86):
```ts
/** URL slug → city option; `null`/unknown slugs have no option. */
export function cityBySlug(slug: string | null): CityOption | undefined {
  if (!slug) {
    return undefined;
  }
  const key = slug.trim().toLowerCase();
  return CITY_OPTIONS.find((option) => option.slug === key);
}
```

**Phase 28 application (D-01/D-02):** Reuse `CITY_OPTIONS` as stable render order. Filter by `availableCities.includes(option.slug)` in toolbar or extract a small helper. Do not create a second city source of truth.

---

### `frontend/lib/filters.ts` (utility/state, transform)

**Analog:** `frontend/lib/filters.ts` (self)

**URL normalization/build pattern** (lines 31-95):
```ts
export function normalizeFilters(input: RawSearchParams): Filters {
  const rawQ = first(input.q)?.trim() ?? "";
  const rawCity = first(input.city)?.trim().toLowerCase() ?? "";
  const rawSort = first(input.sort)?.trim().toLowerCase() ?? "";
  const rawPage = Number.parseInt(first(input.page) ?? "", 10);
  const rawVaga = first(input.vaga)?.trim() ?? "";

  return {
    q: rawQ.slice(0, 80),
    city: CITY_SLUGS.has(rawCity) ? rawCity : null,
    sort: rawSort === "antigas" ? "antigas" : "recentes",
    page: Number.isFinite(rawPage) && rawPage >= 1 ? rawPage : 1,
    // Deliberately NOT validated here: the page's fetch boundary decides what
    // a malformed id means, so the server-rendered not-found panel stays
    // reachable instead of the parser silently dropping the param.
    vaga: rawVaga ? rawVaga.slice(0, 64) : null,
  };
}

/** Canonical, shareable board href — defaults are omitted. */
export function buildBoardHref(filters: Filters): string {
  const params = new URLSearchParams();
  if (filters.q) {
    params.set("q", filters.q);
  }
  if (filters.city) {
    params.set("city", filters.city);
  }
  if (filters.sort !== "recentes") {
    params.set("sort", filters.sort);
  }
  if (filters.page > 1) {
    params.set("page", String(filters.page));
  }
  if (filters.vaga) {
    params.set("vaga", filters.vaga);
  }
  const query = params.toString();
  return query ? `/?${query}` : "/";
}
```

**Phase 28 application (D-03):** Reuse `buildBoardHref({ ...filters, city: null, page: 1, vaga: null })` for obsolete-city cleanup. Keep URL as single filter state source. If cleanup happens in RSC, `redirect()` to cleaned href; if client fallback, `router.replace` with `scroll:false`.

---

### `frontend/app/(public)/page.tsx` (page/RSC, request-response)

**Analog:** `frontend/app/(public)/page.tsx` (self)

**RSC fetch/render pattern** (lines 1-40, 50-93):
```tsx
import Link from "next/link";

import { AdSlot } from "@/components/board/AdSlot";
import { isAdsEnabled } from "@/lib/publicEnv";
import { BoardToolbar } from "@/components/board/BoardToolbar";
import { ChatWidget } from "@/components/board/chat/ChatWidget";
import { JobGrid } from "@/components/board/JobGrid";
import { Pagination } from "@/components/board/Pagination";
import {
  buildBoardHref,
  hasActiveFilters,
  isUuid,
  PAGE_SIZE,
  normalizeFilters,
} from "@/lib/filters";
import { fetchBoard, fetchJob } from "@/lib/jobs";

type BoardSearchParams = Promise<
  Record<string, string | string[] | undefined>
>;

// ...
export default async function Page({
  searchParams,
}: {
  searchParams: BoardSearchParams;
}) {
  const sp = await searchParams;
  const filters = normalizeFilters(sp);

  // D-10a/B-04: `normalizeFilters` is still the only parser, but the raw value
  // is validated at the fetch boundary so a malformed id can reach the
  // server-rendered not-found panel instead of being silently dropped.
  const rawVaga = filters.vaga?.trim() || null;
  const vaga = rawVaga && isUuid(rawVaga) ? rawVaga : null;
  const malformedVaga = Boolean(rawVaga && !vaga);

  // A valid id resolves in parallel with the list: a shared link must open the
  // job even when the current filter/page would not include it.
  const [data, initialJob] = vaga
    ? await Promise.all([fetchBoard(filters), fetchJob(vaga)])
    : [await fetchBoard(filters), null];

  // ...
  return (
    // ...
            <BoardToolbar filters={filters} total={data.total} />
    // ...
  );
}
```

**Phase 28 application (D-03/D-04):** Pass `availableCities={data.available_cities}` to `BoardToolbar`. For D-03, detect obsolete selected city against `data.available_cities` before rendering stale filtered state. Research recommends server-side canonicalization/redirect to cleaned URL; planner should confirm. Preserve existing parallel `vaga` fetch behavior and `cache: "no-store"` semantics in `fetchBoard`.

---

### `frontend/components/board/BoardToolbar.tsx` (component, event-driven/UI state)

**Analog:** `frontend/components/board/BoardToolbar.tsx` (self)

**Client component + URL commit pattern** (lines 1-37, 116-140):
```tsx
"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { CITY_OPTIONS, resolveCitySlugFromText } from "@/lib/cities";
import { buildBoardHref, type Filters } from "@/lib/filters";
import { formatJobCount } from "@/lib/format";

interface BoardToolbarProps {
  filters: Filters;
  total: number;
}

const DEBOUNCE_MS = 300;

// ...
export function BoardToolbar({ filters, total }: BoardToolbarProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const [value, setValue] = useState(filters.q);
  const lastCommittedRef = useRef(filters.q);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const commit = (patch: Partial<Filters>) => {
    const next = { ...filters, page: 1, vaga: null, ...patch };
    startTransition(() => {
      router.replace(buildBoardHref(next), { scroll: false });
    });
  };
```

**City chip pattern** (lines 174-209):
```tsx
      <div
        role="group"
        aria-label="Filtrar por cidade"
        className="-mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] sm:mx-0 sm:flex-wrap sm:overflow-visible"
      >
        <button
          type="button"
          aria-pressed={filters.city === null}
          onClick={() => commit({ city: null })}
          className={
            filters.city === null
              ? "min-h-11 shrink-0 rounded-full bg-accent-strong px-4 text-sm font-semibold text-white"
              : "min-h-11 shrink-0 rounded-full border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft"
          }
        >
          Todas
        </button>
        {CITY_OPTIONS.map((option) => {
          const active = filters.city === option.slug;
          return (
            <button
              key={option.slug}
              type="button"
              aria-pressed={active}
              onClick={() => commit({ city: option.slug })}
              className={
                active
                  ? "min-h-11 shrink-0 rounded-full bg-accent-strong px-4 text-sm font-semibold text-white"
                  : "min-h-11 shrink-0 rounded-full border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft"
              }
            >
              {option.label}
            </button>
          );
        })}
      </div>
```

**Native sort pattern to replace** (lines 211-238):
```tsx
      <div className="mt-3 flex items-center justify-between gap-3">
        {total > 0 ? (
          <p
            aria-live="polite"
            role="status"
            className="text-sm text-fg-muted"
          >
            {formatJobCount(total)}
          </p>
        ) : (
          <span />
        )}
        <label className="sr-only" htmlFor="board-sort">
          Ordenar por
        </label>
        <select
          id="board-sort"
          aria-label="Ordenar por"
          value={filters.sort}
          onChange={(event) =>
            commit({ sort: event.target.value as Filters["sort"] })
          }
          className="h-11 w-40 rounded-lg border border-line-strong bg-canvas px-3 text-sm text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
        >
          <option value="recentes">Mais recentes</option>
          <option value="antigas">Mais antigas</option>
        </select>
      </div>
```

**Phase 28 application (D-01..D-12):** Add `availableCities: string[]` prop; render `Todas` + only active `CITY_OPTIONS`. Keep URL `commit()` as single state writer. Replace native `<select>` with accessible custom listbox/button (D-05/D-06). Apply D-07/D-08/D-10/D-11/D-12 hover/focus/active classes using existing tokens. Preserve `aria-label="Ordenar por"` and result count semantics.

---

### `frontend/components/board/SortDropdown.tsx` (component, event-driven/UI state) — NEW

**Analog:** No direct listbox analog in repo; closest patterns are `BoardToolbar` URL commit and `JobCard`/toolbar button hover/focus classes.

**Closest button/focus pattern** (`frontend/components/board/JobCard.tsx`, lines 97-105):
```tsx
        <button
          type="button"
          onClick={(event) => onOpen(job, event.currentTarget)}
          aria-label={`Ver a vaga: ${job.title}`}
          className="inline-flex h-11 w-full items-center justify-center rounded-lg border border-line-strong text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
        >
          Ver a vaga
        </button>
```

**Phase 28 application (D-05/D-06/D-07/D-08):** Implement local button+listbox with `aria-haspopup="listbox"`, `aria-expanded`, `aria-controls`, option `role="option"`, `aria-selected`; ArrowUp/Down, Enter/Space, Escape, outside click, close on select, focus return to trigger. No new dependency. Keep labels `Mais recentes`/`Mais antigas`, values `recentes`/`antigas`.

---

### `frontend/components/board/JobCard.tsx` (component, event-driven/UI state)

**Analog:** `frontend/components/board/JobCard.tsx` (self)

**Card container hover pattern** (lines 38-47):
```tsx
  return (
    <article className="flex h-full flex-col gap-3 rounded-[12px] border border-line bg-surface p-4 transition-colors hover:border-accent focus-within:border-accent">
      {company ? (
        <p className="text-sm text-fg-muted [overflow-wrap:anywhere]">
          {company}
        </p>
      ) : null}

      <h2 className="line-clamp-2 text-xl font-semibold leading-tight [overflow-wrap:anywhere] [text-wrap:balance]">
        {job.title}
      </h2>
```

**CTA button pattern** (lines 96-105):
```tsx
      <div className="mt-auto pt-1">
        <button
          type="button"
          onClick={(event) => onOpen(job, event.currentTarget)}
          aria-label={`Ver a vaga: ${job.title}`}
          className="inline-flex h-11 w-full items-center justify-center rounded-lg border border-line-strong text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
        >
          Ver a vaga
        </button>
      </div>
```

**Phase 28 application (D-09/D-12):** Increase card hover to medium intensity by adding subtle background cue (e.g. `hover:bg-[rgba(139,92,246,0.04)]` or token-equivalent) while keeping `hover:border-accent` and `focus-within:border-accent`. No layout shift: do not change border width/padding/size.

---

### `frontend/components/board/JobGrid.tsx` (component, event-driven/UI state)

**Analog:** `frontend/components/board/JobGrid.tsx` (self)

**Grid/list pattern** (lines 66-83):
```tsx
  return (
    <>
      <ul className="grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2 sm:gap-6 lg:grid-cols-2 xl:grid-cols-3">
        {jobs.map((job, index) => (
          <>
            <li key={job.id} className="h-full min-w-0">
              <JobCard job={job} onOpen={handleOpen} />
            </li>
            {(index + 1) % 6 === 0 && index + 1 < jobs.length ? (
              <AdSlot key={`ad-${index}`} variant="inline" />
            ) : null}
          </>
        ))}
      </ul>
      {selected ? (
        <JobDetailDialog job={selected} open onClose={handleClose} />
      ) : null}
    </>
  );
```

**Phase 28 application:** Likely no code change. Verify hover/focus on cards/sort does not cause layout shift or regress grid rendering.

---

### `frontend/app/(public)/public.css` (config/style, transform)

**Analog:** `frontend/app/(public)/public.css` (self)

**Token + base accessibility pattern** (lines 8-62):
```css
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

@layer base {
  html { color-scheme: dark; }
  body { background: var(--color-canvas); color: var(--color-fg); ... }
  :focus-visible { outline: 2px solid var(--color-accent-soft); outline-offset: 2px; }
  @media (prefers-reduced-motion: reduce) { ... transition-duration: 0.01ms !important; ... }
  :focus:not(:focus-visible) { outline: none; }
}
```

**Existing hover pattern** (lines 64-73):
```css
@layer components {
  @media (hover: hover) and (pointer: fine) {
    .job-card:hover {
      border-color: var(--color-accent);
    }
  }

  .job-card:focus-within {
    border-color: var(--color-accent);
  }
}
```

**Phase 28 application (D-09/D-12):** Prefer Tailwind utilities on components; `public.css` may remain unchanged unless planner needs a shared class. If adding hover bg to card, keep it subtle and consistent with existing tokens. Do not introduce new color tokens.

## Shared Patterns

### Published/Active Visibility (backend, D-01/D-02)
**Source:** `backend/app/crud/jobs.py` lines 27-38
**Apply to:** `list_published` filters and new active-cities query.
```python
filters: list = [Job.status == JobStatus.published, Job.expires_at > func.now()]
```
Active cities must be computed from published+non-expired jobs only, independent of `q/city/sort`.

### Contact-Free Public Contract (backend/frontend, D-04, PUBL-05/D-18)
**Source:** `backend/app/schemas/job.py` lines 29-54; `frontend/lib/api.ts` lines 5-83
**Apply to:** `JobListResponse` extension and all public board tests.
```python
# NO contact_email / contact_phone (D-18).
```
```ts
export interface JobListResponse {
  items: JobPublic[];
  page: number;
  limit: number;
  total: number;
}
```
Extend with `available_cities` only; never add contact fields.

### URL as Single Filter State Source (frontend, D-03)
**Source:** `frontend/lib/filters.ts` lines 72-92; `frontend/components/board/BoardToolbar.tsx` lines 32-37
**Apply to:** obsolete selected-city cleanup, chip clicks, sort selection.
```ts
const next = { ...filters, page: 1, vaga: null, ...patch };
startTransition(() => {
  router.replace(buildBoardHref(next), { scroll: false });
});
```
```ts
export function buildBoardHref(filters: Filters): string { ... return query ? `/?${query}` : "/"; }
```
D-03 should clear `city` and reset `page/vaga` to avoid stale empty state.

### Focus-Visible / Reduced Motion / Token Language (frontend, D-12)
**Source:** `frontend/app/(public)/public.css` lines 38-57
**Apply to:** sort trigger, sort options, city chips, job card.
```css
:focus-visible {
  outline: 2px solid var(--color-accent-soft);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### Test Patterns

**Backend public contract/integration test pattern** (`backend/tests/test_public_api.py`, lines 16-33):
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


async def test_list_payload_has_no_contact_fields(client, seed_published_job):
    resp = await client.get("/api/v1/public/jobs")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items, "expected at least one published job"
    for item in items:
        assert "contact_email" not in item
        assert "contact_phone" not in item
```

**Frontend lib unit test pattern** (`frontend/lib/cities.test.ts`, lines 1-13):
```ts
import { describe, expect, it } from "vitest";

import { resolveCitySlugFromText } from "@/lib/cities";

describe("resolveCitySlugFromText", () => {
  it("resolves supported cities by label/canonical/slug case and accent insensitively", () => {
    expect(resolveCitySlugFromText("São Paulo")).toBe("sao-paulo");
    expect(resolveCitySlugFromText("sao paulo")).toBe("sao-paulo");
    expect(resolveCitySlugFromText("SAO-PAULO")).toBe("sao-paulo");
  });
});
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `frontend/components/board/SortDropdown.tsx` (if extracted) | component | event-driven/UI state | No existing custom listbox/dropdown pattern in repo. Closest analogs are `BoardToolbar.tsx` (URL commit/state) and `JobCard.tsx` (button/focus/hover classes). Implement per D-05/D-06 and 28-UI-SPEC Interaction Contract; no new dependency. |

## Metadata

**Analog search scope:** `.planning/phases/28-polimento-ux-da-home/*`, `backend/app/{api/v1,crud,schemas,services}`, `frontend/{app/(public),components/board,lib}`, `backend/tests/test_public_*.py`, `frontend/lib/*.test.ts`
**Files scanned:** 20+ targeted reads/greps (phase docs + key implementation/test files)
**Pattern extraction date:** 2026-11-22
