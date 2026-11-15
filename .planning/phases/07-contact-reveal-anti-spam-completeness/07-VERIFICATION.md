---
phase: 07-contact-reveal-anti-spam-completeness
verified: 2026-11-15T03:10:00Z
status: gaps_found
score: 2/3 requirements fully evidenced (SECR-12 split/deferred by design)
gaps:
  - truth: "DB-backed reveal endpoint evidence (test_reveal_api.py) can be re-run and recorded as green in this environment"
    status: failed
    reason: "Targeted DB-backed suite could not execute because the configured test database/migrations were not ready (`relation \"jobs\" does not exist` during test fixture setup). Offline/unit evidence for Turnstile and rate limiting passed."
    artifacts:
      - path: "backend/tests/test_reveal_api.py"
        issue: "10 setup errors in this environment: `sqlalchemy.exc.ProgrammingError ... relation \"jobs\" does not exist` while `tests/conftest.py` executes `DELETE FROM jobs`."
    missing:
      - "Run `cd backend; .\\.venv\\Scripts\\python.exe -m pytest tests/test_reveal_api.py -q` against a migrated TEST_DATABASE_URL/DATABASE_URL (jobs table present) and record passing results."
      - "Optional: perform live/browser smoke for reveal flow with real Turnstile widget/token in a configured environment (TURNSTILE_LIVE or manual UI check)."
human_verification:
  - test: "Execute reveal flow in browser against a running backend+frontend with Turnstile configured"
    expected: "Published job reveals contact only after valid Turnstile token; repeated attempts from same IP hit pt-BR 429 with Retry-After; invalid/expired token returns 403 with fail-closed copy"
    why_human: "Interactive widget/token lifecycle and end-to-end browser behavior are not proven by static inspection; DB-backed API suite was environment-blocked here."
requirements:
  - id: SECR-10
    status: verified_with_caveat
    evidence: "Config/wiring present (`backend/app/core/config.py` Turnstile fail-closed validation and mode derivation, `frontend/app/admin/paste/ExtractForm.tsx` widget wiring). Phase 7 summaries document anti-spam completeness. Operational caveat documented: site key is build-time inlined."
  - id: SECR-11
    status: verified
    evidence: "Offline targeted suites passed (`tests/test_turnstile_service.py`, `tests/test_ratelimit.py`); code paths show server-side Siteverify + endpoint-keyed per-IP limiter + pt-BR 429/Retry-After; DB-backed reveal endpoint suite blocked by environment."
  - id: SECR-12
    status: partial_split
    evidence: "Phase 7-side anti-spam/Turnstile evidence documented here. `/admin/expire` X-Cron-Secret-only contract reconciliation and Phase 9-side evidence are not claimed complete in Phase 11; Phase 12 owns /admin/expire contract reconciliation."
---

# Phase 7: Contact Reveal & Anti-Spam Completeness Verification Report

**Phase Goal:** Um visitante revela o contato de uma vaga publicada passando por verificação anti-bot real, sem que o contato vaze antes disso; um scraper não consegue varrer contatos em massa.
**Verified:** 2026-11-15T03:10:00Z
**Status:** gaps_found
**Re-verification:** No — initial Phase 11 backfill verification

## Goal Achievement

### Observable Truths / Requirement Outcomes

| # | Truth / Outcome | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Reveal/admin anti-spam controls are implemented with server-side Siteverify, fail-closed behavior, and per-IP rate limiting | ✓ VERIFIED (offline + code evidence) | `backend/app/services/turnstile.py` (fail-closed `TurnstileResult`, action binding, no operational exceptions), `backend/app/core/ratelimit.py` (`SafeLimiter`, `key_style="endpoint"`, pt-BR 429 + `Retry-After`), `backend/app/core/client_ip.py` via `resolve_client_ip` usage, `backend/app/api/v1/public.py::reveal_contact` (rate limit -> lookup -> Siteverify -> 403/200). Targeted tests: `tests/test_turnstile_service.py` 23 passed, `tests/test_ratelimit.py` 12 passed. |
| 2 | SECR-10 Turnstile key/anti-spam wiring is evidenced with explicit operational rebuild caveat | ✓ VERIFIED (with caveat) | `backend/app/core/config.py` defines/validates `TURNSTILE_SECRET_KEY`, `TURNSTILE_SITE_KEY`, fail-closed prod behavior, `turnstile_mode`, and test-key handling. `frontend/app/admin/paste/ExtractForm.tsx` reads `process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY` and renders `<Turnstile ... action="login" ... />`. **Operational caveat:** `NEXT_PUBLIC_TURNSTILE_SITE_KEY` is inlined in the frontend bundle at build time; changing the Cloudflare Turnstile site key requires a frontend rebuild/redeploy. |
| 3 | SECR-12 is fully closed in this phase | ✗ NOT CLAIMED / SPLIT | Phase 7-side anti-spam/Turnstile evidence is documented in this report. `/admin/expire` X-Cron-Secret-only contract reconciliation and Phase 9-side evidence are owned by **Phase 12** (`Phase 12 owns /admin/expire contract reconciliation`). This artifact does **not** claim full SECR-12 closure. |

