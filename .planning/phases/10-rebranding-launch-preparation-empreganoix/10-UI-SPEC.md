---
phase: 10
slug: rebranding-launch-preparation-empreganoix
status: draft
shadcn_initialized: false
preset: none
design_system: tailwind-v4
created: 2026-11-14
inherits: .planning/phases/04-public-board-frontend/04-UI-SPEC.md
---

# Phase 10 — UI Design Contract (Rebranding & Launch Preparation — EmpregaNoix)

> Visual and interaction contract for the frontend surface touched by Phase 10.
> Inherited verbatim from `04-UI-SPEC.md` (design system, tokens, spacing,
> typography, color, interaction patterns). This document records the Phase 10
> *delta*: brand rename from "NaoQueroUsar"/"NQU" to "EmpregaNoix", new brand
> assets (logo, favicon, og:image), and launch configuration. No new tokens,
> no new components beyond static brand assets, no change to interaction
> patterns.

**Escopo da fase (UI):** (1) renomeação de conteúdo — wordmark, metadata,
toasts, WhatsApp template, páginas legais (controller + e-mail), área admin,
título da API; (2) geração/integração de assets de marca (logo completo,
favicon, og:image) com fallback de wordmark textual; (3) alinhamento de hosts
e CORS para `empreganoix.vercel.app` / `empreganoix.onrender.com`. Deploy real
e smoke gate são operacionais (sem UI nova), mas o contrato registra os
critérios visíveis (env=prod, Turnstile mode=live, CORS preflight 200).

**Fora do escopo (UI):** compra de domínio próprio, redirect de hosts antigos,
renomeação do diretório do repositório/`.planning`, revisão jurídica dos
textos legais (task humana, herdada do Phase 6).

**Relação com Phase 04/06/09:** tokens, tipografia, espaçamento, cores e regras
de acessibilidade são os mesmos. Nenhum token novo. Nenhuma dependência npm
nova. Nenhum componente novo além dos arquivos estáticos de marca.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | **Tailwind CSS v4** (`4.3.3`, CSS-first via `@import "tailwindcss"` + `@theme`) — herdado do Phase 04 |
| Preset | not applicable |
| Component library | **none** — nenhum shadcn/radix/base-ui |
| Icon library | **none** — SVGs inline em `frontend/components/board/icons.tsx` e `frontend/components/admin/icons.tsx` quando necessário |
| Font | System stack: `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` — herdado |
| Brand assets | **novos** nesta fase — ver §Brand Assets. Servidos como arquivos estáticos (Vercel `public/` ou file-based metadata em `app/`) |

### shadcn gate (executado 2026-11-14)

`components.json` **não existe** e o projeto é Next/React → gate acionado.
Resultado: **shadcn não inicializado** (mesmo veredito dos Phases 04/06/09).
Motivos: (1) não há canal interativo nesta execução para escolher preset;
(2) o Phase 10 não cria componentes novos — é rename + assets + deploy;
(3) todos os tokens visuais já estão travados e reutilizados. Override: rodar
o gate shadcn antes do plan-phase; nada neste contrato depende de shadcn.

### Onde os estilos entram (sem mudança)

- `frontend/app/(public)/public.css` — única fonte de tokens `@theme` (inalterado).
- `frontend/app/globals.css` — base `color-scheme`/body (inalterado).
- `frontend/app/admin/admin.css` — tokens do admin (inalterado).
- Páginas legais herdam o shell de `frontend/app/(public)/layout.tsx`.

---

## Spacing Scale

Mesma escala do Phase 04 (múltiplos de 4). Sem token novo.

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Gap ícone↔texto, padding inline de chip |
| sm | 8px | Gap entre chips, padding vertical de chip |
| md | 16px | Padding de card, gap entre linhas |
| lg | 24px | Padding lateral de página no mobile, gutter do grid |
| xl | 32px | Gap vertical entre toolbar e grid, padding do dialog no desktop |
| 2xl | 48px | Respiro entre blocos de página |
| 3xl | 64px | Altura do header, padding vertical do footer |

