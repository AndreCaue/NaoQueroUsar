# Pitfalls Research

**Domain:** Adding Instagram Graph API Content Publishing to an existing Facebook Pages publishing system (EmpregaNoix v1.5)
**Researched:** 2026-11-23
**Confidence:** HIGH for official Meta API behavior/limits (verified against Meta docs fetched 2026-11-23); MEDIUM for App Review timelines/edge-case policy enforcement; HIGH for codebase integration risks (verified against current backend/frontend social integration code)

## Critical Pitfalls

### Pitfall 1: Treating Instagram as "Facebook with an image"

**What goes wrong:**
The team reuses the existing single-call Facebook publish pattern (`POST /{page_id}/feed`) and assumes Instagram is similar. Instagram Content Publishing is a 2-step async pipeline: create media container (`POST /{ig-user-id}/media`), poll container status (`GET /{ig-container-id}?fields=status_code`) until `FINISHED`, then publish (`POST /{ig-user-id}/media_publish` with `creation_id`). Skipping status checks causes publish attempts on `IN_PROGRESS`/`ERROR`/`EXPIRED` containers and intermittent failures that look random.

**Why it happens:**
The existing `FacebookPublisher.publish()` returns a direct result from one Graph call. Developers naturally extend `SocialPostPayload`/publisher without modeling container lifecycle. The current pipeline marks `publishing` and expects a terminal result in one pass.

**How to avoid:**
- Model IG publishing as a stateful workflow, not a single HTTP call. Persist `ig_container_id`, `container_status`, `container_created_at`, and publish attempt metadata.
- Implement container polling with bounded backoff (Meta recommends checking once per minute, no more than 5 minutes; adapt for worker cadence, but keep bounded).
- Only call `media_publish` when container status is `FINISHED`. Handle `IN_PROGRESS`, `ERROR`, `EXPIRED`, `PUBLISHED` explicitly.
- Keep Facebook single-step path intact; add an IG-specific publisher/workflow behind the same `SocialPublisher`-style interface or a separate IG pipeline branch. Do not force IG into FB assumptions.

**Warning signs:**
- Logs show `9007 / subcode 2207027` "media is not ready for publishing".
- Posts stuck in `publishing` with no `external_post_id`.
- Code calls `media_publish` immediately after container creation without reading `status_code`.
- Tests only mock one successful response for IG publish.

**Phase to address:**
Phase 1 — IG domain model & publish workflow design (before UI wiring). Verify with integration tests that mock container `IN_PROGRESS -> FINISHED -> PUBLISHED` and error/expiry paths.

---

### Pitfall 2: Image URL is not publicly fetchable by Meta at publish time

**What goes wrong:**
IG container creation/publishing fails because Meta cURLs `image_url` from its servers. Local/dev URLs, auth-protected URLs, signed URLs that expire before Meta fetches/processes, redirect-to-login pages, `localhost`, private-network addresses, or non-image content-types cause `2207052` ("media could not be fetched"), processing `ERROR`, or silent downstream failures. "Works in my browser" is not sufficient.

**Why it happens:**
Teams reuse internal admin/upload URLs or generate temporary links. In local dev, backend URLs are not internet-reachable. Signed CDN URLs are generated at review time but expire before delayed/scheduled publish or retry. The existing system has no media hosting requirement for Facebook text/link posts.

**How to avoid:**
- Treat image hosting as a first-class contract: public HTTPS URL, no auth/cookie/session, no private IP, resolves to actual media file, correct `Content-Type`.
- Validate before saving/scheduling: server-side fetch/HEAD check from backend is useful but not sufficient; ensure URL is externally reachable (not just from your server on same network). For local dev, document tunnel/public bucket requirement or provide explicit dev guardrail.
- Ensure URL lifetime covers: review preview, scheduled time, retry window, and Meta processing delay. If using signed URLs, set TTL >= max(schedule delay + retry window + 24h safety) or regenerate just-in-time at publish.
- Enforce image constraints early: JPEG only (no MPO/JPS), max 8MB, aspect ratio 4:5 to 1.91:1. Reject/transform before container creation.
- Store image source metadata (origin: upload/generated/logo), storage key, final public URL, and validation result. Do not store ephemeral signed URL as the only source of truth if regeneration is possible.

