# Phase 22: Qualidade, hardening e validação operacional - Research

**Researched:** 2026-11-18
**Domain:** QA/hardening/operabilidade do chatbot público (FastAPI + intent seam Groq/Pydantic + Next.js chat UI), sem regressão do board
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Validação dos exemplos MVP (QA-01)
- **D-01:** Abordagem **híbrida** para validar e documentar os 5 exemplos-alvo: (a) matriz versionada em `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/` (ex.: `22-MVP-EXAMPLES.md` ou nome equivalente definido no plano) descrevendo, para cada exemplo, mensagem de entrada, interpretação/`applied_params` e status por campo esperados, resultados/`limitations`/guidance esperados e lacunas explícitas; e (b) testes automatizados de cenários-alvo quando determinísticos/mapeáveis (intent/chat com LLM mockado e/ou fixtures), fornecendo evidência executável de regressão.
- **D-02:** O caso **“vagas parecidas com uma vaga”** deve ser tratado como **seed textual limitado** (consulta em linguagem natural que descreve/referencia uma vaga, com termos extraídos para `q` conforme contrato atual). A validação deve explicitar que **não há similaridade semântica/vetorial nem suporte a seed por link/ID de vaga** nesta fase; a resposta deve sinalizar aproximação/limite conforme INT/API.
- **D-03:** Para cada exemplo, a evidência “validada” deve registrar **contrato esperado + resultado observado**: entrada; interpretação esperada (campos entendidos, `field_statuses`/motivos, `applied_params`, `limitations`/`meta.guidance` quando aplicável); comportamento de resultados esperado (incluindo suporte parcial/não filtragem/ausência de resultados automáticos quando couber); e evidência observada (referência a teste automatizado e/ou execução/fixture documentada). Lacunas explícitas obrigatórias para combinações e capacidades não suportadas nativamente (ex.: Campinas fora da whitelist, salário/modalidade/contrato/senioridade aproximados, “parecidas”).

#### Suíte automatizada e UI/E2E viável (QA-02)
- **D-04:** “Validação básica do fluxo de UI/E2E viável” será atendida por **roteiro manual/UAT guiado versionado** cobrindo o fluxo crítico do chat no board (abrir chat sem login, enviar mensagem, estados de carregamento/erro, ver interpretação aplicada/ignorada/aproximada e limitações, ver resultados/“carregar mais” quando aplicável, aplicar no board canônico quando aplicável, abrir detalhe e preservar fluxo de revelação sem expor contatos, atalho de busca manual em degradação/sem resultados) **+ testes automatizados de lógica pura de UI já suportada** (ex.: helpers como `chatApply`). **Não** introduzir Playwright nem configurar React Testing Library/infra nova de browser/E2E nesta fase.
- **D-05:** Para backend (extração/mapeamento/normalização e API `chat-search` com LLM mockado), o foco é **fechar lacunas e consolidar a suíte existente** (ex.: `backend/tests/test_intent_schema.py`, `test_intent_mapper.py`, `test_intent_parser.py`, `test_intent_client.py`, `test_chat_search_api.py`), adicionando apenas casos faltantes para cobrir explicitamente cenários MVP/combinações, contratos de classificação/mapeamento, privacidade (`JobPublic` sem contatos), degradação/fallback seguro, limites/proteções e equivalência determinística — evitando duplicação desnecessária de suítes.

#### Controles operacionais e kill-switch (QA-03)
- **D-06:** Adotar **kill-switch/configuração fim-a-fim** via env/config lido pelo backend: quando o chat estiver desativado, o endpoint de chat-search deve responder de forma **segura e controlada** (estado desativado/guidance pt-BR para busca manual, sem vazar detalhes internos) e o frontend deve **consultar/sinalizar esse estado e ocultar ou desabilitar a entrada do chat**. A implementação deve garantir que desativar/ajustar o chat **não afete** a listagem/busca manual do board público. (Mecanismo exato de sinalização ao frontend — ex.: endpoint/config pública, flag embutida ou equivalente viável — fica a critério da implementação desde que atenda ao comportamento.)
- **D-07:** Observabilidade mínima: **logs estruturados de evento/resultado sem PII sensível**. Não registrar conteúdo da mensagem do usuário nem dados pessoais/contatos. Registrar, no mínimo viável, sinais operacionais como outcome (sucesso, degradado, desativado, erro controlado), motivo/código de degradação ou desativação, latência/duração, indicadores agregados seguros (ex.: contagem de resultados/total quando aplicável) e status/causa operacional relevante (incluindo rate limit/timeout) para diagnóstico e ajuste. Métricas externas/infra de agregação obrigatória estão fora do escopo desta decisão.

