---
phase: 17-publicacao-assincrona-retry-idempotencia-e-status
verified: 2026-11-16T14:30:00Z
status: human_needed
score: 12/12 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 11/12
  gaps_closed:
    - "Itens claimados em `publishing` não ficam mais presos após exceção/crash pós-claim: `run_social_publish_cycle` aplica recuperação compensatória best-effort, persiste falha ambígua segura (`MSG_AMBIGUOUS`), incrementa `attempts`, define `next_retry_at=None`, registra `SocialPostLog` sanitizado (`result=\"ambiguous\"`, `response_summary=\"post_claim_processing_exception\"`) e preserva idempotência quando já publicado/com `external_post_id`."
    - "Casos ambíguos/manual-review recuperados ficam inelegíveis para retry automático/manual até verificação consciente, evitando duplicidade (`compute_social_retry_state` bloqueia com orientação explícita)."
    - "Cobertura automatizada adicionada para o cenário de exceção pós-claim em `backend/tests/test_social_publish_pipeline.py`."
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Publicação real no Facebook (imediata e agendada)"
    expected: "Com integração Meta conectada e app/página válidos, aprovar vaga com 'publicar agora' gera tentativa assíncrona e registra `published` com `external_post_id`/`published_at`; agendar para horário futuro é processado pelo worker/cron no horário e publica uma única vez."
    why_human: "Depende de credenciais Meta reais, Graph API externa, conectividade e execução de cron/ambiente (Render) — não verificável estaticamente."
  - test: "Worker cron protegido em ambiente operacional"
    expected: "`POST /api/v1/admin/social/worker` com `X-Cron-Secret` válido processa elegíveis (1–5 min) e retorna resumo idempotente sem expor segredos; ausência/segredo inválido/secret não configurado respeitam 401/503 conforme configuração."
    why_human: "Requer configuração real de `CRON_SECRET`, agendador externo (Render/cron) e observação operacional."
  - test: "Cenários reais de erro/retry da Graph API"
    expected: "Falhas transitórias exibem 'Falha temporária...' e reagemendam conforme backoff; token/permissão/reconexão necessária orientam reconexão sem loop automático; resultado ambíguo ou recuperação pós-claim exige verificação consciente sem auto-retry/duplicata."
    why_human: "Comportamento depende de respostas/timing reais da Graph API e condições de rede."
  - test: "UX admin ponta a ponta (revisão, diálogo, lista social, retry)"
    expected: "Badges/erros/links/horários pt-BR aparecem corretamente; `Tentar novamente` só ativa para elegíveis com feedback idempotente; bloqueios ambíguos/reconexão exibem orientação correta; refresh/401 funcionam em sessão expirada."
    why_human: "Validação visual/interativa no navegador com backend integrado e estados em tempo real."
---

# Phase 17: Publicação Assíncrona, Retry, Idempotência e Status — Verification Report

**Phase Goal:** Posts sociais sao enviados/agendados de forma assíncrona e resiliente (sem duplicatas), e o admin consegue acompanhar e retentar com segurança.
**Verified:** 2026-11-16T14:30:00Z
**Status:** human_needed
**Re-verification:** Yes — after gap closure (17-04)

## Goal Achievement

