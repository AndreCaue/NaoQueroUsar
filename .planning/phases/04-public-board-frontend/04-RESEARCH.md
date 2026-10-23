# Phase 4: Public Board Frontend - Research

**Researched:** 2026-10-22
**Domain:** Next.js 15 App Router (RSC) + Tailwind v4 + FastAPI/SQLAlchemy search & filter + `<dialog>`/Turnstile reveal UX
**Confidence:** HIGH (stack + codebase), MEDIUM (CSS isolation strategy, city label mapping)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Entrega e fatiamento**
- **D-01:** A fase **não** é dividida em sub-fases. Uma única Phase 4, planejada em **5–6 planos** em ondas: (1) fundação Tailwind v4 + route group público → (2) board + card SSR → (3) modal + reveal + candidatura → (4) backend `q`/`city`/`sort` + busca/filtros/URL → (5) tema/Doações/ADS + polimento. Os 11 requisitos fecham juntos.
- **D-02:** Como a aprovação de vaga é Phase 5, esta fase entrega um **seed local dev-only** (`backend/scripts/seed_public_demo.py` ou equivalente) que insere N vagas `published` com contatos fake e `expires_at` futuro. Regras: só roda com `ENV=dev`/local, **nunca** em produção, não cria endpoint HTTP de seed, e respeita o CHECK `at_least_one_contact`. É o caminho de verificação no browser.

**Busca, filtro e ordenação (SRCH-01..03)**
- **D-03:** `q` procura em **título + empresa + atividades + requisitos**. Cidade tem filtro próprio e **combina com `q` por AND** (não substitui, não preenche `q`).
- **D-04:** A busca usa a coluna **`search_text` já existente** (`backend/app/models/job.py:48`), mantida por trigger `BEFORE INSERT OR UPDATE` com `immutable_unaccent(lower(...))` e indexada por GIN `pg_trgm` parcial (`status='published'`) — tudo criado na migration `0001_initial_jobs.py`. **Não** criar coluna nova e **não** normalizar em Python na escrita.
  - **Lacuna a fechar:** o trigger atual concatena `title + company + activities` e **omite `requirements`**. Uma migration nova (`0003_...`) deve substituir `jobs_set_search_text()` incluindo `coalesce(NEW.requirements,'')` e fazer backfill (`UPDATE jobs SET search_text = ...` ou `UPDATE ... SET title = title` para re-disparar o trigger).
  - A consulta compara `search_text` com `immutable_unaccent(lower(:q))` como substring; o índice trigram já serve. Não introduzir `unaccent(...)` na query (a coluna já está normalizada).
- **D-05:** Params na URL: `q`, `city`, `sort`, `page` (idênticos no front e na API — sem tradução). `city` usa os slugs `sao-paulo | rio-de-janeiro | belo-horizonte | remoto`, mapeados para os valores canônicos de `ALLOWED_CITIES` em `backend/app/services/extraction/extractor.py:56`. **Atenção:** os valores canônicos são **sem acento** (`"Sao Paulo"`, não `"São Paulo"`) — o filtro compara com esses valores.
- **D-06:** `sort` aceita `recentes` (default, `created_at DESC`) e `antigas` (`created_at ASC`), cobrindo SRCH-03. `page` mantém offset; `limit=24` (dentro do `le=50` atual). Filtro de validade (`status='published' AND expires_at > now()`) permanece aplicado em itens **e** no `total`.

**Renderização, cache e URL**
- **D-07:** O board é **Server Component**. A lista é buscada no servidor a partir de `searchParams` e o HTML inicial já contém as vagas (SEO). `q/city/sort/page` disparam re-render no servidor — sem spinner de primeira carga.
- **D-08:** **Sem cache**: `cache: 'no-store'` na leitura do board. Nada de ISR/`revalidateTag`. Justificativa: volume de 100–500 vagas/mês, risco zero de vaga expirada/removida, e evita explosão de variantes de cache com os filtros.
- **D-09:** O card abre um **`<dialog>` nativo** no cliente e grava **`?vaga=<uuid>`** na URL (`history.replaceState`/`router.replace`, preservando `q/city/sort/page`). Carregar a URL com `?vaga=` reabre o modal; um id desconhecido/expirado cai no estado "vaga não encontrada" sem quebrar o board. Fechar o modal remove o param.
- **D-10:** O reveal só monta o widget do Turnstile **no clique** (token vive 300 s e é single-use), com `appearance="interaction-only"` e `id="turnstile-reveal"` (não colide com o `turnstile-widget` do login). O contato revelado fica em memória **por vaga, com escopo de aba** — usar module-scope/context, **não** um `Map` em `useRef` do host do dialog (morre se o grid desmontar).

**Tema, Doações e ADS**
- **D-11:** "Doações" leva a uma rota estática **`/doacoes`** no route group público, com copy honesta ("apoie o projeto — chave PIX em breve") e link de volta. Nunca `#`, nunca botão morto. PIX real é Phase 6.
- **D-12:** ADS nesta fase são **apenas placeholders reservados**: banner topo 90px, sidebar 300×250 (≥1024px) e inline 90px a cada 6 cards — caixa tracejada com rótulo "Publicidade" e **altura fixa** (anti-CLS). Nenhum script de anúncio, nenhum tracking, nenhum cookie de terceiro.

**Contraste e tokens**
- **D-13:** `#a78bfa` é a cor de **texto** de acento e do focus ring; `#8b5cf6` é **marca** (borda/hover/indicador); preenchimento com **texto branco** usa `#7c3aed` (5,70:1) porque `#8b5cf6` reprova AA com branco (4,23:1) — exigência de UIUX-01. Borda de controle `#6d5a91` (3,26:1) no lugar do `#4a3b6b` do admin (1,97:1).

### OpenCode's Discretion
- **Tailwind v4 no route group `(public)`** para que o Preflight não vaze no `/admin/*` (que segue em CSS plano com `globals-admin.css`); shadcn **não** usado; ícones SVG inline. Já aprovado no `04-UI-SPEC.md` (decisão de discrição #1).
- Estrutura de arquivos/componentes do front (`components/` público), nomes de helpers de fetch, e se o fetch do servidor usa `NEXT_PUBLIC_API_URL` ou uma variável server-side.
- Formato do seed dev-only (quantidade de vagas, títulos/cidades variados, guarda de ambiente).
- Paginação visual (controles), skeleton de loading, e detalhes de wiring de foco/aria do `<dialog>`.
- Como `?vaga=` convive com `q/city/sort/page` na montagem do estado inicial.
- Mecânica exata de `immutable_unaccent` na comparação e se o backfill da migration `0003` re-dispara o trigger ou escreve direto.

### Deferred Ideas (OUT OF SCOPE)
- Aprovação/edição/exclusão de vagas no admin (`pending → published`) — Phase 5 (REVW-01..05).
- PIX real / página de doações completa — Phase 6.
- AdSense / anúncios reais, banner de consentimento LGPD e política de privacidade — Phase 6.
- Sitemap, JSON-LD `JobPosting`, OG images.
- Chaves reais do Cloudflare + env vars de deploy — Phase 6.
- Limiter distribuído (Redis/tabela) — Phase 6.
- Página de vaga dedicada `/vagas/[id]` — descartada nesta fase em favor do modal com deep-link.
- `pg_trgm` tuning / busca fuzzy por similaridade.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PUBL-01 | Grade responsiva mobile-first, sem login | §Pattern 1 (RSC fetch), §Pattern 2 (route group + Tailwind), 1/2/4-col grid per UI-SPEC §Breakpoints |
| PUBL-02 | Card: título, início das atividades expansível, salário quando houver, "Ver a vaga" | §Pattern 3 (card anatomy), `JobPublic` field list (verified), §Pitfall "activities overflow" |
| PUBL-03 | Modal de detalhe mobile-friendly | §Pattern 4 (native `<dialog>`), §Pitfall "showModal on server", UI-SPEC §Dialog (bottom sheet 92dvh <640px) |
| PUBL-04 | Contato oculto; revelado por "Mostrar contato" | §Pattern 5 (reveal state machine), Turnstile props verified, §Pitfall "pre-mint token", §Environment (dev mode = `test`, always-pass) |
| PUBL-06 | Candidatura via `wa.me` e/ou `mailto:` | §Pattern 6 (`waHref`/`mailtoHref`), §Pitfall "raw phone has spaces" (verified: seed phone is `+55 11 90000-0000`) |
| SRCH-01 | Busca insensível a acento e caixa | §Pattern 7 (migration 0003 + query expression), §Code Example "SQL match" |
| SRCH-02 | Filtro por cidade (4 valores) | §Pattern 7 (`city` filter + alias dict), §Open Question 2 (label vs canonical) |
| SRCH-03 | Ordenação por data (default recentes) | §Pattern 7 (`sort` + `Job.id` tie-breaker — required for stable paging) |
| UIUX-01 | Dark roxo com contraste AA | §Standard Stack (Tailwind v4 `@theme` from UI-SPEC, verbatim), D-13 contrast rules |
| UIUX-02 | Botão "Doações" amarelo discreto | §Pattern 2 (`/doacoes` under `(public)`), UI-SPEC §F copy |
| UIUX-03 | Espaços reservados de ADS | §Pattern 8 (fixed-height slots), §Pitfall "CLS" |
</phase_requirements>

---

## Summary

Phase 4 is the first phase where the two halves of the repo actually meet: a Next.js 15 App Router front end that today is a 3-file placeholder (`app/page.tsx` prints "em construção"), and a FastAPI backend whose public read surface is finished except for the three query parameters this phase must add (`q`, `city`, `sort`) — a boundary literally marked `# Phase boundary` at `backend/app/api/v1/public.py:32`.

The work splits into four independent risk areas, and they should be planned in that order: **(1) Tailwind v4 + a `(public)` route group** (mechanical, but it silently breaks `/admin/paste` if done wrong); **(2) migration `0003` + `list_published` filters** (the only place correctness is hard — accent folding, wildcard escaping, and a deterministic sort order); **(3) the RSC board + URL state** (fetch caching, `searchParams` as a Promise, and what happens when `?vaga=` names a job not on the current filtered page); **(4) the reveal/contact UX** (native `<dialog>`, Turnstile mounted at click time, tab-scoped contact cache, `wa.me` link building).

Two claims from earlier planning artifacts turned out to be **stale or wrong** and are corrected here: the Phase-3 "Turnstile action binding blocks reveal in dev" blocker is **already fixed in code** (`enforce_action` is only `True` in live mode — `backend/app/deps.py:70`), and `backend/scripts/` is **not** a new directory (it already holds `seed.py`). Both matter to the planner: reveal is verifiable in dev today, and the new seed must add an env guard the existing script lacks.

**Primary recommendation:** Plan five waves in D-01's order, and put the two correctness-bearing pieces (migration `0003` + `list_published` refactor, and the SQL/escaping contract) in a single backend plan with its own tests, ahead of any frontend wiring that depends on them.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Job listing, search, city filter, sort, pagination | **API / Backend** (FastAPI + Postgres) | — | Postgres owns `search_text` + trigram index; filtering in the browser would break `total` and paging |
| `search_text` normalization | **Database / Storage** (trigger + migration) | — | Locked D-04; one normalization authority, index-backed |
| Initial board HTML (SEO) | **Frontend Server (SSR/RSC)** | — | D-07: RSC fetch, filters from `searchParams` |
| Filter/URL state | **Browser / Client** | Frontend Server | Client writes the URL; the server re-renders the list (single source of truth = URL) |
| Modal open/close, focus management, ESC | **Browser / Client** | — | Native `<dialog>`; cannot exist on the server |
| Contact reveal | **API / Backend** (authority) | Browser (trigger) | Backend verifies the Turnstile token (Phase 3); client only mounts the widget |
| Contact cache (per job, tab scope) | **Browser / Client** | — | D-10, module-scope/context |
| `wa.me`/`mailto:` link building | **Browser / Client** | — | Derived from the revealed E.164; never stored |
| ADS slots, donation button | **Browser / Client** (layout) | — | Static markup, no third party (D-12) |
| Seed demo data | **Database / Storage** (script) | — | No HTTP endpoint (D-02) |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next | **15.5.3** (installed) | RSC board, routing, build | Already installed; do **not** upgrade to 16.x in this phase (out of scope, unverified breaking changes) |
| react / react-dom | **19.1.1** (installed) | UI runtime | Pinned by Next 15.5.3 |
| typescript | **5.9.2** (installed) | Types | `strict: true` already on |
| tailwindcss | **4.3.3** (latest, npm-verified) | Styling | Locked stack; CSS-first `@theme` maps 1:1 to the approved token block |
| @tailwindcss/postcss | **4.3.3** (latest, npm-verified) | PostCSS plugin for v4 | The v4 plugin is `@tailwindcss/postcss`, **not** `tailwindcss` |
| postcss | **8.5.31** (latest, npm-verified) | Peer of the plugin | Installed transitively by the plugin, no direct need |
| next-turnstile | **1.0.7** (installed) | Turnstile widget | Already used by `ExtractForm.tsx` |

### Supporting (backend, already installed — verify only)

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| fastapi | 0.143.0 | Query params + validation | `Query(..., max_length=80)` for `q` |
| SQLAlchemy | 2.1.4 | Query composition | 2.0-style `select()`; `or_`/`and_`, `func` |
| asyncpg | 0.32.0 | Driver | Neon pooled URL |
| alembic | 1.20.0 | Migration `0003` | `down_revision = "0002_jobs_source_snippet"` |
| pytest / pytest-asyncio | 9.1.1 | Tests | `asyncio_mode = "auto"`, `testpaths = ["tests"]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Native `<dialog>` | Radix/Headless UI dialog | Adds a dependency for one dialog; native gives ESC, focus trap, `::backdrop`, and inert background for free |
| RSC fetch + URL params | Client `useSWR`/`useEffect` fetch | Breaks SSR/SEO (PUBL-01/D-07) and duplicates state |
| `search_text` + `LIKE` | `to_tsvector`/`pg_trgm similarity()` | Locked by D-04; FTS would need a new index and pt-BR dictionary, similarity is fuzzy (unwanted) |
| `text` search on model | `ILIKE` across 4 columns | Accent-sensitive: SRCH-01 fails ("sao paulo" ≠ "São Paulo") |
| vitest/jsdom for components | Playwright | No runner exists at all today (see Validation Architecture); native `<dialog>` in jsdom is a known gap — don't pick a runner just for the dialog |

**Installation:**
```powershell
# frontend/
npm install -D tailwindcss@4.3.3 @tailwindcss/postcss@4.3.3
```

**Version verification:** `npm view tailwindcss version` → `4.3.3`; `npm view @tailwindcss/postcss version` → `4.3.3`; installed `next@15.5.3`, `react@19.1.1`, `typescript@5.9.2`, `next-turnstile@1.0.7` (read from `frontend/node_modules`). No version in this table is from training data.

---

## Architecture Patterns

### System Architecture Diagram

```
GET /?q=analista&city=sao-paulo&sort=recentes&page=1&vaga=<uuid>
        │
        ▼
┌──────────────────────── Next 15 — Node (RSC) ─────────────────────────┐
│ app/(public)/page.tsx                                                 │
│  1. const sp = await searchParams        → route becomes dynamic (ƒ)  │
│  2. normalizeFilters(sp)  [lib/filters.ts]  whitelist + clamp + trim  │
│  3. fetch(`${API}/api/v1/public/jobs?…`, {cache:"no-store"})          │
│  4. if sp.vaga && !items.some(id)                                     │
│        fetch(`${API}/api/v1/public/jobs/${vaga}`, {cache:"no-store"}) │
│  5. render <Header/> <AdSlot/> <JobGrid items/> <Dialog initialJob/>  │
└───────────────────────────────────────────────────────────────────────┘
        │ HTML (cards + dialog markup + ADS boxes)
        ▼
┌──────────────────────── Browser ──────────────────────────────────────┐
│ JobGrid (client)                                                      │
│  "Ver a vaga" ──► history.replaceState(?vaga=<id>)  (no RSC roundtrip)│
│                └► dialog.showModal()  ← data already in the DOM        │
│  filters ──────► router.replace(?q=…&city=…&page=1)  (RSC re-render)   │
│  dialog close ─► remove ?vaga (replaceState) + restore focus/scroll    │
│                                                                       │
│  "Mostrar contato" ──► mount <Turnstile action="reveal" .../>         │
│      onVerify(token) ──► POST /api/v1/public/jobs/{id}/reveal-contact │
│          200 ─► cache contact by id (tab scope) ─► wa.me / mailto CTA  │
│          403 ─► show detail (pt-BR) + remount widget (key++)          │
│          429 ─► show detail + disable N s (Retry-After)               │
│          404 ─► "Vaga não encontrada ou expirada."                    │
└───────────────────────────────────────────────────────────────────────┘
        │
        ▼
   FastAPI ──► Postgres (search_text GIN trgm, partial WHERE published)
```

### Recommended Project Structure

```
frontend/
├── app/
│   ├── layout.tsx                 # html lang="pt-BR" + import "./globals.css"  (MODIFY)
│   ├── globals.css                # color-scheme + body base  (kept, now imported)
│   ├── (public)/
│   │   ├── layout.tsx             # header/footer/skip-link + import "./public.css"
│   │   ├── public.css             # @import "tailwindcss" + @theme (UI-SPEC block)
│   │   ├── page.tsx               # board RSC (searchParams, fetch, Suspense)
│   │   ├── loading.tsx            # grid skeleton
│   │   ├── error.tsx              # "use client" boundary
│   │   └── doacoes/page.tsx       # static
│   └── admin/paste/…              # UNTOUCHED
├── components/board/
│   ├── JobCard.tsx                # RSC
│   ├── JobGrid.tsx                # "use client" (dialog host + filter state)
│   ├── JobDialog.tsx              # "use client" (native <dialog>)
│   ├── RevealContact.tsx          # "use client" (Turnstile + state machine)
│   ├── FiltersBar.tsx             # "use client" (q/city/sort/page → URL)
│   ├── Pagination.tsx             # client
│   ├── AdSlot.tsx                 # RSC (fixed height)
│   └── icons.tsx                  # 5 inline SVGs
└── lib/
    ├── api.ts                     # EXISTING — add public read + reveal helpers
    ├── jobs.ts                    # server-only fetch helpers (API base URL)
    ├── cities.ts                  # slug ↔ canonical ↔ label
    ├── contacts.ts                # waHref / mailtoHref / validity
    └── format.ts                  # formatDateBR (America/Sao_Paulo)
```

### Pattern 1: RSC data fetch (verified Next 15.5 behaviour)

**What:** `searchParams` is a `Promise`; `fetch` defaults to `auto no cache`, which still **prerenders once at build** if no request-time API is detected — so `cache: "no-store"` is not cosmetic, it is what prevents a frozen build-time snapshot of the job list.

**When to use:** the board page (`app/(public)/page.tsx`).

```tsx
// Source: nextjs.org/docs/app/api-reference/functions/fetch (lastUpdated 2026-08-18)
//         nextjs.org/docs/app/api-reference/file-conventions/page
type BoardSearchParams = {
  q?: string; city?: string; sort?: string; page?: string; vaga?: string;
};

export default async function Page({
  searchParams,
}: { searchParams: Promise<BoardSearchParams> }) {
  const sp = await searchParams;                    // MUST await in Next 15
  const filters = normalizeFilters(sp);             // whitelist + clamp
  const data = await fetchBoard(filters);           // lib/jobs.ts
  …
}

// lib/jobs.ts
const API =
  process.env.BACKEND_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export async function fetchBoard(f: Filters) {
  const qs = new URLSearchParams({ ...toApiParams(f), limit: "24" });
  const res = await fetch(`${API}/api/v1/public/jobs?${qs}`, {
    cache: "no-store",                       // D-08
    signal: AbortSignal.timeout(15_000),
  });
  if (!res.ok) throw new Error(`board ${res.status}`);
  return (await res.json()) as JobListResponse;
}
```

**Why `BACKEND_API_URL` first:** `NEXT_PUBLIC_*` is inlined at **build** time, so a server-side fetch keyed off it silently pins the build machine's URL in production. A non-public var is the correct server seam; the `NEXT_PUBLIC_` fallback keeps today's `.env.local` working unchanged.

### Pattern 2: Tailwind v4 inside a route group, without touching the admin

**What:** Tailwind is imported **only** by `app/(public)/layout.tsx`. Next code-splits layout CSS by route, so a direct hit on `/admin/paste` never downloads it.

**Verified caveat (this is the part that gets skipped):** Next docs state that on client-side navigation it "currently does not remove stylesheets as you navigate between routes which can lead to conflicts" ([nextjs.org/docs/app/getting-started/css](https://nextjs.org/docs/app/getting-started/css), lastUpdated 2026-08-25). So the route group is *isolation by topology*, not a hard guarantee. It is safe **today** because no link goes public → admin. If you want a hard guarantee, import the layers without Preflight instead of the bundle:

```css
/* app/(public)/public.css — HARD isolation variant */
@layer theme, base, components, utilities;
@import "tailwindcss/theme.css" layer(theme);
@import "tailwindcss/utilities.css" layer(utilities);
/* preflight deliberately omitted; add the 3 base rules the board needs */
@layer base {
  *, ::before, ::after { box-sizing: border-box; }
  body { margin: 0; }
}
```

Both subpaths are real exports of `tailwindcss@4.3.3` (`package.json` `exports`: `./preflight.css`, `./theme.css`, `./utilities.css`), and `index.css` is literally `@layer theme, base, components, utilities;` + `@theme default` + Preflight + `@tailwind utilities`. **Recommendation:** use plain `@import "tailwindcss"` (UI-SPEC §38 prescribes it) and add one manual check to the plan ("open `/` then `/admin/paste` via client nav; admin CSS must be unchanged"). Only switch to the layer variant if that check fails.

```js
// frontend/postcss.config.mjs  (new)
const config = { plugins: { "@tailwindcss/postcss": {} } };
export default config;
```

### Pattern 3: `list_published` with filters, one filter list, deterministic order

**What:** Build the predicate list once and reuse it for items **and** `count()` — otherwise `total` and the page contents disagree as soon as a filter is added.

```python
# backend/app/crud/jobs.py — target shape
def _published_filters(*, q: str | None, city: str | None) -> list:
    filters = [Job.status == JobStatus.published, Job.expires_at > func.now()]
    if city:
        filters.append(Job.city == city)
    if q:
        pattern = f"%{escape_like(immutable_unaccent_lower(q))}%"
        filters.append(Job.search_text.like(pattern, escape="\\"))
    return filters

async def list_published(session, *, page=1, limit=20, q=None, city=None, sort="recentes"):
    filters = _published_filters(q=q, city=city)
    order = Job.created_at.asc() if sort == "antigas" else Job.created_at.desc()
    items = (await session.scalars(
        select(Job).where(*filters).order_by(order, Job.id).offset((page-1)*limit).limit(limit)
    )).all()
    total = await session.scalar(select(func.count()).select_from(Job).where(*filters))
    return list(items), int(total or 0)
```

Three non-obvious requirements:
1. **`order_by(order, Job.id)`** — rows created in the same transaction share `now()`, so `created_at` ties are real (the whole test suite inserts inside one transaction; a seed run also inserts in one transaction). Without a tie-breaker, `12, 12, 12` + `limit=1` paging can return the same row twice and skip another.
2. **Backwards-compatible call** — `public.py:33` calls `list_published(session, page=page, limit=limit)` positionally-ish; keep `q/city/sort` keyword-only with defaults so Phase 1–3 tests keep passing.
3. **Filter order** must include `status='published'` literally, because the trigram index is partial (`WHERE status = 'published'`) — searching without it silently drops the index.

### Pattern 4: Migration `0003` — extend the trigger, backfill, keep `updated_at` sane

**What:** `CREATE OR REPLACE FUNCTION jobs_set_search_text()` (same name ⇒ the existing `jobs_search_text_trg` keeps binding), add `requirements`, then backfill.

```python
# backend/alembic/versions/0003_search_text_requirements.py
down_revision = "0002_jobs_source_snippet"

_NEW_BODY = """
CREATE OR REPLACE FUNCTION jobs_set_search_text()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.search_text = immutable_unaccent(lower(
        coalesce(NEW.title, '') || ' ' ||
        coalesce(NEW.company, '') || ' ' ||
        coalesce(NEW.activities, '') || ' ' ||
        coalesce(NEW.requirements, '')
    ));
    RETURN NEW;
END;
$$;
"""

def upgrade() -> None:
    op.execute(_NEW_BODY)
    # Backfill without bumping updated_at (jobs_updated_at is BEFORE UPDATE).
    op.execute("ALTER TABLE jobs DISABLE TRIGGER jobs_updated_at;")
    op.execute("""
        UPDATE jobs SET search_text = immutable_unaccent(lower(
            coalesce(title,'') || ' ' || coalesce(company,'') || ' ' ||
            coalesce(activities,'') || ' ' || coalesce(requirements,'')));
    """)
    op.execute("ALTER TABLE jobs ENABLE TRIGGER jobs_updated_at;")

def downgrade() -> None:
    op.execute(_OLD_BODY)          # same CREATE OR REPLACE, without requirements
    # NOTE: downgrade leaves requirements terms in search_text until the next
    # write; harmless (superset), documented instead of a second backfill.
```

`immutable_unaccent(text)` already exists (0001) and the query expression must be **character-for-character the same composition**: `immutable_unaccent(lower(:q))`. Do not restate it as `lower(immutable_unaccent(...))` — same result for pt-BR, different for nothing, and one less thing to explain.

### Pattern 5: Reveal state machine (Phase 3 contract, implemented here)

`idle → verifying → revealed | error(403|429|404|network)`, with these hard rules from `03-UI-SPEC.md` §B and 04 D-10:

- contact fields are **absent from the DOM** in `idle` (never `hidden`);
- widget mounts **at click time** (`appearance="interaction-only"`, `id="turnstile-reveal"`, `action="reveal"`), never pre-minted;
- 403 → show `detail` verbatim **and** reset the widget (remount via `key++`; `next-turnstile@1.0.7` exposes **no** `reset()` — verified against `dist/types.d.ts`);
- 429 → disable for `Retry-After` seconds, else 10 s (**needs one backend line, see Pitfall 1**);
- 404 → `"Vaga não encontrada ou expirada."`;
- revealed contacts are cached per job for the tab (D-10, module scope/context), so reopening the same card shows the contact **without** a new token — this supersedes `03-UI-SPEC.md` §B's "never cache" sentence, as declared in `04-CONTEXT.md` line 75.

### Pattern 6: Contact links

```ts
// lib/contacts.ts  — DB values are NOT guaranteed E.164 (seed.py uses "+55 11 90000-0000")
export function waHref(phone: string): string | null {
  const digits = phone.replace(/\D/g, "");
  return digits.length >= 10 ? `https://wa.me/${digits}` : null;
}
export function mailtoHref(email: string): string {
  return `mailto:${email.trim()}`;
}
```
Render only the CTAs whose value exists (`JobPublic` allows either contact to be `None`). `wa.me` wants digits only — a raw `+55 11 90000-0000` produces a dead link.

### Pattern 7: URL state hygiene

- `q` → trimmed, dropped when empty, capped at 80 chars (mirror the backend `max_length`).
- `city` → only the 4 slugs; anything else is ignored (falls back to "Todas"), never a 400.
- `sort` → only `recentes|antigas`; unknown → `recentes`.
- `page` → integer ≥ 1; missing/NaN → 1; out of range → empty state with a link to page 1 (do not redirect).
- filter changes: `router.replace(...)` + implicit `page=1`, and **drop `?vaga=`** (a modal about a job that the new filter excludes is a contradiction).
- modal open/close: `window.history.replaceState(...)` (no RSC round-trip; the data is already in the DOM).

### Pattern 8: ADS slots as fixed boxes

`ad-header` (100% × 90px, max content 728px), `ad-inline` (`col-span-full`, 90px, inserted after cards 6/12/18 of the 24-per-page), `ad-sidebar` (300×250, only ≥1024px). Dashed `#6d5a91` border, label `"Espaço publicitário"` (UI-SPEC §ADS says `Espaço publicitário`; D-12 shorthand says "Publicidade" — use the UI-SPEC string, it is the approved one), `aria-label` present, **no** `aria-hidden`, fixed height even when empty (anti-CLS).

### Anti-Patterns to Avoid

- **Filtering or sorting in the browser.** `total` and pagination come from the API; duplicating the rule client-side guarantees divergence.
- **`useSearchParams()` in the client to re-fetch the list.** The RSC already rendered it; the client's job is only to *write* the URL.
- **Rendering the contact from the list payload.** `JobPublic` has no contact fields by design (PUBL-05) — if a planner adds one, the phase fails its own security requirement.
- **`dangerouslySetInnerHTML` for `activities`/`requirements`.** Extracted text is untrusted-ish (LLM + pasted group text). Plain text + `whitespace-pre-line` is the whole formatting story.
- **A `Map` in `useRef` for the contact cache.** Dies with the grid (D-10 explicitly forbids it).
- **Importing `<Turnstile>` from a Server Component.** `next-turnstile@1.0.7` has no `"use client"` directive (verified in `dist`), so it must only be reached through a client boundary.
- **Mounting two widgets at once.** The package uses a single global `window.onloadTurnstileCallback`; reveal and login widgets must never be mounted in the same document.
- **`npm install tailwindcss` and then wiring `tailwindcss: {}` in PostCSS** — that is the v3 recipe and fails silently in v4.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Modal focus trap, ESC, backdrop, background inert | Custom div + keydown/focus loops | Native `<dialog>` + `showModal()` | Browser handles trap/ESC/`::backdrop`/inert; ~40 lines instead of ~200 |
| Accent folding | Python `unicodedata` on write, or `lower()` in SQL only | `immutable_unaccent()` (exists) + trigger | Locked D-04; keeps one normalization authority and the GIN index usable |
| LIKE wildcard safety | Regex whitelisting of `q` | escape `\`, `%`, `_` + `LIKE … ESCAPE '\'` | Rejecting `%` breaks nothing but also loses nothing; escaping is one helper |
| Counting filtered rows | Load all rows and `len()` | `select(func.count()).select_from(Job).where(*same_filters)` | Paging correctness and index use |
| Date formatting | `toLocaleDateString()` with implicit TZ | `Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", … })` in one helper | Server/browser TZ differ → hydration mismatch and off-by-one dates |
| Phone → `wa.me` | String concat of the raw phone | `phone.replace(/\D/g, "")` | Verified: stored/seeded phones contain spaces and `+` |
| Turnstile widget reset | Manual token clearing + hoping | React `key` bump | Package has no reset API (verified) |
| URL param parsing | Ad-hoc `Number()` casts inline in JSX | one `normalizeFilters()` in `lib/filters.ts` | Single place to test/whitelist; keeps page.tsx readable |

**Key insight:** every hard part of this phase already has an owner — Postgres for normalization, the browser for dialog/modal semantics, Phase 3 for the reveal gate. The phase's job is *wiring*, and wiring bugs (cache, ordering, escaping, TZ) are where the time goes.

---

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `jobs.search_text` column: existing rows (dev branch + test fixtures + any seeded row) hold a value **without** `requirements` | Migration `0003` backfill (`UPDATE`) — data migration, not a code edit |
| Stored data | `jobs.updated_at` is bumped by `jobs_updated_at` (BEFORE UPDATE) | Disable that trigger during backfill, re-enable after |
| Live service config | None — Neon branches only carry data; no dashboards/ACLs reference `search_text` | None |
| OS-registered state | None | None — verified by inspecting `backend/` (no service/task registration in repo) |
| Secrets/env vars | `backend/.env`: `DATABASE_URL` (dev branch `ep-snowy-mouse…`), `TEST_DATABASE_URL` (separate branch `ep-holy-rice…`), `TURNSTILE_SECRET_KEY` = Cloudflare **test** key, `ENV` **absent** (defaults to `dev`) | Seed guard must not rely on an env var that isn't set locally — see Pitfall 4 |
| Build artifacts | `frontend/.next/` static output currently marks `/` as `○ (Static)`; `.env.local` selects `NEXT_PUBLIC_API_URL` at build time | After Phase 4, `/` **must** build as `ƒ (Dynamic)` — this is a verification signal, not a chore |

---

## Common Pitfalls

### Pitfall 1: `Retry-After` is unreadable from the browser
**What goes wrong:** the 429 countdown in the reveal UI silently always uses the 10 s fallback.
**Why it happens:** `backend/app/main.py:26-32` configures `CORSMiddleware` **without** `expose_headers`. `Retry-After` is not a CORS-safelisted response header, so `res.headers.get("Retry-After")` is `null` cross-origin (localhost:3000 → localhost:8000).
**How to avoid:** add `expose_headers=["Retry-After"]` to `create_app()` in the same plan that implements the countdown. One line, tests unaffected.
**Warning signs:** the UI shows exactly 10 s every time, even when the limiter says `10/minute`.

### Pitfall 2: `?vaga=` for a job that isn't on the current page
**What goes wrong:** a shared deep link `/?vaga=<uuid>&q=analista` where the job doesn't match `q` renders "Vaga não encontrada" — for a perfectly valid job.
**Why it happens:** D-09 assumes the modal can be built from the list payload, which only contains the current page.
**How to avoid:** if `vaga` is not in `items`, resolve it **on the server** with the existing contact-free `GET /api/v1/public/jobs/{id}` and pass it as `initialJob`; only a 404 from that call produces the "not found" state. This keeps the "no client detail fetch" property and makes the state honest.
**Warning signs:** the deep link works for page 1 and breaks for every filter.

### Pitfall 3: Pagination duplicates rows (or drops them)
**What goes wrong:** with ties on `created_at`, `limit=24&page=2` re-shows a card from page 1.
**Why it happens:** all fixtures/seeded rows in one transaction share the same `now()`; `ORDER BY created_at DESC` is then non-deterministic.
**How to avoid:** append `Job.id` (or `Job.created_at.desc(), Job.id.desc()`) as tie-breaker, and write the test with 3 same-transaction rows at `limit=1`.
**Warning signs:** a job appears twice while another never appears — only visible with small `limit` or after a batch seed.

### Pitfall 4: The seed runs against the wrong database
**What goes wrong:** `seed_public_demo.py` inserts 24 fake published jobs into a deployed/shared branch.
**Why it happens:** `backend/.env` has **no** `ENV` line (`Settings.ENV` defaults to `"dev"`), and the existing `backend/scripts/seed.py` has **no** environment guard at all — the new script inherits a bad precedent.
**How to avoid:** require **both** `settings.ENV == "dev"` **and** an explicit confirmation flag (e.g. `--yes`), and refuse when the `DATABASE_URL` host doesn't look like a local/Neon dev branch. Print the resolved host (not the URL) before inserting. Also: `search_text` must not be set by the script — the trigger owns it (that's the point of migration `0003`).
**Warning signs:** `SELECT count(*) FROM jobs` jumps by 24 after running scripts.

