# Phase 30: Instagram Review Experience - Pattern Map

**Mapped:** 2026-11-24
**Files analyzed:** 9
**Analogs found:** 9 / 9

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `frontend/app/admin/review/EditJobDialog.tsx` | component (client dialog) | request-response | existing Facebook section in same file (`EditJobDialog.tsx:850-1213`) | exact |
| `frontend/lib/api.ts` | utility (API client/types) | request-response | existing social draft/status + Meta integration functions in same file (`api.ts:409-769`, `540-649`) | exact |
| `backend/app/api/v1/admin.py` | controller (FastAPI router) | request-response | existing Facebook social-post endpoints in same file (`admin.py:374-624`) and IG media prepare (`admin.py:131-145`) | exact |
| `backend/app/schemas/social_posts.py` | schema/model (Pydantic) | request-response | existing `SocialPostDraftResponse`/`SocialPostStatusItem` in same file (`social_posts.py:34-105`) | exact |
| `backend/app/crud/social_posts.py` | service/CRUD | CRUD | existing provider-scoped CRUD in same file (`social_posts.py:20-362`) | exact |
| `backend/app/services/social/post_generation.py` | service (template/LLM generation) | transform | existing Facebook template/fallback generation in same file (`post_generation.py:156-297`) | role-match |
| `frontend/app/admin/review/ReviewQueue.tsx` | component (client queue) | request-response | existing Facebook-only `getSocialStatus` fetch + state in same file (`ReviewQueue.tsx:72-164`) | role-match |
| `frontend/components/admin/ReviewRow.tsx` | component (presentational row) | request-response | existing single-platform social badge in same file (`ReviewRow.tsx:68-99`) | role-match |
| `backend/tests/test_admin_instagram_social_posts.py` *(new)* | test | request-response | `backend/tests/test_admin_social_posts.py` | exact |

## Pattern Assignments

### `frontend/app/admin/review/EditJobDialog.tsx` (component, request-response)

**Analog:** `frontend/app/admin/review/EditJobDialog.tsx` — Facebook section (same file), lines 251-445, 850-1213.

**Imports / dependencies pattern** (lines 1-31):
```tsx
"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type RefObject,
} from "react";

import { useToast } from "@/components/admin/ToastProvider";
import { X } from "@/components/admin/icons";
import {
  ApiError,
  generateSocialDraft,
  getSocialDraft,
  getSocialStatus,
  retrySocialPost,
  saveSocialDraft,
  updateJob,
  type JobAdmin,
  type JobUpdate,
  type SocialPostDraft,
  type SocialPostStatusItem,
  type SocialPublishMode,
} from "@/lib/api";
import { buildAdminLoginHref } from "@/lib/adminReturnTo";
import { TOKEN_KEY } from "@/lib/auth";
import { CITY_OPTIONS, type CitySlug } from "@/lib/cities";
```

**Social state + reset pattern** (lines 251-323):
```tsx
// Social draft state
const [socialDraft, setSocialDraft] = useState<SocialPostDraft | null>(null);
const [socialText, setSocialText] = useState("");
const [socialPublishMode, setSocialPublishMode] =
  useState<SocialPublishMode>("publish_now");
const [socialDate, setSocialDate] = useState("");
const [socialTime, setSocialTime] = useState("");
const [socialAction, setSocialAction] = useState<SocialAction>(null);
const [socialLoadError, setSocialLoadError] = useState<string | null>(null);
const [socialActionError, setSocialActionError] = useState<string | null>(null);
const [socialFallbackWarning, setSocialFallbackWarning] = useState(false);
const [socialSaved, setSocialSaved] = useState(false);
...
const resetSocialState = () => { /* resets all social state */ };
const applyDraft = (draft: SocialPostDraft | null) => { /* normalizes draft into state */ };
```

