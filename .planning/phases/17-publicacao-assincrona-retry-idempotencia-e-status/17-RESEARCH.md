# Phase 17: Publicação Assíncrona, Retry, Idempotência e Status - Research

**Researched:** 2026-11-16
**Domain:** Async social publishing pipeline (FastAPI + SQLAlchemy async/Postgres) + Graph API feed publish + idempotent retry worker + admin status/retry UI
**Confidence:** HIGH

## Summary

Phase 17 turns the Phase 16 "site-first, register social as scheduled" flow into a real, resilient publication pipeline for Facebook. The codebase already provides the core persistence and contracts: `social_posts` tracks lifecycle/attempts/scheduling/errors/external IDs, `social_accounts` stores encrypted Page tokens and connection status, `SocialPublisher`/`PublishResult`/`FacebookPublisher` define the publishing seam (currently a stub), admin approval already commits the job first and best-effort marks an approved draft as `scheduled` (`backend/app/api/v1/admin.py`), and operational patterns exist for cron-protected endpoints (`require_cron_secret`, `POST /admin/expire`) and in-process async scheduling (`AsyncIOScheduler` in `backend/app/core/scheduler.py`). Phase 17 must implement the missing execution engine: atomic claim, real Graph publish, retry/backoff/error classification, idempotent no-op/manual retry, cron worker endpoint, immediate non-blocking post-approval dispatch, and admin visibility/actions.

The primary planning risk is **duplication under ambiguity**. Requirements/decisions require `FOR UPDATE SKIP LOCKED` claims, idempotent behavior on `external_post_id`/`published`, and "do not auto-republish on ambiguous outcome" (PUB-07, D-09..D-12). The implementation must therefore separate "claim/transition", "remote call", and "persist outcome" carefully: claim only eligible rows, never republish rows that already have an external ID, and treat timeout-after-send as a non-automatic-retry ambiguity until manually/explicitly reconciled per safe rules. A second risk is coupling social execution to the site publish path; D-01/D-03/D-09 require immediate attempt + cron fallback through the **same pipeline** after commit and non-blocking, so dispatch must not affect the already-returned approval success.

**Primary recommendation:** Build one shared `process_due_social_posts`/`process_social_post` pipeline used by (1) a `POST /admin/social/worker` cron endpoint protected by `CRON_SECRET` and (2) an immediate post-commit `BackgroundTasks` dispatch from approve. Use Postgres row claims (`SELECT ... FOR UPDATE SKIP LOCKED`) to move eligible `scheduled`/retryable-`failed` rows into `publishing`, implement `FacebookPublisher.publish` with `httpx` + decrypted Page token + `message/link` to `POST /{META_GRAPH_VERSION}/{page_id}/feed`, persist `published/failed` outcomes and `social_post_logs`, compute `next_retry_at` from `SOCIAL_MAX_ATTEMPTS`/`SOCIAL_RETRY_DELAYS`, and expose safe admin read/retry APIs consumed by review/edit and a simple admin social-posts view.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Disparo e processamento
- **D-01:** Para aprovação com post "Publicar agora" (`scheduled_at = agora`), a 1ª tentativa deve ser **imediata e não bloqueante** após o commit da aprovação, **com fallback no cron/worker** (1-5 min) para garantir processamento/retries/agendados mesmo se a tentativa imediata falhar.
- **D-02:** O worker acionado por cron externo (Render) deve ser **protegido reutilizando `CRON_SECRET`** no mesmo padrão operacional de `/admin/expire` (`X-Cron-Secret`/`require_cron_secret`), mantendo um único segredo de cron.
- **D-03:** A tentativa imediata pós-aprovação deve usar o **mesmo pipeline único** de claim/publicação do worker de cron (após commit, não bloqueante), compartilhando lógica de lock/claim, transições de status, logging e idempotência.
- **D-04:** Elegibilidade base do worker: processar **posts `scheduled` com `scheduled_at <= agora`** e **posts `failed` elegíveis a retry automático com `next_retry_at <= agora`** (respeitando limite/config). Não incluir por padrão recuperação automática de registros presos em `publishing`; se necessário, tratar como refinamento técnico seguro sem ampliar escopo.

#### Retry e falhas
- **D-05:** Classificar falhas em **transitórias vs permanentes**: transitórias (rede, 5xx, timeout/rate limit temporário) seguem retry automático com backoff configurável até o limite; permanentes (token/permissão inválidos, erro de requisição/conteúdo confirmado, etc.) não entram em retry automático.
- **D-06:** Se a integração Facebook estiver desconectada/`needs_reconnect` ou sem token/página válido, tratar como **falha bloqueante até reconectar** (não-retryable automaticamente) com erro resumido orientando reconexão; retry automático não deve ficar em loop sem conexão válida.
- **D-07:** Ao esgotar `SOCIAL_MAX_ATTEMPTS`, o post fica em **`failed` final sem `next_retry_at` automático**; novas tentativas só via ação manual elegível ("Tentar novamente"), respeitando as mesmas regras do pipeline.
- **D-08:** O erro exibido ao admin deve ser **mensagem amigável e resumida em pt-BR**, segura (sem segredos/tokens/payloads brutos), mapeada por categoria/situação (ex.: falha temporária, reconexão necessária, limite temporário, falha definitiva).

#### Idempotência e duplicatas
- **D-09:** Usar **claim atômico no banco** para concorrência: selecionar elegíveis com `FOR UPDATE SKIP LOCKED` e transicionar para `publishing` na transação de claim antes de chamar a Graph API, evitando processamento paralelo do mesmo post.
- **D-10:** Se o registro já possuir `external_post_id` (ou já estiver `published`), tentativas futuras (cron, imediata, manual, reexecução) devem ser **no-op idempotente**: não reenviar à Graph API e reconciliar estado/timestamps de forma segura.
- **D-11:** Em caso **ambíguo** (possível sucesso remoto sem confirmação local, ex.: timeout antes de persistir `external_post_id`), **priorizar evitar duplicata**: não republicar automaticamente; registrar estado/erro seguro e exigir verificação/retry manual consciente conforme elegibilidade.
- **D-12:** O botão "Tentar novamente" deve passar pelo **mesmo fluxo idempotente** de claim/processamento do worker, respeitando elegibilidade e ignorando cliques repetidos/itens já em processamento ou publicados.

