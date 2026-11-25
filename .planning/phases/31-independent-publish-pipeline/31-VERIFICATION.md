---
phase: 31-independent-publish-pipeline
verified: 2026-11-25T20:55:21-03:00
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Publicação Instagram real (2 passos) com credenciais Meta válidas"
    expected: "Ao aprovar/publicar uma vaga com Instagram habilitado, o backend cria container, consulta status quando necessário e publica a mídia; status final exibe IDs/permalink e histórico seguro sem tokens."
    why_human: "Requer integração externa real com Graph API/conta IG Business vinculada; comportamento de container/status/permalink não é totalmente simulável por inspeção estática."
  - test: "Independência FB x IG em falha real de uma plataforma"
    expected: "Forçando falha no Instagram (ex.: mídia/conta/limite), o Facebook e a publicação do site permanecem íntegros; forçando falha no Facebook, o Instagram não é corrompido."
    why_human: "A prova completa depende de execução fim a fim com provedores externos e estado real de contas."
  - test: "Rate limit/limite diário Instagram em runtime"
    expected: "Ao receber 2207042/content_publishing_limit/rate limit da Meta, UI mostra estado acionável em pt-BR, sem retry storm e sem duplicação cega."
    why_human: "Condição de limite é disparada pelo serviço externo Meta; precisa observação em ambiente integrado."
---

# Phase 31: Independent Publish Pipeline Verification Report

