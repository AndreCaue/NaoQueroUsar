---
phase: 5
slug: admin-review-area
status: draft
shadcn_initialized: false
preset: none
design_system: tailwind-v4
created: 2026-10-27
---

# Phase 05 — UI Design Contract

> Contrato visual e de interação da área de revisão admin (`/admin`, `/admin/paste`, `/admin/review`). Gerado por gsd-ui-researcher, verificado por gsd-ui-checker.

**Escopo da fase:** hub admin, migração do painel admin para Tailwind v4 (paste + fila), fila de revisão de vagas `pending` (aba separada para `needs_review`), aprovar/editar (modal com todos os campos)/excluir (hard delete com confirmação), texto-fonte ao lado dos campos (grounding), toast próprio + atualização otimista, guard client-side. **Não inclui:** aprovação em lote, reversão published→pending, soft delete, busca por texto livre, middleware server-side, biblioteca de toast, badge/report/páginas legais (Phase 6), ciclo de vida/expiração (Phase 6), deploy/env de produção (Phase 6).

**Relação com o Phase 04:** este contrato **reutiliza integralmente** os tokens de `04-UI-SPEC.md` (`--color-canvas`, `--color-surface`, `--color-line`, `--color-line-strong`, `--color-fg`, `--color-fg-muted`, `--color-accent`, `--color-accent-soft`, `--color-accent-strong`, `--color-accent-strong-hover`, `--color-donate`, `--color-danger`, `--color-danger-soft`, escala de 4px, 2 pesos, 4 tamanhos, focus ring `#a78bfa`). A mudança deliberada é: (a) o **painel admin deixa de ser CSS plano** (`globals-admin.css`) e **adota Tailwind v4** em um `admin.css` route-scoped (D-12), com os mesmos tokens do público; (b) acento preenchido usa `#7c3aed` (nunca `#8b5cf6` com texto branco — reprova AA). O admin continua **sem shadcn** e **sem component library**.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | **Tailwind CSS v4** (`4.3.3`, CSS-first via `@import "tailwindcss"` + `@theme`) — adotado no painel admin nesta fase (D-12), adiado no Phase 04 |
| Preset | not applicable |
| Component library | **none** — nenhum shadcn/radix/base-ui |
| Icon library | **none** — SVGs inline (20px no corpo, 16px inline, `stroke-width: 1.75`, `currentColor`), reutilizando `frontend/components/board/icons.tsx` e adicionando ícones admin (`check`, `pencil`, `trash`, `logout`, `plus`, `x`, `chevron-down`) no mesmo estilo |
| Font | System stack: `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` (nenhum webfont — zero request extra, zero FOUT) |

### shadcn gate (executado 2026-10-27)

`components.json` **não existe** e o projeto é Next/React → o gate foi acionado. Resultado: **shadcn não inicializado**. Motivos: (1) não há canal interativo nesta execução para escolher um preset; (2) a superfície do Phase 05 é a fila de revisão + modal de edição — um sistema de componentes seria overhead contra o "board enxuto"; (3) todos os tokens visuais já estão travados e são reutilizados do Phase 04. **Ponto de override:** se o usuário quiser shadcn, ele precisa escolher o preset e rodar `npx shadcn init --preset …` antes do plan-phase; nada neste contrato depende de shadcn.

### Onde o Tailwind entra (e onde não entra)

- `frontend/app/admin/admin.css` → **novo** (D-12): `@import "tailwindcss";` + bloco `@theme` (cópia verbatim dos tokens de `public.css`) + base do admin. Importado **somente** por `app/admin/layout.tsx`, então o Preflight **não** alcança a rota pública (`/`) nem vice-versa.
- `frontend/app/(public)/public.css` → **intocado** (Phase 04).
- `frontend/app/globals.css` → permanece mínimo (`:root { color-scheme: dark; }`, `body` background/color), importado pelo root layout.
- `frontend/app/admin/paste/globals-admin.css` → **removido** após a migração (D-12); `ExtractForm.tsx` passa a usar classes Tailwind.

```css
/* app/admin/admin.css */
@import "tailwindcss";

@theme {
  --color-canvas: #0f0a1a;      /* 60% — fundo da página */
  --color-surface: #1a1025;     /* 30% — cards, dialog, modal, toast */
  --color-line: #2a1f3d;        /* borda decorativa de card/dialog */
  --color-line-strong: #6d5a91; /* borda de CONTROLE (input, botão secundário, chip, tab) — 3.26:1 */
  --color-fg: #e2e8f0;
  --color-fg-muted: #b8a9cc;
  --color-accent: #8b5cf6;      /* marca: bordas/hover/indicador */
  --color-accent-soft: #a78bfa; /* TEXTO de acento + focus ring */
  --color-accent-strong: #7c3aed;       /* preenchimento de CTA (branco 5.70:1) */
  --color-accent-strong-hover: #6d28d9;
  --color-donate: #facc15;      /* reservado ao botão "Doações" do shell público — não usado no admin */
  --color-danger: #f87171;
  --color-danger-soft: #fecaca;
  --radius-card: 12px;
  --radius-dialog: 16px;
}
```

> **Regra dura (herdada):** `#8b5cf6` **nunca** carrega texto (branco sobre ele = 4.23:1, reprova AA). Preenchimento com texto = `#7c3aed` (5.70:1) ou `#6d28d9`. Acento no admin é **mais restrito** que no público: o único botão preenchido de acento da fila é **"Aprovar"**.

