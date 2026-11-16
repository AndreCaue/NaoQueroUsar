---
phase: 18
slug: testes-documentacao-e-fechamento-de-gaps-v11
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-16
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-asyncio (auto) |
| **Config file** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_social_publish_pipeline.py tests/test_social_idempotency.py tests/test_facebook_publisher.py` (targeted offline/social subset; adjust per task) |
| **Full suite command** | `cd backend; .\.venv\Scripts\python.exe -m pytest -q` (DB-backed subsets require migrated `TEST_DATABASE_URL`/`DATABASE_URL`) |
| **Estimated runtime** | ~30-180 seconds (targeted vs broader/DB-backed; environment-dependent) |

---

## Sampling Rate

- **After every task commit:** Run the smallest relevant targeted subset from `backend/` (unit/offline first; DB-backed only when migrated test DB is ready).
- **After every plan wave:** Re-run all tests/artifact checks claimed as evidence in that wave; record skips/blockers explicitly.
- **Before `/gsd-verify-work`:** All claimed automated checks green, or explicitly documented as env-blocked/manual with evidence/handoff.
- **Max feedback latency:** 180 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-TBD-01 | TBD | TBD | TEST-01 | V5/V6 | Generation/classification/backoff logic runs offline with mocked LLM/HTTP; no secrets/tokens leaked | unit | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_social_post_generation.py tests/test_facebook_publisher.py tests/test_social_retry_policy.py tests/test_social_publish_pipeline.py` | ✅ (review/extend) | ⬜ pending |
| 18-TBD-02 | TBD | TBD | TEST-02 | V2/V4/V6 | OAuth/publication flows use Graph API mocks only; admin/cron protections and token handling unchanged; no real external calls | integration (ASGI/mocked HTTP) | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_facebook_publisher.py tests/test_meta_oauth_flow.py tests/test_meta_oauth_security.py tests/test_meta_oauth_validation.py tests/test_integrations_api.py` | ✅ (verify/gap-fill) | ⬜ pending |
| 18-TBD-03 | TBD | TBD | TEST-03 | V4/Integrity | Worker claim/publish/idempotency prevent duplicates under concurrency/retry (`SKIP LOCKED`, guards/constraints); cron auth fail-closed preserved | integration/concurrency | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_social_worker_claim.py tests/test_social_idempotency.py tests/test_social_publish_pipeline.py` | ✅ (may need migrated DB / stronger case) | ⬜ pending |
| 18-TBD-04 | TBD | TBD | TEST-04 | V2/V4/V6 | Manual Meta dev-mode roteiro documents safe, secret-free verification steps and objective criteria | manual | N/A (documented checklist/roteiro review) | ❌ W0 | ⬜ pending |
| 18-TBD-05 | TBD | TBD | DOC-01 | V2/V6 | Operational docs/env examples align (Meta setup, envs, Render cron, App Review/Live), preserve T-06-01 and backend-only secrets | manual/static | `git diff -- backend/.env.example frontend/.env.example docs/* scripts/verify-deploy.ps1` + checklist review | ❌ W0 (updates/additions) | ⬜ pending |
| 18-TBD-06 | TBD | TBD | AUD-01 | V5 | EXTR-10/11/12 closed/validated or partial+handoff with verifiable evidence; minimal fixes only if behavior gap proven | mixed | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_extractor.py tests/test_extract_api.py tests/test_extraction_core.py -k "chunk or contact or fallback"` (adjust to actual coverage) + code/audit matrix | ✅/❓ | ⬜ pending |
| 18-TBD-07 | TBD | TBD | AUD-02 | V4/V5 | PUBL-10..14 evidence respects gated contact reveal and contact-free public payloads/contracts | mixed | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_public_api.py tests/test_reveal_api.py tests/test_report_api.py` + FE inspection/handoff | ✅ (DB/human gaps possible) | ⬜ pending |
| 18-TBD-08 | TBD | TBD | AUD-03 | V5 | SRCH-10..12 behavior/evidence reconciled (query/filter/sort contracts) with traceable artifacts | mixed | `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_public_search.py` + frontend query-state inspection | ✅/❓ | ⬜ pending |
| 18-TBD-09 | TBD | TBD | AUD-04 | N/A | UIUX-10..12 validated via static/manual evidence or code fixes where gaps are real; handoffs explicit if browser/human-only | manual/static | Static review of `frontend/app/(public)/*`, styles/tokens/components + contrast/placement checklist (optional FE tests if added) | ❓ | ⬜ pending |
| 18-TBD-10 | TBD | TBD | AUD-05 | V2/V4 | `11-VERIFICATION.md` backfilled in Phase 11, 07/08 caveats reconciled, DB/human/canonical handoffs recorded with objective criteria; traceability/status updated honestly | manual/artifact | `Test-Path .planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-VERIFICATION.md`; review diffs/status in planning artifacts and evidence docs | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-VERIFICATION.md` — backfill consolidating Phase 11 evidence (D-03, AUD-05)
- [ ] Reproducible DB test setup artifact(s): e.g. `backend/scripts/setup-test-db.ps1` and/or `docs/TESTING.md`/DEPLOY section with `TEST_DATABASE_URL` + `alembic upgrade head` + pytest commands (D-02, AUD-05)
- [ ] Manual Meta dev-mode roteiro/checklist for TEST-04 (no real calls required in CI; live execution may be handoff)
- [ ] Operational Meta/App Review/Live/cron/env alignment doc updates for DOC-01 (including `.env.example` alignment)
- [ ] Evidence matrix/checklist artifacts for EXTR/PUBL/SRCH/UIUX and 07/08 caveat reconciliation (AUD-01..05)
- [ ] Targeted test additions/adjustments as gaps are proven (e.g. stronger `SKIP LOCKED`/idempotency concurrency case, explicit generation/classification/backoff assertions) — only if missing

*Existing infrastructure partially covers TEST-01..03 and audit verification; Wave 0 must close evidence/backfill/DB-setup gaps.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Meta app/Page setup, OAuth connect flow, and publish behavior in real dev-mode environment | TEST-04, DOC-01 (operational validation) | Requires real Meta app/Page/credentials/runtime not available/allowed in CI; D-02/D-04 permit handoff | Follow created roteiro: configure env/Meta app, run OAuth/connect, trigger draft/publish path, capture screenshots/log-safe evidence, record pass/fail per checklist |
| Render cron/worker execution and canonical-host smoke in deployed environment | DOC-01, AUD-05 | Requires provisioned/runtime infra and secrets | Use `docs/DEPLOY.md` and `scripts/verify-deploy.ps1` checklist/commands; record outcomes, blockers, and objective criteria in handoff artifact |
| Human/browser UX checks for 07/08 caveats and UIUX-10..12 where not automatable | AUD-04, AUD-05 | Visual/interaction/contrast/placement and cross-browser behavior need human confirmation | Execute checklist on target viewports/browsers; capture evidence (screenshots/notes) and mark closed vs partial handoff |
| DB-backed suite execution if migrated test DB is unavailable in-session/CI | TEST-03, AUD-05 | Depends on reachable Postgres and migrations applied | Run documented setup (`TEST_DATABASE_URL`, `alembic upgrade head`), then DB-backed pytest subsets; if blocked, produce handoff with commands, env needs, and expected results |

*Some automated coverage exists; items above remain manual or environment-gated.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
