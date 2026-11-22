---
phase: 26-acesso-admin-dedicado
plan: 02
subsystem: admin-auth
tags: [nextjs, auth, admin, routing, sessionstorage, privacy]

# Dependency graph
requires:
  - phase: 26-acesso-admin-dedicado
    provides: Dedicated /admin/login route, safe return-to helpers, AdminGuard redirect contract
provides:
  - Extraction-only guarded /admin/paste flow with no embedded login
  - Consistent admin 401 handling redirecting to /admin/login with safe return-to
  - Discreet Política de Privacidade entry point to /admin/login
  - SSR smoke coverage for /admin/login route
affects: [admin-ui, admin-auth, public-privacy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Admin 401 handlers clear session token and hard-navigate via buildAdminLoginHref using current path+search"
    - "Guarded extraction page keeps SSR shell heading and wraps search-param-aware client form in Suspense"

key-files:
  created: []
  modified:
    - frontend/app/admin/paste/ExtractForm.tsx
    - frontend/app/admin/paste/page.tsx
    - frontend/app/admin/review/ReviewQueue.tsx
    - frontend/app/admin/review/EditJobDialog.tsx
    - frontend/app/admin/social-posts/SocialPostsClient.tsx
    - frontend/app/(public)/privacidade/page.tsx
    - frontend/scripts/verify-ssr.ps1

key-decisions:
  - "Paste extraction keeps existing blocklist/summary behavior but delegates auth entirely to AdminGuard and /admin/login redirects"
  - "401 handlers preserve hard navigation and token removal while adding sanitized return-to through buildAdminLoginHref"
  - "Privacy page exposes only a low-sensitivity muted text link labeled 'Acesso administrativo' below the final disclaimer"

patterns-established:
  - "Admin auth-failure recovery: remove nqu_admin_token then window.location.replace(buildAdminLoginHref(current path+search))"
  - "Public-to-admin discovery: discreet muted text link on privacy page, no button/icon/callout"

requirements-completed: [ADMN-01, ADMN-02]

# Metrics
duration: 3 min
completed: 2026-11-22
---

# Phase 26 Plan 02: Admin Flow Alignment Summary

**Extraction-only guarded paste flow, consistent `/admin/login` 401 recovery with safe return-to, and a discreet privacy-page admin entry**

## Performance

- **Duration:** 3 min
- **Started:** 2026-11-22T21:27:06Z
- **Completed:** 2026-11-22T21:30:19Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Refactored `ExtractForm` into an extraction-only guarded client flow, removing embedded login/password/Turnstile and routing expired sessions to `/admin/login` with safe return-to.
- Aligned `ReviewQueue`, `EditJobDialog`, and `SocialPostsClient` 401 handlers to clear `nqu_admin_token` and hard-navigate to `/admin/login` via `buildAdminLoginHref`.
- Added the discreet "Acesso administrativo" link below the Política de Privacidade disclaimer and extended `verify-ssr.ps1` with a tolerant `/admin/login` smoke check while preserving paste checks.

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor ExtractForm to extraction-only guarded flow and align paste page** - `bdc573c` (feat)
2. **Task 2: Align admin 401 redirect handlers to /admin/login** - `c8208f1` (fix)
3. **Task 3: Add discreet admin link on Privacidade page and update SSR smoke script** - `726928c` (feat)

## Files Created/Modified
- `frontend/app/admin/paste/ExtractForm.tsx` - Guarded extraction-only form; removed login/Turnstile/Sair; 401 redirects through `buildAdminLoginHref`.
- `frontend/app/admin/paste/page.tsx` - Preserved SSR shell heading and added Suspense boundary around `ExtractForm`.
- `frontend/app/admin/review/ReviewQueue.tsx` - 401 auth handler now redirects to `/admin/login` with sanitized return-to.
- `frontend/app/admin/review/EditJobDialog.tsx` - 401 auth handler now redirects to `/admin/login` with sanitized return-to.
- `frontend/app/admin/social-posts/SocialPostsClient.tsx` - 401 auth handler now redirects to `/admin/login` with sanitized return-to.
- `frontend/app/(public)/privacidade/page.tsx` - Added discreet muted "Acesso administrativo" link to `/admin/login` below final disclaimer.
- `frontend/scripts/verify-ssr.ps1` - Updated paste PASS message and added tolerant `/admin/login` SSR smoke check.

## Decisions Made
- Kept extraction behavior, blocklist sanitization, and summary UI intact while removing all login responsibilities from paste.
- Used `buildAdminLoginHref` for all touched 401 redirects so return-to targets flow through the existing sanitizer and avoid login loops/open redirects.
- Treated the privacy admin link as low-sensitivity route discovery (no credentials/data exposure), matching ADMN-02 and the threat model acceptance.

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Threat Flags

None - no new network endpoints, auth paths, file access patterns, or schema changes. Redirect targets are sanitized via `buildAdminLoginHref`; 401 handlers clear session token before hard navigation; privacy link exposes only route existence.

## Known Stubs

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 26 plan objectives are implemented in code: dedicated login flow (26-01) plus paste/401 alignment and discreet privacy entry (26-02).
- Manual smoke should confirm logged-out `/admin/paste` redirect, logged-in extraction without login UI, 401 recovery to `/admin/login`, and privacy "Acesso administrativo" navigation.
- Orchestrator can proceed with phase-level verification/transition; STATE.md/ROADMAP.md were intentionally not updated by this executor.

## Self-Check: PASSED

- FOUND: frontend/app/admin/paste/ExtractForm.tsx
- FOUND: frontend/app/admin/paste/page.tsx
- FOUND: frontend/app/admin/review/ReviewQueue.tsx
- FOUND: frontend/app/admin/review/EditJobDialog.tsx
- FOUND: frontend/app/admin/social-posts/SocialPostsClient.tsx
- FOUND: frontend/app/(public)/privacidade/page.tsx
- FOUND: frontend/scripts/verify-ssr.ps1
- FOUND: .planning/phases/26-acesso-admin-dedicado/26-02-SUMMARY.md
- FOUND: bdc573c
- FOUND: c8208f1
- FOUND: 726928c

---
*Phase: 26-acesso-admin-dedicado*
*Completed: 2026-11-22*