### Observable Truths (Roadmap Success Criteria + PLAN must_haves)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: Aprovação dispara tentativa assíncrona/agendada (quando aplicável); worker protegido acionado por cron processa itens com `FOR UPDATE SKIP LOCKED` sem bloquear resposta de aprovação. | ✓ VERIFIED | `backend/app/api/v1/admin.py`: `approve` mantém site-first (`approve_job` + `commit` + `refresh`) e agenda `process_social_post_safe` via `BackgroundTasks.add_task(...)` após commit para post registrado/devido; `POST /social/worker` usa `Depends(require_cron_secret)` e chama `run_social_publish_cycle()`. `backend/app/crud/social_posts.py`: `list_due_for_claim` usa `with_for_update(skip_locked=True)` para elegíveis (`scheduled` vencidos, `failed` com `next_retry_at` vencido, e claim direcionado por `post_id`). |
| 2 | SC2: `FacebookPublisher` publica via `POST /{page_id}/feed` com `message` e `link`; sucesso registra `external_post_id`/`published_at`; falhas transitórias/permanentes/ambíguas seguem política segura com retry/backoff configurável e erro resumido. | ✓ VERIFIED | `backend/app/services/social/facebook.py`: URL `https://graph.facebook.com/{settings.META_GRAPH_VERSION}/{page_id}/feed`, payload `message`/`link`/`access_token` via `httpx.AsyncClient`, sucesso retorna `external_post_id`; classifica timeout/ambíguo, transitório e permanente com mensagens seguras. `backend/app/services/social/publish_pipeline.py`: `compute_next_retry` usa `SOCIAL_MAX_ATTEMPTS` e `social_retry_delays_list`; persiste `attempts`/`next_retry_at`/`last_error`/`published_at`/`external_post_id` e logs sanitizados. |
| 3 | SC3: Idempotência impede duplicatas em concorrência, reexecução de cron ou clique duplo; posts são fire-and-forget. | ✓ VERIFIED | Claim atômico com `FOR UPDATE SKIP LOCKED` + transição `publishing` (`crud/social_posts.claim_for_publishing`, `publish_pipeline.run_social_publish_cycle`), guards/no-op para `published`/`external_post_id` (`process_claimed_post`, claim/recuperação), retry/direcionamento por `post_id` no mesmo pipeline, UI single-flight (`EditJobDialog`, `SocialPostsClient`) e respostas idempotentes (`noop/not_eligible`). Fire-and-forget preservado (sem update/delete Graph no escopo). |
| 4 | SC4: Admin vê badge/status social, erro resumido e link do post publicado por vaga, e pode acionar "tentar novamente" apenas para casos elegíveis respeitando as mesmas regras. | ✓ VERIFIED | Backend: `GET /jobs/{job_id}/social-status`, `GET /social-posts`, `POST /jobs/{job_id}/social-post/retry` protegidos por `require_admin`; `schemas/social_posts.py` expõe `SocialPostStatusItem` (`status_label`, `last_error`, `published_url`/`external_post_id`, `can_retry`, `retry_block_reason`). Frontend: `EditJobDialog.tsx` ("Status da publicação no Facebook", "Tentar novamente", "Tentando novamente...", "Ver post no Facebook", "Abrir Integrações"), `ReviewRow.tsx` indicador compacto, `/admin/social-posts` (`page.tsx` + `SocialPostsClient.tsx`) com estados/loading/empty/erro/retry, navegação em `layout.tsx` e `admin/page.tsx`. |
| 5 | Resiliência operacional: item claimado não fica silenciosamente preso impedindo acompanhamento/retry seguro (gap 17-04). | ✓ VERIFIED | `backend/app/services/social/publish_pipeline.py`: no `except` por item (`run_social_publish_cycle`), recuperação best-effort reabre sessão, recarrega post (`get_social_post_by_id`) e, se `publishing` sem `external_post_id`, chama `mark_failed(..., attempts+1, last_error=MSG_AMBIGUOUS, next_retry_at=None, final=True)` e `_append_log(..., result="ambiguous", error_message=MSG_AMBIGUOUS, response_summary="post_claim_processing_exception")`; preserva estado se já publicado/com `external_post_id`. `crud/social_posts.py`: `compute_social_retry_state` bloqueia retry para esse caso ambíguo/manual-review com razão segura. `tests/test_social_publish_pipeline.py`: cobre crash pós-claim (não levanta, sai de `publishing`, attempts/log coerentes, `next_retry_at=None`, `can_retry=False`). |
| 6 | Plan 17-01: FacebookPublisher real com token backend-only e `external_post_id` em sucesso. | ✓ VERIFIED | `backend/app/services/social/facebook.py`, `backend/app/services/social/types.py` (`ambiguous`, payload com contexto backend-only). |
| 7 | Plan 17-01: Pipeline único com claim `FOR UPDATE SKIP LOCKED`, transição para `publishing`, backoff configurável e mensagens pt-BR seguras. | ✓ VERIFIED | `publish_pipeline.py`, `crud/social_posts.py`, `crud/social_accounts.py`; mensagens seguras: "Reconecte a integração para publicar", "Falha temporária ao publicar. Uma nova tentativa será feita automaticamente.", "Não foi possível confirmar a publicação. Verifique antes de tentar novamente para evitar duplicidade." |
| 8 | Plan 17-01: Falhas/tentativas persistidas em `social_posts` e `social_post_logs` sem segredos/tokens/payloads brutos. | ✓ VERIFIED | `_append_log` sanitiza/trunca campos e persiste `SocialPostLog`; `last_error` usa mensagens pt-BR seguras; token usado apenas em memória no payload de publicação. |
| 9 | Plan 17-02: Worker cron protegido por `CRON_SECRET` e contratos seguros de status/lista/retry idempotente. | ✓ VERIFIED | `@router.post("/social/worker")` com `Depends(require_cron_secret)`; endpoints status/list/retry com `Depends(require_admin)`; schemas seguros em `schemas/social_posts.py`. |
| 10 | Plan 17-02: Aprovação site-first com dispatch imediato não bloqueante via mesmo pipeline. | ✓ VERIFIED | `approve` agenda `process_social_post_safe(post_id)` pós-commit com tratamento seguro; `process_social_post_safe` chama `run_social_publish_cycle(post_id=..., limit=1)`. |
| 11 | Plan 17-03: UI de revisão/edição com status, erro, link, retry elegível e orientação de reconexão. | ✓ VERIFIED | `frontend/app/admin/review/EditJobDialog.tsx` e `frontend/lib/api.ts` (`getSocialStatus`, `retrySocialPost`) com blocos/ações pt-BR e link externo seguro. |
| 12 | Plan 17-03: Visão `/admin/social-posts` com estados, navegação e retry operacional. | ✓ VERIFIED | `frontend/app/admin/social-posts/page.tsx`, `frontend/app/admin/social-posts/SocialPostsClient.tsx`, navegação em `frontend/app/admin/layout.tsx` e `frontend/app/admin/page.tsx`. |

