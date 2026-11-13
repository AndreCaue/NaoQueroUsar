# Phase 8: Admin Review Area Completeness - Context

**Gathered:** 2026-11-12

<domain>
## Phase Boundary

O master termina a área de revisão admin — fila `pending`, aprovar/editar/excluir vagas com texto-fonte ao lado, publicar, com o fluxo completo colar → extrair → revisar → aprovar funcionando. A área admin (`/admin`) combina a extração jà existente em `/admin/paste` e a nova fila de revisão (`/admin/review`), usando Tailwind v4 (paridade com o público). As vagas aprovadas (`published`) passam a aparecer na home pública imediatamente.

**Entregue nesta fase (ADMN-10/12, REVW-10/12):**
- Fila de vagas `pending` (e aba `needs_review` para correções), com filtro por cidade, ordenação por mais recentes, paginação offset.
- Ações por vaga: Aprovar (→`published`), Editar (modal com todos os campos), Excluir (hard delete com confirmação).
- Aprovação refresca `expires_at` para now + 14 dias, garantindo vaga publicada não está expirada.
- Modal de edição com validação `at_least_one_contact` (title_not_blank + CHECK no banco).
- Feedback via toast próprio + atualização otimista da fila.
- Área admin protegida: `Authorization: Bearer <token>` (JWT). Sem sessão autenticada = 401.
- Texto-fonte (`source_snippet`) exibido ao lado dos campos (desktop: lado a lado; mobile: empilhado/accordion), somente leitura.

**Fora desta fase:** renovação de vagas expiradas (Phase 9), badge "Vaga revisada"/report/páginas legais (Phase 9), deploy produção (Phase 9/10), aprovação em lote (fora do escopo enxuto).
</domain>

<decisions>
## Implementation Decisions

### Fila de revisão (status, filtros, ordenação)
- **D-01:** A fila principal exibe **apenas vagas `pending`**. Vagas `needs_review` (defeitos menores da extração) ficam numa **aba separada** "Precisam correção", cada uma com sua própria fila. `invalid` não é revisável (não foi salvo — Phase 2 D-05). Coerente com REVW-01 e evita misturar "pronto para publicar" com "precisa ajuste".
- **D-02:** Ordenação padrão: **mais recentes primeiro** (`created_at DESC`), tie-break por `id DESC` (Phase 4 D-06a). Vagas recém-extraídas aparecem no topo, coerente com o fluxo colar→revisar→aprovar.
- **D-03:** Filtro por **cidade** (chips SP, RJ, BH, Remoto) reutilizando o padrão da home pública (Phase 4). Busca por texto livre na fila admin não está prevista — volume 100–500/mês torna busca menos crítica; cidade é o filtro útil.

### Extração e ingestão (fluxo colar → extrair → revisar)
- **D-E2E-01:** Quando `POST /admin/extract` retorna 0 linhas válidas (todas descartadas pelo LLM), a resposta é um `ExtractSummaryResponse` válido com `saved_pending=0, saved_needs_review=0, discarded=[...], alerts=[...]`. O frontend deve exibir "Nenhuma vaga encontrada no texto" como resultado bem-sucedido, não como erro. Isso cobre casos de texto de grupos que não contenham formato de vaga reconhecível.
- **D-E2E-02:** **Auto-deduplicação** — se o mesmo texto for colado duas vezes, o sistema suprime o duplicate e exibe notificação ao admin: "Essas vagas já foram inseridas". O hash do texto é usado para comparação (normalizado: lowercased, acentos removidos, espaços collapse). Rationale: reduz ruido na fila; volume 100-500/month torna dedup viável; a revisão manual ainda captura casos edge.

### Interação de revisão (aprovar/editar/excluir)
- **D-E2E-03:** Aprovação via `PATCH /admin/jobs/{job_id}/approve` funciona para ambos os status `pending` e `needs_review`. O status muda para `published` e `expires_at` é refreshed para `now() + 14 dias` (UTC). A aprovação é definitiva — `published` não volta para `pending`.
- **D-E2E-04:** Edição via `PUT /admin/jobs/{job_id}` com schema `JobUpdate` (parcial — apenas campos fornecidos são aplicados). Se o admin tentar salvar sem contato (both `contact_email` e `contact_phone` são null/blank), o DB CHECK `at_least_one_contact` lança `IntegrityError`, que o backend captura e retorna: `"Vaga precisa ter ao menos um contato (email ou telefone)"` (422). Se apenas alguns campos forem fornecidos, os valores existentes são preservados para os campos não fornecidos (semântica de partial update).
- **D-E2E-05:** Exclusão via `DELETE /admin/jobs/{job_id}` é **hard delete**. A operação é naturalmente idempotente: chamar delete duas vezes no mesmo job retorna 404 na segunda chamada (job já foi removido). Não há "soft delete" nem "archive" — o modelo Phase 1 não possui flag de soft delete.

