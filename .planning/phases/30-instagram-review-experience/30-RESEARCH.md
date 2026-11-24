# Phase 30: Instagram Review Experience - Research

**Researched:** 2026-11-23
**Domain:** Admin review UX (Next.js/React + FastAPI) for Instagram publishing controls, caption rules, and image preview (reusing Phase 29 media/readiness contracts)
**Confidence:** HIGH (based on direct code inspection of `EditJobDialog.tsx`, `api.ts`, `admin.py`, `social_posts.py` schemas/models, `image_media.py`, `meta_oauth.py`/schemas, `IntegrationsClient.tsx`, and Phase 29/30 CONTEXTs)

## Summary

Phase 30 adds a “Post para Instagram” section in the admin review dialog (`frontend/app/admin/review/EditJobDialog.tsx`) placed **below** the existing “Post para Facebook” section. The implementation must mirror established Facebook UX patterns (draft load/save/generate, status display, toasts in pt-BR, auth-expired handling, frozen/locked states) while applying Instagram-specific rules: caption max **2200 chars** (block save/approve on over-limit), **warning (non-blocking)** when > **30 hashtags** (`#...` tokens), mandatory guidance that links are not clickable and CTA must be **“link na bio”**, and an Instagram image preview prepared via the Phase 29 endpoint **`POST /admin/jobs/{job_id}/instagram/media/prepare`** with automatic preparation when opening the dialog/toggling on (D-06) and **blocking only Instagram** if the image is invalid/unavailable (D-07).

Backend currently treats social drafts/status as **Facebook-only** in code paths: `SocialPost.provider` is a free string but CRUD/admin endpoints hardcode `provider="facebook"`, and schemas default/limit `provider` to `"facebook"`. Phase 30 therefore requires **schema + CRUD + admin API extensions** to support Instagram drafts/status (and optionally a general `provider` parameter) while preserving Facebook behavior unchanged. Readiness gating comes from `GET /api/v1/admin/integrations/meta/status` → `MetaIntegrationStatus.instagram` (already returned by backend). When not ready, the Instagram section must be **visible but disabled** with clear pt-BR copy and a link to `/admin/integracoes` (D-05), reusing the same readiness states/messages model as the Integrations page.

**Primary recommendation:** Implement Instagram as a **parallel, provider-scoped social workflow** (`provider='instagram'`) in backend (new/extended endpoints or provider-aware variants) and a parallel state block in `EditJobDialog` (new UI subsection + new API client functions). Reuse Phase 29 media prepare endpoint and `MetaIntegrationStatus.instagram` for gating/preview; do **not** reuse Facebook draft text as the default prefill (use template C). 

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 (Prefill legenda IG, Instagram-tuned):** Prefill padrão é **template simples (C)** a partir dos dados da vaga (título, empresa se houver, cidade/remoto, tipo/contrato/salário quando houver) **+ CTA sempre “link na bio”** (ex.: orientação clara de que links na legenda não são clicáveis; usar CTA no estilo “link na bio”). Não reutilizar cegamente o rascunho do Facebook como prefill padrão; o admin pode usar o texto do Facebook manualmente se quiser, mas o padrão é o template C (Instagram-tuned).
- **D-02 (Hashtags sugeridas):** Hashtags sugeridas iniciais no template: `#vagas`, `#emprego`, `#cidade`, `#oportunidade` (o admin pode editar/remover). O template deve ser conciso e adequado ao Instagram.
- **D-03 (Seção/toggle no diálogo):** Seção **“Post para Instagram”** fica **abaixo** de **“Post para Facebook”** no `EditJobDialog`. Publicações Facebook e Instagram são **independentes** (falha/estado de uma não bloqueia a outra).
- **D-04 (Toggle por vaga):** Toggle **“Publicar no Instagram desta vaga”** (por vaga). Quando **desligado**, **esconder** legenda e preview (mostrar apenas o toggle/contexto mínimo). Quando **ligado**, exibir controles da legenda e preview da imagem IG.
- **D-05 (Prontidão IG):** Se o Instagram **não estiver pronto** em Integrações (conta/link/escopos/prontidão insuficiente), a seção permanece **visível mas desabilitada**, com texto explicativo em pt-BR e **link para `/admin/integracoes`** (ação clara de correção/reconexão). Não esconder a seção nesse caso.
- **D-06 (Preview imagem IG):** Preview da imagem exata do Instagram: **carregar/preparar automaticamente** ao abrir o diálogo (quando aplicável) ou ao **ativar** o toggle (escolha A). Exibir estados de **loading** e **erro/mensagem em pt-BR** se a imagem não estiver preparada/inválida.
- **D-07 (Bloqueio só do Instagram):** **Não é possível salvar/aprovar/publicar com Instagram habilitado sem imagem válida** conforme contrato IMAG-01 (Phase 29); isso **não bloqueia** aprovação/publicação do Facebook nem do site. Mensagens e validações devem deixar isso claro.
- **D-08 (Regras de legenda REVW-02/03):** Edição de legenda Instagram com **contador ao vivo `N/2200`**; **não permitir salvar/aprovar** legenda acima do limite (2200). Validação também no backend quando aplicável. **Aviso** (não bloqueante, salvo o limite) quando a legenda tiver **>30 hashtags** (contagem por tokens `#...`). Exibir **orientação clara** de que **links na legenda não são clicáveis** e usar CTA no estilo **“link na bio”**.

