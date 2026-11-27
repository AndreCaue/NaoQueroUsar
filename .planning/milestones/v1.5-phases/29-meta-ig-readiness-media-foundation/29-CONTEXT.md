# Phase 29: Meta/IG Readiness & Media Foundation - Context

**Gathered:** 2026-11-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Entregar a base de prontidão Instagram e de mídia pública necessária para o v1.5: o admin consegue confirmar se a Página Facebook selecionada está pronta para Instagram, o backend resolve/persiste `ig-user-id` reaproveitando o fluxo/token Meta existente com falhas seguras, e existe uma base de imagem válida (card fallback determinístico) servida por URL pública HTTPS acessível pela Meta. Esta fase não implementa a UX completa de revisão Instagram (Phase 30) nem o pipeline de publicação IG (Phase 31), mas estabelece contratos, dados e mídia que essas fases consumirão.

</domain>

<decisions>
## Implementation Decisions

### Origem da imagem
- **D-01:** Origem principal = **card gerado sempre**, determinístico a partir dos dados da vaga. Sem upload manual e sem logo de empresa no v1.5.
- **D-02:** Geração/atualização do card acontece ao **abrir/preparar revisão** (ou fluxo equivalente de preparação do draft), de forma que o preview use a mesma imagem pretendida para publicação.
- **D-03:** Se dados relevantes da vaga mudarem antes da publicação, o card deve ser **regenerado automaticamente**; preview/publicação devem usar a versão atual.
- **D-04:** Imagem ausente/inválida **bloqueia apenas Instagram**. Aprovação/publicação Facebook/site não são bloqueadas por problema de imagem IG (preserva independência, alinha com PUBL-01).