**Load on open + auth-expired pattern** (lines 333-414):
```tsx
const handleAuthExpired = () => {
  try { sessionStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
  window.location.replace(
    buildAdminLoginHref(`${window.location.pathname}${window.location.search}`),
  );
};

useEffect(() => {
  if (!open || !job || !token) return;
  let cancelled = false;
  setSocialAction("load");
  Promise.all([
    getSocialDraft(token, job.id).then(...).catch(err => {
      if (err instanceof ApiError && err.status === 401) { handleAuthExpired(); return; }
      ...
    }),
    getSocialStatus(token, job.id).then(...).catch(...),
  ]).finally(() => { if (!cancelled) { setSocialAction(null); setSocialStatusLoading(false); } });
  return () => { cancelled = true; };
}, [open, job?.id, token]);
```

**Facebook section UI pattern** (lines 850-978, 990-1213):
```tsx
{/* Post para Facebook */}
<section className="mt-6 border-t border-line pt-6">
  <h3 className="text-[20px] font-semibold leading-tight text-fg">
    Post para Facebook
  </h3>
  <div className="mt-4 rounded-lg border border-line bg-canvas p-4">
    <h4 className="text-[16px] font-semibold text-fg">
      Status da publicação no Facebook
    </h4>
    {socialStatusLoading ? <p className="mt-2 text-[14px] text-fg-muted">Carregando...</p>
     : socialStatusError ? <p role="alert" className="mt-2 text-[14px] text-danger-soft">{socialStatusError}</p>
     : !socialStatus ? /* Sem rascunho */ : /* status badge + details + retry */}
  </div>
  {/* draft editor, generate/save/regenerate, publish mode, preview */}
</section>
```

**Draft editor / validation / save pattern** (lines 576-656, 1054-1199):
```tsx
const validateSchedule = (): boolean => { /* schedule date/time required, pt-BR error */ };
const handleGenerate = async (isRegenerate: boolean) => {
  if (!token || !job || frozen || busy) return;
  if (!validateSchedule()) return;
  setSocialAction("generate"); setSocialActionError(null);
  try {
    const draft = await generateSocialDraft(token, job.id, buildSocialPayload());
    applyDraft(draft);
    if (draft.origin === "template_fallback") setSocialFallbackWarning(true);
  } catch (err) {
    const raw = err instanceof ApiError ? err.message : "Não foi possível gerar o rascunho.";
    // map SITE_PUBLIC_URL to actionable pt-BR message
  } finally { setSocialAction(null); }
};
const handleSaveDraft = async () => {
  if (!token || !job || frozen || busy) return;
  if (!validateSchedule()) return;
  if (!socialText.trim()) { setSocialActionError("Texto do rascunho é obrigatório."); return; }
  setSocialAction("save");
  try { const draft = await saveSocialDraft(token, job.id, { ...buildSocialPayload(), text: socialText }); applyDraft(draft); toast("Rascunho salvo.", "success"); }
  catch (err) { ... toast(`Erro: ${message}`, "error"); }
  finally { setSocialAction(null); }
};
```

**Apply for Phase 30:** Add parallel IG state block (`igEnabled`, `igDraft`, `igCaption`, `igStatus`, `igMedia`, `igReadiness`, loading/error flags). Place **"Post para Instagram"** section below Facebook (D-03). Gate by `MetaIntegrationStatus.instagram` (fetch via existing `getMetaIntegrationStatus` or on open) — when not ready, show visible disabled section with pt-BR message + link `/admin/integracoes` (D-05). When toggle off, hide caption/preview (D-04). On toggle on/open, auto-call prepare media endpoint (D-06). Caption: live counter `N/2200`, block save/approve when >2200, warning when hashtag count >30, show “links não clicáveis / link na bio” guidance (D-08/D-09). Do not reuse Facebook draft as default prefill (D-01) — use template C. Keep all Facebook handlers/state unchanged.

---

### `frontend/lib/api.ts` (utility, request-response)

**Analog:** existing social draft/status/Meta functions in same file.

