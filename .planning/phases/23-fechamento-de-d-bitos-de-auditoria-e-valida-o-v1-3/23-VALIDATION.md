---
phase: 23
slug: fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-19
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest (+ pytest-asyncio where repo uses it). Frontend: Vitest (node env for `frontend/lib/**/*.test.ts`). |
| **Config file** | `backend/pyproject.toml`, `backend/tests/conftest.py`; `frontend/vitest.config.ts`, `frontend/package.json`. |
| **Quick run command** | `cd backend && python -m pytest -q tests/test_intent_mapper.py tests/test_intent_parser.py` (CL-01) / `cd frontend && npm run test:chat` or targeted `npx vitest run frontend/lib/chatApply.test.ts frontend/lib/cities.test.ts` (CL-05) |
| **Full suite command** | Targeted phase-relevant suites: backend intent/chat suites as environment allows + `cd frontend && npm test` (or project equivalent). Manual/UAT/Nyquist/audit-gate evidence required for non-automatable closure items. |
| **Estimated runtime** | ~30-120 seconds (targeted automated checks; environment-dependent) |

---

## Sampling Rate

- **After every task commit:** Run the smallest relevant deterministic command for touched scope (e.g. intent mapper/parser tests, chatApply/cities/api-related frontend tests, or artifact consistency checks).
- **After every plan wave:** Re-run targeted backend/frontend tests touched by the wave and refresh reconciliation artifacts/evidence.
- **Before `/gsd-verify-work`:** Targeted automated suites for implemented code changes must be green where runnable; closure artifacts must reflect executed/deferred outcomes per decisions.
- **Max feedback latency:** 120 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 23-TBD-CL01-code | TBD | TBD | CL-01 | T-23-01 | Raw-text city fallback must not classify "Rio Grande do Sul"/"Rio Branco" as Rio de Janeiro while preserving supported RJ/SP/BH/Remoto detection; no non-whitelist invention | unit (backend) | `cd backend && python -m pytest -q tests/test_intent_mapper.py tests/test_intent_parser.py` | ✅ (extend) | ⬜ pending |
| 23-TBD-CL01-runtime | TBD | TBD | CL-01 | N/A | Toolbar and chat recognize/apply registered city correctly (retaste runtime registrado) or accepted per-item deferment documented | manual/runtime + artifact reconciliation | N/A (record evidence in debug/22 UAT/manual/verification/MVP/audit) | ✅ (artifacts exist) | ⬜ pending |
| 23-TBD-CL02 | TBD | TBD | CL-02 | N/A | 4 quick tasks disposed with evidence or justified deferral; none remain missing/incomplete in audit-open context | artifact reconciliation + audit-open check | `gsd-sdk query audit-open` | ✅ (quick task/state/audit artifacts exist) | ⬜ pending |
| 23-TBD-CL03 | TBD | TBD | CL-03 | N/A | 21/22 verification/UAT/manual artifacts reach final accepted traceable states with executed/deferred per-item records | artifact reconciliation + evidence review | `gsd-sdk query audit-open` (supporting gate) | ✅ (artifacts exist) | ⬜ pending |
| 23-TBD-CL04 | TBD | TBD | CL-04 | N/A | 20-VALIDATION created; 19/21/22-VALIDATION evolved to nyquist_compliant or accepted deviation with plan of action | artifact authoring/reconciliation | N/A (file-based) | ❌ `20-VALIDATION.md` missing; others exist partial | ⬜ pending |
| 23-TBD-CL05-chatapply | TBD | TBD | CL-05 | T-23-05A | `canApplyChatToBoard` does not enable apply for non-normalizable city-only applied params; supported cities and gating rules preserved | unit (frontend) | `cd frontend && npm run test:chat` (or targeted vitest for `chatApply`) | ✅ (extend) | ⬜ pending |
| 23-TBD-CL05-api | TBD | TBD | CL-05 | T-23-05B | `chatSearch` maps malformed/failed 200 JSON parse to safe typed `ApiError` pt-BR without leaking internals | unit/manual code check as feasible | Targeted frontend test command if added; otherwise deterministic review + related tests | ⚠️ helper untested as dedicated unit (gap) | ⬜ pending |
| 23-TBD-CL05-a11y | TBD | TBD | CL-05 | N/A | Feasible focus/a11y improvements applied (e.g. restore/focus handling) or explicitly deferred with justification | manual/UI verification + artifact note | N/A | ✅ (components exist) | ⬜ pending |
| 23-TBD-CL05-security | TBD | TBD | CL-05 | T-23-05C | Phase 22 security controls/limitations documented in `22-SECURITY.md`; audit updated to reflect closure/debt state | artifact authoring/reconciliation | N/A (file-based) | ❌ `22-SECURITY.md` missing | ⬜ pending |
| 23-TBD-GATE | TBD | TBD | CL-01..CL-05 | N/A | `gsd-sdk query audit-open` reports no new items from Phase 23 and `v1.3-MILESTONE-AUDIT.md` reflects resolved/deferred debts enabling milestone closure | audit gate + doc reconciliation | `gsd-sdk query audit-open` | ✅ (audit exists) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.planning/phases/20-api-publica-de-chat-search-resiliente/20-VALIDATION.md` — create Nyquist validation artifact for Phase 20 (CL-04)
- [ ] `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-SECURITY.md` — create security review artifact for Phase 22 chat-search controls/limitations (CL-05/D-15)
- [ ] `backend/tests/test_intent_mapper.py` (and `backend/tests/test_intent_parser.py` if needed) — add regressions for `\brio\b` false positives ("Rio Grande do Sul"/"Rio Branco") and preserve valid RJ cases (CL-01)
- [ ] `frontend/lib/chatApply.test.ts` — add non-normalizable city-only apply no-op/gating coverage while preserving supported cases (CL-05)
- [ ] Reconciliation updates to existing artifacts as planned: `19/21/22-VALIDATION.md`, `21/22-VERIFICATION.md`, `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, debug session, `STATE.md`, `REQUIREMENTS.md` (if needed), `v1.3-MILESTONE-AUDIT.md` (CL-01..CL-05)

*Note: some items are documentation/reconciliation Wave 0 gaps rather than test scaffolds; keep honest and traceable.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Registered city correctly recognized/applied in toolbar and chat (reported case) | CL-01 | Requires runtime/browser/app state and real interaction flow; deterministic code/tests alone insufficient | Run app in available environment, reproduce reported scenario, confirm city filter/chat apply registered city correctly and not marked ignored; capture evidence in debug/UAT/verification artifacts or record accepted per-item deferment with reason/risk/next action. |
| Phase 21/22 human/UAT/manual scenarios (responsive/layering/focus, live loading/error/retry/pagination, canonical apply/detail/reveal, kill-switch/non-regression where applicable) | CL-03 | Browser/runtime/operator checks; some may be environment-infeasible | Execute feasible items and document results; for infeasible items record per-item deferment (reason, risk residual, future condition/action) so artifacts reach final accepted traceable states. |
| Feasible chat a11y/focus behavior improvements (dialog focus/restore) | CL-05 | UX/focus behavior is interaction-dependent | Verify focus behavior manually where changes are made; if not viable, document explicit deferment with justification. |
| Quick-task disposition semantics reflected in audit-open and project docs | CL-02, CL-05 (gate) | Depends on `gsd-sdk` audit semantics and cross-artifact consistency | Reconcile STATE/audit/references with evidence/justification, run `gsd-sdk query audit-open`, and confirm no new Phase 23 items remain open. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
