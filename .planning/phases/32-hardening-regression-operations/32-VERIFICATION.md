---
phase: 32-hardening-regression-operations
verified: 2026-11-26T13:30:00Z
reverified: 2026-11-26T19:35:00Z
reverification_mode: phase33_uat_reconciliation
status: passed
score: 9/9 must-haves verified
requirements: [HARD-01, HARD-02]
human_verification:
  status: completed
  source: 32-HUMAN-UAT.md
  completed_at: 2026-11-26T19:35:00Z
  result: 4/4 pass
  items:
    - test: "Conectar/reconectar Meta+IG e validar prontidão live"
      result: pass
    - test: "Smoke publish IG real 2-passos em ambiente autorizado"
      result: pass
    - test: "Validar reconciliação ambígua/rate limit real"
      result: pass
    - test: "App Review/roles/tasks/Advanced Access"
      result: pass
---

# Phase 32: Hardening, Regression & Operations Verification Report

**Phase Goal:** Integração Instagram é verificável, observável e segura de operar sem regressão no fluxo Facebook.
**Verified:** 2026-11-26T13:30:00Z
**Status:** passed
**Re-verification:** Yes — Phase 33 reconciliation with 32-HUMAN-UAT.md 4/4 pass (automated evidence preserved; no new live Meta execution)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Cenários HARD-01 nomeados (draft/validação IG, idempotência, retry, ambiguidade, rate limit, mapeamento de erros, caracterização/regressão FB) estão mapeados para testes automatizados rastreáveis com comando e resultado. | ✓ VERIFIED | HARD-01 Scenario Matrix abaixo; testes existem em `backend/tests/test_social_post_generation.py`, `test_facebook_publisher.py`, `test_instagram_publisher.py`, `test_social_publish_pipeline.py`, `test_ig_media_validation.py`, `test_social_retry_policy.py`, `test_social_idempotency.py`, `test_admin_social_publish.py`, `test_admin_social_retry_api.py`, `test_admin_social_status_api.py`, `test_admin_instagram_social_posts.py`, `test_social_worker_claim.py`, `test_social_publisher.py`. Spot-check: 10 testes passaram (`test_docs_meta_instagram.py`, `test_social_post_generation.py`, `test_facebook_publisher.py`). Gate completo registrado em 32-01-SUMMARY: 73 passed, 1 skipped, 3 warnings. |
| 2 | Facebook Regression Gate cobre ciclo completo FB sem regressão causada por IG. | ✓ VERIFIED | Bloco "Facebook Regression Gate" abaixo com mapeamento por fluxo (draft/geração/contrato FB, aprovação/site-first, publish assíncrono/pipeline, status/logs seguros, retry/idempotência, reconexão/erro seguro). Comando gate registrado como PASS no 32-01-SUMMARY. `test_social_post_generation.py` é explicitamente IG-only. |
| 3 | Testes HARD-01 são backend-first pytest, comportamentais, sem segredos/tokens. | ✓ VERIFIED | Arquivos são pytest em `backend/tests`. `test_facebook_publisher.py` contém asserções `"access_token" not in ...`, `"page_access_token" not in ...`, `"token="` não necessário por presença de checks de token; fixtures usam valores sintéticos. Sem testes frontend adicionados. |
| 4 | Operador encontra em fonte única operacional env vars, checklist manual Meta, expiração/reconexão/rotação e troubleshooting de estados IG. | ✓ VERIFIED | `docs/META-INTEGRATION-TESTING.md` contém seções 6 (env vars canônicas/segurança), 7 (Troubleshooting publicação Instagram), 5.6/8 (expiração/reconexão/rotação/handoff), checklist manual com "Não executado / não evidenciado nesta sessão". |
| 5 | Evidência de Phase 32 separa claramente cobertura automatizada de handoff manual Meta, sem afirmar execução manual não realizada. | ✓ VERIFIED | `32-VERIFICATION.md` tem `Manual Meta Handoff` com "Não executado / não evidenciado nesta sessão" em todos os itens; status reconciliado em Phase 33 com UAT 4/4 pass registrado em `32-HUMAN-UAT.md`. |
| 6 | Facebook Regression Gate aparece como bloco explícito na verificação com arquivos, comando e resultado. | ✓ VERIFIED | Seção "Facebook Regression Gate" presente com tabela Fluxo/Cobertura/Comando/Resultado/Conclusão. |
| 7 | `.env.example` alinhado aos budgets IG publish existentes em config, sem segredos. | ✓ VERIFIED | `backend/.env.example` contém `IG_PUBLISH_HTTP_TIMEOUT_SECONDS=20.0`, `IG_STATUS_POLL_MAX_ATTEMPTS=5`, `IG_STATUS_POLL_DELAY_SECONDS=2.0`, `IG_PUBLISH_MAX_ATTEMPT_SECONDS=45.0`; `backend/app/core/config.py` valida os mesmos campos. |
| 8 | Requirement IDs dos PLAN frontmatter estão contabilizados em REQUIREMENTS.md. | ✓ VERIFIED | 32-01 declara `HARD-01`; 32-02 declara `HARD-02`. REQUIREMENTS.md mapeia HARD-01/HARD-02 para Phase 32 (linhas 39-40, 88-89). Ambos contabilizados; status em REQUIREMENTS.md ainda marcado Pending (atualização de checklist global fora do escopo desta verificação). |
| 9 | Limite HARD-01 draft/validação IG: regras backend-enforced cobertas por pytest; `>30 hashtags` e "link na bio" CTA permanecem UI-only Phase 30 D-09. | ✓ VERIFIED | `test_social_post_generation.py` cobre template determinístico, 2200 cap, link na bio, hashtags obrigatórias, sem vazamento de contato/empresa confidencial. `32-VERIFICATION.md` registra fronteira explícita sem fabricar hard-block backend para `>30 hashtags`. |