#### Status e ações no admin (UI-01, UI-02)
- **D-13:** Status social por vaga deve ser visível no **fluxo admin de revisão/edição** e, para acompanhamento pós-aprovação, em uma **nova visão/lista simples no admin de posts/vagas sociais** (agendados, publicados, falhos etc.), permitindo consultar status/erro/link e acionar retry quando elegível.
- **D-14:** Exibir **badges/rótulos pt-BR para todos os estados relevantes**: sem rascunho, rascunho, agendado, publicando, publicado (com link do post quando disponível), falhou (com erro resumido) e cancelado, quando aplicável.
- **D-15:** "Tentar novamente" deve ficar disponível apenas para **falhas elegíveis com integração conectada e post não publicado**; desabilitar/ocultar (com orientação quando pertinente) para publicado, em processamento, agendado futuro normal, sem conexão/reconexão necessária ou casos não elegíveis pelas regras do pipeline.

### OpenCode's Discretion
- Nomes/paths exatos de endpoints (ex.: endpoint de worker cron, endpoint de retry manual, endpoint/listagem de status social) e formato de payloads/respostas, desde que protegidos, consistentes e sem expor segredos.
- Estratégia concreta de agendamento da tentativa imediata não bloqueante (BackgroundTasks, task no loop, etc.) e granularidade de batches/limites por ciclo do worker, mantendo claim atômico e baixo impacto.
- Mapeamento detalhado de códigos/erros da Graph API para categorias transitória/permanente/ambígua e textos pt-BR finais, preservando segurança e utilidade.
- Uso de `social_post_logs` (granularidade de tentativas/eventos), estrutura de mensagens de `last_error` e campos auxiliares de auditoria/observabilidade dentro do schema existente.
- Implementação da URL/link do post publicado na UI (derivação a partir de `external_post_id`/page ou campo armazenado), desde que confiável e segura.
- Composição visual exata (componentes, posicionamento de badges/lista, estados de loading/empty/erro) alinhada aos padrões do admin.

### Deferred Ideas (OUT OF SCOPE)
- Instagram, múltiplas páginas/admins, métricas/insights de engajamento e sincronização de edição/remoção de posts — fora do milestone v1.2.
- Recuperação automática avançada de itens presos em `publishing` (timeout/orfãos) não foi selecionada como requisito desta discussão; avaliar apenas se necessário para robustez sem ampliar escopo.
- Testes automatizados/manuais abrangentes, documentação operacional (setup Meta/envs/cron/App Review) e fechamento de gaps/evidências do audit v1.1 — Phase 18.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PUB-01 | `FacebookPublisher.publish(post)` cria post via `POST /{page_id}/feed` com `message` e `link` (URL pública da vaga) | Implement real publisher in `backend/app/services/social/facebook.py` using `httpx` + Meta Graph base/version from settings; payload `message`+`link`; return `PublishResult(external_post_id=...)` on success. |
| PUB-02 | Aprovação publica a vaga no site mesmo se o Facebook estiver fora/indisponível (falha social nunca derruba/bloqueia fluxo do site) | Keep existing site-first commit in `approve` (`backend/app/api/v1/admin.py`); immediate publish dispatch must be after commit, non-blocking, and failure-isolated (BackgroundTasks/catch/log), cron remains fallback. |
| PUB-03 | Publicação imediata é tentada de forma assíncrona após aprovação (sem bloquear resposta); cron cobre falhas | Trigger shared pipeline for the approved/scheduled post in background after approval commit; also provide protected cron endpoint that runs same claim/process logic for due items. |
| PUB-04 | Worker por polling acionado por Cron Job (Render, 1–5 min) processa elegíveis (`scheduled`/failed retryable, `scheduled_at`/`next_retry_at <= now`) usando `SELECT ... FOR UPDATE SKIP LOCKED` | New cron-protected endpoint (`require_cron_secret`) + service/CRUD claim query with `with_for_update(skip_locked=True)` and status/time predicates; process batch in loop with per-item session/commit safety. |
| PUB-05 | Retry automático com backoff exponencial configurável por env (`SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS`); padrão 5 tentativas (5min/15min/1h/3h/6h) | Use `settings.SOCIAL_MAX_ATTEMPTS` and `settings.social_retry_delays_list` (already validated/parsed in `config.py`); compute `next_retry_at = now + delays[min(attempt-1, len-1)]` while attempts < max. |
| PUB-06 | Erros transitórios (rede, 5xx, rate limit) → retry com backoff; erros permanentes (token inválido, permissão revogada, conteúdo rejeitado) → falha sem retry com sinalização clara | Central error classifier mapping httpx/network/Graph errors to transient/permanent/ambiguous; permanent and reconnect-needed cases set `failed` without auto `next_retry_at` (or blocked semantics) and safe pt-BR `last_error`. |
| PUB-07 | Idempotência: nunca criar post duplicado (checar status/`external_post_id` antes de enviar, lock de linha/unique constraint; resistente a cron concorrente e clique duplo) | Atomic claim transition, re-check `published/external_post_id` as idempotent no-op, unique `(job_id,provider)` remains, manual retry and immediate path call same pipeline; ambiguous outcomes avoid auto-resend. |
| PUB-08 | Post é fire-and-forget — editar, fechar ou expirar a vaga não atualiza nem remove o post no Facebook | No publish-path coupling to later job edits/delete/expiry; only read needed job/account data for send/logging, never issue update/delete Graph calls. |
| UI-01 | Listagem/detalhe da vaga no admin exibe badge de status social (agendado, publicado, falhou etc.), mensagem de erro resumida, link para post publicado (quando disponível) | Extend admin job/list payloads or add per-job social status fetch; render badges/erro/link in `ReviewRow`/`EditJobDialog` and read-only states for published/processing. |
| UI-02 | Botão manual "tentar novamente" no painel para posts elegíveis; ação respeita idempotência e regras de retry | New protected retry endpoint that enqueues/processes through same pipeline; UI enables button only for eligible failed+connected+not-published cases and handles in-flight/duplicate clicks safely. |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Fixed stack/locale/deploy constraints: Next.js 16 App Router + Tailwind, FastAPI async Python, Neon Postgres, pt-BR, Vercel + Railway/Render. [VERIFIED: AGENTS.md]
- **Core value:** frictionless public job discovery; **integração social não pode bloquear publicação no site** (site-first must remain). [VERIFIED: AGENTS.md, PROJECT.md, 16-CONTEXT/approve implementation]
- Admin único/master, JWT-protected admin flows; operational cron auth via secret header pattern already used. [VERIFIED: `backend/app/deps.py`, `backend/app/api/v1/admin.py`]
- Segredos/tokens/credenciais **somente no backend**, criptografados em repouso; never in logs, API responses, or frontend. [VERIFIED: AGENTS.md, social crypto/account model/config validators]
- Existing Groq/config and prior phase behaviors must not regress; Phase 17 scope is publishing/retry/status/idempotency, not post generation rewrite. [VERIFIED: STATE/ROADMAP/CONTEXT]
- GSD workflow/context: follow established repository patterns (SQLAlchemy 2 async, Pydantic schemas, FastAPI routers/deps, Next admin client patterns) and locked D-01..D-17. [VERIFIED: codebase]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Eligibility/claim/lock, status transitions, attempt accounting, retry scheduling | Database / Storage + Backend services/CRUD | API | Concurrency and idempotency require transactional row locks and authoritative state in Postgres (`FOR UPDATE SKIP LOCKED`, unique constraints). [VERIFIED: schema/indexes + D-09] |
| Real Facebook publish call and result classification | Backend API/service (`FacebookPublisher`, worker/pipeline) | External Meta Graph API | Tokens/page IDs are backend-only; network/Graph responses determine transient/permanent/ambiguous outcomes. [VERIFIED: crypto/account models + D-05/D-06/D-11] |
| Triggering: cron polling and immediate post-approval attempt | Backend operational endpoint + background dispatch | Scheduler/Render cron (external trigger) | D-01/D-02/D-03 require cron-protected polling and non-blocking immediate attempt using same pipeline after commit. [VERIFIED: `require_cron_secret`, approve flow] |
| Error/logging/audit persistence (`last_error`, attempts, `next_retry_at`, `social_post_logs`) | Database + Backend | — | Safe diagnosis and retry decisions must be persisted server-side without leaking secrets. [VERIFIED: models + D-08] |
| Admin status visibility and retry action (review/edit + social posts view) | Frontend admin UI | Backend admin APIs | UI must display pt-BR states/link/errors and gate retry eligibility; backend enforces rules/idempotency. [VERIFIED: D-13..D-15, existing admin pages/api client] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | project stack | Cron/worker/retry/status admin endpoints, BackgroundTasks dispatch | Existing API/dependency patterns (`require_admin`, `require_cron_secret`) [VERIFIED: codebase] |
| SQLAlchemy 2 (async) + asyncpg/Postgres | project stack | Claim/query/update `social_posts` with row locks and transactional state | Existing ORM/session style; `FOR UPDATE SKIP LOCKED` required by PUB-04/D-09 [VERIFIED: models/CRUD/scheduler patterns] |
| Pydantic v2 | project stack | Safe request/response schemas for status list and retry/worker responses | Existing schema conventions [VERIFIED: codebase] |
| `httpx` (async) | project stack | Graph API `POST /{page_id}/feed` calls with timeout/error handling | Already used for outbound Meta calls in OAuth service; async-friendly [VERIFIED: `meta_oauth.py`] |
| Existing `SocialPublisher`/`PublishResult` types | in-repo | Provider contract and result categories | Phase 14 foundation; implement Facebook without coupling flow [VERIFIED: `services/social/*`] |
| Next.js 16 / React / TS admin UI | project stack | Badges, social posts view, retry controls, status refresh | Existing admin review/integrations patterns [VERIFIED: frontend admin files] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `datetime`/`timezone` (stdlib) | stdlib | `now`, due comparisons, `next_retry_at`, `published_at` | All eligibility/retry/success timestamping (store tz-aware UTC consistently) [VERIFIED: existing code uses aware datetimes] |
| `zoneinfo` | stdlib | Only if UI/admin displays/inputs local times beyond existing handling | Existing draft flow already handles BRT conversion for scheduling; Phase 17 mainly processes stored times [VERIFIED: `post_generation.py` usage pattern from phase 16] |
| FastAPI `BackgroundTasks` | FastAPI built-in | Immediate non-blocking attempt after approval commit (D-01/D-03) | Preferred simple dispatch for "after response" work in same process; cron remains safety net [ASSUMED: appropriate for low-volume single-admin workload] |
| Existing `AsyncIOScheduler` (reference) | project dep | In-process scheduling patterns/lifecycle awareness | Reference only; do **not** rely on it for Render sleep scenarios—cron endpoint is authoritative per D-02/D-04 [VERIFIED: `core/scheduler.py` notes] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Shared pipeline invoked by cron endpoint + BackgroundTasks | APScheduler-only in-process polling | Fails when host sleeps/spins down (Render free tier concern noted in scheduler docs); D-02 explicitly requires cron-protected external trigger. [VERIFIED: scheduler.py, D-02] |
| `FOR UPDATE SKIP LOCKED` claim in DB | In-memory locks/flags | Not safe across processes/restarts/cron reentry; DB is source of truth for concurrency. [VERIFIED: requirements D-09] |
| `httpx` for Graph publish | `requests` or custom raw HTTP | Codebase already async; `httpx` matches existing Meta service style. [VERIFIED: `meta_oauth.py`] |
| Single pipeline for immediate/manual/cron | Separate code paths | High duplication/drift risk and easier to violate idempotency/retry parity (D-03/D-12). |

