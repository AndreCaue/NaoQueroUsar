---
phase: 22
slug: qualidade-hardening-e-valida-o-operacional
status: audited
nyquist_compliant: false
wave_0_complete: partial
created: 2026-11-18
updated: 2026-11-20
audited: 2026-11-20
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest 9.x + pytest-asyncio (auto). Frontend: Vitest 2.x (node env, `lib/**/*.test.ts`). |
| **Config file** | `backend/pyproject.toml`, `backend/tests/conftest.py`; `frontend/vitest.config.ts`, `frontend/package.json` |
| **Quick run command** | `cd backend && python -m pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py` e/ou `cd frontend && npm run test:chat` (subsets determinísticos/viáveis) |
| **Full suite command** | `cd backend && python -m pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py tests/test_chat_search_api.py tests/test_ratelimit.py` (subset DB-gated quando aplicável) + `cd frontend && npm test` |
| **Estimated runtime** | ~30-120 seconds (subsets puros/mocked); DB-backed/manual dependem de ambiente |

---

## Sampling Rate

- **After every task commit:** Executar o menor comando determinístico relevante ao escopo alterado (intent/chat mocked/backend, `test:chat`/`npm test` para lógica pura frontend, ou checks de artefatos). Preferir subsets puros quando DB indisponível.
- **After every plan wave:** Executar suites alvo da fase (`intent_*`, `test_chat_search_api.py`, `test_ratelimit.py`, `frontend npm test`) conforme capacidade do ambiente e atualizar evidências em artefatos QA.
- **Before `/gsd-verify-work`:** Consolidar evidência automatizada disponível + artefatos versionados (`22-MVP-EXAMPLES.md`, `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, `22-VERIFICATION.md`) com estados finais rastreáveis e desvios/deferimentos explícitos quando necessário.
- **Max feedback latency:** 120 seconds

---

## Per-task / Requirement Verification Map

| task ID | Plan/Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|-----------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 22-V-01 | 22-01..22-04/23-01,03 | QA-01 | V5 (input integrity) | 5 exemplos MVP validados/documentados com lacunas explícitas (seed textual limitado, sem semântica/vetor/link/ID, Campinas fora da whitelist, campos não nativos aproximados/sinalizados), sem inventar filtros/semântica | unit/integration (mocked) + matriz documentada | `cd backend && python -m pytest -q tests/test_intent_mapper.py tests/test_chat_search_api.py` (subsets MVP conforme ambiente) | ✅ `22-MVP-EXAMPLES.md`, `backend/tests/test_intent_mapper.py`, `backend/tests/test_chat_search_api.py` | ✅ green (evidência automatizada/documental consolidada; reteste runtime CL-01 registrado como deferimento aceito por item) |
| 22-V-02 | 22-01..22-03/23-02,03 | QA-02 | V4/V5 (abuse/input) | Extração/mapeamento/normalização e chat-search com LLM mockado: equivalência determinística (`list_published`), `JobPublic` sem contatos, degradação/fallback segura, limites/rate limit e lógica UI viável automatizada onde suportada | unit/integration + lógica pura UI | `cd backend && python -m pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py tests/test_chat_search_api.py tests/test_ratelimit.py`; `cd frontend && npm test` | ✅ testes intent/chat/rate-limit, `frontend/lib/chatApply.ts`, `frontend/lib/chatApply.test.ts`, `22-MANUAL-UAT.md` | ⚠️ parcial (automatizado presente; validação manual/UI-E2E viável registrada com deferimentos aceitos por item) |
| 22-V-03 | 22-01..22-03/23-02,03 | QA-03 | V4 (availability/abuse), Info Disclosure | Kill-switch/status, resposta controlada, board manual independente, logging estruturado sem PII/conteúdo sensível, e não-regressão operacional; controles documentados | integration/unit + manual/runtime operacional | `cd backend && python -m pytest -q tests/test_chat_search_api.py` (subset disabled/logging quando aplicável) | ✅ `backend/app/api/v1/public.py`, `backend/app/core/config.py`, `backend/tests/test_chat_search_api.py`, `22-VERIFICATION.md`, `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md` | ⚠️ parcial (contratos/testes/evidências presentes; confirmação runtime/UI integrada registrada com deferimentos aceitos por item) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Evidências consolidadas (estado atual):**
- `22-VERIFICATION.md` (`status: accepted_with_deferred_runtime_checks`, score 5/5 must-haves verificados em código/evidências automatizadas; reconciliação 2026-11-20).
- `22-MVP-EXAMPLES.md` (matriz QA-01 com contrato esperado/observado e lacunas mandatórias; hardening CL-01 rastreado 22-04/23-01).
- `22-HUMAN-UAT.md` (`status: complete`, passes preservados; reteste CL-01 e cenários não executáveis como deferimento aceito por item) e `22-MANUAL-UAT.md` (`status: complete`, itens 0–6 como deferimento aceito por item, com motivo/risco/ação futura).
- Artefatos/correções de hardening relacionados: 23-01 (mapper RJ), 23-02 (frontend hardening/foco parcial) e 22-SECURITY planejado nesta fase de fechamento (CL-05) para documentação formal.

---

## Wave 0 Requirements

- [x] `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` — matriz QA-01 (D-01/D-02/D-03) com 5 exemplos, contrato esperado + observado, lacunas explícitas e rastreabilidade.
- [x] `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` — roteiro/manual UAT guiado (QA-02/QA-03) preservado e reconciliado com resolução por item.
- [x] `backend/tests/test_chat_search_api.py` — cobertura de contratos críticos (equivalência/privacidade, degradação/fallback, limites/rate limit, disabled/status/logging, cenários MVP com seam mockado) existente/estendida ao longo da fase.
- [x] `backend/tests/test_intent_schema.py`, `backend/tests/test_intent_mapper.py`, `backend/tests/test_intent_parser.py`, `backend/tests/test_intent_client.py` — suites intent determinísticas consolidadas (incluindo casos MVP/classificação).
- [x] `frontend/lib/chatApply.ts` e `frontend/lib/chatApply.test.ts` — lógica pura viável automatizada para apply/gating canônico (QA-02 viável em frontend).
- [ ] Execução completa DB-backed em ambiente migrado/capaz para todos os subsets dependentes de banco (pré-requisito de ambiente, não afirmado como executado nesta auditoria).
- [ ] Automação UI/E2E browser (Playwright/RTL) para fluxos manuais de chat/board — fora da abordagem viável adotada; coberta por roteiro manual com deferimentos aceitos por item.

*Wave 0 parcialmente completo no sentido de artefatos/coberturas presentes; permanecem dependências de ambiente/runtime e automação UI não introduzida.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fluxo UI/E2E viável do chat no board (abrir sem login, estados, interpretação/limitações, carregar mais, aplicar no board, detalhe/reveal canônico, busca manual em degradação/sem resultados) | QA-02 | Sem Playwright/RTL; validação depende de browser/runtime/dados e integração real | Executar `22-MANUAL-UAT.md` em ambiente integrado; registrar evidência por item (ou deferimento aceito com motivo/risco/ação futura, conforme 23-03). |
| Kill-switch fim-a-fim percebido na UI e não-regressão do board público com chat desativado | QA-03 | Requer alteração de env/config + restart/reload e observação operacional em runtime | Desativar `CHAT_SEARCH_ENABLED`, validar `/chat-search/status` e `POST /chat-search` controlado, ocultação/gating de UI e integridade de `GET /public/jobs`/busca manual/filtros/paginação/detalhe/reveal. |
| Evidência contrato esperado + observado por exemplo MVP com observações runtime quando aplicável | QA-01 | Consolidação de resultados automatizados e observações/fixtures com lacunas explícitas | Revisar/preencher `22-MVP-EXAMPLES.md` com referências rastreáveis; retestes runtime não executados nesta sessão permanecem como deferimento aceito por item. |

---

## Validation Sign-Off

- [x] All requirements/tasks have `<automated>` verify or documented Wave 0/manual dependencies
- [x] Sampling continuity definida para subsets determinísticos e reconciliação de evidências
- [x] Wave 0 gaps/dependências remanescentes (DB-backed, automação UI/E2E, runtime manual) explicitamente registrados
- [x] No watch-mode flags
- [x] Feedback latency < 120s para subsets automatizados viáveis
- [ ] `nyquist_compliant: true` set in frontmatter (não integralmente viável no ambiente atual; desvio aceito documentado com plano de ação)

**Approval:** conditionally approved with accepted deviation (2026-11-20)

## Accepted Deviation / Plan of Action (Desvio aceito e plano de ação)

- **Situação:** `nyquist_compliant: false` mantido de forma honesta. Há forte evidência automatizada/documental (testes intent/chat/rate-limit/chatApply, `22-MVP-EXAMPLES.md`, `22-VERIFICATION.md` accepted_with_deferred_runtime_checks) e reconciliação humana/manual em estado final aceito/rastreável, porém permanecem dependências não integralmente fechadas nesta sessão: execuções DB-backed completas em ambiente migrado, validações manuais/runtime/browser por item (`22-HUMAN-UAT.md`/`22-MANUAL-UAT.md`) e ausência de automação UI/E2E.
- **Plano de ação:** (1) executar suites DB-backed em ambiente com banco de testes migrado e registrar resultados objetivos; (2) executar roteiro `22-MANUAL-UAT.md` em ambiente integrado (incluindo reteste CL-01 e cenários kill-switch/degradação/privacidade operacional), atualizando `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md` e `22-VERIFICATION.md` com evidências; (3) avaliar introdução de automação UI viável (quando houver infraestrutura aprovada) para reduzir dependência manual recorrente; (4) promover este `22-VALIDATION.md` para `nyquist_compliant: true` quando critérios/evidências e sign-off estiverem integralmente atendidos (ou manter desvio aceito apenas para itens explicitamente residualizados).
- **Rastreabilidade:** todos os deferimentos foram registrados por item com motivo, risco residual e condição/ação futura nos artefatos da fase 22 (reconciliação 23-03), sem afirmar execuções runtime/UI/DB-backed não realizadas nesta edição.