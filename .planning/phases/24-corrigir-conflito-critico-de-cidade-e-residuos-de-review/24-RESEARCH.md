# Phase 24: Corrigir conflito crítico de cidade e resíduos de review - Research

**Researched:** 2026-11-21
**Domain:** Intent mapper determinism (backend Python/FastAPI) + chat UI focus/gating hardening (frontend Next.js/React/TypeScript)
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CL-01 | Debug `city-filter-and-chat-ignores-registered-city` resolvido com decisão/evidência registrada (22-04 + hardening 23-01, testes determinísticos) e reteste runtime do caso reportado documentado como deferimento aceito por item quando inviável no ambiente (23-03/debug/UAT). | **Gap remains:** 23-VERIFICATION/23-REVIEW identify CR-01 in `backend/app/services/intent/mapper.py`: candidate-present city path bypasses raw-text alias/abbreviation/remoto conflict detection, allowing incorrect city application. Phase 24 closes CR-01 with deterministic mapper fix + regression tests, and updates evidence/audit context consumed by Phase 25. Runtime retest remains an accepted deferral only if environment is unavailable; code-level deterministic proof is required. |
| CL-05 | Avisos não-bloqueantes tratados quando viáveis (`chatSearch` parse defensivo, `canApplyChatToBoard` sem no-op para cidade-only não normalizável, melhorias focadas de foco/a11y com residual de focus-trap explicitamente deferido/propagado, `22-SECURITY.md` criado) e `v1.3-MILESTONE-AUDIT.md` atualizado in-place para fechamento rastreável do milestone. | Phase 23 delivered most viable CL-05 fixes, but residual review items remain: WR-01 (chat detail close focus restore may target unmounted trigger), WR-03 (non-native influence detection uses substring matching over full `applied_q`), WR-02/D-14 focus trap deferred. Phase 24 must close WR-01 and WR-03 with automated regressions and preserve public/chat contracts; WR-02/D-14 remains explicitly deferred (Phase 25 documents residual). |
</phase_requirements>

## Summary

Phase 24 is a focused gap-closure phase, not a feature phase. The v1.3 audit (`.planning/v1.3-MILESTONE-AUDIT.md`) and Phase 23 verification/review (`23-VERIFICATION.md`, `23-REVIEW.md`) converge on one critical blocker and two viable review residues: **CR-01** in the deterministic intent mapper, **WR-03** in non-native influence classification, and **WR-01** in chat detail-close focus restoration. All three are in code paths already covered by Phase 23 work, so planning should target small, behavior-preserving fixes with deterministic regression tests.

The highest-risk issue is CR-01. Current `map_intent()` detects raw-text city conflicts only via a narrow full-name heuristic when a candidate city is present (`sao paulo`, `rio de janeiro`, `belo horizonte`, `campinas` tokens in raw text). It does **not** reuse alias/abbreviation/remoto conflict detection from `_detect_city_from_raw_text()`. As a result, ambiguous inputs like `"vaga em sp ou rio de janeiro"` with candidate `SP`, or `"vaga remoto ou são paulo"` with candidate `Remoto`, can bypass conflict handling and apply the wrong city. This violates the INT-03/CL-01 safety expectation: conflicting/ambiguous city intent must never silently apply an incorrect city. [VERIFIED: codebase `backend/app/services/intent/mapper.py`, `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-REVIEW.md` CR-01, `23-VERIFICATION.md`]

The frontend residues are smaller. WR-03 is a mapper classification quality bug (substring matching over full `applied_q`) that can mislabel non-native influence; fix is token-aware matching with regression tests. WR-01 is an a11y/focus regression caused by closing the chat panel before opening the job detail dialog, unmounting the trigger that `ChatWidget` later tries to focus on close. The fix should restore focus to a mounted/stable control without creating a new modal/focus-trap system (D-14/WR-02 remains deferred). [VERIFIED: codebase `backend/app/services/intent/mapper.py`, `frontend/components/board/chat/ChatWidget.tsx`, `ChatPanel.tsx`]