**Score:** 12/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/social/facebook.py` | FacebookPublisher real (Graph feed) | ✓ VERIFIED | `async def publish`, `httpx`, `/{page_id}/feed`, `message`/`link`/`access_token`, `external_post_id`. |
| `backend/app/services/social/publish_pipeline.py` | Pipeline claim/process/retry/idempotência/logging + recovery pós-claim | ✓ VERIFIED | `run_social_publish_cycle`, `process_social_post_safe`, `FOR UPDATE SKIP LOCKED` via CRUD claim, backoff/mensagens seguras, recuperação compensatória com `MSG_AMBIGUOUS`/`post_claim_processing_exception`. |
| `backend/app/crud/social_posts.py` | Claim/elegibilidade/transições/status helpers | ✓ VERIFIED | `list_due_for_claim`/`claim_for_publishing` com lock, transições `publishing/published/failed`, `compute_social_retry_state` com bloqueio ambíguo/manual-review. |
| `backend/app/crud/social_accounts.py` | Lookup seguro conta Facebook conectada | ✓ VERIFIED | `get_active_connected_facebook_account`, `SocialAccountStatus.connected`. |
| `backend/app/api/v1/admin.py` | Worker cron, status/retry APIs, dispatch pós-aprovação | ✓ VERIFIED | Rotas `/social/worker`, `/social-posts`, `/jobs/{job_id}/social-status`, `/jobs/{job_id}/social-post/retry`; `require_cron_secret`/`require_admin`; `BackgroundTasks` + `run_social_publish_cycle`. |
| `backend/app/schemas/social_posts.py` | Schemas seguros status/lista/retry/worker | ✓ VERIFIED | `SocialPostStatusItem`, `SocialRetryResponse`, `SocialWorkerResponse`, `can_retry`, `retry_block_reason`, `status_label`. |
| `backend/tests/test_facebook_publisher.py` | Teste publisher Graph (mockado) | ✓ VERIFIED | Existe e cobre contrato de publish/classificação (conforme plano/summaries). |
| `backend/tests/test_social_idempotency.py` | Teste no-op/idempotência | ✓ VERIFIED | Existe e cobre guards/idempotência (conforme plano/summaries). |
| `backend/tests/test_admin_social_publish.py` | Cobertura approve site-first + dispatch | ✓ VERIFIED | Existe (DB-backed, execução dependente de schema no ambiente). |
| `backend/tests/test_admin_social_retry_api.py` | Cobertura retry elegível/idempotente | ✓ VERIFIED | Existe (DB-backed, execução dependente de schema no ambiente). |
| `backend/tests/test_social_publish_pipeline.py` | Pipeline + crash pós-claim recovery | ✓ VERIFIED | Inclui `test_run_social_publish_cycle_recovers_post_claim_exception_without_leaving_publishing` validando saída de `publishing`, falha ambígua segura e bloqueio de retry. |
| `frontend/lib/api.ts` | Tipos/chamadas status/lista/retry | ✓ VERIFIED | `SocialPostStatusItem`, `getAdminSocialPosts`, `getSocialStatus`, `retrySocialPost`. |
| `frontend/app/admin/review/EditJobDialog.tsx` | Status publicação Facebook + retry/link | ✓ VERIFIED | Seção "Status da publicação no Facebook", "Tentar novamente"/"Tentando novamente...", "Ver post no Facebook", "Abrir Integrações". |
| `frontend/components/admin/ReviewRow.tsx` | Indicador compacto de status social na fila | ✓ VERIFIED | Renderiza labels sociais relevantes por status (`Agendado/Publicando/Publicado/Falhou`). |
| `frontend/app/admin/social-posts/page.tsx` | Página "Publicações no Facebook" | ✓ VERIFIED | Heading/intro corretos e composição com `SocialPostsClient`. |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | Lista operacional com estados/badges/links/retry | ✓ VERIFIED | Loading/erro/empty, badges pt-BR, "Ir para a fila de revisão", "Ver post no Facebook", "Abrir Integrações", retry elegível. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/services/social/publish_pipeline.py` | `backend/app/crud/social_posts.py` | claim + transições `publishing/published/failed` + recovery | ✓ WIRED | `list_due_for_claim`/`claim_for_publishing` (`FOR UPDATE SKIP LOCKED`), `mark_published`/`mark_failed`, `get_social_post_by_id` na recuperação pós-exceção. |
| `backend/app/services/social/publish_pipeline.py` | `backend/app/services/social/facebook.py` | publish com contexto backend-only | ✓ WIRED | `FacebookPublisher().publish(SocialPostPayload(..., page_id/page_access_token ...))` com token apenas em memória. |
| `backend/app/services/social/publish_pipeline.py` | `backend/app/core/config.py` | política de tentativas/backoff | ✓ WIRED | `compute_next_retry` usa `SOCIAL_MAX_ATTEMPTS` e `social_retry_delays_list`. |
| `backend/app/api/v1/admin.py` | `backend/app/services/social/publish_pipeline.py` | worker/cron/retry/dispatch imediato | ✓ WIRED | `run_social_publish_cycle`, `process_social_post_safe`, `BackgroundTasks.add_task`. |
| `backend/app/api/v1/admin.py` | `backend/app/deps.py` | proteção de endpoints | ✓ WIRED | `Depends(require_cron_secret)` no worker; `Depends(require_admin)` em status/retry/lista. |
| `backend/app/api/v1/admin.py` | `backend/app/schemas/social_posts.py` | response models seguros | ✓ WIRED | `SocialPostStatusItem`, `SocialPostStatusListResponse`, `SocialRetryResponse`, `SocialWorkerResponse`. |
| `frontend/app/admin/review/EditJobDialog.tsx` | `frontend/lib/api.ts` | status por vaga + retry | ✓ WIRED | `getSocialStatus`, `retrySocialPost`, atualização por resposta/refresh. |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | `frontend/lib/api.ts` | listagem + retry | ✓ WIRED | `getAdminSocialPosts`, `retrySocialPost`. |
| `frontend/app/admin/layout.tsx` e `frontend/app/admin/page.tsx` | `frontend/app/admin/social-posts/page.tsx` | navegação admin | ✓ WIRED | Links para `/admin/social-posts` presentes. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `backend/app/services/social/facebook.py` | outcome / `external_post_id` | `POST https://graph.facebook.com/{version}/{page_id}/feed` (mockável em testes) | Yes (implementação real; depende de credenciais/ambiente em runtime) | ✓ FLOWING (code path) |
| `backend/app/api/v1/admin.py` + `crud/social_posts.py` | `SocialPostStatusItem` | `social_posts`/`jobs`/estado de conta + regras de elegibilidade | Yes | ✓ FLOWING |
| `frontend/app/admin/review/EditJobDialog.tsx` | `socialStatus` | `getSocialStatus` -> `/api/v1/admin/jobs/{id}/social-status` | Yes | ✓ FLOWING |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | `items` | `getAdminSocialPosts` -> `/api/v1/admin/social-posts` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command / Evidence | Result | Status |
|----------|---------------------|--------|--------|
| 17-01 unit tests (publisher/pipeline/retry/idempotency) | `cd backend && python -m pytest -q tests/test_facebook_publisher.py tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py tests/test_social_idempotency.py -x` (17-01 SUMMARY) | Reportado 8 passed | ✓ PASS (reported) |
| 17-04 gap-closure tests (post-claim recovery + idempotency) | `cd backend && python -m pytest -q tests/test_social_publish_pipeline.py tests/test_social_idempotency.py -x` (17-04 SUMMARY) | Reportado 6 passed | ✓ PASS (reported) |
| Frontend lint | `cd frontend && npm run lint` (17-03 SUMMARY) | Exit 0 com warnings | ✓ PASS (with warnings) |
| 17-02 DB-backed API tests | `cd backend && python -m pytest -q tests/test_social_worker_claim.py tests/test_admin_social_status_api.py tests/test_admin_social_retry_api.py tests/test_admin_social_publish.py tests/test_admin_social_posts.py ...` (17-02 SUMMARY) | Falhou no ambiente por schema de teste ausente (`relation "jobs" does not exist`) | ? SKIP (env not migrated) |