Exceptions (herdadas):
- **Touch targets:** mínimo **44×44px** para todo elemento interativo.
- **Input de busca:** altura **48px**.
- **CTA do reveal no dialog:** altura **48px**.
- **Turnstile:** iframe ~**300×65px** — reservar `min-width: 300px; max-width: 100%`, nunca `transform`/`scale`.
- **Slots de ADS:** alturas fixas de mídia (90px / 250px).
- **Container:** `max-width: 1120px`, gutter 24px (mobile 16px), sidebar de ADS 300px fixos.

---

## Typography

Herdado do Phase 04. Sem alterações.

| Role | Size | Weight | Line Height | Uso no rebrand |
|------|------|--------|-------------|----------------|
| Body | 16px | 400 | 1.5 | Texto corrido, descrições, corpo legal |
| Label | 14px | 400 | 1.4 | Metadados, chips, paginação, rótulos de slot de ADS |
| Heading | 20px | 600 | 1.2 | Título de card, título do dialog, **wordmark "EmpregaNoix"** |
| Display | 28px | 600 | 1.2 | `<h1>` único da página, título de página legal |

Rules (herdadas):
- Exatamente **2 pesos**: 400 e 600. Proibido 700/300.
- Menor tamanho permitido: **14px**.
- Wordmark: Heading/20/600, cor `--color-fg` (`#e2e8f0`), com ponto final `.` em `--color-accent-soft` (`#a78bfa`), conforme padrão existente.
- Nenhuma fonte customizada, nenhum `letter-spacing` negativo.

---

## Color

Herdado do Phase 04. Nenhum token novo. A marca visual permanece idêntica
(BRND-03).

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#0f0a1a` (`--color-canvas`) | Fundo da página, header/footer, input de busca |
| Secondary (30%) | `#1a1025` (`--color-surface`) | Cards, dialog, slots de ADS |
| Accent (10%) | `#8b5cf6` (bordas/indicador) · `#a78bfa` (texto) · `#7c3aed` (preenchimento) | Lista fechada do Phase 04 §Color |
| Yellow | `#facc15` (`--color-donate`) | **Somente** o botão "Doações" (discreto, efeito apenas no hover) |
| Destructive | `#f87171` / `#fecaca` | Apenas borda/texto de painel de erro |

**Accent reservado para (lista fechada — herdada do Phase 04):**
1. CTA preenchido "Mostrar contato" no footer do dialog (`#7c3aed`, texto branco).
2. Chip de cidade selecionado (`#7c3aed`, texto branco, `aria-pressed="true"`).
3. Valores de contato revelados e links de texto ("Ver mais", "Limpar filtros", página ativa) em `#a78bfa`.
4. Focus ring: `2px solid #a78bfa`, `outline-offset: 2px`.
5. Borda `#8b5cf6` apenas em hover/focus de botão secundário, card e input.
6. Indicador de verificação do Turnstile.

**Regra dura herdada:** `#8b5cf6` **nunca** carrega texto branco (4.23:1, reprova
AA). Preenchimento com texto = `#7c3aed` (5.70:1) ou `#6d28d9`.

**Contraste (herdado, WCAG 2.1):** todos os pares do Phase 04 §Color permanecem
válidos — nenhum token muda nesta fase.

---

## Copywriting Contract

Todo copy em **pt-BR**. Erros do backend são renderizados **verbatim**
(`body.detail`). O rename afeta apenas as strings de marca; o slogan é mantido
verbatim (BRND-02, D-02).

### Brand wordmark & metadata

| Elemento | Antes | Depois (Phase 10) |
|----------|-------|-------------------|
| `<title>` (público) | `NaoQueroUsar — Vagas sem cadastro` | **`EmpregaNoix — Vagas sem cadastro`** |
| `description` (público) | (inalterado) | `Encontre vagas e o contato para se candidatar em segundos. Sem conta, sem login e sem burocracia.` |
| `og:title` | `NaoQueroUsar — Vagas sem cadastro` | **`EmpregaNoix — Vagas sem cadastro`** |
| `og:description` | (inalterado) | igual à `description` |
| `og:image` | (inexistente) | **novo asset** — ver §Brand Assets (`opengraph-image.png`, 1200×630, alt `EmpregaNoix — Vagas sem cadastro`) |
| `og:url` | (host antigo) | `https://empreganoix.vercel.app` |
| `metadataBase` | (host antigo) | `https://empreganoix.vercel.app` |
| Wordmark (header) | `NaoQueroUsar` + `.` | **`EmpregaNoix`** + `.` (accent-soft) |
| Slogan (header/footer) | `Procurar um emprego, não deve dar trabalho` | **inalterado** (BRND-02) |
| Footer copyright | `© 2026 NaoQueroUsar` | **`© 2026 EmpregaNoix`** |
| Skip link | `Ir para as vagas` | inalterado |
| `theme-color` | `#0f0a1a` | inalterado |

