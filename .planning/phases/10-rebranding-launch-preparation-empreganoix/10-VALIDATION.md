---
phase: 10
slug: rebranding-launch-preparation-empreganoix
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-14
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (backend) + Vitest 5.0.4 (frontend, se aplicável) |
| **Config file** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd backend; .venv\Scripts\python.exe -m pytest -q` |
| **Full suite command** | `cd backend; .venv\Scripts\python.exe -m pytest -q` (backend) + `cd frontend; npm run lint && npm run build` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command (backend) + `cd frontend; npm run build`
- **After every plan wave:** Run full suite + build
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 180 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | BRND-01 | — | Nenhum leftover "NaoQueroUsar"/"NQU"/"suportenqs" em código frontend | grep | `grep -rn "NaoQueroUsar\|suportenqs" frontend/` (deve ser vazio) | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | BRND-02 | — | Slogan presente em layout.tsx e admin layout | grep | `grep -rn "Procurar um emprego, não deve dar trabalho" frontend/` | ✅ | ⬜ pending |
| 10-01-03 | 01 | 1 | BRND-03 | — | Tokens @theme intactos (#8b5cf6/#a78bfa/#facc15) | grep | `grep -n "#8b5cf6\|#a78bfa\|#facc15" frontend/app/(public)/public.css` | ✅ | ⬜ pending |
| 10-02-01 | 02 | 2 | BRND-01 | T-10-01 | Backend title/docs/seed renomeados | unit | `cd backend; .venv\Scripts\python.exe -m pytest -q` | ✅ | ⬜ pending |
| 10-03-01 | 03 | 3 | BRND-04 | T-10-02 | Smoke gate verde com novos hosts | E2E/manual | `powershell -File scripts\verify-deploy.ps1 -FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `grep`-based assertion (ou script) para BRND-01 (nenhum leftover "NaoQueroUsar"/"NQU"/"suportenqs" em código)
- [ ] Atualizar `backend/tests/test_cors.py` exemplos para novo host (consistência)
- [ ] Criar assets de marca (favicon, og-image) — D-05

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Deploy real Vercel + Render com ENV=prod, Turnstile live, CRON_SECRET | BRND-04 | Dashboards externos (Vercel/Render/Cloudflare) | Seguir docs/DEPLOY.md com novos hosts; rodar verify-deploy.ps1 até verde |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending