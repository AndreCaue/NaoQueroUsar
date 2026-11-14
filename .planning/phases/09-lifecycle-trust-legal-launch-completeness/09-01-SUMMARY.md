---
phase: 09-lifecycle-trust-legal-launch-completeness
plan: 01
subsystem: backend
tags: [lifecycle, trust, expires_at, cron, report]
metrics:
  tests_passed: 26
  tests_total: 26
---

# Plan 09-01: Lifecycle & Trust Proofs (Backend) — Complete

**Objective:** Turn already-implemented Phase 6 lifecycle and trust behaviour into an executable contract: pin the 14-day `expires_at` DDL, prove the hard-delete sweep is status-agnostic and future-safe, re-assert that `/admin/expire` accepts only `X-Cron-Secret`, and pin the report endpoint's 500-char/no-persistence contract. Also fix stale ROADMAP/REQUIREMENTS/DEPLOY wording that claims an admin JWT works on the cron endpoint.

## What Was Built

### LIFE-10: DDL-Level 14-Day Expiry Pin
- Added `test_expires_at_column_is_timestamptz_with_14_day_default` to `backend/tests/test_schema.py`
- Pins `expires_at` as `timestamptz` with `now() + interval '14 days'` server default via `information_schema.columns`
- Pins `ix_jobs_expires_at` index existence
- Verified in DB: column data type, stored default expression, index present

### LIFE-11 / LIFE-12: Sweep Status-Agnostic + Future-Safe
- Added parametrized `test_expire_deletes_expired_row_for_every_status` to `backend/tests/test_admin_expire.py`
- Covers all 4 `JobStatus` values: `pending`, `published`, `needs_review`, `invalid`
- Each case: 1 expired row deleted + 1 future row of same status survives
- `test_expire_is_idempotent` retained (second call returns `{"deleted": 0, "status": "ok"}`)

### TRST-11: Report 500-Char Cap + No Persistence
- Added `test_report_reason_at_500_chars_is_accepted_and_logged` — 500-char reason accepted, logged whole, no persistence
- Added `test_report_persists_nothing` — `to_regclass('public.reports')` is `None`

### Documentation Alignment (T-06-01)
- **ROADMAP.md** Phase 9 criterion 2: replaced `(ou Bearer JWT admin)` with `(protegido exclusivamente por \`X-Cron-Secret\`; um Bearer JWT de admin NÃO é aceito — T-06-01)`
- **REQUIREMENTS.md** LIFE-13: replaced `aceita header Bearer JWT admin ou \`X-Cron-Secret\`` with `aceita somente \`X-Cron-Secret\` (Bearer JWT admin NÃO é aceito — T-06-01)`
- **docs/DEPLOY.md**: added "Credencial única" section after "Sem segredo configurado": `POST /api/v1/admin/expire` aceita somente `X-Cron-Secret`; admin JWT NÃO autoriza

## Deviations
None. All acceptance criteria met.

## Verification
```
cd backend
.venv\Scripts\python.exe -m pytest tests/test_schema.py tests/test_admin_expire.py tests/test_report_api.py -q
# 26 passed
```

## Key Files Modified
- `backend/tests/test_schema.py` — DDL pin test (LIFE-10)
- `backend/tests/test_admin_expire.py` — parametrized sweep tests + T-06-01 gate (LIFE-11/LIFE-12)
- `backend/tests/test_report_api.py` — 500-char + no-persistence tests (TRST-11)
- `.planning/ROADMAP.md` — documentation alignment
- `.planning/REQUIREMENTS.md` — LIFE-13 alignment
- `docs/DEPLOY.md` — credential section added

## Success Criteria
- [x] LIFE-10: `expires_at` is `timestamptz` with DB `now() + interval '14 days'` default, asserted at DDL level
- [x] LIFE-11: the sweep is idempotent, uses the DB clock and never deletes future rows
- [x] LIFE-12: expired rows of all four statuses are deleted by the same rule
- [x] TRST-11: report accepts an optional ≤500-char reason, logs it single-line, persists nothing and is throttled
- [x] Criterion 2 documentation no longer claims an admin JWT can authorize `/admin/expire`