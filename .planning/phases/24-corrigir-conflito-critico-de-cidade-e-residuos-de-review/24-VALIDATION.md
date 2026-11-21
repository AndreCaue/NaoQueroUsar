---
phase: 24
slug: corrigir-conflito-critico-de-cidade-e-residuos-de-review
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| **Full suite command** | `cd backend && pytest -q tests/test_intent_mapper.py tests/test_intent_contract.py tests/test_intent_parser.py && cd ../frontend && npm run test -- lib/chatApply.test.ts` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && pytest -q tests/test_intent_mapper.py` for mapper changes; `cd frontend && npm run test -- lib/chatApply.test.ts` for chatApply-only changes; add WR-01-specific command if created.
- **After every plan wave:** Run backend intent suite + frontend chat/unit tests touched by the wave.
- **Before `/gsd-verify-work`:** Full suite must be green; no regression in public/chat contracts.
- **Max feedback latency:** 30 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 24-??-?? | TBD | 1 | CL-01 | T-24-01 | Raw-text alias/abbrev/remoto city conflicts do not apply wrong city when candidate city is present; mapper ignores/conflict-resolves safely | unit | `cd backend && pytest -q tests/test_intent_mapper.py -k conflict` | ✅ `backend/tests/test_intent_mapper.py` (new cases needed) | ⬜ pending |
| 24-??-?? | TBD | 1 | CL-01 | T-24-02 | Supported same-city alias agreement still applies safely | unit | `cd backend && pytest -q tests/test_intent_mapper.py` | ✅ | ⬜ pending |
| 24-??-?? | TBD | 1 | CL-05 | T-24-03 | Non-native influence detection uses token/boundary-aware matching; no substring false positive over full `applied_q` | unit | `cd backend && pytest -q tests/test_intent_mapper.py -k non_native` | ✅ (new case needed) | ⬜ pending |
| 24-??-?? | TBD | 1 | CL-05 | T-24-04 | Chat detail close restores focus to mounted/stable control (no `document.body` loss in keyboard flow) | unit/component/manual-assisted | `cd frontend && npm run test -- lib/chatApply.test.ts` (insufficient alone); add WR-01 helper/seam or document manual keyboard check | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_intent_mapper.py` — add CR-01 regression cases for candidate-present raw-text alias/abbrev/remoto conflicts and same-canonical agreement.
- [ ] `backend/tests/test_intent_mapper.py` — add WR-03 regression case where substring would falsely match but token-aware matching should not.
- [ ] Frontend WR-01 automated coverage gap — current Vitest config includes only `lib/**/*.test.ts` (`frontend/vitest.config.ts`). Either add a pure helper/test seam under `lib/` or extend Vitest config for component tests; if not viable, require explicit manual keyboard verification in plan and capture evidence.

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Chat detail close restores focus to mounted/stable control in real keyboard flow | CL-05 (WR-01) | No existing frontend component test harness; current Vitest scope is `lib/**/*.test.ts` | Open chat, trigger result detail, close detail via keyboard, confirm focus lands on mounted/stable chat control (not `document.body`) |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