**Score:** 2/3 requirements fully evidenced within Phase 11 scope (SECR-12 intentionally split)

## Targeted Test Evidence (recorded)

Executed from `backend/` on 2026-11-15 in this environment.

| Command | Result | Notes |
| --- | --- | --- |
| `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_turnstile_service.py -q` | **PASS** (23 passed, 0 failed) | Offline Siteverify/service behavior evidence (fail-closed paths, action binding behavior covered by suite). |
| `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_ratelimit.py -q` | **PASS** (12 passed, 0 failed) | Limiter behavior, keying/handler/429 semantics evidence at unit/integration-mocked level. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_turnstile_live.py -q` | **SKIPPED** (3 skipped, 0 failed) | Live Siteverify integration is opt-in (`TURNSTILE_LIVE=1`); not executed live in this run, so no real Cloudflare validation claimed. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_reveal_api.py -q` | **ENVIRONMENT BLOCKED** (10 errors during setup, exit code 1) | DB-backed endpoint suite failed before tests ran: `sqlalchemy.exc.ProgrammingError ... relation "jobs" does not exist` raised from `tests/conftest.py` fixture `db_session` (`DELETE FROM jobs`). Indicates missing/misconfigured/mismigrated `TEST_DATABASE_URL`/`DATABASE_URL` for this environment; not treated as a fabricated pass. |

## Required Artifacts / Evidence Anchors

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `backend/app/core/config.py` | Turnstile config/knobs, fail-closed validation, mode derivation | ✓ VERIFIED | `TURNSTILE_SECRET_KEY`, `TURNSTILE_SITE_KEY`, `TURNSTILE_TIMEOUT_SECONDS`, `REVEAL_RATE_LIMIT="10/minute"`, `LOGIN_RATE_LIMIT="5/minute"`; prod rejects missing/test keys unless explicit escape hatch; `turnstile_mode` returns `live/test/disabled`. |
| `backend/app/core/ratelimit.py` | Per-IP endpoint-keyed limiter and pt-BR 429 handling | ✓ VERIFIED | Uses `resolve_client_ip`, `default_limits=[]`, in-memory storage, `key_style="endpoint"`, `RATE_LIMIT_MESSAGE` pt-BR, `Retry-After` header in handler; `SafeLimiter` avoids 500 on missing response injection target. |
| `backend/app/services/turnstile.py` | Server-side Siteverify, fail-closed, action binding | ✓ VERIFIED | Empty token/network/5xx/non-JSON => fail closed (`internal-error`/`missing-input-response`); `expected_action` mismatch => `action-mismatch` (enforced per verifier config); shared pt-BR error mapping helper. |
| `backend/app/api/v1/public.py` | Reveal endpoint contract/order | ✓ VERIFIED (code) | `POST /jobs/{id}/reveal-contact` applies limiter -> `get_published` lookup (404 if missing/expired) -> `verifier.verify(..., expected_action="reveal")` -> 403 on failure -> 200 `ContactRevealResponse`; `get_public_job`/list remain contact-free. |
| `frontend/app/admin/paste/ExtractForm.tsx` | Turnstile site key wiring and widget behavior cues | ✓ VERIFIED (code) | Reads `process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY` (prod requires env), renders `<Turnstile ... action="login" theme="dark" appearance="always" ...>` and remount/reset handling by React key. |
| `backend/tests/test_turnstile_service.py` | Offline service verification | ✓ VERIFIED (executed) | 23 passed. |
| `backend/tests/test_ratelimit.py` | Offline limiter verification | ✓ VERIFIED (executed) | 12 passed. |
| `backend/tests/test_turnstile_live.py` | Optional live Siteverify proof | ⚠️ SKIPPED (opt-in) | 3 skipped (TURNSTILE_LIVE not set). |
| `backend/tests/test_reveal_api.py` | DB-backed reveal contract proof | ✗ BLOCKED (environment) | 10 setup errors: relation `jobs` missing in configured DB. |

## Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `backend/app/api/v1/public.py::reveal_contact` | `backend/app/services/turnstile.py` | `Depends(get_turnstile_verifier)` + `verifier.verify(... expected_action="reveal")` | ✓ WIRED | 403 on verify failure using `turnstile_error_detail`; no degraded 200 path. |
| `backend/app/api/v1/public.py::reveal_contact` | `backend/app/core/ratelimit.py` | `@limiter.limit(reveal_limit)` + endpoint-keyed limiter | ✓ WIRED | Reveal route rate-limited per resolved IP/route before contact release. |
| `backend/app/services/turnstile.py` / verifier DI | `backend/app/core/config.py` | `effective_turnstile_secret`, timeout, mode/action-enforcement | ✓ WIRED | Verifier constructed from settings; mode influences action enforcement behavior. |
| `frontend/app/admin/paste/ExtractForm.tsx` | Turnstile config/build artifact | `process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY` | ✓ WIRED (with operational caveat) | Build-time inlined public key; frontend rebuild/redeploy required on key rotation. |
| `.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md` (this report) | `backend/tests/test_turnstile_service.py`, `backend/tests/test_ratelimit.py`, `backend/tests/test_turnstile_live.py` | Recorded targeted test evidence | ✓ WIRED | Commands/results captured in "Targeted Test Evidence (recorded)". |

