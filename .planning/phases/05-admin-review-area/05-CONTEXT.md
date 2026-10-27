# Phase 5: Admin Review Area - Context

**Gathered:** 2026-10-26
**Status:** Ready for planning

<domain>
## Phase Boundary

O master transforma vagas `pending` em `published` em minutos — colar → extrair → revisar → aprovar — com o texto-fonte ao lado para conferência. A área admin (hub `/admin`) agrupa a extração (já existente em `/admin/paste`) e a nova fila de revisão (`/admin/review`), e o painel admin passa a usar Tailwind v4 (paridade com o público).

**Entregue nesta fase (REVW-01..05):**
- Fila de revisão de vagas `pending` (e aba separada para `needs_review`), com filtro por cidade, ordenação por mais recentes, paginação offset.
- Ações por vaga: Aprovar (→`published`), Editar (modal com todos os campos), Excluir (hard delete com confirmação).
- Modal de edição com todos os campos editáveis (title, company, activities, requirements, salary, benefits, city, contact_email, contact_phone), validando `at_least_one_contact` e cidade do conjunto permitido.
- Texto-fonte (`source_snippet`) exibido ao lado dos campos (desktop: lado a lado; mobile: empilhado/accordion), somente leitura, com placeholder quando vazio.
- Hub `/admin` com links para `/admin/paste` e `/admin/review`, header admin compartilhado (logout), guard client-side de acesso.
- Migração do painel admin para Tailwind v4 (paste + fila), toast próprio para feedback, atualização otimista da fila.

**Fora desta fase:** aprovação em lote (decidido individual), rejeitar/devolver status (decidido não ter), reversão published→pending (decidido não), destaque automático de termos no snippet (decidido não), soft delete (fora do escopo — hard delete), ciclo de vida/expiração (Phase 6), badge "Vaga revisada"/report/páginas legais (Phase 6), deploy/env de produção (Phase 6).

</domain>

<decisions>
## Implementation Decisions

### Fila de revisão (status, filtros, ordenação)
- **D-01:** A fila principal exibe **apenas vagas `pending`** (prontas para aprovar). Vagas `needs_review` (defeitos menores da extração) ficam numa **aba/seção separada** "Precisam correção", cada uma com sua própria fila. `invalid` não é revisável (não foi salvo — Phase 2 D-05). Coerente com REVW-01 e evita misturar "pronto para publicar" com "precisa ajuste".
- **D-02:** Ordenação padrão: **mais recentes primeiro** (`created_at DESC`), tie-break por `id DESC` (Phase 4 D-06a). Vagas recém-extraídas aparecem no topo, coerente com o fluxo colar→revisar→aprovar.
- **D-03:** Filtro por **cidade** (chips SP, RJ, BH, Remoto) reutilizando o padrão da home pública (Phase 4). Sem busca por texto livre na fila admin — volume 100–500/mês torna busca menos crítica; cidade é o filtro útil.
- **D-04:** **Paginação offset** (page/limit, limit 24, controles), mesmo padrão da home pública (Phase 4 D-07/D-09). Reaproveita componentes e padrão de URL state.

### Interação de revisão (aprovar/editar/excluir)
- **D-05:** Aprovação é **individual por vaga**, via botão "Aprovar" em cada item. Ao aprovar, status muda para `published` e o item sai da fila (atualização otimista). Feedback por toast. Sem aprovação em lote (escopo enxuto — REVW-02).
- **D-06:** Edição via **modal** com todos os campos editáveis (title, company, activities, requirements, salary, benefits, city, contact_email, contact_phone). City validado contra o conjunto permitido {São Paulo, Rio de Janeiro, Belo Horizonte, Remoto}; contato exige ao menos um (CHECK `at_least_one_contact`). Salvar persiste (REVW-03).
- **D-07:** Exclusão é **hard delete com confirmação** (modal "Tem certeza?"). Coerente com o modelo sem soft delete (Phase 1 D-06) e com REVW-04. Sem ação "Rejeitar" (redundante com excluir) e sem reversão published→pending (aprovação definitiva).
- **D-08:** Aprovação é **definitiva** — `published` não volta para `pending`. Se errar, o admin exclui e re-extrai/edita. Evita estados inconsistentes na home pública.

### Texto-fonte ao lado dos campos (REVW-05)
- **D-09:** Layout **lado a lado em desktop** (painel de campos à esquerda, snippet à direita, sticky) e **empilhado em mobile** (snippet abaixo dos campos em accordion). Mobile-first, paridade com Phase 4.
- **D-10:** Snippet é **somente leitura** (referência de grounding; não editável). Sem destaque automático de termos — o admin confere visualmente (evita falsos positivos). Quando vazio/nulo, exibir placeholder "Sem texto-fonte disponível" (itálico/cinza), sem mudar o layout.

