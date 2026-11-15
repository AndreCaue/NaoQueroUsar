# Phase 13: Canonical Host, Deploy & Ops Alignment (BRND-04 closeout) - Research

**Researched:** 2026-11-15
**Domain:** Deploy/ops configuration alignment, CORS/API host canonicalization, operator evidence closure (docs + declarative config + smoke-gate mapping)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Hosts canônicos e mapeamento
- **D-01:** Adotar os nomes de marca como **hosts canônicos oficiais** de produção: frontend `https://empreganoix.vercel.app` e backend `https://empreganoix.onrender.com`. Roadmap/requisitos/docs/config-alvo devem refletir esses hosts como canônicos.
- **D-02:** Hosts/domínios já registrados em evidências ou usados anteriormente (ex.: `https://nao-quero-usar.vercel.app`, `https://naoquerousar.onrender.com`, `https://empreganoix-six.vercel.app`, `https://nqu-backend-x60n.onrender.com`) devem ser tratados como **legados/históricos e não canônicos**, com mapeamento explícito preservando a fidelidade das evidências existentes.
- **D-03:** Cobertura operacional **completa** no alinhamento: além de CORS, explicitar/alinhar `CORS_ORIGINS`, `BACKEND_API_URL`/`NEXT_PUBLIC_API_URL`, Turnstile Hostnames do domínio canônico, e exemplos/runbook/scripts de smoke para os hosts de marca.
- **D-04:** **BRND-04 pode ser fechado por alinhamento contratual + evidência documentada** quando os serviços não estiverem efetivamente publicados nos hosts canônicos no momento da execução. Config/docs/runbook/alvos canônicos devem ficar consistentes e o estado atual/legado mapeado com evidência; deploy/smoke real nos hosts canônicos, se ausente, fica como passo operacional externo registrado (não bloquear o fechamento contratual desta fase).

#### Escopo da configuração/alinhamento
- **D-05:** Escopo de artefatos no repositório: **docs + deploy config + scripts de verificação**. Atualizar (no mínimo, conforme aplicável) `docs/DEPLOY.md`, `render.yaml`, `frontend/vercel.json`, `frontend/.env.example` e exemplos/comandos em `scripts/verify-deploy.ps1` para refletir hosts canônicos e mapeamento legado.
- **D-06:** **Evitar mudanças de runtime** em backend/frontend; foco em configuração declarativa, documentação, exemplos e scripts. Se surgir necessidade real de alteração de código de runtime, tratar como desvio explícito e mínimo, mantendo-se dentro da fronteira da fase (sem novas features).
- **D-07:** Política de valores de produção **estrita e de origem única** no estado-alvo: `CORS_ORIGINS` contendo apenas `https://empreganoix.vercel.app` (sem barra final, sem wildcard), e `NEXT_PUBLIC_API_URL`/`BACKEND_API_URL` apontando para `https://empreganoix.onrender.com`. Hosts legados não devem compor o estado-alvo de CORS/URLs.
- **D-08:** Ao alinhar documentos, **normalizar o estado-alvo e exemplos operacionais para os hosts canônicos, preservando o histórico**. Não reescrever linhas/tabelas de evidência histórica para "parecer canônico"; adicionar notas/mapeamento canônico onde necessário para interpretar registros legados.

#### Evidência e critérios de fechamento
- **D-09:** Registrar evidência como **matriz de alinhamento + evidência histórica mapeada** (não exigir nova execução de `verify-deploy.ps1` nos canônicos se eles não estiverem provisionados/publicados). Cada item deve indicar status como verificado em host legado, alinhado contratualmente ao canônico, ou pendente de execução operacional, com referências às evidências existentes (ex.: registros em `docs/DEPLOY.md`).
- **D-10:** A matriz deve cobrir o **conjunto completo do roadmap**: `GET /api/v1/health` (status/env/Turnstile), preflight CORS da origem canônica, endpoint de cron `/admin/expire` (rejeição sem/errada credencial conforme fail-closed + idempotência com `X-Cron-Secret` correto), e superfícies públicas/admin chave relevantes (board, páginas legais, login/admin) com status/mapeamento.
- **D-11:** Fonte principal de registro: **`docs/DEPLOY.md` + notas em `REQUIREMENTS.md` e roadmap**. Incluir em `docs/DEPLOY.md` seção/matriz de alvo canônico, mapeamento de hosts legados e status dos checks; refletir fechamento/caveats e ownership em `.planning/REQUIREMENTS.md` e atualizar status/notas da Phase 13 em `.planning/ROADMAP.md` conforme o critério 4.
- **D-12:** **SECR-12 e LIFE-13** devem ser marcados como **fechados com nota de escopo ops** nesta fase: o lado de código/contrato foi verificado em fases anteriores e o resíduo de alinhamento canônico/evidência operacional é coberto/mapeado agora. Se a execução real em hosts canônicos estiver ausente, registrar como handoff operacional explícito na nota/evidência (sem reabrir T-06-01).
- **D-13:** Recomendar **sequência operacional completa e segura** para aplicação futura: (1) alinhar/provisionar hosts canônicos nos provedores, (2) configurar envs/CORS/Turnstile Hostnames/segredos de cron, (3) rebuild/redeploy do frontend (variáveis `NEXT_PUBLIC_*` são inlinadas no build), (4) validar health/CORS/cron/superfícies com `scripts/verify-deploy.ps1` (ou equivalente), (5) registrar evidência — com rollback por reversão de env/config/domínio.
- **D-14:** Se o nome exato do host canônico não puder ser provisionado, **manter o alvo canônico e registrar bloqueio**: preservar `empreganoix.vercel.app` / `empreganoix.onrender.com` como alvo contratual nos artefatos; documentar o host realmente obtido como desvio/bloqueio com mapeamento explícito, sem trocar silenciosamente o canônico.
- **D-15:** Documentar **postura completa de risco operacional**: execução real pode permanecer pendente (projeto mantido em desenvolvimento/local), `NEXT_PUBLIC_*` exige rebuild, Turnstile Hostnames e CORS devem coincidir com a origem real, cron/scheduler dependem de envs/segredos corretos, cold-start/scheduler split permanecem considerações operacionais conhecidas, e rollback ocorre por reversão de env/config/domínio.
- **D-16:** Atualizar **checkboxes para concluído + notas de evidência/ownership** em `REQUIREMENTS.md` para **BRND-04, SECR-12 e LIFE-13**, apontando para a matriz/evidência de Phase 13 e preservando o histórico de verificações anteriores (código/contrato). Atualizar também o status/notas da Phase 13 em `ROADMAP.md`.

### OpenCode's Discretion
- Formato exato da matriz/tabela em `docs/DEPLOY.md`, nomes das seções e nível de detalhe textual, desde que cubra os checks de D-10 e o mapeamento canônico↔legado.
- Seleção precisa de arquivos de exemplo/env a ajustar dentro do escopo de D-05 (ex.: `.env.example`, `.env.local.example`, notas em `README` se estritamente necessárias para consistência operacional), sem introduzir segredos.
- Estratégia de edição para scripts de verificação (parâmetros/exemplos/defaults documentais) que preserve utilidade para hosts legados históricos quando apropriado, sem conflitar com o alvo canônico.
- Redação final das notas de caveat/handoff em `REQUIREMENTS.md`, `ROADMAP.md` e `docs/DEPLOY.md`, desde que preserve D-04, D-08, D-12, D-14 e D-15.

### Deferred Ideas (OUT OF SCOPE)
- Provisionamento/execução real de deploy, rebuild e smoke gate nos hosts canônicos `empreganoix.vercel.app` / `empreganoix.onrender.com` (handoff operacional; bloqueios de conta/provedor/nomes indisponíveis documentados).
- Compra/configuração de domínio próprio e redirects/aliases de produção — fora desta fase.
- Renomeação de identificadores internos legados não voltados ao usuário (ex.: nome do serviço Render `nqu-backend`, chaves de storage) — não exigida para fechamento de BRND-04/SECR-12/LIFE-13.
- Revalidação Nyquist ou novas validações automatizadas além do escopo de alinhamento/evidência desta fase.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BRND-04 | Domínio e hosts atualizados — backend `https://empreganoix.onrender.com`, frontend `https://empreganoix.vercel.app`; CORS configurado para origens EmpregaNoix *(gap closure: Phase 13 — canonical host/env/CORS alignment & evidence)* | Canonical host/URL/CORS/Turnstile target inventory; file-by-file edit map for docs + deploy config + verify script examples; canonical↔legacy evidence matrix and closure-note pattern preserving historical fidelity (D-01..D-11, D-16). |
| SECR-12 | Endpoint `/admin/expire` autenticado por header `X-Cron-Secret` — fail-closed: 503 quando header ausente/incorreto *(Phase 12 reconciliation — split ownership ... residual canonical-host/deploy evidence owned by Phase 13)* | Evidence mapping shows code/contract already verified (Phase 7/9/12). Research specifies ops-alignment closure: matrix rows for 401/403/503 rejection and 200 idempotency on canonical-target mapping, runbook/cron coherence, and no T-06-01 reopening (D-10, D-12). |
| LIFE-13 | Expiração disparada por endpoint protegido por `CRON_SECRET`, com passe de recuperação (catch-up) — endpoint `/admin/expire` aceita somente `X-Cron-Secret` *(Phase 12 reconciliation — split ownership ... residual canonical-host/deploy evidence owned by Phase 13)* | Same ops-evidence closure as SECR-12: canonical cron endpoint target (`https://empreganoix.onrender.com/api/v1/admin/expire`), GitHub Actions `vars.API_BASE_URL` guidance, smoke-gate cron/idempotency checks, and handoff if not executed on canonical host (D-03, D-10, D-12, D-13). |
</phase_requirements>

## Summary

Phase 13 is a **contractual/documentary closeout**, not a feature or runtime-behavior phase. The authoritative audit gap is host/env/CORS drift: the intended branded contract is `https://empreganoix.vercel.app` (frontend origin) ↔ `https://empreganoix.onrender.com` (backend API/CORS target), but recorded production evidence is on suffixed legacy hosts (`https://empreganoix-six.vercel.app`, `https://nqu-backend-x60n.onrender.com`), and the deploy runbook contains a mixed historical record (including earlier failed checks run against the branded hostnames). [VERIFIED: `.planning/v1.1-MILESTONE-AUDIT.md`, `docs/DEPLOY.md` registro de verificação, `13-CONTEXT.md` D-01/D-02]

The implementation surface is therefore **text/config alignment + evidence traceability** across the repo artifacts named in D-05: `docs/DEPLOY.md`, `render.yaml`, `frontend/vercel.json`, `frontend/.env.example`, and `scripts/verify-deploy.ps1` (plus `REQUIREMENTS.md`/`ROADMAP.md` for closure notes per D-11/D-16). No backend/frontend runtime code changes are required because host resolution is already env-driven (`frontend/lib/api.ts` resolves `NEXT_PUBLIC_API_URL`; `frontend/lib/jobs.ts` prefers `BACKEND_API_URL` server-side; backend CORS is read from `settings.cors_origins_list` in `backend/app/core/config.py`/`backend/app/main.py`) and `/admin/expire` contract is already reconciled (X-Cron-Secret-only, fail-closed). [VERIFIED: `frontend/lib/api.ts`, `frontend/lib/jobs.ts`, `backend/app/main.py`, `backend/app/core/config.py`, `.planning/REQUIREMENTS.md`, `.planning/phases/12-.../12-CONTEXT.md` refs in 13-CONTEXT]

**Primary recommendation:** Plan one small, ordered execution pass: (1) inventory and normalize the *state-alvo canônico* in D-05 artifacts without rewriting historical evidence, (2) add a canonical↔legacy matrix in `docs/DEPLOY.md` covering all D-10 checks with status labels `verificado em host legado | alinhado contratualmente ao canônico | pendente de execução operacional`, (3) close BRND-04/SECR-12/LIFE-13 in `REQUIREMENTS.md` and Phase 13 status/notes in `ROADMAP.md` with explicit ops-scope ownership and handoff text per D-04/D-12/D-14/D-15. Treat real canonical-host execution as documented external handoff, not a blocker.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Canonical public origin (browser requests, CORS allow-origin, Turnstile hostname) | Frontend deploy / Browser edge (Vercel domain) | Backend config (CORS allowlist) | Browser origin is the Vercel host; backend must trust exactly that origin (`CORS_ORIGINS`) [VERIFIED: `docs/DEPLOY.md`, `backend/app/main.py`]. |
| Canonical API base for browser/admin calls | Frontend config (build-time `NEXT_PUBLIC_API_URL`) | Backend service host (Render) | Client bundle bakes `NEXT_PUBLIC_API_URL`; production build fails if missing [VERIFIED: `frontend/lib/api.ts`, `docs/DEPLOY.md`]. |
| Canonical API base for SSR board fetch | Frontend server/runtime config (`BACKEND_API_URL`, fallback `NEXT_PUBLIC_API_URL`) | Backend service host (Render) | SSR fetch reads `BACKEND_API_URL` first at runtime [VERIFIED: `frontend/lib/jobs.ts`]. |
| Cron catch-up target and auth | Ops automation (GitHub Actions `vars.API_BASE_URL` + `secrets.CRON_SECRET`) | Backend API (`/admin/expire`, X-Cron-Secret-only fail-closed) | External scheduler calls backend endpoint; auth/contract enforced server-side, evidence/target documented in ops artifacts [VERIFIED: `.github/workflows/expire-cron.yml`, `docs/DEPLOY.md`, `REQUIREMENTS.md` SECR-12/LIFE-13]. |
| Smoke/evidence gate | Operator script + runbook (`scripts/verify-deploy.ps1`, `docs/DEPLOY.md`) | Frontend/Backend live surfaces | Script validates health/CORS/cron/surfaces/leak/cold-start against provided URLs; evidence recorded in docs/planning [VERIFIED: `scripts/verify-deploy.ps1`, `docs/DEPLOY.md`]. |

## Current State Inventory (Evidence-Based)

> This is the concrete drift surface the planner must close. [VERIFIED: repo reads + `Select-String` on 2026-11-15]

| Artifact | Current state relevant to Phase 13 | Drift / action implied |
|----------|-------------------------------------|------------------------|
| `docs/DEPLOY.md` | Comprehensive runbook with placeholders in some examples **and** branded-host strings in several places; **Registro de verificação** mixes 2026-11-12 rows (tested against `empreganoix.vercel.app`/`empreganoix.onrender.com`, failures recorded), 2026-11-14/15 approved smoke on legacy hosts `empreganoix-six.vercel.app` + `nqu-backend-x60n.onrender.com`, and a pending row referencing `nqu-backend-x60n`. Mentions CORS/Turnstile Hostnames/`NEXT_PUBLIC_*` rebuild/cold-start/rollback. | Add explicit **canonical target** section + canonical↔legacy mapping + D-10 alignment matrix; normalize future/target examples to canonical while preserving every historical row verbatim (D-01,D-02,D-03,D-07,D-08,D-09,D-10,D-11,D-13,D-15). |
| `render.yaml` | Blueprint for service `name: nqu-backend`, region/commands/env declarations correct; secrets `sync:false`; no host URL literals except `healthCheckPath`. Service name is internal legacy identifier. | Keep `nqu-backend` name (deferred, non-user-facing). Ensure comments/env guidance align to canonical CORS/origin semantics if mentioned; no secret values; no runtime behavior change. [VERIFIED: `render.yaml`, D-122 deferred] |
| `frontend/vercel.json` | Minimal (`$schema`, `framework: nextjs`), no host/domain/CORS/redirect config. | Likely no canonical-host value to inject; confirm and, if needed, document in DEPLOY that canonical host is a Vercel project/domain setting (not versioned here) to satisfy D-05 "conforme aplicável" without inventing config. [VERIFIED: `frontend/vercel.json`] |
| `frontend/.env.example` | Local defaults `http://localhost:8000` for `NEXT_PUBLIC_API_URL`/`BACKEND_API_URL`, empty `NEXT_PUBLIC_TURNSTILE_SITE_KEY`; production guidance comments exist. | Normalize production target guidance/examples to canonical `https://empreganoix.onrender.com` and canonical frontend origin context without committing secrets and without breaking local-dev clarity (discretion). [VERIFIED: file content] |
| `scripts/verify-deploy.ps1` | Fully parameterized gate; header/examples use placeholders `<seu-projeto>.vercel.app` / `<backend>.onrender.com`; checks cover health/env/Turnstile, CORS allow/deny, board/legal/API, cron 401/403/503 + idempotency, leak, cold-start — matches D-10. | Update example invocations/comments to show canonical branded hosts as primary state-alvo while keeping parameterization usable for legacy/historical hosts if needed (discretion, D-05,D-08). |
| `.github/workflows/expire-cron.yml` | Uses `vars.API_BASE_URL` and `secrets.CRON_SECRET`; error/help text shows placeholder `https://<backend>.onrender.com`; endpoint path `/api/v1/admin/expire` correct. | Keep contract/coherence: canonical target URL belongs in runbook/matrix and variable guidance (D-03,D-11); workflow itself should remain secret-free and generic unless a comment/example tweak is strictly useful. |
| `frontend/lib/api.ts`, `frontend/lib/jobs.ts` | Env-driven URL resolution, production fail-fast on missing `NEXT_PUBLIC_API_URL`, SSR prefers `BACKEND_API_URL`. | **No runtime change** (D-06). Research confirms correct seams for D-03/D-07 operational alignment. |
| `backend/app/main.py`, `backend/app/core/config.py` | CORS from `settings.cors_origins_list`, strict prod validation (no trailing slash/wildcard/empty/invalid scheme), cron/Turnstile fail-closed semantics. | **No runtime change** (D-06). Behavior already enforces the strict state-alvo policy once envs are set correctly. |

## Standard Stack

### Core (existing, unchanged by this phase)
| Component | Version / Form | Purpose | Why Standard for this phase | Confidence |
|-----------|----------------|---------|-----------------------------|------------|
| Markdown docs (`docs/DEPLOY.md`, `.planning/*.md`) | Repo text artifacts | Canonical runbook, alignment matrix, closure traceability | D-05/D-11 designate docs as primary evidence/registration surface | [VERIFIED: CONTEXT D-05,D-11] |
| PowerShell 5.1+ script (`scripts/verify-deploy.ps1`) | Repo script, UTF-8 BOM, parameterized URLs | Repeatable smoke gate for D-10 checks | Already implements required checks and is the referenced operator gate | [VERIFIED: `scripts/verify-deploy.ps1`, `docs/DEPLOY.md`] |
| Render Blueprint (`render.yaml`) | Declarative YAML | Versioned backend deploy shape (service, env keys, commands, health check) | D-05 in-scope; secrets remain dashboard-only (`sync:false`) | [VERIFIED: `render.yaml`] |
| Vercel config (`frontend/vercel.json`) + env examples | JSON/text | Versioned frontend deploy hints and operator env guidance | D-05 in-scope "conforme aplicável" | [VERIFIED: files] |
| Next.js 16 env model | `NEXT_PUBLIC_*` build-time, server env runtime | Host/API alignment mechanism | Correctly explains rebuild requirement (D-13/D-15) | [VERIFIED: `frontend/lib/api.ts`, `frontend/lib/jobs.ts`, STATE decisions] |
| FastAPI settings/CORS | Pydantic Settings + CORSMiddleware | Strict origin enforcement | Fail-closed validation matches D-07 policy | [VERIFIED: `backend/app/core/config.py`, `backend/app/main.py`] |

### Supporting (operational systems referenced, not modified as code in-repo)
| System | Purpose in phase | When relevant | Confidence |
|--------|------------------|---------------|------------|
| Vercel project/domain + env vars | Canonical frontend host, `NEXT_PUBLIC_API_URL`, `BACKEND_API_URL`, Turnstile site key, rebuild/redeploy | D-01,D-03,D-07,D-13,D-15 (handoff if not executed) | [VERIFIED: `docs/DEPLOY.md`] |
| Render service env vars + manual deploy | Canonical backend host, `CORS_ORIGINS`, Turnstile/cron secrets, Alembic-on-boot | D-01,D-03,D-07,D-13,D-15 | [VERIFIED: `render.yaml`, `docs/DEPLOY.md`] |
| Cloudflare Turnstile Hostnames | Must include canonical frontend origin | D-03,D-15 | [VERIFIED: `docs/DEPLOY.md` pre-reqs/desvio sections] |
| GitHub Actions repo vars/secrets | `vars.API_BASE_URL` canonical backend, `secrets.CRON_SECRET` | D-03,D-10,D-13 | [VERIFIED: `.github/workflows/expire-cron.yml`, `docs/DEPLOY.md`] |
| Neon (Postgres) | DB backing health/expiry behavior (no schema/host-string change expected) | Context only; ops dependency | [VERIFIED: project constraints/runbook] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual markdown matrix in `docs/DEPLOY.md` | Separate `.planning/.../EVIDENCE.md` or JSON artifact | D-11 explicitly names `docs/DEPLOY.md` as principal registro; keep matrix there and reference from REQUIREMENTS/ROADMAP for traceability. |
| Rewriting historical rows to canonical URLs | Preserve rows + add mapping/matrix | Rewriting would falsify evidence history and violates D-02/D-08. |
| Changing `render.yaml` service name to branded name | Keep `nqu-backend` | Internal identifier rename is explicitly deferred and unnecessary for BRND-04/SECR-12/LIFE-13 (D-122). |
| Adding runtime host-override code | Env/config/docs alignment only | Violates D-06 and is unnecessary given existing env-driven resolution/fail-closed CORS. |

**Installation:** None required (documentation/config alignment phase). [VERIFIED: scope]

## Architecture Patterns

### Recommended Alignment Structure (state-alvo first, history preserved)
```
docs/DEPLOY.md
├── [existing] Arquitetura / Pré-requisitos / Backend / Frontend / CORS / Cron / Cold-start / Gate / Rollback / Checklist
├── [add/normalize] Alvo Canônico (D-01, D-07) — hosts, envs, Turnstile Hostnames, exemplos de comando
├── [add] Mapeamento de Hosts Legados ↔ Canônico (D-02, D-14)
├── [add] Matriz de Alinhamento & Evidência (D-09, D-10) — status por check com refs históricas
├── [keep verbatim] Registro de verificação (histórico) — sem reescrita de linhas antigas (D-08)
└── [add] Handoff operacional / riscos (D-04, D-12, D-13, D-15) se não houver execução nos canônicos

.planning/REQUIREMENTS.md  -> checkboxes/notas BRND-04, SECR-12, LIFE-13 (D-16)
.planning/ROADMAP.md       -> Phase 13 status/notas/evidência refs (D-11, D-16)
```

### Pattern 1: State-Alvo vs Evidência Histórica (separation of concerns)
**What:** Declare canonical contract as the single forward-looking target; record what was actually observed against which host as immutable history; connect them via explicit mapping/status.
**When to use:** Any time real deploy ran on non-canonical/suffixed hosts (current situation) or when execution is pending (D-04).
**Example (matrix row shape, illustrative):**
```markdown
| Check (D-10) | Alvo canônico | Host verificado (evidência) | Status | Evidência / nota |
|---|---|---|---|---|
| `GET /api/v1/health` (env/prod, turnstile live) | `https://empreganoix.onrender.com/api/v1/health` | `https://nqu-backend-x60n.onrender.com` (2026-11-15) | verificado em host legado; alinhado contratualmente ao canônico | `docs/DEPLOY.md` registro 2026-11-15: PASS ...; execução em host canônico pendente (handoff D-13) |
| Preflight CORS origem canônica | `Origin: https://empreganoix.vercel.app` | `https://empreganoix-six.vercel.app` ↔ backend legado (2026-11-15) | verificado em host legado; alinhado contratualmente ao canônico | ... |
```
[ASSUMED: exact column names/wording are planner discretion; status vocabulary should make D-09 categories unambiguous.]

### Pattern 2: Strict single-origin production target
**What:** Document and exemplify one exact frontend origin and one exact backend base URL; no trailing slash, no wildcard, no legacy origins in target CORS/URL envs.
**When to use:** `CORS_ORIGINS`, `NEXT_PUBLIC_API_URL`, `BACKEND_API_URL`, Turnstile Hostnames, `vars.API_BASE_URL`, `verify-deploy.ps1` canonical examples.
**Example (state-alvo):**
```text
Frontend (origem canônica): https://empreganoix.vercel.app
Backend  (API canônica):    https://empreganoix.onrender.com

CORS_ORIGINS=https://empreganoix.vercel.app
NEXT_PUBLIC_API_URL=https://empreganoix.onrender.com
BACKEND_API_URL=https://empreganoix.onrender.com
Turnstile Hostnames: empreganoix.vercel.app
GitHub Actions vars.API_BASE_URL=https://empreganoix.onrender.com
verify-deploy: -FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com
```
[VERIFIED: D-01,D-03,D-07; backend rejects trailing slash/wildcard outside dev per `backend/app/core/config.py`]

### Pattern 3: Parameterized smoke gate, canonical-by-default examples
**What:** Keep `verify-deploy.ps1` parameter-driven (supports legacy hosts for reproducing historical evidence) but present canonical branded hosts as the primary documented invocation.
**When to use:** Script header/help/examples in D-05 scope.
**Example:**
```powershell
# Alvo canônico (state-alvo)
$env:CRON_SECRET = "<CRON_SECRET>"
powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 `
  -FrontendUrl https://empreganoix.vercel.app `
  -BackendUrl  https://empreganoix.onrender.com

# Hosts legados/históricos (somente para reproduzir/interpretar evidência registrada)
# -FrontendUrl https://empreganoix-six.vercel.app -BackendUrl https://nqu-backend-x60n.onrender.com
```
[ASSUMED: exact comment wording/layout discretionary; must not break script behavior.]

### Anti-Patterns to Avoid
- **Rewriting history to look canonical:** Editing 2026-11-12/14/15 evidence rows to substitute canonical hosts destroys audit fidelity (violates D-02,D-08). Add mapping/matrix instead.
- **Silent canonical swap:** If branded hostnames cannot be provisioned, do not replace target with suffixed host; record deviation/blocker (D-14).
- **Runtime "quick fix":** Adding host remaps/fallbacks in `api.ts`/`jobs.ts`/CORS middleware is out of scope and unnecessary (D-06).
- **Adding legacy origins to production `CORS_ORIGINS`:** Target must be single canonical origin (D-07); legacy hosts belong only in mapping/evidence notes.
- **Treating pending real execution as failure of contractual closure:** D-04/D-12 explicitly allow closure with documented handoff when canonical infra is unavailable.
- **Committing secrets or real env values:** All D-05 edits must remain secret-free (`sync:false`, placeholders, examples only). [VERIFIED: `render.yaml`, `docs/DEPLOY.md`]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Production smoke validation | New ad-hoc checklist logic or one-off curl notes only | `scripts/verify-deploy.ps1` (existing gate) + `docs/DEPLOY.md` matrix | Gate already covers D-10 (health/env/Turnstile, CORS allow/deny, board/legal/API, cron 401/403/503 + idempotency, leak, cold-start) [VERIFIED: script, D-10]. |
| Evidence traceability | Scattered comments across files | Single matrix/mapping section in `docs/DEPLOY.md` referenced by `REQUIREMENTS.md`/`ROADMAP.md` | D-11 defines principal source and cross-doc ownership notes. |
| CORS/URL enforcement in code | Middleware overrides or special-casing hosts | Existing env-driven config + strict `Settings` validators | Already fail-closed and aligned with D-07; code change forbidden/unneeded (D-06). |
| Cron contract re-verification | Re-testing/reopening T-06-01 | Existing reconciled evidence (Phase 7/9/12) + ops-evidence mapping | D-12 requires split-ownership closure note, not contract rework. |

**Key insight:** This phase closes an **alignment/evidence gap**; the reliable mechanisms (env resolution, CORS validation, cron auth, smoke script) already exist — the risk is inconsistency and undocumented mapping, not missing runtime capability.

## Common Pitfalls

### Pitfall 1: Rewriting historical evidence to match the canonical target
**What goes wrong:** Past verification rows/URLs are edited, making it impossible to tell what host was actually tested and when.
**Why it happens:** Desire for a "clean" document showing only branded hosts.
**How to avoid:** Freeze historical `Registro de verificação` rows as-is; add canonical-target, mapping, and matrix sections that interpret them (D-02,D-08,D-09).
**Warning signs:** Any diff that changes URLs/timestamps/results inside existing dated evidence rows.

### Pitfall 2: `NEXT_PUBLIC_*` treated as runtime-configurable
**What goes wrong:** Docs/envs updated but frontend still calls old backend because bundle was not rebuilt/redeployed.
**Why it happens:** Next.js inlines `NEXT_PUBLIC_*` at build time; `BACKEND_API_URL` is server-side/runtime-read but client calls depend on baked public var. [VERIFIED: `frontend/lib/api.ts`, `frontend/lib/jobs.ts`, STATE]
**How to avoid:** Matrix/runbook/handoff must state "update env + rebuild/redeploy frontend" as a required step (D-13,D-15).
**Warning signs:** Health/CORS pass on backend but browser requests hit legacy host or fail CORS.

### Pitfall 3: CORS origin string mismatch
**What goes wrong:** Preflight returns 400 / missing `Access-Control-Allow-Origin` despite "correct" domain.
**Why it happens:** Trailing slash, wrong scheme, extra origin, or wildcard; backend rejects/doesn't match outside dev. [VERIFIED: `backend/app/core/config.py`, DEPLOY 2026-11-12 CORS failure row]
**How to avoid:** Enforce D-07 exact value `https://empreganoix.vercel.app` in state-alvo docs/examples; keep legacy origins out of target.
**Warning signs:** `verify-deploy.ps1` check 2 fails or check 3 accepts foreign origin.

### Pitfall 4: Turnstile Hostnames not aligned with real/canonical origin
**What goes wrong:** Widget/reveal/login fails in browser even with correct keys and envs.
**Why it happens:** Cloudflare Turnstile validates hostnames; production/staging domains must be listed. [VERIFIED: `docs/DEPLOY.md`]
**How to avoid:** Include Turnstile Hostnames in canonical target, matrix (D-03,D-10 coverage via surfaces/login context), and handoff (D-13,D-15).
**Warning signs:** `turnstile.mode`/health OK but client-side challenges fail on canonical frontend.

### Pitfall 5: Confusing contractual closure with executed canonical deploy
**What goes wrong:** Phase treated as blocked because branded Vercel/Render names are unavailable or not yet deployed.
**Why it happens:** Conflating "target aligned" with "target live".
**How to avoid:** Apply D-04/D-14: keep canonical target, document deviation/blocker/handoff, mark matrix statuses accordingly.
**Warning signs:** Plans that require real provisioning/smoke on canônicos as mandatory in-repo tasks.

### Pitfall 6: Accidental scope creep into runtime code or internal renames
**What goes wrong:** Edits to `api.ts`/`jobs.ts`/backend config behavior or renaming `nqu-backend` service.
**Why it happens:** Desire to "fully rebrand" everything.
**How to avoid:** Limit to D-05 artifacts + planning traceability docs; treat runtime/internal identifiers per D-06 and deferred D-122.
**Warning signs:** Diffs under `backend/app/**` or `frontend/lib/**` without explicit justified deviation.

### Pitfall 7: Cron endpoint mis-targeted or secret mismatch treated as contract regression
**What goes wrong:** `/admin/expire` returns 401/503 in ops tests; responders reopen T-06-01.
**Why it happens:** `vars.API_BASE_URL`/`CRON_SECRET` misconfigured, or confusion between fail-closed 503 (unconfigured) and auth rejection.
**How to avoid:** Matrix must distinguish unauth fail-closed/idempotent-200 checks and preserve X-Cron-Secret-only contract note (D-10,D-12). [VERIFIED: `docs/DEPLOY.md`, `verify-deploy.ps1`, REQUIREMENTS]
**Warning signs:** Language suggesting Bearer JWT admin should work for expire (forbidden by T-06-01).

## Code Examples

Verified patterns from repository sources (reference for planners; not runtime changes):

### Env-driven API base resolution (frontend) — why docs/env alignment is sufficient
```ts
// Source: frontend/lib/api.ts
function resolveApiBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (fromEnv) return fromEnv;
  if (process.env.NODE_ENV === "production") {
    throw new Error("NEXT_PUBLIC_API_URL is not set...");
  }
  return "http://localhost:8000";
}
const API = resolveApiBase();
```

```ts
// Source: frontend/lib/jobs.ts
const API =
  process.env.BACKEND_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";
```
[VERIFIED: repo files] — Implication: canonical production alignment = set `NEXT_PUBLIC_API_URL`/`BACKEND_API_URL` to `https://empreganoix.onrender.com` and rebuild/redeploy frontend (D-07,D-13).

### Strict CORS allowlist from settings (backend)
```python
# Source: backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
    allow_credentials=False,
)
```
```python
# Source: backend/app/core/config.py (behavior)
# outside dev: rejects empty/'*'/trailing-slash/non-http(s) origins
@property
def cors_origins_list(self) -> List[str]:
    origins = self.CORS_ORIGINS.split(",")
    return [origin.strip() for origin in origins]
```
[VERIFIED: repo files] — Implication: state-alvo must be exactly `CORS_ORIGINS=https://empreganoix.vercel.app` (D-07).

### Smoke gate invocation pattern (parameterized)
```powershell
# Source: scripts/verify-deploy.ps1 (header examples, generalized)
powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 `
  -FrontendUrl https://<seu-projeto>.vercel.app `
  -BackendUrl  https://<backend>.onrender.com
# script reads $env:CRON_SECRET by default for authenticated cron check
```
[VERIFIED: script] — Planner should replace documented primary example with canonical hosts and retain legacy-note usage (D-05 discretion).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pre-rebrand/non-canonical deploy hosts recorded as operational reality | Branded canonical contract `empreganoix.vercel.app` / `empreganoix.onrender.com` as state-alvo with legacy-host evidence mapped | v1.1 audit/Phase 13 context (2026-11-15) | BRND-04 closure depends on documented alignment, not silent host substitution [VERIFIED: audit, CONTEXT]. |
| ROADMAP ambiguity around `/admin/expire` auth (historical) | X-Cron-Secret-only, fail-closed (T-06-01) reconciled in code/docs; Phase 13 closes only residual ops-evidence alignment | Phase 12 reconciliation (2026-11-15) | Do not reopen contract; map evidence to canonical target [VERIFIED: REQUIREMENTS, STATE, CONTEXT D-12]. |
| Treating "deploy happened somewhere" as sufficient | Explicit canonical↔legacy mapping + D-10 matrix + handoff when canonical infra unavailable | Phase 13 decisions (D-04,D-09,D-14) | Enables honest closure with traceable caveats. |

**Deprecated/outdated for this phase's target state:**
- `https://empreganoix-six.vercel.app`, `https://nqu-backend-x60n.onrender.com`, `https://nao-quero-usar.vercel.app`, `https://naoquerousar.onrender.com` as *canonical* targets — treat as legacy/historical only (D-02). [VERIFIED: CONTEXT]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Exact markdown table columns/labels for the canonical↔legacy matrix (beyond required status categories and D-10 coverage) are flexible as long as unambiguous. | Architecture Patterns / Validation | Planner may choose a format that is hard to audit; mitigate by including all D-10 checks as explicit rows and citing evidence refs. |
| A2 | `frontend/vercel.json` requires no content change (canonical domain is project/dashboard-level), but documenting "configured in Vercel project settings" in DEPLOY satisfies D-05 "conforme aplicável". | Current State Inventory | If versioned Vercel config is expected to carry domain data, plan may miss an edit; low risk because file currently has no host fields. |
| A3 | `frontend/.env.example` can include commented canonical production examples while keeping localhost defaults for local dev, satisfying both D-07 normalization intent and developer usability. | Current State Inventory / Pitfalls | Could confuse operators if not clearly labeled; planner must separate "dev local" vs "state-alvo produção (canônico)". |
| A4 | No `frontend/.env.local.example` or README host-alignment edit is strictly necessary beyond D-05 named artifacts; planner should only touch them if a concrete inconsistency is found. | Open Questions / discretion | Minor residual doc drift outside named scope. |
| A5 | "Superfícies públicas/admin chave relevantes (board, páginas legais, login/admin)" for D-10 can be evidenced/mapped using existing smoke checks (`/`, `/privacidade`, `/termos-de-uso`, API/health/cron) plus recorded/handoff notes for login/admin UI when not separately scripted. | Validation Architecture | If reviewer expects a distinct automated admin-UI check row, matrix must explicitly mark status/handoff rather than imply automation. |

## Open Questions

1. **How to represent canonical production values in `frontend/.env.example` without harming local dev flow?**
   - What we know: File currently uses localhost; D-07/D-08 require canonical state-alvo normalization; secrets must not be committed. [VERIFIED]
   - What's unclear: Best balance between copy-pasteable local defaults and unmistakable canonical production target.
   - Recommendation: Keep local runnable defaults, add a clearly labeled "Estado-alvo produção (canônico)" block/comments with `https://empreganoix.onrender.com` and note that `NEXT_PUBLIC_*` requires rebuild/redeploy.

2. **Should `.github/workflows/expire-cron.yml` help text be updated from placeholder to canonical host?**
   - What we know: It references `vars.API_BASE_URL` (dashboard-configured) and shows a placeholder example in an error message. [VERIFIED]
   - What's unclear: Whether changing example text materially improves D-03 alignment vs keeping generic.
   - Recommendation: If edited, keep it non-secret and clearly illustrative; canonical target must in any case be explicit in `docs/DEPLOY.md` matrix/runbook (D-11).

3. **Are any additional repo docs (README, frontend README) asserting legacy hosts as current targets?**
   - What we know: Root README currently contains brand name string only (spot check). [VERIFIED: search]
   - What's unclear: Exhaustive repo-wide doc drift outside D-05.
   - Recommendation: Planner should do a quick targeted grep for legacy hosts in docs/examples during execution; only adjust if strictly necessary for operational consistency (discretion) and without scope creep.

4. **Canonical-host execution availability at closeout time**
   - What we know: Project may remain in dev/local; branded hostnames may be unavailable; prior approved evidence is on legacy suffixed hosts. [VERIFIED: STATE, CONTEXT D-04/D-14/D-15]
   - What's unclear: Whether operator will provision canônicos before/after this phase.
   - Recommendation: Default plan to contractual closure + matrix + explicit handoff; if execution happens, record it as additional evidence without rewriting history.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Git repository + text editing tools | All planned doc/config edits and traceability updates | ✓ | repo present (`.git`) | — |
| PowerShell (`pwsh`/Windows PowerShell 5.1) | Running `scripts/verify-deploy.ps1` smoke gate if operator executes | ✓ (script targets 5.1; Windows environment indicated) [ASSUMED: runtime availability on operator machine] | 5.1+ compatible script [VERIFIED: script header] | Manual equivalent checks via curl/browser with same criteria recorded |
| Network access to deployed hosts | Live smoke/CORS/cron verification | Unknown (depends on operator/deploy state) | — | D-04/D-09 contractual alignment + historical-evidence mapping + handoff |
| Vercel dashboard/project access | Set canonical frontend domain/envs, rebuild | Unknown (external account access) | — | Document handoff/blocker (D-14,D-15) |
| Render dashboard/service access | Set canonical backend envs/CORS, deploy | Unknown | — | Document handoff/blocker |
| Cloudflare Turnstile admin access | Add canonical Hostname, live keys if applicable | Unknown | — | Document handoff/risk (`test_override` deviation context remains historical) |
| GitHub repo settings access | Set `vars.API_BASE_URL`, `secrets.CRON_SECRET` | Unknown | — | Document handoff |
| `node` / `gsd-tools.cjs` | Optional planning tooling in this environment | ✓/not required for research output | — | Not needed |

**Missing dependencies with no fallback:**
- None that block producing the in-repo alignment artifacts, matrix, and planning closure notes required by this phase.

**Missing dependencies with fallback:**
- Live provider access and canonical-host execution: fallback is contractual/documented closure with explicit handoff and preserved historical evidence (D-04, D-09, D-14, D-15).

## Validation Architecture

> `workflow.nyquist_validation` is enabled in `.planning/config.json` (key `true`), so this section is included. [VERIFIED: `.planning/config.json`]

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `scripts/verify-deploy.ps1` (operator smoke gate) + repository/document consistency checks (diff/grep/review). No new automated unit test framework introduced by this phase. [VERIFIED: scope + existing gate] |
| Config file | `scripts/verify-deploy.ps1` (parameters: `-FrontendUrl`, `-BackendUrl`, `-CronSecret`/`$env:CRON_SECRET`, `-AllowTestTurnstile`) |
| Quick run command | Targeted consistency checks for aligned artifacts (e.g. grep/read verification that canonical targets appear in state-alvo sections and historical rows unchanged) — define exact commands in plan tasks |
| Full suite command | `powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 -FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com` (when canonical hosts are reachable/configured) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BRND-04 | Canonical branded hosts defined and consistently applied in repo state-alvo (docs/config/examples/scripts) with legacy mapping preserved | manual/document review + scripted smoke (when live) | `scripts/verify-deploy.ps1` checks 1–6,10 against canonical URLs; repo text review of D-05 artifacts + matrix | ✅ gate exists; ❌ canonical execution evidence may be Wave 0/external handoff |
| SECR-12 | `/admin/expire` remains X-Cron-Secret-only fail-closed (401/403/503 as applicable) and documented/mapped to canonical target without T-06-01 drift | smoke/manual evidence mapping | `scripts/verify-deploy.ps1` checks 7–9 (unauth refused/fail-closed, auth idempotent 200 x2, no leak) | ✅ gate exists |
| LIFE-13 | Cron catch-up trigger protected/idempotent and canonical endpoint/ops wiring evidenced or explicitly handed off | smoke/manual evidence mapping | `scripts/verify-deploy.ps1` check 8 (200 + integer `deleted`, twice) and runbook/Actions alignment review | ✅ gate exists |

### Sampling Rate
- **Per task commit:** Review touched D-05/planning files for (a) canonical state-alvo correctness, (b) no historical evidence row rewrites, (c) no secrets added, (d) no runtime code edits.
- **Per wave merge:** Re-read `docs/DEPLOY.md` matrix/mapping + `REQUIREMENTS.md`/`ROADMAP.md` notes for D-04/D-08/D-10/D-12/D-14/D-16 consistency.
- **Phase gate:** D-10 matrix complete with statuses/refs for every check; BRND-04/SECR-12/LIFE-13 closure notes recorded. If canonical hosts executed, `verify-deploy.ps1` all checks passed (or explicitly approved `-AllowTestTurnstile` path) recorded with URLs/results/cold-start.

### Wave 0 Gaps
- [ ] **External/canonical smoke execution evidence** — only creatable by running `scripts/verify-deploy.ps1` against provisioned canonical hosts with correct envs/secrets; if unavailable, record `pendente de execução operacional` + handoff (D-04). Not a repo file gap.
- [ ] **Provider/dashboard alignment** (Vercel domain/env+rebuild, Render env/CORS, Turnstile Hostnames, GitHub Actions vars/secrets) — operational prerequisites outside repo (D-13).

*(No in-repo automated test scaffold gaps identified for this docs/config/evidence phase; existing gate script is present.)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (admin surfaces/login referenced in D-10) | Existing admin JWT auth; Turnstile on login; no changes in this phase (reference/mapping only) [VERIFIED: project state] |
| V3 Session Management | limited | JWT bearer token handling unchanged; phase does not modify session behavior |
| V4 Access Control | yes | Cron endpoint access by `X-Cron-Secret` only, fail-closed; admin routes protected — preserve contract/evidence (SECR-12/LIFE-13) [VERIFIED: REQUIREMENTS, DEPLOY, script checks 7-8] |
| V5 Input Validation | yes (config values) | Strict CORS origin validation (no wildcard/trailing slash/invalid scheme) and prod Turnstile guards in settings; D-07 codifies correct inputs [VERIFIED: `backend/app/core/config.py`] |
| V6 Cryptography | no new crypto | No keys/tokens generated in-repo; secrets remain in env/secret stores only |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Overly permissive or mismatched CORS origin | Spoofing / Elevation (cross-origin abuse) | Single exact origin in `CORS_ORIGINS` (`https://empreganoix.vercel.app`), no wildcard/trailing slash; verify allow/deny preflight (D-07, checks 2-3) [VERIFIED] |
| Cron endpoint exposed without secret / mis-documented auth | Elevation of privilege / Tampering (unauthorized expiry) | Fail-closed behavior, X-Cron-Secret-only (T-06-01), unauth rejection + auth idempotency evidenced (D-10,D-12) [VERIFIED] |
| Secret leakage in docs/logs/artifacts | Information disclosure | No real values in versioned files; gate checks for secret non-leakage (check 9); keep placeholders/examples [VERIFIED: `render.yaml`, script] |
| Turnstile hostname/origin mismatch | Spoofing/repudiation of bot protection effectiveness | Align Turnstile Hostnames with canonical frontend origin; document rebuild when `NEXT_PUBLIC_TURNSTILE_SITE_KEY` changes (D-03,D-13,D-15) [VERIFIED] |
| Stale frontend bundle pointing to wrong API after env change | Tampering with availability/integrity of client-server contract | Rebuild/redeploy on `NEXT_PUBLIC_*` change; verify via smoke gate (D-13) [VERIFIED] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/13-canonical-host-deploy-ops-alignment/13-CONTEXT.md` — locked decisions D-01..D-16, scope, canonical refs [VERIFIED: repo]
- `.planning/REQUIREMENTS.md` — BRND-04/SECR-12/LIFE-13 definitions, current status, split ownership notes [VERIFIED: repo]
- `.planning/STATE.md` — accumulated decisions (deploy local/dev, recorded legacy-host smokes, `NEXT_PUBLIC_*` build-time, `verify-deploy.ps1`) [VERIFIED: repo]
- `.planning/ROADMAP.md` — Phase 13 goal/success criteria/status [VERIFIED: repo]
- `.planning/v1.1-MILESTONE-AUDIT.md` — authoritative gaps (canonical host mismatch, CORS/env/API alignment risk, lifecycle/ops caveats) [VERIFIED: repo]
- `docs/DEPLOY.md` — runbook, check expectations, historical Registro de verificação (2026-11-12 failures, 2026-11-14/15 approvals on legacy hosts) [VERIFIED: repo]
- `scripts/verify-deploy.ps1` — exact smoke checks/parameters/behavior [VERIFIED: repo]
- `render.yaml`, `frontend/vercel.json`, `frontend/.env.example` — versioned deploy/env artifacts [VERIFIED: repo]
- `.github/workflows/expire-cron.yml` — cron catch-up contract (`vars.API_BASE_URL`, `X-Cron-Secret`) [VERIFIED: repo]
- `frontend/lib/api.ts`, `frontend/lib/jobs.ts` — env resolution/build-time vs runtime behavior [VERIFIED: repo]
- `backend/app/main.py`, `backend/app/core/config.py` — CORS wiring and strict origin validation [VERIFIED: repo]
- `.planning/config.json` — `workflow.nyquist_validation: true`, `commit_docs: true` [VERIFIED: repo]

### Secondary (MEDIUM confidence)
- None required; all phase-critical claims grounded in repository artifacts above.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - existing repo tools/artifacts and locked decisions fully define the work.
- Architecture: HIGH - seams (env-driven frontend URLs, settings-driven CORS, parameterized smoke gate) verified in code/config; matrix pattern directly derived from D-08/D-09/D-11.
- Pitfalls: HIGH - drawn from recorded incidents in DEPLOY/STATE (CORS failure, env=dev/test modes, rebuild requirement, host mismatch) and explicit CONTEXT constraints.

**Research date:** 2026-11-15
**Valid until:** 2026-12-15 (stable ops/docs alignment domain; revalidate if provider hostnames/configs or D-05 artifacts change materially)

## RESEARCH COMPLETE

**Phase:** 13 - Canonical Host, Deploy & Ops Alignment (BRND-04 closeout)
**Confidence:** HIGH

### Key Findings
- [x] Phase 13 is contractual ops/docs/config alignment (D-05/D-06): canonical state-alvo must be `https://empreganoix.vercel.app` ↔ `https://empreganoix.onrender.com` while preserving all historical/legacy evidence (notably approved smokes on `empreganoix-six.vercel.app` / `nqu-backend-x60n.onrender.com`).
- [x] No runtime code change is indicated; env-driven seams (`NEXT_PUBLIC_API_URL` build-time, `BACKEND_API_URL` server-side, strict `CORS_ORIGINS` validation) and existing `verify-deploy.ps1` checks already support D-03/D-07/D-10.
- [x] Primary deliverable shape is a `docs/DEPLOY.md` canonical-target + legacy-mapping + D-10 alignment matrix, plus closure/ownership notes in `REQUIREMENTS.md` and `ROADMAP.md` (D-04/D-11/D-12/D-16).
- [x] BRND-04 and the residual ops-evidence ownership for SECR-12/LIFE-13 can close contractually with explicit handoff if canonical-host execution is unavailable (D-04/D-14/D-15), without reopening T-06-01.
- [x] Main risks are evidence-history rewrites, `NEXT_PUBLIC_*` rebuild omission, CORS/Turnstile hostname mismatch, and silent canonical substitution.

### File Created
`.planning/phases/13-canonical-host-deploy-ops-alignment/13-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | Based entirely on in-repo artifacts and locked phase decisions; no new dependencies. |
| Architecture | HIGH | Verified env/config/script seams and direct mapping from D-01..D-16 to concrete files/sections. |
| Pitfalls | HIGH | Grounded in recorded deploy incidents, audit findings, and explicit constraints (rebuild, strict CORS, fail-closed cron, history preservation). |

### Open Questions
- Exact formatting/placement of canonical production guidance in `frontend/.env.example` without reducing local-dev clarity.
- Whether to tweak `.github/workflows/expire-cron.yml` example text (non-secret) beyond DEPLOY/runbook alignment.
- Any minor host-string drift outside D-05 named artifacts (quick grep during planning/execution).
- Whether operator will provision/execute on canonical hosts before closure (defaults to handoff).

### Ready for Planning
Research complete. Planner can now create PLAN.md files.
