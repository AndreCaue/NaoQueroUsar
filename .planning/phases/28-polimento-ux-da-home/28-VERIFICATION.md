---
phase: 28-polimento-ux-da-home
verified: 2026-11-22T22:36:30Z
status: human_needed
score: 4/4 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Hover nos chips de cidade (ativo e inativo)"
    expected: "Chip inativo mostra borda/texto accent e leve fundo accent/10 ao hover; chip ativo (selecionado) clareia com bg-accent-strong-hover; sem mudança de layout."
    why_human: "Aparência visual, contraste percebido e ausência de layout shift precisam de inspeção no navegador."
  - test: "Hover no dropdown de ordenação e nas opções"
    expected: "Trigger mostra feedback accent ao hover/aberto; opções Recentes/Antigas mostram fundo accent/10 + texto accent-soft ao hover e ao navegar por teclado; sem layout shift."
    why_human: "Estados visuais de hover/focus/active-descendant e percepção de consistência são visuais."
  - test: "Teclado no SortDropdown"
    expected: "ArrowUp/Down move opção ativa, Enter/Space seleciona, Escape fecha e devolve foco ao trigger; clique fora fecha; Tab não fica preso."
    why_human: "Comportamento de foco e interação de teclado precisa ser confirmado no browser real."
  - test: "Hover nos cards de vaga"
    expected: "Card ganha borda accent e leve fundo rgba(139,92,246,0.04) ao hover; focus-within mantém borda accent; sem mudança de padding/borda/transform."
    why_human: "Intensidade visual média e ausência de layout shift são melhor validadas visualmente."
  - test: "Filtro de cidades dinâmico com busca ativa"
    expected: "Ao digitar q que reduz resultados, o conjunto de chips de cidade permanece o mesmo (baseado em available_cities do board geral). Selecionar cidade obsoleta/URL antiga redireciona para estado amplo sem cidade."
    why_human: "Requer fluxo end-to-end no app rodando com dados reais/publicados para confirmar comportamento percebido."
---

# Phase 28: Polimento UX da Home Verification Report

