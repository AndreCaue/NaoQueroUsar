---
phase: 19
slug: contrato-de-intencao-e-mapeamento-seguro
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-17
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend, existing) |
| **Config file** | `backend/pyproject.toml` / existing pytest config (if present) |
| **Quick run command** | `cd backend && python -m pytest tests/services/intent -q` (once intent tests exist) |
| **Full suite command** | `cd backend && python -m pytest -q` |
| **Estimated runtime** | ~30 seconds (quick subset), varies for full suite |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/services/intent -q` (or nearest affected intent/unit tests)
- **After every plan wave:** Run `cd backend && python -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD (planner fills) | — | — | INT-01, INT-02, INT-03 | — | Untrusted NL input never invents filters; whitelist/safe defaults enforced; no contact exposure in this phase | unit | `cd backend && python -m pytest tests/services/intent -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/services/intent/` (or equivalent) — unit tests for intent schema, parser/client seams, deterministic mapper/normalization/classification (INT-01..INT-03)
- [ ] Test fixtures/mocks for Groq client responses and timeout/failure/repair paths (no live network)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| — | — | — | — |

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