### OpenCode's Discretion
- Wording final em pt-BR dos textos de ajuda/erros na seção IG (consistentes com padrão admin).
- Detalhes de UX do contador/avisos (posicionamento/estilo) respeitando Tailwind/dark/púrpura.
- Estratégia técnica exata para “preparar automaticamente” (ao abrir vs ao togglar) desde que atenda D-06 e evite chamadas excessivas.
- Se status Instagram exibido na revisão reutiliza dados já buscados no `ReviewQueue`/`EditJobDialog` ou exige nova busca — escolher a abordagem mais simples e coerente (sem quebrar Facebook).

### Deferred Ideas (OUT OF SCOPE)
- Geração automática de legenda IG via LLM separada do Facebook (não decidido agora).
- Campos avançados de IG (hashtags gerenciadas separadamente, primeiros comentários etc.) fora de REVW-01..04.
- Alterações no pipeline assíncrono de publicação IG (Phase 31).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Render “Post para Instagram” section, toggle, caption editor, counters, warnings | Frontend (Next.js `EditJobDialog`) | — | User interaction + validation feedback in admin UI (pt-BR), mirrors Facebook section patterns |
| Fetch/save IG draft + IG publish intent per job (review context) | Backend (FastAPI admin APIs) | Frontend API client (`frontend/lib/api.ts`) | Persist draft/status per `(job_id, provider='instagram')`, enforce limits server-side |
| Fetch Meta integration readiness (`instagram` block) | Backend (`/admin/integrations/meta/status`) | Frontend (IntegrationsClient + EditJobDialog fetch) | Source of truth is server-resolved readiness from `SocialAccount` + Meta checks (Phase 29) |
| Prepare/validate Instagram image (card) + public URL | Backend (`POST /admin/jobs/{id}/instagram/media/prepare`, public `GET /api/v1/public/ig-media/...`) | Frontend preview (loads URL from prepare response) | Phase 29 contracts already implemented; Phase 30 consumes for preview + gating |
| Enforce “block only Instagram if invalid image when enabled” on save/approve flow | Backend validation at the point of enabling IG publish / approval path that includes IG | Frontend pre-check UX | Must not block Facebook/site; validation rules tied to IMAG-01/Phase 31 handoff but UX enforced in Phase 30 review |

## Standard Stack

### Core (already in repo; no new libraries required for Phase 30 scope)
| Library/Component | Version/Ref | Purpose | Why Standard |
|-------------------|------------|---------|--------------|
| Next.js (App Router) + React | Repo `frontend` (see AGENTS/stack context) | Admin UI dialogs/pages | Existing admin review UI lives here (`EditJobDialog`) |
| Tailwind CSS | Repo frontend | Styling, dark/purple theme | Existing design system; follow Facebook section patterns |
| FastAPI + Pydantic v2 | Repo backend | Admin APIs, validation | Existing social/admin endpoints and schemas |
| SQLAlchemy 2.x + Postgres (Neon) | Repo backend | Persistence for `social_posts` (and readiness fields in `social_accounts`) | Existing model `SocialPost` already keyed by `(job_id, provider)` |

### Supporting (reuse)
| Component | Location | Purpose | When to Use |
|-----------|----------|---------|-------------|
| Instagram media prepare | `POST /admin/jobs/{job_id}/instagram/media/prepare` (`backend/app/api/v1/admin.py`, service `app.services.social.image_media`) | Get `image_url`, `validation`, provenance for preview | On dialog open (if IG section will be shown/enabled context) or when toggling IG on (D-06) |
| Public IG image URL | `GET /api/v1/public/ig-media/{job_id}/{version}.jpg` (`backend/app/api/v1/public.py`) | Serve exact image bytes (immutable cache headers) | Preview `<img>` src from prepare response |
| Meta integration status | `GET /api/v1/admin/integrations/meta/status` (`frontend/lib/api.ts:getMetaIntegrationStatus`) | Readiness: `status.instagram` (`ready`, `missing_linkage`, `missing_permissions`, `needs_reconnect`, `unknown`, or null) | Gate IG section visibility-disabled state + link to `/admin/integracoes` (D-05) |
| Social draft/status CRUD patterns | `backend/app/crud/social_posts.py`, `backend/app/api/v1/admin.py` (facebook endpoints) | Canonical patterns to mirror for Instagram | Add parallel endpoints/handlers for provider `instagram` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Separate Instagram admin endpoints (`/instagram/social-post*`) | Generalize existing `/social-post` with `?provider=` | Generalization is cleaner long-term but touches many call sites/tests now; separate endpoints are explicit and lower risk for Phase 30. Recommend **explicit Instagram endpoints** (or explicit provider routes) to minimize regression risk, while reusing shared service/CRUD by passing `provider='instagram'`. |
| Storing “publish to Instagram” toggle as a dedicated DB column on `Job` | Derive from presence of an `instagram` `SocialPost` row + `status/text` intent | Existing Facebook flow uses `SocialPost` rows (draft/scheduled/…). For consistency and independence, prefer a `SocialPost` row with `provider='instagram'` (draft) even if “disabled”, OR add a clear flag. **Recommendation:** treat “enabled” as “there is an IG social post draft intended for publishing” (or add an explicit `enabled` field in a follow-up) — but keep it simple: when toggle is ON, ensure an IG draft record exists (or is created) with current caption/settings; when OFF, either delete/mark disabled. The planner must choose a concrete persistence model (see Open Questions). |

**Installation:** None required (all deps already present).

## Architecture Patterns

### Recommended Project Structure (where changes land)
```
frontend/
├── app/admin/review/EditJobDialog.tsx        # Add "Post para Instagram" section below Facebook
├── lib/api.ts                                 # Add IG draft/status/media/enable APIs + types
└── app/admin/integracoes/IntegrationsClient.tsx  # No change expected (readiness already shown); link target exists

backend/
├── app/api/v1/admin.py                        # Add Instagram endpoints: draft GET/generate/PUT, status, retry? (Phase 31), media prepare already exists
├── app/api/v1/public.py                       # Already serves /ig-media/... (no change)
├── app/crud/social_posts.py                   # Reuse (provider param) — ensure it supports 'instagram'
├── app/schemas/social_posts.py                # Expand provider literals/types to include 'instagram' where needed
├── app/models/social_post.py                  # provider is String (ok); may add constraints/indexes later (not required)
├── app/services/social/image_media.py         # Already used by prepare endpoint (no change)
└── app/schemas/social_media.py                # InstagramMediaPrepareResponse exists (no change)
```

### Pattern 1: Mirror Facebook section UI with Instagram-specific rules
**What:** In `EditJobDialog.tsx`, duplicate the structure of the “Post para Facebook” block into a new section “Post para Instagram” placed after it (D-03). Reuse the same state machine patterns: `loading`, `error`, `saved/dirty` indicators, action buttons, and pt-BR messages.
**When to use:** Any time the admin reviews/publishes social drafts in the review dialog.
**Key differences for Instagram:**
- Caption field: `textarea` with live counter `N/2200` (D-08). Disable/forbid save if `N > 2200`.
- Hashtag warning: if count of `#` tokens (`/#\w+/g` or split by whitespace and check startsWith `#`) > 30, show non-blocking warning (pt-BR), e.g. “Você usou mais de 30 hashtags. Isso pode reduzir o alcance no Instagram.” (wording in OpenCode’s discretion, keep clear).
- Guidance block (always visible when section active): “Links na legenda não são clicáveis. Use **link na bio** como CTA.” (D-01/D-09 context).
- Prefill source: **template C** (not Facebook draft). Generate locally from job fields in frontend for initial prefill OR backend “generate instagram draft” endpoint that returns template C. **Recommendation:** add a backend endpoint to generate IG draft (or a mode) to keep consistency and allow future LLM option; for Phase 30, generate template C server-side (deterministic) similar to Facebook fallback style, but Instagram-tuned (D-01/D-02).

**Example (sketch, not copy-paste ready):**
```tsx
// Inside EditJobDialog.tsx, after Facebook section:
<section className="mt-6 border-t border-line pt-6">
  <h3 className="text-[20px] font-semibold leading-tight text-fg">Post para Instagram</h3>

  {/* Readiness gate (D-05): if not ready, show disabled section + link */}
  {!igReady ? (
    <div className="mt-4 rounded-lg border border-line bg-canvas p-4 opacity-70">
      <p className="text-[14px] text-fg-muted">
        Instagram não está pronto para publicação nesta Página. Configure em Integrações.
      </p>
      <a href="/admin/integracoes" className="mt-2 inline-flex text-[14px] font-medium text-accent-soft underline">
        Abrir Integrações
      </a>
    </div>
  ) : (
    <>
      {/* Toggle D-04 */}
      <label className="mt-4 flex items-center gap-2">
        <input type="checkbox" checked={igEnabled} onChange={...} />
        <span>Publicar no Instagram desta vaga</span>
      </label>

      {igEnabled && (
        <>
          {/* Caption editor + counter + warnings */}
          {/* Image preview (prepare auto-load) */}
        </>
      )}
    </>
  )}
</section>
```

### Pattern 2: Provider-scoped social draft/status APIs (backend)
**What:** Extend backend to support Instagram drafts/status independently of Facebook.
**Current (Facebook-only):**
- `GET /admin/jobs/{job_id}/social-post` → calls `get_by_job_provider(..., provider="facebook")`, returns `SocialPostDraftResponse` (provider literal `"facebook"`).
- `POST /admin/jobs/{job_id}/social-post/generate` and `PUT /admin/jobs/{job_id}/social-post` also hardcode `provider="facebook"`.
- Status endpoints: `GET /admin/jobs/{job_id}/social-status` returns a single `SocialPostStatusItem` (provider `"facebook"` in schema). Also `GET /admin/social-posts` lists Facebook items.

**Recommended for Phase 30 (minimal, safe):**
- Add **Instagram-specific endpoints** under admin (clear and explicit), e.g.:
  - `GET /admin/jobs/{job_id}/instagram/social-post` (or `GET /admin/jobs/{job_id}/social-post?provider=instagram`, but be careful with existing clients)
  - `POST /admin/jobs/{job_id}/instagram/social-post/generate`
  - `PUT /admin/jobs/{job_id}/instagram/social-post`
  - `GET /admin/jobs/{job_id}/instagram/social-status` (or extend existing status to include IG; REVW-01 says “status independente por plataforma”). 
- Reuse CRUD: `get_by_job_provider(session, job_id, provider="instagram")`, `upsert_draft(..., provider="instagram")`. `SocialPost` model already allows any provider string and has unique `(job_id, provider)`.
- Update schemas:
  - `SocialPostDraftResponse.provider`: change from `Literal["facebook"] = "facebook"` to `Literal["facebook", "instagram"]` (or `str` with validation) — **must** allow `"instagram"`.
  - `SocialPostStatusItem.provider`: same change.
- Instagram draft generation (D-01/D-02): implement a **template C generator** for Instagram (server-side) that builds text from job fields + CTA “link na bio” + suggested hashtags `#vagas #emprego #<cidade-slug-ish> #oportunidade` (normalize city to a hashtag token carefully, e.g. `#saopaulo`, `#riodejaneiro`, `#belohorizonte`, `#remoto`). This is different from Facebook generator; do **not** reuse Facebook text as default.

**Example CRUD usage (already supported):**
```python
# backend/app/crud/social_posts.py already accepts provider param
post = await get_by_job_provider(session, job_id, provider="instagram")
post = await upsert_draft(session, job_id, text=caption, scheduled_at=None, provider="instagram")
```

### Pattern 3: Image preview flow (D-06, D-07)
**What:** Use existing `POST /admin/jobs/{job_id}/instagram/media/prepare` to obtain the exact image URL and validation state.
**Flow (recommended):**
- When `EditJobDialog` opens and IG section is relevant (or simply always fetch meta status + optionally prepare), **auto-prepare** if the admin is likely to use IG: easiest is to call prepare when (a) dialog opens for a job AND `igEnabled` becomes true OR (b) dialog opens and we want to show preview readiness — but D-06 says “carregar/preparar automaticamente ao abrir o diálogo (quando aplicável) ou ao ativar o toggle (escolha A)”. 
- **Practical choice (OpenCode discretion):** call prepare when `igEnabled === true`. Also, if you want immediate feedback, call it once when dialog opens if you decide IG is “intended”, but easier: on toggle ON → call prepare (and show loading). Also consider calling on dialog open if a persisted “IG enabled” flag exists. Since persistence model is TBD, a safe default is: **on toggle ON, call prepare**; optionally also call on open if `igEnabled` is already true.
- UI states (pt-BR): loading “Preparando imagem do Instagram…”; error: show `validation.message` from API if present, else fallback “Não foi possível preparar a imagem do Instagram. Tente novamente.”; if `validation.valid === false`, show the message and **disable saving/approving with IG enabled** (D-07).
- Preview: render `<img src={image_url} alt="Prévia da imagem do Instagram" />` when `image_url` is present. Note `image_url` is absolute HTTPS URL from backend (built from `MEDIA_PUBLIC_BASE_URL`).
- **Important:** The prepare endpoint is idempotent/cached by hash (Phase 29). It may return `validation.valid=false` with codes like `invalid_public_url`, `missing_image`, `invalid_image`, `media_not_ready` (see `image_media.py` messages). Surface `validation.message` directly (already pt-BR).

**API client addition (frontend/lib/api.ts):**
```ts
export interface InstagramImageValidation {
  valid: boolean;
  code?: "missing_image" | "invalid_image" | "invalid_public_url" | "media_not_ready" | null;
  message?: string | null;
}
export interface InstagramMediaPrepareResponse {
  job_id: string;
  provider: "instagram";
  version_hash: string;
  template_version: string;
  image_url: string | null;
  mime_type: string;
  width: number;
  height: number;
  byte_size: number | null;
  validation: InstagramImageValidation;
  provenance: Record<string, unknown>;
}
export async function prepareInstagramMedia(token: string, jobId: string): Promise<InstagramMediaPrepareResponse> { ... }
```

### Pattern 4: Readiness gating (D-05)
**What:** Fetch `getMetaIntegrationStatus(token)` (already exists in `api.ts`) inside `EditJobDialog` (or lift to parent). Use `status.instagram`:
- If `status == null` or `status.instagram == null`: treat as **not ready / unknown** → show section visible but disabled, message like “Não foi possível verificar o status do Instagram. Verifique em Integrações.” + link `/admin/integracoes`.
- States from backend (`MetaInstagramReadiness.state`): `ready` → enabled (if other conditions ok). `not_connected`, `missing_linkage`, `missing_permissions`, `needs_reconnect`, `unknown` → **disabled** with `instagram.message` (pt-BR, set by backend) or a safe fallback + link to `/admin/integracoes`.
- UI: follow `IntegrationsClient.getInstagramPanel` messaging style for consistency (reuse the same copy patterns where appropriate).

### Anti-Patterns to Avoid
- **Reusing Facebook draft text as IG default prefill:** D-01 explicitly forbids this as default. Always start from template C for IG.
- **Blocking Facebook/site approval because IG image is invalid:** D-07 requires blocking only Instagram actions when IG is enabled and image invalid.
- **Calling media prepare on every keystroke:** only on open/toggle-on (and optionally on explicit “refresh preview”), not on text edits.
- **Exposing secrets/tokens in frontend or logs:** keep backend safe messages (already done in meta_oauth/image_media).

## Don’t Hand-Roll

| Problem | Don’t Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Instagram image generation/validation/public serving | New image pipeline | Phase 29: `image_media.prepare_instagram_media`, `/api/v1/public/ig-media/{job_id}/{version}.jpg` | Already handles deterministic hash, public URL validation, cache, pt-BR messages, provenance |
| Meta/IG readiness resolution | New Graph calls from frontend or ad-hoc checks | `MetaIntegrationStatus.instagram` from `/admin/integrations/meta/status` (backend `meta_oauth` logic) | Centralized, safe, respects scopes and token state |
| Hashtag counting edge cases from scratch | Complex parser | Simple regex count of `#` tokens: match words starting with `#` (e.g. `/#[\p{L}\p{N}_]+/gu` in JS, or split on whitespace and filter) | Sufficient for warning “>30 hashtags”; avoid overengineering |
| Draft persistence model for social posts | New table for IG-only fields | Reuse `social_posts` with `provider='instagram'` | Model already supports provider scoping; minimal migration risk |

**Key insight:** Most risky pieces (media contracts, IG readiness, Graph/token safety) are already built in Phase 29/backend; Phase 30 is primarily **UI + provider-scoped draft/status API wiring + validation rules**.

## Common Pitfalls

### Pitfall 1: Treating Instagram as “just another Facebook draft”
**What goes wrong:** Copying Facebook draft generation/text into IG default, or reusing the same endpoints without provider separation.
**Why it happens:** Current code is Facebook-hardcoded everywhere.
**How to avoid:** Enforce D-01 (template C default), add provider-aware endpoints/schemas, and keep `provider='instagram'` distinct rows.
**Warning signs:** IG caption starts with Facebook text, or saving IG overwrites Facebook draft.

### Pitfall 2: Enforcing IG image validity too early/global
**What goes wrong:** Blocking Facebook approval or site publishing when IG image is bad.
**Why it happens:** Misplaced validation in shared approve flow.
**How to avoid:** Only validate/block when the action is “save/publish with Instagram enabled” (D-07). Keep Facebook/site paths unchanged.
**Warning signs:** Admin cannot approve a job because IG media is missing while they don’t want to post to IG.

### Pitfall 3: Not handling `MEDIA_PUBLIC_BASE_URL`/public URL issues in UI
**What goes wrong:** Prepare returns `validation.valid=false` with `code='invalid_public_url'` and `image_url=null`; UI shows broken preview or unclear error.
**Why it happens:** Phase 29 requires explicit HTTPS public base URL.
**How to avoid:** Display `validation.message` (pt-BR) prominently in IG preview area; disable IG publish enablement if image not valid.
**Warning signs:** Users see empty image box with no explanation.