**Score:** 9/9 must-haves verified

## UAT Reconciliation (Phase 33, 2026-11-26)

Automated verification remains 9/9. Human UAT completed in `32-HUMAN-UAT.md` with 4/4 pass (total 4, passed 4, issues 0, pending 0, skipped 0, blocked 0; updated 2026-11-26T19:35:00Z). Phase 33 reconciles verification status to passed while preserving the separate nature of automated and human evidence (D-05, D-06, D-08). No new live Meta execution was performed by Phase 33.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/tests/test_facebook_publisher.py` | FB publisher contract/regression + safe error mapping | ✓ VERIFIED | Contém `PublishFailureCategory.transient/ambiguous/permanent` e asserções de ausência de token em `error_message`. |
| `backend/tests/test_social_post_generation.py` | IG draft generation/normalization backend contract | ✓ VERIFIED | Contém `generate_instagram_draft_for_job`, `generate_instagram_template`, "link na bio", "#vagas". |
| `backend/tests/test_social_publish_pipeline.py` | Pipeline HARD-01/FB regression behavioral contracts | ✓ VERIFIED | Referenciado no gate; arquivo existente e incluído no comando HARD-01/FB. |
| `docs/META-INTEGRATION-TESTING.md` | Fonte operacional única Meta/FB/IG | ✓ VERIFIED | Contém env canônicas, `ig_rate_limit_blocked`, `content_publishing_limit`, troubleshooting IG Phase 31, handoff "Não executado / não evidenciado nesta sessão". |
| `backend/.env.example` | Alinhamento env vars IG publish budgets | ✓ VERIFIED | Contém os 4 budgets IG publish Phase 31. |
| `backend/tests/test_docs_meta_instagram.py` | Rastreabilidade HARD-02 documental | ✓ VERIFIED | Preserva contrato Phase 29 e adiciona checks HARD-02; passou em spot-check. |
| `.planning/phases/32-hardening-regression-operations/32-VERIFICATION.md` | Matriz HARD-01, FB gate, handoff Meta | ✓ VERIFIED | Este arquivo; contém matrizes, gate, handoff explícito. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/tests/test_facebook_publisher.py` | `backend/app/services/social/facebook.py` | `FacebookPublisher` publish/error mapping | ✓ WIRED | Testes importam/instanciam publisher e validam `PublishResult`/categorias. |
| `backend/tests/test_social_post_generation.py` | `backend/app/services/social/post_generation.py` | `generate_instagram_template`, `generate_instagram_draft_for_job` | ✓ WIRED | Imports diretos confirmados por grep. |
| `backend/tests/test_social_publish_pipeline.py` | `backend/app/services/social/publish_pipeline.py` | `process_claimed_post` provider-aware outcomes | ✓ WIRED | Arquivo incluído no gate HARD-01/FB; summary/plan mapeiam cenários. |
| `docs/META-INTEGRATION-TESTING.md` | `backend/.env.example` | alinhamento env vars/budgets canônicos | ✓ WIRED | Ambos contêm `IG_PUBLISH_HTTP_TIMEOUT_SECONDS` e variáveis Meta/social canônicas. |
| `32-VERIFICATION.md` | `docs/META-INTEGRATION-TESTING.md` | referência de handoff/fonte operacional sem duplicar status | ✓ WIRED | Seção HARD-02 e Handoff referenciam o doc. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| HARD-01 | 32-01-PLAN.md | Testes automatizados cobrem draft/validação IG, publisher/pipeline (idempotência, retry, ambiguidade, rate limit, mapeamento de erros) e caracterização/regressão do fluxo Facebook. | ✓ SATISFIED (automated) | Matriz HARD-01, gate FB, testes/commits presentes; 10 testes spot-check PASS; gate completo registrado PASS (73 passed, 1 skipped, 3 warnings). |
| HARD-02 | 32-02-PLAN.md | Documentação operacional inclui env vars, checklist manual Meta, orientação de expiração/reconexão de token e troubleshooting de estados de publicação Instagram. | ✓ SATISFIED (doc + handoff) | `docs/META-INTEGRATION-TESTING.md` atualizado, `.env.example` alinhado, `test_docs_meta_instagram.py` PASS; execução live Meta permanece handoff explícito. |