### Pitfall 5: `/` builds as static and the board freezes at build time
**What goes wrong:** production serves the job list as of `next build`.
**Why it happens:** Next 15's default `fetch` cache is `auto no cache`, which is a **build-time** fetch when no request-time API is detected; and reading `searchParams` is what makes the route dynamic.
**How to avoid:** `cache: "no-store"` **and** keep the `searchParams` read (both are in the locked plan). Verify with build output: `/` must print `ƒ (Dynamic)`, not `○ (Static)` (today it prints `○`).
**Warning signs:** a new seeded job doesn't appear until redeploy.

### Pitfall 6: Tailwind's Preflight leaking into the admin
**What goes wrong:** `/admin/paste` inputs and buttons change appearance after a client-side navigation from `/`.
**Why it happens:** Next does not remove route-scoped stylesheets on client navigation (documented), and Preflight resets `button`, `input`, `h1…`, `ul`.
**How to avoid:** don't link public → admin anywhere; add a manual check after implementation (open `/`, then `/admin/paste` via URL is a *hard* load — the real check is any future client nav); keep the layer-split variant documented as the escape hatch.
**Warning signs:** admin labels lose their `display:block`, buttons lose padding.

### Pitfall 7: `next-turnstile` in a Server Component
**What goes wrong:** build error about hooks/`window`, or a widget that renders then disappears.
**Why it happens:** package has no `"use client"`; a single global callback; the widget renders on `[siteKey, sandbox]` only.
**How to avoid:** client boundary (`RevealContact.tsx`), one widget at a time, `key={n}` for a fresh widget after 403/expire, `onError`/`onExpire` → clear token and disable the button.
**Warning signs:** "Cannot read properties of undefined (reading 'render')", or two widgets on one page with the login form open.

