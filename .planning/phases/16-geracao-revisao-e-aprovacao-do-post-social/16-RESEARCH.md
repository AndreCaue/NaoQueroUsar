# Phase 16: Geração, Revisão e Aprovação do Post Social - Research

**Researched:** 2026-11-15
**Domain:** Admin review UX + FastAPI social draft/approval flow + Groq-backed pt-BR post generation + timezone/policy-safe persistence
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Ciclo do rascunho social
- **D-01:** O rascunho do post é gerado **sob demanda no editor** (ação explícita do revisor, ex.: "Gerar post/rascunho"), evitando chamadas ao LLM na listagem da fila de revisão.
- **D-02:** Persistência por **upsert** de um único `social_post` por vaga/provider (`job_id`, `provider='facebook'`, respeitando a unicidade existente): gerar/salvar edição/regenerar atualiza o mesmo registro mantendo `status='draft'` enquanto rascunho. "Regenerar com IA" **sobrescreve** o texto do draft atual.
- **D-03:** Geração em serviço dedicado de post social que **reaproveita a integração/configuração Groq existente** (`backend/app/services/extraction/client.py` como referência de cliente/config) com prompt específico pt-BR (tom profissional e acolhedor, emojis moderados, 3–5 hashtags, CTA com link, alvo ~700 caracteres). Se o LLM falhar ou estiver indisponível, usar **fallback por template local determinístico** a partir dos dados da vaga — a revisão nunca é bloqueada e sempre há draft utilizável.
- **D-04:** Gerar/regenerar sempre a partir do **estado atual salvo** da vaga (`Job` persistido), incluindo edições já salvas pelo revisor; não usar snapshot congelado antigo nem valores não persistidos do formulário.

#### Editor e agendamento na revisão
- **D-05:** Integrar a experiência de post social como **seção dentro de `frontend/app/admin/review/EditJobDialog.tsx`** (no fluxo atual com `ReviewQueue.tsx`), mantendo contexto da vaga e do texto-fonte no mesmo lugar.
- **D-06:** Controles essenciais da seção: textarea editável do texto, **contador de caracteres (alvo ~700)**, botão **"Gerar/Regenerar com IA"** com estado de carregamento, **preview simples** do post (texto/link) e indicadores de origem/estado (gerado por IA, fallback/template, erro ao gerar com fallback aplicado).
- **D-07:** Agendamento com **toggle "Publicar agora" (padrão) vs "Agendar"**; ao agendar, selecionar data/hora interpretada em **`America/Sao_Paulo`** (fuso indicado na UI) e persistir o valor de forma inequívoca para o backend (ex.: convertido/armazenado conforme convenção de tempo do domínio).
- **D-08:** **Salvar explicitamente** o conteúdo do draft e a escolha de modo/horário no `social_post` draft (ação de salvar/ao gerar/regenerar conforme fluxo definido). A aprovação deve usar o **último estado salvo** do draft para registrar o post aprovado, evitando divergência entre o que o revisor vê e o que é registrado.

#### Aprovação da vaga e registro do post social (seguro)
- **D-09:** **Publicar a vaga no site primeiro** e tratar o registro do `social_post` aprovado como etapa **separada/best-effort**: falhas sociais (criar/atualizar/registrar `social_post`) **nunca** desfazem nem bloqueiam a publicação da vaga. Em falha social, a vaga permanece publicada e a operação deve sinalizar aviso/estado de erro social à UI.
- **D-10:** Ao aprovar, registrar o `social_post` aprovado com **`status='scheduled'`** e `scheduled_at` apropriado: **"Publicar agora" ⇒ `scheduled_at = agora`** (elegível imediato para processamento assíncrono na Fase 17); **"Agendar" ⇒ `scheduled_at` = horário futuro escolhido** (origem `America/Sao_Paulo`). O texto/modo/horário aprovados ficam registrados no `social_post`.
- **D-11:** Se **não houver draft social salvo** no momento da aprovação, **publicar a vaga no site normalmente** e **pular/avisar** sobre o registro social (sem bloquear). Se a etapa best-effort de registro social falhar, mesma regra: vaga publicada + aviso/erro social.
- **D-12:** **Congelar o texto ao aprovar/registrar** o post como `scheduled`: o conteúdo aprovado passa a ser tratado como final para envio (edição do texto desabilitada para esse registro aprovado), garantindo consistência com o que será processado/enviado na Fase 17 (em alinhamento com POST-05: texto aprovado imutável após envio e salvo).

#### Conteúdo, URL pública e política do post
- **D-13:** Construir o link público da vaga como **`{SITE_PUBLIC_URL}/?vaga=<job_id>`**, reutilizando o deep-link já suportado pelo board público (`frontend/app/(public)/page.tsx` lê `vaga` UUID e abre o detalhe).
- **D-14:** Template/fallback e guia de prompt **objetivos** em pt-BR: incluir cargo/título, cidade, salário e destaques breves de atividades/benefícios quando couber; **CTA com link**; **3–5 hashtags** relevantes; **emojis moderados**; alvo **~700 caracteres**.
- **D-15 (correção explícita do usuário):** O post social **NÃO deve conter nome da empresa** e **NÃO deve conter qualquer contato** (telefone, e-mail ou similares). Deve conter apenas informações permitidas da vaga e o **link para o site**. Ajustar template/prompt/preview para omitir empresa e contatos.
- **D-16:** Tornar a política de contato **configurável via flag de ambiente no backend** (em `Settings`, documentada em `.env.example`), com **padrão desativado** (sem contato). Aplicar de forma central na geração/montagem do post.
- **D-17:** Aplicar a política de forma **central e robusta** na geração, no template/fallback e no preview: omitir empresa e contatos conforme regras (e nunca vazar contato quando desabilitado), sempre incluir link público quando aplicável. Se `SITE_PUBLIC_URL` estiver ausente/inválida para montar o link, tratar com **validação/erro acionável e claro** no fluxo de geração do draft (sem inventar link) sem bloquear a revisão/publicação da vaga no site.

