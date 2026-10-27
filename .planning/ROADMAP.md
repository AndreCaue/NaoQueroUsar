# Roadmap: NQU — NaoQueroUsar

## Overview

Da fundação de dados ao board público curado e "sem fricção": primeiro garantimos o contrato de dados e o acesso seguro do master, depois automatizamos a extração de vagas brutas com LLM (a parte mais frágil), protegemos o contato com Turnstile server-side, entregamos o board público mobile-first (busca/filtro/reveal), completamos a área de revisão admin, e fechamos com o ciclo de vida de 14 dias, postura de confiança/legal e o wiring de deploy. As fases de extração, reveal e ciclo de vida são as de maior risco e estão sinalizadas para possível pesquisa dedicada.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Backend Foundation, Data & Admin Auth** - FastAPI + Neon, schema `jobs` (status/expires_at/contact invariant) e login master por JWT (completed 2026-10-15)
- [ ] **Phase 2: LLM Extraction Pipeline** - Colar texto bruto → extração estruturada via Groq → cards `pending` (HIGH RISK)
- [ ] **Phase 3: Contact Reveal & Anti-Spam** - Contato só via endpoint dedicado, Turnstile server-side + rate limit (HIGH RISK)
- [x] **Phase 4: Public Board Frontend** - Grade mobile-first, modal, busca/filtro/ordenação, reveal no clique, tema dark roxo (completed 2026-10-27)
- [ ] **Phase 5: Admin Review Area** - Fila `pending`, aprovar/editar/excluir, texto-fonte ao lado dos campos, publicar
- [ ] **Phase 6: Lifecycle, Trust, Legal & Launch** - Expiração hard-delete 14 dias, badge/report, páginas legais e deploy (HIGH RISK)

## Phase Details

### Phase 1: Backend Foundation, Data & Admin Auth

**Goal**: Um backend FastAPI rodando contra o Neon, com o contrato de dados de `jobs` e acesso seguro do master-admin — a base que todas as fases seguintes referenciam.
**Depends on**: Nothing (first phase)
**Requirements**: ADMN-01, ADMN-02, ADMN-03
**Success Criteria** (what must be TRUE):

  1. Master autentica na API admin com a senha definida em variável de ambiente; requisições a rotas administrativas sem token válido recebem 401.
  2. Sessão admin persiste via JWT durante o uso — cada requisição protegida valida o token, sem senha ou token expostos.
  3. A migração inicial cria a tabela `jobs` com enum de status (`pending`/`published`/`needs_review`/`invalid`), CHECK de ao menos um contato (email ou telefone), `created_at`/`expires_at` como `timestamptz` e os índices (lista pública, cidade, busca trigram, `expires_at`).
  4. A API pública de leitura (lista/detalhe de vagas `published`) responde sem autenticação e **sem** expor email/telefone no payload.
  5. Backend sobe localmente contra o Neon com configuração validada por env (`pydantic-settings`), health endpoint, CORS e logging.

**Plans**: 4 plans

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Monorepo scaffold, Python tooling, config (pydantic-settings), app factory, health, CORS, logging, async DB engine

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — `jobs` data contract: SQLAlchemy model + Alembic initial migration (enum, CHECK, timestamptz, search_text/pg_trgm, indexes)
- [x] 01-03-PLAN.md — Admin auth: password hash verify, JWT login (`/auth/login`), `require_admin` guard, protected `/admin/me`

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-04-PLAN.md — Public read API (published/non-expired, contact-free) + pytest validation suite + seed script

### Phase 2: LLM Extraction Pipeline

