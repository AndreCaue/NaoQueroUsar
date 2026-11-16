---
phase: 17-publicacao-assincrona-retry-idempotencia-e-status
reviewed: 2026-11-16T00:00:00Z
depth: standard
files_reviewed: 25
files_reviewed_list:
  - backend/app/crud/social_accounts.py
  - backend/app/services/social/publish_pipeline.py
  - backend/tests/test_facebook_publisher.py
  - backend/tests/test_social_retry_policy.py
  - backend/tests/test_social_idempotency.py
  - backend/tests/test_social_publish_pipeline.py
  - backend/app/services/social/types.py
  - backend/app/services/social/facebook.py
  - backend/app/crud/social_posts.py
  - backend/tests/conftest.py
  - backend/tests/test_social_publisher.py
  - backend/tests/test_admin_social_publish.py
  - backend/tests/test_admin_social_retry_api.py
  - backend/tests/test_admin_social_status_api.py
  - backend/tests/test_social_worker_claim.py
  - backend/app/api/v1/admin.py
  - backend/app/schemas/social_posts.py
  - frontend/app/admin/social-posts/page.tsx
  - frontend/app/admin/social-posts/SocialPostsClient.tsx
  - frontend/lib/api.ts
  - frontend/app/admin/review/EditJobDialog.tsx
  - frontend/app/admin/review/ReviewQueue.tsx
  - frontend/components/admin/ReviewRow.tsx
  - frontend/app/admin/layout.tsx
  - frontend/app/admin/page.tsx
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 17: Code Review Report

**Reviewed:** 2026-11-16T00:00:00Z
**Depth:** standard
**Files Reviewed:** 25
**Status:** issues_found

## Summary

Reviewed the Phase 17 async social publishing, retry/idempotency, worker/status/retry API, and admin UI surfaces. The pipeline shows good intent around claim-before-send, safe user-facing messages, token non-persistence in memory flow, and idempotent/no-duplicate handling for ambiguous outcomes.

Key concerns found: (1) a claimed post can remain stuck in `publishing` if per-item processing crashes after the claim transaction commits, with no recovery path in this code; (2) several admin-facing Portuguese strings in the API are mojibake/corrupted, producing incorrect user-visible messages; (3) the admin social-posts listing endpoint ignores pagination parameters that the frontend client supports, creating a silent contract mismatch. No direct secret-exposure or injection issues were identified in the reviewed files.

## Warnings

### WR-01: Claimed post can remain stuck in `publishing` after processing crash

**File:** `backend/app/services/social/publish_pipeline.py:296-358`
**Issue:** `run_social_publish_cycle` commits claims in a separate transaction (`claimed_ids` persisted as `publishing`) and then processes each post in its own `session.begin()` block. If an exception escapes processing/commit (caught at line 354), the code only increments counters and logs; it does not transition the already-claimed post out of `publishing`, record a safe failure, or schedule recovery. A crash/DB error during `process_claimed_post` or commit can therefore leave the post permanently `publishing`, blocking automatic/manual progress and misrepresenting status to admins.
**Fix:**
```python
for pid in claimed_ids:
    try:
        async with async_session_factory() as session:
            async with session.begin():
                post = await get_social_post_by_id(session, pid)
                if post is None:
                    counters["skipped"] += 1
                    continue
                outcome = await process_claimed_post(session, post, settings=settings)
                counters["processed"] += 1
                # ... existing outcome accounting ...
    except Exception:
        logger.exception("social_publish_item_failed", extra={"social_post_id": str(pid)})
        try:
            async with async_session_factory() as recovery_session:
                async with recovery_session.begin():
                    post = await get_social_post_by_id(recovery_session, pid)
                    if post and post.status == SocialPostStatus.publishing and not post.external_post_id:
                        post.attempts = int(post.attempts or 0) + 1
                        await mark_failed(
                            recovery_session,
                            post,
                            attempts=post.attempts,
                            last_error=MSG_GENERIC_PROCESS,
                            next_retry_at=compute_next_retry(post.attempts, settings, now=_now()),
                            final=False,
                        )
                        await _append_log(
                            recovery_session,
                            post,
                            attempt_number=post.attempts,
                            result="failed_transient",
                            error_message=MSG_GENERIC_PROCESS,
                            response_summary="processing_exception_recovery",
                        )
        except Exception:
            logger.exception("social_publish_item_recovery_failed", extra={"social_post_id": str(pid)})
        counters["failed_final"] += 1
        counters["processed"] += 1
```
Adjust recovery policy (retryable vs final/ambiguous) to match project guarantees for crashes after claim; the key requirement is to never leave claimed items stuck in `publishing` silently.