### Rotas, tema e feedback da área admin
- **D-11:** **Hub `/admin`** com links para `/admin/paste` (colar/extração, já existente) e `/admin/review` (fila). Header admin compartilhado com logout. Ponto de entrada único para o painel.
- **D-12:** O painel admin **adota Tailwind v4** (novo route group), migrando **paste + fila juntos** para unificar o estilo. `globals-admin.css` (CSS plano) é substituído. Paridade visual com o público (Phase 4). *Override da herança Phase 4, que mantinha admin em CSS plano.*
- **D-13:** Feedback via **toast próprio** (componente React mínimo, sem lib externa) + **atualização otimista** da fila (remove o item ao aprovar/excluir e revalida). Variantes success/error, auto-dismiss ~3s.
- **D-14:** Proteção de acesso no front é **guard client-side com redirecionamento**: sem token em `sessionStorage`, redireciona para o login (padrão do `ExtractForm`). O backend continua bloqueando com 401 (`require_admin`) — o front só melhora a UX. Sem middleware server-side (token é Bearer, não cookie — Phase 1 D-01).

### OpenCode's Discretion
- Estrutura de arquivos/componentes da fila e do modal de edição (`components/admin/` ou similar), nomes de helpers de fetch.
- Mecânica exata do toast (posicionamento, animação, z-index) e da atualização otimista (rollback em erro).
- Como o hub `/admin` se comporta quando não autenticado (redireciona para login ou mostra login inline).
- Paginação visual (controles vs "Ver mais") na fila admin — reusar o padrão da Phase 4 (JobGrid/Pagination) se fizer sentido.
- Empty state da fila (copy pt-BR) e estado de loading (skeleton).
- Validação client-side do form de edição (zod) e mensagens de erro (renderizar `body.detail` verbatim, padrão Phase 4).
- Se a aba "Precisam correção" é uma rota separada ou tab client-side.

### Folded Todos
Nenhum todo pendente para esta fase (`todo.match-phase 5` retornou vazio).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos
- `.planning/ROADMAP.md` — Phase 5: goal, dependências (Phase 1 auth, Phase 2 extração, Phase 4 tema), 5 critérios de sucesso, `UI hint: yes`.
- `.planning/REQUIREMENTS.md` — REVW-01..REVW-05 (linhas 30–34); tabela de rastreabilidade (linhas 143–147).
- `.planning/PROJECT.md` — constraints travadas: dark minimalista, pt-BR, admin único, mobile-first, volume 100–500/mês.

### Decisões herdadas (não reabrir)
- `.planning/phases/01-backend-foundation-data-admin-auth/01-CONTEXT.md` — D-06 (UUID opaco), D-14 (paginação), D-17 (filtro published AND expires_at > now()), D-18 (contato nunca no payload público), D-01 (Bearer JWT, sem cookie), D-05 (env obrigatório, falha rápido), D-06 (sem soft delete).
- `.planning/phases/02-llm-extraction-pipeline/02-CONTEXT.md` — D-04 (endpoint + página mínima de paste), D-05/D-06 (status pending/needs_review, descarte sem título/contato), D-08 (source_snippet persistido por vaga para REVW-05).
- `.planning/phases/03-contact-reveal-anti-spam/03-CONTEXT.md` — D-03 (ordem das checagens), D-04 (contato em memória por vaga), D-17 (ordem login: rate limit → Siteverify → bcrypt → JWT).
- `.planning/phases/04-public-board-frontend/04-CONTEXT.md` — D-03..D-06 (busca/filtro/ordenação/paginação), D-07 (Server Component), D-09 (modal + URL state), D-10 (reveal no clique), D-12 (ADS placeholders), D-13 (contraste AA), tokens de tema.

### Backend (contrato e padrões)
- `backend/app/api/v1/admin.py` — router `/admin` atual (só `/me`); comentário explícito de que as rotas de review são Phase 5.
- `backend/app/api/v1/extract.py` — endpoint de extração (a área admin consome); padrão de transaction única (D-03 da Phase 2).
- `backend/app/crud/jobs.py` — `list_published`, `get_published`, `bulk_create_pending`; padrão de paginação/filtros a replicar para a fila admin (listar por status).
- `backend/app/models/job.py` — modelo `Job`, `JobStatus` (pending/published/needs_review/invalid), CHECKs `title_not_blank`/`at_least_one_contact`, `source_snippet`.
- `backend/app/schemas/job.py` — schemas públicos; será necessário schema admin (JobAdmin com contato) para edição/review.
- `backend/app/deps.py` — `require_admin` (Bearer JWT) a reusar em todas as rotas admin.
- `backend/alembic/versions/` — migrations numeradas (0001, 0002, 0003); nova migration apenas se necessário (nenhuma prevista — modelo já tem todos os campos).

### Frontend (padrões e assets)
- `frontend/app/admin/paste/ExtractForm.tsx` — referência de integração (login com Turnstile, token em sessionStorage, reset por remount). A ser migrado para Tailwind v4 (D-12).
- `frontend/app/admin/paste/globals-admin.css` — tokens atuais do admin; a ser substituído por Tailwind v4.
- `frontend/lib/api.ts` — padrão de fetch + extração de `body.detail` (pt-BR) para mensagens de erro.
- `frontend/components/board/` — Pagination, JobCard, JobDetailDialog, JobGrid (padrões reutilizáveis para a fila admin).
- `frontend/app/(public)/public.css` — tokens Tailwind v4 do público (referência de paridade visual).

