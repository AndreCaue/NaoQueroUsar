---
phase: 13-canonical-host-deploy-ops-alignment
verified: 2026-11-15T16:30:00Z
status: passed
score: 10/10 must-haves verified
overrides_applied: 0
---

# Phase 13: Canonical Host, Deploy & Ops Alignment (BRND-04 closeout) — Verification Report

**Phase Goal:** Eliminate canonical branded-host and deploy configuration drift so production operations, CORS, and evidence match the intended EmpregaNoix contract.
**Verified:** 2026-11-15T16:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Scope / Evidence Boundary (explicit)

- **Verified in repo artifacts (this report):** `docs/DEPLOY.md`, `scripts/verify-deploy.ps1`, `frontend/.env.example`, `frontend/.env.local.example`, `.github/workflows/expire-cron.yml`, `render.yaml`, `frontend/vercel.json`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, phase PLAN/SUMMARY/CONTEXT/RESEARCH/REVIEW artifacts, and git history for task/plan commits.
- **Operational handoff (not claimed as executed in this phase):** live provisioning/deploy/rebuild/smoke execution on the canonical branded hosts `https://empreganoix.vercel.app` and `https://empreganoix.onrender.com`. Per D-04/D-14 and ROADMAP SC2, absence of live canonical-host execution is recorded/mapped as `pendente de execução operacional` with explicit handoff; this does **not** reopen T-06-01 and is **not** a hidden canonical swap.
- **Not reopened:** T-06-01 (`/admin/expire` accepts only `X-Cron-Secret`, fail-closed/idempotent) and prior Phase 7/9/12 code/contract verification history remain intact.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Canonical production contract is explicit state-alvo (`https://empreganoix.vercel.app` frontend/origin, `https://empreganoix.onrender.com` backend/API) and legacy hosts are mapped as historical/non-canonical (D-01..D-03, D-07, D-08). | ✓ VERIFIED | `docs/DEPLOY.md` `## Alvo canônico (state-alvo)` declares both hosts and exact env/ops targets (`CORS_ORIGINS=https://empreganoix.vercel.app`, `NEXT_PUBLIC_API_URL=https://empreganoix.onrender.com`, `BACKEND_API_URL=https://empreganoix.onrender.com`, Turnstile Hostnames `empreganoix.vercel.app`, `vars.API_BASE_URL=https://empreganoix.onrender.com`, cron `https://empreganoix.onrender.com/api/v1/admin/expire`, `X-Cron-Secret`, T-06-01). `## Mapeamento canônico ↔ legado/histórico` maps `empreganoix-six.vercel.app`/`nao-quero-usar.vercel.app` and `nqu-backend-x60n.onrender.com`/`naoquerousar.onrender.com` as non-canonical with no silent swap language. |
| 2 | `docs/DEPLOY.md` contains canonical↔legacy mapping and a D-10 alignment matrix with required statuses covering health/env/Turnstile, CORS preflight, cron `/admin/expire` fail-closed/idempotency, and key public/admin surfaces (D-09, D-10, D-11). | ✓ VERIFIED | `## Matriz de alinhamento (D-10)` present with status vocabulary `verificado em host legado`, `alinhado contratualmente ao canônico`, `pendente de execução operacional`. Rows cover `GET /api/v1/health` (env/Turnstile), Preflight CORS/`Access-Control-Allow-Origin`, `POST /api/v1/admin/expire` (rejeição sem/errada credencial fail-closed + idempotência 200+`deleted` 2x, `X-Cron-Secret`, T-06-01 preservado), board `/`, `/privacidade`, `/termos-de-uso`, and login/admin `/admin` (marked `pendente de execução operacional` with handoff). References cite Registro rows and `scripts/verify-deploy.ps1` checks. |
| 3 | Historical `## Registro de verificação` rows remain intact/unrewritten, including 2026-11-12, 2026-11-14, and 2026-11-15 entries and pending rows (D-02, D-08). | ✓ VERIFIED | `docs/DEPLOY.md` still contains `| 2026-11-12 | Render — \`/api/v1/health\` | ... https://empreganoix.onrender.com ...`, `| 2026-11-14 | Deploy produção (10-04 Task 2, checkpoint aprovado) | Frontend https://empreganoix-six.vercel.app, Backend https://nqu-backend-x60n.onrender.com | ...`, `| 2026-11-15 | Smoke gate produção (09-04 Task 3, critério 6) | ... https://empreganoix-six.vercel.app ... https://nqu-backend-x60n.onrender.com ... | **PASS — \`verify-deploy: all checks passed\`** ...`, and `_pendente_` rows. Historical host/evidence values preserved. |
| 4 | No runtime behavior code changed; edits limited to docs/config/examples/scripts/planning-support artifacts and contain no secrets (D-05, D-06). | ✓ VERIFIED | Git commits for phase work (`11b74b6`, `a3341ac`, `ba2bed8`, `09b69ec`, `5f14022`) modified only: `docs/DEPLOY.md`, `scripts/verify-deploy.ps1`, `frontend/.env.example`, `frontend/.env.local.example`, `.github/workflows/expire-cron.yml`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, and phase artifacts. No files under `backend/app/`, `frontend/lib/`, or `frontend/app/` modified. `render.yaml`/`frontend/vercel.json` remain valid/secret-free (`sync: false`, `autoDeploy: false`, `"framework": "nextjs"`). Env examples keep localhost defaults and placeholder/empty Turnstile guidance (no real secrets). |
| 5 | Smoke-gate/examples and env/deploy/workflow guidance reflect canonical branded targets as primary state-alvo while preserving parameterization/local defaults/secret-free config (D-03, D-05, D-07). | ✓ VERIFIED | `scripts/verify-deploy.ps1` keeps executable gate structure (`param(`, `$FrontendUrl`/`$BackendUrl`, `function Invoke-Http`) and documents canonical example `https://empreganoix.vercel.app` / `https://empreganoix.onrender.com` plus legacy reproducibility note (`empreganoix-six.vercel.app` / `nqu-backend-x60n.onrender.com`). `frontend/.env.example` retains `NEXT_PUBLIC_API_URL=http://localhost:8000`, `BACKEND_API_URL=http://localhost:8000` and adds canonical production guidance for `https://empreganoix.onrender.com` / `https://empreganoix.vercel.app` + rebuild note. `frontend/.env.local.example` retains localhost defaults. `.github/workflows/expire-cron.yml` preserves `vars.API_BASE_URL`, `secrets.CRON_SECRET`, `X-Cron-Secret`, `POST "${API_BASE_URL%/}/api/v1/admin/expire"` and includes canonical backend guidance (`https://empreganoix.onrender.com`). |
| 6 | Residual ops evidence for SECR-12/LIFE-13 is mapped to canonical contract with explicit handoff/risk notes and without reopening T-06-01 (D-04, D-12, D-13, D-14, D-15). | ✓ VERIFIED | `docs/DEPLOY.md` matrix maps cron fail-closed/idempotency to canonical endpoint with `X-Cron-Secret` and states **T-06-01 preservado**; adds `## Handoff operacional, riscos e rollback` with safe sequence (provisionar canônicos → envs/CORS/Turnstile/segredos → rebuild/redeploy `NEXT_PUBLIC_*` → validar com `scripts/verify-deploy.ps1` → registrar evidência), rollback por reversão de env/config/domínio, and risks (pendente/dev-local, Turnstile Hostnames/CORS alinhados, cron/scheduler dependências, cold-start/scheduler split). REQUIREMENTS/ROADMAP notes preserve prior code/contract verification history and record ops-scope closure/mapping with handoff where live canonical execution pending. |
| 7 | BRND-04, SECR-12, and LIFE-13 are marked complete in `REQUIREMENTS.md` with Phase 13 ops-scope/canonical-alignment evidence notes, preserved history, and explicit handoff where applicable (D-12, D-16). | ✓ VERIFIED | `.planning/REQUIREMENTS.md` contains `- [x] **BRND-04**`, `- [x] **SECR-12**`, `- [x] **LIFE-13**`, all citing `docs/DEPLOY.md` and `Phase 13` with canonical targets `https://empreganoix.vercel.app` / `https://empreganoix.onrender.com`. SECR-12/LIFE-13 retain T-06-01 and `X-Cron-Secret` contract/history and state "execução real em hosts canônicos pendente / handoff operacional documentado quando aplicável" (no reopen, no target swap). Gap-closure summary and `Last updated` reflect Phase 13 ops-scope alignment. |
| 8 | ROADMAP Phase 13 reflects closure/alignment state with references to canonical target, legacy mapping, D-10 matrix/evidence in `docs/DEPLOY.md`, and consistent progress/status metadata (D-11, D-16). | ✓ VERIFIED | `.planning/ROADMAP.md` Phase 13 section lists `13-01-PLAN.md`/`13-02-PLAN.md`, references `docs/DEPLOY.md`, canonical hosts, D-10/mapping/handoff, states "Nenhuma mudança de runtime/comportamento..." and "Contrato **T-06-01** preservado", and explicitly records live canonical-host execution as `handoff operacional / pending execution`. Progress row: `| 13. Canonical Host, Deploy & Ops Alignment (BRND-04 closeout) | 2/2 | ✓ Complete | 2026-11-15 |` (no `0/TBD | Not started`). |
| 9 | Intended canonical production domains/config targets are consistently applied/mapped in in-scope deploy/docs/script guidance and operator traceability (ROADMAP SC1, SC4). | ✓ VERIFIED | Consistent canonical targets across `docs/DEPLOY.md`, `scripts/verify-deploy.ps1` (primary example), `frontend/.env.example` (production guidance), `.github/workflows/expire-cron.yml` (guidance), `REQUIREMENTS.md`, and `ROADMAP.md`. `render.yaml` remains declarative/secret-free and behavior-preserving for canonical ops guidance; `frontend/vercel.json` valid minimal config (canonical domain is project/dashboard setting, documented in DEPLOY). |
| 10 | Deploy/smoke evidence is recorded/mapped to aligned contract with explicit status/handoff for canonical-host execution (ROADMAP SC2, SC3). | ✓ VERIFIED | D-10 matrix maps each required check to canonical alvo + legacy/historical evidence host(s) + status/reference; historical 2026-11-12/14/15 evidence preserved in Registro; pending canonical execution explicitly labeled `pendente de execução operacional`/handoff (including login/admin row and handoff sequence). BRND-04 and residual SECR-12/LIFE-13 ops caveat closed contratualmente with mapped evidence and no claim of live canonical deploy/smoke. |