**Phase Goal:** Candidato vê apenas filtros úteis e recebe feedback visual claro nos elementos interativos da home.
**Verified:** 2026-11-22T22:36:30Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Usuário vê no filtro de cidades somente cidades que possuem vagas publicadas/ativas no momento. | ✓ VERIFIED | `backend/app/crud/jobs.py` `list_active_cities()` consulta apenas `Job.status == published` e `Job.expires_at > func.now()` com `distinct()`, mapeia por `canonical_to_slug` e retorna na ordem `ACTIVE_CITY_SLUG_ORDER` (sem q/city/sort). `backend/app/api/v1/public.py` inclui `available_cities` em `JobListResponse`. `frontend/app/(public)/page.tsx` lê `data.available_cities`, redireciona cidade obsoleta via `redirect(buildBoardHref({ ...filters, city: null, page: 1, vaga: null }))`. `frontend/components/board/BoardToolbar.tsx` filtra `CITY_OPTIONS` por `availableCities` e renderiza `Todas` + `activeCityOptions.map(...)`. Testes backend `available_cities` passaram: `2 passed, 28 deselected`. |
| 2 | Usuário recebe feedback visual de hover ao passar o mouse sobre opções do dropdown recentes/antigos. | ✓ VERIFIED | `frontend/components/board/SortDropdown.tsx` implementa listbox customizada (`aria-haspopup="listbox"`, `role="listbox"`, `role="option"`, `aria-selected`, `aria-activedescendant`) com opções "Mais recentes"/"Mais antigas", hover `hover:bg-accent/10 hover:text-accent-soft`, active styling, ArrowUp/Down/Enter/Space/Escape e fechamento por clique fora/Escape com retorno de foco ao trigger. `BoardToolbar.tsx` usa `<SortDropdown ...>` e não tem `<select>` nativo. |
| 3 | Usuário recebe feedback visual de hover ao passar o mouse sobre cards de vaga. | ✓ VERIFIED | `frontend/components/board/JobCard.tsx` article possui `transition-colors hover:border-accent hover:bg-[rgba(139,92,246,0.04)] focus-within:border-accent`; sem alteração de padding/border-width/transform no hover. |
| 4 | Usuário recebe feedback visual de hover ao passar o mouse sobre filtros de cidades. | ✓ VERIFIED | `frontend/components/board/BoardToolbar.tsx` aplica chips ativos com `bg-accent-strong ... hover:bg-accent-strong-hover` e chips inativos com `border-line-strong ... hover:border-accent hover:text-accent-soft hover:bg-accent/10`, mantendo `min-h-11`, `transition-colors` e sem estilos de layout-shift. |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `backend/app/schemas/job.py` | `JobListResponse.available_cities` | ✓ VERIFIED | Contém `available_cities: list[str] = Field(default_factory=list)`; `JobPublic` permanece sem campos de contato. |
| `backend/app/services/cities.py` | Mapeamento canônico->slug e ordem estável | ✓ VERIFIED | Exporta `CANONICAL_TO_SLUG`, `ACTIVE_CITY_SLUG_ORDER`, `canonical_to_slug`; mantém `resolve_city/resolve_sort`. |
| `backend/app/crud/jobs.py` | Query de cidades ativas publicada/não expirada | ✓ VERIFIED | `list_active_cities` usa published + expires_at > now, distinct, ignora filtros q/city/sort; exportado em `__all__`. |
| `backend/app/crud/__init__.py` | Exporta `list_active_cities` | ✓ VERIFIED | `from app.crud.jobs import get_published, list_active_cities, list_published`. |
| `backend/app/api/v1/public.py` | GET /public/jobs retorna available_cities | ✓ VERIFIED | Chama `list_active_cities(session)` e retorna `JobListResponse(..., available_cities=available_cities)`. |
| `backend/tests/test_public_api.py` | Regressão de contrato CITY-01 | ✓ VERIFIED | `test_list_includes_available_cities_in_stable_order` verifica ordem estável, chaves e ausência de contato. |
| `backend/tests/test_public_search.py` | Independência de filtros e omissão de inativas | ✓ VERIFIED | `test_available_cities_are_independent_of_q_and_city_filters` valida q/city não afetam available_cities e Rio pendente omitido. |
| `frontend/lib/api.ts` | Contrato frontend `available_cities` | ✓ VERIFIED | `JobListResponse` inclui `available_cities: string[]`. |
| `frontend/app/(public)/page.tsx` | Propagação e limpeza D-03 | ✓ VERIFIED | Lê `data.available_cities`, redireciona cidade obsoleta, passa `availableCities` ao `BoardToolbar`. |
| `frontend/components/board/BoardToolbar.tsx` | Chips ativos + hover D-10/D-11/D-12 + integração SortDropdown | ✓ VERIFIED | Recebe `availableCities`, filtra `CITY_OPTIONS`, renderiza `activeCityOptions.map`; classes de hover ativas/inativas; usa `SortDropdown`. |
| `frontend/components/board/SortDropdown.tsx` | Listbox acessível recentes/antigas | ✓ VERIFIED | Componente client com ARIA de listbox, keyboard handling, outside click, Escape com foco no trigger, hover accent. |
| `frontend/components/board/JobCard.tsx` | Hover médio no card | ✓ VERIFIED | Inclui `hover:bg-[rgba(139,92,246,0.04)]` mantendo hover border accent e focus-within. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `backend/app/api/v1/public.py` | `backend/app/crud/jobs.py` | `list_active_cities(session)` em `list_public_jobs` | WIRED | Importado e chamado antes de montar resposta. |
| `backend/app/crud/jobs.py` | `backend/app/services/cities.py` | `canonical_to_slug` / `ACTIVE_CITY_SLUG_ORDER` | WIRED | Mapeia linhas distintas para slugs suportados em ordem estável. |
| `backend/app/api/v1/public.py` | `backend/app/schemas/job.py` | `JobListResponse(..., available_cities=...)` | WIRED | Campo aditivo presente no contrato e na resposta. |
| `frontend/app/(public)/page.tsx` | `frontend/lib/jobs.ts` / board payload | `data.available_cities` | WIRED | Payload do board consumido no RSC; `fetchBoard` permanece `cache: "no-store"` em `lib/jobs.ts`. |
| `frontend/app/(public)/page.tsx` | `next/navigation` | `redirect(buildBoardHref(... city:null ...))` | WIRED | Limpa URL obsoleta antes de renderizar board stale. |
| `frontend/app/(public)/page.tsx` | `frontend/components/board/BoardToolbar.tsx` | `availableCities={availableCities}` | WIRED | Prop passada explicitamente. |
| `frontend/components/board/BoardToolbar.tsx` | `frontend/lib/cities.ts` | `CITY_OPTIONS.filter(...)` | WIRED | Conjunto de chips vem de CITY_OPTIONS em ordem estável, filtrado por availableCities. |
| `frontend/components/board/BoardToolbar.tsx` | `frontend/components/board/SortDropdown.tsx` | `value={filters.sort} onChange={(sort)=>commit({sort})}` | WIRED | Controla URL sort pelo fluxo existente de `commit()`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `BoardToolbar.tsx` city chips | `availableCities` prop | `page.tsx` ← `data.available_cities` ← `GET /api/v1/public/jobs` ← `list_active_cities` (published/non-expired distinct) | Yes | ✓ FLOWING |
| `JobListResponse.available_cities` | `available_cities` | `list_active_cities` SQLAlchemy distinct query; not from request filters | Yes | ✓ FLOWING |
| `SortDropdown.tsx` | selected sort | `filters.sort` URL state via `BoardToolbar.commit()` | N/A (UI state, not fetched data) | ✓ N/A |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| CITY-01 backend available_cities contract | `cd backend && python -m pytest tests/test_public_api.py tests/test_public_search.py -q -k available_cities` | `2 passed, 28 deselected in 13.01s` | ✓ PASS |
| Frontend unit suite | `cd frontend && npm test -- --run` | `6 files passed, 29 tests passed` | ✓ PASS |
| Frontend lint on touched Phase 28 files | `cd frontend && npx eslint "app/(public)/page.tsx" "lib/api.ts" "components/board/BoardToolbar.tsx" "components/board/SortDropdown.tsx" "components/board/JobCard.tsx"` | No output / clean | ✓ PASS |
| SUMMARY-claimed implementation commits exist | `git log --oneline -1 <hash>` for 632b537,8d1df5a,cfbce44,998e810,153ef7c,99f455c | All 6 commits found | ✓ PASS |
| Visual hover/keyboard behavior | Browser manual check | Not run (visual/interactive) | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| CITY-01 | 28-01, 28-02 | Usuário vê no filtro de cidades da home apenas cidades que possuem vagas publicadas/ativas no momento | ✓ SATISFIED | Backend `available_cities` derivado de published/non-expired; frontend renderiza apenas chips ativos e limpa cidade obsoleta; testes `available_cities` passam. |
| UIUX-01 | 28-02, 28-03 | Usuário recebe feedback visual de hover em dropdown recentes/antigos, cards de vaga e filtros de cidades | ✓ SATISFIED (code) / ? NEEDS HUMAN (visual) | Classes/ARIA/keyboard handlers presentes para dropdown, chips e cards; confirmação visual/teclado final requer browser. |