### WR-02: Mojibake/corrupted Portuguese strings in admin API responses

**File:** `backend/app/api/v1/admin.py:144,147,168,189,200,418,446,510,562`
**Issue:** Multiple user-facing/admin-visible `detail` and message strings are corrupted (e.g. `"Vaga n?o encontrada"`, `"Vaga n?o est? na fila de revis?o"`, `"N?o foi poss?vel registrar o post social agora"`). These messages are returned to the frontend and surfaced in UI/toasts, resulting in incorrect Portuguese text and degraded admin UX. This indicates encoding corruption in source and can confuse operators during review/retry flows.
**Fix:**
```python
# Examples of corrected strings
raise HTTPException(status_code=404, detail="Vaga não encontrada")
raise HTTPException(status_code=409, detail="Vaga não está na fila de revisão")
message="Não foi possível registrar o post social agora"
raise HTTPException(status_code=409, detail="Texto aprovado e bloqueado para envio.")
```
Audit and replace all `n?o`, `est?`, `revis?o`, `poss?vel`, and similar corrupted sequences in this module with proper UTF-8 pt-BR text; save the file as UTF-8.

### WR-03: `list_social_posts` endpoint ignores pagination parameters exposed by client

**File:** `backend/app/api/v1/admin.py:306-315`, `frontend/lib/api.ts:732-746`
**Issue:** The frontend API helper `getAdminSocialPosts` accepts and sends `page`/`limit` query params, but the backend endpoint `GET /admin/social-posts` takes no pagination/filter parameters and always returns up to the CRUD default (200). This is a contract mismatch: callers may assume pagination works while the server silently ignores it, which can lead to incorrect UI behavior as data grows and makes future pagination changes error-prone.
**Fix:**
```python
@router.get("/social-posts", response_model=SocialPostStatusListResponse)
async def list_social_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialPostStatusListResponse:
    _ = claims
    account = await get_facebook_account(session)
    items = await list_social_status_items(
        session,
        account_status=_facebook_account_status_value(account),
        provider="facebook",
        limit=limit,
        # add offset support in CRUD/listing if page > 1 is required
    )
    # optionally return total/pages; keep response backward-compatible as needed
    return SocialPostStatusListResponse(items=items, total=len(items))
```
Alternatively, if pagination is intentionally out of scope, remove `page`/`limit` from `getAdminSocialPosts` and document the fixed-limit behavior to keep contract explicit.

## Info

### IN-01: Corrupted non-asserted seed strings in test fixtures

**File:** `backend/tests/conftest.py:389,410`
**Issue:** Fixture seed data contains mojibake text (`"Post falhou eleg?vel"`, `"Falha tempor?ria anterior"`, `"Post j? publicado"`). Current tests in scope do not assert these strings, so behavior is unaffected, but the corrupted literals reduce fixture readability and can cause confusion or brittle failures if future tests assert messages/titles.
**Fix:**
```python
text="Post falhou elegível",
last_error="Falha temporária anterior",
...
text="Post já publicado",
```
Save the file in UTF-8 and prefer ASCII-safe or correctly encoded pt-BR literals consistently.

### IN-02: Unused/partially redundant failure classification return path

**File:** `backend/app/services/social/publish_pipeline.py:82-97,241-293`
**Issue:** `_classify_failure` accepts `integration_blocked` and returns a third `ambiguous_or_blocked` value, but the call site after publisher execution always passes `integration_blocked=False` and integration-blocked cases are handled earlier. The extra parameter/return value is currently redundant and can mislead future changes about where blocked-integration semantics are applied.
**Fix:**
```python
def _classify_failure(category: PublishFailureCategory | None) -> tuple[str, bool]:
    if category == PublishFailureCategory.transient:
        return MSG_TRANSIENT, True
    if category == PublishFailureCategory.ambiguous:
        return MSG_AMBIGUOUS, False
    if category == PublishFailureCategory.permanent:
        return MSG_PERMANENT, False
    return MSG_PERMANENT, False

# caller:
safe_msg, retryable = _classify_failure(category)
```
Keep integration-blocked handling isolated in its existing branch (or refactor deliberately) so classification responsibilities are explicit.

---

_Reviewed: 2026-11-16T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