**Score:** 10/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/DEPLOY.md` | Canonical state-alvo, legacy mapping, D-10 alignment matrix, preserved historical verification log, handoff/risk guidance | ✓ VERIFIED | Substantive and wired as principal ops/evidence artifact; contains required canonical targets, all 3 D-10 statuses, mapping for 4 legacy hosts, preserved 2026-11-12/14/15 rows, T-06-01, rebuild/rollback/handoff notes. |
| `scripts/verify-deploy.ps1` | Canonical branded hosts as primary smoke-gate examples while preserving parameterized/legacy usability | ✓ VERIFIED | Exists/substantive; executable gate structure retained (`param`, `$FrontendUrl`/`$BackendUrl`, `function Invoke-Http`, checks). Canonical and legacy host strings present in docs/examples/help text; parameterization preserved. |
| `frontend/.env.example` | Canonical production target guidance for API URLs/canonical-origin context without secrets; local defaults retained | ✓ VERIFIED | Local `http://localhost:8000` defaults retained; canonical `https://empreganoix.onrender.com`/`https://empreganoix.vercel.app` guidance present; placeholder/empty Turnstile handling, no secrets. |
| `frontend/.env.local.example` | Local-dev-safe defaults, no secrets | ✓ VERIFIED | `NEXT_PUBLIC_API_URL=http://localhost:8000` retained; no secret values added. |
| `render.yaml` | Declarative deploy config consistent with canonical single-origin ops guidance where applicable, secrets `sync:false` preserved | ✓ VERIFIED | `name: nqu-backend`, `autoDeploy: false`, `healthCheckPath: /api/v1/health`, sensitive keys `sync: false` preserved; no runtime/behavioral drift introduced. |
| `frontend/vercel.json` | Valid minimal config (conforme aplicável) | ✓ VERIFIED | Valid JSON with `"framework": "nextjs"`; canonical domain documented in DEPLOY (dashboard-level). |
| `.github/workflows/expire-cron.yml` | Canonical API target guidance coherent with secret-safe cron contract | ✓ VERIFIED | `vars.API_BASE_URL`, `secrets.CRON_SECRET`, `X-Cron-Secret`, canonical `https://empreganoix.onrender.com` guidance, endpoint path `/api/v1/admin/expire` and retry/fail-fast logic preserved. |
| `.planning/REQUIREMENTS.md` | Checked BRND-04/SECR-12/LIFE-13 with Phase 13 ownership, ops-scope caveats, DEPLOY refs | ✓ VERIFIED | All three checked with Phase 13 notes, DEPLOY refs, canonical targets, T-06-01/`X-Cron-Secret` preserved, explicit handoff wording and updated footer. |
| `.planning/ROADMAP.md` | Phase 13 status/notes/progress reflecting closure with evidence/handoff refs | ✓ VERIFIED | Plans listed, DEPLOY/canonical targets/T-06-01/handoff documented, progress complete (`2/2`, 2026-11-15). |
| `.planning/phases/13-canonical-host-deploy-ops-alignment/{13-01,13-02}-SUMMARY.md` | Execution summaries for completed plans | ✓ VERIFIED | Both present and consistent with commits/artifacts/scope decisions. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `docs/DEPLOY.md` | `scripts/verify-deploy.ps1` | Canonical smoke-gate invocation and D-10 check mapping reference same branded targets | ✓ WIRED | DEPLOY gate example uses `-FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com`; matrix cites `scripts/verify-deploy.ps1` checks and `X-Cron-Secret` cron rows. |
| `docs/DEPLOY.md` | `.planning/REQUIREMENTS.md` | Plan 02 closure notes cite canonical matrix/mapping/evidence in DEPLOY | ✓ WIRED | BRND-04/SECR-12/LIFE-13 notes reference `docs/DEPLOY.md` (state-alvo, mapeamento canônico↔legado, matriz D-10) and Phase 13 ownership. |
| `.planning/ROADMAP.md` | `docs/DEPLOY.md` | Phase 13 notes/status reference recorded alignment evidence and pending canonical-host execution handoff | ✓ WIRED | Phase 13 notes/evidence explicitly reference `docs/DEPLOY.md`, canonical hosts, matrix/mapping, and handoff/pending execution. |

