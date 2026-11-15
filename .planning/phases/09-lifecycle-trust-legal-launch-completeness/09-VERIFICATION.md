---
phase: 09-lifecycle-trust-legal-launch-completeness
verified: 2026-11-15T00:00:00Z
status: gaps_found
score: 4/6 success criteria verified
gaps:
  - truth: "ROADMAP Phase 9 criterion 2 documents that /admin/expire accepts only X-Cron-Secret (Bearer JWT admin is not accepted, T-06-01)"
    status: failed
    reason: "Criterion 2 in .planning/ROADMAP.md still states '(ou Bearer JWT admin)' even though code/tests and other docs enforce/record X-Cron-Secret-only auth."
    artifacts:
      - path: ".planning/ROADMAP.md"
        issue: "Line 89 still contains 'protegido por `X-Cron-Secret` header (ou Bearer JWT admin)' instead of explicitly rejecting admin Bearer JWT per T-06-01."
    missing:
      - "Update .planning/ROADMAP.md Phase 9 criterion 2 to remove '(ou Bearer JWT admin)' and state that a Bearer JWT admin is NOT accepted (T-06-01), matching backend/tests/test_admin_expire.py::test_admin_bearer_token_is_not_a_cron_secret and .planning/REQUIREMENTS.md LIFE-13."
  - truth: "Production smoke gate asserts the exact intermediary notice on /termos-de-uso"
    status: failed
    reason: "scripts/verify-deploy.ps1 check 5 still asserts the weak substring 'intermedi' rather than the exact required phrase 'somos apenas meio de divulgação'."
    artifacts:
      - path: "scripts/verify-deploy.ps1"
        issue: "Contains `Assert ($terms.Body -imatch 'intermedi')` (around line 199) instead of asserting 'somos apenas meio de divulga' / the exact notice."
    missing:
      - "Replace the weak 'intermedi' assertion with an assertion for the exact required intermediary notice and update check comments/pass label accordingly."
  - truth: "Launch readiness runbook records criterion 6 as prepared but human-gated with required prod evidence and preparation log entry"
    status: failed
    reason: "docs/DEPLOY.md does not contain the claimed human-gate warning ('Critério 6 é human-gated') or the 2026-11-13 preparation row, and the start/cold-start text does not document 'uv run --no-sync' as claimed by 09-03."
    artifacts:
      - path: "docs/DEPLOY.md"
        issue: "Missing explicit human-gated criterion 6 block, missing '2026-11-13 | Preparação de deploy (Fase 9)' verification row, and missing 'uv run --no-sync' in start/cold-start documentation despite render.yaml using it."
    missing:
      - "Add the human-gated criterion 6 warning listing required env=prod, turnstile.mode=live/test_override evidence, and CORS allow/deny preflight evidence."
      - "Append the 2026-11-13 preparation row to the verification log stating artifacts prepared and deploy remains human."
      - "Document `uv run --no-sync` in the Render start command and cold-start notes to match render.yaml."
  - truth: "Frontend and backend are deployed with CORS locked to the frontend origin, secrets configured by env, and smoke gate green for production"
    status: failed
    reason: "Production go-live was not executed as part of this phase; prior production smoke (2026-11-12, per STATE/DEPLOY history) failed (env/dev Turnstile/CORS issues) and no new passing production evidence exists. This remains an explicit human-gated operational step."
    artifacts:
      - path: "render.yaml"
        issue: "Blueprint hardened (SCHEDULER_ENABLED, --no-sync) but not evidence of a successful live deploy."
      - path: "scripts/verify-deploy.ps1"
        issue: "Gate script exists but has not produced a passing production run for current artifacts; check 5 is also not tightened to exact notice."
    missing:
      - "Perform real deploy with correct env vars (ENV=prod, live Turnstile or documented test override, exact CORS_ORIGINS), run verify-deploy.ps1 against deployed hosts, and record passing evidence (including CORS allow/deny preflight and cron checks)."