### Área admin

| Elemento | Antes | Depois |
|----------|-------|--------|
| `title` (metadata) | `NaoQueroUsar - Painel admin` | **`EmpregaNoix - Painel admin`** |
| `description` | `Painel de administração - curadoria de vagas` | inalterado |
| Wordmark (header) | `NaoQueroUsar` + `.` | **`EmpregaNoix`** + `.` (accent-soft) |
| Slogan (header) | `Procurar um emprego, não deve dar trabalho` | inalterado |

### Página Doações

| Elemento | Antes | Depois |
|----------|-------|--------|
| `title` | `Doações — NaoQueroUsar` | **`Doações — EmpregaNoix`** |
| `<h1>` | `Doações` | inalterado |
| Corpo | `Em breve você poderá apoiar o NaoQueroUsar por PIX. …` | **`Em breve você poderá apoiar o EmpregaNoix por PIX. Enquanto isso, compartilhe as vagas com quem está procurando emprego.`** |
| CTA voltar | `Voltar para as vagas` | inalterado |

### WhatsApp template (contacts.ts)

| Elemento | Antes | Depois |
|----------|-------|--------|
| Mensagem pré-preenchida | `Olá! Vi a vaga "{title}" no NaoQueroUsar e quero me candidatar.` | **`Olá! Vi a vaga "{title}" no EmpregaNoix e quero me candidatar.`** |
| Assunto do e-mail | `Candidatura: {title}` | inalterado |

### Páginas legais (`/privacidade`, `/termos-de-uso`)

| Elemento | Antes | Depois |
|----------|-------|--------|
| `title` (privacidade) | `Política de Privacidade — NaoQueroUsar` | **`Política de Privacidade — EmpregaNoix`** |
| `title` (termos) | `Termos de Uso — NaoQueroUsar` | **`Termos de Uso — EmpregaNoix`** |
| `description` (privacidade) | `… plataforma NQU — NaoQueroUsar. …` | **`Política de privacidade da plataforma EmpregaNoix. Como coletamos, usamos e protegemos seus dados.`** |
| `description` (termos) | `… plataforma NQU — NaoQueroUsar. …` | **`Termos de uso da plataforma EmpregaNoix. Regras para uso do site e da plataforma de vagas.`** |
| Badge wordmark (legal) | `NQU` (text-2xl font-bold) | **`EmpregaNoix`** (text-2xl font-bold) — ou logo gráfico (ver §Brand Assets) |
| Controller/razão social no texto | `NQU` / `NaoQueroUsar` | **`EmpregaNoix`** em todas as ocorrências (13 seções privacidade, 10 seções termos) |
| Canal de contato/privacidade | `suportenqs@outlook.com` | **`empreganoix@outlook.com`** (em todas as ocorrências: legal pages, metadata, docs) |
| Aviso LGPD/intermediário | `somos apenas meio de divulgação` | inalterado (texto preservado, apenas marca trocada) |
| Link do footer | `Privacidade` · `Termos de Uso` | inalterado |

**Regra herdada (Phase 09):** preservar 100% das palavras do texto legal atual;
mudanças são apenas de marcação semântica (h1/h2, classes) e de strings de
marca (NQU/NaoQueroUsar → EmpregaNoix, e-mail). Não reescrever conteúdo legal.

### Backend (consistência de marca)

| Elemento | Antes | Depois |
|----------|-------|--------|
| `FastAPI(title=…)` (`backend/app/main.py`) | `NQU API` | **`EmpregaNoix API`** |
| `pyproject.toml` description | `NQU backend` | **`EmpregaNoix backend`** |
| `pyproject.toml` name | `nqu-backend` | **`empreganoix-backend`** (ou manter nome do pacote se já publicado — discrição do planner; preferir manter `nqu-backend` se houver lock/CI dependendo dele) |
| `README.md` (raiz) | `# NQU — NaoQueroUsar` | **`# EmpregaNoix`** |
| `backend/README.md` | `NQU Backend` | **`EmpregaNoix Backend`** |
| `alembic.ini` / migration 0001 comentário | `NQU` | **`EmpregaNoix`** |
| `scripts/seed.py` company | `NQU Seed` | **`EmpregaNoix Seed`** |
| `AGENTS.md` título | `NQU — NaoQueroUsar` | **`EmpregaNoix`** |
| `frontend/.env.example` comentário | `NQU` | **`EmpregaNoix`** |

