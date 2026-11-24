---
phase: 30
slug: instagram-review-experience
status: draft
shadcn_initialized: false
preset: none
created: 2026-11-24
---

# Phase 30 — UI Design Contract

> Visual and interaction contract for the Instagram review experience. Generated for the Phase 30 UI surface; consumes Phase 29 media/readiness contracts and Phase 30 CONTEXT decisions (D-01..D-09).

**Scope:** Admin review dialog (`frontend/app/admin/review/EditJobDialog.tsx`) — adds a "Post para Instagram" section below "Post para Facebook", with per-job toggle, readiness gating, caption editor/validation, and exact-image preview. Facebook flow remains independent and unchanged.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none — existing Tailwind v4 token system (`frontend/app/admin/admin.css`) |
| Preset | not applicable |
| Component library | none (native HTML + React; existing admin dialog patterns) |
| Icon library | existing `frontend/components/admin/icons.tsx` (reuse `Spinner`; add no new icon dependency unless already present) |
| Font | ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif |

**Source:** `frontend/app/admin/admin.css` `@theme` tokens, `frontend/app/admin/review/EditJobDialog.tsx` patterns, Phase 30 CONTEXT/RESEARCH.

---

## Spacing Scale

Declared values (multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon/text gap in inline badges, tight chip padding |
| sm | 8px | Compact gaps between related controls (`gap-2`) |
| md | 16px | Default block spacing, card/section padding (`p-4`, `mt-4`) |
| lg | 24px | Section separation inside dialog (`mt-6`, `gap-6`) |
| xl | 32px | Major block separation (rare in dialog; use only if needed) |
| 2xl | 48px | Not expected in this dialog |
| 3xl | 64px | Not expected in this dialog |

Exceptions:
- `44px` minimum touch target height for all interactive controls (`min-h-11`) — accessibility/established admin pattern.
- `1px` borders and focus outline (`2px` outline, `2px` offset) — standard UI chrome.
- Existing dialog radius values: `12px` card/section radius, `16px` dialog radius (already tokenized as `--radius-card`, `--radius-dialog`).

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 16px (`text-base`) | 400 regular | 1.5 |
| Label/Helper | 14px (`text-[14px]` / `text-sm`) | 400 regular; 600 semibold for labels/emphasis | 1.5 |
| Section Heading | 20px (`text-[20px]` / `text-xl`) | 600 semibold | 1.25 (`leading-tight`) |
| Meta/Caption Counter | 12px (`text-[12px]`) only for non-critical metadata | 400 regular | 1.5 |

**Rules:**
- Use only these sizes in the Instagram section; do not introduce new ad-hoc sizes.
- Weights limited to 400 and 600 (500 may appear only where already used by existing shared links; prefer 400/600 for new IG UI).
- Dialog title remains existing `text-xl font-semibold leading-tight`.
- Instagram section heading uses same pattern as Facebook: `text-[20px] font-semibold leading-tight text-fg`.

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#0f0a1a` (`canvas`) | Page/dialog background surfaces behind content |
| Secondary (30%) | `#1a1025` (`surface`), `#2a1f3d` (`line`), `#6d5a91` (`line-strong`) | Dialog/card surfaces, borders, secondary structure |
| Accent (10%) | `#8b5cf6` (`accent`), `#a78bfa` (`accent-soft`), `#7c3aed` (`accent-strong`), `#6d28d9` (`accent-strong-hover`) | Reserved for specific interactive/brand elements listed below |
| Destructive | `#f87171` (`danger`), `#fecaca` (`danger-soft`) | Destructive/error states and destructive actions only |

**Accent reserved for:**
- Primary action buttons (filled): "Salvar rascunho" / save actions use `bg-accent-strong` + white text.
- Active toggle/selected mode chips where already established by Facebook section pattern.
- Focus ring: `outline-accent-soft` / `focus-visible:outline-accent-soft`.
- Interactive links/CTAs: `/admin/integracoes` link, "Ver post..." style links use `text-accent-soft` with underline/hover as appropriate.
- Status/info emphasis borders and subtle accent backgrounds (`border-accent`, `bg-[rgba(139,92,246,0.12)]`) for non-destructive informational states.
- Hover border emphasis on interactive containers/buttons (`hover:border-accent`).

**Do NOT use accent for:** normal body text, helper/counter text, disabled/readiness warning containers except existing subtle border conventions, or decorative backgrounds unrelated to IG action/state.

**Destructive reserved for:** validation/blocking errors, failed publish state, disconnect/destructive confirmations. Warning/non-blocking hashtag guidance must **not** use destructive red; use muted/info styling (e.g. `text-fg-muted` or accent-subtle info panel) unless it becomes a blocking validation.

**Contrast/behavior notes:** Preserve existing dark-theme contrast patterns from `admin.css`; maintain visible focus states; respect `prefers-reduced-motion`.

---

## Copywriting Contract

| Element | Copy (pt-BR, prescriptive) |
|---------|----------------------------|
| Section heading | `Post para Instagram` |
| Toggle label | `Publicar no Instagram desta vaga` |
| Toggle helper (off) | `Ative para editar a legenda e revisar a imagem do Instagram desta vaga.` |
| Readiness disabled heading | Use readiness heading from Meta status when available; fallback: `Instagram não está pronto para publicação` |
| Readiness disabled body | `A seção está visível, mas a publicação no Instagram fica desabilitada até a integração estar pronta.` + specific readiness message from backend/status |
| Readiness CTA | `Abrir Integrações` (link to `/admin/integracoes`) |
| Caption label | `Legenda do Instagram` |
| Caption helper | `Links na legenda não são clicáveis. Use "link na bio" como CTA.` |
| Counter | Live `N/2200 caracteres` (e.g. `0/2200 caracteres`) |
| Over-limit error (blocking) | `A legenda do Instagram deve ter no máximo 2200 caracteres.` |
| Hashtag warning (non-blocking, >30) | `Você usou mais de 30 hashtags. Considere reduzir para melhorar a clareza da publicação.` |
| Image preview heading | `Prévia da imagem do Instagram` |
| Image preview loading | `Preparando imagem do Instagram...` |
| Image preview empty/unavailable | `Nenhuma prévia disponível. Ative a publicação no Instagram para preparar a imagem.` |
| Image preview invalid (blocking IG only) | Use `validation.message` from prepare API when present; fallback: `A imagem do Instagram é inválida ou não está disponível. Corrija antes de publicar no Instagram.` |
| Image preview error (request failure) | `Não foi possível preparar a imagem do Instagram. Tente novamente.` |
| IG-blocked save/approve guard | `Corrija a legenda ou a imagem do Instagram antes de salvar/publicar com Instagram ativado. O Facebook e o site não são bloqueados.` |
| Primary CTA (section action) | `Salvar rascunho` (if IG draft persistence uses same draft action pattern) or reuse existing save action; do not invent a conflicting CTA. For initial Phase 30 UI contract, primary in-section action is `Salvar rascunho` when draft editing is present. |
| Secondary action | `Gerar legenda` / `Regenerar legenda` only if Phase 30 implements explicit IG draft generation; default prefill is automatic template C (D-01), so no required generation CTA. |
| Empty state heading (no IG draft yet, toggle on) | `Legenda pronta para revisão` or show prefilled template immediately; no empty-state dead end. |
| Empty state body | Prefill template C automatically (D-01/D-02) with CTA `link na bio` and suggested hashtags `#vagas #emprego #cidade #oportunidade` (cidade normalized). |
| Destructive confirmation | No new destructive action required in Phase 30. If disable-toggle discards unsaved IG draft in future, use: `Desativar publicação no Instagram: as alterações não salvas da legenda serão perdidas.` For now, no destructive confirmation. |

**Copy rules:**
- All user-facing text in pt-BR.
- Always make independence explicit when blocking: Instagram block must not imply Facebook/site blocked.
- Use “link na bio” wording exactly for CTA guidance (D-01/D-09).
- Do not expose internal provider IDs/tokens/secrets.

---

## Component Inventory (Phase 30 scope)

| Component | Location | Responsibility | States |
|-----------|----------|----------------|--------|
| `EditJobDialog` (extend) | `frontend/app/admin/review/EditJobDialog.tsx` | Host Instagram section below Facebook section | default, loading, dirty, saving, auth-expired redirect |
| Instagram Section container | inside `EditJobDialog` | Group IG toggle/status/caption/preview | ready, not-ready-disabled, loading, error |
| Readiness Gate panel | inside IG section | Show disabled explanation + link when IG not ready (D-05) | not_connected/missing_linkage/missing_permissions/needs_reconnect/unknown/null |
| IG Publish Toggle | inside IG section | Per-job “Publicar no Instagram desta vaga” (D-04) | off, on, disabled-by-readiness, disabled-by-busy/frozen policy |
| IG Caption Editor | inside IG section, visible when toggle on | Edit template C caption, live counter, warnings/errors (D-01/D-02/D-08/D-09) | pristine, dirty, over-limit, hashtag-warning, saving, saved, blocked/frozen (if applicable) |
| IG Image Preview | inside IG section, visible when toggle on | Show exact prepared image or clear loading/error/invalid state (D-06/D-07) | idle, loading, ready, invalid, request-error |
| Status/Badge (optional, only if trivial) | `ReviewRow.tsx` / queue | Independent per-platform status display (REVW-01) | none, draft/scheduled/publishing/published/failed/cancelled for IG; keep Facebook independent |

**Implementation note:** Prefer reusing existing Field/Textarea/button/badge patterns from `EditJobDialog.tsx` and admin.css tokens. Do not create a new design system.

---

## Interaction & State Contract

### D-03 Layout / Independence
- Instagram section is rendered **below** Facebook section in the same review dialog.
- Facebook controls/state remain functional regardless of Instagram readiness/validation state.
- Any IG validation failure message must explicitly state Facebook/site are not blocked (D-07).

### D-04 Toggle behavior
- Toggle off: hide caption editor and image preview; show only toggle + minimal helper.
- Toggle on: show caption editor and image preview; trigger image preparation per D-06.
- Toggle state persists per job according to Phase 30 backend contract (planner decision; UI must reflect persisted state).

### D-05 Readiness gating
- If Meta/IG readiness is not `ready` (or status unavailable): section remains visible but disabled.
- Disabled state includes clear pt-BR explanation and link `Abrir Integrações` to `/admin/integracoes`.
- Do not hide the section.

### D-06 Image preview
- Auto-prepare on dialog open when IG already enabled, or immediately on toggle on.
- Show loading state while preparing.
- On success with `validation.valid=true` and `image_url`: show image preview (`<img>` with alt `Prévia da imagem do Instagram`).
- On `validation.valid=false` or missing URL: show validation message and mark IG as blocked for publish/save-with-IG-enabled.

### D-07 Blocking rule
- If IG is enabled and image invalid/unavailable: block IG save/approve/publish actions that would proceed with IG enabled.
- Do **not** block Facebook-only actions or site approval flows.

### D-08/D-09 Caption rules
- Live counter: `N/2200 caracteres` updates on every input change.
- `N > 2200`: show blocking error, disable IG save/submit action for IG-enabled flow; backend also validates.
- Hashtags: count tokens matching `#...` separated by whitespace/start (`/(?:^|\s)#[^\s#]+/g` or equivalent). Warning when count > 30; warning is non-blocking.
- Always show guidance: links in caption are not clickable; use “link na bio”.

---

## Accessibility & UX Guardrails

- All interactive controls >= 44px touch target height.
- Visible focus uses existing `focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft`.
- Error messages use `role="alert"` where appropriate.
- Disabled readiness panel must still expose explanatory text and Integrations link as keyboard-focusable.
- Image preview has meaningful `alt` text; loading/error states are text-first, not color-only.
- Respect `prefers-reduced-motion` (existing admin.css behavior).
- Keep labels associated with inputs (`label htmlFor/id`).

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not required — shadcn not used |
| third-party | none | not applicable |

**Rationale:** Project admin UI uses an existing Tailwind v4 token system in `frontend/app/admin/admin.css` with no `components.json` and no shadcn dependency. Phase 30 extends existing dialog patterns; no third-party registry blocks are introduced.

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
