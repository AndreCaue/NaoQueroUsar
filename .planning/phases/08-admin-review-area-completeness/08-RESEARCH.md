# Phase 8: Admin Review Area Completeness - Research

**Research Date:** 2026-11-12

## Domain Research

### Admin Review Queue Design Patterns

The admin review area for job platforms typically follows these patterns:

1. **Pending Queue**: Display jobs with `status='pending'` in a paginated table, with filters for city and sorting by creation date (newest first).

2. **Action per Job**: Each job row has actions for:
   - **Approve**: Change status to `published`, refresh `expires_at` to `now + 14 days`
   - **Edit**: Open modal with pre-filled fields, validate at least one contact
   - **Delete**: Hard delete from database, idempotent (second call returns 404)

3. **Authentication**: JWT `Authorization: Bearer <token>` header required on all admin routes. Client-side guard checks `sessionStorage` for token.

4. **Text Snippet Display**: The `source_snippet` field from extraction is displayed alongside extracted job fields. Desktop: side-by-side layout. Mobile: accordion/stacked layout, read-only.

5. **Toast Notifications**: Custom minimal toast component (no external libs) providing feedback for:
   - Success: job approved, job deleted
   - Error: validation failed, network error
   - Info: extraction returned 0 jobs
   - Auto-dismiss after ~3 seconds

6. **Auto-deduplication**: When same text is pasted twice, compute hash (normalized: lowercased, accents removed, spaces collapsed). Suppress duplicate and show notification: "Essas vagas já foram inseridas".

7. **Optimistic Update**: After approval, immediately remove item from pending queue UI, then refetch in background. If refetch fails, item reappears.

### Groq LLM Extraction Research (Phase 2 Integration)

The admin review flow depends on the LLM extraction pipeline from Phase 2. Key findings:

- **Model**: `openai/gpt-oss-20b` (primary) with `openai/gpt-oss-120b` as fallback via `GROQ_MODEL` env
- **Structured Output**: Pydantic schema for extracted jobs, validated after JSON parse from Groq response
- **Contact Validation**: DB CHECK `at_least_one_contact` (email or telephone) - enforced at DB level, backend catches `IntegrityError`
- **City Normalization**: Maps to allowed set: São Paulo, Rio de Janeiro, Belo Horizonte, Remoto
- **14-day Expiry**: `expires_at = created_at + 14 days` computed at job creation

### Turnstile Integration (Phase 7/8 Boundary)

- **Client**: `next-turnstile@1.0.7` widget in admin routes requiring anti-spam
- **Server**: Verify token at `https://challenges.cloudflare.com/turnstile/v0/siteverify` with `secret_key`, `response`, `remoteip`
- **Fail-closed**: In production, missing `TURNSTILE_SECRET_KEY` causes startup error (D-11). In dev, test keys `1x`/`2x`/`3x` are always-pass.
- **Rate limiting**: `REVEAL_RATE_LIMIT=10/min` for reveal endpoint, `LOGIN_RATE_LIMIT=5/min` for login (shared slowapi limiter)

### Backend FastAPI Patterns (Phases 1-7)

- **Router pattern**: `api/v1/admin.py` with routes under `/admin` prefix
- **CRUD layer**: `app/crud/jobs.py` with `list_by_status`, `approve_job`, `update_job`, `delete_job`
- **Model layer**: `app/models/job.py` with CHECK constraints: `title_not_blank`, `at_least_one_contact`
- **Schema layer**: `app/schemas/job.py` with `JobPublic` (no contact), `JobAdmin` (with contact), `JobUpdate` (partial update)
- **Auth dependency**: `require_admin` in `app/deps.py` - validates Bearer JWT, returns 401 if missing
- **PgBouncer compatibility**: `statement_cache_size=0` in async engine connect_args

### Frontend Next.js + Tailwind v4 Patterns (Phases 4-7)

- **Route group**: `(admin)` for admin routes, or `/admin` prefix
- **Tailwind v4**: `@theme` variables for colors: `--color-primary-500: #8b5cf6`, `--color-primary-400: #a78bfa`, `--bg-dark-900: #0f0a1a`, `--bg-dark-800: #1a1025`, `--color-accent-yellow: #facc15`
- **Admin Toast**: Custom component `Toast.tsx` in `frontend/components/admin/`, no external libs
- **Pagination**: Reusable `Pagination.tsx` and `JobGrid.tsx` from `frontend/components/board/`
- **Modals**: `JobDetailDialog.tsx` pattern for edit/approve modals
- **Server Components** for read-only data, **Client Components** for interactive modals and Turnstile widget

### Research Gaps Identified

1. **Exact hash algorithm for auto-deduplication**: Need to confirm normalization (lowercase, accents removed, Unicode NFD decomposition, space collapse)
2. **Toast component API**: Finalize `Toast.tsx` props and positioning (top-right, consistent with Phase 4)
3. **Rate limit configuration**: Precise slowapi decorator placement for admin routes vs public routes
4. **JWT validation strategy**: Exact claims validation for admin token (issuer, audience, expiration)
5. **Edit partial update semantics**: How existing values are preserved when form fields are left blank

## Technical Research Checklist

- [x] JWT auth pattern (Phase 1 D-05, D-06) — Bearer token in Authorization header, 401 if missing
- [x] Turnstile server verify (Phase 7) — endpoint, fail-closed, rate limit
- [x] DB CHECK `at_least_one_contact` (Phase 1 D-06) — IntegrityError handling
- [x] City filter chips (Phase 4) — reuse chip component pattern
- [x] 14-day expiry computation — `expires_at = created_at + timedelta(days=14)`
- [x] Slowapi rate limit integration — `REVEAL_RATE_LIMIT=10/min`, `LOGIN_RATE_LIMIT=5/min`
- [ ] Auto-deduplication hash algorithm — confirm normalization details
- [ ] Toast component final API — props, positioning, auto-dismiss
- [ ] Edit modal partial update — existing value preservation strategy
- [ ] Optimistic update rollback — error handling when refetch fails