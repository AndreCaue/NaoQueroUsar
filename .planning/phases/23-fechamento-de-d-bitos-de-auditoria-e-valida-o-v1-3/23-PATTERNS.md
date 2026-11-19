# Phase 23: Fechamento de débitos de auditoria e validação v1.3 - Pattern Map

**Mapped:** 2026-11-19
**Phase scope:** Closure/hardening/audit-reconciliation only (no new product capabilities). CL-01..CL-05.
**Files analyzed:** 32 (code/tests + reconciliation artifacts/docs + quick-task evidence sources)
**Analogs found:** 30 / 32 (2 targets have no direct prior in-phase artifact: `20-VALIDATION.md`, `22-SECURITY.md`; strong cross-phase analogs identified)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/services/intent/mapper.py` | service (deterministic intent mapper) | transform (NL candidate/raw text → safe contract/applied params) | self + `backend/app/services/intent/parser.py` (orchestration seam) | exact (self) |
| `backend/tests/test_intent_mapper.py` | test (unit, deterministic) | transform verification | self + `backend/tests/test_intent_parser.py` | exact (self) |
| `backend/tests/test_intent_parser.py` | test (unit, fake-client seam) | request-response/orchestration verification | self + `backend/tests/test_intent_mapper.py` | exact (self) |
| `frontend/lib/chatApply.ts` | utility (board-apply mapping/gating) | transform (interpretation/applied_params → canonical board Filters/boolean) | self + `frontend/lib/filters.ts`/`frontend/lib/cities.ts` | exact (self) |
| `frontend/lib/chatApply.test.ts` | test (unit, Vitest node) | transform verification | self + `frontend/lib/cities.test.ts` | exact (self) |
| `frontend/lib/api.ts` | client service/helper | request-response (HTTP fetch, typed errors) | self (`getChatSearchStatus`, `revealContact`) | exact (self) |
| `frontend/components/board/chat/ChatWidget.tsx` | component (chat orchestrator, client state) | event-driven/UI + request-response | self + `frontend/components/board/JobDetailDialog.tsx` (detail open/close/focus) | exact (self) |
| `frontend/components/board/chat/ChatPanel.tsx` | component (dialog/panel container) | event-driven/UI (dialog semantics, keyboard/focus) | self + `frontend/components/board/JobDetailDialog.tsx` (native dialog/focus/ESC) | role-match |
| `frontend/components/board/chat/ChatResultsList.tsx` | component (results/actions list) | event-driven/UI (render + callbacks) | self + `frontend/components/board/chat/ChatResultItem.tsx` | exact (self) |
| `frontend/components/board/chat/ChatResultItem.tsx` | component (result item/button) | event-driven/UI (click/open detail) | self (paired with `ChatResultsList.tsx`) | exact (self) |
| `frontend/components/board/JobDetailDialog.tsx` | component (canonical detail dialog) | event-driven/UI (native dialog, focus/scroll lock, reveal) | self | exact (self) |
| `frontend/lib/cities.ts` | utility (city normalization) | transform | self + `backend/app/services/cities.py` (contract parity context) | exact (self) |
| `frontend/lib/cities.test.ts` | test (unit, Vitest) | transform verification | self | exact (self) |
| `frontend/components/board/BoardToolbar.tsx` | component (board controls/URL writer) | event-driven/UI + URL state | self | exact (self) |
| `backend/app/api/v1/public.py` | route/controller (public API) | request-response (chat-search/jobs/reveal/report) | self (context for CL-01/CL-05 safety/privacy docs) | exact (self) |
| `.planning/debug/city-filter-and-chat-ignores-registered-city.md` | debug/reconciliation artifact | state/traceability record | self (existing diagnosed session) | exact (self) |
| `.planning/phases/19-.../19-VALIDATION.md` | validation artifact (Nyquist) | traceability/evidence record | self + `21-VALIDATION.md`, `22-VALIDATION.md` | exact (self) |
| `.planning/phases/20-.../20-VALIDATION.md` | validation artifact (Nyquist, **create**) | traceability/evidence record | `21-VALIDATION.md` (audited/partial) + `22-VALIDATION.md` (draft) + `19-VALIDATION.md` | role-match |
| `.planning/phases/21-.../21-VALIDATION.md` | validation artifact (Nyquist) | traceability/evidence record | self + `22-VALIDATION.md` | exact (self) |
| `.planning/phases/22-.../22-VALIDATION.md` | validation artifact (Nyquist) | traceability/evidence record | self + `21-VALIDATION.md` | exact (self) |
| `.planning/phases/21-.../21-VERIFICATION.md` | verification artifact | traceability/evidence record | self + `22-VERIFICATION.md`; reconciliation target uses `21-HUMAN-UAT.md` evidence | exact (self) |
| `.planning/phases/22-.../22-VERIFICATION.md` | verification artifact | traceability/evidence record | self + `21-VERIFICATION.md` | exact (self) |
| `.planning/phases/21-.../21-HUMAN-UAT.md` | UAT artifact | manual/runtime evidence record | self | exact (self) |
| `.planning/phases/22-.../22-HUMAN-UAT.md` | UAT artifact | manual/runtime evidence record | self + `21-HUMAN-UAT.md` (final-state example) | exact (self) |
| `.planning/phases/22-.../22-MANUAL-UAT.md` | manual UAT runbook/artifact | manual/runtime evidence record | self | exact (self) |
| `.planning/phases/22-.../22-MVP-EXAMPLES.md` | validation matrix artifact | evidence/traceability record | self (update if CL-01 retest/evidence relevant) | exact (self) |
| `.planning/phases/22-.../22-SECURITY.md` | security artifact (**create**) | controls/limitations documentation | `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-SECURITY.md` | role-match |
| `.planning/STATE.md` | project state/reconciliation artifact | traceability/state record | self | exact (self) |
| `.planning/REQUIREMENTS.md` | requirements traceability artifact | traceability record | self | exact (self) |
| `.planning/v1.3-MILESTONE-AUDIT.md` | milestone audit artifact (in-place closure) | traceability/gate record | self + `gsd-sdk query audit-open` categories/items | exact (self) |
| `.planning/quick/261110-u28-*` (PLAN,SUMMARY) | quick-task evidence (read-only) | execution evidence | `.planning/quick/261110-uik-*` (superseding behavior/evidence pair) | role-match |
| `.planning/quick/261110-uik-*` (PLAN,SUMMARY) | quick-task evidence (read-only) | execution evidence | self | exact (self) |
| `.planning/quick/261111-krt-*` (PLAN,SUMMARY) | quick-task evidence (read-only) | execution evidence | other quick SUMMARY files (e.g. `261110-uik-SUMMARY.md`) | role-match |
| `.planning/quick/261112-ttk-*` (PLAN only) | quick-task evidence (read-only, **deferred justificado**) | planned-but-unexecuted evidence | other quick PLAN files | role-match (plan-only) |

## Pattern Assignments

### `backend/app/services/intent/mapper.py` (service, transform)

**Analog:** self (deterministic, server-authoritative mapper; whitelist-safe normalization).

**Imports / module contract** (`backend/app/services/intent/mapper.py:1-25`):
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
    AppliedParams, FieldAssessment, FieldStatus, IntentContract,
    IntentLLMOutput, IntentSalary, UnderstoodIntent,
)
```

