# Feature Research

**Domain:** Instagram job-post publishing integration in admin review (EmpregaNoix v1.5 subsequent milestone)
**Researched:** 2026-11-23
**Confidence:** MEDIUM-HIGH (Meta constraints verified via official docs; UX patterns from existing codebase + common admin publishing workflows; some product-pattern confidence is MEDIUM)

## Scope

This research covers **only** the new v1.5 capability: publishing approved jobs to Instagram from the review stage, alongside the existing Facebook flow. It assumes existing v1.2/v1.4 foundations remain: Meta OAuth/connect, selected Facebook Page, admin review queue/dialog, social draft generation/save, async publish worker/retry/idempotency primitives, per-job social status, and secure token storage.

**Out of scope (explicit):** Stories/Reels/carousel, scheduling, analytics/insights, comment/DM handling, multiple Instagram accounts, auto-sync edits/deletes to published social posts.

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = the Instagram integration feels incomplete, unsafe, or unusable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Instagram section in review, alongside Facebook** | Admin already reviews Facebook draft in `EditJobDialog`; adding another platform in a different place would fragment the approval workflow. | MEDIUM | Extend existing review dialog/status surfaces; do not fork a separate Instagram-only review page. Keep platform sections visually distinct but in same job review context. Depends on existing review UI (`ReviewQueue`, `EditJobDialog`, `ReviewRow`). |
| **Per-vaga Instagram toggle (opt-in/out per job)** | Not every approved job should be posted everywhere; admins expect control before publish. | LOW | Toggle state must be explicit and persisted (or clearly derived) before approval/publish. Default should be conservative (off or remembered policy) — decide in discuss-phase, but UX must show state unambiguously. |
| **Editable caption prefilled from job data** | Facebook flow already has generate/edit/save draft; Instagram expects same editorial control with platform-specific copy. | MEDIUM | Prefill from structured job fields (title/company/city/salary/benefits) and job public link context, but caption must follow Instagram constraints. Reuse generation pattern carefully; do not blindly reuse Facebook 700-char/link-at-end draft. |
| **2200-character caption counter** | Instagram caption limit is 2200 chars; admin needs immediate feedback before publish fails. | LOW | Show `current/2200` counter near caption textarea. Count actual caption text that will be sent. Block/disable publish action when over limit with clear pt-BR message. |
| **>30 hashtags warning** | Instagram allows max 30 hashtags per caption; exceeding causes publish failure/rejection. | LOW | Warning at >30 (and ideally helper at 25+). Count `#tokens` robustly. Warning is table stakes because hashtag-heavy job posts are common. Do not silently trim hashtags. |
| **No-clickable-link handling + "link na bio" CTA** | Instagram captions do not render clickable URLs; posting raw URL as primary CTA creates false expectation. | LOW | UI copy/helper text must state links are not clickable. Prefilled caption should include CTA like "Link na bio" / "Veja o link na bio" when appropriate; optionally include URL as plain text for copyability, but do not present it as clickable CTA. |
| **Image required guardrail** | Instagram Content Publishing requires media; image container requires `image_url`. No image = cannot publish. | MEDIUM | Block Instagram publish when image missing/invalid. Show clear state: "Imagem obrigatória para publicar no Instagram". This is a hard platform constraint, not a nice-to-have validation. |
| **Image preview before publish** | Admin must see what will be posted; image is mandatory and often generated. | MEDIUM | Preview the exact image that will be sent (or a faithful render) with aspect ratio/context. For generated card, preview after generation; for upload/logo, preview selected asset. |
| **Per-platform publish status (Facebook vs Instagram independent)** | Existing UI has single social status; with two platforms, combined status becomes ambiguous and dangerous. | MEDIUM | Each platform needs its own status badge/state: none/draft/scheduled-if-ever/publishing/published/failed/cancelled-equivalent as applicable. A Facebook failure must not mark Instagram failed, and vice versa. `ReviewRow` badge and dialog status panel must become platform-aware. |
| **Independent publish execution** | User decision: failure of one platform must not block the other. | HIGH | Separate publish records/jobs per provider. Pipeline/worker must claim/process/retry independently. Shared Meta token/account issues should be surfaced per platform with clear reason, but execution path remains isolated. |
| **Visible publish outcome with permalink/external ID** | Admin needs confirmation where post landed; existing Facebook status exposes published state/URL behavior. | MEDIUM | Store and show Instagram permalink when available (via media permalink field after publish/lookup) and external media/post ID. If permalink unavailable, show "Publicado no Instagram. Link indisponível" with ID-safe fallback — same honesty pattern as Facebook. |
| **Error visibility and retry** | Async publish can fail (token, media URL fetch, rate limit, container error). Admin needs actionable recovery. | MEDIUM | Show last safe error, attempt count/timestamps where useful, and retry only when eligible. Distinguish reconnect-needed, transient retryable, rate-limited/wait, ambiguous/manual-check, and permanent validation/content errors. |
| **Persist audit trail for Instagram publish** | Existing social tables/logs provide traceability; Instagram must meet same operational bar. | MEDIUM | Persist caption used, image source/reference, post/container IDs, permalink, status, last_error, timestamps, attempts/retry metadata. Reuse/extend `social_posts`/`social_post_logs` patterns; keep logs token-free. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Generated job card fallback (1080x1080 or 1080x1350 JPEG)** | Removes "I don't have an image" blocker; keeps publishing fast for one-person admin workflow. | HIGH | Milestone requires fallback generated card served by public URL accessible to Meta. Needs deterministic template, storage/serving, and cleanup/expiry policy. Good differentiator because it makes Instagram publish as fast as paste-review-approve. |
| **Caption prefill tuned for Instagram job posts** | Better than generic copy: short hook, role/company/city/salary/benefits, CTA "link na bio", relevant hashtags, no fake clickable link. | MEDIUM | Different from Facebook: Instagram favors concise scannable caption + hashtags; Facebook already targets ~700 chars. Keep tone professional/acolhedor pt-BR, but optimize for IG reading behavior. |
| **Hashtag quality assist (count + suggestions, not auto-spam)** | Prevents over-limit and low-quality hashtag stuffing while keeping speed. | LOW | Show count and optional suggested hashtags from city/role; admin can edit/remove. Avoid auto-adding 30 hashtags. |
| **Pre-publish validation summary** | Catches avoidable failures before async worker: missing image, bad aspect ratio, over char/hashtag limit, missing IG account linkage. | MEDIUM | Inline checklist/status near publish controls: "Legenda OK", "Imagem OK", "Conta Instagram pronta". Saves retry cycles and Meta API quota. |
| **Safe retry with ambiguity guard** | Prevents duplicate Instagram posts when publish result is ambiguous — critical trust feature. | MEDIUM | Existing pipeline already has ambiguity concept (`ambiguous`/no auto-retry). Extend to Instagram container publish flow: if create/publish response uncertain, require manual check before retry. |
| **Image source provenance** | Helps admin understand what image was used (uploaded, generated card, logo) and reproduce/fix issues. | LOW | Store simple provenance metadata (source type, asset ID/path/template version). Useful for audits/debugging; no heavy DAM needed. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Auto-publish Instagram on job approval by default** | "One click does everything." | Risky when image/caption/account may be unready; Instagram has stricter media constraints than Facebook text posts. Can create failed/low-quality posts. | Per-vaga toggle + explicit review state. If auto-publish ever added later, gate on all validations passing. |
| **Reusing Facebook caption unchanged** | Seems efficient; one draft for all platforms. | Facebook draft may include clickable-style link CTA, different length target (~700), fewer hashtags, and formatting assumptions. Instagram needs "link na bio" and has different constraints. | Separate Instagram caption field prefilled from job data, optionally "Copy from Facebook" action. |
| **Posting external URL directly in caption as primary CTA** | URL is easy to include. | Instagram captions are not clickable; users can't tap through. Creates friction and confusion. | CTA "link na bio"; keep canonical job URL in profile/site flow. If URL included, treat as plain text secondary info. |
| **Stories/Reels/carousel/video in same milestone** | "Instagram means all formats." | Different media specs, containers, UX, and failure modes; explodes scope. Current need is feed image post for job card. | Single-image feed post only. Document others as out of scope. |
| **Scheduling UI for Instagram** | Facebook has schedule/publish-now concepts; parity feels nice. | Milestone explicitly out of scope; adds time zone, queue, edit-after-schedule, and worker complexity. | Publish-now only (or inherit only if already trivial, but do not add new scheduling product surface). Keep schema extensible only if cheap. |
| **In-app Instagram analytics/comments/DM inbox** | Feels like "complete social management". | Large API/scope/permissions surface; not core to job discovery. | Store permalink and publish status only; use native Instagram/Meta tools for engagement. |
| **Multiple Instagram accounts / account picker** | Agencies want it. | Conflicts with single-admin, single-page operating model and adds token/page/account selection complexity. | One IG business/creator account linked to selected Facebook Page. |
| **Silent image auto-crop without preview** | Makes uploads "just work". | Can cut off job title/salary/CTA in generated/uploaded image; damages trust. | Enforce supported aspect ratios/templates (4:5 or 1:1), preview final render, reject or require adjustment when unsafe. |
| **Auto-retry ambiguous publishes aggressively** | Retries feel resilient. | Instagram container/publish ambiguity can create duplicate posts; duplicates are painful to clean up manually. | Mark ambiguous, block auto-retry, require admin check/permalink confirmation before manual retry. |

