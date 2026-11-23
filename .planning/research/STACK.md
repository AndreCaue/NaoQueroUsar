# Stack Research — Instagram Publishing (v1.5)

**Project:** EmpregaNoix  
**Researched:** 2026-11-23  
**Scope:** Subsequent milestone additions only — Instagram publishing in review stage, reusing existing Meta/Facebook foundation  
**Overall confidence:** HIGH for Meta API shape/constraints (official docs verified), HIGH for Pillow/serving patterns, MEDIUM for rate-limit numbers due Meta doc inconsistency (mitigated by runtime endpoint)

---

## Executive Summary

Instagram publishing fits the existing stack with **minimal additions**: keep FastAPI + SQLAlchemy async + Postgres + httpx + existing worker/cron/idempotency patterns, add **Pillow** for deterministic 1080x1080/1080x1350 JPEG card generation, and serve generated images through a **public backend URL** that Meta can cURL. Do **not** add a new queue, object-storage SDK, image CDN, or separate media service for v1.5.

The main integration work is not new infrastructure; it is extending the existing Facebook/Meta social foundation: add Instagram scopes/permissions, resolve/store the Instagram professional account ID (`ig-user-id`) from the linked Facebook Page, add an Instagram publisher that implements the existing `SocialPublisher`-style result contract, and generalize the social draft/status/pipeline so Facebook and Instagram are independent per-platform records with shared operational safeguards.

**Key Meta facts verified against official docs (2026-11-23):** Graph API latest is **v27.0** (changelog), while project config currently pins `META_GRAPH_VERSION=v21.0` (valid until 2027-01-21). Instagram Content Publishing for Facebook Login uses `graph.facebook.com`, Page access token, and permissions `instagram_basic`, `instagram_content_publish`, `pages_read_engagement` (plus BM-role ads permissions in some cases). Image containers require a **publicly accessible JPEG URL**; creation is `POST /{ig-user-id}/media`, publish is `POST /{ig-user-id}/media_publish`, status is `GET /{ig-container-id}?fields=status_code`.

---

## Recommended Stack Additions

### Core Technologies (No Change)

| Technology | Current | Purpose | Instagram Impact | Confidence |
|------------|---------|---------|------------------|------------|
| FastAPI | 0.143.0 | Backend API/worker endpoints | Reuse; add public image-serving endpoint and Instagram admin endpoints | HIGH |
| SQLAlchemy async + asyncpg | 2.1.4 / 0.32.0 | Persistence | Reuse; add small schema fields/tables for IG account id, image asset, per-platform post metadata | HIGH |
| httpx | 0.28.1 | HTTP client | Reuse for Graph API container/publish/status/limit calls; no new client | HIGH |
| APScheduler/existing cron worker | 3.10.4 / cron secret endpoint | Async publish | Reuse existing claim/lock/retry/idempotency pipeline; add Instagram provider handling | HIGH |
| Next.js 16 + React 19 + Tailwind 4 | existing | Admin review UI | Reuse; extend EditJobDialog/review status UI with Instagram section | HIGH |
| Neon Postgres | managed | DB | Reuse; acceptable for small JPEG bytea/blob metadata in v1.5 | HIGH |

### Supporting Libraries (New)

| Library | Version | Purpose | When to Use | Why | Confidence |
|---------|---------|---------|-------------|-----|------------|
| Pillow | `13.0.0` | Generate fallback job card image (1080x1080 or 1080x1350 JPEG) | When Instagram post has no selected/uploaded image source and fallback card is required | Standard Python imaging lib; pure backend generation; supports JPEG, drawing, text, RGB conversion. Current PyPI release 2026-10-16. | HIGH |
| python-multipart | `>=0.0.22,<1.0` | Parse multipart/form-data image uploads in FastAPI | Only if v1.5 review flow supports admin image upload | FastAPI form/file upload dependency; small, explicit. Do **not** add if image source is logo/card-generated only. | MEDIUM |

### Development Tools / Assets (New)

| Tool/Asset | Purpose | Notes | Confidence |
|------------|---------|-------|------------|
| Bundled OSS font files (`.ttf/.otf`) in backend assets | Deterministic card rendering with Pillow | Use a permissively licensed font (e.g., Noto Sans / Inter / DejaVu Sans). Do not rely on OS fonts in Railway/Render. Store under `backend/app/assets/fonts/` and load by path. | HIGH |
| Meta Graph API Explorer / Access Token Debugger (manual) | Manual checklist and permission/token validation | Operational tooling, not runtime dependency. Document in checklist. | HIGH |

