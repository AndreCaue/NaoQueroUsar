---
phase: 23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3
reviewed: 2026-11-20T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - backend/app/services/intent/mapper.py
  - backend/tests/test_intent_mapper.py
  - frontend/lib/api.ts
  - frontend/lib/chatApply.ts
  - frontend/lib/chatApply.test.ts
  - frontend/components/board/chat/ChatPanel.tsx
  - frontend/components/board/chat/ChatWidget.tsx
  - frontend/components/board/chat/ChatThread.tsx
  - frontend/components/board/chat/ChatResultsList.tsx
  - frontend/components/board/chat/ChatResultItem.tsx
findings:
  critical: 1
  warning: 3
  info: 0
  total: 4
status: issues_found
---

# Phase 23: Code Review Report

**Reviewed:** 2026-11-20T00:00:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Standard review of the phase 23 mapper hardening and chat parsing/gating/focus-a11y surfaces. The backend intent mapper is mostly deterministic and defensive, but it can still apply a city filter when the raw text contains an ambiguous city choice expressed via aliases/abbreviations while the LLM candidate already provides a city. The frontend chat flow handles degraded/disabled responses and request races reasonably well, but modal focus management is incomplete: detail-close focus restoration targets an unmounted trigger and the chat dialog does not trap or restore focus. One mapper classification path uses substring matching that can mislabel non-native field influence.

## Critical Issues

### CR-01: Candidate city bypasses raw-text alias/remote conflict detection

**File:** `backend/app/services/intent/mapper.py:309-364`
**Issue:** City conflict pre-check only inspects full-name tokens (`sao paulo`, `rio de janeiro`, `belo horizonte`, `campinas`) and ignores aliases/abbreviations/remoto patterns. When a candidate city is present and that weak pre-check does not flag a conflict, the mapper resolves/applies the candidate via `_resolve_city_safe(...)` without honoring `_detect_city_from_raw_text(...)`'s conflict result. This can apply the wrong city on ambiguous input (incorrect filter behavior), e.g. raw `"vaga em sp ou rio de janeiro"` with candidate `city="SP"` applies `São Paulo`, or raw `"vaga remoto ou são paulo"` with candidate `city="Remoto"` applies `Remoto`, even though the text is conflicting.
**Fix:**
```python
# In map_intent(), replace the split conflict/resolution logic with a raw-text-aware guard:
raw_detected_city, raw_city_reason = _detect_city_from_raw_text(raw)
candidate_city_present = bool(candidate.city and str(candidate.city).strip())

if raw_city_reason == "conflict_resolved":
    applied_city = None
    city_status = FieldStatus.IGNORADO
    city_reason_code = "conflict_resolved"
    city_reason = "Múltiplas cidades mencionadas geraram conflito; nenhuma cidade aplicada."
else:
    # Keep whitelist-only resolution, but prefer explicit raw-text conflict safety above.
    applied_city, city_reason_code = _resolve_city_safe(candidate.city, raw)
    # ...existing status/reason mapping...
```

(Alternatively, fold alias-aware conflict detection into the pre-check so abbreviations/remoto conflicts are caught even when `candidate.city` is present, and add regression tests for these cases.)

## Warnings

### WR-01: Closing chat job detail restores focus to an unmounted trigger

**File:** `frontend/components/board/chat/ChatWidget.tsx:282-294`, `frontend/components/board/chat/ChatPanel.tsx:40-75`
**Issue:** `handleOpenDetail` closes the chat panel and stores the clicked result item as `detailTriggerRef` before opening `JobDetailDialog`. Because `ChatPanel` returns `null` when `open` is false, the result item button is unmounted. `handleCloseDetail` then schedules `trigger?.focus()` on a detached node, so keyboard focus is lost after closing the detail dialog (focus falls back to `document.body`). This breaks the chat-detail focus flow relevant to CL-05.
**Fix:**
```tsx
const handleOpenDetail = (job: JobPublic, trigger?: HTMLElement | null) => {
  detailTriggerRef.current = trigger ?? null;
  // Keep panel mounted/open behind the dialog, or restore to a stable fallback on close.
  setSelectedJob(job);
  syncVagaParam(job.id);
};

const handleCloseDetail = () => {
  setSelectedJob(null);
  syncVagaParam(null);
  setIsOpen(true); // if keeping chat context
  const trigger = detailTriggerRef.current;
  window.requestAnimationFrame(() => {
    if (trigger && trigger.isConnected) {
      trigger.focus();
      return;
    }
    // stable fallback (e.g. expose launcher ref/id or focus manual search anchor)
    document.querySelector<HTMLButtonElement>('[aria-label="Buscar vagas no chat"]')?.focus();
  });
};
```

(Choose one consistent strategy: keep the chat open behind the dialog so the original trigger remains mounted, or always restore focus to a stable mounted control.)

### WR-02: Chat modal dialog does not trap focus or restore focus on close

**File:** `frontend/components/board/chat/ChatPanel.tsx:23-75`
**Issue:** The panel sets initial focus to the close button and closes on `Escape`, but it does not trap `Tab`/`Shift+Tab` within the dialog and does not restore focus to the invoking launcher/control when closed. With `aria-modal="true"` and an underlying interactive page, keyboard and assistive-technology users can move focus outside the modal and lose their place after dismissal.
**Fix:**
```tsx
// Track opener and restore on close/unmount when transitioning open -> closed.
const openerRef = useRef<HTMLElement | null>(null);
useEffect(() => {
  if (open) openerRef.current = document.activeElement as HTMLElement | null;
  return () => {
    if (open) openerRef.current?.focus?.();
  };
}, [open]);

// Add a keydown handler on the dialog container to cycle focus within focusable elements
// (or replace with a vetted dialog primitive that provides focus trapping/inert background).
```

(Implement a minimal focus trap for the dialog's focusable elements and ensure `onClose` paths return focus to the launcher.)

### WR-03: Non-native approximation influence uses substring matching over the full query string

**File:** `backend/app/services/intent/mapper.py:446-459`
**Issue:** Influence detection checks `if k and k in aq:` where `aq` is the full lowercased `applied_q` string. Because this is substring-based (not token-based), a term token can match inside an unrelated word, causing a non-native field to be incorrectly classified as `aproximado` / `textual_approximation_in_q` (and adding related limitations) even when its token was not actually applied as a term.
**Fix:**
```python
if applied_q:
    aq_tokens = set(_strip_accents_lower(applied_q).split())
    for t in raw_terms:
        for tok in _normalize_whitespace(str(t)).split(" "):
            k = _strip_accents_lower(tok)
            if k and k in aq_tokens:
                influenced = True
                break
        if influenced:
            break
```

---

_Reviewed: 2026-11-20T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
