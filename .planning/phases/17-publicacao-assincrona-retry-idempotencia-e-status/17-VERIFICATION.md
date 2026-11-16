---
phase: 17-publicacao-assincrona-retry-idempotencia-e-status
verified: 2026-11-16T00:00:00Z
status: gaps_found
score: 11/12 must-haves verified
overrides_applied: 0
gaps:
  - truth: "Posts sociais são processados de forma resiliente e o admin consegue acompanhar/retentar com segurança mesmo após falhas internas de processamento."
    status: failed
    reason: "Itens claimados como `publishing` podem ficar presos sem recuperação se ocorrer exceção/erro após o commit do claim no ciclo por item; o caminho de erro registra contador/log mas não reverte o estado nem agenda recuperação segura, deixando o admin sem ação elegível (retry bloqueado por 'Publicação em andamento')."
    artifacts:
      - path: "backend/app/services/social/publish_pipeline.py"
        issue: "`run_social_publish_cycle` faz claim em transação separada e, no `except` do processamento por item (linhas ~354-357), não restaura `publishing` para estado recuperável/seguro nem cria `SocialPostLog`/`next_retry_at` coerente."
      - path: "backend/app/crud/social_posts.py"
        issue: "Não há fluxo de recuperação/reclaim para registros órfãos em `publishing` (consistente com D-04), mas ausência de recovery no crash pós-claim torna o estado silenciosamente preso."
    missing:
      - "Recovery transacional/compensatória no `except` por item: se post segue `publishing` sem `external_post_id`, persistir falha segura (mensagem pt-BR), attempts/log coerentes e política explícita de retry/manual-review sem duplicar publicação."
      - "Teste automatizado cobrindo crash/exceção pós-claim garantindo que o post não permaneça preso em `publishing`."
human_verification:
  - test: "Publicação real no Facebook (imediata e agendada)"
    expected: "Com integração Meta conectada e app/página válidos, aprovar vaga com 'publicar agora' gera tentativa assíncrona e registra `published` com `external_post_id`; agendar para horário futuro é processado pelo worker/cron no horário e publica uma única vez."
    why_human: "Depende de credenciais Meta reais, Graph API externa, conectividade e execução de cron/ambiente (Render) — não verificável estaticamente."
  - test: "Worker cron protegido em ambiente operacional"
    expected: "Chamada externa `POST /api/v1/admin/social/worker` com `X-Cron-Secret` válido processa elegíveis (1–5 min) sem expor segredos; sem/segredo inválido retorna 401/503 conforme configuração."
    why_human: "Requer configuração real de `CRON_SECRET`, agendamento Render/cron e observação operacional."
  - test: "Convivência com falhas transitórias/permanentes reais da Graph API"
    expected: "Erros transitórios exibem 'Falha temporária...' e reagemendam conforme backoff; token/permissão inválidos orientam reconexão sem loop automático; resultado ambíguo não gera duplicata e permanece para ação consciente."
    why_human: "Comportamento depende de respostas reais da Graph API e timing/rede; testes locais usam mocks."
  - test: "UX admin ponta a ponta (revisão, lista social, retry)"
    expected: "Badges/erros/links/horários aparecem corretamente; 'Tentar novamente' só ativa para elegíveis com feedback idempotente; refresh/401 funcionam conforme esperado em sessão expirada."
    why_human: "Validação visual/interativa no navegador com backend integrado."
---

# Phase 17: Publicação Assíncrona, Retry, Idempotência e Status — Verification Report