## Feature Dependencies

```
[Existing Meta OAuth + connected Facebook Page]
    └──requires──> [Instagram-capable account discovery]
                       └──requires──> [IG User ID resolution/storage]
                                          └──requires──> [Instagram publish capability]

[Existing Review Dialog + Social Draft pattern]
    └──requires──> [Instagram section in review]
                       ├──requires──> [Instagram caption draft model/UI]
                       ├──requires──> [Image asset selection/generation/preview]
                       └──requires──> [Per-platform validation]

[Image public URL accessible by Meta]
    └──requires──> [Generated card storage/serving OR uploaded asset hosting]
                       └──requires──> [Instagram container creation (image_url)]

[Instagram container creation]
    └──requires──> [Container status check when needed]
                       └──requires──> [media_publish]
                                          └──requires──> [Permalink/ID capture + status persist]

[Existing async worker/retry/idempotency pattern]
    └──enhances──> [Instagram independent publish pipeline]
                       └──requires──> [Provider-aware social_posts/social_post_logs]

[Per-platform status model]
    └──requires──> [ReviewRow badge + EditJobDialog status panels per provider]

[Facebook publish flow] ──must remain independent of──> [Instagram publish flow]
[Clickable link CTA] ──conflicts with──> [Instagram caption UX]
[Ambiguous publish auto-retry] ──conflicts with──> [Duplicate-post safety]
```

