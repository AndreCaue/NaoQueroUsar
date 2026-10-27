---
phase: 04-public-board-frontend
plan: 04
subsystem: ui
tags: [nextjs, turnstile, contact-reveal, cors, deep-link, client-state]
requires:
  - phase: 04-public-board-frontend
    provides: public shell, dark-purple tokens and skip-link target (`04-01`)
  - phase: 04-public-board-frontend
    provides: public jobs API with `q`/`city`/`sort`/`page` + accented canonical cities (`04-02`)
  - phase: 04-public-board-frontend
    provides: SSR board, native dialog, `fetchJob` helper, `isUuid`/`normalizeFilters` (`04-03`)
provides:
  - Contact link builders (`wa.me`/`mailto`) and a tab-scoped in-memory contact cache
  - `RevealError`/`revealContact` client with status, kind and `retryAfter` (15 s timeout)
  - CORS exposure of `Retry-After` on the backend, asserted on a real cross-origin GET
  - `RevealContact` state machine (idle/verifying/revealed/error) with approved pt-BR copy
  - Deep-link resolution: valid `?vaga=` opens the job on any page; unknown/malformed ids render a server-side not-found panel with a clear-filters CTA
  - URL sync on open/close (`replaceState`, preserves other params, restores focus)
affects: [04-05, 04-06]
tech-stack:
  added: []
  patterns:
    - "Contact is revealed only after a successful Turnstile verification; cached per job/tab in a module-scope Map (never storage/URL)"
    - "Turnstile widget mounts only while verifying, remounts via `key` after every error so a consumed token is never resent"
    - "Deep-link not-found is server-rendered (RSC panel) so a plain HTTP GET sees it; the client grid keeps no not-found state"
    - "URL is the single source of truth for `?vaga=`; open/close use `history.replaceState` (no new history entries)"
key-files:
  created:
    - frontend/lib/contacts.ts
    - frontend/lib/contact-cache.ts
    - frontend/components/board/RevealContact.tsx
  modified:
    - frontend/lib/api.ts
    - frontend/components/board/JobDetailDialog.tsx
    - frontend/components/board/JobGrid.tsx
    - frontend/app/(public)/page.tsx
    - backend/app/main.py
    - backend/tests/test_public_api.py
key-decisions:
  - "Reveal widget uses `appearance=\"interaction-only\"`, `action=\"reveal\"`, `id=\"turnstile-reveal\"`, theme dark; SITE_KEY mirrors ExtractForm.tsx (dev fallback `1x00000000000000000000AA`)."
  - "Backend `detail` is rendered verbatim; only 403/429/404/network/timeout pick local approved copy or a countdown."
  - "A consumed Turnstile token is never resent: 403 bumps `revealKey` so the widget remounts; 429 disables the button with a `Retry-After` countdown."
  - "Contact cache is a module-scope `Map`; reload clears it (no sessionStorage/localStorage/IndexedDB/cookie/URL)."
  - "Deep-link not-found is server-rendered in `page.tsx` (malformed OR valid-but-missing `?vaga=`), with the board rendered underneath; the client grid keeps only `initialJob` state."
  - "CORS `Retry-After` exposure is asserted on an actual cross-origin GET (Starlette sets `Access-Control-Expose-Headers` only on actual responses, never on preflight)."
  - "Live end-to-end reveal cannot be confirmed with Cloudflare's public test secrets, which do not return the `action` field; the frontend is built against the documented 403 contract and the anti-spam gate is left untouched (SECR-01/02, PUBL-05)."
requirements-completed: [PUBL-03, PUBL-04, PUBL-06]
duration: ~20min
completed: 2026-10-26
---

# Phase 4 Plan 4: Contact reveal + deep link Summary

**Reveal a job's contact behind Turnstile from the dialog footer, cache it per job/tab, build WhatsApp/e-mail links, and make `?vaga=` a real server-resolved deep link that degrades to an honest not-found panel**

## Performance

- **Duration:** ~20 min
- **Tasks:** 3
- **Files modified:** 10 (3 created, 7 modified)
- **Tests:** frontend `npm run lint` + `npm run build` green (`/` dynamic); backend `tests/test_public_api.py` 10/10 (CORS exposure)

## Accomplishments