**Installation:** No new dependencies expected; prefer existing `httpx`, SQLAlchemy, FastAPI, stdlib. [ASSUMED]

**Version verification:** `npm view`/`pip show` registry checks were not executed in this research session. Use pinned project stack and verify only if adding packages. [ASSUMED]

## Architecture Patterns

### System Architecture Diagram

```text
Admin approval (site-first, already committed)
  └─ if social draft registered/scheduled (Phase 16 result)
       └─ enqueue BackgroundTasks: run_social_publish_cycle(scope=post/job)  [D-01, D-03, non-blocking]

Render Cron (1–5 min)
  └─ POST /api/v1/admin/social/worker  (X-Cron-Secret / require_cron_secret) [D-02]
       └─ run_social_publish_cycle(scope=due batch)

Admin UI (review/edit + posts sociais view)
  ├─ GET social status/list (per job / admin list)  -> badges, pt-BR labels, last_error, published link [D-13,D-14]
  └─ POST retry (eligible failed post)             -> same pipeline claim/process [D-12,D-15]

run_social_publish_cycle (shared) [D-03,D-09..D-12]
  ├─ begin tx: claim eligible rows (scheduled due OR failed retryable due, next_retry_at due)
  │    SELECT ... FOR UPDATE SKIP LOCKED LIMIT N
  │    ├─ if published/external_post_id exists => idempotent reconcile/no-op
  │    ├─ else set status='publishing' (+ attempt/log prep) and COMMIT claim
  ├─ for each claimed post (separate tx/steps as needed):
  │    ├─ load active connected Facebook account + decrypt token (safe)
  │    │    └─ if missing/disconnected/needs_reconnect/decrypt fail => permanent blocked failure "reconectar integração" [D-06,D-08]
  │    ├─ FacebookPublisher.publish(message, link, page_id, token, META_GRAPH_VERSION)
  │    │    └─ POST https://graph.facebook.com/{v}/{page_id}/feed
  │    ├─ classify outcome:
  │    │    ├─ success + id => published, external_post_id, published_at, clear retry/error
  │    │    ├─ transient (network/5xx/429/temp) => failed or retry state with attempts+1, next_retry_at if attempts < max else final failed [D-05,D-07]
  │    │    ├─ permanent (auth/permissions/invalid request/content) => failed final, no auto next_retry_at [D-05,D-06]
  │    │    └─ ambiguous (timeout/unknown after send) => do NOT auto-republish; record safe error/state for manual verification [D-11]
  │    └─ persist SocialPost fields + SocialPostLog attempt row
  └─ return summary counts (processed/claimed/published/retried/failed/skipped)
```

