---
phase: 31-independent-publish-pipeline
reviewed: 2026-11-25T00:00:00Z
depth: standard
files_reviewed: 19
files_reviewed_list:
  - backend/alembic/versions/0008_instagram_publish_reconciliation.py
  - backend/app/api/v1/admin.py
  - backend/app/core/config.py
  - backend/app/crud/social_accounts.py
  - backend/app/crud/social_posts.py
  - backend/app/models/social_post.py
  - backend/app/schemas/social_posts.py
  - backend/app/services/social/instagram.py
  - backend/app/services/social/publish_pipeline.py
  - backend/app/services/social/types.py
  - backend/tests/conftest.py
  - backend/tests/test_admin_instagram_social_posts.py
  - backend/tests/test_admin_social_publish.py
  - backend/tests/test_instagram_publisher.py
  - backend/tests/test_social_publish_pipeline.py
  - frontend/app/admin/review/EditJobDialog.tsx
  - frontend/app/admin/review/ReviewQueue.tsx
  - frontend/app/admin/social-posts/SocialPostsClient.tsx
  - frontend/lib/api.ts
findings:
  critical: 0
  warning: 6
  info: 0
  total: 6
status: issues_found
---

# Phase 31: Code Review Report

**Reviewed:** 2026-11-25T00:00:00Z
**Depth:** standard
**Files Reviewed:** 19
**Status:** issues_found

## Summary

Reviewed the Phase 31 Instagram publish/reconciliation diff set at standard depth: migration, admin API/approval/retry routes, config, CRUD/model/schema changes, Instagram publisher, publish pipeline, related tests, and admin frontend surfaces. The implementation has solid intent around provider isolation, safe reconciliation metadata, and redacted logging. I found no Critical issues in the reviewed scope, but there are reliability gaps that can leave social posts stuck in `publishing`, a rate-limit handling gap in IG reconciliation polling, silent error swallowing in approve-time scheduling, unsafe direct use of backend-provided URLs in frontend link/image sinks, and a duplicate test name that masks coverage.

## Warnings

### WR-01: Claim-then-crash can leave posts permanently stuck in `publishing`

**Severity:** WARNING
**File:** `backend/app/services/social/publish_pipeline.py:1119-1181`
**Issue:** `run_social_publish_cycle` claims due posts in a committed transaction (`claim_for_publishing` moves them to `publishing`) and only processes them in later per-post transactions. If the worker/process crashes, is killed, or loses the session before the processing loop handles a claimed ID, the post remains `publishing` with no visible reclaim path. `claim_for_publishing`/`list_due_for_claim` only consider `scheduled`/`failed`, so these rows can become operationally stuck until manual DB intervention.
**Fix:**
```python
# Add stale-claim reclaim metadata and a sweeper.
# 1) Persist claimed_at when claiming.
#    post.status = SocialPostStatus.publishing
#    post.claimed_at = now
#    post.next_retry_at = None

# 2) Reclaim stale publishing rows before/alongside normal claiming.
STALE_PUBLISHING_MINUTES = 15

async def reclaim_stale_publishing(session, *, now: datetime, provider: str) -> int:
    cutoff = now - timedelta(minutes=STALE_PUBLISHING_MINUTES)
    stmt = (
        select(SocialPost)
        .where(
            SocialPost.provider == provider,
            SocialPost.status == SocialPostStatus.publishing,
            SocialPost.external_post_id.is_(None),
            SocialPost.claimed_at.is_not(None),
            SocialPost.claimed_at <= cutoff,
        )
        .with_for_update(skip_locked=True)
    )
    rows = (await session.scalars(stmt)).all()
    for post in rows:
        attempt = int(post.attempts or 0) + 1
        await mark_failed(
            session,
            post,
            attempts=attempt,
            last_error=MSG_AMBIGUOUS,
            next_retry_at=None,
            final=True,
        )
        if (post.provider or "").lower() == "instagram" and post.ig_container_id:
            post.ig_reconciliation_required = True
            post.ig_reconciliation_state = "needs_reconciliation"
            post.ig_last_reconciled_at = now
    return len(rows)
```

### WR-02: Recovery exception can leave a failed processing attempt stuck in `publishing`

**Severity:** WARNING
**File:** `backend/app/services/social/publish_pipeline.py:1182-1238`
**Issue:** When per-post processing raises, the code attempts recovery in a fresh transaction and marks the post ambiguous/final. If that recovery also raises, it only logs and increments `processed/failed_final` counters. The post may still be `publishing` in the database, and because normal claiming ignores `publishing`, it can remain stuck indefinitely. The counter output can also report a final failure that was not actually persisted.
**Fix:**
```python
except Exception:
    logger.exception("social_publish_item_failed", extra={"social_post_id": str(pid), "provider": provider})
    recovery_outcome = "failed_final"
    recovered = False
    try:
        async with async_session_factory() as session:
            async with session.begin():
                post = await get_social_post_by_id(session, pid)
                if post is not None and post.status == SocialPostStatus.publishing and not post.external_post_id:
                    attempt_number = int(post.attempts or 0) + 1
                    ambiguous_msg = MSG_IG_AMBIGUOUS if (post.provider or "") == "instagram" else MSG_AMBIGUOUS
                    await mark_failed(session, post, attempts=attempt_number, last_error=ambiguous_msg, next_retry_at=None, final=True)
                    # ...existing IG reconciliation flagging/log...
                    recovered = True
                elif post is not None and (post.status == SocialPostStatus.published or post.external_post_id):
                    recovery_outcome = "idempotent"
                    recovered = True
    except Exception:
        logger.exception("social_publish_item_recovery_failed", extra={"social_post_id": str(pid), "provider": provider})

    if not recovered and recovery_outcome != "idempotent":
        logger.error("social_publish_item_stuck_publishing", extra={"social_post_id": str(pid), "provider": provider})
        counters["skipped"] += 1
        pcounts["skipped"] += 1
        continue

    counters["processed"] += 1
    pcounts["processed"] += 1
    ...
```

