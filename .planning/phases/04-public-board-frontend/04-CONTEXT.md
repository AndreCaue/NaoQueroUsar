# Phase 4: Public Board Frontend - Context

**Gathered:** 2026-10-22
**Status:** Ready for planning

<domain>
## Phase Boundary

O visitante encontra uma vaga e o contato em segundos, no celular, sem cadastro nem login: grade de vagas publicadas → modal de detalhe → reveal do contato (Turnstile) → candidatura por WhatsApp/e-mail. Inclui busca sem acento, filtro por cidade, ordenação por data com estado na URL, o tema dark roxo com contraste AA, o botão "Doações" e os espaços reservados de ADS.

**Entregue nesta fase (PUBL-01..04, PUBL-06, SRCH-01..03, UIUX-01..03):**
- Rota pública do board (`/`), renderizada no servidor, mobile-first, dark.
- Card com título, início das atividades expansível, salário quando houver e "Ver a vaga".
- Modal de detalhe mobile-friendly (`<dialog>` nativo) com deep-link `?vaga=<uuid>`.
- Reveal do contato no clique, contra o endpoint da Phase 3, com os 7 estados do `03-UI-SPEC.md`.
- Candidatura via `wa.me` (primário) e `mailto:` (secundário), montados no front a partir do E.164 cru.
- Backend: `q`, `city`, `sort` em `GET /api/v1/public/jobs` (a fronteira explícita em `public.py:32`).
- Tema dark com os tokens do `04-UI-SPEC.md` (aprovado), botão "Doações" → `/doacoes`, placeholders de ADS.
- Seed **dev-only** para popular vagas `published` e permitir verificação no browser.

**Fora desta fase:** aprovação/edição de vagas no admin (Phase 5 — REVW-01..05); PIX real e páginas legais (Phase 6); AdSense/consentimento LGPD (Phase 6); chaves reais do Cloudflare e wiring de deploy (Phase 6); limiter distribuído (Phase 6); sitemap/JSON-LD/OG images (não requisitado).

</domain>

<decisions>
## Implementation Decisions

### Entrega e fatiamento
- **D-01:** A fase **não** é dividida em sub-fases. Uma única Phase 4, planejada em **5–6 planos** em ondas: (1) fundação Tailwind v4 + route group público → (2) board + card SSR → (3) modal + reveal + candidatura → (4) backend `q`/`city`/`sort` + busca/filtros/URL → (5) tema/Doações/ADS + polimento. Os 11 requisitos fecham juntos.
- **D-02:** Como a aprovação de vaga é Phase 5, esta fase entrega um **seed local dev-only** (`backend/scripts/seed_public_demo.py` ou equivalente) que insere N vagas `published` com contatos fake e `expires_at` futuro. Regras: só roda com `ENV=dev`/local, **nunca** em produção, não cria endpoint HTTP de seed, e respeita o CHECK `at_least_one_contact`. É o caminho de verificação no browser.

### Busca, filtro e ordenação (SRCH-01..03)
- **D-03:** `q` procura em **título + empresa + atividades + requisitos**. Cidade tem filtro próprio e **combina com `q` por AND** (não substitui, não preenche `q`).
- **D-04:** A busca usa a coluna **`search_text` já existente** (`backend/app/models/job.py:48`), mantida por trigger `BEFORE INSERT OR UPDATE` com `immutable_unaccent(lower(...))` e indexada por GIN `pg_trgm` parcial (`status='published'`) — tudo criado na migration `0001_initial_jobs.py`. **Não** criar coluna nova e **não** normalizar em Python na escrita.
  - **Lacuna a fechar:** o trigger atual concatena `title + company + activities` e **omite `requirements`**. Uma migration nova (`0003_...`) deve substituir `jobs_set_search_text()` incluindo `coalesce(NEW.requirements,'')` e fazer backfill (`UPDATE jobs SET search_text = ...` ou `UPDATE ... SET title = title` para re-disparar o trigger).
  - A consulta compara `search_text` com `immutable_unaccent(lower(:q))` como substring; o índice trigram já serve. Não introduzir `unaccent(...)` na query (a coluna já está normalizada).