### OpenCode's Discretion
- Nomes exatos de endpoints/rotas, schemas, funções e organização de módulos/arquivos (ex.: serviço de geração social em `backend/app/services/social/`, endpoints admin para draft/save/approve) desde que sigam convenções do backend/frontend e as decisões acima.
- Formato exato de persistência/conversão de fuso para `scheduled_at` (ex.: armazenar UTC derivado de `America/Sao_Paulo`) e representação de "publicar agora".
- Redação/copy exata do template/prompt, seleção de hashtags, truncamento/ajuste para ~700 caracteres e detalhes visuais da seção no `EditJobDialog`, respeitando D-14/D-15/D-17.
- Nome, formato e documentação da(s) env var(s) de configurabilidade da política (D-16) e mensagens de erro/aviso na UI e API.
- Estratégia de retorno da API de aprovação para comunicar sucesso da vaga + sucesso/aviso/falha do registro social (best-effort), sem expor segredos.
- Como desabilitar/bloquear edição de texto quando o post estiver aprovado/`scheduled` (D-12) na UI e/ou validações de backend.

### Deferred Ideas (OUT OF SCOPE)
- Publicação real no Facebook, worker/cron com `FOR UPDATE SKIP LOCKED`, retries/backoff, classificação de erros, idempotência operacional e "tentar novamente" (Fase 17).
- Badges/status social por vaga, erro resumido e link do post publicado na listagem/detalhe admin (UI-01/UI-02, Fase 17).
- Testes automatizados/manuais e documentação operacional/App Review (Fase 18), e carry-over de gaps v1.1.
- Detalhes finos não discutidos (contrato exato de APIs/payloads, UX específica para `SITE_PUBLIC_URL` ausente, nome exato da env var) a definir no planejamento/pesquisa dentro do escopo.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| POST-01 | Reutiliza integração LLM existente para gerar texto do post a partir dos dados estruturados da vaga (tom profissional e acolhedor, pt-BR, emojis moderados, até ~700 caracteres, destaque cargo/cidade/salário se informado/benefícios, CTA com link, 3–5 hashtags) terminando com link da vaga | Reuse Groq config/client seam patterns from `backend/app/services/extraction/client.py`; add dedicated `social` post-generation service with strict prompt/guards and deterministic fallback (D-03/D-04/D-14/D-15/D-17). |
| POST-02 | Fallback por template estático se LLM falhar (revisão nunca bloqueada); texto gerado ao entrar em revisão e salvo como `draft` | Deterministic template builder in backend social service; generate endpoint persists/upserts draft and returns origin/fallback warning when LLM fails/unavailable (D-01/D-02/D-03). |
| POST-03 | Revisor pode editar o texto antes de aprovar (campo editável, contador de caracteres, botão "regenerar com IA", preview simples) | Embed section in `EditJobDialog.tsx` per UI-SPEC/CONTEXT: textarea, live counter, regenerate with confirmation, preview, save/origin/unsaved indicators (D-05/D-06/D-08). |
| POST-04 | Revisor escolhe "publicar agora / agendar" com data e hora (fuso `America/Sao_Paulo`); padrão imediata; agendamento respeita horário escolhido | UI toggle + BRT-labeled inputs; persist publish mode/schedule in draft; convert BRT wall time to unambiguous stored `scheduled_at` and use now for immediate approval (D-07/D-08/D-10). |
| POST-05 | Texto aprovado é imutável após envio e fica salvo em `social_posts` | Approve/registration flow stores approved content/schedule and freezes approved `scheduled` record (backend rejects edits; UI read-only/disabled) while text remains saved in `social_posts` (D-10/D-12). |
| POST-06 | Por padrão o post não inclui contato direto da vaga, apenas link para o site (`SITE_PUBLIC_URL` + URL pública da vaga); comportamento configurável conforme implementação documentada | Central policy sanitizer/enforcer in generation/template/preview/save path, backend flag in `Settings` + `.env.example` default off, deep-link `/?vaga=<id>`, never include company/contact by D-15 (D-13..D-17). |
</phase_requirements>

## Summary

Phase 16 is a **cross-cutting integration** inside the existing admin review flow: add a backend "social post draft" capability (generate/save/fetch) and evolve approval so it continues to publish the job on the site while registering an approved `social_post` as a best-effort side effect. The codebase already has the key building blocks: `SocialPost`/`SocialPostStatus` with unique `(job_id, provider)` and draft/scheduled states (`backend/app/models/social_post.py`), Groq integration/config patterns (`backend/app/services/extraction/client.py`, `backend/app/core/config.py`), an admin-protected API surface (`backend/app/api/v1/admin.py`), and the review UI shell/toast/optimistic patterns (`EditJobDialog.tsx`, `ReviewQueue.tsx`, `frontend/lib/api.ts`).

**Primary recommendation:** Implement a dedicated backend social-post service (prompt/template/policy/link/time conversion) and expose explicit admin endpoints for draft lifecycle plus an approval response contract that separates `job` success from `social` outcome/warnings. Keep all policy enforcement and "last saved draft is source of truth" logic server-side; keep the frontend focused on UX states defined by `16-UI-SPEC.md` (generate/regenerate/save, BRT scheduling, preview/counter/origin, frozen approved state, and non-blocking social warnings on approve).

## Project Constraints (from AGENTS.md)