### Toast notifications e feedback visual
- **D-E2E-06:** Feedback via **toast próprio** (componente React mínimo, sem lib externa, paridade com Phase 4) + **atualização otimista** da fila (remove o item ao aprovar/excluir e revalida). Variantes: success (aprovado, excluído), error (validacao falhou, rede), info (extração 0 vagas). Auto-dismiss ~3s. O toast carrega o tipo e a mensagem pt-BR verbatim.

### Rotas, tema e proteção da área admin
- **D-E2E-07:** Todas as rotas admin (`/admin/jobs`, `/admin/jobs/{job_id}/approve`, `/admin/jobs/{job_id}`, `/admin/jobs/{job_id}/delete`, `/admin/extract`) exigem `Authorization: Bearer <token>` via `require_admin`. Acesso sem token = 401. Rota `/admin/extract` também exige admin (não é pública). O front tem guard client-side: sem token em `sessionStorage`, redireciona para login. O backend continua bloqueando com 401 (`require_admin`) — o front apenas melhora a UX.
- **D-E2E-08:** O painel admin adota **Tailwind v4** (route group `(admin)`), migrando paste + fila juntos para unificar o estilo com o público. `globals-admin.css` (CSS plano) é substituído. Paridade visual com o público (Phase 4 D-12/D-13). *Override da herança Phase 4, que mantinha admin em CSS plano.*
- **D-E2E-09:** O hub `/admin` tem links para `/admin/paste` (colar/extração, já existente) e `/admin/review` (fila). Header admin compartilhado com logout. Ponto de entrada único para o painel.

### Pós-aprovação
- **D-E2E-10:** Após aprovar um job, o frontend usa **otimista update** — remove o item aprovado imediatamente da fila `pending`, então faz refetch da lista em background. Se o refetch falhar, o item reaparece na fila. Isso fornece feedback instantâneo ao admin sem esperar a resposta da API.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos
- `.planning/ROADMAP.md` — Phase 8: goal, dependências (Phase 1 auth, Phase 2 extração, Phase 4 tema), sucesso criteria `REVW-10/12/ADMN-10/12`, `UI hint: yes`.
- `.planning/REQUIREMENTS.md` — REVW-10..REVW-12, ADMN-10..12, EXTR-10..12 (linhas 16-26); tabela de rastreabilidade (linhas 8-27).
- `.planning/PROJECT.md` — constraints travadas: dark minimalista, pt-BR, admin único, mobile-first, volume 100-500/mês, sem cadastro/login.
- `.planning/STATE.md` — posição atual: milestone v1.1 EmpregaNoix, Phase 7 executado, iniciando Phase 8.

### Decisões herdadas (não reabrir)
- `.planning/phases/01-backend-foundation-data-admin-auth/01-CONTEXT.md` — D-01 (Bearer JWT, sem cookie), D-05 (env obrigatório, falha rápido), D-06 (sem soft delete), D-14 (paginação), D-17 (filtro published AND expires_at > now()), D-18 (contato nunca no payload público).
- `.planning/phases/02-llm-extraction-pipeline/02-CONTEXT.md` — D-04 (endpoint + página mínima de paste), D-05/D-06 (status pending/needs_review, descarte sem título/contato), D-08 (source_snippet persistido por vaga para REVW-05).
- `.planning/phases/03-contact-reveal-anti-spam/03-CONTEXT.md` — D-03 (ordem das checagens), D-04 (contato em memória por vaga), D-17 (ordem login: rate limit → Siteverify → bcrypt → JWT).
- `.planning/phases/04-public-board-frontend/04-CONTEXT.md` — D-03..D-06 (busca/filtro/ordenação/paginação), D-07 (Server Component), D-09 (modal + URL state), D-10 (reveal no clique), D-12 (tokens de tema), D-13 (contraste AA).
- `.planning/phases/05-admin-review-area/05-CONTEXT.md` — D-01..D-04 (fila status/filtros/ordenacao), D-05..D-08 (interacao approve/editar/excluir), D-09..D-10 (texto-fonte layout), D-11..D-14 (rotas, tema, feedback admin).

