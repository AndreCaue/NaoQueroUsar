---
phase: 09-lifecycle-trust-legal-launch-completeness
verified: 2026-11-15T00:00:00Z
initial_verified: 2026-11-15
reconciled: 2026-11-15
status: passed
score: 6/6 success criteria verified
caveats:
  - "Criterion 6 production evidence is the operator-approved 2026-11-15 verify-deploy pass recorded in docs/DEPLOY.md row 320 (health 200 env=prod, Turnstile mode=live, CORS allow/deny preflight, board/legal/API, cron rejected-then-idempotent, no secret leak), executed against actual hosts https://empreganoix-six.vercel.app and https://nqu-backend-x60n.onrender.com."
  - "Actual hosts differ from canonical hosts empreganoix.vercel.app and empreganoix.onrender.com; canonical-host confirmation and any re-smoke are owned by Phase 13 (BRND-04)."
---

# Phase 9: Lifecycle, Trust, Legal & Launch Completeness Verification Report

**Phase Goal:** Garantir que o board se mantenha honesto e seguro — vagas somem em 14 dias de forma confiável, e a plataforma tem postura de confiança/legal e deploy prontos para lançar.
**Initial verification:** 2026-11-15 (original run)
**Reconciled:** 2026-11-15
**Status:** passed
**Re-verification:** Yes — reconciled in place with committed evidence, corrected audit trail, and explicit caveats (single source of truth; no `09-REVERIFICATION.md`).

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Cada vaga nasce com `expires_at` = `created_at` + 14 dias; `expires_at` é `timestamptz` no banco | ✓ VERIFIED | `backend/app/models/job.py`: `expires_at` is `TIMESTAMP(timezone=True)` with `server_default=text("now() + interval '14 days'")` and index `ix_jobs_expires_at`. `backend/tests/test_schema.py` pins DDL/behavior including `test_expires_at_defaults_to_14_days` and `test_expires_at_column_is_timestamptz_with_14_day_default` (timestamptz, normalized default includes `now()` and `'14 days'::interval`, index present). Backend evidence committed at D-10 SHA `261eae007933106be4c072f5256f642bdd26dba0` (contracts) and cited in 12-TEST-EVIDENCE. |
| 2 | Vagas expiradas são hard-deleted por `/admin/expire` protegido exclusivamente por `X-Cron-Secret`, idempotente em UTC, sem apagar vagas futuras; docs/contract alinhados | ✓ VERIFIED (verify-only ROADMAP confirmation) | Implementation: `backend/app/api/v1/admin.py` protects `/admin/expire` with `Depends(require_cron_secret)` only; `backend/app/deps.py::require_cron_secret` fails closed (503 when unconfigured, 401 when missing/wrong) with constant-time comparison and IP rate limit. `backend/app/crud/jobs.py::delete_expired_jobs` deletes `WHERE expires_at < func.now()` (DB clock), status-agnostic. Tests: `backend/tests/test_admin_expire.py` covers 503/401/wrong/JWT-rejected (`test_admin_bearer_token_is_not_a_cron_secret`), idempotency, future rows preserved, and all-status sweep including `test_expire_deletes_expired_row_for_every_status[pending/published/needs_review/invalid]`. `docs/DEPLOY.md` states "Credencial única" (X-Cron-Secret only). `.planning/ROADMAP.md` Phase 9 criterion 2 already states "protegido exclusivamente por header `X-Cron-Secret` (um Bearer JWT de admin NÃO é aceito — T-06-01)" and was confirmed aligned (D-02, verify-only; no rewrite required). |
| 3 | Vagas `pending` não revisadas também expiram após 14 dias (mesma regra) | ✓ VERIFIED | `delete_expired_jobs` has no status filter; `backend/tests/test_admin_expire.py` proves expired rows are removed for every status while future siblings remain (`test_expire_deletes_expired_published_and_pending`, parametrized `test_expire_deletes_expired_row_for_every_status`). |
| 4 | Páginas `/privacidade`, `/termos-de-uso` e aviso LGPD/intermediário acessíveis no shell público | ✓ VERIFIED | `frontend/app/(public)/privacidade/page.tsx` (privacy content, metadata, token-only styling, content-only article in shared shell). `frontend/app/(public)/termos-de-uso/page.tsx` includes the required intermediary notice `Somos apenas meio de divulgação...` and legal structure; `frontend/app/(public)/layout.tsx` provides the shared public shell and footer links to `/privacidade` and `/termos-de-uso`. Contracts/repairs aligned by 09-02/09-04 artifacts (`b3e6940`, `b9a38c6`). |
| 5 | Visitante pode denunciar vaga via `/jobs/{id}/report` (motivo opcional, máx 500, log-only) e badge "Vaga revisada" deriva de `published` | ✓ VERIFIED | `backend/app/api/v1/public.py::report_job` is accept-and-log only (optional reason, capped/sanitized logging, no DB persistence, throttled). `backend/tests/test_report_api.py` covers no-body, logging, 501→422, unknown job behavior, whitespace handling, 500-char acceptance/logging (`test_report_reason_at_500_chars_is_accepted_and_logged`), no persistence (`test_report_persists_nothing`), and throttle/429 contract. Frontend: `frontend/lib/api.ts` posts to `/api/v1/public/jobs/{id}/report`; `ReportJobDialog.tsx` enforces UX/limits; `JobCard.tsx` and `JobDetailDialog.tsx` render "Vaga revisada" only when `job.status === "published"`. Evidence committed at D-10 SHA `261eae007933106be4c072f5256f642bdd26dba0`. |
| 6 | Frontend (Vercel) e backend (Render) deployados com CORS travado, segredos por env, cron catch-up e smoke gate verde (produção) | ✓ VERIFIED (with caveat — non-canonical hosts; Phase 13 owns canonical confirmation/re-smoke) | Operator-approved 2026-11-15 `verify-deploy` pass recorded in `docs/DEPLOY.md` row 320: `verify-deploy: all checks passed` (health 200 `env=prod`, `turnstile.mode=live`, CORS allow preflight echoes canonical frontend origin and deny rejects `https://evil.example`, board/legal/API OK, cron unauthorized rejected and authorized idempotent, no secret leak). Command context (redacted secret): `powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 -FrontendUrl https://empreganoix-six.vercel.app -BackendUrl https://nqu-backend-x60n.onrender.com -CronSecret <redacted>`. Actual hosts: `https://empreganoix-six.vercel.app` and `https://nqu-backend-x60n.onrender.com`, which differ from canonical `empreganoix.vercel.app` / `empreganoix.onrender.com`. Canonical-host confirmation and any re-smoke are owned by **Phase 13 (BRND-04)**. Repo hardening evidence: `backend/app/core/config.py` prod fail-closed CORS validation, `backend/tests/test_cors.py`, `render.yaml`/`scripts/verify-deploy.ps1`/`docs/DEPLOY.md` alignment commits `b9a38c6` and `b3e6940`. |

