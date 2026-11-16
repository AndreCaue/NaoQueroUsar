---
phase: 16-geracao-revisao-e-aprovacao-do-post-social
verified: 2026-11-16T00:00:00Z
status: human_needed
score: 10/10 must-haves verified
overrides_applied: 0
requirements_accounted:
  - POST-01
  - POST-02
  - POST-03
  - POST-04
  - POST-05
  - POST-06
human_verification:
  - test: "Fluxo completo de rascunho social no admin"
    expected: "Ao abrir uma vaga em revisão, a seção 'Post para Facebook' permite gerar/regenerar, editar, ver contador/prévia/origem, salvar explicitamente, alternar 'Publicar agora'/'Agendar publicação' com data/hora em America/Sao_Paulo, e reflete estados 'Alterações não salvas' e 'Texto bloqueado após aprovação' quando aplicável."
    why_human: "Interação visual, estados de loading/confirmação, acessibilidade e comportamento do dialog nativo não são totalmente verificáveis por inspeção estática."
  - test: "Aprovação site-first com feedback social"
    expected: "Aprovar vaga com draft salvo registra/agenda social e mostra toast de sucesso social; aprovar sem draft publica a vaga e mostra warning de rascunho ausente; falha de registro social (simulada) mantém vaga publicada e mostra warning sem tratar como falha de publicação do site."
    why_human: "Requer execução integrada com UI/DB para confirmar experiência ponta a ponta e mensagens exibidas."
  - test: "Execução dos testes de integração DB-backed"
    expected: "`cd backend && python -m pytest -q tests/test_admin_social_posts.py tests/test_social_post_generation.py tests/test_social_post_policy.py -x` passa em ambiente com banco de testes migrado."
    why_human: "Ambiente desta verificação não executou os testes DB-backed; 16-02-SUMMARY registrou bloqueio por relações ausentes no DB de teste."
---

# Phase 16: Geração, Revisão e Aprovação do Post Social — Verification Report

**Phase Goal:** Na revisão, o admin recebe um rascunho de post (IA ou fallback), pode ajustar/agendar e aprovar a vaga com criação do registro social sem que falhas sociais afetem a publicação no site.
**Verified:** 2026-11-16T00:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Ao revisar, sistema gera rascunho pt-BR via LLM (Groq config existente) ou template fallback determinístico com CTA/link, salvo como `draft` sem bloquear revisão. | ✓ VERIFIED | `backend/app/services/social/post_generation.py`: `generate_draft_for_job` usa `settings.GROQ_*`, mensagens pt-BR, fallback `template_fallback` com `FALLBACK_WARNING`, `generate_template_fallback` com CTA/hashtags/emoji/alvo ~700 e `sanitize_and_enforce_policy`. `backend/app/api/v1/admin.py` `POST /jobs/{id}/social-post/generate` carrega Job persistido, gera, faz `upsert_draft(... status draft)` e retorna `origin/warning`. `backend/app/crud/social_posts.py` `upsert_draft` persiste/atualiza draft por `(job_id, provider)`. Testes unitários: `tests/test_social_post_generation.py`, `tests/test_social_post_policy.py` → **10 passed**. |
| 2 | Revisor pode editar, regenerar, ver preview/contador e escolher publicar agora ou agendar em `America/Sao_Paulo` (padrão imediato). | ✓ VERIFIED | `frontend/app/admin/review/EditJobDialog.tsx`: seção `Post para Facebook`, textarea, contador `{n}/700 caracteres`, `Prévia do post`, botões `Gerar rascunho`/`Regenerar com IA`/`Salvar rascunho`, confirmação de sobrescrita, toggle `Publicar agora`/`Agendar publicação`, inputs date/time com helper `Horário em America/Sao_Paulo.` e validação. `frontend/lib/api.ts`: `get/generate/saveSocialDraft`, tipos/mode/schedule. Backend: `SocialPostDraftRequest` (`publish_mode`, `scheduled_date/time`), `_resolve_draft_schedule` + `brt_wall_time_to_utc` (`ZoneInfo("America/Sao_Paulo")`) em `post_generation.py`, `PUT/POST` admin persistem draft explicitamente. |
| 3 | Aprovar publica vaga no site imediatamente e registra `social_post` aprovado (`scheduled`, imutável após envio) com modo/horário corretos; falha/ausência social nunca bloqueia/desfaz publicação da vaga. | ✓ VERIFIED | `backend/app/api/v1/admin.py` `approve`: valida fila, executa `approve_job` + `session.commit()` + `refresh` (site-first) antes do social; busca draft: ausente → `skipped/no_draft`, draft → `mark_scheduled` com `scheduled_at` salvo ou `now_utc()` e commit separado → `registered`, exceção no registro → `rollback` isolado e `warning/social_registration_failed`; retorna `JobApproveResponse{job,social}`. `mark_scheduled` define `status=scheduled`. Mutações `generate/save` rejeitam não-draft com 409 `Texto aprovado e bloqueado para envio.`; `upsert_draft` levanta `frozen` para não-draft. Testes de integração cobrindo invariantes existem em `tests/test_admin_social_posts.py` (DB-backed, não executados neste ambiente). |
| 4 | Conteúdo segue política configurada: por padrão sem empresa/contatos, apenas link público `{SITE_PUBLIC_URL}/?vaga=<job_id>`; ausente/inválida falha com erro acionável sem inventar link. | ✓ VERIFIED | `backend/app/core/config.py`: `SOCIAL_POST_INCLUDE_CONTACT: bool = False`; `backend/.env.example`: `SOCIAL_POST_INCLUDE_CONTACT=false` com comentário pt-BR (sem empresa/contatos por padrão). `post_generation.py`: `build_public_job_link` valida http/https e retorna `{base}/?vaga={job_id}` ou levanta `ACTIONABLE_SITE_URL_ERROR` exato; `sanitize_and_enforce_policy` remove `company`/contatos/padrões email/telefone/whats, nunca inclui contato com flag off, garante link; geração/template aplicam sanitização. Admin propaga erro acionável (422). UI exibe mensagem acionável (`SITE_PUBLIC_URL_ERROR`). |

