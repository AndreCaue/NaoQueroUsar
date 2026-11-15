# Phase 13: Canonical Host, Deploy & Ops Alignment (BRND-04 closeout) - Pattern Map

**Mapped:** 2026-11-15
**Files analyzed:** 9 (docs/config/scripts/planning alignment; no runtime code per D-06)
**Analogs found:** 9 / 9 (operational/config/documentation/traceability patterns)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog (pattern source) | Match Quality |
|-------------------|------|-----------|----------------------------------|---------------|
| `docs/DEPLOY.md` | ops-runbook/doc | declarative config + evidence traceability | Self: "Arquitetura/Pré-requisitos/Cron", **Registro de verificação** table, desvio/handoff notes (e.g. Turnstile desvio temporário, critério 6 human-gated) | exact (self/section analog) |
| `scripts/verify-deploy.ps1` | verification-script | parameterized smoke checks (request/response gate) | Self: param block + header `.SYNOPSIS/.DESCRIPTION/.EXAMPLE` + `Assert/Invoke-Http` helpers + check sections 1–10 | exact (self) |
| `render.yaml` | deploy-config (blueprint) | declarative env/service config | Self: header comments (operational notes) + `envVars` `sync:false` secret declarations | exact (self) |
| `frontend/.env.example` | env-example/doc | declarative env guidance (build-time vs runtime) | Self: comment blocks separating local/dev vs produção and "OBRIGATÓRIA em produção" semantics | exact (self) |
| `frontend/.env.local.example` | env-example/doc (local) | declarative local dev guidance | `frontend/.env.example` comment/value style (localhost defaults, non-secret public key note) | role-match |
| `frontend/vercel.json` | deploy-config (minimal) | declarative framework hint | Self: minimal schema+framework; `docs/DEPLOY.md` states "configuração de projeto no dashboard — não está no vercel.json de propósito" | exact (self; likely no canonical host value to inject) |
| `.github/workflows/expire-cron.yml` | ops-workflow/config | scheduled HTTP trigger (idempotent catch-up) | Self: `env` vars/secrets usage + fail-fast validation + placeholder help text (`https://<backend>.onrender.com`) | exact (self) |
| `.planning/REQUIREMENTS.md` | planning-traceability | requirement state + evidence/ownership mapping | Self: Phase 11/12 gap-closure note style (inline evidence refs, caveats, split ownership "owned by Phase 13") | exact (self) |
| `.planning/ROADMAP.md` | planning-traceability | phase status/criteria/ownership | Self: Phase 11/12/13 entries (goal/depends/requirements/gap closure/success criteria) + Progress table/status notes | exact (self) |

## Pattern Assignments

### `docs/DEPLOY.md` (ops-runbook/doc, declarative config + evidence traceability)

**Analog:** `docs/DEPLOY.md` (self; preserve history per D-08)

**Document header / scope-of-truth pattern** (lines 1-7):
```md
# Deploy — EmpregaNoix

Runbook de produção: frontend na **Vercel**, backend **FastAPI** no **Render**, banco **Neon (Postgres)** e **GitHub Actions** como cron de catch-up da expiração.

> **Nenhum segredo real entra neste arquivo ou em qualquer arquivo versionado.** Todos os valores sensíveis são configurados apenas em variáveis de ambiente (Render/Vercel/GitHub). Onde este documento mostra `https://<backend>.onrender.com`, substitua pelos endereços reais do seu deploy.
```

**Architecture / canonical-seams context to keep consistent** (lines 9-31, excerpt):
```md
Navegador ──HTTPS──► Vercel (Next.js 16 App Router, SSR + server fetch)
                         │ cache: "no-store" com timeout de 15 s (frontend/lib/jobs.ts)
                         ▼
                 Render (FastAPI, plano free)