**Primary recommendation:** Plan Phase 24 as three targeted fixes with regression-first tests: (1) make raw-text city conflict detection authoritative even when candidate city is present, (2) replace substring influence matching with token/boundary-safe matching, (3) keep chat detail-close focus restoration on a mounted control; then rerun affected pytest/vitest suites and update phase/audit evidence handoff for Phase 25.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| City conflict detection and safe application to search params | API / Backend (`intent/mapper`) | — | `map_intent()` is the deterministic, server-authoritative contract that produces `applied_params.city`; frontend must not infer/fix city safety. [VERIFIED: `backend/app/services/intent/mapper.py`, Phase 19 decisions in `STATE.md`] |
| Non-native field approximation classification | API / Backend (`intent/mapper`) | Frontend consumer | Mapper emits `field_statuses`/limitations consumed by chat UI; classification must be deterministic and server-owned. [VERIFIED: `mapper.py`, `frontend/components/board/chat/*` rendering interpretation] |
| Chat detail-close keyboard focus restoration | Frontend / Client (React components) | Browser dialog behavior | Focus management is DOM/runtime behavior in client components; backend has no role. [VERIFIED: `frontend/components/board/chat/ChatWidget.tsx`, `frontend/components/board/JobDetailDialog.tsx`] |
| Milestone closure evidence / audit gate reconciliation | Planning artifacts / Process | — | CL-02 audit-open heuristic and v1.3 audit updates are Phase 25 scope; Phase 24 only provides code/test evidence needed for re-audit. [VERIFIED: `.planning/ROADMAP.md` Phase 25, `.planning/v1.3-MILESTONE-AUDIT.md`] |

## Project Constraints (from AGENTS.md)

- Work must start through a GSD command for file-changing work; this research is being produced inside the GSD workflow. [VERIFIED: `AGENTS.md` GSD Workflow Enforcement]
- Preserve project stack/constraints: Next.js 16 App Router + Tailwind dark/mobile-first frontend, FastAPI backend, Portuguese pt-BR UI/errors, no friction public board. [VERIFIED: `AGENTS.md` Project section]
- Public chat must not expose contacts and must preserve canonical board behavior. [VERIFIED: `AGENTS.md` context, `REQUIREMENTS.md` UI-02/API-01, codebase behavior]

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| Python / pytest | repo current (`pytest` in backend venv/tooling; pyproject not inspected) | Deterministic backend regression tests | Existing mapper/intent suite is pytest-based and fast. [VERIFIED: `backend/tests/test_intent_mapper.py`, Phase 23 summaries] | HIGH |
| FastAPI / Pydantic v2 | FastAPI 0.143.x, Pydantic 2.14.x per stack research | Intent contract schemas and deterministic service behavior | Phase 24 changes are inside existing Pydantic-typed intent mapper contract. [VERIFIED: `.planning/research/STACK.md`, `backend/app/services/intent/schema.py` referenced by mapper] | MEDIUM |
| Next.js 16 / React 19 / TypeScript 5.9.2 | `next@16.4.6`, `react@19.1.1`, `typescript@5.9.2` | Chat UI components and client focus behavior | Existing chat UI is App Router client components. [VERIFIED: `frontend/package.json`] | HIGH |
| Vitest | `vitest@^2.1.9` | Frontend deterministic unit tests | Used for `lib/chatApply.test.ts` and configured for `lib/**/*.test.ts`. [VERIFIED: `frontend/package.json`, `frontend/vitest.config.ts`] | HIGH |