---

## Spacing Scale

Mesma escala do Phase 04 (múltiplos de 4). Sem token novo.

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Gap ícone↔texto, padding inline de chip/tab, gap entre meta itens |
| sm | 8px | Gap entre chips/tabs, padding vertical de chip, gap título↔meta |
| md | 16px | Padding de card/linha da fila, gap entre linhas de formulário, gap de toast |
| lg | 24px | Padding lateral de página no mobile, gutter, seções do modal |
| xl | 32px | Gap vertical entre toolbar e lista, padding do modal no desktop |
| 2xl | 48px | Respiro entre blocos de página (header → conteúdo) |
| 3xl | 64px | Altura do header, padding vertical do footer |

Exceptions:
- **Touch targets:** mínimo **44×44px** para todo elemento interativo (abas, chips, botões de ação da linha, X do modal, paginação, logout). A exceção ao 8-point vale só para `min-height`/`min-width`.
- **Input/textarea/select do modal de edição:** altura **48px** (mobile-first, dedo) para campos de linha única; `textarea` com `min-height: 96px` e resize vertical.
- **Turnstile:** o iframe da Cloudflare ocupa ~**300×65px** — reservar `min-width: 300px; max-width: 100%` e **nunca** aplicar `transform`/`scale` (regra herdada do Phase 03).
- **Container admin:** `max-width: 1120px`, gutter 24px (mobile 16px). O modal de edição tem `max-width: 720px` (desktop) e é bottom sheet no mobile.
- **Toast:** largura máx. **360px**, fixo no canto inferior direito (desktop) / inferior central (mobile <640).

---

## Typography

Mesma tabela do Phase 04. Exatamente **2 pesos** (400, 600) e **4 tamanhos**.

| Role | Size | Weight | Line Height | Uso no admin |
|------|------|--------|-------------|--------------|
| Body | 16px | 400 | 1.5 | Texto de `activities`/`requirements`/`benefits` no modal, snippet, toast |
| Label | 14px | 400 | 1.4 | Metadados (empresa, cidade, data), chips/tabs, paginação, rótulos de campo, placeholders, contagem, badge de status, toast |
| Heading | 20px | 600 | 1.2 | Título do modal de edição, título da seção, wordmark, nome da vaga na linha da fila |
| Display | 28px | 600 | 1.2 | `<h1>` único da página (`/admin/review`: "Revisão de vagas"; `/admin`: "Painel admin") |

Rules:
- Exatamente **2 pesos**: 400 e 600. Proibido 700/300.
- Menor tamanho permitido: **14px** (nunca 12px para texto informativo). Rótulo "Espaço publicitário" usa Label (não aplicável no admin, mas reservado).
- Valores de contato no modal: Body/16, peso **600**, cor `--color-accent-soft` (mesma regra do público).
- Snippet (somente leitura): Body/16, 400, `#b8a9cc` (muted), `white-space: pre-wrap`, `overflow-wrap: anywhere`.
- Placeholder do snippet vazio: Label/14, 400, italic, `#b8a9cc`.
- Nenhuma fonte customizada, nenhum `letter-spacing` negativo.

---

## Color

Mesma paleta do Phase 04.

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#0f0a1a` (`--color-canvas`) | Fundo da página, fundo do header, input/textarea/select |
| Secondary (30%) | `#1a1025` (`--color-surface`) | Cards/linhas da fila, modal, toast, painel de erro/sucesso |
| Accent (10%) | `#8b5cf6` (bordas/indicador) · `#a78bfa` (texto) · `#7c3aed` (preenchimento) | Lista fechada abaixo |
| Yellow | `#facc15` (`--color-donate`) | **Somente** o botão "Doações" do shell público — **não usado** na área admin |
| Destructive | `#f87171` / `#fecaca` | Apenas borda/texto do modal de confirmação de exclusão e painel de erro de mutação |

**Accent reservado para (lista fechada — nunca "todos os interativos"):**

1. Botão **"Aprovar"** em cada linha da fila (`#7c3aed`, texto branco, 600) — **o único botão preenchido de acento do admin**.
2. Aba ativa (`pending`/`needs_review`) — fundo `#7c3aed`, texto branco, `aria-selected="true"`.
3. Link de texto de ação secundária (`#a78bfa`): "Limpar filtros", "Tentar novamente", "Voltar", página ativa na paginação.
4. Valores de contato revelados no modal (telefone/e-mail) em `#a78bfa`/600.
5. Focus ring: `2px solid #a78bfa`, `outline-offset: 2px` — em todo elemento focável.
6. Borda `#8b5cf6` **apenas em hover/focus** de botão secundário, linha da fila, input/textarea/select, tab inativa.

**Nunca acento:** superfície de linha/card, botões "Editar"/"Excluir" (secundários outline), header admin, footer, datas, empresa, placeholder, toast de sucesso (usa borda `#7c3aed` mas fundo `--color-surface`).

**Estados por componente:**

| Componente | Base | Hover | Active/Pressed | Focus |
|------------|------|-------|----------------|-------|
| CTA primário ("Aprovar") | bg `#7c3aed`, texto `#fff`, 600 | bg `#6d28d9` | bg `#5b21b6` | ring `#a78bfa` |
| Secundário ("Editar", "Excluir", "Salvar", "Cancelar", "Fechar", "Tentar novamente") | bg transparente, borda 1px `#6d5a91`, texto `#e2e8f0` | borda `#8b5cf6`, texto `#a78bfa` | bg `rgba(139,92,246,.10)` | ring `#a78bfa` |
| Ghost (X, logout, limpar) | texto `#b8a9cc` | texto `#e2e8f0`, bg `rgba(167,139,250,.08)` | bg `rgba(167,139,250,.14)` | ring `#a78bfa` |
| Tab inativa | borda inferior 1px `#6d5a91`, texto `#e2e8f0` | texto `#a78bfa`, borda `#8b5cf6` | — | ring `#a78bfa` |
| Tab ativa | bg `#7c3aed`, texto `#fff`, 600, `aria-selected="true"` | bg `#6d28d9` | — | ring `#a78bfa` |
| Chip de cidade (filtro) não selecionado | borda 1px `#6d5a91`, texto `#e2e8f0` | borda `#8b5cf6`, texto `#a78bfa` | — | ring `#a78bfa` |
| Chip de cidade selecionado | bg `#7c3aed`, texto `#fff`, 600, `aria-pressed="true"` | bg `#6d28d9` | — | ring `#a78bfa` |
| Input/textarea/select | bg `#0f0a1a`, borda 1px `#6d5a91`, texto `#e2e8f0`, placeholder `#b8a9cc` | borda `#8b5cf6` | — | ring `#a78bfa` |
| Linha da fila | bg `#1a1025`, borda 1px `#2a1f3d`, radius 12px | borda `#8b5cf6` (desktop hover) | — | `:focus-within` → borda `#8b5cf6` |
| Desabilitado | `opacity: .5; cursor: not-allowed` | — | — | não recebe foco |
| Destructive ("Excluir" no modal de confirmação) | bg transparente, borda 1px `#f87171`, texto `#f87171` | bg `rgba(248,113,113,.10)`, texto `#fecaca` | bg `rgba(248,113,113,.18)` | ring `#a78bfa` |

**Contraste (calculado, WCAG 2.1)** — mesmos pares do Phase 04 (revalidados; nenhum par novo fora da tabela):

| Par | Ratio | Requisito | Resultado |
|-----|-------|-----------|-----------|
| `#e2e8f0` sobre `#0f0a1a` | **15.8:1** | 4.5:1 texto | PASS |
| `#e2e8f0` sobre `#1a1025` | **14.9:1** | 4.5:1 texto | PASS |
| `#b8a9cc` sobre `#0f0a1a` | **8.1:1** | 4.5:1 texto | PASS |
| `#b8a9cc` sobre `#1a1025` | **7.7:1** | 4.5:1 texto | PASS |
| `#a78bfa` sobre `#0f0a1a` | **7.1:1** | 4.5:1 texto | PASS |
| `#a78bfa` sobre `#1a1025` | **6.7:1** | 4.5:1 texto | PASS |
| `#ffffff` sobre `#7c3aed` | **5.7:1** | 4.5:1 texto | PASS |
| `#ffffff` sobre `#8b5cf6` | 4.23:1 | 4.5:1 texto | **FAIL — proibido** |
| `#fecaca` sobre erro (`rgba(248,113,113,.10)` em `#1a1025`) | **~10.4:1** | 4.5:1 texto | PASS |
| `#f87171` (borda) sobre `#1a1025` | **6.7:1** | 3:1 não-texto | PASS |
| `#6d5a91` (borda de controle) sobre `#0f0a1a` | **3.26:1** | 3:1 não-texto | PASS |

---

## Copywriting Contract

Todo copy em **pt-BR**. Erros do backend são renderizados **verbatim** (`body.detail`), como no Phase 03/04 — o front não mantém tabela de tradução de erro. Nenhum texto de marketing; tom direto e operacional (admin único).