**Goal**: O admin cola um texto bruto com várias vagas e obtém cards estruturados com status `pending`, sem vagas perdidas nem campos inventados.
**Depends on**: Phase 1
**Requirements**: EXTR-01, EXTR-02, EXTR-03, EXTR-04, EXTR-05, EXTR-06, EXTR-07, EXTR-08, EXTR-09
**Success Criteria** (what must be TRUE):

  1. Colar um texto com múltiplas vagas gera uma lista estruturada e cada vaga entra no banco com status `pending` — e só é criada se tiver ao menos um contato (email ou telefone).
  2. Saídas que falham na validação estrita de schema ou no grounding contra o texto-fonte viram `needs_review`/`invalid`, em vez de publicar dados inventados.
  3. Pastes grandes são chunked/throttled abaixo do TPM do Groq sem estourar 429; truncamento (`finish_reason == length`) e divergência entre vagas detectadas e extraídas são sinalizados.
  4. Telefones em pt-BR são normalizados para E.164 gerando links `wa.me` confiáveis; o texto de entrada é delimitado para reduzir prompt injection.
  5. O modelo é configurável via `GROQ_MODEL` com cadeia de fallback e erro claro (nunca hardcoded) — corrigindo os Llama aposentados em 2026-08-16.

**Plans**: 4 plans

Plans:
**Wave 1**

- [ ] 02-01-PLAN.md — Extraction foundations: source_snippet-less schema config (EXTRACT_* envs, .env.example), strict JSON Schema + Pydantic contract, chunking, pt-BR phone normalization, grounding helpers

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 02-02-PLAN.md — Groq extraction engine: AsyncGroq client, model fallback chain (gpt-oss-20b/120b), throttled chunked `extract_jobs` with grounding, classification (D-05/D-06), truncation/divergence detection

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 02-03-PLAN.md — Persistence + admin endpoint: Alembic migration adding `jobs.source_snippet`, `POST /api/v1/admin/extract` (JWT, sync timeout, atomic commit, save+summary), API test suite

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 02-04-PLAN.md — Minimal `/admin/paste` frontend: login → paste → extract → summary with alerts/discards (D-04), plain-CSS dark theme, human smoke checkpoint

**⚠️ HIGH RISK**: Componente mais frágil (churn de modelo, limites de taxa, truncamento silencioso, hallucination). Pode precisar de `/gsd-research-phase` — confirmar IDs de modelo Groq vivos, suporte a strict structured outputs, limites TPM/TPD atuais e estratégia de chunking. *(Phase 2 research done: `02-RESEARCH.md` — openai/gpt-oss-20b/120b vivos, strict structured outputs OK, 30 RPM/1K RPD/8K TPM/200K TPD.)*

### Phase 3: Contact Reveal & Anti-Spam

**Goal**: O contato das vagas é servido apenas por um endpoint dedicado, protegido por Turnstile verificado no servidor e rate limiting por IP — ocultar no cliente não basta.
**Depends on**: Phase 1
**Requirements**: SECR-01, SECR-02, SECR-03, PUBL-05
**Success Criteria** (what must be TRUE):

  1. Email/telefone **não** aparecem no payload público de lista/detalhe; o contato só é retornado por um endpoint dedicado de reveal por ID.
  2. O reveal exige token Turnstile válido, single-use e não expirado, verificado server-side (Siteverify), rejeitando `timeout-or-duplicate`.
  3. O endpoint de reveal tem rate limiting por IP; excesso de requisições é bloqueado.
  4. O login do admin também é protegido por Turnstile contra credential stuffing.

**Plans**: 5 plans

**Wave 1**

- [x] 03-01-PLAN.md — Fundação fail-closed: `Settings` do Turnstile (chave obrigatória fora de dev, chave de teste bloqueada em prod), knobs `REVEAL_RATE_LIMIT`/`LOGIN_RATE_LIMIT`, pin do `slowapi==0.1.10` e resolver de IP proxy-aware (`X-Real-IP` → XFF mais à direita público → client host → `unknown`)

**Wave 2** *(blocked on 03-01)*

- [x] 03-02-PLAN.md — Cliente Siteverify (httpx) fail-closed com binding de `action`, seam `get_turnstile_verifier`, limiter slowapi in-memory com handler 429 pt-BR, status do Turnstile no `/health` e fixtures de teste offline