...
1. **Primário** — APScheduler in-process ...
2. **Catch-up** — GitHub Actions chamando `POST /api/v1/admin/expire` com `X-Cron-Secret`. Idempotente ...
```

**Runbook section / env-table pattern** (lines 60-86, excerpt):
```md
   | Variável               | Valor / origem ... | Notas ... |
   | ---------------------- | ------------------ | --------- |
   | `ENV`                  | `prod` (já no blueprint) | ... |
   | `DATABASE_URL`         | Neon → ... `postgresql+asyncpg://` ... `?ssl=require` | ... |
   | `CORS_ORIGINS`         | Origem exata da Vercel (ex.: `https://<seu-projeto>.vercel.app`) | Sem barra final, sem `*`, sem espaços |
   | `TURNSTILE_SITE_KEY`   | Site key do widget de produção | ... |
   | `ALLOW_TEST_TURNSTILE` | ausente (padrão `false`) | **Desvio temporário.** ... |
```

**Historical evidence / registro table pattern — MUST PRESERVE VERBATIM ROWS** (lines 300-324, excerpt):
```md
## Registro de verificação

> Preencher **no checkpoint humano** ... Não inventar valores: se um passo falhou, registrar o que foi observado.

| Data (UTC) | Etapa ... | URL / comando ... | Resultado observado ... | Cold-start | Notas ... |
| ---------- | --------- | ----------------- | ---------------------- | ---------- | --------- |
| 2026-11-12 | Render — `/api/v1/health` | `https://empreganoix.onrender.com/api/v1/health` | 200 ... **`env=dev`**, **`turnstile.mode=test`** | — | **FALHA** ... |
| 2026-11-14 | Deploy produção (10-04 Task 2, checkpoint aprovado) | Frontend `https://empreganoix-six.vercel.app`, Backend `https://nqu-backend-x60n.onrender.com` | **Aprovado pelo usuário** ... | 0.2s | Hosts reais diferem ... serviço Render permanece `nqu-backend` ... |
| 2026-11-15 | Smoke gate produção (09-04 Task 3, critério 6) | Frontend `https://empreganoix-six.vercel.app` · Backend `https://nqu-backend-x60n.onrender.com` | **PASS — `verify-deploy: all checks passed`** ... | 0.2s | Evidência humana aprovada ... |
| _pendente_ | Cold-start após ~20 min ocioso | | | | tempo real + comportamento da UI |
```

**Deviation/handoff/risk documentation pattern** (lines 99-127, 215-224 excerpts):
```md
## Desvio temporário: Turnstile de teste em produção
> **Estado:** ativo desde 2026-11-12 (operador ainda sem domínio próprio). Remover assim que houver um widget live.
... Comportamento quando o flag está ligado: ... **Riscos aceitos neste desvio:** ...
**Para sair do desvio:** (1) Hostnames ... (2) chaves live ... (3) Render env + Manual Deploy (4) Vercel env + Redeploy (5) Re-rodar gate sem `-AllowTestTurnstile` ...

### Critério 6 (human-gated) — evidência de produção obrigatória
> **Critério 6 é human-gated.** ... só é considerado fechado após um deploy real executado por operador e um `scripts/verify-deploy.ps1` aprovado com evidência registrada.
Evidência mínima exigida ... Health/CORS preflight/cron/Registro ...
```

**Apply/copy:** Add (without rewriting historical rows) a canonical state-alvo section (D-01,D-03,D-07), canonical↔legacy host mapping (D-02,D-14), and D-10 alignment matrix with statuses `verificado em host legado | alinhado contratualmente ao canônico | pendente de execução operacional` referencing existing registro rows; normalize target/examples/commands to canonical hosts while keeping legacy examples only as clearly labeled historical reproduction where useful (D-08, discretion). Include D-13 sequence and D-15 risks/handoff language consistent with existing deviation/critério-6 style.

---

### `scripts/verify-deploy.ps1` (verification-script, parameterized smoke checks)

**Analog:** `scripts/verify-deploy.ps1` (self)

**Header/help and parameterization pattern** (lines 1-49, excerpt):
```powershell
#Requires -Version 5.1
<#
.SYNOPSIS
  Gate de fumaça pós-deploy (produção) do EmpregaNoix.

.DESCRIPTION
  Valida o deploy de produção de ponta a ponta:
    1.  GET  /api/v1/health            -> 200, status=ok, env=prod, turnstile.mode=live
                                          (-AllowTestTurnstile aceita mode=test somente
                                           com turnstile.test_override=true)
    ...
    10. Cold-start (informativo)       -> usa a latência do PRIMEIRO request (health) ...

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 `
    -FrontendUrl https://<seu-projeto>.vercel.app `
    -BackendUrl  https://<backend>.onrender.com `
    -CronSecret  <CRON_SECRET>