### OpenCode's Discretion
- Nomes, localização exata e formato dos artefatos de validação (arquivo de matriz QA-01, roteiro manual QA-02), desde que versionados em `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/` e rastreáveis aos requisitos.
- Seleção precisa dos casos de teste a adicionar/consolidar (evitando duplicação) e organização de fixtures/mocks para cenários MVP e combinações.
- Nomes/valores exatos de env/config do kill-switch, forma de expor estado ao frontend, shape de resposta “chat desativado” (compatível com UX segura/guidance) e detalhes de implementação dos logs estruturados (campos/formato) desde que sem PII e úteis operacionalmente.
- Pequenos ajustes de copy pt-BR e estados de UI necessários para refletir “desativado” com orientação para busca manual, preservando o contrato público e o comportamento canônico do board.
- Critério exato de “executável/viável no ambiente do projeto” para comandos de teste/documentação de pré-requisitos, sem prometer execução de suites dependentes de infraestrutura indisponível.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| QA-01 | O MVP cobre os exemplos-alvo do milestone com comportamento validado e documentado (incluindo combinações e lacunas explícitas): dev pleno SP salário >= 8k; remoto frontend React preferência CLT; vagas parecidas com uma vaga (abordagem limitada/seed por texto/link conforme suportado); analista de dados Campinas ou remoto 6–10k; estágio marketing digital em SP. | Matriz versionada `22-MVP-EXAMPLES.md` (contrato esperado + observado, lacunas) + casos determinísticos em suítes existentes com intent/LLM mockado (mapper/parser/chat API) cobrindo whitelist/Remoto, aproximações não nativas, `not_in_whitelist` Campinas, e “parecidas” como seed textual sem semântica/link/ID. |
| QA-02 | Existem testes automatizados cobrindo extração/mapeamento/normalização e API de chat-search (com LLM mockado) e validação básica do fluxo de UI/E2E conforme viável no ambiente do projeto. | Consolidar/extender `backend/tests/test_intent_{schema,mapper,parser,client}.py` e `backend/tests/test_chat_search_api.py` (LLM seam mockado, sem rede) + manter/estender lógica pura frontend em Vitest (`frontend/lib/chatApply.test.ts`, helpers puros se extraídos) + roteiro manual/UAT guiado versionado (sem Playwright/RTL novo). |
| QA-03 | O sistema possui controles operacionais mínimos para o chat (config/feature toggle ou kill-switch, logs/métricas básicas sem PII sensível) para permitir desativação/ajuste seguro em caso de abuso, custo ou degradação, sem regredir o board público existente. | Kill-switch fim-a-fim via `Settings`/env lido no backend (`POST /api/v1/public/chat-search` resposta 200 controlada desativada + guidance pt-BR, sem internos) e sinal consumível pelo frontend para ocultar launcher/painel; logs estruturados por evento (outcome/reason/latency/contagens) sem mensagem/PII/contatos; board/listagem manual (`GET /public/jobs`, toolbar/grid/detalhe/reveal) independentes. |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- **Core value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção. [VERIFIED: `AGENTS.md`]
- **Stack fixa:** Frontend Next.js 16 (App Router, 16.4.6) + Tailwind CSS + dark mode; Backend FastAPI (Python); DB Neon Postgres; LLM Groq `openai/gpt-oss-20b` (padrão) com fallback `openai/gpt-oss-120b` via `GROQ_MODEL`; anti-spam Turnstile; deploy Vercel + Railway/Render; pt-BR. [VERIFIED: `AGENTS.md`, `backend/app/core/config.py`]
- **LLM extrai apenas parâmetros; busca determinística reutiliza `list_published`/contrato público (`JobPublic`) sem contatos** — validações/kill-switch/logs não podem violar isso. [VERIFIED: `AGENTS.md`, `.planning/PROJECT.md`, `.planning/STATE.md`, `backend/app/api/v1/public.py`]
- **Campos não nativos = suporte limitado/aproximado e sinalizado** (nunca afirmar filtragem inexistente); degradação/fallback controlado em pt-BR. [VERIFIED: `.planning/STATE.md`, `backend/app/api/v1/public.py`, `backend/app/services/intent/mapper.py`]
- **URL canônica do board** (`q/city/sort/page/vaga`) como fonte de verdade; contatos nunca expostos no payload do chat e revelação apenas no fluxo canônico. [VERIFIED: `.planning/PROJECT.md`, `frontend/lib/filters.ts`, `frontend/components/board/chat/ChatWidget.tsx`]
- **Workflow:** não fazer edições diretas fora de fluxo GSD salvo pedido explícito; usar `/gsd-quick|/gsd-debug|/gsd-execute-phase` conforme caso. [VERIFIED: `AGENTS.md`]

## Summary

Phase 22 is a hardening/validation/operability phase over an already-implemented chat search path: `POST /api/v1/public/chat-search` (`backend/app/api/v1/public.py`) orchestrates `extract_and_map_intent` (`backend/app/services/intent/parser.py` → `client.py` seam + `mapper.py`) and runs deterministic retrieval via `list_published` (`backend/app/crud/jobs.py`) returning `ChatSearchResponse(interpretation: IntentContract, results: ChatSearchResults{items: JobPublic[], page, limit, total})` with no contacts (`backend/app/schemas/chat.py`, `backend/app/schemas/job.py`). [VERIFIED: code reads] The frontend consumes this via `frontend/lib/api.ts#chatSearch` and session-local UI state in `frontend/components/board/chat/*`, applying canonical board params through `frontend/lib/chatApply.ts` + `frontend/lib/filters.ts` and opening details through the canonical `JobDetailDialog`/`?vaga` flow. [VERIFIED: code reads]

The planner must focus on **gaps**, not reimplementation: (1) QA-01 versioned MVP matrix + deterministic evidence for the 5 target examples and explicit capability limits (Campinas outside whitelist, salary/modality/contract/seniority not native structured filters, “parecidas” as textual seed only, no semantic/link/ID); (2) QA-02 consolidation by extending existing pytest/Vitest suites (LLM always mocked at intent seam, no network) and adding a versioned manual/UAT guide feasible in current infra (no Playwright/RTL); (3) QA-03 end-to-end kill-switch/config and structured no-PII event logging, while keeping `GET /api/v1/public/jobs`, manual board search, detail/reveal, and canonical URL behavior fully independent.