### Dependency Notes

- **Instagram section requires existing review flow:** `frontend/app/admin/review/ReviewQueue.tsx`, `ReviewRow.tsx`, and `EditJobDialog.tsx` already own review UX. Instagram should extend these surfaces, not create a parallel review system.
- **IG publish requires IG User ID from connected Page:** Meta Content Publishing publishes against IG user/media objects. v1.5 must obtain/store the professional IG account linked to the selected Facebook Page while reusing existing token lifecycle.
- **Image preview/publish requires public URL:** Meta fetches `image_url` from a public server. Local-only paths, auth-protected URLs, or expiring/private blobs will fail. Generated/uploaded assets need a stable public URL strategy.
- **Independent publish requires provider-aware persistence:** current `social_posts` is effectively one record per job/provider concept; schema already has `provider` and unique `(job_id, provider)`. v1.5 should extend this pattern, not overload a single Facebook row with Instagram fields.
- **Per-platform status requires API/UI contract changes:** `getSocialStatus`, `SocialPostStatusItem`, and review badges are Facebook-shaped (`provider: "facebook"`, single status). v1.5 needs platform-specific or multi-provider status responses.
- **Facebook flow must remain independent:** approval/site publish remains source of truth; social publishing for each platform is best-effort/async and isolated. Regression protection is a table stake.

## MVP Definition

### Launch With (v1)

Minimum viable for v1.5 — what's needed to validate "approved job can also be published to Instagram safely".

- [ ] **Instagram review section with per-vaga toggle** — admin can decide per job; no hidden auto-posting.
- [ ] **Editable Instagram caption prefilled from job data** — fast workflow, admin control preserved.
- [ ] **Caption constraints UX: 2200 counter + 30-hashtag warning + no-clickable-link CTA** — prevents common platform-specific failures and misleading copy.
- [ ] **Mandatory image with preview** — satisfies IG Content Publishing requirement; admin sees final media.
- [ ] **Generated fallback card (1080x1080 or 1080x1350 JPEG, public URL)** — ensures image is always possible even without logo/upload. Origin can remain open, but fallback must exist.
- [ ] **IG account linkage using existing Meta connection** — resolve/store IG user ID from linked Page; block with actionable state if unavailable.
- [ ] **Async independent publish pipeline** — separate provider execution/retry/idempotency; Facebook unaffected.
- [ ] **Per-platform status, error, retry, permalink/ID persistence** — admin can trust what happened on each platform.

### Add After Validation (v1.x)

- [ ] **Image source options beyond fallback (logo/upload)** — add when template quality or branding needs are confirmed; requires asset management/validation.
- [ ] **"Copy from Facebook" / "Regenerate Instagram caption" actions** — convenience after base flow is stable.
- [ ] **Better preflight diagnostics** — aspect-ratio checker, hashtag parser details, token expiry warning banner, rate-limit countdown.

### Future Consideration (v2+)

- [ ] **Scheduling** — explicitly out of scope for v1.5; adds queue/time UX complexity.
- [ ] **Stories/Reels/carousel/multi-image** — different media products and review UX.
- [ ] **Analytics/engagement sync** — requires extra permissions, storage, and product surface.
- [ ] **Multi-account / multi-page Instagram selection** — conflicts with current single-admin/simple model.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Per-platform independent status model | HIGH | HIGH | P1 |
| Instagram section in review + per-vaga toggle | HIGH | MEDIUM | P1 |
| Editable caption + prefill | HIGH | MEDIUM | P1 |
| 2200 char counter + 30 hashtag warning + link-na-bio helper | HIGH | LOW | P1 |
| Mandatory image validation + preview | HIGH | MEDIUM | P1 |
| Generated fallback card + public hosting | HIGH | HIGH | P1 |
| IG user ID resolution/storage from linked Page | HIGH | MEDIUM | P1 |
| Async publish + retry/idempotency + ambiguity guard | HIGH | HIGH | P1 |
| Permalink/external ID/timestamps/error persistence | HIGH | MEDIUM | P1 |
| Image upload/logo source options | MEDIUM | HIGH | P2 |
| Caption quality helpers/suggestions | MEDIUM | LOW | P2 |
| Rate-limit countdown UI | MEDIUM | MEDIUM | P2 |
| Scheduling/Stories/Reels/analytics | LOW (for this milestone) | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Detailed Expectations

### Caption Review ("done" looks like)

- Admin sees an **Instagram caption** field in review, separate from Facebook text.
- Field is **prefilled** from job data when empty/generated; admin can edit freely before publish.
- UI shows **live `N/2200` character count**; at >2200, publish is blocked and error is specific.
- UI shows **hashtag count warning when >30**; warning is visible before publish, not only after API error.
- Helper copy makes clear: **Instagram caption links are not clickable**; CTA should direct to "link na bio" (or equivalent). Any URL shown is plain text, not a primary clickable CTA expectation.
- Caption used for publish is the **saved/approved Instagram draft caption**; persisted for audit/debug.
- Empty caption or invalid caption state prevents Instagram publish but should not corrupt Facebook draft.

### Image Handling ("done" looks like)

- Instagram publish cannot proceed without an image.
- Admin can see **image preview** for the exact asset intended for publish.
- v1.5 has at least one reliable path: **generated fallback card** (1080x1080 or 1080x1350, JPEG) rendered from job data and served by a **public URL accessible by Meta**.
- Image validation covers platform basics before send: JPEG/acceptable format, accessible public URL, supported aspect ratio (4:5 to 1.91:1 for feed image), and file size guard (8MB max).
- Image origin/provenance is recorded (generated/upload/logo/template) for debugging.
- If image hosting/URL is temporary, it must remain accessible long enough for Meta fetch/container processing; do not use auth-gated or localhost URLs.