### Backend (contrato e padrões)
- `backend/app/api/v1/extract.py` — endpoint `/admin/extract` (transação única, bulk_create_pending, alerts pt-BR, fallback de modelo via `GROQ_MODEL` env).
- `backend/app/api/v1/admin.py` — rotas admin: `/jobs` (listar por status/cidade/paginação/sort), `/jobs/{job_id}` (retrieve), `/jobs/{job_id}/approve` (pending/needs_review → published, expiry refresh), `/jobs/{job_id}` (PUT edit, IntegrityError → contato), `/jobs/{job_id}` (DELETE hard delete), `/expire` (catch-up, X-Cron-Secret).
- `backend/app/api/v1/router.py` — registro das rotas admin under prefix `/admin`, tags `admin`.
- `backend/app/crud/jobs.py` — `list_by_status` (paginação offset, filtro cidade, tie-break id), `approve_job` (refresca expires_at), `update_job` (partial update, IntegrityError → at_least_one_contact), `delete_job` (hard delete), `get_job`.
- `backend/app/models/job.py` — modelo `Job`, `JobStatus` (pending/published/needs_review/invalid), CHECK `title_not_blank`, CHECK `at_least_one_contact` (email ou telefone), `expires_at` timestamptz, `source_snippet` text.
- `backend/app/schemas/job.py` — `JobPublic` (sem contato), `JobAdmin` (com contato, para respostas admin), `JobUpdate` (fields: title, company, activities, requirements, salary, benefits, city, contact_email, contact_phone).
- `backend/app/deps.py` — `require_admin` (Bearer JWT, 401 sem token), `require_cron_secret` (X-Cron-Secret header, 503 quando ausente/incorreto).
- `backend/app/services/extraction/extractor.py` — `extract_jobs()`: chama Groq modelo via `GROQ_MODEL`, retorna `CandidateOutcome` (save/save_needs_review/discarded), validacao de contato via DB CHECK.
- `backend/alembic/versions/` — migrations numeradas (0001, 0002, 0003); schema já tem todos os CHECKs e colunas necessárias.

### Frontend (padrões e assets)
- `frontend/app/admin/paste/page.tsx` — referência de integração (login com Turnstile, token em sessionStorage, reset por remount). A ser migrado para Tailwind v4.
- `frontend/app/admin/review/page.tsx` — nova página da fila admin (listar, aprovar, editar, excluir). Route group `(admin)` ou `/admin/review`.
- `frontend/lib/api.ts` — estender com funções admin autenticadas (Bearer token de sessionStorage): `listJobsByStatus`, `approveJob`, `updateJob`, `deleteJob`, `extractJobs`.
- `frontend/components/board/Pagination.tsx`, `JobGrid.tsx`, `JobDetailDialog.tsx` — padrões de paginação/modal/grid reutilizáveis para a fila admin.
- `frontend/components/admin/Toast.tsx` — componente de toast próprio, sem lib externa, pt-BR messages, auto-dismiss 3s.
- `frontend/app/(public)/public.css` — tokens Tailwind v4 do público (referência de paridade visual).
- `frontend/tokens/` — tokens Tailwind v4: `--color-primary-500: #8b5cf6`, `--color-primary-400: #a78bfa`, `--bg-dark-900: #0f0a1a`, `--bg-dark-800: #1a1025`, `--color-accent-yellow: #facc15`.