### Pesquisa
- `.planning/research/STACK.md` — versões fixadas (Next 16, Tailwind 4, FastAPI, Pydantic v2).
- `.planning/research/PITFALLS.md` — Pitfall 7 (contato oculto ≠ protegido), checklist "Looks Done But Isn't".

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/deps.py::require_admin` — guard Bearer JWT a reusar em todos os endpoints admin de review (listar/editar/excluir/aprovar).
- `backend/app/crud/jobs.py` — padrão de query paginada/filtrada (`list_published`) a replicar para listar por status (`list_by_status` ou similar), com paginação offset e tie-break por id.
- `backend/app/models/job.py::Job` / `JobStatus` — modelo completo, já tem `source_snippet`, `status`, todos os campos editáveis. Nenhuma migration nova prevista.
- `frontend/app/admin/paste/ExtractForm.tsx` — referência de login (Turnstile interaction-only, token em sessionStorage, reset por remount) e de extração.
- `frontend/components/board/Pagination.tsx`, `JobGrid.tsx`, `JobDetailDialog.tsx` — padrões de paginação/modal/grid reutilizáveis para a fila admin.
- `frontend/lib/api.ts` — padrão de fetch + `body.detail` pt-BR; estender com funções admin (listJobsByStatus, approveJob, updateJob, deleteJob).

### Established Patterns
- **Camadas backend:** `api/v1` (router fino) → `services` → `crud` → `schemas`/`models`. Novas rotas admin seguem o padrão do `extract.py` (transaction única, commit explícito).
- **Erros pt-BR no `detail`**, renderizados verbatim pelo front.
- **Chaves obrigatórias no startup** via `Settings` (pydantic-settings).
- **Frontend admin hoje é CSS plano** (`globals-admin.css`); a partir desta fase, Tailwind v4 no route group admin (D-12) — paridade com o público.
- **Testes** rodam a partir de `backend/` (`cd backend; .venv\Scripts\python.exe -m pytest -q`), contra Postgres real.

### Integration Points
- `backend/app/api/v1/admin.py` — adicionar rotas de review (listar por status, aprovar, editar, excluir) neste router (prefixo `/admin`).
- `backend/app/api/v1/router.py` — registro das rotas (já registra `admin.router`).
- `backend/app/schemas/job.py` — adicionar schema admin (JobAdmin/JobUpdate) com campos de contato (diferente de JobPublic).
- `frontend/app/admin/` — novo route group `(admin)` ou reorganização de `/admin/paste` e `/admin/review` sob Tailwind v4.
- `frontend/app/admin/paste/page.tsx` + `ExtractForm.tsx` — migrar para Tailwind v4 (D-12).
- `frontend/lib/api.ts` — estender com funções admin autenticadas (Bearer token de sessionStorage).

</code_context>

<specifics>
## Specific Ideas

- **Volume 100–500 vagas/mês** e extração em lotes: a fila admin precisa ser rápida de processar; aprovação individual com atualização otimista mantém o fluxo fluido.
- **Aprovação é o gate de qualidade** (PROJECT.md): o admin confere o texto-fonte ao lado antes de publicar.
- **Paridade visual com o público** (D-12): o painel admin adota Tailwind v4, unificando o estilo e acelerando o dev da fila/modal.
- **Toast próprio** (sem lib) mantém o bundle enxuto e o padrão "sem shadcn/lib" da Phase 4.
- **Contato nunca no payload público** (Phase 3): o schema admin pode expor contato (é área autenticada), mas a home pública continua contact-free.

</specifics>

<deferred>
## Deferred Ideas

- **Aprovação em lote** (checkbox + "Aprovar selecionadas") — descartado nesta fase; se o volume justificar, considerar depois.
- **Ação "Rejeitar"** (→`invalid` ou →`needs_review`) — descartado; excluir cobre o caso.
- **Reversão published→pending** ("Despublicar") — descartado; aprovação definitiva.
- **Destaque automático de termos no snippet** — descartado; conferência visual.
- **Soft delete / arquivar** — fora do escopo (modelo sem soft delete; hard delete).
- **Busca por texto livre na fila admin** — descartado (filtro por cidade basta).
- **Middleware Next.js server-side para proteção admin** — descartado (token é Bearer em sessionStorage; mudar para cookie httpOnly é fora do escopo).
- **Biblioteca de toast externa** (sonner/react-hot-toast) — descartado; componente próprio.
- **PIX real / páginas legais / badge "Vaga revisada" / report** — Phase 6 (TRST-01..03).
- **Ciclo de vida / expiração hard-delete 14 dias** — Phase 6 (LIFE-01..04).
- **Chaves reais do Cloudflare + wiring de deploy** — Phase 6.

### Reviewed Todos (not folded)
Nenhum todo revisado (nenhum match para a Phase 5).

</deferred>

---

*Phase: 05-admin-review-area*
*Context gathered: 2026-10-26*