### Supporting

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| `node:path`/Vitest alias config | repo config | Resolve `@/` imports in frontend tests | Needed only if adding frontend component tests outside current `lib/**/*.test.ts` include; prefer keeping tests in existing patterns. [VERIFIED: `frontend/vitest.config.ts`] | HIGH |
| Native `<dialog>` (`JobDetailDialog`) | Browser/React DOM | Modal detail view with built-in focus trapping | WR-01 fix must account for native dialog focus behavior; do not replace with custom dialog. [VERIFIED: `frontend/components/board/JobDetailDialog.tsx`] | HIGH |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Token/boundary-aware matching in mapper | Regex word-boundary matching on normalized string | Regex boundaries can work, but token-set comparison is simpler for already-normalized whitespace terms and aligns with current normalization helpers. Either is acceptable if deterministic and accent-insensitive. [ASSUMED] |
| Keep chat panel mounted while detail open | Close panel and restore focus to launcher via delayed query | Reopening/focusing launcher is timing-fragile because launcher mounts conditionally; keeping panel mounted or focusing a stable always-mounted control is less flaky. [VERIFIED: `ChatWidget.tsx` conditional launcher render] |
| Add React Testing Library/component test for focus | Manual reasoning only | Repo currently has Vitest node-environment tests for `lib/**/*.test.ts`; adding component tests may require config expansion. Prefer smallest viable deterministic coverage; if component test harness is absent, add focused unit/helper extraction or minimally extend config with care. [VERIFIED: `frontend/vitest.config.ts`] | 

**Installation:** No new packages required.

## Architecture Patterns

### Recommended Project Structure

```text
backend/
├── app/services/intent/mapper.py      # CR-01 + WR-03 deterministic mapping logic
└── tests/test_intent_mapper.py        # regression coverage for mapper
frontend/
├── components/board/chat/ChatWidget.tsx   # WR-01 detail open/close focus flow
├── components/board/chat/ChatPanel.tsx    # dialog semantics/focus (WR-02 deferred)
├── components/board/chat/ChatThread.tsx   # trigger propagation (already present)
├── components/board/chat/ChatResultsList.tsx
├── components/board/chat/ChatResultItem.tsx
└── lib/chatApply.test.ts                  # existing Vitest pattern (not WR-01/03 target)
```

### Pattern 1: Server-authoritative safe mapping

**What:** LLM candidate is untrusted; `map_intent()` computes final safe `applied_params`, statuses, and limitations.
**When to use:** Any ambiguity/conflict in city/sort/non-native fields.
**Example:**

```python
# Source: backend/app/services/intent/mapper.py [VERIFIED]
# Candidate is untrusted; mapper computes safe applied_params and statuses.
applied_city, city_reason_code = _resolve_city_safe(candidate.city, raw)
...
return IntentContract(..., applied_params=AppliedParams(q=applied_q, city=applied_city, sort=applied_sort), ...)
```

### Pattern 2: Deterministic regression-first closure

**What:** Phase 23 used TDD-style targeted commits (RED/GREEN) for mapper hardening; Phase 24 should follow same pattern for CR-01/WR-03/WR-01.
**When to use:** Gap closure where audit already identified exact failing behavior.
**Example:**

```text
# Source: 23-01-SUMMARY.md [VERIFIED]
Task 1 commits: 8d0c621 (test), 27e1a8c (fix) — TDD task with RED and GREEN commits.
```

### Pattern 3: Canonical board state preserved by chat

**What:** Chat apply maps to canonical board filters via `appliedParamsToBoardFilters`/`buildBoardHref` and never exposes contacts.
**When to use:** Any UI change in chat/apply/detail flow.
**Example:**

```ts
// Source: frontend/components/board/chat/ChatWidget.tsx [VERIFIED]
const filters = appliedParamsToBoardFilters(lastResponse.interpretation.applied_params);
const href = buildBoardHref({ ...filters, page: 1, vaga: null });
router.replace(href, { scroll: false });
```

### Anti-Patterns to Avoid

