---
phase: 13
slug: canonical-host-deploy-ops-alignment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-15
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Repository consistency checks (diff/grep/read review) + `scripts/verify-deploy.ps1` operator smoke gate |
| **Config file** | `scripts/verify-deploy.ps1` (`-FrontendUrl`, `-BackendUrl`, `-CronSecret`/`$env:CRON_SECRET`, `-AllowTestTurnstile`) |
| **Quick run command** | Targeted checks on touched artifacts (e.g. `rg -n "empreganoix\.vercel\.app|empreganoix\.onrender\.com|nao-quero-usar|nqu-backend-x60n|empreganoix-six" docs/DEPLOY.md render.yaml frontend/.env.example scripts/verify-deploy.ps1 .planning/REQUIREMENTS.md .planning/ROADMAP.md`) and review that historical evidence rows are preserved |
| **Full suite command** | `powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 -FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com` (when canonical hosts are provisioned/reachable with correct envs/secrets) |
| **Estimated runtime** | ~30 seconds (repo checks) / ~60-180 seconds (live smoke, excluding cold start) |

---

## Sampling Rate

- **After every task commit:** Review touched D-05/planning files for (a) canonical state-alvo correctness, (b) historical evidence rows unchanged, (c) no secrets added, (d) no runtime code edits (per D-06) unless explicitly justified.
- **After every plan wave:** Re-read `docs/DEPLOY.md` canonical target/mapping/D-10 matrix and `REQUIREMENTS.md`/`ROADMAP.md` notes for D-04/D-08/D-10/D-12/D-14/D-16 consistency.
- **Before `/gsd-verify-work`:** D-10 matrix complete with status/ref for every required check; closure notes for BRND-04/SECR-12/LIFE-13 recorded. If canonical execution occurred, full `verify-deploy.ps1` pass recorded with URLs/results/cold-start.
- **Max feedback latency:** 180 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 13-?-?? | TBD | TBD | BRND-04 | — | Canonical hosts applied as state-alvo in docs/config/examples/scripts with legacy hosts mapped (no silent canonical swap) | manual + smoke (when live) | `powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 -FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com` (checks 1–6,10) | ✅ | ⬜ pending |
| 13-?-?? | TBD | TBD | SECR-12 | T-06-01 | `/admin/expire` documented/evidenced as X-Cron-Secret-only fail-closed; unauth rejected, auth path idempotent; no T-06-01 drift | smoke/manual evidence mapping | `scripts\verify-deploy.ps1` checks 7–9 (unauth refused/fail-closed, 200 idempotent x2, no leak) | ✅ | ⬜ pending |
| 13-?-?? | TBD | TBD | LIFE-13 | — | Cron catch-up target/auth/idempotency aligned to canonical endpoint or explicitly handed off with mapped evidence | smoke/manual evidence mapping | `scripts\verify-deploy.ps1` check 8 + runbook/Actions alignment review | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements (repo alignment + existing `scripts/verify-deploy.ps1` gate). No in-repo test scaffold creation required.

*External prerequisites (not in-repo):*
- [ ] Canonical host provisioning/execution evidence — run `scripts/verify-deploy.ps1` against canonical hosts when available; otherwise record `pendente de execução operacional` with handoff (D-04/D-14).
- [ ] Provider/dashboard alignment (Vercel domain/env+rebuild, Render env/CORS, Turnstile Hostnames, GitHub Actions `vars.API_BASE_URL`/`CRON_SECRET`) as applicable (D-13).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Canonical↔legacy evidence mapping preserves historical records and marks status correctly | BRND-04, SECR-12, LIFE-13 | Requires judgment over historical logs/tables and contractual handoff wording | Compare `docs/DEPLOY.md` historical Registro de verificação rows (unchanged) against new canonical-target/mapping/D-10 matrix; confirm statuses: verificado em host legado / alinhado contratualmente ao canônico / pendente de execução operacional |
| No runtime behavior changes introduced | BRND-04 | Scope constraint D-06 is a review gate, not a runtime test | Inspect diffs for backend/frontend runtime files; ensure changes limited to docs/config/examples/scripts/planning unless explicitly documented deviation |
| Requirements/roadmap closure notes reflect split ownership and residual ops handoff | BRND-04, SECR-12, LIFE-13 | Traceability/wording must match D-04/D-12/D-16 and T-06-01 | Verify `REQUIREMENTS.md` checkboxes/notes and `ROADMAP.md` Phase 13 status/notes reference Phase 13 evidence/matrix and preserve prior code/contract verification history |

*Additional live checks (health/env/Turnstile, CORS preflight, cron auth/idempotency, key surfaces) are automated by `scripts/verify-deploy.ps1` when canonical hosts are reachable.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