#>
param(
    [Parameter(Mandatory = $true)][string]$FrontendUrl,
    [Parameter(Mandatory = $true)][string]$BackendUrl,
    # ... lê $env:CRON_SECRET por padrão ...
    [string]$CronSecret = $env:CRON_SECRET,
    # DESVIO TEMPORARIO ...
    [switch]$AllowTestTurnstile
)
```

**Canonicalization seam:** ` $FrontendUrl = $FrontendUrl.TrimEnd('/') ; $BackendUrl = $BackendUrl.TrimEnd('/')` (lines 57-58) and `Write-Pass/Assert/Invoke-Http` helpers — **preserve behavior/parameters** (D-06, no runtime logic change beyond strictly necessary docs/examples if any). Update `.SYNOPSIS/.DESCRIPTION/.EXAMPLE` comments to present canonical branded hosts as primary state-alvo while keeping script usable for legacy hosts (discretion, D-05/D-08): e.g. show `https://empreganoix.vercel.app` / `https://empreganoix.onrender.com` as main example and optionally note legacy hosts only for reproducing historical evidence.

---

### `render.yaml` (deploy-config, declarative env/service config)

**Analog:** `render.yaml` (self)

**Header comment / operational intent + secrets posture** (lines 1-35, excerpt):
```yaml
# Blueprint do backend EmpregaNoix no Render (free tier).
#
# ... ENV=prod ativa validador fail-closed ...
# - ALLOW_TEST_TURNSTILE=true e um ESCAPE HATCH TEMPORARIO ...
# - Deploys são MANUAIS (autoDeploy: false): ...
# - `alembic upgrade head` roda a CADA boot ... forward-only ...
# - `region: ohio` deve ser alinhada à região do projeto Neon de produção ...
# - Todos os segredos ficam com `sync: false`: o valor é definido SOMENTE no
#   dashboard ... — nunca neste arquivo.
services:
  - type: web
    name: nqu-backend
    ...
    autoDeploy: false
    healthCheckPath: /api/v1/health
```

**Env declaration pattern (secret-free, value only in dashboard)** (lines 49-76, excerpt):
```yaml
    envVars:
      - key: ENV
        value: prod
      ...
      # ---- Segredos / configuração sensível: valor SÓ no dashboard ----
      - key: DATABASE_URL # Neon pooled connection string + ?ssl=require
        sync: false
      - key: CORS_ORIGINS # origem exata da Vercel, sem barra final, sem *
        sync: false
      - key: CRON_SECRET # 32+ caracteres; o mesmo valor vai em GitHub secrets.CRON_SECRET
        sync: false
```

**Apply/copy:** Keep `name: nqu-backend` and internal identifiers (deferred). If adjusting comments for canonical alignment, reflect state-alvo origin semantics (single canonical frontend origin, no wildcard/trailing slash) without adding real values/hosts as secrets and without changing runtime behavior/keys structure except where strictly declarative guidance applies (D-05/D-06/D-07).

---

### `frontend/.env.example` (env-example/doc, declarative env guidance)

**Analog:** `frontend/.env.example` (self)

**Guidance/comment structure (local vs produção, build-time warning)** (lines 1-22):
```dotenv
# Frontend — variáveis de ambiente (EmpregaNoix)
#
# Copie para `.env.local` e ajuste. NUNCA comite `.env.local` nem valores
# reais de produção. Nenhum `NEXT_PUBLIC_*` pode conter segredos ...
#
# Produção (Vercel): configure estas vars no dashboard (Production scope).
# Desde WR-04, `next build` FALHA se NEXT_PUBLIC_API_URL estiver ausente —
# não existe mais fallback para localhost em build de produção.

# URL pública do backend FastAPI (ex.: https://<backend>.onrender.com).
# Usada no browser para login/reveal/report/admin. OBRIGATÓRIA em produção.
NEXT_PUBLIC_API_URL=http://localhost:8000

# URL do backend usada apenas no SSR ... Lida em RUNTIME no servidor ...
# em produção aponta para a mesma URL pública do backend. Opcional em dev (cai para a pública).
BACKEND_API_URL=http://localhost:8000

# Site key pública do widget Cloudflare Turnstile (widget de produção).
# Em dev, se ausente, usa a chave pública always-pass do Cloudflare.
NEXT_PUBLIC_TURNSTILE_SITE_KEY=
```

