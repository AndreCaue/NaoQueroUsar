---
phase: 22-qualidade-hardening-e-valida-o-operacional
verified: 2026-11-18T12:10:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Executar `22-MANUAL-UAT.md` (testes 1–6) em ambiente com backend/frontend e dados de teste"
    expected: "Todos os casos críticos registram `pass` (ou justificativa objetiva): board manual sem login, fluxo chat habilitado, interpretação/limites/carregar mais/aplicar, detalhe/revelação canônica sem contatos no chat, estados degradado/sem resultados com busca manual, e cenários com `CHAT_SEARCH_ENABLED=false`."
    why_human: "QA-02 (D-04) exige validação básica de UI/E2E viável por roteiro manual/UAT guiado (sem Playwright/RTL). O artefato `22-MANUAL-UAT.md` existe, mas todos os resultados estão pendentes (`result: [pending]`), sem evidência de execução assinada."
  - test: "Validar kill-switch fim-a-fim percebido na UI com `CHAT_SEARCH_ENABLED=false`"
    expected: "`GET /api/v1/public/chat-search/status` retorna `enabled:false`; `POST /api/v1/public/chat-search` responde 200 controlado (`chat_disabled`, guidance pt-BR, `applied_params` nulos, `results` vazio, sem contatos/internos); frontend oculta launcher/painel do chat e não bloqueia render; busca manual/filtros/paginação/detalhe/revelação continuam utilizáveis."
    why_human: "A implementação e testes automatizados cobrem contrato/gating, mas a percepção de UX em runtime (ocultação real do launcher/painel, ausência de bloqueio visual, navegação manual fluida) depende de ambiente/config/restart reais."
  - test: "Confirmar não-regressão do board público em estados degradado/sem resultados do chat"
    expected: "Mensagens/guidance pt-BR seguras sem detalhes internos, sem aplicação automática indevida ao board, atalho para busca manual funcional e contatos revelados apenas no fluxo canônico."
    why_human: "Coberto por testes de contrato/lógica pura e pelo runbook, porém a experiência integrada no board (copy, foco, transições, `carregar mais`, abertura de detalhe a partir do chat) requer validação manual no navegador."
---

# Phase 22: Qualidade, hardening e validação operacional — Verification Report

**Phase Goal:** O chatbot de busca opera de forma validada, observável e controlável sem regredir a experiência pública existente
**Verified:** 2026-11-18T12:10:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Os 5 exemplos-alvo do MVP têm comportamento validado e documentado (incluindo combinações e lacunas explícitas: seed textual limitado sem semântica/vetor/link/ID, Campinas fora da whitelist, campos não nativos aproximados/sinalizados). | ✓ VERIFIED | Matriz versionada `22-MVP-EXAMPLES.md` documenta os 5 casos com **Contrato esperado + Resultado observado**, evidências rastreáveis e lacunas obrigatórias (`seed textual limitado`, `sem similaridade semântica/vetorial`, `link/ID`, `Campinas`/`not_in_whitelist`, salário/modalidade/contrato/senioridade não nativos). Testes determinísticos: `backend/tests/test_intent_mapper.py` (`test_mvp_dev_pleno_sp_salary_not_native`, `test_mvp_remoto_frontend_react_clt_textual_approximation`, `test_mvp_parecidas_com_vaga_seed_textual_limitado_sem_link_id`, `test_mvp_analista_dados_campinas_ou_remoto_salary_combo`, `test_mvp_estagio_marketing_digital_em_sp`) e `backend/tests/test_chat_search_api.py` (5 casos `test_mvp_*` com `extract_and_map_intent` mockado, equivalência a `GET /api/v1/public/jobs`, `_assert_no_contacts`). |
| 2 | Existe suíte automatizada executável cobrindo extração/mapeamento/normalização e API de chat-search (LLM mockado), além de validação básica de UI/E2E viável no ambiente do projeto. | ✓ VERIFIED | Backend: intent puro whitelisted em `backend/tests/conftest.py` (`test_intent_schema.py`, `test_intent_mapper.py`, `test_intent_parser.py`, `test_intent_client.py`) e consolidado; `backend/tests/test_chat_search_api.py` cobre equivalência/paginação/contrato, privacidade sem contatos, invalidação/limites/rate-limit, degradação (`llm_unavailable`/timeout/`no_extractable_params`), `chat_disabled` e logging estruturado (`caplog`) sempre com seam mockado. Frontend viável: `frontend/lib/chatApply.ts` + `frontend/lib/chatApply.test.ts` (Vitest, lógica pura, inclui `chat_disabled`) sem Playwright/RTL. UI/E2E viável versionada por roteiro: `22-MANUAL-UAT.md`. Evidência de execução registrada nos artefatos/summaries: intent puras 30 passed e chat/rate-limit DB-backed 33 passed (commit `10ca96e`); execução DB-backed permanece pré-requisito de ambiente migrado. |
| 3 | Operadores dispõem de controles mínimos (kill-switch/config e logs/métricas básicas sem PII sensível) para desativar/ajustar o chat com segurança. | ✓ VERIFIED | Config/env: `backend/app/core/config.py` (`CHAT_SEARCH_ENABLED: bool = True`), `backend/.env.example` (`CHAT_SEARCH_ENABLED=true`). Backend enforcement/sinal: `backend/app/api/v1/public.py` (`GET /chat-search/status` -> `{"enabled": ...}`, short-circuit disabled antes de `extract_and_map_intent`/`list_published`, resposta 200 controlada `chat_disabled` com guidance pt-BR, `applied_params` nulos, `results` vazio, sem internos/contatos). Observabilidade: `logger.info("chat_search", extra={outcome,reason,latency_ms,results_count,total,page,limit})` em `finally`; sem `payload.message` em chamadas de logger. Frontend consome sinal/gating: `frontend/lib/api.ts` (`getChatSearchStatus`), `frontend/components/board/chat/ChatWidget.tsx` (consulta assíncrona, oculta launcher/painel quando desativado confirmado, trata resposta `chat_disabled` sem aplicar ao board), `frontend/lib/chatApply.ts` bloqueia `chat_disabled`/degradado. |
| 4 | Com chat desativado ou degradado, o board público existente continua utilizável para busca/listagem manual. | ✓ VERIFIED | Independência backend: `GET /api/v1/public/jobs` inalterado e testado (`test_public_jobs_remain_independent_when_chat_disabled`, `_assert_no_contacts`); kill-switch atua apenas no boundary do chat-search/status. Frontend: mount/status check não bloqueante, fail-safe sem bloquear board (`ChatWidget`), sem mutação automática de filtros em disabled/degraded (`canApplyChatToBoard` falso; resposta `chat_disabled` sanitizada/fechada para manual). Roteiro `22-MANUAL-UAT.md` cobre busca manual/filtros/paginação/detalhe/revelação em habilitado, degradado e desativado. |
| 5 | Respostas/artefatos preservam o contrato público e limites (LLM só extrai parâmetros; busca determinística; `JobPublic` sem contatos; suporte não nativo aproximado/sinalizado). | ✓ VERIFIED | `chat_search` usa `extract_and_map_intent` + `list_published` para `applied_params` efetivos e retorna `ChatSearchResults.items` como `JobPublic`; testes afirmam equivalência de ids/total com `GET /api/v1/public/jobs` e ausência de `contact_*`. Matriz/testes explícitos: salário/modalidade/contrato/senioridade não nativos/aproximados, Campinas `not_in_whitelist`, "parecidas" apenas seed textual em `q` sem semântica/vetor/link/ID. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `backend/app/core/config.py` | Kill-switch operacional `CHAT_SEARCH_ENABLED` | ✓ VERIFIED | Existe, substantivo e wired: define `CHAT_SEARCH_ENABLED: bool = True` (L61) e é consumido por `backend/app/api/v1/public.py` via `get_settings()` para status/short-circuit. |
| `backend/.env.example` | Documentação do kill-switch operacional | ✓ VERIFIED | Existe e documenta `CHAT_SEARCH_ENABLED=true` com orientação de board/listagem manual intactos (L60). |
| `backend/app/api/v1/public.py` | Kill-switch/status, resposta controlada, logging estruturado sem PII, busca determinística | ✓ VERIFIED | Existe e wired: `GET /chat-search/status` (L208), `_CHAT_GUIDANCE_DISABLED` (L56), tratamento `chat_disabled` em `_chat_degraded_contract` (L90–111), short-circuit sem LLM/DB (L294–310), `extract_and_map_intent`/`list_published` no caminho habilitado, `logger.info("chat_search", extra={...})` em `finally` (L388–399), sem `payload.message` em logger calls. |
| `backend/tests/test_chat_search_api.py` | Cobertura automatizada disabled/status/logging/MVP/equivalência/privacidade com LLM mockado | ✓ VERIFIED | Existe e substantivo: testes `test_chat_search_disabled_*`, `test_chat_search_status_endpoint_reflects_toggle`, `test_public_jobs_remain_independent_when_chat_disabled`, `test_chat_search_*_emits_structured_log_without_pii`, 5 `test_mvp_*`; usa `monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", ...)`, `_assert_no_contacts`, comparações com `GET /api/v1/public/jobs`. |
| `backend/tests/conftest.py` | Intent suites puras executáveis sem DB quando aplicável | ✓ VERIFIED | Whitelist inclui `test_intent_schema.py`, `test_intent_mapper.py`, `test_intent_parser.py`, `test_intent_client.py` (L107–110); `test_chat_search_api.py` permanece fora da whitelist DB-independente. |
| `frontend/lib/api.ts` | Consulta de status e tipos/contrato do chat | ✓ VERIFIED | `ChatSearchStatus` e `getChatSearchStatus()` para `GET ${API}/api/v1/public/chat-search/status` (L811–875), com timeout/erro controlado. |
| `frontend/components/board/chat/ChatWidget.tsx` | Gating/hide launcher/panel por estado desativado confirmado e fallback seguro | ✓ VERIFIED | Consulta status no mount (não bloqueante), oculta launcher/painel quando `enabled===false`, trata `chat_disabled` (sanitiza, fecha, não aplica, foca busca manual), preserva `JobDetailDialog`/`?vaga` e fluxo canônico. |
| `frontend/lib/chatApply.ts` | Gating puro para não aplicar busca em estados degradados/desativados | ✓ VERIFIED | `canApplyChatToBoard` retorna `false` para `meta.degraded===true` ou `degradation_reason==="chat_disabled"` (L17–20). |
| `frontend/lib/chatApply.test.ts` | Cobertura Vitest de gating/mapeamento incluindo `chat_disabled` | ✓ VERIFIED | Casos para `chat_disabled` (degradado explícito e razão isolada) e regressão de mapeamento/aplicabilidade. |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` | Matriz QA-01 (5 exemplos, esperado/observado, lacunas, refs) | ✓ VERIFIED | Existe, versionado e rastreável: 5 exemplos completos, `Contrato esperado + Resultado observado`, refs a testes/casos, lacunas explícitas obrigatórias (seed textual limitado, sem semântica/vetor/link/ID, Campinas `not_in_whitelist`, campos não nativos). |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` | Roteiro manual/UAT guiado QA-02/QA-03 viável | ✓ VERIFIED | Existe com pré-requisitos, 6 casos cobrindo fluxo crítico, `carregar mais`, aplicar, detalhe/revelação, degradado/sem resultados, `CHAT_SEARCH_ENABLED=false` e não-regressão do board; sem Playwright/RTL. **Substantivo porém ainda não executado** (resultados pendentes) — ver Human Verification. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `backend/app/core/config.py` | `backend/app/api/v1/public.py` | `get_settings().CHAT_SEARCH_ENABLED` short-circuit/status | ✓ WIRED | `public.py` consulta setting para status endpoint (L211) e gating do chat-search (L294). |
| `backend/app/api/v1/public.py` | `logger.info("chat_search")` | `extra` seguro em `finally` | ✓ WIRED | Log estruturado com outcome/reason/latency/counts/page/limit (L388–399), sem mensagem/contatos. |
| `frontend/lib/api.ts` | Backend status endpoint | `GET /api/v1/public/chat-search/status` | ✓ WIRED | `getChatSearchStatus()` faz fetch ao endpoint público (L850–851). |
| `frontend/components/board/chat/ChatWidget.tsx` | `ChatLauncher` / painel | Render condicional + `setIsOpen(false)` em disabled | ✓ WIRED | Launcher só renderiza quando permitido (L304–314), `chatEnabled` confirmado desliga UI (L104–106, L158–160, L296–300). |
| `frontend/components/board/chat/ChatWidget.tsx` + `frontend/lib/chatApply.ts` | Board canônico | `canApplyChatToBoard` + `buildBoardHref`/`router.replace` bloqueados em disabled/degraded | ✓ WIRED | Apply gated (L271–280, `chatApply.ts` L17–26); respostas `chat_disabled` não aplicam e direcionam busca manual. |
| `backend/app/api/v1/public.py` | `list_published` / `GET /api/v1/public/jobs` | Busca determinística com `applied_params` efetivos | ✓ WIRED | `chat_search` chama `list_published` (L357–365) após intent/mapeamento; rota pública de jobs usa o mesmo CRUD/predicados (L178–185). |
| `22-MVP-EXAMPLES.md` | `backend/tests/test_intent_*.py`, `backend/tests/test_chat_search_api.py` | Referências de evidência esperado/observado | ✓ WIRED | Matriz cita casos concretos (mapper e 5 `test_mvp_*` da API) e estado observado. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| QA-01 | 22-03-PLAN | 5 exemplos-alvo MVP com comportamento validado/documentado (combinações e lacunas explícitas: dev pleno SP salário>=8k; remoto frontend React preferência CLT; vagas parecidas/seed limitado; analista de dados Campinas ou remoto 6–10k; estágio marketing digital em SP) | ✓ SATISFIED | `22-MVP-EXAMPLES.md` (5 seções, esperado+observado, lacunas mandatórias) + testes determinísticos MVP em `test_intent_mapper.py` e `test_chat_search_api.py` com seam mockado e contratos explícitos. **Nota:** `.planning/REQUIREMENTS.md` ainda marca QA-01 como `[ ] Pending` (traceability desatualizada), mas a evidência de implementação/validação documentada está presente. |
| QA-02 | 22-01, 22-02, 22-03-PLANs | Testes automatizados para extração/mapeamento/normalização e API de chat-search (LLM mockado) e validação básica de UI/E2E viável | ✓ SATISFIED | Suites consolidadas/estendidas (`backend/tests/test_intent_{schema,mapper,parser,client}.py`, `backend/tests/test_chat_search_api.py`, `backend/tests/test_ratelimit.py`, `backend/tests/conftest.py`) + lógica pura frontend (`frontend/lib/chatApply.test.ts`) + roteiro viável `22-MANUAL-UAT.md` (sem Playwright/RTL, conforme D-04). Execução real da suíte DB-backed é dependente de ambiente; execução manual do UAT permanece pendente (human). **Nota:** traceability em `REQUIREMENTS.md` ainda pendente. |
| QA-03 | 22-01, 22-02, 22-03-PLANs | Controles operacionais mínimos (toggle/kill-switch, logs/métricas básicas sem PII sensível) para desativar/ajustar chat com segurança sem regredir board público | ✓ SATISFIED | `CHAT_SEARCH_ENABLED` + status endpoint + disabled short-circuit seguro em backend, logging estruturado sem PII/mensagem/contatos, gating/hide no frontend, independência de `GET /public/jobs` e manual board; testes/casos e runbook cobrem disabled/degraded/non-regression. **Nota:** traceability em `REQUIREMENTS.md` ainda pendente. |