**Phase Goal:** Posts sociais sao enviados/agendados de forma assíncrona e resiliente (sem duplicatas), e o admin consegue acompanhar e retentar com segurança.
**Verified:** 2026-11-16T00:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria + PLAN must_haves)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: Aprovação dispara tentativa assíncrona (quando aplicável) e/ou agenda elegível; worker protegido acionado por cron processa itens com `FOR UPDATE SKIP LOCKED` sem bloquear resposta de aprovação. | ✓ VERIFIED | `backend/app/api/v1/admin.py`: `approve` usa `BackgroundTasks` e agenda `process_social_post_safe` após `approve_job` + `commit` + `refresh` apenas para post registrado/devido (`background_tasks.add_task`); `POST /social/worker` com `Depends(require_cron_secret)` chama `run_social_publish_cycle()`. `backend/app/crud/social_posts.py`: `list_due_for_claim` usa `with_for_update(skip_locked=True)` e elegibilidade `scheduled` vencido / `failed` com `next_retry_at` vencido. `publish_pipeline.run_social_publish_cycle` faz claim em transação e processa itens. |
| 2 | SC2: `FacebookPublisher` publica via `POST /{page_id}/feed` com `message` e `link`; sucesso registra `external_post_id`/`published_at` e falhas transitórias/permanentes seguem política de retry/backoff configurável (default 5) com `next_retry_at`/erro resumido. | ✓ VERIFIED | `backend/app/services/social/facebook.py`: `httpx.AsyncClient`, URL `https://graph.facebook.com/{settings.META_GRAPH_VERSION}/{page_id}/feed`, payload `message`/`link`/`access_token`, sucesso extrai `id` -> `external_post_id`; classifica timeout como `ambiguous`, rede/429/5xx como `transient`, erros definitivos como `permanent`. `publish_pipeline.py`: `compute_next_retry` usa `SOCIAL_MAX_ATTEMPTS` e `social_retry_delays_list`; persiste `attempts`/`next_retry_at`/`last_error`/`published_at`/`external_post_id`; logs sanitizados. |
| 3 | SC3: Idempotência impede duplicatas em concorrência, reexecução de cron ou clique duplo (estado/ID externo + lock/constraint); posts são fire-and-forget. | ✓ VERIFIED (core) | Claim com `FOR UPDATE SKIP LOCKED` + transição `publishing` antes do envio (`crud/social_posts.claim_for_publishing`, `publish_pipeline`); no-op se `published`/`external_post_id` (`process_claimed_post`, `list_due_for_claim`/claim guards); retry/direcionamento por `post_id` usa mesmo pipeline; UI retry single-flight (`EditJobDialog`, `SocialPostsClient`) e backend retorna `noop/not_eligible`. Não há chamadas Graph de update/delete no escopo (fire-and-forget preservado). Observação: recuperação de crash pós-claim ausente (ver gap/truth 5). |
| 4 | SC4: Admin vê badge/status social, erro resumido e link do post publicado por vaga, e pode acionar "tentar novamente" apenas para casos elegíveis respeitando as mesmas regras. | ✓ VERIFIED | Backend: `GET /jobs/{job_id}/social-status`, `GET /social-posts`, `POST /jobs/{job_id}/social-post/retry` protegidos por `require_admin`; `SocialPostStatusItem` com `status_label`, `last_error`, `published_url`/`external_post_id`, `can_retry`, `retry_block_reason`. Frontend: `EditJobDialog` bloco "Status da publicação no Facebook" com badges pt-BR, erro/link `Ver post no Facebook`, orientação `Abrir Integrações`, retry elegível com `Tentando novamente...`; `ReviewRow`/`ReviewQueue` indicadores; `/admin/social-posts` (`SocialPostsClient`) com lista/loading/empty/erro/retry; navegação em `layout.tsx` e `page.tsx`. |
| 5 | Resiliência operacional: item claimado não fica silenciosamente preso impedindo acompanhamento/retry seguro. | ✗ FAILED | `backend/app/services/social/publish_pipeline.py` (linhas ~296-358): se `process_claimed_post`/commit lança exceção após claim persistido, o `except` apenas incrementa contadores e loga; não há compensação para sair de `publishing` quando `external_post_id` ausente. `ReviewQueue`/UI exibem `Publicando`/`Publicação em andamento` e elegibilidade de retry bloqueia `publishing` (`crud/social_posts.compute_social_retry_state`). |
| 6 | Plan 17-01: FacebookPublisher real com token backend-only e `external_post_id` em sucesso. | ✓ VERIFIED | `backend/app/services/social/facebook.py` + `types.py` (`ambiguous`, `page_id/page_access_token`, `async def publish`). |
| 7 | Plan 17-01: Pipeline único com claim `FOR UPDATE SKIP LOCKED`, transição para `publishing`, backoff configurável e mensagens pt-BR seguras. | ✓ VERIFIED | `publish_pipeline.py`, `crud/social_posts.py`, `crud/social_accounts.py`; mensagens: "Reconecte a integração para publicar", "Falha temporária ao publicar. Uma nova tentativa será feita automaticamente.", "Não foi possível confirmar a publicação. Verifique antes de tentar novamente para evitar duplicidade." |
| 8 | Plan 17-01: Falhas/ tentativas persistidas em `social_posts` e `social_post_logs` sem segredos/tokens/payloads brutos. | ✓ VERIFIED | `_append_log` cria `SocialPostLog` com campos sanitizados/truncados (`_safe_text`), sem token/payload bruto; erros pt-BR resumidos em `last_error`. |
| 9 | Plan 17-02: Worker cron protegido por `CRON_SECRET` e contratos seguros de status/lista/retry idempotente. | ✓ VERIFIED | `@router.post("/social/worker")` + `Depends(require_cron_secret)`; endpoints status/list/retry com `require_admin`; schemas `SocialPostStatusItem/SocialRetryResponse/SocialWorkerResponse` em `schemas/social_posts.py`. |
| 10 | Plan 17-02: Aprovação site-first com dispatch imediato não bloqueante via mesmo pipeline. | ✓ VERIFIED | `approve` mantém `approve_job` + `commit` antes de dispatch; `BackgroundTasks.add_task(process_social_post_safe, ...)` protegido por try/except; `process_social_post_safe` chama `run_social_publish_cycle(post_id=...)`. |
| 11 | Plan 17-03: UI de revisão/edição com status, erro, link, retry elegível e orientação de reconexão. | ✓ VERIFIED | `EditJobDialog.tsx` contém "Status da publicação no Facebook", "Tentar novamente", "Tentando novamente...", "Ver post no Facebook", "Abrir Integrações", link externo com `target="_blank"`/`rel="noopener noreferrer"`. |
| 12 | Plan 17-03: Visão `/admin/social-posts` com estados, navegação e retry operacional. | ✓ VERIFIED | `frontend/app/admin/social-posts/page.tsx`, `SocialPostsClient.tsx`, links em `layout.tsx` e `admin/page.tsx`. |