### Pitfall 4: Hashtag counting off-by-one / wrong definition
**What goes wrong:** Warning triggers incorrectly (counts `#` in URLs? no URLs expected, but admin might paste) or misses pasted tags.
**Why it happens:** Naive string split.
**How to avoid:** Count tokens that start with `#` after whitespace/newlines (regex `(?:^|\s)#\S+` in practice) — keep it simple and documented in code comments; warning threshold is `> 30` (so 31+).
**Warning signs:** Warning shows at 30 instead of >30, or doesn’t count hashtags attached to punctuation oddly (acceptable to be lenient).

### Pitfall 5: Readiness gating hides section (violates D-05)
**What goes wrong:** Section is hidden when IG not ready, so admin doesn’t know it exists or how to fix.
**Why it happens:** Misreading “disabled if not ready” as “hidden”.
**How to avoid:** Always render “Post para Instagram” section; when not ready, render disabled controls + explanatory text + link to `/admin/integracoes`.
**Warning signs:** Admin can’t find IG settings entry point from review dialog.

## Code Examples (verified from repo patterns)

### Fetching Meta integration status (existing)
```ts
// frontend/lib/api.ts
export async function getMetaIntegrationStatus(token: string): Promise<MetaIntegrationStatus> { ... }
```
Use in `EditJobDialog` on open (alongside existing social draft/status fetches) to get `status.instagram`.

### Preparing Instagram media (existing backend endpoint)
```ts
// Proposed addition in frontend/lib/api.ts
export async function prepareInstagramMedia(token: string, jobId: string): Promise<InstagramMediaPrepareResponse> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${encodeURIComponent(jobId)}/instagram/media/prepare`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as InstagramMediaPrepareResponse;
}
```

### Counting hashtags (frontend, simple)
```ts
function countHashtags(text: string): number {
  // Count tokens that start with # (separated by whitespace)
  const matches = text.match(/(?:^|\s)#[^\s#]+/g);
  return matches ? matches.length : 0;
}
// Warning if countHashtags(caption) > 30 (D-08)
```

### Template C prefill (conceptual, backend or frontend)
```text
Title + (Company?) + City/Remote + (Contract/Type?) + (Salary?) 
+ blank line
+ "Confira os detalhes e candidatar-se: link na bio"
+ blank line
+ hashtags: #vagas #emprego #<cidadeTag> #oportunidade
```
City tag normalization examples (pt-BR): “São Paulo” → `#saopaulo`, “Rio de Janeiro” → `#riodejaneiro`, “Belo Horizonte” → `#belohorizonte`, “Remoto” → `#remoto` (adjust to project conventions).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Facebook-only social draft/status in review | Provider-scoped (`facebook`/`instagram`) social drafts | Phase 30 (this phase) | Enables independent IG review controls |
| No IG image preview contract in review | Reuse Phase 29 `instagram/media/prepare` + public URL | Phase 29/30 | Exact image preview, validation gated to IG only |
| IG readiness only visible in Integrations page | IG readiness surfaced as gating in Review dialog (D-05) | Phase 30 | Admin sees and can act from review flow context |

**Deprecated/outdated:**
- None identified; this is additive work building on Phase 29 outputs.

## Open Questions (for planner/implementer)
1. **Persistence model for “Publicar no Instagram desta vaga” (D-04 toggle)**
   - What we know: Facebook uses `SocialPost` rows per job/provider with status/frozen semantics. D-04 says “toggle Publish to Instagram for this job”.
   - Options: (a) Create/update an IG `SocialPost` (provider='instagram') when enabled (draft) and delete/cancel when disabled; (b) Add an explicit boolean field (e.g. `instagram_enabled`) to `Job` or to a new mapping table.
   - Recommendation: Prefer (a) for consistency (one source of truth per provider). If disabled, keep row optional or set a specific state — but need to be careful with “frozen after approval/publish” in Phase 31. Planner should define the contract.

2. **Exact API surface for IG draft/status**
   - Options: (a) New routes `/admin/jobs/{id}/instagram/social-post` (+ generate/PUT) and `/admin/jobs/{id}/instagram/social-status`; (b) Extend existing routes with `provider` query/body.
   - Recommendation: (a) is explicit and lowers regression risk in current Facebook-only frontend/tests.

3. **Where to generate template C (caption prefill)**
   - Options: (a) Frontend-only generation from job fields (no backend call) — fast, offline-ish, but logic duplicated later? (b) Backend endpoint (generate IG draft) returning template C — consistent, testable, allows future LLM swap.
   - Recommendation: Backend endpoint (mirrors Facebook pattern) for consistency; can be deterministic template C now.

4. **IG status in ReviewQueue list (REVW-01 mentions “status independente por plataforma”)**
   - What we know: `ReviewRow` currently shows a single social status badge derived from Facebook `socialStatus` prop. REVW-01 says “exibe seção Instagram ao lado do Facebook com toggle por vaga e status independente por plataforma.” (in review dialog context). The CONTEXT says “foca em REVW-01..04 no diálogo/experiência de revisão conforme escopo.” and code_context notes “ReviewRow.tsx — pode precisar refletir status IG independente no futuro, mas Phase 30 foca em…” 
   - Recommendation: For Phase 30, **prioritize EditJobDialog** (section + toggle + caption + preview + readiness). Status badge per platform in the queue row can be deferred unless trivial; planner should confirm scope (REVW-01 text says “Diálogo de revisão exibe seção…” so primary is dialog; queue badges may be a small enhancement). 

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified beyond existing backend/frontend runtimes, DB, and Meta/IG config already in place). This phase is primarily code/config/UI changes over existing services.