- Follow fixed stack/locale/design constraints (Next.js 16 App Router + Tailwind CSS, FastAPI async Python, Neon Postgres, pt-BR, dark admin tokens) and existing project conventions/patterns.
- **Core value/constraint:** qualquer pessoa vê vagas sem fricção; integração social **nunca** pode bloquear publicação no site.
- Segredos/tokens/config sensível só no backend; não expor segredos no frontend/logs/respostas.
- Admin único, fluxo existente de revisão/admin deve ser preservado e estendido (não reescrito).
- Groq config/modelo atual do projeto deve ser respeitado/reutilizado (`openai/gpt-oss-20b` padrão com fallback configurável) — não reintroduzir modelos aposentados.
- Planner/implementation must honor locked phase decisions (D-01..D-17) and AGENTS.md with equal authority.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Draft generation (LLM + deterministic fallback), policy/link enforcement, schedule conversion/validation | API / Backend (`app/services/social/*`, `core/config`) | — | Sensitive rules (no company/contact, `SITE_PUBLIC_URL`, secrets, source-of-truth draft) must be centralized and non-bypassable server-side (D-03/D-04/D-15..D-17). |
| Draft persistence and approved registration state | Database / Storage + Backend | API / Backend | `social_posts` unique draft per `(job_id, provider)` and status transitions/scheduling fields are authoritative persistence concerns (D-02/D-08/D-10/D-12). |
| Job publication on approve (must remain successful independently) | API / Backend + Database | — | `approve_job`/job commit is the site-critical path and must complete even if social registration fails (D-09/D-11). |
| Review/editor UI (generate/edit/save/schedule/preview/approve feedback) | Frontend Client (Next.js admin components) | API / Backend | `EditJobDialog.tsx`/`ReviewQueue.tsx` own interactions, loading/errors, frozen state, and toasts per UI-SPEC; backend provides data/contracts. |
| Public deep-link target consumed by post CTA | Frontend (public page) + Config | API / Backend | Link format is `{SITE_PUBLIC_URL}/?vaga=<job_id>` and public page already resolves `vaga` (`frontend/app/(public)/page.tsx`) (D-13). |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| Python (backend runtime) | 3.x (repo standard) | Async API/services implementation | Existing FastAPI/SQLAlchemy async codebase | HIGH [VERIFIED: codebase] |
| FastAPI | project stack (declared 0.143.x) | Admin endpoints, DI, validation, responses | Existing API framework in `backend/app/api/v1/*` | HIGH [VERIFIED: codebase + AGENTS.md] |
| SQLAlchemy (async ORM) | 2.x project stack | `social_posts`/`jobs` persistence, upsert/update flows | Existing models/CRUD/session patterns | HIGH [VERIFIED: codebase] |
| Pydantic v2 | project stack | Request/response schemas for draft/save/approve payloads | Existing schema style (`ConfigDict`, validators) | HIGH [VERIFIED: codebase] |
| Groq Python SDK (`groq`) | project stack | LLM text generation for post draft (reusing existing integration/config) | Already used by extraction seam; D-03 requires reuse of integration/config | HIGH [VERIFIED: `backend/app/services/extraction/client.py`] |
| Next.js App Router + React client components | 16.x / 19.x project stack | Admin review UI changes in `EditJobDialog.tsx`/`ReviewQueue.tsx` | Existing frontend architecture and UI-SPEC target files | HIGH [VERIFIED: codebase] |
| TypeScript | project stack | Typed API client/contracts in `frontend/lib/api.ts` and UI state | Existing frontend conventions | HIGH [VERIFIED: codebase] |

### Supporting
| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| `zoneinfo` (stdlib) | Python stdlib | Convert `America/Sao_Paulo` wall-clock schedule to aware datetime for persistence | Required for D-07/D-10 scheduling correctness (BRT input, unambiguous stored value) | HIGH [CITED: Python stdlib timezone conversion pattern] / [ASSUMED] tz data availability in target runtime |
| `datetime` (stdlib) | Python stdlib | "Publish now" timestamps, comparisons, normalization | Approve/register scheduling and validations | HIGH [VERIFIED: common codebase usage] |
| Existing Groq client seam usage (`AsyncGroq`/settings) | project stack | LLM calls with existing timeout/model/error conventions (adapted subset) | Draft generation service; prefer thin reuse/adaptation over new client stack | MEDIUM [VERIFIED: extraction seam exists; exact reuse shape discretionary] |
| `re` / string utilities (stdlib) | Python stdlib | Central sanitization/guards (strip/deny company/contact patterns), cleanup/length handling | Enforce D-15/D-17 in template/fallback and post-process LLM output before save/return | HIGH [VERIFIED: standard approach] |
| Native HTML controls (`<textarea>`, date/time inputs, `<dialog>`) | browser/platform | UI-SPEC controls in admin dialog | Matches existing `EditJobDialog.tsx` patterns and 16-UI-SPEC contract | HIGH [VERIFIED: UI-SPEC + codebase] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Backend-owned policy/scheduling/link enforcement | Frontend-only enforcement/preview filtering | Rejected for correctness/security: backend must be source of truth for D-08/D-10/D-12/D-15/D-17 and prevent leakage/bypass. |
| Store "publish now" as implicit null/sentinel | Store concrete `scheduled_at` (now or future) | Concrete timestamp is clearer for Phase 17 eligibility (`scheduled_at <= now`) and avoids ambiguity; planner should pick one convention and apply consistently. |
| Reusing extraction prompt/schema pipeline directly | Dedicated social prompt + plain-text/simple response handling | Extraction pipeline is tuned to job parsing/grounding; dedicated prompt/service is simpler and aligned to POST-01/03. |

**Installation:** No new packages expected. Prefer stdlib + existing dependencies (`groq`, FastAPI/SQLAlchemy/Pydantic/Next.js stack already present).

**Version verification:** [ASSUMED] Stack versions are as documented in repo guidance/AGENTS stack summary; `npm view`/`pip show` verification was not executed in this research session. Planner should treat dependency additions as unnecessary unless a concrete gap is found during implementation.

## Architecture Patterns

### System Architecture Diagram