human_verification:
  - test: "Run production smoke gate against deployed Vercel + Render"
    expected: "scripts/verify-deploy.ps1 reports all checks passed: health 200 with env=prod and turnstile.mode=live (or explicitly approved test_override), allowed CORS preflight echoes exact frontend origin, foreign-origin preflight denied, board/legal/API checks pass, cron unauthorized rejected and authorized idempotent."
    why_human: "Requires real deployed environments, secrets/env configuration, network reachability, and operator-run script execution; cannot be verified from repo state alone."
  - test: "Validate CORS behavior against live hosts from browser context"
    expected: "Browser requests from the production Vercel origin succeed; requests/preflights from foreign origins do not receive permissive Access-Control-Allow-Origin."
    why_human: "Actual cross-origin behavior depends on deployed Render env (CORS_ORIGINS) and live network/browser enforcement."
  - test: "Confirm cron catch-up works in deployed environment"
    expected: "POST /api/v1/admin/expire without/with wrong secret is rejected as configured; with correct X-Cron-Secret returns 200 and idempotent deleted counts; scheduler/catch-up behavior matches production settings."
    why_human: "Depends on deployed secrets, hosting runtime behavior, and operational scheduling."
---

# Phase 9: Lifecycle, Trust, Legal & Launch Completeness Verification Report

**Phase Goal:** Garantir que o board se mantenha honesto e seguro — vagas somem em 14 dias de forma confiável, e a plataforma tem postura de confiança/legal e deploy prontos para lançar.
**Verified:** 2026-11-15T00:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Cada vaga nasce com `expires_at` = `created_at` + 14 dias; `expires_at` é `timestamptz` no banco | ✓ VERIFIED | `backend/app/models/job.py` defines `expires_at` as `TIMESTAMP(timezone=True)` with `server_default=text("now() + interval '14 days'")` and index `ix_jobs_expires_at`; `backend/tests/test_schema.py` includes `test_expires_at_defaults_to_14_days` and DDL pin `test_expires_at_column_is_timestamptz_with_14_day_default` asserting timestamptz, normalized default contains `now()` + `'14 days'::interval`, and index exists. |
| 2 | Vagas expiradas são hard-deleted por `/admin/expire` protegido exclusivamente por `X-Cron-Secret`, idempotente em UTC, sem apagar vagas futuras; docs alinhadas | ✗ FAILED | Code/tests are aligned: `backend/app/api/v1/admin.py` protects endpoint with `require_cron_secret`; `backend/app/crud/jobs.py::delete_expired_jobs` deletes `WHERE expires_at < func.now()` (DB clock) and is status-agnostic; `backend/tests/test_admin_expire.py` proves 503/401/missing/wrong/JWT-rejected, idempotency, future rows preserved, and all statuses swept. `docs/DEPLOY.md` states credencial única / JWT not authorized and `.planning/REQUIREMENTS.md` LIFE-13 updated. **Gap:** `.planning/ROADMAP.md` Phase 9 criterion 2 still says `(ou Bearer JWT admin)` (line 89), contradicting T-06-01. |
| 3 | Vagas `pending` não revisadas também expiram após 14 dias (mesma regra) | ✓ VERIFIED | `delete_expired_jobs` has no status filter; `test_expire_deletes_expired_published_and_pending` and parametrized `test_expire_deletes_expired_row_for_every_status` cover `pending/published/needs_review/invalid` while preserving future siblings. |
| 4 | Páginas `/privacidade`, `/termos-de-uso` e aviso LGPD/intermediário acessíveis no shell público | ✓ VERIFIED | `frontend/app/(public)/privacidade/page.tsx`: 1 `<h1>`, 13 `<h2>`, metadata export, token-only classes, content-only article in shared layout, LGPD/contact text present. `frontend/app/(public)/termos-de-uso/page.tsx`: 1 `<h1>`, 10 `<h2>`, metadata export, exact notice `Somos apenas meio de divulgação de vagas...` present (after section 1 and in footer note), next/link to privacy. `frontend/app/(public)/layout.tsx` provides single shell and footer links to both `/privacidade` and `/termos-de-uso`. |
| 5 | Visitante pode denunciar vaga via `/jobs/{id}/report` (motivo opcional, máx 500, log-only) e badge "Vaga revisada" deriva de `published` | ✓ VERIFIED | `backend/app/api/v1/public.py::report_job` logs via `_log_safe` (500 cap, whitespace collapsed), no DB persistence, 5/min rate limit; `backend/tests/test_report_api.py` covers no-body, reason logging, 501→422, unknown job ok, whitespace-only, 500-char accepted/logged, `to_regclass('public.reports') is None`, 6th request 429. Frontend: `frontend/lib/api.ts` posts to `/api/v1/public/jobs/{id}/report`; `ReportJobDialog.tsx` has `role="status"`, `role="alert"`, `maxLength={MAX_REASON}` (500); `JobCard.tsx` and `JobDetailDialog.tsx` render badge only when `job.status === "published"` with text `Vaga revisada`. |
| 6 | Frontend (Vercel) e backend (Render) deployados com CORS travado, segredos por env, cron catch-up e smoke gate verde | ✗ FAILED | Repo prep exists but goal not achieved/end-to-end proven: `backend/app/core/config.py` adds prod fail-closed `_validate_cors_origins`; `backend/tests/test_cors.py` pins exact-origin echo, foreign-origin denial, report preflight, and unsafe prod origins rejected; `render.yaml` sets `SCHEDULER_ENABLED="true"` and `uv run --no-sync` start command. **Gaps:** `scripts/verify-deploy.ps1` still checks weak `intermedi` substring (not exact notice); `docs/DEPLOY.md` lacks claimed human-gated warning/2026-11-13 prep row/`uv run --no-sync` documentation; no passing production deploy/smoke evidence (prior 2026-11-12 smoke failed per project state/history) — production verification remains human-gated. |