**Apply/copy:** Normalize production/state-alvo guidance to canonical `https://empreganoix.onrender.com` and call out canonical frontend origin `https://empreganoix.vercel.app` / Turnstile Hostname context where helpful, while keeping localhost defaults runnable for local dev and adding no secrets (D-03/D-07/D-08, A3). Clearly label "Estado-alvo produção (canônico)" vs local.

---

### `frontend/.env.local.example` (env-example/doc local, declarative local dev guidance)

**Analog:** `frontend/.env.example` (role-match)

**Existing pattern** (lines 1-5):
```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
# Public Turnstile site key (safe to expose in the browser).
# Empty in dev = use the Cloudflare always-pass test key; mandatory in production.
NEXT_PUBLIC_TURNSTILE_SITE_KEY=
# .env.local is gitignored and must not be committed
```

**Apply/copy:** Only adjust if needed for consistency with canonical state-alvo guidance (discretion, D-05). Keep local-dev-safe, no secrets, no `.env.local` edits.

---

### `frontend/vercel.json` (deploy-config minimal, declarative framework hint)

**Analog:** `frontend/vercel.json` (self) + `docs/DEPLOY.md` note

**Existing pattern** (lines 1-4):
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "nextjs"
}
```
**Runbook context (docs/DEPLOY.md ~line 132):** `frontend/vercel.json` só fixa `framework: "nextjs"` e o `$schema`; Root Directory/domínios/envs são configuração de projeto no dashboard. **Apply:** likely no host literal to change; confirm "conforme aplicável" (D-05). If untouched, canonical host alignment is documented in DEPLOY/matrix as Vercel project/domain setting.

---

### `.github/workflows/expire-cron.yml` (ops-workflow/config, scheduled HTTP trigger)

**Analog:** `.github/workflows/expire-cron.yml` (self)

**Contract/help text and secret-safe invocation pattern** (lines 26-50, excerpt):
```yaml
      - name: Chamar POST /api/v1/admin/expire
        env:
          API_BASE_URL: ${{ vars.API_BASE_URL }}
          CRON_SECRET: ${{ secrets.CRON_SECRET }}
        run: |
          set -euo pipefail
          if [ -z "${API_BASE_URL:-}" ]; then
            echo "::error::vars.API_BASE_URL não está configurada. Configure em Settings → Secrets and variables → Actions → Variables (ex.: https://<backend>.onrender.com, sem barra final)."
            exit 1
          fi
          ...
          curl --fail-with-body --silent --show-error \
            --retry 3 --retry-delay 15 --retry-connrefused --max-time 120 \
            -X POST "${API_BASE_URL%/}/api/v1/admin/expire" \
            -H "X-Cron-Secret: ${CRON_SECRET}"
          echo
          echo "expire-jobs: chamada concluída (resposta 200 com {\"deleted\": N, \"status\": \"ok\"})"
```

**Apply/copy:** Preserve contract (`X-Cron-Secret`, endpoint path, idempotent semantics, no secret echo). If editing examples/help text, keep non-secret and coherent with canonical state-alvo guidance (`vars.API_BASE_URL` = `https://empreganoix.onrender.com` in runbook/matrix) without hardcoding secrets (discretion, D-03/D-11).

---

### `.planning/REQUIREMENTS.md` (planning-traceability, requirement state + evidence/ownership)

**Analog:** `.planning/REQUIREMENTS.md` (self)

**Gap-closure inline evidence / caveat / split-ownership note pattern** (examples):
```md
- [x] **ADMN-10**: ... *(Phase 11 gap closure: verificado em `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md` — evidência de código/widget + nota de verificação humana/browser; caveats/ambiente documentados)*
...
- [x] **SECR-12**: ... *(Phase 12 reconciliation — split ownership: lado Phase 7 verificado em ...; lado Phase 9 (... X-Cron-Secret-only, fail-closed ..., T-06-01) verificado em ...; evidência residual de host canônico/deploy é owned by **Phase 13** (BRND-04). No full closure beyond reconciled code/contract evidence claimed here.)*
...
- [x] **LIFE-13**: ... *(Phase 12 reconciliation — split ownership: lado code/contract (... T-06-01 ...) verificado em ...; evidência residual de host canônico/deploy é owned by **Phase 13** (BRND-04), que mantém LIFE-13 em sua lista de requisitos.)*
- [ ] **BRND-04**: ... *(gap closure: Phase 13 — canonical host/env/CORS/API alignment & evidence)*
```
**Summary/gap-closure section pattern** (lines 74-89): lists Phase 11/12/13 ownership and requirement sets.

