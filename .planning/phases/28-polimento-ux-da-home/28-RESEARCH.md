# Phase 28: Polimento UX da Home - Research

**Researched:** 2026-11-22
**Domain:** Next.js 16 App Router public board UX polish + FastAPI/SQLAlchemy board contract extension
**Confidence:** HIGH

## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Fonte das cidades ativas
- **D-01:** O filtro de cidades considera vagas publicadas/ativas **no geral** do board, independentemente da busca atual (`q`). O conjunto de cidades não deve mudar enquanto o usuário digita/refina a busca textual.
- **D-02:** Cidades sem vagas publicadas/ativas no momento **não aparecem** no filtro (chip oculto).
- **D-03:** Se a URL já tiver uma cidade selecionada e ela ficar sem vagas ativas/publicadas, o filtro de cidade deve ser **limpo da URL** e o board deve voltar ao estado amplo (sem filtro de cidade), evitando tela vazia por filtro obsoleto.
- **D-04:** A lista de cidades ativas deve vir **junto com a resposta do board** (`GET /api/v1/public/jobs`), na mesma carga usada pela home, para manter consistência com os dados publicados/ativos exibidos.

#### Hover do sort Recentes/Antigos
- **D-05:** O controle de ordenação deixa de ser `<select>` nativo e passa a ser um **dropdown custom acessível** (listbox/button), permitindo estilizar hover/focus nas opções e atender literalmente ao critério de hover nas opções.
- **D-06:** A interação do dropdown custom deve seguir o padrão de **listbox simples**: botão abre lista abaixo, opção ativa marcada, hover/focus visíveis; fecha ao selecionar, ao clicar fora e com `Escape`; mantém navegação por teclado acessível.
- **D-07:** O controle de ordenação fechado deve ter feedback de hover com **borda/realce accent** (alinhado aos inputs/chips). O estado ativo/aberto pode manter destaque coerente.
- **D-08:** O feedback de hover/focus das opções do sort deve ser **consistente com os chips de cidade**, usando a mesma linguagem visual (accent, borda/texto, fundo sutil), adaptada ao formato de menu/lista.

#### Intensidade do hover visual
- **D-09:** Cards de vaga recebem hover de intensidade **média**: borda accent + leve mudança de fundo/sombra sutil, mantendo o visual minimalista dark/roxo.
- **D-10:** Chips de cidade **ativos** recebem hover leve (leve escurecimento/realce do fundo accent), mantendo legibilidade e indicando interatividade.
- **D-11:** Chips de cidade **inativos** recebem hover reforçado leve: mantém borda/texto accent e adiciona fundo sutil no hover.
- **D-12:** A linguagem de hover deve ser **consistente** entre cards, chips e sort (accent, transição suave, foco visível), com intensidade adaptada por componente.

### OpenCode's Discretion

- Nome/formato exato do campo de cidades ativas no payload do board (ex.: `available_cities`) e ajuste correspondente nos tipos frontend/backend, desde que a fonte venha na mesma resposta do board (D-04).
- Implementação da query backend para cidades ativas (distinct sobre vagas publicadas e não expiradas), sem alterar a semântica pública existente.
- Estratégia de acessibilidade ARIA do dropdown custom (atributos de listbox/button, foco inicial, roving tabindex/active descendant), desde que cumpra D-05/D-06.
- Valores exatos de sombra/fundo/transição no hover, respeitando tokens existentes em `frontend/app/(public)/public.css` e o tema dark/roxo.
- Comportamento visual exato quando o filtro selecionado é limpo por D-03 (ex.: transição suave/replace de URL) sem introduzir fricção.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CITY-01 | Usuário vê no filtro de cidades da home apenas cidades que possuem vagas publicadas/ativas no momento | `available_cities` in `GET /api/v1/public/jobs` response (D-04), backend distinct published/non-expired city query independent of `q` (D-01), toolbar renders only active chips (D-02), obsolete selected city URL cleanup (D-03) |
| UIUX-01 | Usuário recebe feedback visual de hover em dropdown recentes/antigos, cards de vaga e filtros de cidades | Custom accessible sort listbox replacing native `<select>` (D-05/D-06), accent hover language aligned across sort trigger/options, city chips and job cards (D-07-D-12), existing `public.css` tokens and reduced-motion behavior |

