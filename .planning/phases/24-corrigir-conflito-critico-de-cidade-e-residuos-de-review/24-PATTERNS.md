# Phase 24: Corrigir conflito crítico de cidade e resíduos de review - Pattern Map

**Mapped:** 2026-11-21
**Files analyzed:** 5 primary targets (+ 4 preserve/verify integration points)
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/services/intent/mapper.py` | service (deterministic mapper) | transform | `backend/app/services/intent/mapper.py` (self; existing patterns in same module) | exact |
| `backend/tests/test_intent_mapper.py` | test | N/A | `backend/tests/test_intent_mapper.py` (self; existing test style) | exact |
| `frontend/components/board/chat/ChatWidget.tsx` | component (client orchestrator) | event-driven / UI state | `frontend/components/board/chat/ChatWidget.tsx` (self; existing trigger/focus flow) | exact |
| `frontend/components/board/chat/ChatPanel.tsx` | component (dialog/panel UI) | UI state | `frontend/components/board/chat/ChatPanel.tsx` (self; existing open/focus semantics) | exact |
| `frontend/lib/chatApply.ts` | utility | transform | `frontend/lib/chatApply.ts` (self) | exact (preserve, no change expected) |

**Verify/preserve only (integration points, no planned change):**

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `frontend/components/board/chat/ChatThread.tsx` | component | event-driven | Trigger already propagated to `onOpenDetail(job, trigger)`; preserve. |
| `frontend/components/board/chat/ChatResultsList.tsx` | component | event-driven | Pass-through trigger chain; preserve. |
| `frontend/components/board/chat/ChatResultItem.tsx` | component | event-driven | Originates trigger via `onClick={(e) => onOpen(job, e.currentTarget)}`; preserve. |
| `frontend/components/board/JobDetailDialog.tsx` | component (native dialog) | UI state | Canonical native `<dialog>.showModal()`; WR-01 must work with it, not replace it. |
| `frontend/lib/chatApply.test.ts` | test | N/A | Existing CL-05 gating coverage; preserve/no regression. |

## Pattern Assignments

### `backend/app/services/intent/mapper.py` (service, transform)

**Analog:** self (`backend/app/services/intent/mapper.py`) — deterministic, server-authoritative mapping. LLM candidate is untrusted; mapper computes safe `applied_params`, `field_statuses`, `limitations`, `meta`.

**Imports / module pattern** (lines 1-25):
```python
"""Deterministic, server-authoritative intent mapping (INT-03, D-01..D-12,D-15).

LLM output is treated as an untrusted candidate ("understood" proposal). This
module computes the final contract: normalized understood intent, per-field
statuses (aplicado/ignorado/aproximado + reason), and safe `applied_params`
compatible with public search (`list_published(q, city, sort)`).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.services.cities import resolve_city
from app.services.intent.schema import (
    AppliedParams,
    FieldAssessment,
    FieldStatus,
    IntentContract,
    IntentLLMOutput,
    IntentSalary,
    UnderstoodIntent,
)
```

**Canonical raw-city detection pattern — reuse for CR-01** (lines 34-97):
```python
_RAW_TEXT_CITY_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    ("São Paulo", (re.compile(r"\bsp\b"), re.compile(r"\bsao\s+paulo\b"))),
    ("Rio de Janeiro", (re.compile(r"\brj\b"), re.compile(r"\brio\s+de\s+janeiro\b"))),
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

def _detect_city_from_raw_text(raw_text: str) -> tuple[str | None, str]:
    """Detect unambiguous whitelist city mentions from raw text (accent-insensitive)."""
    normalized = _strip_accents_lower(raw_text or "")
    if not normalized.strip():
        return None, "missing"

    matches: list[str] = []
    for canonical, patterns in _RAW_TEXT_CITY_PATTERNS:
        if any(pattern.search(normalized) for pattern in patterns):
            matches.append(canonical)

    distinct = list(dict.fromkeys(matches))
    if len(distinct) == 1:
        return distinct[0], "normalized"
    if len(distinct) > 1:
        return None, "conflict_resolved"
    return None, "missing"
```

**CR-01 gap — current candidate-present city flow to replace/integrate** (lines 308-363):
```python
    # ----- CITY (whitelist only, D-05) -----
    # simple conflict heuristic: multiple known distinct city tokens in raw text
    lowered = _strip_accents_lower(raw)
    mentioned = []
    for token, canon in (
        ("sao paulo", "São Paulo"),
        ("rio de janeiro", "Rio de Janeiro"),
        ("belo horizonte", "Belo Horizonte"),
        ("campinas", "Campinas"),
    ):
        if token in lowered:
            mentioned.append(canon)
    distinct_whitelist = {m for m in mentioned if m in {"São Paulo", "Rio de Janeiro", "Belo Horizonte"}}
    city_conflict = len(distinct_whitelist) > 1

    candidate_city_present = bool(candidate.city and str(candidate.city).strip())

    if city_conflict:
        applied_city = None
        city_status = FieldStatus.IGNORADO
        city_reason_code = "conflict_resolved"
        city_reason = "Múltiplas cidades incompatíveis; nenhuma cidade aplicada."
    else:
        applied_city, city_reason_code = _resolve_city_safe(candidate.city, raw)
        if applied_city:
            city_status = FieldStatus.APLICADO
            ...
```
**Copy/adapt rule (D-01/D-02/D-03):** Use `_detect_city_from_raw_text(raw)` as canonical raw signal. If `raw_city_reason == "conflict_resolved"` OR raw-detected supported city differs from resolved candidate supported city, return `city=None, FieldStatus.IGNORADO, reason_code="conflict_resolved"`. Preserve `not_in_whitelist` for non-whitelist candidate when no raw conflict promotes wrong city; preserve candidate-absent safe apply.

**WR-03 gap — substring influence detection to replace** (lines 446-456):
```python
        if applied_q:
            aq = _strip_accents_lower(applied_q)
            for t in raw_terms:
                for tok in _normalize_whitespace(str(t)).split(" "):
                    k = _strip_accents_lower(tok)
                    if k and k in aq:
                        influenced = True
                        break
                if influenced:
                    break
```
**Copy/adapt rule (D-05/D-06):** Replace `aq` string with token-set membership, e.g. `aq_tokens = set(_strip_accents_lower(applied_q).split())` and check `k in aq_tokens`. Preserve normalization, term extraction, status/reason semantics.

**Field status helper pattern** (lines 208-224):
```python
def _build_field_status(
    field: str,
    understood: Any,
    applied: Any,
    status: FieldStatus | str,
    reason_code: str,
    reason: str,
) -> FieldAssessment:
    status_value = status.value if isinstance(status, FieldStatus) else status
    return FieldAssessment(
        field=field,
        understood=understood,
        applied=applied,
        status=status_value,  # pydantic will coerce to Enum
        reason_code=reason_code,
        reason=reason,
    )
```

---

### `backend/tests/test_intent_mapper.py` (test, N/A)

**Analog:** self (`backend/tests/test_intent_mapper.py`) — deterministic pytest cases, helper `_field`, `IntentLLMOutput.model_validate(...)`, `map_intent(..., raw_text=...)`.

**Imports and helper pattern** (lines 1-18):
```python
"""Deterministic intent mapper tests (INT-03, D-01..D-12,D-15).