**Score:** 11/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/social/facebook.py` | FacebookPublisher real (Graph feed) | ✓ VERIFIED | Existe, substantivo, wired via `publish_pipeline`/`PublishResult`; usa `httpx`, `/{page_id}/feed`, `message/link/access_token`, `external_post_id`. |
| `backend/app/services/social/publish_pipeline.py` | Pipeline claim/process/retry/idempotência/logging | ✓ VERIFIED (with gap) | Existe e exporta `process_social_post_safe`, `run_social_publish_cycle`; claim/lock/backoff/mensagens/logs presentes; falta recovery de crash pós-claim. |
| `backend/app/crud/social_posts.py` | Claim/elegibilidade/transições/status helpers | ✓ VERIFIED | `with_for_update(skip_locked=True)`, `publishing`, `published`, `failed`, `next_retry_at`, consultas status/retry. |
| `backend/app/crud/social_accounts.py` | Lookup seguro conta Facebook conectada | ✓ VERIFIED | `get_active_connected_facebook_account` e `SocialAccountStatus.connected`. |
| `backend/app/api/v1/admin.py` | Worker cron, status/retry APIs, dispatch pós-aprovação | ✓ VERIFIED | Rotas `/social/worker`, `/social-posts`, `/jobs/{job_id}/social-status`, `/jobs/{job_id}/social-post/retry`; `require_cron_secret`, `require_admin`, `BackgroundTasks`, `run_social_publish_cycle`. |
| `backend/app/schemas/social_posts.py` | Schemas seguros status/lista/retry/worker | ✓ VERIFIED | `SocialPostStatusItem`, `SocialRetryResponse`, `SocialWorkerResponse`, `can_retry`, `retry_block_reason`, `status_label`. |
| `backend/tests/test_facebook_publisher.py` | Teste publisher Graph (mockado) | ✓ VERIFIED | Arquivo existe (3590 bytes), contém testes. |
| `backend/tests/test_social_idempotency.py` | Teste no-op/idempotência | ✓ VERIFIED | Arquivo existe (3915 bytes), contém testes. |
| `backend/tests/test_admin_social_publish.py` | Cobertura approve site-first + dispatch | ✓ VERIFIED | Arquivo existe (4266 bytes), contém testes de approve/dispatch. |
| `backend/tests/test_admin_social_retry_api.py` | Cobertura retry elegível/idempotente | ✓ VERIFIED | Arquivo existe (4299 bytes), contém testes de retry. |
| `frontend/lib/api.ts` | Tipos/chamadas status/lista/retry | ✓ VERIFIED | `SocialPostStatusItem`, `getAdminSocialPosts`, `getSocialStatus`, `retrySocialPost`, endpoints `/admin/social-posts` e `/retry`. |
| `frontend/app/admin/review/EditJobDialog.tsx` | Status publicação Facebook + retry/link | ✓ VERIFIED | Seção "Status da publicação no Facebook", "Tentar novamente", "Ver post no Facebook", "Abrir Integrações". |
| `frontend/components/admin/ReviewRow.tsx` | Indicador compacto de status social na fila | ✓ VERIFIED | Renderiza labels sociais relevantes (`status_label`) com destaque para estados operacionais. |
| `frontend/app/admin/social-posts/page.tsx` | Página "Publicações no Facebook" | ✓ VERIFIED | Heading/intro presentes. |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | Lista operacional com estados/badges/links/retry | ✓ VERIFIED | Loading/empty/erro, "Ir para a fila de revisão", "Tentar novamente", "Ver post no Facebook", "Abrir Integrações". |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/services/social/publish_pipeline.py` | `backend/app/crud/social_posts.py` | claim + transições `publishing/published/failed` | ✓ WIRED | `list_due_for_claim`/`claim_for_publishing` com `FOR UPDATE SKIP LOCKED`, `mark_published`/`mark_failed`. |
| `backend/app/services/social/publish_pipeline.py` | `backend/app/services/social/facebook.py` | publish com contexto backend-only | ✓ WIRED | `FacebookPublisher().publish(SocialPostPayload(... page_id/page_access_token ...))`; token apenas em memória. |
| `backend/app/services/social/publish_pipeline.py` | `backend/app/core/config.py` | política de tentativas/backoff | ✓ WIRED | Usa `SOCIAL_MAX_ATTEMPTS` e `social_retry_delays_list`. |
| `backend/app/api/v1/admin.py` | `backend/app/services/social/publish_pipeline.py` | worker/cron/retry/dispatch imediato | ✓ WIRED | `run_social_publish_cycle`, `process_social_post_safe`, `BackgroundTasks.add_task`. |
| `backend/app/api/v1/admin.py` | `backend/app/deps.py` | proteção de endpoints | ✓ WIRED | `Depends(require_cron_secret)` no worker, `Depends(require_admin)` em status/retry/lista. |
| `backend/app/api/v1/admin.py` | `backend/app/schemas/social_posts.py` | response models seguros | ✓ WIRED | `SocialPostStatusItem`, `SocialPostStatusListResponse`, `SocialRetryResponse`, `SocialWorkerResponse`. |
| `frontend/app/admin/review/EditJobDialog.tsx` | `frontend/lib/api.ts` | status por vaga + retry | ✓ WIRED | `getSocialStatus`, `retrySocialPost`, render de link/ações. |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | `frontend/lib/api.ts` | listagem + retry | ✓ WIRED | `getAdminSocialPosts`, `retrySocialPost`. |
| `frontend/app/admin/layout.tsx` | `frontend/app/admin/social-posts/page.tsx` | navegação admin | ✓ WIRED | `href="/admin/social-posts"` presente. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `backend/app/services/social/facebook.py` | publish outcome / `external_post_id` | Resposta real de `POST https://graph.facebook.com/{version}/{page_id}/feed` (mockável em testes) | Yes (quando chamado com conta/token válidos; implementação não é stub) | ✓ FLOWING (code path) |
| `backend/app/api/v1/admin.py` + `schemas/social_posts.py` | `SocialPostStatusItem` (status/erro/link/eligibilidade) | `crud/social_posts` + `social_posts`/`jobs`/estado da conta | Yes | ✓ FLOWING |
| `frontend/app/admin/review/EditJobDialog.tsx` | `socialStatus` | `getSocialStatus` -> `GET /api/v1/admin/jobs/{id}/social-status` | Yes | ✓ FLOWING |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | `items` | `getAdminSocialPosts` -> `GET /api/v1/admin/social-posts` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Frontend lint (per SUMMARY/execução disponível) | `cd frontend && npm run lint` | Reportado como exit 0 com warnings (17-03 SUMMARY) | ✓ PASS (with warnings) |
| Phase 17 backend unit tests (per SUMMARY 17-01) | `cd backend && python -m pytest -q tests/test_facebook_publisher.py tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py tests/test_social_idempotency.py -x` | Reportado 8 passed em 17-01 | ✓ PASS (reported) |
| Phase 17 backend DB-backed API tests (per SUMMARY 17-02) | `cd backend && python -m pytest -q tests/test_social_worker_claim.py tests/test_admin_social_status_api.py tests/test_admin_social_retry_api.py tests/test_admin_social_publish.py tests/test_admin_social_posts.py ...` | Falhou no ambiente por schema de teste ausente (`relation "jobs" does not exist`) | ? SKIP (env not migrated) |