**Warning signs:**
- `error_subcode 2207052` or container status `ERROR`.
- Image URL contains `localhost`, `127.0.0.1`, private IP, query-signed expiry soon, or admin-auth path.
- Scheduled posts fail more than immediate posts.
- Preview works in admin (authenticated) but Meta publish fails.

**Phase to address:**
Phase 1 — Media contract & storage decision. Phase 2 — Publish pipeline must validate/refresh URL just before container creation.

---

### Pitfall 3: Missing/incorrect permissions and IG account linkage assumptions

**What goes wrong:**
Publishing fails with OAuth/permission errors, or works in developer/admin testing but fails for real operational flow. Common causes: missing `instagram_content_publish` / `instagram_basic` / `pages_read_engagement`; app has no Advanced Access/App Review when needed; Instagram account not Business/Creator; IG account not linked to the selected Facebook Page; Page requires PPA; app user lacks required Page task/role; Business Manager role requires `ads_management`/`ads_read` in some cases.

**Why it happens:**
Existing FB integration uses `pages_show_list,pages_manage_posts,pages_read_engagement` (see `meta_oauth.py`). Teams add IG UI but forget to extend OAuth scopes, re-consent flow, and token capability verification. They also assume "connected Facebook Page" implies "publishable Instagram account". Meta's permission names differ across FB Login vs Instagram Login products.