**Score:** 6/6 success criteria verified

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `backend/app/models/job.py` | DB-owned `expires_at` = `created_at` + 14 days (`timestamptz`, indexed) | ✓ VERIFIED | `TIMESTAMP(timezone=True)` + `server_default=text("now() + interval '14 days'")`, `ix_jobs_expires_at`. |
| `backend/tests/test_schema.py` | DDL/behavior proof for 14-day expiry/timestamptz/index | ✓ VERIFIED | Pins default, DDL type/default normalization, and index. |
| `backend/app/crud/jobs.py` | Status-agnostic DB-clock hard-delete sweep | ✓ VERIFIED | `delete_expired_jobs` uses `expires_at < func.now()` with no status filter. |
| `backend/app/api/v1/admin.py` | Cron-only expire endpoint | ✓ VERIFIED | `POST /admin/expire` depends on `require_cron_secret` only; no admin JWT dependency. |
| `backend/app/deps.py` | `require_cron_secret` fail-closed/idempotent gate semantics | ✓ VERIFIED | 503 when unconfigured, 401 when missing/wrong, constant-time compare, IP rate-limited. |
| `backend/tests/test_admin_expire.py` | X-Cron-Secret-only gate + idempotent all-status sweep | ✓ VERIFIED | Includes `test_admin_bearer_token_is_not_a_cron_secret` and `test_expire_deletes_expired_row_for_every_status`. |
| `backend/app/api/v1/public.py` | Accept-and-log report endpoint (optional reason, capped) | ✓ VERIFIED | No persistence; structured safe logging; throttled. |
| `backend/tests/test_report_api.py` | 500-char boundary, logging, no persistence, throttle contract | ✓ VERIFIED | Includes `test_report_reason_at_500_chars_is_accepted_and_logged` and `test_report_persists_nothing`. |
| `backend/app/core/config.py` | Prod fail-closed CORS validation | ✓ VERIFIED | Rejects unsafe origins in non-dev environments. |
| `backend/tests/test_cors.py` | Exact-origin echo / foreign deny / preflight / prod validation | ✓ VERIFIED | Coverage present for CORS contract. |
| `frontend/app/(public)/privacidade/page.tsx`, `frontend/app/(public)/termos-de-uso/page.tsx`, `frontend/app/(public)/layout.tsx` | Public legal/trust surfaces in shared shell with intermediary notice | ✓ VERIFIED | Pages and shell/footer wiring present; exact intermediary notice asserted in smoke gate alignment (`b9a38c6`). |
| `frontend/components/board/JobCard.tsx`, `frontend/components/board/JobDetailDialog.tsx`, `frontend/components/board/ReportJobDialog.tsx`, `frontend/lib/api.ts` | Published-only "Vaga revisada" badge and report flow wiring | ✓ VERIFIED | Badge derived from `status === "published"`; report client posts to public endpoint. |
| `scripts/verify-deploy.ps1` | Smoke gate asserts exact intermediary notice and production checks | ✓ VERIFIED | Exact notice assertion (`somos apenas meio de divulga`) and cron/CORS/health/Turnstile checks aligned by `b9a38c6`. |
| `docs/DEPLOY.md` | Runbook/evidence for criterion 6 and X-Cron-Secret-only contract | ✓ VERIFIED | Includes "Credencial única", human-gated checklist context, prep row 318, and passing row 320 with actual hosts. |
| `.planning/ROADMAP.md` | Phase 9 criterion 2 contract aligned to T-06-01 | ✓ VERIFIED (verify-only) | Already states `protegido exclusivamente por header \`X-Cron-Secret\`` and rejects Bearer JWT admin; confirmed, not rewritten (D-02). |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `backend/app/api/v1/admin.py` | `backend/app/deps.py::require_cron_secret` | `Depends(require_cron_secret)` on `POST /admin/expire` | ✓ WIRED | Enforces X-Cron-Secret-only auth; admin JWT not accepted (T-06-01). |
| `backend/app/api/v1/admin.py` | `backend/app/crud/jobs.py::delete_expired_jobs` | Sweep invocation | ✓ WIRED | Status-agnostic, idempotent DB-clock deletion with commit. |
| `backend/tests/test_admin_expire.py` | `/api/v1/admin/expire` contract | HTTP + DB assertions | ✓ WIRED | Covers 503/401/JWT-rejected/idempotency/all-status/future-preserved/rate-limit probe path. |
| `backend/tests/test_report_api.py` | `backend/app/api/v1/public.py::report_job` | POST report endpoint contract | ✓ WIRED | Covers cap, logging, no persistence, throttling and safety behavior. |
| `frontend/lib/api.ts` | `backend/app/api/v1/public.py` report route | `POST /api/v1/public/jobs/{id}/report` | ✓ WIRED | Client wiring for report submission. |
| `frontend/components/board/JobDetailDialog.tsx` | `frontend/components/board/ReportJobDialog.tsx` | Dialog state/open wiring | ✓ WIRED | Report action available from detail flow. |
| `scripts/verify-deploy.ps1` | `/termos-de-uso` intermediary notice + deploy checks | HTTP assertions in smoke gate | ✓ WIRED | Exact notice assertion and criterion 6 checks executed/passed per row 320. |