### Data-Flow Trace (Level 4)

Not applicable. This phase delivered documentation/configuration/examples/scripts/planning alignment artifacts (no new runtime components rendering dynamic data). Behavioral/runtime data flow remains governed by prior phases and is only mapped/documented here.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Task/plan commits exist for declared artifacts | `git --no-pager log --oneline` / `git rev-parse --verify 11b74b6 a3341ac ba2bed8 09b69ec 5f14022` | All commits found (11b74b6, a3341ac, ba2bed8, 09b69ec, 5f14022) | ✓ PASS |
| Required canonical/mapping/matrix/status/historical strings present in DEPLOY and traceability docs | Targeted content checks over `docs/DEPLOY.md`, `REQUIREMENTS.md`, `ROADMAP.md` | Required strings/rows/status labels present | ✓ PASS |
| Live canonical-host smoke (`verify-deploy.ps1` against `empreganoix.vercel.app` / `empreganoix.onrender.com`) | Not executed (external provisioning/access; out of repo-only verification) | Explicitly recorded as `pendente de execução operacional`/handoff in DEPLOY matrix/notes and roadmap/requirements | ✓ SKIP (operational handoff documented) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| BRND-04 | 13-01, 13-02 | Domínio e hosts atualizados/canônicos com CORS configurado para origens EmpregaNoix (Phase 13 canonical host/env/CORS alignment & evidence) | ✓ SATISFIED (repo/contract + mapped evidence; live canonical execution pending/handoff) | `docs/DEPLOY.md` state-alvo/mapping/D-10/handoff; `scripts/verify-deploy.ps1` + env/workflow guidance aligned to canonical targets; `REQUIREMENTS.md`/`ROADMAP.md` mark closure with canonical targets and explicit handoff, no silent swap. |
| SECR-12 | 13-01, 13-02 | `/admin/expire` `X-Cron-Secret` only, fail-closed (residual canonical-host/deploy ops evidence owned by Phase 13) | ✓ SATISFIED (ops-evidence alignment/mapping; prior code/contract history preserved, T-06-01 intact) | DEPLOY canonical cron endpoint/matrix rows document fail-closed rejection + idempotency with `X-Cron-Secret` and preserve T-06-01; `REQUIREMENTS.md` keeps Phase 7/9/12 verification refs, adds Phase 13 ops mapping/handoff. No runtime/contract reopening. |
| LIFE-13 | 13-01, 13-02 | Expiração via endpoint protegido por `CRON_SECRET` com catch-up, `/admin/expire` aceita somente `X-Cron-Secret` (residual canonical-host/deploy ops evidence owned by Phase 13) | ✓ SATISFIED (ops-evidence alignment/mapping; prior code/contract history preserved, T-06-01 intact) | DEPLOY matrix/handoff map canonical catch-up endpoint/idempotency/`X-Cron-Secret`; `REQUIREMENTS.md` keeps Phase 12 contract evidence refs and records Phase 13 residual ops alignment with explicit handoff. |