| Elemento | Copy |
|----------|------|
| `<title>` da área admin | `NaoQueroUsar — Painel admin` |
| `description` | `Área restrita de curadoria de vagas.` |
| `<h1>` do hub (`/admin`) | **"Painel admin"** |
| Subtítulo do hub | `Curadoria de vagas: extraia, revise e publique.` |
| `<h1>` da fila (`/admin/review`) | **"Revisão de vagas"** |
| Subtítulo da fila | `Confira o texto-fonte ao lado e aprove para publicar.` |
| Abas | `Pendentes` · `Precisam correção` (com contagem: `Pendentes (12)`) |
| CTA da linha | **"Aprovar"** (primário) · **"Editar"** (secundário) · **"Excluir"** (destructive) |
| Botão "Aprovar" em loading | `Aprovando...` |
| Botão "Salvar" do modal | `Salvar alterações` · loading: `Salvando...` |
| Botão "Excluir" do modal de confirmação | `Excluir vaga` · loading: `Excluindo...` |
| Rótulos de campo (modal) | `Título` · `Empresa` · `Atividades` · `Requisitos` · `Salário` · `Benefícios` · `Cidade` · `E-mail de contato` · `Telefone de contato` |
| Placeholder dos campos | `Título da vaga` · `Nome da empresa (opcional)` · `Descreva as atividades` · `Requisitos (opcional)` · `Ex.: R$ 2.500 ou A combinar` · `Benefícios (opcional)` · `seu@email.com` · `+55 11 99999-9999` |
| Select de cidade (opções) | `São Paulo` · `Rio de Janeiro` · `Belo Horizonte` · `Remoto` |
| Rótulo do painel de snippet | `Texto-fonte` |
| Placeholder snippet vazio | `Sem texto-fonte disponível` (Label, italic, `#b8a9cc`) |
| Rótulo do status (badge) | `Pendente` · `Precisa correção` |
| Contagem de resultados (fila) | `{n} vagas pendentes` · singular `1 vaga pendente` · `needs_review`: `{n} vagas para correção` |
| Empty — fila `pending` vazia | Título: **"Nenhuma vaga pendente"** · Corpo: `Todas as vagas extraídas já foram revisadas. Cole um novo texto em "Colar vagas".` (sem CTA extra — link para paste no hub) |
| Empty — aba `needs_review` vazia | Título: **"Nenhuma vaga para correção"** · Corpo: `A extração não gerou vagas com defeitos. Volte quando colar um novo texto.` |
| Empty — filtro de cidade sem resultado | Título: `Nenhuma vaga nesta cidade` · Corpo: `Remova o filtro de cidade para ver todas.` · Botão: `Limpar filtro` |
| Erro de fetch (fila) | Título: `Não foi possível carregar a fila.` · Corpo: `Verifique sua conexão e tente novamente.` · Botão: `Tentar novamente` |
| Erro de mutação (aprovar/editar/excluir) | Toast de erro com `body.detail` verbatim (ex.: `Vaga precisa ter ao menos um contato (email ou telefone)`, `Vaga não encontrada`, `Status inválido`) |
| Sucesso — aprovar | Toast: `Vaga aprovada e publicada.` |
| Sucesso — editar | Toast: `Vaga atualizada.` |
| Sucesso — excluir | Toast: `Vaga excluída.` |
| Login (paste) — labels herdados | `Senha` · `Verificação anti-bot` · botão `Entrar` · loading `Entrando...` |
| Hub — links | `Colar vagas` (descrição: `Cole um texto bruto e extraia vagas`) · `Revisar vagas` (descrição: `Aprove, edite ou exclua vagas pendentes`) |
| Logout | `Sair` (ghost, header) |
| Modal de confirmação de exclusão | Título: `Excluir esta vaga?` · Corpo: `Esta ação é permanente. A vaga será removida do banco e não aparecerá mais no painel.` · Botões: `Cancelar` · `Excluir vaga` |
| Validação client-side (modal de edição) | `Título é obrigatório.` · `Cidade inválida.` · `Informe ao menos um contato (e-mail ou telefone).` · `E-mail inválido.` · `Telefone inválido.` |
| Paginação | `Anterior` · `Página 2 de 5` · `Próxima` (`aria-label`: `Página anterior` / `Próxima página`) |
| Guard (sem token) | Redireciona silenciosamente para `/admin/paste` (sem copy — a página de paste mostra o login) |
| Toast de sucesso (variante) | fundo `#1a1025`, borda esquerda 4px `#7c3aed`, texto `#e2e8f0`, ícone `check` `#a78bfa` |
| Toast de erro (variante) | fundo `#1a1025`, borda esquerda 4px `#f87171`, texto `#fecaca`, ícone `x` `#f87171` |
| Auto-dismiss | 3000ms; hover pausa o timer; botão `×` (aria-label `Fechar notificação`) fecha manualmente |

Pluralização: `{n} vagas pendentes` com `n === 1` → `1 vaga pendente`; `n === 0` → o empty state substitui a contagem (não renderizar "0 vagas pendentes"). Mesma regra para `needs_review`.

---

## Contrato de dados (o que a UI pode renderizar)

Schema admin (novo, `JobAdmin`) — diferente do `JobPublic` (contact-free). Exposto **apenas** em rotas atrás de `require_admin`.

| Campo (`JobAdmin`) | Onde aparece | Regra |
|---------------------|--------------|-------|
| `id` | chave de lista, payload de mutação | nunca exibido |
| `title` | linha da fila (Heading 20/600) + modal | obrigatório |
| `company` | linha da fila (Label muted) + modal | `null`/vazio → `—` no modal (campo editável), omitido na linha da fila |
| `activities` | modal (textarea) | `null` → campo vazio |
| `requirements` | modal (textarea) | `null` → campo vazio |
| `salary` | linha da fila (Label, se houver) + modal | texto livre — renderizar **cru** |
| `benefits` | modal (textarea) | `null` → campo vazio |
| `city` | badge na linha + select no modal | uma das 4 labels fixas |
| `status` | aba ativa determina; badge na linha (`Pendente`/`Precisa correção`) | não editável |
| `contact_email` | modal (input) | `null` → campo vazio; exposto só aqui |
| `contact_phone` | modal (input) | `null` → campo vazio; exposto só aqui |
| `source_snippet` | painel "Texto-fonte" (read-only) | `null`/vazio → placeholder `Sem texto-fonte disponível` |
| `created_at` | linha da fila (`Criada em dd/mm/aaaa`) | `Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo" })` |
| `updated_at` | não exibido no MVP | — |
| `expires_at` | não exibido no MVP (Phase 6 pode exibir) | — |

