# Architecture Research: Instagram Publishing Integration (v1.5)

**Domain:** Add Instagram Graph API Content Publishing to existing EmpregaNoix Facebook/Meta social review-and-publish architecture
**Researched:** 2026-11-23
**Confidence:** MEDIUM-HIGH (HIGH on existing codebase integration points from direct code reading; MEDIUM on Meta Instagram Graph API behavior/details that must be confirmed against current Meta docs before implementation)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Admin Review UI (Next.js)                            │
├──────────────────────────────────────────────────────────────────────────────┤
│  ReviewQueue/EditJobDialog                                                   │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │ Facebook Section (existing)  │  │ Instagram Section (NEW)              │ │
│  │ - draft text/editor          │  │ - toggle enabled                     │ │
│  │ - publish now/schedule       │  │ - caption editor + counters          │ │
│  │ - generate/save/regenerate   │  │ - image source/preview               │ │
│  │ - status/retry               │  │ - status/retry/permalink             │ │
│  └──────────────┬───────────────┘  └──────────────────┬───────────────────┘ │
├─────────────────┴─────────────────────────────────────┴──────────────────────┤
│                         FastAPI Admin/Social API                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  Existing                          │  New/Modified                           │
│  - /admin/jobs/{id}/approve        │  - provider-aware draft/status/retry    │
│  - /admin/jobs/{id}/social-post*   │  - instagram draft/generate/save        │
│  - /admin/jobs/{id}/social-status  │  - image upload/generate/preview URL    │
│  - /admin/jobs/{id}/social-post/   │  - approve registers both providers     │
│    retry                           │    independently                        │
│  - /admin/social-posts            │  - worker processes facebook+instagram  │
│  - /admin/social/worker (cron)     │                                         │
├────────────────────────────────────┴─────────────────────────────────────────┤
│                         Social Domain Services                               │
├──────────────────────────────────────────────────────────────────────────────┤
│  Shared/Existing                   │  New                                    │
│  - SocialPublisher protocol        │  - InstagramPublisher                    │
│  - PublishResult/FailureCategory   │  - IG container create/poll/publish     │
│  - publish_pipeline (FB-specific)  │  - provider-aware pipeline/dispatcher   │
│  - post_generation (FB text)       │  - instagram caption generation/policy  │
│  - meta_oauth/token crypto         │  - ig-user-id resolution/cache          │
│  - site-first approve registration │  - image asset service/storage/URL      │
├────────────────────────────────────┴─────────────────────────────────────────┤
│                         Persistence (Neon/Postgres)                          │
├──────────────────────────────────────────────────────────────────────────────┤
│  social_accounts      social_posts        social_post_logs   social_media_*  │
│  + ig_user_id?        + provider=ig       (shared)            (NEW, image    │
│  + ig_username?       + caption/media     attempt/result     asset metadata  │
│  token reused           fields/permalink    per provider       + public URL) │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                        Meta Graph API / Instagram Graph API
                        - /{page-id}?fields=instagram_business_account
                        - /{ig-user-id}/media  (container)
                        - /{ig-container-id}?fields=status_code,status
                        - /{ig-user-id}/media_publish
