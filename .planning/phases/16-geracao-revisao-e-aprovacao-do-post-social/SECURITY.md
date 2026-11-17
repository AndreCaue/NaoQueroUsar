---
phase: 16-geracao-revisao-e-aprovacao-do-post-social
asvs_level: 2
block_on: open
threats_open: 0
threats_closed: 14
unregistered_flags: 0
audited_at: 2026-11-17
---

# Phase 16: Geração, Revisão e Aprovação do Post Social — Security Audit

## Threat Verification

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-16-01 | Tampering / Injection | mitigate | CLOSED | `backend/app/services/social/post_generation.py`: LLM prompt built only from allowed job fields via `_job_allowed_data`/`_build_llm_messages` (title/city/salary/activities/benefits, no company/contact) and output always passed through `sanitize_and_enforce_policy` (strips `company/contact_email/contact_phone` values and scrubs email/phone/WhatsApp patterns; enforces link) for both LLM and template paths; `generate_draft_for_job` returns sanitized text. Tests: `backend/tests/test_social_post_generation.py` (LLM/fallback results exclude company/contacts, link present), `backend/tests/test_social_post_policy.py` (scrub removes company/contacts). |
| T-16-02 | Denial of Service / Abuse | mitigate | CLOSED | `backend/app/services/social/post_generation.py` `generate_draft_for_job`: wraps Groq call in `try/except Exception` and on failure/empty response returns deterministic `generate_template_fallback` with `origin='template_fallback'` and `FALLBACK_WARNING` (review not blocked). Tests: `test_generate_draft_falls_back_to_template_on_llm_failure` in `backend/tests/test_social_post_generation.py`. |
| T-16-03 | Information Disclosure | mitigate | CLOSED | `backend/app/services/social/post_generation.py` `build_public_job_link`: validates `SITE_PUBLIC_URL` scheme/netloc (http/https) and returns only `{base}/?vaga={job_id}` or raises `SocialPostLinkError(ACTIONABLE_SITE_URL_ERROR)` (exact actionable pt-BR, no invented link). Config: `backend/app/core/config.py` `SOCIAL_POST_INCLUDE_CONTACT: bool = False`; `backend/.env.example` documents default no company/contact. API propagates actionable error (`admin.py` generate/save catch `SocialPostLinkError` -> 422 with `ACTIONABLE_SITE_URL_ERROR`). No prompt/response/secret logging added in generation/admin draft paths; tests assert actionable error (`backend/tests/test_social_post_policy.py`, `backend/tests/test_admin_social_posts.py`). |
| T-16-04 | Tampering | mitigate | CLOSED | `backend/app/services/social/post_generation.py`: `BRT_TZ = ZoneInfo("America/Sao_Paulo")`, `brt_wall_time_to_utc` parses wall time and returns timezone-aware UTC; `resolve_scheduled_at` validates mode. `backend/app/api/v1/admin.py` `_resolve_draft_schedule` validates `publish_mode`, requires date/time for `schedule`, converts via `brt_wall_time_to_utc` and raises clear 422 (`Escolha uma data e hora válidas para agendar.` / invalid mode). Tests: `backend/tests/test_admin_social_posts.py` schedule persists coherent UTC and invalid datetime returns 422. |
| T-16-05 | Tampering / Integrity | mitigate | CLOSED | `backend/app/crud/social_posts.py`: `get_by_job_provider`/`upsert_draft` (create-or-update only when `status == draft`, else `ValueError("frozen")`) and `mark_scheduled` sets `status=SocialPostStatus.scheduled`, persists approved text/scheduled_at and flushes. `backend/app/models/social_post.py` defines status enum/uniqueness; `backend/app/api/v1/admin.py` uses CRUD for draft/save and approve registration. Freeze/transition exercised in tests (`backend/tests/test_admin_social_posts.py` approve registers scheduled, frozen mutations rejected). |
| T-16-06 | Elevation of Privilege | mitigate | CLOSED | `backend/app/api/v1/admin.py` protects admin endpoints with `Depends(require_admin)` on social/status/approve routes (e.g. `get_job_social_post` ~L494, `generate_job_social_post` ~L514, `save_job_social_post` ~L561, `approve` ~L139 and related admin handlers); UUID/job lookup enforced (`404 Vaga não encontrada`), draft scoped by `(job_id, 'facebook')`. |
| T-16-07 | Tampering / Integrity | mitigate | CLOSED | `backend/app/api/v1/admin.py` `approve`: site-first — `approve_job` + `await session.commit()` + `await session.refresh(job)` completed before social handling; social registration runs in separate `try/except` with isolated rollback on failure and returns outcomes `skipped|registered|warning` (`no_draft`, `social_registration_failed`) without undoing published job. Tests: `test_approve_without_draft_skips_social_and_keeps_job_published`, `test_approve_with_draft_registers_scheduled`, `test_approve_social_registration_failure_returns_warning_but_keeps_job_published` in `backend/tests/test_admin_social_posts.py`. |
| T-16-08 | Tampering / Integrity | mitigate | CLOSED | `backend/app/api/v1/admin.py`: generate/save reject when existing social post `status != SocialPostStatus.draft` with `HTTPException(409, "Texto aprovado e bloqueado para envio.")` and map CRUD `frozen` to same 409; approve marks draft scheduled (immutable). `backend/app/crud/social_posts.py` `upsert_draft` refuses non-draft. `frontend/app/admin/review/EditJobDialog.tsx` shows frozen state and disables controls. Tests: `test_mutation_rejected_when_draft_scheduled_frozen` in `backend/tests/test_admin_social_posts.py`. |
| T-16-09 | Information Disclosure | mitigate | CLOSED | `backend/app/api/v1/admin.py` returns pt-BR `HTTPException` details for expected errors (e.g. not found, frozen message, actionable SITE_PUBLIC_URL, schedule validation) without exposing tokens/secrets/stack traces in responses. `frontend/app/admin/review/EditJobDialog.tsx` and `ReviewQueue.tsx` surface safe/actionable messages/toasts from API/generic fallbacks. |
| T-16-10 | Tampering / Input Validation | mitigate | CLOSED | `backend/app/api/v1/admin.py` `_resolve_draft_schedule`: validates `publish_mode`, requires `scheduled_date`/`scheduled_time` for `schedule`, converts via `brt_wall_time_to_utc` and rejects invalid/unsupported input with 422 (`Escolha uma data e hora válidas para agendar.` / `Modo de publicação inválido.`); save also validates non-empty text. Tests: `backend/tests/test_admin_social_posts.py` (schedule/publish_now acceptance, invalid datetime 422). |
| T-16-11 | Elevation of Privilege | mitigate | CLOSED | `frontend/lib/api.ts` draft/approve helpers send `Authorization: Bearer ${token}` (`getSocialDraft`, `generateSocialDraft`, `saveSocialDraft`, `approveJob`) and use `ApiError/readError`. `frontend/app/admin/review/ReviewQueue.tsx` `handleAuthError` clears `TOKEN_KEY` and redirects on 401; `EditJobDialog.tsx` also handles expired auth via `handleAuthError` flows for social actions. |
| T-16-12 | Information Disclosure | mitigate | CLOSED | `frontend/app/admin/review/EditJobDialog.tsx` displays actionable/safe errors (maps SITE_PUBLIC_URL to exact safe message; generic fallbacks) and toasts; `frontend/app/admin/review/ReviewQueue.tsx` uses fixed/safe outcome toasts. No token/secret rendering; preview rendered as plain text. |
| T-16-13 | Tampering (UI integrity) | mitigate | CLOSED | `frontend/app/admin/review/EditJobDialog.tsx`: loads saved draft (`getSocialDraft`), tracks dirty vs `lastSavedSnapshot` with `Alterações não salvas` indicator and reminder to save, disables controls when `frozen`, uses explicit save/regenerate actions (last-saved draft used by approve contract), and renders preview as text with `whitespace-pre-wrap` (no `dangerouslySetInnerHTML`). |
| T-16-14 | Spoofing/Confusion | mitigate | CLOSED | `frontend/app/admin/review/ReviewQueue.tsx` `handleApprove` consumes `result.job`/`result.social` and branches toasts: `registered` => site published + social registered, `skipped` => site published + no saved draft warning, `warning` => site published + could not register social now (social failure never reported as site publish failure). |

## Unregistered Flags

None. All plan/summary `## Threat Flags` reviewed (16-01/16-02/16-03: none/planned mitigations noted); no new attack surface without threat mapping identified.

## Accepted Risks

None. All threats disposition `mitigate` and verified CLOSED.

## Notes

- `16-VERIFICATION.md` records human/environment checks pending for full DB-backed integration runtime and UI E2E behavior; code-level mitigations above are present in implementation/tests as cited.
- `16-VERIFICATION.md` notes WR-01 (draft origin/warning provenance on GET) as a non-security UX warning; no impact on threat mitigations verified here.
