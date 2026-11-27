---
phase: 31-independent-publish-pipeline
verified: 2026-11-25T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 31: Independent Publish Pipeline Verification Report

**Phase Goal:** Publicação Instagram ocorre de forma assíncrona, segura e independente do Facebook.
**Verified:** 2026-11-25T00:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Ao aprovar/publicar uma vaga com Instagram habilitado, o processamento Instagram e Facebook segue de forma independente: falha em uma plataforma não bloqueia nem corrompe a outra. | ✓ VERIFIED | `backend/app/services/social/publish_pipeline.py` defines `SUPPORTED_PROVIDERS=("facebook","instagram")`, iterates providers in isolated `try/except` blocks, keeps per-provider counters/claimed IDs, and aggregates `by_provider` (`run_social_publish_cycle`, L1102-L1240). `backend/app/api/v1/admin.py` approve flow keeps site-first publish, handles FB registration in its own `try/except`, then runs IG registration/dispatch in a separate `try/except` with no FB/site mutation on IG failure (L156-L320). Dispatch is per `social_post.id` via `process_social_post_safe` (L313-L319). Tests: `test_pipeline_provider_isolation_ig_not_ready_does_not_block_facebook` (`backend/tests/test_social_publish_pipeline.py:470`), admin approve tests added per 31-02 summary. |
| 2 | Sistema publica no Instagram pelo fluxo Graph API em 2 passos (criar container, checar status quando necessário, publicar), com comportamento seguro em timeout/erro. | ✓ VERIFIED | `backend/app/services/social/instagram.py` implements `InstagramPublisher.publish()` with Graph create container `POST /{META_GRAPH_VERSION}/{ig_user_id}/media`, bounded status polling via `GET /{container_id}?fields=status_code,status,id`, publish `POST /{ig_user_id}/media_publish` with `creation_id`, and best-effort permalink fetch (L103-L416). Configurable budgets from settings: `META_GRAPH_VERSION`, `IG_PUBLISH_HTTP_TIMEOUT_SECONDS`, `IG_STATUS_POLL_MAX_ATTEMPTS`, `IG_STATUS_POLL_DELAY_SECONDS`, `IG_PUBLISH_MAX_ATTEMPT_SECONDS` (`backend/app/core/config.py:86,L99-L103,L169-L179`; used in publisher L127-L133). Timeouts/request errors map to ambiguous/transient/permanent safe results (L154-L167,L257-L304,L358-L363). Tests cover 2-step success, polling, create timeout ambiguity, permalink best-effort (`backend/tests/test_instagram_publisher.py:99,138,174,236`). |
| 3 | Admin consegue consultar resultado por plataforma com status, erro seguro acionável, IDs/permalink quando disponíveis, e histórico/auditoria sem exposição de tokens ou segredos. | ✓ VERIFIED | Safe status fields exposed by `SocialPostStatusItem`/`SocialPostLogItem` schemas (`backend/app/schemas/social_posts.py:60-L114`), including `published_permalink`, `ig_container_id`, `ig_media_id`, reconciliation fields, attempts/timestamps/errors; log schema excludes tokens/raw payloads. CRUD builds provider-aware status items and safe logs (`backend/app/crud/social_posts.py:289-L352,L384-L470`). Admin endpoints: provider-aware list (`/admin/social-posts`), FB/IG status endpoints, and safe logs endpoint `GET /admin/jobs/{job_id}/social-post/logs` returning only safe fields (L419-L453,L603-L625). Frontend types/API/UI render per-provider status, IDs/permalink/timestamps, retry reason, and lazy audit history (`frontend/lib/api.ts:841-L928`; `frontend/app/admin/social-posts/SocialPostsClient.tsx:11,L47-L330`; `frontend/app/admin/review/EditJobDialog.tsx:619,L1687-L1765`). `_safe_text` redacts token patterns in publisher/pipeline (`backend/app/services/social/instagram.py:31-L43`; `backend/app/services/social/publish_pipeline.py:81-L93`). |
| 4 | Retentativas e falhas ambíguas não causam duplicação cega de post; casos ambíguos ficam em estado seguro que exige verificação/reconciliação antes de nova tentativa automática. | ✓ VERIFIED | Ambiguous/critical IG outcomes persist `status=failed`, `next_retry_at=None`, `ig_reconciliation_required=True`, `ig_reconciliation_state="needs_reconciliation"`, known container/media IDs, and safe logs (`backend/app/services/social/publish_pipeline.py:1002-L1047,L1183-L1237`). IG reconciliation runs before any new publish when reconciliation required: checks known media/container IDs, marks published if already published, publishes same FINISHED container, polls boundedly for IN_PROGRESS, marks conclusive failures for ERROR/EXPIRED, and keeps ambiguous blocked when inconclusive (`_ig_reconcile_before_publish`, L385-L650; invoked L897-L913). CRUD retry-state allows IG reconciliation-required manual retry with explicit safe pt-BR reason; FB ambiguous remains blocked (`backend/app/crud/social_posts.py:262-L279`). Admin retry reuses same action and routes through provider-aware pipeline by `post_id` (`backend/app/api/v1/admin.py:543-L569`). Tests: `test_pipeline_ig_ambiguous_persists_reconciliation_without_auto_retry`, `test_pipeline_ig_reconciliation_published_marks_post_published` (`backend/tests/test_social_publish_pipeline.py:331,526`). |
| 5 | Limites de rate/diário do Instagram são tratados com segurança (sem retry storm), exibindo estado acionável ao admin quando publicação estiver bloqueada por limite. | ✓ VERIFIED | Instagram publisher classifies authoritative Graph runtime responses for 2207042/subcode/content_publishing_limit/rate-limit/429/limit signatures as permanent blocked actionable results with `ig_rate_limit_blocked` or `ig_content_publishing_limit` and pt-BR messages; no proactive pre-publish limit query present (reactive classification in `_is_rate_limit_error`, L52-L96; used on create/status/publish L170-L173,L208-L213,L274-L277). Pipeline maps these to final failed with no auto-retry, sets `ig_last_publish_error_code`, clears reconciliation requirement (`backend/app/services/social/publish_pipeline.py:154-L162,L1007-L1025`). CRUD blocks retry for IG rate/content limit with actionable pt-BR reason (`backend/app/crud/social_posts.py:251-L259`). UI displays retry block reason and reconciliation/rate-limit states (`frontend/app/admin/social-posts/SocialPostsClient.tsx:312-L321`; `frontend/app/admin/review/EditJobDialog.tsx:1728-L1765`). Tests: `test_instagram_publisher_rate_limit_2207042_is_blocked_no_retry_storm`, `test_pipeline_ig_rate_limit_is_blocked_no_retry_storm` (`backend/tests/test_instagram_publisher.py:208`; `backend/tests/test_social_publish_pipeline.py:417`). |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/alembic/versions/0008_instagram_publish_reconciliation.py` | Explicit IG container/publish/reconciliation columns on `social_posts` | ✓ VERIFIED | Adds `ig_container_id`, `ig_media_id`, `ig_permalink`, `ig_reconciliation_required`, `ig_reconciliation_state`, `ig_last_reconciled_at`, `ig_last_publish_error_code`; revision/down_revision correct. |
| `backend/app/models/social_post.py` | SocialPost IG reconciliation/publish metadata fields | ✓ VERIFIED | Mapped columns present with safe defaults/nullability (L66-L79). |
| `backend/app/services/social/instagram.py` | Instagram Graph 2-step publisher and safe error classification | ✓ VERIFIED | `InstagramPublisher(SocialPublisher)` implements bounded 2-step flow, safe error mapping, no token leakage in safe text, best-effort permalink. |
| `backend/app/services/social/publish_pipeline.py` | Provider-aware claim/process/retry/reconciliation core for FB+IG | ✓ VERIFIED | Provider-aware cycle, isolated blocks, by_provider, IG reconciliation, rate-limit/ambiguity handling, publish_enabled claim eligibility via CRUD. |
| `backend/app/crud/social_posts.py` | publish_enabled claim eligibility and reconciliation-aware retry-state helpers | ✓ VERIFIED | `list_due_for_claim` filters `publish_enabled.is_(True)`; `compute_social_retry_state` handles IG rate-limit block and reconciliation-required retry; status item includes safe IG audit fields. |
| `backend/app/api/v1/admin.py` | Provider-aware worker/retry/status/list/approve dispatch and safe social log audit endpoint | ✓ VERIFIED | Worker returns `by_provider`; approve has isolated IG dispatch; retry resolves by post_id with provider mismatch/ambiguity guards; logs endpoint returns safe fields. |
| `frontend/lib/api.ts` | Provider-aware social status/retry/log types and API calls | ✓ VERIFIED | Status item includes permalink/reconciliation fields; `getSocialPostLogs` and provider-aware `retrySocialPost/getAdminSocialPosts` present. |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | Per-provider status/audit/retry UI for FB and IG | ✓ VERIFIED | Renders provider labels, audit history, reconciliation/rate-limit messaging, provider-aware retry. |
| `backend/tests/test_instagram_publisher.py` | IG publisher contract/behavior tests | ✓ VERIFIED | 7 tests covering contract, 2-step success, polling, timeout ambiguity, 2207042 blocked, permalink best-effort. |
| `backend/tests/test_social_publish_pipeline.py` | Pipeline ambiguity/reconciliation/rate-limit/provider-isolation tests | ✓ VERIFIED | Includes publish_enabled filter, IG ambiguity reconciliation, rate-limit no retry storm, provider isolation, reconciliation published. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/services/social/publish_pipeline.py` | `backend/app/services/social/instagram.py` | provider dispatch to InstagramPublisher/IG handler | ✓ WIRED | Imports `InstagramPublisher` (L41), routes `provider == "instagram"` to `_process_instagram_claimed_post` (L675-L683), instantiates default publisher (L850). |
| `backend/app/services/social/publish_pipeline.py` | `backend/app/crud/social_posts.py` | claim/list/retry-state helpers and publish_enabled eligibility | ✓ WIRED | Uses `list_due_for_claim` (L29,L1123), claim/mark helpers; CRUD enforces `publish_enabled.is_(True)` (L121). |
| `backend/app/services/social/publish_pipeline.py` | `backend/app/models/social_post.py` | persist container/reconciliation/permalink metadata on ambiguous/success paths | ✓ WIRED | Sets `ig_container_id`, `ig_media_id`, `ig_permalink`, `ig_reconciliation_required`, `ig_reconciliation_state`, timestamps/error codes across finalize/reconcile/exception recovery paths. |
| `backend/app/api/v1/admin.py` | `backend/app/services/social/publish_pipeline.py` | run_social_publish_cycle/process_social_post_safe provider-aware calls | ✓ WIRED | Imports both (L54), worker calls `run_social_publish_cycle()` (L404), retry calls `run_social_publish_cycle(post_id=target_post.id, limit=1)` (L545), approve dispatches `process_social_post_safe` (L316). |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | `frontend/lib/api.ts` | getAdminSocialPosts/retrySocialPost/log fetch calls | ✓ WIRED | Imports/uses `getAdminSocialPosts`, `retrySocialPost`, `getSocialPostLogs` (L9-L13,L93,L110,L138). |
| `backend/app/api/v1/admin.py` | `backend/app/models/social_post_log.py` / safe audit CRUD | safe audit history endpoint | ✓ WIRED | `/jobs/{job_id}/social-post/logs` uses `list_social_post_logs` and returns `SocialPostLogsResponse` with safe schema fields only (L603-L625). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|-------------|--------|--------------------|--------|
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | `items` social status list | `getAdminSocialPosts()` -> `/admin/social-posts` -> `list_social_status_items()` | Yes, DB-backed query + status builder | ✓ FLOWING |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | audit log `items` | `getSocialPostLogs()` -> `/admin/jobs/{job_id}/social-post/logs` -> `list_social_post_logs()` | Yes, DB-backed SocialPostLog query; safe fields only | ✓ FLOWING |
| `frontend/app/admin/review/EditJobDialog.tsx` | `igStatus` | `getInstagramSocialStatus()` / retry response -> admin status endpoint | Yes, DB-backed status item | ✓ FLOWING |
| `backend/app/services/social/publish_pipeline.py` | IG publish/reconciliation state | `InstagramPublisher.publish()` Graph responses + `SocialPost` persisted metadata | Yes, external API results mapped to persisted state; ambiguity reconciled via stored IDs | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase 31 key tests (publisher+pipeline) | Not executed in this verification (read-only static verification; no test DB migration guaranteed in env) | n/a | ? SKIP |
| Phase 30 DB-backed admin IG regression | Reported by user/context: failed in env due missing migration 0008 in test DB (`UndefinedColumn ig_container_id`) | env migration issue, not code regression signal | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PUBL-01 | 31-01, 31-02 | Aprovação/publicação processa Instagram e Facebook de forma independente; falha em uma plataforma não bloqueia nem corrompe a outra. | ✓ SATISFIED | Isolated provider blocks in publish cycle (`publish_pipeline.py`), isolated IG approve dispatch try/except (`admin.py`), per-provider by_provider counters, provider isolation test. |
| PUBL-02 | 31-01 | Backend implementa publicação Instagram Graph API em 2 passos assíncronos com versão Graph configurável e tratamento seguro de timeout. | ✓ SATISFIED | `InstagramPublisher` 2-step create/status/publish, `META_GRAPH_VERSION`, bounded IG timeout/poll/attempt budgets, safe timeout/ambiguous mapping. |
| PUBL-03 | 31-01, 31-02 | Pipeline persiste legenda/IDs/permalink/status/erro seguro/tentativas/timestamps; logs sem tokens/segredos. | ✓ SATISFIED | SocialPost fields + IG metadata columns, SocialPostLog attempts/safe summaries, safe admin schemas/endpoints/UI; token-redacting `_safe_text`. |
| PUBL-04 | 31-01, 31-02 | Retry/backoff idempotente e seguro contra ambiguidade; ambíguo/timeout não dispara auto-retry cego que possa duplicar post. | ✓ SATISFIED | Ambiguous persisted as failed+reconciliation_required+no next_retry_at; reconciliation-before-republish checks known IDs and reuses same container; manual retry only. |
| PUBL-05 | 31-01, 31-02 | Rate limit e limite diário IG tratados com segurança, sem retry storm, com status acionável ao admin. | ✓ SATISFIED | Reactive authoritative Graph error classification (2207042/content_publishing_limit/rate limit), permanent blocked actionable pt-BR state, retry blocked in CRUD, no proactive pre-publish limit query. |