**Step 7b:** Parcialmente verificável no ambiente atual (sem DB de testes migrado e sem credenciais/cron Meta reais). Checks de execução completos requerem ambiente integrado.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PUB-01 | 17-01 | `FacebookPublisher.publish(post)` cria post via `POST /{page_id}/feed` com `message` e `link` | ✓ SATISFIED | `backend/app/services/social/facebook.py` implementa chamada real com payload `message/link/access_token` e URL `/{page_id}/feed`. |
| PUB-02 | 17-02 | Aprovação publica vaga no site mesmo se Facebook fora/indisponível | ✓ SATISFIED | `approve` faz `approve_job`+`commit` antes de social/dispatch; falhas sociais/dispatch capturadas sem alterar sucesso da vaga. |
| PUB-03 | 17-02 | Publicação imediata tentada de forma assíncrona após aprovação | ✓ SATISFIED | `BackgroundTasks.add_task(process_social_post_safe, post_id)` após commit para elegíveis; cron permanece como fallback (`/social/worker`). |
| PUB-04 | 17-01, 17-02 | Worker protegido por segredo/cron processa elegíveis com `FOR UPDATE SKIP LOCKED` | ✓ SATISFIED | `/social/worker` protegido por `require_cron_secret`; claim com `with_for_update(skip_locked=True)` e elegibilidade por `scheduled_at/next_retry_at`. |
| PUB-05 | 17-01 | Retry automático com backoff exponencial configurável; padrão 5 tentativas | ✓ SATISFIED | `compute_next_retry` usa `SOCIAL_MAX_ATTEMPTS` e `social_retry_delays_list` (`config.py` defaults 5 e delays); exaustão -> sem `next_retry_at`. |
| PUB-06 | 17-01 | Erros transitórios/permanentes classificados com backoff ou falha sem retry e sinalização clara | ✓ SATISFIED | Classificação em `facebook.py`/`publish_pipeline.py`; transitório agenda retry, permanente/ambíguo/bloqueado sem auto-retry; mensagens pt-BR seguras (reconexão/temporária/ambígua/definitiva). |
| PUB-07 | 17-01, 17-02 | Idempotência: nunca criar post duplicado (estado/`external_post_id` + lock/constraint; resistente a concorrência/clique duplo) | ✓ SATISFIED (core paths) | Guards de `published/external_post_id`, claim lock, pipeline único para cron/imediato/retry, UI single-flight e respostas `noop`. Gap separado: crash pós-claim pode prender item em `publishing` (sem duplicata, mas sem recuperação). |
| PUB-08 | 17-02 | Fire-and-forget: editar/fechar/expirar vaga não atualiza/remove post no Facebook | ✓ SATISFIED | Nenhuma chamada de update/delete Graph introduzida no fluxo; pipeline publica apenas. |
| UI-01 | 17-02, 17-03 | Admin exibe badge de status social, erro resumido, link do post publicado por vaga | ✓ SATISFIED | APIs/schemas seguros e UI em revisão/edição + `/admin/social-posts` com badges pt-BR, `last_error`, `Ver post no Facebook` quando disponível. |
| UI-02 | 17-02, 17-03 | Botão manual "tentar novamente" para posts elegíveis respeitando idempotência/regras de retry | ✓ SATISFIED | `can_retry`/`retry_block_reason` calculados no backend; retry via pipeline único; UI desabilita/oculta inelegíveis e trata `noop/not_eligible`. |