**Step 7b:** Execução completa end-to-end não realizada neste ambiente (sem DB de testes migrado, sem integração Meta/cron real). Evidência automatizada local disponível cobre os caminhos unitários críticos, inclusive a recuperação pós-claim.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PUB-01 | 17-01 | `FacebookPublisher.publish(post)` cria post via `POST /{page_id}/feed` com `message` e `link` | ✓ SATISFIED | `backend/app/services/social/facebook.py` implementa `POST /{page_id}/feed` com `message`/`link`/`access_token` e retorno de `external_post_id`. |
| PUB-02 | 17-02 | Aprovação publica vaga no site mesmo se Facebook fora/indisponível | ✓ SATISFIED | `approve` em `backend/app/api/v1/admin.py` é site-first e isola falhas sociais/dispatch da resposta de sucesso. |
| PUB-03 | 17-02 | Publicação imediata tentada de forma assíncrona após aprovação | ✓ SATISFIED | `BackgroundTasks.add_task(process_social_post_safe, post_id)` pós-commit para elegíveis; cron `/social/worker` como fallback. |
| PUB-04 | 17-01, 17-02, 17-04 | Worker protegido por segredo/cron processa elegíveis com `FOR UPDATE SKIP LOCKED` | ✓ SATISFIED | Worker protegido por `require_cron_secret`; claim com `with_for_update(skip_locked=True)`; ciclo resiliente com recuperação pós-claim sem ficar preso em `publishing`. |
| PUB-05 | 17-01 | Retry automático com backoff exponencial configurável; padrão 5 tentativas | ✓ SATISFIED | `compute_next_retry` + `SOCIAL_MAX_ATTEMPTS`/`social_retry_delays_list` (defaults configurados). |
| PUB-06 | 17-01, 17-04 | Erros transitórios/permanentes classificados com backoff ou falha sem retry e sinalização clara | ✓ SATISFIED | Classificação segura (transient/permanent/ambiguous/blocked); ambíguo/pós-claim tratado como falha segura sem auto-retry e com orientação de verificação. |
| PUB-07 | 17-01, 17-02, 17-04 | Idempotência: nunca criar post duplicado (estado/`external_post_id` + lock/constraint; resistente a concorrência/clique duplo) | ✓ SATISFIED | Claim/transição atômica, guards por `published/external_post_id`, pipeline único para cron/imediato/retry, UI single-flight, recuperação pós-claim preserva idempotência e evita reenvio automático ambíguo. |
| PUB-08 | 17-02 | Fire-and-forget: editar/fechar/expirar vaga não atualiza/remove post no Facebook | ✓ SATISFIED | Nenhuma chamada de update/delete Graph introduzida no fluxo de publicação/status/retry. |
| UI-01 | 17-02, 17-03 | Admin exibe badge de status social, erro resumido, link do post publicado por vaga | ✓ SATISFIED | APIs/schemas seguros e UI em revisão/edição + `/admin/social-posts` com badges pt-BR, erro resumido e `Ver post no Facebook` quando disponível. |
| UI-02 | 17-02, 17-03, 17-04 | Botão manual "tentar novamente" para posts elegíveis respeitando idempotência/regras de retry | ✓ SATISFIED | `can_retry`/`retry_block_reason` no backend (incl. bloqueio ambíguo/manual-review), retry via pipeline único, UI habilita/desabilita e trata `noop/not_eligible` com feedback seguro. |