### Pitfall 8: Hydration mismatch on dates and on the search input
**What goes wrong:** console errors, or the input resets while typing.
**Why it happens:** server/browser timezone and locale differ; or the filter input is controlled by a value derived from `searchParams` that only updates after a server round-trip.
**How to avoid:** one `formatDateBR()` using explicit `timeZone: "America/Sao_Paulo"`; the search input keeps local state (`defaultValue` from the server value + local state for typing) and commits on submit.
**Warning signs:** "Text content does not match server-rendered HTML"; typing loses characters.

---

## Code Examples

### The SQL match (accent + case insensitive, index-friendly)

```python
# backend/app/crud/jobs.py
from sqlalchemy import func, literal
# immutable_unaccent lives in the DB; reference it with func.*
def _norm(q: str):
    return func.immutable_unaccent(func.lower(q))

def escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

pattern = f"%{escape_like(normalized)}%"
select(Job).where(Job.search_text.like(pattern, escape="\\"))
```
`search_text` is stored as `immutable_unaccent(lower(concat))` (verified in `0001_initial_jobs.py:128-131`), so the *pattern* must be normalized the same way. `ILIKE` alone fails SRCH-01 (accent-sensitive).

### `pt-BR` date, timezone-stable

```ts
// lib/format.ts
const fmt = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit", month: "2-digit", year: "numeric",
  timeZone: "America/Sao_Paulo",
});
export const formatDateBR = (iso: string) => fmt.format(new Date(iso)); // dd/mm/aaaa
```