- **D-05:** Params na URL: `q`, `city`, `sort`, `page` (idênticos no front e na API — sem tradução). `city` usa os slugs `sao-paulo | rio-de-janeiro | belo-horizonte | remoto`, mapeados para os valores canônicos de `ALLOWED_CITIES` em `backend/app/services/extraction/extractor.py:56`. **Atenção:** os valores canônicos são **sem acento** (`"Sao Paulo"`, não `"São Paulo"`) — o filtro compara com esses valores.
- **D-06:** `sort` aceita `recentes` (default, `created_at DESC`) e `antigas` (`created_at ASC`), cobrindo SRCH-03. `page` mantém offset; `limit=24` (dentro do `le=50` atual). Filtro de validade (`status='published' AND expires_at > now()`) permanece aplicado em itens **e** no `total`.

### Renderização, cache e URL
- **D-07:** O board é **Server Component**. A lista é buscada no servidor a partir de `searchParams` e o HTML inicial já contém as vagas (SEO). `q/city/sort/page` disparam re-render no servidor — sem spinner de primeira carga.
- **D-08:** **Sem cache**: `cache: 'no-store'` na leitura do board. Nada de ISR/`revalidateTag`. Justificativa: volume de 100–500 vagas/mês, risco zero de vaga expirada/removida, e evita explosão de variantes de cache com os filtros.
- **D-09:** O card abre um **`<dialog>` nativo** no cliente e grava **`?vaga=<uuid>`** na URL (`history.replaceState`/`router.replace`, preservando `q/city/sort/page`). Carregar a URL com `?vaga=` reabre o modal; um id desconhecido/expirado cai no estado "vaga não encontrada" sem quebrar o board. Fechar o modal remove o param.
- **D-10:** O reveal só monta o widget do Turnstile **no clique** (token vive 300 s e é single-use), com `appearance="interaction-only"` e `id="turnstile-reveal"` (não colide com o `turnstile-widget` do login). O contato revelado fica em memória **por vaga, com escopo de aba** — usar module-scope/context, **não** um `Map` em `useRef` do host do dialog (morre se o grid desmontar).

### Tema, Doações e ADS
- **D-11:** "Doações" leva a uma rota estática **`/doacoes`** no route group público, com copy honesta ("apoie o projeto — chave PIX em breve") e link de volta. Nunca `#`, nunca botão morto. PIX real é Phase 6.
- **D-12:** ADS nesta fase são **apenas placeholders reservados**: banner topo 90px, sidebar 300×250 (≥1024px) e inline 90px a cada 6 cards — caixa tracejada com rótulo "Publicidade" e **altura fixa** (anti-CLS). Nenhum script de anúncio, nenhum tracking, nenhum cookie de terceiro.

### Contraste e tokens (herdado do UI-SPEC aprovado)
- **D-13:** `#a78bfa` é a cor de **texto** de acento e do focus ring; `#8b5cf6` é **marca** (borda/hover/indicador); preenchimento com **texto branco** usa `#7c3aed` (5,70:1) porque `#8b5cf6` reprova AA com branco (4,23:1) — exigência de UIUX-01. Borda de controle `#6d5a91` (3,26:1) no lugar do `#4a3b6b` do admin (1,97:1).