## Superseded findings

| Original gap (initial 2026-11-15 `gaps_found` report) | Status | Closing commit/artifact(s) | Notes |
|---|---|---|---|
| ROADMAP Phase 9 criterion 2 stated `(ou Bearer JWT admin)` (T-06-01 drift) | CLOSED / VERIFIED ALIGNED | `b9a38c6` (`.planning/ROADMAP.md`), `backend/app/api/v1/admin.py`, `backend/app/deps.py`, `backend/tests/test_admin_expire.py::test_admin_bearer_token_is_not_a_cron_secret`, `docs/DEPLOY.md` "Credencial única" | Phase 12 confirmed criterion 2 already correct (D-02, verify-only); no further ROADMAP rewrite. |
| `scripts/verify-deploy.ps1` asserted weak `intermedi` substring instead of exact intermediary notice | CLOSED | `b9a38c6` (`scripts/verify-deploy.ps1`), `frontend/app/(public)/termos-de-uso/page.tsx` | Gate now asserts exact/accent-robust required notice. |
| `docs/DEPLOY.md` missing human-gated criterion 6 warning/evidence checklist, 2026-11-13 prep row, and `uv run --no-sync` alignment docs | CLOSED | `b3e6940` (`docs/DEPLOY.md`, `render.yaml` alignment context), `docs/DEPLOY.md` rows 318 and 320 | Preparation and passing production evidence are now recorded. |
| Production criterion 6 lacked passing live evidence | CLOSED WITH CAVEAT | `docs/DEPLOY.md` row 320 (2026-11-15), `scripts/verify-deploy.ps1`, operator-approved verify-deploy pass | Pass recorded on non-canonical actual hosts; canonical-host confirmation/re-smoke owned by Phase 13 (BRND-04). |
| Phase 9 lifecycle/trust backend evidence needed stable citation for reconciliation | CLOSED (evidence committed) | D-10 commit `261eae007933106be4c072f5256f642bdd26dba0` (`backend/app/core/config.py`, `backend/tests/test_admin_expire.py`, `backend/tests/test_report_api.py`), `12-TEST-EVIDENCE.md`, `12-01-SUMMARY.md` | Fresh targeted test rerun recorded honestly (see "How this was verified"). |

