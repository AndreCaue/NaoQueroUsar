---
phase: 04-public-board-frontend
plan: 01
subsystem: ui
tags: [nextjs, tailwindcss, postcss, route-group, dark-mode, rsc]

# Dependency graph
requires:
  - phase: 03-contact-reveal-anti-spam
    provides: frontend/lib/api.ts fetch pattern, next-turnstile wiring, admin plain-CSS route that must stay untouched
provides:
  - Route-scoped Tailwind v4 setup (public.css with the approved @theme tokens, @tailwindcss/postcss)
  - (public) route group with the public shell (skip link, sticky header, Doações entry point, footer)
  - Interim `/` page inside the shell and a static `/doacoes` page
  - Root layout importing globals.css with theme-color/color-scheme metadata
affects: [04-02, 04-03, 04-04, 04-05, 04-06, phase-6-legal-links-pix]

# Tech tracking
tech-stack:
  added:
    - tailwindcss 4.3.3
    - "@tailwindcss/postcss 4.3.3"
  patterns:
    - "Tailwind v4 imported only by app/(public)/layout.tsx (route-scoped, Preflight never reaches /admin/*)"
    - "Design tokens declared once as CSS variables in @theme, consumed as Tailwind utilities (bg-canvas, text-fg-muted, text-donate)"
    - "next/link instead of raw <a> for internal routes (required by @next/next/no-html-link-for-pages)"

key-files:
  created:
    - frontend/postcss.config.mjs
    - frontend/app/(public)/public.css
    - frontend/app/(public)/layout.tsx
    - frontend/app/(public)/page.tsx
    - frontend/app/(public)/doacoes/page.tsx
  modified:
    - frontend/package.json
    - frontend/package-lock.json
    - frontend/app/layout.tsx
    - frontend/app/globals.css
    - frontend/tsconfig.json

key-decisions:
  - "Tailwind v4 tokens live verbatim in public.css @theme; #8b5cf6 is brand-only, #a78bfa text/focus, #7c3aed reserved for filled CTAs with white text"
  - "Internal navigation uses next/link (renders the same <a href>) because next lint rejects raw anchors to app routes"
  - "globals.css stays free of Tailwind and is now imported by the root layout; public.css is imported only by the route-group layout"
  - "Next 15 wrote target ES2017 into tsconfig.json during lint; kept as a one-line diff so repeat lint runs are stable"

patterns-established:
  - "Route-group CSS isolation: public.css -> (public)/layout.tsx only; globals.css (base) -> root layout"
  - "Proof of isolation: built HTML for / and /doacoes links the canvas CSS chunk; /admin/paste links only globals + admin CSS"

requirements-completed: [UIUX-01, UIUX-02]

# Metrics
duration: 7min
completed: 2026-10-26
---

# Phase 4 Plan 1: Public Route Group and Tailwind v4 Foundation Summary

**Tailwind v4 wired through PostCSS with the approved dark-purple @theme tokens, plus a `(public)` route group whose shell (skip link, 64px sticky header, yellow Doações entry, footer) serves `/` and a real static `/doacoes` while `/admin/paste` keeps its plain CSS.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-26T21:48:40Z
- **Completed:** 2026-10-26T21:55:37Z
- **Tasks:** 3
- **Files modified:** 11 (5 created, 5 modified, 1 deleted)

## Accomplishments

- Installed `tailwindcss@4.3.3` and `@tailwindcss/postcss@4.3.3` at exact pins under `frontend/node_modules`, with `postcss.config.mjs` using the v4 plugin (not the v3 `tailwindcss: {}` recipe) and the frontend lockfile committed for reproducibility.
- Created `app/(public)/public.css` carrying the 15 approved UI-SPEC tokens verbatim, a base layer (`color-scheme`, body surface, `:focus-visible` 2px `#a78bfa` ring, `prefers-reduced-motion` kill switch), and imported it only from the route-group layout.
- Built the public shell: skip link (`Ir para as vagas` → `#vagas`), sticky 64px header with accent-dot wordmark, slogan at `≥768` only, yellow `Doações` entry (min 44×44, hover-only tint), `<main>` at 1120px, footer with copyright + slogan and space reserved for Phase 6 legal links.
- Moved `/` into the route group (deleting the duplicate root `app/page.tsx`) and added the honest static `/doacoes` page; `/admin/paste` still builds and renders unchanged.
- Proved CSS isolation from the build output: `index.html`/`doacoes.html` link `14b42977789ac17d.css` (contains `--color-canvas`), while `admin/paste.html` links only `b3bc5a64894136ef.css` (globals) + `7f10d5f8f9a1f9ae.css` (admin) — Tailwind Preflight never reaches the admin (T-04-01).

## Task Commits

Each task was committed atomically:

1. **task 1: install Tailwind v4 and wire PostCSS** - `d70a22f` (chore)
2. **task 2: create route-scoped theme and public shell** - `4017c0c` (feat)
3. **task 3: move `/` into `(public)` and add the donations page** - `45a3ce8` (feat)

**Plan metadata:** see the docs commit created after this summary.

## Files Created/Modified

