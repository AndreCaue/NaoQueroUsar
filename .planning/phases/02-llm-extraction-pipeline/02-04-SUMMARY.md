---
phase: 02-llm-extraction-pipeline
plan: 04
subsystem: ui
tags: [nextjs, react, admin, extraction-ui, typescript, plain-css, jwt, dark-theme]

# Dependency graph
requires:
  - phase: 02-llm-extraction-pipeline
    provides: "plan 02-03 — POST /api/v1/admin/extract + /api/v1/auth/login (JWT), ExtractSummaryResponse contract; plans 02-01/02-02 — extraction pipeline behind the endpoint"
provides:
  - "frontend/lib/api.ts typed fetch helpers (loginAdmin, extractJobs, ExtractSummary/DiscardedJob interfaces) built on NEXT_PUBLIC_API_URL"
  - "/admin/paste route (server component) rendering ExtractForm (client component): password → JWT (state + sessionStorage), paste → submit → pt-BR summary with counts/alerts/discarded snippets, error box, reset"
  - "frontend/app/admin/paste/globals-admin.css — locked dark theme (#0f0a1a / #1a1025 / #8b5cf6 / #a78bfa / #facc15) via plain CSS, no Tailwind (Phase 4 owns the design system)"
  - "frontend/.env.local.example documenting NEXT_PUBLIC_API_URL"
affects: [04-review-ui, 05-admin-review-flow, phase-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "typed API helper layer in frontend/lib/api.ts: native fetch, no deps, server `detail` surfaced as pt-BR Error"
    - "admin JWT in React state + sessionStorage key `nqu_admin_token` (reload resilience; T-02-13 accept per D-01 Bearer decision)"
    - "plain-CSS colocated admin stylesheet with theme variables — Tailwind deferred to Phase 4"
    - "no secrets in frontend: only NEXT_PUBLIC_API_URL referenced"

key-files:
  created:
    - frontend/lib/api.ts
    - frontend/app/admin/paste/page.tsx
    - frontend/app/admin/paste/ExtractForm.tsx
    - frontend/app/admin/paste/globals-admin.css
    - frontend/.env.local.example
  modified: []

key-decisions:
  - "ExtractSummary interface mirrors backend ExtractSummaryResponse field-for-field (single source of truth is the backend schema; frontend copy is structural, not generated — acceptable at this scale)"
  - "token stored in both React state and sessionStorage so a page reload keeps the admin logged in without a cookie (D-01 Bearer, no cookie)"
  - "summary reset via 'Nova extração' clears summary+error but keeps the token, avoiding re-login per paste"

patterns-established:
  - "frontend/lib/api.ts is the single typed seam to the FastAPI backend; future Phase 4/5 pages extend it instead of ad-hoc fetch"
  - "admin pages use the .admin-page/.admin-panel/.admin-btn/.admin-alert/.admin-error class set from globals-admin.css"

requirements-completed: [EXTR-01]

# Metrics
duration: ~5min (continuation; task 1 ~35min + checkpoint)
completed: 2026-10-20
---

# Phase 02 Plan 04: Admin Paste Page and Live Extraction Smoke Summary

**Dark-themed /admin/paste page with typed login+extract API helper closing the D-04 loop — human-verified live end-to-end (login → paste → Groq extraction → summary with alerts/discards → DB rows).**

## Performance

- **Duration:** ~5 min (continuation after approved human-verify checkpoint; task 1 code committed earlier)
- **Started:** 2026-10-19 (task 1) / 2026-10-20 (finalization)
- **Completed:** 2026-10-20
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- `/admin/paste` route live: master logs in with admin password → JWT, pastes raw WhatsApp-style text, runs extraction, and reads the pt-BR summary (count badges, yellow alerts, discarded reason+snippet in `<details>`) without leaving the page — D-04 fully realized
- `frontend/lib/api.ts` provides typed, dependency-free `loginAdmin`/`extractJobs` against the plan-03 contracts (`/api/v1/auth/login`, `/api/v1/admin/extract`), surfacing backend `detail` as clear pt-BR errors
- Dark theme implemented as plain colocated CSS with the locked palette — no Tailwind, no new dependencies, `npm run build` exits 0
- **Task 2 human-verify APPROVED:** live smoke verified login → paste → extraction summary end-to-end against running backend+frontend (per plan's how-to-verify steps), confirming DB rows with `status` + `source_snippet`

## task Commits

Each task was committed atomically:

1. **task 1: typed API helper + /admin/paste page + ExtractForm** - `079e8e8` (feat)
2. **task 2: live smoke of /admin/paste extraction flow (human verify)** - human-approved, no code changes

## Files Created/Modified

- `frontend/lib/api.ts` — `loginAdmin`/`extractJobs` typed helpers + `ExtractSummary`/`DiscardedJob` interfaces; URLs from `NEXT_PUBLIC_API_URL ?? "http://localhost:8000"`
- `frontend/app/admin/paste/page.tsx` — server component rendering `<h1>` + `<ExtractForm />`
- `frontend/app/admin/paste/ExtractForm.tsx` — client component: login form, sessionStorage token restore, textarea, loading state, summary (badges/alerts/discards), error box, reset
- `frontend/app/admin/paste/globals-admin.css` — theme variables + .admin-* classes (bg #0f0a1a, panel #1a1025, purple accents, yellow alerts, red errors)
- `frontend/.env.local.example` — `NEXT_PUBLIC_API_URL=http://localhost:8000` + gitignore note

## Decisions Made

- Token kept in React state and sessionStorage (reload resilience) per accepted threat T-02-13 and D-01 Bearer-JWT decision — no httpOnly cookie at this stage
- "Nova extração" reset preserves the token so repeated pastes don't require re-login

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

`GROQ_API_KEY` (backend `.env`) required for live extraction — provided during the human-verify smoke. `NEXT_PUBLIC_API_URL` optionally set in `frontend/.env.local` (defaults to http://localhost:8000).

## Known Stubs

None.

## Threat Flags

None — no new security-relevant surface beyond the plan's threat register (T-02-13 accept, T-02-14/T-02-15 transfer/mitigate as planned; no secrets in frontend code).

## Next Phase Readiness

- Phase 2 complete: extraction core (01), orchestrator (02), API+DB (03), admin paste UI + live smoke (04)
- Phase 3 (contact reveal + Turnstile anti-spam) and Phase 4/5 (review UI) can build on the now-verified pipeline; `frontend/lib/api.ts` is the seam to extend
- No blockers

---
*Phase: 02-llm-extraction-pipeline*
*Completed: 2026-10-20*

## Self-Check: PASSED

- All 5 key files exist on disk (lib/api.ts, page.tsx, ExtractForm.tsx, globals-admin.css, .env.local.example)
- Task commit `079e8e8` present in history; task 2 approved by human after live end-to-end smoke (no code changes)
- STATE.md and ROADMAP.md untouched by this finalization (orchestrator owns those writes)