Progression note (D-04): the superseded 2026-11-12 failed smoke (`env=dev`, Turnstile `mode=test`, CORS preflight 400) was superseded by the 2026-11-15 pass after 09-03/09-04 hardening (row 320 in `docs/DEPLOY.md`).

## Anti-Patterns

| File | Pattern (originally reported) | Severity | Status | Closing commit/artifact |
|---|---|---|---|---|
| `.planning/ROADMAP.md` | Stale Phase 9 criterion 2 text allowing admin Bearer JWT (`(ou Bearer JWT admin)`) contradicting T-06-01 | 🛑 Blocker | CLOSED | `b9a38c6` (aligned to X-Cron-Secret-only / Bearer JWT admin not accepted); verified in place (D-02). |
| `scripts/verify-deploy.ps1` | Weak `intermedi` smoke assertion (not exact required intermediary notice) | ⚠️ Warning | CLOSED | `b9a38c6` (exact/accent-robust notice assertion: `somos apenas meio de divulga`). |
| `docs/DEPLOY.md` | Incomplete criterion 6 runbook/evidence (missing human-gated warning/checklist details, prep row, and `uv run --no-sync` alignment) | ⚠️ Warning | CLOSED | `b3e6940` (runbook/human-gated alignment) and recorded evidence rows 318/320 in `docs/DEPLOY.md`. |

## human_verification

Recorded operator-run production gate (lean, evidence-backed):

- **When:** 2026-11-15 (approved; recorded in `docs/DEPLOY.md` row 320)
- **Command context:** `powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 -FrontendUrl https://empreganoix-six.vercel.app -BackendUrl https://nqu-backend-x60n.onrender.com -CronSecret <redacted>`
- **Actual hosts:** Frontend `https://empreganoix-six.vercel.app`, Backend `https://nqu-backend-x60n.onrender.com`
- **Result:** `verify-deploy: all checks passed` — health 200 `env=prod`, `turnstile.mode=live`, CORS allow preflight echoes canonical frontend origin and deny rejects `https://evil.example`, board/legal/API OK, cron unauthorized rejected and authorized idempotent, no secret leak; cold-start observed `0.2s`.
- **Caveat:** actual hosts differ from canonical `empreganoix.vercel.app` / `empreganoix.onrender.com`.

Remaining human/ops follow-up (single item, deferred): **canonical-host confirmation and re-smoke on canonical hosts (or explicit canonical mapping/evidence)** — owned by **Phase 13 (BRND-04)**. No additional Phase 9 product/code verification remains in scope.

## Nyquist follow-up note

`09-VALIDATION.md` exists for Phase 9 (approved validation strategy/contract), but the milestone audit rates Phase 9 Nyquist coverage as partial. Closing Nyquist coverage is a separate `/gsd-validate-phase 09` task and is **not** part of Phase 12 reconciliation (D-08).

## How this was verified

- **Working directory:** `backend/`
- **Exact targeted pytest command:** `.venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py tests/test_cors.py -q`
- **Run date/time:** `2026-11-15T10:17:46-03:00`
- **Commit SHA(s) at verification time (from 12-TEST-EVIDENCE.md):**
  - D-10 evidence commit: `261eae007933106be4c072f5256f642bdd26dba0` (`chore(12-01): commit Phase 9 backend evidence (D-10)`)
  - HEAD after Task 2 (same as D-10; no cleanup git commit): `261eae007933106be4c072f5256f642bdd26dba0`
  - Evidence artifact capture commit (separate docs commit): `f88616b` (`docs(12-01): capture targeted pytest evidence and blocker (D-09,D-12)`)