```

### Component Responsibilities

| Component | Responsibility | Existing/New | Notes |
|-----------|----------------|--------------|-------|
| `SocialAccount` / `social_accounts` | Stores connected Meta Page, encrypted page token, connection status; should also expose/cache Instagram Business account identity | **MODIFY** | Reuse same Page token for IG calls. Add `ig_user_id` (and optionally `ig_username`) or equivalent durable field after resolving from linked Page. |
| `SocialPost` / `social_posts` | Per-job, per-provider publish record with status, schedule, attempts, retry, external id, errors, timestamps | **MODIFY** | Already has `provider` + unique `(job_id, provider)`. Add IG-specific fields: `caption`/reuse `text`, `media_asset_id`/`image_url`, `permalink`, `external_container_id` or generic metadata; keep status machine shared. |
| `SocialPostLog` | Attempt/result audit log | **REUSE/MINOR EXTEND** | Already provider-agnostic via `social_post_id`. May add `provider`/`step` metadata if useful, but not required if response_summary captures container/publish step. |
| `SocialPublisher` protocol | Provider publish contract | **REUSE** | Keep protocol stable; IG publisher implements same shape. Consider extending `PublishResult` with `permalink`, `external_container_id`, `raw_status` as optional safe fields. |
| `FacebookPublisher` | FB Graph `/{page}/feed` publish | **REUSE** | No behavior change except shared type evolution. |
| `InstagramPublisher` | IG 2-step Content Publishing | **NEW** | Create container, poll status, publish. Must return safe `PublishResult`; no tokens in logs/errors. |
| `publish_pipeline.py` | Claim, integration checks, publish, retry/finalize, idempotency, logging | **MODIFY (significant)** | Currently hardcoded to Facebook. Refactor to provider-aware orchestration while preserving existing FB behavior and counters. |
| `post_generation.py` | Draft generation/sanitization/schedule conversion | **MODIFY/EXTEND** | FB text rules differ from IG caption rules (hashtags, 2200 chars, no clickable link CTA, image required). Add IG caption generator/policy or parallel module; keep FB path intact. |
| `meta_oauth.py` | Meta OAuth, token exchange, page selection, connection verification | **MODIFY** | Extend scopes for IG permissions; during page selection/verification resolve and persist `ig-user-id`; status endpoint should report IG readiness. |
| `admin.py` social endpoints | Draft CRUD, approve registration, status, retry, worker | **MODIFY** | Make provider-aware. Avoid breaking existing FB frontend contracts; add explicit provider param or parallel IG endpoints, then migrate UI. |
| `ReviewQueue.tsx` / `EditJobDialog.tsx` | Admin review and social controls | **MODIFY** | Add Instagram section alongside Facebook with independent toggle/state/status. Keep FB UX/regression-safe. |
| `frontend/lib/api.ts` | Admin API client/types | **MODIFY** | Add IG draft/status types and provider-aware calls. |
| Public media serving | Publicly fetchable image URL for Meta | **NEW** | Serve image bytes from stable public URL. Must be unauthenticated, HTTPS in prod, cacheable, and not expose admin-only data. |
| Image asset generation/storage | Create or store mandatory IG image | **NEW** | Accept selected origin (logo/card/upload - decision pending) and normalize to IG-compatible JPEG/size; persist metadata and public URL. |

## Recommended Project Structure

```
backend/app/
├── api/v1/
│   ├── admin.py                     # MODIFY: provider-aware social endpoints, approve handles IG
│   ├── integrations.py              # MODIFY: IG readiness in status/verify/connect flow
│   └── public.py                    # MODIFY or add media route: public image serving endpoint
├── crud/
│   ├── social_accounts.py           # MODIFY: fetch/store IG account identity
│   ├── social_posts.py              # MODIFY: provider-aware status/retry/listing; IG fields
│   └── social_media.py              # NEW: image asset CRUD (if persisted in DB/storage table)
├── models/
│   ├── social_account.py            # MODIFY: ig_user_id / ig_username / ig linkage fields
│   ├── social_post.py               # MODIFY: IG caption/media/permalink/container fields
│   ├── social_post_log.py           # REUSE or minor extend
│   └── social_media_asset.py        # NEW: image metadata/storage reference/public token/path
├── schemas/
│   ├── social_posts.py              # MODIFY: provider-aware draft/status; IG fields, counters, warnings
│   └── social_integrations.py       # MODIFY: IG connection/readiness fields
├── services/social/
│   ├── publisher.py                 # REUSE: protocol
│   ├── types.py                     # MODIFY: richer PublishResult/SocialPostPayload or provider payloads
│   ├── facebook.py                  # REUSE: existing FB publisher
│   ├── instagram.py                 # NEW: IG Graph publisher (container+poll+publish)
│   ├── publish_pipeline.py          # MODIFY: provider-aware orchestration/dispatch
│   ├── post_generation.py           # MODIFY: split FB/IG caption generation or add IG module
│   ├── caption_policy.py            # NEW (optional): IG caption normalization/hashtag/count warnings
│   ├── meta_oauth.py                # MODIFY: scopes, ig-user-id resolution, verify
│   ├── image_assets.py              # NEW: image source resolution, generation, validation
│   └── media_storage.py             # NEW: store/serve strategy (local file/DB/object storage)
└── core/config.py                   # MODIFY: IG/media settings, public media base URL if needed

frontend/
├── app/admin/review/
│   ├── EditJobDialog.tsx            # MODIFY: add Instagram section, independent state/actions
│   └── ReviewQueue.tsx              # MODIFY: show per-provider status badges/outcomes
├── app/admin/integracoes/
│   └── IntegrationsClient.tsx       # MODIFY: show IG linkage/readiness, scopes/reconnect guidance
└── lib/api.ts                       # MODIFY: provider-aware social draft/status/retry types/functions
```

### Structure Rationale

- **`services/social/instagram.py`:** Keep IG API specifics isolated from Facebook and pipeline orchestration. The 2-step flow is materially different from FB feed publish.
- **`services/social/image_assets.py` + `media_storage.py`:** Image generation/storage/public serving is a new concern with security/operability constraints; do not bury it in post generation or API handlers.
- **Provider-aware CRUD/pipeline, not duplicate tables per provider:** `social_posts` already models per-provider records. Reuse it to keep independence/idempotency/audit consistent.
- **Public media endpoint in backend/public API:** Meta fetches image URL server-side; URL must be public. Keeping it in backend avoids coupling to Vercel admin deployment and makes URL lifecycle controllable.

## Architectural Patterns

### Pattern 1: Provider-Aware Social Post Records (Keep, Extend)

**What:** One `SocialPost` row per `(job_id, provider)` with shared lifecycle status and per-provider payload/result fields.
**When to use:** Always for Facebook/Instagram publish records.
**Trade-offs:** Shared table keeps dashboard/retry/idempotency simple; but columns become a superset. Avoid excessive provider-specific columns by using a small number of explicit fields plus carefully scoped JSON only if necessary.

**Example:**
```python
# Existing shape already supports independence
UniqueConstraint("job_id", "provider", name="uq_social_posts_job_provider")

# Extend with explicit IG fields (preferred over opaque JSON for queryability)
caption_text = mapped_column(Text, nullable=True)      # or keep `text` as caption/body
image_asset_id = mapped_column(UUID, ForeignKey("social_media_assets.id"), nullable=True)
external_container_id = mapped_column(String(255), nullable=True)
permalink = mapped_column(String(512), nullable=True)
```

**Recommendation:** Keep `text` as provider-facing content body/caption to minimize migration churn; add `permalink`, `external_container_id`, and image reference fields. Be explicit in schema/docs that `text` means FB message or IG caption depending on provider.

### Pattern 2: Separate Publisher Adapters Behind Shared Pipeline Contract

**What:** Keep `SocialPublisher.publish(payload) -> PublishResult`, implement `FacebookPublisher` and `InstagramPublisher`.
**When to use:** For actual Meta API calls.
**Trade-offs:** Clean boundary and testability; IG is multi-step so "publish" internally performs create/poll/publish. That fits if result captures final outcome and idempotency keys are persisted.

**Example:**
```python
class SocialPublisher(Protocol):
    async def publish(self, post: SocialPostPayload) -> PublishResult: ...

class InstagramPublisher(SocialPublisher):
    async def publish(self, post: SocialPostPayload) -> PublishResult:
        # 1) create container
        # 2) poll container status until ready/timeout
        # 3) publish container
        # 4) fetch permalink if needed
        return PublishResult(ok=True, external_post_id=media_id, permalink=permalink)
```

**Caution:** Do not put DB writes inside publisher. Publisher returns outcome; pipeline persists state transitions/logs.

### Pattern 3: Pipeline Orchestrator per Provider, Shared Core

**What:** Extract provider-specific preflight/build/publisher selection from `publish_pipeline.py`, keep shared claim/log/retry/idempotency/finalization rules.
**When to use:** Needed because current pipeline is Facebook-coupled (`get_active_connected_facebook_account`, FB message/link, FacebookPublisher).
**Trade-offs:** Refactor risk to existing FB flow; mitigate by preserving FB behavior with characterization tests before changing.

**Example:**
```python
async def process_claimed_post(session, post, settings=None, publisher=None):
    if post.provider == "facebook":
        return await _process_facebook(session, post, settings, publisher)
    if post.provider == "instagram":
        return await _process_instagram(session, post, settings, publisher)
    return "skipped"
```

**Recommendation:** Start with explicit provider dispatch functions, then extract common helpers (`append_log`, `classify`, `compute_next_retry`, idempotent guards). Avoid over-abstracting into a plugin framework.

### Pattern 4: Public Media Asset with Opaque Stable URL

**What:** Store image asset and expose through a public, non-guessable/stable URL that Meta can fetch. The IG container uses `image_url`.
**When to use:** Mandatory for IG image publishing.
**Trade-offs:** Simple backend serving works, but disk persistence/hosting matters. External object storage is more durable; local filesystem may be ephemeral on Render.

**Example:**
```text
POST /api/v1/admin/jobs/{id}/instagram/image  -> creates asset, returns preview URL
GET  /api/v1/public/media/{asset_token}.jpg   -> public image bytes for Meta/browser preview
```

**Recommendation:** Treat public image URL as a first-class persisted field. Do not generate ephemeral signed URLs that expire before Meta fetches/publishes.

## Data Flow

### Request Flow

```
[Admin edits IG section in Review]
    ↓
