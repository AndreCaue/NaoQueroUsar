---
phase: 04-public-board-frontend
plan: 03
subsystem: ui
tags: [nextjs, react-server-components, tailwind, native-dialog, ssr, no-store, pt-br]
requires:
  - phase: 04-public-board-frontend
    provides: public shell, dark-purple tokens and skip-link target (`04-01`)
  - phase: 04-public-board-frontend
    provides: public jobs API with `q`/`city`/`sort`/`page` + accented canonical cities (`04-02`)
provides:
  - Contact-free `JobPublic`/`JobListResponse`/`JobStatus` types in the frontend API client
  - Server fetch helpers with `cache: "no-store"` and a 15 s `AbortSignal.timeout`
  - Single URL-parse boundary (`normalizeFilters`) plus canonical `buildBoardHref`
  - Server-rendered board at `/` (cards, count, empty states, pagination)
  - Native `<dialog>` detail view with server-seeded `?vaga=` deep links
  - `loading.tsx` skeleton and approved `error.tsx` copy (cold start vs. generic failure)
affects: [04-04, 04-05, 04-06]
tech-stack:
  added: []
  patterns:
    - "RSC board reads `searchParams` (a Promise in Next 15) and awaits the fetch — no client waterfall"
    - "Server-only fetch module throws `BoardError` with a `kind` so `error.tsx` picks copy without importing server code"
    - "Client grid seeded from server props (`useState(initialJob ?? null)`) so deep links render dialog markup in the SSR HTML"
    - "Native `showModal()` dialog (no dependency) with `onClose` wired to the native `close` event"
key-files:
  created:
    - frontend/lib/jobs.ts
    - frontend/lib/filters.ts
    - frontend/lib/format.ts
    - frontend/lib/cities.ts
    - frontend/components/board/icons.tsx
    - frontend/components/board/JobCard.tsx
    - frontend/components/board/Pagination.tsx
    - frontend/components/board/JobGrid.tsx
    - frontend/components/board/JobDetailDialog.tsx
    - frontend/app/(public)/loading.tsx
    - frontend/app/(public)/error.tsx
  modified:
    - frontend/lib/api.ts
    - frontend/app/(public)/page.tsx
key-decisions:
  - "City canonical values are accented (`São Paulo`), following the 04-02 Rule 1 discovery rather than the plan's unaccented table; `cityLabel` folds accents/case so slug, label and unaccented spellings all resolve."
  - "`BoardError.message` carries the error kind (`timeout` | `http` | `network`) so the client `error.tsx` can select the cold-start copy without importing the server-only module."
  - "`page.tsx` resolves the `?vaga=` deep link against the current page's `data.items` and passes `initialJob`; server-side `fetchJob` fallback plus the not-found panel stay in 04-04."
  - "The grid remounts on `key={buildBoardHref(filters)}` so per-card `Ver mais` expand state resets when filters/page change."
  - "Pagination hrefs strip `vaga`, and prev/next are only emitted when the target page is in range."
patterns-established:
  - "URL params are parsed exactly once, in `normalizeFilters`; malformed `vaga` is preserved so the future not-found state stays reachable."
  - "Board components render job text as JSX text nodes only and never receive contact fields."
  - "Scroll lock restores the previous `documentElement.style.overflow` value on cleanup, not a hardcoded `auto`."
requirements-completed: [PUBL-01, PUBL-02, PUBL-03]
duration: 13min
completed: 2026-10-26
---

# Phase 4 Plan 3: Public board rendering Summary

**Server-rendered dark-purple job board with `Ver a vaga` cards, native modal detail, filter-aware pagination, and approved cold-start error copy**

## Performance

- **Duration:** 13 min
- **Started:** 2026-10-26T21:25:00-03:00
- **Completed:** 2026-10-26T21:38:00-03:00
- **Tasks:** 3
- **Files modified:** 13 (11 created, 2 modified)

## Accomplishments
- `/` now renders the published board on the server from `searchParams` (`ƒ` dynamic route in the build output), with count, cards, pagination and the three approved empty states — no login, no client fetch waterfall.
- Cards follow the locked UI-SPEC anatomy: title, optional company, city with pin, optional salary, clamped activities preview with `Ver mais`/`Ver menos`, absolute `Publicada em` date and a 44 px `Ver a vaga` outline CTA.
- One native `<dialog>` serves the whole board: `showModal()` for focus trapping/ESC/backdrop, bottom sheet under 640 px and a centred 640 px panel above, section order Atividades → Requisitos → Benefícios → Salário → Local, with focus returning to the trigger card on close.
- `?vaga=<uuid>` is seeded in state (not a mount effect) so the dialog markup exists in the SSR HTML; ids outside the current page are left for 04-04.
- Failure paths are copy-approved: `loading.tsx` renders a six-card pulse skeleton and `error.tsx` distinguishes the 15 s timeout (`O servidor está acordando.`) from generic network/HTTP failures.

## task Commits

Each task was committed atomically:

1. **task 1: write the board contracts, fetch helpers, URL filters and icons** - `32edfbf` (feat)
2. **task 2: render the SSR board, cards, pagination and loading/error states** - `5c5c0de` (feat)
3. **task 3: add the native detail dialog and open it from the grid** - `21bd3a8` (feat)

**Plan metadata:** see the docs commit created after this summary.

