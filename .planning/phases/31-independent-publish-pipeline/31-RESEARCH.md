# Phase 31: Independent Publish Pipeline - Research

**Researched:** 2026-11-25
**Domain:** Instagram Graph API Content Publishing (2-step), async provider-isolated publish pipeline, idempotent reconciliation, rate-limit safety
**Confidence:** MEDIUM-HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Modelo de execução FB+IG
- **D-01:** **Ciclo por provider.** Generalizar o ciclo para iterar providers suportados (Facebook, Instagram), mantendo claim/processamento por item e isolamento por post/provider. Reaproveitar o padrão atual de `list_due_for_claim(provider=...)` / `run_social_publish_cycle`, sem acoplar falhas entre providers (PUBL-01).
- **D-02:** **Worker drena todos; retry infere provider.** `/admin/social/worker` processa todos os providers suportados em blocos independentes na mesma invocação, agregando contadores; retry/dispatch por `post_id` carrega o `social_post` e usa seu `provider`. Mantém endpoint simples e operação unificada.
- **D-03:** **Core compartilhado + handler por provider.** Manter núcleo comum de claim/attempt/log/idempotência/backoff e extrair handler/adapter por provider para conta/credenciais, payload, publisher e mapeamento de erros. Reaproveitar `SocialPublisher`/`PublishResult` e isolar bugs de IG do FB.
- **D-04:** **Resultado do worker agregado + breakdown por provider.** Manter contadores totais para compatibilidade e adicionar breakdown por provider (facebook/instagram) na resposta/log; cada provider roda em bloco isolado.
- **D-05:** **`publish_enabled=false` ignorado no claim.** `list_due_for_claim` só considera posts elegíveis com `publish_enabled=true`; posts desativados não são claimados nem mutados pelo worker. Preserva escolha intencional do admin.
- **D-06:** **Dispatch imediato independente por post/provider.** Para cada `social_post` elegível (FB/IG), disparar processamento independente (background/worker) por `post_id`; falha/timeout em um não afeta o outro. Alinha com PUBL-01 e com `process_social_post_safe(post_id)`.
- **D-07:** **IG indisponível/não pronto = falha final acionável.** Se conta IG não pronta, token inválido ou `needs_reconnect`, marcar como `failed` final (sem auto-retry) com mensagem segura em pt-BR orientando reconexão/verificação em Integrações. Evita retry storm e deixa estado claro.
- **D-08:** **Ordem sequencial por provider, isolada.** Dentro da mesma invocação do worker, processar um provider por vez (ex.: FB depois IG), cada um em bloco isolado com próprios claims/processamentos. Simples, previsível e suficiente para o volume esperado.

### Estados IG 2-passos/ambiguidade
- **D-09:** **Ambiguidade bloqueia para verificação/reconciliação.** Se houver timeout/resultado ambíguo após criar container IG (ou antes de confirmar publish), persistir IDs conhecidos, marcar estado ambíguo seguro sem auto-retry e exigir verificação/reconciliação antes de nova tentativa. Nunca duplicação cega (PUBL-04).
- **D-10:** **Colunas explícitas em `social_posts`.** Persistir IDs/estado IG em campos dedicados (ex.: container ID, ID final de mídia/publicação, permalink, metadados de reconciliação necessários), além dos campos atuais. `external_post_id` pode representar o ID final publicado; logs complementam auditoria.
- **D-11:** **Polling limitado quando necessário.** Após criar container, consultar status só quando necessário (não concluído/in_progress), com limite curto de tentativas/espera dentro do orçamento de timeout; se expirar sem conclusão segura, tratar como ambíguo/bloqueado (PUBL-02).
- **D-12:** **Ambíguo = `failed` + bloqueio de reconciliação.** Reusar status `failed` com erro seguro específico e metadados de reconciliação (container/IDs conhecidos, motivo bloqueado). Preserva enum atual e padrão já usado no FB, exigindo ação explícita antes de retry.
- **D-13:** **Retry manual reconcilia antes de publicar.** Ao retry manual em post IG ambíguo com `container_id` conhecido, consultar status/resultado do container ou mídia publicada antes de qualquer novo publish; se já publicado, registrar IDs/permalink e concluir; se container pronto, publicar o mesmo container; se expirado/inválido, falhar com orientação segura. Nunca criar novo container cegamente.
- **D-14:** **Orçamento limitado por tentativa.** Definir timeout por chamada HTTP e orçamento total limitado por tentativa; se estourar após ponto crítico (container criado/publicação enviada), marcar ambíguo/bloqueado para reconciliação. Evita worker preso e respeita PUBL-02.
- **D-15:** **Classificação de status do container.** `FINISHED` segue para publish; `IN_PROGRESS` entra em polling limitado; `ERROR/EXPIRED` vira falha conclusiva (nova tentativa pode criar novo container apenas quando seguro e sem ambiguidade de publish); timeout/inconclusivo vira ambíguo bloqueado.
- **D-16:** **Permalink best-effort pós-publish.** Após publish IG bem-sucedido, tentar buscar permalink em chamada separada; se falhar, manter post como publicado com ID e sem permalink (sem reverter sucesso). Atende PUBL-03 "quando disponível".
- **D-17:** **Ação admin reutiliza retry com semântica de reconciliação.** Manter ação de retry, com texto/estado deixando claro que será feita reconciliação segura (checar status/IDs antes de publicar). Aproveita endpoint/padrão atual.
- **D-18:** **Auditoria por eventos principais da tentativa.** Registrar resultado final da tentativa e resumos seguros dos passos principais (criação container, status check, publish, busca permalink), sem payloads sensíveis/tokens/segredos (PUBL-03).
- **D-19:** **Bloqueio ambíguo permanece até reconciliação.** Casos ambíguos bloqueados permanecem seguros indefinidamente até verificação/reconciliação; sem expiração automática para retry.
- **D-20:** **Reconciliação conclusiva atualiza local como publicado.** Se reconciliação detectar que container/mídia IG já foi publicado com sucesso, registrar IDs/permalink/timestamps, marcar `published`, limpar erro ambíguo e anexar log de reconciliação.