### Publish Status ("done" looks like)

- Review row and review dialog show **Instagram status independently** from Facebook.
- Status model covers at least: not configured/not enabled/no draft, draft/ready, publishing, published, failed, blocked-needs-action (e.g., reconnect/rate limit/manual check).
- Published state shows **published timestamp** and **permalink** when available; otherwise external ID and honest fallback message.
- Failed state shows **safe, actionable error** (pt-BR), no raw tokens/secrets/provider dumps.
- `publishing` is visually in-progress and not retryable.
- Status refresh after retry/publish reflects latest persisted state; no stale "published" or "failed" badge after action.

### Error Recovery ("done" looks like)

- **Transient errors** (network/5xx/temporary) use bounded retry/backoff and surface "nova tentativa automática" when applicable.
- **Rate limit / daily limit reached** is surfaced clearly; auto-retry waits for window or blocks with explicit next-eligible timing/message. Do not hammer API.
- **Token/permission/account linkage errors** become blocked/reconnect-needed with CTA to Integrations; no silent failure.
- **Media/container errors** (bad image URL, fetch failed, invalid aspect ratio, processing error) are shown as actionable content/media errors.
- **Ambiguous publish outcome** (timeout after publish call, uncertain container/publish state) is marked for manual verification; no automatic duplicate retry.
- Retry action is idempotent and disabled when not eligible. Manual retry creates/uses safe path that checks existing external ID/permalink before republishing.

## Competitor Feature Analysis

| Feature | Common Job/Social Admin Tools | Existing EmpregaNoix Facebook Flow | Our Approach (v1.5) |
|---------|-------------------------------|------------------------------------|---------------------|
| Multi-platform review | Separate tabs/platform cards with per-network status | Single Facebook draft/status in review dialog | Add Instagram as parallel section in same review dialog; keep per-platform status independent. |
| Caption editing | Editable per-platform caption with counters/warnings | Editable Facebook text, ~700 char guidance | Instagram-specific caption editor: 2200 counter, 30-hashtag warning, "link na bio" CTA guidance. |
| Media handling | Upload/library + preview; required for IG | Facebook flow is text/link oriented | Make image mandatory for Instagram; provide generated fallback card + preview + public URL. |
| Publish status | Per-network badges, timestamps, link to post | `SocialPostStatusItem` for Facebook | Extend status model to provider-aware/per-platform items with permalink/ID/error/retry state. |
| Error recovery | Retry, reconnect, rate-limit messaging | Retry/backoff/idempotency/blocked reasons exist | Reuse pattern, add Instagram-specific media/rate-limit/ambiguity handling and duplicate-post safety. |

## Sources

- [Meta - Instagram Platform Content Publishing](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/content-publishing) — HIGH, official docs fetched 2026-11-23. Confirms image/video container + publish flow, public media hosting, rate limit (100 API-published posts/24h), container publish troubleshooting.
- [Meta - IG User Media endpoint](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media) — HIGH, official docs fetched 2026-11-23. Confirms image specs (JPEG, 8MB, 4:5-1.91:1, 320-1440 width), caption limits (2200 chars, 30 hashtags, 20 @tags), required permissions, alt_text, container creation fields, status/error behavior.
- [Meta - IG Container endpoint](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-container) — MEDIUM, referenced by docs; should be rechecked during implementation for `status_code` polling semantics. 
- Existing codebase patterns (HIGH for project fit): `frontend/app/admin/review/EditJobDialog.tsx`, `frontend/app/admin/review/ReviewQueue.tsx`, `frontend/components/admin/ReviewRow.tsx`, `frontend/app/admin/social-posts/SocialPostsClient.tsx`, `backend/app/models/social_post.py`, `backend/app/schemas/social_posts.py`, `backend/app/crud/social_posts.py`, `backend/app/services/social/publish_pipeline.py`, `backend/app/services/social/types.py`.
- Project constraints: `.planning/PROJECT.md` v1.5 scope/guardrails.

---
*Feature research for: EmpregaNoix v1.5 Instagram publishing integration in review stage*
*Researched: 2026-11-23*