`JobUpdate` (body de `PUT /admin/jobs/{id}`): todos os campos editáveis; `title` e `city` obrigatórios; `contact_email`/`contact_phone` opcionais mas ao menos um; city validado contra `{São Paulo, Rio de Janeiro, Belo Horizonte, Remoto}` (aceita slug/label/canônico, normalizado para canônico antes de persistir — Pitfall 2).

**Datas são absolutas por decisão** (herdado do Phase 04): `dd/mm/aaaa` em `America/Sao_Paulo`, nunca "há X dias".

---

## Contrato de URL e estado

A área admin é **client-fetched** (token em `sessionStorage`, sem cookie — Phase 1 D-01), então o estado vive em **memória de componente**, não na URL. Diferente do board público (que usa URL state por ser RSC).

| Estado | Onde vive | Default | Comportamento |
|--------|-----------|---------|---------------|
| Aba ativa (`pending`/`needs_review`) | `useState` no `ReviewQueue` | `pending` | troca refaz fetch da página 1 |
| Filtro de cidade | `useState` | ausente = Todas | troca refaz fetch da página 1 |
| Página atual | `useState` | `1` | controles de paginação chamam fetch |
| Tamanho de página | constante | `24` | fixo (limit do backend) |
| Ordenação | constante | `recentes` (`created_at DESC`) | fixo por D-02; não exposto na UI |

Regras:
- Toda mutação (aprovar/editar/excluir) **revalida** a página atual (refetch) após sucesso para manter `total` correto; otimista remove/atualiza imediatamente, rollback em erro.
- Se a página atual fica vazia após mutação e `page > 1`, decrementa `page` e refaz fetch.
- Sem `localStorage`/`sessionStorage` para estado de UI (exceto o token `nqu_admin_token`).
- Deep link `?vaga=` **não** se aplica ao admin.

---

## Interaction Contract

### A. Hub `/admin` (D-11)

```
┌──────────────────────────────────────────────────┐  header h64 · bg #0f0a1a · border-b #2a1f3d
│  NaoQueroUsar · Painel admin        [Sair]       │
├──────────────────────────────────────────────────┤
│                                                  │
│  Painel admin                                    │  Display 28/600
│  Curadoria de vagas: extraia, revise e publique.  │  Body muted
│                                                  │
│  ┌────────────────────┐  ┌────────────────────┐  │
│  │  Colar vagas        │  │  Revisar vagas     │  │  cards #1a1025, border #2a1f3d
│  │  Cole um texto      │  │  Aprove, edite ou  │  │  hover → border #8b5cf6
│  │  bruto e extraia... │  │  exclua vagas...   │  │
│  └────────────────────┘  └────────────────────┘  │
└──────────────────────────────────────────────────┘
```

- Guard client-side: sem token → redireciona para `/admin/paste` (que mostra o login). Sem copy de "acesso negado".
- Cards do hub são `<Link>` para `/admin/paste` e `/admin/review`, com `aria-label` descritivo.
- Header admin compartilhado (mesmo componente em `/admin`, `/admin/paste`, `/admin/review`): wordmark `NaoQueroUsar · Painel admin` (Heading 20/600) + botão `Sair` (ghost) à direita.
- `Sair`: remove `nqu_admin_token` de `sessionStorage` e redireciona para `/admin/paste`.

### B. Fila de revisão `/admin/review` (REVW-01)

```
┌─────────────────────────────────────────────────────────────┐
│  Revisão de vagas                                           │
│  Confira o texto-fonte ao lado e aprove para publicar.      │
│  [ Pendentes (12) ]  [ Precisam correção (3) ]              │  tabs, h44
│  [ Todas ] [São Paulo] [Rio de Janeiro] [BH] [Remoto]       │  chips, h44
│  ─────────────────────────────────────────────────────────  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  {title}                            [Pendente]       │  │  Heading 20/600
│  │  {company} · {city} · Criada em dd/mm/aaaa            │  │  Label muted
│  │  Salário: {salary}                                    │  │  Label (se houver)
│  │  ┌──────────┐ ┌────────┐ ┌──────────┐                │  │
│  │  │ Aprovar  │ │ Editar │ │ Excluir  │                │  │  h44
│  │  └──────────┘ └────────┘ └──────────┘                │  │
│  └───────────────────────────────────────────────────────┘  │
│  … (até 24 por página)                                     │
│  [ Anterior ]  Página 2 de 5  [ Próxima ]                  │
└─────────────────────────────────────────────────────────────┘
```