Covers empty intent, whitelist/city normalization, explicit-only sort,
conflicts, non-native approximation/ignored statuses, and applied_params safety.
"""

from __future__ import annotations

from app.services.intent import IntentLLMOutput, IntentSalary, map_intent, build_empty_intent
from app.services.intent.schema import IntentContractType, IntentMode, IntentSeniority


def _field(contract, name: str):
    for fs in contract.field_statuses:
        if fs.field == name:
            return fs
    raise AssertionError(f"missing field status: {name}")
```

**CR-01 regression shape — copy existing conflict/city assertion style** (lines 298-352):
```python
def test_absent_candidate_raw_text_applies_supported_city_safely() -> None:
    c1 = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga de analista em São Paulo")
    assert c1.applied_params.city == "São Paulo"
    fs1 = _field(c1, "city")
    assert fs1.status == "aplicado"
    assert fs1.reason_code == "normalized"
    assert fs1.understood is None
    ...

def test_absent_candidate_raw_text_city_safeguards() -> None:
    conflict = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga em sp ou rj")
    assert conflict.applied_params.city is None
    fs_conflict = _field(conflict, "city")
    assert fs_conflict.status == "ignorado"
    assert fs_conflict.reason_code == "conflict_resolved"
    ...
    # present non-whitelist candidate remains not_in_whitelist (existing MVP behavior)
    present = map_intent(IntentLLMOutput.model_validate({"city": "Campinas"}), raw_text="vaga em campinas")
    assert present.applied_params.city is None
    assert _field(present, "city").reason_code == "not_in_whitelist"
```

**WR-03 / non-native approximation assertion shape** (lines 84-116):
```python
def test_non_native_fields_are_approximated_in_q_or_ignored_without_structured_filter() -> None:
    contract = map_intent(
        IntentLLMOutput.model_validate(
            {
                "q": "React",
                "seniority": {"value": "pleno", "raw": "pleno"},
                "contract_type": {"value": "clt", "raw": "CLT"},
                "salary": {"min": 8000, "max": None, "currency": "BRL"},
            }
        ),
        raw_text="vaga dev react pleno clt salario 8000",
    )

    assert contract.applied_params.q is not None
    q_lower = contract.applied_params.q.lower()
    assert "react" in q_lower
    ...
    fs_seniority = _field(contract, "seniority")
    assert fs_seniority.status == "aproximado"
    assert fs_seniority.reason_code == "textual_approximation_in_q"
```

**CR-01 required new cases (D-04):** cover named audit examples (`"vaga em sp ou rio de janeiro"` + candidate `SP` => `city=None`, `ignorado`, `conflict_resolved`; `"vaga remoto ou são paulo"` + candidate `Remoto` => not applied), aliases/abbrev/remoto conflict matrix, same canonical agreement (raw SP + candidate "São Paulo" applies), candidate absent still applies, non-whitelist candidate stays `not_in_whitelist`, raw-vs-candidate supported-city divergence => `conflict_resolved`. **WR-03 case:** token-set membership should not false-positive on substring inside larger token.

---

### `frontend/components/board/chat/ChatWidget.tsx` (component, event-driven/UI state)

**Analog:** self (`frontend/components/board/chat/ChatWidget.tsx`) — owns chat open/close, request sequencing, detail open/close, focus restoration, and canonical board apply.

**Trigger/focus refs and detail flow — WR-01 gap** (lines 92-96, 282-294):
```tsx
  const requestSeq = useRef(0);
  const activeRequestRef = useRef(0);
  const idRef = useRef(0);
  const detailTriggerRef = useRef<HTMLElement | null>(null);
...
  const handleOpenDetail = (job: JobPublic, trigger?: HTMLElement | null) => {
    detailTriggerRef.current = trigger ?? null;
    setIsOpen(false);
    setSelectedJob(job);
    syncVagaParam(job.id);
  };

  const handleCloseDetail = () => {
    setSelectedJob(null);
    syncVagaParam(null);
    const trigger = detailTriggerRef.current;
    window.requestAnimationFrame(() => trigger?.focus());
  };
```
**Copy/adapt rule (D-07/D-08):** Do not unmount chat panel before detail opens; keep panel mounted behind native dialog so trigger remains in DOM. On close, restore focus to `trigger` only if `trigger?.isConnected`; otherwise focus a stable mounted chat fallback (e.g. ChatPanel close button). Never fall back to `document.body`. Keep native `JobDetailDialog` flow and `syncVagaParam`.

**Canonical chat-apply pattern — preserve** (lines 271-280):
```tsx
  const handleApplyToBoard = () => {
    if (!lastResponse) return;
    if (!canApplyChatToBoard(lastResponse.interpretation)) return;
    const filters = appliedParamsToBoardFilters(
      lastResponse.interpretation.applied_params,
    );
    const href = buildBoardHref({ ...filters, page: 1, vaga: null });
    router.replace(href, { scroll: false });
    setIsOpen(false);
  };
```

**Mounted-panel render pattern — WR-01 integration point** (lines 302-349):
```tsx
  return (
    <>
      {!isOpen && !selectedJob ? (
        <ChatLauncher
          onOpen={() => {
            if (!chatEnabled) return;
            setIsOpen(true);
          }}
        />
      ) : null}
      <ChatPanel
        open={isOpen}
        titleId="chat-panel-title"
        onClose={() => setIsOpen(false)}
        composer={...}
      >
        ...
      </ChatPanel>
      {selectedJob ? (
        <JobDetailDialog job={selectedJob} open onClose={handleCloseDetail} />
      ) : null}
    </>
  );
```
**Note:** If ChatPanel stays mounted while detail is open, `isOpen` and launcher visibility conditions must be adjusted carefully to avoid UX regressions and to satisfy D-07.

---

### `frontend/components/board/chat/ChatPanel.tsx` (component, UI state)

**Analog:** self (`frontend/components/board/chat/ChatPanel.tsx`) — chat dialog semantics, close button ref, ESC handling, focus-on-open.

**Close/focus semantics — WR-01 fallback compatibility** (lines 21-41, 60-68):
```tsx
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  useEffect(() => {
    if (!open) return;
    closeButtonRef.current?.focus();
  }, [open]);

  if (!open) return null;
...
            <button
              type="button"
              ref={closeButtonRef}
              onClick={onClose}
              className="inline-flex h-11 min-h-11 items-center justify-center rounded-lg px-3 text-sm font-semibold text-fg-muted transition-colors hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
            >
              Fechar chat
            </button>
```
**Copy/adapt rule (D-07/D-08):** Current `if (!open) return null` unmounts the panel and trigger descendants. For WR-01, panel may need to remain mounted while detail is open; if so, hide visually/aria appropriately without breaking dialog semantics or causing duplicate focus traps (WR-02 remains deferred). If ChatPanel close button is used as stable fallback, expose/focus it only when mounted and visible/appropriate; avoid focusing hidden controls.

---

### `frontend/lib/chatApply.ts` (utility, transform) — PRESERVE

**Analog:** self (`frontend/lib/chatApply.ts`).

**Canonical board-apply normalization/gating pattern** (lines 1-28):
```ts
import { normalizeFilters, type Filters } from "@/lib/filters";
import type { ChatAppliedParams, ChatInterpretation } from "@/lib/api";

export function appliedParamsToBoardFilters(applied: ChatAppliedParams): Filters {
  const normalized = normalizeFilters({
    q: (applied.q ?? "").trim(),
    city: (applied.city ?? "").trim().toLowerCase(),
    sort: applied.sort ?? "recentes",
    page: "1",
    vaga: "",
  });
  return { ...normalized, page: 1, vaga: null };
}

export function canApplyChatToBoard(interpretation: ChatInterpretation): boolean {
  if (
    interpretation.meta?.degraded === true ||
    interpretation.meta?.degradation_reason === "chat_disabled"
  ) {
    return false;
  }
  const normalized = appliedParamsToBoardFilters(interpretation.applied_params);
  return (
    normalized.q.trim().length > 0 ||
    normalized.city !== null ||
    normalized.sort === "antigas"
  );
}
```
**Rule:** No behavior change. Any mapper/UI fix must preserve this contract and existing tests in `frontend/lib/chatApply.test.ts`.

## Shared Patterns

### Server-authoritative deterministic mapping
**Source:** `backend/app/services/intent/mapper.py` lines 1-7, 259-539
**Apply to:** Any CR-01/WR-03 change in mapper.
```python
"""Deterministic, server-authoritative intent mapping (INT-03, D-01..D-12,D-15).
...
LLM output is treated as an untrusted candidate ("understood" proposal). This
module computes the final contract...
"""
```
**Rule:** Candidate is untrusted. Never apply conflicting/unsafe city. Preserve `FieldStatus`, reason codes, and `applied_params` compatibility with public search.

### Canonical city whitelist normalization
**Source:** `backend/app/services/cities.py` lines 11-28
**Apply to:** mapper city resolution; tests asserting canonical applied city.
```python
CITY_ALIASES: Final[dict[str, str]] = {
    "sao-paulo": "São Paulo",
    "sao paulo": "São Paulo",
    "são paulo": "São Paulo",
    "rio-de-janeiro": "Rio de Janeiro",
    "rio de janeiro": "Rio de Janeiro",
    "belo-horizonte": "Belo Horizonte",
    "belo horizonte": "Belo Horizonte",
    "remoto": "Remoto",
}

def resolve_city(value: str | None) -> str | None:
    if not value:
        return None
    return CITY_ALIASES.get(value.strip().lower())
```

### Deterministic pytest regression style
**Source:** `backend/tests/test_intent_mapper.py` lines 13-18, 298-352
**Apply to:** all new mapper tests.
```python
def _field(contract, name: str):
    for fs in contract.field_statuses:
        if fs.field == name:
            return fs
    raise AssertionError(f"missing field status: {name}")
```
**Rule:** Assert `applied_params`, `field_statuses` status/reason_code, and limitations/meta as needed. Use `IntentLLMOutput.model_validate({...})` and `raw_text=...`.

### Chat trigger propagation / focus restoration
**Source:** `frontend/components/board/chat/ChatResultItem.tsx` line 18; `ChatResultsList.tsx` line 75; `ChatThread.tsx` line 110; `ChatWidget.tsx` lines 282-294.
**Apply to:** WR-01 only.
```tsx
// ChatResultItem.tsx:18
onClick={(e) => onOpen(job, e.currentTarget)}

// ChatWidget.tsx:282-294
const handleOpenDetail = (job: JobPublic, trigger?: HTMLElement | null) => {
  detailTriggerRef.current = trigger ?? null;
  setIsOpen(false);
  setSelectedJob(job);
  syncVagaParam(job.id);
};
const handleCloseDetail = () => {
  setSelectedJob(null);
  syncVagaParam(null);
  const trigger = detailTriggerRef.current;
  window.requestAnimationFrame(() => trigger?.focus());
};
```
**Rule:** Preserve trigger chain. Fix must ensure focus lands on mounted/stable control (`isConnected` trigger or stable fallback), never `document.body`.

### Native dialog canonical detail flow
**Source:** `frontend/components/board/JobDetailDialog.tsx` lines 54-66, 90-99
**Apply to:** WR-01 verification; no dialog replacement.
```tsx
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      dialog.focus();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);
...
    <dialog
      ref={dialogRef}
      tabIndex={-1}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) {
          dialogRef.current?.close();
        }
      }}
      ...
    >
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `frontend/lib/chatFocus.test.ts` (possible, discretionary) | test helper/seam for WR-01 | N/A | Repo Vitest config only includes `lib/**/*.test.ts` (`frontend/vitest.config.ts` lines 13-17). No existing component-test harness for `components/**/*.tsx`. If automated WR-01 coverage is added, prefer a small pure helper under `lib/` with node-vitest tests; otherwise document explicit keyboard/manual verification. |

## Metadata

**Analog search scope:** `backend/app/services/intent/`, `backend/tests/test_intent_*.py`, `frontend/components/board/chat/`, `frontend/components/board/JobDetailDialog.tsx`, `frontend/lib/chatApply.*`, `frontend/lib/filters.ts`, `frontend/vitest.config.ts`
**Files scanned:** 14
**Pattern extraction date:** 2026-11-21