**How to avoid:**
- Use Facebook Login for Business / IG Graph API with Facebook Login consistently with existing system. For this setup, confirm required permissions: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement` (Meta doc, fetched 2026-11-23). If app user role is granted via Business Manager, also assess `ads_management` and `ads_read`.
- At connect/verify time, fetch and persist IG professional account ID: `GET /{page-id}?fields=instagram_business_account{id,username,name}` (or equivalent). Fail clearly if no linked IG professional account.
- Add explicit preflight checks in UI and backend: connected FB page, linked IG account, token valid, required permissions/scopes present. Distinguish "not connected", "needs reconnect/consent", "missing IG account linkage", "missing permission".
- Plan for App Review/Access Level: single-admin own-business use may work in Standard Access; any external app users/tech-provider scenario requires Advanced Access + App Review + Business Verification. Document current assumption in checklist.
- Handle Page Publishing Authorization (PPA) as an operator-facing warning/blocker; Meta cannot be queried reliably for PPA beforehand per docs — surface actionable guidance when publish fails.

**Warning signs:**
- OAuth callback succeeds but publish returns 200/10/190/permissions errors.
- `instagram_business_account` is null for selected Page.
- Scopes requested in `META_OAUTH_SCOPES` do not include IG publish permissions.
- Integration works for app developer but not for target admin account/role.

**Phase to address:**
Phase 1 — OAuth/permissions/linkage foundation. Include migration/reconnect path for existing connected FB accounts.

---

### Pitfall 4: Duplicate Instagram posts from retries, ambiguous outcomes, or double-submit

**What goes wrong:**
The same job is published twice on Instagram. Causes: retrying after timeout/ambiguous response, worker reprocessing after crash, admin double-click/manual retry on an already-published-but-unrecorded post, or creating a new container when old publish may have succeeded. Unlike FB feed post, IG publish has container lifecycle and ambiguous failure modes.

**Why it happens:**
Existing pipeline already knows ambiguous failures (`PublishFailureCategory.ambiguous` -> no auto-retry, manual verification). IG adds more ambiguity: container created but publish response lost; publish returns transient/timeout after Meta accepted; container `PUBLISHED` but local DB not updated. Developers also may "retry" by creating a fresh container+publish, bypassing idempotency.

**How to avoid:**
- Preserve and extend existing idempotency invariants: never republish if `external_post_id` exists or status is `published`. This is already in `process_claimed_post` — keep it for IG.
- Persist container ID immediately after creation. Before creating another container, check existing container status; if `PUBLISHED`, record external media ID and stop.
- Treat `media_publish` timeout/5xx/unknown as ambiguous until proven otherwise. Do not auto-create new container+publish on ambiguous outcome. Require status reconciliation: check container status and/or query media.
- Make manual retry endpoint idempotent and guarded: if post has `external_post_id`, return noop. If last failure was ambiguous, force operator confirmation or automated "check remote status" step before enabling publish retry.
- Add DB/logic uniqueness: one active IG publish record per job/provider (`uq_social_posts_job_provider` exists) — good. Also guard against concurrent workers with claim lock (already exists). Consider unique constraint/index on `external_post_id` per provider where not null.
- UI: disable publish/retry button while request in flight; render server state after refresh.

**Warning signs:**
- Duplicate posts visible on Instagram for same job.
- Retry creates a new container when previous container exists.
- Ambiguous failures converted to auto-retry.
- No stored `ig_container_id`/publish attempt correlation.

**Phase to address:**
Phase 2 — Publish pipeline/idempotency. Phase 3 — Admin retry/status UX. Add explicit tests for timeout-after-publish and duplicate-click.

---

### Pitfall 5: Rate limits and daily publish cap handled too late or globally

**What goes wrong:**
Posts fail with `code 9, subcode 2207042` ("reached maximum number of posts...") or app-level throttling. Batch approve/retry bursts consume the 24h moving-window quota. System retries aggressively, making throttling worse. Admin sees opaque errors and keeps retrying.

**Why it happens:**
EmpregaNoix is low volume now, so limits feel irrelevant. But moving-window caps, retry bursts, tests, or future growth can hit them. Existing FB pipeline has retry/backoff for transient errors but no IG-specific 24h publish cap awareness.

**How to avoid:**
- Query `GET /{ig-user-id}/content_publishing_limit` before publish bursts and/or after 2207042. Expose safe summary in admin diagnostics (no tokens).
- Treat 2207042 as non-retryable-until-window-moves. Do not schedule immediate exponential retry; mark as blocked/rate-limited with clear next action.
- Add per-account publish pacing/queueing. For scheduled posts, spread dispatch; for manual bulk actions, serialize or warn.
- Keep retry backoff jittered and cap attempts (existing `SOCIAL_MAX_ATTEMPTS`/`SOCIAL_RETRY_DELAYS` pattern). Ensure rate-limit errors map to appropriate category — not transient auto-retry storm unless carefully bounded.
- Log/metric rate-limit events with sanitized fields for observability.

**Warning signs:**
- Spikes of 2207042 in logs.
- Worker retries every few minutes on daily-limit error.
- No use of `content_publishing_limit` endpoint.
- Bulk review approvals trigger many simultaneous IG publishes.

**Phase to address:**
Phase 2 — Pipeline error classification/backoff. Phase 3 — Admin status/diagnostics.

---

### Pitfall 6: Token expiry/revocation breaks publish silently or corruptly

**What goes wrong:**
IG publish starts failing after token expiry, password change, permission removal, app deauthorization, or Page role changes. System either keeps retrying uselessly, marks posts as generic permanent failures, or loses clarity about whether reconnect is needed. Because FB and IG share the Meta app/token context in this design, an FB token problem can also block IG.

**Why it happens:**
Current system has `SocialAccountStatus.needs_reconnect`, `debug_token` verification, and transient/definitive classification in `meta_oauth.py` — good foundation. Pitfall is not extending it to IG publish failures and not mapping IG-specific OAuth errors (190, 102, 200, 10, 2207006 permission/token) to reconnect/block states consistently. Long-lived tokens expire (~60 days) and there is no renewal/alert strategy yet (open decision in PROJECT.md).

**How to avoid:**
- Reuse/extend `meta_oauth` verification for IG publish capability: validate token, required scopes/permissions, Page access, IG account linkage.
- Map definitive auth/permission Graph errors during publish to `needs_reconnect` or a clear integration-blocked state; do not auto-retry publish until reconnect.
- Add proactive expiry/health signal: store token debug info checked_at; surface "reconecte em breve" / "reconexão necessária" in Integrations and review UI. If using long-lived tokens, define renewal/alert strategy (cron check + admin banner).
- On reconnect, preserve existing pending social posts safely; define whether drafts/scheduled items remain valid.
- Never log tokens, decrypted secrets, or raw OAuth responses containing tokens.

**Warning signs:**
- Repeated 190/OAuthException errors classified as generic permanent.
- `needs_reconnect` only set by manual verify endpoint, not by publish pipeline.
- No admin-visible token health/expiry warning.
- IG and FB statuses diverge confusingly after reconnect.

**Phase to address:**
Phase 1 — Token/linkage verification model. Phase 2 — Error classification maps auth failures to blocked state. Phase 3 — Admin UX for reconnect/health.

---

### Pitfall 7: UI/status coupling makes Facebook and Instagram block each other

**What goes wrong:**
Adding IG to the review dialog creates a monolithic social flow: one save button, one status badge, one error message, or one "publish social" action that conflates FB and IG. A FB failure prevents IG retry, IG image validation blocks FB draft save, or status list shows ambiguous "Publicado/Falhou" without platform identity. This violates the v1.5 constraint: "falha de um não bloqueia o outro".

**Why it happens:**
Current UI is FB-centric: `EditJobDialog` has one `socialDraft`, one `socialStatus`, labels like "Publicar no Facebook"; `SocialPostStatusItem.provider` is `Literal["facebook"]`; `build_social_status_item` hardcodes Facebook labels/URLs. The simplest implementation extends these fields in-place.

**How to avoid:**
- Model per-platform state in API and UI: separate draft/status/action/error/loading for `facebook` and `instagram`. Shared job approval remains site-first.
- Allow independent actions: save IG draft without touching FB; retry IG without FB; approve site even if one/both social registrations have warnings.
- Make status explicit per platform: provider badge, platform-specific error, timestamps, external ID/permalink when available. Avoid one combined "social status".
- Validate IG-specific prerequisites only for IG publish path (image required, caption length, hashtag warning) — do not block FB text-only publish.
- Keep `ReviewQueue`/status list clear: per-platform chips/rows or expandable detail. Preserve existing FB behavior and tests.

**Warning signs:**
- One `socialAction`/`socialStatus` state drives both platforms in frontend.
- API schema still has `provider: Literal["facebook"]`.
- Retry endpoint/action cannot target IG independently.
- FB regression tests fail after IG UI changes.

**Phase to address:**
Phase 3 — Review UI & status API. Include regression tests for FB-only flow and dual-platform independent outcomes.

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Reuse `social_posts` row/provider=`facebook` logic by adding special cases everywhere | Fewer schema changes now | Brittle conditionals, broken idempotency/status semantics, hard to add future providers | Never; extend schema deliberately with provider-aware fields |
| Store only final `image_url` and discard source/validation metadata | Simpler model | Cannot regenerate expired signed URLs, cannot audit what was published, hard to debug 2207052 | Only MVP if URL is permanent public CDN and documented; prefer storing source + canonical public URL |
| Auto-retry all IG failures with same FB transient policy | Reuses existing backoff code | Duplicate posts on ambiguous publish, wasted attempts on 2207042/auth errors, container spam | Never for ambiguous/auth/daily-limit classes; acceptable only for proven transient classes with safeguards |
| Poll container status synchronously inside HTTP request | Easy to implement | Request timeouts, worker/API coupling, poor UX, duplicate triggers on retries | Only for local spike/debug; never in production request path |
| Hardcode "Facebook" in labels/helpers and add "Instagram" ad hoc | Fast UI delivery | Inconsistent status/retry rules, broken admin mental model, regression risk | Never; make provider-aware status mapping |
| Skip `content_publishing_limit` precheck because volume is low | Less code | Sudden failures during bursts/tests; poor operability | Acceptable for MVP only if 2207042 is classified clearly and surfaced; add precheck before scale/bulk features |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Meta OAuth / Graph permissions | Add IG UI but keep old scopes (`pages_show_list,pages_manage_posts,pages_read_engagement`) and never force re-consent | Add/confirm `instagram_basic`, `instagram_content_publish`, `pages_read_engagement` for FB Login flow; detect missing capabilities and prompt reconnect/consent |
| FB Page -> IG account linkage | Assume selected Page has publishable IG account | Fetch `instagram_business_account` for Page; store `ig_user_id`/username; block IG enablement with actionable message if missing |
| IG media container creation | Pass non-public/expiring/authenticated image URL | Host JPEG on public HTTPS URL reachable by Meta at attempt time; validate format/size/aspect before create |
| Container publish lifecycle | Call `media_publish` immediately, ignore `status_code` | Poll `GET /{ig-container-id}?fields=status_code`; publish only on `FINISHED`; handle `ERROR/EXPIRED/PUBLISHED/IN_PROGRESS` |
| Error handling | Treat all non-200 as transient retryable | Classify by Graph `code/subcode`: 2207042 daily limit (blocked), 2207027 not ready (wait/poll), 2207052 bad URL (fix media), 2207008 temporary (limited retry then recreate), 190/permissions definitive auth (needs reconnect) |
| Rate limits | Only react after publish fails | Use `GET /{ig-user-id}/content_publishing_limit`; pace bulk publishes; back off/jitter on 429/app limits |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Publishing IG inline in approve/review request | Slow approve endpoint, timeouts, duplicate submits on client retry | Keep approve site-first; enqueue/dispatch async IG publish like existing social pipeline | As soon as image processing/polling or Meta latency exceeds request budget |
| Polling container status too aggressively across many posts | Rate-limit pressure, wasted worker cycles | Bounded polling (e.g., 1/min, max ~5-10 checks) with persisted next-check time; stop on terminal states | Dozens of concurrent publishes or retry storms |
| Regenerating/uploading image on every retry attempt | Extra storage, inconsistent media, slower retries | Generate/store canonical public media once per approved content version; reuse URL if still valid | Repeated transient failures/retries |
| Bulk "retry all failed" without pacing | 2207042/429 spikes, noisy failures | Queue with per-account concurrency=1 or small batch + delay; surface daily quota remaining | >10-20 posts in short window, or lower effective quota |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Logging raw Graph responses, access tokens, or signed image URLs with sensitive params | Credential/media URL leakage in logs/Sentry/support bundles | Reuse existing sanitization discipline; log only safe IDs/status codes/subcodes/categories; redact token/query secrets |
| Making image URLs guessable/publicly enumerable with sensitive job data | Unintended disclosure of unpublished/job info, scraping | Use unguessable object keys; separate public media from private admin data; keep captions/job PII policy explicit |
| Accepting arbitrary `image_url` from client without server validation | SSRF-like fetch abuse, hosting malware/non-image content, publishing unintended media | Server generates or strictly validates allowed origins/storage keys; enforce MIME/size/dimensions; never proxy arbitrary URLs to Meta blindly |
| Storing long-lived tokens without clear reconnect/revocation handling | Unauthorized posting window after compromise, broken ops after revocation | Encrypt at rest (existing Fernet pattern), minimal scope, debug_token checks, needs_reconnect flow, documented rotation/reconnect procedure |
| Coupling IG publish capability to overly broad permissions without need | Larger blast radius, harder App Review | Request minimum required permissions for FB Login IG publishing; justify any extra scopes |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| One generic "Social publish failed" message | Admin cannot tell whether FB or IG failed, or what to do | Per-platform status, safe pt-BR error, and actionable next step (reconnect, wait, check Instagram, fix image) |
| Allowing IG toggle without image/preflight | Admin thinks post is scheduled/published; fails later | Inline validation: image required, JPEG/ratio/size checks, caption counter, hashtag warning before save/approve |
| Auto-enabling IG retry after ambiguous publish | Admin creates duplicate Instagram post | Disable auto-retry; show "verifique no Instagram antes de tentar novamente" and require explicit reconciliation/confirmation |
| Hiding linkage/permission problems until publish time | Late failure after content work | Show IG account linkage, permission/connection health, and token status in Integrations and Review panel |
| Preview that doesn't match publish constraints | Surprise cropping/failure/ugly post | Use same aspect ratio/template rules as publish; show 1080x1080 or 1080x1350 preview and safe text area/caption length warnings |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **IG OAuth/connect:** Often missing re-consent for existing FB connections — verify existing connected accounts gain `instagram_content_publish`/`instagram_basic` capabilities or are prompted to reconnect.
- [ ] **IG account linkage:** Often missing stored `ig_user_id` and "no linked IG Business/Creator account" handling — verify Page->IG lookup and clear blocked state.
- [ ] **Image pipeline:** Often missing public reachability/expiry/JPEG/aspect validation — verify Meta-fetchable HTTPS URL, 8MB, 4:5-1.91:1, JPEG only.
- [ ] **Container lifecycle:** Often missing status polling and terminal-state handling — verify `IN_PROGRESS/FINISHED/ERROR/EXPIRED/PUBLISHED` paths and 24h container expiry.
- [ ] **Idempotency:** Often missing ambiguous publish reconciliation — verify timeout after `media_publish` does not create duplicate; retry checks container/external ID first.
- [ ] **Rate limit handling:** Often missing 2207042 classification and quota visibility — verify daily-limit error is non-retry-storming and operator sees safe guidance.
- [ ] **Decoupling:** Often missing independent FB/IG persistence/status/actions — verify FB publish succeeds when IG fails and vice versa.
- [ ] **Observability:** Often missing sanitized structured logs/metrics — verify logs include provider/job/container/status/error code class but never tokens/raw secrets.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Duplicate IG post published | MEDIUM | Mark local record with confirmed external media ID; hide/disable retry; document manual deletion in Instagram if needed; add reconciliation check before future retries. |
| Container expired before publish | LOW | Create new container from still-valid public image URL; restart publish flow; if image URL expired, regenerate URL first. |
| Ambiguous publish (timeout/unknown) | MEDIUM | Query container `status_code`; if `PUBLISHED` or media exists, persist external ID and mark published; if `FINISHED`, publish once carefully; if `ERROR/EXPIRED`, create new container only after confirming no media was published. |
| Token expired/revoked | LOW | Set integration `needs_reconnect`; prompt admin reconnect; after reconnect, re-run preflight and allow manual retry of blocked/failed posts. |
| Image URL not fetchable | LOW | Fix storage/public URL/content-type; regenerate image URL; validate externally; retry with new container. |
| Daily publish limit reached (2207042) | LOW | Pause IG dispatch for account; show next retry/window guidance; query `content_publishing_limit`; resume after window moves. |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| IG treated as single-step FB publish | Phase 1: IG data model & publisher contract | Unit/integration tests cover container create -> poll -> publish; no direct single-call IG publish path |
| Public image URL/fetchability | Phase 1: Media strategy/storage; Phase 2: publish preflight | Validation rejects private/expired/non-JPEG/bad-ratio media; staging test confirms Meta-fetchable URL |
| Permissions/linkage/PPA gaps | Phase 1: OAuth scopes, Page->IG lookup, reconnect | Connect flow stores `ig_user_id`; missing linkage/permission produces actionable blocked state; reconnect upgrades existing FB connection |
| Duplicate posts/idempotency | Phase 2: Pipeline/idempotency/reconciliation | Tests simulate timeout after publish, duplicate retry click, worker crash recovery; DB ends with one external post ID |
| Rate/daily limit mishandling | Phase 2: Error classification & pacing; Phase 3: admin messaging | 2207042 mapped to blocked/non-storming; `content_publishing_limit` visible/queried; bulk publish paced |
| Token expiry/revocation | Phase 1: verification model; Phase 2: publish-time classification; Phase 3: UX alerts | Auth errors set `needs_reconnect`; admin sees reconnect CTA; posts not auto-retried endlessly |
| FB/IG UI-status coupling | Phase 3: Review/status UI/API | FB-only publish unaffected; IG failure leaves FB published; per-platform status/actions/errors render independently |
| Observability/security leaks | All phases (cross-cutting) | Log audit finds no tokens/secrets; structured logs include provider, job_id, post_id, container_id, status, error class/code |

## Sources

- Meta Content Publishing guide (official, fetched 2026-11-23): https://developers.facebook.com/docs/instagram-platform/content-publishing — confirms 2-step container/publish flow, public media URL requirement, PPA note, FB Login permissions (`instagram_basic`, `instagram_content_publish`, `pages_read_engagement`), 100 posts/24h moving period, `content_publishing_limit`, container status codes, 5-min/1-min polling recommendation, containers expire in 24h.
- Meta Instagram Platform error codes (official, fetched 2026-11-23): https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/error-codes — confirms 2207042 daily limit, 2207027 not ready, 2207052 media fetch failure, 2207008 temporary/expired builder, 2207020 expired media, 2207004/2207005/2207009/2207010 media/caption validation, 2207050 restricted account.
- Meta App Review / permissions overview (official, fetched 2026-11-23): https://developers.facebook.com/docs/instagram-platform/app-review and https://developers.facebook.com/docs/instagram-platform/overview — confirms Standard vs Advanced Access, App Review scenarios, FB Login vs Instagram Login permission sets.
- EmpregaNoix codebase (HIGH confidence, inspected 2026-11-23): `backend/app/services/social/publish_pipeline.py`, `facebook.py`, `publisher.py`, `meta_oauth.py`, `crud/social_posts.py`, `models/social_post.py`, `models/social_account.py`, `schemas/social_posts.py`, `frontend/app/admin/review/EditJobDialog.tsx`, `frontend/app/admin/integracoes/IntegrationsClient.tsx`.
- Project context (HIGH confidence): `.planning/PROJECT.md` — v1.5 scope/constraints/decisions em aberto.

**Confidence notes / assumptions to validate in implementation planning:**
- **MEDIUM:** The official Content Publishing doc contains an internal inconsistency in carousel limitations ("50 published posts within a 24-hour period") versus Rate Limit section ("100 API-published posts within a 24-hour moving period"). Plan against `content_publishing_limit` endpoint and 100/24h rule, but handle 2207042 defensively. 
- **MEDIUM:** App Review/Advanced Access requirements depend on whether app serves only owned/managed business assets (Standard may suffice) or other users/businesses (Advanced required). EmpregaNoix is single-master; confirm in Meta App Dashboard before launch.
- **MEDIUM:** Exact PPA detectability is limited; docs state no reliable way to determine in advance. Design UX for clear remediation on failure.
- **HIGH:** IG image must be publicly accessible at attempt time, JPEG-only, 8MB, 4:5-1.91:1, container lifecycle and error subcodes as documented above.

---
*Pitfalls research for: EmpregaNoix v1.5 — Instagram Graph API Content Publishing added to existing Facebook Pages integration*
*Researched: 2026-11-23*