**Primary recommendation:** Add a single env-driven `CHAT_SEARCH_ENABLED` setting enforced at the chat endpoint boundary (safe 200 disabled contract + pt-BR guidance, no internals) plus a lightweight frontend-consumable status signal so `ChatWidget` hides launcher/panel when disabled; instrument one structured per-request `chat_search` log (outcome/reason/latency/counts, never message/PII/contacts); and encode the 5 MVP scenarios as deterministic mocked-contract/candidate tests + a `22-MVP-EXAMPLES.md` matrix and `22-MANUAL-UAT.md` runbook reusing existing seams/fixtures.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| NL intent extraction (LLM seam) | API / Backend | — | `intent/client.py` calls Groq from backend; LLM must only extract params and is mockable in tests. [VERIFIED] |
| Intent validation/mapping/classification (`q/city/sort`, applied/ignored/aproximado) | API / Backend | — | `intent/schema.py`, `mapper.py`, `parser.py` are server-authoritative/deterministic. [VERIFIED] |
| Deterministic job retrieval | API / Backend (DB) | Database / Storage | `public.chat_search` must reuse `list_published` predicates/total semantics over `JobPublic`. [VERIFIED] |
| Kill-switch enforcement & safe disabled/degraded response | API / Backend | — | Config read in backend; endpoint must not leak internals and must not affect other public routes. [VERIFIED: D-06, `config.py`, `public.py`] |
| Operational logging (no PII/message/contacts) | API / Backend | — | Server-side boundary in `public.py`/intent flow; use stdlib logging (`app.core.logging`). [VERIFIED] |
| Chat availability signaling & UI hide/disable | Frontend Server/Client (Browser) | API / Backend | Frontend consults backend-provided signal and hides launcher/panel; board remains usable. [VERIFIED: 22-UI-SPEC, `ChatWidget.tsx`, `page.tsx`] |
| Chat interpretation/results rendering & apply-to-board | Browser / Client | — | Client components/state in `components/board/chat/*`, `lib/api.ts`, `lib/chatApply.ts`, `filters.ts`. [VERIFIED] |
| Canonical detail & contact reveal | Browser / Client | API / Backend | `JobDetailDialog`/`RevealContact` and public reveal endpoint remain the only contact path; chat must not expose contacts. [VERIFIED] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.143.0 | Public/admin HTTP API | Existing async app, validation/errors/DI, rate-limit integration. [VERIFIED: `backend/pyproject.toml`, `AGENTS.md`] |
| Pydantic | 2.14.1 | Strict request/response/intent contracts | `IntentLLMOutput`/`IntentContract`, `ChatSearchRequest/Response`, `JobPublic` validation and `extra="forbid"` safety. [VERIFIED] |
| groq (Python SDK) | 1.7.0 | Intent extraction seam | Existing `AsyncGroq` client with strict json_schema, timeout, repair/fallback; must remain mocked in tests. [VERIFIED: `intent/client.py`, `pyproject.toml`] |
| SQLAlchemy (async) + asyncpg | 2.1.4 + 0.32.0 | Deterministic DB search | `list_published` shared predicate/total logic for public jobs/chat-search equivalence. [VERIFIED] |
| Next.js (App Router) + React | 16.4.6 + 19.1.1 | Public board/chat UI | Existing server-rendered board with client chat widget; no new framework/infra. [VERIFIED: `frontend/package.json`, `AGENTS.md`] |
| TypeScript | 5.9.2 (repo) / 7.x noted in AGENTS | Typed frontend contracts | `lib/api.ts` chat/public types, helpers and Vitest node tests. [VERIFIED: `frontend/package.json`, `frontend/lib/api.ts`] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| slowapi | 0.1.10 | Per-IP per-endpoint rate limiting | Keep `chat_search` protected; 429 pt-BR with `Retry-After`. [VERIFIED: `core/ratelimit.py`, `public.py`] |
| pytest + pytest-asyncio | 9.1.1 + >=1,<2 (auto) | Backend unit/API tests | Extend intent/chat suites with fake client/monkeypatch; DB-backed only when test DB available. [VERIFIED: `pyproject.toml`, `conftest.py`] |
| Vitest | ^2.1.9 (node env) | Frontend pure-logic tests | `lib/**/*.test.ts` (currently `chatApply.test.ts`); no RTL/Playwright. [VERIFIED: `frontend/vitest.config.ts`, `package.json`] |
| stdlib `logging` | Python stdlib | Structured operational events | D-07 no-PII outcome/reason/latency/count logs via `extra` at endpoint boundary. [VERIFIED: `core/logging.py`, `public.py`] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Groq SDK direct + Pydantic (keep) | Instructor / LangChain / agent SDKs | Explicitly out for Phase 22 hardening: adds churn/surface and risks contract/regression; current seam is testable and sufficient. [CITED: `22-AI-SPEC.md` §2] |
| Manual/UAT runbook + Vitest pure logic | Playwright / RTL E2E | Forbidden by D-04 in this phase; environment/infra cost not justified for scope. [VERIFIED: 22-CONTEXT D-04] |
| In-memory status fetch/config signal | Persistent feature-flag service | Out of scope; env/config + code is sufficient and deterministic for operator kill-switch (QA-03). [VERIFIED: D-06] |

**Installation:**
```bash
# No new dependencies expected. Use existing project installs.
cd backend && pip install -e ".[dev]"   # or existing venv/uv workflow
cd frontend && npm ci
```

**Version verification:** Versions above reflect repository manifests at research time (`backend/pyproject.toml`, `frontend/package.json`, `AGENTS.md`), not fresh registry checks. [VERIFIED: repo files] [ASSUMED] Patch drift may exist in deployed environments; Phase 22 must not introduce version bumps unless required.

## Architecture Patterns

### System Architecture Diagram

```text
[Public visitor, no login]
        |
        v
[Next.js public board (Server Component)] ----renders----> [BoardToolbar/JobGrid/Pagination, canonical q/city/sort/page/vaga]
        |                                                         ^
        | mounts                                                  | router.replace(buildBoardHref) / ?vaga sync
        v                                                         |
[ChatWidget (client, session memory)] --consult chat status--> (GET status signal, optional)
        |                                                         |
        | chatSearch(message,page,limit)                          | open detail
        v                                                         v
POST /api/v1/public/chat-search  ------------------------>  [JobDetailDialog + RevealContact (canonical, contacts only via reveal)]
        |
        +--> [rate limit (IP+endpoint)] --> [request/schema validation]
        +--> [kill-switch check (CHAT_SEARCH_ENABLED)] --off--> controlled 200 disabled (guidance pt-BR, empty results, no internals)
        +--> [extract_and_map_intent(message, timeout)] --fail/timeout--> degraded 200 (meta.degraded/reason/guidance)
        +--> [effective no-params?] -------------------------------> degraded 200 (no_extractable_params)
        +--> [apply approx guidance/limitations]
        +--> [list_published(q, city, sort, page, limit)] <== same deterministic predicates/total as GET /api/v1/public/jobs
        +--> [ChatSearchResponse: interpretation + JobPublic items, no contacts]
        +--> [structured log event: outcome/reason/latency/counts, NO message/PII/contacts]

Independent path (must remain unaffected): GET /api/v1/public/jobs + manual board UI + /reveal-contact
```

### Recommended Project Structure
```text
.planning/phases/22-qualidade-hardening-e-valida-o-operacional/
├── 22-MVP-EXAMPLES.md          # QA-01 matriz (D-01/D-02/D-03)
├── 22-MANUAL-UAT.md            # QA-02 roteiro manual guiado (viável, sem Playwright/RTL)
└── 22-RESEARCH.md              # this file

backend/
├── app/core/config.py          # add CHAT_SEARCH_ENABLED (+ optional observability knobs if needed)
├── app/api/v1/public.py        # kill-switch enforcement, disabled/degraded guidance, structured logging
├── app/schemas/chat.py         # keep compatible response contract (meta/guidance/degraded reason)
└── tests/
    ├── test_intent_{schema,mapper,parser,client}.py  # consolidate/extend MVP + contract cases
    ├── test_chat_search_api.py                       # extend disabled/logging/equivalence/privacy cases
    └── conftest.py                                   # consider DB-independent whitelist for pure intent tests (discretion)

frontend/
├── app/(public)/page.tsx                 # board unchanged; ChatWidget mount remains safe
├── components/board/chat/ChatWidget.tsx  # consult status, hide launcher/panel when disabled, handle disabled response
├── lib/api.ts                            # status fetch/type + chatSearch handling as needed
├── lib/chatApply.ts(.test.ts)            # existing pure-logic coverage; extend only if needed
└── lib/*.test.ts                         # Vitest node-only, pure helpers
```

### Pattern 1: Deterministic MVP evidence with mocked LLM seam
**What:** For QA-01/QA-02, drive scenarios via `IntentLLMOutput` candidates (mapper/parser tests) or mocked `extract_and_map_intent`/intent client (API tests) to assert `IntentContract` (`understood`, `field_statuses`, `applied_params`, `limitations`, `meta`) and `list_published`-equivalent results without network/LLM variability. [VERIFIED: `backend/tests/test_intent_*`, `backend/tests/test_chat_search_api.py`]
**When to use:** Every example/combination that must be regression-safe and CI-feasible (including Campinas whitelist, non-native approximations, no-params/degraded/timeout/disabled cases).
**Example:**
```python
# Source: backend/tests/test_chat_search_api.py, backend/app/api/v1/public.py [VERIFIED]
interpretation = _contract(q="analista", city="São Paulo", sort="recentes")

async def fake_extract(*args, **kwargs):
    return interpretation

monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)
chat = await client.post("/api/v1/public/chat-search", json={"message": "analista em sp", "page": 1, "limit": 20})
jobs = await client.get("/api/v1/public/jobs", params={"q": "analista", "city": "sao-paulo", "sort": "recentes", "page": 1, "limit": 20})
assert [i["id"] for i in chat.json()["results"]["items"]] == [i["id"] for i in jobs.json()["items"]]
assert "contact_email" not in chat.json()["results"]["items"][0]
```

### Pattern 2: Kill-switch as boundary guard + safe disabled contract
**What:** Read `CHAT_SEARCH_ENABLED` from `get_settings()`; if disabled, short-circuit to a controlled 200 response (no LLM call, no DB query required) with empty `results`, `applied_params` null, `meta.degraded/guidance` (and a stable `degradation_reason` such as `chat_disabled`) in pt-BR, and no internal details. Frontend consumes a status signal and hides launcher/panel when disabled (UI-SPEC). [VERIFIED: D-06, 22-UI-SPEC, `config.py`, `public.py`]
**When to use:** Operator disablement for abuse/cost/degradation and QA-03 acceptance.
**Example:**
```python
# Source pattern derived from backend/app/api/v1/public.py::_chat_degraded_contract [VERIFIED]
if not settings.CHAT_SEARCH_ENABLED:
    degraded = _chat_degraded_contract(
        payload.message,
        "chat_disabled",  # add handling for guidance/limitations coherently
        "A busca por chat está indisponível no momento. Use a busca manual para encontrar vagas.",
    )
    return ChatSearchResponse(
        interpretation=degraded,
        results=ChatSearchResults(items=[], page=payload.page, limit=payload.limit, total=0),
    )
```

### Pattern 3: No-PII structured event logging at request boundary
**What:** Wrap `chat_search` with `time.perf_counter()` and emit one `logger.info("chat_search", extra={...})` in `finally`/terminal paths carrying only safe aggregates: `outcome`, `reason`/`degradation_reason`, `latency_ms`, `results_count`, `total`, `page`, `limit` (and optionally status class). Never log `payload.message`, extracted text, contacts, or exception internals to users. [VERIFIED: D-07, `public.py` current logging, `core/logging.py`]
**When to use:** Every chat-search request outcome (success, degraded, disabled, controlled_error/5xx) for operational diagnosis.
**Example:**
```python
# Source: 22-AI-SPEC §4 guidance, adapted to existing public.py seam [CITED: 22-AI-SPEC]
start = time.perf_counter()
outcome, reason, items_count, total = "success", None, 0, 0
try:
    ...
finally:
    logger.info(
        "chat_search",
        extra={
            "outcome": outcome,
            "reason": reason,
            "latency_ms": int((time.perf_counter() - start) * 1000),
            "results_count": items_count,
            "total": total,
        },
    )
```