**Wave 3** *(blocked on 03-02)*

- [x] 03-03-PLAN.md — Endpoint único de reveal `POST /api/v1/public/jobs/{id}/reveal-contact`: rate limit → 404 → Siteverify (403) → 200, com `RevealRequest`/`ContactRevealResponse` e 10 casos de teste

**Wave 4** *(blocked on 03-02, 03-03)*

- [x] 03-04-PLAN.md — Login do master protegido: `cf_token` no `LoginRequest`, ordem rate limit → Siteverify (403) → bcrypt (401) → JWT (200), `loginAdmin(password, cfToken)` e widget `next-turnstile` `interaction-only` no admin (backend + front no mesmo plano)

**Wave 5** *(blocked on 03-03, 03-04)*

- [x] 03-05-PLAN.md — Prova real: smoke test do Siteverify contra a Cloudflare (segredos `1x`/`2x`/`3x`), regressão completa, varredura de vazamento de segredo e checkpoint do login no browser

**⚠️ HIGH RISK**: Superfície sensível a scraping e momento de payoff — precisa ser server-side desde o início (retrofit seria reescrita). Pode precisar de `/gsd-research-phase` — detalhes do Siteverify (vida útil/single-use do token, `timeout-or-duplicate`, extração de IP via proxy, chaves de teste) e abordagem de rate limiting.

### Phase 4: Public Board Frontend

**Goal**: Qualquer visitante encontra uma vaga e o contato para se candidatar em segundos, no mobile, sem cadastro nem login.
**Depends on**: Phase 3 (reveal), Phase 1 (API pública de leitura)
**Requirements**: PUBL-01, PUBL-02, PUBL-03, PUBL-04, PUBL-06, SRCH-01, SRCH-02, SRCH-03, UIUX-01, UIUX-02, UIUX-03
**Success Criteria** (what must be TRUE):

  1. Visitante vê uma grade responsiva mobile-first de vagas publicadas sem login; o card mostra título, início das atividades (expansível), salário quando houver e botão "Ver a vaga".
  2. Abrir o card mostra um modal de detalhes completo e mobile-friendly; o contato fica oculto por padrão e é revelado no clique via Turnstile.
  3. Busca por palavra-chave é insensível a acento e caixa ("sao paulo" == "São Paulo"); filtro por cidade (SP, RJ, BH, Remoto) e ordenação por data (recentes primeiro) funcionam e o estado persiste na URL.
  4. Tema dark roxo minimalista atende contraste WCAG AA (`#a78bfa` para texto); botão "Doações" amarelo `#facc15` discreto (efeito só no hover) no topo; espaços de ADS reservados (banner topo, sidebar, entre cards).
  5. Candidatura funciona por WhatsApp (`wa.me`) e/ou email a partir do detalhe da vaga.

**Plans**: 6 plans

**Wave 1**

- [x] 04-01-PLAN.md — Public shell + Tailwind v4 foundation: theme tokens, header/Doações/footer/skip link, `/doacoes`, route group
- [x] 04-02-PLAN.md — Backend search & demo seed: migration `0003` (requirements in `search_text`), accent-insensitive `q`, `city`, `sort`, dev-only seed script

**Wave 2** *(blocked on 04-01)*

- [x] 04-03-PLAN.md — Server-rendered board: cards, pagination, skeleton/error states, native detail dialog

**Wave 3** *(blocked on 04-03)*

- [x] 04-04-PLAN.md — Reveal & apply: Turnstile-gated contact, tab-scoped cache, WhatsApp/e-mail links, `?vaga=` deep link

**Wave 4** *(blocked on 04-02, 04-03, 04-04)*

- [x] 04-05-PLAN.md — Search/city/sort controls with URL state, debounce, and filtered/out-of-range states

**Wave 5** *(blocked on 04-01..04-05)*

- [x] 04-06-PLAN.md — ADS placeholders, focus/motion polish, `verify-ssr.ps1` gate, human verification checkpoint