**Orphaned requirements for Phase 17:** None (all Phase 17 IDs in REQUIREMENTS.md — PUB-01..PUB-08, UI-01..UI-02 — are declared across 17-01/17-02/17-03/17-04 PLAN frontmatter and are accounted for).

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `backend/app/api/v1/admin.py` | Mojibake em strings pt-BR (`"Vaga n?o..."`, `"N?o foi poss?vel..."` em trechos existentes) | ⚠️ Warning | Mensagens admin podem ficar corrompidas em alguns caminhos; não afeta claim/idempotência/segurança de tokens nem o fluxo principal de publicação social. |
| `backend/app/api/v1/admin.py` + `frontend/lib/api.ts` | Contrato de paginação inconsistente (`getAdminSocialPosts` envia `page/limit`, endpoint de listagem ignora parâmetros) | ℹ️ Info | Lista funciona com limite fixo; pode confundir evolução futura de paginação, sem bloquear operação atual. |
| `frontend` (componentes sociais/admin alterados) | Lint warnings `react-hooks/set-state-in-effect` reportados (lint ainda exit 0) | ℹ️ Info | Não bloqueante; recomendado acompanhar para higiene/manutenibilidade. |

### Human Verification Required

### 1. Publicação real no Facebook (imediata e agendada)

**Test:** Configurar integração Meta conectada e aprovar uma vaga com "Publicar agora" e outra agendada para horário próximo; aguardar worker/cron.
**Expected:** Post "agora" é processado assincronamente e vira `Publicado` com `external_post_id`/`published_at` (e link se derivado disponível); post agendado publica no horário correto sem duplicatas.
**Why human:** Depende de Graph API real, credenciais/app/página, rede e agendamento operacional.

