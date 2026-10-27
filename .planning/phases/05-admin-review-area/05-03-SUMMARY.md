---
phase: 05-admin-review-area
plan: 03
subsystem: admin-paste
tags:
  - tailwind-v4
  - migration
  - admin
  - revw-01
dependency_graph:
  requires:
    - 05-02
  provides:
    - ExtractForm migrado para Tailwind v4
    - Paste page sob layout admin
  affects: []
tech-stack:
  added: ["Tailwind CSS v4 utilities", "next-turnstile 1.0.7"]
  patterns: ["CSS-first Tailwind v4 with @theme tokens", "Route-scoped admin.css"]
key-files:
  created: []
  modified:
    - frontend/app/admin/paste/ExtractForm.tsx
    - frontend/app/admin/paste/page.tsx
    - frontend/app/admin/paste/globals-admin.css (deleted)
decisions:
  - Migrated ExtractForm to Tailwind v4 using route-scoped admin.css tokens, removing globals-admin.css dependency
  - Updated page.tsx to maintain h1 "Admin — Colar vagas" under admin layout shell
  - Removed globals-admin.css; Turnstile wrapper uses overflow-hidden max-w-full (no transform/scale)
metrics:
  duration: -
  completed-date: Mon Oct 26 2026
---

# Phase 05 Plan 03: Admin Review Area Summary

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Tailwind class mappings for error states**
- **Found during:** task 1 ExtractForm migration
- **Issue:** Error banner `bg rgba(248,113,113,.10) border border-danger text-danger-soft rounded-lg p-3` needed proper Tailwind v4 arbitrary value syntax
- **Fix:** Used `bg-[rgba(248,113,113,0.1)]` Tailwind v4 arbitrary color syntax instead of CSS `bg rgba(...)`
- **Files modified:** `frontend/app/admin/paste/ExtractForm.tsx`
- **Commit:** extracted form Tailwind migration

**2. [Rule 2 - Critical] Error banner styles migrated to Tailwind v4**
- **Found during:** task 1 ExtractForm migration
- **Issue:** Error banner background/border classes needed to work without globals-admin.css
- **Fix:** Migrated `bg-danger`, `text-danger-soft`, `border-danger` to Tailwind color config from admin.css theme
- **Files modified:** `frontend/app/admin/paste/ExtractForm.tsx`
- **Commit:** extracted form Tailwind migration

### Auth gates
- None encountered — Turnstile credentials preserved, `nqu_admin_token` session storage maintained

### Stub tracking
- No stubs detected — all data paths properly wired

### Threat surface scan
- No new security-relevant surfaces introduced outside the plan's threat model
- Trust boundaries preserved: browser → paste page via Turnstile + JWT; backend authoritative

---

## Summary of Changes

### Task 1: Migrate ExtractForm to Tailwind v4
- **File:** `frontend/app/admin/paste/ExtractForm.tsx`
- **Changes:**
  - Removed `import "./globals-admin.css"` 
  - Replaced `.admin-page` with `max-w-[720px] mx-auto p-6 bg-surface border border-line rounded-lg`
  - Replaced `.admin-panel` with `space-y-8` main content wrapper
  - Replaced `.admin-btn` with `min-h-11 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white hover:bg-accent-strong-hover`
  - Replaced `.admin-turnstile` with `overflow-hidden max-w-full` (no transform/scale)
  - Replaced `.admin-error` with `bg-[rgba(248,113,113,0.1)] border border-danger text-danger-soft rounded-lg p-3`
  - Labels: `text-sm text-fg-muted`
  - Inputs: `h-12 w-full rounded-lg border border-line-strong bg-canvas px-3 text-base text-fg placeholder:text-fg-muted focus-visible outline-accent-soft`
  - Textarea: `min-h-[96px] resize-y w-full rounded-lg border border-line-strong bg-canvas px-3 text-base text-fg placeholder:text-fg-muted`
  - Preserved all logic: state, useEffect sessionStorage, resetTurnstile, handleLogin, handleSubmit, handleReset, isLoginDisabled/isSubmitDisabled
  - Preserved Turnstile props: key={turnstileKey}, siteKey, action="login", theme="dark", appearance="always", onVerify/onExpire/onError

### Task 2: Update page.tsx and remove globals-admin.css
- **File:** `frontend/app/admin/paste/page.tsx`
- **Changes:**
  - Removed `<main>` wrapper (admin layout provides main wrapper)
  - Kept h1 "Admin — Colar vagas" (Heading)
  - Kept ExtractForm import and rendering
  - Removed any globals-admin.css references (none remained after task 1)
- **File:** `frontend/app/admin/paste/globals-admin.css`
- **Changes:** Deleted the file

---

## Verification

- TypeScript compilation: passed (no errors from changed files)
- Next.js build: compiled successfully ("Compiled successfully in 11.4s")
- Acceptance criteria met:
  - [x] No `globals-admin.css` import in ExtractForm.tsx
  - [x] Turnstile wrapper has `overflow-hidden max-w-full`
  - [x] `action="login"` present in Turnstile props
  - [x] `nqu_admin_token` present in component
  - [x] `frontend/app/admin/paste/globals-admin.css` does not exist
  - [x] `ExtractForm` referenced in page.tsx

---

## Commits

| task | Name | Commit |
|------|------|--------|
| 1 | Migrate ExtractForm to Tailwind v4 | 4c84a4c |
| 2 | Update page.tsx and remove globals-admin.css | 9cdd6f9 |