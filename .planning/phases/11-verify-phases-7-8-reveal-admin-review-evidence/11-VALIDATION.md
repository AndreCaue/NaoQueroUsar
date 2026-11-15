---
phase: 11
slug: verify-phases-7-8-reveal-admin-review-evidence
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-15
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio + httpx (backend, offline fakes/ASGI where applicable) |
| **Config file** | `backend/pyproject.toml` (run tests from `backend/`) |
| **Quick run command** | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_turnstile_service.py tests/test_ratelimit.py -q` |
| **Full suite command** | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_reveal_api.py tests/test_admin_jobs.py tests/test_extract_api.py tests/test_turnstile_service.py tests/test_ratelimit.py tests/test_turnstile_live.py -q` (DB-backed subsets require configured/migrated `TEST_DATABASE_URL`/`DATABASE_URL`) |
| **Estimated runtime** | ~60-180 seconds (environment-dependent; DB-backed runs vary) |

---

## Sampling Rate

- **After every task commit:** Run the smallest relevant targeted subset for the artifact/requirement being updated (e.g. offline Phase 7 set, or `-k approve/update/delete/auth` for Phase 8 evidence) from `backend/`
- **After every plan wave:** Re-run all targeted commands cited in `07-VERIFICATION.md`/`08-VERIFICATION.md` that are feasible in the current environment; record skips/blockers with reason
- **Before `/gsd-verify-work`:** All cited/feasible targeted checks green or explicitly documented (env-blocked/manual) with evidence
- **Max feedback latency:** 180 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-TBD-01 | TBD | TBD | SECR-10, SECR-11, SECR-12 (Phase 7 side) | — | Reveal/login anti-spam controls evidenced; SECR-10 rebuild caveat documented; SECR-12 split ownership preserved | unit/integration + manual doc caveat | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_turnstile_service.py tests/test_ratelimit.py tests/test_reveal_api.py -q` | ✅ tests exist (DB-backed may be env-blocked) | ⬜ pending |
| 11-TBD-02 | TBD | TBD | ADMN-10, ADMN-11, ADMN-12, REVW-10, REVW-11, REVW-12 | — | Admin auth/review CRUD semantics evidenced; UI claims have code + human/browser notes; REVW-12 404 mapped to "exclusão duplicada é no-op" | integration + manual UI checks | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_admin_jobs.py tests/test_extract_api.py -q` | ✅ tests exist (DB-backed may be env-blocked) | ⬜ pending |
| 11-TBD-03 | TBD | TBD | SECR-10..12, ADMN-10..12, REVW-10..12 (traceability/requirements) | — | Traceability artifacts and REQUIREMENTS updates are machine-checkable and ownership/split notes unambiguous | manual/doc verification | `rg -n "ADMN-12|REVW-12|SECR-12" .planning/phases/08-admin-review-area-completeness .planning/REQUIREMENTS.md .planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md .planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md` | N/A (created during phase) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Ensure a configured/migrated Postgres test database is available for DB-backed targeted tests (`test_reveal_api.py`, `test_admin_jobs.py`, `test_extract_api.py`) — probed environment lacked `jobs` schema
- [ ] Capture targeted command outputs/snippets in verification artifacts (or supporting evidence doc) per D-01/D-04
- [ ] No new test framework install expected; pytest/venv already present in `backend/.venv`

*Existing infrastructure covers most phase requirements once DB-backed test environment is available; this phase is primarily verification/traceability work.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Admin login shows Turnstile indicator/widget interaction-only behavior | ADMN-10 | Interactive browser/widget behavior not proven by static inspection alone | Review `frontend/app/admin/paste/ExtractForm.tsx` evidence and record human/browser check notes in `08-VERIFICATION.md` (or mark as human verification item) |
| Toast/feedback and "vaga aparece imediatamente na home pública" after approve | REVW-10, ADMN/REVW UX criteria | End-to-end UI/public refresh behavior may not be exercised by backend tests alone | Cite review UI/API code paths and record human/browser verification notes in `08-VERIFICATION.md` |
| Turnstile site key rebuild operational caveat | SECR-10 | Build-time inlining/redeploy behavior is operational, not fully assertable by unit tests | Document caveat explicitly in `07-VERIFICATION.md` with code/config evidence |
| `test_turnstile_live.py` real Cloudflare round-trip (optional) | SECR-10/11 supporting confidence | Opt-in network test; skipped by default without `TURNSTILE_LIVE=1` | Record skip rationale now; run only with explicit approval/env and capture result if executed |

*All phase behaviors have automated verification.* (No — several UI/operational claims require documented manual/human verification notes per CONTEXT decisions.)

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
