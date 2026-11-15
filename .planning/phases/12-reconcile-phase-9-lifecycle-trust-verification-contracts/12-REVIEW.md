---
phase: 12-reconcile-phase-9-lifecycle-trust-verification-contracts
reviewed: 2026-11-15T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - backend/app/core/config.py
  - backend/tests/test_admin_expire.py
  - backend/tests/test_report_api.py
findings:
  critical: 0
  warning: 2
  info: 0
  total: 2
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-11-15T00:00:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed `backend/app/core/config.py`, `backend/tests/test_admin_expire.py`, and `backend/tests/test_report_api.py`. The configuration module is generally well-structured with clear fail-closed validation for Turnstile and CORS outside dev, and the tests exercise important security/contract behaviors (closed cron gate, idempotent sweep, report accept-and-log/no-enumeration). No critical bugs or security vulnerabilities were identified in the reviewed code. Findings are limited to test-reliability risks around cross-session state visibility and rate-limiter state accumulation that can make assertions or ordering-dependent checks flaky depending on fixture isolation.

## Warnings

### WR-01: Post-request DB assertions may observe stale session state

**File:** `backend/tests/test_admin_expire.py:150-153`, `backend/tests/test_admin_expire.py:160-168`, `backend/tests/test_admin_expire.py:195-199`; `backend/tests/test_report_api.py:86-96`
**Issue:** These tests perform mutations through API requests (e.g. `POST /api/v1/admin/expire`, `POST .../report`) and then assert database state using the same test `db_session`/ORM queries (`db_session.scalars(select(...))`, `db_session.scalar(text(...))`). If the endpoint commits using a different session/transaction than the injected test session, the test session can retain a stale identity map/transaction snapshot and return outdated results or miss committed deletes, depending on fixture isolation behavior. This is a common source of flaky async integration tests.
**Fix:** Synchronize the test session state before asserting post-request DB effects. For example, expire/rollback or start a fresh read as appropriate for the fixture setup:
```python
resp = await client.post(ENDPOINT, headers={"X-Cron-Secret": cron_secret})
assert resp.status_code == 200

await db_session.rollback()  # or: db_session.expire_all()
remaining = list((await db_session.scalars(select(Job.title))).all())
assert sorted(remaining) == ["Pending viva", "Publicada viva"]
```
Apply the same pattern in idempotency/status-parameterized expire tests and in `test_report_persists_nothing` if the fixture does not already guarantee visibility.

### WR-02: Rate-limit tests depend on shared limiter state across requests/tests

**File:** `backend/tests/test_admin_expire.py:110-123`; `backend/tests/test_report_api.py:99-108`
**Issue:** Both tests issue enough requests within the same test to cross the per-IP/per-minute threshold and assert `429` on the final call. If the rate limiter storage is process-global or keyed in a way that persists across tests (and not reset by fixtures between tests), earlier tests or test ordering can consume quota and cause false failures/passes. `test_expire_probing_is_rate_limited` is especially sensitive because it assumes a clean 10-then-429 window at the start of the test.
**Fix:** Ensure limiter state is isolated/reset per test (preferred, in fixture/conftest), or use a test-specific key/client identity and document/reset it explicitly in the test. For example:
```python
@pytest.fixture(autouse=True)
def reset_rate_limiter(limiter):
    limiter.reset()
    yield
    limiter.reset()
```
Or, if supported by the app, override the limiter/storage dependency in the test client fixture so each test gets a fresh in-memory limiter instance.

---

_Reviewed: 2026-11-15T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_