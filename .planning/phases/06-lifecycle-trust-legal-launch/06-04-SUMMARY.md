---
phase: 06-lifecycle-trust-legal-launch
plan: 04
subsystem: infra/deploy
tags: [render, vercel, neon, github-actions, cron, cors, deploy, runbook, powershell]

# Dependency graph
requires:
  - phase: 06-lifecycle-trust-legal-launch
    plan: 01
    provides: CRON_SECRET semantics, in-process APScheduler (03:00 UTC), POST /api/v1/admin/expire {deleted, status}
  - phase: 06-lifecycle-trust-legal-launch
    plan: 02
    provides: report endpoint + badge (public surface unchanged)
  - phase: 06-lifecycle-trust-legal-launch
    plan: 03
    provides: /privacidade page + footer link (used in smoke gate)
  - phase: 04-public-board-frontend
    provides: error.tsx cold-start copy, lib/jobs.ts 15 s timeout, verify-ssr.ps1 BOM pattern
provides:
  - render.yaml blueprint (uv + frozen lock, alembic upgrade head on boot, /api/v1/health check, sync:false secrets)
  - .github/workflows/expire-cron.yml (daily 03:00 UTC + workflow_dispatch → POST /api/v1/admin/expire with X-Cron-Secret)
  - frontend/vercel.json (minimal Next.js project config)
  - docs/DEPLOY.md (pt-BR runbook: Arquitetura, Pré-requisitos, Backend no Render, Frontend na Vercel, CORS, Cron de catch-up, Cold-start, Gate de fumaça, Rollback, Checklist de go-live, Registro de verificação)
  - scripts/verify-deploy.ps1 (UTF-8 BOM, PS 5.1) — 10-check production smoke gate
  - README.md deploy link
affects: [phase-6-verification, launch checklist, future deploy/rollback decisions]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deploy artifacts carry ZERO secrets: sync:false in render.yaml, repo vars/secrets in GitHub, env vars in Vercel/Render"
    - "PowerShell 5.1 gate scripts saved UTF-8 with BOM (like frontend/scripts/verify-ssr.ps1)"
    - "CI cron calls the idempotent CRON_SECRET endpoint as catch-up for the in-process scheduler, never the admin JWT"

key-files:
  created:
    - render.yaml
    - .github/workflows/expire-cron.yml
    - frontend/vercel.json
    - docs/DEPLOY.md
    - scripts/verify-deploy.ps1
  modified:
    - README.md

key-decisions:
  - "Region do Render fixada em ohio com comentário para alinhar à região do Neon de produção (Neon → Settings → General → Region)"
  - "alembic upgrade head roda a CADA boot (redeploys e wake-ups do spin-down); migrações são forward-only — corrigir com nova migration, nunca editar histórico"
  - "SCHEDULER_ENABLED documentado como knob operacional (default true); endpoint CRON_SECRET é o catch-up no free tier que dorme"
  - "verify-deploy.ps1 usa HttpWebRequest com captura de WebException (4xx/5xx viram resposta normal; erros de rede abortam) — sem abortar em 4xx esperado"
  - "Cold-start nunca falha o gate: imprime INFO com latência e avisa (sem falhar) se > 15 s citando o timeout do frontend"

patterns-established:
  - "Smoke gate pattern: Assert/Invoke-Http/Write-Pass helpers, each check prints 'PASS - ...', gate ends with 'verify-deploy: all checks passed'"
  - "Docs runbook pattern: placeholders only (https://<backend>.onrender.com), never real values; verification table to be filled at the human checkpoint"

requirements-completed: []

# Metrics
duration: ~30min (Tasks 1–2 only; not machine-timed)
completed: 2026-11-02
---

# Phase 6 Plan 04: Deploy Pipeline & Go-Live Runbook Summary

**Deploy artifacts for produção: Render blueprint (uv, migrations on boot, health check, secrets only via dashboard), GitHub Actions 03:00 UTC catch-up cron, minimal Vercel config, pt-BR deploy runbook and a PS 5.1 `verify-deploy.ps1` production smoke gate — Task 3 (deploy real + human verification) is pending.**