**Meta integration status types/pattern** (lines 558-622):
```ts
export type MetaInstagramReadinessState =
  | "ready" | "not_connected" | "missing_linkage" | "missing_permissions" | "needs_reconnect" | "unknown";

export interface MetaInstagramReadiness {
  ready: boolean;
  ig_user_id: string | null;
  ig_username: string | null;
  state: MetaInstagramReadinessState;
  message: string | null;
  checked_at?: string | null;
}

export interface MetaIntegrationStatus {
  provider: "facebook";
  status: "connected" | "needs_reconnect" | "disconnected";
  page_id: string | null;
  page_name: string | null;
  connected_at: string | null;
  token_checked_at: string | null;
  pending_selection: boolean;
  alert: MetaIntegrationAlert | null;
  instagram?: MetaInstagramReadiness | null;
}

export async function getMetaIntegrationStatus(token: string): Promise<MetaIntegrationStatus> {
  const res = await fetch(`${API}/api/v1/admin/integrations/meta/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as MetaIntegrationStatus;
}
```

**Social draft/status types pattern** (lines 409-437, 467-510, 707-769):
```ts
export type SocialPublishMode = "publish_now" | "schedule";
export type SocialDraftOrigin = "llm" | "template_fallback";

export interface SocialPostDraft {
  job_id: string;
  provider: "facebook";
  status: "draft" | "scheduled" | "publishing" | "published" | "failed" | "cancelled";
  text: string;
  publish_mode: SocialPublishMode | null;
  scheduled_at: string | null;
  origin: SocialDraftOrigin | null;
  saved: boolean;
  frozen: boolean;
  warning: string | null;
}

export interface SocialPostStatusItem {
  job_id: string;
  job_title?: string | null;
  provider: "facebook";
  status: SocialStatusValue;
  status_label: string;
  last_error: string | null;
  published_url: string | null;
  external_post_id: string | null;
  attempts: number;
  next_retry_at: string | null;
  scheduled_at: string | null;
  published_at: string | null;
  can_retry: boolean;
  retry_block_reason: string | null;
}
```

**API call / error pattern** (lines 467-489, 736-750):
```ts
export async function getSocialDraft(token: string, jobId: string): Promise<SocialPostDraft | null> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-post`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as SocialPostDraft;
}

export async function getSocialStatus(token: string, jobId: string): Promise<SocialPostStatusItem | null> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as SocialPostStatusItem;
}
```

**Apply for Phase 30:** Extend `SocialPostDraft.provider` and `SocialPostStatusItem.provider` to include `"instagram"` (or a shared literal union) without breaking FB consumers. Add IG-specific types/functions: `InstagramMediaPrepareResponse` (image_url, version_hash, validation {valid,code,message}, provenance, mime/size dims), `prepareInstagramMedia(token, jobId)` POST `/admin/jobs/{id}/instagram/media/prepare`, and IG draft/status functions (either explicit `/instagram/social-post*` routes or provider-aware). Reuse `ApiError`/`readError`/auth header pattern exactly.

---

### `backend/app/api/v1/admin.py` (controller, request-response)

**Analog:** existing Facebook social draft/status endpoints (same file, lines 374-624) and IG media prepare endpoint (lines 131-145).

**Auth + 404 + admin guard pattern** (lines 131-145, 509-523):
```python
@router.post("/jobs/{job_id}/instagram/media/prepare", response_model=InstagramMediaPrepareResponse)
async def prepare_job_instagram_media(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> InstagramMediaPrepareResponse:
    """Prepare/validate the exact intended Instagram image for a job (IMAG-01/02/03)."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    result = await prepare_instagram_media(session, job_id, settings)
    await session.commit()
    return result
```

**Facebook draft GET/POST generate/PUT pattern** (lines 509-624):
```python
@router.get("/jobs/{job_id}/social-post", response_model=SocialPostDraftResponse)
async def get_job_social_post(job_id: uuid.UUID, session: AsyncSession = Depends(get_session), claims: dict = Depends(require_admin)) -> SocialPostDraftResponse:
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    post = await get_by_job_provider(session, job_id, provider="facebook")
    if post is None:
        raise HTTPException(status_code=404, detail="Rascunho social não encontrado")
    return _draft_response(post)

@router.post("/jobs/{job_id}/social-post/generate", response_model=SocialPostDraftResponse)
async def generate_job_social_post(..., payload: SocialPostDraftRequest | None = None, ..., settings: Settings = Depends(get_settings)) -> SocialPostDraftResponse:
    job = await get_job(session, job_id)
    if job is None: raise HTTPException(status_code=404, detail="Vaga não encontrada")
    existing = await get_by_job_provider(session, job_id, provider="facebook")
    if existing is not None and existing.status != SocialPostStatus.draft:
        raise HTTPException(status_code=409, detail="Texto aprovado e bloqueado para envio.")
    req = payload or SocialPostDraftRequest()
    scheduled_at = _resolve_draft_schedule(req.publish_mode, req.scheduled_date, req.scheduled_time)
    try:
        generated = await generate_draft_for_job(job, settings=settings)
    except SocialPostLinkError as exc:
        raise HTTPException(status_code=422, detail=ACTIONABLE_SITE_URL_ERROR) from exc
    post = await upsert_draft(session, job_id, text=generated.text, scheduled_at=scheduled_at, provider="facebook")
    await session.commit(); await session.refresh(post)
    return _draft_response(post, origin=generated.origin, warning=generated.warning)

@router.put("/jobs/{job_id}/social-post", response_model=SocialPostDraftResponse)
async def save_job_social_post(..., payload: SocialPostDraftRequest, ...) -> SocialPostDraftResponse:
    ... validate text required; resolve schedule; build link; safe_text = sanitize_and_enforce_policy(...); upsert_draft(..., provider="facebook"); commit; refresh; return _draft_response(post)
```

**Apply for Phase 30:** Add explicit IG endpoints (recommended by RESEARCH A2, lower regression risk), e.g. `GET/POST generate/PUT /admin/jobs/{job_id}/instagram/social-post` and `GET /admin/jobs/{job_id}/instagram/social-status`. Reuse `get_by_job_provider/upsert_draft` with `provider="instagram"`. For IG generate, use deterministic template C (D-01/D-02) — do not call Facebook LLM generator as default; either add a dedicated IG template generator or a provider-aware branch. Enforce server-side caption length <=2200 on save/generate (D-08) with pt-BR 422 (e.g. `"Legenda do Instagram deve ter no máximo 2200 caracteres."`). Keep Facebook endpoints unchanged.

---

### `backend/app/schemas/social_posts.py` (schema/model, request-response)

**Analog:** same file, lines 34-105.

**Existing schema pattern** (lines 34-49, 59-78):
```python
class SocialPostDraftResponse(BaseModel):
    """Rascunho/estado do post social para UI admin (Phase 16)."""
    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    provider: Literal["facebook"] = "facebook"
    status: SocialPostStatusLiteral
    text: str
    publish_mode: Literal["publish_now", "schedule"] | None = None
    scheduled_at: datetime | None = None
    origin: Literal["llm", "template_fallback"]
    saved: bool
    frozen: bool
    warning: str | None = None

class SocialPostStatusItem(BaseModel):
    ...
    provider: Literal["facebook"] = "facebook"
    status: SocialPostUiStatusLiteral
    status_label: str
    ...
    can_retry: bool = False
    retry_block_reason: str | None = None
```

**Apply for Phase 30:** Widen `provider` literals to `Literal["facebook", "instagram"]` (or equivalent) in draft/status/response schemas as needed. Keep defaults/backward compatibility for Facebook responses. Do not expose tokens/secrets. If adding IG-specific fields (e.g. caption validation metadata), keep them additive.

---

### `backend/app/crud/social_posts.py` (service/CRUD, CRUD)

**Analog:** same file, lines 20-60, 257-362.

**Provider-scoped CRUD pattern** (lines 20-60):
```python
async def get_by_job_provider(
    session: AsyncSession,
    job_id: uuid.UUID,
    provider: str = "facebook",
) -> SocialPost | None:
    stmt = select(SocialPost).where(
        SocialPost.job_id == job_id,
        SocialPost.provider == provider,
    )
    return await session.scalar(stmt)

async def upsert_draft(session: AsyncSession, job_id: uuid.UUID, *, text: str, scheduled_at, provider: str = "facebook") -> SocialPost:
    post = await get_by_job_provider(session, job_id, provider=provider)
    if post is None:
        post = SocialPost(job_id=job_id, provider=provider, text=text, status=SocialPostStatus.draft, scheduled_at=scheduled_at)
        session.add(post)
        await session.flush()
        return post
    if post.status != SocialPostStatus.draft:
        raise ValueError("frozen")
    post.text = text
    post.scheduled_at = scheduled_at
    await session.flush()
    return post
```

**Status item builder (Facebook-biased today)** (lines 257-302):
```python
def build_social_status_item(*, job_id: uuid.UUID, job_title: str | None, post: SocialPost | None, account_status: SocialAccountStatus | None, now: datetime | None = None) -> SocialPostStatusItem:
    ...
    if post is None:
        return SocialPostStatusItem(..., provider="facebook", status="none", status_label=_STATUS_LABELS_PT["none"], ...)
    ...
    return SocialPostStatusItem(..., provider=post.provider or "facebook", status=status_value, ...)
```

**Apply for Phase 30:** Reuse CRUD functions as-is for `provider="instagram"` (already parameterized). Update `build_social_status_item` / `get_job_social_status_item` / `list_social_status_items` to handle instagram provider cleanly (status labels/none state) without regressing Facebook. For IG, retry/account-status semantics may differ in Phase 31; in Phase 30 focus on draft/status retrieval for review dialog. Avoid hardcoding `"facebook"` in returned item when post/provider is instagram.

---

### `backend/app/services/social/post_generation.py` (service, transform)

**Analog:** existing template fallback and policy enforcement, same file.

**Template fallback pattern** (lines 156-210):
```python
def _build_hashtags(job: Any) -> list[str]:
    city = _clean_text(getattr(job, "city", None))
    tags = ["#Emprego", "#Vagas"]
    if city:
        tags.append(f"#{_slugify_hashtag_token(city)}")
    tags.append("#EmpregaNoix")
    tags.append("#Oportunidade")
    return tags[:5]

def generate_template_fallback(job: Any, *, link: str, settings: Any | None = None) -> str:
    ...
    lines: list[str] = [f"💼 {title}"]
    location_line = f"📍 {city}" if city else "📍 Local a confirmar"
    ...
    lines.append(f"👉 Confira e candidate-se: {link}")
    hashtags = " ".join(_build_hashtags(job))
    lines.append("")
    lines.append(hashtags)
    text = "\n".join(lines).strip()
    text = _truncate_preserving_link(text, link, max_chars=760)
    return sanitize_and_enforce_policy(text, job, link=link, settings=settings)
```

**Policy/sanitization pattern** (lines 113-153):
```python
def sanitize_and_enforce_policy(text: str, job: Any, *, link: str, settings: Any | None = None) -> str:
    """Aplica política central: sem empresa/contatos e com link público."""
    ...
    if not include_contact:
        sanitized = _scrub_contacts(sanitized)
    if link not in sanitized:
        base = sanitized.rstrip()
        joiner = "\n\n" if base else ""
        sanitized = f"{base}{joiner}Confira e candidate-se: {link}".strip()
    ...
    return sanitized
```

**Apply for Phase 30 (D-01/D-02):** Create a deterministic Instagram template C generator (server-side preferred, per RESEARCH A3). Do **not** reuse Facebook template text as default. IG template must: use job data (title, company if present? follow D-01 "empresa se houver", city/remoto, tipo/contrato/salário when present), always include CTA “link na bio” (and guidance that links not clickable is UI concern; caption should not rely on clickable URL), include suggested hashtags `#vagas #emprego #<cidade> #oportunidade` (D-02), be concise. Hashtag normalization can reuse `_slugify_hashtag_token` style. Enforce max 2200 chars. Keep Facebook generator unchanged.

---

### `frontend/app/admin/review/ReviewQueue.tsx` (component, request-response)

**Analog:** existing Facebook social status fetch in same file, lines 72-164.

**Social status fetch pattern** (lines 72-164):
```tsx
const [socialStatuses, setSocialStatuses] = useState<
  Record<string, SocialPostStatusItem | null>
>({});
const socialFetchSeq = useRef(0);

useEffect(() => {
  if (!token || items.length === 0) {
    if (items.length === 0) setSocialStatuses({});
    return;
  }
  const seq = ++socialFetchSeq.current;
  let cancelled = false;
  Promise.all(
    items.map(async (id) => {
      try {
        const status = await getSocialStatus(token, id);
        return [id, status] as const;
      } catch (err) {
        if (handleAuthError(err)) throw err;
        return [id, null] as const;
      }
    }),
  ).then((entries) => {
    if (cancelled || seq !== socialFetchSeq.current) return;
    setSocialStatuses((prev) => { ...current ids only... });
  });
  return () => { cancelled = true; };
}, [token, items]);
```

**Apply for Phase 30:** REVW-01 requires independent status per platform in review experience; primary surface is `EditJobDialog`. If queue badges are updated, extend state to hold IG status per job (separate map or combined structure) and render independent badges. Be careful not to double-fetch excessively; reuse existing seq/cancel pattern.

---

### `frontend/components/admin/ReviewRow.tsx` (component, request-response)

**Analog:** same file, lines 20-99.

**Single social badge pattern** (lines 20-27, 68-99):
```tsx
export interface ReviewRowProps {
  job: JobAdmin;
  socialStatus?: SocialPostStatusItem | null;
  onApprove: () => Promise<void> | void;
  onEdit: () => void;
  onDelete: () => void;
  loading?: boolean;
}

const socialLabel =
  socialStatus && ["scheduled", "publishing", "published", "failed"].includes(socialStatus.status)
    ? socialStatus.status_label
    : null;
...
{socialLabel ? (
  <span className={`rounded-full border px-3 py-1 text-[14px] ${socialClass}`}>
    {socialLabel}
  </span>
) : null}
```

**Apply for Phase 30:** If showing independent platform statuses in queue, add `instagramStatus?: SocialPostStatusItem | null` (additive prop) and render separate badges for FB/IG without changing existing FB behavior. Keep styling consistent with existing badge classes.

---

### `backend/tests/test_admin_instagram_social_posts.py` (test, request-response)

**Analog:** `backend/tests/test_admin_social_posts.py` (lines 1-120+).

**Test harness / auth / seed pattern** (lines 1-64):
```python
"""Integration/API tests for admin social post draft ..."""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.job import Job, JobStatus
from app.models.social_post import SocialPost, SocialPostStatus

VALID_CF_TOKEN = "token-de-teste"

async def _login(client, admin_password="test-password"):
    resp = await client.post("/api/v1/auth/login", json={"password": admin_password, "cf_token": VALID_CF_TOKEN})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]

async def _seed_job(db_session, **overrides) -> Job:
    data = dict(title="Vaga Social", company="Empresa Confidencial", ..., status=JobStatus.pending, ...)
    data.update(overrides)
    job = Job(**data); db_session.add(job); await db_session.flush(); return job

def _draft_result(text="Texto gerado", origin="llm", warning=None):
    return SimpleNamespace(text=text, origin=origin, warning=warning)
```

**Endpoint test pattern** (lines 66-120):
```python
@pytest.mark.asyncio
async def test_social_post_get_generate_save_upsert_and_fields(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()
    async def fake_generate(job_arg, settings=None, client=None): return _draft_result(...)
    monkeypatch.setattr("app.api.v1.admin.generate_draft_for_job", fake_generate)

    resp = await client.get(f"/api/v1/admin/jobs/{job.id}/social-post", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404
    ...
```

**Apply for Phase 30:** Create IG-focused tests mirroring this style. Cover: IG draft GET 404 when missing, generate returns template C (D-01/D-02) with provider instagram, save persists and enforces 2200 max (422 pt-BR when over limit), provider isolation from Facebook (saving IG does not overwrite FB), status endpoint shape, and auth required. Mock generation as deterministic (no LLM call). Use `db_session`/`client` fixtures per existing harness.

## Shared Patterns

### Admin auth / 401 redirect (frontend)
**Source:** `frontend/app/admin/review/EditJobDialog.tsx:333-342`, `frontend/app/admin/review/ReviewQueue.tsx:28-41`
**Apply to:** any new IG fetch/action in EditJobDialog/ReviewQueue.
```ts
const handleAuthExpired = () => {
  try { sessionStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
  window.location.replace(
    buildAdminLoginHref(`${window.location.pathname}${window.location.search}`),
  );
};
// on catch: if (err instanceof ApiError && err.status === 401) { handleAuthExpired(); return; }
```

### pt-BR loading/error/alert UI states
**Source:** `frontend/app/admin/review/EditJobDialog.tsx:861-867, 984-988, 1045-1052`
**Apply to:** IG caption/preview/readiness states.
```tsx
{socialStatusLoading ? <p className="mt-2 text-[14px] text-fg-muted">Carregando...</p> : null}
{socialStatusError ? <p role="alert" className="mt-2 text-[14px] text-danger-soft">{socialStatusError}</p> : null}
```

### IG readiness interpretation (D-05)
**Source:** `frontend/app/admin/integracoes/IntegrationsClient.tsx:49-113`
**Apply to:** EditJobDialog IG section gating (visible but disabled when not ready, with link to `/admin/integracoes`).
```tsx
function getInstagramPanel(instagram: MetaInstagramReadiness | null | undefined, fbStatus: MetaIntegrationStatus["status"]) {
  const state = instagram?.state ?? "unknown";
  if (state === "ready") return { ..., action: "verify", tone: "success" };
  if (state === "missing_linkage") return { heading: "Instagram não vinculado", ..., action: "reconnect", tone: "warning" };
  if (state === "missing_permissions") return { heading: "Permissões do Instagram ausentes", ..., action: "reconnect", tone: "warning" };
  if (state === "needs_reconnect") return { heading: "Reconexão necessária para o Instagram", ..., action: "reconnect", tone: "warning" };
  return { heading: "Prontidão do Instagram indisponível", message: "Não foi possível confirmar a prontidão do Instagram agora.", action: fbStatus === "needs_reconnect" ? "reconnect" : "verify", tone: "info" };
}
```

### Backend admin endpoint guard + safe pt-BR errors
**Source:** `backend/app/api/v1/admin.py:131-145, 509-624`
**Apply to:** all new IG admin endpoints.
```python
@router.<method>("/jobs/{job_id}/instagram/...", response_model=...)
async def handler(job_id: uuid.UUID, session: AsyncSession = Depends(get_session), claims: dict = Depends(require_admin), ...):
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    ...
    await session.commit()
    await session.refresh(obj)
    return ...
```

### Instagram media prepare contract (Phase 29, reuse as-is)
**Source:** `backend/app/services/social/image_media.py:155-227`, `backend/app/api/v1/admin.py:131-145`
**Apply to:** IG image preview in EditJobDialog (D-06/D-07).
```python
result = await prepare_instagram_media(session, job_id, settings)
# result.validation.valid/code/message, result.image_url, result.version_hash, result.provenance
# codes: missing_image | invalid_image | invalid_public_url | media_not_ready
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | All Phase 30 files have close analogs in the existing Facebook social flow, Phase 29 media/readiness contracts, or existing admin test patterns. The IG caption template C (D-01/D-02) has no exact prior IG analog, but `backend/app/services/social/post_generation.py` template/fallback generation is a strong role-match to adapt. |

## Metadata

**Analog search scope:** `frontend/app/admin/review/*`, `frontend/components/admin/*`, `frontend/lib/api.ts`, `frontend/app/admin/integracoes/*`, `backend/app/api/v1/admin.py`, `backend/app/schemas/social_posts.py`, `backend/app/crud/social_posts.py`, `backend/app/services/social/*`, `backend/tests/test_*social*`, `backend/tests/test_*ig*`
**Files scanned:** 12 (targeted reads/greps; stopped after strong analogs identified)
**Pattern extraction date:** 2026-11-24