- `frontend/package.json` - added `tailwindcss`/`@tailwindcss/postcss` pinned at `4.3.3`; Next/React/next-turnstile untouched
- `frontend/package-lock.json` - first committed lockfile, pins reproducible
- `frontend/postcss.config.mjs` - `{ "@tailwindcss/postcss": {} }` v4 plugin
- `frontend/app/(public)/public.css` - `@import "tailwindcss"` + the 15 approved tokens + base/reduced-motion rules
- `frontend/app/(public)/layout.tsx` - public shell (skip link, header, Doações Link, main, footer), metadata + viewport
- `frontend/app/layout.tsx` - imports `globals.css`, exports viewport `themeColor`/`colorScheme: dark`
- `frontend/app/globals.css` - minimal dark base, no Tailwind import
- `frontend/app/(public)/page.tsx` - interim home: h1 "Vagas abertas", subtitle, `#vagas` target
- `frontend/app/(public)/doacoes/page.tsx` - static Doações page with approved copy and back link
- `frontend/app/page.tsx` - deleted (duplicate `/` next to the route group)
- `frontend/tsconfig.json` - Next 15 added `target: ES2017` during lint (kept, minimal diff)

## Decisions Made

- **Tokens are the single colour source:** every public colour is a Tailwind utility derived from `@theme` (`bg-canvas`, `border-line`, `text-fg-muted`, `text-donate`); no raw hex in JSX except the two approved `rgba(250,204,21,…)` hover/border values for Doações, which have no token in the spec.
- **`next/link` for internal navigation** instead of raw `<a>`: `@next/next/no-html-link-for-pages` fails lint otherwise. `<Link>` still renders `<a href="/doacoes">`, so UI-SPEC §F and the plan's key-link pattern hold.
- **No transition on Doações:** UI-SPEC §F forbids animation/glow/pulse, so the hover change is instant.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `next lint` rejected raw `<a href="/">`**
- **Found during:** task 2 (public shell)
- **Issue:** `@next/next/no-html-link-for-pages` errors on `<a href="/">` ("Use `<Link />` from `next/link`"). The header's `/doacoes` anchor would also trip it once that route exists.
- **Fix:** imported `next/link` and used `<Link href="/">` for the wordmark and `<Link href="/doacoes">` for the Doações entry. Both render plain anchors in HTML, satisfying the UI-SPEC contract.
- **Files modified:** `frontend/app/(public)/layout.tsx`, `frontend/app/(public)/doacoes/page.tsx`
- **Verification:** `npm run lint` → "No ESLint warnings or errors"; build output contains `href="/doacoes"`.
- **Committed in:** `4017c0c` (task 2) and `45a3ce8` (task 3)

**2. [Rule 3 - Blocking] Next 15 rewrote `tsconfig.json` during lint**
- **Found during:** task 2 verification
- **Issue:** `next lint` added `target: ES2017` and reformatted the whole file; the extra formatting noise would keep reappearing.
- **Fix:** kept `target: ES2017` (required by Next's top-level-await detection) and restored the original compact formatting so the diff is a single line. Re-ran lint to confirm Next does not rewrite it again.
- **Files modified:** `frontend/tsconfig.json`
- **Verification:** `git diff` shows only `+ "target": "ES2017"`; lint passes without further rewrites.
- **Committed in:** `4017c0c` (task 2)

---

**Total deviations:** 2 auto-fixed (both Rule 3 - blocking)
**Impact on plan:** No scope creep. Both fixes were forced by the project's existing lint/build tooling; the visual contract is unchanged.

## Issues Encountered

- `next lint`/`next build` warn about multiple lockfiles and infer `C:\Users\AndreC` as the workspace root (an ancestor `package-lock.json` exists outside the repo). Harmless for compilation; a future cleanup could set `outputFileTracingRoot` in `next.config.mjs`, but that is outside this plan's files and was left untouched.
- `npm install` reported 3 advisories (2 high, 1 critical) in the existing dependency tree; per the plan, no `npm audit fix` was run.
- `next-env.d.ts` remains untracked (pre-existing scratch state, explicitly out of scope).

## User Setup Required

None - no external service configuration required. Everything runs with the existing local `.env.local`.

## Next Phase Readiness

- Plan 04-02 can render the board directly into `(public)/page.tsx`; the shell, tokens and Doações entry point are ready.
- `/` currently builds as `○ (Static)` because it reads no request-time API yet. Plan 04-02/04-04 must keep the `searchParams` read and `cache: "no-store"` so it flips to `ƒ (Dynamic)` per Pitfall 5.
- CSS isolation is proven at build time today; keep the rule "never import `public.css` from the root layout" and avoid public → admin links.
- UIUX-01/UIUX-02 are marked complete for this plan's scope (tokens + Doações). Later plans must keep using these tokens (`#8b5cf6` never carries text; filled CTAs use `#7c3aed`).

## Self-Check: PASSED

- `frontend/app/(public)/public.css` contains `@import "tailwindcss"` and all 15 tokens — FOUND
- `frontend/app/(public)/layout.tsx` exists, ≥40 lines, imports `./public.css` and links `href="/doacoes"` — FOUND
- `frontend/postcss.config.mjs` contains `@tailwindcss/postcss` — FOUND
- `frontend/app/(public)/doacoes/page.tsx` exists, ≥15 lines — FOUND
- `frontend/app/layout.tsx` imports `./globals.css` — FOUND
- Commits `d70a22f`, `4017c0c`, `45a3ce8` exist on `master` — FOUND
- `npm run lint` and `npm run build` pass; routes `/`, `/doacoes`, `/admin/paste` build