```text
Admin reviewer (browser, /admin/review)
  ├─ opens EditJobDialog (ReviewQueue -> selected JobAdmin)
  │    ├─ [Gerar/Regenerar] -> POST /api/v1/admin/jobs/{id}/social-post/generate
  │    ├─ [Salvar rascunho]  -> PUT  /api/v1/admin/jobs/{id}/social-post
  │    ├─ [Carregar rascunho]-> GET  /api/v1/admin/jobs/{id}/social-post (recommended)
  │    └─ [Aprovar vaga]     -> PATCH /api/v1/admin/jobs/{id}/approve (extended response)
  │
  └─ receives UI state: draft text/origin/mode/schedule, warnings, frozen state

FastAPI admin API (protected by require_admin)
  ├─ Draft generate/save/get handlers
  │    ├─ load persisted Job (D-04)
  │    ├─ Social post service
  │    │    ├─ build/validate public link from SITE_PUBLIC_URL + /?vaga=<job_id> (D-13/D-17)
  │    │    ├─ enforce policy (no company, no contact; configurable flag default off) (D-15/D-16/D-17)
  │    │    ├─ try Groq generation (reuse config/integration patterns) (D-03)
  │    │    └─ fallback deterministic template on failure/unavailable (D-02/D-03/D-14)
  │    └─ upsert SocialPost (job_id, provider='facebook', status='draft') (D-02/D-08)
  │
  └─ Approve flow (job-first, social best-effort)
       ├─ Step A (critical, committed): approve_job(job) + commit (site publish + expiry refresh)
       ├─ Step B (separate/best-effort): read last saved draft -> if present register/transition to scheduled
       │           (status='scheduled', scheduled_at now/future, text frozen) else skip/warn
       └─ Response: job result + social outcome {registered|skipped|warning} for UI toasts (D-09..D-12)

PostgreSQL (Neon)
  ├─ jobs (source of truth for draft generation; published independently)
  └─ social_posts (unique per job/provider; draft -> scheduled in Phase 16; worker consumes later in Phase 17)
```

### Recommended Project Structure
```
backend/app/
├── api/v1/admin.py                    # add social draft endpoints + extend approve response/flow
├── crud/
│   ├── jobs.py                        # keep approve_job semantics (site publish + expiry refresh)
│   └── social_posts.py                # NEW (recommended): get/upsert draft, transition to scheduled
├── schemas/
│   ├── job.py                         # extend approve response schema (job + social outcome) as needed
│   └── social_posts.py                # NEW: draft/get/save/generate/approve-social response schemas
├── services/social/
│   ├── post_generation.py             # NEW: prompt/template/policy/link/sanitize/schedule helpers
│   ├── publisher.py/types.py/facebook.py # existing (no Phase 16 publish implementation)
│   └── ...
└── core/config.py                     # add policy flag env (D-16), keep SITE_PUBLIC_URL validation

frontend/
├── app/admin/review/
│   ├── EditJobDialog.tsx              # embed "Post para Facebook" section + draft UX/state machine
│   └── ReviewQueue.tsx                # handle enriched approve response/toasts (site vs social outcome)
└── lib/api.ts                         # add social draft types/functions; update approve return contract
```

### Pattern 1: Dedicated social draft service with centralized policy enforcement
**What:** One backend module owns (a) loading persisted job fields, (b) building the public link, (c) generating LLM text, (d) deterministic fallback, and (e) policy sanitization/validation so every path (generate, save, preview-safe text) applies the same rules.
**When to use:** Any draft generation, regeneration, save normalization, or approval-time registration source preparation.
**Example (shape):**
```python
# Source: repo service conventions + D-03/D-13..D-17 [VERIFIED: codebase/CONTEXT]
class SocialPostGenerationService:
    def build_public_link(self, job_id: UUID) -> str: ...
    async def generate(self, job: Job) -> GeneratedDraft: ...  # llm or fallback + origin/warnings
    def sanitize_and_enforce_policy(self, text: str) -> str: ...
```

### Pattern 2: Upsert draft by `(job_id, provider)` and mutate only while `draft`
**What:** Query existing `SocialPost` for job/provider; create if missing, update same row on generate/save/regenerate while status is `draft`. Reject edits/regeneration when status is not `draft` (approved/scheduled frozen, D-12).
**When to use:** All draft CRUD operations.
**Example:**
```python
# Source: backend/app/models/social_post.py + SQLAlchemy async patterns [VERIFIED: codebase]
stmt = select(SocialPost).where(SocialPost.job_id == job_id, SocialPost.provider == "facebook")
post = await session.scalar(stmt)
if post is None:
    post = SocialPost(job_id=job_id, provider="facebook", text=text, status=SocialPostStatus.draft)
    session.add(post)
elif post.status == SocialPostStatus.draft:
    post.text = text
    post.scheduled_at = scheduled_at
else:
    raise HTTPException(status_code=409, detail="Texto aprovado e bloqueado para envio.")
```

### Pattern 3: Approve job first, register social second (best-effort, separate step)
**What:** Preserve existing site-publish behavior (`approve_job` + commit) as the success boundary. After job commit succeeds, attempt social registration in separate try/except and separate persistence step; never rollback/unpublish job on social failure. Return structured social outcome for UI messaging.
**When to use:** Approve endpoint evolution (D-09/D-10/D-11).
**Example:**
```python
# Source: backend/app/api/v1/admin.py + backend/app/crud/jobs.py [VERIFIED: codebase]
await approve_job(session, job)
await session.commit()
await session.refresh(job)

social = {"status": "skipped", "message": "no_draft"}
try:
    social = await register_saved_social_draft_as_scheduled(...)
except Exception:
    social = {"status": "warning", "message": "social_registration_failed"}
return {"job": job, "social": social}
```

### Pattern 4: BRT input -> unambiguous persisted schedule; UI reflects frozen/unsaved state
**What:** Frontend collects "Publicar agora" vs "Agendar" with BRT-labeled datetime (UI-SPEC D-07). Backend interprets scheduled wall time in `America/Sao_Paulo`, converts/stores an unambiguous timezone-aware `scheduled_at` and uses now for immediate publish-now approval. Frontend distinguishes saved draft from unsaved edits and disables editing after approved/scheduled.
**When to use:** Draft save/generate response shaping and approve/register.
**Example:**
```python
# Source: Python stdlib zoneinfo/datetime pattern [CITED: stdlib practice] / [ASSUMED exact storage convention]
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

local = datetime.fromisoformat(f"{date_str}T{time_str}").replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
scheduled_at_utc = local.astimezone(timezone.utc)
```