- `frontend/lib/contacts.ts` ships `digitsOnly`, `waHref` (null when < 10 digits, otherwise `https://wa.me/{digits}?text=...` with the approved message), `mailtoHref` (CR/LF stripped, `Candidatura: {title}` subject) and `messageFor`.
- `frontend/lib/contact-cache.ts` keeps a module-scope `Map` (tab lifetime only; no storage/cookie/URL) with `getCachedContact`/`setCachedContact`/`clearContactCache`.
- `frontend/lib/api.ts` adds `ContactRevealResponse`, `RevealError` (status/kind/retryAfter) and `revealContact` (15 s `AbortSignal.timeout`, backend `detail` verbatim, `Retry-After` parsed as int).
- `backend/app/main.py` exposes `Retry-After` via CORS (already present); `backend/tests/test_public_api.py` asserts it on a real cross-origin GET.
- `RevealContact.tsx` implements the 7-state machine (idle/verifying/revealed/error for 403/429/404/network/timeout) with the approved pt-BR copy, a single widget mounted only while verifying, remount on error, 429 countdown, and conditional WhatsApp/e-mail buttons (or `Contato não disponível para esta vaga.`).
- `JobDetailDialog.tsx` gains a sticky footer rendering `<RevealContact>`, reusing the same `close()` as the X button.
- `page.tsx` validates `?vaga=` at the fetch boundary (`isUuid`), resolves valid ids via `fetchJob` in parallel with `fetchBoard`, and renders a server-side not-found panel (malformed OR missing) with `Limpar filtros`, board underneath.
- `JobGrid.tsx` syncs `?vaga=` on open/close via `history.replaceState` (preserves other params, drops the param on close, restores focus to the trigger).

## task Commits

Each task was committed atomically:

1. **task 1: contact helpers, tab cache, reveal client and CORS header exposure** - `3aac9c9` (feat)
2. **task 2: implement the reveal state machine and mount it in the dialog footer** - `8b1f8ad` (feat)
3. **task 3: resolve `?vaga=` server-side and sync it to the URL** - `c1f6c92` (feat)

## Files Created/Modified

- `frontend/lib/contacts.ts` - `digitsOnly`, `waHref`, `mailtoHref`, `messageFor`
- `frontend/lib/contact-cache.ts` - module-scope `Map` + get/set/clear
- `frontend/lib/api.ts` - `ContactRevealResponse`, `RevealError`, `revealContact`
- `backend/app/main.py` - `expose_headers=["Retry-After"]` (CORS)
- `backend/tests/test_public_api.py` - CORS `Retry-After` exposure assertion
- `frontend/components/board/RevealContact.tsx` - 7-state machine + Turnstile widget
- `frontend/components/board/JobDetailDialog.tsx` - sticky reveal footer
- `frontend/app/(public)/page.tsx` - server-side `?vaga=` resolution + not-found panel
- `frontend/components/board/JobGrid.tsx` - URL sync on open/close + focus restore

## Decisions Made

- Contacts never pre-render in `idle`/`verifying` (not even hidden/data-*); markup exists only in `revealed`.
- Turnstile mounts only on click (`appearance="interaction-only"`), single widget, remount via `key` after every error.
- Deep-link not-found is server-rendered so a plain HTTP GET exposes it; the client grid keeps no not-found state.
- Backend `detail` is rendered verbatim; only local copy for network/timeout and the 429 countdown.
- `Retry-After` exposure asserted on an actual response (not preflight), per Starlette semantics.

## Deviations from Plan

None material — the implementation matches the plan's contract. The only environmental note is the open Phase 03 blocker (Cloudflare test secrets do not return `action`), which makes live reveal return 403 in dev; the frontend surfaces the backend copy and allows retry, and the anti-spam gate is untouched.

## Issues Encountered

- Cloudflare public test secrets (1x/2x/3x…AA) do not return the `action` field from Siteverify, so `reveal-contact` and `login` return 403 in dev/local. Symptom measured, fix awaiting user verdict; no production code changed. Live end-to-end reveal cannot be confirmed with test keys.
- `frontend/tsconfig.tsbuildinfo` remains an untracked local artifact (candidate for a future `.gitignore` chore).

## Threat Flags

None new — all threats in the plan's register are mitigated by the implementation (single widget, no storage, digits-only `wa.me`, CR/LF stripping, 429 cooldown).

## User Setup Required

None — no external service configuration required for the build. (Live reveal needs real Turnstile keys; see the open blocker above.)

## Next Phase Readiness

- Board is ready for 04-05 to add the filter toolbar on top of `normalizeFilters`/`buildBoardHref`.
- 04-06 can run the SSR gate and the human verification checkpoint against the revealed-contact contract.
- The open Turnstile `action` blocker should be resolved (or accepted) before the human UAT of 04-06.

---
*Phase: 04-public-board-frontend*
*Completed: 2026-10-26*

## Self-Check: PASSED

- All plan files exist on disk.
- Commits `3aac9c9`, `8b1f8ad`, `c1f6c92` exist in git history.
- `npm run lint` and `npm run build` pass with `/` rendered as `ƒ (Dynamic)`.
- `tests/test_public_api.py` 10/10 (CORS exposure).