### OpenCode's Discretion
- **Rate limit e limite diário (PUBL-05, não discutido):** usuário não selecionou esta área. OpenCode tem discrição na implementação, mas DEVE satisfazer PUBL-05: tratar `content_publishing_limit` como autoridade de runtime quando aplicável, classificar 2207042/rate limit com segurança, sem retry storm, e expor estado acionável ao admin. Preferir padrão conservador alinhado a `PublishFailureCategory` e backoff existente.
- **Status e auditoria no admin (PUBL-03, superfície UI não discutida):** usuário não selecionou esta área. OpenCode tem discrição no formato exato da UI/API admin, mas DEVE satisfazer PUBL-03: status por plataforma, erro seguro acionável, IDs/permalink quando disponíveis, tentativas/timestamps e histórico/auditoria sem exposição de tokens/segredos. Reaproveitar padrões de `ReviewQueue`/status social existentes.
- Nomes exatos de colunas/campos novos em `social_posts`, schemas e migrations, desde que atendam PUBL-03/PUBL-04 e sejam claros.
- Orçamento numérico exato de timeout/polling/backoff e limites de tentativas por chamada, desde que seguros e configuráveis quando apropriado.
- Shape exato do breakdown por provider no worker response, preservando compatibilidade com consumidores atuais.
- Wording pt-BR exato de erros/ações de reconciliação, desde que claro, seguro e acionável.
- Estratégia interna de reconciliar "já publicado" (campos Graph consultados, ordem de checks), desde que não crie duplicação.

### Deferred Ideas (OUT OF SCOPE)
- **Rate limit e limite diário (PUBL-05) — área não discutida nesta sessão.** Requisitos permanecem obrigatórios; implementação fica em discrição do OpenCode/planner, desde que cumpra PUBL-05.
- **Status e auditoria no admin (PUBL-03) — superfície UI detalhada não discutida.** Requisitos permanecem obrigatórios; planner deve definir mínima UI/API útil e segura.
- Qualquer evolução para agendamento avançado, múltiplas contas IG, Stories/Reels/carrossel, métricas/analytics ou inbox de comentários/DMs — fora do escopo v1.5.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PUBL-01 | Aprovação/publicação processa Instagram e Facebook de forma independente; falha em uma plataforma não bloqueia nem corrompe a outra. | Provider-isolated dispatch on approve (`BackgroundTasks` per post/provider), provider-aware worker cycle with isolated try/except blocks, separate `social_posts` rows per `(job_id, provider)`, no shared mutable state between FB/IG handlers. |
| PUBL-02 | Backend implementa publicação Instagram Graph API (Content Publishing) em 2 passos assíncronos (criar container, checar status quando necessário, publicar) com versão Graph configurável e tratamento seguro de timeout. | New `InstagramPublisher` with create-container → poll-status → media_publish flow; uses `settings.META_GRAPH_VERSION`; bounded polling/timeout budget; timeout after critical point becomes ambiguous (D-09/D-11/D-14/D-15). |
| PUBL-03 | Pipeline persiste legenda usada, IDs de container/post, permalink quando disponível, status, erro seguro, tentativas e timestamps; logs não expõem tokens/segredos. | Explicit `social_posts` columns for IG IDs/permalink/reconciliation metadata; `SocialPostLog` step/result summaries; safe pt-BR messages; sanitize/redact in logs; admin status/list endpoints expose safe fields. |
| PUBL-04 | Retry/backoff é idempotente e seguro contra ambiguidade; resultado ambíguo/timeout não dispara auto-retry cego que possa duplicar post. | Ambiguous state = `failed` + reconciliation metadata + no `next_retry_at`; manual retry reconciles before creating/publishing; existing idempotency by `external_post_id` preserved; container/status checks before new publish. |
| PUBL-05 | Rate limit e limite diário de publicação Instagram são tratados com segurança (consulta/runtime authority como `content_publishing_limit` quando aplicável, classificação segura de 2207042/rate limit, sem retry storm) com status acionável ao admin. | Classify 2207042/rate-limit as blocked/non-retry-storming failure; optional precheck via `content_publishing_limit`; safe actionable admin message; no automatic tight retry; record actionable state in `last_error`/retry metadata. |
</phase_requirements>