**Orphaned requirements for Phase 13:** None found. REQUIREMENTS traceability maps BRND-04, SECR-12, LIFE-13 to Phase 13 (gap closure ownership) and all are declared in both plan frontmatters and accounted for above.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `docs/DEPLOY.md` | 241 | Markdown table separator row structurally malformed in `## Registro de verificação` (documented in `13-REVIEW.md` WR-01) | ℹ️ Info | Readability/audit rendering issue in historical log table; historical evidence rows/content remain present and preserved. Not a phase-goal blocker for canonical contract/mapping/matrix closure. |
| `scripts/verify-deploy.ps1` | 220-235 | Gate cannot complete "all checks passed" when manual cron is intentionally disabled (503) without secret (documented in `13-REVIEW.md` WR-02) | ℹ️ Info | Operational script UX/edge-case limitation noted by review; does not alter documented canonical contract, T-06-01 semantics, or repo alignment evidence delivered in Phase 13. |

No blocker anti-patterns found in phase artifacts. `13-REVIEW.md` findings are warnings carried forward as informational notes (not reopened/resolved in this verification scope).

### Human Verification Required

None for repo-level phase goal achievement. Operational execution on canonical hosts (provisioning, env/CORS/Turnstile/cron secret wiring, frontend rebuild/redeploy for `NEXT_PUBLIC_*`, and running `scripts/verify-deploy.ps1` against `https://empreganoix.vercel.app` / `https://empreganoix.onrender.com`) is explicitly documented as handoff/pending in `docs/DEPLOY.md`, `REQUIREMENTS.md`, and `ROADMAP.md` per D-04/D-13/D-14 and is outside automated repo verification.

### Gaps Summary

No gaps found. Phase 13 achieves its stated goal at the repo/contract/evidence-mapping level: canonical branded host state-alvo and deploy/ops guidance are aligned and traceable, legacy evidence is mapped without rewriting history, D-10 coverage/status vocabulary is recorded, and BRND-04 plus residual ops-evidence ownership for SECR-12/LIFE-13 are closed in traceability with T-06-01 preserved and explicit operational handoff where canonical-host execution remains pending.

---

_Verified: 2026-11-15T16:30:00Z_
_Verifier: OpenCode (gsd-verifier)_