**Phase Goal:** Publicação Instagram ocorre de forma assíncrona, segura e independente do Facebook.
**Verified:** 2026-11-25T20:55:21-03:00
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Ao aprovar/publicar vaga com Instagram habilitado, processamento FB e IG é independente; falha em uma não bloqueia/corrompe a outra. | ✓ VERIFIED | `backend/app/api/v1/admin.py:199-325` aprova site-first, registra/dispatch FB em try/except próprio, depois bloco IG independente (`# IG independent dispatch (D-06, PUBL-01)`, `try/except` isolado) e dispatch por `process_social_post_safe`. `backend/app/services/social/publish_pipeline.py:1102-1240` percorre providers `("facebook","instagram")` em blocos isolados, agrega `by_provider`, e trata falhas por item/provider. |
| 2 | Publicação Instagram usa fluxo Graph API 2 passos (criar container, checar status quando necessário, publicar), com timeout/erro seguro. | ✓ VERIFIED | `backend/app/services/social/instagram.py:103-319` implementa `InstagramPublisher.publish`: POST `/{ig_user_id}/media`, polling bounded de status (`_wait_container_ready`, `IN_PROGRESS`/`FINISHED`/`ERROR`/`EXPIRED`), POST `/{ig_user_id}/media_publish`, permalink best-effort. Timeouts/orçamento limitados via `IG_PUBLISH_HTTP_TIMEOUT_SECONDS`, `IG_STATUS_POLL_MAX_ATTEMPTS`, `IG_STATUS_POLL_DELAY_SECONDS`, `IG_PUBLISH_MAX_ATTEMPT_SECONDS` (`backend/app/core/config.py:100-178`). |
| 3 | Admin consulta resultado por plataforma com status, erro seguro acionável, IDs/permalink quando disponíveis, e auditoria sem exposição de tokens/segredos. | ✓ VERIFIED | `backend/app/schemas/social_posts.py:61-136` expõe campos seguros (`published_permalink`, `ig_container_id/ig_media_id`, reconciliação, `by_provider`) e `SocialPostLogItem/LogsResponse` sem tokens. `backend/app/api/v1/admin.py:396-625` retorna worker `by_provider`, listagem provider-aware, status por provider e `/jobs/{job_id}/social-post/logs`. `backend/app/crud/social_posts.py:315-351,422+` mapeia campos seguros e lista logs sanitizados. Frontend: `frontend/lib/api.ts` tem tipos/calls (`getSocialPostLogs`, retry provider-aware), `SocialPostsClient.tsx` e `EditJobDialog.tsx` exibem status/IDs/permalink/reconciliação/histórico. |
| 4 | Retentativas/falhas ambíguas não causam duplicação cega; ambíguos ficam em estado seguro exigindo reconciliação antes de nova tentativa automática. | ✓ VERIFIED | `backend/app/services/social/publish_pipeline.py:385+` reconcilia IG por IDs conhecidos antes de novo publish; ambiguidade marca `failed` + `ig_reconciliation_required=True`, `ig_reconciliation_state="needs_reconciliation"`, `next_retry_at=None` (verificados em múltiplos pontos, ex.: 454-456, 1026+). `compute_social_retry_state` em `backend/app/crud/social_posts.py:252-309` bloqueia auto-retry ambíguo e permite retry manual IG com mensagem de reconciliação. `admin.py:543-545` reutiliza retry com reconciliação pelo pipeline. |
| 5 | Limites de rate/diário do Instagram tratados com segurança (sem retry storm), com estado acionável ao admin. | ✓ VERIFIED | `backend/app/services/social/instagram.py:53-97,170-172,274-276,365-367` classifica 2207042/subcode, `content_publishing_limit`, 429/rate-limit como bloqueio permanente acionável (`ig_rate_limit_blocked`/`ig_content_publishing_limit`) sem sinal de retry transitório. `publish_pipeline.py` persiste `ig_last_publish_error_code` e caminhos bloqueados; `crud/social_posts.py:252-279` retorna `can_retry=False` com razão pt-BR para rate/content limit. UI exibe `retry_block_reason`/mensagens acionáveis. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/alembic/versions/0008_instagram_publish_reconciliation.py` | Campos explícitos de reconciliação/publicação IG | ✓ VERIFIED | Contém `revision "0008..."`, `down_revision "0007..."`, colunas `ig_container_id`, `ig_media_id`, `ig_permalink`, `ig_reconciliation_required`, `ig_reconciliation_state`, `ig_last_reconciled_at`, `ig_last_publish_error_code`. |
| `backend/app/models/social_post.py` | Campos IG no modelo SocialPost | ✓ VERIFIED | Grep confirma mapeamentos IG reconciliation/publish metadata (container/media/permalink/reconciliação/erro/timestamps). |
| `backend/app/services/social/instagram.py` | Publisher IG 2 passos + classificação segura | ✓ VERIFIED | `class InstagramPublisher(SocialPublisher)` com `async def publish`, `media_publish`, `status_code`, `permalink`, detecção `2207042/content_publishing_limit`, sem vazamento de token em mensagens seguras. |
| `backend/app/services/social/publish_pipeline.py` | Pipeline provider-aware, claim/retry/reconciliation FB+IG | ✓ VERIFIED | `SUPPORTED_PROVIDERS=("facebook","instagram")`, `by_provider`, `run_social_publish_cycle`, dispatch IG, reconciliação `_ig_reconcile_before_publish`, marca ambíguo com `next_retry_at=None` e reconciliation required. |
| `backend/app/crud/social_posts.py` | Claim eligibility `publish_enabled` e retry-state seguro | ✓ VERIFIED | `list_due_for_claim` filtra `SocialPost.publish_enabled.is_(True)`; `compute_social_retry_state` trata ambíguo/reconciliação/rate-limit; `build_social_status_item` expõe campos seguros. |
| `backend/app/api/v1/admin.py` | Endpoints admin provider-aware, retry determinístico, logs seguros | ✓ VERIFIED | Worker retorna `by_provider`; approve tem dispatch IG isolado; retry resolve por post/provider com guards 400/409; endpoint `/jobs/{job_id}/social-post/logs`; status/list provider-aware. |
| `frontend/lib/api.ts` | Tipos/calls provider-aware e logs | ✓ VERIFIED | Campos `published_permalink`, `reconciliation_required`, etc.; `getSocialPostLogs`; `retrySocialPost` com provider. |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | UI por plataforma, audit, retry | ✓ VERIFIED | Renderiza provider Instagram/Facebook, usa `getSocialPostLogs`, `retrySocialPost(token, item.job_id, item.provider)`, mostra reconciliação/rate-limit/retry_block_reason. |
| `frontend/app/admin/review/EditJobDialog.tsx` | Retry IG e estados acionáveis | ✓ VERIFIED | Chama `retrySocialPost(token, job.id, "instagram")`; exibe permalink/IDs/timestamps/reconciliação/rate-limit. |
| `backend/tests/test_instagram_publisher.py` | Testes publisher IG | ✓ VERIFIED | Arquivo existe; suíte alvo passou (`19 passed` junto com pipeline/publisher). |
| `backend/tests/test_social_publish_pipeline.py` | Testes pipeline/reconciliação/rate/isolation | ✓ VERIFIED | Arquivo atualizado; suíte alvo passou. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/services/social/publish_pipeline.py` | `backend/app/services/social/instagram.py` | Dispatch para `InstagramPublisher`/handler IG | ✓ WIRED | `InstagramPublisher` importado e usado em `_process_instagram_claimed_post`/flow IG. |
| `backend/app/services/social/publish_pipeline.py` | `backend/app/crud/social_posts.py` | Claim/list/retry-state helpers | ✓ WIRED | Usa `list_due_for_claim`, claim helpers e persiste campos consumidos por retry-state/status. |
| `backend/app/services/social/publish_pipeline.py` | `backend/app/models/social_post.py` | Persistência container/reconciliação/permalink | ✓ WIRED | Atribui `ig_container_id`, `ig_reconciliation_required/state`, `ig_last_reconciled_at`, `ig_permalink`, `ig_last_publish_error_code`. |
| `backend/app/api/v1/admin.py` | `backend/app/services/social/publish_pipeline.py` | Worker/retry/dispatch chamam pipeline | ✓ WIRED | `run_social_publish_cycle` no worker/retry; `process_social_post_safe` no dispatch approve. |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | `frontend/lib/api.ts` | Status/retry/log calls | ✓ WIRED | Usa `getAdminSocialPosts`, `retrySocialPost`, `getSocialPostLogs`. |
| `backend/app/api/v1/admin.py` | `backend/app/models/social_post_log.py` / CRUD logs | Endpoint de auditoria segura | ✓ WIRED | `/social-post/logs` retorna `SocialPostLogsResponse` via `list_social_post_logs`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `SocialPostsClient.tsx` | `items`/`logs` | `getAdminSocialPosts`, `getSocialPostLogs` (admin API + DB) | Sim, consulta backend/DB | ✓ FLOWING |
| `EditJobDialog.tsx` | `igStatus` | `getInstagramSocialStatus` / retry response | Sim, estado persistido por provider | ✓ FLOWING |
| `InstagramPublisher` | publish outcome | Graph API create/status/publish/permalink | Sim (externo); código faz chamadas reais | ✓ FLOWING |
| `publish_pipeline` | IG reconciliation state | `social_posts` + Graph status/media lookups | Sim, baseado em IDs persistidos e respostas Graph | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Publisher/pipeline unit tests alvo do plano 31-01 | `cd backend && pytest -q tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py tests/test_social_publisher.py` | `19 passed in 0.22s` | ✓ PASS |
| Admin DB-backed tests citados pelos summaries | Não executado completamente neste verificador (ambiente já sinalizado sem migração 0008 nos summaries) | Summaries 31-01/31-02 registram falha de ambiente por coluna `social_posts.ig_container_id` ausente no test DB | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PUBL-01 | 31-01, 31-02 | Aprovação/publicação processa IG e FB de forma independente; falha em uma não bloqueia/corrompe a outra. | ✓ SATISFIED | Approve com blocos isolados + dispatch por post; pipeline por provider com `by_provider` e isolamento por item. |
| PUBL-02 | 31-01 | Backend publica IG por fluxo Graph 2 passos assíncronos com versão configurável e timeout seguro. | ✓ SATISFIED | `InstagramPublisher` implementa container/status/publish, `META_GRAPH_VERSION`, timeouts/budgets. |
| PUBL-03 | 31-01, 31-02 | Pipeline persiste legenda usada, IDs container/post, permalink, status, erro seguro, tentativas e timestamps; logs sem segredos. | ✓ SATISFIED | Campos IG em model/migration/schema; logs seguros e endpoint `/social-post/logs`; UI exibe campos seguros. |
| PUBL-04 | 31-01, 31-02 | Retry/backoff idempotente e seguro contra ambiguidade; ambíguo/timeout não dispara auto-retry cego. | ✓ SATISFIED | Ambíguo => `failed`+reconciliation required+`next_retry_at=None`; retry manual reconcilia IDs conhecidos antes de novo publish. |
| PUBL-05 | 31-01, 31-02 | Rate limit/limite diário tratados com segurança, sem retry storm, com status acionável. | ✓ SATISFIED | Classificação 2207042/content_publishing_limit/rate limit; `can_retry=False`/mensagem acionável; sem auto-retry. |

