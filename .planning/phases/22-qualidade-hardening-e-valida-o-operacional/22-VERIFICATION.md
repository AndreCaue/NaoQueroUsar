---
phase: 22-qualidade-hardening-e-valida-o-operacional
verified: 2026-11-18T12:10:00Z
status: accepted_with_deferred_runtime_checks
score: 5/5 must-haves verified
overrides_applied: 0
reconciliation:
  - date: 2026-11-20
    note: "Reconciliação final 23-03 (D-10/D-11/D-12): estado promovido de human_needed para final aceito e rastreável. Evidências automatizadas/código preservadas; validações manuais/runtime reconciliadas com `22-HUMAN-UAT.md` e `22-MANUAL-UAT.md` (passes preservados, reteste CL-01 e itens inviáveis registrados como deferimento aceito por item com motivo, risco residual e condição/ação futura). Correções/hardening 23-01/23-02 e residual D-14 (focus-trap) refletidos sem inventar execução."
human_verification_resolutions:
  - test: "Executar roteiro manual/UAT guiado (22-MANUAL-UAT.md) em ambiente integrado com backend/frontend e dados de teste"
    resolution: "deferimento aceito por item (itens 0–6 em `22-MANUAL-UAT.md`; item 1 CL-01 + passes 2–3 preservados em `22-HUMAN-UAT.md`) — motivo: ambiente/runtime/dados/browser/infra indisponíveis nesta sessão; risco residual documentado por item; condição/ação futura: executar roteiro em ambiente integrado/controlado e registrar evidências."
  - test: "Validar kill-switch fim-a-fim percebido na UI com `CHAT_SEARCH_ENABLED=false`"
    resolution: "deferimento aceito por item em `22-MANUAL-UAT.md` (item 5). Evidência humana anterior preservada em `22-HUMAN-UAT.md` item 2 (`result: pass`) e contratos/testes automatizados permanecem verificados; confirmação operacional adicional depende de restart/config em ambiente real."
  - test: "Confirmar não-regressão do board público em estados degradado/sem resultados do chat"
    resolution: "deferimento aceito por item em `22-MANUAL-UAT.md` (item 4). Evidência humana anterior preservada em `22-HUMAN-UAT.md` item 3 (`result: pass`) e contratos/lógica permanecem verificados; validação integrada de copy/foco/transições requer runtime real."
---

# Phase 22: Qualidade, hardening e validação operacional — Verification Report

