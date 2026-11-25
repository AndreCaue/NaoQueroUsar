---
phase: 31-independent-publish-pipeline
reviewed: 2026-11-25T00:00:00Z
depth: standard
files_reviewed: 19
files_reviewed_list:
  - backend/alembic/versions/0008_instagram_publish_reconciliation.py
  - backend/app/services/social/instagram.py
  - backend/tests/test_instagram_publisher.py
  - backend/app/models/social_post.py
  - backend/app/schemas/social_posts.py
  - backend/app/services/social/types.py
  - backend/app/services/social/publish_pipeline.py
  - backend/app/crud/social_posts.py
  - backend/app/crud/social_accounts.py
  - backend/app/core/config.py
  - backend/tests/test_social_publish_pipeline.py
  - backend/tests/conftest.py
  - backend/app/api/v1/admin.py
  - backend/tests/test_admin_social_publish.py
  - backend/tests/test_admin_instagram_social_posts.py
  - frontend/lib/api.ts
  - frontend/app/admin/social-posts/SocialPostsClient.tsx
  - frontend/app/admin/review/EditJobDialog.tsx
  - frontend/app/admin/review/ReviewQueue.tsx
findings:
  critical: 0
  warning: 4
  info: 0
  total: 4
status: issues_found
---

# Phase 31: Code Review Report

**Reviewed:** 2026-11-25T00:00:00Z
**Depth:** standard
**Files Reviewed:** 19
**Status:** issues_found

## Summary

Reviewed the Phase 31 Instagram publish/reconciliation changes across backend publisher/pipeline/CRUD/API, tests, and admin frontend. The implementation shows good safety intent (ambiguous classification, no token leakage in messages, reconciliation metadata, rate-limit handling). Four warnings were found: one reconciliation-safety gap in IG failure handling, one stale request-session read after cross-session retry execution, one frontend URL-scheme defense-in-depth gap, and duplicate test names that reduce effective test coverage.

## Warnings

### WR-01: IG non-ambiguous failure with known container can skip reconciliation

**File:** `backend/app/services/social/publish_pipeline.py:1027-1087`
**Issue:** The IG failure branch treats `container_id` as critical, but only enters the reconciliation-required path when `category == ambiguous` or `error_code` contains `"ambiguous"`. For a non-ambiguous result with a known `container_id` (including `unknown` fallback from `result.category or PublishFailureCategory.unknown`), execution falls through to the permanent/conclusive handler and marks `ig_reconciliation_required=False`, `ig_reconciliation_state="reconciled_failed"`. The comment at line 1028 states "any ambiguity or critical-step result with known container must be reconciliation-safe", but the code does not enforce that for all critical-step outcomes. If a publish step had an uncertain server-side outcome despite a non-ambiguous classification, this can prematurely mark the post as conclusively failed and bypass reconciliation-before-republish safety.
**Fix:**
```python
# Treat any known container/critical publish outcome conservatively unless it is
# explicitly proven safe. At minimum, unknown+container should be reconciliation-safe.
if category == PublishFailureCategory.ambiguous or bool(container_id):
    ambiguous_like = (
        category == PublishFailureCategory.ambiguous
        or (error_code and "ambiguous" in error_code)
        or category == PublishFailureCategory.unknown
    )
    if ambiguous_like:
        post.ig_last_reconciled_at = now
        post.ig_last_publish_error_code = error_code
        return await _finalize_failed(
            session,
            post,
            attempt_number=attempt_number,
            safe_msg=MSG_IG_AMBIGUOUS,
            result="ambiguous",
            summary="ig_ambiguous_needs_reconciliation",
            final=True,
            category=PublishFailureCategory.ambiguous,
            ig_container_id=container_id,
            ig_media_id=published_media_id,
            ig_reconciliation_required=True,
            ig_reconciliation_state="needs_reconciliation",
            ig_last_reconciled_at=now,
            ig_last_publish_error_code=error_code,
        )
    # For conclusive permanent+container, keep conservative behavior only if
    # you can prove Meta did not accept publish; otherwise route to reconciliation.
```

### WR-02: Retry endpoint may return stale social status after cross-session pipeline execution

**File:** `backend/app/api/v1/admin.py:545-567`
**Issue:** `_retry_job_social_post_impl` calls `run_social_publish_cycle(...)`, which processes and commits using its own session factory/sessions. It then re-reads status via `get_job_social_status_item(...)` on the same request-scoped `session`. If the request session has cached ORM state (`session.get` identity map / `expire_on_commit=False` patterns), the refreshed item can be stale and the endpoint may return an outdated `outcome/item` to the admin UI.
**Fix:**
```python
counters = await run_social_publish_cycle(post_id=target_post.id, limit=1) or {}

# Ensure request session sees commits made by pipeline sessions.
await session.expire_all()

refreshed_item, _ = await get_job_social_status_item(
    session,
    job_id,
    account_status=_facebook_account_status_value(await get_facebook_account(session))
    if target_provider == "facebook"
    else None,
    provider=target_provider,
)
```

### WR-03: Published/permalink links are not scheme-validated before rendering in href

**File:** `frontend/app/admin/social-posts/SocialPostsClient.tsx:277-289`, `frontend/app/admin/review/EditJobDialog.tsx:1693-1706`
**Issue:** The UI renders `published_permalink` / `published_url` directly into anchor `href` attributes. Backend sanitization limits/redacts text but does not enforce an `https://` (or safe http) URL scheme. As defense-in-depth against unexpected or malicious stored values, the frontend should only render clickable links for safe URL schemes.
**Fix:**
```ts
function safeExternalHttpUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    if (url.protocol === "https:" || url.protocol === "http:") return url.toString();
  } catch {
    return null;
  }
  return null;
}

const permalink = safeExternalHttpUrl(item.published_permalink || item.published_url);
...
{permalink ? (
  <a href={permalink} target="_blank" rel="noopener noreferrer">Ver post no {platform}</a>
) : (
  <p className="text-fg-muted">Publicado no {platform}. Link indisponível.</p>
)}
```

### WR-04: Duplicate test names override earlier tests, reducing effective coverage

**File:** `backend/tests/test_admin_social_publish.py:143,249,282,411,495,548`
**Issue:** Several tests share identical names (`test_approve_dispatches_fb_and_ig_independently`, `test_worker_response_includes_by_provider_breakdown`, and overlapping retry/ambiguity coverage at 282/548). In pytest, a later function with the same name overrides the earlier one in the same module, so earlier cases do not execute. This creates false confidence in the test suite and can hide regressions in the Phase 31 admin publish/retry behavior.
**Fix:**
```python
# Rename duplicates to unique, intention-revealing names, or merge assertions.
@pytest.mark.asyncio
async def test_approve_dispatches_fb_and_ig_independently_publ01(...):
    ...

@pytest.mark.asyncio
async def test_worker_response_includes_by_provider_breakdown_contract(...):
    ...

# For overlapping retry tests, keep one canonical case per behavior and remove
# dead duplicates; ensure each scenario name is unique.
```

---

_Reviewed: 2026-11-25T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