**Score:** 10/10 truths verified (roadmap SC 1–4 + plan must-haves consolidados)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/social/post_generation.py` | Geração LLM+fallback, política/link, BRT | ✓ VERIFIED | `build_public_job_link`, `/?vaga=`, `ZoneInfo("America/Sao_Paulo")`, sanitização, `generate_draft_for_job`, fallback determinístico, erro acionável. |
| `backend/app/crud/social_posts.py` | get/upsert draft, mark_scheduled por `(job_id, provider)` | ✓ VERIFIED | `get_by_job_provider`, `upsert_draft` (draft-only/frozen), `mark_scheduled` → `SocialPostStatus.scheduled`. |
| `backend/app/schemas/social_posts.py` | Schemas draft/save/outcome | ✓ VERIFIED | `SocialPostDraftRequest/Response`, `SocialApproveOutcome` (`registered|skipped|warning`). |
| `backend/app/schemas/job.py` | Envelope approve | ✓ VERIFIED | `JobApproveResponse(job: JobAdmin, social: SocialApproveOutcome)`. |
| `backend/app/core/config.py` | Flag política default off | ✓ VERIFIED | `SOCIAL_POST_INCLUDE_CONTACT: bool = False`. |
| `backend/.env.example` | Documentação flag/política | ✓ VERIFIED | `SOCIAL_POST_INCLUDE_CONTACT=false` + comentário sem empresa/contatos. |
| `backend/app/api/v1/admin.py` | Endpoints draft GET/POST generate/PUT e approve envelope site-first | ✓ VERIFIED | Rotas protegidas por `require_admin`; 409 frozen; erro SITE_PUBLIC_URL; approve retorna envelope e trata `registered/skipped/warning` após commit do job. |
| `backend/tests/test_social_post_generation.py` | Cobertura POST-01/02 | ✓ VERIFIED | Casos LLM, fallback, policy-safe; suíte unitária passou. |
| `backend/tests/test_social_post_policy.py` | Cobertura POST-06/link/política | ✓ VERIFIED | Link, erro acionável exato, scrub contatos/empresa. |
| `backend/tests/test_admin_social_posts.py` | Cobertura POST-03..06, D-04/08..12/17 | ✓ VERIFIED (authored) | Testes presentes e alinhados ao contrato; execução DB-backed não verificada neste ambiente. |
| `frontend/lib/api.ts` | Tipos/funções draft e approve envelope | ✓ VERIFIED | `SocialPostDraft`, `JobApproveResponse`, `get/generate/saveSocialDraft`, `approveJob` → `Promise<JobApproveResponse>`, rotas `/social-post` e `/social-post/generate`. |
| `frontend/app/admin/review/EditJobDialog.tsx` | Seção Post para Facebook com estados/controles | ✓ VERIFIED | Heading, gerar/regenerar/salvar, contador/prévia, modos agora/agendar BRT, unsaved/frozen/origem/fallback, mensagem acionável SITE_PUBLIC_URL. |
| `frontend/app/admin/review/ReviewQueue.tsx` | Approve consome `{job,social}` e toasts site vs social | ✓ VERIFIED | Usa `result.job`/`result.social.status`; mensagens para `skipped` e `warning` preservam sucesso da vaga no site. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `services/social/post_generation.py` | `core/config.py` | `settings.GROQ_*`, `SITE_PUBLIC_URL`, `SOCIAL_POST_INCLUDE_CONTACT` | ✓ WIRED | Lidos/validados no serviço. |
| `services/social/post_generation.py` | `models/job.py` (dados persistidos) | Campos permitidos; company/contatos excluídos/scrub | ✓ WIRED | `_job_allowed_data`/sanitização; testes garantem ausência. |
| `crud/social_posts.py` | `models/social_post.py` | `SocialPost`, `SocialPostStatus`, upsert por job/provider | ✓ WIRED | Draft/scheduled e guarda `frozen`. |
| `api/v1/admin.py` (approve) | `crud/jobs.py` | `approve_job` + commit antes do social | ✓ WIRED | `approve()` commit site-first. |
| `api/v1/admin.py` | `crud/social_posts.py` | `get_by_job_provider`, `upsert_draft`, `mark_scheduled` | ✓ WIRED | Draft endpoints e registro best-effort. |
| `api/v1/admin.py` | `services/social/post_generation.py` | `generate_draft_for_job`, `build_public_job_link`, `brt_wall_time_to_utc`, `sanitize_and_enforce_policy`, `now_utc` | ✓ WIRED | Geração, validação, política e agendamento. |
| `EditJobDialog.tsx` | `frontend/lib/api.ts` | `get/generate/saveSocialDraft` | ✓ WIRED | Carrega/gera/salva draft. |
| `ReviewQueue.tsx` | `frontend/lib/api.ts` | `approveJob` + `result.job/result.social` | ✓ WIRED | Branch de toasts por outcome social. |
| `frontend (draft UI)` | Backend draft/approve contract | `publish_now/schedule`, BRT, frozen/saved/origin, envelope approve | ✓ WIRED | Campos/strings/fluxos alinhados ao contrato 16-02. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `EditJobDialog.tsx` social section | `socialDraft` / `socialText` / mode/schedule | `getSocialDraft` → `GET /admin/jobs/{id}/social-post`; generate/save responses | ✓ API-backed (DB via backend CRUD) | ✓ FLOWING |
| `admin.py` generate/save/get | Draft content/schedule/origin | `generate_draft_for_job` (Groq/fallback) + `upsert_draft`/`get_by_job_provider` on persisted `Job`/`social_posts` | ✓ Persisted job & generation service (LLM mocked in tests; fallback deterministic) | ✓ FLOWING |
| `admin.py` approve | `social` outcome + job state | Persisted draft lookup + `mark_scheduled`/exceptions after committed `approve_job` | ✓ Real state transitions/outcomes | ✓ FLOWING |
| `ReviewQueue.tsx` | Approve toasts/list mutation | `approveJob` envelope `result.job`, `result.social.status` | ✓ API-backed | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Unit tests: geração (LLM/fallback) e política/link (POST-01/02/06) | `cd backend; python -m pytest -q tests/test_social_post_generation.py tests/test_social_post_policy.py -x` | 10 passed in 0.10s | ✓ PASS |
| Unit/integration subset completo do plano 02 (inclui DB-backed admin social) | `cd backend; python -m pytest -q tests/test_admin_social_posts.py tests/test_social_post_generation.py tests/test_social_post_policy.py -x` | Não executado completo aqui (DB de testes/migrações não verificados); plano 16-02 registrou bloqueio `relation "jobs" does not exist` em ambiente semelhante | ? SKIP |
| Frontend lint/build | `cd frontend; npm run lint && npm run build` | Não reexecutado integralmente; 16-03 registrou lint ok e build bloqueado por issue pré-existente em `/admin/integracoes` (fora do escopo) | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| POST-01 | 16-01, 16-02 | Geração de texto do post via LLM existente a partir de dados estruturados da vaga (pt-BR, tom/hashtags/emoji/~700, CTA+link) | ✓ SATISFIED | `post_generation.py` (Groq + prompt + trunc/hashtags + link + sanitização), endpoint generate, testes geração passam. |
| POST-02 | 16-01, 16-02 | Fallback por template se LLM falhar; draft gerado/salvo como `draft`, revisão não bloqueada | ✓ SATISFIED | `template_fallback` + `FALLBACK_WARNING`, try/except retorna fallback, `upsert_draft` status draft, UI mostra aviso fallback. |
| POST-03 | 16-02, 16-03 | Revisor edita texto, contador, regenerar com IA, preview | ✓ SATISFIED | `EditJobDialog.tsx` textarea/contador/preview/regenerar/salvar; endpoints GET/POST generate/PUT. |
| POST-04 | 16-01, 16-02, 16-03 | Publicar agora/agendar em `America/Sao_Paulo` (padrão imediato) | ✓ SATISFIED | `brt_wall_time_to_utc` (ZoneInfo BRT), `resolve_scheduled_at/_resolve_draft_schedule`, UI toggle + date/time BRT, approve usa `now_utc` ou horário salvo. |
| POST-05 | 16-02, 16-03 | Texto aprovado imutável após envio e salvo em `social_posts` | ✓ SATISFIED | Approve marca `scheduled` com texto/horário; `mark_scheduled`/`upsert_draft` impedem mutação não-draft; rotas retornam 409 `Texto aprovado e bloqueado para envio.`; UI desabilita quando frozen. |
| POST-06 | 16-01, 16-02, 16-03 | Por padrão sem contato direto, apenas link público `SITE_PUBLIC_URL` + URL da vaga; configurável documentado | ✓ SATISFIED | `SOCIAL_POST_INCLUDE_CONTACT=false` (config/.env), link `/?vaga=<job_id>` validado, scrub empresa/contatos, erro acionável quando URL ausente/inválida. |

**Orphaned requirements (Phase 16, per REQUIREMENTS/ROADMAP):** None — all POST-01..POST-06 declared in plans and accounted for.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/app/api/v1/admin.py` | 255, 312 | `_draft_response` default `origin="template_fallback"` e GET retorna sem origem real persistida (`16-REVIEW.md` WR-01) | ⚠️ Warning | Reabrir/carregar draft salvo pode rotular incorretamente origem (LLM vs fallback) e omitir warning original; não impede geração/edição/salvamento/aprovação nem o registro seguro, mas degrada confiança/UX de procedência. |

