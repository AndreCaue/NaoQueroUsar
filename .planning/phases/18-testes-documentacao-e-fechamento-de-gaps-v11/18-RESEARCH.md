# Phase 18: Testes, Documentação e Fechamento de Gaps v1.1 - Research

**Researched:** 2026-11-16
**Domain:** QA/evidence closure for Facebook social integration + v1.1 audit gap reconciliation (FastAPI/Next.js/Postgres, pytest, docs/runbooks)
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Adotar estratégia **híbrida: validar e corrigir lacunas reais**. Para cada requisito/lacuna auditada, comparar comportamento e código/testes atuais; implementar correção pontual quando faltar comportamento/aceite; quando já estiver atendido, produzir evidência rastreável e atualizar status/artefatos de forma coerente com a realidade.
- **D-02:** Tratar bloqueios de evidência de forma **reprodutível no repositório + handoffs explícitos**: criar/setup documentado e reproduzível para DB de testes com migrações (permitindo rodar suites DB-backed localmente e, quando viável, em CI), registrar evidências do que for executado neste ambiente, e manter smoke canônico e verificações humanas/browser como **handoff operacional** com checklist, comandos e critérios objetivos.
- **D-03:** Tratar a lacuna do artefato da Fase 11 com **backfill de `11-VERIFICATION.md` na própria Fase 11** (`.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-VERIFICATION.md`), consolidando evidências rastreáveis já existentes (plans/summaries, verificações 07/08/12/13 e artefatos correlatos) e atualizando verificações/traceability relacionadas quando necessário (incluindo caveats de 07/08).
- **D-04:** Prioridade/ordem de execução: **(1)** fechar EXTR/PUBL/SRCH/UIUX e lacunas verificáveis localmente com código + testes + artefatos; **(2)** backfill de `11-VERIFICATION.md` e tratamento dos caveats 07/08; **(3)** preparar DB de testes reprodutível e registrar handoffs canônicos/humanos com critérios objetivos. Critério de fechamento: marcar requisito/lacuna como **fechado/validado** somente com evidência disponível; quando depender de runtime/infra/credenciais indisponíveis aqui (ex.: smoke no host canônico, validação browser humana, app/página Meta real), registrar como **evidência parcial + handoff rastreável** com status explícito, passos e critérios de aceite.
- **D-05:** Estas áreas estão no escopo da fase (ROADMAP/REQUIREMENTS), mas **não foram detalhadas na discussão**. O planejador/pesquisador deve derivar a abordagem concreta a partir dos requisitos, do código/testes/docs existentes e das decisões D-01..D-04: cobrir geração/classificação/backoff, OAuth/publicação com Graph API mockada e concorrência/idempotência do worker sem chamadas reais em CI; produzir roteiro manual Meta em modo dev e documentação operacional (setup Meta, envs, cron Render, checklist App Review/modo Live, alinhamento de `.env.example`/docs). Reutilizar e estender a base existente (`backend/tests`, `docs/DEPLOY.md`, `scripts/verify-deploy.ps1`, `.github/workflows`) sempre que adequado.

### OpenCode's Discretion
- Forma exata do setup reprodutível de DB de testes/migrações (ex.: script, compose/serviço local, instruções de `alembic upgrade`, fixtures/config de pytest, integração com CI) desde que reproduzível, documentado e sem exigir segredos reais.
- Estrutura, localização e granularidade dos artefatos de evidência/reconciliação (além do backfill obrigatório de `11-VERIFICATION.md` na Fase 11), formato de atualização de status em `REQUIREMENTS.md`/`STATE.md`/verificações e nível de detalhe dos checklists/handoffs.
- Nível e organização dos testes TEST-01..03 e do roteiro/documentação TEST-04/DOC-01, desde que atendam aos critérios de sucesso e não dependam de chamadas reais em CI.
- Necessidade e escopo de correções de código pontuais para tornar requisitos/evidências verdadeiros, preservando contratos existentes e evitando mudanças fora do escopo da fase.