### Anti-Patterns to Avoid
- **Coupling job publish success to social registration:** any exception in social lookup/upsert/transition during approve must not rollback published job (violates D-09/D-11/core value).
- **Trusting frontend for policy compliance:** omitting company/contact, validating `SITE_PUBLIC_URL`, and selecting approval text/schedule must be enforced server-side (D-08/D-15/D-17).
- **Generating drafts from unsaved form/job edits:** draft generation must read persisted `Job` state (D-04).
- **Listing-time LLM calls:** review queue/list endpoints must not trigger Groq generation (D-01).
- **In-place mutation of approved scheduled text:** once registered approved/scheduled, treat text as frozen (D-12/POST-05).
- **Inventing missing public link:** if `SITE_PUBLIC_URL` is absent/invalid, return actionable draft-generation error; never fabricate URL (D-17).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Groq HTTP/auth/request plumbing from scratch | bespoke raw HTTP client for completions in social module | Existing Groq SDK integration/config seam patterns (`groq` + settings) | Retries/errors/model config already exist; reuse reduces drift and secret handling mistakes (D-03). |
| Timezone conversion logic | ad-hoc string math for BRT offsets/DST | `zoneinfo.ZoneInfo("America/Sao_Paulo")` + aware `datetime` conversion | DST/offset correctness and explicit conversions are error-prone by hand. |
| Job review/auth/public URL routing primitives | new auth, new public detail route, custom deep-link parser | Existing `require_admin`, `SITE_PUBLIC_URL`, and `/?vaga=<id>` support in public page | Reuse validated patterns and preserve current behavior (D-13). |
| UI primitives inconsistent with admin theme | new component library/design-system migration | Existing admin tokens/classes, dialog/toast patterns, native controls per UI-SPEC | Phase scope is embedded section, not design-system work. |

**Key insight:** Phase 16 is mostly orchestration and policy-safe state transitions over existing primitives (Groq, `SocialPost`, review UI). Custom low-level solutions increase risk in the exact areas locked by constraints: non-blocking approval, policy leakage, and schedule correctness.

## Common Pitfalls

### Pitfall 1: Social registration failure rolls back published job
**What goes wrong:** Approve handler registers social post in same transaction and exception rolls back/unpublishes job.
**Why it happens:** Tendency to perform all work in one request transaction.
**How to avoid:** Commit job publish first; run social registration in separate best-effort step with isolated error handling and explicit social outcome in response (D-09/D-11).
**Warning signs:** Single try/except around both operations; no social status in approve response; UI cannot distinguish site success from social failure.

### Pitfall 2: Policy leak (company/contact appears in post)
**What goes wrong:** Template or LLM output includes company name, email, phone, WhatsApp, or other contact hints despite D-15.
**Why it happens:** Job payload contains company/contact fields and prompt/template interpolates too much.
**How to avoid:** Centralize allowed-field assembly/sanitization (only title/city/salary/activities/benefits excerpts + CTA/link), enforce on LLM and template outputs, never include company/contact as allowed content, and defensively scrub obvious email/phone patterns before save/return (D-15/D-16/D-17). [RECOMMENDED]
**Warning signs:** Prompt/template references `company`, `contact_email`, `contact_phone`; preview differs from saved text.

### Pitfall 3: Approve uses unsaved editor state
**What goes wrong:** UI shows edited text/schedule but approve registers older saved draft (or none), causing inconsistency.
**Why it happens:** Frontend local state not persisted; approval endpoint reads DB draft only.
**How to avoid:** Explicit save action/state indicators (D-08, UI-SPEC `Alterações não salvas`), backend approval consumes only last saved draft, and UI reminds before approve when unsaved (discretionary but recommended).
**Warning signs:** No save call on edits; regenerate/save doesn't update "Rascunho salvo" state.

### Pitfall 4: `America/Sao_Paulo` schedule stored ambiguously
**What goes wrong:** Scheduled posts become due at wrong UTC time or behave incorrectly across DST/naive datetimes.
**Why it happens:** Treating user-entered local datetime as UTC/naive without conversion metadata.
**How to avoid:** Parse schedule as BRT wall time, attach `ZoneInfo("America/Sao_Paulo")`, convert to unambiguous timezone-aware value before persisting; "publish now" uses current time unambiguously (D-07/D-10).
**Warning signs:** BRT shown in UI but backend stores naive/assumed UTC values.

### Pitfall 5: `SITE_PUBLIC_URL` missing/invented
**What goes wrong:** Generate crashes opaquely or code fabricates a link, producing unusable/non-compliant posts.
**Why it happens:** `SITE_PUBLIC_URL` is optional in settings and may be empty in some environments.
**How to avoid:** Validate/normalize URL at draft-generation boundary; return actionable error for generate/regenerate and never invent link; keep job publish/review usable (D-17).
**Warning signs:** Concatenation on empty base URL; generic failures without actionable message.

### Pitfall 6: Breaking existing admin/frontend contracts
**What goes wrong:** `approveJob` currently expects `JobAdmin`; changing endpoint response shape without coordinated frontend/types update breaks queue actions.
**Why it happens:** D-09 requires communicating social warning/outcome from approve.
**How to avoid:** Plan explicit API contract update (new response schema) and update `frontend/lib/api.ts`, `ReviewQueue.tsx` optimistic/toast handling together.
**Warning signs:** Backend returns envelope but frontend still types/parses `JobAdmin`.

## Code Examples

Verified patterns from current codebase / standard stdlib usage:

### Upsert/get draft by unique `(job_id, provider)`
```python
# Source: backend/app/models/social_post.py + SQLAlchemy async patterns [VERIFIED: codebase]
stmt = select(SocialPost).where(
    SocialPost.job_id == job_id,
    SocialPost.provider == "facebook",
)
social_post = await session.scalar(stmt)
if social_post is None:
    social_post = SocialPost(job_id=job_id, provider="facebook", text=text, status=SocialPostStatus.draft)
    session.add(social_post)
else:
    if social_post.status != SocialPostStatus.draft:
        raise HTTPException(status_code=409, detail="Texto aprovado e bloqueado para envio.")
    social_post.text = text
    social_post.scheduled_at = scheduled_at
await session.flush()
```

### Reuse Groq config seam for dedicated social prompt
```python
# Source: backend/app/services/extraction/client.py (config/seam patterns) [VERIFIED: codebase]
# Phase 16 adaptation: separate prompt/messages and plain-text post output; keep settings-driven model/timeout.
client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=settings.GROQ_TIMEOUT_SECONDS)
resp = await client.chat.completions.create(
    model=settings.GROQ_MODEL,
    messages=[
        {"role": "system", "content": SOCIAL_SYSTEM_PROMPT},
        {"role": "user", "content": prompt_from_persisted_job},
    ],
    temperature=0.4,
)
text = (resp.choices[0].message.content or "").strip()
```

### BRT schedule conversion to unambiguous datetime
```python
# Source: Python stdlib zoneinfo/datetime pattern [CITED: stdlib practice] / [ASSUMED implementation details]
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def brt_wall_time_to_utc(date_str: str, time_str: str) -> datetime:
    local_naive = datetime.fromisoformat(f"{date_str}T{time_str}")
    local_aware = local_naive.replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
    return local_aware.astimezone(timezone.utc)
```

### Public deep-link construction (D-13)
```python
# Source: D-13 + frontend/app/(public)/page.tsx + Settings.SITE_PUBLIC_URL [VERIFIED: codebase/CONTEXT]
base = settings.SITE_PUBLIC_URL.strip().rstrip("/")
# require valid http/https URL before use (D-17)
return f"{base}/?vaga={job_id}"
```