**Phase Goal:** O chatbot de busca opera de forma validada, observável e controlável sem regredir a experiência pública existente
**Verified:** 2026-11-18T12:10:00Z
**Status:** accepted_with_deferred_runtime_checks (estado final aceito e rastreável; validações runtime/UI não executadas nesta sessão registradas como deferimento aceito por item)
**Re-verification:** 2026-11-20 — reconciliação documental final com `22-HUMAN-UAT.md` e `22-MANUAL-UAT.md` (sem nova execução runtime/UI), incorporando evidências/correções 22-04, 23-01 e 23-02.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Os 5 exemplos-alvo do MVP têm comportamento validado e documentado (incluindo combinações e lacunas explícitas: seed textual limitado sem semântica/vetor/link/ID, Campinas fora da whitelist, campos não nativos aproximados/sinalizados). | ✓ VERIFIED | Matriz versionada `22-MVP-EXAMPLES.md` documenta os 5 casos com **Contrato esperado + Resultado observado**, evidências rastreáveis e lacunas obrigatórias (`seed textual limitado`, `sem similaridade semântica/vetorial`, `link/ID`, `Campinas`/`not_in_whitelist`, salário/modalidade/contrato/senioridade não nativos). Testes determinísticos: `backend/tests/test_intent_mapper.py` (`test_mvp_dev_pleno_sp_salary_not_native`, `test_mvp_remoto_frontend_react_clt_textual_approximation`, `test_mvp_parecidas_com_vaga_seed_textual_limitado_sem_link_id`, `test_mvp_analista_dados_campinas_ou_remoto_salary_combo`, `test_mvp_estagio_marketing_digital_em_sp`) e `backend/tests/test_chat_search_api.py` (5 casos `test_mvp_*` com `extract_and_map_intent` mockado, equivalência a `GET /api/v1/public/jobs`, `_assert_no_contacts`). Rastreabilidade de hardening CL-01 atualizada em `22-MVP-EXAMPLES.md` (22-04 + 23-01) preservando lacunas mandatórias. |
| 2 | Existe suíte automatizada executável cobrindo extração/mapeamento/normalização e API de chat-search (LLM mockado), além de validação básica de UI/E2E viável no ambiente do projeto. | ✓ VERIFIED | Backend: intent puro whitelisted em `backend/tests/conftest.py` (`test_intent_schema.py`, `test_intent_mapper.py`, `test_intent_parser.py`, `test_intent_client.py`) e consolidado; `backend/tests/test_chat_search_api.py` cobre equivalência/paginação/contrato, privacidade sem contatos, invalidação/limites/rate-limit, degradação (`llm_unavailable`/timeout/`no_extractable_params`), `chat_disabled` e logging estruturado (`caplog`) sempre com seam mockado. Frontend viável: `frontend/lib/chatApply.ts` + `frontend/lib/chatApply.test.ts` (Vitest, lógica pura, inclui `chat_disabled`) sem Playwright/RTL. UI/E2E viável versionada por roteiro em `22-MANUAL-UAT.md` (estado final aceito/rastreável com deferimentos por item em 23-03). Execuções DB-backed permanecem pré-requisito de ambiente migrado quando aplicável. |
| 3 | Operadores dispõem de controles mínimos (kill-switch/config e logs/métricas básicas sem PII sensível) para desativar/ajustar o chat com segurança. | ✓ VERIFIED | Config/env: `backend/app/core/config.py` (`CHAT_SEARCH_ENABLED: bool = True`), `backend/.env.example` (`CHAT_SEARCH_ENABLED=true`). Backend enforcement/sinal: `backend/app/api/v1/public.py` (`GET /chat-search/status` -> `{"enabled": ...}`, short-circuit disabled antes de `extract_and_map_intent`/`list_published`, resposta 200 controlada `chat_disabled` com guidance pt-BR, `applied_params` nulos, `results` vazio, sem internos/contatos). Observabilidade: `logger.info("chat_search", extra={outcome,reason,latency_ms,results_count,total,page,limit})` em `finally`; sem `payload.message` em chamadas de logger. Frontend consome sinal/gating: `frontend/lib/api.ts` (`getChatSearchStatus`), `frontend/components/board/chat/ChatWidget.tsx` (consulta assíncrona, oculta launcher/painel quando desativado confirmado, trata resposta `chat_disabled` sem aplicar ao board), `frontend/lib/chatApply.ts` bloqueia `chat_disabled`/degradado. |
| 4 | Com chat desativado ou degradado, o board público existente continua utilizável para busca/listagem manual. | ✓ VERIFIED | Independência backend: `GET /api/v1/public/jobs` inalterado e testado (`test_public_jobs_remain_independent_when_chat_disabled`, `_assert_no_contacts`); kill-switch atua apenas no boundary do chat-search/status. Frontend: mount/status check não bloqueante, fail-safe sem bloquear board (`ChatWidget`), sem mutação automática de filtros em disabled/degraded (`canApplyChatToBoard` falso; resposta `chat_disabled` sanitizada/fechada para manual). `22-HUMAN-UAT.md` preserva passes humanos anteriores (itens 2–3); `22-MANUAL-UAT.md` registra deferimentos aceitos por item para cenários runtime não executados nesta sessão. |
| 5 | Respostas/artefatos preservam o contrato público e limites (LLM só extrai parâmetros; busca determinística; `JobPublic` sem contatos; suporte não nativo aproximado/sinalizado). | ✓ VERIFIED | `chat_search` usa `extract_and_map_intent` + `list_published` para `applied_params` efetivos e retorna `ChatSearchResults.items` como `JobPublic`; testes afirmam equivalência de ids/total com `GET /api/v1/public/jobs` e ausência de `contact_*`. Matriz/testes explícitos: salário/modalidade/contrato/senioridade não nativos/aproximados, Campinas `not_in_whitelist`, "parecidas" apenas seed textual em `q` sem semântica/vetor/link/ID. Correções 23-01/23-02 preservam busca determinística, privacidade (sem contatos no chat) e sinalização de limites. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `backend/app/core/config.py` | Kill-switch operacional `CHAT_SEARCH_ENABLED` | ✓ VERIFIED | Existe, substantivo e wired: define `CHAT_SEARCH_ENABLED: bool = True` e é consumido por `backend/app/api/v1/public.py` via `get_settings()` para status/short-circuit. |
| `backend/.env.example` | Documentação do kill-switch operacional | ✓ VERIFIED | Existe e documenta `CHAT_SEARCH_ENABLED=true` com orientação de board/listagem manual intactos. |
| `backend/app/api/v1/public.py` | Kill-switch/status, resposta controlada, logging estruturado sem PII, busca determinística | ✓ VERIFIED | `GET /chat-search/status`, resposta controlada `chat_disabled`, short-circuit sem LLM/DB quando desativado, `extract_and_map_intent`/`list_published` no caminho habilitado, log estruturado em `finally` sem `payload.message`. |
| `backend/tests/test_chat_search_api.py` | Cobertura automatizada disabled/status/logging/MVP/equivalência/privacidade com LLM mockado | ✓ VERIFIED | Cobertura de disabled/status/logging/MVP/equivalência/privacidade/rate-limit com `extract_and_map_intent` mockado e `_assert_no_contacts` (conforme evidência histórica consolidada da fase). |
| `backend/tests/conftest.py` | Intent suites puras executáveis sem DB quando aplicável | ✓ VERIFIED | Whitelist inclui suites de intent (`test_intent_schema.py`, `test_intent_mapper.py`, `test_intent_parser.py`, `test_intent_client.py`). |
| `frontend/lib/api.ts` | Consulta de status e tipos/contrato do chat; parsing defensivo | ✓ VERIFIED | `getChatSearchStatus` presente; 23-02 endureceu `chatSearch` para falha de parse JSON em 200 com `ApiError("Resposta inválida do servidor.", 0)` (evidência: `23-02-SUMMARY.md`). |
| `frontend/components/board/chat/ChatWidget.tsx` | Gating/hide launcher/panel por estado desativado confirmado e fallback seguro | ✓ VERIFIED | Consulta status, oculta launcher/painel quando desativado confirmado, trata `chat_disabled` sem aplicar ao board, preserva fluxo canônico de detalhe; 23-02 adicionou propagação/restauração de foco ao fechar detalhe aberto via chat. |
| `frontend/lib/chatApply.ts` | Gating puro para não aplicar busca em estados degradados/desativados/não úteis | ✓ VERIFIED | Bloqueia `chat_disabled`/degradado; 23-02 passou a exigir params normalizados úteis (evita apply no-op para cidade-only não normalizável como `campinas`). |
| `frontend/lib/chatApply.test.ts` | Cobertura Vitest de gating/mapeamento incluindo `chat_disabled` e casos úteis | ✓ VERIFIED | Cobertura determinística preservada/estendida (inclui caso `campinas` não aplicável e cenários suportados), conforme `23-02-SUMMARY.md`. |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` | Matriz QA-01 (5 exemplos, esperado/observado, lacunas, refs) | ✓ VERIFIED | 5 exemplos completos com lacunas mandatórias preservadas; rastreabilidade atualizada para 22-04 e 23-01 (hardening `\brio\b`, reteste CL-01 com deferimento aceito por item). |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md` | UAT humano fase 22 em estado final aceito e rastreável | ✓ VERIFIED | `status: complete`; passes (itens 2–3) preservados; item 1 (CL-01) resolvido como **deferimento aceito por item** com motivo, risco residual e condição/ação futura; residual D-14 propagado. |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` | Roteiro/manual UAT fase 22 em estado final aceito e rastreável | ✓ VERIFIED | `status: complete`; roteiro preservado; itens 0–6 resolvidos por **deferimento aceito por item** (nenhum `[pending]`), cada um com motivo, risco residual e condição/ação futura; residual D-14 propagado. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `backend/app/core/config.py` | `backend/app/api/v1/public.py` | `get_settings().CHAT_SEARCH_ENABLED` short-circuit/status | ✓ WIRED | Setting consumido para status endpoint e gating do chat-search. |
| `backend/app/api/v1/public.py` | `logger.info("chat_search")` | `extra` seguro em `finally` | ✓ WIRED | Log estruturado com outcome/reason/latency/counts/page/limit, sem mensagem/contatos. |
| `frontend/lib/api.ts` | Backend status endpoint | `GET /api/v1/public/chat-search/status` | ✓ WIRED | `getChatSearchStatus()` consulta endpoint público. |
| `frontend/components/board/chat/ChatWidget.tsx` + `frontend/lib/chatApply.ts` | Board canônico | `canApplyChatToBoard` + navegação canônica bloqueados em disabled/degraded/não útil | ✓ WIRED | Gating preservado; 23-02 reforçou utilidade normalizada e manteve fluxo canônico sem exposição de contatos. |
| `backend/app/api/v1/public.py` | `list_published` / `GET /api/v1/public/jobs` | Busca determinística com `applied_params` efetivos | ✓ WIRED | `chat_search` e endpoint público de jobs compartilham predicados/CRUD determinísticos. |
| `22-VERIFICATION.md` | `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md` | Reconciliação final de estado/runtime checks | ✓ WIRED | Resoluções por item (passes preservados, CL-01 reteste e deferimentos aceitos com motivo/risco/ação futura) registradas e referenciadas explicitamente. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| QA-01 | 22-03-PLAN, 23-01-PLAN, 23-03-PLAN (fechamento/rastreabilidade) | 5 exemplos-alvo MVP com comportamento validado/documentado (combinações e lacunas explícitas) | ✓ SATISFIED | `22-MVP-EXAMPLES.md` + testes determinísticos MVP (mapper/API) + hardening CL-01 documentado (22-04/23-01) preservando lacunas mandatórias. **Nota:** `.planning/REQUIREMENTS.md` pode ainda refletir traceability pendente de reconciliação formal (tratada em 23-05, se aplicável). |
| QA-02 | 22-01/02/03-PLANs, 23-03-PLAN (reconciliação) | Testes automatizados e validação básica de UI/E2E viável | ✓ SATISFIED | Suites automatizadas consolidadas (backend/frontend lógica pura) + `22-MANUAL-UAT.md` como validação viável versionada; execução manual/runtime não realizada nesta sessão foi registrada como deferimento aceito por item em `22-HUMAN-UAT.md`/`22-MANUAL-UAT.md`. **Nota:** traceability em `REQUIREMENTS.md` tratada em 23-05 se ainda pendente. |
| QA-03 | 22-01/02/03-PLANs, 23-02-PLAN, 23-03-PLAN (reconciliação) | Controles operacionais mínimos e segurança operacional sem regredir board público | ✓ SATISFIED | Kill-switch/status/logging sem PII, gating frontend e independência do board preservados/verificados; correções 23-02 aplicadas; artefato `22-SECURITY.md` **ainda não existe neste momento** e será tratado em CL-05 (23-04) sem marcar gap de implementação não tratado aqui. **Nota:** traceability em `REQUIREMENTS.md` tratada em 23-05 se ainda pendente. |

**Orphaned requirements for Phase 22:** None detected (ROADMAP/REQUIREMENTS mapeiam QA-01..QA-03 para a fase; evidências/reconciliações existentes cobrem o escopo desta verificação).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| Nenhum blocker/warning de implementação automatizável identificado nas áreas reconciliadas | - | Stubs, bypasses, logs com PII/mensagem, exposição de contatos no chat | - | Sem gaps de implementação automatizável abertos nesta reconciliação. |
| Residual UX/a11y (propagado de 23-02, D-14) | n/a | Focus-trap completo ausente no diálogo custom do chat | ℹ️ Info (deferimento aceito residual) | Usuários de teclado/leitor de tela podem mover foco para fora do diálogo enquanto aberto; mitigação parcial implementada (foco inicial e restauração de foco). Não bloqueia fechamento rastreável desta verificação; requer ação futura dedicada com validação manual. |

### Human Verification / Resoluções (reconciliado 23-03)

- **Reteste CL-01 (cidade, toolbar/chat)** — **deferimento aceito por item** (registrado em `22-HUMAN-UAT.md` item 1, `22-MANUAL-UAT.md` item 0 e debug session). *Motivo:* ambiente integrado indisponível (backend/frontend/DB/dados/navegador). *Risco residual:* possível divergência ponta a ponta em runtime real apesar de correções 22-04/23-01 e testes determinísticos. *Condição/ação futura:* executar revalidação runtime/manual em ambiente integrado com vagas por cidade e registrar evidência objetiva de `city=<slug>` e interpretação correta.
- **Roteiro manual/UAT guiado (`22-MANUAL-UAT.md` itens 0–6)** — **deferimentos aceitos por item** (nenhum item pendente sem resolução). *Motivo:* dependências de runtime/config/restart, dados/fixtures, simulação de falhas e inspeção browser/rede/logs não disponíveis nesta sessão. *Risco residual:* regressões de UX/integração/privacidade operacional não observadas diretamente. *Condição/ação futura:* executar por item em ambiente integrado/controlado com evidências.
- **Passes humanos preservados (`22-HUMAN-UAT.md`)** — itens 2 (kill-switch fim-a-fim percebido na UI) e 3 (degradação/sem resultados e não-regressão) permanecem `result: pass` (evidência histórica preservada).
- **Residual D-14 (23-02, foco/a11y)** — focus-trap completo no diálogo custom do chat **deferido por sub-item** com justificativa, risco residual e condição/ação futura (propagado em `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md` e neste relatório).

### Gaps Summary

Sem gaps de implementação automatizável abertos para os must-haves/código verificados da fase 22. O estado final é aceito e rastreável com base em evidências automatizadas, correções 22-04/23-01/23-02 e reconciliação de `22-HUMAN-UAT.md`/`22-MANUAL-UAT.md`.

**Deferimentos aceitos residuais (não-bloqueantes para este fechamento documental, explicitamente rastreados):**
1. **CL-01 reteste runtime/manual (cidade, toolbar/chat):** deferimento aceito por item — motivo (ambiente integrado indisponível), risco residual (divergência operacional real), condição/ação futura (revalidação em ambiente integrado com dados e registro de evidência).
2. **Execução manual/runtime dos cenários de `22-MANUAL-UAT.md` (itens 0–6):** deferimentos aceitos por item com motivo específico, risco residual e condição/ação futura em cada item.
3. **D-14 focus-trap completo do diálogo custom do chat (residual 23-02):** deferimento aceito por sub-item — justificativa (viabilidade/risco de escopo), risco residual (foco pode sair do diálogo), condição/ação futura (contenção de foco dedicada + validação manual de teclado/a11y).

**Notas operacionais factuais:**
- `22-SECURITY.md` (Phase 22) **não existe no momento desta edição** — a ser tratado em CL-05 (23-04), sem marcar gap não tratado nesta verificação.
- Traceability em `.planning/REQUIREMENTS.md` (QA-01/QA-02/QA-03 ainda pendentes de reconciliação formal, se aplicável) permanece como item de fechamento documental tratado em 23-05, se ainda pendente.

---

_Verified: 2026-11-18T12:10:00Z_
_Reconciled: 2026-11-20T00:00:00Z_
_Verifier: OpenCode (gsd-verifier, reconciled in 23-03 execution)_