### Deferred Ideas (OUT OF SCOPE)
- Execução operacional real em hosts canônicos (provisionamento/smoke `scripts/verify-deploy.ps1` no state-alvo), validações humanas/browser completas e testes com app/página Meta reais/credenciais de produção: permanecem como handoffs quando o ambiente/credenciais não estiverem disponíveis nesta sessão, com evidência e critérios registrados (dentro de AUD-05/DOC-01/TEST-04, não como novas capacidades).
- Novas capacidades fora do milestone (Instagram, múltiplas páginas/admins, métricas, sync edição/remoção, imagem em post): fora de escopo.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-01 | Testes unitários cobrem geração de texto (LLM mockado), classificação de erros e cálculo de backoff | Existing `test_social_post_generation.py`, `test_social_post_policy.py`, `test_social_retry_policy.py`, `test_facebook_publisher.py` and `publish_pipeline.compute_next_retry/_classify_failure`; extend gaps with explicit LLM-mocked generation and classification/backoff assertions per requirement wording |
| TEST-02 | Testes de integração cobrem `FacebookPublisher` e OAuth com Graph API mockada (sem chamadas reais em CI) | Existing `test_facebook_publisher.py` (mocked httpx) and `test_meta_oauth_*`/`test_integrations_api.py`; verify completeness, ensure no network calls, add missing cases/contracts if any |
| TEST-03 | Testes de concorrência do worker (`SKIP LOCKED`) e idempotência (sem duplicatas) | Existing `test_social_worker_claim.py`, `test_social_idempotency.py`, `test_social_publish_pipeline.py`; add/strengthen concurrent claim scenarios and duplicate-prevention proofs as feasible (DB-backed or controlled concurrency simulation) |
| TEST-04 | Roteiro de teste manual documentado para Página real com app Meta em modo desenvolvimento | Produce runbook/checklist (likely `docs/` or `.planning/phases/18-...`) covering dev-mode Meta app/page prerequisites, OAuth connect, draft/review/publish-now/schedule/retry flows, expected UI/API states, safety limits |
| DOC-01 | Documentação inclui setup do app Meta, variáveis de ambiente, configuração do cron no Render (novo ou reaproveitado) e checklist de App Review/modo Live | Align/extend `docs/DEPLOY.md`, `backend/.env.example`, `frontend/.env.example`, and add dedicated Meta/App Review/cron operational doc(s) + checklist; preserve secret-safety |
| AUD-01 | Fechar/validar requisitos de extração EXTR-10/11/12 com evidência verificável | Compare implementation/tests in `backend/app/api/v1/extract.py`/extractor/core/config and existing suites; fix if missing, else collect evidence and reconcile status |
| AUD-02 | Fechar/validar requisitos públicos PUBL-10/11/12/13/14 com evidência | Audit frontend public board/modal/reveal and backend public/reveal/report APIs + tests; reconcile with prior 07 gaps (PUBL-13) |
| AUD-03 | Fechar/validar requisitos de busca/filtro/ordenação SRCH-10/11/12 com evidência | Audit `public` API query/search/filter/sort behavior and frontend URL/state plumbing + tests |
| AUD-04 | Fechar/validar requisitos de UI/tema/ads UIUX-10/11/12 com evidência | Audit theme/tokens/contrast, Doações button, AdSlot placement/reservation in frontend with static evidence/human checklist as needed |
| AUD-05 | Resolver lacunas de verificação/evidência v1.1 aceitas (11-VERIFICATION/equivalente, caveats 07/08, handoffs DB/human/browser/canônicos) com artefatos e rastreabilidade | Backfill `11-VERIFICATION.md` in Phase 11, update 07/08 caveat context where appropriate, create reproducible DB test setup docs/artifacts, produce explicit handoff checklists for canonical smoke/human/browser/Meta-real with objective criteria |
</phase_requirements>

## Summary

Phase 18 is primarily a **verification, evidence, and documentation closure** phase (not net-new product scope), executed under a hybrid strategy (D-01): validate reality, patch only proven gaps, and produce auditable artifacts/status updates. The repo already contains substantial implementation and tests for the v1.2 Facebook flow (OAuth, draft generation, async publish pipeline with `FOR UPDATE SKIP LOCKED`, retry/backoff/idempotency, admin status/retry UI) and operational docs/gates (`docs/DEPLOY.md`, `scripts/verify-deploy.ps1`). The main risks are (a) **evidence debt** (missing `11-VERIFICATION.md`, env-blocked DB-backed suites, human/browser/canonical runtime checks), (b) **requirements/traceability drift** (PUB-01..08 still Pending in `REQUIREMENTS.md` despite Phase 17 completion artifacts; v1.1 EXTR/PUBL/SRCH/UIUX unchecked), and (c) **DB reproducibility** required by D-02.

**Primary recommendation:** Plan as 3-4 waves aligned to D-04: (1) local-verifiable gap closure for EXTR/PUBL/SRCH/UIUX + TEST-01..03 hardening using existing backend/frontend tests/mocks; (2) evidence/traceability backfill (`11-VERIFICATION.md` in Phase 11, reconcile 07/08 caveats and REQUIREMENTS/STATE/ROADMAP statuses with proof); (3) reproducible DB test workflow + TEST-04/DOC-01 operational manuals/checklists and explicit handoffs for runtime/credential-dependent checks. Never mark closed without evidence; use "partial + handoff rastreável" for unavailable runtime.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Social text generation/classification/backoff correctness | API / Backend | — | Logic in `backend/app/services/social/*` and config-driven retry policy; unit/integration-testable with mocks |
| OAuth Meta + Facebook publishing (Graph API) | API / Backend | External (Meta Graph API, mocked in CI) | Backend owns tokens/crypto/calls; CI must mock external HTTP |
| Worker claim, retry, idempotency, fire-and-forget safety | Database / Storage + API / Backend | — | Postgres row locks/constraints + async pipeline/CRUD enforce semantics |
| Admin social status/retry UX and public site behavior | Frontend Server (SSR)/Client | API / Backend | Next.js surfaces consume backend contracts; some UX acceptance remains human/browser |
| DB-backed test reproducibility | Developer Tooling / CI | Database / Storage | Alembic migrations + test DB config + documented commands/scripts enable evidence runs |
| Canonical deploy/cron/App Review operational proof | External Ops (Render/Vercel/GitHub/Meta) | — | Runtime/credentials/hosts required; produce handoff/checklists when unavailable |

## Project Constraints (from AGENTS.md)

- **Stack fixed:** Next.js 16 (App Router) + Tailwind, FastAPI (Python async), Neon Postgres, Groq, Cloudflare Turnstile, Vercel + Railway/Render. [VERIFIED: `AGENTS.md`, `.planning/PROJECT.md`]
- **pt-BR/locale and UX constraints:** dark minimal purple theme; Doações `#facc15`; mobile-first public flow. [VERIFIED: `AGENTS.md`]
- **Core value/non-regression:** no login/cadastro friction for public job/contact access; social failures must not block site publication; secrets/tokens backend-only and encrypted in logs/UI avoidance patterns. [VERIFIED: `AGENTS.md`, `PROJECT.md`, Phase 17 artifacts]
- **Preserve contracts:** e.g. T-06-01 `/admin/expire` only `X-Cron-Secret` fail-closed/idempotent; canonical-vs-legacy host distinction in `docs/DEPLOY.md`. [VERIFIED: `docs/DEPLOY.md`, `scripts/verify-deploy.ps1`, audit/phase 12-13]
- **GSD workflow rule present in AGENTS:** normally file-changing work goes through GSD commands; this session is a read/write research deliverable per orchestrator objective — follow orchestrator scope. [ASSUMED: interpret as applicable to implementation, not this spawned research write]

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| Python | 3.11+ (project requires `>=3.11`) | Backend runtime/tests | Matches `backend/pyproject.toml` | HIGH [VERIFIED: `backend/pyproject.toml`] |
| FastAPI | 0.143.0 | Backend API | Project standard | HIGH [VERIFIED] |
| SQLAlchemy (async) + asyncpg + Alembic | 2.1.4 / 0.32.0 / 1.20.0 | ORM, driver, migrations | Existing DB-backed tests and schema evolution | HIGH [VERIFIED] |
| pytest + pytest-asyncio + httpx | 9.1.1 / >=1.0,<2.0 / 0.28.1 | Automated tests (unit/integration/ASGI/mocks) | Entire backend suite and conftest built on this | HIGH [VERIFIED] |
| Next.js / React / TypeScript / Tailwind | 16.x / 19.x / 7.x / 4.x (per stack docs) | Frontend/admin/public UI | Project standard | MEDIUM [CITED: `AGENTS.md` stack section; not revalidated from package manifests in this pass] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| APScheduler | 3.10.4 | In-process expiry scheduling patterns/reference | Not new in Phase 18; preserve behavior, document cron interplay |
| cryptography (Fernet) | 50.0.2 | Social token encryption tests/setup | Use generated test keys only (no real secrets) |
| `uv` / `python -m pytest` from `backend/.venv` | project-managed | Consistent test execution | Prefer repo-local venv commands already used in artifacts |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Postgres (real, migrated) for DB-backed tests | SQLite/mocks for all DB paths | SQLite misses Postgres-specific locking/`SKIP LOCKED`/constraints; D-02 and prior blockers require real migrated schema evidence where applicable |
| Local script/docs for DB setup | Mandatory CI job in this phase | CI integration is good if low-risk, but must not depend on secrets; local reproducibility is the locked minimum |

**Installation:**
```bash
# From backend/ (existing project)
uv sync --group dev
# or use existing venv: .\.venv\Scripts\python.exe -m pytest -q
```
[VERIFIED: `backend/pyproject.toml`, existing `.venv`/test commands in verification artifacts]

**Version verification:** Not run against registries in this session (no `npm view`/`pip index` checks executed). Versions above reflect repo declarations/artifacts. [ASSUMED]

## Architecture Patterns

### System Architecture Diagram

```mermaid
flowchart LR
  A[Admin UI / Review + Integrações] -->|JWT-protected API calls| B[FastAPI /admin + /integrations]
  B --> C[Services: draft generation, Meta OAuth, publish pipeline]
  C --> D[(Postgres: jobs, social_accounts, social_posts, social_post_logs)]
  C -->|Graph API calls mocked in tests| E[Meta Graph API (external, runtime only)]
  F[GitHub Actions / Render Cron] -->|X-Cron-Secret| G[/admin/expire + /admin/social/worker]
  G --> C
  H[Public SSR/Client] -->|read-only/search/reveal/report| I[FastAPI /public APIs]
  I --> D
  J[Test Runner: pytest + ASGI/httpx mocks] --> B
  J --> C
  J -->|migrated TEST DB required for DB-backed suites| D
  K[Docs/Gates: DEPLOY.md, .env.example, verify-deploy.ps1] --> F
  K --> H
```

### Recommended Project Structure
```
.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/
  11-VERIFICATION.md                 # D-03 backfill target (evidence consolidation)
.planning/phases/18-.../
  18-RESEARCH.md
  18-VERIFICATION.md (planned)       # phase evidence/status reconciliation
  EVIDENCE/ or notes (discretion)     # command outputs, checklists, handoffs
docs/
  DEPLOY.md                          # extend operational alignment (DOC-01/AUD-05)
  META-INTEGRATION.md (candidate)    # Meta setup/App Review/Live/teste manual
backend/
  .env.example                       # align env docs
  scripts/ (optional)                # reproducible test DB bootstrap helpers
  tests/                             # extend TEST-01..03 and fix real gaps
frontend/
  .env.example                       # align public/frontend vars
scripts/
  verify-deploy.ps1                  # keep canonical smoke gate/handoff refs
```
[ASSUMED: exact file names/locations except D-03-mandated `11-VERIFICATION.md`; choose for traceability and minimal churn]

### Pattern 1: Evidence-First Hybrid Closure (D-01/D-04)
**What:** For each audited requirement/test/doc item: inventory existing behavior+tests -> classify (satisfied / gap / env-blocked) -> implement minimal fix if gap -> capture evidence artifact -> update status/traceability.
**When to use:** AUD-01..05, TEST-01..03 validation, reconciliation tasks.
**Example:**
```markdown
| Item | Current behavior/test evidence | Gap? | Action | Evidence path | Status |
|------|-------------------------------|------|--------|---------------|--------|
| EXTR-10 | `extract.py` chunks <= cap; `test_extractor.py` passes | no | cite tests/code | 18 evidence note | validated |
| 11 artifact | missing `11-VERIFICATION.md` | yes | backfill in Phase 11 | phase 11 file | validated |
```
[CITED: D-01/D-04, `.planning/milestones/v1.1-MILESTONE-AUDIT.md`, existing phase verification patterns]

### Pattern 2: Reproducible DB-Backed Test Evidence (D-02)
**What:** Document and (optionally) script a local Postgres test DB flow using Alembic migrations so DB-dependent suites (`test_reveal_api.py`, `test_admin_jobs.py`, `test_extract_api.py`, social DB suites, etc.) can run deterministically without real secrets.
**When to use:** Any claim of "DB-backed suite verified" and closure of repeated `relation "jobs" does not exist` blockers.
**Example:**
```powershell
# backend/
$env:TEST_DATABASE_URL="postgresql+asyncpg://USER:PASS@HOST:PORT/empreganoix_test?ssl=require"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest -q tests/test_reveal_api.py tests/test_admin_jobs.py tests/test_extract_api.py
```
[VERIFIED pattern basis: `backend/tests/conftest.py` resolves `TEST_DATABASE_URL`/`DATABASE_URL` and clears `jobs`; `backend/alembic/env.py` reads `settings.DATABASE_URL`; prior blockers in 07/08/12/17 verifications]

### Pattern 3: External APIs Mocked in CI (TEST-01..03)
**What:** Use ASGI/httpx mocking/fakes and injected publishers/verifiers for Groq/Graph/Turnstile paths; never perform real Meta/Groq/Cloudflare calls in automated tests.
**When to use:** All social OAuth/publish/generation and worker tests.
**Example:**
```python
# Existing style: monkeypatch/httpx mock transports or FakeTurnstileVerifier, injected publisher
result = await FacebookPublisher().publish(payload)  # against mocked client
assert result.ok and result.external_post_id
```
[VERIFIED: `backend/tests/conftest.py` `FakeTurnstileVerifier`, `backend/tests/test_facebook_publisher.py`, `test_social_publish_pipeline.py`, `test_meta_oauth_*`]

### Anti-Patterns to Avoid
- **"Closed in docs only" without comparing runtime behavior:** violates D-01; reconcile with code/tests or mark partial+handoff.
- **Claiming DB-backed pass without migrated schema evidence:** prior audit repeatedly blocked by missing `jobs` relation.
- **Real external calls/credentials in CI:** explicitly forbidden by TEST-01..03; keep mocks/fakes and env placeholders.
- **Reopening preserved contracts:** do not change `/admin/expire` auth semantics (T-06-01), fire-and-forget social behavior, or canonical-vs-legacy host truth model.
- **Silent canonical-host "success":** if not executed, record `pendente de execução operacional`/handoff with criteria (Phase 13/DEPLOY pattern).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DB schema setup for tests | Ad-hoc SQL files diverging from app | Alembic migrations (`alembic upgrade head`) + existing models/env wiring | Keeps test DB aligned with production schema and lock/index semantics |
| HTTP API mocking | Custom network stubs hitting real endpoints | `httpx` mocking/ASGI transport, monkeypatch, existing fakes/fixtures | Deterministic, offline, CI-safe |
| Concurrent claim/idempotency guarantees | In-memory locks | Postgres `FOR UPDATE SKIP LOCKED` + unique constraints/indexes already modeled | Correctness under cron/retry concurrency |
| Secret handling in docs/tests | Hardcoded tokens/keys | `.env.example` placeholders, generated Fernet keys in tests, env vars | Prevents leakage and keeps reproducibility |
| Smoke verification | Manual ad-hoc curl notes only | `scripts/verify-deploy.ps1` + DEPLOY matrix/checklists | Repeatable, mapped evidence/handoff format |

**Key insight:** Phase 18 value is **trustworthy evidence and operability**, not bespoke frameworks; reuse existing tests, contracts, and runbooks.

## Runtime State Inventory

> Omitted — not a rename/refactor/migration phase.

## Common Pitfalls

### Pitfall 1: DB-backed suites "blocked by environment" forever
**What goes wrong:** `pytest` fails during fixture setup (`relation "jobs" does not exist`) so AUD/TEST claims remain partial.
**Why it happens:** `conftest.py` expects `TEST_DATABASE_URL`/`DATABASE_URL` pointing to a DB with migrations applied; no repo-level bootstrap/evidence path recorded.
**How to avoid:** Implement D-02 concretely (documented command sequence and/or helper script, optional dockerized/local Postgres instructions), run feasible subsets, capture outputs; if CI DB unavailable, still provide local reproducible path + explicit CI note.
**Warning signs:** Verification artifacts repeat "env-blocked" without new setup artifacts. [VERIFIED: 07/08/12/17-02, STATE.md]

### Pitfall 2: Traceability drift after implementation
**What goes wrong:** Code/tests/docs exist but `REQUIREMENTS.md`/phase verifications/STATE remain Pending/unchecked or contradictory.
**Why it happens:** Phase 17 completed but PUB-01..08 and UI traceability not fully reconciled in requirements table; v1.1 audit items long-lived.
**How to avoid:** Include an explicit reconciliation task (update statuses with evidence pointers, note split ownership/handoffs), and backfill `11-VERIFICATION.md` in correct location (D-03).
**Warning signs:** "Complete" in summaries but `[ ] Pending` in `REQUIREMENTS.md`. [VERIFIED: `REQUIREMENTS.md`, `17-VERIFICATION.md`, `STATE.md`]

### Pitfall 3: Flaky/non-deterministic concurrency tests
**What goes wrong:** `SKIP LOCKED`/idempotency tests pass locally but are timing-sensitive or accidentally hit real DB/network.
**Why it happens:** Improper session/transaction control or reliance on wall-clock/network.
**How to avoid:** Use controlled DB transactions/fixtures, deterministic task orchestration, mocked publisher delays/time where needed, and assert state transitions/logs/idempotent outcomes.
**Warning signs:** Sleeps, real Graph calls, non-isolated records.

### Pitfall 4: Documentation implies live Meta/cron success without credentials
**What goes wrong:** DOC-01/TEST-04 read as "validated in production" but no real app/page/cron evidence exists.
**Why it happens:** Conflating runbook completeness with execution.
**How to avoid:** Separate "configured/documented" from "executed"; provide manual roteiro + objective acceptance checklist and mark runtime steps as handoff when not run (D-04).
**Warning signs:** Missing prerequisites/expected screenshots/log fields/rollback notes.

### Pitfall 5: Evidence touches secrets or weakens safety
**What goes wrong:** Tokens, `CRON_SECRET`, decrypted page tokens, or raw Meta payloads appear in artifacts/logs/examples.
**Why it happens:** Copy-paste from live debugging.
**How to avoid:** Use placeholders/redaction, rely on existing sanitization (`publish_pipeline` logs safe summaries/messages), review docs/examples for secret-free content.
**Warning signs:** Real-looking IDs/tokens/headers in markdown or committed test outputs.

## Code Examples

### DB-independent social unit test pattern (no DB required)
```python
# Source: backend/tests/conftest.py (collection behavior) [VERIFIED]
# Files in db_independent set run even when TEST_DATABASE_URL is unset:
# test_social_post_generation.py, test_social_post_policy.py, test_facebook_publisher.py,
# test_social_retry_policy.py, test_social_idempotency.py, test_social_publish_pipeline.py, ...
```

### Offline ASGI + fakes for protected/admin flows
```python
# Source pattern: backend/tests/conftest.py [VERIFIED]
async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
    res = await ac.post("/api/v1/admin/social/worker", headers=cron_secret_header)
assert res.status_code == 200
```

### Mocked Graph publish (no real network)
```python
# Source pattern: backend/app/services/social/facebook.py + backend/tests/test_facebook_publisher.py [VERIFIED]
# Use monkeypatched httpx.AsyncClient.post to return {"id": "123_456"} / error bodies
# Assert payload contains message/link/access_token usage only in-memory, and result categories/messages are safe
```

### Reproducible migrations for evidence (proposed command)
```powershell
# backend/ — requires a reachable Postgres TEST_DATABASE_URL (no real secrets committed)
$env:DATABASE_URL=$env:TEST_DATABASE_URL
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest -q
```
[ASSUMED: exact env wiring depends on helper/script chosen; must be documented and tested in-phase]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Unverified/missing phase artifacts (07/08/11 gaps) | Evidence-first VERIFICATION artifacts with explicit caveats/handoffs | Phases 11-13, carried into 18 | Phase 18 must consolidate, not regress traceability |
| Synchronous assumptions / env-blocked DB tests | Reproducible migrated test DB + recorded evidence (D-02) | Phase 18 target | Enables closure of long-standing audit debt |
| Implicit cron/auth behavior | Explicit protected endpoints/contracts (`X-Cron-Secret`, `verify-deploy.ps1`, DEPLOY matrix) | v1.1/v1.2 ops hardening | Docs/tests must stay aligned to preserved contracts |

**Deprecated/outdated:**
- Treating "PASS on legacy/non-canonical host" as canonical closure without mapping: keep historical evidence mapped, but follow DEPLOY state-alvo/handoff model. [VERIFIED: `docs/DEPLOY.md`, Phase 13]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Frontend has no existing automated test suite/config requiring Phase 18 changes; evidence will be mostly static code inspection + manual/browser handoff unless gaps demand lightweight tests | Architecture/Validation | May need to add FE test tooling if AUD-04/PUBL/SRCH/UIUX cannot be evidenced credibly |
| A2 | Exact placement/naming of new docs (e.g. Meta ops guide/manual roteiro) is discretionary if discoverable and aligned with `docs/` and phase artifacts | Standard Stack/Patterns | Planner may pick different paths; low impact if traceable |
| A3 | A local/hosted Postgres instance is available to the executor/operator for D-02 evidence runs in this environment (or can be provisioned without secrets committed) | Pitfalls/Validation | DB-backed closure may remain "partial + handoff" despite reproducible instructions |
| A4 | Current implementation already satisfies some/most EXTR-10..12, PUBL/SRCH/UIUX behaviors; Phase 18 should start by auditing before coding (D-01) | Phase Requirements | Unnecessary churn if assumed true, or missed fixes if assumed false without audit |

## Open Questions

1. **Actual satisfaction status of EXTR-10/11/12 and PUBL/SRCH/UIUX acceptance**
   - What we know: v1.1 audit marked them unsatisfied/unverified in audited scope; codebase evolved since then. [VERIFIED: audit]
   - What's unclear: Which specific acceptance criteria remain unmet today vs only lacking evidence artifacts.
   - Recommendation: First plan task per cluster is a targeted audit matrix (code + existing tests + quick command/static checks) producing fix list or evidence bundle.

2. **CI capability for Postgres-backed tests**
   - What we know: No dedicated backend test CI workflow found (only `expire-cron.yml`); pytest/conftest supports DB-backed runs. [VERIFIED: `.github/workflows/`, `backend/tests/conftest.py`]
   - What's unclear: Whether adding CI service (e.g. Postgres) is in-scope/low-risk in this phase.
   - Recommendation: Prioritize local reproducible setup + docs (must-have). Add CI job only if straightforward and secret-free; otherwise document handoff.

3. **PUB-01..08/UI-01..02 traceability reconciliation extent**
   - What we know: Phase 17/17-VERIFICATION reports implementation and 12/12 must-haves verified (human_needed for runtime), but `REQUIREMENTS.md` still lists PUB-01..08 Pending. [VERIFIED]
   - What's unclear: Whether to mark complete based on automated/static evidence or partial pending operational UAT.
   - Recommendation: Reconcile using honest status model (complete where criteria met with evidence, else partial with explicit note) consistent with D-04 and existing docs.

4. **Meta dev-mode/manual test feasibility in-session**
   - What we know: TEST-04 requires documented manual roteiro for real Page/app in dev mode; credentials/runtime likely unavailable. [CITED: requirements/context]
   - What's unclear: Any sandbox credentials available?
   - Recommendation: Produce high-quality roteiro/checklist and capture as handoff with prerequisites/expected outcomes; do not fabricate execution evidence.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js / npm | Frontend inspection/build checks (if needed) | ✓ | Node v24.14.1, npm 11.12.1 | — [VERIFIED: local probe] |