- **Candidate-trusted city application:** Never apply `candidate.city` just because it resolved to whitelist if raw text indicates conflicting supported cities/aliases/remoto. [VERIFIED: CR-01]
- **Substring semantics on whole query string:** Do not check `term in applied_q` across the full string for influence detection; it creates false positives. [VERIFIED: WR-03]
- **Unmount-and-pray focus restore:** Do not store a trigger ref, unmount its DOM node, then `requestAnimationFrame(() => trigger.focus())` without verifying connectivity/fallback. [VERIFIED: WR-01]
- **Scope creep into WR-02/D-14:** Do not implement full custom focus trap unless plan explicitly expands scope; Phase 25 marks it deferred. [VERIFIED: ROADMAP Phase 25, 23-02 SUMMARY]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| City whitelist normalization | New ad-hoc city parser scattered in UI or endpoint | Existing `resolve_city` + `_resolve_city_safe` + `_detect_city_from_raw_text` in mapper | Single deterministic source prevents conflicting behavior. [VERIFIED] |
| Board filter normalization for apply gating | Manual string checks in components | `normalizeFilters` / `appliedParamsToBoardFilters` | Already encodes canonical supported-city/sort semantics. [VERIFIED: `chatApply.ts`] |
| Modal dialog semantics | Custom focus trap/dialog from scratch | Native `<dialog>.showModal()` in `JobDetailDialog`; minimal focused improvements in `ChatPanel` | Native dialog already gives focus trap/ESC/backdrop/inert behavior. [VERIFIED: `JobDetailDialog.tsx`] |

**Key insight:** Phase 24 is about closing specific safety/a11y gaps in existing deterministic seams; new abstractions increase regression risk more than they help.

## Common Pitfalls

### Pitfall 1: Fixing only the exact reported CR-01 examples
**What goes wrong:** Tests pass for `sp ou rio de janeiro` but miss `rj`, `bh`, `home office`, or candidate-absent/present asymmetry.
**Why it happens:** CR-01 description names two examples; implementation bug is broader.
**How to avoid:** Add a matrix covering aliases (`sp/rj/bh`), full names, `remoto/home office/trabalho remoto`, candidate present/absent, and same-city alias agreement. [VERIFIED: `_RAW_TEXT_CITY_PATTERNS` contains these forms]
**Warning signs:** Fix adds special-case `if "sp" in raw and "rio" in raw` style checks.

### Pitfall 2: Over-blocking legitimate same-city mentions
**What goes wrong:** "vaga em sp, sao paulo" or candidate=SP with raw "sp" becomes conflict/ignored.
**Why it happens:** Raw-text detection sees multiple patterns mapping to same canonical city or different text forms.
**How to avoid:** Treat same canonical city as agreement, different canonical cities as conflict. Use `_detect_city_from_raw_text()` canonicalization result, not raw token count. [VERIFIED: `_detect_city_from_raw_text` dedupes by canonical name]
**Warning signs:** Regression where previously applied SP/RJ/BH/Remoto becomes ignored.

### Pitfall 3: Changing non-whitelist candidate semantics accidentally
**What goes wrong:** Candidate "Campinas" with raw containing "remoto" starts applying Remoto, changing existing MVP limitation behavior.
**Why it happens:** Raw-text conflict/normalization is consulted before/instead of candidate handling without preserving intended precedence.
**How to avoid:** Add/keep regressions for present non-whitelist candidate (`Campinas`) remaining `not_in_whitelist`; only block unsafe application. Verify against existing tests in `test_intent_mapper.py`. [VERIFIED: existing test `test_absent_candidate_raw_text_city_safeguards`]
**Warning signs:** `not_in_whitelist` becomes `normalized` for Campinas candidate.

### Pitfall 4: Focus restore target unmounted by design
**What goes wrong:** Detail closes and focus goes to `document.body`.
**Why it happens:** Chat panel is closed before detail opens; trigger node is removed from DOM.
**How to avoid:** Keep trigger mounted while detail is open, or restore to an always-mounted stable fallback after detail close (and ensure fallback exists after render). Prefer keeping panel mounted behind native dialog, because dialog is modal/inert anyway. [VERIFIED: `ChatWidget.tsx`, `ChatPanel.tsx` returns null when closed]
**Warning signs:** `trigger?.focus()` called on disconnected node; no fallback.

### Pitfall 5: Scope creep into full focus trap
**What goes wrong:** Phase 24 balloons into dialog primitive rewrite.
**Why it happens:** WR-01 and WR-02 are adjacent.
**How to avoid:** Implement WR-01 only (stable mounted focus restore). Keep WR-02/D-14 explicitly deferred in summaries/audit handoff. [VERIFIED: ROADMAP Phase 24 SC3/25 SC4]

## Code Examples

### Current CR-01 gap (to replace)

```python
# Source: backend/app/services/intent/mapper.py [VERIFIED]
lowered = _strip_accents_lower(raw)
mentioned = []
for token, canon in (
    ("sao paulo", "SA�o Paulo"),
    ("rio de janeiro", "Rio de Janeiro"),
    ("belo horizonte", "Belo Horizonte"),
    ("campinas", "Campinas"),
):
    if token in lowered:
        mentioned.append(canon)
distinct_whitelist = {m for m in mentioned if m in {"SA�o Paulo", "Rio de Janeiro", "Belo Horizonte"}}
city_conflict = len(distinct_whitelist) > 1
...
if city_conflict:
    ...
else:
    applied_city, city_reason_code = _resolve_city_safe(candidate.city, raw)
```

**Problem:** ignores alias/abbrev/remoto forms already modeled by `_RAW_TEXT_CITY_PATTERNS`.

### Safer CR-01 direction (pattern)

```python
# Pattern example for planner; adapt carefully to preserve existing reason semantics [ASSUMED]
raw_detected_city, raw_city_reason = _detect_city_from_raw_text(raw)
resolved_candidate_city, resolved_candidate_reason = _resolve_city_safe(candidate.city, raw)

if raw_city_reason == "conflict_resolved":
    applied_city, city_status, city_reason_code = None, FieldStatus.IGNORADO, "conflict_resolved"
elif raw_detected_city and resolved_candidate_city and raw_detected_city != resolved_candidate_city:
    applied_city, city_status, city_reason_code = None, FieldStatus.IGNORADO, "conflict_resolved"
else:
    # keep existing resolution semantics; prefer explicit candidate when safe,
    # or raw-detected city when candidate absent.
    ...
```

### Current WR-03 gap (to replace)

```python
# Source: backend/app/services/intent/mapper.py [VERIFIED]
if applied_q:
    aq = _strip_accents_lower(applied_q)
    for t in raw_terms:
        for tok in _normalize_whitespace(str(t)).split(" "):
            k = _strip_accents_lower(tok)
            if k and k in aq:
                influenced = True
```

**Problem:** substring match on whole query string can misclassify influence.

### Safer WR-03 direction (pattern)

```python
# Pattern example for planner [ASSUMED]
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

### Current WR-01 gap (to replace)

```tsx
// Source: frontend/components/board/chat/ChatWidget.tsx [VERIFIED]
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

**Problem:** trigger is inside `ChatPanel`; closing panel unmounts it.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw-text city fallback used ambiguous `\brio\b` | 23-01 removed bare `\brio\b`, kept `rj`/`rio de janeiro` | 2026-11-20 (23-01) | Reduced false positives but left CR-01 alias/conflict bypass. [VERIFIED: 23-01 SUMMARY] |
| Apply gating allowed city-only no-op cases | 23-02 gated by normalized useful filters | 2026-11-20 (23-02) | Prevented no-op apply for unsupported city-only input. [VERIFIED: 23-02 SUMMARY] |
| Chat focus had no trigger propagation on detail close | 23-02 propagated trigger and attempted restore | 2026-11-20 (23-02) | Improved intent but left WR-01 unmounted-trigger edge case. [VERIFIED: 23-02 SUMMARY, 23-REVIEW] |