**Orphaned requirements check:** REQUIREMENTS.md traceability mapeia PUBL-01..05 para Phase 31 e ambos PLANs declaram esses IDs. Nenhum ID órfão para Phase 31.

**Doc note:** REQUIREMENTS.md ainda marca PUBL-01..05 como `Pending` (linhas 83-87) e REVW/HARD pendentes; evidência de código para PUBL-01..05 está presente. Isso é drift documental, não gap de implementação desta fase.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/tests` (DB-backed admin suites, ambiente) | n/a | `UndefinedColumnError: column social_posts.ig_container_id does not exist` relatado nos SUMMARYs 31-01/31-02 | ⚠️ Warning | Indica test DB sem migração 0008; bloqueia confiança total de regressão DB-backed neste ambiente, mas não evidencia ausência de implementação no código. |

### Human Verification Required

### 1. Publicação Instagram real ponta a ponta

**Test:** Em ambiente com integração Meta válida, aprovar vaga com IG habilitado e imagem válida.
**Expected:** Status evolui pelo fluxo 2 passos, publica com sucesso, e UI mostra ID/permalink/timestamps/histórico seguro.
**Why human:** Depende de Graph API real, conta IG Business, permissões e mídia acessível pela Meta.

### 2. Falha real isolada entre provedores

**Test:** Induzir falha IG (ex.: mídia inválida/remover readiness) e falha FB separadamente em vagas apropriadas.
**Expected:** Apenas a plataforma afetada falha/bloqueia; a outra e o site permanecem corretos.
**Why human:** Requer comportamento real dos serviços externos e validação operacional.

### 3. Rate limit/content publishing limit real

**Test:** Exercitar cenário de limite Meta (ou sandbox que retorne 2207042/content_publishing_limit).
**Expected:** Estado acionável pt-BR, `can_retry` bloqueado quando aplicável, sem tempestade de retries/duplicação.
**Why human:** Limites são impostos pelo Meta runtime.

### Gaps Summary

Nenhum gap de código identificado para os must-haves da fase. Verificação automatizada de código e testes unitários/pipeline alvo passaram. Status permanece `human_needed` por exigir confirmação de integração externa Meta (publicação real, isolamento sob falhas externas reais e rate limits reais).

---

_Verified: 2026-11-25T20:55:21-03:00_
_Verifier: Claude (gsd-verifier)_
