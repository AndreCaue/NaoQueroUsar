---
phase: 04-public-board-frontend
plan: 02
subsystem: api
tags: [fastapi, sqlalchemy, postgres, alembic, unaccent, like-escape, pagination, seed]

# Dependency graph
requires:
  - phase: 03-contact-reveal-anti-spam
    provides: public router, JobPublic/JobListResponse schemas, reveal endpoint that must stay contact-gated
  - phase: 02-admin-review-publish
    provides: jobs table, jobs_set_search_text()/jobs_updated_at triggers, immutable_unaccent, published status
provides:
  - Migration 0003 replacing jobs_set_search_text() so search_text includes requirements, plus a backfill that preserves updated_at
  - list_published(q=, city=, sort=) with one shared predicate list for items and total
  - Public API params q/city/sort on GET /api/v1/public/jobs (slug, canonical and accented city accepted; unknown values ignored)
  - 18 integration tests (5 trigger/migration + 13 HTTP) in tests/test_public_search.py
  - scripts/seed_public_demo.py, a guarded dev-only seed of 30 published demo jobs
affects: [04-03, 04-04, 04-05, 04-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Accent/case-insensitive search: store immutable_unaccent(lower(...)) in search_text, normalize the query identically, LIKE with ESCAPE '\\\\'"
    - "LIKE metacharacters escaped in Python (backslash first) and passed as a bound parameter via func.concat — never interpolated into SQL"
    - "Items and total built from the same _published_filters() list with status='published' literal, keeping the partial trigram index usable"
    - "Deterministic paging: order_by(created_at direction, id direction) so ties never repeat or drop rows"
    - "Dev seed safety by construction: ENV=dev + local/.neon.tech host + --yes, marker-based delete-before-insert idempotency"

key-files:
  created:
    - backend/alembic/versions/0003_search_text_requirements.py
    - backend/tests/test_public_search.py
    - backend/scripts/seed_public_demo.py
  modified:
    - backend/app/crud/jobs.py
    - backend/app/api/v1/public.py

key-decisions:
  - "Canonical city values in the DB are the accented ALLOWED_CITIES tuple (São Paulo, Rio de Janeiro, Belo Horizonte, Remoto); aliases resolve to that accented form, contradicting the plan's unaccented 'Sao Paulo' claim"
  - "Migration 0003 keeps jobs_search_text_trg enabled during the backfill and disables only jobs_updated_at, so search_text is recomputed exactly once without bumping updated_at"
  - "Unknown city/sort values are silently ignored (200) instead of 400 — the URL is a user-facing filter, not an input contract"
  - "The seed never writes search_text (trigger-owned) and backdates created_at on the model before insert instead of a raw UPDATE"

patterns-established:
  - "Search normalization happens in exactly two places: the DB trigger (write) and func.immutable_unaccent(func.lower(...)) on the bound pattern (read)"
  - "Seed scripts for this project must gate on ENV, resolved DB host and an explicit --yes, and print the host only"

requirements-completed: [SRCH-01, SRCH-02, SRCH-03]

# Metrics
duration: 197min
completed: 2026-10-26
---

# Phase 4 Plan 2: Accent-Insensitive Search, City Filter and Deterministic Sort Summary

**Public jobs API now accepts `q`/`city`/`sort` with accent- and case-insensitive LIKE over a trigger-maintained `search_text` that includes `requirements`, plus migration 0003 and a guarded dev seed of 30 published demo jobs.**

## Performance

- **Duration:** 3h 17m
- **Started:** 2026-10-26T19:00:06Z
- **Completed:** 2026-10-26T22:17:30Z
- **Tasks:** 3
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments

- Shipped migration `0003_search_text_requirements`: `CREATE OR REPLACE FUNCTION jobs_set_search_text()` adds `coalesce(NEW.requirements,'')` as the last concatenated field (same function name, so `jobs_search_text_trg` keeps binding), and a one-shot backfill recomputes every existing `search_text` with `jobs_updated_at` disabled and re-enabled inside the same transaction. Applied to **both** Neon branches (test `ep-holy-rice…` and dev `ep-snowy-mouse…`); verified live that the function body contains `requirements` and `pg_trigger.tgenabled='O'` afterwards.
- Rewrote `list_published` with `q`/`city`/`sort` keyword-only args: one `_published_filters()` list feeds both the page query and `count()`, `q` escapes `\`, `%`, `_` and binds an unaccented pattern through `func.concat`, and ordering always ends with an `id` tie-break (`created_at DESC, id DESC` for `recentes`, both `ASC` for `antigas`).
- Exposed the wire contract the frontend will call: `GET /api/v1/public/jobs?q=&city=&sort=&page=&limit=`; `q` max 80 chars and trimmed, `city` max 40 and whitelisted (slug/canonical/accented label), `sort` only `antigas` changes order, default `limit=20`/`le=50` untouched. Bad `city`/`sort` never produce a 400.
- 18 new integration tests against the real Postgres branch: 5 trigger/backfill tests and 13 HTTP tests covering case folding, accent folding, requirements-only matches, literal `%`/`_`, three city spellings, unknown city ignored, AND combination, both sort directions, unknown sort fallback, `created_at` tie-break across pages, `total` parity, and contact-free payloads.
- Created `scripts/seed_public_demo.py` and exercised both paths: `--dry-run` exits 0 printing marker/host/count/cities/titles; `ENV=staging` + live-like secret exits 1 with `seed_public_demo só roda com ENV=dev`; `--yes --count 30` wrote 30 published rows on the dev branch, all carrying `SEED_PUBLIC_DEMO`, with `requirements` text present in the trigger-generated `search_text` and 0 expired.

## Task Commits

Each task was committed atomically (TDD tasks have a test commit followed by a feat commit):

1. **task 1: migration 0003 — include requirements in search_text and backfill** - `4be6982` (test), `eecf857` (feat)
2. **task 2: filtered and sorted list_published with API params** - `9b6414c` (test), `6e2a08b` (feat)
3. **task 3: dev-only published demo seed with environment guard** - `49c6f95` (feat)

**Plan metadata:** see the docs commit created after this summary.

## Files Created/Modified

- `backend/alembic/versions/0003_search_text_requirements.py` - replaces the search_text trigger function to include `requirements`; backfills with `jobs_updated_at` disabled; `downgrade()` restores the 0002 body and deliberately leaves the (harmless superset) values alone
- `backend/app/crud/jobs.py` - `_escape_like`, `_published_filters`, extended `list_published` signature, deterministic `created_at` + `id` ordering, shared predicate list for `total`
- `backend/app/api/v1/public.py` - `_CITY_ALIASES`, `_resolve_city`, `_resolve_sort`, `q`/`city`/`sort` query params with length caps, trimmed `q`, stale phase-boundary comment removed
- `backend/tests/test_public_search.py` - 18 tests: trigger definition/refresh, backfill `updated_at` preservation, trigger re-enabled, and the full HTTP filter/sort/pagination matrix
- `backend/scripts/seed_public_demo.py` - dev-only published demo seed with ENV/host/`--yes` guards, `SEED_PUBLIC_DEMO` marker idempotency, 30-row default (> `PAGE_SIZE` 24), no `search_text` writes

## Decisions Made

- **Canonical city values are accented.** `ALLOWED_CITIES` in `app/services/extraction/extractor.py` is `("São Paulo", "Rio de Janeiro", "Belo Horizonte", "Remoto")`, so the alias map resolves `sao-paulo`, `sao paulo`, `São Paulo` and `Sao Paulo` to the accented `São Paulo` stored in the DB. Tests insert accented values, mirroring production data.
- **One predicate list, two queries.** `_published_filters()` returns the exact same list for `items` and `count()`; `status = 'published'` stays a literal predicate so the partial trigram index remains usable (T-04-06).
- **No `ILIKE`, no `unaccent()` at query time.** Both the stored `search_text` and the bound pattern are normalized with `immutable_unaccent(lower(...))`, keeping the read path index-friendly and the escaping in one place.
- **Fail-soft URL filters.** Unknown `city` and `sort` are ignored (200) rather than rejected; a mistyped shared link still shows jobs.
- **Seed idempotency by marker, not by truncate.** Each run deletes `source_snippet = 'SEED_PUBLIC_DEMO'` before inserting, so the dev branch keeps its real approval-flow rows untouched.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] City canonical values are accented, not unaccented as the plan stated**
- **Found during:** task 2 (filtered listing + API)
- **Issue:** The plan and CONTEXT (D-05/D-06b) claim the canonical DB values are `Sao Paulo`, `Rio de Janeiro`, `Belo Horizonte`, `Remoto`, but the real `ALLOWED_CITIES` tuple in `backend/app/services/extraction/extractor.py` uses `São Paulo` (accented). Mapping aliases to the plan's unaccented string would have filtered to zero rows against every extracted job.
- **Fix:** `_CITY_ALIASES` resolves every accepted spelling to the accented canonical value, and `tests/test_public_search.py` inserts accented cities. The three aliases per city still work exactly as specified (`city=sao-paulo` matches `São Paulo`).
- **Files modified:** `backend/app/api/v1/public.py`, `backend/tests/test_public_search.py`
- **Verification:** `test_city_filter_accepts_slug_canonical_and_label` and `test_q_and_city_combine_with_and` pass; the seed's 30 live rows all filter correctly by slug.
- **Committed in:** `9b6414c` (tests) and `6e2a08b` (implementation)

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** No scope creep. The fix was required for the city filter to work against real data; the public wire contract (slug spellings) is unchanged.

## Issues Encountered

- `alembic upgrade head` had to be run twice with `DATABASE_URL` explicitly set — once against `TEST_DATABASE_URL` and once against the dev branch — because `backend/.env` holds both URLs. Both branches are now at revision `0003_search_text_requirements (head)`.
- The real seed write path was executed against the dev branch (`--yes --count 30`) to prove delete-by-marker + published insert without touching `search_text`. The 2 pre-existing `needs_review` rows were untouched (total jobs 32 = 30 demo + 2 review), and the demo rows are intentionally left in place so later browser verification has a populated board.
- Console output renders `São` as mojibake under PowerShell 5.1; files are UTF-8 and the DB values are correct — no encoding change was made.

## User Setup Required

None - no external service configuration required. `backend/.env` already carries `DATABASE_URL` and `TEST_DATABASE_URL`.

## Next Phase Readiness

- Frontend plans 04-03/04-04 can call `GET /api/v1/public/jobs?q=&city=sao-paulo&sort=recentes&page=&limit=24` exactly as specified; unknown values will not break the page.
- The dev branch is seeded with 30 published demo jobs (`SEED_PUBLIC_DEMO`) spanning the last 13 days, so both sort directions, pagination page 2 and all four cities are visible in the browser. Re-running the seed is safe and idempotent.
- Later plans that touch `search_text` must keep the single-writer rule (trigger only) and must not add `unaccent()` to the query or switch to `ILIKE`.
- `limit` default stays 20 on the API; the frontend sends 24 — page 2 exists with the seeded 30 rows.

## Self-Check: PASSED

- `backend/alembic/versions/0003_search_text_requirements.py` exists and contains `requirements` — FOUND
- `backend/app/crud/jobs.py` contains `_escape_like`, `_published_filters`, `list_published` with `q`/`city`/`sort` — FOUND
- `backend/app/api/v1/public.py` contains `q`, `city`, `sort` params and `_CITY_ALIASES` — FOUND
- `backend/tests/test_public_search.py` has 18 tests (5 trigger + 13 HTTP), 375 lines — FOUND
- `backend/scripts/seed_public_demo.py` contains `SEED_PUBLIC_DEMO` and all three guards — FOUND
- Commits `4be6982`, `eecf857`, `9b6414c`, `6e2a08b`, `49c6f95` exist on `master` — FOUND
- Full backend suite: `193 passed, 3 skipped` (196 collected) — no regressions against the 178-test baseline
- `seed_public_demo.py --dry-run` exits 0; `ENV=staging` refuses with the `ENV=dev` message — VERIFIED

---
*Phase: 04-public-board-frontend*
*Completed: 2026-10-26*
