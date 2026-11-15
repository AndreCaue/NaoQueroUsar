---
phase: 09-lifecycle-trust-legal-launch-completeness
plan: 02
subsystem: ui
tags: [nextjs, tailwind, legal, lgpd, accessibility, tokens]

# Dependency graph
requires:
  - phase: 09-01
    provides: lifecycle and trust proofs baseline for Phase 9 legal/launch completion
provides:
  - Public legal pages (/privacidade, /termos-de-uso) rendered inside shared (public) shell with token-only styling
  - Required LGPD/intermediary notice present verbatim in Termos de Uso
  - Footer links to both legal pages and verified published-only trust/report UI wiring
affects: [09-03 launch readiness, public trust surface, legal compliance]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Public legal pages as RSC content-only inside (public) layout (no nested landmarks)"
    - "Token-only typography/classes for public legal content with one h1 and h2-per-section hierarchy"

key-files:
  created: []
  modified:
    - frontend/app/(public)/privacidade/page.tsx
    - frontend/app/(public)/termos-de-uso/page.tsx
    - frontend/app/(public)/layout.tsx

key-decisions:
  - "Preserved all existing legal copy while restructuring markup, headings, metadata, and design tokens"
  - "Kept EmpregaNoix-branded metadata/wording consistent with current product naming while satisfying plan acceptance strings"

patterns-established:
  - "Legal pages export pt-BR metadata and rely on the shared public shell for header/footer/main"

requirements-completed: [TRST-10, TRST-12]

# Metrics
duration: 12min
completed: 2026-11-15
---

# Phase 09 Plan 02: Legal Pages & Trust Surface Summary

**Tokenized public legal pages with the required intermediary notice, shared-shell structure, and verified published-only trust/report UI wiring**

## Performance

- **Duration:** 12 min
- **Started:** 2026-11-15T01:10:00Z
- **Completed:** 2026-11-15T01:22:00Z
- **Tasks:** 4
- **Files modified:** 2

## Accomplishments
- Restructured `/privacidade` into the shared `(public)` shell with one `<h1>`, 13 token-styled `<h2>` sections, pt-BR metadata, and preserved legal copy.
- Restructured `/termos-de-uso` with 10 token-styled sections, next/link privacy navigation, pt-BR metadata, and the required "Somos apenas meio de divulgação de vagas" notice after section 1.
- Confirmed footer already links to both `/privacidade` and `/termos-de-uso` with 44px touch targets, and verified "Vaga revisada" badge/report dialog wiring without UI changes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Restructure /privacidade into the shared shell with one h1 and 13 h2 sections** - `6930cc8` (feat)
2. **Task 2: Restructure /termos-de-uso and add the required intermediary notice** - `537c2dd` (feat)
3. **Task 3: Link both legal pages from the public footer** - no code change required (already compliant)
4. **Task 4: Verify the "Vaga revisada" badge and the report dialog wiring (no feature change)** - verification only, no commit

## Files Created/Modified
- `frontend/app/(public)/privacidade/page.tsx` - Rebuilt as content-only article with metadata, token classes, and 13 legal sections preserving text.
- `frontend/app/(public)/termos-de-uso/page.tsx` - Rebuilt as content-only article with metadata, required intermediary notice, 10 sections, and tokenized internal link.
- `frontend/app/(public)/layout.tsx` - Verified compliant footer links to both legal pages (no changes).

## Decisions Made
- Preserved every existing legal sentence/wording in both pages while applying required structural and styling changes.
- Kept the project’s current EmpregaNoix branding in metadata/titles where present, satisfying acceptance criteria that require the page titles to contain the legal page names.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- PowerShell does not provide `tail`; lint/build verification commands were re-run without piping to `tail` to capture results. Lint completed with 6 pre-existing warnings in unrelated files (exit 0) and build succeeded.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- TRST-10 legal surface is structurally and visually aligned with the public shell and includes the required intermediary notice for downstream smoke-gate tightening.
- TRST-12 trust/report UI wiring is verified intact; ready for Phase 09-03 launch-readiness hardening and deploy checks.

## Self-Check: PASSED

- FOUND: frontend/app/(public)/privacidade/page.tsx
- FOUND: frontend/app/(public)/termos-de-uso/page.tsx
- FOUND: frontend/app/(public)/layout.tsx
- FOUND: .planning/phases/09-lifecycle-trust-legal-launch-completeness/09-02-SUMMARY.md
- FOUND: 6930cc8
- FOUND: 537c2dd

---
*Phase: 09-lifecycle-trust-legal-launch-completeness*
*Completed: 2026-11-15*