### Native dialog, opened only from the client

```tsx
"use client";
// components/board/JobDialog.tsx
useEffect(() => {
  const el = ref.current;
  if (!el) return;
  if (open && !el.open) el.showModal();
  if (!open && el.open) el.close();
}, [open]);

// close event fires for ESC and for el.close()
<dialog ref={ref} onClose={onClose} onCancel={onClose} tabIndex={-1} …>
  <div onClick={(e) => { if (e.target === ref.current) onClose(); }}>…</div>
</dialog>
```
`onClose`/`onCancel` exist on React 19's `<dialog>` props (verified in `@types/react@19.1.13`). Relying on the `close` event (not on a local flag set at click time) is what makes ESC remove `?vaga=` too.

### Seed guard

```python
# backend/scripts/seed_public_demo.py
MARKER = "SEED_PUBLIC_DEMO"   # written into source_snippet → idempotent delete-then-insert
settings = get_settings()
if settings.ENV != "dev":
    raise SystemExit("seed_public_demo só roda com ENV=dev")
host = make_url(settings.DATABASE_URL).host or ""
if not args.yes:
    raise SystemExit(f"alvo: {host} — rode com --yes para confirmar")
# delete previous demo rows by marker, insert 12–24 published jobs,
# contact_phone in E.164 (+5511…), city ∈ ALLOWED_CITIES, never set search_text,
# expires_at = created_at + 14d when backdating created_at
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind `tailwind.config.js` + `@tailwind base/components/utilities` | `@import "tailwindcss"` + `@theme` in CSS, `@tailwindcss/postcss` plugin | v4 (2025) | No config file; tokens are CSS vars → utilities derive from them |
| `searchParams` as a plain object | `Promise<…>`, must `await` | Next 15 | Silent type errors if a v15 example is copied from v14 |
| `fetch` defaults to caching in the App Router | default `auto no cache`; `force-cache` is opt-in | Next 15 | `no-store` still required to keep the board off the build snapshot |
| Custom modal components | native `<dialog>` + `showModal()` | broadly available | Focus trap/ESC/backdrop for free |

**Deprecated/outdated in this repo's own docs:**
- `03-UI-SPEC.md` §B "never cache the contact" — superseded by D-10 (declared in `04-CONTEXT.md:75`).
- `03-UI-SPEC.md` §A "reset the widget (`turnstile.reset` via ref/props)" — the installed package has no reset API; `ExtractForm.tsx` already uses the correct `key` bump. Don't propagate the wrong mechanism into the reveal.
- `.planning/STATE.md` "Turnstile action binding blocks reveal in dev (403)" — **resolved in code**: `get_turnstile_verifier()` sets `enforce_action=(settings.turnstile_mode == "live")`, and local `.env` uses a Cloudflare **test** key → mode `test` → reveal succeeds in dev. Verify with `GET /api/v1/health` → `turnstile.mode == "test"`.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The Neon Postgres locale folds non-ASCII correctly under `lower()`, so reusing the exact trigger expression is sufficient for SRCH-01 | Pattern 4 / Code Examples | LOW — the expression is *identical* to the trigger, so column and pattern fold identically regardless of locale; only a mismatch could break it |
| A2 | `gin_trgm_ops` serves `LIKE '%…%'` with a bound parameter | Pattern 3 | LOW — established pg_trgm behaviour and already the reason the index exists; a small `EXPLAIN` check is cheap if in doubt |
| A3 | Dev verification of reveal works with Cloudflare test keys (always-pass, action omitted) | Pitfall / Stack of the Art | MEDIUM — verified in code (`enforce_action` false in `test` mode); if the local secret were live, reveal would 403 in dev |
| A4 | UI-SPEC's literal chip labels (`Sao Paulo`) vs CONTEXT line 127 ("exibir o rótulo acentuado é responsabilidade da UI") is a copy decision, not a data decision | Open Question 2 | MEDIUM — affects whether `lib/cities.ts` holds 3 fields or 2; no backend impact |
| A5 | Nothing else in the repo links `/` → `/admin/paste`, so route-scoped Preflight is sufficient | Pattern 2 | MEDIUM — true today (verified: `app/page.tsx` is a placeholder, admin has no back-link) |
| A6 | `backend/scripts/` is the right home for the new seed (dir already exists with `seed.py` + `__init__.py`) | Pattern / Pitfalls | LOW — CONTEXT says "novo diretório", reality is it exists |

**If this table is short:** all other claims in this document were verified by reading the repo or by fetching the cited docs this session.

---

## Open Questions (RESOLVED 2026-10-22)

1. **Should `q` also match `city`?** — **RESOLVED: no.**
   - User decision: keep D-03 (`q` = title + company + activities + requirements) and fix the copy instead.
   - Final placeholder string: `Busque por cargo, empresa ou palavra-chave` (already applied to `04-UI-SPEC.md` and recorded as D-06c). City keeps its own chip filter.

2. **Accented or unaccented city labels in the chips?** — **RESOLVED: accented labels, unaccented canonical.**
   - User decision: `lib/cities.ts` maps `slug → { label: "São Paulo", canonical: "Sao Paulo" }`; chips and cards display the accented label; the API receives the slug (or canonical) and translates to the DB value.
   - Recorded as D-06b in `04-CONTEXT.md`; `04-UI-SPEC.md` line 181 already lists `São Paulo`.
   - Backend tolerates both spellings and ignores unknown cities (D-05).

3. **Is a frontend test runner in scope?** — **RESOLVED: no.**
   - User decision: no Vitest/Playwright this phase.
   - Gate = `npm run build` (must show `ƒ /`) + `npm run lint` + PowerShell HTTP assertions + manual browser UAT. Recorded as D-12a.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Next dev/build | ✓ | 22.18.0 | — |
| npm | install Tailwind | ✓ | 10.9.3 | — |
| `next` | board | ✓ | 15.5.3 (installed) | — |
| tailwindcss + @tailwindcss/postcss | UIUX-01 | ✗ | — | none needed; one `npm install -D` (Wave 0) |
| `uv` | backend tests/migrations | ❌ | **not installed** (`Get-Command uv` fails) | use `backend\.venv\Scripts\python.exe -m ...` |
| Python venv | backend | ✓ | `backend\.venv\Scripts\python.exe` (Python 3.11.17) | — |
| pytest | backend tests | ✓ | 9.1.1, **178 tests collected in 0.29 s** | — |
| Neon Postgres (dev branch) | seed + manual UAT | ✓ (configured) | `ep-snowy-mouse…` pooled | — |
| Neon Postgres (test branch) | `TEST_DATABASE_URL` | ✓ (configured) | `ep-holy-rice…` pooled | falls back to `DATABASE_URL` |
| Cloudflare Turnstile | PUBL-04 | ✓ test keys (mode `test`, always-pass) | — | reveal still 403-fails if key removed outside dev |
| Playwright / vitest / jsdom | frontend tests | ✗ | — | `next build` + `next lint` + HTTP assertions + manual UAT |

**Missing dependencies with no fallback:** none.

**Missing dependencies with fallback:** frontend test runner (see Open Question 3).

**Baseline commands (verified this session):**
- `Push-Location backend; .\.venv\Scripts\python.exe -m pytest -q; Pop-Location` → 178 tests, collection works, DB-gated.
- `cd frontend; npm run build` → compiles in ~6 s; current routes: `/` `○`, `/admin/paste` `○` (both static today).

---

## Validation Architecture

> `workflow.nyquist_validation: true` in `.planning/config.json` → required.

### Test Framework

| Property | Value |
|----------|-------|
| Framework (backend) | pytest 9.1.1 + pytest-asyncio 1.x (`asyncio_mode = "auto"`) |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths = ["tests"]`) |
| Framework (frontend) | **none** — `next build` + `next lint` + HTTP assertions |
| Config file | `frontend/.eslintrc.json`, `frontend/tsconfig.json` |
| Quick run command | `Push-Location backend; .\.venv\Scripts\python.exe -m pytest -q; Pop-Location` |
| Full suite command | `Push-Location backend; .\.venv\Scripts\python.exe -m pytest -q; Pop-Location` (single suite, ~fast) + `cd frontend; npm run build` + `npm run lint` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| SRCH-01 | `q=analista` matches `ANALISTA`; `q=sao paulo` matches `São Paulo`; `q=requisito` matches a term that exists **only** in `requirements` | integration | `Push-Location backend; .\.venv\Scripts\python.exe -m pytest tests/test_public_search.py -q; Pop-Location` | ❌ Wave 0 |
| SRCH-02 | `city=sao-paulo` returns only São Paulo rows; `city=Sao Paulo` also works; unknown `city` ignored (no 400); `q`+`city` narrows `total` | integration | same file | ❌ Wave 0 |
| SRCH-03 | `sort=antigas` reverses order; default = `recentes`; unknown sort → `recentes` | integration | same file | ❌ Wave 0 |
| SRCH-03 / PUBL-01 | 3 same-transaction rows + `limit=1` pages 1..3 return 3 distinct ids | integration | `… -k tie_break` | ❌ Wave 0 |
| SRCH-01 | `q=%` / `q=_` treated literally (no wildcard blow-up) | integration | `… -k wildcard` | ❌ Wave 0 |
| PUBL-05 (regression) | list + detail payloads contain no `contact_*` keys | integration | existing `tests/test_public_api.py` | ✅ |
| PUBL-01 / PUBL-02 | SSR HTML contains seeded job titles + "Ver a vaga" | smoke | `Invoke-WebRequest http://localhost:3000/ -UseBasicParsing` → `-match 'Analista'` | ❌ Wave 0 (script/manual) |
| PUBL-01 / SRCH-02 | SSR HTML for `?city=sao-paulo` excludes other cities' titles | smoke | `Invoke-WebRequest 'http://localhost:3000/?city=sao-paulo'` | ❌ Wave 0 |
| PUBL-03 | `?vaga=<uuid>` server-renders the dialog content (or the "não encontrada" state for a bogus uuid) | smoke | `Invoke-WebRequest 'http://localhost:3000/?vaga=<seed-uuid>'` | ❌ Wave 0 |
| PUBL-04 | contact strings absent from HTML before reveal; present after a real reveal | manual-only | browser UAT (Turnstile iframe cannot be driven headlessly without a runner) | ❌ manual |
| PUBL-06 | `wa.me` link has digits only; `mailto:` matches the revealed email | unit (manual) | browser devtools inspection of the rendered `href` | ❌ manual |
| UIUX-01 | `#8b5cf6` never carries text; text uses `#a78bfa` | review | UI-SPEC contrast table + `next lint` | ✅ (spec) |
| UIUX-02 | "Doações" links to `/doacoes` (never `#`) | smoke | `Invoke-WebRequest '/doacoes'` → 200 + title | ❌ Wave 0 |
| UIUX-03 | 3 ADS slots present with fixed heights | smoke | `Invoke-WebRequest '/'` → 3 × `Espaço publicitário` | ❌ Wave 0 |
| PUBL-01..04 | `/` must build as `ƒ (Dynamic)` | build assertion | `npm run build` → grep route table for `ƒ /` | ✅ command exists |
| All | type/lint clean | static | `npm run lint` (runs `next lint` incl. type check via build) | ✅ |
| Migration | `0003` applies, backfills, keeps `updated_at` | integration | run `alembic upgrade head` on the test branch + assert `search_text` contains a requirements term | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `Push-Location backend; .\.venv\Scripts\python.exe -m pytest -q; Pop-Location` (whole suite is small) and `Push-Location frontend; npm run lint; Pop-Location`.
- **Per wave merge:** backend suite + `cd frontend; npm run build` (must show `ƒ /`).
- **Phase gate:** backend suite green, `next build` green with `/` dynamic, seeded board verified in a real browser (search with/without accents, city chip, sort, page 2, deep link, reveal, `wa.me`, ESC/backdrop close).

