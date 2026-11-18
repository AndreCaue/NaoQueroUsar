---
phase: 21-interface-de-chat-e-integracao-no-board
reviewed: 2026-11-17T00:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - frontend/vitest.config.ts
  - frontend/lib/chatApply.ts
  - frontend/lib/chatApply.test.ts
  - frontend/package.json
  - frontend/lib/api.ts
  - frontend/components/board/chat/ChatLauncher.tsx
  - frontend/components/board/chat/ChatPanel.tsx
  - frontend/components/board/chat/ChatThread.tsx
  - frontend/components/board/chat/ChatComposer.tsx
  - frontend/components/board/chat/ChatInterpretation.tsx
  - frontend/components/board/chat/ChatResultsList.tsx
  - frontend/components/board/chat/ChatResultItem.tsx
  - frontend/components/board/chat/ChatWidget.tsx
  - frontend/app/(public)/page.tsx
findings:
  critical: 0
  warning: 4
  info: 1
  total: 5
status: issues_found
---

# Phase 21: Code Review Report

**Reviewed:** 2026-11-17T00:00:00Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Reviewed the chat UI integration and supporting API/filter helpers at standard depth (per-file analysis with TypeScript/React checks and light cross-file context). The implementation is generally cohesive: request sequencing guards against stale responses, user content is rendered as React text nodes (no raw HTML injection observed), and board-apply mapping reuses `normalizeFilters` to keep URL/filter behavior consistent.

Four warnings were identified around accessibility/focus handling in the modal flows and error-handling robustness in `chatSearch`. No critical security, data-loss, or crash defects were found in the reviewed files.

`frontend/package-lock.json` was provided in scope but excluded from review as a lock file (non-source artifact) per review filtering rules.

## Warnings

### WR-01: Chat panel modal lacks focus trap and initial focus management

**File:** `frontend/components/board/chat/ChatPanel.tsx:21-66`
**Issue:** The chat UI implements a custom dialog (`role="dialog"`, `aria-modal="true"`) with overlay click and Escape-to-close handling, but it does not trap focus inside the panel or move focus into the dialog when opened. Keyboard and screen-reader users can tab to content outside the dialog while it is visually/modal-presented, unlike the native `<dialog>` + `showModal()` pattern used in `JobDetailDialog`.
**Fix:**
```tsx
// Option A (preferred): switch to a native <dialog> and mirror JobDetailDialog
// (showModal(), focus management, onClose, backdrop click handling).

// Option B: keep current structure but add focus management, e.g.:
const panelRef = useRef<HTMLElement>(null);
const closeButtonRef = useRef<HTMLButtonElement>(null);

useEffect(() => {
  if (!open) return;
  const previous = document.activeElement as HTMLElement | null;
  closeButtonRef.current?.focus();

  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
      return;
    }
    if (e.key !== "Tab") return;
    const root = panelRef.current;
    if (!root) return;
    const focusables = root.querySelectorAll<HTMLElement>(
      'a[href],button:not([disabled]),textarea,input,select,[tabindex]:not([tabindex="-1"])',
    );
    if (focusables.length === 0) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };

  document.addEventListener("keydown", onKeyDown);
  return () => {
    document.removeEventListener("keydown", onKeyDown);
    previous?.focus();
  };
}, [open, onClose]);
```

### WR-02: Focus is not restored to the chat result trigger after closing job details

**File:** `frontend/components/board/chat/ChatWidget.tsx:61,183-195`, `frontend/components/board/chat/ChatThread.tsx:224`, `frontend/components/board/chat/ChatResultsList.tsx:75`, `frontend/components/board/chat/ChatResultItem.tsx:16-19`
**Issue:** `ChatWidget` stores `detailTriggerRef` and attempts to restore focus on detail close, but the open path never receives the originating element: `ChatThread` calls `onOpenDetail(job)` and `ChatResultItem`'s button click invokes `onOpen(job)` without passing the button/trigger. As a result, closing the job detail dialog does not return keyboard focus to the "Ver detalhes" control that opened it.
**Fix:**
```tsx
// ChatResultItem.tsx
interface ChatResultItemProps {
  job: JobPublic;
  onOpen: (job: JobPublic, trigger: HTMLButtonElement) => void;
}

<button
  type="button"
  onClick={(e) => onOpen(job, e.currentTarget)}
  ...
>

// Propagate trigger through ChatResultsList/ChatThread callbacks:
// onOpenDetail: (job: JobPublic, trigger: HTMLElement | null) => void
// ...
onOpenDetail={(job, trigger) => handleOpenDetail(job, trigger)}
```

### WR-03: `chatSearch` does not handle invalid JSON success responses consistently

**File:** `frontend/lib/api.ts:811-838`
**Issue:** On non-OK responses `chatSearch` normalizes errors through `readError`/`ApiError`, but on success it returns `res.json()` directly without guarding parse failures. A 200 response with malformed/non-JSON content will throw a raw parsing error (not an `ApiError`), unlike `revealContact` which converts parse failures into a typed transport/reveal error. This creates inconsistent error handling for callers and makes failure classification harder.
**Fix:**
```ts
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }

  try {
    return (await res.json()) as ChatSearchResponse;
  } catch {
    throw new ApiError(
      "Não foi possível buscar agora. Verifique sua conexão e tente novamente.",
      0,
    );
  }
```

### WR-04: Message length constraint is enforced only at submit time

**File:** `frontend/components/board/chat/ChatComposer.tsx:29-41,68-97`
**Issue:** The composer rejects messages over 400 characters when submitting, but the `<textarea>` has no `maxLength` constraint or live counter. Users can type far beyond the limit and only discover the problem on send, which is avoidable friction and can lead to repeated failed submissions.
**Fix:**
```tsx
const MAX_CHAT_MESSAGE_LENGTH = 400;

<textarea
  id="chat-message"
  rows={2}
  value={draft}
  maxLength={MAX_CHAT_MESSAGE_LENGTH}
  ...
/>

{draft.length > MAX_CHAT_MESSAGE_LENGTH - 40 ? (
  <p className="mt-2 text-sm text-fg-muted">
    {draft.length}/{MAX_CHAT_MESSAGE_LENGTH}
  </p>
) : null}
```
(If server-side validation is the source of truth, keep it and align the UI limit/counter to the same value.)

## Info

### IN-01: Vitest is scoped to `lib/**/*.test.ts` only

**File:** `frontend/vitest.config.ts:13-17`
**Issue:** The current Vitest include pattern only runs tests under `lib/**/*.test.ts`. This matches the newly added `chatApply` tests but means future component/hook tests outside `lib/` (for chat UI behavior, accessibility, or interaction regressions) will not run unless the config is expanded.
**Fix:**
```ts
test: {
  environment: "node",
  include: ["lib/**/*.test.ts", "components/**/*.test.{ts,tsx}", "app/**/*.test.{ts,tsx}"],
  globals: false,
},
```
(Adjust environment/setup as needed if DOM/component tests are added.)

---

_Reviewed: 2026-11-17T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_