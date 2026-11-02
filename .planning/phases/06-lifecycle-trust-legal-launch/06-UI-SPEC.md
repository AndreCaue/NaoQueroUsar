---
phase: 6
slug: lifecycle-trust-legal-launch
status: draft
shadcn_initialized: false
preset: none
design_system: tailwind-v4
created: 2026-10-28
---

# Phase 06 — UI Design Contract

> Visual and interaction contract for frontend phases. Generated manually (subagent spawn failed due to free usage limit), verified by gsd-ui-checker.

**Escopo da fase:** badge "Vaga revisada" em cards e modal (TRST-01), UI de report de vaga no modal (TRST-02), e páginas legais com seções (privacidade, termos, aviso LGPD/intermediário) acessíveis (TRST-03). As alterações ao ciclo de vida (LIFE-01..04) são backend/APScheduler/endpoint protegido e **não** mudam UI. O deploy real com CORS/segredos (critério de sucesso 5) está **no escopo da fase** via `06-04-PLAN.md`, mas também **não** introduz mudança visual: a UI já entrega o estado de cold-start (`error.tsx`) e o contrato visual desta spec cobre apenas o que o usuário vê.

**Relação com o Phase 04:** este contrato reutiliza integralmente os tokens, tipografia, espaçamento e padrões do `04-UI-SPEC.md` (Tailwind v4, dark theme roxo, sem shadcn, ícones SVG inline). Novos elementos seguem os mesmos estados e acessibilidade.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | **Tailwind CSS v4** (`4.3.3`, CSS-first via `@import "tailwindcss"` + `@theme`) — herdado do Phase 04 |
| Preset | not applicable |
| Component library | **none** — nenhum shadcn/radix/base-ui |
| Icon library | **none** — reutilizar SVGs inline em `frontend/components/board/icons.tsx` ou adicionar se necessário (manter `stroke-width: 1.75`, `currentColor`) |
| Font | System stack: `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` — herdado |

### Onde os estilos entram
- Reutilizar `frontend/app/(public)/public.css` com os mesmos tokens `@theme` do Phase 04.
- Páginas legais (`/privacidade`, `/termos`) usam o mesmo shell público (`app/(public)/layout.tsx`).
- Nenhuma alteração em `frontend/app/admin/paste/globals-admin.css`.

---

## Spacing Scale

Mesma escala do Phase 04 (múltiplos de 4). Sem token novo.

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Gap ícone↔texto |
| sm | 8px | Gap entre elementos compactos |
| md | 16px | Padding padrão |
| lg | 24px | Seções |
| xl | 32px | Layout gaps |
| 2xl | 48px | Major breaks |
| 3xl | 64px | Page-level |

**Exceções (herdadas):** touch targets mínimos 44×44px; focus ring obrigatório.

---

## Typography

Herdado do Phase 04. Sem alterações.

| Role | Size | Weight | Line Height | Uso |
|------|------|--------|-------------|-----|
| Body | 16px | 400 | 1.5 | Texto corrido |
| Label | 14px | 400 | 1.4 | Metadados, badges |
| Heading | 20px | 600 | 1.2 | Títulos de card/dialog |
| Display | 28px | 600 | 1.2 | `<h1>` da página |

---

## Color

Herdado do Phase 04. Badge e elementos de report seguem a paleta existente.

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#0f0a1a` (`--color-canvas`) | Fundo |
| Secondary (30%) | `#1a1025` (`--color-surface`) | Cards, dialog |
| Accent (10%) | `#8b5cf6` / `#a78bfa` / `#7c3aed` | Marca, foco, CTA preenchido (respeitando regra AA) |
| Yellow | `#facc15` (`--color-donate`) | Somente botão "Doações" |
| Destructive | `#f87171` / `#fecaca` | Erros/report negativos |

**Badge "Vaga revisada":** usar cor neutra/indicativa coerente com o tema. Sugestão: texto `#a78bfa` (accent-soft) ou borda sutil `#6d5a91` com texto `#e2e8f0`. **Nunca** usar amarelo/vermelho para transmitir "confiável" — manter semântico neutro. Não competir com o CTA preenchido.

**Elemento de report:** botão/ação secundário seguindo o padrão dos botões secundários do board (borda `#6d5a91`, hover com `#8b5cf6`, texto `#e2e8f0`).

---

## Copywriting Contract

Todo copy em **pt-BR**.

| Elemento | Copy |
|----------|------|
| Badge "Vaga revisada" | **"Vaga revisada"** |
| Botão "Reportar vaga" (modal) | **"Reportar vaga"** |
| Modal de report - título | **"Reportar esta vaga"** |
| Modal de report - descrição | `Se você acredita que esta vaga é suspeita ou tem informações incorretas, envie um reporte. Não é necessário identificar-se.` |
| Modal de report - campo motivo (opcional) | `Motivo (opcional)` |
| Modal de report - placeholder | `Descreva brevemente o motivo...` |
| Modal de report - CTA enviar | **"Enviar reporte"** → `Enviando...` |
| Modal de report - sucesso | `Reporte enviado. Obrigado pela colaboração.` |
| Modal de report - erro genérico | `Não foi possível enviar o reporte. Tente novamente.` |
| Link "Privacidade e termos" (footer) | **"Privacidade e termos"** |
| Página `/privacidade` - título | **"Privacidade, Termos e Aviso Legal"** |
| Seção 1 | **"1. Privacidade"** |
| Seção 2 | **"2. Termos de Uso"** |
| Seção 3 | **"3. Aviso de Intermediário e LGPD"** |
| Nota rodapé páginas legais | `Esta página contém informações gerais. Para questões jurídicas específicas, consulte um advogado.` |

