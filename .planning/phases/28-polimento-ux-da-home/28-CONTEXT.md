# Phase 28: Polimento UX da Home - Context

**Gathered:** 2026-11-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase entrega polimento de UX na home pública: o filtro de cidades passa a mostrar apenas cidades com vagas publicadas/ativas no momento, e os elementos interativos da home recebem feedback visual claro de hover (dropdown de ordenação, cards de vaga e filtros de cidade). Não inclui novos filtros, busca avançada, redesign amplo do board, mudanças no fluxo de candidatura/revelação de contato, nem alterações no contrato público além do necessário para suportar as cidades ativas.

</domain>

<decisions>
## Implementation Decisions

### Fonte das cidades ativas
- **D-01:** O filtro de cidades considera vagas publicadas/ativas **no geral** do board, independentemente da busca atual (`q`). O conjunto de cidades não deve mudar enquanto o usuário digita/refina a busca textual.
- **D-02:** Cidades sem vagas publicadas/ativas no momento **não aparecem** no filtro (chip oculto).
- **D-03:** Se a URL já tiver uma cidade selecionada e ela ficar sem vagas ativas/publicadas, o filtro de cidade deve ser **limpo da URL** e o board deve voltar ao estado amplo (sem filtro de cidade), evitando tela vazia por filtro obsoleto.
- **D-04:** A lista de cidades ativas deve vir **junto com a resposta do board** (`GET /api/v1/public/jobs`), na mesma carga usada pela home, para manter consistência com os dados publicados/ativos exibidos.

### Hover do sort Recentes/Antigos
- **D-05:** O controle de ordenação deixa de ser `<select>` nativo e passa a ser um **dropdown custom acessível** (listbox/button), permitindo estilizar hover/focus nas opções e atender literalmente ao critério de hover nas opções.
- **D-06:** A interação do dropdown custom deve seguir o padrão de **listbox simples**: botão abre lista abaixo, opção ativa marcada, hover/focus visíveis; fecha ao selecionar, ao clicar fora e com `Escape`; mantém navegação por teclado acessível.
- **D-07:** O controle de ordenação fechado deve ter feedback de hover com **borda/realce accent** (alinhado aos inputs/chips). O estado ativo/aberto pode manter destaque coerente.
- **D-08:** O feedback de hover/focus das opções do sort deve ser **consistente com os chips de cidade**, usando a mesma linguagem visual (accent, borda/texto, fundo sutil), adaptada ao formato de menu/lista.

### Intensidade do hover visual
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` §"Phase 28: Polimento UX da Home" — Goal, depends on Phase 27, requisitos CITY-01/UIUX-01, success criteria e UI hint.
- `.planning/REQUIREMENTS.md` §"Busca e Filtros" / §"Interface e Experiência" — CITY-01 (filtro de cidades mostra apenas cidades com vagas publicadas/ativas) e UIUX-01 (hover em dropdown recentes/antigos, cards e filtros de cidades).
- `.planning/PROJECT.md` §"Current Milestone: v1.4 Polimento UX e Admin" — contexto do milestone; preservar fricção zero do candidato.

### Board público e filtros atuais
- `frontend/components/board/BoardToolbar.tsx` — search, chips de cidade estáticos (`CITY_OPTIONS`), sort `<select>` nativo; ponto principal para CITY-01 e UIUX-01.
- `frontend/components/board/JobCard.tsx` — card atual com `hover:border-accent`; ajustar feedback visual de hover.
- `frontend/components/board/JobGrid.tsx` — grid/lista de cards; verificar impacto visual de hover/foco sem regressão de layout.
- `frontend/app/(public)/page.tsx` — RSC do board; carrega `fetchBoard(filters)` e passa dados para toolbar/grid; ponto natural para receber cidades ativas.
- `frontend/app/(public)/public.css` — tokens dark/roxo e padrões de hover/focus; manter consistência visual.

### Contrato de filtros/cidades no frontend
- `frontend/lib/cities.ts` — `CITY_OPTIONS`, slugs/labels/canonicais e resolução de cidade; base para mapear cidades ativas para chips.
- `frontend/lib/filters.ts` — contrato URL `q/city/sort/page/vaga`, `normalizeFilters`, `buildBoardHref`; relevante para D-03 (limpar cidade obsoleta).
- `frontend/lib/jobs.ts` — fetch server-side do board (`GET /api/v1/public/jobs`); precisa transportar cidades ativas.
- `frontend/lib/api.ts` — tipos `JobListResponse`/`JobPublic` e helpers; atualizar contrato frontend conforme D-04.

### Contrato/API backend do board público
- `backend/app/api/v1/public.py` — endpoint `GET /public/jobs` retorna `JobListResponse`; incluir cidades ativas na mesma resposta.
- `backend/app/schemas/job.py` — `JobListResponse`/`JobPublic`; estender schema público com cuidado para não expor contato.
- `backend/app/crud/jobs.py` — `list_published` já aplica `status=published` e `expires_at > now()`; base para query de cidades ativas.
- `backend/app/services/cities.py` — resolução/normalização de cidades; garantir que cidades ativas retornem slugs/canonicais compatíveis com o frontend.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/components/board/BoardToolbar.tsx`: já centraliza busca, chips de cidade e ordenação; evoluir no próprio componente evita espalhar estado de filtro.
- `frontend/lib/cities.ts`: mapeamento canônico de slugs/labels já existe; reutilizar para exibir apenas cidades ativas sem duplicar normalização.
- `frontend/lib/filters.ts`: `normalizeFilters`/`buildBoardHref` já são a única fonte de verdade da URL; D-03 deve se integrar aqui/no fluxo de URL existente.
- `frontend/app/(public)/public.css`: tokens de cor, borda e focus-visible já definidos; usar tokens existentes para hover consistente.
- `backend/app/crud/jobs.py` + `backend/app/services/cities.py`: filtros publicados/ativos e resolução de cidade já existem; reutilizar semântica para calcular cidades ativas.

### Established Patterns
- Estado do board vive na URL (`q`, `city`, `sort`, `page`, `vaga`); mudanças de filtro usam `router.replace` com `scroll: false`.
- Board público é RSC em `frontend/app/(public)/page.tsx`, com `fetchBoard` `cache: "no-store"` e timeout em `frontend/lib/jobs.ts`.
- Contrato público não expõe contato (`JobPublic`/`JobListResponse`); qualquer extensão de payload deve preservar isso.
- Tema dark/roxo com tokens CSS: `accent`, `accent-soft`, `accent-strong`, `line-strong`, `surface`, `canvas`.

### Integration Points
- `backend/app/schemas/job.py` e `backend/app/api/v1/public.py`: estender resposta do board com cidades ativas (D-04).
- `backend/app/crud/jobs.py`: adicionar consulta de cidades ativas publicadas/não expiradas compatível com filtros globais do board.
- `frontend/lib/api.ts`, `frontend/lib/jobs.ts`, `frontend/app/(public)/page.tsx`: propagar novo campo até a UI.
- `frontend/components/board/BoardToolbar.tsx`: renderizar apenas chips ativos (D-01/D-02), lidar com cidade selecionada obsoleta (D-03), e substituir sort nativo por dropdown custom acessível (D-05/D-08).
- `frontend/components/board/JobCard.tsx` e chips/sort em `BoardToolbar.tsx`: aplicar linguagem de hover consistente (D-09-D-12).

</code_context>

<specifics>
## Specific Ideas

No specific external product references — seguir as decisões capturadas, os critérios de sucesso da fase e os padrões visuais existentes do board público.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 28-polimento-ux-da-home*
*Context gathered: 2026-11-22*
