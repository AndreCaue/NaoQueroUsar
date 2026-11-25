---
phase: 30-instagram-review-experience
verified: 2026-11-25T15:10:00Z
status: gaps_found
score: 3/4 must-haves verified
gaps:
  - truth: "Admin vê na revisão uma seção Instagram ao lado do Facebook, com toggle por vaga e status independente por plataforma."
    status: partial
    reason: "A seção Instagram, o toggle por vaga e o isolamento de estado/dados por provider existem, mas a UI da seção Instagram não exibe o status independente do Instagram (status_label/estado) como faz a seção Facebook."
    artifacts:
      - path: "frontend/app/admin/review/EditJobDialog.tsx"
        issue: "igStatus é carregado por getInstagramSocialStatus e armazenado em estado, porém não há renderização visível do status Instagram na seção 'Post para Instagram'. A seção Facebook exibe socialStatus.status_label."
    missing:
      - "Renderizar status Instagram independente na seção IG (ex.: rascunho/agendado/publicado/falhou/sem rascunho), usando igStatus.status_label ou equivalente, sem acoplar ao status Facebook."
---

# Phase 30: Instagram Review Experience Verification Report

**Phase Goal:** Admin revisa e ajusta a publicação Instagram por vaga com feedback claro antes de aprovar.
**Verified:** 2026-11-25T15:10:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Admin vê na revisão uma seção Instagram ao lado do Facebook, com toggle por vaga e status independente por plataforma. | ⚠️ PARTIAL | `frontend/app/admin/review/EditJobDialog.tsx:1539-1608` renderiza seção "Post para Instagram" abaixo do Facebook com toggle "Publicar no Instagram desta vaga" e estado IG separado (`igEnabled`, `igDraft`, `igCaption`, `igStatus`). `frontend/lib/api.ts:550-621` e `607-621` buscam draft/status IG por endpoints próprios; backend tem `/jobs/{id}/instagram/social-status` (`backend/app/api/v1/admin.py:828-846`) e CRUD/provider `instagram` (`backend/app/crud/social_posts.py:20-29,310-336`). **Gap:** `igStatus` não é exibido na UI IG; FB exibe `socialStatus.status_label` em `:1219`. |
| 2 | Admin edita legenda Instagram pré-preenchida a partir da vaga, vê contador ao vivo `N/2200` e não consegue salvar/aprovar legenda acima do limite. | ✓ VERIFIED | Template C pré-preenchido: `backend/app/services/social/post_generation.py:295-331` (`generate_instagram_template`, `link na bio`, hashtags). UI: `EditJobDialog.tsx:1618-1665` mostra textarea, helper "link na bio", contador `{igCharCount}/2200 caracteres`, erro blocking >2200 e `handleIgSave` bloqueia `igOverLimit` (`:864-876`). Backend: `admin.py:534-551,785-786,176-183` valida 2200 em save/generate/approve. Teste passa: `tests/test_admin_instagram_social_posts.py::test_instagram_caption_over_2200_rejected`. |
| 3 | Admin recebe aviso quando a legenda passa de 30 hashtags e orientação clara de que links na legenda não são clicáveis, com CTA no estilo “link na bio”. | ✓ VERIFIED | `EditJobDialog.tsx:1638-1654` mostra orientação "Links na legenda não são clicáveis. Use &quot;link na bio&quot; como CTA." e aviso não bloqueante quando `igHashtagWarning` (>30). Backend template C inclui "Confira os detalhes e candidate-se: link na bio" (`post_generation.py:315`) e save IG não injeta link público/sanitização FB (`admin.py:782-786` comentário/implementação). |
| 4 | Admin visualiza antes de aprovar/publicar o preview da imagem exata que será enviada ao Instagram e não consegue aprovar/publicar Instagram sem imagem válida, sem bloquear Facebook/site. | ✓ VERIFIED | Preview: `EditJobDialog.tsx:1692-1726` chama `prepareInstagramMedia` (`:469-488`, auto-prepare em open/toggle), exibe loading/erro e `<img src={igMedia.image_url} alt="Prévia da imagem do Instagram">`. Bloqueio IG-only UI: `:866-876,1718-1726` desabilita save IG e mostra "O Facebook e o site não são bloqueados". Backend D-07: `_validate_instagram_publish_ready` usa `prepare_instagram_media` em save/generate (`admin.py:542-558,732-738,798-804`) e approve guard antes de `approve_job`/commit só quando `publish_enabled` (`:173-193`), com mensagem de escape hatch desativar IG; Facebook flow permanece separado (`:210+`). Testes: `test_instagram_enabled_requires_valid_image_on_save`, `test_approve_blocked_by_invalid_instagram_then_allowed_when_disabled` passaram. |