### Anti-Patterns to Avoid
- **Logging message/PII/contacts or echoing internals:** violates D-07/QA-03/privacy; never include `payload.message`, raw exception strings shown to clients, or contact fields. [VERIFIED: D-07, PROJECT core value]
- **Coupling kill-switch to board/list jobs:** do not gate `GET /public/jobs`, server-rendered board fetch, filters, pagination, detail, or reveal on chat config. [VERIFIED: D-06, `page.tsx`, `public.py` list/get routes]
- **Inventing semantic/link/ID “parecidas” support:** matrix/tests must state and assert textual-seed-only/limitation behavior (D-02). [VERIFIED: D-02]
- **Adding Playwright/RTL/browser E2E infra:** out of scope for Phase 22; use runbook + pure Vitest logic only. [VERIFIED: D-04]
- **Duplicating new parallel test suites:** extend existing intent/chat/chatApply tests and fixtures instead. [VERIFIED: D-05]
- **Letting LLM influence results/corpus:** results must remain `list_published` for effective `applied_params` and `JobPublic` only. [VERIFIED: API-01/03, `public.py`]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Intent extraction/repair/timeout behavior | New ad-hoc HTTP/LLM glue | Existing `intent/client.py` + `parser.py` seam with injectable fake client/sleep | Already bounded, schema-validated, mockable; preserves contracts. [VERIFIED] |
| City/sort normalization & applied params | Custom parsing in endpoint/UI | `services/cities.resolve_city/resolve_sort`, `intent/mapper.py`, `filters.normalizeFilters` | Single source of whitelist/determinism; avoids drift/invention. [VERIFIED] |
| Deterministic search & pagination totals | Separate chat query logic | `crud.jobs.list_published` shared predicates | Guarantees equivalence to public jobs endpoint and consistent totals. [VERIFIED] |
| Public contact safety | New chat-specific payloads | `schemas.job.JobPublic` / existing reveal flow | Structural prevention of contact leakage. [VERIFIED] |
| Rate limiting & pt-BR 429 handling | Manual counters/middleware | `core.ratelimit.limiter` + existing handler | Consistent per-IP+endpoint semantics and `Retry-After`. [VERIFIED] |
| Canonical board URL application | Manual query-string assembly in chat | `buildBoardHref` + `normalizeFilters` + `appliedParamsToBoardFilters`/`canApplyChatToBoard` | Preserves canonical contract (`page=1`, `vaga` cleared) and existing tests. [VERIFIED] |

**Key insight:** Phase 22 value comes from tightening contracts, evidence, and ops controls around existing seams; custom parallel paths increase regression and privacy risk.

## Common Pitfalls

### Pitfall 1: Kill-switch regresses the public board
**What goes wrong:** Chat toggle disables/breaks shared UI or backend paths, making manual list/search/detail unusable.
**Why it happens:** Shared state/rendering or endpoint coupling; frontend blocks on status fetch.
**How to avoid:** Gate only chat entry/endpoint; keep `GET /public/jobs` and board components independent; make status check non-blocking for board render and fail safe (backend remains authoritative with controlled disabled response). [VERIFIED: D-06, 22-UI-SPEC]
**Warning signs:** `page.tsx` board data fetch or toolbar/grid depend on chat status; launcher renders as dead control.

### Pitfall 2: Disabled-state contract drift (backend vs frontend)
**What goes wrong:** Frontend can’t recognize “disabled” and shows generic errors or keeps chat interactive.
**Why it happens:** No stable status signal or inconsistent `meta.degradation_reason`/guidance handling.
**How to avoid:** Define one explicit disabled reason (e.g. `chat_disabled`) and/or a tiny status endpoint returning enabled flag; handle in `api.ts`/`ChatWidget` and assert in API/UI-logic tests. [VERIFIED: D-06 discretion]
**Warning signs:** 500s, opaque messages, or launcher visible while endpoint refuses use.

### Pitfall 3: PII leakage in “structured” logs
**What goes wrong:** Message text, inferred entities, or contacts appear in logs/extras/exceptions.
**Why it happens:** Logging full payloads/contract dumps or exception messages containing user text.
**How to avoid:** Log only outcome/reason/latency/counts/status; never include `message`, `understood.q` raw user content dumps, or contact fields; add tests with `caplog` asserting absence. [VERIFIED: D-07]
**Warning signs:** `extra` or formatted logs containing free-text query.

### Pitfall 4: False confidence in MVP examples (non-deterministic evidence)
**What goes wrong:** QA-01 marked validated but depends on live LLM variability; “parecidas” implied as semantic/link-supported.
**Why it happens:** No mocked-contract determinism or missing explicit limitations in matrix.
**How to avoid:** Record contrato esperado/observado per D-03; automate deterministic cases by mocking intent seam; explicitly document Campinas/salary-modality-contract-seniority limits and textual-seed-only “parecidas” (no semantic/vector/link/ID). [VERIFIED: D-01..D-03, mapper behavior]
**Warning signs:** Matrix lacks observed evidence refs or omits “lacunas explícitas”.

### Pitfall 5: Test environment blind spots (DB-dependent harness)
**What goes wrong:** Suites assumed runnable fail in environments without migrated test DB; CI/agents report false negatives.
**Why it happens:** `backend/tests/conftest.py` skips DB-dependent tests when `TEST_DATABASE_URL`/`DATABASE_URL` unset and only whitelists specific DB-independent files (intent/chat suites not currently whitelisted). [VERIFIED: `backend/tests/conftest.py`]
**How to avoid:** Document prerequisites/commands; for Phase 22, consider whitelisting pure intent unit tests as DB-independent if they need no fixtures, and keep DB-backed chat API tests explicitly marked as requiring test DB. Do not claim execution without environment.
**Warning signs:** “0 tests collected/skipped” due to harness, not code.

### Pitfall 6: Apply-to-board edge cases create misleading no-op UX
**What goes wrong:** “Aplicar no board” enabled for unsupported/unknown params or disabled-state flows.
**Why it happens:** `canApplyChatToBoard` treats any non-empty `city` string as applicable before whitelist normalization (`frontend/lib/chatApply.ts`), and disabled/degraded responses may be mishandled. [VERIFIED: `frontend/lib/chatApply.ts`, `21-VERIFICATION.md` warning]
**How to avoid:** Keep gating conservative (respect degraded/disabled), assert mapping via `normalizeFilters`, and document/cover known edge cases in QA artifacts (fix only if in-scope and non-regressive).

## Code Examples

Verified patterns from repository sources:

### Chat-search orchestration seam (mockable, deterministic retrieval)
```python
# Source: backend/app/api/v1/public.py [VERIFIED]
@router.post("/chat-search", response_model=ChatSearchResponse)
@limiter.limit(chat_search_limit)
async def chat_search(request: Request, payload: ChatSearchRequest, session: AsyncSession = Depends(get_session)) -> ChatSearchResponse:
    settings = get_settings()
    chat_timeout = getattr(settings, "CHAT_SEARCH_INTENT_TIMEOUT_SECONDS", 12)
    try:
        contract = await extract_and_map_intent(payload.message, settings, timeout_seconds=chat_timeout)
    except Exception as exc:
        # ... classify timeout vs llm_unavailable -> degraded 200 with guidance, no auto results
        ...
    if contract is None or _is_effectively_no_params(contract):
        ...  # degraded no_extractable_params
    contract = _apply_approx_guidance(contract)
    items, total = await list_published(session, page=payload.page, limit=payload.limit,
        q=contract.applied_params.q, city=contract.applied_params.city, sort=(contract.applied_params.sort or "recentes"))
    return ChatSearchResponse(interpretation=contract, results=ChatSearchResults(..., total=total))
```

### Mapper guarantees relevant to MVP examples
```python
# Source: backend/app/services/intent/mapper.py [VERIFIED]
# - City applied only via whitelist/obvious-safe mentions (SP/RJ/BH/Remoto); others -> not_in_whitelist/ignored.
# - Sort applied only when explicit in raw text; conflicts -> conflict_resolved (not applied).
# - Salary understood but never structured filter -> ignored + unsupported_structured_filter limitation.
# - work_mode/contract_type/seniority: aproximado via textual q terms when influencing q, else ignored/non-native limited.
# - Remote modality can map to applied city "Remoto" when safe.
```

### Frontend chat send + apply + canonical detail
```ts
// Source: frontend/components/board/chat/ChatWidget.tsx, frontend/lib/api.ts, frontend/lib/chatApply.ts [VERIFIED]
const response = await chatSearch({ message: trimmed, page: 1, limit: 20 });
// ... store interpretation/items/total; render interpretation + results
if (canApplyChatToBoard(response.interpretation)) {
  const filters = appliedParamsToBoardFilters(response.interpretation.applied_params);
  const href = buildBoardHref({ ...filters, page: 1, vaga: null });
  router.replace(href, { scroll: false });
  setIsOpen(false);
}
// detail: minimize chat, sync ?vaga, open <JobDetailDialog job={selectedJob} open ... />
```

