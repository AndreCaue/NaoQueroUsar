---
phase: 28-polimento-ux-da-home
reviewed: 2026-11-22T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - backend/app/schemas/job.py
  - backend/app/services/cities.py
  - backend/app/crud/jobs.py
  - backend/app/crud/__init__.py
  - backend/app/api/v1/public.py
  - backend/tests/test_public_api.py
  - backend/tests/test_public_search.py
  - frontend/lib/api.ts
  - frontend/app/(public)/page.tsx
  - frontend/components/board/BoardToolbar.tsx
  - frontend/components/board/SortDropdown.tsx
  - frontend/components/board/JobCard.tsx
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 28: Code Review Report

**Reviewed:** 2026-11-22T00:00:00Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Reviewed the 13 phase-scoped files at standard depth (backend schemas/services/CRUD/API/tests and frontend board UI/API). The public read surface keeps the contact-free contract intact, SQL query construction is parameterized with explicit LIKE escaping, and Turnstile/rate-limit ordering in the reveal path is sound. The main defects are in the board toolbar client behavior: a native form submit path and stale debounce closures can cause spurious full reloads or overwrite newer filter state.

## Warnings

### WR-01: Search form submits natively on Enter

**File:** `frontend/components/board/BoardToolbar.tsx:128`, `frontend/components/board/BoardToolbar.tsx:84-99`
**Issue:** The search control is wrapped in `<form role="search">` with no `onSubmit` handler. The `Enter` branch in `handleKeyDown` commits the query via `router.replace`, but it does not call `event.preventDefault()`. Pressing Enter in a text input inside a form triggers native form submission, which can cause a full document navigation/reload alongside the SPA update. This is incorrect interactive behavior for the toolbar.
**Fix:**
```tsx
<form
  role="search"
  className="flex items-center gap-2"
  onSubmit={(event) => event.preventDefault()}
>
```

Alternatively, add `event.preventDefault()` in the `Enter` branch before committing.

### WR-02: Debounced search commit uses stale filter state and can re-fire

**File:** `frontend/components/board/BoardToolbar.tsx:35-41`, `frontend/components/board/BoardToolbar.tsx:50-82`, `frontend/components/board/BoardToolbar.tsx:110-121`
**Issue:** `commit` closes over the current `filters` prop, but the debounce effect depends only on `[value]` and intentionally omits `commit`/`filters`. A pending timeout therefore captures stale filter state. If the user changes city/sort (or other URL state) while typing, the delayed commit can rebuild the URL from stale filters and overwrite the newer selection. The same stale-closure path also allows an unnecessary duplicate commit when Enter/Escape/clear updates `value` to a trimmed value: the effect re-runs, sees `trimmed !== filters.q` against the still-old server prop, and schedules another timeout; because `filters.q` is not a dependency, that timeout may still fire after the server state catches up.
**Fix:**
```tsx
const filtersRef = useRef(filters);
filtersRef.current = filters;

const commit = (patch: Partial<Filters>) => {
  const next = { ...filtersRef.current, page: 1, vaga: null, ...patch };
  startTransition(() => {
    router.replace(buildBoardHref(next), { scroll: false });
  });
};
```

Also guard the debounce effect against re-scheduling when the value already matches the committed/server query, and include the dependencies needed for the chosen strategy (or keep a ref-based stable commit) so pending timers cannot apply stale URL state.

## Info

### IN-01: `loginAdmin` comment claims sessionStorage persistence

**File:** `frontend/lib/api.ts:167-171`
**Issue:** The JSDoc says "Returns JWT access_token stored in sessionStorage as \"nqu_admin_token\".", but `loginAdmin` only validates and returns the token; it does not write to `sessionStorage`. The comment overstates the function's behavior and can mislead callers during maintenance.
**Fix:**
```ts
/**
 * Login admin via password + Cloudflare Turnstile token.
 * Returns the JWT access token; callers are responsible for persisting it.
 */
export async function loginAdmin(password: string, cfToken: string): Promise<string> {
```

---

_Reviewed: 2026-11-22T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
