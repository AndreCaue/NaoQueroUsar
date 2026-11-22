---
phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review
reviewed: 2026-11-21T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - backend/app/services/intent/mapper.py
  - backend/tests/test_intent_mapper.py
  - frontend/components/board/chat/ChatPanel.tsx
  - frontend/components/board/chat/ChatWidget.tsx
  - frontend/lib/chatFocus.test.ts
  - frontend/lib/chatFocus.ts
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 24: Code Review Report

**Reviewed:** 2026-11-21T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed the 6 phase-scoped files (intent mapper + tests, chat panel/widget, chat focus helper + tests) at standard depth. The city-conflict hardening in `mapper.py` covers the main CR-01 matrix and the frontend focus helper is small and well-tested. Findings focus on an uncovered city-conflict separator gap in the safety-critical mapper path, and accessibility/focus-management gaps in the custom chat dialog.

## Warnings

### WR-01: City conflict guard misses non-whitelist alternatives joined by "e" or comma

**File:** `backend/app/services/intent/mapper.py:321-354`
**Issue:** Non-whitelist-vs-supported conflict detection only sets `has_conflict_sep` for `ou|or|vs` and slash-adjacent supported-city patterns. When a supported whitelist city and a non-whitelist city are joined by `e` or a comma, `_detect_city_from_raw_text()` returns only the supported city, `has_conflict_sep` stays false, and the guard at lines 321-354 is skipped. The mapper can then apply the supported city instead of returning `conflict_resolved`. Example: `raw_text="vaga em sp e curitiba"` with absent candidate yields `applied_params.city == "São Paulo"`, while `raw_text="vaga em sp ou curitiba"` correctly yields `None/conflict_resolved`. This is a safety gap in the phase-24 city-conflict path.
**Fix:**
```python
# Extend separator detection carefully; "e" and commas can appear in normal phrases,
# so keep the existing supported/unsupported segment heuristic and add regression tests.
has_nl_conflict_sep = bool(re.search(r"\b(ou|or|vs|e)\b", normalized_raw))
has_comma_sep = "," in normalized_raw
has_conflict_sep = has_nl_conflict_sep or has_slash_city_alt or has_comma_sep

# Also update split_pattern below when has_comma_sep is true:
split_pattern = r"\b(?:ou|or|vs|e)\b|/|," if (has_slash_city_alt or has_comma_sep) else r"\b(?:ou|or|vs|e)\b"
```

Add regression tests before applying the fix, including false-positive guards such as `"analista e desenvolvedor em sp"` (should still apply SP, not conflict) and `"vaga em sp, pleno"` (should not create a city conflict). The fix should only trigger conflict when the non-supported side looks like a location token/phrase, not any arbitrary meaningful token.

### WR-02: Custom chat dialog has no keyboard focus trap

**File:** `frontend/components/board/chat/ChatPanel.tsx:45-80`
**Issue:** The panel declares `role="dialog"` and `aria-modal="true"`, but it does not trap Tab/Shift+Tab focus inside the dialog. Keyboard users can move focus to background page content while the modal overlay is visible. The project already uses native `<dialog>.showModal()` in `JobDetailDialog` for focus trapping; this custom dialog lacks equivalent containment.
**Fix:**
```tsx
// Add a focus-trap effect inside ChatPanel (or extract a small hook).
useEffect(() => {
  if (!open) return;
  const panel = panelRef.current;
  if (!panel) return;

  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key !== "Tab") return;
    const focusable = panel.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    );
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };

  document.addEventListener("keydown", onKeyDown);
  return () => document.removeEventListener("keydown", onKeyDown);
}, [open]);
```

Alternatively, convert ChatPanel to a native `<dialog>` and use `showModal()` like `JobDetailDialog`, preserving the existing visual layout and dismissible behavior.

### WR-03: Chat focus restoration is incomplete after panel/detail close

**File:** `frontend/components/board/chat/ChatWidget.tsx:289-301, 314-327`
**Issue:** `handleCloseDetail()` restores focus to the stored trigger or `#chat-panel-close`, but when the trigger is disconnected and the chat panel is not mounted (e.g. chat disabled path, or panel closed), `getChatDetailCloseFocusTarget()` returns `null` and focus falls to `body`. Separately, closing the chat panel does not restore focus to the launcher; `ChatLauncher` is conditionally unmounted while open and remounted on close, so keyboard focus is lost after close/Escape.
**Fix:**
```tsx
const launcherRef = useRef<HTMLButtonElement | null>(null);
const wasOpenRef = useRef(false);

useEffect(() => {
  if (wasOpenRef.current && !isOpen && !selectedJob) {
    window.requestAnimationFrame(() => {
      launcherRef.current?.focus();
    });
  }
  wasOpenRef.current = isOpen;
}, [isOpen, selectedJob]);

// Pass launcherRef to ChatLauncher, and make it accept/ref-forward it.
```

For detail close, keep the existing trigger/fallback logic but add a final stable fallback (e.g. launcher ref or a known page focus target) before giving up:

```tsx
const target = getChatDetailCloseFocusTarget(
  trigger,
  fallback instanceof HTMLElement ? fallback : launcherRef.current,
);
window.requestAnimationFrame(() => {
  target?.focus();
});
```

## Info

### IN-01: `build_empty_intent` accepts unused `raw_text` parameter

**File:** `backend/app/services/intent/mapper.py:226`
**Issue:** `build_empty_intent(raw_text: str | None = None, reason_code: str = "empty_input")` never uses `raw_text`. This adds a small API surface/noise and can mislead callers into thinking the raw text affects the empty contract.
**Fix:**
```python
def build_empty_intent(reason_code: str = "empty_input") -> IntentContract:
    """Return a valid empty/clear intent contract with no applied filters (D-15)."""
    ...
```

If external callers already pass `raw_text`, keep a backward-compatible signature temporarily and document/deprecate the unused argument.

### IN-02: Load-more chat-disabled path does not mirror send-path turn update

**File:** `frontend/components/board/chat/ChatWidget.tsx:237-251`
**Issue:** When `chatSearch` returns a disabled response during load-more, the code clears active query/turn state and disables chat, but it does not update the corresponding turn in `turns` as the send path does at lines 157-179. Today this is mostly invisible because the widget hides itself when chat is disabled, but the state transition is inconsistent and easier to regress.
**Fix:**
```ts
setTurns((prev) =>
  prev.map((t) =>
    t.id === turnAtStart
      ? { ...t, status: "done", response: disabledResponse, error: undefined }
      : t,
  ),
);
```

Consider extracting a shared `applyDisabledChatResponse(...)` helper used by both send and load-more paths to keep state transitions identical.

---

_Reviewed: 2026-11-21T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_