---
phase: 06-lifecycle-trust-legal-launch
plan: 03
subsystem: legal/trust
tags: [legal, lgpd, footer, rsc, public-pages]

# Dependency graph
requires:
  - phase: 06-lifecycle-trust-legal-launch
    plan: 02
    provides: baseline /privacidade needs none of the 06-02 code; executed after wave 2 in this branch
  - phase: 04-public-board-frontend
    provides: public.css tokens (@theme), (public) layout shell, doacoes page patterns
provides:
  - "/privacidade RSC with 3 sections: 1. Privacidade, 2. Termos de Uso, 3. Aviso de Intermediário e LGPD (TRST-03, D-07)"
  - "Footer link 'Privacidade e termos' in app/(public)/layout.tsx pointing to /privacidade"
affects: [06-04-deploy-and-launch, phase-6-verification, human legal review task]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single legal page with âncoras; RSC only, no client JS"
    - "Placeholders explicit where legal drafting requires a human (D-07) — never fake legal authority"

key-files:
  created:
    - frontend/app/(public)/privacidade/page.tsx
  modified:
    - frontend/app/(public)/layout.tsx

key-decisions:
  - "Single /privacidade page with 3 anchored sections (D-07 recommended structure); no separate /termos route"
  - "Legal copy is general informative text marked as pending human review; contact e-mail left as explicit placeholder instead of an invented address"
  - "Anchor navigation nav with surface/line tokens; scroll-mt-24 so sticky header does not cover section tops"

patterns-established:
  - "Public legal RSC: h1 + optional anchor nav + h2 sections + muted footer note (no forms, no client JS)"

requirements-completed: [TRST-03]

# Metrics
duration: ~4min
completed: 2026-11-02
---

# Phase 6 Plan 03: Legal Pages Summary

**Single /privacidade page with the 3 required legal sections (PT-BR) and a token-consistent footer link from the public shell**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-11-02T20:43:09Z
- **Completed:** 2026-11-02T20:47:09Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- `/privacidade` is a static public RSC (○ prerendered, 127 B): h1 "Privacidade, Termos e Aviso Legal", anchor nav, sections "1. Privacidade", "2. Termos de Uso", "3. Aviso de Intermediário e LGPD".
- Reutilizando o shell público: max-width 860px, mesmas cores/tokens (`surface`, `line`, `fg`, `fg-muted`, `accent-soft`), folha de estilo única (public.css).
- Footer note verbatim from UI-SPEC: "Esta página contém informações gerais. Para questões jurídicas específicas, consulte um advogado."
- PT-BR metadata: title "Privacidade, Termos e Aviso Legal — NaoQueroUsar" and description covering privacidade, termos e aviso LGPD/intermediário.
- Footer link "Privacidade e termos" added in the public layout, Next.js Link, 44px min touch target, wraps without breaking the mobile layout.

## Task Commits

1. **Task 1: Página legal única com 3 seções** — `b3fc283` (feat)
2. **Task 2: Link "Privacidade e termos" no footer** — `70f6198` (feat)

## Files Created/Modified

- `frontend/app/(public)/privacidade/page.tsx` *(new)* — the legal page
- `frontend/app/(public)/layout.tsx` — replaced the Phase 6 placeholder comment with the footer link

## Decisions Made

- **Single page, not /termos too** — UI-SPEC/D-07 explicitly recommends one page with sections.
- **No invented contact e-mail** — the planned contact address would have been fabricated; the page states the address is pending official definition before launch instead.
- **Legal drafting stays human** (D-07) — section text is general/purposefully generic, marked with italic "[Redação jurídica detalhada pendente…]" placeholders; no claims of legal accuracy are made.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] Removed invented contact e-mail**
- **Found during:** Task 1
- **Issue:** First draft included `privacidade@naoquerousar.com.br`, an unverified address that could misdirect LGPD requests and would be an unverified public claim.
- **Fix:** Replaced with an explicit "[E-mail de contato para privacidade: pendente…]" placeholder; contact section now points to the site footer/official launch channel until a human defines the address.
- **Files modified:** frontend/app/(public)/privacidade/page.tsx
- **Commit:** b3fc283

**2. [Rule 1 - Bug] Copy grammar fix**
- **Found during:** Task 1
- **Issue:** "Sem verificação garantias" was grammatically broken.
- **Fix:** Renamed heading to "Sem garantia de verificação".
- **Files modified:** frontend/app/(public)/privacidade/page.tsx
- **Commit:** b3fc283

## Issues Encountered

- PowerShell does not accept bash `VAR=$(…)` — timing variables were set in PowerShell syntax (same workaround as 06-02).
- Build/lint warn about multiple lockfiles (repo root vs frontend) — pre-existing, out of scope, left untouched.

## User Setup Required

None. Static content only.

## Known Stubs

- **Privacy contact e-mail** — `privacidade/page.tsx` §3 "Contato": deliberately a placeholder; a human must define the official LGPD e-mail before launch (tracked in the launch checklist / human legal review task).
- **Legal drafting** — all three sections contain "[Redação jurídica detalhada pendente…]" markers. This is intentional per D-07 (human legal review before launch) and does not block TRST-03 structural acceptance.
- **Copyright year** — footer shows 2026 (as before).

## Threat Flags

None — fully static, no endpoints, no input, no personal data handling added.

## Verification

- `npx tsc --noEmit` → clean (exit 0).
- `npm run lint` → "No ESLint warnings or errors" (deprecation notice for `next lint` is pre-existing).
- `npm run build` → success; `/privacidade` generated as static page (127 B, First Load JS 102 kB).
- Plan verify greps: "Privacidade, Termos e Aviso Legal" (page.tsx L13), "Aviso de Intermediário" (L33), "Privacidade e termos" + `/privacidade` (layout.tsx L62/L65).
- No modifications to `.planning/STATE.md` or `.planning/ROADMAP.md`; no file deletions in task commits.

## Self-Check: PASSED

- Created files exist: `frontend/app/(public)/privacidade/page.tsx` ✓
- Commits exist: `b3fc283`, `70f6198` ✓
- Footer link points to `/privacidade` ✓
- STATE.md / ROADMAP.md untouched ✓

---
*Phase: 06-lifecycle-trust-legal-launch*
*Completed: 2026-11-02*