## Summary

Phase 31 extends an existing Facebook-only social publish system into a provider-aware, safety-first pipeline that also publishes Instagram. The codebase already has the right foundations: `social_posts` is unique per `(job_id, provider)`, `publish_pipeline.py` has claim/lock/idempotency/ambiguous-no-auto-retry semantics, `SocialPublisher`/`PublishResult` provide a publisher contract, `image_media.py` can prepare/validate the exact IG image, and Phase 30 already created Instagram draft/status/review contracts with `publish_enabled`. **The main work is generalization, not reinvention.** [VERIFIED: codebase]

The highest-risk behaviors are the ones the user locked: IG 2-step container/publish ambiguity, duplicate-post prevention, rate-limit storms, and provider isolation. The current Facebook pipeline classifies timeout as ambiguous and refuses auto-retry - Phase 31 must preserve that posture and add IG-specific reconciliation using persisted container/media IDs. The plan should treat "unknown after critical Graph action" as unsafe to retry automatically. [VERIFIED: `backend/app/services/social/publish_pipeline.py`, `backend/app/services/social/facebook.py`; CITED: .planning/research/PITFALLS.md]

**Primary recommendation:** Refactor `publish_pipeline.py` into a shared provider-agnostic core plus explicit Facebook/Instagram handlers/publishers, add explicit IG reconciliation columns on `social_posts`, and make every admin/worker/retry surface provider-aware while keeping Facebook response compatibility. Do not build a generic plugin framework; use small explicit provider dispatches.

## Project Constraints (from AGENTS.md)