### Frontend approve response handling split (site success vs social warning)
```ts
// Source: frontend/app/admin/review/ReviewQueue.tsx patterns [VERIFIED: codebase]
const result = await approveJob(token, job.id); // proposed: { job, social }
setItems(prev => prev.filter(i => i.id !== result.job.id));
if (result.social.status === "registered") toast("Vaga publicada no site. Post social registrado para envio.", "success");
else if (result.social.status === "skipped") toast("Vaga publicada no site. Nenhum rascunho social salvo — publicação no Facebook não foi registrada.", "warning");
else toast("Vaga publicada no site. Não foi possível registrar o post social agora.", "warning");
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Approve endpoint returns only approved `JobAdmin` | Approve returns site-publish result plus best-effort social registration outcome | Phase 16 (planned) | Enables D-09/D-11 UX without making social failures fatal. |
| Extraction-only Groq usage | Reused Groq integration/config for social copy generation with dedicated prompt and deterministic fallback | Phase 16 (planned) | Satisfies POST-01/02 while preserving reliability of review flow. |
| Social foundation data/contracts only (Phase 14/15) | Active draft lifecycle and approval-time registration into `social_posts` (`draft` -> `scheduled`) | Phase 16 (planned) | Bridges admin curation to Phase 17 async publishing worker. |

**Deprecated/outdated:**
- Any prompt/template variant that includes company name or direct contact details: **superseded by D-15** (explicit user correction), even if earlier generic examples suggested them.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Existing project dependency versions match AGENTS/stack summary; no new libraries are required for Phase 16 implementation. | Standard Stack / Installation | Minor planning drift; implementation may need quick verification/addition (unlikely). |
| A2 | Best contract is to evolve approve API to an envelope containing `job` and `social` outcome and update frontend callers/types atomically. | Architecture Patterns / Pitfall 6 | Contract mismatch/refactor risk; mitigated by coordinated same-phase change. |
| A3 | `scheduled_at` should be stored as a concrete timezone-aware timestamp for both "publish now" (now) and future schedules (BRT converted), to be Phase 17 worker-friendly. | Pattern 4 / Code Examples | Phase 17 may expect different representation; confirm consistency during planning/implementation. |
| A4 | A dedicated boolean policy env var in `Settings` + `.env.example` (default false) satisfies POST-06 configurability; exact name/shape is discretionary. | D-16 / Open Questions | Naming mismatch with future expectations; easy to align if documented clearly. |
| A5 | Defensive backend scrubbing of email/phone/contact-like tokens (in addition to prompt/template rules) is the most robust central enforcement for D-17. | Common Pitfalls / Pattern 1 | Over-scrubbing could remove benign text in edge cases; tune patterns conservatively. |
| A6 | `zoneinfo` timezone data for `America/Sao_Paulo` is available in backend runtime environments (dev/deploy). | Pattern 4 / Environment Availability | Schedule conversion failures at runtime; may require tzdata/package verification. |

## Open Questions (RESOLVED)

1. **Exact approve response contract shape — RESOLVED**
   - Decision (16-01/16-02/16-03): `PATCH /api/v1/admin/jobs/{job_id}/approve` returns `JobApproveResponse` envelope `{ job: JobAdmin, social: { status: 'registered'|'skipped'|'warning', code?: string|null, message?: string|null } }`.
   - Compatibility: all callers updated in the same phase (`frontend/lib/api.ts` `approveJob` returns `JobApproveResponse`, `ReviewQueue.tsx` consumes `result.job` and branches toasts on `result.social.status`). No backward-compat shim retained for the old `JobAdmin`-only shape.

2. **Canonical draft endpoint design and payload — RESOLVED**
   - Decision (16-02/16-03): admin-protected endpoints `GET /api/v1/admin/jobs/{job_id}/social-post`, `POST /api/v1/admin/jobs/{job_id}/social-post/generate`, `PUT /api/v1/admin/jobs/{job_id}/social-post` (provider fixed to `facebook`).
   - Behavior: `POST .../generate` generates/regenerates from persisted `Job`, applies policy/link rules, **auto-persists/upserts** the draft (`status='draft'`) and returns `SocialPostDraftResponse` with `origin` (`llm`/`template_fallback`) and `warning` when applicable. `PUT .../social-post` performs explicit save of last edited text + `publish_mode` + BRT schedule inputs with upsert/draft-only mutability. `GET .../social-post` loads current draft state for dialog open/reopen (absence handled consistently per implemented schema with frontend `null`/empty-state handling). Mutations on non-draft (`frozen`) return HTTP 409 `Texto aprovado e bloqueado para envio.`

3. **"Publish now" persistence convention — RESOLVED**
   - Decision (16-01/16-02): draft payload/state persists explicit `publish_mode` (`publish_now`|`schedule`) and BRT schedule inputs for "last saved draft" semantics (D-08). **Approval registration is authoritative:** on approve, draft `status` becomes `scheduled` with concrete timezone-aware `scheduled_at` = `now_utc()` for `publish_now`, or BRT wall-time converted unambiguously (via `zoneinfo("America/Sao_Paulo")`) for `schedule` (D-10), ensuring Phase 17 eligibility/compatibility.

4. **Policy env var naming/format (POST-06/D-16) — RESOLVED**
   - Decision (16-01): `SOCIAL_POST_INCLUDE_CONTACT: bool = False` in `backend/app/core/config.py` and `SOCIAL_POST_INCLUDE_CONTACT=false` documented in `backend/.env.example` with pt-BR comment stating default excludes company/contact and keeps only public job link. Central enforcement remains server-side in generation/template/fallback/sanitization/save paths.

5. **How to load/freeze draft state across dialog reopen — RESOLVED**
   - Decision (16-02/16-03): `EditJobDialog` fetches draft on open/job select via `GET /social-post` and renders saved/frozen/unsaved/origin states per `16-UI-SPEC.md`. Server-side enforcement: only `status='draft'` is mutable (generate/save reject frozen with 409); approve consumes last saved draft and marks registered post `scheduled` (immutable). UI disables editing/controls when `frozen` and shows `Texto aprovado e bloqueado para envio.` / `Texto bloqueado após aprovação` states as specified.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python + FastAPI/SQLAlchemy app runtime | Backend endpoints/services | ✓ (repo present) | [ASSUMED] per project stack | — |
| Node.js / npm + Next.js dev/build | Frontend admin UI changes | ✓ (repo present) | [ASSUMED] per project stack | — |
| PostgreSQL (Neon / configured DB) | `social_posts` upsert/approve registration | ✓ (project configured) | Managed/Postgres-compatible | Use configured `DATABASE_URL`/`TEST_DATABASE_URL` per env |
| Groq API (`GROQ_API_KEY`) | LLM post generation (POST-01) | ? (env-dependent) | API service | Deterministic template fallback (POST-02/D-03); review must remain unblocked |
| `SITE_PUBLIC_URL` configured (valid http/https) | Public CTA link in draft/post (D-13/D-17) | ? (env-dependent) | URL config | Actionable draft-generation error (no invented link); job publish/review remain unblocked |
| `America/Sao_Paulo` timezone data (`zoneinfo`) | BRT schedule conversion (D-07/D-10) | ✓ likely in modern Python runtimes | stdlib tz database | [ASSUMED] verify in target env; provide tzdata if missing |

**Missing dependencies with no fallback:**
- None that block Phase 16 delivery if deterministic fallback and actionable `SITE_PUBLIC_URL` validation are implemented as specified.

**Missing dependencies with fallback:**
- Groq unavailable/misconfigured: use template fallback and surface warning/origin state.
- `SITE_PUBLIC_URL` absent/invalid: block draft link generation with clear actionable error, but do not block vaga review/publish flow.

## Validation Architecture

> `workflow.nyquist_validation` is enabled in `.planning/config.json` (true), so this section is included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend, existing) + frontend lint/type/build checks (existing project practice); comprehensive automation/manual docs remain Phase 18 scope |
| Config file | `backend/pyproject.toml` / `backend/tests/*` conventions (existing); frontend `package.json` scripts (existing) |
| Quick run command | `cd backend && pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py tests/test_admin_social_posts.py` |
| Full suite command | `cd backend && pytest -q` and frontend project checks as applicable (e.g. `npm run lint` / `npm run build` in `frontend`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| POST-01 | Generate pt-BR draft from persisted job via Groq-configured service with CTA/link, hashtags/emojis, ~700 target; no company/contact in allowed content/output | unit/integration (mock Groq) | `pytest tests/test_social_post_generation.py -x` | ❌ Wave 0 |
| POST-02 | LLM failure/unavailable yields deterministic template fallback and saved draft (never blocks review) | unit/integration | `pytest tests/test_social_post_generation.py -x` | ❌ Wave 0 |
| POST-03 | Draft edit/save/regenerate API behavior and response fields support editor workflow (text, origin/state, saved draft) | integration/API | `pytest tests/test_admin_social_posts.py -x` | ❌ Wave 0 |
| POST-04 | Publish-now vs schedule in `America/Sao_Paulo` persisted/converted correctly for approval/registration | unit/integration | `pytest tests/test_admin_social_posts.py -x` | ❌ Wave 0 |
| POST-05 | Approved/scheduled post text becomes immutable (saved in `social_posts`, edits/regenerate rejected) | integration/API | `pytest tests/test_admin_social_posts.py -x` | ❌ Wave 0 |
| POST-06 | Default policy excludes direct contact and excludes company; link built from `SITE_PUBLIC_URL + /?vaga=<id>`; configurable backend flag; actionable error on missing/invalid site URL for draft link generation | unit/integration | `pytest tests/test_social_post_policy.py tests/test_admin_social_posts.py -x` | ❌ Wave 0 |
| D-09/D-11 | Approve publishes site even when no draft or social registration fails (best-effort warning outcome) | integration/API | `pytest tests/test_admin_social_posts.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** Run targeted backend tests for touched social/admin modules (and quick frontend type/lint if UI/API contract files changed).
- **Per wave merge:** `cd backend && pytest -q` for relevant suites; frontend `lint`/`build` smoke for admin review changes.
- **Phase gate:** Phase 16 implementation tasks green on targeted tests + no contract regressions in review/approve flow; full formal automated/manual coverage remains scoped to Phase 18 per roadmap.

### Wave 0 Gaps
- [ ] `backend/tests/test_social_post_generation.py` — covers POST-01/POST-02 (prompt/template/fallback/policy-safe output, mocked Groq)
- [ ] `backend/tests/test_social_post_policy.py` — covers POST-06/D-15/D-17 (no company/contact, link construction, SITE_PUBLIC_URL validation, config flag behavior)
- [ ] `backend/tests/test_admin_social_posts.py` — covers POST-03/04/05 and D-08..D-12 (draft CRUD/upsert, approve best-effort contract, immutability, schedule conversion/persistence expectations)
- [ ] `backend/tests/conftest.py` (extend as needed) — fixtures/helpers for admin-auth requests, job fixtures, social post assertions
- [ ] Frontend validation scripts/tasks for `EditJobDialog.tsx`/`ReviewQueue.tsx`/`lib/api.ts` contract changes (lint/build/typecheck) — confirm existing commands in `frontend/package.json`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Reuse existing admin JWT auth (`require_admin`) on all new draft/save/approve social endpoints; no new auth surface. |
| V3 Session Management | limited | No new session mechanism; rely on existing token/session handling patterns in admin frontend/backend. |
| V4 Access Control | yes | Admin-only access to social draft/approval operations and to any social outcome data exposed in Phase 16 responses; never expose secrets/tokens. |
| V5 Input Validation | yes | Pydantic schemas for draft/save/schedule payloads, strict enum/mode validation, UUID/path validation, BRT datetime parsing/validation, `SITE_PUBLIC_URL`/policy config validation. |
| V6 Cryptography | no (new crypto ops) | No new token encryption required for draft text flow; reuse existing social crypto only where already applicable. |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection / unsafe reuse of untrusted job text in LLM prompt | Tampering | Treat job fields as data (clear prompt framing), constrain output intent, and post-process with policy sanitizer (D-15/D-17). |
| Sensitive/contact data leakage in generated post or logs | Information Disclosure | Central policy enforcement removes company/contact, avoid logging raw sensitive content, never return secrets. |
| Broken authorization on new admin social endpoints | Elevation of Privilege | Require `Depends(require_admin)` consistently; mirror existing admin route protections. |
| State inconsistency enabling unintended approval behavior | Tampering / Integrity | Server-side "last saved draft" as approval source (D-08), immutable approved records (D-12), separate site-vs-social outcome reporting. |
| Invalid schedule/timezone input causing wrong-time publication later | Integrity | Strict BRT parsing + timezone-aware conversion/validation; reject ambiguous/invalid schedule inputs per chosen contract. |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/16-geracao-revisao-e-aprovacao-do-post-social/16-CONTEXT.md` - locked decisions D-01..D-17, scope boundaries, discretion/deferred items
- `.planning/phases/16-geracao-revisao-e-aprovacao-do-post-social/16-UI-SPEC.md` - UI contract for embedded social post section, states/copy/interactions/accessibility
- `.planning/phases/16-geracao-revisao-e-aprovacao-do-post-social/16-DISCUSSION-LOG.md` - rationale and selected alternatives (audit trail)
- `.planning/REQUIREMENTS.md` - POST-01..POST-06 definitions and traceability
- `.planning/ROADMAP.md` - Phase 16 goal/success criteria/dependencies
- `.planning/PROJECT.md`, `.planning/STATE.md` - milestone constraints, core value, prior decisions
- `.planning/phases/14-fundacao-social-dados-e-configuracao/14-CONTEXT.md`, `.planning/phases/15-oauth-meta-e-integracoes-no-admin/15-CONTEXT.md` - inherited social/domain constraints
- `backend/app/models/social_post.py`, `backend/app/models/social_post_log.py`, `backend/app/models/social_account.py` - persistence model/status/fields/uniqueness
- `backend/app/api/v1/admin.py`, `backend/app/crud/jobs.py`, `backend/app/models/job.py` - current approve/review flow and persisted job source fields
- `backend/app/services/extraction/client.py`, `backend/app/services/extraction/extractor.py`, `backend/app/core/config.py`, `backend/.env.example` - Groq/config patterns and env surface
- `backend/app/api/v1/integrations.py`, `backend/app/schemas/social_integrations.py`, `backend/app/services/social/*` - existing social domain conventions and router/schema/service organization
- `frontend/app/admin/review/EditJobDialog.tsx`, `frontend/app/admin/review/ReviewQueue.tsx`, `frontend/app/admin/review/page.tsx` - integration points and UI behavior patterns
- `frontend/lib/api.ts`, `frontend/app/(public)/page.tsx` - API client contract and deep-link `?vaga=<id>` behavior
- `.planning/config.json` - workflow/validation settings (nyquist enabled)

### Secondary (MEDIUM confidence)
- Python `zoneinfo` / `datetime` timezone conversion approach for local wall-time to UTC persistence (standard library practice, not fetched from external docs in-session)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - derived from existing repository stack, codebase patterns, and locked project constraints
- Architecture: HIGH - integration points and data flow verified against current backend/frontend/social models and locked decisions
- Pitfalls: HIGH - based on explicit phase constraints (non-blocking approval, policy, BRT schedule, saved-draft source of truth) and observed current contracts

**Research date:** 2026-11-15
**Valid until:** 2026-12-15 (stable internal architecture/policies; revalidate if Phase 16 scope decisions or social schema/contracts change)