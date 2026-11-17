---
phase: 20-api-publica-de-chat-search-resiliente
verified: 2026-11-17T23:45:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 20: API pública de chat-search resiliente Verification Report

**Phase Goal:** Usuários e o frontend público podem obter resultados de busca por chat via um endpoint seguro, rápido o suficiente e consistente com o contrato público atual
**Verified:** 2026-11-17T23:45:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Usuário (via cliente autorizado do board) envia mensagem e recebe interpretação + resultados pagináveis/limitados no formato público (`JobPublic`, com `total`), sem contatos expostos | ✓ VERIFIED | `backend/app/api/v1/public.py:253-321` expõe `POST /chat-search` com `response_model=ChatSearchResponse`; monta `results` com `JobPublic.model_validate(job)` e `total` de `list_published`; `backend/app/schemas/chat.py:10-40` define envelope `interpretation: IntentContract` + `results.items: list[JobPublic]`; `backend/tests/test_chat_search_api.py` (`equivalent_to_public_jobs_and_hides_contacts`, `response_has_interpretation_and_results_contract`) passou em execução local (9/9). |
| 2 | Resultados refletem busca determinística equivalente à lógica pública existente (`GET /api/v1/public/jobs` / `list_published`) para parâmetros efetivamente aplicados | ✓ VERIFIED | `backend/app/api/v1/public.py:304-320` usa apenas `applied_params` finais (`q/city/sort`) e chama `list_published(session, page, limit, q=applied.q, city=applied.city, sort=(applied.sort or "recentes"))`; `backend/app/crud/jobs.py:53-91` aplica mesmo predicado publicado+não-expirado e retorna `(items,total)` no mesmo filtro; teste de equivalência compara ids/`total` com `GET /api/v1/public/jobs`. |
| 3 | Requisições abusivas/inválidas são contidas por proteções ativas (rate limit por IP, limites de tamanho/tempo) e retornam erros pt-BR seguros sem vazar detalhes internos | ✓ VERIFIED | `backend/app/api/v1/public.py:253-254` aplica `@limiter.limit(chat_search_limit)` (IP+endpoint via `backend/app/core/ratelimit.py:87-108`); `backend/app/schemas/chat.py:14-24`/`backend/app/core/config.py:56-59` limitam mensagem (trim, obrigatória, max 400) e paginação; `public.py:262-271,273-287,324-328` usa timeout curto dedicado `CHAT_SEARCH_INTENT_TIMEOUT_SECONDS`, 400/422/500 com `detail` pt-BR e logging server-side; testes validam 4xx, 429 com `Retry-After`/detail pt-BR e ausência de vazamento óbvio. |
| 4 | Em falha/timeout/indisponibilidade do LLM, usuário recebe fallback controlado com orientação para busca manual/keyword em vez de erro opaco | ✓ VERIFIED | `backend/app/api/v1/public.py:268-301` captura falha de `extract_and_map_intent`/caso sem parâmetros úteis e retorna 200 degradado com `results` vazio (`items=[]`, `total=0`, page/limit preservados), `meta.degraded=True`, `degradation_reason` (`timeout`/`llm_unavailable`/`no_extractable_params`) e `meta.guidance` pt-BR (`_CHAT_GUIDANCE_*`); testes cobrem indisponibilidade, timeout e sem parâmetros extraíveis. |
| 5 | Filtros não nativos (salário, modalidade, tipo de contrato/senioridade) e locais fora da whitelist recebem apenas estratégia limitada/aproximada e sinalização explícita, sem afirmar filtragem inexistente | ✓ VERIFIED | `backend/app/services/intent/mapper.py` produz `applied_params` apenas com `q/city/sort` e marca campos não nativos como aproximados/ignorados com `limitations`/`reason_code` (`unsupported_structured_filter`, `textual_approximation_in_q`, `non_native_fields_limited`) e cidade fora da whitelist como `not_in_whitelist` sem inferir SP/RJ/BH; `backend/app/api/v1/public.py:112-133,303` preserva/completa sinalização (`_apply_approx_guidance`) e não pós-filtra resultados; teste `partial_support_and_non_whitelist_city_signaled` valida contrato honesto. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/schemas/chat.py` | Schemas request/response do chat-search | ✓ VERIFIED | Define `ChatSearchRequest` (mensagem trim/obrigatória, `page>=1`, `limit` 1-50), `ChatSearchResults` (`items: list[JobPublic]`, `page/limit/total`) e `ChatSearchResponse` (`interpretation: IntentContract`). |
| `backend/app/api/v1/public.py` | Endpoint público com orquestração segura | ✓ VERIFIED | Contém `@router.post("/chat-search")`, `@limiter.limit(chat_search_limit)`, chamada `extract_and_map_intent(..., timeout_seconds=chat_timeout)`, busca `list_published(...)` por `applied_params`, serialização `JobPublic.model_validate`, fallback degradado 200 com `items=[]/total=0`, `degraded/guidance/degradation_reason`, e erros pt-BR (400/500) sem expor stack interna. |
| `backend/app/core/config.py` | Knobs dedicados do chat-search | ✓ VERIFIED | Expõe `CHAT_SEARCH_RATE_LIMIT="20/minute"`, `CHAT_SEARCH_MAX_MESSAGE_CHARS=400`, `CHAT_SEARCH_INTENT_TIMEOUT_SECONDS=12`. |
| `backend/app/core/ratelimit.py` | Rate limit dedicado por IP+endpoint | ✓ VERIFIED | Expõe `chat_search_limit()` lendo setting; reusa `SafeLimiter(..., key_style="endpoint")` e handler 429 pt-BR com `Retry-After`. |
| `backend/app/services/intent/client.py` | Timeout dedicado retrocompatível no seam de intent | ✓ VERIFIED | `call_intent_llm(..., timeout_seconds=...)` e helpers propagam timeout efetivo para client/create; fallback para `GROQ_TIMEOUT_SECONDS` preservado. |
| `backend/app/services/intent/parser.py` | Propagação de timeout e degradação segura | ✓ VERIFIED | `parse_intent`/`extract_and_map_intent` aceitam e repassam `timeout_seconds`; falhas degradam para contrato seguro (`build_empty_intent`). |
| `backend/tests/test_chat_search_api.py` | Cobertura automatizada API-01/02/03 | ✓ VERIFIED | 327 linhas, 9 testes cobrindo equivalência/privacidade/paginação, validação, 429+Retry-After, fallback degradado (falha/timeout/sem params) e sinalização parcial/whitelist; execução: `pytest tests/test_chat_search_api.py -x` → 9 passed. |
| `backend/.env.example` | Documentação dos knobs de chat-search | ✓ VERIFIED | Inclui `CHAT_SEARCH_RATE_LIMIT`, `CHAT_SEARCH_MAX_MESSAGE_CHARS`, `CHAT_SEARCH_INTENT_TIMEOUT_SECONDS` com comentários. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/api/v1/public.py` | `app.services.intent.extract_and_map_intent` | Orquestração da mensagem NL → `IntentContract` server-authoritative | ✓ WIRED | Import + chamada com `timeout_seconds=chat_timeout`; resultado usado para decisão de busca/degradação. |
| `backend/app/api/v1/public.py` | `app.crud.jobs.list_published` | Busca determinística com `applied_params.q/city/sort` + `page/limit` e `total` no mesmo predicado | ✓ WIRED | Chamada direta retorna `(items,total)` serializados em envelope de resultados. |
| `backend/app/api/v1/public.py` | `app.core.ratelimit.limiter`/`chat_search_limit` | Proteção por IP+endpoint com 429 pt-BR/Retry-After | ✓ WIRED | Decorator na rota e helper de limite dedicado configurados; handler global registrado no app. |
| `backend/app/api/v1/public.py` | `backend/app/schemas/chat.py` | Contrato HTTP tipado (request/response) | ✓ WIRED | Endpoint recebe `ChatSearchRequest` e retorna `ChatSearchResponse`. |
| `backend/app/schemas/chat.py` | `app.schemas.job.JobPublic` / `app.services.intent.schema.IntentContract` | Envelope sem contato + interpretação canônica | ✓ WIRED | Tipos compostos garantem shape público/contact-free. |
| `backend/tests/test_chat_search_api.py` | Endpoint/intent/crud público | Mocks + requests HTTP + comparação com `/api/v1/public/jobs` | ✓ WIRED | Exercita caminho real do endpoint e contratos observáveis. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `backend/app/api/v1/public.py` (`chat_search`) | `interpretation` | `extract_and_map_intent` (Groq seam) ou `_chat_degraded_contract` determinístico | Sim (contrato estruturado; fallback determinístico quando indisponível) | ✓ FLOWING |
| `backend/app/api/v1/public.py` (`chat_search`) | `results.items/total` | `list_published` → SQLAlchemy query publicada/não expirada (`backend/app/crud/jobs.py`) | Sim (consulta DB real com mesmo predicado para itens e total) | ✓ FLOWING |
| `backend/app/api/v1/public.py` (`chat_search`) degraded | `results.items/total` | Construção explícita controlada (`items=[]`, `total=0`) | Intencional por design (sem resultados automáticos em falha/sem params) | ✓ FLOWING (safe degraded) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Suíte automatizada do contrato chat-search (equivalência, privacidade, validação/rate limit, fallback, suporte parcial) | `cd backend && python -m pytest tests/test_chat_search_api.py -x` | 9 passed in 46.84s | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| API-01 | 20-01, 20-02 | Endpoint público de chat-search executa extração→mapeamento→busca determinística reutilizando contrato/ lógica pública e retorna interpretação + resultados pagináveis em `JobPublic` (sem contatos) com `total` | ✓ SATISFIED | `POST /chat-search` implementado com `extract_and_map_intent` + `list_published` + `JobPublic`; testes de equivalência/contrato/privacidade passando. |
| API-02 | 20-01, 20-02 | Proteções de abuso/custo e resiliência: rate limit por IP, limites de tamanho/tempo, erros pt-BR seguros e fallback controlado em falha/timeout/indisponibilidade do LLM | ✓ SATISFIED | Limite de mensagem/paginação, rate limit dedicado, timeout curto de intent, 4xx/429/500 pt-BR seguros, fallback 200 degradado com orientação; testes específicos passando. |
| API-03 | 20-01, 20-02 | Campos sem filtro nativo recebem estratégia explícita/limitada e sinalização de suporte parcial/aproximado sem afirmar filtragem inexistente | ✓ SATISFIED | `applied_params` restrito a `q/city/sort`; aproximações/limites e cidades fora da whitelist sinalizados via `field_statuses/limitations/meta.guidance`; sem inferência indevida; teste de suporte parcial passando. |

**Orphaned requirements for Phase 20:** None (REQUIREMENTS.md maps API-01, API-02, API-03 to Phase 20 and both plans declare them).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| - | - | - | - | Nenhum TODO/FIXME/placeholder/stub detectado nos artefatos modificados do chat-search (`config.py`, `ratelimit.py`, `schemas/chat.py`, `public.py`, `intent/client.py`, `intent/parser.py`, `tests/test_chat_search_api.py`, `.env.example`). |

### Human Verification Required

None.

### Gaps Summary

No gaps found. A fase entrega o endpoint público `/api/v1/public/chat-search` com contrato interpretação+resultados pagináveis em `JobPublic` (sem contatos), busca determinística server-authoritative equivalente ao contrato público, proteções ativas e fallback/erros pt-BR seguros, além de sinalização honesta para suporte parcial/aproximações. Evidência automatizada local: `backend/tests/test_chat_search_api.py` com 9 testes aprovados.

---

_Verified: 2026-11-17T23:45:00Z_
_Verifier: OpenCode (gsd-verifier)_