**Score:** 4/6 success criteria verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `backend/tests/test_schema.py` | DDL-level expires_at 14-day/timestamptz/index proof | ✓ VERIFIED | Contains `test_expires_at_column_is_timestamptz_with_14_day_default`; asserts `timestamp with time zone`, normalized default with `now()` and `'14 days'::interval`, and `ix_jobs_expires_at`. |
| `backend/tests/test_admin_expire.py` | All-status sweep + idempotency + X-Cron-Secret-only gate | ✓ VERIFIED | Parametrized `test_expire_deletes_expired_row_for_every_status` over all 4 statuses; `test_expire_is_idempotent`; `test_admin_bearer_token_is_not_a_cron_secret` asserts 401. |
| `backend/tests/test_report_api.py` | 500-char boundary, no persistence, throttling contract | ✓ VERIFIED | `test_report_reason_at_500_chars_is_accepted_and_logged`; `test_report_persists_nothing` checks `to_regclass('public.reports') is None`; existing 501→422 and 429 cases present. |
| `backend/app/core/config.py` | Prod fail-closed CORS validator | ✓ VERIFIED | `_validate_cors_origins` rejects empty/wildcard/trailing-slash/scheme-less origins outside dev. |
| `backend/tests/test_cors.py` | Exact-origin/foreign/preflight/prod-validation tests | ✓ VERIFIED | 6 tests present covering echo, deny, report preflight, unsafe origins rejected, spaces stripped, dev default. |
| `backend/app/models/job.py` | `expires_at` DB-owned 14-day default | ✓ VERIFIED | `TIMESTAMP(timezone=True)` + `server_default=text("now() + interval '14 days'")`. |
| `backend/app/crud/jobs.py` | Status-agnostic DB-clock sweep | ✓ VERIFIED | `delete_expired_jobs` uses `expires_at < func.now()` with no status filter. |
| `backend/app/api/v1/admin.py` | Cron-only expire endpoint | ✓ VERIFIED | Depends on `require_cron_secret`; no admin JWT auth. |
| `backend/app/api/v1/public.py` | Accept-and-log report endpoint with cap/throttle | ✓ VERIFIED | Optional reason, `_log_safe` truncation, no persistence, 5/min limit, no enumeration oracle behavior. |
| `frontend/app/(public)/privacidade/page.tsx` | 13-section privacy policy in shared shell | ✓ VERIFIED | 1 h1, 13 h2, metadata, token classes, no nested shell landmarks. |
| `frontend/app/(public)/termos-de-uso/page.tsx` | 10-section terms with exact intermediary notice | ✓ VERIFIED | 1 h1, 10 h2, metadata, required notice present, next/link privacy link. |
| `frontend/app/(public)/layout.tsx` | Footer links to both legal pages | ✓ VERIFIED | Separate `Privacidade` and `Termos de Uso` links present. |
| `frontend/components/board/JobCard.tsx` | Published-only "Vaga revisada" badge | ✓ VERIFIED | `status === "published"` gate and badge text present. |
| `frontend/components/board/JobDetailDialog.tsx` | Published-only badge + report dialog wiring | ✓ VERIFIED | Badge gate present; renders `ReportJobDialog`; "Reportar vaga" button wired. |
| `frontend/components/board/ReportJobDialog.tsx` | Accessible report UX/state handling | ✓ VERIFIED | `idle/submitting/success/error`, `role="status"`, `role="alert"`, `maxLength={MAX_REASON}`. |
| `frontend/lib/api.ts` | Report client posts to public report endpoint | ✓ VERIFIED | `reportJob` posts to `/api/v1/public/jobs/{id}/report`. |
| `render.yaml` | Scheduler knob and no-sync boot command | ✓ VERIFIED | `SCHEDULER_ENABLED` declared; start command uses `uv run --no-sync` for alembic and uvicorn. |
| `scripts/verify-deploy.ps1` | Exact intermediary notice smoke assertion | ✗ STUB/INCOMPLETE | Still asserts weak `imatch 'intermedi'`; not tightened to exact required notice. |
| `docs/DEPLOY.md` | Runbook reflects T-06-01, CORS/no-sync hardening, human-gated criterion 6 | ⚠️ PARTIAL | Contains "Credencial única" note for cron secret; lacks claimed human-gated criterion 6 warning, 2026-11-13 prep row, and `uv run --no-sync` documentation. |
| `.planning/ROADMAP.md` | Phase 9 criterion 2 aligned to T-06-01 | ✗ STUB/INCOMPLETE | Criterion 2 still states `(ou Bearer JWT admin)`; not aligned with enforced behavior. |
| `.planning/REQUIREMENTS.md` | LIFE-13 aligned to T-06-01 | ✓ VERIFIED | States endpoint accepts only `X-Cron-Secret` and Bearer JWT admin is not accepted. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `backend/tests/test_schema.py` | `backend/app/models/job.py` DDL contract | `information_schema.columns` / `pg_indexes` assertions | ✓ WIRED | Test pins timestamptz default/index matching model/migration intent. |
| `backend/tests/test_admin_expire.py` | `backend/app/crud/jobs.py::delete_expired_jobs` | `POST /api/v1/admin/expire` | ✓ WIRED | Route invokes CRUD sweep; tests validate behavior across statuses and idempotency. |
| `backend/tests/test_report_api.py` | `backend/app/api/v1/public.py::report_job` | POST report endpoint contract | ✓ WIRED | Exercises logging, cap, throttling, and no-persistence behavior. |
| `backend/app/core/config.py` | `backend/app/main.py` CORS setup | `settings.cors_origins_list` consumed by middleware (validated at boot) | ✓ WIRED | Validator constrains production origin values before runtime CORS use. |
| `backend/tests/test_cors.py` | `backend/app/main.py` CORSMiddleware | HTTP origin/preflight requests | ✓ WIRED | Tests assert echo/deny/preflight behavior against app. |
| `render.yaml` | `backend/app/core/config.py` / runtime | `SCHEDULER_ENABLED` env + `uv run --no-sync` start command | ✓ WIRED | Blueprint declares knob and boot behavior used by app/runtime. |
| `frontend/app/(public)/privacidade/page.tsx`, `termos-de-uso/page.tsx` | `frontend/app/(public)/layout.tsx` | Route group shared shell/footer | ✓ WIRED | Pages render content-only articles; layout owns header/main/footer and links. |
| `frontend/components/board/JobDetailDialog.tsx` | `frontend/components/board/ReportJobDialog.tsx` | "Reportar vaga" button opens dialog | ✓ WIRED | Dialog imported/rendered and controlled by local state. |
| `frontend/lib/api.ts` | `backend/app/api/v1/public.py` report route | `POST /api/v1/public/jobs/{id}/report` | ✓ WIRED | Client function targets public report endpoint. |
| `scripts/verify-deploy.ps1` | `frontend/app/(public)/termos-de-uso/page.tsx` notice | Smoke check 5 assertion | ✗ NOT_WIRED (to exact contract) | Gate checks generic `intermedi` instead of exact notice added in 09-02. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `backend/app/api/v1/admin.py` expire endpoint | `deleted` count | `app.crud.jobs.delete_expired_jobs` DB delete result (`expires_at < func.now()`) | Yes | ✓ FLOWING |
| `backend/app/api/v1/public.py` report endpoint | report reason log field | Request body `ReportRequest.reason` -> `_log_safe` -> structured log | Yes (log-only by design) | ✓ FLOWING |
| `frontend/app/(public)/termos-de-uso/page.tsx` | intermediary notice text | Static authored JSX content | Yes (static legal content) | ✓ FLOWING |
| `frontend/components/board/JobDetailDialog.tsx` | "Vaga revisada" badge | `job.status === "published"` prop condition | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