- **Tabs** (client-side): `Pendentes` (status `pending`) e `Precisam correção` (status `needs_review`). Cada aba tem sua própria fila e contagem. Tab ativa = preenchida `#7c3aed`; inativa = outline. `role="tablist"`/`role="tab"`/`aria-selected`.
- **Chips de cidade**: single-select + `Todas` (reusa padrão do board público: `aria-pressed`, container `role="group"` `aria-label="Filtrar por cidade"`). No mobile, linha com scroll horizontal (`overflow-x-auto`, `scrollbar-width: none`).
- **Linha da fila**: `bg #1a1025`, borda 1px `#2a1f3d`, radius 12px, padding 16px. Hover (desktop) → borda `#8b5cf6`. `:focus-within` → borda `#8b5cf6`.
- **Badge de status**: pill, `#a78bfa` texto sobre `rgba(139,92,246,.12)`, radius 999px, Label 14/400.
- **Ações** (gap 8px, wrap no mobile): `Aprovar` (primário, h44), `Editar` (secundário), `Excluir` (destructive outline).
- **Estados de loading da linha**: ao aprovar/excluir, a linha inteira recebe `opacity: .6; pointer-events: none` + spinner de 16px no botão acionado; texto do botão muda para `Aprovando...`/`Excluindo...`. Em erro, reverte + toast.
- **Empty states**: ver tabela de copy (3 variantes: pending vazio, needs_review vazio, filtro de cidade sem resultado).
- **Skeleton (1ª carga)**: 6 linhas placeholder (`h-6 w-3/5`, `h-4 w-2/5`, `h-10` para ações), blocos `#2a1f3d`, `animate-pulse` (desligado sob `prefers-reduced-motion: reduce`). Container `aria-busy="true"` + `sr-only` "Carregando fila".
- **Paginação**: controles `Anterior`/`Página N de M`/`Próxima`, h44, desabilitados nas pontas (não escondidos). Só renderiza se `total > 24`.
- **Erro de fetch**: painel de erro (`bg rgba(248,113,113,.10)`, borda `#f87171`, texto `#fecaca`) no lugar da lista + botão `Tentar novamente`.
- **Optimistic remove**: ao aprovar/excluir, a linha é removida da lista imediatamente (animação de fade 150ms) e o toast de sucesso aparece; em erro, a linha volta na posição original + toast de erro com `body.detail`.

### C. Modal de edição (REVW-03, REVW-05)

**Elemento:** `<dialog>` nativo + `showModal()` (trap de foco, ESC, backdrop de graça — padrão do Phase 04). `aria-labelledby` aponta para o `<h2>` do título (`Editar vaga`).

| Aspecto | Contrato |
|---------|----------|
| Mobile (<640) | Bottom sheet: ancorado embaixo, largura 100%, `max-height: 92dvh`, topo arredondado 16px, handle decorativo (32×4px, `#6d5a91`, `aria-hidden`), `padding-bottom: env(safe-area-inset-bottom)` |
| Desktop (≥640) | Centralizado, `max-width: 720px`, `max-height: 88dvh`, radius 16px, `::backdrop` = `rgba(5,2,12,.72)` |
| Estrutura | Header sticky (`bg #1a1025`, `border-b #2a1f3d`): título `Editar vaga` + X 44×44. Corpo com scroll (`overflow-y: auto; overscroll-behavior: contain`). Footer sticky (`border-t #2a1f3d`): `Cancelar` + `Salvar alterações`. |
| Layout do corpo | **Desktop (≥768):** grid 2 colunas — coluna esquerda (formulário, flex-1) + coluna direita (painel "Texto-fonte", `width: 320px`, `position: sticky; top: 0`). **Mobile (<768):** empilhado — formulário primeiro, painel "Texto-fonte" abaixo em `<details>` (accordion, fechado por default, `summary` = "Texto-fonte"). |
| Abertura | `showModal()`; foco vai para o primeiro campo (`title`); scroll do documento travado; estado do form resetado quando `job.id` muda (Pitfall 9). |
| Fechamento | X, `Esc` (evento `cancel`), clique no backdrop, `Cancelar`, ou após salvar com sucesso. Foco volta para o botão `Editar` de origem. |
| Fechar durante submit | **Bloqueado** (modal não fecha enquanto `saving === true`; X e ESC desabilitados). |
| Seções do form | `Título`* · `Empresa` · `Cidade`* (select) · `Salário` · `E-mail de contato` · `Telefone de contato` · `Atividades` (textarea) · `Requisitos` (textarea) · `Benefícios` (textarea). `*` obrigatório. |
| Validação | Client-side (manual, sem zod — A5): título não vazio, cidade no conjunto, ao menos um contato, e-mail válido se preenchido, telefone com dígitos se preenchido. Erros inline abaixo do campo (`#f87171`, Label 14). Submit bloqueado até válido. Backend revalida (422 → toast com `body.detail`). |
| Painel "Texto-fonte" | Read-only, `white-space: pre-wrap`, `overflow-wrap: anywhere`, `max-height: 60vh`, scroll próprio, fundo `#0f0a1a`, borda 1px `#2a1f3d`, radius 8px, padding 12px. Quando vazio/nulo: placeholder `Sem texto-fonte disponível` (Label, italic, `#b8a9cc`) no mesmo slot. **Sem destaque automático de termos** (D-10). |
| Submit | `PUT /admin/jobs/{id}` com todos os campos. Em sucesso: toast `Vaga atualizada.`, atualiza a linha na lista (in-place), fecha o modal. Em 422: toast de erro com `body.detail` verbatim, modal permanece aberto. |

### D. Modal de confirmação de exclusão (REVW-04)

`<dialog>` nativo, `max-width: 480px`, centralizado em todas as faixas (não é bottom sheet). Estrutura: título `Excluir esta vaga?` (Heading 20/600) + corpo (Body 16) + footer com `Cancelar` (secundário) + `Excluir vaga` (destructive). Durante exclusão, botão destructive mostra `Excluindo...` e fica disabled; `Cancelar` desabilitado. ESC e backdrop fecham **apenas** se não estiver excluindo.

### E. Toast (D-13)