| Python | Backend tests/tooling | ✓ | Python 3.14.4 | Use `backend/.venv` interpreter for project deps [VERIFIED: local probe + repo `.venv`] |
| `uv` | Reproducible backend env sync | ✓ | uv 0.11.6 | `pip`/venv fallback if documented [VERIFIED: local probe] |
| Git | Evidence/commits/inspection | ✓ | git 2.53.0 | — [VERIFIED] |
| `psql` client | Manual DB setup/debug | ✗ | — | Use GUI client, hosted console, or SQLAlchemy/Alembic-only flows; document alternatives |
| Docker | Optional local Postgres for D-02 | ✗ | — | Use existing/local Postgres or Neon test branch/DB; provide instructions, not hard dependency |
| `gh` (GitHub CLI) | Workflow/ops convenience | ✗ | — | Browser/API/manual GitHub Actions UI |
| Reachable migrated Postgres test DB | DB-backed pytest suites, migration verification | ? | — | **Blocking for "executed green" DB evidence**; unblocks via configured `TEST_DATABASE_URL` + `alembic upgrade head` (handoff if unavailable) [VERIFIED need: conftest/alembic/prior blockers] |
| Meta app/Page dev credentials + Graph access | Live TEST-04 execution, App Review live checks | ? | — | Documented manual roteiro + handoff (no real calls in CI) |

**Missing dependencies with no fallback:**
- None strictly code-blocking for writing plans/research; **DB-backed execution evidence** is blocked until a migrated test DB is available.

**Missing dependencies with fallback:**
- `psql`/Docker/`gh`: alternative tooling or manual steps.
- Live Meta/canonical hosts: operational handoffs with objective criteria (D-02/D-04).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-asyncio (auto) |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_social_publish_pipeline.py tests/test_social_idempotency.py tests/test_facebook_publisher.py` (or targeted subset) |
| Full suite command | `cd backend; .\.venv\Scripts\python.exe -m pytest -q` (DB-backed subsets require migrated `TEST_DATABASE_URL`/`DATABASE_URL`) |

[VERIFIED: `backend/pyproject.toml`, `backend/tests/conftest.py`]

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-01 | Geração texto (LLM mockado), classificação erros, cálculo backoff | unit | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_social_post_generation.py tests/test_facebook_publisher.py tests/test_social_retry_policy.py tests/test_social_publish_pipeline.py` | ✅ (review/extend for explicit coverage wording) |
| TEST-02 | `FacebookPublisher` e OAuth com Graph API mockada | integration (ASGI/mocked HTTP) | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_facebook_publisher.py tests/test_meta_oauth_flow.py tests/test_meta_oauth_security.py tests/test_meta_oauth_validation.py tests/test_integrations_api.py` | ✅ (verify no real calls, fill gaps) |
| TEST-03 | Concorrência worker (`SKIP LOCKED`) e idempotência sem duplicatas | integration/concurrency (DB-backed where needed) | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_social_worker_claim.py tests/test_social_idempotency.py tests/test_social_publish_pipeline.py` | ✅ (may need migrated DB / stronger concurrency case) |
| TEST-04 | Roteiro manual Meta dev | manual | N/A (documented checklist) | ❌ Wave 0 (create doc/roteiro) |
| DOC-01 | Docs operacionais Meta/env/cron/App Review + alinhamento `.env.example` | manual/static verification | `git diff -- backend/.env.example frontend/.env.example docs/* scripts/verify-deploy.ps1` + checklist review | ❌ Wave 0 (new/updated docs) |
| AUD-01 | EXTR-10/11/12 evidência/fechamento | mixed (unit/integration/static) | Targeted: `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_extractor.py tests/test_extract_api.py tests/test_extraction_core.py -k "chunk or contact or fallback"` (adjust to actual names) + code audit | ✅/❓ (confirm coverage per req) |
| AUD-02 | PUBL-10..14 evidência | mixed (API/FE/manual) | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_public_api.py tests/test_reveal_api.py tests/test_report_api.py` + FE inspection | ✅ (DB-backed/human gaps possible) |
| AUD-03 | SRCH-10..12 evidência | mixed | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_public_search.py` + FE query-state inspection | ✅/❓ |
| AUD-04 | UIUX-10..12 evidência | manual/static (+ optional FE tests) | Static review of `frontend/app/(public)/*`, styles/tokens/components; contrast/placement checklist | ❓ (likely manual evidence) |
| AUD-05 | 11-VERIFICATION backfill + 07/08 caveats + DB/human/canonical handoffs | manual/artifact verification | `Test-Path .planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-VERIFICATION.md` + diff/status checks + evidence docs | ❌ Wave 0 (`11-VERIFICATION.md`, handoff/DB docs) |

