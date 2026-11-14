---
phase: 10-rebranding-launch-preparation-empreganoix
plan: 01
subsystem: ui
tags: [nextjs, metadata, branding, frontend]

# Dependency graph
requires:
  - phase: 09-lifecycle-trust-legal-launch-completeness
    provides: stable public/admin/legal frontend surfaces to rebrand
provides:
  - EmpregaNoix wordmark, metadata, and legal/contact copy across frontend touchpoints
  - Updated WhatsApp application template and .env.example brand label
  - File-based SVG favicon and metadata wiring for empreganoix.vercel.app
affects: [10-02, 10-03, 10-04, deploy, launch]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Next.js file-based metadata via app/icon.svg with metadataBase/icons/openGraph"

key-files:
  created:
    - frontend/app/icon.svg
  modified:
    - frontend/app/(public)/layout.tsx
    - frontend/app/admin/layout.tsx
    - frontend/app/(public)/doacoes/page.tsx
    - frontend/lib/contacts.ts
    - frontend/.env.example
    - frontend/app/(public)/privacidade/page.tsx
    - frontend/app/(public)/termos-de-uso/page.tsx

key-decisions:
  - "Kept slogan and all @theme color tokens unchanged while renaming brand strings"
  - "Used SVG favicon and omitted optional PNG apple/OG assets (fallback accepted per plan) without blocking metadata integration"

patterns-established:
  - "Brand identity strings centralized in layouts, legal pages, contact template, and env example"

requirements-completed: [BRND-01, BRND-02, BRND-03]

# Metrics
duration: 2min
completed: 2026-11-14
---

# Phase 10 Plan 01: Frontend Rebranding Summary

**EmpregaNoix wordmark, metadata, legal copy, and WhatsApp template shipped across the frontend with SVG favicon metadata and preserved slogan/theme tokens**

## Performance

- **Duration:** 2 min
- **Started:** 2026-11-14T17:56:36Z
- **Completed:** 2026-11-14T17:58:47Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Rebranded public/admin layouts, doações page, WhatsApp template, and frontend env example to EmpregaNoix with `metadataBase`/icons/openGraph pointing to `https://empreganoix.vercel.app`.
- Rebranded privacy and terms pages (titles, descriptions, controller copy, and contact channel to `empreganoix@outlook.com`) while preserving the legal text and LGPD notice.
- Integrated brand asset fallback by adding `frontend/app/icon.svg` and wiring `/icon.svg`; optional PNG assets were not generated and deploy is unblocked per plan fallback.

## Task Commits

Each task was committed atomically:

1. **Task 1: Renomear wordmark, metadata e WhatsApp template (layouts + doações + contacts + .env.example)** - `334d900` (feat)
2. **Task 2: Renomear páginas legais (privacidade + termos-de-uso) — marca e canal de contato** - `8cbb2cb` (feat)
3. **Task 3: Integrar assets de marca (favicon SVG + PNG opcionais) via metadata, com fallback de wordmark** - `6676bf5` (feat)

**Plan metadata:** recorded in final docs/state commit for this plan execution

## Files Created/Modified
- `frontend/app/icon.svg` - Textual SVG favicon used by Next.js file-based metadata.
- `frontend/app/(public)/layout.tsx` - Public title/wordmark/copyright, metadataBase, icon/openGraph metadata.
- `frontend/app/admin/layout.tsx` - Admin title and wordmark updated to EmpregaNoix.
- `frontend/app/(public)/doacoes/page.tsx` - Donations page title and body brand copy updated.
- `frontend/lib/contacts.ts` - WhatsApp prefilled message references EmpregaNoix.
- `frontend/.env.example` - Frontend env header label updated to EmpregaNoix.
- `frontend/app/(public)/privacidade/page.tsx` - Privacy policy brand/controller/contact and metadata updated.
- `frontend/app/(public)/termos-de-uso/page.tsx` - Terms of use brand/controller/contact and metadata updated.

## Decisions Made
- Preserved the slogan `Procurar um emprego, não deve dar trabalho` verbatim in public and admin layouts and left `@theme` color tokens (`#8b5cf6`, `#a78bfa`, `#facc15`) unchanged (BRND-02, BRND-03).
- Accepted the D-05 fallback: integrated SVG favicon and omitted optional `apple-icon.png`/`opengraph-image.png` references because PNG assets were not generated.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `grep`/`test` CLI utilities were unavailable in the Windows PowerShell environment; acceptance checks were completed with PowerShell-native file/search commands. Lint and build completed successfully (exit 0; pre-existing warnings only).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Frontend brand/content surface for BRND-01/02/03 is ready for subsequent Phase 10 plans (backend/docs/infra rename, host/CORS alignment, and deploy smoke gate).
- Optional PNG brand assets (`icon.png`, `apple-icon.png`, `opengraph-image.png`) remain a visual follow-up; sharing will rely on title/description until OG image is added.

## Self-Check: PASSED

- FOUND: frontend/app/icon.svg
- FOUND: frontend/app/(public)/layout.tsx
- FOUND: frontend/app/admin/layout.tsx
- FOUND: frontend/app/(public)/doacoes/page.tsx
- FOUND: frontend/lib/contacts.ts
- FOUND: frontend/.env.example
- FOUND: frontend/app/(public)/privacidade/page.tsx
- FOUND: frontend/app/(public)/termos-de-uso/page.tsx
- FOUND: .planning/phases/10-rebranding-launch-preparation-empreganoix/10-01-SUMMARY.md
- FOUND: 334d900
- FOUND: 8cbb2cb
- FOUND: 6676bf5

---
*Phase: 10-rebranding-launch-preparation-empreganoix*
*Completed: 2026-11-14*