### 2. Worker cron protegido em ambiente operacional

**Test:** Acionar `POST /api/v1/admin/social/worker` com/sem `X-Cron-Secret` correto no ambiente de deploy (Render/cron).
**Expected:** Segredo correto retorna contadores/resumo idempotente; ausente/incorreto/secret não configurado respeitam semântica 401/503.
**Why human:** Requer configuração real de ambiente e execução por agendador externo.

### 3. Cenários reais de erro/retry da Graph API

**Test:** Observar/simular em ambiente integrado falha transitória, falha de permissão/token e timeout/ambiguidade (incluindo cenário de verificação manual pós-ambiguidade).
**Expected:** Transitórias reagemendam com backoff; permanentes/bloqueantes orientam reconexão sem loop; ambíguas não geram auto-retry/duplicata e permanecem para verificação consciente.
**Why human:** Depende de respostas e timing reais da Graph API.

### 4. UX admin ponta a ponta (revisão, diálogo, lista social, retry)

**Test:** Navegar por fila/revisão, diálogo de edição e `/admin/social-posts` com estados variados (sem rascunho, agendado, publicando, publicado, falhou, reconexão necessária, ambíguo/manual-review).
**Expected:** Copy/badges/horários/erros/links pt-BR corretos, `Abrir Integrações` quando aplicável, retry apenas elegível com feedback idempotente e bloqueio explícito em casos ambíguos.
**Why human:** Requer validação visual/interativa com backend integrado e estados dinâmicos.

### Gaps Summary

Nenhum gap de código bloqueante permanece aberto após 17-04: o pipeline publica no Facebook via Graph feed com claim `FOR UPDATE SKIP LOCKED`, idempotência por estado/`external_post_id`, retry/backoff configurável, classificação/mensagens seguras, logging sanitizado, endpoints protegidos (worker/status/retry), dispatch imediato site-first não bloqueante e UI admin para acompanhamento/retry elegível. A lacuna anterior de item preso em `publishing` após exceção pós-claim foi fechada com recuperação compensatória segura e teste automatizado.

A fase permanece `human_needed` (não `passed`) porque critérios operacionais dependem de verificação em ambiente integrado real: publicação Meta, execução de cron com segredo, comportamento real de falhas/ambiguidade da Graph API e UX ponta a ponta no navegador.

---

_Verified: 2026-11-16T14:30:00Z_
_Verifier: OpenCode (gsd-verifier)_