**CL-01 hotspot: raw-text city patterns** (`backend/app/services/intent/mapper.py:34-46`):
```python
_RAW_TEXT_CITY_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    ("São Paulo", (re.compile(r"\bsp\b"), re.compile(r"\bsao\s+paulo\b"))),
    ("Rio de Janeiro", (re.compile(r"\brj\b"), re.compile(r"\brio\b"), re.compile(r"\brio\s+de\s+janeiro\b"))),
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
**Hardening guidance (D-01, 22-REVIEW WR-04):** remove/replace bare `\brio\b` so "Rio Grande do Sul"/"Rio Branco" do **not** map to Rio de Janeiro, while preserving safe supported RJ detection (`rj`, `rio de janeiro`, and only safe "rio" forms if intentionally retained). Never invent non-whitelist cities.

**Normalization/detection helpers** (`backend/app/services/intent/mapper.py:49-55,81-97`):
```python
def _strip_accents_lower(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    without = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without.lower()

def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

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

**Safe city resolution and fallback semantics** (`backend/app/services/intent/mapper.py:100-132,299-363`):
```python
def _resolve_city_safe(raw_city: str | None, raw_text: str = "") -> tuple[str | None, str]:
    """Resolve city via whitelist/obvious-safe mentions. Returns (applied, reason_code)."""
    # Explicit candidate first
    if raw_city:
        ...
        resolved = resolve_city(raw_city)
        if resolved:
            return resolved, "normalized"
        return None, "not_in_whitelist"

    # Fallback: deterministic whitelist detection in raw text when candidate absent
    return _detect_city_from_raw_text(raw_text)

# map_intent city handling (excerpt)
candidate_city_present = bool(candidate.city and str(candidate.city).strip())
...
applied_city, city_reason_code = _resolve_city_safe(candidate.city, raw)
if applied_city:
    city_status = FieldStatus.APLICADO
    if not candidate_city_present and city_reason_code == "normalized":
        city_reason = "Cidade detectada no texto e aplicada com segurança via whitelist."
...
# FieldAssessment for city uses reason_code/status consistent with applied outcome
```
**Preserve:** whitelist-only canonical outputs (`São Paulo`, `Rio de Janeiro`, `Belo Horizonte`, `Remoto` or `None`), deterministic conflict/missing/not_in_whitelist handling, and coherent `understood/field_statuses/applied_params/meta/limitations`.

**Safety guard at end of mapping** (`backend/app/services/intent/mapper.py:520-532`):
```python
applied_params = AppliedParams(q=applied_q, city=applied_city, sort=applied_sort)

# sanity: applied_params city must be canonical whitelist or None
if applied_params.city is not None:
    canon = resolve_city(applied_params.city)
    if canon != applied_params.city and applied_params.city not in {"São Paulo", "Rio de Janeiro", "Belo Horizonte", "Remoto"}:
        applied_params.city = None

if applied_params.q is not None and not applied_params.q.strip():
    applied_params.q = None
```

---

### `backend/tests/test_intent_mapper.py` (test, transform verification)

**Analog:** self (pytest, deterministic, pure mapper assertions via `map_intent`/`build_empty_intent`).

**Imports / helper** (`backend/tests/test_intent_mapper.py:1-18`):
```python
"""Deterministic intent mapper tests (INT-03, D-01..D-12,D-15)."""

from __future__ import annotations

from app.services.intent import IntentLLMOutput, IntentSalary, map_intent, build_empty_intent
from app.services.intent.schema import IntentContractType, IntentMode, IntentSeniority


def _field(contract, name: str):
    for fs in contract.field_statuses:
        if fs.field == name:
            return fs
    raise AssertionError(f"missing field status: {name}")
```

**Existing regression style: absent-candidate raw-text fallback and safeguards** (`backend/tests/test_intent_mapper.py:298-339`):
```python
def test_absent_candidate_raw_text_applies_supported_city_safely() -> None:
    c1 = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga de analista em São Paulo")
    assert c1.applied_params.city == "São Paulo"
    fs1 = _field(c1, "city")
    assert fs1.status == "aplicado"
    assert fs1.reason_code == "normalized"
    assert fs1.understood is None

    c_sp = map_intent(IntentLLMOutput.model_validate({}), raw_text="emprego em sp")
    assert c_sp.applied_params.city == "São Paulo"
    assert _field(c_sp, "city").status == "aplicado"

    c_rj = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga no Rio de Janeiro")
    assert c_rj.applied_params.city == "Rio de Janeiro"
    assert _field(c_rj, "city").status == "aplicado"

    c_bh = map_intent(IntentLLMOutput.model_validate({}), raw_text="oportunidade em bh")
    assert c_bh.applied_params.city == "Belo Horizonte"
    assert _field(c_bh, "city").status == "aplicado"

    c_remoto = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga home office para dev")
    assert c_remoto.applied_params.city == "Remoto"
    assert _field(c_remoto, "city").status == "aplicado"


def test_absent_candidate_raw_text_city_safeguards() -> None:
    conflict = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga em sp ou rj")
    assert conflict.applied_params.city is None
    fs_conflict = _field(conflict, "city")
    assert fs_conflict.status == "ignorado"
    assert fs_conflict.reason_code == "conflict_resolved"

    campinas = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga em campinas")
    assert campinas.applied_params.city is None
    assert campinas.applied_params.city != "Campinas"

    present = map_intent(IntentLLMOutput.model_validate({"city": "Campinas"}), raw_text="vaga em campinas")
    assert present.applied_params.city is None
    assert _field(present, "city").reason_code == "not_in_whitelist"
```

**CL-01 regression additions to copy/adapt:** add negative cases for bare/ambiguous `rio` tokens in non-RJ contexts (e.g. `"Rio Grande do Sul"`, `"Rio Branco"`) asserting `applied_params.city is None` and no false RJ application/status, **and** keep positive RJ cases (`"rj"`, `"Rio de Janeiro"`, and any intentionally-safe `"rio"` form chosen by implementation) passing.

---

### `backend/tests/test_intent_parser.py` (test, request-response/orchestration verification)

**Analog:** self (pytest-asyncio, fake Groq client seam, no network/DB).

**Seam/mocking pattern** (`backend/tests/test_intent_parser.py:1-45,54-66`):
```python
"""Unit tests for intent parser/orchestrator (INT-01/02/03, D-15/D-16).

No network/DB: fake client seam injected.
"""

from __future__ import annotations

from types import SimpleNamespace
import pytest
from app.services.intent.schema import IntentContract, IntentLLMOutput


class _Settings:
    GROQ_API_KEY = "test-key"
    GROQ_MODEL = "model-a"
    GROQ_MODEL_FALLBACK = "model-b"
    GROQ_TIMEOUT_SECONDS = 12


class _FakeCompletions:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        if callable(item):
            return item(kwargs)
        return item


class FakeGroqClient:
    def __init__(self, script):
        self.chat = SimpleNamespace(completions=_FakeCompletions(script))

    @property
    def calls(self):
        return self.chat.completions.calls


def _response(content: str, finish_reason: str = "stop"):
    return SimpleNamespace(
        choices=[SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(content=content))]
    )
```

**Contract/failure behavior pattern** (`backend/tests/test_intent_parser.py:73-93,156-164`):
```python
@pytest.mark.asyncio
async def test_extract_and_map_intent_empty_input_returns_safe_contract_without_llm():
    from app.services.intent.parser import extract_and_map_intent

    class NoCallClient:
        class _C:
            async def create(self, **kwargs):
                raise AssertionError("LLM must not be called for empty input")

        chat = SimpleNamespace(completions=_C())

    for value in ("", "   ", None):
        contract = await extract_and_map_intent(value, _Settings(), client=NoCallClient())
        assert isinstance(contract, IntentContract)
        assert contract.applied_params.q is None
        assert contract.applied_params.city is None
        assert contract.applied_params.sort is None
        assert _status(contract, "q").status == "ignorado"


@pytest.mark.asyncio
async def test_extract_and_map_intent_client_failure_propagates_for_api_degradation():
    from app.services.intent.client import IntentExtractionError
    from app.services.intent.parser import extract_and_map_intent

    with pytest.raises(IntentExtractionError):
        await extract_and_map_intent("dev backend", _Settings(), client=RaisingClient())
```
**CL-01 use:** extend only if parser/orchestrator contract is impacted by mapper hardening (typically mapper tests are primary); keep fake-seam/no-network determinism.

---

### `frontend/lib/chatApply.ts` (utility, transform)

**Analog:** self + `frontend/lib/filters.ts` (`normalizeFilters`, canonical URL semantics).

**Current mapping and gating** (`frontend/lib/chatApply.ts:1-27`):
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
  const p = interpretation.applied_params;
  const hasQ = typeof p.q === "string" && p.q.trim().length > 0;
  const hasCity = typeof p.city === "string" && p.city.trim().length > 0;
  const hasSort = p.sort === "antigas";
  return hasQ || hasCity || hasSort;
}
```

**CL-05 required change (D-14):** gate apply by **useful normalized board outcome** (not raw non-empty `city` string) so non-normalizable city-only cases (e.g. `"campinas"`) do not enable misleading no-op apply. Preserve degraded/`chat_disabled` gating and supported cases (`q`, supported whitelist cities/slugs via normalization, `sort: "antigas"`), and keep `appliedParamsToBoardFilters` forcing `page: 1` and `vaga: null`.

**Related normalization analog** (`frontend/lib/cities.ts:89-103`):
```ts
export function resolveCitySlugFromText(
  value: string | null | undefined,
): CitySlug | null {
  if (typeof value !== "string") {
    return null;
  }
  const key = fold(value);
  if (!key) {
    return null;
  }
  return CITY_TEXT_TO_SLUG.get(key) ?? null;
}
```

---

### `frontend/lib/chatApply.test.ts` (test, transform verification)

**Analog:** self + `frontend/lib/cities.test.ts` (Vitest style for pure helpers).

**Test helper and existing coverage** (`frontend/lib/chatApply.test.ts:1-35,38-117`):
```ts
import { describe, expect, it } from "vitest";

