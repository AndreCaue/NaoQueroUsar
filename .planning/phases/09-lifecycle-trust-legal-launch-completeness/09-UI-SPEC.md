---
phase: 9
slug: lifecycle-trust-legal-launch-completeness
status: draft
shadcn_initialized: false
preset: none
design_system: tailwind-v4
created: 2026-11-13
inherits: .planning/phases/06-lifecycle-trust-legal-launch/06-UI-SPEC.md
---

# Phase 09 — UI Design Contract

> Visual and interaction contract for the frontend surface touched by Phase 9.
> Inherited verbatim from `06-UI-SPEC.md` (same components and same design
> system); this document only records the Phase 9 *delta*: making the legal
> pages consistent with the public shell.

**Escopo da fase (UI):** As páginas legais `/privacidade` e `/termos-de-uso`
já existem com o texto final pt-BR. O que falta é consistência visual: hoje
cada página renderiza seu próprio `<main>`/header/footer **dentro** do route
group `(public)`, que já tem `<main>`, header e footer — resultado: dois
`<main>` aninhados, dois headers e cores fora dos tokens
(`bg-gray-900`/`text-white` em vez de `bg-canvas`/`text-fg`). O footer público
também só linka `/privacidade`, deixando `/termos-de-uso` órfão.

**Fora do escopo (UI):** badge "Vaga revisada" e diálogo de report já estão
implementados desde a Phase 6 — esta fase apenas os verifica, sem mudar o
contrato visual. Ciclo de vida/expiração, CORS, deploy e cron não têm UI.

**Relação com Phase 04/06:** tokens, tipografia, espaçamento, cores e regras de
acessibilidade são os mesmos de `04-UI-SPEC.md` e `06-UI-SPEC.md`. Nenhum token
novo. Nenhuma dependência npm nova.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | **Tailwind CSS v4** (`4.3.3`, CSS-first via `@import "tailwindcss"` + `@theme`) — herdado do Phase 04 |
| Preset | not applicable |
| Component library | **none** — nenhum shadcn/radix/base-ui |
| Icon library | **none** — SVGs inline em `frontend/components/board/icons.tsx` quando necessário |
| Font | System stack: `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` — herdado |

### Onde os estilos entram
- `frontend/app/(public)/public.css` — única fonte de tokens `@theme`.
- Páginas legais herdam o shell de `frontend/app/(public)/layout.tsx`; **não**
  declaram `<main>`, header ou footer próprios.
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
| Heading | 20px | 600 | 1.2 | Títulos de seção (`<h2>`) |
| Display | 28px | 600 | 1.2 | `<h1>` da página legal |

**Hierarquia obrigatória nas páginas legais:** exatamente um `<h1>` (título da
página) e `<h2>` por seção numerada. Os atuais `<h2>` de título de página e
`<h3>` de seção devem virar `<h1>` e `<h2>` respectivamente.

---

## Color

Herdado do Phase 04. Páginas legais passam a usar **somente** tokens.

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#0f0a1a` (`--color-canvas`) | Fundo (shell) |
| Secondary (30%) | `#1a1025` (`--color-surface`) | Blocos/seções destacadas |
| Accent (10%) | `#8b5cf6` / `#a78bfa` / `#7c3aed` | Links, foco |
| Yellow | `#facc15` (`--color-donate`) | Somente botão "Doações" |
| Destructive | `#f87171` / `#fecaca` | Erros/report negativos |

**Proibido nas páginas legais:** `bg-gray-900`, `text-white`,
`border-gray-700`, `hover:text-accent-strong` (classe inexistente nos tokens).
Usar `bg-canvas`, `text-fg`, `border-line`, `hover:text-accent-soft`.

**Badge "Vaga revisada" (verificação, sem mudança):** `inline-flex items-center
rounded-full px-2 py-0.5 text-xs font-medium border border-line-strong
text-fg-muted`, derivado apenas de `status === "published"`.

---

## Copywriting Contract

Todo copy em **pt-BR**. Os textos legais finais são conteúdo editorial e **não
devem ser reescritos** por esta fase — apenas reestruturados.

