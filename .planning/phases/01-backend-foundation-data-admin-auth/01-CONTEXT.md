# Phase 1: Backend Foundation, Data & Admin Auth - Context

**Gathered:** 2026-10-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Um backend FastAPI rodando contra o Neon, com o contrato de dados de `jobs` e acesso seguro do master-admin — a base que todas as fases seguintes referenciam.

**Entregue nesta fase (ADMN-01, ADMN-02, ADMN-03):**
- Login do master com senha em variável de ambiente → JWT; rotas admin bloqueiam acesso sem token válido.
- Migração inicial criando a tabela `jobs` (enum de status de 4 valores, CHECK de ao menos um contato, `created_at`/`expires_at` timestamptz, índices) + infraestrutura de busca.
- API pública de leitura (lista/detalhe de `published`) sem auth e sem expor contato.
- Backend sobe localmente contra o Neon com config validada por env (`pydantic-settings`), health endpoint, CORS e logging.
- Esqueleto do monorepo (`backend/` + `frontend/`).

**Fora desta fase:** extração LLM (Phase 2), Turnstile/rate limit e endpoint de reveal (Phase 3), UI pública e busca/filtros (Phase 4), área de revisão admin (Phase 5), hard-delete/expiração e deploy (Phase 6).

</domain>

<decisions>
## Implementation Decisions

### Autenticação do master
- **D-01:** JWT via header `Authorization: Bearer <token>` (não cookie httpOnly — o front em Vercel e o backend em Railway/Render são domínios distintos, cookies cross-site complicam).
- **D-02:** Token único de vida longa (12h) guardado em `sessionStorage` no front — sobrevive a F5 dentro da aba, morre ao fechar a aba. Sem refresh token.
- **D-03:** Senha do master armazenada como hash no ambiente: `ADMIN_PASSWORD_HASH` (bcrypt/argon2 via `passlib`). Nunca em texto puro.
- **D-04:** Proteção do login (rate limit + Turnstile) fica para a Phase 3 (SECR-02/SECR-03). Phase 1 entrega login apenas com verificação de hash.
- **D-05:** Env obrigatório nesta fase: `DATABASE_URL`, `ADMIN_PASSWORD_HASH`, `JWT_SECRET`, `JWT_EXPIRES_IN`, `CORS_ORIGINS`, `ENV`. Validação na inicialização (falha rápido se faltar). Incluir `.env.example` (sem segredos).

### Schema `jobs` (detalhes)
- **D-06:** PK `id UUID DEFAULT gen_random_uuid()` — IDs opacos/não-enumeráveis (expostos na URL pública e no reveal).
- **D-07:** `city` como `varchar` com validação no app (Pydantic), conjunto permitido: São Paulo, Rio de Janeiro, Belo Horizonte, Remoto. Sem enum de DB nem CHECK (adicionar cidade não exige migração).
- **D-08:** `salary` como texto livre (`varchar`) — guarda "R$ 2.000 a R$ 2.500", "A combinar", etc. (filtro por faixa salarial fica para v2/FCT-01).
- **D-09:** Enum de status `job_status` com 4 valores: `pending`, `published`, `needs_review`, `invalid`.
- **D-10:** CHECK de ao menos um contato (email ou telefone não vazios após trim).
- **D-11:** Migração inicial cria `pg_trgm` + `unaccent` e uma coluna normalizada `search_text` = `lower(unaccent(title || ' ' || company || ' ' || activities))` com índice GIN trigram — deixa a busca acento-insensível (SRCH-01) pronta para a Phase 4, com filtro de status aplicável.
- **D-12:** `created_at`/`expires_at`/`updated_at` como `timestamptz`; `expires_at` computado no servidor (`created_at` + 14 dias). Índices para lista pública, cidade, trigram search e `expires_at`.
- **D-13:** Sem soft delete — hard delete (a cargo da Phase 6). Campos de referência da pesquisa: title (obrigatório), company, activities, requirements, salary, benefits, city, contact_email, contact_phone.

### API pública de leitura
- **D-14:** Paginação por offset: `?page=&limit=` (limit 1–50, default ~20), com total count na resposta.
- **D-15:** A lista retorna todos os campos **exceto contato** (title, company, activities, requirements, salary, benefits, city, created_at, expires_at, status) — o modal abre instantâneo sem segundo request.
- **D-16:** Phase 1 entrega apenas `GET /public/jobs` (lista) e `GET /public/jobs/{id}` (detalhe). Busca/filtro/ordenação (SRCH-01..03) ficam para a Phase 4.
- **D-17:** A query pública sempre filtra `status='published' AND expires_at > now()` — vagas expiradas nunca aparecem mesmo antes do hard-delete da Phase 6.
- **D-18:** Contato NUNCA no payload público (nem lista nem detalhe). O reveal é endpoint dedicado na Phase 3.