### Card: formato e geração
- **D-05:** Formato padrão: **1080x1350 (retrato 4:5)**, JPEG sRGB, <8MB, compatível com IMAG-02 (proporção 4:5–1.91:1).
- **D-06:** Estilo visual: **Dark brand EmpregaNoix** — fundo escuro, acentos roxos (#8b5cf6/#a78bfa, fundos #0f0a1a/#1a1025), identidade EmpregaNoix, CTA "link na bio", legível no feed.
- **D-07:** Conteúdo do card: **essencial sem contato** — título, empresa (se houver), cidade/remoto, tipo/contrato e salário quando disponível; CTA "link na bio". Não incluir WhatsApp/e-mail/telefone no card.
- **D-08:** Estratégia de geração: **Pillow/PIL no backend Python/FastAPI**, determinística; implementação deve cuidar de fontes, quebra de texto e limites de tamanho/qualidade JPEG.

### Armazenamento e URL pública
- **D-09:** Servir imagem por **endpoint público no backend** (sem depender de R2/S3/DB blob como infraestrutura primária no v1.5).
- **D-10:** Estratégia de obtenção: **gerar sob demanda + cache**. Se não houver arquivo/cache válido, gerar a partir da vaga e cachear (disco/volume quando disponível); deve tolerar reconstrução após perda de cache efêmero.
- **D-11:** Identificação da URL: **por job ID com versão/hash** (ex.: query `v={hash}` ou path versionado). A URL deve representar a imagem exata pretendida, suportar proveniência e facilitar invalidação/cache.
- **D-12:** Base pública da URL vem de **env explícita** (ex.: `BACKEND_PUBLIC_URL` ou `MEDIA_PUBLIC_BASE_URL`; nome exato em OpenCode's Discretion), não inferida de `SITE_PUBLIC_URL`. A URL final deve ser HTTPS pública, não-localhost, sem auth, e validada antes do publish.

### Prontidão IG e token
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and product context
- `.planning/ROADMAP.md` §"Phase 29: Meta/IG Readiness & Media Foundation" — Goal, depends_on, requirements META-01..03/IMAG-01..03, success criteria, research flags/open decisions.
- `.planning/REQUIREMENTS.md` §"IG Readiness & Meta" + §"Mídia / Imagem Pública" — Contrato normativo META-01..03, IMAG-01..03; traceability Phase 29.
- `.planning/PROJECT.md` — Core value, v1.5 goal/constraints, open decisions list, key decisions (site-first/best-effort patterns, token safety).
- `.planning/STATE.md` — Current position, v1.5 concerns (Meta verification, open decisions, carry-over residuals).

### Existing Meta/Facebook integration (reuse/extend, do not regress)
- `backend/app/services/social/meta_oauth.py` — OAuth state, token exchange, page listing, debug_token verification, pending selection, connection status/disconnect/replace. Hardcoded FB scopes currently at `META_OAUTH_SCOPES`.
- `backend/app/api/v1/integrations.py` — Admin integrations endpoints (`/meta/oauth/*`, `/meta/status`, `/meta/verify`, `/meta/pending*`, `/meta/select-page`, `/meta/disconnect`) and safe redirect/error handling.
- `backend/app/models/social_account.py` — Current SocialAccount model (provider, page_id, page_name, encrypted token, status, connected/token_checked timestamps). Extend here for IG readiness.
- `backend/app/schemas/social_integrations.py` — Meta integration status/pending/action schemas; extend carefully for IG readiness fields.
- `frontend/app/admin/integracoes/IntegrationsClient.tsx` — Current FB-only Integrations UI (connect/verify/disconnect/pending selection, banners, dialog). META-01 readiness UI will extend this surface.
- `frontend/app/admin/integracoes/page.tsx` — Integrations admin page wrapper.

### Social publish/review foundation (downstream context, no Phase 29 regression)
- `backend/app/models/social_post.py` — SocialPost lifecycle/status/attempts/external_post_id; Phase 31 will extend for IG independence.
- `backend/app/services/social/publish_pipeline.py` — Existing async FB publish pipeline/claim/retry/idempotency patterns; Phase 31 must keep independent.
- `backend/app/services/social/publisher.py` — Publisher protocol; useful reference for future IG publisher shape.
- `backend/app/services/social/facebook.py` — Existing Facebook publisher implementation (inspect before planning for reuse boundaries).
- `frontend/app/admin/review/ReviewQueue.tsx` — Current review flow; Phase 30 will add IG section, Phase 29 must not break it.

### Config, env, and ops
- `backend/.env.example` — Existing Meta/social/env vars (`META_APP_ID`, `META_APP_SECRET`, `META_GRAPH_VERSION`, `META_OAUTH_REDIRECT_URI`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, `SITE_PUBLIC_URL`, etc.). Phase 29 should document any new env vars here.
- `backend/app/core/config.py` — Settings/env loading (inspect when adding new env vars).

### Research
- `.planning/research/SUMMARY.md` — v1.5 research synthesis, risks, suggested phase structure and open questions.
- `.planning/research/ARCHITECTURE.md` — Integration architecture patterns for IG/media/publish.
- `.planning/research/PITFALLS.md` — Known pitfalls (Meta fetch URL, token/scopes, retry/idempotency, media constraints).
- `.planning/research/STACK.md` — Stack additions/constraints for image generation and IG integration.
- `.planning/research/FEATURES.md` — Feature landscape and expectations.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/social/meta_oauth.py`: complete Meta OAuth/token/debug/pending-selection/status/verify/disconnect flow. Reuse for resolving IG readiness and extending scopes/checks; preserve safe error classification and no-token-leak logging.
- `backend/app/services/social/crypto.py`: Fernet token encryption helpers used by SocialAccount/pending OAuth payloads. Reuse for any stored sensitive token material (do not store plaintext).
- `backend/app/models/social_account.py` + `backend/app/models/social_oauth_pending.py`: existing persistence for Meta connection lifecycle. Extend rather than replace for IG readiness.
- `frontend/app/admin/integracoes/IntegrationsClient.tsx`: established admin integration UX patterns (status banners, verify, reconnect, pending selection, confirmation dialog, pt-BR safe messaging).
- `backend/app/services/social/publish_pipeline.py`: claim/lock/retry/idempotency patterns and safe logging conventions; relevant reference for future Phase 31 and for shaping IG readiness/publish error semantics consistently.

### Established Patterns
- **Site-first / social independent:** Facebook integration is best-effort and should not be broken by IG additions. IG failures/readiness must be isolated.
- **Safe external integration errors:** meta_oauth maps failures to safe pt-BR messages; logs avoid secrets/tokens. Preserve this pattern for IG Graph calls.
- **Encrypted secrets at rest:** page tokens encrypted via `SOCIAL_TOKEN_ENCRYPTION_KEY`. Any new persisted sensitive data must follow same rule.
- **Admin-protected endpoints + JWT:** integrations endpoints use `require_admin`; frontend uses admin guard/token.
- **Config-driven env:** Meta Graph version/config already env-driven (`META_GRAPH_VERSION`); new IG/media public base URL should also be env-driven.

### Integration Points
- `backend/app/models/social_account.py` / Alembic migration: add IG readiness fields.
- `backend/app/services/social/meta_oauth.py` and/or new IG readiness helper: resolve `ig-user-id` from linked Page (`/{page-id}?fields=instagram_business_account{...}` pattern to be confirmed during research/implementation) and evaluate scopes/readiness.
- `backend/app/api/v1/integrations.py` + `backend/app/schemas/social_integrations.py`: expose IG readiness in status/action responses.
- `frontend/app/admin/integracoes/IntegrationsClient.tsx` + `frontend/lib/api.ts`: render IG readiness state and actionable reconnect/correction.
- New backend public media endpoint/router (exact module path in discretion): serve generated IG card by job/version with HTTPS public access, no auth.
- `backend/app/services/social/` (new image/card service module): deterministic Pillow render + cache/provenance.
- `backend/.env.example` + `backend/app/core/config.py`: add media public base URL and any IG/media config needed.

</code_context>

<specifics>
## Specific Ideas

- "Card gerado sempre" foi escolhido para v1.5: simples, determinístico, sem upload/logo de empresa.
- Card deve parecer EmpregaNoix (dark + roxo), com CTA "link na bio" e sem contatos no card.
- URL pública da imagem deve incluir versão/hash para representar a imagem exata pretendida e facilitar cache/proveniência.
- Prontidão IG deve ser acionável na tela de Integrações, reaproveitando o padrão de reconexão já existente no Facebook.

</specifics>

<deferred>
## Deferred Ideas

- Upload manual de imagem na revisão — adiado; v1.5 usa card gerado sempre. Reavaliar em fase futura se houver demanda.
- Logo/arte por empresa como origem primária — adiado; exigiria modelagem/cadastro de marca por empresa.
- Renovação automática de token Meta — adiado; v1.5 usa alerta + reconexão.
- Object storage/CDN dedicado para mídia IG (R2/S3) — adiado; v1.5 usa endpoint público no backend com cache/reconstrução.
- Stories/Reels/carrossel/vídeo, agendamento, métricas, múltiplas contas IG — permanecem fora de escopo (PROJECT.md).

</deferred>

---

*Phase: 29-meta-ig-readiness-media-foundation*
*Context gathered: 2026-11-23*