### Recommended Project Structure
```
backend/app/
├── api/v1/admin.py                 # extend: social worker endpoint, retry endpoint, status/list endpoint(s); approve dispatch hook
├── deps.py                         # reuse require_cron_secret / require_admin (no new secret types)
├── core/config.py                  # reuse SOCIAL_MAX_ATTEMPTS/RETRY_DELAYS; optional batch/timeout knobs only if needed
├── crud/social_posts.py            # extend: claim_due, mark_publishing/published/failed_retry/final_failed, idempotent lookup helpers
├── crud/social_accounts.py         # NEW or extend: get active connected facebook account (safe lookup)
├── models/social_post.py           # existing fields/states/indexes (likely no schema change)
├── models/social_post_log.py       # persist attempt outcomes (recommended)
├── schemas/social_posts.py         # extend: status/list item, retry/worker responses
└── services/social/
    ├── publisher.py/types.py       # existing contract (extend payload/result if needed: page/token context handled in pipeline)
    ├── facebook.py                 # implement real POST /{page_id}/feed
    ├── publish_pipeline.py         # NEW: shared claim/process/retry/idempotency/error-mapping logic
    └── crypto.py/meta_oauth.py     # reuse decrypt and account/status semantics

frontend/
├── lib/api.ts                      # extend types/functions for social status list + retry; extend JobAdmin if embedding status
├── app/admin/review/ReviewQueue.tsx, EditJobDialog.tsx, components/admin/ReviewRow.tsx
│                                   # show social badge/error/link/retry in review flow (D-13,D-14,D-15)
├── app/admin/social-posts/page.tsx # NEW simple operational view (recommended path/name discretionary)
└── app/admin/integracoes/*         # keep reconnect guidance consistent (D-06)
```
[VERIFIED: existing structure + discretionary endpoint/path choices]

### Pattern 1: Atomic claim with `FOR UPDATE SKIP LOCKED` (single pipeline entry)
**What:** Select eligible IDs/rows in a transaction, lock them with `skip_locked`, transition to `publishing` (and capture claim metadata) before any external call. Re-fetch/process by claimed IDs.
**When to use:** Cron batch, immediate post-approval attempt, and manual retry (all must converge to same safe claim/process behavior).
**Example:**
```python
# Source: SQLAlchemy 2 async + Postgres locking semantics [VERIFIED pattern; implementation details to confirm in code]
from datetime import datetime, timezone
from sqlalchemy import and_, or_, select

now = datetime.now(timezone.utc)
stmt = (
    select(SocialPost)
    .where(
        SocialPost.provider == "facebook",
        or_(
            and_(SocialPost.status == SocialPostStatus.scheduled, SocialPost.scheduled_at <= now),
            and_(
                SocialPost.status == SocialPostStatus.failed,
                SocialPost.next_retry_at.is_not(None),
                SocialPost.next_retry_at <= now,
            ),
        ),
    )
    .order_by(SocialPost.scheduled_at.nulls_last(), SocialPost.updated_at)
    .limit(batch_size)
    .with_for_update(skip_locked=True)
)
rows = (await session.scalars(stmt)).all()
# filter defensive: skip if external_post_id/published (idempotent reconcile), else mark publishing
```
[ASSUMED: exact SQLAlchemy `select(...).with_for_update(skip_locked=True)` usage against async session; verify during implementation.]

### Pattern 2: Site-first approval + non-blocking immediate dispatch + cron fallback
**What:** Keep `approve_job` commit and response contract intact. After commit/refresh and best-effort social registration result, schedule background processing for the target post (or due cycle) without awaiting network publish in request path.
**When to use:** Approvals where post becomes eligible now/scheduled (D-01/D-03/PUB-02/PUB-03).
**Example:**
```python
# Source: FastAPI BackgroundTasks pattern + existing approve flow [VERIFIED: approve flow; dispatch shape ASSUMED]
from fastapi import BackgroundTasks

@router.patch("/jobs/{job_id}/approve", response_model=JobApproveResponse)
async def approve(..., background_tasks: BackgroundTasks):
    # ... approve site + commit + refresh ...
    # ... best-effort register draft -> scheduled + commit ...
    background_tasks.add_task(process_social_post_safe, post_id=str(social_post.id))
    return JobApproveResponse(job=..., social=social_outcome)
```
[ASSUMED: adding `BackgroundTasks` parameter to existing endpoint is acceptable; alternative is `asyncio.create_task` with careful session/lifecycle handling.]

### Pattern 3: Real Graph publish and safe result persistence
**What:** Resolve connected account/page/token, call Graph feed endpoint, parse external ID, and persist success/failure in dedicated transactions with sanitized errors and attempt logs.
**When to use:** Processing a claimed `publishing` post.
**Example:**
```python
# Source: Meta Graph Pages publish contract (feed message/link) [CITED: Meta Graph API Pages Publishing docs] + existing httpx/crypto patterns [VERIFIED: codebase]
import httpx

async def publish_to_facebook(*, settings, page_id: str, page_token: str, message: str, link: str | None):
    url = f"https://graph.facebook.com/{settings.META_GRAPH_VERSION}/{page_id}/feed"
    payload = {"message": message, "access_token": page_token}
    if link:
        payload["link"] = link
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, data=payload)
    data = resp.json() if resp.content else {}
    if resp.status_code >= 400:
        raise GraphPublishError(status_code=resp.status_code, payload=data)
    return data.get("id")  # external_post_id
```
[ASSUMED: response field is `id`; exact timeout/request shape and error body parsing to verify against Meta docs/implementation tests.]