### Existing API test shape (DB + monkeypatch seam)
```python
# Source: backend/tests/test_chat_search_api.py [VERIFIED]
async def fake_extract(*args, **kwargs): return interpretation
monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)
resp = await client.post("/api/v1/public/chat-search", json={"message": "...", "page": 1, "limit": 20})
assert resp.status_code == 200
# compare ids/total with GET /api/v1/public/jobs and assert no contact_* in items
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LLM over vaga corpus / invented filters | LLM extracts params only; deterministic `list_published` over `JobPublic` | Phases 19–20 (v1.3) | Preserves cost/privacy/determinism; QA must verify equivalence and no contact/PII leakage. [VERIFIED] |
| Chat always-on assumption | Chat behind operational kill-switch/config with safe disabled signaling (Phase 22 target) | Phase 22 (planned) | Board remains usable during abuse/cost/degradation; requires end-to-end enforcement/signaling/logging. [VERIFIED: QA-03/D-06] |
| Ad-hoc validation | Versioned MVP matrix + consolidated deterministic automated suites + guided manual runbook | Phase 22 (planned) | Traceable evidence for QA-01/02 without new E2E infra. [VERIFIED: D-01..D-05] |

**Deprecated/outdated:**
- Assuming Groq `llama-3.1-8b-instant`/`llama-3.3-70b` as current defaults: project uses `openai/gpt-oss-20b` (+120b fallback). [VERIFIED: `AGENTS.md`, `config.py`]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `frontend/package.json` devDependency `vitest` (^2.1.9) is the executable version in typical envs even though other docs mention 5.x; commands should rely on local `npx vitest`/scripts. | Validation Architecture / Environment | Test command or API mismatch; planner should pin to `npm --prefix frontend run test` / existing scripts. |
| A2 | A minimal public status signal (e.g. `GET /api/v1/public/chat-search/status` or equivalent enabled flag) is acceptable under D-06 discretion to let frontend hide launcher proactively without blocking board render. | Architecture Patterns / Pitfalls | If maintainers prefer a different mechanism, implementation changes shape but must still satisfy “consult/sinalizar estado e ocultar/desabilitar entrada”. |
| A3 | `backend/tests/conftest.py` DB-skip whitelist can be safely extended to include pure intent unit tests (schema/mapper/parser/client) if they remain fixture-independent, improving QA-02 executability without DB. | Validation Architecture / Pitfalls | If those tests rely (now/future) on app/db fixtures, they must stay DB-gated; planner should verify per-file dependencies. |
| A4 | “Carregar mais” pagination and degraded/disabled UI states are sufficiently covered by existing Phase 21 UAT evidence for regression, needing only targeted runbook steps/cases in Phase 22 (not new browser automation). | QA-02 / Open Questions | Residual UI regressions could slip; mitigated by explicit manual checklist and preserved pure-logic tests. |

## Open Questions (RESOLVED)

1. **Exact disabled-state signaling shape and frontend fail-safe default** — **RESOLVED (Plans 22-01/02/03).**
   - What we know: D-06/UI-SPEC require backend-safe controlled response and frontend consult/signal to hide launcher/panel when disabled; board must not block. [VERIFIED]
   - Resolution: enforce `CHAT_SEARCH_ENABLED` at the backend chat boundary with a controlled 200 disabled contract (`degradation_reason="chat_disabled"`, safe pt-BR guidance, empty `JobPublic` results, `applied_params` null, no internals/LLM/DB coupling) and expose an explicit lightweight public status signal returning `{"enabled": boolean}` for frontend consumption. Frontend consults status and hides the launcher/panel only when disabled is confirmed (backend remains authoritative; status uncertainty must not block board render/manual search and fail-safe behavior/tests/runbook follow the planned contract).

2. **Structured log format compatibility with `configure_logging`** — **RESOLVED (Plans 22-01/03).**
   - What we know: stdlib text formatter (`%(asctime)s %(levelname)s %(name)s %(message)s`) is configured; `extra` fields are attachable to records. [VERIFIED: `core/logging.py`]
   - Resolution: emit one stable `logger.info("chat_search", extra={...})` per request at the chat boundary with safe fields only (`outcome`, `reason`/`degradation_reason`, `latency_ms`, `results_count`/`total`, `page`/`limit` as applicable). No new logging dependencies and never log message text, contacts, or PII; correctness verified via `caplog`/record inspection in tests.

3. **DB-backed test executability in target environment** — **RESOLVED (Plans 22-01/03, validation artifacts).**
   - What we know: most suites (including `test_chat_search_api.py`) are skipped without `TEST_DATABASE_URL`/`DATABASE_URL`; pure intent files currently not in DB-independent whitelist. [VERIFIED: `conftest.py`]
   - Resolution: treat DB-backed `test_chat_search_api.py` execution as prerequisite/environment-gated (`TEST_DATABASE_URL`/`DATABASE_URL` with migrated schema) and do not claim execution without environment evidence. Whitelist truly fixture-free pure intent unit suites as DB-independent where safe to improve QA-02 executability, and capture MVP/manual evidence in `22-MVP-EXAMPLES.md`/`22-MANUAL-UAT.md` per D-01/D-03/D-04.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Backend/tests | ✓ | 3.11.4 (`backend/.python-version`) [VERIFIED] | — |
| Node.js / npm | Frontend tests/build | ✓ | Node present in env (npm in `frontend/`) [VERIFIED: `frontend/package.json` exists] | Run only backend-pure scopes if unavailable (not expected) |
| pytest/pytest-asyncio | QA-02 backend suites | ? | Declared in `pyproject.toml` (9.1.1 / >=1,<2) [VERIFIED] | Install dev deps in `backend` venv; skip with documented prerequisite if unavailable |
| Vitest | QA-02 UI logic tests | ? | Declared `^2.1.9` + script `test` [VERIFIED] | `npm ci` in `frontend`; manual runbook covers UI behavior per D-04 |
| Postgres test DB (`TEST_DATABASE_URL`/`DATABASE_URL`) + migrations/schema | DB-backed API tests (`test_chat_search_api.py`, fixtures) | ? | Harness requires URL; schema assumed provisioned externally [VERIFIED: `conftest.py`] | Run pure intent tests + frontend logic tests; document DB-backed as handoff/prerequisite |
| Groq API/network | Live LLM calls | Not required | N/A | **Must not be used:** all automated extraction/chat tests mock seam/client [VERIFIED: D-05, existing tests] |
| Playwright / RTL | Browser E2E | ✗ (not installed/required) | — | Versioned manual/UAT runbook + Vitest pure logic [VERIFIED: D-04, `frontend/vitest.config.ts`] |

**Missing dependencies with no fallback:**
- None blocking Phase 22 artifact delivery. Deterministic automated coverage is feasible without live LLM/Playwright/RTL; DB-backed execution is prerequisite-gated (not “no fallback” for evidence, but required for that subset).

**Missing dependencies with fallback:**
- Migrated test DB unavailable → cannot execute DB-backed `test_chat_search_api.py` in-place; rely on pure intent suites + Vitest + documented runbook and state prerequisite explicitly. [VERIFIED]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Backend: pytest 9.1.1 + pytest-asyncio (auto, `backend/pyproject.toml`) [VERIFIED]. Frontend: Vitest ^2.1.9, node env, `lib/**/*.test.ts` (`frontend/vitest.config.ts`) [VERIFIED]. |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`), `backend/tests/conftest.py`; `frontend/vitest.config.ts`, `frontend/package.json` scripts. [VERIFIED] |
| Quick run command | `cd backend && pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py` (pure seam/logic; see DB-harness caveat) and/or `cd frontend && npm run test:chat` [VERIFIED] |
| Full suite command | `cd backend && pytest -q` (requires configured/migrated test DB for DB-dependent tests) ; `cd frontend && npm test` [VERIFIED] |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QA-01 | 5 exemplos MVP: interpretação/`applied_params`/status/limitações/guidance, combinações e lacunas (Campinas whitelist, salário/modalidade/contrato/senioridade aproximados/não nativos, “parecidas” seed textual sem semântica/link/ID) com contrato esperado + observado | integration/unit (mocked intent) + documented matrix | `cd backend && pytest -q tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_chat_search_api.py -k "mvp or campinas or salary or parecid or remoto or estagio"` (targeted names to add) + manual evidence in `22-MVP-EXAMPLES.md` | ❌ Wave 0 (matrix + targeted MVP cases/gaps) |
| QA-02 | Extração/mapeamento/normalização e API chat-search com LLM mockado (equivalência `list_published`, privacidade `JobPublic` sem contatos, degradação/fallback, limites/proteções) + validação básica UI/E2E viável | unit/integration + manual/UAT + pure UI logic | `cd backend && pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py tests/test_chat_search_api.py tests/test_ratelimit.py`; `cd frontend && npm test` | ✅ partial (suites exist; consolidate/extend gaps) + ❌ Wave 0 `22-MANUAL-UAT.md` |
| QA-03 | Kill-switch/config fim-a-fim (backend seguro/controlado quando off, frontend sinaliza/oculta entrada) sem afetar board; logs estruturados sem PII (outcome/motivo/latência/contagens) | integration/unit (API + pure frontend helpers) + manual verification | `cd backend && pytest -q tests/test_chat_search_api.py -k "disabled or kill_switch or logging"` (cases to add, caplog/no-PII assertions); `cd frontend && npm test` (helpers if added) + runbook step | ❌ Wave 0 (feature + tests + runbook steps) |