### Wave 0 Gaps
- [ ] `backend/tests/test_public_search.py` — covers SRCH-01/02/03 + tie-break + wildcard + `total` consistency (patterns: `conftest.py` fixtures `app`, `db_session`, `fake_turnstile`; insert rows directly via the session so one transaction owns all rows).
- [ ] `frontend/scripts/verify-ssr.ps1` (optional, ~20 lines) — the `Invoke-WebRequest` assertions above, so the phase gate isn't purely manual. PowerShell 5.1, no `&&`.
- [ ] Tailwind install: `cd frontend; npm install -D tailwindcss@4.3.3 @tailwindcss/postcss@4.3.3` + `postcss.config.mjs`.
- [ ] `backend/scripts/seed_public_demo.py` is a *product* deliverable (D-02), not a test fixture, but the smoke tests above depend on it.
- [ ] No frontend test runner — accepted gap (Open Question 3), covered by build/lint/HTTP/manual.

---

## Security Domain

`security_enforcement` is enabled (absent = enabled in config).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No accounts on the public surface by design (core value) |
| V3 Session Management | no | No session; admin JWT lives in `sessionStorage` (Phase 3, untouched) |
| V4 Access Control | **yes** | Contact only via `POST /jobs/{id}/reveal-contact`; `JobPublic` has no contact fields; single-master admin via `require_admin` |
| V5 Input Validation | **yes** | `q` `max_length=80`; `city` whitelist; `sort` whitelist; `page` `ge=1`; `limit` `le=50`; LIKE metacharacter escaping; `job_id` typed `uuid.UUID` by FastAPI |
| V6 Cryptography | no | Nothing new; Turnstile/JWT are Phase 3 |
| V7 Error Handling/Logging | yes | Block `detail` strings rendered verbatim, no stack traces leaked (FastAPI default); never log tokens |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Contact harvesting / scraping | Information Disclosure | Contact exists only behind Turnstile + `10/minute` per IP (Phase 3); the phase must not add any endpoint or payload field that returns it |
| SQL injection | Tampering | SQLAlchemy bound parameters only; the only string interpolation is the LIKE pattern **built from a bound value** — never `text()` concatenation |
| LIKE wildcard abuse (`%`, `_`) | DoS / Information Disclosure | Escape `\ % _` and use `ESCAPE '\'`; combined with `max_length=80` and the rate limiter |
| XSS via extracted job text | Tampering | React auto-escapes; forbid `dangerouslySetInnerHTML` for `activities`/`requirements` |
| Open redirect via `?vaga=` or next-param | Tampering | `vaga` is parsed as a UUID and used only as a lookup key; never as a URL |
| CORS misconfiguration | Spoofing | `CORS_ORIGINS` stays an explicit allowlist (`http://localhost:3000` locally); the only change is `expose_headers=["Retry-After"]` |
| Token replay across flows (login ↔ reveal) | Spoofing | Turnstile `action` binding in live mode (Phase 3, verified) |
| Cache poisoning / stale privacy leak | Information Disclosure | `no-store` on every board/detail fetch (D-08); no `revalidateTag` |