### Pattern 4: Retry/backoff and eligibility rules
**What:** On failure, classify outcome, increment attempts, and either schedule retry (`next_retry_at`) or mark final blocked/failed state with pt-BR summary.
**When to use:** Every non-success publish outcome.
**Example:**
```python
# Source: project settings/config + D-05..D-07 [VERIFIED: config.py]
delays = settings.social_retry_delays_list  # e.g. [300,900,3600,10800,21600]
max_attempts = settings.SOCIAL_MAX_ATTEMPTS  # default 5

post.attempts = (post.attempts or 0) + 1
post.last_error = safe_ptbr_message
if retryable and post.attempts < max_attempts:
    idx = min(post.attempts - 1, len(delays) - 1)
    post.next_retry_at = now + timedelta(seconds=delays[idx])
    post.status = SocialPostStatus.failed  # retryable failed (eligible later) OR keep failed semantics per schema
else:
    post.next_retry_at = None
    post.status = SocialPostStatus.failed  # final/manual-only
```
[ASSUMED: retryable-failed is represented by `status=failed` + `next_retry_at` set; confirm planner/schema semantics consistently.]

### Anti-Patterns to Avoid
- **Publishing outside a claimed state:** calling Graph API while row is still `scheduled/failed` without `publishing` claim allows duplicate concurrent sends.
- **Auto-retrying ambiguous outcomes:** timeout/network uncertainty after possible remote success must not trigger automatic resend (D-11).
- **Blocking approval response on publish:** any immediate attempt must run after commit and off request path (PUB-02/D-01).
- **Leaking secrets/raw Graph payloads:** tokens, app secrets, full request/response bodies, or decrypted credentials must never reach logs/UI/responses.
- **Separate retry logic for manual/cron/immediate paths:** violates D-03/D-12 and creates idempotency drift.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Distributed/concurrent queue locking | in-memory mutexes, "if status==scheduled then publish" checks without lock | Postgres row lock claim: `FOR UPDATE SKIP LOCKED` + transactional status transition | Cron reentry, double-click, and parallel workers require DB-enforced exclusion. [VERIFIED: PUB-04/D-09] |
| Secret/token storage and handling | plaintext tokens, ad-hoc masking, returning account tokens to UI | Existing Fernet crypto service + server-only account access + safe error summaries | Prevents credential leakage and aligns with SOC-04/META-05. [VERIFIED: crypto/meta_oauth/config] |
| Cron authentication scheme | new auth tokens/secrets for social worker | Existing `X-Cron-Secret` / `require_cron_secret` + `CRON_SECRET` | D-02 requires same operational pattern as `/admin/expire`. [VERIFIED: deps/admin] |
| HTTP client plumbing for Meta calls | raw sockets/custom retry HTTP stack | `httpx.AsyncClient` with explicit timeout and response parsing | Consistent with codebase and async FastAPI runtime. [VERIFIED: meta_oauth.py] |
| New social domain models/tables | duplicate status stores outside `social_posts` | Existing `social_posts` (+ `social_post_logs`, `social_accounts`) | Foundation already modeled for lifecycle/retries/audit/connection state. [VERIFIED: models] |

**Key insight:** Phase 17 is a correctness/idempotency problem over existing primitives; custom concurrency or security plumbing is the highest-risk path to duplicate posts or secret leakage.

## Common Pitfalls

### Pitfall 1: Duplicate Facebook posts on race/retry
**What goes wrong:** Same post published twice by concurrent cron + immediate dispatch, cron reentry, or manual retry clicks.
**Why it happens:** No atomic claim, no pre-send idempotency check, or auto-resend after ambiguous timeout.
**How to avoid:** Claim with `SKIP LOCKED`, transition to `publishing` before send, short-circuit if `published`/`external_post_id`, and make manual retry go through same pipeline (D-09/D-10/D-12). Treat ambiguous remote outcomes as non-auto-retry (D-11).
**Warning signs:** Multiple `external_post_id`-creating calls for same row in logs; status checks done outside claim transaction.

### Pitfall 2: Blocking or breaking site approval flow
**What goes wrong:** Approval waits on Graph/network or fails when social dispatch errors.
**Why it happens:** Immediate publish executed inline before response/commit boundary handling.
**How to avoid:** Preserve existing site-first commit and response; dispatch only after commit via non-blocking mechanism and swallow/log dispatch failures; cron endpoint provides fallback (PUB-02/D-01/D-03).
**Warning signs:** Approve handler awaits `publish`; exceptions from social path change approve HTTP result.

### Pitfall 3: Retry loops without valid connection
**What goes wrong:** Worker repeatedly retries posts when account is disconnected/`needs_reconnect` or token invalid/decrypt fails.
**Why it happens:** Classifying auth/config failures as transient or not checking account state before send.
**How to avoid:** Resolve and validate connected account/token before publish; if unavailable/invalid, mark blocked permanent/non-auto-retryable with safe pt-BR guidance to reconnect (D-06). Optionally mark account `needs_reconnect` on definitive token failures only via safe existing semantics. [VERIFIED: account model/status + D-06/D-10 policy parallels]
**Warning signs:** Increasing attempts with "reconectar" errors and `next_retry_at` still set.

### Pitfall 4: Leaking secrets or unsafe diagnostics
**What goes wrong:** Access tokens, decrypted page tokens, app secrets, or raw Graph responses appear in logs/UI/API.
**Why it happens:** Logging exception payloads or persisting raw provider responses in `last_error`.
**How to avoid:** Map errors to fixed pt-BR summaries; store only safe summaries/codes in `last_error`/logs; never include token-like fields; keep `social_post_logs.response_summary` sanitized/truncated. [VERIFIED: security constraints + model fields]
**Warning signs:** `access_token`, `page_access_token`, or full JSON error bodies in strings returned to frontend.

### Pitfall 5: Manual retry shown/enabled for ineligible states
**What goes wrong:** UI allows retry for published/processing/future-scheduled/disconnected cases, causing confusing behavior or race pressure.
**Why it happens:** UI eligibility not aligned with backend rules.
**How to avoid:** Backend computes/exposes eligibility and enforces it on retry endpoint; UI uses pt-BR badges and only enables retry for eligible failed + connected + not published (D-14/D-15). Treat duplicate clicks as idempotent success/no-op response.
**Warning signs:** Retry button active on `publishing` or `published`; frontend-only gating.

### Pitfall 6: "Stuck in publishing" ambiguity mishandled
**What goes wrong:** Crashed worker leaves rows in `publishing`; naive auto-recovery republishes duplicates.
**Why it happens:** Process dies between claim/send/persist.
**How to avoid:** Per D-04/D-11, do **not** add default automatic recovery for stuck `publishing` and do **not** auto-republish ambiguous cases. If needed later, handle as explicit safe refinement (manual/verified recovery) outside this phase scope. [VERIFIED: D-04, D-11]
**Warning signs:** Automatic sweep resetting `publishing` to `scheduled` and causing duplicate sends.

## Code Examples