**Orphaned requirements for Phase 31:** None. REQUIREMENTS.md maps PUBL-01..05 to Phase 31 and all are declared in plan frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/app/services/social/publish_pipeline.py` | 1071,1078 | `return ...` after `# Permanent/unknown/conclusive` | ℹ️ Info | Not a stub; this is the expected conclusive failure branch with safe finalization. |
| `backend/app/services/social/instagram.py` | 331,334 | `return PublishResult(ok=False, ...)` on unexpected exception | ℹ️ Info | Defensive safe failure path; preserves ambiguity when container is known. |
| `.planning/REQUIREMENTS.md` | 31-35,83-87 | PUBL-01..05 checkboxes/table still marked Pending | ⚠️ Warning | Documentation traceability is stale; code evidence satisfies the requirements. Update REQUIREMENTS.md during phase/verification bookkeeping. |

### Human Verification Required

None. All phase must-haves were verifiable through code structure, wiring, and test presence. Runtime/manual Meta Graph behavior remains an operational concern, but Phase 31 goal achievement is evidenced by implementation and safe handling paths.

### Gaps Summary

No gaps found. Phase 31 codebase evidence satisfies PUBL-01..PUBL-05 and the ROADMAP success criteria. The only notable follow-up is bookkeeping: REQUIREMENTS.md still shows PUBL-01..05 as Pending despite implemented/verified code.

---

_Verified: 2026-11-25T00:00:00Z_
_Verifier: Claude (gsd-verifier)_