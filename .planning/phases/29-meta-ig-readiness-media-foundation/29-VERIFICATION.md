---
phase: 29-meta-ig-readiness-media-foundation
verified: 2026-11-23T17:10:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Confirmar prontidão Instagram real no Meta"
    expected: "Em /admin/integracoes, com Página Facebook conectada e conta Instagram Business/Creator vinculada, o status mostra 'Instagram pronto para publicação' com ig_user_id/username; estados missing_linkage e missing_permissions aparecem de forma acionável quando aplicável."
    why_human: "Depende de app Meta real, permissões instagram_basic/instagram_content_publish concedidas, Page↔IG linkage e credenciais de teste; não verificável apenas no código."
  - test: "Validar URL pública HTTPS de mídia acessível pela Meta"
    expected: "Com MEDIA_PUBLIC_BASE_URL configurada para backend público HTTPS, POST /api/v1/admin/jobs/{job_id}/instagram/media/prepare retorna image_url pública; GET nessa URL sem auth retorna image/jpeg e é acessível externamente pela Meta."
    why_human: "Requer deploy/backend público acessível pela internet e configuração real de ambiente; testes locais validam contrato, não fetch externo da Meta."
  - test: "Confirmar reconexão/reautorização para escopos IG"
    expected: "Uma conexão Facebook existente sem escopos IG novos exibe estado acionável e, após Reconectar e autorizar, passa a ready sem quebrar o estado Facebook."
    why_human: "Fluxo OAuth real com Meta e consentimento de permissões não pode ser exercitado de forma determinística offline."
---

# Phase 29: Meta/IG Readiness & Media Foundation Verification Report