**Score:** 3/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/models/social_post.py` | `publish_enabled` em SocialPost | ✓ VERIFIED | `Boolean` import e `publish_enabled` com `server_default true` (`:5,42-46`). |
| `backend/alembic/versions/0007_instagram_review_social_post_publish_enabled.py` | Migração publish_enabled | ✓ VERIFIED | `upgrade` adiciona coluna boolean not null default true; `downgrade` remove. |
| `backend/app/schemas/social_posts.py` | Provider instagram + publish_enabled | ✓ VERIFIED | Draft request/response e status item aceitam `instagram` e `publish_enabled` (`:30,41,45,68`). |
| `backend/app/crud/social_posts.py` | CRUD provider-aware e publish_enabled | ✓ VERIFIED | `upsert_draft` persiste `publish_enabled`; status builder aceita provider para caso none (`:39-64,261-287,310-336`). |
| `backend/app/services/social/post_generation.py` | Template C determinístico IG | ✓ VERIFIED | `generate_instagram_template`, `generate_instagram_draft_for_job`, "link na bio", hashtags, export em `__all__`. |
| `backend/app/api/v1/admin.py` | Endpoints IG draft/status e guards | ✓ VERIFIED | GET/POST generate/PUT draft e GET status em `/instagram/social-post*` (`:680-846`); `_validate_instagram_publish_ready` (`:542-558`); approve guard IG (`:173-193`); `_draft_response` inclui `publish_enabled` (`:502`). |
| `backend/tests/test_admin_instagram_social_posts.py` | Cobertura backend contratos IG | ✓ VERIFIED | 4 testes passaram (`pytest -q tests/test_admin_instagram_social_posts.py` => `4 passed`). |
| `frontend/lib/api.ts` | Tipos/funções IG draft/status/media | ✓ VERIFIED | Tipos widen provider/publish_enabled, `InstagramMediaPrepareResponse`, `prepareInstagramMedia`, `get/save/generate InstagramSocialDraft`, `getInstagramSocialStatus` (`:426,445,453,550-637`). |
| `frontend/app/admin/review/EditJobDialog.tsx` | Seção IG com D-01..D-09 | ⚠️ PARTIAL | Seção, toggle, readiness gate, contador/warnings, preview, bloqueio IG-only presentes. Falta exibir status IG independente (`igStatus` carregado mas não renderizado). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `frontend/app/admin/review/EditJobDialog.tsx` | `frontend/lib/api.ts` | `getMetaIntegrationStatus`, `prepareInstagramMedia`, IG draft/status calls | ✓ WIRED | Imports/uso em `:16-25,469,500,516,543,837,878,917,956`. |
| `frontend/app/admin/review/EditJobDialog.tsx` | `/admin/integracoes` | CTA readiness disabled | ✓ WIRED | Link `href="/admin/integracoes"` com "Abrir Integrações" (`:1579-1583`). |
| `frontend/lib/api.ts` | `/api/v1/admin/jobs/{id}/instagram/*` | fetch IG draft/status/media | ✓ WIRED | Endpoints instagram/social-post, generate, status, media/prepare (`:554,572,593,611,628`). |
| `backend/app/api/v1/admin.py` | `backend/app/crud/social_posts.py` | `get_by_job_provider/upsert_draft` provider instagram | ✓ WIRED | Vários usos `provider="instagram"` (`:173,693,716,741,747,778,807,812`). |
| `backend/app/api/v1/admin.py` | `backend/app/services/social/post_generation.py` | `generate_instagram_draft_for_job` | ✓ WIRED | Import `:47`, uso em generate endpoint `:731`. |
| `backend/app/api/v1/admin.py` | `backend/app/services/social/image_media.py` | `prepare_instagram_media` D-07 | ✓ WIRED | Import `:40`, helper `:553`, approve guard `:184`. |
| `EditJobDialog IG section` | IG status display | `igStatus.status_label` render | ✗ NOT_WIRED | `igStatus` é setado (`:296,546,554`) mas não renderizado na seção Instagram; somente FB status é renderizado. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `EditJobDialog.tsx` IG caption | `igCaption`/`igDraft` | `getInstagramSocialDraft` / `generateInstagramSocialDraft` / `saveInstagramSocialDraft` | Yes (backend draft + template C) | ✓ FLOWING |
| `EditJobDialog.tsx` IG preview | `igMedia.image_url` | `prepareInstagramMedia` -> `/instagram/media/prepare` | Yes (prepared media response; backend uses image_media) | ✓ FLOWING |
| `EditJobDialog.tsx` IG readiness | `igReadiness` | `getMetaIntegrationStatus` | Yes (Meta integration status) | ✓ FLOWING |
| `EditJobDialog.tsx` IG status | `igStatus` | `getInstagramSocialStatus` | Yes (backend status item), but not rendered | ⚠️ DISCONNECTED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Backend IG review contracts/regression tests | `cd backend && pytest -q tests/test_admin_instagram_social_posts.py` | `4 passed in 45.52s` | ✓ PASS |
| Instagram media-related regressions still pass | Not run (covered partially by phase plan commands in summaries; targeted IG contract tests passed) | N/A | ? SKIP |
| Frontend lint for modified files | Not run here (summary recorded lint pass; command adaptation noted) | N/A | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| REVW-01 | 30-01, 30-02 | Seção Instagram ao lado do Facebook com toggle por vaga e status independente por plataforma | ⚠️ PARTIAL | Seção/toggle/isolamento independentes verificados; exibição de status IG independente ausente na UI. |
| REVW-02 | 30-01, 30-02 | Edita legenda IG pré-preenchida, contador `N/2200`, bloqueia acima do limite | ✓ SATISFIED | Template C, contador UI, bloqueio UI save, validação backend save/generate/approve, teste 2201/422. |
| REVW-03 | 30-01, 30-02 | Avisa >30 hashtags e orienta link não clicável / CTA "link na bio" | ✓ SATISFIED | Warning >30 não bloqueante e helper link-na-bio na UI; template C e save sem injeção de link público. |
| REVW-04 | 30-01, 30-02 | Preview da imagem exata antes de aprovar/publicar | ✓ SATISFIED | `prepareInstagramMedia` + `<img src={igMedia.image_url}>` com estados loading/erro/inválido; D-07 bloqueia IG inválido sem bloquear FB/site. |

**Orphaned requirements for Phase 30:** None. REQUIREMENTS.md traceability maps only REVW-01..04 to Phase 30.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `frontend/app/admin/review/EditJobDialog.tsx` | 296,546-559 | `igStatus` fetched/stored but not rendered | ⚠️ Warning | Usuário não vê status independente do Instagram na seção, enfraquecendo REVW-01. |
| `frontend/app/admin/review/EditJobDialog.tsx` | 1718-1726 | Approve-block message is informational in dialog (no approve button in dialog) | ℹ️ Info | Enforcement real está no backend approve; ReviewQueue precisa exibir 422. Não é stub, mas depende de UX fora do dialog. |

### Human Verification Required

### 1. IG status visibility in review dialog

**Test:** Abrir `/admin/review`, editar uma vaga com draft/status Instagram existente (draft, failed, published/simulado conforme ambiente).
**Expected:** A seção "Post para Instagram" mostra claramente o status independente do Instagram, sem confundir com o status Facebook.
**Why human:** Confirmar necessidade/expectativa de UX do produto; o dado existe no backend, mas a apresentação atual não foi encontrada.

### 2. End-to-end approve block behavior

**Test:** Com Instagram ativado e imagem inválida/ausente, tentar aprovar a vaga pela ReviewQueue; depois desativar Instagram e aprovar.
**Expected:** Primeiro caso retorna erro acionável de Instagram (422) sem bloquear Facebook/site de forma permanente; após desativar IG, aprovação segue.
**Why human:** EditJobDialog não tem botão aprovar; fluxo cruza ReviewQueue + backend.

### Gaps Summary

A fase entrega a maior parte da experiência de revisão Instagram: seção independente, toggle, readiness gate, template C, contador 2200 com bloqueio, aviso de hashtags, orientação "link na bio", preview da imagem preparada e guards backend D-07 preservando independência do Facebook/site. O gap principal é de apresentação: o status Instagram independente é buscado pelo frontend, mas não aparece na seção Instagram, deixando o REVW-01 parcialmente atendido do ponto de vista do usuário.

---

_Verified: 2026-11-25T15:10:00Z_
_Verifier: Claude (gsd-verifier)_