**Deprecated/outdated:**
- **Assuming "candidate present => candidate resolution is authoritative":** outdated after CR-01; raw-text conflicts must be able to veto. [VERIFIED]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | No new dependencies are needed; pytest/vitest and existing project stack are sufficient. | Standard Stack | Low - if component testing requires setup, plan may need small config/test-harness task. |
| A2 | Token-set matching for WR-03 is sufficient and preferable to substring matching for current `applied_q` composition. | Architecture Patterns / Code Examples | Low/Medium - could miss edge cases where normalization differs; mitigate with targeted regressions. |
| A3 | Keeping chat panel mounted behind native `JobDetailDialog` is acceptable UX and satisfies "mounted/stable control" for WR-01. | Common Pitfalls / Code Examples | Medium - if product wanted panel hidden, may need alternative stable fallback focus target. |
| A4 | Full focus trap (WR-02/D-14) remains out of Phase 24 and should not be implemented. | Scope / Anti-Patterns | Low - roadmap/Phase 25 explicitly defer it; if user expects it, scope conflict must be resolved before planning. |

## Open Questions

1. **WR-01 fix strategy: keep ChatPanel mounted or restore to stable fallback?**
   - What we know: Current trigger is inside ChatPanel and unmounts when panel closes; native JobDetailDialog is modal and manages its own trap. [VERIFIED]
   - What's unclear: Whether product prefers chat hidden behind detail or visible after close.
   - Recommendation: Keep panel mounted while detail is open (simplest mounted trigger), or on close reopen chat and focus trigger; pick one and cover with deterministic/manual check. Avoid timing-fragile focus to conditionally rendered launcher.

2. **Should CR-01 treat raw-detected single city different from resolved candidate city as conflict?**
   - What we know: Review examples are clear conflicts; `_detect_city_from_raw_text` can return a single canonical city. [VERIFIED]
   - What's unclear: Rare cases where raw text mentions a supported city but candidate is another supported city due model extraction; safest is conflict/ignore.
   - Recommendation: Treat any disagreement between raw-detected supported city signal and resolved candidate as `conflict_resolved`/ignored unless clearly same canonical city.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js / npm | Frontend vitest/tsc | ✓ | Node present (`node -v` not captured in research shell; npm project present) [ASSUMED] | Run in project env; CI/local dev standard |
| Python + pytest | Backend mapper tests | ✓ | pytest used by project; exact version not captured [ASSUMED] | Use existing backend test environment/venv |
| Git | Evidence/commits | ✓ | Repo is git | — |

**Missing dependencies with no fallback:**
- None identified.

**Missing dependencies with fallback:**
- None identified.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Backend: pytest; Frontend: Vitest 2.1.9 |
| Config file | Backend: pytest config not inspected (assume repo default/pyproject); Frontend: `frontend/vitest.config.ts` |
| Quick run command | `cd backend && pytest -q tests/test_intent_mapper.py` |
| Full suite command | `cd backend && pytest -q tests/test_intent_mapper.py tests/test_intent_contract.py tests/test_intent_parser.py` and `cd frontend && npm run test -- lib/chatApply.test.ts` (extend as needed) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CL-01 | Raw-text alias/abbrev/remoto city conflicts do not apply wrong city when candidate present | unit | `cd backend && pytest -q tests/test_intent_mapper.py -k conflict` | ✅ `backend/tests/test_intent_mapper.py` (new cases needed) |
| CL-01 | Supported same-city alias agreement still applies safely | unit | `cd backend && pytest -q tests/test_intent_mapper.py` | ✅ |
| CL-05 / WR-03 | Non-native influence detection does not misclassify by substring over full `applied_q` | unit | `cd backend && pytest -q tests/test_intent_mapper.py -k non_native` | ✅ (new case needed) |
| CL-05 / WR-01 | Chat detail close restores focus to mounted/stable control | unit/component/manual-assisted | `cd frontend && npm run test -- lib/chatApply.test.ts` (insufficient alone); add focused test/harness or document manual keyboard check | ❌ Wave 0 for automated WR-01 coverage |

### Sampling Rate

