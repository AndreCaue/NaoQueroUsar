---
phase: 25
slug: reconciliar-gates-de-fechamento-e-revalidar-auditoria-v1-3
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-22
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None (artifact reconciliation only; no product code changes) |
| **Config file** | none |
| **Quick run command** | `gsd-sdk query audit-open` |
| **Full suite command** | `gsd-sdk query audit-open` + `rg -n "status:|gaps_found|human_needed|partial|gaps_closed_with_accepted_residuals|accepted_with_deferred_runtime_checks|passed|CL-02|CL-05|D-14/WR-02" .planning/v1.3-MILESTONE-AUDIT.md .planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-VERIFICATION.md .planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-VERIFICATION.md .planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-HUMAN-UAT.md .planning/REQUIREMENTS.md .planning/STATE.md` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `gsd-sdk query audit-open`
- **After every plan wave:** Run full suite command (audit-open + consistency grep)
- **Before `/gsd-verify-work`:** Full suite must be green and all reconciled statuses internally consistent
- **Max feedback latency:** 15 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 25-01-01 | 01 | 1 | CL-02 | T-25-01 | No fabricated evidence; only 4 known quick-task slugs may receive formal audit-open heuristic acceptance | smoke/manual-doc | `gsd-sdk query audit-open` | ✅ | ⬜ pending |
| 25-01-02 | 01 | 1 | CL-05 | T-25-02 | 24-HUMAN-UAT/24-VERIFICATION reconciled to traceable accepted states; no ambiguous partial/human_needed left undocumented | smoke/manual-doc | `rg -n "status:|complete|accepted_with_deferred_runtime_checks|deferimento aceito por item" .planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-HUMAN-UAT.md .planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-VERIFICATION.md` | ✅ | ⬜ pending |
| 25-01-03 | 01 | 1 | CL-05 | T-25-03 | 23-VERIFICATION updated in-place with dated re-verification; history preserved; D-14/WR-02 remains accepted residual only | smoke/manual-doc | `rg -n "gaps_closed_with_accepted_residuals|Re-verificação|D-14/WR-02|focus trap" .planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-VERIFICATION.md` | ✅ | ⬜ pending |
| 25-02-01 | 02 | 2 | CL-02, CL-05 | T-25-01 | v1.3-MILESTONE-AUDIT updated in-place to passed-with-accepted-residuals; CL-02 acceptance registered in audit/REQUIREMENTS/STATE with no-new-missing condition | smoke/manual-doc | `rg -n "passed|accepted_residual|CL-02|CL-05|pronto para .*audit-milestone|nenhum .*missing.*novo" .planning/v1.3-MILESTONE-AUDIT.md .planning/REQUIREMENTS.md .planning/STATE.md` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] No new test framework or code stubs required — phase is artifact reconciliation only.
- [ ] Existing artifacts and `gsd-sdk query audit-open` cover phase validation.

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 24 WR-01 keyboard/browser checks remain deferred by item | CL-05 | Browser/integrated runtime unavailable in this execution context | Confirm `24-HUMAN-UAT.md` and `24-VERIFICATION.md` record each pending WR-01 scenario as accepted deferment with motivo, risco residual, and ação futura; do not mark executed. |
| Audit-open heuristic may still report 4 known quick tasks | CL-02 | Scanner behavior is heuristic/implementation-defined | Run `gsd-sdk query audit-open`; if only the 4 known slugs remain as `[missing]`, confirm audit/REQUIREMENTS/STATE record explicit formal acceptance with scope and no-new-missing condition. Any other missing item blocks. |

*All other phase behaviors have automated/smoke verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending