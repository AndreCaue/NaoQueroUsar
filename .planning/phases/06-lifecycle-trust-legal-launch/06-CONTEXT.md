# Phase 6: Lifecycle, Trust, Legal & Launch - Context

**Gathered:** 2026-10-27
**Status:** Ready for planning

<domain>
## Phase Boundary

O board se mantém honesto e seguro — vagas somem em 14 dias de forma confiável — e a plataforma tem postura de confiança/legal e deploy prontos para lançar.

**Entregue nesta fase (LIFE-01 a LIFE-04, TRST-01 a TRST-03):**

- **LIFE-01:** Cada vaga nasce com `expires_at` = `created_at` + 14 dias.
- **LIFE-02:** Job agendado (APScheduler no processo) hard-deleta vagas publicadas expiradas, de forma idempotente em UTC.
- **LIFE-03:** Vagas `pending` não revisadas também expiram após 14 dias (mesma regra de clock).
- **LIFE-04:** Expiração também acionável via endpoint protegido por `CRON_SECRET` (trigger manual/catch-up).
- **TRST-01:** Vaga publicada exibe badge "Vaga revisada" (automático via status).
- **TRST-02:** Visitante pode reportar uma vaga (endpoint + log estruturado no backend).
- **TRST-03:** Páginas de privacidade, termos e aviso de intermediário (LGPD) acessíveis.

**Fora desta fase:** deploy real (frontend Vercel + backend Railway/Render) com CORS travado, segredos e cold-start (critério de sucesso 5); PIX real; AdSense/consentimento LGPD; SEO avançado; alerts/retention (v2).

</domain>

<decisions>
## Implementation Decisions

### Ciclo de vida e expiração (LIFE-01 a LIFE-04)
- **D-01:** Agendador do hard delete: **APScheduler no processo** do backend (`BackgroundScheduler` no FastAPI). Sem scheduler externo no MVP.
- **D-02:** **Diário às 03:00 UTC** (sweep no APScheduler) **+ endpoint protegido por `CRON_SECRET`** para trigger manual/catch-up (LIFE-04). Endpoint idempotente.
- **D-03:** Política de expiração: **mesma regra para `pending` e `published`** — `expires_at = created_at + 14 dias` (LIFE-01); não revisado não escapa do clock.
- **D-04:** **Hard delete** cobre **publicadas e pending expiradas** — tudo que passou de `expires_at` é removido.

### Confiança e legal (TRST-01 a TRST-03)
- **D-05:** Badge "Vaga revisada" = **automático por status** — derivado de `published` (único path que passa pela aprovação manual; aprovação é definitiva — D-08 da Fase 5). Sem campo extra no Job.
- **D-06:** Report de visitante = **endpoint + log estruturado** no backend (sem tabela/migration nova); sem follow-up automático persistido (notificação ao master fica manual).
- **D-07:** Estrutura das páginas legais = **página única com seções** (privacidade, termos, aviso LGPD/intermediário).

### OpenCode's Discretion
- Mecânica exata da rota do endpoint `CRON_SECRET` e nome do secret (`CRON_SECRET`) no Settings.
- Copy/texto das páginas legais (redação jurídica pendente — task humana, fora de código).
- Estratégia de retry/fallback do hard delete (falha transiente).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos
- `.planning/ROADMAP.md` — Phase 6: goal, dependências (Phase 1, Phase 4), 5 critérios de sucesso, HIGH RISK, UI hint: yes.
- `.planning/REQUIREMENTS.md` — LIFE-01 a LIFE-04, TRST-01 a TRST-03; tabela de rastreabilidade (linhas 148-154).

### Decisões herdadas (não reabrir)
- `.planning/phases/01-backend-foundation-data-admin-auth/01-CONTEXT.md` — D-06 (UUID), D-14 (paginação), D-17 (filtro `published AND expires_at > now()`), D-18 (contato nunca no payload público).
- `.planning/phases/02-llm-extraction-pipeline/02-CONTEXT.md` — D-04 (endpoint + página mínima de paste), D-05/D-06 (status pending/needs_review), D-08 (source_snippet).
- `.planning/phases/03-contact-reveal-anti-spam/03-CONTEXT.md` — D-03 (ordem das checagens), D-04 (contato em memória por job), D-05 a D-10 (rate limit), D-11 a D-14 (fail-closed), D-17 (ordem login).
- `.planning/phases/04-public-board-frontend/04-CONTEXT.md` — D-03 a D-06 (busca/filtro/ordenação/paginação), D-07 (Server Component), D-09 (modal + URL state), D-10 (reveal no clique), D-12 (ADS placeholders), D-13 (contraste AA).
- `.planning/phases/05-admin-review-area/05-CONTEXT.md` — D-01 a D-04 (fila/status/ordenação), D-05/D-06 (aprovação individual/edição), D-07/D-08 (hard delete/definitiva).