---

## Sources

### Primary (HIGH confidence)
- `backend/app/api/v1/public.py`, `backend/app/crud/jobs.py`, `backend/app/models/job.py`, `backend/app/schemas/job.py`, `backend/app/main.py`, `backend/app/deps.py`, `backend/app/core/config.py`, `backend/app/services/turnstile.py` — read in full this session.
- `backend/alembic/versions/0001_initial_jobs.py` (trigger `jobs_set_search_text`, `immutable_unaccent`, `idx_jobs_search_trgm` partial index, `jobs_updated_at`), `0002_jobs_source_snippet.py` (head).
- `backend/tests/conftest.py`, `backend/tests/test_public_api.py`, `backend/pyproject.toml`, `backend/scripts/seed.py`, `backend/app/services/extraction/extractor.py:56` (`ALLOWED_CITIES` unaccented tuple).
- `frontend/package.json`, `app/layout.tsx` (`lang="pt-BR"`), `app/page.tsx`, `app/globals.css` (orphan), `app/admin/paste/{ExtractForm.tsx,globals-admin.css}`, `lib/api.ts`, `next.config.mjs`, `.eslintrc.json`.
- `frontend/node_modules/next-turnstile/dist/types.d.ts` — full prop list, no reset API, no `"use client"`.
- `frontend/node_modules/@types/react@19.1.13/index.d.ts` — `onClose`/`onCancel` on dialog props.
- npm registry (`npm view`): `tailwindcss@4.3.3`, `@tailwindcss/postcss@4.3.3`, `postcss@8.5.31`, `next@16.4.2` (latest; project stays on 15.5.3).
- [unpkg.com/tailwindcss@4.3.3/index.css](https://unpkg.com/tailwindcss@4.3.3/index.css) — `@layer theme, base, components, utilities;` + inlined Preflight.
- [unpkg.com/tailwindcss@4.3.3/package.json](https://unpkg.com/tailwindcss@4.3.3/package.json) — `./preflight.css`, `./theme.css`, `./utilities.css` exports.

### Secondary (MEDIUM confidence)
- [nextjs.org/docs/app/api-reference/functions/fetch](https://nextjs.org/docs/app/api-reference/functions/fetch) (lastUpdated 2026-08-18) — `auto no cache` default, `no-store`, HMR cache caveat.
- [nextjs.org/docs/app/getting-started/css](https://nextjs.org/docs/app/getting-started/css) (lastUpdated 2026-08-25) — route-scoped layout CSS + "does not remove stylesheets as you navigate".
- [nextjs.org/docs/app/api-reference/file-conventions/page](https://nextjs.org/docs/app/api-reference/file-conventions/page) — `searchParams` as `Promise`, dynamic rendering opt-in.
- `.planning/phases/04-public-board-frontend/04-UI-SPEC.md` (approved 6/6) — `@theme` token block (lines 42-63), copy table, URL contract (line 248), ADS table, dialog anatomy.
- `.planning/phases/03-contact-reveal-anti-spam/03-UI-SPEC.md` §B — reveal states, copy, 44px targets (with the two superseded sentences noted above).

### Tertiary (LOW confidence)
- pg_trgm index usage for parameterised `LIKE '%…%'` — standard behaviour, not re-verified with `EXPLAIN` this session (A2).

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — every version read from `node_modules` or the registry this session; Tailwind v4 wiring read from the published artifact, not memory.
- Architecture: **HIGH** for RSC/fetch/searchParams/migration mechanics (source-verified); **MEDIUM** for CSS isolation (documented Next caveat makes the route group a soft boundary) and for the city label mapping (two approved artifacts disagree).
- Pitfalls: **HIGH** — each one is anchored to a file or doc line read this session (missing `expose_headers`, non-deterministic ordering, missing `ENV` in `.env`, static `/` in the build output, `wa.me` phone formatting).

**Research date:** 2026-10-22
**Valid until:** 2026-11-21 (30 days) — Next 15.5.3 and Tailwind 4.3.3 are pinned by `package.json`/install, so only the docs drift.