### Human Verification Required

### 1. Fluxo completo de rascunho social no admin

**Test:** Abrir uma vaga na fila de revisão, gerar rascunho, editar texto, observar contador/prévia/origem, salvar, alternar para agendar com data/hora BRT, regenerar (confirmar sobrescrita) e reabrir dialog.
**Expected:** Estados e cópias conforme UI-SPEC (loading, fallback quando aplicável, erro acionável de `SITE_PUBLIC_URL`, `Alterações não salvas`, `Rascunho salvo`, frozen após aprovação) e persistência consistente.
**Why human:** Comportamento visual/interativo e acessibilidade do dialog.

### 2. Aprovação site-first com feedback social

**Test:** Aprovar (a) sem draft, (b) com draft salvo (agora/agendado), (c) simulando falha de registro social.
**Expected:** Vaga sempre publicada no site nos casos de sucesso do endpoint; toasts distintos para `registered`/`skipped`/`warning` sem mensagem de falha de publicação da vaga.
**Why human:** Validação ponta a ponta UI↔API↔DB e feedback percebido.

### 3. Testes de integração DB-backed

**Test:** Executar suíte completa do plano 02 em banco migrado.
**Expected:** `tests/test_admin_social_posts.py` e demais passam.
**Why human:** Dependência de ambiente/migrações de teste não confirmada aqui.

### Gaps Summary

No blocking code gaps found against Phase 16 goal or POST-01..POST-06. One warning remains from review (WR-01: draft origin/warning not faithfully preserved on GET), which may misreport provenance after reload but does not block the required outcomes. Automated unit evidence for generation/policy passed; DB-backed integration and full UI runtime behavior need human/environment confirmation.

---

_Verified: 2026-11-16T00:00:00Z_
_Verifier: OpenCode (gsd-verifier)_