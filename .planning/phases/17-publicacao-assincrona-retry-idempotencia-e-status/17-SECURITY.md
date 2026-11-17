---
phase: 17
slug: publicacao-assincrona-retry-idempotencia-e-status
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-17
---

# Phase 17 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Backend -> Meta Graph API (Facebook) | PublicaAA�o de posts sociais em `/{page_id}/feed` via `FacebookPublisher` | Texto/link do post, `page_id`, token de pA�gina (somente em memA3ria backend) |
| Cron externo -> endpoint worker | Acionamento operacional do worker de publicaAA�o sem sessA�o admin | Segredo de cron (`X-Cron-Secret`), gatilho de processamento de lote |
| Admin UI/client -> endpoints de status/retry | Leitura e mutaAA�o de estado de publicaAA�o restritas ao admin | JWT admin, `job_id`, comandos de retry, respostas de status/eligibilidade |
| Backend -> UI/admin payloads | Respostas admin expA�em apenas dados operacionais seguros | Status/labels pt-BR, erro resumido, `external_post_id`/link pA�blico (quando disponA-vel), timestamps/contadores |
| Pipeline/worker interno -> banco/logs | PersistA�ncia de estado, tentativas e auditoria operacional | `social_posts`, `social_post_logs`, `attempts`, `next_retry_at`, `last_error` sanitizado |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-17-01 | Information Disclosure | `backend/app/services/social/facebook.py`, `backend/app/services/social/publish_pipeline.py`, logs/`last_error` | mitigate | Token de pA�gina descriptografado/aplicado apenas em memA3ria no backend (nunca retornado/logado); falhas mapeadas para mensagens pt-BR seguras; logs/persistA�ncia usam campos sanitizados (`_safe_text`, `error_message`/`response_summary`/`external_post_id`) sem payload bruto/segredos. | closed |
| T-17-02 | Tampering / Integrity (duplicidade) | `backend/app/crud/social_posts.py`, `backend/app/services/social/publish_pipeline.py` | mitigate | Claim atA3mico de elegA-veis com `SELECT ... FOR UPDATE SKIP LOCKED` + transiAA�o para `publishing`; no-op para publicado/`external_post_id`; resultado ambA-guo nA�o recebe auto-retry; 17-04 adiciona recuperaAA�o compensatA3ria pA3s-exceAA�o sem duplicar publicaAA�o. | closed |
| T-17-03 | Spoofing / Tampering (destino externo) | `backend/app/services/social/facebook.py` | mitigate | URL de publicaAA�o construA-da apenas com `settings.META_GRAPH_VERSION` e `page_id` da conta persistida (`https://graph.facebook.com/{version}/{page_id}/feed`); nenhum destino fornecido pelo usuA�rio. | closed |
| T-17-04 | Denial of Service | worker/pipeline, retries | mitigate | Processamento limitado a elegA-veis/devidos e lotes (`limit`), timeout explA-cito no `httpx.AsyncClient`, tentativas limitadas por `SOCIAL_MAX_ATTEMPTS` e backoff configurA�vel; permanentes/ambA-guos/reconexA�o nA�o geram auto-retry indevido. | closed |
| T-17-05 | Elevation of Privilege | mA3dulos internos de execuAA�o (17-01) | accept | Sem rotas HTTP expostas na wave 17-01; risco aceito como transitA3rio de composiAA�o e resolvido por proteAA�es de endpoint implementadas em 17-02 (`require_cron_secret`/`require_admin`, T-17-06/T-17-07). | closed |
| T-17-06 | Spoofing / Elevation of Privilege | `POST /api/v1/admin/social/worker` | mitigate | Rota protegida por `Depends(require_cron_secret)` (padrA�o de `/admin/expire`, header `X-Cron-Secret`); Bearer admin nA�o Ac substituto para acionamento cron. | closed |
| T-17-07 | Elevation of Privilege / Information Disclosure | endpoints de status/lista/retry | mitigate | `GET /admin/social-posts`, `GET /admin/jobs/{job_id}/social-status`, `POST /admin/jobs/{job_id}/social-post/retry` exigem `Depends(require_admin)`; contratos/schemas retornam apenas campos seguros (status/labels, erro resumido pt-BR, `published_url`/`external_post_id`, timestamps, elegibilidade) sem tokens/segredos/payload bruto. | closed |
| T-17-08 | Tampering / Integrity (duplicidade/replay) | retry manual e dispatch imediato | mitigate | Retry/dispatch delegam ao pipeline A�nico (`run_social_publish_cycle`/`process_social_post_safe`) com claim+idempotA�ncia; respostas/fluxos idempotentes para publicado, em processamento/jA� resolvido ou inelegA-vel; processamento direcionado por alvo especA-fico. | closed |
| T-17-09 | Denial of Service | worker/retry endpoints | mitigate | Worker processa lote limitado de elegA-veis devidos; retry atua por alvo especA-fico com validaAA�o de elegibilidade (`compute_social_retry_state`/`can_retry`); falhas sociais tratadas sem travar aprovaAA�o do site. | closed |
| T-17-10 | Tampering (regressA�o de fluxo) | `approve` site-first | mitigate | `approve_job + commit + refresh` executados antes de qualquer dispatch social; `BackgroundTasks.add_task(process_social_post_safe, ...)` agendado apenas apA3s commit para casos elegA-veis/registrados, com falhas de dispatch isoladas da resposta HTTP. | closed |
| T-17-11 | Information Disclosure | `frontend/lib/api.ts`, componentes admin sociais | mitigate | UI consome e renderiza apenas campos seguros dos contratos (`status_label`, `last_error`, `published_url`, `external_post_id`, timestamps/contadores); erros apresentados como mensagens pt-BR seguras, sem tokens/segredos/payload bruto/stack trace. | closed |
| T-17-12 | Tampering / Integrity (UI double-submit) | botA�es `Tentar novamente` (revisA�o/lista) | mitigate | Single-flight por item com disable + estado `Tentando novamente...`, atualizaAA�o por resposta/refetch idempotente do backend, e CTA habilitado apenas quando `can_retry=true` (inelegA-veis bloqueados). | closed |
| T-17-13 | Elevation of Privilege (sessA�o expirada) | chamadas admin em novas telas/componentes | mitigate | PadrA�o de tratamento `ApiError.status === 401`: limpeza de `nqu_admin_token` e redirecionamento para `/admin/paste` nas telas/componentes sociais admin. | closed |
| T-17-14 | Spoofing / ConfusA�o de usuA�rio | aAA�es inelegA-veis/reconexA�o | mitigate | UI exibe orientaAA�es pt-BR conforme estado/elegibilidade (`retry_block_reason`, agendado/em andamento/publicado), link `Abrir IntegraAA�es` (`/admin/integracoes`) quando reconexA�o necessA�ria, e nA�o sugere ediAA�o/remoAA�o de post publicado no Facebook (fire-and-forget). | closed |