## Installation

```bash
# Backend (pyproject.toml / uv)
uv add "Pillow==13.0.0"

# Only if review-stage image upload is chosen:
uv add "python-multipart>=0.0.22,<1.0"
```

```toml
# backend/pyproject.toml additions
dependencies = [
  # existing...
  "Pillow==13.0.0",
  # "python-multipart>=0.0.22,<1.0",  # only for upload flow
]
```

**No frontend package additions required** for the core Instagram review/publish flow. Use existing React/Tailwind components and browser APIs for character/hashtag counting and image preview.

---

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| Image generation | Pillow 13.0.0 | Playwright/HTML-to-image screenshot, Weasyprint, ImageMagick | Use browser rendering only if card design becomes too complex for Pillow. Avoid for v1.5: heavier runtime, fonts/browser deps, slower in worker. |
| Public image hosting for Meta fetch | Backend public endpoint serving DB-stored JPEG bytes | S3/R2/Supabase Storage/Cloudinary public object URL | Use object storage when image volume/traffic grows, or when backend public serving becomes operationally limiting. Not needed for 100-500 jobs/month. |
| Image persistence | Postgres `bytea`/metadata table with unguessable token | Filesystem on container disk | Use filesystem only with persistent volume. Avoid ephemeral disk on Railway/Render because Meta may fetch after restart/redeploy. |
| Instagram API client | Direct httpx calls following existing FacebookPublisher pattern | Third-party Meta/Instagram SDK wrapper | Use SDK only if it is actively maintained and covers Content Publishing clearly. Avoid now: extra dependency, abstraction mismatch with existing explicit Graph error handling. |
| Graph API version | Keep `META_GRAPH_VERSION` config-driven; current project default `v21.0`, latest verified `v27.0` | Hardcode v27.0 | Only hardcode after deliberate upgrade/test. Config-driven is safer and matches existing pattern. |
| Instagram account linkage | Store `ig_user_id` (instagram_business_account id) on social account/metadata at connect/verify time | Resolve ig-user-id on every publish | On-demand lookup is acceptable fallback, but storing reduces publish latency and failure modes. Refresh on reconnect/verify. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| New queue/broker (Celery, Redis, BullMQ, SQS) | Overkill for existing single-admin, low-volume, already-working worker/cron with claim/lock/retry/idempotency | Extend existing `publish_pipeline` / worker / cron pattern with provider-aware processing |
| New object-storage service/SDK by default | Adds infra, credentials, failure modes, and unnecessary cost/complexity for small JPEG cards | DB-backed public image endpoint first; revisit object storage only if needed |
| Frontend-only generated image data URLs/base64 for Meta | Meta fetches `image_url` from a public server; data URLs are not publishable URLs | Persist JPEG server-side and expose stable public HTTPS URL |
| Localhost/ephemeral file URLs in production | Meta cannot fetch localhost; ephemeral disk may lose files before container fetch/publish | Public backend URL backed by persistent DB/object storage |
| Separate Meta app/token system for Instagram | Product constraint: reuse existing Meta/Facebook integration | Reuse existing app, encrypted token storage, OAuth/connect flow, env vars |
| Generic "social media scheduler" libraries | They hide Graph API behavior, idempotency, and error taxonomy needed for safe retries | Explicit provider publishers with existing `PublishResult` categories |
| Storing raw Graph error payloads/tokens in logs | Security/privacy risk; tokens/secrets must never leak | Existing sanitized logging pattern and safe error messages |

---

## Stack Patterns by Variant

**If image source is "generated card from job data" (recommended default):**
- Use Pillow to render 1080x1080 (1:1) or 1080x1350 (4:5) JPEG, sRGB, <8MB.
- Store generated bytes + metadata in Postgres; expose public fetch URL.
- Because it has no external asset dependency and is deterministic/retry-safe.

**If image source is "admin upload in review":**
- Add `python-multipart`, validate MIME (`image/jpeg`, optionally accept PNG then normalize to JPEG), dimensions/aspect ratio, and max size.
- Normalize to JPEG sRGB before storing/serving.
- Because Meta image container supports JPEG; normalizing avoids runtime publish failures.

**If image source is "company logo":**
- Treat logo as an asset input, not final publish image unless it already meets IG image rules.
- Compose logo into a generated branded card via Pillow.
- Because logos often have transparent PNG, wrong aspect ratio, or small dimensions.

**If backend is not publicly reachable by Meta (local dev):**
- Use a tunnel/public dev URL only for manual end-to-end IG publish tests.
- Keep unit/integration tests fully mocked.
- Because Meta must cURL `image_url`; localhost is not reachable from Meta.