Step 7b: SKIPPED for runtime API/DB behavior (no running backend/app server started; would require DB/env/services and side-effectful or environment-dependent checks). Evidence is based on static code inspection, schema/model alignment, and test definitions present in repo.

### Requirements Coverage

| Requirement | Source Plan | Description (summary) | Status | Evidence |
| --- | --- | --- | --- | --- |
| LIFE-10 | 09-01 | `expires_at` = `created_at` + 14 days, DB-owned/timestamptz | ✓ SATISFIED | `job.expires_at` server default and DDL/index pin test in `backend/tests/test_schema.py`; model uses `TIMESTAMP(timezone=True)`. |
| LIFE-11 | 09-01 | Expired jobs hard-deleted idempotently in UTC, future rows safe | ✓ SATISFIED | `delete_expired_jobs` uses DB clock; expire tests prove idempotency and future-row preservation. |
| LIFE-12 | 09-01 | `pending` (and other statuses) expire under same 14-day rule | ✓ SATISFIED | Status-agnostic delete + parametrized all-status expiry test. |
| TRST-10 | 09-02 | Privacy/terms/intermediary notice accessible | ✓ SATISFIED | `/privacidade` and `/termos-de-uso` restructured in public shell with required notice and footer links. |
| TRST-11 | 09-01 | Report endpoint accepts optional reason (<=500), logs without persistence | ✓ SATISFIED | Public report route + `test_report_api.py` (cap, logging, no `reports` table, throttling). |
| TRST-12 | 09-02 | "Vaga revisada" badge for published/approved jobs | ✓ SATISFIED | Badge rendered only when `job.status === "published"` in card/detail; report dialog wiring intact. |

