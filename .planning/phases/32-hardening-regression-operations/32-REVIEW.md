---
phase: 32-hardening-regression-operations
reviewed: 2026-11-26T12:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - backend/.env.example
  - backend/tests/test_admin_social_publish.py
  - backend/tests/test_docs_meta_instagram.py
  - backend/tests/test_facebook_publisher.py
  - backend/tests/test_social_post_generation.py
  - docs/META-INTEGRATION-TESTING.md
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 32: Code Review Report

**Reviewed:** 2026-11-26T12:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed 6 scoped files (env template, 4 test modules, 1 operational doc) at standard depth. No critical security or correctness bugs were found in production-facing content; the `.env.example` contains placeholders only, docs are sanitized and include explicit handoff boundaries, and publisher/generation tests include token-leak and policy-safety assertions. The main issues are in `backend/tests/test_admin_social_publish.py`: a duplicate test name silently overrides an earlier test (coverage loss), and a weak assertion accepts multiple status codes, reducing regression detection.

## Warnings

### WR-01: Duplicate test name silently overrides earlier test

**File:** `backend/tests/test_admin_social_publish.py:249`, `backend/tests/test_admin_social_publish.py:513`
**Issue:** `test_worker_response_includes_by_provider_breakdown` is defined twice. In Python/pytest, the second definition at line 513 replaces the first at line 249 in the module namespace, so the first test is never collected or executed. The overridden test uses the `cron_secret_header` fixture and validates the expected worker response shape; the overriding test hardcodes `X-Cron-Secret` and skips on `401/403`, which can also mask configuration/fixture regressions. This creates silent coverage loss for the social worker response contract.
**Fix:**
```python
# Keep a single deterministic test using the cron_secret_header fixture.
@pytest.mark.asyncio
async def test_worker_response_includes_by_provider_breakdown(
    client, admin_password, cron_secret_header, monkeypatch
):
    await _login(client, admin_password)

    async def fake_cycle(**kwargs):
        return {
            "claimed": 2,
            "processed": 2,
            "published": 1,
            "retried": 0,
            "failed_final": 1,
            "skipped": 0,
            "idempotent": 0,
            "by_provider": {
                "facebook": {"claimed": 1, "processed": 1, "published": 1, "retried": 0, "failed_final": 0, "skipped": 0, "idempotent": 0},
                "instagram": {"claimed": 1, "processed": 1, "published": 0, "retried": 0, "failed_final": 1, "skipped": 0, "idempotent": 0},
            },
        }

    monkeypatch.setattr("app.api.v1.admin.run_social_publish_cycle", fake_cycle)

    resp = await client.post("/api/v1/admin/social/worker", headers=cron_secret_header)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ok"
    assert body["claimed"] == 2
    assert body["by_provider"]["facebook"]["published"] == 1
    assert body["by_provider"]["instagram"]["failed_final"] == 1

# Remove the duplicate definition at line 513 (or rename/merge only if it adds
# distinct assertions not already covered).
```

### WR-02: Weak assertion allows multiple unrelated outcomes

**File:** `backend/tests/test_admin_social_publish.py:579`
**Issue:** `test_retry_provider_resolution_mismatch_and_omitted_ambiguity` asserts `resp.status_code in (200, 409, 400)` after requesting retry with `provider=facebook` for a job that has both Facebook and Instagram failed posts. Accepting success, conflict, and bad request in the same case makes the test non-deterministic as a contract check and can hide regressions in provider resolution, validation, or retry eligibility.
**Fix:**
```python
# Make the expected contract explicit. If explicit provider is valid and the
# Facebook post is retry-eligible, assert 200 and the selected provider.
resp = await client.post(
    f"/api/v1/admin/jobs/{job.id}/social-post/retry?provider=facebook",
    headers={"Authorization": f"Bearer {token}"},
)
assert resp.status_code == 200, resp.text
body = resp.json()
assert body["item"]["provider"] == "facebook"

# If the intended contract is 409 for this specific setup, assert 409 with the
# expected error shape instead. Avoid multi-status acceptance.
```

## Info

### IN-01: Unused imports and unused test parameter

**File:** `backend/tests/test_admin_social_publish.py:1`, `backend/tests/test_admin_social_publish.py:2`, `backend/tests/test_admin_social_publish.py:566`
**Issue:** `uuid`, `datetime`, `timedelta`, and `timezone` are imported but not used. In `test_retry_provider_resolution_mismatch_and_omitted_ambiguity`, the `monkeypatch` parameter is declared but unused. These are minor maintainability issues that add noise and can hide real lint/test hygiene problems.
**Fix:**
```python
# Remove unused imports:
import pytest
from fastapi import BackgroundTasks

# Remove unused monkeypatch parameter if no patching is needed:
async def test_retry_provider_resolution_mismatch_and_omitted_ambiguity(
    client, db_session, admin_password
):
    ...
```

### IN-02: Overlapping duplicate test scenarios increase maintenance cost

**File:** `backend/tests/test_admin_social_publish.py:143`, `backend/tests/test_admin_social_publish.py:198`, `backend/tests/test_admin_social_publish.py:282`, `backend/tests/test_admin_social_publish.py:411`, `backend/tests/test_admin_social_publish.py:466`, `backend/tests/test_admin_social_publish.py:566`
**Issue:** Several tests cover overlapping approve/dispatch/retry scenarios with slightly different names and setup (`*_publ01`, alternate dispatch-failure/ambiguity cases). Duplication is not harmful by itself, but it raises maintenance cost and makes it easier for contract drift or accidental name collisions to slip in, as seen with WR-01.
**Fix:**
```python
# Consolidate overlapping scenarios into parametrized tests where behavior is the
# same, and keep distinct test names only when the contract being proven differs.
# Example shape:
@pytest.mark.parametrize("case", ["fb_only", "fb_and_ig", "ig_dispatch_fails"])
async def test_approve_dispatch_contract(case, ...):
    ...
```

---

_Reviewed: 2026-11-26T12:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