**UI hint**: yes

### Phase 5: Admin Review Area

**Goal**: O master transforma vagas `pending` em `published` em minutos — colar → extrair → revisar → aprovar — com o texto-fonte ao lado para conferência.
**Depends on**: Phase 1 (auth), Phase 2 (extração), Phase 4 (tema)
**Requirements**: REVW-01, REVW-02, REVW-03, REVW-04, REVW-05
**Success Criteria** (what must be TRUE):

  1. Admin autenticado vê a fila de vagas com status `pending`.
  2. Admin aprova uma vaga (status muda para `published` e ela passa a aparecer na home pública) / edita os campos pelo ID / exclui uma vaga — com mudanças persistidas.
  3. Admin vê o trecho do texto-fonte ao lado dos campos extraídos como auxílio de conferência (grounding).
  4. O fluxo completo colar → extrair → revisar → aprovar funciona de ponta a ponta dentro da área admin (consumindo o endpoint de extração da Fase 2).
  5. A área admin é protegida: acesso sem sessão autenticada é redirecionado/negado.

**Plans**: 4 plans

Plans:
**Wave 1**

- [ ] 05-01-PLAN.md — Backend review API (CRUD helpers, schemas, rotas, testes)
- [x] 05-02-PLAN.md — Admin shell Tailwind v4 (admin.css, layout, ToastProvider, AdminGuard, hub)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 05-03-PLAN.md — Migracao do paste para Tailwind v4
- [ ] 05-04-PLAN.md — Fila de review (ReviewRow, modais, ReviewQueue, page)

**UI hint**: yes

### Phase 6: Lifecycle, Trust, Legal & Launch

**Goal**: O board se mantém honesto e seguro — vagas somem em 14 dias de forma confiável — e a plataforma tem postura de confiança/legal e deploy prontos para lançar.
**Depends on**: Phase 1 (schema/expires_at), Phase 4 (board público)
**Requirements**: LIFE-01, LIFE-02, LIFE-03, LIFE-04, TRST-01, TRST-02, TRST-03
**Success Criteria** (what must be TRUE):

  1. Cada vaga nasce com `expires_at` = `created_at` + 14 dias; vagas `published` expiradas são hard-deleted por uma declaração idempotente em UTC (invocação duplicada não causa erro; vaga futura nunca é apagada).
  2. Vagas `pending` não revisadas também expiram após 14 dias; a expiração é disparada por endpoint protegido por `CRON_SECRET`, com passe de recuperação (catch-up).
  3. Vaga publicada exibe o badge "Vaga revisada"; o visitante consegue denunciar uma vaga (report).
  4. As páginas de privacidade, termos e o aviso "somos apenas meio de divulgação" (LGPD) existem e são acessíveis.
  5. Frontend (Vercel) e backend (Railway/Render) estão deployados com CORS travado à origem do front e segredos configurados; o caminho de leitura pública permanece rápido quando o backend está acordando (cold-start documentado).

**Plans**: TBD
**UI hint**: yes
**⚠️ HIGH RISK**: Pitfalls operacionais (cron do Vercel Hobby 1x/dia UTC sem retry, spin-down Render, locks do Neon, timezones) + wiring de infra. Pode precisar de `/gsd-research-phase` — escolher scheduler externo, confirmar comportamento de CU-hour/pooling do Neon e mecânica dos free-tiers Render/Railway empiricamente.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend Foundation, Data & Admin Auth | 4/4 | Complete   | 2026-10-15 |
| 2. LLM Extraction Pipeline | 0/TBD | Not started | - |
| 3. Contact Reveal & Anti-Spam | 4/5 | In Progress|  |
| 4. Public Board Frontend | 6/6 | Complete   | 2026-10-27 |
| 5. Admin Review Area | 1/4 | In Progress|  |
| 6. Lifecycle, Trust, Legal & Launch | 0/TBD | Not started | - |