### Toasts / mensagens admin

Nenhuma mensagem de toast referencia a marca hoje (verificado por grep). Se alguma
string contiver "NaoQueroUsar"/"NQU" em `frontend/components/admin/ToastProvider.tsx`
ou nas páginas admin, trocar por "EmpregaNoix". Contrato: toasts permanecem
curtos, em pt-BR, sem dependência de biblioteca externa (D-E2E-06).

### Strings que NÃO mudam

- Slogan `Procurar um emprego, não deve dar trabalho` (BRND-02).
- Nomes de cidade (`São Paulo`, `Rio de Janeiro`, `Belo Horizonte`, `Remoto`).
- CTAs (`Ver a vaga`, `Mostrar contato`, `Doações`, `Enviar e-mail`, `WhatsApp`).
- Mensagens de erro do backend (verbatim, pt-BR, sem referência de marca).
- `theme-color` `#0f0a1a`, tokens `@theme`.

---

## Brand Assets (novo nesta fase — D-05)

Identidade visual: roxo `#8b5cf6`/`#a78bfa` sobre fundo `#0f0a1a`/`#1a1025`,
botão Doações amarelo `#facc15`. Logo completo novo (wordmark + marca gráfica
opcional) além do wordmark textual. OpenCode gera os assets (image generation)
e integra via file-based metadata ou `metadata.icons`/`openGraph.images`.

### Arquivos de marca (contrato de localização e dimensão)

| Arquivo | Local | Dimensão | Uso | Obrigatório? |
|---------|-------|----------|-----|--------------|
| `icon.png` (ou `favicon.ico`) | `frontend/app/icon.png` (file-based metadata) | fonte 512×512 (Next gera 16/32/48/192) | `<link rel="icon">` em todas as rotas | **sim** (fallback: manter favicon padrão do Next até o asset chegar) |
| `apple-icon.png` | `frontend/app/apple-icon.png` | 180×180 | `<link rel="apple-touch-icon">` | sim (pode reusar `icon.png` redimensionado) |
| `opengraph-image.png` | `frontend/app/opengraph-image.png` (ou em `(public)/`) | 1200×630 | `<meta property="og:image">` para compartilhamento | sim |
| Logo gráfico (horizontal) | `frontend/public/logo.svg` (ou `.png`) | altura 24px (h-6) no header; 32px no footer/legal | substituir o wordmark textual se aprovado | **não** — D-05 permite fallback wordmark textual |
| Logo mark (ícone) | `frontend/public/logo-mark.svg` | 32×32 | favicon alternativo / PWA | não (opcional) |

### Regras de uso dos assets

1. **Fallback obrigatório:** se o logo gráfico atrasar, o wordmark textual
   `EmpregaNoix` (Heading/20/600, fg, ponto `.` accent-soft) permanece no header
   e no footer. O deploy **não bloqueia** por ausência de logo gráfico (D-05).
2. **Acessibilidade:** logo gráfico no header é `<img alt="EmpregaNoix">` (ou
   SVG com `role="img"` + `<title>EmpregaNoix</title>`). Nunca `<img alt="">`
   para o logo principal.
3. **Altura fixa:** logo gráfico no header = `h-6` (24px), no footer/legal =
   `h-8` (32px). Nunca escalar acima de 40px em nenhum contexto.
4. **Sem fundo branco:** logo sobre `#0f0a1a` (canvas) ou `#1a1025` (surface).
   Variante "on light" não é necessária nesta fase (dark mode only).
5. **og:image:** 1200×630, fundo `#0f0a1a`, wordmark `EmpregaNoix` em
   `#a78bfa` (Heading/Display), slogan em `#b8a9cc` (Label), botão Doações
   `#facc15` opcional como detalhe. Texto legível em thumbnail (mín. 48px).
6. **Favicon:** preferir PNG (Next gera os tamanhos); `favicon.ico` 32×32
   opcional para retrocompatibilidade com browsers antigos.