### Estrutura do repo & dev local
- **D-19:** Monorepo: `backend/` (FastAPI) preenchido nesta fase; `frontend/` (Next.js) criado como esqueleto mínimo, pronto para a Phase 4.
- **D-20:** Tooling Python com `uv` + `pyproject.toml` (+ lockfile).
- **D-21:** Dev conecta direto ao Neon (string `-pooler`, `sslmode=require`); sem Docker/Postgres local. Migrações (`alembic upgrade head`) rodam contra o Neon.
- **D-22:** Validação da fase com uma suíte `pytest` (+`pytest-asyncio`) focada nos critérios (login ok/errado, rota admin sem token→401, rota pública sem contato, lista só `published` e não-expiradas) rodando contra um banco de teste (branch do Neon) + script de seed de um job publicado.

### OpenCode's Discretion
- Estrutura interna de camadas do FastAPI (`api/`, `services/`, `crud/`, `schemas/`, `models/`, `core/`) — seguir o padrão da pesquisa `ARCHITECTURE.md`.
- Formato exato do envelope de resposta de erro, logging estruturado, shape do `/health`, claims exatos do JWT (`sub=admin`, `role=admin`, `exp`, `iat`).
- Estratégia do banco de teste (branch dedicada do Neon) e ferramentas de teste/CI.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos
- `.planning/ROADMAP.md` — Phase 1: goal, dependências e os 5 critérios de sucesso.
- `.planning/REQUIREMENTS.md` — ADMN-01, ADMN-02, ADMN-03 e restrições de escopo.
- `.planning/PROJECT.md` — visão, constraints (stack fixada), Key Decisions.

### Arquitetura e contrato de dados
- `.planning/research/ARCHITECTURE.md` — SQL do schema `jobs`, estrutura de projeto FastAPI, superfície REST, padding/deploy, CORS, env vars.
- `.planning/research/STACK.md` — versões fixadas e bibliotecas (FastAPI, SQLAlchemy 2.x async, asyncpg, Alembic, Pydantic v2, PyJWT, passlib).
- `.planning/research/PITFALLS.md` — Pitfalls 7 (contato fora do payload), 11 (timezone/expires_at), 12 (Neon CU-hour/pooling), 13 (host free); seção de Security Mistakes (auth).
- `.planning/research/FEATURES.md` — tabela de features table-stakes, dependências e anti-features.

</canonical_refs>

<code_context>
## Existing Code Insights

Projeto greenfield — nenhum código de aplicação existe ainda (apenas `.planning/` e `AGENTS.md`). Nada a reutilizar; esta fase estabelece os padrões-base (camadas FastAPI, config por env, migrations, convenções de teste) que as fases seguintes herdam.

</code_context>

<specifics>
## Specific Ideas

- Contato é o ativo sensível: nunca no payload público, mesmo na lista — o reveal é exclusivo da Phase 3 (alinhado ao Pitfall 7).
- `expires_at > now()` já na leitura pública, para o board nunca mostrar vaga morta antes mesmo do hard-delete.
- Busca acento-insensível resolvida no banco desde a migração inicial (`unaccent` + trigram), evitando retrofit na Phase 4.
- Fronteira de fase respeitada: sem Turnstile/rate limit (Phase 3), sem filtros/busca/ordenação (Phase 4), sem hard-delete (Phase 6).

</specifics>

<deferred>
## Deferred Ideas

- **Turnstile no login + rate limiting** — Phase 3 (SECR-02/SECR-03).
- **Endpoint de reveal de contato** — Phase 3.
- **Busca por palavra-chave, filtro por cidade e ordenação** (SRCH-01..03) — Phase 4.
- **Páginas/UI pública e tema dark** — Phase 4.
- **Hard-delete de vagas expiradas (14 dias)** — Phase 6 (Phase 1 apenas filtra na leitura).
- **Filtro por faixa salarial (FCT-01)** — v2; exigiria campos numéricos (hoje `salary` é texto livre).

</deferred>

---

*Phase: 1-Backend Foundation, Data & Admin Auth*
*Context gathered: 2026-10-13*
