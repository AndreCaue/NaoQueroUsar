---
phase: 20
slug: api-publica-de-chat-search-resiliente
status: audited
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-20
updated: 2026-11-20
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + pytest-asyncio (backend, repo padrão) |
| **Config file** | `backend/pyproject.toml`, `backend/tests/conftest.py` |
| **Quick run command** | `cd backend && python -m pytest -q tests/test_chat_search_api.py` |
| **Full suite command** | `cd backend && python -m pytest -q` (ou suíte alvo incluindo `tests/test_chat_search_api.py tests/test_ratelimit.py` conforme ambiente) |
| **Estimated runtime** | ~30-90 seconds (subset chat-search; ambiente DB-dependente quando aplicável) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest -q tests/test_chat_search_api.py` (ou subconjunto mais próximo quando alterando intent/chat/rate limit).
- **After every plan wave:** Run suíte alvo backend relacionada a chat-search/intenção/rate limit (ex.: `tests/test_chat_search_api.py`, `tests/test_ratelimit.py` e testes de intent impactados).
- **Before `/gsd-verify-work`:** Evidência automatizada do contrato chat-search verde e `20-VERIFICATION.md` consistente (status passed).
- **Max feedback latency:** 120 seconds

---

## Per-task / Requirement Verification Map

| ID | Plan/Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|----|-----------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-V-01 | 20-01/20-02 | API-01 | V5/Tampering, Info Disclosure | `POST /api/v1/public/chat-search` retorna interpretação + resultados pagináveis em `JobPublic` (com `total`) sem contatos; busca determinística equivalente a `GET /api/v1/public/jobs` para `applied_params` efetivos via `list_published` | integration (mocked seam) | `cd backend && python -m pytest -q tests/test_chat_search_api.py` | ✅ `backend/tests/test_chat_search_api.py` | ✅ green (evidência `20-VERIFICATION.md`: 9 passed) |
| 20-V-02 | 20-01/20-02 | API-02 | V4/DoS, V5 | Proteções ativas (rate limit por IP, limites de mensagem/paginação, timeout dedicado), erros pt-BR seguros e fallback 200 degradado controlado (`llm_unavailable`/`timeout`/`no_extractable_params`) sem detalhes internos | integration/unit (mocked seam) | `cd backend && python -m pytest -q tests/test_chat_search_api.py` | ✅ `backend/tests/test_chat_search_api.py`, `backend/app/core/ratelimit.py`, `backend/app/core/config.py` | ✅ green |
| 20-V-03 | 20-01/20-02 | API-03 | Integrity/Tampering | Campos não nativos (salário/modalidade/contrato/senioridade) e cidades fora da whitelist recebem apenas estratégia limitada/aproximada com sinalização explícita; nunca afirmar filtragem inexistente; `applied_params` restrito a `q/city/sort` | integration/unit (determinístico, seam mockado) | `cd backend && python -m pytest -q tests/test_chat_search_api.py` | ✅ `backend/tests/test_chat_search_api.py`, `backend/app/services/intent/mapper.py`, `backend/app/api/v1/public.py` | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Evidência principal:** `.planning/phases/20-api-publica-de-chat-search-resiliente/20-VERIFICATION.md` — `status: passed`, score 5/5 must-haves, suíte `backend/tests/test_chat_search_api.py` executada com **9 passed** (equivalência/privacidade/paginação, validação, 429+Retry-After, fallback degradado e sinalização parcial/whitelist), com LLM/seam mockado.

---

## Wave 0 Requirements

- [x] `backend/tests/test_chat_search_api.py` — cobertura automatizada dos contratos API-01/API-02/API-03 (equivalência com `/api/v1/public/jobs`, privacidade `JobPublic` sem contatos, limites/rate limit/timeout, fallback degradado, suporte parcial/sinalização).
- [x] `backend/app/schemas/chat.py` — contrato HTTP tipado (request/response, `IntentContract` + `JobPublic` sem contatos).
- [x] `backend/app/api/v1/public.py` — endpoint `POST /api/v1/public/chat-search` (orquestração intent→`list_published`, proteções, erros pt-BR seguros, fallback 200 controlado).
- [x] `backend/app/core/config.py` e `backend/app/core/ratelimit.py` — knobs/limite dedicado (`CHAT_SEARCH_RATE_LIMIT`, `CHAT_SEARCH_MAX_MESSAGE_CHARS`, `CHAT_SEARCH_INTENT_TIMEOUT_SECONDS`, `chat_search_limit`).
- [x] Seam de intent com timeout propagável (`backend/app/services/intent/client.py`, `parser.py`) e mapeamento determinístico seguro (`backend/app/services/intent/mapper.py`).

*Infraestrutura/cobertura Wave 0 existente e rastreável no repositório.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| N/A | — | Contratos críticos de API-01..03 cobertos por testes automatizados determinísticos (seam mockado) e verificação da fase | Consultar `20-VERIFICATION.md` e reexecutar `cd backend && python -m pytest -q tests/test_chat_search_api.py` em ambiente capaz. |

*All phase behaviors have automated verification (com evidência documentada em `20-VERIFICATION.md`).*

---

## Validation Sign-Off

- [x] All tasks/requirements have `<automated>` verify or Wave 0 dependencies satisfied (evidência existente)
- [x] Sampling continuity: estratégia de execução incremental definida para escopo chat-search/intenção
- [x] Wave 0 covers all required references (testes/artefatos presentes)
- [x] No watch-mode flags
- [x] Feedback latency < 120s (subset alvo)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (retrospective audit, 2026-11-20; baseado em `20-VERIFICATION.md` passed e `backend/tests/test_chat_search_api.py`)