*Status: open �+' closed*  
*Disposition: mitigate (implementation required) �+' accept (documented risk) �+' transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-17 | 14 | 14 | 0 | gsd-security-auditor (workflow: gsd-secure-phase, state B from PLAN/SUMMARY artifacts + code verification) |

### 2026-11-17 — Phase 17 artifact/code audit notes

- Input state: **B** (no prior `*-SECURITY.md`; `17-01..17-04` PLAN/SUMMARY artifacts present and complete).
- Threat sources: `<threat_model>` registers in `17-01-PLAN.md` (T-17-01..T-17-05), `17-02-PLAN.md` (T-17-06..T-17-10), `17-03-PLAN.md` (T-17-11..T-17-14). No `## Threat Flags` found in `17-01..17-04` SUMMARY files.
- Evidence (representative): worker/cron and admin protections in `backend/app/api/v1/admin.py` (`require_cron_secret`, `require_admin`, `BackgroundTasks` dispatch post-commit); claim/retry/idempotency and safe status contracts in `backend/app/crud/social_posts.py` and `backend/app/schemas/social_posts.py`; Graph publish and pipeline safeguards/sanitized logging in `backend/app/services/social/facebook.py` and `backend/app/services/social/publish_pipeline.py`; admin UI status/retry/reconnect handling in `frontend/lib/api.ts`, `frontend/app/admin/review/EditJobDialog.tsx`, `frontend/app/admin/review/ReviewQueue.tsx`, `frontend/components/admin/ReviewRow.tsx`, and `frontend/app/admin/social-posts/SocialPostsClient.tsx`.
- Residual/operational notes (not open threats): DB-backed automated verification and real Meta/cron end-to-end/human UAT remain environment-dependent per phase artifacts; these do not change `threats_open` for the registered dispositions.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-17