### Backend (contrato e padrões)
- `backend/app/models/job.py` — modelo `Job`, `JobStatus`, CHECKs `title_not_blank`/`at_least_one_contact`, `expires_at`.
- `backend/app/crud/jobs.py` — `list_published`, `get_published`, `bulk_create_pending` (padrão para o sweep).
- `backend/app/api/v1/admin.py` — router admin (rota nova de expiração sob `/admin`).
- `backend/app/core/config.py` — `Settings` (novas chaves: `CRON_SECRET`).
- `backend/alembic/versions/` — migrations numeradas (0001-0003); sweep não exige migration nova.

### Frontend (padrões e assets)
- `frontend/components/board/` — `Pagination`, `JobCard`, `JobDetailDialog`, `JobGrid` (padrões para badge/report).
- `frontend/app/(public)/` — board, modal, reveal, `/doacoes`.

### Pesquisa
- `.planning/research/PITFALLS.md` — Pitfall 7 (contato oculto ≠ protegido); checklist "Looks Done But Isn't".
- `.planning/research/STACK.md` — stack fixada (FastAPI, SQLAlchemy 2.x async, APScheduler a adicionar).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/crud/jobs.py::list_published` — query paginada/filtrada já pronta; servir de base para o sweep de expiração (status + `expires_at < now()`).
- `backend/app/models/job.py::Job` — clock de expiração já materializado (`expires_at = created_at + 14d`); sweep é operação sobre esse campo.

### Established Patterns
- Camadas: `api/v1` (router fino) → `services` → `crud` → `schemas`/`models`; commit explícito por operação.
- Erros pt-BR no `detail`; validação de env obrigatória no startup (`Settings`).
- Testes: pytest + pytest-asyncio; suíte roda de `backend/`; contratos pt-BR.

### Integration Points
- Backend: adicionar `BackgroundScheduler` (APScheduler) + job de hard delete + endpoint protegido por `CRON_SECRET` (rota admin).
- Frontend: badge "Vaga revisada" no card/modal; UI de report no modal; páginas legais server-rendered (rota pública).

</code_context>

<specifics>
## Specific Ideas

- **Sweep:** diário às 03:00 UTC; idempotente; UTC; hard delete de vagas com `expires_at < now()` (published + pending); catch-up via endpoint `CRON_SECRET`.
- **Badge:** automático por status — `published` já implica revisão (aprovação manual); sem campo novo.
- **Report:** endpoint público com `job_id` + motivo → log estruturado; sem tabela nova.

</specifics>

<deferred>
## Deferred Ideas

- **Deploy real:** frontend no Vercel + backend no Railway/Render; CORS travado à origem do front; segredos (`CRON_SECRET`, Cloudflare, Groq, DB); cold-start do backend documentado (critério de sucesso 5).
- **Chaves Cloudflare reais + widget de produção** — Phase 6.
- **PIX real / doações** — Phase 6 (TRST-03 adjacent) / já adiado.
- **AdSense / banner de consentimento LGPD** — Phase 6 / v2.
- **Limiter distribuído** (Redis/tabela) — Phase 6, se backend sair de 1 worker.
- **SEO avançado** (sitemap, JSON-LD `JobPosting`, OG) — v2 (SEO-01/02).
- **Alerts/retention** (ALRT-01) — v2.
- **LGPD:** revisão jurídica por advogado brasileiro antes do lançamento — task humana, não de código (registrada em STATE.md).
- **`/gsd-research-phase`** para scheduler externo, comportamento de CU-hour/pooling do Neon e empirismo dos free-tiers Render/Railway — fase HIGH RISK aberta.

### Reviewed Todos (not folded)

- Nenhum todo pendente para esta fase (`todo.match-phase 6` retornou vazio).

</deferred>

---

*Phase: 06-lifecycle-trust-legal-launch*
*Context gathered: 2026-10-27*
