---
phase: 26-acesso-admin-dedicado
plan: 01
subsystem: admin-auth
tags: [nextjs, auth, turnstile, admin, routing, sessionstorage]

# Dependency graph
requires:
  - phase: 01-fundacao-extracao
    provides: Admin auth endpoint, sessionStorage token pattern, Turnstile login flow
provides:
  - Dedicated /admin/login route with focused Turnstile login UI
  - Safe admin return-to sanitization/build helpers
  - AdminGuard redirect to /admin/login with sanitized next
  - Logout hard navigation to /admin/login
  - Pathname-aware AdminChrome hiding admin nav on login
affects: [26-02, admin-ui, admin-auth]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sanitize untrusted return-to params to internal /admin paths before router.replace"
    - "Wrap useSearchParams-dependent guarded client content in Suspense boundaries"
    - "Keep admin shell chrome as client component so layout remains server-owned with metadata/providers"

key-files:
  created:
    - frontend/lib/adminReturnTo.ts
    - frontend/lib/adminReturnTo.test.ts
    - frontend/app/admin/login/page.tsx
    - frontend/components/admin/AdminLoginForm.tsx
    - frontend/components/admin/AdminChrome.tsx
  modified:
    - frontend/app/admin/layout.tsx
    - frontend/components/admin/AdminGuard.tsx
    - frontend/components/admin/LogoutButton.tsx
    - frontend/app/admin/page.tsx
    - frontend/app/admin/review/page.tsx
    - frontend/app/admin/social-posts/page.tsx

key-decisions:
  - "Return-to sanitization accepts only /admin paths, rejects protocol-relative/backslash/control chars, and maps /admin/login* to /admin to prevent redirect loops"
  - "AdminGuard computes current admin path with search params and redirects via buildAdminLoginHref; useSearchParams required Suspense boundaries on guarded callers"
  - "AdminChrome moved to client component for pathname-aware nav hiding while AdminLayout stays server component with metadata/viewport/ToastProvider"

patterns-established:
  - "Return-to helper: use sanitizeAdminReturnTo/buildAdminLoginHref for any admin login redirect target"
  - "Guarded admin pages: render useAdminGuard callers under Suspense when guard reads search params"

requirements-completed: [ADMN-01]

# Metrics
duration: 6 min
completed: 2026-11-22
---

# Phase 26 Plan 01: Dedicated Admin Login Summary

**Dedicated `/admin/login` with Turnstile auth, safe admin-only return-to redirects, and pathname-aware admin chrome that hides nav while logged out**

## Performance

- **Duration:** 6 min
- **Started:** 2026-11-22T18:18:35-03:00
- **Completed:** 2026-11-22T18:24:19-03:00
- **Tasks:** 4
- **Files modified:** 11

## Accomplishments
- Added pure `adminReturnTo` helpers with unit tests covering valid admin paths, login-loop prevention, and rejection of external/protocol-relative/backslash/non-admin targets.
- Created focused `/admin/login` route and `AdminLoginForm` reusing the existing Turnstile + `loginAdmin` + sessionStorage token contract, with sanitized `next` redirect behavior.
- Split admin chrome into pathname-aware `AdminChrome`, keeping layout server-owned while hiding Publicações/Integrações/Sair on the login route.
- Aligned `AdminGuard` and `LogoutButton` to `/admin/login`, and added Suspense boundaries to guarded admin pages required by `useSearchParams`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create adminReturnTo helper with unit tests** - `39bb4a5` (test), `80e6316` (feat)
2. **Task 2: Build dedicated /admin/login page, AdminLoginForm, and pathname-aware AdminChrome** - `343a0fe` (feat)
3. **Task 3: Align AdminGuard and LogoutButton to /admin/login with safe return-to** - `f6acb44` (feat)
4. **Task 4: Make all useAdminGuard callers Suspense-safe for useSearchParams** - `02e11b4` (fix)

**Plan metadata:** recorded in final docs commit for this plan.

_Note: Task 1 used TDD and produced RED + GREEN commits._

## Files Created/Modified
- `frontend/lib/adminReturnTo.ts` - Pure helpers to sanitize admin return-to targets and build `/admin/login?next=...` URLs.
- `frontend/lib/adminReturnTo.test.ts` - Vitest coverage for safe/unsafe return-to cases and login loop prevention.
- `frontend/app/admin/login/page.tsx` - Dedicated admin login route with Suspense boundary for search-param reading form.
- `frontend/components/admin/AdminLoginForm.tsx` - Client login form with Turnstile, password, session redirect, and safe post-login navigation.
- `frontend/components/admin/AdminChrome.tsx` - Pathname-aware admin shell that hides admin nav on `/admin/login`.
- `frontend/app/admin/layout.tsx` - Server layout delegating chrome while preserving metadata, viewport, and ToastProvider.
- `frontend/components/admin/AdminGuard.tsx` - Redirects missing token to sanitized `/admin/login?next=...`.
- `frontend/components/admin/LogoutButton.tsx` - Clears token and hard-navigates to `/admin/login`.
- `frontend/app/admin/page.tsx` - Suspense-wrapped guarded dashboard content.
- `frontend/app/admin/review/page.tsx` - Suspense-wrapped ReviewQueue for guard search-param compatibility.
- `frontend/app/admin/social-posts/page.tsx` - Suspense-wrapped SocialPostsClient for guard search-param compatibility.

## Decisions Made
- Used a dedicated pure helper (`adminReturnTo`) as the single sanitization point for login redirects, preventing open redirects and `/admin/login` loops.
- Kept the auth contract unchanged by reusing `loginAdmin(password, cfToken)` and `nqu_admin_token` sessionStorage behavior.
- Kept `AdminLayout` server-owned for metadata/providers and moved pathname-aware nav rendering to a client `AdminChrome`.

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Threat Flags

None - no new network endpoints, auth paths, file access patterns, or schema changes beyond planned client-side redirect hardening. Backend auth authority remains unchanged.

## Known Stubs

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- ADMN-01 login foundation is in place: dedicated login route, safe return-to, guard/logout alignment, and admin chrome separation.
- Ready for `26-02-PLAN.md`, which can remove remaining paste-page login coupling and add the discreet privacy-page admin entry.
- Manual smoke should confirm unauthenticated `/admin/review` redirect, login return-to, authenticated `/admin/login` redirect, and logout landing on `/admin/login`.

## Self-Check: PASSED

- FOUND: frontend/lib/adminReturnTo.ts
- FOUND: frontend/lib/adminReturnTo.test.ts
- FOUND: frontend/app/admin/login/page.tsx
- FOUND: frontend/components/admin/AdminLoginForm.tsx
- FOUND: frontend/components/admin/AdminChrome.tsx
- FOUND: frontend/app/admin/layout.tsx
- FOUND: frontend/components/admin/AdminGuard.tsx
- FOUND: frontend/components/admin/LogoutButton.tsx
- FOUND: frontend/app/admin/page.tsx
- FOUND: frontend/app/admin/review/page.tsx
- FOUND: frontend/app/admin/social-posts/page.tsx
- FOUND: .planning/phases/26-acesso-admin-dedicado/26-01-SUMMARY.md
- FOUND: 39bb4a5
- FOUND: 80e6316
- FOUND: 343a0fe
- FOUND: f6acb44
- FOUND: 02e11b4

---
*Phase: 26-acesso-admin-dedicado*
*Completed: 2026-11-22*
