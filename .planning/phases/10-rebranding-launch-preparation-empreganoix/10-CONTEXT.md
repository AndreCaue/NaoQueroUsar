# Phase 10: Rebranding & Launch Preparation (EmpregaNoix) - Context

**Gathered:** 2026-11-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Renomear a aplicação de "NaoQueroUsar"/"NQU" para "EmpregaNoix" em todo o frontend e infraestrutura, garantindo consistência de marca e configurações de deploy, e executar o deploy real (Vercel + Render) com smoke gate verde. A marca visual passa a ser "EmpregaNoix", com logo completo novo, favicon e og:image; o slogan "Procurar um emprego, não deve dar trabalho" é mantido. Hosts passam para `empreganoix.vercel.app` / `empreganoix.onrender.com`.

**Entregue nesta fase (BRND-01..04):**
- Textos, labels, headings, meta tags, toasts, WhatsApp template, legal pages, backend API title, docs, README, pyproject description, seed company e email atualizados para "EmpregaNoix".
- Hosts atualizados (frontend `https://empreganoix.vercel.app`, backend `https://empreganoix.onrender.com`); CORS/`ALLOWED_ORIGINS`/`NEXT_PUBLIC_API_URL`/`BACKEND_API_URL` travados nas novas origens.
- Deploy Vercel + Render executado com `ENV=prod`, Turnstile live, `CRON_SECRET` configurado; smoke gate verde (health 200, env=prod, Turnstile mode=live, CORS preflight 200 com `Access-Control-Allow-Origin`).
- Logo completo novo + favicon + og:image para EmpregaNoix.

**Fora desta fase:** compra/configuração de domínio próprio (fica em tier gratuito Vercel/Render por ora); manutenção de hosts antigos como redirect (não mantidos); renomeação do diretório do repositório/`.planning` (permanecem "NaoQueroUsar").
</domain>

<decisions>
## Implementation Decisions

### Escopo do rename
- **D-01:** Renomeação completa do **conteúdo** (textos, labels, headings, meta tags, toasts, template WhatsApp, páginas legais, título da API FastAPI, docs, README, descrição do pyproject, seed company, email) de "NaoQueroUsar"/"NQU" para "EmpregaNoix". O **diretório do repositório** e `.planning/` permanecem "NaoQueroUsar" — não renomear a pasta (evita quebrar paths absolutos em scripts/docs, histórico git e a sessão OpenCode). Somente o conteúdo dos arquivos é alterado.
- **D-02:** Slogan mantido verbatim: "Procurar um emprego, não deve dar trabalho" (BRND-02).

### Hosts e domínios
- **D-03:** Novos hosts oficiais: frontend `https://empreganoix.vercel.app`, backend `https://empreganoix.onrender.com`. Hosts antigos (`nao-quero-usar.vercel.app` / `naoquerousar.onrender.com`) **não** são mantidos como redirect — lançamento ocorre apenas sob a nova marca (BRND-04). Atualizar `CORS_ORIGINS`/`ALLOWED_ORIGINS`, `NEXT_PUBLIC_API_URL`/`BACKEND_API_URL` e Turnstile Hostnames para as novas origens.

### Deploy real
- **D-04:** Executar **deploy real** Vercel + Render agora, configurando `ENV=prod`, CORS travado às origens EmpregaNoix, chaves Turnstile de produção (live) e `CRON_SECRET` em ambos os hosts; rodar o smoke gate (`verify-deploy.ps1`) até verde (health 200, env=prod, Turnstile mode=live, CORS preflight 200 com `Access-Control-Allow-Origin`, cron idempotente). Isso fecha BRND-04 e o deploy pendente do Phase 6 (decisão anterior de manter em dev local é revogada para o lançamento).

### Assets de marca
- **D-05:** Criar **logo completo novo** para EmpregaNoix (identidade visual completa), incluindo **favicon** e **og:image** para compartilhamento, além do wordmark textual. OpenCode gera os assets (image generation) e os integra no frontend (metadata `icons`, `openGraph.images`). Se o logo atrasar, o wordmark textual "EmpregaNoix" serve como fallback sem bloquear o deploy (OpenCode decide).

