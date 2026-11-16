---
phase: 18
slug: testes-documentacao-e-fechamento-de-gaps-v11
status: draft
shadcn_initialized: false
preset: none
created: 2026-11-16
---

# Phase 18 — UI Design Contract

> **Scope declaration:** Phase 18 is a **tests, documentação e fechamento/registro de evidências de gaps v1.1** phase (per ROADMAP, CONTEXT, RESEARCH, REQUIREMENTS). It has **no planned frontend/UI implementation work**. This contract records that no new visual/interaction surface is introduced by this phase and must not be used to invent UI scope.

## Design System

| Property | Value |
|----------|-------|
| Tool | none (no UI changes in scope) |
| Preset | N/A — no design-system work planned |
| Component library | N/A (existing project UI unchanged by this phase) |
| Icon library | N/A |

**Notes:** Project stack remains Next.js 16 + Tailwind (see AGENTS.md/STACK). Phase 18 work is limited to automated/manual tests, operational docs/runbooks/checklists, and evidence/traceability artifacts (including backfill/reconciliation). Any UI/UX validation referenced by AUD-04/UIUX-10/11/12 is **evidence/acceptance verification of existing behavior**, not a design contract for new UI.

## Spacing Scale

Declared: N/A — no UI layout or component changes in scope for Phase 18.

Exceptions: none.

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | N/A | N/A | N/A |
| Heading | N/A | N/A | N/A |

Declared: N/A — no UI typography changes in scope. Existing product typography is out of scope to modify here.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | N/A | No new UI surfaces |
| Secondary (30%) | N/A | No new UI surfaces |
| Accent (10%) | N/A | No new UI surfaces |
| Destructive | N/A | No new UI surfaces |

Accent reserved for: N/A

**Constraint (preserved):** Existing project constraints remain unchanged (dark mode minimalista; roxo principal/accent tokens; botão Doações discreto `#facc15`), but Phase 18 does not define or alter UI implementation.

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | N/A — no user-facing UI flow introduced |
| Empty state | N/A |
| Error state | N/A |
| Destructive confirmations | N/A |

**Operational/docs copy (non-UI artifact guidance):** Phase 18 produces developer/operator-facing artifacts (test evidence, runbooks, checklists, handoff docs such as TEST-04/DOC-01/AUD handoffs). These should be explicit, pt-BR where user-facing operational docs require it, objective (pass/fail criteria, commands, prerequisites), and must never include secrets/tokens/credentials.

## Component Inventory

| Component | Source | Usage |
|-----------|--------|-------|
| — | — | No UI components added, removed, or modified in Phase 18 |

**Out of scope:** Frontend/admin/public component changes, new screens, styling refactors, or interaction changes. If a gap closure proves a real UI bug requiring a code fix, that fix must follow existing project conventions but is not pre-contracted here as new UI design work.

## Interaction Contracts

| Interaction | States | Feedback |
|-------------|--------|----------|
| — | — | No UI interactions introduced in Phase 18 |

**Verification-only interactions (existing UI):** Browser/human checks may be required as evidence or handoff for AUD-02/03/04/05 (public board/modal/reveal/search/sort/theme/ads/admin flows). These validate current behavior against requirements; they do not create new interaction contracts.

## Accessibility

N/A for new UI scope. Phase 18 does not introduce UI changes; any accessibility findings discovered during evidence review should be recorded as findings/handoffs or handled as minimal corrective fixes per D-01/D-04 only if required by audited acceptance, preserving existing contracts.

## Responsive Behavior

N/A for new UI scope. Existing mobile-first/public behavior remains governed by prior phases/contracts; Phase 18 performs validation/evidence only.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| none | none | not applicable — no shadcn/registry UI work in scope |

Third-party registries: none declared.

## Third-Party Registry Vetting

Not applicable. No third-party UI registry blocks are declared or permitted by this phase scope.

## Pre-Populated From Upstream

| Source | Decisions/Signals Used |
|--------|-------------------------|
| ROADMAP.md | Phase 18 goal/success criteria: tests, docs, evidence closure; no UI hint |
| 18-CONTEXT.md | Scope limited to TEST-01..04, DOC-01, AUD-01..05; no new product/UI capabilities; preserve existing contracts |
| 18-RESEARCH.md | Primarily verification/evidence/documentation closure; frontend evidence mostly static/manual/handoff unless gaps demand fixes |
| REQUIREMENTS.md | Phase 18 maps to TEST/DOC/AUD requirements only |
| STATE.md / PROJECT.md | Core constraints preserved (no-login public access, social failures non-blocking, secrets backend-only) |
| Existing codebase scout | No Phase 18 UI contract work required; existing design system/config not modified by this phase |

## Open Questions / Handoffs

- **AUD-02/03/04/05 browser-human evidence:** where runtime/browser validation cannot be executed, produce explicit handoff artifacts with objective criteria (per D-02/D-04) rather than claiming UI verification.
- **Corrective UI fixes:** if audit proves a real UI acceptance gap, implement minimal fix under existing project patterns and capture evidence; do not expand scope into redesign.

---
*Phase: 18-testes-documentacao-e-fechamento-de-gaps-v11*
*UI-SPEC created: 2026-11-16 (no UI implementation scope)*