## Validation Architecture

> `workflow.nyquist_validation` is not explicitly set to false in `.planning/config.json` (treat as enabled). Include this section.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Backend: pytest (repo standard). Frontend: not explicitly configured in scanned files (no jest/vitest config found in quick grep) — likely manual/E2E or minimal unit tests; follow existing patterns. |
| Config file | Backend: `pytest.ini`/`pyproject.toml` (repo) — not re-verified here; assume existing. Frontend: none detected for unit tests in this phase scope. |
| Quick run command (backend) | `cd backend && pytest -q` (or targeted test files for admin/social/media) |
| Full suite command (backend) | `cd backend && pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REVW-01 | Dialog shows Instagram section below Facebook with independent toggle and status context | Manual/UI (frontend) | N/A (no frontend unit harness detected) | ❌ manual verification |
| REVW-02 | Caption editor enforces live counter `N/2200` and blocks save/approve when >2200 | Manual/UI + backend validation tests | Backend: add tests for IG draft save/generate rejecting >2200 if server-enforced | ❌ Wave 0 (backend tests likely needed) |
| REVW-03 | UI warns when >30 hashtags and shows guidance about non-clickable links + “link na bio” | Manual/UI | N/A | ❌ manual |
| REVW-04 | Preview shows exact intended IG image via prepare endpoint (loading/error states) | Manual/UI + backend integration tests exist for prepare/public media (`test_public_ig_media.py`, `test_ig_media_validation.py`) | `cd backend && pytest tests/test_public_ig_media.py tests/test_ig_media_validation.py -q` | ✅ (backend media) |

### Sampling Rate
- **Per task commit:** Run targeted backend tests related to changed files (e.g. `pytest tests/test_ig_media_validation.py -q` if touching media-adjacent logic; otherwise relevant admin/social tests).
- **Per wave merge:** `cd backend && pytest -q`
- **Phase gate:** Backend suite green for touched areas + manual UI verification of REVW-01..04 flows (with/without IG ready, invalid image case, caption limits/warnings).

### Wave 0 Gaps
- [ ] Backend tests for Instagram draft/status endpoints (if added): cover create/get/update IG draft, provider isolation from Facebook, caption length validation (>2200 rejected), and status retrieval.
- [ ] (Optional) Frontend test setup not present — rely on manual verification checklist in PLANs.

*(Existing backend media tests already cover prepare/public media behavior; no new framework install needed.)*

## Security Domain

> `security_enforcement` not set to false in config → include this section.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Admin endpoints require JWT (`require_admin`) — already enforced for all `/admin/*` routes |
| V3 Session Management | yes | Frontend uses token from `TOKEN_KEY`, handles 401 → redirect to login (existing pattern in `EditJobDialog`) |
| V4 Access Control | yes | IG draft/status/media prepare are admin-only; no public write paths added |
| V5 Input Validation | yes | Validate caption length (<=2200) server-side; validate hashtag warning is UI-only (not security). Sanitize/limit stored text same as Facebook flow (`sanitize_and_enforce_policy` patterns exist for Facebook — consider reusing for IG). |
| V6 Cryptography | no | No new secrets stored; uses existing encrypted token storage for Meta accounts |

### Known Threat Patterns for {stack}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Oversized/unbounded caption stored | Tampering/DoS (storage) | Enforce 2200 char limit server-side on IG draft save/generate endpoints |
| Unauthorized access to IG draft/media endpoints | Elevation of Privilege | Keep under `/admin/*` with `require_admin` (already the case for prepare and social endpoints) |
| Information disclosure via error messages | Info Disclosure | Reuse existing safe pt-BR error handling; do not leak tokens/Graph details (already done in `meta_oauth`, `image_media`) |

## Sources

### Primary (HIGH confidence)
- Direct code inspection:
  - `frontend/app/admin/review/EditJobDialog.tsx` (Facebook section structure, state, API calls)
  - `frontend/lib/api.ts` (social + meta integration + error handling patterns)
  - `backend/app/api/v1/admin.py` (media prepare route, social draft/status endpoints, approval flow)
  - `backend/app/schemas/social_posts.py`, `backend/app/models/social_post.py` (provider model)
  - `backend/app/crud/social_posts.py` (provider-scoped CRUD)
  - `backend/app/services/social/image_media.py`, `backend/app/schemas/social_media.py` (prepare/validation contracts)
  - `backend/app/services/social/meta_oauth.py`, `backend/app/schemas/social_integrations.py` (IG readiness resolution/storage)
  - `frontend/app/admin/integracoes/IntegrationsClient.tsx` (IG readiness UI patterns, link to `/admin/integracoes`)
  - `backend/app/api/v1/public.py` (public IG media serving)
- Project docs:
  - `.planning/phases/30-instagram-review-experience/30-CONTEXT.md`
  - `.planning/phases/29-meta-ig-readiness-media-foundation/29-CONTEXT.md`
  - `.planning/REQUIREMENTS.md` (REVW-01..04)
  - `.planning/ROADMAP.md`, `.planning/STATE.md`

### Secondary (MEDIUM confidence)
- None beyond primary code/docs (this is an internal codebase phase; no external library/version uncertainty for the specific UI/API changes described).

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all components inspected in repo; no new external deps.
- Architecture: HIGH — patterns derived directly from existing Facebook flow + Phase 29 endpoints/schemas.
- Pitfalls: HIGH — grounded in current code hardcodings (provider="facebook"), D-07/D-05 constraints, and known Phase 29 behaviors.

**Research date:** 2026-11-23
**Valid until:** 2026-12-23 (stable internal codebase patterns; revisit if Phase 31 changes social post model/pipeline significantly)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | “Publish to Instagram for this job” is best persisted as an IG `SocialPost` row (`provider='instagram'`) (draft/scheduled states later), consistent with Facebook flow | Architecture Patterns / Open Questions | If a different flag model is chosen, API and UI state management will differ; planner must decide explicitly |
| A2 | Phase 30 will add Instagram-specific admin endpoints (e.g. `/admin/jobs/{id}/instagram/social-post*`) rather than generalizing existing Facebook endpoints now | Architecture Patterns (Pattern 2) | If generalized, frontend/api.ts changes and tests are broader; risk of regressions higher but design cleaner |
| A3 | Template C caption generation for IG is implemented server-side (deterministic) in Phase 30, not client-only | Code Examples / Open Questions | If client-only, backend cannot validate/enforce consistently; recommend server-side |

**If this table is empty:** N/A

## Open Questions

1. **Toggle persistence (“Publicar no Instagram desta vaga”)**
   - What we know: D-04 requires a per-job toggle; Facebook uses `SocialPost` records.
   - What's unclear: Should enabling IG create an IG `SocialPost` draft immediately (empty/template) or only mark intent? Should disabling delete the IG draft row?
   - Recommendation: Create/update IG `SocialPost` with `provider='instagram'` when toggled on (seed with template C if none). When toggled off, either set a local UI state only? No — must persist. Recommend: if user turns off, keep the draft row but treat as “disabled for publishing” via a field or by convention (e.g. a separate flag). But `SocialPost` has no `enabled` flag today. Simplest: store enabled state implicitly? Or add `enabled_for_instagram` to Job? Or add a column to `social_posts` (e.g. `publish_enabled`). This needs a planner decision; flag as **needs decision**.

2. **IG social status endpoint shape**
   - What we know: REVW-01 wants “status independente por plataforma” in review context. Current `GET /admin/jobs/{id}/social-status` returns Facebook item only.
   - What's unclear: Add `GET /admin/jobs/{id}/instagram/social-status`, or change response to include both providers?
   - Recommendation: Add a dedicated IG status endpoint for clarity in Phase 30; Phase 31 can unify if desired.

3. **Server-side enforcement of 2200 char limit and hashtag warning**
   - What we know: D-08 says “não permitir salvar/aprovar legenda acima do limite (2200). Validação também no backend quando aplicável.” Hashtag warning is “não bloqueante”.
   - What's unclear: Exact backend error shape/message for IG caption too long.
   - Recommendation: Mirror Facebook draft save validation style; return 422 with pt-BR message like “Legenda do Instagram deve ter no máximo 2200 caracteres.” 

## Security Domain (duplicate short note)
See “Security Domain” section above. Key points: keep IG admin endpoints behind `require_admin`, validate caption length server-side, reuse safe error messages, no new secret storage.

## Sources (repeat for clarity)
### Primary (HIGH confidence)
- Repo source files listed in “Primary (HIGH confidence)” under Sources.

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None.