### Claim due posts (`FOR UPDATE SKIP LOCKED`)
```python
# Source: SQLAlchemy ORM + Postgres row locking intent from requirements [VERIFIED: PUB-04/D-09; query shape ASSUMED]
from datetime import datetime, timezone
from sqlalchemy import and_, or_, select
from app.models.social_post import SocialPost, SocialPostStatus

async def claim_due_social_posts(session, *, provider="facebook", limit=20):
    now = datetime.now(timezone.utc)
    stmt = (
        select(SocialPost)
        .where(
            SocialPost.provider == provider,
            or_(
                and_(
                    SocialPost.status == SocialPostStatus.scheduled,
                    SocialPost.scheduled_at.is_not(None),
                    SocialPost.scheduled_at <= now,
                ),
                and_(
                    SocialPost.status == SocialPostStatus.failed,
                    SocialPost.next_retry_at.is_not(None),
                    SocialPost.next_retry_at <= now,
                ),
            ),
        )
        .order_by(SocialPost.next_retry_at.nulls_last(), SocialPost.scheduled_at.nulls_last())
        .with_for_update(skip_locked=True)
        .limit(limit)
    )
    posts = list((await session.scalars(stmt)).all())
    claimed = []
    for post in posts:
        # Idempotent guard: never (re)publish if already published/has external id
        if post.status == SocialPostStatus.published or post.external_post_id:
            continue
        post.status = SocialPostStatus.publishing
        post.last_error = None
        post.next_retry_at = None
        claimed.append(post)
    await session.flush()
    return claimed
```

### Facebook feed publish call (backend-only)
```python
# Source: Meta Graph API Pages Publishing (`POST /{page-id}/feed`) [CITED: developers.facebook.com/docs/pages-api/posts] + httpx pattern [VERIFIED: meta_oauth.py]
import httpx

async def publish_feed_post(*, graph_version: str, page_id: str, access_token: str, message: str, link: str | None):
    url = f"https://graph.facebook.com/{graph_version}/{page_id}/feed"
    data = {"message": message, "access_token": access_token}
    if link:
        data["link"] = link
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, data=data)
    body = resp.json() if resp.content else {}
    return resp.status_code, body
```
[ASSUMED: form-encoded `data=` is acceptable; confirm against Meta API behavior and error schema.]

### Safe error mapping (pt-BR, no secrets)
```python
# Source: D-05/D-06/D-08/D-11 [VERIFIED: CONTEXT]
def map_publish_error(*, kind: str, reconnect_required: bool = False):
    if reconnect_required:
        return {
            "category": "permanent",
            "retry_auto": False,
            "message": "Conexão com o Facebook indisponível. Reconecte a integração para publicar.",
        }
    if kind == "transient":
        return {
            "category": "transient",
            "retry_auto": True,
            "message": "Falha temporária ao publicar. Uma nova tentativa será feita automaticamente.",
        }
    if kind == "ambiguous":
        return {
            "category": "ambiguous",
            "retry_auto": False,
            "message": "Não foi possível confirmar a publicação. Verifique antes de tentar novamente para evitar duplicidade.",
        }
    return {
        "category": "permanent",
        "retry_auto": False,
        "message": "Não foi possível publicar este post. Revise a integração ou o conteúdo e tente novamente.",
    }
```

### Suggested admin API contract shapes (discretionary but recommended)
```python
# Source: existing API/schema style [VERIFIED: codebase patterns]
# GET /api/v1/admin/social-posts?status=&page=&limit=  (D-13)
# Response item:
# {
#   "job_id": "...", "job_title": "...", "provider": "facebook",
#   "status": "scheduled|publishing|published|failed|cancelled|draft",
#   "status_label": "Agendado|Publicando|Publicado|Falhou|Cancelado|Rascunho",
#   "last_error": "mensagem segura pt-BR" | null,
#   "published_url": "https://facebook.com/..." | null,
#   "external_post_id": "..." | null,
#   "attempts": 2,
#   "next_retry_at": "...",
#   "can_retry": true|false,
#   "retry_block_reason": "Reconexão necessária" | null
# }
#
# POST /api/v1/admin/social-posts/{job_id}/retry  (D-12,D-15)
# -> 202/200 with same pipeline outcome; idempotent no-op if not eligible
#
# POST /api/v1/admin/social/worker (X-Cron-Secret)  (D-02,D-04)
# -> {"status":"ok","claimed":n,"processed":n,"published":n,"retried":n,"failed_final":n,"skipped":n}
```
[ASSUMED: exact paths/fields; planner should pick names consistent with existing routers/schemas and keep protected.]

## State of the Art

| Old Approach | Current Approach (this phase) | When Changed | Impact |
|--------------|-------------------------------|--------------|--------|
| Approve registers `scheduled` social post but `FacebookPublisher` is stub/no worker | Real async pipeline: cron + immediate dispatch, claim/lock, Graph publish, retry/backoff, status/retry UI | Phase 17 (planned) | Completes PUB/UI delivery while preserving site-first behavior. [VERIFIED: roadmap/requirements/current stub] |
| Draft/approve-focused social API only (`GET/POST generate/PUT draft`) | Add operational status/list + manual retry + worker trigger endpoints | Phase 17 (planned) | Enables observability and safe recovery without DB access. [VERIFIED: CONTEXT D-13/D-15] |
| "Fire-and-forget" as business intent only | Fire-and-forget enforced operationally (no post-edit/delete sync to Facebook) | Phase 16 decision, enforced in 17 | Avoids scope creep and unsafe update/delete calls. [VERIFIED: POST/PUB-08] |

**Deprecated/outdated:**
- Treating `SOCIAL_WORKER_SECRET` as the cron auth for this worker path: D-02 requires **reusing `CRON_SECRET` / `require_cron_secret`** (same as `/admin/expire`). [VERIFIED: CONTEXT D-02, deps/config]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Immediate non-blocking dispatch is best implemented with FastAPI `BackgroundTasks` (or equivalent in-process task) after commit/response, with cron as required fallback. | Architecture / Pitfalls | If task scheduling is unreliable under chosen server model, first attempt may be skipped but cron still covers (acceptable per D-01). |
| A2 | SQLAlchemy async supports `select(...).with_for_update(skip_locked=True)` correctly on Neon/Postgres in this codebase setup. | Patterns / Code Examples | Claim query may need dialect-specific adjustment; concurrency safety depends on this. |
| A3 | Retryable-failed posts are represented as `status=failed` with `next_retry_at` set (and due), while final/manual-only failures have `next_retry_at=NULL`; worker eligibility follows D-04 exactly. | Pattern 4 / Data semantics | Off-by-one or wrong requeue behavior; planner must codify one consistent state rule. |
| A4 | Graph feed publish success returns JSON containing post `id` usable as `external_post_id` and for constructing a stable admin-facing link; if not reliably derivable, store best-known URL/id fields safely. | PUB-01 / UI | UI "link do post publicado" may be incomplete; may need fallback display of external ID. [CITED: Graph API behavior; details ASSUMED] |
| A5 | Ambiguous failures (e.g. timeout after request send) should be persisted as failed/manual-review-required without auto `next_retry_at`, to satisfy "priorizar evitar duplicata" (D-11). | Retry/idempotency | Posts may require manual intervention more often; safer than duplicates. |
| A6 | A small batch limit per worker cycle (e.g. 10–50) is sufficient for 100–500 jobs/month and avoids long cron requests/timeouts. | Architecture / Discretion | Under-sizing could delay backlog; over-sizing could hit runtime/request limits. |
| A7 | Existing `social_post_logs` schema is sufficient for attempt/result/error/response summaries without migration; optional only if new fields are strictly needed. | Observability | Extra migration work if current columns cannot represent required audit info. |