### Textos legais e canal de contato
- **D-06:** Atualizar referências "NQU"/"NaoQueroUsar" em `/privacidade` e `/termos-de-uso` para "EmpregaNoix" (controller/razão exibida nos textos legais). Canal de contato/privacidade passa de `suportenqs@outlook.com` para `empreganoix@outlook.com` em todos os lugares (legal pages, metadata, docs). WhatsApp template (`frontend/lib/contacts.ts`) passa a "Vi a vaga ... no EmpregaNoix".

### OpenCode's Discretion
- Ferramenta/fluxo exato para gerar os assets de marca (favicon, og:image, logo) — image generation ou SVG manual.
- Ordem de execução das substituições (frontend primeiro, depois backend/docs/infra).
- Fallback de wordmark textual se assets não estiverem prontos no momento do deploy (não bloquear BRND-04).
- Se o logo completo atrasar, manter wordmark textual como fallback sem bloquear deploy.

### Folded Todos
Nenhum todo pendente para esta fase (`todo.match-phase 10` retornou vazio).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos
- `.planning/ROADMAP.md` — Phase 10: goal, dependências (Phases 3–9), 5 critérios de sucesso, BRND-01..04, `UI hint: yes`.
- `.planning/REQUIREMENTS.md` — BRND-01..04 (linhas 67–72); tabela de rastreabilidade.
- `.planning/PROJECT.md` — constraints travadas: dark minimalista, pt-BR, admin único, mobile-first, cores #8b5cf6/#a78bfa/#facc15, fundos #0f0a1a/#1a1025.
- `.planning/STATE.md` — posição atual: milestone v1.1 EmpregaNoix, Phases 7–8 completas, Phase 9 em execução.

### Deploy e infraestrutura (herdados)
- `docs/DEPLOY.md` — runbook de deploy Vercel + Render, smoke gate `verify-deploy.ps1`, Turnstile hostnames, CORS, cold-start.
- `render.yaml` — blueprint Render (autoDeploy, env vars, health check).
- `frontend/vercel.json` — config Vercel.
- `.planning/phases/06-lifecycle-trust-legal-launch/06-CONTEXT.md` — D-01..D-07 (APScheduler, CRON_SECRET, legal pages, deploy).
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-03-SUMMARY.md` — CORS fail-closed, hardening Render, smoke gate com aviso exato.

### Superfícies de texto a renomear (inventário)
- `frontend/app/(public)/layout.tsx` — metadata title/description, wordmark header/footer.
- `frontend/app/(public)/page.tsx` — headings, empty states.
- `frontend/app/(public)/privacidade/page.tsx` — title/description e texto legal (NQU → EmpregaNoix, email).
- `frontend/app/(public)/termos-de-uso/page.tsx` — title/description e texto legal (NQU → EmpregaNoix).
- `frontend/app/(public)/doacoes/page.tsx` — título/corpo com "NaoQueroUsar".
- `frontend/app/admin/layout.tsx` — metadata "NaoQueroUsar — Painel admin", wordmark header.
- `frontend/lib/contacts.ts` — template WhatsApp "no NaoQueroUsar".
- `frontend/app/layout.tsx` — (sem nome de marca, mas metadata default).
- `backend/app/main.py` — `FastAPI(title="NQU API", ...)` → "EmpregaNoix API".
- `backend/README.md`, `backend/pyproject.toml` — description "NQU backend".
- `backend/scripts/seed.py` — `company="NQU Seed"` → "EmpregaNoix Seed".
- `README.md` (raiz) — "# NQU — NaoQueroUsar".
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` — títulos "NQU — NaoQueroUsar" (atualizar para EmpregaNoix no conteúdo; diretório mantido).