- **Per task commit:** `cd backend && pytest -q tests/test_intent_mapper.py` for mapper changes; `cd frontend && npm run test -- lib/chatApply.test.ts` for chatApply-only changes; add WR-01-specific command if created.
- **Per wave merge:** Backend intent suite + frontend chat/unit tests touched.
- **Phase gate:** All Phase 24 targeted tests green before `/gsd-verify-work`; no regression in public/chat contracts.

### Wave 0 Gaps

- [ ] `backend/tests/test_intent_mapper.py` — add CR-01 regression cases for candidate-present raw-text alias/abbrev/remoto conflicts and same-canonical agreement.
- [ ] `backend/tests/test_intent_mapper.py` — add WR-03 regression case where substring would falsely match but token-aware should not.
- [ ] Frontend WR-01 automated coverage gap: current Vitest config includes only `lib/**/*.test.ts` (`frontend/vitest.config.ts`). Either add a pure helper/test seam under `lib/` or extend Vitest config to support component tests; if not viable, require explicit manual keyboard verification in plan and capture evidence.

*(If no gaps: "None — existing test infrastructure covers all phase requirements")*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth changes; public board/chat remain unauthenticated. |
| V3 Session Management | no | No session changes. |
| V4 Access Control | no | No admin/public boundary change; chat still public. |
| V5 Input Validation | yes | Deterministic server-side mapping/validation remains authoritative; raw text treated as untrusted; no new unsafe parsing. [VERIFIED: mapper/parser design] |
| V6 Cryptography | no | No crypto changes. |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| LLM prompt/input causes unsafe filter application | Tampering / Elevation of trust | Treat candidate as untrusted; deterministic whitelist/conflict resolution; never apply conflicting city. [VERIFIED] |
| UI focus loss / keyboard trap regression | Spoofing/DoS-adjacent usability (accessibility) | Maintain visible focus, return focus to mounted stable control, avoid custom trap regressions. [VERIFIED: WR-01/WR-02] |
| Regressing contact exposure in chat payload | Information Disclosure | Preserve `JobPublic` contract and existing chat response handling; no contact fields in chat. [VERIFIED: API-01/UI-02] |

## Sources

### Primary (HIGH confidence)

- `.planning/v1.3-MILESTONE-AUDIT.md` - Phase 24 gap scope, CR-01/WR-01/WR-03, CL-01/CL-02/CL-05 status.
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-VERIFICATION.md` - Phase 23 gaps/deferred items and evidence.
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-REVIEW.md` - CR-01/WR-01/WR-02/WR-03 review findings.
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-01-SUMMARY.md`, `23-02-SUMMARY.md` - prior fix patterns and scope decisions.
- `backend/app/services/intent/mapper.py` - current mapper implementation and exact CR-01/WR-03 locations.
- `backend/tests/test_intent_mapper.py` - current regression coverage and test style.
- `frontend/components/board/chat/ChatWidget.tsx`, `ChatPanel.tsx`, `ChatThread.tsx`, `ChatResultsList.tsx`, `ChatResultItem.tsx` - current focus/trigger flow.
- `frontend/lib/chatApply.ts`, `frontend/lib/chatApply.test.ts` - current CL-05 gating semantics.
- `frontend/components/board/JobDetailDialog.tsx` - native dialog focus/trap behavior.
- `frontend/package.json`, `frontend/vitest.config.ts`, `.planning/config.json` - test/tooling/workflow constraints.

### Secondary (MEDIUM confidence)

- `.planning/research/STACK.md` - stack baseline versions/rationale (may be stale in places; verified key frontend versions against `package.json`).

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified from package.json/config/codebase.
- Architecture: HIGH - verified from current code, audit, verification, and review artifacts.
- Pitfalls: HIGH - directly derived from confirmed CR-01/WR-01/WR-03 behavior and existing tests.

**Research date:** 2026-11-21
**Valid until:** 2026-12-21 (stable internal codebase patterns; recheck if mapper/chat files changed)
