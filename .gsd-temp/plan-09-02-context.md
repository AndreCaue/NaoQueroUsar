## Plan 09-02: Legal Pages & Trust Surface (Frontend)

**Depends on:** 09-01 (lifecycle/trust proofs must be regression-proof first)

**Objective:** Restructure `/privacidade` and `/termos-de-uso` to render as content inside `(public)/layout.tsx`, convert them to the project's design tokens and heading hierarchy, add pt-BR metadata, add the required "somos apenas meio de divulgação" notice, and link both pages from the footer. Verify without changing the "Vaga revisada" badge and the report flow.

**Purpose:** Criterion 4 is the only success criterion with real missing content; criterion 5's UI already exists but has never been asserted inside a Phase 9 plan. This wave closes the legal/trust gap without touching backend behaviour or rewriting the user-authored legal copy.

**Context (loaded artifacts):**
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-UI-SPEC.md` — Phase 9 UI contract (the authoritative visual/interaction spec)
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-RESEARCH.md` — REV-08 evidence (nested landmarks, non-token colours, orphan page)
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-PATTERNS.md` — `doacoes/page.tsx` as the page analog
- `frontend/app/(public)/layout.tsx` — shell, tokens and footer
- `.planning/ROADMAP.md` Phase 9 criterion 4; `.planning/REQUIREMENTS.md` TRST-10/TRST-12

**Copy rule:** the legal text is user-authored. Re-tag headings, change classes, add `metadata` and add the required notice sentence. Do **not** rewrite, summarise or delete any existing legal sentence.

**Interfaces:**
- `frontend/app/(public)/layout.tsx` (shell — provides the page frame)
  - `<main className="mx-auto w-full max-w-[1120px] flex-1 px-4 py-8 md:px-6">` wraps `{children}`.
  - Header (sticky) and footer already exist.
  - Footer currently renders a single link labeled "Privacidade e termos" to `/privacidade` (lines 61-66).

**Page contract (both legal pages):**
```tsx
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "<Page title> — NaoQueroUsar",
```

**Must-haves:**
1. `/privacidade` and `/termos-de-uso` render inside the single `(public)` shell: no nested `<main>`, `<header>` or `<nav>` and no duplicate NQU header
2. Each legal page has exactly one `<h1>` (page title) and one `<h2>` per numbered section — 13 sections in Privacidade, 10 in Termos de Uso
3. Legal pages use only design tokens (`bg-canvas`, `text-fg`, `text-fg-muted`, `border-line`, `border-line-strong`, `bg-surface`, `text-accent-soft`) — no `bg-gray-900`, `text-white`, `border-gray-700` or `text-accent-strong`
4. The required notice "Somos apenas meio de divulga" exists verbatim in `/termos-de-uso`
5. Both legal pages export pt-BR `metadata` (title + description) and preserve 100% of the existing legal copy
6. The public footer links to both `/privacidade` ('Privacidade') and `/termos-de-uso` ('Termos de Uso')
7. The "Vaga revisada" badge is rendered only from `status === "published"` and 'Reportar vaga' still opens the report dialog

**Artifacts:**
- `frontend/app/(public)/privacidade/page.tsx` — 13-section privacy policy inside the shared shell, one h1, token-only styling and metadata
- `frontend/app/(public)/termos-de-uso/page.tsx` — 10-section terms of use, required intermediary notice, metadata and tokens
- `frontend/app/(public)/layout.tsx` — Footer with separate Privacidade and Termos de Uso links

**Key links:**
- `frontend/app/(public)/privacidade/page.tsx` → `frontend/app/(public)/layout.tsx` — page renders content only; the layout owns `<main>`, header and footer
- `frontend/app/(public)/termos-de-uso/page.tsx` → `scripts/verify-deploy.ps1` — the exact notice phrase added here is asserted by the (tightened) smoke gate in plan 09-03
- `frontend/components/board/JobDetailDialog.tsx` → `frontend/components/board/ReportJobDialog.tsx` — the report dialog remains wired to the 'Reportar vaga' button