**Nota:** Textos jurídicos detalhados ficam a cargo de redação humana (conforme D-07/OpenCode's discretion). O código deve apenas criar a estrutura com as seções solicitadas.

---

## Interaction Contract

### A. Badge "Vaga revisada" (TRST-01)
- **Localização:** no card (`JobCard`) e no header do modal (`JobDetailDialog`).
- **Regra:** **automático por status `published`** (D-05). Não adicionar campo ao modelo `Job`. A badge só aparece para vagas com `status === "published"`.
- **Visual:** pequeno badge inline. Sugestão de classes: `inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border border-line-strong text-fg-muted` ou `text-accent-soft`. Manter discreto, não competir com título.
- **Acessibilidade:** elemento semântico com texto "Vaga revisada". Não usar apenas cor/icon para transmitir informação.
- **Posicionamento card:** próximo ao título ou abaixo da empresa, sem quebrar layout existente. Deve respeitar `overflow-wrap` e não empurrar CTA "Ver a vaga".
- **Posicionamento modal:** próximo ao título/empresa no header, antes ou depois dos metadados.

### B. Report de vaga (TRST-02)
- **Localização:** no footer do `JobDetailDialog`, abaixo do `RevealContact` ou em seção separada. Não interferir com o fluxo de revelar contato.
- **Trigger:** botão secundário "Reportar vaga" (outline, mesmo estilo de "Ver a vaga").
- **Modal/Sheet de report:** pode ser um segundo `<dialog>` ou um painel inline expansível. Preferir `<dialog>` nativo por consistência com o modal existente (trap de foco, ESC, backdrop).
- **Form:** textarea opcional para motivo (max ~500 caracteres). Não exigir dados pessoais.
- **Endpoint:** `POST /api/v1/public/jobs/{id}/report` (ou rota pública equivalente). Payload: `{ reason?: string }`. Sem autenticação.
- **Backend:** log estruturado (sem tabela). Frontend apenas envia e exibe feedback.
- **Estados:** `idle` → `submitting` (desabilita botões, mostra "Enviando...") → `success` (mostra mensagem, fecha após breve delay ou permite fechar) → `error` (mostra erro com opção "Tentar novamente").
- **Anti-abuso:** respeitar o mesmo espírito do Phase 03 (rate limit já pode existir no backend; frontend trata 429 com mensagem verbatim se houver).
- **Acessibilidade:** labels associados, `aria-live` para feedback de sucesso/erro.

### C. Páginas legais (TRST-03)
- **Rotas:** criar rotas públicas em `app/(public)/privacidade/page.tsx` e/ou `app/(public)/termos/page.tsx`. D-07 permite "página única com seções" — **recomendado:** uma única página `/privacidade` (ou `/legal`) com âncoras para seções Privacidade, Termos, Aviso LGPD/Intermediário. Também pode criar ambas, mas página única é mais simples.
- **Acesso:** link no footer do shell público (`app/(public)/layout.tsx`). Footer já existe no shell do board — adicionar link "Privacidade e termos" apontando para a página legal.
- **Layout:** usar mesmo shell (header, footer, background). Conteúdo em container com max-width (~800-900px), padding consistente com o board.
- **Estrutura:** `<h1>` "Privacidade, Termos e Aviso Legal", navegação por âncoras opcional, seções com `<h2>`. Incluir placeholders para texto jurídico a ser preenchido posteriormente.
- **SEO:** metadata básica (`title`, `description`) em pt-BR.
- **Sem formulários:** páginas estáticas/read-only.

---

## Component Inventory

| # | Componente / arquivo | Tipo | Phase | Status |
|---|----------------------|------|-------|--------|
| 1 | `frontend/components/board/JobCard.tsx` | Client | 6 | **modificar** (adicionar badge "Vaga revisada" quando `status === "published"`) |
| 2 | `frontend/components/board/JobDetailDialog.tsx` | Client | 6 | **modificar** (badge no header, seção/botão "Reportar vaga", segundo dialog de report) |
| 3 | `frontend/components/board/ReportJobDialog.tsx` | Client | 6 | **novo** (modal de reporte com form opcional) |
| 4 | `frontend/app/(public)/privacidade/page.tsx` ou `frontend/app/(public)/legal/page.tsx` | RSC | 6 | **novo** (página única com 3 seções) |
| 5 | `frontend/app/(public)/layout.tsx` | RSC | 6 | **modificar** (adicionar link "Privacidade e termos" no footer) |
| 6 | `frontend/lib/api.ts` | TS | 6 | **modificar** (adicionar `reportJob(jobId, reason?)`) |
| 7 | Backend `POST /api/v1/public/jobs/{id}/report` | Python | 6 | **novo** (endpoint público, log estruturado) |

**Notas:** Reutilizar ícones existentes se possível. Não criar novas dependências npm.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not required (shadcn não inicializado) |
| third-party registries | none | not required |

Nenhum bloco de registry utilizado.

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

*Sources: `06-CONTEXT.md` (D-05–D-07, LIFE-01–04, TRST-01–03), `04-UI-SPEC.md` (design system herdado), `ROADMAP.md` Phase 6, `REQUIREMENTS.md`.*