- Provider `ToastProvider` envolve `app/admin/layout.tsx` (ou um client wrapper) e expõe `useToast()`.
- Container fixo: `bottom-16 right-4` (desktop ≥640) / `bottom-4 left-4 right-4` (mobile <640), `z-50`, `flex flex-col gap-8px`, `max-width: 360px`.
- Toast: `bg #1a1025`, borda 1px `#2a1f3d`, radius 8px, padding 12px 16px, shadow `0 8px 24px rgba(0,0,0,.4)`. Borda esquerda 4px colorida por variante (sucesso `#7c3aed`, erro `#f87171`). Ícone 16px à esquerda, mensagem Body 14/400, botão `×` ghost à direita.
- Animação: slide-in de baixo + fade (150ms ease-out); respeita `prefers-reduced-motion`.
- Auto-dismiss 3000ms; hover pausa; múltiplos toasts empilham (max 3 visíveis, o mais antigo é removido).
- Sem lib externa (D-13).

### F. Guard client-side (D-14)

- Hook `useAdminGuard()` lê `sessionStorage.getItem("nqu_admin_token")` em `useEffect`; se ausente, `router.replace("/admin/paste")`.
- Aplicado em `/admin` (hub) e `/admin/review`. `/admin/paste` não usa guard (é a tela de login quando não autenticado).
- Backend permanece autoritativo (`require_admin` → 401); o front só melhora a UX.
- Token nunca é logado nem exposto em URL.

### G. Migração do paste (D-12)

- `ExtractForm.tsx` deixa de importar `globals-admin.css` e usa classes Tailwind (mesmos tokens). Comportamento preservado: login com Turnstile `interaction-only`, `action="login"`, reset por remount (`key`), token em `sessionStorage`, extração, alertas/discards.
- Layout do paste: container centralizado `max-width: 720px`, painel `#1a1025`, radius 12px, padding 24px. Turnstile wrapper mantém `overflow: hidden; max-width: 100%` e **sem** `transform`/`scale`.
- Sem mudança de copy do paste (herdado do Phase 02/03).

### H. Header admin compartilhado

- `sticky top-0`, h64, `bg #0f0a1a`, `border-b 1px #2a1f3d`, container 1120px.
- Esquerda: wordmark `NaoQueroUsar` (Heading 20/600, `#e2e8f0`) + separador `·` + `Painel admin` (Label 14, `#b8a9cc`).
- Direita: `Sair` (ghost, h44).
- **Sem botão "Doações"** (reservado ao shell público — UIUX-02). Admin não exibe ADS.

### Universal

- Focus ring `2px solid #a78bfa`, `outline-offset: 2px`, em **todo** focável (`:focus-visible`).
- `prefers-reduced-motion: reduce` → sem `animate-pulse`, sem `transition` de duração > 0, sem `scroll-behavior: smooth`, toasts sem animação.
- Nenhuma informação transmitida só por cor (tab ativa = fill + peso 600 + `aria-selected`; badge de status = texto + cor; erro = texto + borda).
- Toque mín. 44×44 com ≥8px entre alvos adjacentes.
- Sem `transform`/`scale` no iframe do Turnstile.
- `lang="pt-BR"` no `<html>` (já existe) e `<meta name="theme-color" content="#0f0a1a">`.

---

## Responsive Contract

Breakpoints = defaults do Tailwind (não inventar novos). Admin é mais simples que o board (sem sidebar de ADS).

| Faixa | Fila | Modal de edição | Hub |
|-------|------|-----------------|-----|
| `<640` (base, mobile) | 1 coluna de linhas; chips com scroll horizontal; ações wrap (botões full-width em coluna) | bottom sheet 92dvh; form empilhado; snippet em accordion abaixo | cards empilhados (1 coluna) |
| `≥640` (`sm`) | linhas full-width; chips quebram em linha; ações em linha | centralizado 720px | cards lado a lado (2 colunas) |
| `≥768` (`md`) | — | grid 2 colunas (form + snippet sticky) | — |
| `≥1024` (`lg`) | container 1120px | — | — |

- Mobile-first: CSS base é o mobile; `sm:`/`md:`/`lg:` só adicionam.
- Nenhum scroll horizontal na página (só a linha de chips tem scroll próprio).
- Linhas da fila usam `gap: 16px` (mobile) / `24px` (≥640).

---

## Component Inventory

| # | Componente / arquivo | Tipo | Status |
|---|----------------------|------|--------|
| 1 | `frontend/app/admin/admin.css` (`@import "tailwindcss"` + `@theme`) | CSS | **novo** |
| 2 | `frontend/app/admin/layout.tsx` (shell: header admin, importa `admin.css`, envolve com `ToastProvider`) | RSC | **novo** |
| 3 | `frontend/app/admin/page.tsx` (hub: links para paste/review, guard client) | Client (guard) | **novo** |
| 4 | `frontend/app/admin/review/page.tsx` + `ReviewQueue.tsx` (client: fetch, tabs, chips, paginação, otimismo) | Client | **novo** |
| 5 | `frontend/app/admin/review/EditJobDialog.tsx` (modal `<dialog>`: form + snippet side panel) | Client | **novo** |
| 6 | `frontend/app/admin/review/DeleteConfirmDialog.tsx` (modal de confirmação) | Client | **novo** |
| 7 | `frontend/app/admin/paste/page.tsx` | RSC | **modificar** (importa layout novo; remove `globals-admin.css`) |
| 8 | `frontend/app/admin/paste/ExtractForm.tsx` | Client | **modificar** (migra para Tailwind v4; preserva Turnstile) |
| 9 | `frontend/components/admin/ToastProvider.tsx` + `useToast` | Client | **novo** |
| 10 | `frontend/components/admin/AdminGuard.tsx` (ou hook `useAdminGuard`) | Client | **novo** |
| 11 | `frontend/components/admin/ReviewRow.tsx` (linha da fila) | Client | **novo** |
| 12 | `frontend/components/admin/CityChips.tsx` (reuso do padrão do board) | Client | **novo** (ou reuso de `BoardToolbar` subset) |
| 13 | `frontend/components/admin/icons.tsx` (ícones admin inline) | RSC | **novo** |
| 14 | `frontend/lib/api.ts` → `JobAdmin`, `JobAdminListResponse`, `JobUpdate`, `listAdminJobs`, `approveJob`, `updateJob`, `deleteJob` | TS | **modificar** |
| 15 | Backend `GET/PATCH/PUT/DELETE /api/v1/admin/jobs[/{id}[/approve]]` | Python | **novo** (rotas em `admin.py`) |
| 16 | Backend `JobAdmin`, `JobUpdate`, `JobAdminListResponse` schemas | Python | **novo** |
| 17 | Backend `list_by_status`, `get_job`, `approve_job`, `update_job`, `delete_job` em `crud/jobs.py` | Python | **novo/modificar** |
| 18 | `frontend/app/admin/paste/globals-admin.css` | CSS | **removido** (D-12) |
| 19 | `backend/tests/test_admin_jobs.py` | Tests | **novo** (Wave 0) |

Notas de arquitetura: a fila é client-fetched (token em `sessionStorage`); não há RSC para o admin. O modal de edição é único (instância controlada por `selectedJob`), não um por linha. O snippet é renderizado em `<pre>`/`<div>` com `white-space: pre-wrap`.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not required (shadcn não inicializado — ver §Design System) |
| third-party registries | none | not required |

`next-turnstile@1.0.7` é dependência npm já vetada no Phase 03 (sem dependências de runtime). Nenhum bloco de registry entra neste contrato → nenhum gate de `shadcn view` foi acionado. Nenhuma dependência nova no frontend (sem zod, sem lib de toast — D-13 e A5).

---

## Decisões de discrição (OpenCode) — defaults aplicados

Não houve canal interativo nesta execução; cada decisão abaixo tem default seguro e caminho de override. Nenhuma bloqueia o plano.

| # | Questão | Decisão | Por quê / override |
|---|---------|---------|--------------------|
| 1 | Design system | **Tailwind v4 no admin (admin.css route-scoped), shadcn não, ícones SVG inline** | Stack travada no PROJECT.md + D-12; paridade visual com o público. Override: rodar gate shadcn antes do plano |
| 2 | Aba "Precisam correção" | **tab client-side** na mesma rota `/admin/review` | Single fetch state, mais simples; override: rota separada se preferir |
| 3 | Guard sem token | **redirect silencioso para `/admin/paste`** | Login vive lá; evita tela de "acesso negado" extra |
| 4 | Paginação na fila | **controles `Anterior`/`Página N de M`/`Próxima` (botões client, não `<Link>`)** | Admin é client-fetched; reusa visual do `Pagination` mas com `onClick` |
| 5 | Empty state da fila | **3 variantes** (pending vazio, needs_review vazio, filtro sem resultado) com copy da tabela | — |
| 6 | Validação do modal de edição | **manual (sem zod)** | Form pequeno; evita dependência nova (A5). Override: adicionar zod se preferir |
| 7 | Toast | **provider próprio, bottom-right, 3s, variantes success/error, max 3** | D-13; sem lib externa |
| 8 | Atualização otimista | **remove/atualiza imediatamente + refetch após sucesso + rollback em erro + decremento de página se vazia** | Pitfalls 3 e 8 |
| 9 | Acento no admin | **"Aprovar" é o único botão preenchido de acento**; "Editar"/"Excluir" são outline | Admin é ferramenta, não vitrine; evita competição visual com a ação principal |
| 10 | Snippet | **read-only, sem highlight automático, placeholder quando vazio** | D-10; evita falsos positivos |
| 11 | Modal de edição — layout | **2 colunas no desktop (form + snippet sticky), accordion no mobile** | D-09; mobile-first |
| 12 | Exclusão | **hard delete com confirmação (modal dedicado, não `window.confirm`)** | D-07; UX consistente com o restante |

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

*Sources: `05-CONTEXT.md` (decisões D-01..D-14), `05-RESEARCH.md` (endpoints, schemas, pitfalls), `04-UI-SPEC.md` (tokens herdados), `03-UI-SPEC.md` (tokens originais), `REQUIREMENTS.md` (REVW-01..05), `ROADMAP.md` (Phase 5), `STATE.md`, codebase scout (`frontend/app/(public)/public.css`, `frontend/app/admin/paste/*`, `frontend/components/board/*`, `frontend/lib/api.ts`, `backend/app/api/v1/admin.py`, `backend/app/crud/jobs.py`, `backend/app/models/job.py`, `backend/app/schemas/job.py`, `backend/app/deps.py`). Nenhuma dependência nova.*