### Decisões herdadas (não reabrir)
- `.planning/phases/01-backend-foundation-data-admin-auth/01-CONTEXT.md` — D-01 (Bearer JWT), D-05 (env obrigatório, falha rápido), D-06 (sem soft delete), D-14 (paginação), D-17 (filtro published AND expires_at > now()), D-18 (contato nunca no payload público).
- `.planning/phases/04-public-board-frontend/04-CONTEXT.md` — D-03..D-06 (busca/filtro/ordenação/paginação), D-07 (Server Component), D-09 (modal + URL state), D-10 (reveal no clique), D-12 (tokens de tema), D-13 (contraste AA).
- `.planning/phases/08-admin-review-area-completeness/08-CONTEXT.md` — D-E2E-01..D-E2E-10 (fluxo colar→extrair→revisar→aprovar, toasts, proteção admin).

### Pesquisa
- `.planning/research/STACK.md` — versões fixadas (Next 16.4.6, Tailwind 4.3.3, FastAPI 0.143).
- `.planning/research/PITFALLS.md` — Pitfall 7 (contato oculto ≠ protegido).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/app/(public)/public.css` — tokens Tailwind v4 (`--color-primary-500: #8b5cf6`, `--color-primary-400: #a78bfa`, `--bg-dark-900: #0f0a1a`, `--bg-dark-800: #1a1025`, `--color-accent-yellow: #facc15`) — mantidos (BRND-03).
- `frontend/lib/contacts.ts` — `wa.me`/`mailto` builder com template de mensagem; único ponto de atualização do texto WhatsApp.
- `frontend/app/admin/layout.tsx` — metadata + wordmark admin; padrão a replicar.
- `backend/app/main.py` — `create_app()` com `FastAPI(title=...)`; único ponto do título da API.

### Established Patterns
- **Metadata por rota** via `export const metadata` em `page.tsx`/`layout.tsx` (Next 16 App Router) — atualizar title/description/og em cada rota.
- **Erros pt-BR no `detail`**, renderizados verbatim pelo front.
- **Chaves obrigatórias no startup** via `Settings` (pydantic-settings); novos hosts/origens entram em `CORS_ORIGINS`/`ALLOWED_ORIGINS`.
- **Testes** rodam a partir de `backend/` (`cd backend; .venv\Scripts\python.exe -m pytest -q`).

### Integration Points
- `frontend/app/(public)/layout.tsx` + `admin/layout.tsx` — wordmark e metadata.
- `frontend/lib/contacts.ts` — template WhatsApp.
- `backend/app/main.py` — título da API.
- `render.yaml` / `frontend/vercel.json` / `docs/DEPLOY.md` — hosts, env vars, smoke gate.
- Cloudflare Turnstile — Hostnames list (novas origens).

</code_context>

<specifics>
## Specific Ideas

- **Lançamento sob nova marca apenas** — sem redirect dos hosts antigos; quem acessar hosts antigos cai no 404/default da Vercel/Render (aceitável, sem usuários externos ainda).
- **Logo completo novo** — gerar assets de marca (logo, favicon, og:image) com identidade EmpregaNoix (roxo #8b5cf6/#a78bfa sobre fundo #0f0a1a), mantendo o botão Doações amarelo #facc15.
- **Email de contato** `empreganoix@outlook.com` substitui `suportenqs@outlook.com` em legal pages e metadata.
- **Deploy real fecha Phase 6** — `ENV=prod`, Turnstile live, `CRON_SECRET` configurado; smoke gate verde é o critério de aceite.
- **Diretório do repo permanece "NaoQueroUsar"** — apenas conteúdo renomeado.

</specifics>

<deferred>
## Deferred Ideas

- **Domínio próprio** (ex.: `empreganoix.com.br`) — fora desta fase; mantém tier gratuito Vercel/Render (`*.vercel.app`/`*.onrender.com`). Considerar quando houver orçamento/validação de marca.
- **Redirect dos hosts antigos** — não mantidos; se no futuro houver tráfego nos hosts antigos, adicionar redirect 301.
- **Renomeação do diretório do repositório/`.planning`** — não feita (risco de paths); pode ser feita manualmente depois se desejado.
- **Revisão jurídica dos textos legais** — fora de escopo de código (task humana), assim como no Phase 6.

### Reviewed Todos (not folded)
Nenhum todo pendente para esta fase (verificação contra `todo.match-phase 10` retornou vazio).

</deferred>

---

*Phase: 10-rebranding-launch-preparation-empreganoix*
*Context gathered: 2026-11-14*