---

## Version Compatibility

| Package/API | Compatible With | Notes |
|-------------|-----------------|-------|
| `Pillow==13.0.0` | Python >=3.11 (project uses 3.11+) | Current PyPI release verified 2026-10-16. Use `Image.new("RGB", ...)`, `ImageDraw`, `ImageFont.truetype`; save JPEG with `quality`, `optimize=True`, `progressive=False` as needed. |
| Meta Graph API `v27.0` | Instagram Graph API Content Publishing | Latest per Graph API changelog (2026-11-04). Project currently configured as `v21.0`; keep config-driven and test before bump. |
| Facebook Login Page access token | Instagram Content Publishing (Facebook Login flow) | Official docs: Facebook Login can publish using Page access token on `graph.facebook.com`; app user must have required tasks/roles on Page. |
| `httpx==0.28.1` | Existing FacebookPublisher/pipeline | Reuse same timeout/error taxonomy style; add explicit handling for IG container status and rate-limit responses. |

---

## Meta Graph API / Permissions / Limits (Verified)

### Verified endpoints and flow (Facebook Login / existing app shape)

| Step | Endpoint | Purpose | Notes |
|------|----------|---------|-------|
| Resolve IG user id | `GET /{page-id}?fields=instagram_business_account&access_token={page_access-token}` | Obtain `ig-user-id` linked to selected FB Page | Official Page/IG docs. Requires Page token and permissions; store resulting `instagram_business_account.id`. |
| Create image container | `POST /{ig-user-id}/media` | Create IG media container | Params: `image_url` (required, public HTTPS), `caption` optional, `access_token`. Returns container `id`. For Facebook Login use `graph.facebook.com/{META_GRAPH_VERSION}`. |
| Check container status | `GET /{ig-container-id}?fields=status_code` | Confirm readiness before publish when needed | Status: `EXPIRED`, `ERROR`, `FINISHED`, `IN_PROGRESS`, `PUBLISHED`. Poll ~1/min, max ~5 min for async cases; images often finish quickly but code must handle `IN_PROGRESS`. |
| Publish container | `POST /{ig-user-id}/media_publish` | Publish container | Params: `creation_id`, `access_token`. Returns published media `id`. |
| Read publish limit | `GET /{ig-user-id}/content_publishing_limit?fields=quota_usage,config` | Observe account quota | Use live values; do not hardcode 25/50/100. |
| Optional permalink/status enrichment | `GET /{ig-media-id}?fields=id,permalink,timestamp` | Persist permalink/metadata | Only request needed fields; handle missing permalink gracefully. |

### Permissions / App Review assumptions

| Permission | Needed | Why | Confidence |
|------------|--------|-----|------------|
| `instagram_basic` | Yes | Read IG business account linkage and basic IG account/media access required by IG publishing flow | HIGH (official docs) |
| `instagram_content_publish` | Yes | Create/publish IG containers | HIGH (official docs) |
| `pages_read_engagement` | Yes | Required in Facebook Login IG Content Publishing requirements; already present | HIGH |
| `pages_show_list` | Yes (already present) | Page listing/selection and Page->IG discovery flows | HIGH |
| `pages_manage_posts` | Keep (already present) | Existing Facebook Page publishing; no regression | HIGH |
| `ads_management` / `ads_read` | Conditional | Meta docs: may be required if app user role granted via Business Manager for some IG/Page flows | MEDIUM (role-dependent) |

**App Review / access caveat:** Instagram Content Publishing and permissions may require Advanced Access/App Review for external users. EmpregaNoix is single-admin now, but checklist must document current mode, role/task requirements, and review needs before broader rollout.

### Rate limits / publishing constraints

| Constraint | Verified Value / Behavior | Stack implication | Confidence |
|------------|---------------------------|-------------------|------------|
| Content publishing limit | Meta docs currently conflict: Content Publishing guide says 100 posts/24h; other refs/pages mention 50; older blog posts mention 25. `content_publishing_limit` is authoritative at runtime. | Do **not** hardcode. Query `content_publishing_limit` before publish batches or on 429/rate-limit errors; expose safe retry/wait messaging. | MEDIUM (doc inconsistency), HIGH (mitigation) |
| Container creation limit | 400 containers / rolling 24h (IG User Media reference) | Avoid unnecessary container recreation; reuse idempotency keys and persist container/media IDs. | HIGH |
| Container expiry | 24 hours | Publish before expiry; if expired, recreate container. | HIGH |
| Image format | JPEG only; no MPO/JPS | Normalize generated/uploaded output to JPEG. | HIGH |
| Image size/aspect | <=8MB; width 320-1440; aspect ratio within 4:5 to 1.91:1; sRGB | Generate 1080x1080 or 1080x1350 JPEG, sRGB. | HIGH |
| Caption | Max 2200 chars, 30 hashtags, 20 @ tags (API enforces/limits) | Keep existing backend validation as source of truth; UI counter/warning is advisory. | HIGH |
| Media fetch | Meta cURLs `image_url`; must be public at attempt time | Public HTTPS URL, no auth, stable during publish window. | HIGH |