**Orphaned requirements for Phase 22:** None detected (ROADMAP/REQUIREMENTS mapeiam QA-01..QA-03 para a fase; todos cobertos por planos/evidência).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `22-MANUAL-UAT.md` | (múltiplas) | `result: [pending]` / `pending` no frontmatter-summary | ℹ️ Info | Artefato de validação manual existe e está correto por desenho, mas execução humana ainda não registrada; não indica stub de implementação, apenas evidência operacional pendente. |
| Nenhum stub/bypass detectado nos artefatos de código inspecionados | - | `TODO/FIXME/HACK/PLACEHOLDER`, retorno estático indevido, handler vazio, log com `payload.message` | - | Sem blockers/warnings de implementação observados nas áreas modificadas (config, endpoint chat-search, API frontend, chat widget, chatApply, testes, conftest). |

### Human Verification Required

### 1. Execução do roteiro manual/UAT guiado (QA-02/QA-03 viável)

**Test:** Executar `22-MANUAL-UAT.md` (casos 1–6) em ambiente rodando backend+frontend com banco/dados apropriados.
**Expected:** Fluxo crítico do chat (abrir sem login, enviar, loading/erro, interpretação aplicada/ignorada/aproximada e limitações, resultados/`carregar mais`, aplicar no board canônico quando aplicável, detalhe/revelação canônica) validado; estados degradado/sem resultados com guidance pt-BR e busca manual; com `CHAT_SEARCH_ENABLED=false` launcher/painel ausentes e board manual íntegro.
**Why human:** Validação UI/E2E viável definida como manual guiada (D-04); resultados no artefato estão pendentes.