import type { ChatInterpretation } from "@/lib/api";
import { appliedParamsToBoardFilters, canApplyChatToBoard } from "@/lib/chatApply";

function interpretation(overrides: {
  degraded?: boolean;
  degradationReason?: string;
  q?: string | null;
  city?: string | null;
  sort?: "recentes" | "antigas" | null;
}): ChatInterpretation {
  const meta: ChatInterpretation["meta"] = {};
  if (overrides.degraded) meta.degraded = true;
  if (overrides.degradationReason) {
    meta.degradation_reason = overrides.degradationReason;
    if (overrides.degradationReason === "chat_disabled") {
      meta.degraded = true;
    }
  }
  return {
    understood: {},
    field_statuses: [],
    applied_params: { q: overrides.q ?? null, city: overrides.city ?? null, sort: overrides.sort ?? null },
    limitations: [],
    meta,
  };
}

describe("appliedParamsToBoardFilters", () => {
  it("maps q/city/sort and forces page 1 and vaga null", () => { ... });
  it("normalizes unknown city to null", () => {
    expect(
      appliedParamsToBoardFilters({ q: "dev", city: "campinas", sort: "recentes" }),
    ).toEqual({ q: "dev", city: null, sort: "recentes", page: 1, vaga: null });
  });
});

describe("canApplyChatToBoard", () => {
  it("returns false when degraded or all empty/default", () => { ... });
  it("returns false when degradation_reason is chat_disabled", () => { ... });
  it("returns true when q, whitelisted city, or sort antigas is present", () => {
    expect(canApplyChatToBoard(interpretation({ q: "react" }))).toBe(true);
    expect(canApplyChatToBoard(interpretation({ city: "sao-paulo" }))).toBe(true);
    expect(canApplyChatToBoard(interpretation({ sort: "antigas" }))).toBe(true);
  });
});
```

**CL-05 additions:** include `canApplyChatToBoard(interpretation({ city: "campinas" })) === false` (and similar non-normalizable city-only) while preserving existing true/false cases and `chat_disabled`/degraded behavior.

---

### `frontend/lib/api.ts` (client service/helper, request-response)

**Analog:** self (`getChatSearchStatus`, `revealContact`, `reportJob`) for typed errors, timeout/transport handling, and defensive JSON parsing.

**`ApiError` and safe error extraction** (`frontend/lib/api.ts:132-164`):
```ts
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readError(res: Response): Promise<string> {
  const fallback = `Erro ${res.status}`;
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) { /* flatten validation detail */ }
  } catch {
    // non-JSON body — the status is still authoritative
  }
  return fallback;
}
```

**Current `chatSearch` (CL-05 hotspot: no guarded parse on 200)** (`frontend/lib/api.ts:815-843`):
```ts
export async function chatSearch(
  payload: ChatSearchRequest,
): Promise<ChatSearchResponse> {
  let res: Response;
  try {
    res = await fetch(`${API}/api/v1/public/chat-search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(15_000),
    });
  } catch (error) {
    const timedOut =
      error instanceof Error &&
      (error.name === "TimeoutError" || error.name === "AbortError");
    throw new ApiError(
      timedOut
        ? "A requisição demorou demais. Verifique sua conexão e tente novamente."
        : "Não foi possível buscar agora. Verifique sua conexão e tente novamente.",
      0,
    );
  }

  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }

  return (await res.json()) as ChatSearchResponse;
}
```

**Defensive parse analog to copy** (`frontend/lib/api.ts:845-875`, `getChatSearchStatus`):
```ts
if (!res.ok) {
  throw new ApiError(await readError(res), res.status);
}

try {
  return (await res.json()) as ChatSearchStatus;
} catch {
  throw new ApiError("Resposta inválida do servidor.", 0);
}
```
**CL-05 required change (D-14):** apply same try/catch-safe parse for `chatSearch` 200 responses so malformed/unparseable JSON becomes typed pt-BR `ApiError("Resposta inválida do servidor.", 0)` (no raw parse exception leakage).

---

### `frontend/components/board/chat/ChatWidget.tsx` (component, event-driven/UI + request-response)

**Analog:** self (client-owned chat orchestration) + `JobDetailDialog` usage/focus restoration.

**State, request sequencing, and detail trigger refs** (`frontend/components/board/chat/ChatWidget.tsx:74-99,282-298`):
```tsx
const [chatEnabled, setChatEnabled] = useState(true);
const [isOpen, setIsOpen] = useState(false);
const [draft, setDraft] = useState("");
const [turns, setTurns] = useState<ChatTurn[]>([]);
const [isSending, setIsSending] = useState(false);
const [isLoadingMore, setIsLoadingMore] = useState(false);
...
const requestSeq = useRef(0);
const activeRequestRef = useRef(0);
const idRef = useRef(0);
const detailTriggerRef = useRef<HTMLElement | null>(null);

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

**Current wiring (focus target not propagated)** (`frontend/components/board/chat/ChatWidget.tsx:329-337`):
```tsx
<ChatThread
  ...
  onOpenDetail={(job) => handleOpenDetail(job, null)}
  onManualSearch={handleManualSearch}
/>
```
**Feasible CL-05 a11y improvement:** pass originating trigger element/ref from results thread (`ChatResultsList`/`ChatResultItem`) so close restores focus usefully. Keep canonical `vaga` sync, apply flow, degraded/disabled gating, and in-memory session behavior unchanged.

**Canonical apply flow** (`frontend/components/board/chat/ChatWidget.tsx:271-280`):
```tsx
const handleApplyToBoard = () => {
  if (!lastResponse) return;
  if (!canApplyChatToBoard(lastResponse.interpretation)) return;
  const filters = appliedParamsToBoardFilters(lastResponse.interpretation.applied_params);
  const href = buildBoardHref({ ...filters, page: 1, vaga: null });
  router.replace(href, { scroll: false });
  setIsOpen(false);
};
```

---

### `frontend/components/board/chat/ChatPanel.tsx` (component, event-driven/UI)

**Analog:** self (custom dialog) + `JobDetailDialog.tsx` (focus/ESC behavior reference). **Note:** custom panel (not native `<dialog>`), so robust focus-trap work is higher risk.

**Dialog semantics and Escape handling** (`frontend/components/board/chat/ChatPanel.tsx:21-67`):
```tsx
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

if (!open) return null;

return (
  <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-stretch sm:justify-end">
    <button type="button" aria-label="Fechar chat" onClick={onClose}
      className="absolute inset-0 bg-[rgba(5,2,12,0.72)]" />
    <section role="dialog" aria-modal="true" aria-labelledby={titleId}
      className="relative z-10 flex h-[85dvh] w-full max-w-none flex-col ...">
      <header ...>
        <h2 id={titleId} className="text-[20px] font-semibold leading-[1.2] text-fg">
          Buscar vagas no chat
        </h2>
        <button type="button" onClick={onClose} ...>Fechar chat</button>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-3 sm:p-4">{children}</div>
      {composer}
    </section>
  </div>
);
```
**Feasible CL-05 a11y (D-14):** add minimal initial focus on open (e.g. focus close button/title container or first meaningful control via ref/effect) without broad refactor; keep `role="dialog"`, `aria-modal`, labelledby, Escape/close/backdrop operable. If full focus trap is not viable, **explicitly defer** in artifacts.

---

### `frontend/components/board/chat/ChatResultsList.tsx` and `ChatResultItem.tsx` (component, event-driven/UI)

**Analog:** self pair (list delegates open action to item).

**Current callback contract** (`frontend/components/board/chat/ChatResultsList.tsx:6-16,73-77`):
```tsx
interface ChatResultsListProps {
  interpretation: ChatInterpretation;
  items: JobPublic[];
  total: number;
  isLoadingMore: boolean;
  canApply: boolean;
  onLoadMore: () => void;
  onApplyToBoard: () => void;
  onOpenDetail: (job: JobPublic) => void;
  onManualSearch: () => void;
}

{items.map((job) => (
  <ChatResultItem key={job.id} job={job} onOpen={onOpenDetail} />
))}
```

**Current item trigger** (`frontend/components/board/chat/ChatResultItem.tsx:6-20`):
```tsx
interface ChatResultItemProps {
  job: JobPublic;
  onOpen: (job: JobPublic) => void;
}

export function ChatResultItem({ job, onOpen }: ChatResultItemProps) {
  ...
  return (
    <button
      type="button"
      onClick={() => onOpen(job)}
      className="w-full rounded-lg border border-line bg-surface p-3 text-left ..."
    >
      ...
      <span className="mt-1 inline-flex text-sm font-semibold text-accent-soft">Ver detalhes</span>
    </button>
  );
}
```
**Feasible CL-05 a11y touchpoint:** evolve callback/type to accept optional trigger element (e.g. `onOpen(job, event.currentTarget)` / ref) and thread through `ChatThread -> ChatResultsList -> ChatResultItem -> ChatWidget.handleOpenDetail` for focus restore. Keep public-only rendering (no contacts), copy/layout, and canonical detail open behavior.

---

### `frontend/components/board/JobDetailDialog.tsx` (component, event-driven/UI)

**Analog:** self (native `<dialog>` canonical flow).

**Native dialog lifecycle and focus/scroll handling** (`frontend/components/board/JobDetailDialog.tsx:43-80,89-101`):
```tsx
export function JobDetailDialog({ job, open, onClose }: JobDetailDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = `job-dialog-title-${job.id}`;
  const [reportOpen, setReportOpen] = useState(false);
  const close = () => dialogRef.current?.close();

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

  // Lock document scroll while modal is open
  useEffect(() => {
    if (!open) return;
    const root = document.documentElement;
    const previous = root.style.overflow;
    root.style.overflow = "hidden";
    return () => { root.style.overflow = previous; };
  }, [open]);

  return (
    <>
      <dialog
        ref={dialogRef}
        tabIndex={-1}
        aria-labelledby={titleId}
        onClose={onClose}
        onClick={(event) => {
          if (event.target === dialogRef.current) dialogRef.current?.close();
        }}
        className="..."
      >
        ...
        <button type="button" aria-label="Fechar" onClick={close} ...>...</button>
        ...
        <footer ...>
          <RevealContact job={job} onClose={close} />
          <button type="button" onClick={() => setReportOpen(true)} ...>Reportar vaga</button>
        </footer>
      </dialog>
      <ReportJobDialog jobId={job.id} open={reportOpen} onClose={() => setReportOpen(false)} />
    </>
  );
}
```
**CL-05 guidance:** preserve native dialog/focus/ESC/backdrop behavior, scroll lock, canonical reveal/report flows, and contact safety. Only minimal, safe adjustments if needed; avoid regressions.

---

### Documentation & reconciliation artifacts (CL-01..CL-05)

#### `.planning/debug/city-filter-and-chat-ignores-registered-city.md` (update)
**Analog:** self (diagnosed debug session; overwrite/append per its own conventions).

**Frontmatter/status + Current Focus contract** (`.planning/debug/city-filter-and-chat-ignores-registered-city.md:1-15`):
```md
---
status: diagnosed
trigger: "UAT gap diagnosis (Phase 22, Test 1): toolbar não reconhece cidade cadastrada usa ?q=city-name e retorna nada; chatbot marca cidade cadastrada como ignorada."
created: 2026-11-18T00:00:00Z
updated: 2026-11-18T00:00:00Z
---

## Current Focus
<!-- OVERWRITE on each update - reflects NOW -->
...
next_action: "Return ROOT CAUSE FOUND with file-level evidence and fix direction (no code changes)."
```
**Evidence/Resolution sections** (`:39-73`): append CL-01 fix/retest evidence; overwrite `Current Focus`/`Resolution` appropriately; update `status`/`updated` to reflect final disposition (resolved or formally deferred with decision recorded) per D-01..D-03. Keep facts append-only in Evidence/Eliminated as established by file.

#### `21-VERIFICATION.md` / `22-VERIFICATION.md` (update to final accepted traceable states)
**Analogs:** self files + cross-reference each other’s structure.

**21 frontmatter and reconciliation basis** (`.planning/phases/21-.../21-VERIFICATION.md:1-9,56-63`):
```md
---
phase: 21-interface-de-chat-e-integracao-no-board
verified: 2026-11-17T21:55:00Z
status: human_needed
score: 4/4 must-haves verified
re_verification: false
---

| UI-01 | 21-01, 21-02 | ... | ✓ SATISFIED (code + automated checks; UX perception human) | ... `.planning/REQUIREMENTS.md` still marks Pending (traceability/docs update outside this verification artifact). |
```
**22 frontmatter and honest pending-human model** (`.planning/phases/22-.../22-VERIFICATION.md:1-18,104-110`):
```md
---
phase: 22-qualidade-hardening-e-valida-o-operacional
verified: 2026-11-18T12:10:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Executar `22-MANUAL-UAT.md` (testes 1–6) ..."
    expected: "..."
    why_human: "..."
---
...
## Human Verification Required
...
### Gaps Summary
Nenhum gap de implementação automatizável identificado...
**Notas operacionais:** (1) `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/SECURITY.md` não existe ... (2) `.planning/REQUIREMENTS.md` ainda lista QA-01/QA-02/QA-03 como `Pending`...
```
**Reconciliation pattern (D-09/D-11/D-12):** 21-HUMAN-UAT is `status: complete` with 4/4 pass (`.planning/phases/21-.../21-HUMAN-UAT.md:1-8,31-38`) — use as evidence to close 21 verification traceably. 22 must record CL-01 retest outcome (executed or explicit per-item accepted deferment with reason/risk/next action) and final accepted state; preserve passed items and do not leave unresolved `human_needed` without resolution text.

#### `21-HUMAN-UAT.md`, `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md` (update/reconcile)
**Analogs:** self files.

**21 completed state example** (`.planning/phases/21-.../21-HUMAN-UAT.md:1-39`):
```md
---
status: complete
phase: 21-interface-de-chat-e-integracao-no-board
source: [21-VERIFICATION.md]
started: 2026-11-17T21:55:00Z
updated: 2026-11-17T23:49:00Z
---
...
## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0
```

**22 partial + retest/deferment structure** (`.planning/phases/22-.../22-HUMAN-UAT.md:1-9,18-35,51-67`):
```md
---
status: partial
phase: 22-qualidade-hardening-e-valida-o-operacional
source:
  - 22-VERIFICATION.md
  - 22-MANUAL-UAT.md
  - 22-04-PLAN.md
updated: 2026-11-18T23:59:00Z
---
...
## Atualização de gap closure (22-04)
- **Fix aplicado (pendente revalidação manual em runtime):** ...
- **Evidência automatizada adicionada/atualizada (22-04):** ...

### 1. Revalidar caso reportado (toolbar e chat) + roteiro manual/UAT guiado
- **result:** [pending retest]
...
## Summary
total: 3
passed: 2
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
- truth: "Busca manual (toolbar/filtros) e chat reconhecem corretamente a cidade..."
  status: retest_required
  reason: "... **reteste manual/runtime pendente** ..."
  debug_session: ".planning/debug/city-filter-and-chat-ignores-registered-city.md"
```

**22 manual runbook structure** (`.planning/phases/22-.../22-MANUAL-UAT.md:1-19,39-52,113-121`):
```md
---
status: draft
phase: 22-qualidade-hardening-e-valida-o-operacional
source: [22-CONTEXT.md (D-04, D-06), 22-UI-SPEC.md, 22-RESEARCH.md, 21-HUMAN-UAT.md, 22-01/02-PLAN.md]
started: 2026-11-18
updated: 2026-11-18
mode: guided-manual
automation_scope: "Sem Playwright, sem React Testing Library/infra browser E2E nesta fase..."
---
...
### 0. Revalidação do caso reportado (22-04): cidade suportada no toolbar e no chat
...
**result:** [pending]
...
## Summary
total: 7
passed: 0
issues: 0
pending: 7
skipped: 0
blocked: 0
```
**Pattern:** move to final accepted traceable states per D-10/D-11/D-12 — execute/register CL-01 retest; preserve already-passed items; for infeasible items record accepted deferral per item with justification, reason (ambiente/dados/runtime/browser/infra), residual risk, and future condition/action.

#### Validation artifacts (CL-04): create `20-VALIDATION.md`, evolve `19/21/22-VALIDATION.md`
**Analogs:** existing validation files in same family.

**19 draft (minimal scaffold)** (`.planning/phases/19-.../19-VALIDATION.md:1-14,17-35,48-75`):
```md
---
phase: 19
slug: contrato-de-intencao-e-mapeamento-seguro
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-17
---

# Phase 19 — Validation Strategy

## Test Infrastructure
| **Framework** | pytest (backend, existing) |
| **Quick run command** | `cd backend && python -m pytest tests/services/intent -q` (once intent tests exist) |
| **Full suite command** | `cd backend && python -m pytest -q` |

## Sampling Rate
- **After every task commit:** Run `cd backend && python -m pytest tests/services/intent -q` ...

## Per-task Verification Map
| task ID | Plan | Wave | Requirement | ... | Automated Command | File Exists | Status |
| TBD (planner fills) | — | — | INT-01, INT-02, INT-03 | ... | `cd backend && python -m pytest tests/services/intent -q` | ❌ W0 | ⬜ pending |

## Wave 0 Requirements
...
## Validation Sign-Off
- [ ] `nyquist_compliant: true` set in frontmatter
**Approval:** pending
```

**21 audited-partial (richer evidence model, best analog for honest compliant/deviation evolution)** (`.planning/phases/21-.../21-VALIDATION.md:1-9,19-49,85-93`):
```md
---
phase: 21
slug: interface-de-chat-e-integracao-no-board
status: audited
nyquist_compliant: false
wave_0_complete: partial
created: 2026-11-17
audited: 2026-11-17
---

## Test Infrastructure
| **Framework** | Frontend: Vitest 2.x ... Backend: pytest (referência Phase 20) |
| **Quick run command** | `npm --prefix frontend run test:chat` |

## Per-task Verification Map
| 21-W0-03 | W0 | 0 | UI-03 | ... | `npm --prefix frontend run test:chat` | ✅ `frontend/lib/chatApply.test.ts` | ✅ green |

**Nota (auditoria 2026-11-17):** `npm --prefix frontend run test:chat` executado com sucesso (6 testes). Gaps restantes...

## Validation Audit 2026-11-17
| Gaps found (initial state) | 3 (W0-01, W0-02, W0-03) |
| Resolved | 1 (W0-03 via `frontend/lib/chatApply.test.ts`, 6/6 passing) |
| Escalated / still missing | 2 (W0-01, W0-02 — no automated UI/component tests) |
**Commands run:** `npm --prefix frontend run test:chat` → PASS (6 tests).
```

**22 draft with explicit wave-0/manual/DB caveats** (`.planning/phases/22-.../22-VALIDATION.md:1-8,19-60,63-84`):
```md
---
phase: 22
slug: qualidade-hardening-e-valida-o-operacional
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-18
---

## Per-task Verification Map
| 22-XX-01 | TBD | TBD | QA-01 | — | ... | `cd backend && pytest -q ...` | ❌ W0 | ⬜ pending |

## Wave 0 Requirements
- [ ] `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` ...
- [ ] `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` ...
*DB-backed execution evidence is prerequisite-gated when TEST_DATABASE_URL/DATABASE_URL or migrated schema is unavailable; do not claim execution without environment.*

## Manual-Only Verifications
| Fluxo UI/E2E viável do chat no board ... | QA-02 | Playwright/RTL não serão introduzidos nesta fase (D-04)... | Executar `22-MANUAL-UAT.md` ... |
| Kill-switch fim-a-fim percebido na UI e não-regressão... | QA-03 | ... | Desativar via env/config... |

## Validation Sign-Off
- [ ] `nyquist_compliant: true` set in frontmatter
**Approval:** pending
```
**CL-04 pattern:** create `20-VALIDATION.md` (phase 20 was API-01..03, pytest backend; see `20-VERIFICATION.md` for evidence/contracts) and evolve 19/21/22 to `nyquist_compliant` **when viably evidenced**, else record **accepted deviation with plan-of-action** in-file (honest, traceable). Keep frontmatter fields, infrastructure/sampling/per-task/manual/wave-0/sign-off (and audit section when useful) consistent with repo style.

#### `22-SECURITY.md` (create, CL-05/D-15)
**Analog:** `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-SECURITY.md` (same artifact family).

**Frontmatter and sections** (`.planning/phases/21-.../21-SECURITY.md:1-12,17-76`):
```md
---
phase: 21
slug: interface-de-chat-e-integracao-no-board
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-17
---

# Phase 21 — Security

## Trust Boundaries
| Boundary | Description | Data Crossing |

## Threat Register
| Threat ID | Category | Component | Disposition | Mitigation | Status |

## Accepted Risks Log
No accepted risks.

## Security Audit Trail
| Audit Date | Threats Total | Closed | Open | Run By |
...
## Sign-Off
- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter
```
**22-SECURITY content scope (D-15, evidence in `backend/app/api/v1/public.py` + 22 artifacts):** document controls/review for chat-search: kill-switch/status (`CHAT_SEARCH_ENABLED`, `/chat-search/status`), rate limit/size/timeout limits, server-side validation, deterministic search via `list_published` with applied params only, privacy (no `contact_email`/`contact_phone` in chat payloads; reveal canonical), safe degraded fallback/guidance, structured operational logging without PII/message content; include known limitations/residual risks and honest status/sign-off.

#### `.planning/STATE.md`, `.planning/REQUIREMENTS.md`, `.planning/v1.3-MILESTONE-AUDIT.md` (update)
**Analogs:** self (in-place, traceable reconciliation).

**STATE current markers** (`.planning/STATE.md:24-34,83-103`):
```md
## Current Position

Phase: 23
Plan: Not started
Status: Phase added, awaiting planning
Last activity: 2026-11-19

Progress: [████------] 80%
...
## Deferred Items
...
| quick_task | 261110-u28-bloquear-a-expressao-jacira-chavare-ao-c | incomplete |
| quick_task | 261110-uik-remover-jacira-chavare-do-texto-colado-s | incomplete |
| quick_task | 261111-krt-atualizar-next-16-4-6-eslint-9 | incomplete |
| quick_task | 261112-ttk-escape-hatch-turnstile-teste-em-prod | incomplete |
```
**Pattern (D-05..D-08):** cite evidence/justification per quick task (u28/uik concluded with evidence, uik supersedes u28 blocking behavior; krt concluded with historical evidence; ttk deferred justificado with PLAN-only state) so none remain `missing/incomplete` in `audit-open` context. Update phase/progress/last activity consistently when applicable.

**REQUIREMENTS closure section** (`.planning/REQUIREMENTS.md:34-45,89-99`):
```md
## v1.3 Closure Requirements (Phase 23)
...
- [ ] **CL-01**: ...
- [ ] **CL-02**: ...
- [ ] **CL-03**: ...
- [ ] **CL-04**: ...
- [ ] **CL-05**: ...
...
| CL-01 | Phase 23 | Not started |
| CL-02 | Phase 23 | Not started |
| CL-03 | Phase 23 | Not started |
| CL-04 | Phase 23 | Not started |
| CL-05 | Phase 23 | Not started |
```
**Pattern:** update checklist/traceability/status only with honest, evidenced closure (or keep deferred-justified states reflected consistently) as required for CL-02/CL-05 traceability; do not regress INT/API/UI/QA completed items.

**Milestone audit in-place closure** (`.planning/v1.3-MILESTONE-AUDIT.md:1-45,65-94,127-161`):
```md
---
milestone: v1.3
audited: 2026-11-18T12:30:00Z
status: tech_debt
scores:
  requirements: 12/12
  phases: 4/4
  integration: 18/18
  flows: 4/4
gaps: { requirements: [], integration: [], flows: [] }
tech_debt:
  - phase: 21-interface-de-chat-e-integracao-no-board
    items: [...]
  - phase: 22-qualidade-hardening-e-valida-o-operacional
    items: [...]
  - phase: 20-api-publica-de-chat-search-resiliente
    items: ["Nyquist: 20-VALIDATION.md missing (flagged for /gsd-validate-phase 20)."]
  - phase: 19-contrato-de-intencao-e-mapeamento-seguro
    items: ["Nyquist: 19-VALIDATION.md exists but nyquist_compliant false (draft)."]
nyquist:
  compliant_phases: []
  partial_phases: ["19","21","22"]
  missing_phases: ["20"]
  overall: non-compliant
...
## Tech Debt / Deferred Review Items
...
## Conclusion
Milestone v1.3 meets its scoped requirements by code/evidence ... **not fully runtime-validated** ...
```
**Pattern (D-16):** update frontmatter/status/scores, remove/adjust resolved `tech_debt`/notes, record CL-01..CL-05 outcomes and any accepted per-item deferments with evidence, and reflect gate state consistent with `gsd-sdk query audit-open` (no new Phase 23 items).

#### Quick-task reconciliation evidence (read-only sources)
**Analogs:** existing quick PLAN/SUMMARY pairs and PLAN-only case.

**uik SUMMARY evidence pattern (supersedes u28; completed with commits/tests)** (`.planning/quick/261110-uik-.../261110-uik-SUMMARY.md:1-41,71-79,110-123`):
```md
---
phase: 261110-uik
plan: 01
subsystem: extraction
key-decisions:
  - "The term is REMOVED, never blocked..."
key-files:
  modified: [backend/app/services/extraction/blocklist.py, backend/tests/test_blocklist.py, backend/app/api/v1/extract.py, backend/tests/test_extract_api.py, frontend/lib/blocklist.ts, frontend/app/admin/paste/ExtractForm.tsx]
requirements-completed: []
duration: 12min
completed: 2026-11-10
---
...
## Task Commits
1. ... - `04a468e` (feat)
2. ... - `a8f35cf` (feat)
3. ... - `75c19ef` (feat)

## Verification
| `backend> ... pytest -q tests/test_blocklist.py tests/test_extract_api.py` | 31 passed ... |
| `backend> ... pytest -q` | 267 passed, 3 skipped ... |
...
Replacement confirmation: this task supersedes quick task 261110-u28 (commit `fd281dd`, 422 rejection). No blocking behavior for the term remains...
```

**ttk PLAN-only (deferred justificado evidence source)** (`.planning/quick/261112-ttk-.../261112-ttk-PLAN.md:1-6,16-28,29-55,64-70`):
```md
---
phase: 261112-ttk
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [backend/app/core/config.py, backend/app/api/v1/health.py, backend/tests/test_security_config.py, backend/tests/test_health.py, scripts/verify-deploy.ps1, render.yaml, docs/DEPLOY.md, .planning/STATE.md]
autonomous: true
requirements: []   # quick task — desvio temporário pedido pelo usuário
user_setup:
  - service: render
---
...
Purpose: o usuário pediu para "desativar essa trava temporariamente"...
Output: código + testes + gate + blueprint + runbook documentando o desvio...
```
**Pattern (D-05..D-08):** cite `261110-u28` PLAN+SUMMARY and `261110-uik` PLAN+SUMMARY as concluded with evidence and state uik as vigente/superseding; cite `261111-krt` PLAN+SUMMARY as concluded with historical evidence; cite `261112-ttk` PLAN (no SUMMARY) as **deferred justificado** (validation segura em produção/ambiente controlado fora do escopo local) with explicit justification and current state reference. Reflect in `.planning/STATE.md`, `.planning/v1.3-MILESTONE-AUDIT.md`, and any required references so none remain `missing/incomplete` in audit-open context.

## Shared Patterns

### 1) Deterministic whitelist-only city safety (backend + frontend parity)
**Sources:** `backend/app/services/intent/mapper.py:34-46,81-132,520-528`, `frontend/lib/cities.ts:11-103`, `frontend/components/board/BoardToolbar.tsx:57-96`, `frontend/lib/filters.ts` (consumed).
**Apply to:** CL-01 mapper hardening/tests and any doc reconciliation describing supported-city behavior.
```python
# backend: raw-text detection must stay whitelist-only and unambiguous
distinct = list(dict.fromkeys(matches))
if len(distinct) == 1:
    return distinct[0], "normalized"
if len(distinct) > 1:
    return None, "conflict_resolved"
return None, "missing"
```
```ts
// frontend: exact supported-city resolution + promotion to canonical slug, not q
const matchedCity = resolveCitySlugFromText(trimmed);
if (matchedCity) {
  commit({ q: "", city: matchedCity });
  lastCommittedRef.current = "";
  setValue("");
} else {
  commit({ q: trimmed });
  lastCommittedRef.current = trimmed;
}
```

### 2) Canonical board URL/reset semantics for chat apply
**Sources:** `frontend/lib/chatApply.ts:5-13,15-26`, `frontend/lib/chatApply.test.ts:38-74`, `frontend/components/board/chat/ChatWidget.tsx:271-280`.
**Apply to:** `canApplyChatToBoard`/tests and a11y/focus changes that must not regress apply behavior.
```ts
const normalized = normalizeFilters({
  q: (applied.q ?? "").trim(),
  city: (applied.city ?? "").trim().toLowerCase(),
  sort: applied.sort ?? "recentes",
  page: "1",
  vaga: "",
});
return { ...normalized, page: 1, vaga: null };

// apply: gated, then canonical replace
if (!canApplyChatToBoard(lastResponse.interpretation)) return;
const href = buildBoardHref({ ...filters, page: 1, vaga: null });
router.replace(href, { scroll: false });
setIsOpen(false);
```

### 3) Typed, user-safe pt-BR error/parse handling in frontend API client
**Sources:** `frontend/lib/api.ts:132-164,819-843,870-874`.
**Apply to:** `chatSearch` defensive JSON parse (CL-05), preserving existing transport/timeout/status handling.
```ts
throw new ApiError(
  timedOut
    ? "A requisição demorou demais. Verifique sua conexão e tente novamente."
    : "Não foi possível buscar agora. Verifique sua conexão e tente novamente.",
  0,
);

if (!res.ok) {
  throw new ApiError(await readError(res), res.status);
}

try {
  return (await res.json()) as ChatSearchStatus;
} catch {
  throw new ApiError("Resposta inválida do servidor.", 0);
}
```

### 4) Honest, traceable artifact reconciliation (evidence or accepted deferral)
**Sources:** `21-HUMAN-UAT.md` (complete), `22-HUMAN-UAT.md`/`22-MANUAL-UAT.md`/`22-VERIFICATION.md` (pending/deferred patterns), `19/21/22-VALIDATION.md`, debug session template, milestone audit.
**Apply to:** CL-01..CL-05 docs (verification/UAT/manual/validation/security/debug/state/requirements/audit) and quick-task dispositions.
```md
# UAT/manual item resolution pattern
- result: pass | pending | blocked | skipped | accepted_deferral
- reason/justification: (ambiente/dados/runtime/browser/infra quando inviável)
- residual risk + future condition/action
- evidence refs (tests, commits, PLAN/SUMMARY, runtime notes)

# Nyquist honesty pattern
status: draft|audited|...
nyquist_compliant: false|true  # only with evidence; otherwise accepted deviation documented with plan-of-action
wave_0_complete: false|partial|true
```

### 5) Privacy and public-contract non-regression
**Sources:** `backend/app/api/v1/public.py` (chat-search returns `JobPublic`, controlled guidance/errors, no PII logging of message), `frontend/lib/api.ts` chat types, `ChatWidget.tsx` + `JobDetailDialog.tsx` canonical reveal.
**Apply to:** CL-01/CL-05 fixes and `22-SECURITY.md`/audit closure.
```py
# backend: results serialized as public contract only
return ChatSearchResponse(
    interpretation=contract,
    results=ChatSearchResults(
        items=[JobPublic.model_validate(job) for job in items],
        page=payload.page,
        limit=payload.limit,
        total=total,
    ),
)
# logging: outcome/reason/latency/counts/page/limit only (no payload.message)
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.planning/phases/20-api-publica-de-chat-search-resiliente/20-VALIDATION.md` | validation artifact (Nyquist, create) | traceability/evidence record | No `20-VALIDATION.md` exists in phase 20 (verified missing). Use `21-VALIDATION.md` (audited partial) / `22-VALIDATION.md` (draft) / `19-VALIDATION.md` as structural analogs and `20-VERIFICATION.md` + 20 plans/summaries/tests for evidence. |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-SECURITY.md` | security artifact (create) | controls/limitations documentation | No `22-SECURITY.md` and no prior SECURITY artifact in phase 22. Use `21-SECURITY.md` as direct cross-phase analog and 22 code/artifacts (`public.py`, config/status/kill-switch behavior, 22 verification/manual/mvp) as evidence. |

## Metadata

**Analog search scope:** `.planning/phases/23-*`, `.planning/phases/19-22-*`, `.planning/debug/*`, `.planning/quick/261110-u28-*|261110-uik-*|261111-krt-*|261112-ttk-*`, `.planning/{STATE,REQUIREMENTS,v1.3-MILESTONE-AUDIT,ROADMAP}.md`, `backend/app/services/intent/**`, `backend/app/api/v1/public.py`, `backend/tests/test_intent_{mapper,parser}.py`, `frontend/lib/{api,chatApply,cities}.{ts,tsx}` and tests, `frontend/components/board/{BoardToolbar,JobDetailDialog}.tsx`, `frontend/components/board/chat/**`.
**Files scanned:** 70+ (required planning inputs, phase 19-22 artifact directories, 4 quick-task dirs, and targeted code/test files named in context).
**Pattern extraction date:** 2026-11-19