## Open Questions

1. **How to represent "ambiguous, needs verification" distinctly from retryable/permanent failed in current status enum?**
   - What we know: Enum has `failed`; D-11 requires no auto-republish and safe/manual handling. `last_error` can carry guidance. [VERIFIED: model + CONTEXT]
   - What's unclear: Whether UI/backend needs a separate marker/category for manual-only ambiguous failures vs exhausted retries.
   - Recommendation: Keep DB enum unchanged; encode via `failed` + `next_retry_at NULL` + categorized safe `last_error`/log reason (and/or eligibility flag in API). Only add schema state if necessary.

2. **Published post link derivation**
   - What we know: UI must show link when available (UI-01/D-14). Graph returns IDs; page context is known (`page_id`). [VERIFIED: requirements/context/models]
   - What's unclear: Most reliable permalink format across post types from feed publish response alone.
   - Recommendation: Persist `external_post_id`; if permalink derivable reliably, expose computed URL; otherwise expose ID and/or best-effort link builder marked safe, and keep UI resilient when link unavailable.

3. **Manual retry behavior when account is not connected**
   - What we know: D-15 says disable/ocultar with orientação when reconnection needed/not eligible. D-06 requires blocked non-auto-retry with reconnection guidance. [VERIFIED: CONTEXT]
   - What's unclear: Whether retry endpoint should reject with actionable 409/422 or accept and record blocked outcome.
   - Recommendation: Prefer deterministic reject/no-op with safe pt-BR reason when ineligible, and let UI disable based on `can_retry`/reason from status payload.

4. **Immediate dispatch granularity (single post vs due-batch cycle)**
   - What we know: D-01 targets "publish now" approval first attempt; D-03 requires same pipeline. [VERIFIED: CONTEXT]
   - What's unclear: Whether background task should process only the specific post ID or run a general due cycle.
   - Recommendation: Support targeted processing by `social_post_id` (fast path, minimal contention) implemented atop the same claim/process functions, plus cron full due-batch cycle.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python/FastAPI/SQLAlchemy async runtime | Worker, endpoints, pipeline | ✓ | project stack [ASSUMED] | — |
| Neon/Postgres with row locking | `FOR UPDATE SKIP LOCKED` claim/idempotency | ✓ | managed Postgres [ASSUMED] | — |
| `httpx` (backend) | Facebook Graph publish | ✓ (used in project) | project stack [ASSUMED] | — |
| Meta Graph API + configured app/page envs (`META_*`) | Real publishing (PUB-01) | ? env-dependent | `META_GRAPH_VERSION` configurable (default in settings) [VERIFIED: config] | Safe failure + admin reconnect/error messaging (no site impact) |
| Connected Facebook Page + valid decryptable token (`SOCIAL_TOKEN_ENCRYPTION_KEY`) | Publishing attempts | ? env-dependent | runtime state [VERIFIED: models/crypto] | Block as reconnect-needed/non-auto-retry per D-06 |
| `CRON_SECRET` + Render cron (1–5 min) hitting worker endpoint | Reliable polling/retries in deployed env | ? env-dependent | N/A | Immediate attempt may process some cases; manual ops limited without cron in sleeping hosts |
| `SITE_PUBLIC_URL` | Link included in post payload (from draft content) | ? env-dependent | URL config [VERIFIED: Phase 16 behavior/config] | Draft generation/approval already guards; publish sends stored approved text/link data as-is |

**Missing dependencies with no fallback:**
- None that should block site publishing; social publishing degrades safely with status/error visibility (PUB-02). [VERIFIED: constraints]

**Missing dependencies with fallback:**
- Meta config/connection/cron not ready: posts remain scheduled/failed with pt-BR guidance and can be retried when eligible.

## Validation Architecture