7. **Sem alteração de layout:** a introdução dos assets não muda alturas do
   header (h-16/64px) nem do footer. O logo gráfico substitui o texto no mesmo
   espaço (`h-6`, `max-w-[160px]`).
8. **Metadata por rota:** `app/(public)/layout.tsx` e `app/admin/layout.tsx`
   mantêm `export const metadata` com `title`/`description` atualizados; os
   assets file-based (`app/icon.png`, `app/opengraph-image.png`) aplicam-se a
   todas as rotas automaticamente. Se for desejado og:image diferente por rota,
   usar `export const metadata.openGraph.images` naquele `page.tsx`.

### Fallback de wordmark textual (se assets não prontos no deploy)

Se `icon.png`/`opengraph-image.png` não existirem no momento do deploy, o
contrato exige:
- Manter o wordmark textual `EmpregaNoix` no header/footer (já é o default).
- Aceitar o favicon padrão do Next (globo) temporariamente — não bloqueia
  BRND-04, mas registrar como débito visual para fechar antes do go-live
  público.
- `og:image` ausente → compartilhamento em redes sociais mostra apenas título +
  descrição (sem imagem). Aceitável para launch inicial; fechar com asset
  depois.

---

## Launch Configuration (BRND-04 — operacional, sem UI nova)

Contrato de configuração que afeta a UI (hosts, CORS, Turnstile). Sem mudança
de código de componente; apenas env/config.

| Item | Valor | Onde | Efeito na UI |
|------|-------|------|--------------|
| Frontend host | `https://empreganoix.vercel.app` | Vercel project + `metadataBase`/`og:url` | URL canônica, compartilhamento |
| Backend host | `https://empreganoix.onrender.com` | Render service + `NEXT_PUBLIC_API_URL`/`BACKEND_API_URL` | fetch de vagas/reveal/login |
| `ALLOWED_ORIGINS`/`CORS_ORIGINS` | `https://empreganoix.vercel.app` (exato, sem trailing slash) | Render env (fail-closed, T-09-13) | CORS preflight 200 com `Access-Control-Allow-Origin` |
| `ENV` | `prod` | Render env | `health.env === "prod"`, Turnstile modo live |
| `NEXT_PUBLIC_API_URL` | `https://empreganoix.onrender.com` | Vercel env (inlined no build) | bundle cliente aponta para backend novo |
| `BACKEND_API_URL` | `https://empreganoix.onrender.com` | Vercel env (SSR) | RSC fetch no servidor |
| Turnstile Hostnames | adicionar `empreganoix.vercel.app` | Cloudflare dashboard (widget de produção) | widget aceita o domínio |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | chave live | Vercel env (inlined no build) | widget live (não teste) |
| `TURNSTILE_SECRET_KEY` | segredo live | Render env | `health.turnstile.mode === "live"` |
| `CRON_SECRET` | valor existente (43 chars, não commitado) | Render env + GitHub Actions secret | `/admin/expire` idempotente |
| GitHub Actions `vars.API_BASE_URL` | `https://empreganoix.onrender.com` | GitHub repo vars | cron catch-up |
| Vercel `NEXT_PUBLIC_*` | — | rebuild obrigatório após troca | Pitfall 1 (T-03-18) |

**Critérios de aceite visíveis (smoke gate — `scripts/verify-deploy.ps1`):**
- `GET /health` → 200, `env=prod`, `turnstile.mode=live`.
- CORS preflight de `https://empreganoix.vercel.app` → 200 com `Access-Control-Allow-Origin: https://empreganoix.vercel.app`.
- Board (`/`) renderiza vagas via SSR com host novo no bundle.
- `/privacidade` e `/termos-de-uso` acessíveis, com marca EmpregaNoix e e-mail `empreganoix@outlook.com`.
- `POST /admin/expire` sem header → 401; com `X-Cron-Secret` correto → 200 idempotente.
- Nenhum "NaoQueroUsar"/"NQU"/"suportenqs" em `frontend/` (grep vazio).

**Hosts antigos não mantidos (D-03):** `nao-quero-usar.vercel.app` /
`naoquerousar.onrender.com` não recebem redirect. Acesso a eles cai no default
da plataforma (aceitável — sem usuários externos ainda).