## Project Constraints (from AGENTS.md)

- **Tech stack — Frontend:** Next.js 16 (App Router, `16.4.6`) + Tailwind CSS + dark mode. [CITED: AGENTS.md]
- **Tech stack — Backend:** FastAPI (Python). [CITED: AGENTS.md]
- **Banco:** Neon (Postgres gratuito). [CITED: AGENTS.md]
- **Idioma/Locale:** Português (Brasil), datas e textos em pt-BR. [CITED: AGENTS.md]
- **Design:** dark mode minimalista; roxo principal (#8b5cf6 / #a78bfa); fundos escuros (#0f0a1a / #1a1025); botão Doações amarelo (#facc15) discreto. [CITED: AGENTS.md]
- **Core value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção. [CITED: AGENTS.md]
- **Contrato público sem contato:** `JobPublic`/`JobListResponse` must not expose contact fields. [VERIFIED: backend/app/schemas/job.py, backend/tests/test_public_api.py]
- **GSD workflow:** File-changing work should go through GSD workflow; this is a research artifact only. [CITED: AGENTS.md]

## Summary

Phase 28 is a focused polish phase on the existing public board: it makes the city filter reflect only currently published/active jobs and adds consistent hover feedback to the sort control, city chips, and job cards. The codebase already has the right seams: `GET /api/v1/public/jobs` is the single board payload, `BoardToolbar` owns filter UI state via URL, and `public.css` already defines the dark/roxo tokens and focus-visible/reduced-motion rules.

The main technical work is additive contract extension plus a small accessible UI refactor. Backend needs a published/non-expired distinct-city query independent of request `q/city/sort` filters and must return it in the same `JobListResponse` (D-04). Frontend needs to propagate `available_cities`, render only active city chips in stable `CITY_OPTIONS` order (D-01/D-02), clear an obsolete selected city from the URL to avoid a stale empty state (D-03), and replace the native sort `<select>` with an accessible button/listbox dropdown (D-05/D-06) while applying the UI-SPEC hover language (D-07-D-12).

**Primary recommendation:** Extend `JobListResponse` with `available_cities: string[]` (supported slugs, stable `CITY_OPTIONS` order), compute it with a dedicated published+non-expired distinct query that ignores `q/city/sort`, and handle D-03 as a server-side canonicalization/redirect before rendering stale filtered results; implement the sort control as a small local accessible listbox component with no new dependencies.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Active city computation (published, non-expired, general board) | API / Backend | Database / Storage | Active-city truth is data/query semantics; SQLAlchemy/Postgres should compute distinct published/non-expired cities. |
| Board payload extension (`available_cities`) | API / Backend | Frontend Server (SSR) | Backend owns response contract; RSC consumes the same payload for initial render. |
| Obsolete selected-city URL cleanup (D-03) | Frontend Server (SSR) | Browser / Client | Server must avoid fetching/rendering a stale empty board; URL canonicalization belongs at route boundary, with client replacement as fallback only if needed. |
| City chip rendering/filter state | Browser / Client | Frontend Server (SSR) | `BoardToolbar` is a client component that writes URL filters via `router.replace`. |
| Custom sort dropdown interaction/a11y | Browser / Client | — | Keyboard, focus, outside click, Escape, hover/focus states are DOM interaction concerns. |
| Hover visual feedback | Browser / Client | CDN / Static | Tailwind classes/tokens in public CSS define visual state; no backend involvement. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| Next.js (App Router) | 16.4.6 | Public board RSC + client interactions | Already used by `frontend/app/(public)/page.tsx` and board components; SSR fetch + client URL updates fit phase scope. [VERIFIED: frontend/package.json] | HIGH |
| React | 19.1.1 | Client component state/effects for toolbar/dropdown | Existing `BoardToolbar`/`JobCard`/`JobGrid` are React client components. [VERIFIED: frontend/package.json] | HIGH |
| Tailwind CSS | 4.3.3 | Hover/focus/border/background utilities | Existing board styles use Tailwind utilities + `public.css` tokens. [VERIFIED: frontend/package.json, frontend/app/(public)/public.css] | HIGH |
| FastAPI | 0.143.0 | Public board endpoint contract | Existing `GET /api/v1/public/jobs` endpoint and Pydantic response models. [CITED: AGENTS.md; VERIFIED: backend/app/api/v1/public.py] | HIGH |
| Pydantic v2 | 2.14.1 | Response schema extension | `JobListResponse`/`JobPublic` schemas enforce public contract. [CITED: AGENTS.md; VERIFIED: backend/app/schemas/job.py] | HIGH |
| SQLAlchemy 2.x async | 2.1.4 | Published/active distinct city query | Existing CRUD uses SQLAlchemy async `select/func` and shared published filters. [CITED: AGENTS.md; VERIFIED: backend/app/crud/jobs.py] | HIGH |

### Supporting
| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| pytest | 9.1.1 (stack) / repo-configured | Backend contract/regression tests | Extend `backend/tests/test_public_api.py` or `test_public_search.py` for `available_cities` and D-01/D-03 semantics. [CITED: AGENTS.md; VERIFIED: backend/tests/*] | HIGH |
| Vitest | ^2.1.9 | Frontend unit tests for pure helpers | Use for `cities`/`filters` pure logic if planner extracts helper; current config only includes `lib/**/*.test.ts`. [VERIFIED: frontend/package.json, frontend/vitest.config.ts] | HIGH |
| Playwright | 1.64.0 (stack) | E2E smoke for hover/dropdown/a11y | Optional/manual or future automation; not currently wired as a phase-local test in repo scan. [CITED: AGENTS.md; ASSUMED] | MEDIUM |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Local accessible listbox component | Radix UI / Headless UI / shadcn select | Would speed a11y, but adds dependency and conflicts with phase's "no new component library need" / no shadcn initialization. [VERIFIED: 28-UI-SPEC.md Design System] |
| Separate `/public/cities` endpoint | Field in `GET /public/jobs` response | Simpler isolation, but violates D-04 and risks inconsistency/stale extra request. [VERIFIED: 28-CONTEXT.md D-04] |
| Client-only D-03 cleanup | RSC redirect/canonical fetch | Client-only is easy but can briefly render stale empty results because server fetched obsolete city; RSC redirect avoids dead-end. [VERIFIED: frontend/app/(public)/page.tsx is RSC; ASSUMED redirect behavior] |

**Installation:**
```bash
# No new packages required for Phase 28.
# Existing stack already covers backend contract, RSC fetch, Tailwind styling, and tests.
```

**Version verification:** Versions above are from repository manifests/stack docs, not live registry checks in this session. [VERIFIED: frontend/package.json; CITED: AGENTS.md]

## Architecture Patterns

### System Architecture Diagram

```text
Browser URL (?q&city&sort&page&vaga)
        │
        ▼
frontend/app/(public)/page.tsx (RSC)
  - normalizeFilters(searchParams)
  - fetchBoard(filters) ───────────────► GET /api/v1/public/jobs (FastAPI)
  - receives JobListResponse             - validates q/city/sort/page
      {items,page,limit,total,            - list_published(..., q, city, sort)
       available_cities}                  - list_active_cities()  [NEW, D-01/D-04]
  - if selected city obsolete (D-03)      - returns same response payload
      redirect(/...?without city)
        │
        ▼
BoardToolbar (client)
  - renders only available city chips (D-02)
  - commits URL via router.replace (existing)
  - custom sort listbox button+options (D-05-D-08)
        │
        ▼
JobGrid / JobCard (client)
  - medium hover border/bg cue (D-09, D-12)
  - focus-visible/reduced-motion preserved by public.css
```

### Recommended Project Structure
```text
backend/app/
├── api/v1/public.py            # extend GET /public/jobs response assembly
├── crud/jobs.py                # add published/active distinct city query
├── schemas/job.py              # extend JobListResponse
└── services/cities.py          # optional canonical->slug helper for available_cities

frontend/
├── app/(public)/page.tsx       # propagate available_cities; D-03 canonicalization
├── components/board/
│   ├── BoardToolbar.tsx        # active chips + custom sort dropdown
│   ├── JobCard.tsx             # hover intensity update
│   └── JobGrid.tsx             # verify no layout shift/regression
└── lib/
    ├── api.ts                  # JobListResponse type extension
    ├── jobs.ts                 # fetchBoard returns extended response
    ├── filters.ts              # reuse URL helpers for D-03 cleanup
    └── cities.ts               # CITY_OPTIONS order/slug mapping
```

### Pattern 1: Additive Board Contract Extension
**What:** Extend `JobListResponse` with a new backward-compatible field while keeping existing fields and contact-free guarantees unchanged.
**When to use:** D-04 requires active cities in the same board response.
**Example:**
```python
# Source: [VERIFIED: backend/app/schemas/job.py, backend/app/api/v1/public.py]
class JobListResponse(BaseModel):
    items: list[JobPublic]
    page: int
    limit: int
    total: int
    available_cities: list[str] = Field(default_factory=list)
```

### Pattern 2: General Active-City Query, Separate from Search Filters
**What:** Compute available cities using only published/non-expired semantics; do not apply `q`, selected `city`, or `sort`.
**When to use:** D-01/D-02.
**Example:**
```python
# Source: [VERIFIED: backend/app/crud/jobs.py _published_filters pattern]
stmt = (
    select(Job.city)
    .where(Job.status == JobStatus.published, Job.expires_at > func.now())
    .distinct()
)
rows = (await session.scalars(stmt)).all()
# map canonical DB city -> supported slug; return in CITY_OPTIONS order
```

### Pattern 3: URL as Single Filter State Source + Obsolete-City Canonicalization
**What:** Keep filter state in URL. If URL contains a city slug that is no longer active, clean it and show broad state.
**When to use:** D-03.
**Example:**
```ts
// Source: [VERIFIED: frontend/lib/filters.ts, frontend/app/(public)/page.tsx; ASSUMED: next/navigation redirect in RSC]
if (filters.city && !data.available_cities.includes(filters.city)) {
  redirect(buildBoardHref({ ...filters, city: null, page: 1, vaga: null }));
}
```

### Pattern 4: Accessible Button + Listbox Sort Control
**What:** Replace native `<select>` with button trigger and listbox options; manage open state, active option, keyboard, outside click, and Escape.
**When to use:** D-05/D-06/D-07/D-08.
**Example:**
```tsx
// Source: [VERIFIED: 28-UI-SPEC.md Interaction Contracts; ASSUMED: WAI-ARIA APG listbox pattern]
<button
  type="button"
  aria-haspopup="listbox"
  aria-expanded={open}
  aria-controls={listboxId}
>
  {selectedLabel}
</button>
<ul id={listboxId} role="listbox">
  <li role="option" aria-selected={selected}>Mais recentes</li>
</ul>
```

### Anti-Patterns to Avoid
- **Filtering active cities by current `q`:** Violates D-01 and causes confusing chip churn while typing. [VERIFIED: 28-CONTEXT.md D-01]
- **Separate client fetch for cities:** Violates D-04 and can desync with board payload. [VERIFIED: 28-CONTEXT.md D-04]
- **Client-only obsolete-city cleanup after stale fetch:** Can briefly show empty/stale board; handle canonically before stale filtered render when possible. [VERIFIED: 28-CONTEXT.md D-03]
- **Native `<select>` with styled options:** Cannot reliably satisfy option hover styling across browsers; D-05 requires custom accessible dropdown. [VERIFIED: 28-CONTEXT.md D-05]
- **Adding new UI dependency/registry:** Unnecessary for two-option listbox and conflicts with UI-SPEC "no shadcn init / no new component library". [VERIFIED: 28-UI-SPEC.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Published/active job visibility rules | Ad-hoc SQL in route | Reuse `Job.status == published` + `Job.expires_at > func.now()` semantics / existing CRUD patterns | Avoids diverging from board visibility rules. [VERIFIED: backend/app/crud/jobs.py] |
| URL filter parsing/building | Manual query string concatenation in components | `normalizeFilters` / `buildBoardHref` | Existing single source of truth for board URL contract. [VERIFIED: frontend/lib/filters.ts] |
| City slug/label/canonical mapping | New ad-hoc strings in UI | `CITY_OPTIONS` and existing city helpers | Keeps stable order and known slug set. [VERIFIED: frontend/lib/cities.ts] |
| Focus-visible/reduced-motion baseline | Custom global CSS reset | Existing `public.css` tokens and global rules | Already provides accessible defaults. [VERIFIED: frontend/app/(public)/public.css] |

**Key insight:** This phase is contract/UI polish on an established board. Reuse the existing board query and URL contracts; only add the missing active-cities field and the local dropdown interaction.

## Common Pitfalls

### Pitfall 1: Active cities coupled to search query
**What goes wrong:** Chips disappear/reappear as user types `q`, violating D-01.
**Why it happens:** Reusing the filtered `list_published` result or applying `q` to the distinct-cities query.
**How to avoid:** Compute `available_cities` with a dedicated query using only published + non-expired predicates. [VERIFIED: 28-CONTEXT.md D-01; backend/app/crud/jobs.py]
**Warning signs:** Typing a query that matches only one city removes other active city chips.

### Pitfall 2: Obsolete selected city causes empty board
**What goes wrong:** URL keeps `?city=...` for a city with no active jobs; board renders empty/stale state.
**Why it happens:** Only hiding chip in UI without cleaning filter state/fetch.
**How to avoid:** Detect `filters.city not in available_cities`, clear city and reset page/vaga as appropriate, and return broad board state. Prefer RSC redirect/canonical refetch. [VERIFIED: 28-CONTEXT.md D-03, 28-UI-SPEC.md]
**Warning signs:** Manual URL with inactive city shows "Nenhuma vaga encontrada" despite other active jobs.

### Pitfall 3: Inaccessible custom dropdown
**What goes wrong:** Sort looks custom but fails keyboard/screen reader use, regressing accessibility.
**Why it happens:** Missing ARIA attributes, no focus management, no Escape/outside click handling.
**How to avoid:** Implement button+listbox semantics, `aria-expanded`, `aria-controls`, option `aria-selected`, ArrowUp/Down, Enter/Space, Escape closes and restores focus to trigger. [VERIFIED: 28-CONTEXT.md D-05/D-06, 28-UI-SPEC.md]
**Warning signs:** Tab/arrow keys cannot operate menu; screen reader does not announce expanded/selected state.

### Pitfall 4: Hover-only affordance or layout shift
**What goes wrong:** Controls look inactive without hover, or card hover causes jitter/layout movement.
**Why it happens:** Relying on hover only; changing border width/padding/transform.
**How to avoid:** Keep default borders/labels visible; use color/background/shadow transitions only; no size changes. Respect existing `prefers-reduced-motion` global rule. [VERIFIED: frontend/app/(public)/public.css, 28-UI-SPEC.md]
**Warning signs:** Grid/cards jump on hover; keyboard users cannot perceive interactivity.

### Pitfall 5: Public contract leak/regression
**What goes wrong:** Adding `available_cities` accidentally changes existing payload semantics or exposes contact data.
**Why it happens:** Editing shared schema/serialization carelessly.
**How to avoid:** Add only `available_cities: list[str]` to `JobListResponse`; keep `JobPublic` contact-free; extend tests to assert existing fields and no contact fields. [VERIFIED: backend/app/schemas/job.py, backend/tests/test_public_api.py]

## Code Examples

### Backend: extend `JobListResponse`
```python
# Source: [VERIFIED: backend/app/schemas/job.py]
class JobListResponse(BaseModel):
    items: list[JobPublic]
    page: int
    limit: int
    total: int
    available_cities: list[str] = Field(default_factory=list)
```

### Backend: active cities query (general board)
```python
# Source pattern: [VERIFIED: backend/app/crud/jobs.py published filters]
async def list_active_cities(session: AsyncSession) -> list[str]:
    stmt = (
        select(Job.city)
        .where(Job.status == JobStatus.published, Job.expires_at > func.now())
        .distinct()
    )
    rows = list((await session.scalars(stmt)).all())
    # map canonical DB value -> slug, filter supported, return CITY_OPTIONS order
    ...
```

### Frontend: extended board response type
```ts
// Source: [VERIFIED: frontend/lib/api.ts]
export interface JobListResponse {
  items: JobPublic[];
  page: number;
  limit: number;
  total: number;
  available_cities: string[];
}
```

### Frontend: render only active city chips
```tsx
// Source pattern: [VERIFIED: frontend/components/board/BoardToolbar.tsx, frontend/lib/cities.ts]
const activeCityOptions = CITY_OPTIONS.filter((o) =>
  availableCities.includes(o.slug),
);
```

### Frontend: card hover medium intensity
```tsx
// Source: [VERIFIED: frontend/components/board/JobCard.tsx, 28-UI-SPEC.md D-09]
<article className="... border-line bg-surface ... transition-colors hover:border-accent hover:bg-[rgba(139,92,246,0.04)] focus-within:border-accent">
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static city chips (`CITY_OPTIONS.map`) regardless of active jobs | Dynamic chips from board `available_cities` | Phase 28 | Prevents useless filters and stale empty states. [VERIFIED: BoardToolbar.tsx, 28-CONTEXT.md] |
| Native `<select>` for sort | Custom accessible listbox dropdown | Phase 28 | Enables option hover/focus styling and explicit keyboard/a11y behavior. [VERIFIED: 28-CONTEXT.md D-05] |
| Border-only card hover | Medium hover with border + subtle background cue | Phase 28 | Clearer affordance while preserving minimal dark/roxo style. [VERIFIED: JobCard.tsx, 28-UI-SPEC.md D-09] |

**Deprecated/outdated:**
- Native sort `<select>` for this UI requirement: insufficient for option-level hover styling required by UIUX-01/D-05. [VERIFIED: 28-CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Next.js RSC `redirect()` from `next/navigation` is acceptable for D-03 URL canonicalization before render; alternative is client `router.replace` plus server refetch strategy. | Architecture Patterns / Pitfalls | If redirect causes undesirable UX in this route, D-03 may need client-side replacement with careful loading handling. Mitigation: verify in implementation; keep logic centralized. |
| A2 | A small local button+listbox implementation can satisfy D-05/D-06 without adding dependencies, using standard ARIA attributes. | Architecture Patterns | If keyboard/focus edge cases are missed, a11y regression. Mitigation: follow UI-SPEC contract and add focused tests/manual checklist. |
| A3 | `available_cities` should return supported slugs in `CITY_OPTIONS` order, as resolved by UI-SPEC discretion. | Standard Stack / Architecture | If backend/frontend expect canonical labels instead, mapping bugs occur. Mitigation: lock contract in schema/types/tests. |
| A4 | Vitest remains lib-only (`lib/**/*.test.ts`) per current config; component-level tests may require config adjustment or be deferred to manual/E2E. | Validation Architecture | Validation may miss dropdown interaction regressions. Mitigation: add pure helper tests + manual accessibility checks; optionally extend Vitest config if planner chooses. |

## Open Questions

1. **Where should D-03 obsolete-city cleanup run?**
   - What we know: D-03 requires URL cleared and broad board state; UI-SPEC allows `router.replace` or equivalent; page is RSC and fetches filtered board. [VERIFIED: 28-CONTEXT.md, 28-UI-SPEC.md, page.tsx]
   - What's unclear: Best UX in Next 16 between server `redirect()` and client effect replacement.
   - Recommendation: Prefer server-side canonicalization (redirect to cleaned URL) before rendering stale filtered results; if redirect is unsuitable, fetch broad data when city obsolete and emit client replace. Planner should pick one and test no empty flash.

2. **How should backend map canonical DB cities to slugs?**
   - What we know: DB stores canonical accented names; frontend expects slugs in `CITY_OPTIONS`; backend has `CITY_ALIASES` canonical resolver only. [VERIFIED: crud/jobs.py, services/cities.py, cities.ts]
   - What's unclear: Whether to add canonical->slug map in backend service or return canonical and map in frontend.
   - Recommendation: Return slugs as per UI-SPEC (`available_cities` slug array). Add a small explicit canonical->slug mapping in backend `services/cities.py` to keep contract clear.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend build/tests | ✓ | `v22.17.0` | — |
| npm | Frontend package scripts | ✓ | `11.5.2` | — |
| Python | Backend tests/runtime | ✓ | `3.13.5` | — |
| Postgres test DB (`TEST_DATABASE_URL`/`DATABASE_URL`) | Backend pytest DB integration tests | Unknown in this session | — | Run non-DB unit tests where possible; CI/dev env provides DB per conftest behavior. |

**Missing dependencies with no fallback:**
- None identified. Postgres availability is environment-dependent but test harness already skips DB-dependent tests when unconfigured. [VERIFIED: backend/tests/conftest.py]

**Missing dependencies with fallback:**
- Postgres test DB unavailable locally: backend DB tests skipped by conftest; use focused logic review and run in DB-enabled environment. [VERIFIED: backend/tests/conftest.py]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Backend: pytest + pytest-asyncio/httpx ASGITransport; Frontend: Vitest ^2.1.9 (node env) |
| Config file | Backend: `backend/tests/conftest.py`, `backend/pytest.ini`/pyproject (if present); Frontend: `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm test -- --run lib/cities.test.ts` |
| Full suite command | `cd backend && pytest tests/test_public_api.py tests/test_public_search.py -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CITY-01 | `GET /api/v1/public/jobs` includes `available_cities` with supported slugs in stable order; independent of `q`; excludes cities with no published/non-expired jobs | integration | `cd backend && pytest tests/test_public_api.py tests/test_public_search.py -q -k available_cities` | ❌ Wave 0 |
| CITY-01 | Obsolete selected city is cleaned and board returns broad state (no stale empty dead-end) | integration/manual | `cd backend && pytest tests/test_public_search.py -q -k obsolete_city` (if backend handles) / manual browser check | ❌ Wave 0 |
| UIUX-01 | Sort control exposes accessible button/listbox, keyboard/escape/outside click, and visible hover/focus states | manual/a11y (or component test if harness added) | Manual: keyboard + hover checklist on `/` | ❌ Wave 0 |
| UIUX-01 | City chips and job cards show specified hover/focus states without layout shift | manual visual | Manual: desktop pointer:fine hover on chips/cards | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd frontend && npm test -- --run lib/cities.test.ts`
- **Per wave merge:** `cd backend && pytest tests/test_public_api.py tests/test_public_search.py -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_public_search.py` or `backend/tests/test_public_api.py` — add `available_cities` contract tests (D-01/D-02/D-04), ensuring no contact leakage and independence from `q`.
- [ ] `frontend/lib/cities.test.ts` or new `frontend/lib/filters.test.ts` — cover slug/order mapping helper for active cities and obsolete-city cleanup helper if extracted.
- [ ] Frontend component test harness gap: `frontend/vitest.config.ts` includes only `lib/**/*.test.ts` and environment is `node`; no React Testing Library setup for BoardToolbar/JobCard interaction tests. If planner wants automated UIUX-01 tests, add component test config/deps.
- [ ] Manual accessibility checklist artifact for custom listbox (keyboard, aria-expanded/selected, Escape/outside click, focus return).

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth changes; public board only. [VERIFIED: phase scope] |
| V3 Session Management | no | No session changes. [VERIFIED: phase scope] |
| V4 Access Control | no | Public endpoint remains anonymous; no admin path changes. [VERIFIED: backend/app/api/v1/public.py] |
| V5 Input Validation | yes | Keep existing query param validation/whitelisting (`normalizeFilters`, FastAPI Query constraints, `resolve_city/resolve_sort`). `available_cities` is server-derived, not user input. [VERIFIED: filters.ts, public.py] |
| V6 Cryptography | no | No crypto/secrets changes. [VERIFIED: phase scope] |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Public payload data leak when extending response | Information Disclosure | Extend `JobListResponse` only with `available_cities`; keep `JobPublic` contact-free and assert absence in tests. [VERIFIED: schemas/job.py, test_public_api.py] |
| Obsolete filter causing confusing/abusable empty state | Tampering/DoS-ish UX degradation | Canonicalize/clear invalid obsolete selected city; ensure broad state. [VERIFIED: D-03] |
| Inaccessible custom control | Spoofing/Repudiation of UI intent (usability/a11y) | Implement standard listbox keyboard/ARIA semantics and visible focus states. [VERIFIED: D-05/D-06, public.css focus-visible] |

## Sources

### Primary (HIGH confidence)
- [VERIFIED: .planning/phases/28-polimento-ux-da-home/28-CONTEXT.md] - locked decisions D-01..D-12, discretion, deferred.
- [VERIFIED: .planning/phases/28-polimento-ux-da-home/28-UI-SPEC.md] - approved draft UI contract, data contract, interaction/verification expectations.
- [VERIFIED: .planning/REQUIREMENTS.md] - CITY-01, UIUX-01 requirement definitions.
- [VERIFIED: .planning/ROADMAP.md] - Phase 28 goal, dependencies, success criteria.
- [VERIFIED: frontend/components/board/BoardToolbar.tsx] - current native sort, static city chips, URL commit behavior.
- [VERIFIED: frontend/components/board/JobCard.tsx] - current hover/focus-within styling.
- [VERIFIED: frontend/components/board/JobGrid.tsx] - grid structure and remount key behavior.
- [VERIFIED: frontend/app/(public)/page.tsx] - RSC board fetch/render flow.
- [VERIFIED: frontend/lib/cities.ts, frontend/lib/filters.ts, frontend/lib/jobs.ts, frontend/lib/api.ts] - city/URL/response contracts.
- [VERIFIED: frontend/app/(public)/public.css] - tokens, focus-visible, reduced-motion, existing hover patterns.
- [VERIFIED: backend/app/api/v1/public.py, backend/app/schemas/job.py, backend/app/crud/jobs.py, backend/app/services/cities.py] - public endpoint, schema, published query semantics, city resolution.
- [VERIFIED: backend/tests/test_public_api.py, backend/tests/test_public_search.py, backend/tests/conftest.py] - existing public contract and DB test patterns.
- [VERIFIED: frontend/package.json, frontend/vitest.config.ts] - frontend test/runtime versions and config.

### Secondary (MEDIUM confidence)
- [CITED: AGENTS.md / project stack constraints] - fixed stack versions/constraints; used where repo manifests do not directly expose backend package versions.

### Tertiary (LOW confidence)
- [ASSUMED] - Next.js RSC `redirect()` UX suitability for D-03 canonicalization; needs implementation-time validation in this app route.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified from repo manifests/code and AGENTS constraints.
- Architecture: HIGH - integration points directly observed in codebase; D-03 redirect choice marked as assumption.
- Pitfalls: HIGH - derived from locked decisions, existing query/URL contracts, and observed code paths.

**Research date:** 2026-11-22
**Valid until:** 2026-12-22 (stable internal UI contract; recheck if UI-SPEC or board contracts change)