### WR-03: IG reconciliation status polling can amplify rate limits

**Severity:** WARNING
**File:** `backend/app/services/social/publish_pipeline.py:484-513`
**Issue:** During `_ig_reconcile_before_publish`, `ambiguous_http` status-check responses are treated as retryable `IN_PROGRESS` unless they match the 2207042/content-publishing-limit case. Generic 429 rate-limit responses from the status endpoint fall through and the loop sleeps/polls again, which can amplify throttling. Reconciliation should be conservative and stop on platform rate limiting.
**Fix:**
```python
elif info["kind"] in {"ambiguous", "ambiguous_http"}:
    body = info.get("body")
    err = body.get("error") if isinstance(body, dict) else None
    err = err if isinstance(err, dict) else {}
    code = err.get("code")
    subcode = err.get("error_subcode")
    blob = " ".join([
        str(err.get("message") or "").lower(),
        str(err.get("error_user_title") or "").lower(),
        str(err.get("error_user_msg") or "").lower(),
    ])
    if code == 2207042 or subcode == 2207042 or "content_publishing_limit" in blob:
        ...
        return await _finalize_failed(..., ig_last_publish_error_code="ig_content_publishing_limit")
    if info.get("status_code") == 429 or code in {4, 17, 32, 613} or "rate limit" in blob or "too many" in blob:
        post.ig_last_reconciled_at = now
        post.ig_last_publish_error_code = "ig_rate_limit_blocked"
        return await _finalize_failed(
            session, post,
            attempt_number=attempt_number,
            safe_msg=MSG_IG_RATE_LIMIT,
            result="failed_permanent",
            summary="ig_rate_limit_blocked",
            final=True,
            category=PublishFailureCategory.permanent,
            ig_container_id=container_id,
            ig_reconciliation_required=False,
            ig_reconciliation_state="reconciled_failed",
            ig_last_reconciled_at=now,
            ig_last_publish_error_code="ig_rate_limit_blocked",
        )
    status = "IN_PROGRESS"
```

### WR-04: Approve-time social scheduling failures are swallowed without logs

**Severity:** WARNING
**File:** `backend/app/api/v1/admin.py:267-277`, `backend/app/api/v1/admin.py:307-312`
**Issue:** Both the Facebook registration block and the independent Instagram scheduling/dispatch-prep block catch broad `Exception`, roll back, and `pass` silently. This hides operational failures (DB errors, serialization bugs, unexpected state) and makes approve-time IG/FB scheduling issues hard to diagnose. For IG, the failure is completely invisible to the caller because the response only carries Facebook `social` outcome.
**Fix:**
```python
import logging

logger = logging.getLogger(__name__)

...
    except Exception:
        logger.exception("approve_fb_social_registration_failed", extra={"job_id": str(job_id)})
        try:
            await session.rollback()
        except Exception:
            logger.exception("approve_fb_social_registration_rollback_failed", extra={"job_id": str(job_id)})

...
    except Exception:
        logger.exception("approve_ig_social_dispatch_prep_failed", extra={"job_id": str(job_id)})
        try:
            await session.rollback()
        except Exception:
            logger.exception("approve_ig_social_dispatch_prep_rollback_failed", extra={"job_id": str(job_id)})
```

### WR-05: Backend-provided URLs are used directly in frontend `href`/`src` sinks

**Severity:** WARNING
**File:** `frontend/app/admin/review/EditJobDialog.tsx:1695`, `frontend/app/admin/review/EditJobDialog.tsx:1885`, `frontend/app/admin/social-posts/SocialPostsClient.tsx:278`
**Issue:** The admin UI renders `published_permalink`/`published_url` directly into anchor `href` attributes and `igMedia.image_url` directly into an `img src`. These values come from backend responses. While the expected sources are Meta/controlled media URLs, the frontend should enforce an `https:` allowlist before rendering to avoid unsafe navigation or unexpected resource loading if malformed data is persisted or returned.
**Fix:**
```ts
function safeHttpsUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}

// EditJobDialog
const igPermalink = safeHttpsUrl(igStatus.published_permalink || igStatus.published_url);
{igPermalink ? <a href={igPermalink} ...>Ver post no Instagram</a> : <p>Link indisponível.</p>}

const igImageUrl = safeHttpsUrl(igMedia?.image_url);
{igImageUrl ? <img src={igImageUrl} ... /> : ...}

// SocialPostsClient
const permalink = safeHttpsUrl(item.published_permalink || item.published_url);
```

### WR-06: Duplicate test name masks an existing admin social publish test

**Severity:** WARNING
**File:** `backend/tests/test_admin_social_publish.py:249`, `backend/tests/test_admin_social_publish.py:495`
**Issue:** `test_worker_response_includes_by_provider_breakdown` is defined twice in the same module. Pytest's default collection keeps the latter definition, so the earlier test case (using `cron_secret_header` and a different response shape/assertion path) is never executed. This silently reduces regression coverage for the worker endpoint contract.
**Fix:**
```python
# Keep one canonical name per test.
async def test_worker_response_includes_by_provider_breakdown_with_cron_secret(
    client, admin_password, cron_secret_header, monkeypatch
):
    ...

# Rename the later test, or merge its assertions into the first.
async def test_worker_response_includes_by_provider_breakdown_without_cron_fixture(
    client, admin_password, monkeypatch
):
    ...
```

---

_Reviewed: 2026-11-25T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