## Performance

- **Duration:** ~30 min (Tasks 1–2)
- **Started:** 2026-11-02
- **Completed (Tasks 1–2):** 2026-11-02T23:56Z
- **Tasks:** 2 of 3 complete (**Task 3 pending human deploy — see below**)
- **Files modified:** 6 (5 created, 1 modified)

## Accomplishments

- `render.yaml` sobe o backend como UM serviço web (`rootDir: backend`, `runtime: python`, `plan: free`, `region: ohio`): build com `pip install uv && uv sync --frozen --no-dev` (sem `requirements.txt`), start com `uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health check em `/api/v1/health`. Segredos (`DATABASE_URL`, `ADMIN_PASSWORD_HASH`, `JWT_SECRET`, `CORS_ORIGINS`, `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`, `GROQ_API_KEY`, `CRON_SECRET`) com `sync: false` — **nenhum valor real no git**. `ENV=prod` ativa o validador fail-closed do Turnstile; comentário documenta o `alembic upgrade head` no boot.
- `.github/workflows/expire-cron.yml` (`expire-jobs`): gatilhos `schedule: cron '0 3 * * *'` (UTC) e `workflow_dispatch`; `concurrency` com `cancel-in-progress: false`; `timeout-minutes: 10`; step valida `vars.API_BASE_URL`/`secrets.CRON_SECRET` com mensagem clara se vazios e chama `curl --fail-with-body --retry 3 --retry-delay 15 --retry-all-errors --max-time 120 -X POST "${API_BASE_URL%/}/api/v1/admin/expire" -H "X-Cron-Secret: ${CRON_SECRET}"` — o secret nunca é ecoado.
- `frontend/vercel.json`: `{ "$schema": "https://openapi.vercel.sh/vercel.json", "framework": "nextjs" }` — Root Directory `frontend` fica documentado no runbook (é config de projeto, não de arquivo).
- `docs/DEPLOY.md` (pt-BR): Arquitetura → Pré-requisitos → Backend no Render → Frontend na Vercel → CORS → Cron de catch-up → Cold-start → Gate de fumaça → Rollback → Checklist de go-live → Registro de verificação (tabela data/URL/resultado a preencher no checkpoint humano). Contém `CORS_ORIGINS`, `cold-start`, `verify-deploy.ps1`, `Rollback`, `CRON_SECRET` — verificado. Só placeholders (`https://<backend>.onrender.com`), zero segredos.
- `scripts/verify-deploy.ps1`: UTF-8 **com BOM** (EF BB BF), compatível com PowerShell 5.1 (`#Requires -Version 5.1`), compila via `[scriptblock]::Create`. 10 checks: health (`env=prod`, `turnstile.mode=live`), CORS permitido (`Access-Control-Allow-Origin` == origem do front) e preflight negado (`https://evil.example` → 400 ou header ausente/diferente), board com `Vagas abertas` e **sem** `contact_email`/`contact_phone`/`mailto:`, `/privacidade` com `LGPD`/`intermedi`, contrato da API (`items`/`total`), cron sem segredo → 401/403, cron com segredo → 200 + `deleted` inteiro 2x (idempotência), não-vazamento do secret, e cold-start informativo (`INFO - latência do primeiro request: Ns`; avisa sem falhar se > 15 s). Final: `verify-deploy: all checks passed`.
- `README.md`: apenas um link curto para `docs/DEPLOY.md` sob `## Deploy` (nada mais reescrito).
- Task 1 verify: `render/workflow/docs/vercel ok`. Task 2 verify: `verify-deploy.ps1 parses and has all checks`.

## Task Commits

1. **Task 1: Criar artefatos de deploy (Render, cron, Vercel) e runbook** — `1f99010` (feat)
2. **Task 2: Criar script de verificação de deploy** — `7e3142e` (feat)
3. **Task 3: deploy real e verificação em produção** — **PENDENTE** (checkpoint humano, gate bloqueante — não executado)

**Plan metadata:** este commit (docs: 06-04 Tasks 1–2 summary)