### Sampling Rate
- **Per task commit:** Run smallest relevant targeted subset (unit/offline first; DB-backed only when env ready) from `backend/`
- **Per wave merge:** Re-run all tests/artifact checks claimed as evidence in that wave; record skips/blockers explicitly
- **Phase gate:** All claimed automated checks green or explicitly documented as env-blocked/manual with evidence/handoff before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-VERIFICATION.md` — backfill consolidating Phase 11 evidence (D-03, AUD-05)
- [ ] Reproducible DB test setup artifact(s): e.g. `backend/scripts/setup-test-db.ps1` or `docs/TESTING.md`/section in DEPLOY with `TEST_DATABASE_URL` + `alembic upgrade head` + pytest commands (D-02, AUD-05)
- [ ] Manual Meta dev-mode roteiro (TEST-04) — new doc/checklist
- [ ] Operational Meta/App Review/Live/cron/env alignment doc updates (DOC-01)
- [ ] Evidence matrix/checklist artifacts for EXTR/PUBL/SRCH/UIUX and 07/08 caveats reconciliation (AUD-01..05)
- [ ] Optional CI test workflow/job with Postgres service — only if feasible and secret-free (discretion)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing admin JWT + cron `X-Cron-Secret`/`require_cron_secret`; preserve fail-closed (T-06-01) |
| V3 Session Management | partial | Admin token/session handling in frontend; verify no regression in evidence/UI checks |
| V4 Access Control | yes | `require_admin`/`require_cron_secret` on sensitive endpoints incl. social worker/status/retry/integrations |
| V5 Input Validation | yes | Pydantic schemas, FastAPI validation, safe error mapping (pt-BR), no raw payload leakage |
| V6 Cryptography | yes | Fernet-encrypted page tokens at rest (`SOCIAL_TOKEN_ENCRYPTION_KEY`), backend-only decryption in memory |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Token/secret leakage in logs/docs/tests | Information Disclosure | Never log tokens; use placeholders/generated keys; sanitize `last_error`/logs (existing pipeline pattern) |
| Forged cron/worker invocation | Spoofing/Elevation of Privilege | `X-Cron-Secret` only, fail-closed/503-401 semantics preserved; idempotent operations |
| Duplicate social posts on retries/concurrency | Tampering/Integrity | `FOR UPDATE SKIP LOCKED`, idempotency guards, unique `(job_id, provider)`, external_post_id checks |
| CSRF/state issues in OAuth callback | Spoofing | Signed/validated state and safe redirects (existing Meta OAuth flow) |
| Public contact/scraping leakage regressions | Information Disclosure | Keep contact reveal gated and public payloads contact-free; validate in AUD-02 evidence |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-CONTEXT.md` — locked decisions D-01..D-05, discretion, deferred [VERIFIED]
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` (Phase 18 section), `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/milestones/v1.1-MILESTONE-AUDIT.md` — scope, reqs, gaps, current state [VERIFIED]
- Phase artifacts: `07-VERIFICATION.md`, `08-VERIFICATION.md`, `11-CONTEXT.md`, `11-VALIDATION.md`, `12-VERIFICATION.md`, `13-VERIFICATION.md`, `17-CONTEXT.md`, `17-VERIFICATION.md` [VERIFIED]
- Repo implementation/docs: `docs/DEPLOY.md`, `scripts/verify-deploy.ps1`, `.github/workflows/expire-cron.yml`, `backend/.env.example`, `frontend/.env.example` [VERIFIED]
- Backend code/tests: `backend/tests/*` (esp. social/meta/publish/retry/idempotency/admin/public/reveal/expiry), `backend/app/services/social/*`, `backend/app/api/v1/admin.py`, `backend/app/api/v1/integrations.py`, `backend/app/core/config.py`, `backend/app/core/scheduler.py`, `backend/app/crud/social_posts.py`, `backend/app/schemas/social_posts.py`, `backend/app/models/*`, `backend/alembic/*`, `backend/tests/conftest.py`, `backend/pyproject.toml` [VERIFIED]
- Frontend surfaces: `frontend/lib/api.ts`, `frontend/app/admin/review/EditJobDialog.tsx`, `frontend/app/admin/social-posts/*`, `frontend/app/(public)/*` [VERIFIED]

### Secondary (MEDIUM confidence)
- `AGENTS.md` embedded stack/architecture notes for package intent (not revalidated against manifests/registries in this pass) [CITED]

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - derived from repo manifests/configs and existing test/tooling [VERIFIED]
- Architecture: HIGH - derived from current codebase structure and phase contracts [VERIFIED]
- Pitfalls: MEDIUM-HIGH - grounded in recorded blockers/audit and known concurrency/test patterns, but some execution details (CI/DB provisioning) are environment-dependent [VERIFIED + ASSUMED]

**Research date:** 2026-11-16
**Valid until:** 2026-12-16 (stable internal codebase/contracts; recheck if social pipeline, requirements traceability, or CI/test infra changes)