**Orphaned requirements check:** REQUIREMENTS.md maps Phase 28 to CITY-01 and UIUX-01 only. No additional Phase 28 requirements found. All Phase 28 requirement IDs are declared by plan frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `frontend/components/board/BoardToolbar.tsx` | 150, 154 | `placeholder` attribute/class | ℹ️ Info | Legitimate search input placeholder; not a stub. |

No blocker/warning anti-patterns found in Phase 28 key files. No TODO/FIXME/HACK/return-null stubs detected.

### Human Verification Required

### 1. Hover de chips de cidade

**Test:** Abrir home com vagas ativas em cidades diferentes; passar mouse em chip inativo e ativo.
**Expected:** Inativo ganha borda/texto accent e fundo accent/10; ativo ganha hover bg-accent-strong-hover; sem salto de layout.
**Why human:** Aparência visual e layout shift não são totalmente confiáveis por inspeção estática.

### 2. Hover e teclado do SortDropdown

**Test:** Abrir dropdown Recentes/Antigas; usar mouse e teclado (ArrowUp/Down, Enter/Space, Escape, Tab, clique fora).
**Expected:** Hover/focus consistentes; seleção atualiza ordenação; Escape/clique fora fecha; foco volta ao trigger após Escape/seleção; sem trap de Tab.
**Why human:** Interação real de foco/teclado/fechamento depende do browser.

### 3. Hover de cards de vaga

**Test:** Passar mouse sobre cards no grid.
**Expected:** Borda accent + fundo sutil rgba(139,92,246,0.04), mantendo focus-within; sem mudança de tamanho.
**Why human:** Intensidade visual e estabilidade de layout precisam confirmação visual.

### 4. Dinâmica de chips com busca/filtro

**Test:** Com dados ativos em múltiplas cidades, buscar texto que reduza resultados; acessar URL com cidade obsoleta.
**Expected:** Chips permanecem baseados no board geral; URL obsoleta é limpa para estado amplo.
**Why human:** Valida fluxo end-to-end com dados reais e navegação RSC.

### Gaps Summary

No code gaps found. All Phase 28 must-have artifacts exist, are substantive, and are wired. Automated checks passed (targeted backend CITY-01 tests, frontend vitest suite, ESLint on touched files). Status is `human_needed` because UIUX-01 includes visual/keyboard behaviors that require browser confirmation.

---

_Verified: 2026-11-22T22:36:30Z_
_Verifier: OpenCode (gsd-verifier)_