---

## Interaction Contract

Nenhuma interação nova. Todas as interações (board, dialog, reveal, admin,
report, legal) permanecem idênticas ao Phase 04/06/09. O rename é puramente
de strings; a troca de marca não altera fluxos, estados ou atalhos.

Deltas menores de copy em interações:
- `messageFor(title)` (WhatsApp) passa a usar "EmpregaNoix" (ver §Copywriting).
- Toasts admin: se referenciarem a marca, usar "EmpregaNoix".
- Empty state do board e doações: inalterados (sem referência de marca hoje,
  exceto doações body — atualizado).

---

## Component Inventory

| # | Arquivo | Tipo | Status | Notas |
|---|---------|------|--------|-------|
| 1 | `frontend/app/icon.png` (ou `favicon.ico`) | asset | **novo** | favicon via file-based metadata |
| 2 | `frontend/app/apple-icon.png` | asset | **novo** | 180×180 |
| 3 | `frontend/app/opengraph-image.png` | asset | **novo** | 1200×630, og:image |
| 4 | `frontend/public/logo.svg` (opcional) | asset | **novo** | logo gráfico; fallback wordmark textual |
| 5 | `frontend/app/(public)/layout.tsx` | RSC | **modificar** | title, wordmark, copyright, metadataBase, og:url, og:image |
| 6 | `frontend/app/(public)/page.tsx` | RSC | **verificar** | headings/empty states sem marca hoje |
| 7 | `frontend/app/(public)/doacoes/page.tsx` | RSC | **modificar** | title, body |
| 8 | `frontend/app/(public)/privacidade/page.tsx` | RSC | **modificar** | title, description, badge wordmark, controller, e-mail |
| 9 | `frontend/app/(public)/termos-de-uso/page.tsx` | RSC | **modificar** | title, description, badge wordmark, controller, e-mail |
| 10 | `frontend/app/admin/layout.tsx` | RSC | **modificar** | title, wordmark |
| 11 | `frontend/lib/contacts.ts` | TS | **modificar** | WhatsApp template |
| 12 | `frontend/.env.example` | config | **modificar** | comentário |
| 13 | `backend/app/main.py` | Python | **modificar** | `FastAPI(title="EmpregaNoix API")` |
| 14 | `backend/pyproject.toml` | config | **modificar** | description (name a discricionar) |
| 15 | `backend/alembic.ini` | config | **modificar** | comentário |
| 16 | `backend/alembic/versions/0001_initial_jobs.py` | Python | **modificar** | comentário (migration forward-only — apenas comentário, não schema) |
| 17 | `backend/scripts/seed.py` | Python | **modificar** | company |
| 18 | `backend/README.md` | docs | **modificar** | título |
| 19 | `README.md` (raiz) | docs | **modificar** | título |
| 20 | `AGENTS.md` | docs | **modificar** | título (bloco GSD project) |
| 21 | `docs/DEPLOY.md` | docs | **modificar** | título e exemplos de host |
| 22 | `render.yaml` | config | **modificar** | comentário |
| 23 | `scripts/verify-deploy.ps1` | script | **modificar** | comentário |
| 24 | `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` | docs | **modificar** (conteúdo apenas; diretório mantido) |

**Notas:** nenhum componente React novo; nenhum componente modificado além de
strings/metadata. Migrations não são editadas no schema (apenas comentário).

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not required (shadcn não inicializado — ver §Design System) |
| third-party registries | none | not required |

Nenhum bloco de registry utilizado. `next-turnstile@1.0.7` é dependência npm
já vetada nos Phases 03/04 (sem dependências de runtime). Nenhum gate de
`shadcn view` acionado.

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending

---

*Sources: `10-CONTEXT.md` (D-01..D-06, escopo, canonical refs), `10-RESEARCH.md`
(rename inventory, pitfalls, validation architecture), `04-UI-SPEC.md` (design
system/tokens herdados), `09-UI-SPEC.md` (delta pattern para páginas legais),
`06-UI-SPEC.md` (legal copy baseline), codebase scout (grep de "NaoQueroUsar"/
"NQU"/"suportenqs" em frontend e backend), `.planning/research/STACK.md`
(Next 16.4.6, Tailwind 4.3.3, FastAPI 0.143). Nenhum CONTEXT.md adicional
além do Phase 10.*