**Apply/copy:** Update checkboxes/notes for **BRND-04, SECR-12, LIFE-13** per D-12/D-16: mark closed with explicit ops-scope note pointing to Phase 13 matrix/evidence in `docs/DEPLOY.md` (and canonical mapping), preserve prior verification history (Phases 7/9/12), keep split ownership/caveat clarity and do not reopen T-06-01. Update last-updated line accordingly.

---

### `.planning/ROADMAP.md` (planning-traceability, phase status/criteria/ownership)

**Analog:** `.planning/ROADMAP.md` (self)

**Phase entry and progress pattern** (examples, lines 33-36, 162-191):
```md
**Phase 13: Canonical Host, Deploy & Ops Alignment (BRND-04 closeout)** — Resolve branded-host/env/CORS/API drift and record aligned deploy evidence (audit gap closure)
...
### Phase 13: Canonical Host, Deploy & Ops Alignment (BRND-04 closeout)
**Goal:** ...
**Depends on:** Phase 10 ... and `.planning/v1.1-MILESTONE-AUDIT.md`
**Requirements:** BRND-04, SECR-12, LIFE-13
**Gap Closure:** Closes audit gaps for canonical host mismatch ...
**Success Criteria** (what must be TRUE): 1-4 ...
...
| 13. Canonical Host, Deploy & Ops Alignment (BRND-04 closeout) | 0/TBD | Not started | - |
```

**Apply/copy:** Update Phase 13 status/plan count/notes and progress table to reflect completion state and evidence/ownership per D-11/D-16, referencing `docs/DEPLOY.md` canonical matrix/mapping and noting any handoff (D-04/D-14/D-15) without altering historical phase records.

## Shared Patterns

### 1) Canonical state-alvo (strict, single-origin) — D-01, D-03, D-07
**Apply to:** `docs/DEPLOY.md`, `scripts/verify-deploy.ps1` (examples), `render.yaml` (comments/guidance if touched), `frontend/.env.example`, `frontend/.env.local.example` (if needed), `.github/workflows/expire-cron.yml` (guidance if touched), planning notes.
```text
Frontend (origem canônica): https://empreganoix.vercel.app
Backend  (API canônica):    https://empreganoix.onrender.com

CORS_ORIGINS=https://empreganoix.vercel.app   # exato, sem barra final, sem wildcard, sem legados
NEXT_PUBLIC_API_URL=https://empreganoix.onrender.com
BACKEND_API_URL=https://empreganoix.onrender.com
Turnstile Hostnames: empreganoix.vercel.app (widget de produção)
GitHub Actions vars.API_BASE_URL=https://empreganoix.onrender.com
verify-deploy: -FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com
Cron endpoint canônico: https://empreganoix.onrender.com/api/v1/admin/expire (X-Cron-Secret-only, fail-closed; T-06-01 preservado)
```
**Source basis:** `13-CONTEXT.md` D-01/D-03/D-07/D-13, `13-RESEARCH.md` §Pattern 2, `docs/DEPLOY.md` env/CORS/cron semantics.