## Files Created/Modified
- `frontend/lib/api.ts` - appended `JobStatus`, `JobPublic`, `JobListResponse`; existing admin exports untouched
- `frontend/lib/jobs.ts` - `fetchBoard`/`fetchJob` with `no-store`, `AbortSignal.timeout(15_000)` and `BoardError` kinds
- `frontend/lib/filters.ts` - `PAGE_SIZE`, `normalizeFilters`, `isUuid`, `toApiParams`, `buildBoardHref`, `hasActiveFilters`
- `frontend/lib/format.ts` - pt-BR date formatter (America/Sao_Paulo) and `formatJobCount`
- `frontend/lib/cities.ts` - slug/label/canonical map with accent-folding `cityLabel`
- `frontend/components/board/icons.tsx` - inline `Search`, `X`, `ChevronDown`, `MapPin`, `Whatsapp` SVGs
- `frontend/components/board/JobCard.tsx` - card anatomy, `Ver mais` toggle and `onOpen(job, trigger)` contract
- `frontend/components/board/Pagination.tsx` - `Anterior` / `Página X de Y` / `Próxima`, hidden at one page
- `frontend/components/board/JobGrid.tsx` - client grid, selected-job state, focus restore, single dialog
- `frontend/components/board/JobDetailDialog.tsx` - native modal with sections, dates and scroll lock
- `frontend/app/(public)/page.tsx` - RSC board, empty states, deep-link seeding, pagination hrefs
- `frontend/app/(public)/loading.tsx` - six-card skeleton with `aria-busy`
- `frontend/app/(public)/error.tsx` - timeout vs. generic copy with `Tentar novamente`

## Decisions Made
- Accented city canonicals (04-02 reality) with a fold-based `cityLabel`, instead of the plan's unaccented canonical table.
- `BoardError.message` = kind, keeping `error.tsx` free of server-only imports.
- Deep-link resolution lives in `page.tsx` (task-2 file) because `JobGrid` is a client component and the lookup needs `data.items`; server-side `fetchJob` fallback remains 04-04.
- Grid remount keyed on the canonical board href so card expand state cannot leak across filter changes.
- Pagination drops `vaga` from its hrefs to avoid reopening a dialog from the previous page.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] City canonicals are accented, not unaccented**
- **Found during:** task 1 (board contracts and helpers)
- **Issue:** The plan's interface table lists canonical `Sao Paulo`, but 04-02 established that the API/database store `São Paulo`; filtering with the unaccented value would return zero rows.
- **Fix:** `CITY_OPTIONS.canonical` uses the accented values and `cityLabel` compares with an NFD fold so slug, label and unaccented spellings all resolve to the accented label.
- **Files modified:** `frontend/lib/cities.ts`
- **Verification:** lint + `tsc --noEmit` clean; label/slug/canonical all resolve in the build; 04-02's API tests already assert accented filtering.
- **Committed in:** `32edfbf` (task 1 commit)

**2. [Rule 3 - Blocking] Doc comment tripped the contact/HTML grep gate**
- **Found during:** task 3 (dialog verification)
- **Issue:** The verify gate greps board components for the literal `dangerouslySetInnerHTML`; the first version of the dialog's doc comment named that API while explaining it is banned, so the gate failed on documentation.
- **Fix:** Reworded the comment to "raw HTML injection is never used" — no behavior change, the gate now measures code only.
- **Files modified:** `frontend/components/board/JobDetailDialog.tsx`
- **Verification:** `Select-String` gate returns nothing; `showModal` gate passes.
- **Committed in:** `21bd3a8` (task 3 commit)

**3. [Rule 1 - Bug] Dynamic-route assertion corrected for Next 15.5's manifest shape**
- **Found during:** task 3 (build verification)
- **Issue:** The plan's threat table expects `/` inside `prerender-manifest.dynamicRoutes`, but in Next 15.5 that object is empty (`{}`); a dynamic page driven by `searchParams` simply has no entry in `routes`.
- **Fix:** Asserted `/` is absent from `prerender-manifest.routes` (it only lists `/doacoes`, `/admin/paste`, `/_not-found`) while the build output shows `ƒ /`.
- **Files modified:** none (verification command only)
- **Verification:** `node -e` check prints `forbidden-patterns clear; showModal ok; / dynamic ok`.
- **Committed in:** n/a (verification only)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All three were required for correctness or for the gates to measure code rather than comments. No scope creep; no new dependencies; no contact field or raw-HTML rendering was introduced.

## Issues Encountered
- `npm run build` warns that Next inferred `C:\Users\AndreC\package-lock.json` as the workspace root (pre-existing environment condition from a parent lockfile); build and routes are unaffected and `next.config`/`package-lock.json` were left untouched per plan scope.
- `frontend/tsconfig.tsbuildinfo` is generated by the task-1 `tsc --noEmit` run and is not covered by the root/frontend `.gitignore`. It is a local artifact only; left untracked rather than widening the plan's file scope (candidate for a future `.gitignore` chore).

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: untrusted-text-render | `frontend/components/board/JobCard.tsx`, `frontend/components/board/JobDetailDialog.tsx` | Pasted job text (title/activities/requirements/benefits/salary) is rendered as JSX text nodes; the grep gate now also guards comments, so any future raw-HTML injection is caught at lint time (T-04-08) |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Board is ready for 04-04 to add the contact reveal footer in the dialog and the server-side `?vaga=` not-found panel (`fetchJob` already exists and returns `null` on 404).
- 04-05 can build the filter bar on top of `normalizeFilters`/`buildBoardHref` without touching this plan's files.
- 04-06 browser verification should hit the 30 seeded demo jobs on the dev branch; the deep link only opens a dialog when the id is on the loaded page until 04-04 lands.

---
*Phase: 04-public-board-frontend*
*Completed: 2026-10-26*

## Self-Check: PASSED

- All 13 plan files exist on disk.
- Commits `32edfbf`, `5c5c0de`, `21bd3a8` exist in git history.
- `npm run lint` and `npm run build` pass with `/` rendered as `ƒ (Dynamic)`.
