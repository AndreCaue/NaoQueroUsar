# Phase 29: Meta/IG Readiness & Media Foundation - Research

**Researched:** 2026-11-23
**Domain:** Meta/Instagram readiness, public media serving, deterministic job-card generation
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Origem principal = **card gerado sempre**, determinístico a partir dos dados da vaga. Sem upload manual e sem logo de empresa no v1.5.
- **D-02:** Geração/atualização do card acontece ao **abrir/preparar revisão** (ou fluxo equivalente de preparação do draft), de forma que o preview use a mesma imagem pretendida para publicação.
- **D-03:** Se dados relevantes da vaga mudarem antes da publicação, o card deve ser **regenerado automaticamente**; preview/publicação devem usar a versão atual.
- **D-04:** Imagem ausente/inválida **bloqueia apenas Instagram**. Aprovação/publicação Facebook/site não são bloqueadas por problema de imagem IG (preserva independência, alinha com PUBL-01).
- **D-05:** Formato padrão: **1080x1350 (retrato 4:5)**, JPEG sRGB, <8MB, compatível com IMAG-02 (proporção 4:5–1.91:1).
- **D-06:** Estilo visual: **Dark brand EmpregaNoix** — fundo escuro, acentos roxos (#8b5cf6/#a78bfa, fundos #0f0a1a/#1a1025), identidade EmpregaNoix, CTA "link na bio", legível no feed.
- **D-07:** Conteúdo do card: **essencial sem contato** — título, empresa (se houver), cidade/remoto, tipo/contrato e salário quando disponível; CTA "link na bio". Não incluir WhatsApp/e-mail/telefone no card.
- **D-08:** Estratégia de geração: **Pillow/PIL no backend Python/FastAPI**, determinística; implementação deve cuidar de fontes, quebra de texto e limites de tamanho/qualidade JPEG.
- **D-09:** Servir imagem por **endpoint público no backend** (sem depender de R2/S3/DB blob como infraestrutura primária no v1.5).
- **D-10:** Estratégia de obtenção: **gerar sob demanda + cache**. Se não houver arquivo/cache válido, gerar a partir da vaga e cachear (disco/volume quando disponível); deve tolerar reconstrução após perda de cache efêmero.
- **D-11:** Identificação da URL: **por job ID com versão/hash** (ex.: query `v={hash}` ou path versionado). A URL deve representar a imagem exata pretendida, suportar proveniência e facilitar invalidação/cache.
- **D-12:** Base pública da URL vem de **env explícita** (ex.: `BACKEND_PUBLIC_URL` ou `MEDIA_PUBLIC_BASE_URL`; nome exato em OpenCode's Discretion), não inferida de `SITE_PUBLIC_URL`. A URL final deve ser HTTPS pública, não-localhost, sem auth, e validada antes do publish.
- **D-13:** Modelagem: **estender `SocialAccount`** com campos de prontidão IG (ex.: `ig_user_id`, identificador/username IG quando disponível, estado/readiness, timestamps/erros seguros conforme necessário). Uma conexão por página; reutiliza token/fluxo Meta existente.
- **D-14:** Resolução/atualização de `ig-user-id` e prontidão: ao **conectar/concluir OAuth-seleção de página** e ao **verificar agora/status** quando aplicável. Não consultar Graph em toda leitura de status por padrão.
- **D-15:** Conexões Facebook existentes que não tenham escopos IG necessários devem entrar em estado **acionável de reconexão/reautorização** para obter novos escopos. Estado claro, sem quebrar integração Facebook.
- **D-16:** Estratégia de token/expiração: **alerta + reconexão**. Detectar invalidação/expiração via verificação e erros de publicação; marcar `needs_reconnect` com orientação clara. Sem renovação automática complexa no v1.5.

### OpenCode's Discretion
- Nome exato da env de base pública de mídia (desde que explícita, documentada e validada).
- Nome exato dos campos/colunas IG em `SocialAccount` e shape do schema de status, desde que atendam META-01/02 e não exponham segredos.
- Layout visual exato do card (tipografia, espaçamento, hierarquia), desde que siga D-05/D-06/D-07 e seja determinístico/legível.
- Estratégia de cache (memória/disco/chave), TTL e invalidação interna, desde que a URL pública sirva a imagem exata pretendida e seja reconstruível.
- Heurística de hash/versionamento (campos incluídos), desde que mudanças relevantes nos dados do card gerem nova versão.
- Momento técnico exato de "preparar revisão" para geração (endpoint explícito, hook de draft, ou lazy generate no preview), desde que cumpra D-02/D-03 e mantenha UX clara.

### Deferred Ideas (OUT OF SCOPE)
- Upload manual de imagem na revisão — adiado; v1.5 usa card gerado sempre. Reavaliar em fase futura se houver demanda.
- Logo/arte por empresa como origem primária — adiado; exigiria modelagem/cadastro de marca por empresa.
- Renovação automática de token Meta — adiado; v1.5 usa alerta + reconexão.
- Object storage/CDN dedicado para mídia IG (R2/S3) — adiado; v1.5 usa endpoint público no backend com cache/reconstrução.
- Stories/Reels/carrossel/vídeo, agendamento, métricas, múltiplas contas IG — permanecem fora de escopo (PROJECT.md).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| META-01 | Admin vê no Integrações o estado de prontidão do Instagram para a Página Facebook selecionada (conta IG Business/Creator vinculada, `ig-user-id` resolvido/armazenado, permissões/escopos necessários presentes) com estado acionável de reconexão/correção. | Extend `SocialAccount` with IG readiness fields, extend `meta_oauth` scope/status/verify flow, add IG readiness schema/UI section in Integrações; actionable reconnect state without breaking FB. |
| META-02 | Backend resolve e persiste `ig-user-id` a partir da Página Facebook vinculada reutilizando o fluxo/token Meta existente; linkage ausente/inválido é tratado com erro seguro e não quebra a integração Facebook. | Resolve `instagram_business_account` at connect/selection and verify-now; persist safe IG fields; map missing/invalid linkage to actionable IG-not-ready state and safe pt-BR messages. |
| META-03 | Projeto documenta permissões/escopos Meta atuais, premissas de App Review/Advanced Access/roles/tasks e checklist manual de setup/verificação Instagram. | Update `docs/META-INTEGRATION-TESTING.md` (or add a focused IG section) with scopes, Page↔IG linkage, app mode/review assumptions, env vars, troubleshooting, and explicit "manual verification required" checklist. |
| IMAG-01 | Publicação no Instagram exige imagem válida; a revisão bloqueia publish IG sem imagem válida com feedback claro em pt-BR. | Define image validation contract/service and admin-facing validation result; Phase 29 provides backend contract/UI feedback primitives, Phase 30 wires review block, Phase 31 enforces publish guard. |
| IMAG-02 | Sistema gera card fallback determinístico a partir dos dados da vaga (1080x1080 ou 1080x1350, JPEG sRGB, <8MB, proporção compatível 4:5–1.91:1) quando não houver imagem de origem selecionada/disponível. | D-01/D-05 lock 1080x1350 generated card; Pillow renderer + font bundling + deterministic hash/version from job card fields. |
| IMAG-03 | A imagem usada no Instagram é servida por URL pública HTTPS estável, acessível pela Meta (sem auth, não localhost/privada/efêmera), com validação, preview e proveniência registrada. | Public backend media endpoint, explicit media base URL env, version/hash URL, on-demand generate+cache with rebuild, validation before publish, provenance metadata. |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- No direct repo edits outside GSD workflow unless user explicitly bypasses (`/gsd-*` workflow enforcement). This research output is the GSD artifact for planning.
- Stack fixed: Next.js 16 App Router + Tailwind dark theme; FastAPI async + SQLAlchemy 2.0 + Alembic + Neon Postgres; Groq; Cloudflare Turnstile; Vercel + Railway/Render.
- Admin único; pt-BR locale; dark purple EmpregaNoix brand.
- Security: secrets/tokens backend-only, never logged/exposed; Turnstile server-side patterns; env-driven config.
- Existing social integration patterns: site-first, best-effort social, encrypted tokens at rest, safe pt-BR errors, idempotent publish pipeline.

## Summary

Phase 29 should be planned as a **foundation contract phase**, not a full Instagram publishing phase. It extends the existing Meta/Facebook connection so admins can confirm Instagram readiness, and it introduces a deterministic, publicly fetchable media primitive that Phase 30/31 can consume. The codebase already has the right seams: `meta_oauth.py` owns Meta OAuth/token/debug/pending/verify, `SocialAccount` stores the encrypted Page token, integrations UI already renders actionable connection states, and the social pipeline already has safe error/idempotency conventions.

The main planning risk is accidental coupling: IG readiness must not change Facebook semantics, and image/media contracts must be reusable by review/publish without forcing Phase 29 to implement those future flows. The plan should therefore produce three concrete outputs: (1) IG readiness data + API/UI, (2) deterministic card generation + public media endpoint + validation/provenance contract, and (3) operational Meta/IG documentation/checklist. Downstream phases should consume stable contracts (readiness fields, media URL/version/hash, validation result, and actionable error states) rather than re-deciding them.

**Primary recommendation:** Extend `SocialAccount`/Meta OAuth/Integrações for additive IG readiness, add a dedicated Pillow-based IG media service with a public backend URL keyed by `job_id + version/hash`, and document explicit Meta scope/reconnect assumptions — all without changing Facebook publish behavior.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| IG readiness state and actionable reconnect | API / Backend | Frontend admin UI | Backend resolves Graph/linkage/token state authoritatively; UI renders safe actionable status. |
| `ig-user-id` resolution and persistence | API / Backend | Database / Storage | Uses encrypted Page token and Graph calls; persisted on `SocialAccount`. |
| Meta OAuth scope upgrade / reconnect flow | API / Backend | Frontend admin UI | Scope list, callback, verify, and token checks are backend-owned; UI only triggers/reflects. |
| Deterministic IG card generation | API / Backend | OS/Build artifacts (fonts) | Pillow rendering is deterministic server-side; fonts/assets must be bundled/reproducible. |
| Public media URL serving for Meta fetch | API / Backend | CDN/Static (future only) | D-09 requires backend public endpoint in v1.5; Meta fetches over HTTPS. |
| Image validity blocking for Instagram | API / Backend | Frontend admin UI | Backend owns validation contract; Phase 30 UI enforces block with pt-BR feedback, Phase 31 revalidates before publish. |
| Meta/IG operational checklist | Project docs / Ops | API / Backend config | Manual App Review/roles/tasks are operational; docs must reflect actual env/config names. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| FastAPI | 0.143.0 (pyproject) | Admin/public endpoints for readiness and media | Already used by integrations/public/admin routers; async and Pydantic-native. | HIGH [VERIFIED: backend/pyproject.toml] |
| SQLAlchemy + Alembic | 2.1.4 / 1.20.0 (pyproject) | `SocialAccount` extension and optional media/provenance persistence | Existing migration/model pattern; async sessions in use. | HIGH [VERIFIED: backend/pyproject.toml, 0004_social_foundation.py] |
| httpx | 0.28.1 (pyproject) | Meta Graph calls and future Meta fetch validation patterns | Already used by `meta_oauth.py` and Facebook publisher. | HIGH [VERIFIED: backend/pyproject.toml, meta_oauth.py] |
| Pillow | 13.0.0 (latest verified; not yet in pyproject) | Deterministic 1080x1350 JPEG card generation | Standard Python imaging lib; fits D-08; supports text/draw/JPEG/RGB. | HIGH [VERIFIED: `python -m pip index versions Pillow` on 2026-11-23 returned LATEST 13.0.0] |
| Next.js / React | 16.4.6 / 19.1.1 (package.json) | Integrations admin UI extension | Existing admin surface and patterns. | HIGH [VERIFIED: frontend/package.json] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| cryptography/Fernet | 50.0.2 (pyproject) | Encrypt sensitive stored token/pending payloads | Reuse for any persisted sensitive Meta token data; never plaintext. [VERIFIED: pyproject, crypto.py] |
| Pydantic v2 | 2.14.1 (pyproject) | Extend integration/media schemas | Status responses, validation payloads, admin/public contracts. [VERIFIED] |
| pytest / pytest-asyncio | 9.1.1 / >=1.0.0,<2.0.0 | Backend unit/integration coverage | Media renderer, URL validation, meta_oauth IG readiness, endpoint contracts. [VERIFIED] |
| Vitest | ^2.1.9 (package.json) | Frontend utility/component tests where viable | Integration UI state mapping/helpers; optional if component harness exists. [VERIFIED] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Backend Pillow renderer | Playwright/HTML-to-image | More visual flexibility but heavy runtime/browser deps and operational fragility; conflicts with v1.5 simplicity. |
| Backend public media endpoint | R2/S3/CDN object storage | Better durability/scale, but explicitly deferred by D-09/D-33; adds infra/credentials/failure modes. |
| DB-persisted media bytes | Ephemeral disk only | Disk-only is fragile on redeploy/restart; D-10 allows cache but requires rebuildability. Persisting bytes/metadata in Postgres is acceptable at current scale. |
| Separate IG SocialAccount row | Extend existing SocialAccount | Separate row duplicates encrypted token and complicates "one connection per page"; D-13 locks extension. |

**Installation:**
```bash
# backend
uv add "Pillow==13.0.0"
# optional only if a future upload decision is made (NOT in v1.5 per D-01)
# uv add "python-multipart>=0.0.22,<1.0"
```

**Version verification:** `python -m pip index versions Pillow` run 2026-11-23 reported `LATEST: 13.0.0`, `INSTALLED: 12.2.0` in current environment. Pin `Pillow==13.0.0` in `backend/pyproject.toml` when implementing. [VERIFIED: local command]

## Architecture Patterns

### System Architecture Diagram

```text
Admin (/admin/integracoes)
  -> GET /api/v1/admin/integrations/meta/status
  -> POST /api/v1/admin/integrations/meta/verify
  -> POST /api/v1/admin/integrations/meta/oauth/start
        |
        v
FastAPI integrations router
        |
        v
meta_oauth service (existing, extend)
  - OAuth state/exchange/pending page selection
  - debug_token / connection verification
  - resolve Page -> instagram_business_account
  - classify IG readiness + safe actionable errors
        |
        +--> Meta Graph API (config-driven META_GRAPH_VERSION)
        |
        +--> Postgres social_accounts (encrypted page token + IG readiness fields)

Admin review preparation (Phase 29 contract, consumed by Phase 30)
  -> POST/GET /api/v1/admin/jobs/{id}/instagram/media/prepare-or-get (name discretionary)
        |
        v
IG media service (new)
  - load Job
  - compute card version hash from relevant fields
  - validate/generate 1080x1350 JPEG (Pillow)
  - persist/reuse cached asset metadata/bytes/path
  - return preview URL + validation + provenance
        |
        +--> Postgres social_media_assets / cache table (recommended durable storage)
        |
        +--> Public endpoint GET /api/v1/public/ig-media/{job_id}/{version_or_token}.jpg
                    |
                    v
              Meta fetcher / browser preview
              (no auth, HTTPS, public, non-localhost)
```

### Recommended Project Structure

```text
backend/
├── app/
│   ├── api/v1/
│   │   ├── integrations.py          # extend IG readiness status/verify responses
│   │   ├── admin.py                 # add IG media prepare/validate endpoint (or dedicated router)
│   │   └── public.py                # add public IG media serving endpoint (no auth)
│   ├── core/config.py               # add explicit MEDIA_PUBLIC_BASE_URL and IG/media settings
│   ├── models/
│   │   ├── social_account.py        # extend with IG readiness fields
│   │   └── social_media_asset.py    # NEW: durable media metadata/bytes/cache identity
│   ├── schemas/
│   │   ├── social_integrations.py   # extend status/action payloads with safe IG readiness
│   │   └── social_media.py          # NEW: media prepare/validate/preview contracts
│   ├── crud/
│   │   ├── social_accounts.py       # IG readiness-aware lookup/update helpers
│   │   └── social_media.py          # NEW: asset get/create/upsert by job/version
│   └── services/social/
│       ├── meta_oauth.py            # extend scopes, resolve IG account, readiness evaluation
│       ├── instagram_readiness.py   # NEW: isolate IG-specific Graph/readiness rules
│       ├── image_card.py            # NEW: deterministic Pillow renderer
│       └── image_media.py           # NEW: hash/version/cache/public URL/validation
├── alembic/versions/0006_*.py       # IG readiness + media asset migration(s)
├── assets/fonts/                    # bundled deterministic fonts (OFL/Apache licensed)
└── tests/
    ├── test_meta_oauth_instagram.py
    ├── test_instagram_readiness.py
    ├── test_social_media_card.py
    └── test_public_ig_media.py

frontend/
├── app/admin/integracoes/IntegrationsClient.tsx  # show IG readiness/actionable states
├── lib/api.ts                                    # extend MetaIntegrationStatus/types
└── app/admin/review/*                            # NO functional regression in Phase 29

docs/
└── META-INTEGRATION-TESTING.md                   # extend with IG scopes/readiness/checklist (META-03)
```

### Pattern 1: Additive IG Readiness on Existing Meta Connection
**What:** Extend the existing Facebook Page connection record to also carry Instagram readiness, resolved from the same Page/token.
**When to use:** META-01/META-02; any integration status/verify/connect flow.
**Example:**
```python
# Source: backend/app/services/social/meta_oauth.py + Meta Graph pattern (CITED)
# Extend scopes (exact set validated during implementation; do not drop existing FB scopes)
META_OAUTH_SCOPES = (
    "pages_show_list,pages_manage_posts,pages_read_engagement,"
    "instagram_basic,instagram_content_publish"
)

# Resolve linked IG business account from selected Page
# GET /{page-id}?fields=instagram_business_account{id,username}
# Use stored encrypted Page token; never log token.
data = await _graph_get_json(
    f"{_graph_base(settings)}/{page_id}",
    {
        "fields": "instagram_business_account{id,username}",
        "access_token": page_access_token_plain,
    },
)
ig = (data.get("instagram_business_account") or {}) if isinstance(data, dict) else {}
ig_user_id = str(ig.get("id")) if ig.get("id") else None
ig_username = ig.get("username") if isinstance(ig.get("username"), str) else None
```

### Pattern 2: Separate FB Connection Status from IG Readiness
**What:** Keep `SocialAccount.status` semantics for Facebook connection health; represent IG as additive readiness fields/state.
**When to use:** D-15 requires FB not broken when IG scopes/linkage missing.
**Example:**
```python
# Recommendation (OpenCode's Discretion, grounded by D-13/D-15)
# social_accounts additions:
# ig_user_id: str | None
# ig_username: str | None
# ig_readiness: "ready" | "missing_linkage" | "missing_scopes" | "needs_reconnect" | "unknown"
# ig_last_checked_at: datetime | None
# ig_last_error_code: str | None  # safe internal code, not raw provider dump
# ig_last_error_message: str | None  # safe pt-BR

# FB remains connected for Facebook publish; IG UI shows actionable correction:
# "Instagram não está pronto: reconecte a Página para conceder as permissões do Instagram."
```

### Pattern 3: Deterministic Media Version Hash
**What:** Compute a stable version/hash from the card-relevant job fields and template version. Same input => same hash => same URL/version.
**When to use:** D-02/D-03/D-11/IMAG-03.
**Example:**
```python
# Source pattern: deterministic hash (standard Python hashlib) [CITED: Python docs]
import hashlib, json

CARD_TEMPLATE_VERSION = "ig-card-v1"

def compute_ig_card_hash(job) -> str:
    payload = {
        "template": CARD_TEMPLATE_VERSION,
        "title": job.title or "",
        "company": job.company or "",
        "city": job.city or "",
        "contract_type": getattr(job, "contract_type", None) or getattr(job, "employment_type", None) or "",
        "salary": job.salary or "",
        # D-07: no contacts in card; do not include contact fields
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
```

### Pattern 4: Public, Authless, Rebuildable Media Endpoint
**What:** Serve image bytes through a backend public route. Cache if possible, regenerate on miss from Job data.
**When to use:** D-09/D-10/D-11/D-12/IMAG-03.
**Example:**
```python
# FastAPI Response pattern [CITED: FastAPI Custom Response docs]
from fastapi import Response, HTTPException

@router.get("/public/ig-media/{job_id}/{version}.jpg")
async def get_public_ig_media(job_id: UUID, version: str, session=Depends(get_session)):
    asset = await media_service.get_or_build_public_asset(session, job_id, version)
    if asset is None:
        raise HTTPException(status_code=404, detail="Mídia não encontrada")
    return Response(
        content=asset.bytes,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "Content-Disposition": 'inline; filename="vaga-instagram.jpg"',
        },
    )
```

### Anti-Patterns to Avoid
- **Querying Graph on every status GET:** Violates D-14 and creates avoidable latency/rate-limit risk. Status should read persisted readiness; verify-now/connect flows refresh.
- **Breaking FB on IG scope gaps:** Do not flip the whole account to unusable for Facebook posting when only IG is not ready; expose IG readiness as actionable separate state.
- **Inferring public media base from request host or SITE_PUBLIC_URL:** Violates D-12 and risks localhost/private URLs. Use explicit env and validate HTTPS/public/non-localhost.
- **Ephemeral-only cache with no rebuild path:** Violates D-10. Disk cache is optimization; Job + template hash must be enough to rebuild.
- **Rendering with OS-dependent fonts:** Produces non-deterministic cards across dev/CI/deploy. Bundle fonts in repo and load by explicit path.
- **Putting contacts on card:** Violates D-07 and weakens the existing contact-protection posture.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OAuth state/signing | Custom ad-hoc state tokens | Existing `build_meta_oauth_state`/JWT HS256 pattern in `meta_oauth.py` | Already has TTL/purpose/nonce; extending is safer. [VERIFIED: meta_oauth.py] |
| Token encryption | Plaintext columns or custom crypto | Existing Fernet helpers `encrypt_token/decrypt_token` | Secret-at-rest rule already established. [VERIFIED: crypto.py] |
| Image rendering primitives | Manual pixel/font raster logic | Pillow (`Image`, `ImageDraw`, `ImageFont`) | Handles JPEG encoding, text measurement, RGB conversion. [CITED: Pillow docs] |
| Public image bytes response | Custom streaming framework | FastAPI `Response`/`StreamingResponse` | Simple, documented, correct content-type/header control. [CITED: FastAPI docs] |
| Graph HTTP plumbing | Raw urllib/error soup | Existing httpx + safe error classification patterns | Codebase already standardizes timeouts/safe failures. [VERIFIED] |
| Version/hash invalidation | Random UUID per request | Deterministic SHA-256 over canonical card payload | Satisfies D-03/D-11 and makes preview/publish provenance testable. |

**Key insight:** Phase 29 is mostly careful extension of existing Meta/social patterns plus one focused media primitive. New abstractions should be small and isolated (`instagram_readiness.py`, `image_card.py`, `image_media.py`), not a new social platform framework.

## Common Pitfalls

### Pitfall 1: IG Readiness Breaks Facebook
**What goes wrong:** Missing IG scopes/linkage causes whole integration to become `needs_reconnect`/disconnected for FB.
**Why it happens:** Reusing a single status enum without additive IG readiness.
**How to avoid:** Keep FB connection status authoritative for FB; add IG readiness fields and UI messages. Only mark FB `needs_reconnect` on definitive token invalidation affecting FB connection. [VERIFIED: D-15, meta_oauth.py status model]
**Warning signs:** Existing FB-connected account shows disconnected after IG scope upgrade detection; FB publish blocked by IG-only issue.

### Pitfall 2: Meta Cannot Fetch the "Public" Image
**What goes wrong:** Preview works in admin but IG publish fails because URL is localhost, auth-gated, private, HTTP, or ephemeral.
**Why it happens:** Reusing internal/admin URLs or request host.
**How to avoid:** D-12 explicit public base env; validate HTTPS, public hostname, no localhost/private IP literals; serve via unauthenticated route; rebuild on cache miss. [CITED: Meta Content Publishing requires publicly accessible image URL]
**Warning signs:** URL contains `localhost`, `127.0.0.1`, private IP, auth path, or depends on dev tunnel absent in prod.

### Pitfall 3: Preview/Publish Image Drift
**What goes wrong:** Admin previews one image, publish uses another after job edits or cache inconsistency.
**Why it happens:** No version/hash tied to card-relevant job data.
**How to avoid:** Deterministic hash over relevant fields + template version; D-02/D-03 prepare flow regenerates when hash changes; URL includes version. [VERIFIED: D-02/D-03/D-11]
**Warning signs:** Card URL lacks version; changing job title/salary keeps same URL.

### Pitfall 4: Non-deterministic Card Rendering
**What goes wrong:** Same job renders differently across machines/deploys; tests flaky; hash/provenance unreliable.
**Why it happens:** OS fonts, locale-dependent formatting, random layout, timestamp overlays.
**How to avoid:** Bundle font files, fixed template constants, explicit text wrapping, no "generated at" timestamp in image, stable sort/order, RGB/JPEG output settings. [VERIFIED: D-01/D-08]
**Warning signs:** Renderer reads system fonts; image includes current datetime; tests compare PNG bytes without fixed environment.

### Pitfall 5: Graph Scope Upgrade Not Actionable
**What goes wrong:** Existing FB connections technically connected but missing IG permissions; IG publish later fails obscurely.
**Why it happens:** OAuth scopes updated in code but old grants not detected/surfaced.
**How to avoid:** Store/evaluate IG readiness; when `instagram_business_account` cannot be resolved due to missing permission or missing linkage, set actionable IG state and UI CTA to reconnect/re-authorize. [VERIFIED: D-15, META-01]
**Warning signs:** Status says connected but has no `ig_user_id`; verify-now returns generic success.

### Pitfall 6: Unsafe Error/Secret Leakage
**What goes wrong:** Tokens, raw Graph payloads, or internal exception details appear in logs/UI.
**Why it happens:** Reusing debug logging during Graph integration.
**How to avoid:** Follow `meta_oauth.py` pattern: map exceptions to safe pt-BR messages, log only error type/code class/safe identifiers. Never include `access_token`, encrypted blobs, or raw provider body. [VERIFIED: meta_oauth.py, social pipeline]
**Warning signs:** Logs include query params, response bodies, or token-like strings.

## Code Examples

### Extend MetaIntegrationStatus with additive IG readiness
```python
# Source pattern: backend/app/schemas/social_integrations.py [VERIFIED]
from typing import Literal
from pydantic import BaseModel

class MetaInstagramReadiness(BaseModel):
    ready: bool
    ig_user_id: str | None = None
    ig_username: str | None = None
    state: Literal[
        "ready",
        "not_connected",
        "missing_linkage",
        "missing_permissions",
        "needs_reconnect",
        "unknown",
    ]
    message: str | None = None  # safe pt-BR actionable message

class MetaIntegrationStatus(BaseModel):
    provider: Literal["facebook"] = "facebook"
    status: Literal["connected", "needs_reconnect", "disconnected"]
    page_id: str | None = None
    page_name: str | None = None
    connected_at: datetime | None = None
    token_checked_at: datetime | None = None
    pending_selection: bool = False
    alert: MetaIntegrationAlert | None = None
    instagram: MetaInstagramReadiness | None = None  # additive, non-breaking
```

### Validate explicit public media base URL
```python
# Source pattern: backend/app/core/config.py validators [VERIFIED]
from urllib.parse import urlparse
import ipaddress

def validate_public_https_base(url: str, field_name: str) -> str:
    value = (url or "").strip()
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        raise ValueError(f"{field_name} deve ser uma URL HTTPS pública válida")
    if host in {"localhost"} or host.endswith(".local"):
        raise ValueError(f"{field_name} não pode apontar para host local")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            raise ValueError(f"{field_name} não pode apontar para IP privado/local")
    except ValueError:
        # hostname (non-IP) is acceptable if HTTPS/public
        pass
    return value.rstrip("/")
```

### Prepare/serve deterministic IG card
```python
# Source pattern: Pillow + FastAPI Response [CITED: Pillow docs, FastAPI docs]
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350  # D-05
BG = "#0f0a1a"
PURPLE = "#8b5cf6"

def render_ig_card(job, font_regular, font_bold) -> bytes:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # layout omitted: deterministic text wrapping, no contacts, CTA "link na bio"
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90, optimize=True, progressive=True, subsampling="4:2:0")
    data = buf.getvalue()
    # reduce quality deterministically if > 8MB (unlikely for text card)
    quality = 90
    while len(data) > 8 * 1024 * 1024 and quality >= 70:
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        data = buf.getvalue()
        quality -= 5
    return data
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Facebook-only Page connection status | Additive IG readiness on same Meta connection | Phase 29 (v1.5) | Admin can see IG linkage/scope problems before publish. |
| Text-only social draft preview | Deterministic media preview URL/version contract | Phase 29 (v1.5) | Enables Phase 30 exact preview and Phase 31 exact publish URL. |
| Ad-hoc image hosting assumptions | Explicit public backend media base URL + validation | Phase 29 (v1.5) | Prevents localhost/private URL failures with Meta fetch. |

**Deprecated/outdated:**
- Reusing Facebook caption/content assumptions for Instagram: keep separate IG-aware contracts (caption in Phase 30, image/media in Phase 29).
- Implicit request-host media URLs: insecure/unreliable for Meta; use explicit env.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | For Facebook Login / Page-linked IG publishing, the practical scope set for v1.5 is `pages_show_list,pages_manage_posts,pages_read_engagement,instagram_basic,instagram_content_publish`; `ads_management/ads_read` may be role-dependent. | Standard Stack / Architecture / META-02 | Missing scope causes IG readiness false-negative or publish failure; plan must include reconnect/verification messaging and manual checklist confirmation. |
| A2 | `GET /{page-id}?fields=instagram_business_account{id,username}` is the right readiness probe for linked IG professional account. | Architecture Patterns | Wrong field/permission assumption yields readiness errors; isolate in `instagram_readiness.py` and verify against current Meta docs before live rollout. |
| A3 | DB-backed durable asset storage (bytea or dedicated table) is acceptable at 100-500 jobs/month for 1080x1350 JPEG cards. | Architecture / Pitfalls | DB bloat or performance issues; mitigation: size cap, immutable cache key, optional future move to object storage. |
| A4 | Phase 29 can satisfy IMAG-01 by delivering validation contract and clear pt-BR feedback primitives, while Phase 30/31 enforce UI/publish blocking. | Phase Requirements / Open Questions | Scope mismatch if stakeholders expect full review-dialog blocking in Phase 29; plan must explicitly split contract vs enforcement. |

## Open Questions

1. **Where should the IMAG-01 "block Instagram publish" be enforced in Phase 29?**
   - What we know: IMAG-01 is assigned to Phase 29; Phase 30 owns review UX and Phase 31 owns publish pipeline. D-04 says block only Instagram.
   - What's unclear: Whether Phase 29 must add review-dialog blocking now or provide enforceable validation contracts consumed by Phase 30/31.
   - Recommendation: Plan Phase 29 to implement backend validation + actionable pt-BR reason codes and integrate enforcement at the nearest existing Phase 29-touched surface only if trivial; otherwise create explicit contracts/tests and ensure Phase 30/31 plans consume them. Do not silently claim full review UX complete.

2. **Media asset persistence shape: bytea in table vs filesystem cache + rebuild metadata?**
   - What we know: D-09 backend endpoint; D-10 generate on demand + cache and tolerate rebuild; deploy may be ephemeral.
   - What's unclear: Operational preference on Render disk persistence.
   - Recommendation: Store durable metadata and, at MVP scale, image bytes in Postgres (`social_media_assets`) or a bytea cache table keyed by job_id+hash; treat filesystem as optional hot cache. This satisfies rebuildability and Meta fetch stability.

3. **IG readiness when FB token is valid but lacks new IG scopes**
   - What we know: D-15 requires actionable reconnect/reautorização; must not break FB integration.
   - What's unclear: Whether to expose as `status=connected` + `instagram.needs_reconnect` or a distinct top-level state.
   - Recommendation: Keep top-level FB `status` unchanged when FB token remains valid for FB; add `instagram.state='missing_permissions'|'needs_reconnect'` with clear CTA. This preserves FB while making IG actionable.

4. **Exact "prepare review" hook for D-02**
   - What we know: EditJobDialog currently loads/generates FB draft on demand; Phase 30 will own IG review section.
   - What's unclear: Best minimal Phase 29 hook without building Phase 30 UI.
   - Recommendation: Add an idempotent admin endpoint like `POST /api/v1/admin/jobs/{id}/instagram/media/prepare` returning `{job_id, image_url, version_hash, valid, validation_errors, provenance}`. Phase 30 can call it on dialog open; endpoint can also be used by future publish guard.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Backend runtime/tests | ✓ | 3.14.5 (`python --version`) | — |
| Node.js | Frontend build/tests | ✓ | v24.14.1 | — |
| npm | Frontend package management | ✓ | 11.12.1 | — |
| uv | Backend dependency management (project uses uv.lock/pyproject) | ✓ | 0.11.6 | Use pip/venv only if uv unavailable |
| Pillow | IG card generation (new dependency) | ✗ in project deps / ✗ installed? (env had 12.2.0, not in pyproject) | Latest verified 13.0.0 | Add pinned dependency; tests can mock renderer but real renderer needed for IMAG-02 |
| PostgreSQL/Neon access | Migrations/runtime | ? | Unknown in local shell context | Use configured `DATABASE_URL`/`TEST_DATABASE_URL`; document in plan |
| Meta app credentials / IG-linked Page | Live OAuth/readiness verification | ? | — | Mock Graph in tests; manual checklist for live verification (META-03) |

**Missing dependencies with no fallback:**
- None blocking planning; live Meta credentials are required only for manual/live verification, not for code/test scaffolding.

**Missing dependencies with fallback:**
- Pillow not declared in `backend/pyproject.toml`: add `Pillow==13.0.0`. [VERIFIED: pyproject lacks Pillow; pip index shows 13.0.0]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-asyncio >=1.0.0,<2.0.0 (backend); Vitest ^2.1.9 (frontend) |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`, `asyncio_mode=auto`); `frontend/package.json` scripts |
| Quick run command | `cd backend && uv run pytest tests/test_meta_oauth_security.py -q` (baseline exists; Phase 29 adds targeted tests) |
| Full suite command | `cd backend && uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| META-01 | Integrações status exposes actionable IG readiness (linked/missing/reconnect) without secrets | integration/unit | `cd backend && uv run pytest tests/test_meta_oauth_instagram.py -q` | ❌ Wave 0 |
| META-02 | Resolve/persist `ig-user-id` from linked Page; missing/invalid linkage safe and FB not broken | unit/integration | `cd backend && uv run pytest tests/test_meta_oauth_instagram.py tests/test_integrations_instagram.py -q` | ❌ Wave 0 |
| META-03 | Operational docs/checklist contain required env/scopes/manual verification | unit/doc smoke | `cd backend && uv run pytest tests/test_docs_meta_instagram.py -q` | ❌ Wave 0 |
| IMAG-01 | Missing/invalid IG image produces clear pt-BR validation and blocks only IG path | unit/integration | `cd backend && uv run pytest tests/test_ig_media_validation.py -q` | ❌ Wave 0 |
| IMAG-02 | Deterministic 1080x1350 JPEG card, sRGB, <8MB, no contacts | unit | `cd backend && uv run pytest tests/test_ig_media_card.py -q` | ❌ Wave 0 |
| IMAG-03 | Public HTTPS non-auth URL serves exact versioned image; preview/provenance metadata available | integration | `cd backend && uv run pytest tests/test_public_ig_media.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && uv run pytest tests/test_meta_oauth_instagram.py tests/test_ig_media_card.py -q`
- **Per wave merge:** `cd backend && uv run pytest -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`; manual Meta checklist items recorded as handoff, not fabricated pass.

### Wave 0 Gaps
- [ ] `backend/tests/test_meta_oauth_instagram.py` — covers META-01, META-02
- [ ] `backend/tests/test_integrations_instagram.py` — covers integrations endpoint/schema safety
- [ ] `backend/tests/test_ig_media_card.py` — covers IMAG-02 determinism/size/format
- [ ] `backend/tests/test_ig_media_validation.py` — covers IMAG-01 validation contract
- [ ] `backend/tests/test_public_ig_media.py` — covers IMAG-03 public serving/version/provenance
- [ ] `backend/tests/test_docs_meta_instagram.py` — covers META-03 checklist presence (lightweight doc assertion)
- [ ] `backend/assets/fonts/` test fixture/font license note — deterministic render fixture
- [ ] Framework install: `cd backend && uv add "Pillow==13.0.0"`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (admin endpoints) | Existing `require_admin` + JWT; no new auth surface for public media except intentional unauthenticated read-only image. |
| V3 Session Management | yes | Reuse existing admin JWT/session handling; no new session cookies. |
| V4 Access Control | yes | Admin-only for readiness/prepare/verify endpoints; public only for specific media asset path by version/hash; never expose admin tokens. |
| V5 Input Validation | yes | Validate job IDs, version/hash format, env URLs, image dimensions/size/content type, Graph response shapes, safe error mapping. |
| V6 Cryptography | yes | Reuse Fernet for encrypted token storage; never store plaintext tokens; no custom crypto. |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Token/secret leakage in logs or API responses | Information Disclosure | Reuse `meta_oauth` safe logging/error mapping; schema allowlist fields; tests assert no token fields. |
| SSRF/private URL confusion for Meta media fetch | Spoofing / Information Disclosure | Explicit `MEDIA_PUBLIC_BASE_URL` HTTPS validation; reject localhost/private IP; serve known public route only. |
| Unauthorized access to admin readiness operations | Elevation of Privilege | `require_admin` on integrations/media prepare endpoints. |
| Public media endpoint enumeration / object exposure | Information Disclosure | Use deterministic but non-sensitive version hash; serve only intended JPEG media; do not include contacts/PII beyond already-public job card content; optional opaque token if needed. |
| Unbounded image generation/resource use | Denial of Service | Fixed 1080x1350 canvas, max text lengths/wrapping, JPEG size guard, cache by hash, no user-supplied image in v1.5. |
| Path traversal / arbitrary file read in media serving | Tampering / Information Disclosure | Never serve by user-provided filesystem path; resolve by job_id+version from DB/job rebuild; constant media type. |

## Sources

### Primary (HIGH confidence)
- Codebase (VERIFIED): `backend/app/services/social/meta_oauth.py`, `backend/app/api/v1/integrations.py`, `backend/app/models/social_account.py`, `backend/app/schemas/social_integrations.py`, `backend/app/crud/social_posts.py`, `backend/app/services/social/publish_pipeline.py`, `backend/app/core/config.py`, `backend/.env.example`, `frontend/app/admin/integracoes/IntegrationsClient.tsx`, `frontend/lib/api.ts`, `backend/alembic/versions/0004_social_foundation.py`, `docs/META-INTEGRATION-TESTING.md`.
- Project planning (VERIFIED): `.planning/phases/29-meta-ig-readiness-media-foundation/29-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/research/*.md`.
- Version check (VERIFIED): `python -m pip index versions Pillow` (2026-11-23) — latest 13.0.0.
- Pillow docs (CITED): https://pillow.readthedocs.io/en/stable/reference/Image.html — image creation/save/JPEG.
- FastAPI docs (CITED): https://fastapi.tiangolo.com/advanced/custom-response/ — `Response` for bytes/media.

### Secondary (MEDIUM confidence)
- Meta Content Publishing (CITED, from prior research, verify before live rollout): https://developers.facebook.com/docs/instagram-platform/content-publishing — IG container/publish flow, public image URL requirement, permissions/rate limits.
- Meta IG User media endpoints (CITED): https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media and https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish.
- Meta Page/IG linkage pattern (CITED): `/{page-id}?fields=instagram_business_account{id,username}` (confirm exact fields/permissions in current app mode).

### Tertiary (LOW confidence)
- None retained as recommendation without mitigation; role-dependent ads permissions and exact App Review path remain manual-confirm items.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - existing stack verified in repo; Pillow version verified locally.
- Architecture: HIGH - integration points verified in code; Meta endpoint semantics marked CITED/MEDIUM where live behavior can vary by app mode.
- Pitfalls: HIGH - grounded in codebase patterns and official Meta constraints documented in project research.

**Research date:** 2026-11-23
**Valid until:** 2026-12-23 (Meta docs/app-review details should be rechecked before live rollout)
