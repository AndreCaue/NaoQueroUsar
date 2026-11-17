---
phase: 16
slug: geracao-revisao-e-aprovacao-do-post-social
status: verified
threats_open: 0
asvs_level: 2
created: 2026-11-17
---

# Phase 16 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail for social post draft generation, review, approval, and registration.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Admin UI -> Backend admin API | Authenticated admin actions (draft get/generate/save, approve) via Bearer token | Job IDs, draft text, publish mode/schedule inputs, admin auth token |
| Backend -> LLM (Groq) | Draft generation request built from persisted Job fields | Sanitized/allowed job fields for prompt (no company/contact by policy) and generated text response |
| Backend persistence (DB) | Store/retrieve/update `social_posts` draft/scheduled state | Draft text, status, schedule timestamps, provider/job linkage |
| Admin UI rendering | Render draft/preview/status/toasts from backend responses | User-visible pt-BR messages and draft content (text-only preview) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-16-01 | Tampering / Injection | `post_generation` prompt/contexto LLM | mitigate | `backend/app/services/social/post_generation.py`: prompt usa apenas campos permitidos do Job persistido (sem empresa/contatos); saída LLM/template passa por `sanitize_and_enforce_policy` (remove company/contatos e padrões email/telefone/WhatsApp, garante link). Evidência: `backend/tests/test_social_post_generation.py`, `backend/tests/test_social_post_policy.py`; commits 5c8379f, dd4c093. | closed |
| T-16-02 | Denial of Service / Abuse | Chamadas Groq na geração | mitigate | `generate_draft_for_job` captura falhas/timeout/saída inválida e retorna fallback determinístico `template_fallback` com aviso, sem bloquear revisão/aprovação. Evidência: `post_generation.py` fallback path; `tests/test_social_post_generation.py::test_generate_draft_falls_back_to_template_on_llm_failure`. | closed |
| T-16-03 | Information Disclosure | Link público e logs/erros de geração | mitigate | `build_public_job_link` valida `SITE_PUBLIC_URL` (http/https, netloc) e constrói apenas `{base}/?vaga={job_id}` ou erro acionável pt-BR (`ACTIONABLE_SITE_URL_ERROR`) sem inventar link/expor segredos; `SOCIAL_POST_INCLUDE_CONTACT=false` por padrão. Evidência: `post_generation.py`, `core/config.py`, `.env.example`, `tests/test_social_post_policy.py`, `tests/test_admin_social_posts.py`. | closed |
| T-16-04 | Tampering | Agendamento BRT->UTC | mitigate | `brt_wall_time_to_utc`/`resolve_scheduled_at` com `ZoneInfo("America/Sao_Paulo")` para UTC timezone-aware; admin valida `publish_mode`/data-hora e rejeita inválidos com 422 claro. Evidência: `post_generation.py`, `api/v1/admin.py` `_resolve_draft_schedule`, `tests/test_admin_social_posts.py`. | closed |
| T-16-05 | Tampering / Integrity | Persistência de rascunho/status | mitigate | `crud/social_posts.py` `get_by_job_provider`, `upsert_draft` (flush-only, atualiza apenas draft; frozen -> erro) e `mark_scheduled` (status scheduled, texto/horário aprovados, limpa retry/erro, flush) com unicidade `(job_id, provider)`. Evidência: `crud/social_posts.py`, `models/social_post.py`, `tests/test_admin_social_posts.py`. | closed |
| T-16-06 | Elevation of Privilege | Endpoints `/admin/jobs/{id}/social-post*` e approve | mitigate | Rotas sociais/admin protegidas com `Depends(require_admin)` (e sessão/admin deps), validação de job/path e escopo por `job_id/provider`. Evidência: `backend/app/api/v1/admin.py`. | closed |
| T-16-07 | Tampering / Integrity | Fluxo de approve (site-first) | mitigate | `approve_job` + `commit` + `refresh` antes de qualquer registro social; etapa social isolada em try/except com rollback próprio e outcomes `registered|skipped|warning` (sem desfazer vaga publicada). Evidência: `api/v1/admin.py` approve flow; `tests/test_admin_social_posts.py`, `tests/test_admin_jobs.py`; commit fcfa903. | closed |
| T-16-08 | Tampering | Mutação de draft aprovado/congelado | mitigate | Generate/save rejeitam `status != draft` com HTTP 409 `Texto aprovado e bloqueado para envio.`; CRUD recusa upsert em não-draft; approve registra texto `scheduled` imutável. UI desabilita controles quando frozen. Evidência: `api/v1/admin.py`, `crud/social_posts.py`, `EditJobDialog.tsx`, `tests/test_admin_social_posts.py`. | closed |
| T-16-09 | Information Disclosure | Respostas/erros de API | mitigate | Mensagens pt-BR seguras/acionáveis via `HTTPException` (404/409/422), sem expor tokens/segredos/stack traces. Evidência: `api/v1/admin.py` handlers; auditoria de código. | closed |
| T-16-10 | Tampering / Input Validation | Schedule e payloads de draft | mitigate | Validação de `publish_mode`, exigência de `scheduled_date/time` para agendar, conversão BRT->UTC validada, texto salvo não vazio e 422 claro para entradas inválidas. Evidência: `api/v1/admin.py`, `post_generation.py`, `tests/test_admin_social_posts.py`. | closed |
| T-16-11 | Elevation of Privilege | Chamadas draft/approve no frontend | mitigate | `frontend/lib/api.ts` envia `Authorization: Bearer ${token}` em `get/generate/saveSocialDraft` e `approveJob` com `ApiError/readError`; `ReviewQueue.tsx` mantém `handleAuthError` (401 limpa sessão/redireciona) e `EditJobDialog.tsx` trata sessão expirada. Evidência: `lib/api.ts`, `ReviewQueue.tsx`, `EditJobDialog.tsx`; commit ad18cd3. | closed |
| T-16-12 | Information Disclosure | Toasts/erros de UI | mitigate | UI exibe mensagens seguras/acionáveis retornadas (incl. SITE_PUBLIC_URL) ou genéricas, sem segredos/tokens; toasts de approve usam textos fixos seguros. Evidência: `EditJobDialog.tsx`, `ReviewQueue.tsx`. | closed |
| T-16-13 | Tampering (UI integrity) | Aprovação com estado não salvo / edição de congelado | mitigate | Draft salvo carregado ao abrir, rastreio dirty vs snapshot salvo com `Alterações não salvas` e lembrete de salvar, controles desabilitados quando `frozen`, fluxos explícitos gerar/salvar/regenerar; preview em texto (`whitespace-pre-wrap`, sem `dangerouslySetInnerHTML`). Evidência: `EditJobDialog.tsx`. | closed |
| T-16-14 | Spoofing/Confusion | Feedback de aprovação site vs social | mitigate | `ReviewQueue.tsx` consome `result.job`/`result.social` e comunica site-first com outcomes distintos (`registered`, `skipped`, `warning`) sem tratar falha social como falha de publicação da vaga. Evidência: `ReviewQueue.tsx`, `EditJobDialog.tsx`. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-17 | 14 | 14 | 0 | gsd-security-auditor (verified) |

**Notes:** State B audit (no prior SECURITY.md). Evidence reviewed against plans 16-01/02/03, summaries, code, and tests. `16-VERIFICATION.md` status `human_needed` for runtime/DB-backed confirmation; no open threats identified by this audit.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-17
