# Phase 32: Hardening, Regression & Operations - Research

**Researched:** 2026-11-26
**Domain:** Test hardening/regression, operational documentation, validation evidence handoff (Instagram/Facebook social publish)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Regressão Facebook (gate de não-regressão)
- **D-01:** Artefato principal = **estender testes atuais** (`backend/tests/test_facebook_publisher.py`, `backend/tests/test_social_publish_pipeline.py` e outros testes FB/sociais relevantes) com casos explícitos de regressão/contrato FB, reaproveitando padrões existentes. Não criar suíte paralela de snapshot desconectada sem necessidade.
- **D-02:** Escopo do gate = **ciclo completo FB**. Cobrir draft/geração, aprovação/site-first, publish assíncrono, status/logs seguros, retry/idempotência e reconexão/erro seguro — tudo que a integração IG não pode quebrar.
- **D-03:** Rigidez das asserções = **contrato comportamental**. Assertar comportamentos, estados, campos críticos e mensagens seguras; evitar snapshots frágeis de texto/payload inteiro quando não essenciais. Mudanças intencionais devem exigir atualização consciente do teste.
- **D-04:** Sinalização do gate = **pytest normal + evidência**. A regressão FB roda na suíte pytest normal; `32-VERIFICATION.md`/evidência HARD-02 deve identificar claramente quais testes/arquivos formam o gate FB e seu resultado.

### Cobertura HARD-01 (suíte automatizada)
- **D-05:** Camada prioritária = **backend-first, gaps reais**. Focar em pytest backend (draft/validação, publisher/pipeline, idempotência, retry, ambiguidade, rate limit, mapeamento de erros). Incluir frontend (Vitest/RTL) apenas se houver gap crítico e infra/harness já existente; não criar infraestrutura frontend de testes do zero nesta fase sem necessidade clara.
- **D-06:** Interpretação de "draft/validação Instagram" = **backend/schemas/serviços**. Cobrir geração/normalização de draft IG, validações (limite 2200, hashtags/mídia/regras aplicáveis), contratos de API/schemas e erros seguros. Alinha com testes pytest existentes. Comportamento UI admin (contador/aviso/bloqueio/preview) não é alvo primário de HARD-01 salvo gap crítico já testável.
- **D-07:** Critério de suficiência = **cenários HARD-01 rastreados**. Cada cenário nomeado em HARD-01 deve ser mapeado para teste(s) automatizado(s) claro(s), arquivo/comando e resultado; gaps devem ser explícitos e justificados. Sem meta de percentual de cobertura arbitrária.
- **D-08:** Prioridade em trade-offs = **risco operacional IG/FB**. Priorizar ambiguidade/duplicação, rate limit, reconciliação, idempotência, erros seguros e não-regressão FB antes de casos felizes redundantes.

### Docs operacionais (HARD-02)
- **D-09:** Forma do artefato = **expandir doc existente**. Evoluir `docs/META-INTEGRATION-TESTING.md` como fonte única operacional (Meta/FB + IG readiness + IG publish pipeline + troubleshooting), evitando duplicação. Manter referências cruzadas necessárias.
- **D-10:** Troubleshooting de estados IG = **tabela acionável**. Para cada estado/sintoma: significado, causa provável, ação do admin, se pode retry/reconciliar, pré-condições, e quando escalar. Cobrir estados Phase 31 (ex.: `published`, `failed`, ambíguo/reconciliação requerida, `ig_rate_limit_blocked`/`content_publishing_limit`, `needs_reconnect`, `publish_enabled=false`, permalink ausente, container/publish inconclusivo).
- **D-11:** Env vars e token = **canônica + segurança**. Incluir tabela alinhada a `backend/.env.example` com finalidade, obrigatório/opcional, formato, riscos e comportamento quando ausente/inválido; seção clara de expiração/reconexão (`needs_reconnect`), rotação segura e nunca expor segredos em logs/docs/evidências.
- **D-12:** Checklist manual Meta = **handoff explícito**. Checklist marcado como handoff (não executar sem credenciais/autorização), com pré-condições, passos, critérios de evidência e campos para registrar resultado sanitizado. Não fabricar execução.