### Pesquisa
- `.planning/research/STACK.md` — versões fixadas (Next 16, Tailwind 4, FastAPI, Pydantic v2).
- `.planning/research/PITFALLS.md` — Pitfall 7 (contato oculto ≠ protegido), checklist "Looks Done But Isn't".

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/api/v1/extract.py` — endpoint de extração admin; transação única, tratamento de 0 resultados, alerts, modelo via `GROQ_MODEL`.
- `backend/app/api/v1/admin.py` — todas as rotas admin (list, approve, edit, delete, expire); auth via `require_admin`; resolução de cidade via `resolve_city`.
- `backend/app/crud/jobs.py` — padrões de query paginada/filtrada (`list_by_status`), aprovação, edição com validação de contato, exclusão hard.
- `backend/app/models/job.py` — modelo Job completo com CHECKs, `source_snippet`, `expires_at` computation.
- `frontend/lib/api.ts` — funções admin autenticadas (Bearer token); estender com extract, list, approve, update, delete.
- `frontend/components/admin/Toast.tsx` — referência de toast próprio (sem lib externa).
- `frontend/components/admin/` — novos componentes de fila e modal em desenvolvimento (Tailwind v4).

### Established Patterns
- **Camadas backend:** `api/v1` (router fino) → `services` → `crud` → `schemas`/`models`. Novas rotas admin seguem o padrão do `extract.py` (transaction única, commit explícito).
- **Erros pt-BR no `detail`**, renderizados verbatim pelo front.
- **Chaves obrigatórias no startup** via `Settings` (pydantic-settings).
- **Frontend admin hoje é CSS plano** (`globals-admin.css`); a partir desta fase, Tailwind v4 no route group admin (D-E2E-08) — paridade com o público.
- **Testes** rodam a partir de `backend/` (`cd backend; .venv\Scripts\python.exe -m pytest -q`), contra Postgres real.

### Integration Points
- `backend/app/api/v1/admin.py` — adicionar/verificar rotas de review (listar por status, aprovar, editar, excluir) neste router (prefixo `/admin`).
- `backend/app/api/v1/router.py` — registro das rotas (já registra `admin.router`).
- `backend/app/schemas/job.py` — schema `JobAdmin` e `JobUpdate` com campos de contato (diferente de `JobPublic`).
- `frontend/app/admin/` — novo route group `(admin)` ou reorganização de `/admin/paste` e `/admin/review` sob Tailwind v4.
- `frontend/lib/api.ts` — estender com funções admin autenticadas (Bearer token de sessionStorage).
- `frontend/components/board/` — Pagination, JobGrid, JobDetailDialog — padrões reutilizáveis adaptados para a fila admin.

</code_context>

<specifics>
## Specific Ideas

- **Volume 100–500 vagas/mês** e extração em lotes: a fila admin precisa ser rápida de processar; aprovação individual com atualização otimista mantém o fluxo fluido.
- **Aprovação é o gate de qualidade** (PROJECT.md): o admin confere o texto-fonte ao lado antes de publicar.
- **Paridade visual com o público** (D-E2E-08): o painel admin adota Tailwind v4, unificando o estilo e acelerando o dev da fila/modal.
- **Toast próprio** (sem lib) mantém o bundle enxuto e o padrão "sem shadcn/lib" da Phase 4.
- **Contato nunca no payload público** (Phase 3): o schema admin pode expor contato (é área autenticada), mas a home pública continua contact-free.
- **Auto-deduplicação de paste** (D-E2E-02): hash do texto normalizado para evitar duplicatas na fila; notificação ao admin quando duplicate é suprimido.
- **Otimista update pós-aprovação** (D-E2E-10): remove item da fila imediatamente, refetch background; melhora a UX do master na revisão.

</specifics>

<deferred>
## Deferred Ideas

- **Aprovação em lote** (checkbox + "Aprovar selecionadas") — descartado nesta fase; volume 100-500/mês justifica aprovação individual; se o volume crescer, considerar depois.
- **Ação "Rejeitar"** (→`invalid` ou →`needs_review`) — descartado; excluir cobre o caso de remover vaga indesejada.
- **Reversão published→pending** ("Despublicar") — Descartado; aprovação definitiva. Se admin errar, exclui e re-extrai/edita.
- **Busca por texto livre na fila admin** — Descartado (filtro por cidade basta).
- **Middleware Next.js server-side para proteção admin** — Descartado (token é Bearer em sessionStorage; mudar para cookie httpOnly é fora do escopo).
- **Biblioteca de toast externa** (sonner/react-hot-toast) — Descartado; componente próprio mantém consistência com Phase 4.
- **Ciclo de vida / expiração hard-delete 14 dias** — Phase 6 (LIFE-01..04).
- **Chaves reais do Cloudflare + wiring de deploy** — Phase 6.

### Reviewed Todos (not folded)
Nenhum todo pendente para esta fase (verificação contra `todo.match-phase 8` retornou vazio).

</deferred>

---

*Phase: 08-admin-review-area-completeness*
*Context gathered: 2026-11-12*