---

## Image Generation / Serving / Public URL Guidance (Concrete)

### Recommended v1.5 default (no new infra)

1. **Generate** image with Pillow in backend service (`app/services/social/image_card.py` or similar).
2. **Normalize** to JPEG RGB/sRGB, dimensions 1080x1080 or 1080x1350, quality tuned to stay comfortably under 8MB.
3. **Persist** bytes in Postgres in a small dedicated table, e.g. `social_media_assets`:
   - `id` UUID PK
   - `provider` (`instagram`)
   - `job_id` FK
   - `kind` (`generated_card`, `upload`, future)
   - `mime_type` (`image/jpeg`)
   - `width`, `height`, `bytes_size`
   - `sha256` (dedupe/debug, optional)
   - `storage` (`db`)
   - `data` `bytea` (or split table if preferred)
   - `public_token` unique, unguessable
   - `created_at`, `expires_at` optional
4. **Serve** via public endpoint: `GET /api/v1/public/social-images/{public_token}.jpg`.
5. **Return URL** as `settings.BACKEND_PUBLIC_URL`/`SITE_PUBLIC_URL`-derived absolute HTTPS URL for `image_url` in IG container creation.

### FastAPI serving pattern

```py
from fastapi import Response

@app.get("/api/v1/public/social-images/{token}.jpg")
async def get_social_image(token: str, session: AsyncSession = Depends(get_session)):
    asset = await get_public_image_asset(session, token)
    if asset is None:
        raise HTTPException(status_code=404)
    return Response(
        content=asset.data,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "Content-Disposition": 'inline; filename="job-card.jpg"',
        },
    )
```

**Rules:**
- No auth on this endpoint (Meta fetches it), but path token must be unguessable.
- Do not expose sequential IDs.
- Set `Content-Type: image/jpeg` and long cache headers; tokened URLs are immutable.
- Ensure backend URL is publicly reachable over HTTPS in deployed env.
- For local dev, Meta cannot fetch `localhost`; use mock publish tests or a temporary tunnel only for manual validation.

### Pillow card generation pattern

```py
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

def render_job_card(payload: JobCardPayload, size=(1080, 1350)) -> bytes:
    img = Image.new("RGB", size, "#0f0a1a")
    draw = ImageDraw.Draw(img)
    font_title = ImageFont.truetype("app/assets/fonts/NotoSans-Bold.ttf", 56)
    # ...draw branded card...
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92, optimize=True, progressive=True)
    data = buf.getvalue()
    if len(data) > 8_000_000:
        # deterministic fallback: reduce quality/dimensions while keeping aspect
        ...
    return data
```

**Rules:**
- Bundle fonts in repo; never depend on host OS fonts.
- Enforce aspect ratio and size before persisting.
- Keep rendering deterministic and idempotent for same input+template version.
- Include only safe job fields; avoid leaking admin-only/private data beyond intended caption/card policy.

---

## Integration Points with Existing Stack