### 2) Preserve historical evidence; add mapping/matrix — D-02, D-08, D-09, D-10
**Apply to:** `docs/DEPLOY.md` (and references in REQUIREMENTS/ROADMAP).
```md
<!-- Do NOT rewrite dated rows in Registro de verificação -->
| Host canônico (alvo) | Host legado/histórico | Papel | Notas/evidência |
|---|---|---|---|
| https://empreganoix.vercel.app | https://empreganoix-six.vercel.app, https://nao-quero-usar.vercel.app | frontend/origem CORS | preservar evidências 2026-11-12/14/15; mapear interpretação |

| Check (D-10) | Alvo canônico | Host verificado (evidência) | Status | Evidência / nota |
|---|---|---|---|---|
| GET /api/v1/health (status/env/Turnstile) | https://empreganoix.onrender.com/api/v1/health | legado (ex.: nqu-backend-x60n.onrender.com, 2026-11-15) | verificado em host legado; alinhado contratualmente ao canônico / pendente de execução operacional | ref Registro ... |
| Preflight CORS origem canônica | Origin: https://empreganoix.vercel.app | legado | ... | allow/deny conforme gate |
| POST /admin/expire (401/403/503 sem/errado, 200 idempotente x2 com X-Cron-Secret) | https://empreganoix.onrender.com/api/v1/admin/expire | legado | ... | fail-closed, sem reabrir T-06-01 |
| Superfícies públicas/admin chave (board, /privacidade, /termos-de-uso, login/admin) | https://empreganoix.vercel.app ... | legado | ... | ... |
```
**Status vocabulary (required):** `verificado em host legado`, `alinhado contratualmente ao canônico`, `pendente de execução operacional`. **Source:** `docs/DEPLOY.md` Registro table pattern, `13-RESEARCH.md` §Pattern 1, D-09/D-10.

### 3) Handoff operacional, riscos e bloqueio de provisionamento — D-04, D-12, D-13, D-14, D-15
**Apply to:** `docs/DEPLOY.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`.
```md
- Fechamento contratual/documental permitido com evidência mapeada quando canônicos não provisionados/publicados; execução real em canônicos = handoff operacional explícito (não bloqueia D-04).
- SECR-12/LIFE-13: código/contrato já verificados (Phases 7/9/12); resíduo ops/canônico coberto/mapeado aqui; **não reabrir T-06-01**.
- Sequência segura (D-13): (1) provisionar/alinhar hosts canônicos (2) envs/CORS/Turnstile Hostnames/segredos cron (3) rebuild/redeploy frontend (`NEXT_PUBLIC_*` inlined) (4) validar health/CORS/cron/superfícies via `scripts/verify-deploy.ps1` (5) registrar evidência — rollback por reversão env/config/domínio.
- Se nome canônico indisponível: manter alvo contratual `empreganoix.vercel.app` / `empreganoix.onrender.com`, registrar host real como desvio/bloqueio com mapeamento (não trocar canônico silenciosamente) (D-14).
- Riscos: execução pode ficar pendente, rebuild obrigatório, Turnstile Hostnames e CORS devem coincidir com origem real, cron/segredos corretos, cold-start/scheduler split conhecidos (D-15).
```

### 4) Secret-free, no runtime behavior change — D-05, D-06
**Apply to:** all in-scope edits. `render.yaml`/env examples use placeholders or localhost; `sync:false` and dashboard-only secrets; do not alter `backend/app/**` or `frontend/lib/**`; keep `verify-deploy.ps1` logic intact except unavoidable non-behavioral text if needed.

## No Analog Found

Files with no close *external* analog in the codebase (treat file itself as canonical pattern; planner should follow RESEARCH.md + existing section styles above):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `docs/DEPLOY.md` (new canonical/matrix sections) | ops-runbook/doc | evidence traceability | No prior "alvo canônico ↔ legado" matrix section exists; compose from Registro table + deviation/handoff patterns already in file. |
| `frontend/vercel.json` (canonical host field) | deploy-config | declarative | No host/domain entries today; canonical host is likely dashboard-level (document, don't invent schema). |
| `.planning/ROADMAP.md` (Phase 13 completed-state note) | planning-traceability | status/ownership | Current entry is "Not started/0-TBD"; follow existing Phase 11/12 completion-note style as nearest shape. |

## Metadata

**Analog search scope:** `.planning/phases/13-canonical-host-deploy-ops-alignment/*`, `docs/DEPLOY.md`, `render.yaml`, `frontend/{vercel.json,.env.example,.env.local.example}`, `scripts/verify-deploy.ps1`, `.github/workflows/expire-cron.yml`, `.planning/{REQUIREMENTS.md,ROADMAP.md}` (read-only)
**Files scanned:** 13 (3 phase docs + 10 in-scope/reference artifacts)
**Pattern extraction date:** 2026-11-15