| Elemento | Copy |
|----------|------|
| `/privacidade` — `<h1>` | **"Política de Privacidade"** |
| `/privacidade` — seções | **"1. Quem somos"** … até **"13. …"** (13 seções, preservar texto atual) |
| `/termos-de-uso` — `<h1>` | **"Termos de Uso"** |
| `/termos-de-uso` — seções | **"1. …"** até **"10. …"** (10 seções, preservar texto atual, foro Americana/SP) |
| Aviso LGPD/intermediário | texto atual de `/termos-de-uso` (contém "somos apenas meio de divulgação") |
| Link do footer | **"Privacidade"** e **"Termos de Uso"** (dois links separados) |
| Nota de revisão jurídica | manter a nota existente; não inventar autoridade legal |

**Regra:** preservar 100% das palavras do texto legal atual; mudanças são
apenas de marcação semântica (h1/h2, remoção de header/footer duplicados) e de
classes de estilo.

---

## Interaction Contract

### A. Páginas legais (`/privacidade`, `/termos-de-uso`)
- **Layout:** conteúdo somente; o shell `(public)/layout.tsx` fornece `<main>`
  (max-w-[1120px]), header e footer.
- **Container de leitura:** `mx-auto w-full max-w-3xl` (≈768px) dentro do
  `<main>` do shell; padding vertical `py-8` do shell + `py-4` local no máximo.
- **Sem navegação própria:** remover o `<nav>` com "Painel Admin" e o link
  cruzado do header local; a navegação entre as duas páginas passa a viver no
  footer do shell.
- **Âncoras:** seções com `id` estáveis (`#secao-1`… ou slug do título) — não
  obrigatório, mas se existirem devem ser `scroll-mt-24` para não ficar sob o
  header sticky.
- **Links:** internos via `next/link`; texto de link com sublinhado visível
  (`underline underline-offset-2`).
- **Metadata:** `export const metadata` pt-BR por página (`title`,
  `description`); `/privacidade` e `/termos-de-uso` permanecem indexáveis
  (o `noindex` da versão Lorem Ipsum não se aplica mais ao texto final — se
  ainda existir, remover apenas se o master confirmar; caso contrário manter).
- **Sem formulários, sem client JS, sem estado.**

### B. Badge "Vaga revisada" (verificação)
- Presente em `JobCard` e `JobDetailDialog` quando `status === "published"`.
- Semântica textual (não só cor), sem competir com o CTA.

### C. Report de vaga (verificação)
- Botão secundário "Reportar vaga" no footer do `JobDetailDialog`, `<dialog>`
  nativo, textarea opcional (máx 500), estados idle/submitting/success/error
  com `aria-live`.
- Endpoint público `POST /api/v1/public/jobs/{id}/report`; sem persistência.

---

## Component Inventory

| # | Componente / arquivo | Tipo | Phase | Status |
|---|----------------------|------|-------|--------|
| 1 | `frontend/app/(public)/privacidade/page.tsx` | RSC | 9 | **modificar** (remover `<main>`/header/nav próprios, h1/h2, tokens) |
| 2 | `frontend/app/(public)/termos-de-uso/page.tsx` | RSC | 9 | **modificar** (idem) |
| 3 | `frontend/app/(public)/layout.tsx` | RSC | 9 | **modificar** (footer com links "Privacidade" e "Termos de Uso") |
| 4 | `frontend/components/board/JobCard.tsx` | Client | 6 | verificar (badge) |
| 5 | `frontend/components/board/JobDetailDialog.tsx` | Client | 6 | verificar (badge + report) |
| 6 | `frontend/components/board/ReportJobDialog.tsx` | Client | 6 | verificar (estados/aria) |

**Notas:** nenhuma dependência npm nova; nenhum componente novo.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not required (shadcn não inicializado) |
| third-party registries | none | not required |

Nenhum bloco de registry utilizado.

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS (texto legal preservado)
- [ ] Dimension 2 Visuals: PASS (shell único, sem duplicação)
- [ ] Dimension 3 Color: PASS (somente tokens)
- [ ] Dimension 4 Typography: PASS (h1 único, h2 por seção)
- [ ] Dimension 5 Spacing: PASS (max-w-3xl, escala herdada)
- [ ] Dimension 6 Registry Safety: PASS (nenhum registry)

**Approval:** pending

---

*Sources: `06-UI-SPEC.md` (herdado), `04-UI-SPEC.md` (design system), `ROADMAP.md`
Phase 9 success criteria 4–5, `REQUIREMENTS.md` TRST-10..12, `06-04-REVIEW.md`
REV-08 (achado que motivou o delta de UI).*