## Files Created/Modified

- `render.yaml` *(new)* — blueprint do serviço web `nqu-backend`
- `.github/workflows/expire-cron.yml` *(new)* — cron diário 03:00 UTC + `workflow_dispatch`
- `frontend/vercel.json` *(new)* — config mínima Vercel/Next.js
- `docs/DEPLOY.md` *(new)* — runbook completo de deploy/rollback/go-live
- `scripts/verify-deploy.ps1` *(new)* — gate de fumaça pós-deploy (UTF-8 BOM)
- `README.md` *(modified)* — link para o runbook

## Decisions Made

- **Nenhum segredo versionado:** `render.yaml` usa apenas `sync: false`; GitHub usa `vars.API_BASE_URL` e `secrets.CRON_SECRET`; Vercel/Render recebem valores via dashboard. O gate confere que o secret não vaza no board/health/legal.
- **`alembic upgrade head` no boot:** migrações rodam a cada start (deploys e wake-ups); são forward-only — correção sempre com nova migration.
- **Rollback documentado por camada:** Render (deploy anterior), Vercel (Instant Rollback), Neon (sem rollback de schema — forward-only), CORS (corrige + redeploy, sem frontend).
- **Cold-start nunca quebra o gate:** é informativo; a recuperação é a copy "O servidor está acordando." + "Tentar novamente" de `error.tsx` dentro do timeout de 15 s de `lib/jobs.ts`.
- **`verify-deploy.ps1` 5.1-safe:** sem ternário/null-conditional/PS7-only; helpers `Assert`/`Invoke-Http`/`Write-Pass`; 4xx/5xx são respostas válidas, erros de rede/TLS abortam.
- **Task 3 fora do escopo deste executor:** deploy real exige contas/secrets interativos (Neon, Render, Vercel, GitHub) e verificação humana em produção; não foi executado nenhum passo de deploy, `git push`, chamada a APIs ou curl contra URLs reais.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] PowerShell mangled the plan's inline verify command**
- **Found during:** Task 1 verification
- **Issue:** The plan's `<automated>` one-liner uses bash-style nested single quotes inside a double-quoted `python -c` string; under Windows PowerShell the quotes are eaten and Python raises `SyntaxError: unterminated string literal`.
- **Fix:** The exact same assertion set was written to a temp Python file (`%TEMP%/opencode/verify-06-04-task1.py`) and executed with `backend\.venv\Scripts\python.exe`. All assertions from the plan passed (`render/workflow/docs/vercel ok`).
- **Files modified:** none in repo (temp file outside repo)
- **Verification:** `render/workflow/docs/vercel ok`

**2. [Rule 3 - Blocking] CRLF/BOM drift on Windows checkout**
- **Found during:** Task 2 commit
- **Issue:** `core.autocrlf=true` rewrote line endings; risk of losing the mandatory UTF-8 BOM.
- **Fix:** Blob bytes verified via `cmd /c "git show HEAD:scripts/verify-deploy.ps1 > file"` → `EF BB BF` (BOM intact, 12645 bytes — identical to working copy).
- **Files modified:** `scripts/verify-deploy.ps1` (working copy normalized with BOM)
- **Verification:** Task 2 verify command passes (BOM + assertion scan + `[scriptblock]::Create`).

---

**Total deviations:** 2 auto-fixed (both blocking, shell/OS-level; no repo content changes beyond the plan)
**Impact on plan:** None — same assertions as the plan's verify, executed in a PowerShell-safe way.

## Issues Encountered

- PowerShell does not accept `VAR=$(...)` bash syntax nor `grep`/`head`; commands were rewritten with PowerShell cmdlets or `workdir`.
- `>` redirection in PowerShell re-encodes to UTF-16 — avoided for byte-level blob inspection (used `cmd /c` redirection instead).
- `git status --short` shows pre-existing orchestrator modifications to `.planning/STATE.md` (not mine); STATE.md/ROADMAP.md were **not** modified or staged.

## User Setup Required (Task 3)

**Deploy real ainda NÃO executado — requer o operador humano.** Conforme `docs/DEPLOY.md` e o Task 3 do plano:

1. **Neon:** criar/confirmar projeto de produção (separado do dev/test); connection string **pooled** com `?ssl=require`; anotar região.
2. **Render:** New → Blueprint → selecionar o repositório; aplicar `render.yaml`; preencher `DATABASE_URL`, `ADMIN_PASSWORD_HASH`, `JWT_SECRET`, `CORS_ORIGINS` (inicial), `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`, `GROQ_API_KEY`, `CRON_SECRET` (32+ chars). Confirmar no boot: `alembic upgrade head` OK e `https://<backend>.onrender.com/api/v1/health` → `status=ok`, `env=prod`, `turnstile.mode=live`.
3. **Vercel:** importar repo; **Root Directory = `frontend`**; `BACKEND_API_URL`, `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`; deploy; anotar o domínio de produção.
4. **Render → CORS:** trocar `CORS_ORIGINS` para exatamente o domínio da Vercel (sem barra final); redeploy; abrir board e confirmar ausência de erro de CORS.
5. **GitHub:** criar `vars.API_BASE_URL` (Render, sem barra final) e `secrets.CRON_SECRET` (mesmo valor do Render); rodar `expire-jobs` via **Run workflow**; conferir log sem o secret e resposta `{"deleted": N, "status": "ok"}`.
6. **Gate:** `powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 -FrontendUrl https://<frontend> -BackendUrl https://<backend> -CronSecret <secret>` — exigir todas as linhas `PASS` e `verify-deploy: all checks passed`.
7. **Cold-start:** deixar ocioso ~20 min; abrir o board no celular (390 px); se dormir, a UI deve mostrar **"O servidor está acordando."** e **"Tentar novamente"**; anotar o tempo real na tabela **Registro de verificação** de `docs/DEPLOY.md`.
8. **Fluxo real:** buscar vaga → abrir modal → revelar contato (Turnstile real) → reportar vaga → `/privacidade`; confirmar HTML sem `contact_email`/`contact_phone`/`mailto:`.
9. **Admin:** `/admin/login`, `/admin/paste` e fila de review funcionando.
10. **Segredos:** `git status --porcelain` sem `.env`/`.env.local`; nenhum secret em logs do Render/Vercel/Actions.

Registrar URLs e tempos de cold-start na seção **Registro de verificação** de `docs/DEPLOY.md` antes de declarar go-live.

## Known Stubs

- **`docs/DEPLOY.md` → Registro de verificação:** tabela intencionalmente vazia ("_pendente_") — deve ser preenchida no checkpoint humano com URLs/tempos reais; não inventar valores.
- Nenhuma stub de código: todos os artefatos de deploy estão completos e verificados estaticamente.

## Threat Flags

Nenhuma nova superfície fora do `<threat_model>` do plano — os artefatos implementam as mitigações registradas (T-06-04-01 cron secret, T-06-04-02 sync:false/sem segredos, T-06-04-03 CORS exato, T-06-04-05 ENV=prod/turnstile live). O endpoint destrutivo continua protegido por `X-Cron-Secret` (503/401 fail-closed) e o gate prova 401/403/200.

## Self-Check: PASSED

- Created files exist: `render.yaml` ✓, `.github/workflows/expire-cron.yml` ✓, `frontend/vercel.json` ✓, `docs/DEPLOY.md` ✓, `scripts/verify-deploy.ps1` ✓
- Task 1 verify: `render/workflow/docs/vercel ok` ✓
- Task 2 verify: `verify-deploy.ps1 parses and has all checks` + BOM `EF BB BF` ✓
- Commits exist: `1f99010` ✓, `7e3142e` ✓ (blob BOM verificado via `cmd /c git show`)
- No modifications to `.planning/STATE.md` ou `.planning/ROADMAP.md` ✓
- No real secrets in any created file (placeholders only) ✓
- Task 3 (human deploy) NOT executed — by design ✓

---
*Phase: 06-lifecycle-trust-legal-launch*
*Completed (Tasks 1–2): 2026-11-02 — Task 3 pending*