- Stack fixed: Next.js 16 App Router + Tailwind; FastAPI; Neon Postgres; Groq; Cloudflare Turnstile; Vercel + Railway/Render. [VERIFIED: AGENTS.md]
- Locale pt-BR for user-facing/admin text. [VERIFIED: AGENTS.md, existing code]
- Admin-only single master, no multi-user. [VERIFIED: AGENTS.md]
- Social/ops must not leak secrets/tokens; errors must be safe and actionable. [VERIFIED: AGENTS.md, existing social services]
- No direct repo edits outside GSD workflow unless user explicitly bypasses. [VERIFIED: AGENTS.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Approve/register/dispatch FB+IG independently | API / Backend | Database / Storage | Approve endpoint orchestrates site-first approval and independent provider registration/dispatch; DB rows track per-provider state. |
| Claim/process/publish/retry/reconcile | API / Backend | Database / Storage | Pipeline owns state transitions, locks, idempotency, logs, and provider handler dispatch. |
| Instagram container create/status/publish/permalink | API / Backend | External (Meta Graph) | Backend publisher performs Graph calls with stored credentials and safe error mapping. |
| IG image revalidation before publish | API / Backend | External/Public Media URL | `image_media.prepare_instagram_media` and public media contract ensure IMAG-01; only IG blocked. |
| Admin status/audit/retry UI | Frontend (Admin) | API / Backend | UI renders backend-safe status/audit fields and invokes provider-aware retry/status endpoints. |
| Rate-limit visibility/blocking | API / Backend | Frontend (Admin) | Backend classifies/stores actionable state; admin displays it. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python / FastAPI | existing repo stack | Admin/API endpoints, background dispatch | Already used for social/admin endpoints. [VERIFIED: codebase] |
| SQLAlchemy 2.x async + Alembic | existing repo stack | `social_posts`/logs schema, migrations, claim/query updates | Existing social persistence pattern. [VERIFIED: codebase] |
| httpx | existing repo stack | Facebook/Instagram Graph HTTP calls | Already used by FB publisher/meta_oauth/image checks. [VERIFIED: codebase] |
| Pydantic v2 | existing repo stack | Admin/social schemas | Existing request/response contracts. [VERIFIED: codebase] |
| Next.js 16 / React / TS | existing repo stack | Admin review/social status UI | Existing admin surfaces. [VERIFIED: codebase] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `app.services.social.image_media` | internal | Revalidate exact IG image/public URL before publish | Every IG publish attempt/reconciliation that may publish. [VERIFIED: codebase] |
| `app.services.social.meta_oauth` / `instagram_readiness` | internal | Resolve account/token/IG readiness/reconnect state | IG preflight and auth failure classification. [VERIFIED: codebase] |
| APScheduler patterns | existing | Reference only for in-process scheduling | Not needed for Phase 31 unless adding polling jobs; prefer worker/dispatch model. [VERIFIED: scheduler.py] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Explicit provider dispatch (`facebook`/`instagram`) | Generic plugin registry/framework | Registry adds abstraction and indirection; only 2 providers and strong safety constraints make explicit dispatch clearer. |
| Persist IG reconciliation fields on `social_posts` | Infer from logs only | Logs are audit; columns are needed for deterministic reconciliation/idempotency decisions. D-10 locks columns. |
| Manual retry with reconciliation | Separate "reconcile" endpoint/button | D-17 locks reusing retry action with clear semantics; separate endpoint increases surface area. |

**Installation:** No new packages required.

## Architecture Patterns

### System Architecture Diagram

```text
[Admin Approve / Retry / Worker Cron]
              |
              v
      [FastAPI admin.py]
              |
   +----------+-----------+
   |                      |
   v                      v
[FB social_post row]   [IG social_post row]   (unique per job_id+provider)
   |                      |
   |  BackgroundTasks /   |  BackgroundTasks /
   |  worker claim        |  worker claim
   v                      v
[process_social_post_safe(post_id)]
              |
              v
    [publish_pipeline core]
    - claim_for_publishing
    - idempotency guard (external_post_id/published)
    - append safe logs
    - classify/retry/finalize
              |
     provider dispatch
     /              \
    v                v
[FB handler]      [IG handler]
    |                |
    |                +--> [IMAG-01 revalidate via image_media]
    |                +--> [resolve IG account/readiness/token]
    |                +--> [InstagramPublisher]
    |                         |
    |                         +--> POST /{ig-user-id}/media (container)
    |                         +--> GET /{container}?fields=status_code (limited poll)
    |                         +--> POST /{ig-user-id}/media_publish
    |                         +--> GET /{media-id}?fields=permalink (best-effort)
    v
[FacebookPublisher] -> POST /{page-id}/feed
              |
              v
     [social_posts + social_post_logs]
              |
              v
[Admin status/list/review APIs + UI]
  - status/error/IDs/permalink/timestamps
  - retry = reconcile-before-publish for ambiguous IG
```

### Recommended Project Structure

```text
backend/app/
├── api/v1/admin.py                         # MODIFY: worker breakdown, provider-aware retry/status/list, approve IG dispatch
├── crud/social_posts.py                    # MODIFY: publish_enabled claim filter, reconciliation-aware retry helpers
├── models/social_post.py                   # MODIFY: explicit IG/reconciliation columns
├── schemas/social_posts.py                 # MODIFY: status/retry/worker/audit-safe fields
├── services/social/
│   ├── publish_pipeline.py                 # MODIFY: shared core + provider dispatch + reconciliation
│   ├── publisher.py                        # REUSE (maybe unchanged)
│   ├── types.py                            # MODIFY: add safe optional fields if needed
│   ├── facebook.py                         # REUSE/MINOR: align with shared classification
│   └── instagram.py                        # NEW: IG 2-step publisher + status/permalink helpers
└── core/config.py                          # MODIFY only if adding safe polling/timeout/rate knobs

backend/alembic/versions/
└── 0008_*.py                               # NEW: IG publish/reconciliation columns

frontend/
├── lib/api.ts                              # MODIFY: provider-aware status/retry/list/worker types as needed
├── app/admin/review/EditJobDialog.tsx      # MODIFY: IG retry/status action clarity if surfaced
├── app/admin/social-posts/SocialPostsClient.tsx  # MODIFY: provider-aware display, permalink, reconciliation message
└── app/admin/review/ReviewQueue.tsx        # MODIFY if status surface needs per-provider awareness
```

### Pattern 1: Shared Core, Explicit Provider Handlers
**What:** Keep one claim/log/idempotency/finalize core; select provider handler by `post.provider`.
**When to use:** All publish processing.
**Example:**
```python
# Source: codebase pattern from publish_pipeline.py (VERIFIED)
async def process_claimed_post(session, post, ...):
    if post.external_post_id or post.status == SocialPostStatus.published:
        return "idempotent"
    handler = get_provider_handler(post.provider)  # facebook | instagram
    preflight = await handler.preflight(session, post, settings)
    if preflight.blocked:
        return await finalize_blocked(...)
    result = await handler.publish(session, post, settings, publisher=...)
    return await finalize_result(...)
```

### Pattern 2: Ambiguity Becomes Reconciliation State
**What:** If a critical IG step may have succeeded externally but local confirmation is missing, persist known IDs and mark blocked ambiguous - never auto-retry.
**When to use:** container create timeout/unknown, publish timeout/unknown, status polling inconclusive after container exists.
**Example:**
```python
# Source: D-09/D-12/D-13/D-15/D-19 (VERIFIED context) + existing ambiguous pattern
if outcome.ambiguous_after_critical_step:
    post.ig_reconciliation_state = "needs_reconciliation"
    post.ig_last_reconciled_at = now
    post.next_retry_at = None  # D-19
    post.last_error = SAFE_AMBIGUOUS_IG_MESSAGE
    await mark_failed(..., final=True)
    await append_log(..., result="ambiguous", response_summary="ig_publish_ambiguous")
```

### Pattern 3: Manual Retry = Reconcile Then Act
**What:** Retry endpoint/action first reconciles IG ambiguous state; only publishes when safe.
**When to use:** `POST /admin/jobs/{id}/social-post/retry` for IG, especially ambiguous/reconciliation states.
**Example:**
```text
retry(post_id)
  -> load post.provider
  -> if instagram and reconciliation needed:
       check known container/media state
       if published: mark_published + log reconciled_published
       if finished_not_published: publish same container
       if in_progress: poll limited; if still unclear -> keep blocked ambiguous
       if error/expired/no_evidence: clear ambiguity only if safe, then create new container
  -> else run normal provider claim/process
```

### Anti-Patterns to Avoid
- **Single Facebook-only worker cycle:** breaks D-01/D-02 and PUBL-01. Iterate providers in isolated blocks.
- **Creating a new IG container during ambiguity:** violates D-09/D-13/PUBL-04. Reconcile known IDs first.
- **Auto-retrying 2207042/rate limit:** violates PUBL-05. Mark actionable and wait for operator/window.
- **Treating IG image validation as site/Facebook blocker:** violates IMAG-01. Block only IG.
- **Logging raw Graph payloads/tokens:** violates PUBL-03/security constraints. Log safe summaries/codes/categories only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| IG image public URL/validation | Ad-hoc URL checks or regeneration in publisher | `app.services.social.image_media.prepare_instagram_media` + `validate_media_public_base_url` | Phase 29 already encodes IMAG-01/03 rules, hash/version exactness, safe pt-BR messages. [VERIFIED: codebase] |
| Claim locking/idempotency | New queue/lock system | Existing `list_due_for_claim(..., with_for_update(skip_locked=True))`, `claim_for_publishing`, `external_post_id` guards | Already battle-tested for FB; extend carefully. [VERIFIED: codebase] |
| Retry/backoff | Custom scheduler/state machine framework | Existing `compute_next_retry`, `mark_failed`, `next_retry_at` pattern + reconciliation metadata | Keep behavior consistent and simple. [VERIFIED: codebase] |
| Admin auth/secret handling | New auth path for worker/retry | Existing `require_admin`, `require_cron_secret`, token encryption helpers | Preserve security model. [VERIFIED: codebase] |

**Key insight:** The dangerous part of Phase 31 is state ambiguity, not HTTP plumbing. Reuse existing persistence/guards and spend complexity budget on reconciliation and provider isolation.

## Common Pitfalls

### Pitfall 1: Duplicate IG post after ambiguous publish
**What goes wrong:** Timeout/5xx occurs after container publish may have succeeded; naive retry creates/publishes again.
**Why it happens:** IG publish is 2-step async and network failures are ambiguous. [CITED: .planning/research/PITFALLS.md]
**How to avoid:** Persist container ID immediately; on ambiguous post-critical step mark `failed` with reconciliation metadata and no `next_retry_at`; manual retry checks status/media before any new publish (D-09/D-13/D-19).
**Warning signs:** New container created while old container ID exists and ambiguous flag set; multiple external IDs for same `social_post`.

### Pitfall 2: Facebook regression from provider generalization
**What goes wrong:** Worker/retry/status changes break FB-only flow or couple FB to IG errors.
**Why it happens:** Current code hardcodes `provider="facebook"` in many paths. [VERIFIED: admin.py, crud, publish_pipeline]
**How to avoid:** Isolated provider blocks in worker (D-08), provider-aware functions with FB defaults where needed for compatibility, characterization tests for FB before/with changes.
**Warning signs:** FB status endpoint behavior changes; approve dispatch fails both providers on one exception; FB tests start failing.

### Pitfall 3: Claiming disabled IG drafts
**What goes wrong:** `publish_enabled=false` IG draft gets claimed/published unexpectedly.
**Why it happens:** Current `list_due_for_claim` only filters status/schedule/retry, not `publish_enabled`. [VERIFIED: crud/social_posts.py]
**How to avoid:** Add `publish_enabled == true` eligibility filter in claim query (D-05); keep admin toggle semantics intact.
**Warning signs:** Disabled draft transitions to publishing/failed.

### Pitfall 4: Rate-limit retry storm
**What goes wrong:** 2207042/daily limit treated as transient; worker retries rapidly.
**Why it happens:** Existing transient classification schedules backoff. [VERIFIED: publish_pipeline.py; CITED: .planning/research/PITFALLS.md]
**How to avoid:** Classify 2207042/rate-limit as blocked/non-auto-retry (or very conservative delayed, but no storm). Prefer final/blocked actionable state until operator action or explicit window expiry strategy. D-19 means ambiguous stays blocked; rate-limit should also be clearly actionable. [ASSUMED: final blocked is safest for PUBL-05 given "sem retry storm" and no discussed auto-window behavior]
**Warning signs:** Many attempts with same rate-limit error in short interval.

### Pitfall 5: Image URL valid at review but invalid at publish
**What goes wrong:** IG container creation fails with media fetch error.
**Why it happens:** `MEDIA_PUBLIC_BASE_URL` misconfigured, asset missing, or deployment/routing changed. [CITED: .planning/research/PITFALLS.md]
**How to avoid:** Revalidate via `prepare_instagram_media` immediately before IG publish/reconciliation publish (IMAG-01). Fail only IG with safe pt-BR message.
**Warning signs:** `invalid_public_url`/media fetch failures in publish logs.

## Code Examples

Verified patterns from official sources/local codebase:

### Provider-aware claim filter (required by D-05)
```python
# Source: backend/app/crud/social_posts.py (VERIFIED pattern, modify)
stmt = select(SocialPost).where(
    SocialPost.provider == provider,
    SocialPost.publish_enabled.is_(True),  # D-05
)
```

### Instagram publisher flow shape (2-step, safe)
```python
# Source: Meta IG Content Publishing flow (CITED: .planning/research/STACK.md, .planning/research/PITFALLS.md; verify before implementation)
# 1) POST /{ig-user-id}/media {image_url, caption, access_token} -> {id: container_id}
# 2) GET /{container_id}?fields=status_code -> FINISHED|IN_PROGRESS|ERROR|EXPIRED|PUBLISHED
# 3) POST /{ig-user-id}/media_publish {creation_id=container_id, access_token} -> {id: media_id}
# 4) GET /{media_id}?fields=id,permalink -> best-effort
```

### Safe reconciliation decision
```python
# Source: D-13/D-15/D-20 (VERIFIED context)
if status == "FINISHED":
    return "publish_same_container"
if status == "IN_PROGRESS":
    return "poll_limited"
if status in {"ERROR", "EXPIRED"}:
    return "conclusive_failure_new_container_only_if_no_publish_ambiguity"
if status in {"PUBLISHED"}:
    return "mark_published_from_existing"
return "ambiguous_blocked"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Facebook-only publish pipeline | Provider-aware FB+IG independent pipeline | Phase 31 | Enables PUBL-01 without regressions. |
| Single publish call result | 2-step IG container lifecycle + reconciliation | Phase 31 | Required for IG correctness and duplicate safety. |
| `retry_block_reason` only for generic FB ambiguous case | Reconciliation-aware retry semantics for IG ambiguity | Phase 31 | PUBL-03/PUBL-04 actionable admin behavior. |

**Deprecated/outdated:**
- Hardcoded Facebook-only worker/status/retry assumptions in admin CRUD/UI. Replace with provider-aware behavior while preserving FB compatibility. [VERIFIED: codebase]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Treat IG rate-limit/daily-limit (2207042/content publishing limit) as blocked actionable state with no automatic retry storm; do not auto-schedule near-term retries unless clear safe window is known. | PUBL-05 / pitfalls | If Meta expects fast retry after specific window, posts may remain blocked longer; safer than duplication/storm. |
| A2 | `external_post_id` remains the final published IG media ID; container ID stored in a dedicated column (e.g., `ig_container_id`). | Data model | If later code assumes container ID in `external_post_id`, reconciliation/published links may break. Make explicit in schema/docs. |
| A3 | Existing `GET /admin/social-posts` and frontend SocialPostsClient are the minimum PUBL-03 admin audit/status surface to extend; no new page required. | PUBL-03 UI | If product expects a richer audit screen, Phase 31 may need follow-up UI polish, but requirement can be met by extending existing surfaces. |
| A4 | Phase 31 should add IG registration/dispatch on approve for enabled IG drafts, because PUBL-01 says approve/publication processes IG independently and D-06 requires dispatch per eligible post/provider. Current approve path only handles Facebook. | Integration points | If IG dispatch is intended elsewhere, duplicate scheduling/dispatch could occur; plan must define single source of truth. |

## Open Questions

1. **How should PUBL-05 "blocked by limit" be represented?**
   - What we know: D-12 uses `failed` + reconciliation for ambiguity; PUBL-05 needs actionable admin state and no retry storm. `SocialPostStatus` has no `blocked` enum. [VERIFIED]
   - What's unclear: whether to add enum value, or represent as `failed` with specific error code/retry_block_reason and `next_retry_at=null`.
   - Recommendation: prefer `failed` + explicit safe error/reason code metadata (or dedicated columns) to avoid enum migration ripple; expose clear "bloqueado por limite/rate limit" state in UI.

2. **Should IG publish be dispatched on approve or only by worker?**
   - What we know: D-06 says dispatch immediate independent per eligible post/provider; approve currently dispatches FB due posts. [VERIFIED]
   - What's unclear: Phase 30 did not add IG approve dispatch.
   - Recommendation: extend approve to register/schedule/dispatch IG draft independently when enabled and due, mirroring FB but isolated.

3. **Where should audit "history" live for PUBL-03?**
   - What we know: `social_post_logs` exists per attempt; UI currently shows current status only. [VERIFIED]
   - What's unclear: required depth of "histórico/auditoria" in admin UI.
   - Recommendation: add admin endpoint to fetch logs for a `social_post`/job+provider and show compact attempt history in SocialPostsClient or detail drawer; keep payload safe.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python/uv/pytest | Backend tests | ✓ | Python 3.14.3 observed during earlier phase tests [VERIFIED: 30-01 summary] | — |
| Node/npm | Frontend lint/build | ✓ | Present in repo workflows [ASSUMED] | — |
| Postgres test DB / Alembic | Migration and DB-backed tests | ⚠️ | Prior phase noted test DB migration/version column issue [VERIFIED: 29-02 summary] | Run migrations against test DB; widen alembic_version column if same env issue recurs |
| Meta Graph API / IG account | Live end-to-end publish verification | ✗/external | N/A | Mocked tests; manual Meta checklist remains operational handoff |

**Missing dependencies with no fallback:**
- None for planning/code implementation.

**Missing dependencies with fallback:**
- Live Meta IG publish environment — use mocked unit/integration tests; document manual verification. [VERIFIED: STATE/PROJECT constraints]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend) + existing frontend lint/manual checks |
| Config file | `backend/pyproject.toml` / pytest defaults; frontend eslint config |
| Quick run command | `cd backend && pytest -q tests/test_social_publish_pipeline.py tests/test_admin_social_publish.py tests/test_admin_instagram_social_posts.py` |
| Full suite command | `cd backend && pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PUBL-01 | FB+IG dispatch/process independent; one provider failure does not block/corrupt other | integration/unit | `pytest -q tests/test_admin_social_publish.py tests/test_social_publish_pipeline.py -k "instagram or provider or independent"` | ❌ Wave 0 |
| PUBL-02 | IG 2-step container/status/publish with safe timeout and configurable Graph version | unit | `pytest -q tests/test_instagram_publisher.py` | ❌ Wave 0 |
| PUBL-03 | Status/audit fields persisted and exposed safely; no secrets/tokens; permalink/IDs/timestamps present when available | integration/unit | `pytest -q tests/test_admin_social_publish.py tests/test_social_publish_pipeline.py -k "audit or status or permalink"` | ❌ Wave 0 |
| PUBL-04 | Ambiguous timeout does not auto-retry; retry reconciles known container before publish; no duplicate | unit/integration | `pytest -q tests/test_social_publish_pipeline.py -k "ambiguous or reconcile or idempotent"` | ✅ partial / extend |
| PUBL-05 | 2207042/content_publishing_limit/rate limit classified safely; no retry storm; actionable admin state | unit | `pytest -q tests/test_instagram_publisher.py tests/test_social_publish_pipeline.py -k "rate or 2207042 or limit"` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** Run targeted backend social tests for touched files.
- **Per wave merge:** `cd backend && pytest -q tests/test_social_publish_pipeline.py tests/test_social_publisher.py tests/test_admin_social_publish.py tests/test_admin_instagram_social_posts.py`
- **Phase gate:** Backend social suite green + FB characterization unchanged + frontend lint/manual checks for status/retry surfaces before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `backend/tests/test_instagram_publisher.py` — covers PUBL-02, PUBL-05, timeout/error mapping, permalink best-effort.
- [ ] Extend `backend/tests/test_social_publish_pipeline.py` — covers provider dispatch, D-05 publish_enabled claim, IG ambiguity/reconciliation (PUBL-01/04).
- [ ] Extend `backend/tests/test_admin_social_publish.py` — covers worker breakdown, provider-aware retry/status/list, approve IG dispatch (PUBL-01/03).
- [ ] Frontend tests absent in area; use lint + manual verification checklist for SocialPostsClient/EditJobDialog/ReviewQueue.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Admin endpoints keep `require_admin`; worker keeps `require_cron_secret`. [VERIFIED: admin.py] |
| V3 Session Management | yes | Frontend uses existing Bearer token + 401 redirect pattern. [VERIFIED: frontend api/admin clients] |
| V4 Access Control | yes | No public publish endpoints; IG media/public endpoints remain unauthenticated only as already designed and exact-hash constrained. [VERIFIED: image_media/public.py] |
| V5 Input Validation | yes | Validate provider/job IDs, caption/media readiness, safe status transitions; reject unsupported provider. [VERIFIED: existing patterns] |
| V6 Cryptography | yes | Reuse Fernet-encrypted page tokens; never persist/log plain tokens. [VERIFIED: meta_oauth/crypto/config] |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Token/secret leakage in logs or audit payloads | Information Disclosure | Sanitize all Graph errors/log summaries; never include access_token/raw response. [VERIFIED: existing social code] |
| Duplicate publish via ambiguous retry | Tampering / Integrity | Idempotency by `external_post_id`, reconciliation-before-republish, no auto-retry on ambiguity. [VERIFIED: D-09/D-13/D-20] |
| Unauthorized worker invocation | Elevation of Privilege | `require_cron_secret` fail-closed. [VERIFIED: deps/admin.py] |
| Unsafe public image URL / SSRF-ish fetch behavior | Tampering / Info Disclosure | Reuse explicit `MEDIA_PUBLIC_BASE_URL` validation and exact-hash public serving; do not accept arbitrary client URLs. [VERIFIED: image_media.py] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/31-independent-publish-pipeline/31-CONTEXT.md` — locked decisions D-01..D-20 and discretion boundaries.
- Codebase (VERIFIED): `backend/app/services/social/publish_pipeline.py`, `facebook.py`, `publisher.py`, `types.py`, `image_media.py`, `meta_oauth.py`, `instagram_readiness.py`, `crud/social_posts.py`, `models/social_post.py`, `models/social_post_log.py`, `models/social_account.py`, `schemas/social_posts.py`, `api/v1/admin.py`, `api/v1/integrations.py`, `core/config.py`, `frontend/lib/api.ts`, `frontend/app/admin/review/EditJobDialog.tsx`, `frontend/app/admin/review/ReviewQueue.tsx`, `frontend/app/admin/social-posts/SocialPostsClient.tsx`.
- Phase 29/30 artifacts (VERIFIED): `29-CONTEXT.md`, `29-01-SUMMARY.md`, `29-02-SUMMARY.md`, `30-CONTEXT.md`, `30-RESEARCH.md`, `30-01..03-SUMMARY.md`, `30-VERIFICATION.md`.

### Secondary (MEDIUM confidence)
- `.planning/research/SUMMARY.md` — v1.5 synthesis; flags IG as stateful 2-step flow and rate-limit/idempotency risks.
- `.planning/research/STACK.md` — Meta Graph IG publishing flow, endpoints, permissions, rate-limit notes (researched 2026-11-23).
- `.planning/research/ARCHITECTURE.md` — provider-aware architecture, public media constraints, idempotency boundaries.
- `.planning/research/PITFALLS.md` — duplicate/ambiguous publish, rate limits, token/linkage, image URL pitfalls (cites Meta docs fetched 2026-11-23).

### Tertiary (LOW confidence)
- None. External Meta behavior should be rechecked against current official Meta docs during implementation if any 4xx/limit semantics differ. [ASSUMED: research docs remain accurate]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - existing repo stack; no new deps.
- Architecture: HIGH - directly grounded in codebase and locked decisions.
- Pitfalls: MEDIUM-HIGH - strong local research + code patterns; live Meta behavior/rate-limit edge details should be confirmed during implementation.

**Research date:** 2026-11-25
**Valid until:** 2026-12-09 (IG Graph behavior/rate-limit details can drift; confirm before live rollout)

## RESEARCH COMPLETE

**Phase:** 31 - independent-publish-pipeline
**Confidence:** MEDIUM-HIGH

### Key Findings
- The codebase already has the key primitives (provider-unique `social_posts`, claim/lock/idempotency, ambiguous-no-auto-retry, safe logging, IG draft/media/readiness contracts); Phase 31 should generalize, not replace, this foundation.
- Instagram publishing must be modeled as a stateful reconciliation workflow (container create → limited status poll → publish → best-effort permalink), with ambiguity persisted as blocked `failed` state and never auto-retried.
- Current admin/worker/retry/status paths are Facebook-hardcoded; PUBL-01/PUBL-03 require provider-aware dispatch, status/audit exposure, and IG retry reconciliation semantics while preserving FB behavior.
- `list_due_for_claim` currently ignores `publish_enabled`; D-05 requires filtering it, and approve currently dispatches only Facebook so IG approve dispatch is a likely missing integration point.
- PUBL-05 should be implemented conservatively: classify 2207042/content publishing limit as actionable blocked state with no retry storm, surfacing clear admin guidance.

### File Created
`.planning/phases/31-independent-publish-pipeline/31-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | No new libraries; all patterns verified in codebase. |
| Architecture | HIGH | Locked decisions + existing social pipeline/readiness/media contracts make integration points clear. |
| Pitfalls | MEDIUM-HIGH | Ambiguity/rate-limit/media risks well documented in project research and code, but live Meta edge behavior should be confirmed before rollout. |

### Open Questions
- Represent PUBL-05 rate-limit block as `failed` with actionable metadata vs adding a new status enum.
- Confirm exact minimum "audit/history" UI shape needed for PUBL-03 (existing SocialPostsClient extension vs detail drawer).
- Confirm approve-flow ownership for IG dispatch to avoid double-dispatch while satisfying D-06/PUBL-01.

### Ready for Planning
Research complete. Planner can now create PLAN.md files.