## Requirements Coverage

| Requirement | Status | Evidence / Notes |
| --- | --- | --- |
| SECR-10 | ✓ VERIFIED WITH CAVEAT | Turnstile wiring/config evidenced in backend/frontend (`backend/app/core/config.py`, `frontend/app/admin/paste/ExtractForm.tsx`) and Phase 7 summaries. **Caveat:** `NEXT_PUBLIC_TURNSTILE_SITE_KEY` is inlined in the frontend bundle at build time; changing the Cloudflare Turnstile site key requires a frontend rebuild/redeploy. |
| SECR-11 | ✓ VERIFIED (offline evidence) | Server-side anti-bot/rate-limit controls evidenced in code and passing offline suites (`tests/test_turnstile_service.py`, `tests/test_ratelimit.py`); reveal endpoint enforces limiter + Siteverify (`backend/app/api/v1/public.py`). DB-backed endpoint suite `test_reveal_api.py` blocked by missing `jobs` relation in current test DB. |
| SECR-12 | ◐ PARTIAL / SPLIT (not closed here) | Phase 7-side anti-spam/Turnstile evidence is documented in this file. `Phase 12 owns /admin/expire contract reconciliation` (X-Cron-Secret-only contract and Phase 9-side evidence). No full SECR-12 closure claimed in Phase 11. |

## Phase 7 Artifact Citations

- `.planning/phases/07-contact-reveal-anti-spam-completeness/07-01-SUMMARY.md`
- `.planning/phases/07-contact-reveal-anti-spam-completeness/07-02-SUMMARY.md`
- `.planning/phases/07-contact-reveal-anti-spam-completeness/07-03-SUMMARY.md`

## Anti-Patterns / Audit Integrity Notes

| Area | Observation | Severity | Impact |
| --- | --- | --- | --- |
| Evidence completeness | DB-backed `test_reveal_api.py` could not run in this environment (`jobs` relation missing) | ⚠️ Warning | Endpoint-level DB integration proof for reveal contract is not freshly re-recorded here; offline unit/service/limiter evidence and code inspection support SECR-11 but do not replace migrated DB test execution. |
| Live Cloudflare proof | `test_turnstile_live.py` skipped (TURNSTILE_LIVE not set) | ℹ️ Info | No real Cloudflare Siteverify network proof claimed in this run. |
| Scope boundary | SECR-12 shared across phases | ℹ️ Info | Explicitly split to avoid false closure: Phase 11 documents Phase 7 side only; Phase 12 owns `/admin/expire` contract reconciliation. |

## Human Verification Required

### 1. Reveal Flow (Browser/UI + Real Widget)

**Test:** Run frontend+backend locally or in a configured environment, open a published job, request contact reveal, and complete Turnstile.
**Expected:** Contact is revealed only after valid server-side verification; invalid/expired token yields 403 copy; repeated attempts from same IP eventually yield pt-BR 429 with `Retry-After`; reopening same revealed job can reuse in-memory contact behavior (frontend concern).
**Why human:** Requires interactive Turnstile widget/token lifecycle and browser runtime behavior not exercised by the recorded automated tests here.

### 2. DB-backed Reveal Endpoint Suite in a Migrated Test DB

**Test:** Configure/migrate `TEST_DATABASE_URL` (or DATABASE_URL used by tests) so `jobs` exists, then rerun `test_reveal_api.py`.
**Expected:** Suite passes and confirms 404/403/429/200 reveal contract cases end-to-end against the DB-backed app fixture.
**Why human/environmental:** Blocked here by missing relation `jobs` in the configured database.

## Gaps Summary

Offline anti-spam primitives and code wiring for Phase 7 are evidenced (`test_turnstile_service.py`, `test_ratelimit.py`, Turnstile/rate-limit/reveal code paths, and SECR-10 rebuild caveat). The verification is marked `gaps_found` because DB-backed reveal API evidence (`test_reveal_api.py`) could not be executed in the current environment due to missing `jobs` relation. SECR-12 remains intentionally split: this report covers the Phase 7 side only, and **Phase 12 owns /admin/expire contract reconciliation**.

---
_Verified: 2026-11-15T03:10:00Z_
_Verifier: OpenCode (gsd-executor, Phase 11 backfill)_
