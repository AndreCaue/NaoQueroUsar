---
phase: 30-instagram-review-experience
reviewed: 2026-11-25T08:56:37Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - backend/alembic/versions/0007_instagram_review_social_post_publish_enabled.py
  - backend/tests/test_admin_instagram_social_posts.py
  - backend/app/models/social_post.py
  - backend/app/schemas/social_posts.py
  - backend/app/crud/social_posts.py
  - backend/app/services/social/post_generation.py
  - backend/app/api/v1/admin.py
  - frontend/lib/api.ts
  - frontend/app/admin/review/EditJobDialog.tsx
findings:
  critical: 0
  warning: 1
  info: 3
  total: 4
status: issues_found
---

# Phase 30: Code Review Report

**Reviewed:** 2026-11-25T08:56:37Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Reviewed the Phase 30 Instagram review/draft persistence slice across migration, model, schemas, CRUD, generation, admin API, frontend API, and the admin review dialog. The implementation is generally coherent: `publish_enabled` is persisted with a safe default, IG draft endpoints are isolated from Facebook, caption length and image-readiness guards are enforced on save and approve, and tests cover the main happy/guard paths.

One warning was found in the IG toggle flow where a failed auto-generate leaves the UI in an enabled-but-unsaveable state. Remaining findings are low-severity consistency/maintenance issues.

## Warnings

### WR-01: IG toggle stays enabled after auto-generate failure

**File:** `frontend/app/admin/review/EditJobDialog.tsx:903-913`, `frontend/app/admin/review/EditJobDialog.tsx:831-861`
**Issue:** When the admin enables "Publicar no Instagram desta vaga" for a job with no existing IG draft/caption, `handleIgToggle` optimistically sets `igEnabled(true)` and calls `handleIgGenerate(true)`, then returns. `handleIgGenerate` catches generation/save-validation failures and sets `igActionError`, but it never reverts `igEnabled`. If the backend rejects generation (for example, image/public media validation fails while publish is enabled), the toggle remains on with no draft and `igImageInvalid` true, so the IG save button is disabled. The user can recover by toggling off, but the UI state is inconsistent and confusing.

**Fix:**
```tsx
const handleIgGenerate = async (publishEnabledOverride?: boolean): Promise<SocialPostDraft | null> => {
  if (!token || !job || !igReady || igFrozen || busy || igBusy) return null;
  const publishEnabled = publishEnabledOverride ?? igEnabled;
  setIgAction("generate");
  setIgActionError(null);
  try {
    const draft = await generateInstagramSocialDraft(token, job.id, {
      publish_mode: "publish_now",
      publish_enabled: publishEnabled,
    });
    setIgDraft(draft);
    setIgCaption(draft.text ?? "");
    setIgEnabled(Boolean(draft.publish_enabled));
    setIgSaved(Boolean(draft.saved));
    if (draft.publish_enabled) {
      await prepareIgMedia(token, job.id);
    }
    return draft;
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      handleAuthExpired();
      return null;
    }
    setIgActionError(
      err instanceof ApiError
        ? err.message
        : "Não foi possível gerar a legenda do Instagram.",
    );
    return null;
  } finally {
    setIgAction(null);
  }
};

// In handleIgToggle, enable path with no draft:
setIgEnabled(true);
setIgSaved(false);
if (!igDraft && !igCaption.trim()) {
  const draft = await handleIgGenerate(true);
  if (!draft) {
    setIgEnabled(false);
  }
  return;
}
```

## Info

### IN-01: Duplicate Instagram caption length validation

**File:** `backend/app/api/v1/admin.py:785-786`, `backend/app/api/v1/admin.py:550-551`
**Issue:** `save_job_instagram_social_post` rejects captions over `IG_CAPTION_MAX_CHARS` before calling `_validate_instagram_publish_ready`, which performs the same length check again. The duplicate check is harmless but adds maintenance noise and can drift if the rule/message changes.
**Fix:** Keep the length check in one place. Either remove the pre-check in the save endpoint and rely on `_validate_instagram_publish_ready`, or make the helper responsible only for image-readiness validation and keep length validation at the endpoint boundary.

### IN-02: Approve endpoint drops specific Instagram image validation message

**File:** `backend/app/api/v1/admin.py:186-193`, `backend/app/api/v1/admin.py:553-558`
**Issue:** During approve, invalid IG media returns a fixed generic detail string. The save/generate validation path uses `result.validation.message or IG_IMAGE_INVALID_DETAIL`, which preserves the specific reason from `prepare_instagram_media` (missing image, invalid public URL, not ready, etc.). The less specific approve message makes admin recovery harder.
**Fix:**
```python
ig_media = await prepare_instagram_media(session, job_id, settings=settings)
if not ig_media.validation.valid:
    raise HTTPException(
        status_code=422,
        detail=(
            f"{ig_media.validation.message or IG_IMAGE_INVALID_DETAIL} "
            "Corrija ou desative a publicação no Instagram desta vaga para aprovar. "
            "O Facebook e o site não são bloqueados."
        ),
    )
```

### IN-03: Toggle-off media reset is optimistic and causes unnecessary re-prepare on failure

**File:** `frontend/app/admin/review/EditJobDialog.tsx:949-979`, `frontend/app/admin/review/EditJobDialog.tsx:569-576`
**Issue:** When disabling IG publication for an existing draft, the UI clears `igMedia`/`igMediaError` before persisting `publish_enabled=false`. If the save fails, the code restores `igEnabled(true)` but does not restore prior media state. The auto-prepare effect then re-runs and issues another prepare request. This is self-healing, but it adds avoidable work and transient UI churn.
**Fix:** Capture previous media/mediaError before clearing, or only clear them after a successful disable save. For example:

```tsx
const previousMedia = igMedia;
const previousMediaError = igMediaError;
setIgEnabled(false);
setIgSaved(false);
setIgMedia(null);
setIgMediaError(null);
// ...on error:
setIgEnabled(true);
setIgMedia(previousMedia);
setIgMediaError(previousMediaError);
```

---

_Reviewed: 2026-11-25T08:56:37Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