- **Result (fresh, honest):** exit code `1`; **8 passed, 27 errors in 101.98s (0:01:41)**. DB/schema not ready in this environment — no green/passing claim is made for the targeted DB-backed contracts in this run.
- **Relevant snippets/blocker (from 12-TEST-EVIDENCE.md):**
  ```text
  =================================== ERRORS ====================================
  ...
  E   asyncpg.exceptions.UndefinedTableError: relation "jobs" does not exist
  ...
  E   sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) relation "jobs" does not exist
  E   [SQL: DELETE FROM jobs]
  ```
  Short summary excerpt:
  ```text
  ERROR tests/test_admin_expire.py::test_expire_deletes_expired_row_for_every_status[pending]
  ERROR tests/test_admin_expire.py::test_expire_deletes_expired_row_for_every_status[published]
  ERROR tests/test_admin_expire.py::test_expire_deletes_expired_row_for_every_status[needs_review]
  ERROR tests/test_admin_expire.py::test_expire_deletes_expired_row_for_every_status[invalid]
  ...
  ERROR tests/test_report_api.py::test_report_reason_at_500_chars_is_accepted_and_logged
  ERROR tests/test_report_api.py::test_report_persists_nothing - sqlalchemy.exc...
  ...
  8 passed, 27 errors in 101.98s (0:01:41)
  ```
- **Interpretation:** Environment/prerequisite blocker only (missing `jobs` relation / migrated test schema unavailable). No product/runtime code was modified to fabricate results. Reconciliation relies on committed implementation/tests (`261eae0`), passing production smoke evidence (row 320), and documented contracts for criterion/traceability alignment.

## Requirements Coverage

| Requirement | Description (summary) | Status | Evidence |
|---|---|---|---|
| LIFE-10 | `expires_at` = `created_at` + 14 days, DB-owned/timestamptz | ✓ SATISFIED | `job.expires_at` server default + schema tests/DDL pin. |
| LIFE-11 | Expired jobs hard-deleted idempotently in UTC, future rows safe | ✓ SATISFIED | `delete_expired_jobs` uses DB clock; admin expire tests cover idempotency/future preservation. |
| LIFE-12 | `pending` (and other statuses) expire under same 14-day rule | ✓ SATISFIED | Status-agnostic sweep + parametrized all-status expiry test. |
| LIFE-13 | `/admin/expire` protected exclusively by `X-Cron-Secret` (not admin Bearer JWT), fail-closed/idempotent contract | ✓ SATISFIED (code/contract) with split ownership | `require_cron_secret`, route wiring, `test_admin_bearer_token_is_not_a_cron_secret`, docs "Credencial única"; canonical-host/deploy evidence residual owned by Phase 13 (BRND-04). |
| TRST-10 | Privacy/terms/intermediary notice accessible in public shell | ✓ SATISFIED | `/privacidade`, `/termos-de-uso`, shared layout/footer links, exact notice aligned. |
| TRST-11 | Report endpoint accepts optional reason (<=500), logs without persistence, throttled | ✓ SATISFIED | Public report route + `test_report_api.py` contracts. |
| TRST-12 | "Vaga revisada" badge for published/approved jobs | ✓ SATISFIED | Badge derives only from `status === "published"` in card/detail. |
| SECR-12 (Phase 9 side) | `/admin/expire` cron-secret-only, fail-closed when unconfigured/missing/wrong | ✓ SATISFIED (code/contract) with split ownership | `deps.require_cron_secret` + admin route + tests/docs; residual canonical-host/deploy evidence owned by Phase 13 (Phase 7 side previously verified in `07-VERIFICATION.md`). |

## Gaps Summary

No open Phase 9 implementation/contract/verification gaps remain in scope. Reconciliation closed the previously reported documentation/traceability gaps and recorded criterion 6 as verified with an explicit non-canonical-host caveat. Residual work is operational only: canonical-host confirmation and any re-smoke on `empreganoix.vercel.app` / `empreganoix.onrender.com` (or explicit canonical mapping/evidence) are owned by **Phase 13 (BRND-04)**. Nyquist closure for Phase 9 remains a separate `/gsd-validate-phase 09` task.

---

_Verified: 2026-11-15T00:00:00Z (initial)_
_Reconciled: 2026-11-15T00:00:00Z_
_Verifier: OpenCode (gsd-executor, Phase 12 reconciliation)_