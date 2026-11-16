---
phase: 16-geracao-revisao-e-aprovacao-do-post-social
reviewed: 2026-11-15T00:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - backend/.env.example
  - backend/app/api/v1/admin.py
  - backend/app/core/config.py
  - backend/app/crud/social_posts.py
  - backend/app/schemas/job.py
  - backend/app/schemas/social_posts.py
  - backend/app/services/social/__init__.py
  - backend/app/services/social/post_generation.py
  - backend/tests/conftest.py
  - backend/tests/test_admin_jobs.py
  - backend/tests/test_admin_social_posts.py
  - backend/tests/test_social_post_generation.py
  - backend/tests/test_social_post_policy.py
  - frontend/app/admin/review/EditJobDialog.tsx
  - frontend/app/admin/review/ReviewQueue.tsx
  - frontend/lib/api.ts
findings:
  critical: 0
  warning: 1
  info: 0
  total: 1
status: issues_found
---

# Phase 16: Code Review Report

**Reviewed:** 2026-11-15T00:00:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed the Phase 16 social post draft/review/approval implementation across backend config, schemas, CRUD, generation service, admin API, frontend admin UI, API client, and tests (16 files). The implementation generally enforces server-side content policy/sanitization, site-first approval behavior, frozen-draft guards, and actionable `SITE_PUBLIC_URL` errors as intended. One correctness issue was found in the admin draft-read path: persisted draft origin metadata is not preserved on GET, causing the UI to mislabel previously LLM-generated drafts as template fallback after reload.

## Warnings

### WR-01: GET social draft hardcodes `origin` to template fallback, misreporting saved drafts

**File:** `backend/app/api/v1/admin.py:255-273`, `backend/app/api/v1/admin.py:299-312`
**Issue:** `_draft_response()` defaults `origin="template_fallback"` and `get_job_social_post()` returns `_draft_response(post)` without passing the real origin. Because `SocialPost` persistence/response reconstruction does not supply generation provenance here, any saved draft fetched via `GET /admin/jobs/{job_id}/social-post` is reported as `origin: "template_fallback"` (and `warning: null`). The frontend uses `draft.origin` to render provenance chips/warnings (`"Gerado por IA"` vs `"Modelo padrão (fallback)"`), so reopening the dialog or reloading state can incorrectly tell the reviewer that an AI-generated draft came from fallback. This undermines review confidence and can drive unnecessary regeneration.

**Fix:**
```python
# Persist origin/warning with the draft (model + schema + CRUD), or derive accurately when possible.
# Example direction (requires schema/model support): include origin/warning in SocialPost and responses.

def _draft_response(
    post,
    *,
    origin: Literal["llm", "template_fallback"] | None = None,
    warning: str | None = None,
) -> SocialPostDraftResponse:
    frozen = post.status != SocialPostStatus.draft
    resolved_origin = origin or getattr(post, "origin", None) or "template_fallback"
    resolved_warning = warning if warning is not None else getattr(post, "warning", None)
    return SocialPostDraftResponse(
        job_id=post.job_id,
        provider="facebook",
        status=post.status.value,
        text=post.text,
        publish_mode=_draft_publish_mode(post),
        scheduled_at=post.scheduled_at,
        origin=resolved_origin,
        saved=True,
        frozen=frozen,
        warning=resolved_warning,
    )

@router.get("/jobs/{job_id}/social-post", response_model=SocialPostDraftResponse)
async def get_job_social_post(... ) -> SocialPostDraftResponse:
    ...
    post = await get_by_job_provider(session, job_id, provider="facebook")
    if post is None:
        raise HTTPException(status_code=404, detail="Rascunho social não encontrado")
    return _draft_response(post)  # should reflect stored origin/warning, not a hardcoded fallback
```
If provenance cannot be stored yet, avoid emitting a definitive fallback label on GET (e.g. make origin nullable/unknown in the contract and update UI accordingly) so the UI does not present incorrect information.

---

_Reviewed: 2026-11-15T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