> `workflow.nyquist_validation` key absent in `.planning/config.json` → treat as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio/httpx test tooling (backend) [ASSUMED: per project stack] |
| Config file | `backend/pyproject.toml` / existing `backend/tests` conventions [ASSUMED] |
| Quick run command | `cd backend && pytest -q tests/test_social_publish_pipeline.py tests/test_facebook_publisher.py -x` [ASSUMED paths for new phase tests] |
| Full suite command | `cd backend && pytest -q` [ASSUMED] |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PUB-01 | `FacebookPublisher` posts `message`+`link` to `/{page_id}/feed` and returns external ID on success | unit/integration (mock httpx/Graph) | `pytest backend/tests/test_facebook_publisher.py -x` | ❌ Wave 0 |
| PUB-02 | Approve remains successful and non-blocking when social publish path fails/unavailable | integration/API | `pytest backend/tests/test_admin_social_publish.py -x` | ❌ Wave 0 |
| PUB-03 | Immediate attempt is dispatched asynchronously after approval (or equivalent non-blocking trigger) and cron path reuses pipeline | integration | `pytest backend/tests/test_admin_social_publish.py -x` | ❌ Wave 0 |
| PUB-04 | Worker/cron processes due `scheduled` and retryable `failed` with `FOR UPDATE SKIP LOCKED` claim semantics | integration/concurrency-oriented | `pytest backend/tests/test_social_worker_claim.py -x` | ❌ Wave 0 |
| PUB-05 | Backoff/attempts use `SOCIAL_MAX_ATTEMPTS` and `SOCIAL_RETRY_DELAYS` defaults/overrides; exhausted retries stop auto scheduling | unit/integration | `pytest backend/tests/test_social_retry_policy.py -x` | ❌ Wave 0 |
| PUB-06 | Transient vs permanent (incl. reconnect-needed) classification sets correct retryability and safe pt-BR errors | unit | `pytest backend/tests/test_social_retry_policy.py -x` | ❌ Wave 0 |
| PUB-07 | No duplicates on concurrent/repeated claim, existing `external_post_id`, or ambiguous outcomes/manual retry | integration/concurrency | `pytest backend/tests/test_social_idempotency.py -x` | ❌ Wave 0 |
| PUB-08 | Job edit/close/expire flows do not trigger Graph update/delete or alter published social record behavior | integration/regression | `pytest backend/tests/test_social_fire_and_forget.py -x` | ❌ Wave 0 |
| UI-01 | Admin APIs/UI data expose status badge info, safe error summary, and published link/ID | integration/API (+ frontend checks) | `pytest backend/tests/test_admin_social_status_api.py -x` | ❌ Wave 0 |
| UI-02 | Manual retry endpoint/UI eligibility enforces idempotent, eligible-only retries | integration/API | `pytest backend/tests/test_admin_social_retry_api.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** Run targeted backend tests for touched publish/pipeline/admin modules and frontend lint/type/build checks for admin UI/API client changes. [ASSUMED]
- **Per wave merge:** `cd backend && pytest -q` for social/admin suites; frontend validation commands per `frontend/package.json`. [ASSUMED]
- **Phase gate:** Success criteria 1–4 satisfied with targeted automated coverage and safe degradation verified (no site publish regression, no duplicate/idempotency violations in tested races).

### Wave 0 Gaps
- [ ] `backend/tests/test_facebook_publisher.py` — PUB-01 Graph request/response/error mapping (mocked HTTP)
- [ ] `backend/tests/test_social_publish_pipeline.py` — shared pipeline flow, claim/process, status transitions, logs
- [ ] `backend/tests/test_social_retry_policy.py` — PUB-05/PUB-06 backoff, exhaustion, transient/permanent/ambiguous/reconnect cases
- [ ] `backend/tests/test_social_worker_claim.py` — PUB-04 eligibility and `SKIP LOCKED`/concurrency behavior
- [ ] `backend/tests/test_social_idempotency.py` — PUB-07 no-op/duplicate prevention/manual retry races
- [ ] `backend/tests/test_admin_social_publish.py` — PUB-02/PUB-03 approve non-blocking + dispatch/cron reuse
- [ ] `backend/tests/test_admin_social_status_api.py` / `test_admin_social_retry_api.py` — UI-01/UI-02 contracts and eligibility enforcement
- [ ] `backend/tests/conftest.py` fixtures for connected social account, encrypted token, due social posts, cron/admin auth helpers
- [ ] Framework/install gaps: none expected if pytest stack already present [ASSUMED]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Admin-only status/retry endpoints via existing `require_admin`; cron worker endpoint via `require_cron_secret` (`X-Cron-Secret`) only. [VERIFIED: deps/admin] |
| V3 Session Management | limited | Reuse existing JWT/admin session model; no new session mechanism. [VERIFIED: codebase] |
| V4 Access Control | yes | Strict separation: public never sees social internals; admin endpoints protected; cron endpoint not publicly usable without secret. [VERIFIED: patterns] |
| V5 Input Validation | yes | Validate path/query/body params (UUIDs, pagination/status filters), enforce state/eligibility server-side, sanitize/limit stored/displayed error text. [ASSUMED implementation detail] |
| V6 Cryptography | yes | Decrypt Page tokens only in backend using existing Fernet utilities/keys; never persist/log plaintext tokens. [VERIFIED: crypto.py, models, config validation] |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secret/token leakage via logs, `last_error`, API responses, or UI payloads | Information Disclosure | Map provider errors to fixed pt-BR summaries; redact/sanitize; never serialize tokens/decrypted secrets; audit response schemas. [VERIFIED: D-08/security constraints] |
| Unauthorized trigger of publish worker or retry actions | Spoofing / Elevation of Privilege | `require_cron_secret` for worker, `require_admin` for retry/status mutations/reads as applicable; constant-time secret compare already used. [VERIFIED: deps.py] |
| Duplicate publication caused by replay/race/ambiguous retry | Tampering / Integrity | DB claim locks, idempotent checks on `published/external_post_id`, ambiguous-no-auto-republish policy, unique `(job_id,provider)`. [VERIFIED: PUB-07, D-09..D-11] |
| SSRF/config abuse via outbound publish URL construction | Tampering | Do not accept user-controlled publish destination; build Graph URL only from trusted config/version + stored page ID. [ASSUMED control] |
| Denial of service via heavy cron cycles or hot retry loops | Denial of Service | Batch limits, due-only eligibility, bounded timeouts on `httpx`, no auto-retry loop when disconnected/permanent. [ASSUMED implementation detail] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-CONTEXT.md` — locked decisions D-01..D-17, scope, discretion/deferred
- `.planning/REQUIREMENTS.md` — PUB-01..PUB-08, UI-01..UI-02 definitions and traceability
- `.planning/ROADMAP.md` — Phase 17 goal, dependencies, success criteria
- `.planning/PROJECT.md`, `.planning/STATE.md`, `AGENTS.md` — core constraints, milestone decisions, current focus
- Prior phase context/research: `.planning/phases/14-*/14-CONTEXT.md`, `.planning/phases/15-*/15-CONTEXT.md`, `.planning/phases/16-*/16-CONTEXT.md`, `.planning/phases/16-*/16-RESEARCH.md`
- Codebase (verified by read): `backend/app/models/social_post.py`, `backend/app/models/social_account.py`, `backend/app/models/social_post_log.py`, `backend/app/crud/social_posts.py`, `backend/app/services/social/{publisher,types,facebook,crypto,meta_oauth}.py`, `backend/app/api/v1/admin.py`, `backend/app/deps.py`, `backend/app/core/{scheduler,config}.py`, `backend/.env.example`, `backend/app/schemas/*social*`, `frontend/lib/api.ts`, `frontend/app/admin/review/*`, `frontend/components/admin/ReviewRow.tsx`, `frontend/app/admin/integracoes/*`, `frontend/app/(public)/page.tsx`

### Secondary (MEDIUM confidence)
- Meta Graph API Pages Publishing docs (feed endpoint behavior/fields): https://developers.facebook.com/docs/pages-api/posts [CITED: endpoint family and publish concept; exact request/response nuances to confirm during implementation]
- SQLAlchemy/Postgres locking semantics for `FOR UPDATE SKIP LOCKED` (standard behavior) [CITED conceptually; API usage in this codebase ASSUMED]

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - grounded in existing repository dependencies and established module patterns
- Architecture: HIGH - driven by locked CONTEXT decisions and verified current models/APIs/flows
- Pitfalls: HIGH - directly derived from idempotency/retry/security requirements and existing site-first/ops patterns

**Research date:** 2026-11-16
**Valid until:** 2026-12-16 (stable internal phase scope; revalidate if Meta Graph behavior assumptions or endpoint contracts are revised)