[PUT/POST /admin/jobs/{id}/social-post?provider=instagram]
    ↓
[Validate caption + image requirement + schedule]
    ↓
[Persist social_posts row (provider=instagram, status=draft/scheduled)]
    ↓
[Admin approves job]
    ↓
[approve_job() commits site publish FIRST]
    ↓
[Register/schedule Facebook draft (existing) AND Instagram draft (new), independently]
    ↓
[BackgroundTasks/cron worker claims eligible social_posts rows by provider]
    ↓
[InstagramPublisher: create container -> poll status -> publish]
    ↓
[Persist external IDs/permalink/status/logs; UI polls/status endpoints]
```

### State Management

```
[DB: social_posts row per provider]
    ↓ (admin GET status/draft)
[Review UI local state per provider]
    ↓ (user edits/generates/saves)
[Admin API validates/persists]
    ↓ (approve/worker)
[Pipeline transitions: draft/scheduled -> publishing -> published/failed]
    ↓
[Review/Admin status views reflect per-provider state]
```

### Key Data Flows

1. **Instagram draft save:** Admin edits caption/image/schedule in review -> backend validates (caption length, hashtag warning threshold, image present, schedule BRT->UTC) -> upsert `social_posts(provider='instagram')` as draft with image asset reference. Independent from FB draft.
2. **Approve (site-first):** Job status becomes published/approved on site and commits. Then social registration runs best-effort per provider. FB success/failure must not block IG registration; IG failure must not block FB or site.
3. **Worker publish (IG):** Claim due `social_posts` row with lock -> resolve connected account + decrypted Page token + `ig_user_id` -> ensure image public URL reachable/valid -> create IG media container -> poll container status -> publish container -> fetch/store permalink/external id -> mark published. Any ambiguous external state becomes `ambiguous`/no auto-retry per existing safety pattern.
4. **Token/permission failure:** Verification/OAuth marks account `needs_reconnect`; IG publish preflight fails final with safe reconnect message. No token exposure in logs or UI.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k jobs/month (current) | Current in-process cron endpoint + DB claim/lock is sufficient. Single admin, single IG account. Keep simple. |
| 1k-10k jobs/month | Add provider-aware batch limits, observability metrics, and object storage/CDN for media. Ensure worker interval handles due posts within SLA. |
| 10k+ jobs/month | Move media to dedicated object storage/CDN, split worker execution per provider/queue, add explicit job queue and dead-letter/reconciliation tooling. Likely overkill now. |

### Scaling Priorities

1. **First bottleneck:** Public image hosting reliability/latency for Meta fetches. Fix by using durable object storage + stable HTTPS URLs and cache headers.
2. **Second bottleneck:** Worker throughput and Meta rate limits. Fix by per-provider rate limiting, backoff honoring `Retry-After`/error codes, and bounded batch sizes.

## Anti-Patterns

### Anti-Pattern 1: Coupling FB and IG into one publish transaction/outcome

**What people do:** Approve/register/publish FB and IG as one unit; one failure marks both failed.
**Why it's wrong:** Violates milestone requirement and creates operational confusion/retries/duplicates.
**Do this instead:** Separate `social_posts` rows per provider, separate registration outcomes, separate claim/process cycles/logs, and independent retry actions.

### Anti-Pattern 2: Storing or exposing Meta tokens in image/public flows

**What people do:** Reuse private Meta/CDN URLs requiring auth, or log raw Graph responses containing sensitive data.
**Why it's wrong:** Meta cannot fetch protected images; logs may leak secrets.
**Do this instead:** Public image endpoint/object URL with no auth; sanitize logs/errors; keep token decryption in-memory only inside pipeline.

### Anti-Pattern 3: Treating IG container creation as immediately publishable

**What people do:** Create container and immediately call publish without checking container status.
**Why it's wrong:** IG media containers may be in progress; premature publish causes failures or ambiguous states.
**Do this instead:** Poll container status with bounded timeout/backoff; persist `external_container_id`; on timeout, classify as transient/ambiguous according to safety rules.

### Anti-Pattern 4: Ephemeral local image URLs on Render

**What people do:** Save generated image to local `/tmp` or instance disk and send that URL to Meta.
**Why it's wrong:** Render instances can restart; file disappears; Meta fetch fails later/retries break.
**Do this instead:** Persist image bytes in durable storage (object storage preferred; DB blob acceptable for small scale) and serve via stable public URL.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Meta OAuth / Graph API | Server-side OAuth + Graph calls via `httpx` | Extend scopes for Instagram Content Publishing; confirm current required permissions in Meta docs before implementation. Reuse encrypted Page token; resolve/store `ig-user-id`. |
| Instagram Graph Content Publishing | Two-step async: create container, poll status, publish | Requires publicly fetchable `image_url`. Handle rate limits, media processing states, and ambiguous publish outcomes conservatively. |
| Meta image fetcher | Outbound fetch from Meta to our public media URL | URL must be HTTPS/public/no auth/no IP allowlist assumptions. Return correct `Content-Type`, `Content-Length`, cache headers; avoid redirects that break Meta fetch if possible. |
| Groq LLM | Caption draft generation (admin-only) | Reuse existing pattern with IG-specific prompt/policy and fallback template. Never send secrets; keep fallback deterministic. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `admin.py` ↔ `crud.social_posts` | Direct async calls | Add provider parameter/default carefully; preserve FB callers. |
| `admin.py` ↔ `publish_pipeline.py` | Direct call / BackgroundTasks | Approve enqueues due posts; worker endpoint runs cycle. Both must become provider-aware. |
| `publish_pipeline.py` ↔ `InstagramPublisher` | In-process adapter call | Publisher returns `PublishResult`; pipeline owns DB transitions/logging/retry decisions. |
| `meta_oauth.py` ↔ `social_accounts` persistence | Direct CRUD/model updates | Store/revalidate IG user id and connection readiness alongside FB Page connection. |
| `Review UI` ↔ `admin social endpoints` | HTTP JSON (Bearer admin) | Per-provider draft/status/retry. Keep backward-compatible FB behavior during migration. |
| `Public media endpoint` ↔ `media storage` | Direct read by asset token/id | No admin auth. Must enforce safe path/token lookup and only serve intended media type. |

## Suggested Build Order

Dependencies drive this order. Each step should preserve FB behavior.

1. **Schema/model groundwork (foundation)** — **MODIFY/NEW**
   - Add IG identity to `social_accounts` (nullable `ig_user_id`, optional `ig_username`).
   - Add IG publish fields to `social_posts` (`permalink`, `external_container_id`, image/media reference; decide whether to reuse `text` as caption).
   - Add `social_media_assets` table/model if image persistence is DB/object-reference backed.
   - Alembic migration(s), model/schema updates, CRUD read/write support.
   - *Why first:* every other IG flow needs durable IDs/media references.

2. **Meta connection readiness for Instagram** — **MODIFY**
   - Extend OAuth scopes/config and callback/status handling.
   - Resolve `instagram_business_account` from selected Page and persist `ig_user_id`.
   - Update `/admin/integracoes` status UI to show IG ready/not ready/reconnect.
   - *Depends on:* schema fields for IG identity.

3. **Public image asset service + serving** — **NEW**
   - Define image origin strategy interface (generated card now; upload/logo later if chosen).
   - Implement deterministic fallback card generator (1080x1080 or 1080x1350 JPEG) and storage.
   - Expose public media URL endpoint; validate Meta-fetchability constraints (HTTPS/public/content-type).
   - *Depends on:* storage decision; can run parallel to publisher once schema exists.

4. **Instagram draft/caption API and review UI** — **MODIFY/NEW**
   - Provider-aware draft endpoints (`provider=instagram`) or parallel routes.
   - Caption generation with IG rules: 2200 chars, >30 hashtags warning, CTA "link na bio" style (links not clickable), no contacts/company leakage by existing policy defaults.
   - Review dialog: IG section alongside FB with independent toggle, preview, save/regenerate/schedule.
   - *Depends on:* image asset service for preview/required image; schema for draft fields.

5. **Approve/register integration for IG (site-first, independent)** — **MODIFY**
   - On approve, register/schedule IG draft independently of FB outcome.
   - Return per-provider outcomes in approve response; UI toast/status handles partial success.
   - *Depends on:* IG draft persistence and provider-aware CRUD.

6. **InstagramPublisher + provider-aware worker pipeline** — **MODIFY/NEW**
   - Implement IG container create/poll/publish with idempotency guards.
   - Refactor `publish_pipeline.py` to dispatch by provider, preserving FB path.
   - Worker endpoint processes both providers or accepts provider filter; cron remains safe/idempotent.
   - Add retry semantics for IG (no auto-retry on ambiguous; manual retry allowed when safe).
   - *Depends on:* account IG id, image public URL, draft registration.

7. **Observability, hardening, and tests** — **MODIFY/NEW**
   - Unit tests for caption policy, image URL builder/storage, IG publisher parsing/polling, pipeline idempotency/retries.
   - Integration tests for approve/register/site-first independence and worker cycles.
   - Manual Meta checklist doc update (permissions, IG business account linkage, image fetchability, rate-limit behavior).
   - *Depends on:* all prior steps.

## Data/Schema Impacts (Explicit)

### `social_accounts` — **MODIFY**

| Change | Type | Purpose |
|--------|------|---------|
| `ig_user_id` | `String(64)`, nullable, indexed optional | Instagram Business/Creator account ID resolved from linked FB Page; required for IG publishing. |
| `ig_username` | `String(255)`, nullable | Admin/operator visibility; optional. |
| `ig_connection_status` or derive from fields | nullable enum/string or computed | Optional; can derive "IG ready" from `status == connected` + `ig_user_id is not null`. Prefer derived first to avoid state drift. |

**Note:** Keep one social account row for the Facebook Page connection if token is shared. Do not create a separate account row with duplicated token unless product later supports multiple IG accounts.

### `social_posts` — **MODIFY**

| Change | Type | Purpose |
|--------|------|---------|
| `permalink` | `String(512)`, nullable | Persist IG permalink (and optionally FB permalink later) for admin visibility. |
| `external_container_id` | `String(255)`, nullable | IG container creation id for idempotency/debug/reconciliation. |
| `media_asset_id` | `UUID`, FK `social_media_assets.id`, nullable | Required for IG before scheduling/publish; null for FB. |
| `media_url` (optional denorm) | `Text`, nullable | Snapshot of public URL used at publish time; useful for audit/debug. Prefer asset relation as source of truth. |
| `provider` check/usage | existing string | Add `'instagram'` as supported provider. Consider app-level enum/validation; DB enum migration only if needed. |

**No change:** unique `(job_id, provider)` remains correct and enforces independence. Status enum remains shared.

### `social_post_logs` — **REUSE / minor MODIFY**

| Change | Type | Purpose |
|--------|------|---------|
| `step` or richer `response_summary` | optional `String(32)` / use existing text | Distinguish `container_create`, `container_status`, `publish` in IG flow. Can start by encoding in `response_summary`. |

### `social_media_assets` — **NEW (recommended)**

| Field | Type | Purpose |
|-------|------|---------|
| `id` | UUID PK | Asset identity |
| `job_id` | UUID FK jobs.id nullable/on delete set null or cascade policy | Traceability; asset may be reused/regenerated. |
| `provider_target` | String(32) | `instagram` (future-proof) |
| `kind` | String(32) | `generated_card`, `uploaded`, `company_logo`, `external_url_snapshot` |
| `source_url` | Text nullable | Original logo/image URL if applicable; never trusted for Meta fetch directly unless copied/stabilized. |
| `storage_key` / `file_path` | Text | Internal storage location |
| `public_token` or `public_path` | String/Text unique | Stable public serving key; opaque recommended. |
| `mime_type` | String(64) | Expect `image/jpeg` for IG v1.5. |
| `width`, `height` | Integer | Validation/audit. |
| `created_at` | timestamptz | Audit |

**Storage note:** If durable object storage is not available in current infra, DB `bytea` can work at small scale but increases DB size/backup cost. For 100-500 jobs/month, JPEG card storage is likely manageable; still document the tradeoff.

## Public Image URL Serving (Critical)

Instagram Graph API container creation requires an image URL Meta can fetch. This is a hard architectural constraint.

**Requirements:**
- Public HTTPS URL in production (no admin auth, no Turnstile, no cookies).
- Stable for long enough for container creation/publish/retries; preferably permanent for audit.
- Correct `Content-Type: image/jpeg` (or supported format), reasonable cache headers.
- No token leakage in URL query params except opaque asset token.
- Avoid ephemeral Render local disk unless persistent disk is mounted.

**Recommended serving options:**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| FastAPI public endpoint backed by durable object storage (S3/R2/Supabase/etc.) | Durable, scalable, clean URLs | New infra dependency/credentials | **Best medium-term** if easy to provision |
| FastAPI public endpoint backed by Postgres `bytea` | No new infra; durable with DB | DB bloat; larger responses from app server | **Acceptable MVP** at current volume |
| FastAPI static files on Render disk | Simple | Ephemeral on many setups; risky after deploy/restart | **Avoid** unless persistent disk confirmed |
| Direct external logo URL | No storage | Often not publicly fetchable/unstable/CORS irrelevant but Meta fetch may fail; format/size unknown | **Do not use directly**; snapshot/copy instead |

**Design rule:** Persist an internal asset and expose a canonical app URL like `https://<backend>/api/v1/public/media/ig/<opaque>.jpg`. Meta gets that canonical URL. The canonical URL resolves to durable storage.

## Idempotency / Retry Boundaries Per Provider

### Shared rules (keep)
- Unique social post per `(job_id, provider)`.
- Claim before publish (`scheduled/failed` -> `publishing`) via DB lock/atomic update.
- If already `published` or has `external_post_id`, return idempotent no-op.
- Ambiguous outcomes: mark failed with no auto-retry and clear operator message.

### Facebook (existing)
- Single Graph call `POST /{page-id}/feed`.
- Ambiguity mainly from timeout/uncertain response. Current behavior: no auto-retry on ambiguous.

### Instagram (new)
- Multi-step boundary:
  1. **Create container** - returns `creation_id/container_id`. Persist it immediately on success.
  2. **Poll container status** - `status_code` may be `IN_PROGRESS`, `FINISHED`, `ERROR`, `EXPIRED`. Bounded polling inside worker attempt.
  3. **Publish container** - returns media id. Persist `external_post_id`.
  4. **Fetch permalink** - optional post-publish enrichment; failure should not flip published to failed.

**Idempotency keys/state:**
- If `external_post_id` exists: published, no-op.
- If `external_container_id` exists but no `external_post_id`: resume at poll/publish, do **not** create another container unless Meta indicates container invalid/expired and safe to recreate.
- If no container/media id and request timed out before confirmed response: treat as ambiguous (safe default), require reconciliation/manual retry only with explicit check.

**Retry classification:**
- `transient`: 429, 5xx, network timeout before confirmed create, container `IN_PROGRESS` beyond short poll window (retry later), temporary fetch issues.
- `permanent`: invalid image URL, permissions missing, unsupported media, bad caption format/length, account not IG business/creator, missing `ig_user_id`.
- `ambiguous`: publish call timeout/uncertain response after container ready; create/publish response indeterminate. No auto-retry.

## Integration Points: New vs Modified

| Area | File/Component | Status | Change |
|------|----------------|--------|--------|
| DB schema | `backend/alembic/versions/0004_social_foundation.py` | **EXISTING** | No edit; add new migration(s). |
| DB schema | `backend/alembic/versions/0006_instagram_social.py` (name TBD) | **NEW** | Add IG account fields, social post IG fields, media asset table/indexes. |
| Model | `backend/app/models/social_account.py` | **MODIFY** | Add `ig_user_id`, optional `ig_username`. |
| Model | `backend/app/models/social_post.py` | **MODIFY** | Add `permalink`, `external_container_id`, `media_asset_id`/media fields. |
| Model | `backend/app/models/social_media_asset.py` | **NEW** | Public media asset metadata/storage reference. |
| Model exports | `backend/app/models/__init__.py` | **MODIFY** | Export new model if project pattern requires. |
| CRUD | `backend/app/crud/social_accounts.py` | **MODIFY** | Helpers for IG-ready connected account lookup. |
| CRUD | `backend/app/crud/social_posts.py` | **MODIFY** | Provider-aware queries/status/retry rules; include permalink/media in status item. |
| CRUD | `backend/app/crud/social_media.py` | **NEW** | Create/get asset by token/job. |
| Schemas | `backend/app/schemas/social_posts.py` | **MODIFY** | Provider-aware request/response, caption limits/warnings, image fields, permalink. |
| Schemas | `backend/app/schemas/social_integrations.py` | **MODIFY** | IG readiness/status fields (`ig_user_id`, `instagram_ready`, permission warnings). |
| API | `backend/app/api/v1/admin.py` | **MODIFY** | Provider-aware social draft/status/retry; approve registers FB+IG independently; worker handles both. |
| API | `backend/app/api/v1/public.py` | **MODIFY** | Public media serving endpoint for IG image fetch. Ensure no auth and safe content-type. |
| API | `backend/app/api/v1/integrations.py` | **MODIFY** | Expose IG readiness in status/verify responses. |
| Service | `backend/app/services/social/types.py` | **MODIFY** | Extend payload/result for image/container/permalink while keeping FB compatible. |
| Service | `backend/app/services/social/facebook.py` | **REUSE/MINOR** | Adapt only if shared types change. |
| Service | `backend/app/services/social/instagram.py` | **NEW** | IG publisher. |
| Service | `backend/app/services/social/publish_pipeline.py` | **MODIFY** | Major refactor for provider dispatch and IG flow; preserve FB idempotency semantics. |
| Service | `backend/app/services/social/post_generation.py` | **MODIFY** | FB/IG caption generation split or parameterized policy. |
| Service | `backend/app/services/social/meta_oauth.py` | **MODIFY** | Scopes, ig-user-id resolution, verification. |
| Service | `backend/app/services/social/image_assets.py` | **NEW** | Image validation/generation/normalization. |
| Service | `backend/app/services/social/media_storage.py` | **NEW** | Durable storage/read/write abstraction. |
| Config | `backend/app/core/config.py` | **MODIFY** | IG/media settings (max caption? not needed; storage path/bucket/public base URL/feature flags). |
| Frontend API | `frontend/lib/api.ts` | **MODIFY** | Add provider-aware social types/functions. |
| Frontend review | `frontend/app/admin/review/EditJobDialog.tsx` | **MODIFY** | Add IG section with independent state; image preview/upload/generate controls depending on decision. |
| Frontend review | `frontend/app/admin/review/ReviewQueue.tsx` | **MODIFY** | Per-provider status badges and approve outcome messaging. |
| Frontend integrations | `frontend/app/admin/integracoes/IntegrationsClient.tsx` | **MODIFY** | IG readiness/reconnect messaging. |
| Docs/tests | `docs/META-INTEGRATION-TESTING.md`, backend/frontend tests | **MODIFY/NEW** | Add IG checklist and mocks. |

## Risks and Open Decisions

| Risk / Decision | Impact | Architectural Guidance |
|-----------------|--------|------------------------|
| **Image origin decision open** (logo/card/upload) | Affects schema, UI, storage, validation | Implement `ImageAssetSource` strategy interface now; v1.5 can ship generated card fallback first, but schema should support `kind/source_url`. |
| **Image storage durability on Render** | Meta fetch failures, broken retries/audit | Do not rely on ephemeral disk. Prefer object storage or DB-backed bytes. Make storage backend swappable. |
| **Meta permissions/App Review** | OAuth/connect/publish blocked in live mode | Add scope/config plumbing, but gate rollout on confirmed current Meta permissions and review requirements. Document manual checklist. |
| **IG container async processing** | Worker may time out or publish too early | Bounded poll with backoff; persist container id; classify long `IN_PROGRESS` as transient retry. |
| **Rate/daily limits** | Failed publishes, noisy retries | Parse Graph error codes/subcodes; treat as transient with delayed retry when safe; expose clear admin error. Do not blind-retry. |
| **Token expiration / missing IG permission** | Publish failures after prior success | Reuse existing `needs_reconnect` pattern. Verification should check both FB page token validity and IG account resolvability. |
| **Provider-coupled pipeline refactor** | FB regression risk | Characterize FB behavior with existing tests first; refactor behind provider dispatch with minimal behavior change. |

## Sources

- Direct codebase inspection (HIGH): `backend/app/models/social_*.py`, `backend/app/services/social/*.py`, `backend/app/crud/social_posts.py`, `backend/app/crud/social_accounts.py`, `backend/app/api/v1/admin.py`, `backend/app/api/v1/integrations.py`, `backend/app/schemas/social_*.py`, `backend/app/core/config.py`, `backend/alembic/versions/0004_social_foundation.py`, `frontend/lib/api.ts`, `frontend/app/admin/review/*`, `frontend/app/admin/integracoes/IntegrationsClient.tsx`, `docs/META-INTEGRATION-TESTING.md`.
- Project context (HIGH): `.planning/PROJECT.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`.
- Instagram Graph API Content Publishing behavior (MEDIUM, training knowledge; verify before implementation): two-step container+publish, image URL must be publicly accessible, container status polling may be required, business/creator account linked to Facebook Page, permissions/rate limits subject to Meta current docs. **Verification required against current Meta developer docs during implementation.**

---
*Architecture research for: EmpregaNoix v1.5 Instagram publishing integration*
*Researched: 2026-11-23*