| Existing Component | Current Behavior | Instagram Addition | Confidence |
|--------------------|------------------|--------------------|------------|
| `app/services/social/meta_oauth.py` | FB scopes `pages_show_list,pages_manage_posts,pages_read_engagement`; stores Page token/account | Add `instagram_basic,instagram_content_publish` to scope set; on connect/verify fetch `instagram_business_account` for selected Page and persist `ig_user_id` (new column/field). Handle missing linked IG account as actionable safe error. | HIGH |
| `app/models/social_account.py` / Alembic | Stores provider/page/token/status | Extend for IG linkage: either add `ig_user_id`/`ig_username` nullable columns or provider-specific metadata. Prefer explicit columns for queryability; keep token encrypted. | HIGH |
| `app/services/social/types.py` | `SocialPostPayload` has FB/page fields only | Extend payload for Instagram: `ig_user_id`, `image_url`, `caption`, optional `alt_text`, `container_id`; keep provider-neutral result types. | HIGH |
| `app/services/social/publisher.py` | Protocol `publish(post)` | Keep protocol; implement `InstagramPublisher` with same `PublishResult` category contract (`transient/permanent/ambiguous`). | HIGH |
| `app/services/social/publish_pipeline.py` | Facebook-only claim/process/publish | Refactor to provider-aware pipeline or parallel IG pipeline reusing shared helpers. Preserve FB behavior exactly; isolate IG-specific container creation/status/publish. | HIGH |
| `app/crud/social_posts.py` | Assumes one FB social post shape; status item builder FB-specific | Support per-platform records (`provider=facebook|instagram`, unique `(job_id, provider)` already exists). Add IG-specific status labels/URLs/permalink handling. | HIGH |
| `app/api/v1/admin.py` | FB draft/generate/save/approve/status/retry endpoints | Add Instagram draft/status/retry endpoints or generalize by provider query param. Keep backward compatibility for FB UI. | HIGH |
| `frontend/app/admin/review/EditJobDialog.tsx` | Single "Post para Facebook" section | Add "Post para Instagram" section side-by-side: toggle, editable caption prefilled, 2200 counter, >30 hashtags warning, image preview, per-platform status. Reuse existing auth/error patterns. | HIGH |
| `frontend/app/admin/integracoes/IntegrationsClient.tsx` | Facebook connection UI | Show IG linked account state derived from FB Page connection; surface "no Instagram Business account linked" and permission/reconnect actions. | HIGH |
| `backend/.env.example` / config | Meta/FB/social env vars | Add only needed vars: e.g. `BACKEND_PUBLIC_URL` (if needed for image URL), `INSTAGRAM_IMAGE_*` limits optional, feature flag if desired. Do **not** duplicate Meta app secrets. | MEDIUM |

---

## Observability / Safety Additions

| Concern | Recommendation | Confidence |
|---------|----------------|------------|
| Token/secret logging | Never log access tokens, image public tokens in sensitive contexts beyond necessary URL generation; never log raw Graph responses containing tokens. | HIGH |
| Error taxonomy | Map IG Graph errors to existing `PublishFailureCategory`: 429/5xx/transient network = transient; invalid token/permission/media format/ownership = permanent; timeout after create/publish ambiguity = ambiguous/no auto-retry. | HIGH |
| Idempotency | Reuse `(job_id, provider)` uniqueness; persist `external_container_id`, `external_post_id`, attempts, status. Before create/publish, check existing IDs to avoid duplicates. | HIGH |
| Rate limit handling | Read `content_publishing_limit` and back off when quota exhausted; treat publish 2207042/subcode as rate-limited transient/permanent-by-policy with clear operator message and next retry window. | MEDIUM |
| Token expiration | Reuse existing verify/reconnect model; mark account `needs_reconnect` on definitive token/permission failures. Optional proactive alert before expiry if expiry metadata available. | HIGH |

---

## Sources

| Source | What was verified | Confidence |
|--------|-------------------|------------|
| https://developers.facebook.com/docs/instagram-platform/content-publishing | IG Content Publishing flow, requirements, permissions by login type, image public URL requirement, JPEG-only limitation, container/publish/status endpoints, rate-limit text, container expiry | HIGH |
| https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media | Image specs (JPEG, 8MB, 320-1440, 4:5-1.91:1, sRGB), container creation params, 400 containers/24h, caption limits, status behavior | HIGH |
| https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish | Publish endpoint, creation_id, permissions/tasks, limitations | HIGH |
| https://developers.facebook.com/docs/graph-api/changelog/ | Current Graph API version v27.0 (2026-11-04), v21.0 availability until 2027-01-21 | HIGH |
| https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/page/ and Page docs (via web search results) | `GET /{page-id}?fields=instagram_business_account` returns linked IG business account id; permission requirements | HIGH |
| https://pypi.org/project/pillow/ and https://pillow.readthedocs.io/en/latest/releasenotes/13.0.0.html | Pillow latest version 13.0.0 (2026-10-16), Python >=3.11 | HIGH |
| https://fastapi.tiangolo.com/advanced/custom-response/ | Serving bytes via `Response(content=..., media_type="image/jpeg")` | HIGH |
| Project code inspection (`backend/app/services/social/*`, models, schemas, admin routes, frontend review/integrations) | Existing integration points, provider contract, worker/pipeline patterns, env/config conventions | HIGH |

---

*Stack research for: EmpregaNoix v1.5 Instagram publishing additions*  
*Researched: 2026-11-23*