**Orphaned requirements for Phase 9:** None found (all phase-mapped in-scope requirement IDs appear in plan frontmatter: 09-01 covers LIFE-10/11/12,TRST-11; 09-02 covers TRST-10,TRST-12).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `.planning/ROADMAP.md` | 89 | Stale contract text (`(ou Bearer JWT admin)`) contradicts T-06-01 | 🛑 Blocker | Misleading operational/security guidance; phase criterion 2 documentation not actually aligned. |
| `scripts/verify-deploy.ps1` | 199 | Weak legal notice assertion (`imatch 'intermedi'`) | ⚠️ Warning | Smoke gate can pass without exact required intermediary phrase, weakening launch evidence. |
| `docs/DEPLOY.md` | n/a | Missing claimed human-gated criterion 6 prep notes/row and `uv run --no-sync` docs | ⚠️ Warning | Launch readiness/runbook claims from 09-03 are not fully evidenced in docs. |

### Human Verification Required

### 1. Production Deploy and Smoke Gate

**Test:** Deploy backend/frontend with production env vars/secrets and run `scripts/verify-deploy.ps1` against deployed hosts (once script/doc gaps are addressed as needed).
**Expected:** All checks pass, including `env=prod`, `turnstile.mode=live` (or approved documented test override), exact-origin CORS preflight allowed, foreign-origin preflight denied, cron unauthorized rejected and authorized idempotent.
**Why human:** Requires real Render/Vercel environments, secret management, DNS/network, and operator execution.

### 2. Live CORS and Turnstile Behavior

**Test:** Exercise board/report/reveal/login flows from the production frontend origin and attempt cross-origin/preflight requests from a foreign origin.
**Expected:** Legitimate frontend origin works; foreign origins denied; Turnstile live validation behaves correctly.
**Why human:** Depends on deployed configuration and third-party/browser behavior.

### 3. Cron/Scheduler Operational Behavior

**Test:** Verify scheduled and manual catch-up expiry in production (or production-like deployed host) using `X-Cron-Secret`.
**Expected:** Manual endpoint idempotent and secret-gated; scheduler/catch-up operate without deleting future rows.
**Why human:** Runtime scheduling and hosting lifecycle (sleep/wake) cannot be proven from repository inspection.

### Gaps Summary

Phase 9's core lifecycle/trust/legal implementations are largely present and well-covered in code and tests (14-day DB-owned expiry, status-agnostic/idempotent sweep with cron-secret-only protection in implementation, log-only capped report flow, and legal/trust UI surfaces). However, the phase goal is **not fully achieved** as stated: ROADMAP criterion 2 documentation remains stale (still permits admin Bearer JWT in text), launch-readiness artifacts claimed in 09-03 are incomplete (`verify-deploy.ps1` not tightened to exact notice; `docs/DEPLOY.md` missing human-gated/runbook updates), and criterion 6's production deployment/smoke success remains human-gated with no passing live evidence. Close the documented/artifact gaps and complete a passing production smoke gate to satisfy the full phase outcome.

---

_Verified: 2026-11-15T00:00:00Z_
_Verifier: OpenCode (gsd-verifier)_