### 2. Confirmação visual/runtime do kill-switch e não-regressão do board

**Test:** Alternar `CHAT_SEARCH_ENABLED` (reiniciar/recarregar conforme ambiente), observar status/endpoint/UI e operar board manual.
**Expected:** Chat some/é bloqueado com segurança quando desativado; nenhuma regressão em `GET /public/jobs`, filtros, paginação, detalhe e revelação; sem exposição de contatos/internos.
**Why human:** Integração config + render/UX real não é totalmente comprovável por inspeção estática.

### 3. Experiência integrada em degradação/sem resultados

**Test:** Simular timeout/indisponibilidade/sem parâmetros extraíveis e consultas sem correspondência no ambiente.
**Expected:** Guidance segura pt-BR, sem aplicação automática indevida, caminho claro para busca manual, contatos só no fluxo canônico.
**Why human:** Comportamento de UI e copy em contexto real (foco/transições/estados) requer observação humana.

### Gaps Summary

Nenhum gap de implementação automatizável identificado nas must-haves, artefatos ou wiring verificados: kill-switch/config, status, resposta segura `chat_disabled`, logging estruturado sem PII, preservação de privacidade/contrato determinístico, consolidação de testes e artefatos QA-01/QA-02/QA-03 estão presentes e consistentes com o objetivo da fase. O bloqueio remanescente é de **validação operacional/manual em runtime** (execução do `22-MANUAL-UAT.md` e confirmação visual fim-a-fim), inerente ao critério viável definido em D-04/SC-2/SC-4.

**Notas operacionais:** (1) `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/SECURITY.md` não existe — a nota do solicitante permanece válida: se enforcement de segurança for requerido, considerar `/gsd-secure-phase 22`. (2) `.planning/REQUIREMENTS.md` ainda lista QA-01/QA-02/QA-03 como `Pending`; recomenda-se reconciliar traceability após conclusão do UAT/verificação final.

---

_Verified: 2026-11-18T12:10:00Z_
_Verifier: OpenCode (gsd-verifier)_