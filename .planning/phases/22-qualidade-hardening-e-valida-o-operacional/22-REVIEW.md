---
phase: 22-qualidade-hardening-e-valida-o-operacional
reviewed: 2026-11-18T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - frontend/lib/cities.ts
  - frontend/lib/cities.test.ts
  - frontend/components/board/BoardToolbar.tsx
  - frontend/lib/filters.ts
  - backend/app/services/intent/mapper.py
  - backend/app/services/cities.py
  - backend/app/services/intent/parser.py
  - backend/tests/test_intent_mapper.py
  - backend/tests/test_intent_parser.py
  - backend/tests/test_chat_search_api.py
findings:
  critical: 0
  warning: 4
  info: 0
  total: 4
status: issues_found
---

# Phase 22: Code Review Report

**Reviewed:** 2026-11-18T00:00:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Adversarial standard-depth review of the Phase 22 gap-closure (plan 22-04) city-recognition changes: frontend supported-city text resolution/promotion (`resolveCitySlugFromText`, `BoardToolbar` commit paths) and backend deterministic raw-text whitelist fallback in intent mapping (`_detect_city_from_raw_text`, `_resolve_city_safe`/`map_intent`) with related tests.

The core direction is sound (exact/normalized matching, whitelist-only application, conflict safeguards, preserved canonical board params and `JobPublic`/no-contact behavior in touched paths). However, the toolbar debounce/promotion logic introduces correctness races (stale timer/closure and an extra debounced commit after programmatic clear) that can revert or drop the intended `city`/`q` state under quick interactions. The mapper fallback also treats bare `rio` as `Rio de Janeiro` in free text, which can misapply the city filter for other "Rio ..." place names.

No BLOCKER security, data-loss, or contact-exposure defects were identified in the reviewed implementation.

## Warnings

### WR-01: Debounced search does not clear a pending timer when input already matches committed `q`

**Severity:** WARNING
**File:** `frontend/components/board/BoardToolbar.tsx:48-56,71-78`
**Issue:** In the debounce `useEffect`, when `trimmed === filters.q` the effect returns early without clearing `timerRef.current`. If the user types to an intermediate value (scheduling a timer) and then quickly edits back to the currently committed `q` before the delay elapses, the stale timer still fires and commits the intermediate `q` (or a stale city promotion), reverting the user's intent and potentially triggering unwanted navigation/state updates.
**Fix:**
```tsx
useEffect(() => {
  const trimmed = value.trim();
  if (trimmed === filters.q) {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    return;
  }
  if (timerRef.current) {
    clearTimeout(timerRef.current);
  }
  timerRef.current = setTimeout(() => {
    // ...
  }, DEBOUNCE_MS);
  return () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [value]);
```

### WR-02: Debounced commit captures a stale `filters` closure and can override newer board state

**Severity:** WARNING
**File:** `frontend/components/board/BoardToolbar.tsx:32-37,48-78`
**Issue:** `commit` spreads `filters` from the render scope and is invoked by a `setTimeout` scheduled in an effect that depends only on `[value]`. When the timer fires, it uses the `filters` snapshot captured when that effect ran, not the latest props. If `filters` changes before the timer fires (for example, a user clicks a city chip or another committed navigation updates state), the delayed commit can overwrite newer `city/sort/page` context with stale values (except the fields explicitly patched), causing incorrect canonical URL/state.
**Fix:**
```tsx
const filtersRef = useRef(filters);
useEffect(() => {
  filtersRef.current = filters;
}, [filters]);

const commit = (patch: Partial<Filters>) => {
  const next = { ...filtersRef.current, page: 1, vaga: null, ...patch };
  startTransition(() => {
    router.replace(buildBoardHref(next), { scroll: false });
  });
};

// Ensure debounce scheduling/guards account for latest state as needed
// (and keep timer cleanup consistent with WR-01).
```

### WR-03: City promotion clears the input and can schedule a follow-up debounced commit that races/drops the promoted city

**Severity:** WARNING
**File:** `frontend/components/board/BoardToolbar.tsx:58-70,86-95`
**Issue:** On a supported-city match, the debounce/Enter paths commit `{ q: "", city: matchedCity }` and then call `setValue("")`. Because the debounce effect runs on `[value]` and compares `trimmed` only against `filters.q`, clearing the input before `filters.q` reflects the committed empty query can make the effect treat `""` as a new user edit and schedule another timeout that commits `{ q: "" }` (without `city`) using a stale `filters` snapshot. This introduces a race/redundant navigation that can drop the promoted `city=<slug>` or fight the intended state during the async server update window.
**Fix:**
```tsx
const suppressDebounceRef = useRef(false);

// In debounce effect, before scheduling:
if (suppressDebounceRef.current) {
  suppressDebounceRef.current = false;
  if (timerRef.current) {
    clearTimeout(timerRef.current);
    timerRef.current = null;
  }
  return;
}

// When promoting a matched city (debounce timeout or Enter):
suppressDebounceRef.current = true;
commit({ q: "", city: matchedCity });
lastCommittedRef.current = "";
setValue("");
```
Also ensure the effect clears pending timers on the `trimmed === filters.q` path (WR-01) so programmatic sync states do not leave stale timers behind.

### WR-04: Raw-text city fallback treats bare `rio` as `Rio de Janeiro`, risking false positives in NL queries

**Severity:** WARNING
**File:** `backend/app/services/intent/mapper.py:34-46,81-100`
**Issue:** `_RAW_TEXT_CITY_PATTERNS` maps the token pattern `\brio\b` to `Rio de Janeiro` and `_detect_city_from_raw_text` applies a canonical city when exactly one supported match is found in absent-candidate raw text. In longer natural-language messages this can misclassify other Brazilian place names containing the word `rio` (for example, "Rio Grande do Sul", "Rio Branco") as `Rio de Janeiro`, producing an incorrect applied `city`/`field_status` even though the query is not an unambiguous supported-city request. This is less constrained than the frontend's exact full-text promotion and can degrade deterministic search correctness.
**Fix:**
```python
_RAW_TEXT_CITY_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    ("São Paulo", (re.compile(r"\bsp\b"), re.compile(r"\bsao\s+paulo\b"))),
    (
        "Rio de Janeiro",
        (
            re.compile(r"\brj\b"),
            re.compile(r"\brio\s+de\s+janeiro\b"),
            # Avoid bare "rio" matching "Rio Grande...", "Rio Branco", etc. in NL text.
            # (Keep explicit "rj"/"rio de janeiro"; handle exact "rio" only if desired
            # via a stricter, context-aware rule.)
        ),
    ),
    ("Belo Horizonte", (re.compile(r"\bbh\b"), re.compile(r"\bbelo\s+horizonte\b"))),
    (
        "Remoto",
        (
            re.compile(r"\bremoto\b"),
            re.compile(r"\bhome[\s-]?office\b"),
            re.compile(r"\btrabalho\s+remoto\b"),
        ),
    ),
)
```
If bare `rio` must remain supported, tighten it with negative lookaheads for common non-RJ continuations (e.g. `grande`, `branco`, `negro`, `claro`, `bonito`, `verde`) and add mapper tests for those negative cases.

---
_Reviewed: 2026-11-18T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