**Orphaned requirements for Phase 32:** None. REQUIREMENTS.md maps only HARD-01, HARD-02 to Phase 32.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | - | - | - | Nenhum blocker/warning detectado nos artefatos verificados por spot-check. |

### Human Verification (Completed via 32-HUMAN-UAT.md)

| Test | Result | Evidence |
|---|---|---|
| Conectar/reconectar Meta+IG e validar prontidão live | pass | Recorded in 32-HUMAN-UAT.md (2026-11-26T19:35:00Z). Expected: status/prontidão coerente em `/admin/integracoes`, sem exposição de segredos; Facebook permanece utilizável. |
| Smoke publish IG real 2-passos em ambiente autorizado | pass | Recorded in 32-HUMAN-UAT.md (2026-11-26T19:35:00Z). Expected: publicação IG conclui com status/IDs/permalink sanitizados e logs seguros; sem duplicação. |
| Validar reconciliação ambígua/rate limit real | pass | Recorded in 32-HUMAN-UAT.md (2026-11-26T19:35:00Z). Expected: estados ambíguos/rate limit acionáveis; sem retry storm; reconciliação antes de republicar quando aplicável. |
| App Review/roles/tasks/Advanced Access | pass | Recorded in 32-HUMAN-UAT.md (2026-11-26T19:35:00Z). Expected: permissões, papéis e status de review coerentes com operação IG. |

### Gaps Summary

Nenhum gap automatizado encontrado. Human UAT foi concluído com 4/4 pass e reconciliado na Phase 33; nenhum item humano permanece pendente nesta verificação. Phase 33 não executou nova validação live Meta.

---

## HARD-01 Scenario Matrix

| Cenário HARD-01 | Requisito | Risco | Evidência automatizada (arquivo/teste) | Comando | Resultado | Tipo | Notas |
|---|---|---|---|---|---|---|---|
| draft/validação Instagram | HARD-01 | Caption inválida, vazamento de contato, mídia inválida, drift de contrato UI/backend | `backend/tests/test_social_post_generation.py`, `backend/tests/test_ig_media_validation.py`, `backend/tests/test_admin_instagram_social_posts.py` | `cd backend && pytest -q tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_admin_instagram_social_posts.py` | PASS (incluído no gate HARD-01/FB: 73 passed, 1 skipped, 3 warnings) | automatizado | Fronteira explícita: regras backend-enforced cobertas por pytest incluem limite 2200, template determinístico/normalização, texto seguro sem vazamento de contato (email/telefone), ausência de empresa confidencial/inventada no contrato de template, e contratos de mídia/validação IG referenciados pelos testes existentes. **Phase 30 D-09 UI-only contracts (no fabricated backend enforcement):** aviso `>30 hashtags` e orientação/CTA "link na bio" são contratos de UI/copy/orientação; não há hard-block/backend validation fabricado para `>30 hashtags`. |
| idempotência | HARD-01 | Duplicação de publicação/retry | `backend/tests/test_social_idempotency.py`, `backend/tests/test_social_publish_pipeline.py` | `cd backend && pytest -q tests/test_social_idempotency.py tests/test_social_publish_pipeline.py` | PASS (incluído no gate HARD-01/FB) | automatizado | Cobre no-op/idempotência por estado publicado/external_id e proteção contra duplicação cega. |
| retry | HARD-01 | Retry storm, backoff incorreto, reprocessamento inseguro | `backend/tests/test_social_retry_policy.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_admin_social_retry_api.py` | `cd backend && pytest -q tests/test_social_retry_policy.py tests/test_social_publish_pipeline.py tests/test_admin_social_retry_api.py` | PASS (incluído no gate HARD-01/FB) | automatizado | Cobre backoff/transient retry, exaustão/final, semântica segura de retry manual. |
| ambiguidade | HARD-01 | Duplicação por timeout/resultado inconclusivo | `backend/tests/test_facebook_publisher.py`, `backend/tests/test_instagram_publisher.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_admin_instagram_social_posts.py` | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_admin_instagram_social_posts.py` | PASS (incluído no gate HARD-01/FB) | automatizado | IG ambíguo requer reconciliação antes de publicar; sem auto-retry cego. FB timeout ambíguo preserva contrato anti-duplicação. |
| rate limit | HARD-01 | Retry storm em limite Meta/IG | `backend/tests/test_instagram_publisher.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_admin_instagram_social_posts.py` | `cd backend && pytest -q tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_admin_instagram_social_posts.py` | PASS (incluído no gate HARD-01/FB) | automatizado | `ig_rate_limit_blocked` / `content_publishing_limit` tratados como bloqueio acionável final, sem retry storm. |
| mapeamento de erros | HARD-01 | Vazamento de segredo/token, mensagem insegura, classificação errada | `backend/tests/test_facebook_publisher.py`, `backend/tests/test_instagram_publisher.py`, `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_admin_social_status_api.py` | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_admin_social_status_api.py` | PASS (incluído no gate HARD-01/FB) | automatizado | Mensagens pt-BR seguras; sem `access_token`/`page_access_token`/segredos em erros/logs/respostas. |
| caracterização/regressão do fluxo Facebook | HARD-01 | Regressão FB por mudanças IG/provider-aware | Gate FB completo (ver bloco abaixo) | Ver comando no bloco "Facebook Regression Gate" | PASS (73 passed, 1 skipped, 3 warnings) | automatizado | Gate executado em pytest normal; sem regressão observada no conjunto selecionado. |

## Facebook Regression Gate

**Gate executado em pytest normal.** Conclusão: **sem regressão Facebook observada** no escopo automatizado selecionado (resultado verde).

| Fluxo FB | Cobertura (testes/arquivos) | Comando | Resultado | Conclusão |
|---|---|---|---|---|
| Draft/geração/contrato social (FB-safe) | `backend/tests/test_social_publisher.py`, `backend/tests/test_admin_social_publish.py` | `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_social_retry_policy.py tests/test_social_idempotency.py tests/test_admin_social_publish.py tests/test_admin_social_retry_api.py tests/test_admin_social_status_api.py tests/test_admin_instagram_social_posts.py tests/test_social_worker_claim.py tests/test_social_publisher.py` | PASS (73 passed, 1 skipped, 3 warnings) | Contratos de publisher/approve preservados. |
| Aprovação/site-first/dispatch | `backend/tests/test_admin_social_publish.py` | mesmo comando do gate | PASS | Site-first e dispatch isolado preservados. |
| Publish assíncrono/pipeline | `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_facebook_publisher.py`, `backend/tests/test_social_worker_claim.py` | mesmo comando do gate | PASS | Pipeline provider-aware mantém FB funcional e isolado. |
| Status/logs seguros | `backend/tests/test_admin_social_status_api.py`, `backend/tests/test_admin_social_retry_api.py` | mesmo comando do gate | PASS | Status/retry/logs seguros e acionáveis. |
| Retry/idempotência | `backend/tests/test_social_retry_policy.py`, `backend/tests/test_social_idempotency.py`, `backend/tests/test_admin_social_retry_api.py` | mesmo comando do gate | PASS | Sem regressão de retry/idempotência. |
| Reconexão/erro seguro | `backend/tests/test_social_publish_pipeline.py`, `backend/tests/test_facebook_publisher.py` | mesmo comando do gate | PASS | Erros seguros pt-BR e sem vazamento de token. |

**Nota de escopo:** `test_social_post_generation.py` aparece no gate como evidência HARD-01 de draft/validação Instagram (IG), não como evidência de draft/geração Facebook.

## HARD-02 Operational Evidence

| Item | Evidência automatizada | Comando | Resultado | Status |
|---|---|---|---|---|
| Fonte operacional única Meta/FB/IG | `docs/META-INTEGRATION-TESTING.md` | `cd backend && pytest -q tests/test_docs_meta_instagram.py` | PASS (1 passed) | automatizado/documental |
| Alinhamento env vars canônicas/budgets IG | `backend/.env.example`, `backend/app/core/config.py`, `docs/META-INTEGRATION-TESTING.md` | `cd backend && pytest -q tests/test_docs_meta_instagram.py` | PASS | automatizado/documental |
| Checklist/handoff explícito | `docs/META-INTEGRATION-TESTING.md` | inspeção documental + `pytest -q tests/test_docs_meta_instagram.py` | PASS | automatizado/documental; execução live permanece handoff |

Referências: `docs/META-INTEGRATION-TESTING.md`, `backend/.env.example`. Não duplicar status operacional no doc; este arquivo é a evidência de fase.

## Manual Meta Handoff

| Item | Status | Pré-condições | Responsável/Ambiente necessário | Evidência sanitizada requerida | Executado nesta sessão | Resultado |
|---|---|---|---|---|---|---|
| Conexão OAuth Meta/IG e prontidão live | handoff/manual | App Meta, Page, IG Business/Creator vinculado, papéis/tarefas, envs canônicas configuradas | Operador autorizado + ambiente com credenciais Meta válidas | Screenshot/log sanitizado de `/admin/integracoes` e estado de prontidão, sem tokens/segredos | Não | Não executado / não evidenciado nesta sessão; UAT 4/4 pass registrado em 32-HUMAN-UAT.md (2026-11-26T19:35:00Z) |
| Smoke publish IG real (2-passos) | handoff/manual | Prontidão IG ready, mídia pública HTTPS acessível, job aprovado para teste | Operador autorizado + ambiente Meta/IG autorizado | IDs/permalink/timestamps sanitizados, status final e logs seguros | Não | Não executado / não evidenciado nesta sessão; UAT 4/4 pass registrado em 32-HUMAN-UAT.md (2026-11-26T19:35:00Z) |
| Reconciliação ambígua/rate limit real | handoff/manual | Cenário controlado ou incidente real autorizado; integração pronta | Operador autorizado + suporte Meta se necessário | Evidência sanitizada do estado, ação tomada, e resultado final/reconciliação | Não | Não executado / não evidenciado nesta sessão; UAT 4/4 pass registrado em 32-HUMAN-UAT.md (2026-11-26T19:35:00Z) |
| App Review/roles/tasks/Advanced Access conforme necessário | handoff/manual | Acesso ao Meta App Dashboard e permissões administrativas | Responsável legal/técnico do app Meta | Checklist/print sanitizado de permissões, papéis e status de review | Não | Não executado / não evidenciado nesta sessão; UAT 4/4 pass registrado em 32-HUMAN-UAT.md (2026-11-26T19:35:00Z) |

## Comandos Executados

| Comando | Resultado | Observação |
|---|---|---|
| `cd backend && python -m pytest -q tests/test_docs_meta_instagram.py tests/test_social_post_generation.py tests/test_facebook_publisher.py` | PASS (10 passed, 0.19s) | Spot-check executado pelo verificador nesta sessão. |
| `cd backend && pytest -q tests/test_docs_meta_instagram.py` | PASS (1 passed, 0.07s) | Registrado no 32-02-SUMMARY (Plan 32-02, Task 1). |
| `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_social_retry_policy.py tests/test_social_idempotency.py tests/test_admin_social_publish.py tests/test_admin_social_retry_api.py tests/test_admin_social_status_api.py tests/test_admin_instagram_social_posts.py tests/test_social_worker_claim.py tests/test_social_publisher.py` | PASS (73 passed, 1 skipped, 3 warnings) | Registrado no 32-01-SUMMARY (Plan 32-01, Task 2, commit `e0e028a`). Gate completo não reexecutado nesta verificação por custo; evidência de commit/summary consistente com artefatos presentes. |

---

_Verified: 2026-11-26T13:30:00Z_
_Reverified: 2026-11-26T19:35:00Z_
_Verifier: OpenCode (gsd-verifier), reconciled by OpenCode (gsd-executor, Phase 33 UAT reconciliation)_