### Evidência/handoff de validação
- **D-13:** Local/formato principal = **`32-VERIFICATION.md` + matriz**. Concentrar evidência em `32-VERIFICATION.md` com matriz cenário→evidência (automatizada/handoff), comandos/resultados e status claro. Docs operacionais podem ser referenciados, mas não devem duplicar status de fase.
- **D-14:** Itens manuais Meta = **handoff explícito bloqueado**. Marcar como `handoff/manual`, com pré-condições, ambiente/responsável necessário e "não executado/não evidenciado nesta sessão" quando aplicável. Nunca marcar aprovado sem execução real.
- **D-15:** Granularidade HARD-01 = **por cenário HARD-01**. Mapear cada cenário nomeado (draft/validação IG, idempotência, retry, ambiguidade, rate limit, mapeamento de erros, caracterização/regressão FB) para testes/arquivos/comandos e evidência.
- **D-16:** Gate FB na evidência = **bloco explícito no VERIFICATION**. Incluir seção dedicada "Facebook Regression Gate" com fluxos cobertos, testes/arquivos, resultado e conclusão de não-regressão observada.

### OpenCode's Discretion
- Nomes exatos de arquivos de teste novos/extensões, desde que sigam convenções pytest existentes e facilitem rastreabilidade HARD-01.
- Estratégia de fixtures/mocks para cenários Graph IG/FB (timeouts, 2207042/content_publishing_limit, ambiguidade, reconciliação), desde que não exponham segredos e cubram os cenários exigidos.
- Se algum gap HARD-01 exige pequeno ajuste de contrato interno para testabilidade, permitido apenas se não alterar comportamento de produto e sem regressão FB/site.
- Estrutura editorial final do `docs/META-INTEGRATION-TESTING.md` (seções/tabelas/âncoras), desde que preserve conteúdo útil existente e cumpra D-09..D-12.
- Forma exata da matriz em `32-VERIFICATION.md` (colunas/ordem), desde que cumpra D-13..D-16 e deixe claro automatizado vs handoff.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HARD-01 | Testes automatizados cobrem draft/validação Instagram, publisher/pipeline (idempotência, retry, ambiguidade, rate limit, mapeamento de erros) e caracterização/regressão do fluxo Facebook. | Existing pytest suites cover large portions (publisher, pipeline, admin, CRUD, idempotency/retry policy). Research maps scenario-by-scenario coverage, identifies concrete gaps, and recommends extending existing test files as FB regression gate + HARD-01 matrix. |
| HARD-02 | Documentação operacional inclui env vars, checklist manual Meta, orientação de expiração/reconexão de token e troubleshooting de estados de publicação Instagram. | `docs/META-INTEGRATION-TESTING.md` already exists (FB + IG readiness sections) and must be expanded as the single source. Research identifies missing Phase 31 publish-state troubleshooting, env var/canonical alignment gaps, and handoff-safe checklist/evidence language. |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Follow GSD workflow enforcement: do not make direct repo edits outside GSD workflow unless explicitly asked to bypass. [VERIFIED: AGENTS.md]
- Preserve core value: find job + contact in seconds, no cadastro/login/friction. Hardening must not add friction/regress public flow. [VERIFIED: AGENTS.md, PROJECT.md]
- Fixed stack constraints: Next.js 16 App Router + Tailwind, FastAPI, Neon Postgres, Groq free model env-configured, Cloudflare Turnstile, Vercel + local/Railway-Render split, pt-BR, dark purple minimal design, single master admin. [VERIFIED: AGENTS.md]
- Security/ops constraints from project patterns: no secrets/tokens in logs/docs/evidence; site-first and FB↔IG independence; safe pt-BR errors. [VERIFIED: AGENTS.md, STATE.md, 31/32 CONTEXT]

## Summary

Phase 32 is a hardening/operations phase, not a feature phase. The codebase already has substantial backend pytest coverage for Instagram publish (publisher 2-step, ambiguity, 2207042/content_publishing_limit, permalink best-effort, pipeline reconciliation/rate-limit/provider isolation, admin status/retry/log endpoints) and Facebook publish (publisher classification, pipeline retry/ambiguous recovery, admin/worker/idempotency tests). [VERIFIED: codebase tests read]

The planning challenge is **not** to invent new test infrastructure, but to (1) map HARD-01 named scenarios to exact tests/files/commands with explicit gap handling, (2) promote Facebook characterization into an explicit release gate by extending existing FB tests per D-01/D-02, and (3) evolve `docs/META-INTEGRATION-TESTING.md` into the single operational source for Meta/FB/IG readiness/publish troubleshooting with handoff-safe evidence language. [VERIFIED: 32-CONTEXT.md, docs/META-INTEGRATION-TESTING.md]

**Primary recommendation:** Plan Phase 32 as three tightly scoped outputs: HARD-01 scenario matrix + targeted pytest extensions in existing social test modules; HARD-02 expansion of `docs/META-INTEGRATION-TESTING.md` with actionable IG publish-state troubleshooting and env/security alignment; and `32-VERIFICATION.md` evidence matrix that separates automated pass/fail from manual Meta handoff, including an explicit Facebook Regression Gate block.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HARD-01 automated scenario coverage | Backend tests (pytest) | Backend services/schemas only for testability seams | D-05/D-06 lock backend-first coverage; behavior lives in FastAPI services/pipeline/publishers/schemas. |
| Facebook regression gate | Backend tests (pytest) + verification artifact | — | D-01/D-04 require extending existing pytest FB tests and surfacing gate in 32-VERIFICATION. |
| Instagram publish troubleshooting/runbook | Documentation (`docs/`) | Admin/API contracts as reference | D-09/D-10 require operational doc, not product UI changes. |
| Env var/token/reconnect/rotation guidance | Documentation + config alignment check | `.env.example` / config as canonical references | D-11 requires canonical env/security documentation; code changes only if needed for doc alignment/testability without behavior change. |
| Validation evidence/handoff separation | Planning verification artifact (`.planning/phases/32.../32-VERIFICATION.md`) | — | D-13..D-16 define evidence contract. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| pytest | 9.1.1 (AGENTS stack) | Backend automated tests | Existing backend test suite and all HARD-01 scenarios are backend-first. [VERIFIED: AGENTS.md, backend/tests/*] | HIGH |
| pytest-asyncio | repo dependency (existing) | Async service/pipeline tests | Publish pipeline and publishers are async. [VERIFIED: backend/tests use @pytest.mark.asyncio] | HIGH |
| httpx | 0.28.1 (AGENTS stack) | Mocked Graph/API transport in tests | Existing publisher tests patch `httpx.AsyncClient` / fake responses. [VERIFIED: test_facebook_publisher.py, test_instagram_publisher.py] | HIGH |
| FastAPI/Pydantic/SQLAlchemy async | existing project stack | Contracts under test | Draft/validation, schemas, API, pipeline and persistence are in FastAPI/Pydantic/SQLAlchemy. [VERIFIED: AGENTS.md, codebase] | HIGH |

### Supporting
| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| Vitest | ^2.1.9 in `frontend/package.json` | Existing frontend unit test runner | Only for critical HARD-01 gap if harness already exists; D-05 forbids creating infra from scratch. [VERIFIED: frontend/package.json] | MEDIUM |
| ESLint (frontend) | ^9.39.5 | Frontend lint sanity | If docs/UI-adjacent frontend files touched, not a HARD-01 substitute. [VERIFIED: frontend/package.json] | HIGH |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Extending existing pytest files (D-01) | New parallel snapshot/characterization suite | Rejected by D-01; adds disconnected maintenance and weak traceability. |
| Backend pytest for HARD-01 | New frontend RTL harness for admin IG UI | Rejected by D-05 unless critical gap and harness already exists; expensive/risky in this phase. |
| `docs/META-INTEGRATION-TESTING.md` as single source (D-09) | New IG-only ops doc | Rejected by D-09; duplicates FB/Meta setup and increases drift. |

**Installation:** No new packages expected. Reuse existing backend/frontend tooling. [ASSUMED - confirm during planning if a gap truly needs new dependency; default is none]

**Version verification:** Not run via registry in this research session (no external version changes proposed). Existing versions taken from `AGENTS.md` and `frontend/package.json`. [VERIFIED: local files]

## Architecture Patterns

### System Architecture Diagram

```text
HARD-01 automated evidence flow

  HARD-01 scenarios (ROADMAP/REQUIREMENTS/32-CONTEXT)
        |
        v
  Scenario matrix in 32 plan/verification
        |
        +--> existing pytest modules extended (no parallel snapshot suite)
        |      |- test_facebook_publisher.py / FB pipeline tests  => FB Regression Gate
        |      |- test_instagram_publisher.py / pipeline/admin/validation tests => IG scenarios
        |      \- targeted new tests only if gap not naturally covered
        |
        v
  pytest commands + pass/fail evidence
        |
        v
  32-VERIFICATION.md
        |- Automated matrix by HARD-01 scenario
        |- Facebook Regression Gate block (D-16)
        \- Manual Meta handoff block (blocked/not executed unless real evidence)

HARD-02 operational flow

  backend/.env.example + config + Phase 29/30/31 contracts
        |
        v
  docs/META-INTEGRATION-TESTING.md (single source, expanded)
        |- env vars canonical/security table
        |- token expiration/reconnect/rotation/never expose secrets
        |- IG publish troubleshooting actionable table (Phase 31 states)
        \- manual Meta checklist (handoff, explicit not-executed)
        |
        v
  32-VERIFICATION.md references doc sections (no status duplication)
```

### Pattern 1: Scenario-to-Test Traceability Matrix
**What:** For each HARD-01 named scenario, record scenario → requirement/risk → test file(s) → command → result/evidence status. [VERIFIED: D-07, D-15]
**When to use:** Planning HARD-01 tasks and writing 32-VERIFICATION.
**Example:**
```markdown
| HARD-01 Scenario | Risk | Automated Evidence | Command | Status |
|---|---|---|---|---|
| Ambiguidade IG | Duplicate publish | `backend/tests/test_social_publish_pipeline.py::test_pipeline_ig_ambiguous_persists_reconciliation_without_auto_retry` | `cd backend && pytest -q ...` | PASS/HANDOFF-GAP |
```

### Pattern 2: Extend Existing Contract Tests, Not Snapshots
**What:** Add/adjust assertions on behavior, state transitions, safe fields, and error categories. Avoid full payload/text snapshots. [VERIFIED: D-01, D-03]
**When to use:** FB gate and IG publisher/pipeline error mapping.
**Example:**
```python
result = await publisher.publish(payload)
assert result.ok is False
assert result.category == PublishFailureCategory.ambiguous
assert "duplic" in (result.error_message or "").lower()
```

### Pattern 3: Single Operational Doc With Actionable Table
**What:** Expand `docs/META-INTEGRATION-TESTING.md`; add table rows with meaning/probable cause/admin action/retry-reconcile/preconditions/escalation. [VERIFIED: D-09, D-10]
**When to use:** HARD-02 troubleshooting and env/security sections.
**Example:**
```markdown
| Estado/Sintoma | Significado | Causa provável | Ação do admin | Retry/Reconciliar? | Pré-condições | Escalar quando |
|---|---|---|---|---|---|---|
| `failed` + reconciliação requerida | Resultado IG ambíguo | timeout após container/publish | Usar retry (reconcilia antes) | Somente reconciliação segura | container/IDs conhecidos | IDs inconsistentes ou erro Graph persistente |
```

### Anti-Patterns to Avoid
- **Parallel FB snapshot suite:** Creates drift and violates D-01; extend existing tests instead.
- **Frontend test infra bootstrap:** Violates D-05; backend pytest is the HARD-01 surface.
- **Claiming manual Meta execution:** Violates D-12/D-14; handoff must be explicit.
- **Doc duplication:** New IG ops doc conflicts with D-09; keep one source.
- **Over-broad happy-path tests:** Violates D-08; prioritize risk scenarios.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async HTTP Graph behavior in tests | Live Meta calls in pytest | Existing `httpx.AsyncClient` monkeypatch/fake response pattern | Deterministic, no secrets, covers timeout/rate-limit/ambiguity. [VERIFIED: test_instagram_publisher.py, test_facebook_publisher.py] |
| Publish-state idempotency/reconciliation logic | New ad-hoc test-only state machine | Existing `publish_pipeline.py` helpers + CRUD retry-state | Production logic already encodes D-19/D-20/PUBL-04 semantics. [VERIFIED: publish_pipeline.py, crud/social_posts.py] |
| Operational source of truth | Multiple docs/checklists | Expand `docs/META-INTEGRATION-TESTING.md` | D-09 requires single source. [VERIFIED: 32-CONTEXT.md] |
| Evidence format | Ad-hoc notes in summary | `32-VERIFICATION.md` matrix + FB gate block | D-13..D-16 require auditable handoff. [VERIFIED: 32-CONTEXT.md] |

**Key insight:** Phase 32 hardening is mostly traceability and gap closure over existing contracts; new abstractions increase regression risk.

## Runtime State Inventory

> Not applicable (no rename/refactor/migration phase; no stored identifiers/runtime registrations being renamed). [VERIFIED: phase scope]

## Common Pitfalls

### Pitfall 1: FB Regression Gate Becomes Implicit
**What goes wrong:** FB tests pass but nobody can point to the gate scope/result; HARD-01 "caracterização/regressão do fluxo Facebook" is weakly evidenced.
**Why it happens:** Tests are distributed across files and Phase 32 adds IG focus.
**How to avoid:** Create explicit "Facebook Regression Gate" block in 32-VERIFICATION and tag/identify gate tests by file+name. [VERIFIED: D-04, D-16]
**Warning signs:** Verification lists commands only, not gate composition.

### Pitfall 2: Ambiguity/Rate-Limit Covered at Publisher but Not Pipeline/Admin Contract
**What goes wrong:** Unit publisher maps error, but operator-facing state/retry semantics regress.
**Why it happens:** HARD-01 names publisher/pipeline/error mapping; easy to cover only one layer.
**How to avoid:** Map each risk scenario across layers where applicable: publisher classification, pipeline persistence/retry-state, admin/CRUD safe exposure. [VERIFIED: test_instagram_publisher.py, test_social_publish_pipeline.py, test_admin_instagram_social_posts.py]
**Warning signs:** Scenario marked covered by a single unit test despite operator-visible contract.

### Pitfall 3: IG Rate-Limit Semantics Drift Into Retry Storm
**What goes wrong:** 2207042/content_publishing_limit becomes transient or auto-retryable.
**Why it happens:** Generic transient handling reused incorrectly.
**How to avoid:** Assert `failed_final`, `next_retry_at is None`, safe pt-BR actionable message, retry blocked unless semantics explicitly differ. [VERIFIED: instagram.py, publish_pipeline.py, crud/social_posts.py, existing IG rate-limit tests]
**Warning signs:** Tests only assert error code, not retry scheduling/block reason.

### Pitfall 4: Docs Drift From Canonical Env/State Contracts
**What goes wrong:** Docs omit new IG publish budget env vars or Phase 31 states; operators follow stale guidance.
**Why it happens:** `.env.example` and code evolved through Phases 29-31; doc section 5 focuses on readiness.
**How to avoid:** Build env table from `backend/.env.example` + config settings used by IG publish/reconciliation; add troubleshooting rows for Phase 31 states named in D-10. [VERIFIED: backend/.env.example, backend/app/core/config.py, 32-CONTEXT.md D-10/D-11]
**Warning signs:** Doc mentions MEDIA_PUBLIC_BASE_URL but not `IG_PUBLISH_HTTP_TIMEOUT_SECONDS`/poll/attempt budgets despite config requiring them.

### Pitfall 5: Fabricated Manual Evidence
**What goes wrong:** Verification implies Meta/App Review/live Graph checks were executed.
**Why it happens:** Desire to close HARD-02 completely.
**How to avoid:** Use explicit `handoff/manual`, `blocked`, `not executed in this session` labels with preconditions/responsible/evidence fields. [VERIFIED: D-12, D-14, PROJECT/STATE guardrails]

## Code Examples

### Existing IG ambiguity contract (pipeline) — extend, don't reinvent
```python
# Source: backend/tests/test_social_publish_pipeline.py
outcome = await process_claimed_post(..., publisher=AmbiguousIGPublisher(), ...)
assert outcome == "failed_final"
assert post.status == SocialPostStatus.failed
assert post.next_retry_at is None
assert post.ig_reconciliation_required is True
assert post.ig_reconciliation_state == "needs_reconciliation"
assert post.ig_container_id == "container-1"
```

### Existing FB error mapping contract — extend for full-cycle gate
```python
# Source: backend/tests/test_facebook_publisher.py
result = await publisher.publish(payload)
assert result.ok is False
assert result.category == PublishFailureCategory.ambiguous
assert "duplic" in (result.error_message or "").lower() or "confirmar" in (result.error_message or "").lower()
```

### Existing IG rate-limit classification (publisher)
```python
# Source: backend/tests/test_instagram_publisher.py
result = await InstagramPublisher().publish(_ig_payload())
assert result.ok is False
assert result.category == PublishFailureCategory.permanent
assert result.error_code in {"ig_rate_limit_blocked", "ig_content_publishing_limit"}
assert "aguarde" in (result.error_message or "").lower()
```

### Verification matrix shape (for 32-VERIFICATION)
```markdown
## HARD-01 Scenario Matrix
| Scenario | Requirement | Automated Tests | Command | Result | Notes |
|---|---|---|---|---|---|
| draft/validação Instagram | HARD-01 | ... | ... | PASS | backend/schemas/services per D-06 |

## Facebook Regression Gate
| Flow | Tests | Result |
|---|---|---|
| FB draft/generate/approve/site-first/async publish/status/retry/idempotency/reconnect-safe | ... | PASS/FAIL |

## Manual Meta Handoff
| Item | Status | Preconditions | Evidence Required | Executed |
|---|---|---|---|---|
| Live IG publish/reconcile/rate-limit smoke | handoff/manual | Meta app/page/IG perms/credentials | sanitized screenshots/log IDs | Not executed in this session |
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FB-only social publish path | Provider-aware FB+IG pipeline with isolated blocks and by_provider counters | Phase 31 (2026-11-25) | HARD-01/02 must protect isolation and operator visibility. [VERIFIED: 31-SUMMARY/VERIFICATION] |
| IG readiness only | IG readiness + review + 2-step publish + reconciliation/rate-limit handling | Phases 29-31 | Hardening must cover operational states beyond readiness. [VERIFIED: 29/30/31 artifacts] |
| Implicit FB non-regression confidence | Explicit FB regression gate evidence in verification | Phase 32 target | Required by D-01/D-04/D-16. [VERIFIED: 32-CONTEXT] |

**Deprecated/outdated:**
- Treating live Meta manual checks as "done" without credentials/evidence: never acceptable; use handoff. [VERIFIED: D-12/D-14, PROJECT/STATE]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | No new Python/frontend dependencies are needed for Phase 32; existing pytest/vitest/eslint tooling is sufficient. | Standard Stack | Low - if a gap needs new dep, plan must justify and keep scope minimal. |
| A2 | "draft/validação Instagram" backend scope is satisfied by backend/schema/service/API tests; UI counter/warning behavior remains Phase 30 concern unless a critical already-testable gap is found. | HARD-01 gap analysis | Medium - planner may need one small backend contract test if a validation rule is only UI-enforced. |
| A3 | Adding IG publish budget env vars to `backend/.env.example` is acceptable doc/config alignment (no behavior change) if they are already in config. | HARD-02 gaps | Low - env example is canonical documentation; verify with config semantics before editing. |

## Open Questions (RESOLVED)

1. **Are IG publish HTTP/poll/budget env vars intentionally omitted from `.env.example`?**
   - What we know: `backend/app/core/config.py` defines `IG_PUBLISH_HTTP_TIMEOUT_SECONDS`, `IG_STATUS_POLL_MAX_ATTEMPTS`, `IG_STATUS_POLL_DELAY_SECONDS`, `IG_PUBLISH_MAX_ATTEMPT_SECONDS` with validation. [VERIFIED: config.py]
   - What's unclear: `.env.example` currently does not list them. [VERIFIED: backend/.env.example]
   - RESOLVED: Treat as documentation/config-alignment gap, not intentional omission. HARD-02 must document these vars canonically (purpose, required/optional, format, safe default/behavior, security notes) and align `backend/.env.example` in a behavior-preserving way per D-11. No secret values.

2. **What exact FB "full cycle" tests count as gate?**
   - What we know: D-02/D-16 require full cycle and explicit gate block. Existing tests cover pieces (publisher classification, pipeline retry/idempotency/ambiguous recovery, admin social publish/worker/status/retry). [VERIFIED: tests listed in codebase]
   - What's unclear: No single named gate selection exists yet.
   - RESOLVED: Plans must name an explicit FB Regression Gate test set/command and mirror it in `32-VERIFICATION.md`. Gate covers full cycle FB via existing pytest files extended as needed: draft/generation and approval/site-first/admin dispatch (`test_admin_social_publish.py`, `test_social_publisher.py` where applicable), async publish/pipeline/worker (`test_facebook_publisher.py`, `test_social_publish_pipeline.py`, `test_social_worker_claim.py`, `test_social_publisher.py`), status/logs seguros (`test_admin_social_status_api.py`, `test_admin_social_retry_api.py`), retry/idempotency (`test_social_retry_policy.py`, `test_social_idempotency.py`, `test_admin_social_retry_api.py`), reconnect/safe error (`test_facebook_publisher.py`, `test_social_publish_pipeline.py`). Any file listed must be justified by actual FB coverage; do not claim FB draft coverage from IG-only test files.

3. **Is there any backend enforcement gap for IG hashtag >30 / CTA "link na bio"?**
   - What we know: D-06 includes validations/rules applicable to draft/validation IG; Phase 30 D-09 framed >30 hashtags as warning and link-in-bio orientation in UI. [VERIFIED: 32-CONTEXT, 30-CONTEXT]
   - What's unclear: backend may not enforce >30 as hard rule (likely warning-only UI concern).
   - RESOLVED: HARD-01 backend scope covers backend/schemas/services/contracts and safe errors (2200 cap, normalization, media/URL validation, safe error mapping, no secrets). `>30 hashtags` is a Phase 30 D-09 UI warning contract, not a backend hard-block rule unless code evidence shows otherwise; plans/verification must explicitly record this boundary (automated backend tests for enforced rules + explicit justified gap/note for UI-only >30 warning). "Link na bio" CTA is copy/orientation in template/UI, not a clickable backend validation rule; plans should not invent backend enforcement.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Backend pytest | ✓ | 3.13.3 (`python --version` observed earlier in environment) | — |
| Node/npm | Frontend lint/tests if touched | ✓ | Present in repo toolchain [ASSUMED from frontend/package.json/scripts] | Skip frontend automated checks unless frontend files touched |
| pytest | HARD-01 | ✓ (repo standard) | per backend deps/AGENTS | — |
| Vitest | Optional frontend gap | ✓ installed in frontend devDeps | ^2.1.9 [VERIFIED: frontend/package.json] | Do not create harness; backend-first |

**Missing dependencies with no fallback:**
- None identified.

**Missing dependencies with fallback:**
- None identified. Live Meta credentials/access are not local deps; they are manual handoff items (D-12/D-14).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (backend) |
| Config file | backend/pyproject.toml / pytest defaults (existing) |
| Quick run command | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_post_generation.py tests/test_ig_media_validation.py` |
| Full suite command | `cd backend && pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HARD-01 | Draft/validação IG: geração/normalização, limite 2200, mídia inválida/ausente/public URL, contratos/schema seguros | unit/integration | `cd backend && pytest -q tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_admin_instagram_social_posts.py -k "instagram or 2200 or caption or media or draft"` | ✅ (extend as gaps found) |
| HARD-01 | Idempotência IG/FB: no duplicate on external_id/published/ambiguous reconciliation | unit/integration | `cd backend && pytest -q tests/test_social_idempotency.py tests/test_social_publish_pipeline.py -k "idempoten or ambiguous or reconcile"` | ✅ |
| HARD-01 | Retry/backoff: transient retry, exhausted/final, manual retry semantics safe | unit/integration | `cd backend && pytest -q tests/test_social_retry_policy.py tests/test_social_publish_pipeline.py tests/test_admin_social_retry_api.py -k "retry or backoff"` | ✅ |
| HARD-01 | Ambiguidade: FB/IG ambiguous no blind auto-retry; IG reconciliation required | unit/integration | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "ambig"` | ✅ |
| HARD-01 | Rate limit: FB 429/transient classification, IG 2207042/content_publishing_limit blocked actionable no retry storm | unit/integration | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "rate or 2207042 or content_publishing_limit"` | ✅ |
| HARD-01 | Mapeamento de erro seguro: transient/permanent/ambiguous/unknown, pt-BR safe, no secrets | unit | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "transient or permanent or ambiguous or unknown or safe"` | ✅ (extend for systematic matrix) |
| HARD-01 | FB regression gate full cycle | integration/contract | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_social_publish_pipeline.py tests/test_admin_social_publish.py tests/test_admin_social_status_api.py tests/test_admin_social_retry_api.py tests/test_social_idempotency.py -k "facebook or social"` | ✅ (needs explicit gate selection/extension per D-01/D-02) |
| HARD-02 | Operational doc/checklist/handoff completeness | doc/manual verification | `rg -n "Instagram|needs_reconnect|content_publishing_limit|ig_rate_limit_blocked|handoff|não executado|CRON_SECRET|MEDIA_PUBLIC_BASE_URL" docs/META-INTEGRATION-TESTING.md` | ✅ (doc exists, needs expansion) |

### Sampling Rate
- **Per task commit:** Narrowest affected pytest command for touched tests/files
- **Per wave merge:** `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_social_retry_policy.py tests/test_social_idempotency.py tests/test_admin_social_publish.py tests/test_admin_social_retry_api.py tests/test_admin_social_status_api.py tests/test_admin_instagram_social_posts.py`
- **Phase gate:** Targeted HARD-01 gate green before `/gsd-verify-work`; manual Meta items remain explicit handoff

### Wave 0 Gaps
- [ ] `backend/tests/test_facebook_publisher.py` — extend for explicit FB regression/contract cases (D-01/D-02)
- [ ] `backend/tests/test_social_publish_pipeline.py` — extend any missing FB full-cycle/regression and HARD-01 traceability gaps
- [ ] `backend/tests/test_admin_social_publish.py` or other existing FB/social admin tests — include in FB gate selection if they cover approve/dispatch/status/retry/site-first
- [ ] `docs/META-INTEGRATION-TESTING.md` — HARD-02 expansion (not a test file, but required artifact)
- [ ] `.planning/phases/32-hardening-regression-operations/32-VERIFICATION.md` — created during execution/verification with matrix + FB gate + handoff (D-13..D-16)

*(No new test framework install expected.)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (admin endpoints/token-gated ops) | Existing admin auth/JWT/cron-secret patterns; tests must not weaken auth. [VERIFIED: admin endpoints/tests patterns] |
| V3 Session Management | limited | Admin JWT/session behavior not phase focus; preserve existing behavior. [ASSUMED] |
| V4 Access Control | yes | Worker/cron secret fail-closed; admin-only social status/retry/log endpoints. [VERIFIED: test_social_worker_claim.py, admin routes] |
| V5 Input Validation | yes | Caption/media/env/url validation; safe 422/pt-BR errors. [VERIFIED: admin.py, image_media.py, config.py] |
| V6 Cryptography | yes (token handling) | Fernet-encrypted tokens; never log/expose tokens/secrets. [VERIFIED: config.py, crypto usage, safe_text redaction] |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Token/secret leakage in logs/docs/evidence | Information Disclosure | Redact/sanitize; `_safe_text` patterns; docs state "never expose secrets"; verification marks handoff without secrets. [VERIFIED: publish_pipeline.py, D-11/D-14] |
| Ambiguous publish retried blindly | Tampering / Integrity | Persist ambiguous reconciliation state, no auto-retry, reconcile before publish. [VERIFIED: PUBL-04, pipeline tests] |
| Retry storm on IG rate limit | Denial of Service / Abuse | Classify 2207042/content_publishing_limit as blocked actionable, no auto-retry. [VERIFIED: PUBL-05, instagram/pipeline/crud tests] |
| FB regression via IG changes | Tampering / Functional integrity | Explicit FB regression gate in pytest + verification block. [VERIFIED: D-01/D-02/D-16] |
| Misconfigured public media base URL | Information Disclosure / Integration failure | Validate HTTPS public non-local/private base URL; document env behavior. [VERIFIED: config.py, image_media validation] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/32-hardening-regression-operations/32-CONTEXT.md` - locked decisions D-01..D-16, discretion, scope
- `.planning/REQUIREMENTS.md` - HARD-01/HARD-02 requirement contracts and traceability
- `.planning/ROADMAP.md` - Phase 32 goal/success criteria/dependencies
- `.planning/STATE.md` - current position, concerns, carry-over guardrails
- `.planning/PROJECT.md` - core value, constraints, validated behavior
- `docs/META-INTEGRATION-TESTING.md` - existing operational doc to expand (D-09 baseline)
- `backend/.env.example` - canonical env vars baseline for D-11
- `backend/app/core/config.py` - env validation including IG publish budgets and MEDIA_PUBLIC_BASE_URL
- `backend/app/services/social/publish_pipeline.py` - provider-aware pipeline, ambiguity/reconciliation/rate-limit/idempotency/safe logging
- `backend/app/services/social/instagram.py` - IG 2-step publish, status polling, error classification, permalink best-effort
- `backend/app/services/social/facebook.py` - FB publish/error classification
- `backend/app/crud/social_posts.py` - claim eligibility `publish_enabled`, retry-state semantics, safe status/log builders
- `backend/app/schemas/social_posts.py` - safe status/log/worker schemas
- `backend/app/api/v1/admin.py` - worker/retry/status/logs/approve dispatch contracts (grep/read)
- `backend/tests/test_facebook_publisher.py`, `backend/tests/test_instagram_publisher.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_social_idempotency.py`, `backend/tests/test_social_retry_policy.py`, `backend/tests/test_social_worker_claim.py`, `backend/tests/test_admin_social_publish.py`, `backend/tests/test_admin_social_retry_api.py`, `backend/tests/test_admin_social_status_api.py`, `backend/tests/test_admin_instagram_social_posts.py`, `backend/tests/test_social_post_generation.py`, `backend/tests/test_ig_media_validation.py`, `backend/tests/test_integrations_instagram.py`, `backend/tests/test_meta_oauth_instagram.py`, `backend/tests/test_docs_meta_instagram.py` - existing coverage and patterns
- `.planning/phases/31-independent-publish-pipeline/31-VERIFICATION.md` - Phase 31 evidence baseline and bookkeeping warning
- `.planning/phases/31-independent-publish-pipeline/31-VALIDATION.md` - validation map pattern

### Secondary (MEDIUM confidence)
- `.planning/phases/31-independent-publish-pipeline/31-RESEARCH.md`, `31-01-PLAN.md`, `31-02-SUMMARY.md` - implementation intent/details; useful for gap context, but code/tests are authoritative.

### Tertiary (LOW confidence)
- None. No websearch needed; this phase is grounded in local code/contracts.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - existing repo stack/tests; no new stack proposed.
- Architecture: HIGH - directly derived from D-01..D-16 and existing code/test/doc layout.
- Pitfalls: HIGH - grounded in actual Phase 31 contracts and current doc/config gaps.

**Research date:** 2026-11-26
**Valid until:** 2026-12-26 (stable internal hardening/docs phase; recheck if Phase 31 code changes)
