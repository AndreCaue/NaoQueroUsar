---
phase: 24
slug: corrigir-conflito-critico-de-cidade-e-residuos-de-review
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-21
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest; Frontend: Vitest 2.1.9 |
| **Config file** | Backend: repo pytest defaults/pyproject; Frontend: `frontend/vitest.config.ts` |
| **Quick run command** | `cd backend && pytest -q tests/test_intent_mapper.py` |
| **Full suite command** | `cd backend && pytest -q tests/test_intent_mapper.py tests/test_intent_contract.py tests/test_intent_parser.py && cd ../frontend && npm run test -- lib/chatApply.test.ts lib/chatFocus.test.ts` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && pytest -q tests/test_intent_mapper.py` for mapper changes; `cd frontend && npm run test -- lib/chatApply.test.ts lib/chatFocus.test.ts` for chat focus/apply changes.
- **After every plan wave:** Run backend intent suite + frontend chat/lib tests touched by the wave.
- **Before `/gsd-verify-work`:** Full suite must be green; no regression in public/chat contracts.
- **Max feedback latency:** 30 seconds

---

## Per-task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 24-01-01 | 01 | 1 | CL-01 | T-24-01 | Raw-text alias/abbrev/remoto city conflicts do not apply wrong city when candidate city is present; general non-whitelist-vs-supported conflict guard prevents wrong-city promotion; same-canonical agreement remains safe | unit | `cd backend && pytest -q tests/test_intent_mapper.py -k "conflict or cidade or whitelist"` | ✅ (new cases in plan) | ⬜ pending |
| 24-01-02 | 01 | 1 | CL-05 | T-24-03 | Non-native influence detection uses normalized token-set membership; no substring false positive over full `applied_q`; genuine token membership still marks approximation | unit | `cd backend && pytest -q tests/test_intent_mapper.py -k "non_native or token_set or wr03"` | ✅ (new case in plan) | ⬜ pending |
| 24-02-01 | 02 | 1 | CL-05 | T-24-04 | Focus target helper returns connected trigger or stable mounted fallback (`#chat-panel-close`), never `document.body` | unit | `cd frontend && npm run test -- lib/chatFocus.test.ts` | ❌ W0 (created by plan) | ⬜ pending |
| 24-02-02 | 02 | 1 | CL-05 | T-24-04 | Chat detail close restores focus to mounted/stable control in keyboard flow; ChatPanel remains mounted while detail open; no custom focus trap | manual-assisted + unit regression | `cd frontend && npm run test -- lib/chatApply.test.ts lib/chatFocus.test.ts` (automated regression only; WR-01 component flow requires manual keyboard check) | ✅ partial | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/test_intent_mapper.py` — CR-01 regression cases planned (24-01-01), including candidate-present raw-text alias/abbrev/remoto conflicts, same-canonical agreement, and general non-whitelist-vs-supported conflict guard.
- [x] `backend/tests/test_intent_mapper.py` — WR-03 regression case planned (24-01-02) with observable false-positive and positive control.
- [x] Frontend WR-01 coverage gap addressed by plan: `frontend/lib/chatFocus.ts` + `frontend/lib/chatFocus.test.ts` seam (24-02-01), plus explicit manual keyboard verification for ChatWidget focus flow (24-02-02).

*Existing infrastructure covers remaining phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Chat detail close restores focus to mounted/stable control in real keyboard flow | CL-05 (WR-01) | No existing frontend component test harness; Vitest scope is `lib/**/*.test.ts` and plan uses helper seam only | Open chat, open a result detail by keyboard, close detail by keyboard/Escape, confirm focus lands on original chat trigger when connected or `#chat-panel-close` fallback; confirm focus is never `document.body`; confirm chat panel remained mounted behind native dialog |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready
