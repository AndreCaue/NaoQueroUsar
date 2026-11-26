---
phase: 32-hardening-regression-operations
verified: 2026-11-26T12:39:54Z
status: human_needed
score: 7/7 automated scenario checks passed; 4 manual handoff items pending
requirements: [HARD-01, HARD-02]
---

# Phase 32: Hardening, Regression & Operations — Verification

**Phase Goal:** Hardening de regressão e operação: suíte automatizada para cenários críticos Instagram/Facebook e documentação operacional Meta/Instagram.
**Verified:** 2026-11-26T12:39:54Z
**Status:** human_needed
**Reason:** Cobertura automatizada HARD-01/HARD-02 passou; itens de validação Meta/live permanecem como handoff manual explícito e não foram executados nesta sessão.

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
| Conexão OAuth Meta/IG e prontidão live | handoff/manual | App Meta, Page, IG Business/Creator vinculado, papéis/tarefas, envs canônicas configuradas | Operador autorizado + ambiente com credenciais Meta válidas | Screenshot/log sanitizado de `/admin/integracoes` e estado de prontidão, sem tokens/segredos | Não | Não executado / não evidenciado nesta sessão |
| Smoke publish IG real (2-passos) | handoff/manual | Prontidão IG ready, mídia pública HTTPS acessível, job aprovado para teste | Operador autorizado + ambiente Meta/IG autorizado | IDs/permalink/timestamps sanitizados, status final e logs seguros | Não | Não executado / não evidenciado nesta sessão |
| Reconciliação ambígua/rate limit real | handoff/manual | Cenário controlado ou incidente real autorizado; integração pronta | Operador autorizado + suporte Meta se necessário | Evidência sanitizada do estado, ação tomada, e resultado final/reconciliação | Não | Não executado / não evidenciado nesta sessão |
| App Review/roles/tasks/Advanced Access conforme necessário | handoff/manual | Acesso ao Meta App Dashboard e permissões administrativas | Responsável legal/técnico do app Meta | Checklist/print sanitizado de permissões, papéis e status de review | Não | Não executado / não evidenciado nesta sessão |

## Comandos Executados

| Comando | Resultado | Observação |
|---|---|---|
| `cd backend && pytest -q tests/test_docs_meta_instagram.py` | PASS (1 passed, 0.07s) | Executado nesta sessão (Plan 32-02, Task 1). |
| `cd backend && pytest -q tests/test_facebook_publisher.py tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_post_generation.py tests/test_ig_media_validation.py tests/test_social_retry_policy.py tests/test_social_idempotency.py tests/test_admin_social_publish.py tests/test_admin_social_retry_api.py tests/test_admin_social_status_api.py tests/test_admin_instagram_social_posts.py tests/test_social_worker_claim.py tests/test_social_publisher.py` | PASS (73 passed, 1 skipped, 3 warnings) | Resultado registrado no `32-01-SUMMARY.md` (Plan 32-01, Task 2, commit `e0e028a`). |