**Orphaned requirements for Phase 17:** None (all Phase 17 IDs in REQUIREMENTS — PUB-01..PUB-08, UI-01..UI-02 — are declared in 17-01/17-02/17-03 PLAN frontmatter).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/app/services/social/publish_pipeline.py` | 354-357 | Claimed `publishing` item not recovered on processing exception/commit failure | 🛑 Blocker | Pode deixar post preso em "Publicando", sem retry elegível e com acompanhamento incorreto (falha de resiliência). |
| `backend/app/api/v1/admin.py` | 144,147,168,189,200 etc. | Mojibake em strings pt-BR (`"Vaga n?o..."`, `"N?o foi poss?vel..."`) | ⚠️ Warning | Mensagens admin/UI podem ficar corrompidas; não afeta idempotência/segredos/publicação. (Também apontado em 17-REVIEW) |
| `backend/app/api/v1/admin.py` + `frontend/lib/api.ts` | 302-315, 732-746 | Contrato de paginação inconsistente (`getAdminSocialPosts` envia `page/limit`, endpoint ignora) | ℹ️ Info | Lista funciona com limite fixo; pode confundir evolução futura de paginação. |
| `frontend/*` (novos componentes sociais) | n/a | Lint warnings `react-hooks/set-state-in-effect` reportados no SUMMARY 17-03 | ℹ️ Info | `npm run lint` saiu 0, mas warnings merecem acompanhamento. |

### Human Verification Required

### 1. Publicação real no Facebook (imediata e agendada)

**Test:** Configurar integração Meta conectada e aprovar uma vaga com "Publicar agora" e outra agendada para horário próximo; aguardar worker/cron.
**Expected:** Post "agora" é processado assincronamente e vira `Publicado` com link/ID externo; post agendado publica no horário correto sem duplicatas.
**Why human:** Depende de Graph API real, credenciais/app/página, rede e cron operacional.

### 2. Worker cron protegido em ambiente operacional

**Test:** Acionar `POST /api/v1/admin/social/worker` com/sem `X-Cron-Secret` correto no ambiente de deploy.
**Expected:** Segredo correto retorna resumo idempotente; ausente/incorreto/secret não configurado respeita semântica 401/503.
**Why human:** Depende de configuração de ambiente e agendador externo.

### 3. Cenários reais de erro/retry da Graph API

**Test:** Simular/observar falha transitória, falha de permissão/token e timeout/ambiguidade.
**Expected:** Backoff automático para transitório, reconexão/orientação para permanente/bloqueante, sem auto-retry/duplicata em ambíguo.
**Why human:** Timing e respostas reais da API externa.

### 4. UX admin ponta a ponta

**Test:** Navegar por revisão, diálogo e `/admin/social-posts` com estados variados (agendado, publicando, publicado, falhou, sem conexão).
**Expected:** Copy pt-BR, badges, links externos, orientações e retry idempotente conforme elegibilidade.
**Why human:** Comportamento visual/interativo e estados em tempo real.

### Gaps Summary

A implementação principal da Fase 17 está presente no código: `FacebookPublisher` real para `/{page_id}/feed` com `message/link`, pipeline único com claim `FOR UPDATE SKIP LOCKED`, transição para `publishing`, idempotência por estado/`external_post_id`, backoff configurável (`SOCIAL_MAX_ATTEMPTS`/`SOCIAL_RETRY_DELAYS`), classificação/mensagens seguras em pt-BR, logging sanitizado, endpoints de worker/status/retry protegidos e UI admin para acompanhamento/retry elegível.

Há, porém, uma lacuna de resiliência: se o processamento falhar após o claim persistido, o item pode permanecer em `publishing` sem recuperação, impedindo retry manual seguro e degradando a observabilidade/operabilidade. Além disso, permanecem itens de qualidade/contrato (mojibake em mensagens admin e mismatch de paginação no endpoint de listagem) e a validação end-to-end depende de ambiente integrado (DB migrado, Meta/cron reais), por isso a meta da fase não pode ser marcada como totalmente atingida.

---

_Verified: 2026-11-16T00:00:00Z_
_Verifier: OpenCode (gsd-verifier)_