**Phase Goal:** Admin e sistema têm prontidão Instagram confirmável e uma base de mídia pública válida para o fluxo de publicação.
**Verified:** 2026-11-23T17:10:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Admin vê em Integrações prontidão Instagram da Página selecionada, incluindo conta IG vinculada, `ig_user_id` resolvido e estado acionável de reconexão/correção quando faltar. | ✓ VERIFIED | `backend/app/schemas/social_integrations.py` define `MetaInstagramReadiness` e `MetaIntegrationStatus.instagram`; `backend/app/services/social/meta_oauth.py` popula `instagram` em status/verify/connect e mapeia estados seguros pt-BR; `frontend/lib/api.ts` e `frontend/app/admin/integracoes/IntegrationsClient.tsx` renderizam estados `ready/missing_linkage/missing_permissions/needs_reconnect/unknown` com CTAs "Reconectar"/"Verificar agora". Testes `tests/test_integrations_instagram.py` passaram. |
| 2 | Backend resolve e persiste `ig_user_id` reaproveitando fluxo/token Meta existente; linkage ausente/inválido tratado com erro seguro sem quebrar integração Facebook. | ✓ VERIFIED | `backend/app/services/social/instagram_readiness.py` consulta `/{page-id}?fields=instagram_business_account{id,username}` via token fornecido, mapeia `missing_linkage/missing_permissions/unknown` com mensagens seguras; `meta_oauth.py` chama `resolve_instagram_readiness` em connect/replace e verify (linhas observadas), não em status GET (`get_current_meta_status` lê campos persistidos). `SocialAccount` tem campos `ig_*` e migration `0006_ig_readiness_media_foundation.py` adiciona colunas. `tests/test_meta_oauth_instagram.py` passou. |
| 3 | Sistema expõe contrato de validação/preparação de imagem Instagram com feedback claro pt-BR e bloqueio aplicável apenas ao Instagram (contrato/preparação na Phase 29; enforcement na revisão Phase 30; revalidação publish Phase 31). | ✓ VERIFIED | `backend/app/schemas/social_media.py` define `InstagramImageValidation`/`InstagramMediaPrepareResponse`; `backend/app/services/social/image_media.py` retorna pt-BR para `missing_image`, `invalid_image`, `invalid_public_url`, `media_not_ready`; `POST /api/v1/admin/jobs/{job_id}/instagram/media/prepare` exposto em `admin.py` com `Depends(require_admin)`. Não há bloqueio aplicado a Facebook/site; escopo de enforcement delegado a Phase 30/31 conforme REQ/plan. `tests/test_ig_media_validation.py` passou. |
| 4 | Sem imagem de origem disponível, sistema gera card fallback determinístico compatível com Instagram e admin consegue visualizar imagem exata pretendida por URL pública HTTPS acessível pela Meta. | ✓ VERIFIED | `backend/app/services/social/image_card.py` define `CARD_TEMPLATE_VERSION="ig-card-v1"`, `1080x1350`, JPEG, `MAX_BYTES=8MB`, paleta dark/roxo, CTA `link na bio`, sem contatos, fontes bundled DejaVu; `image_media.py` calcula hash determinístico por campos relevantes e prepara/armazenar `SocialMediaAsset`; `public.py` serve `GET /api/v1/public/ig-media/{job_id}/{version}.jpg` sem auth com `Cache-Control: public, max-age=31536000, immutable`; prepare retorna `image_url` e proveniência. Visualização por UI de revisão fica para Phase 30, mas URL pública/preview por URL é fornecida. `tests/test_ig_media_card.py` e `tests/test_public_ig_media.py` passaram. |
| 5 | Existe documentação/checklist operacional Meta/Instagram (permissões/escopos, premissas App Review/roles/tasks, setup/verificação) disponível para execução manual. | ✓ VERIFIED | `docs/META-INTEGRATION-TESTING.md` inclui `instagram_basic`, `instagram_content_publish`, `instagram_business_account`, `MEDIA_PUBLIC_BASE_URL`, troubleshooting `missing_linkage/missing_permissions/needs_reconnect/unknown`, CTA Reconectar e handoff explícito: "não marcar como aprovado sem execução real". `backend/tests/test_docs_meta_instagram.py` passou. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `backend/app/models/social_account.py` | Campos aditivos de prontidão IG | ✓ VERIFIED | Contém `ig_user_id`, `ig_username`, `ig_readiness_state`, `ig_readiness_checked_at`, `ig_readiness_last_error_*`. |
| `backend/app/models/social_media_asset.py` | Modelo durável de mídia IG por job/version hash | ✓ VERIFIED | `SocialMediaAsset` com `job_id/provider/version_hash/template_version/mime_type/width/height/byte_size/image_bytes/provenance_json`, unique `uq_social_media_assets_job_provider_version`. |
| `backend/alembic/versions/0006_ig_readiness_media_foundation.py` | Migração 0006 | ✓ VERIFIED | `revision="0006_ig_readiness_media_foundation"`, `down_revision="0005_social_oauth_pending"`, adiciona colunas IG e cria `social_media_assets`. |
| `backend/app/services/social/instagram_readiness.py` | Resolução isolada de prontidão IG | ✓ VERIFIED | `resolve_instagram_readiness` consulta Graph, mapeia ready/missing_linkage/missing_permissions/unknown, sem exposição de token/raw payload. |
| `backend/app/services/social/image_card.py` | Renderizador determinístico Pillow | ✓ VERIFIED | 1080x1350, JPEG RGB, `link na bio`, `MAX_BYTES`, fontes bundled, sem contatos. |
| `backend/app/services/social/image_media.py` | Hash/versionamento/validação/preparo/public URL | ✓ VERIFIED | `compute_ig_card_hash`, validação `MEDIA_PUBLIC_BASE_URL`, mensagens pt-BR IMAG-01, `prepare_instagram_media`, `get_or_build_public_asset`. |
| `backend/app/api/v1/public.py` | Endpoint público de mídia IG | ✓ VERIFIED | `GET /ig-media/{job_id}/{version}.jpg`, sem auth, valida hash, 404 seguro, resposta image/jpeg imutável. |
| `backend/app/api/v1/admin.py` | Endpoint admin de preparo de mídia IG | ✓ VERIFIED | `POST /jobs/{job_id}/instagram/media/prepare` com `require_admin`, retorna `InstagramMediaPrepareResponse`. |
| `frontend/lib/api.ts` | Tipos IG readiness aditivos | ✓ VERIFIED | `MetaInstagramReadiness`, `MetaInstagramReadinessState`, `instagram` em status/action. |
| `frontend/app/admin/integracoes/IntegrationsClient.tsx` | Painel aditivo de prontidão IG | ✓ VERIFIED | Estados e copy pt-BR acionáveis; disconnect menciona FB+IG; fallback seguro. |
| `docs/META-INTEGRATION-TESTING.md` | Checklist operacional META-03 | ✓ VERIFIED | Escopos, linkage, env, troubleshooting, handoff explícito. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `meta_oauth.py` | `instagram_readiness.py` | `resolve_instagram_readiness` em connect/verify | ✓ WIRED | Import e chamadas em replace/connect e verify_current_connection; status GET usa campos persistidos. |
| `integrations.py` / `meta_oauth.py` | `social_integrations.py` | `MetaIntegrationStatus.instagram` / `MetaActionResponse.instagram` | ✓ WIRED | Schemas aditivos usados nas respostas de status/verify/action. |
| `image_media.py` | `image_card.py` | render determinístico em cache miss | ✓ WIRED | `prepare_instagram_media`/build path usa `render_ig_card` e fontes bundled. |
| `public.py` | `image_media.py`/CRUD | endpoint público resolve/build por job+version | ✓ WIRED | `get_or_build_public_asset` chamado por rota pública sem auth. |
| `admin.py` | `social_media.py` schema | prepare retorna contrato de validação/proveniência | ✓ WIRED | Endpoint retorna `InstagramMediaPrepareResponse`. |
| `IntegrationsClient.tsx` | `lib/api.ts` | consumo de `status.instagram` | ✓ WIRED | UI lê estado/mensagem/IDs e renderiza ações. |
| `META-INTEGRATION-TESTING.md` | `.env.example` / config | alinhamento de envs IG/media | ✓ WIRED | Doc inclui `MEDIA_PUBLIC_BASE_URL` e escopos IG; `.env.example` contém `MEDIA_PUBLIC_BASE_URL=`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `IntegrationsClient.tsx` | `status.instagram` | `GET /api/v1/admin/integrations/meta/status` → `meta_oauth` persisted IG fields / verify refresh | Yes, quando conta IG resolvida; estados seguros quando não | ✓ FLOWING |
| `admin.py prepare_job_instagram_media` | `InstagramMediaPrepareResponse.image_url/validation/provenance` | `image_media.prepare_instagram_media` → hash + DB asset + renderer/public URL validation | Yes | ✓ FLOWING |
| `public.py get_public_ig_media` | `asset.image_bytes` | `get_or_build_public_asset` → `social_media_assets`/render determinístico | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| META-01/02/IMAG-01/02/03/META-03 automated tests | `cd backend; uv run pytest tests/test_meta_oauth_instagram.py tests/test_integrations_instagram.py tests/test_ig_media_card.py tests/test_ig_media_validation.py tests/test_public_ig_media.py tests/test_docs_meta_instagram.py -q` | `16 passed in 44.49s` | ✓ PASS |
| Frontend lint for touched Integrations files | `cd frontend; npx eslint app/admin/integracoes/IntegrationsClient.tsx app/admin/integracoes/page.tsx lib/api.ts` | Exit 0; 2 pre-existing warnings (`react-hooks/set-state-in-effect`) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| META-01 | 29-01, 29-03 | Admin vê prontidão IG em Integrações com estado acionável | ✓ SATISFIED | Schema/API `instagram` aditivo, UI Integrations com estados/CTAs, testes integrations instagram; validação live Meta permanece humana. |
| META-02 | 29-01 | Backend resolve/persiste `ig_user-id` com erro seguro sem quebrar Facebook | ✓ SATISFIED | `instagram_readiness.py` + `meta_oauth.py` + campos IG/migração 0006 + testes meta oauth instagram. |
| META-03 | 29-03 | Documentação de permissões/escopos, premissas e checklist manual Meta/IG | ✓ SATISFIED | `docs/META-INTEGRATION-TESTING.md` atualizado; teste smoke de docs passou; execução real marcada como handoff. |
| IMAG-01 | 29-02 | Contrato/validação de imagem IG com feedback pt-BR; bloqueio apenas IG; split 29/30/31 | ✓ SATISFIED | Contrato de validação/prepare implementado e testado; enforcement de review/publish explicitamente delegado a Phase 30/31 conforme REQUIREMENTS. |
| IMAG-02 | 29-02 | Card fallback determinístico 1080x1350/1080x1080 compatível, JPEG sRGB, <8MB | ✓ SATISFIED | Renderer Pillow determinístico 1080x1350 JPEG, <8MB guard, fontes bundled, sem contatos; testes de card/hash passaram. |
| IMAG-03 | 29-02 | Imagem por URL pública HTTPS estável, acessível pela Meta, com validação/preview/proveniência | ✓ SATISFIED | Endpoint público sem auth, URL versionada por job/hash, `MEDIA_PUBLIC_BASE_URL` validada, prepare retorna image_url+proveniência; acessibilidade real pela Meta requer verificação humana. |

**Orphaned requirements for Phase 29:** None (REQUIREMENTS.md maps META-01/02/03, IMAG-01/02/03 to Phase 29; all present in plan frontmatter).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `frontend/app/admin/integracoes/IntegrationsClient.tsx` | 181, 220 | `react-hooks/set-state-in-effect` warnings (ESLint) | ℹ️ Info | Pre-existing lint warnings; eslint exited 0 and no new errors introduced. |

### Human Verification Required

### 1. Prontidão IG real com credenciais Meta

**Test:** Conectar Página Facebook real com conta Instagram Business/Creator vinculada e permissões `instagram_basic,instagram_content_publish`; abrir `/admin/integracoes` e usar "Verificar agora".
**Expected:** Estado ready com `ig_user_id`/username ou estado acionável correto para linkage/permissões ausentes; Facebook não quebra.
**Why human:** Depende de app/credenciais/permissões/linkage reais no Meta.

### 2. Fetch público da imagem pela Meta

**Test:** Configurar `MEDIA_PUBLIC_BASE_URL` HTTPS público, preparar mídia de uma vaga e acessar a `image_url` externamente.
**Expected:** URL pública sem auth retorna JPEG compatível e é acessível por crawler/fetch externo.
**Why human:** Requer deploy público real e validação externa de acessibilidade.

### 3. Reconexão para novos escopos IG

**Test:** Usar conta FB conectada antes dos novos escopos e executar Reconectar.
**Expected:** Admin recebe orientação acionável e, após reautorizar, prontidão IG atualiza.
**Why human:** Consentimento OAuth real não é simulável fielmente offline.

### Gaps Summary

No automated gaps found in codebase evidence. Phase 29 delivers the backend/frontend/doc foundation required by META-01/02/03 and IMAG-01/02/03. Remaining items are operational/live-environment confirmations (Meta permissions/linkage and public HTTPS reachability) and are tracked as human verification, not code gaps.

---

_Verified: 2026-11-23T17:10:00Z_
_Verifier: Claude (gsd-verifier)_