### OpenCode's Discretion
- **Tailwind v4 no route group `(public)`** para que o Preflight não vaze no `/admin/*` (que segue em CSS plano com `globals-admin.css`); shadcn **não** usado; ícones SVG inline. Já aprovado no `04-UI-SPEC.md` (decisão de discrição #1).
- Estrutura de arquivos/componentes do front (`components/` público), nomes de helpers de fetch, e se o fetch do servidor usa `NEXT_PUBLIC_API_URL` ou uma variável server-side.
- Formato do seed dev-only (quantidade de vagas, títulos/cidades variados, guarda de ambiente).
- Paginação visual (controles), skeleton de loading, e detalhes de wiring de foco/aria do `<dialog>`.
- Como `?vaga=` convive com `q/city/sort/page` na montagem do estado inicial.
- Mecânica exata de `immutable_unaccent` na comparação e se o backfill da migration `0003` re-dispara o trigger ou escreve direto.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos
- `.planning/ROADMAP.md` — Phase 4: goal, `Depends on` (Phase 3, Phase 1), 5 critérios de sucesso, `UI hint: yes`.
- `.planning/REQUIREMENTS.md` — PUBL-01, PUBL-02, PUBL-03, PUBL-04, PUBL-06, SRCH-01, SRCH-02, SRCH-03, UIUX-01, UIUX-02, UIUX-03; tabela de rastreabilidade (linhas 131–142).
- `.planning/PROJECT.md` — constraints travadas: dark minimalista, `#8b5cf6`/`#a78bfa`, `#facc15`, pt-BR, admin único, mobile-first.

### Contrato visual (obrigatório)
- `.planning/phases/04-public-board-frontend/04-UI-SPEC.md` — **aprovado (6/6 dimensões)**. Tokens de espaçamento/tipografia/cor, 13 pares de contraste calculados, ~45 strings pt-BR, contrato de URL (`q/city/sort/page`), anatomia do card, máquina de estados do reveal, `<dialog>` + acessibilidade, alturas de ADS, e 14 linhas de discrição.
- `.planning/phases/03-contact-reveal-anti-spam/03-UI-SPEC.md` — máquina de estados e copy do reveal herdadas. **Atenção:** §B ("nunca cachear o contato entre abertura/fechamento do modal") é **substituída** por D-04 da Phase 3 e por D-10 acima; a reconciliação está declarada no `04-UI-SPEC.md` §E.

### Contrato de backend e reveal
- `.planning/phases/03-contact-reveal-anti-spam/03-CONTEXT.md` — D-01..D-19: ordem das checagens, cache em memória por vaga (D-04), rate limit (D-05..D-10), fail-closed (D-11..D-14).
- `backend/app/api/v1/public.py` — `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/reveal-contact`; **linha 32** é a fronteira explícita `# Phase boundary (D-16): search/city/sort are Phase 4`.
- `backend/app/schemas/job.py` — `JobPublic` (sem contato), `JobListResponse`, `RevealRequest`, `ContactRevealResponse` (contrato de campos para card/modal).
- `backend/app/crud/jobs.py` — `list_published` (filtros + paginação) e `get_published` (404 do reveal) a estender.
- `backend/app/models/job.py` — modelo `Job`; `search_text` na linha 48; CHECKs `title_not_blank` e `at_least_one_contact`.
- `backend/alembic/versions/0001_initial_jobs.py` — `pg_trgm` + `unaccent`, `immutable_unaccent`, trigger `jobs_set_search_text`, GIN `idx_jobs_search_trgm`, `idx_jobs_city_published`.
- `backend/alembic/versions/0002_jobs_source_snippet.py` — última migration; a nova é `0003`.
- `backend/app/services/extraction/extractor.py` — `ALLOWED_CITIES` (linha 56, valores **sem acento**) e `CITY_MAP`.

### Decisões herdadas (não reabrir)
- `.planning/phases/01-backend-foundation-data-admin-auth/01-CONTEXT.md` — D-06 (UUID opaco), D-14 (paginação), D-17 (filtro `published AND expires_at > now()`), D-18 (contato nunca no payload público).
- `.planning/phases/02-llm-extraction-pipeline/02-CONTEXT.md` — telefone em E.164; `wa.me` montado no front.
- `.planning/research/PITFALLS.md` — Pitfall 7 (contato oculto ≠ protegido), checklist "Looks Done But Isn't".
- `.planning/research/STACK.md` — Tailwind v4, Next/React, zod; versões fixadas.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/lib/api.ts` — padrão de `fetch` para a API + extração de `body.detail` (pt-BR) para mensagens de erro; seguir o mesmo estilo para os novos helpers de leitura e reveal.
- `frontend/app/admin/paste/ExtractForm.tsx` — componente `"use client"` com `next-turnstile` (`appearance="always"` no login), reset por remount via `key`, e `sessionStorage["nqu_admin_token"]`; é a referência de integração do widget.
- `frontend/app/admin/paste/globals-admin.css` — tokens de cor/tipografia e classes `.admin-error`/disabled do admin, em **CSS plano**. Não deve receber o Preflight do Tailwind.
- `backend/app/schemas/job.py::JobPublic` — campos exatos que o card/modal renderizam (`title`, `company`, `activities`, `requirements`, `salary`, `benefits`, `city`, `created_at`).
- `backend/app/crud/jobs.py::list_published` — já devolve `(items, total)` com filtro de validade; é o ponto único a estender com `q`/`city`/`sort`.
- `backend/app/api/v1/public.py::reveal_contact` — endpoint pronto; a UI só consome (403 com `detail` pt-BR, 404, 429 com `Retry-After`).

### Established Patterns
- **Erros pt-BR no `detail`, renderizados verbatim** pelo front — a UI não traduz nem reescreve o texto do backend.
- **`/api/v1/public/*` sem autenticação**; CORS travado à origem do front.
- **Testes** rodam contra Postgres real (`TEST_DATABASE_URL`/`DATABASE_URL`; suite é skipada sem DB), com `conftest.py` forçando env determinístico.
- **Migrations numeradas** (`0001`, `0002`), com extensões `pg_trgm`/`unaccent` já habilitadas e índice trigram em uso.
- **Frontend atual é mínimo**: `app/page.tsx` é um placeholder, não há Tailwind/postcss/shadcn, e `app/globals.css` está órfão (não importado).

### Integration Points
- `frontend/app/layout.tsx` — `<html lang="pt-BR">`; o route group público entra aqui (ou em `app/(public)/layout.tsx`).
- `frontend/app/page.tsx` — placeholder a substituir pelo board.
- `backend/app/api/v1/public.py:32` — remover o comentário de fronteira ao adicionar os filtros.
- `backend/app/crud/jobs.py:13` — assinatura de `list_published` ganha `q`/`city`/`sort`.
- `backend/alembic/versions/` — nova migration `0003` (trigger + backfill).
- `backend/scripts/` — novo diretório para o seed dev-only.

</code_context>

<specifics>
## Specific Ideas

- **Seed dev-only** é o único caminho para ver vagas no browser nesta fase: a aprovação (`pending → published`) só existe na Phase 5.
- **Cidades no banco não têm acento** (`"Sao Paulo"`): os slugs da URL mapeiam para esses valores; exibir o rótulo acentuado é responsabilidade da UI.
- **Datas sempre absolutas** `dd/mm/aaaa` em `America/Sao_Paulo` (evita divergência de hidratação RSC↔browser).
- **O reveal só existe dentro do modal** e nunca pré-mintido; reabrir a mesma vaga mostra o contato do cache de aba sem novo token.
- **Vagas expiradas nunca aparecem** — o filtro de `expires_at` já existe e vale para itens e `total`.
- **`wa.me` usa o E.164 cru**; sem canal de contato, o CTA correspondente não renderiza.
- **Doações é amarelo `#facc15`, discreto, efeito só no hover**, no topo à direita.

</specifics>

<deferred>
## Deferred Ideas

- **Aprovação/edição/exclusão de vagas no admin** (`pending → published`) — Phase 5 (REVW-01..05). É por isso que esta fase usa seed dev-only.
- **PIX real / página de doações completa** — Phase 6.
- **AdSense / anúncios reais**, banner de consentimento LGPD e política de privacidade — Phase 6.
- **Sitemap, JSON-LD `JobPosting`, OG images** — SEO avançado não requisitado; considerar depois que houver volume real de vagas.
- **Chaves reais do Cloudflare + env vars de deploy** (`NEXT_PUBLIC_TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`) — Phase 6.
- **Limiter distribuído (Redis/tabela)** — Phase 6, se o backend passar de 1 worker.
- **Página de vaga dedicada `/vagas/[id]`** — descartada nesta fase em favor do modal com deep-link; reavaliar se SEO por vaga se mostrar necessário.
- **`pg_trgm` tuning / busca fuzzy por similaridade** — complexidade antecipada; a substring normalizada resolve o volume atual.

</deferred>

---

*Phase: 04-public-board-frontend*
*Context gathered: 2026-10-22*