### Sampling Rate
- **Per task commit:** Quick run — relevant backend intent/chat tests for touched scope (or pure subset) and `frontend npm run test:chat` / `npm test` when frontend logic touched. [VERIFIED: scripts/config]
- **Per wave merge:** `cd backend && pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py tests/test_chat_search_api.py tests/test_ratelimit.py` (DB-gated subset) + `cd frontend && npm test`. [VERIFIED]
- **Phase gate:** Targeted phase suites green in a capable environment (DB-backed where applicable) + QA-01 matrix and manual/UAT runbook completed with contrato esperado/observado evidence before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` — covers QA-01 (D-01/D-02/D-03, 5 exemplos + lacunas explícitas)
- [ ] `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` — covers QA-02/QA-03 UI viável (D-04), incluindo chat desativado/degradado e não-regressão do board/reveal
- [ ] `backend/tests/test_chat_search_api.py` (extend) — disabled/kill-switch response, structured no-PII logging assertions (`caplog`), MVP combination gaps not yet explicit (QA-01/02/03)
- [ ] `backend/tests/test_intent_mapper.py` / `test_intent_parser.py` / `test_intent_schema.py` / `test_intent_client.py` (extend/consolidate) — deterministic MVP/combination and classification cases (D-02/D-05)
- [ ] `frontend/lib/*.test.ts` (extend only if pure helpers added for status/disabled gating) — QA-02 logic viável (D-04)
- [ ] `backend/tests/conftest.py` (optional) — whitelist pure intent tests as DB-independent if confirmed fixture-free, to improve executability (discretion)
- [ ] Framework install: `cd backend && pip install -e ".[dev]"`; `cd frontend && npm ci` — if environments not prepared

*(If DB unavailable: treat DB-backed cases as environment-gated gaps for execution evidence, not as missing test code.)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Public chat-search and board are anonymous by design; admin paths unchanged/out of scope. [VERIFIED] |
| V3 Session Management | no | No user session/login introduced; chat state is client-memory only. [VERIFIED] |
| V4 Access Control | yes (abuse/availability control) | Kill-switch, per-IP+endpoint rate limiting, bounded input/timeouts on public chat endpoint. [VERIFIED: D-06, `ratelimit.py`, `config.py`] |
| V5 Input Validation | yes | Pydantic request validation (`message` trim/len, `page/limit`), strict intent schemas, whitelist normalization, safe pt-BR errors. [VERIFIED: `schemas/chat.py`, `intent/*`, `cities.py`] |
| V6 Cryptography | no (no new crypto) | No secrets/tokens/crypto added; existing secret handling unchanged. [VERIFIED] |

### Known Threat Patterns for {FastAPI + Groq intent + public Next.js UI}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt/input injection influencing extraction | Tampering / Elevation of intent | Treat user text as untrusted data (delimiters/sanitization), strict JSON schema + Pydantic validation + deterministic server mapping/whitelists. [VERIFIED: `intent/client.py`, `mapper.py`] |
| Abuse/cost amplification & DoS on LLM endpoint | Denial of Service | Dedicated rate limit, message/timeout caps, kill-switch returns cheap controlled response without LLM/DB. [VERIFIED: D-06/D-07, `ratelimit.py`, `config.py`] |
| PII/contact leakage (responses or logs) | Information Disclosure | `JobPublic`-only responses (no contacts), never log message/PII/contacts, guidance without internals. [VERIFIED: D-07, `JobPublic`, `public.py`] |
| Misleading capability claims (unsupported filters/semantic similarity) | Tampering (integrity of info) | `field_statuses`/`limitations`/`meta.guidance` signaling; “parecidas” textual-seed-only documented. [VERIFIED: D-02/D-03, mapper/api] |
| Availability regression of core board | Denial of Service / Reliability | Decouple chat from `GET /public/jobs` and manual UI; frontend hide/disable without blocking board render. [VERIFIED: D-06, 22-UI-SPEC] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-CONTEXT.md`, `22-AI-SPEC.md`, `22-UI-SPEC.md` — phase decisions, framework/eval/guardrails, UI delta. [VERIFIED]
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, `AGENTS.md` — requirements QA-01..03, scope/contracts, constraints/history. [VERIFIED]
- `.planning/phases/19-*/19-CONTEXT.md`, `20-*/20-CONTEXT.md`, `21-*/21-CONTEXT.md`, `21-VERIFICATION.md`, `21-HUMAN-UAT.md` — upstream contracts and verification/UAT evidence. [VERIFIED]
- Backend implementation: `backend/app/api/v1/public.py`, `backend/app/services/intent/{schema,parser,mapper,client}.py`, `backend/app/schemas/{chat,job}.py`, `backend/app/crud/jobs.py`, `backend/app/services/cities.py`, `backend/app/core/{config,ratelimit,logging}.py`, `backend/app/main.py`, `backend/.env.example`. [VERIFIED]
- Frontend implementation: `frontend/app/(public)/page.tsx`, `frontend/components/board/chat/{ChatWidget,ChatPanel,ChatLauncher,ChatThread,ChatComposer,ChatInterpretation,ChatResultsList,ChatResultItem}.tsx`, `frontend/lib/{api,chatApply,chatApply.test,filters}.ts`, `frontend/{package.json,vitest.config.ts}`. [VERIFIED]
- Tests/fixtures: `backend/tests/{test_intent_schema,test_intent_mapper,test_intent_parser,test_intent_client,test_chat_search_api,test_ratelimit,conftest}.py`, `backend/pyproject.toml`. [VERIFIED]

### Secondary (MEDIUM confidence)
- None required; research grounded in repository state and phase specs.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versions/patterns confirmed from repo manifests and code; no new stack introduced. [VERIFIED]
- Architecture: HIGH - integration points, data flow, and seams traced directly in current implementation. [VERIFIED]
- Pitfalls: HIGH - derived from locked decisions, UI/AI specs, and concrete code behaviors (logging, conftest gating, apply gating). [VERIFIED]

**Research date:** 2026-11-18
**Valid until:** 2026-12-18 (stable internal architecture; recheck if chat endpoint/contracts/config/tests change)
