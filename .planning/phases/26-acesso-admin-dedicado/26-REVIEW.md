---
phase: 26-acesso-admin-dedicado
reviewed: 2026-11-22T00:00:00Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - frontend/app/(public)/privacidade/page.tsx
  - frontend/app/admin/layout.tsx
  - frontend/app/admin/login/page.tsx
  - frontend/app/admin/page.tsx
  - frontend/app/admin/paste/ExtractForm.tsx
  - frontend/app/admin/paste/page.tsx
  - frontend/app/admin/review/EditJobDialog.tsx
  - frontend/app/admin/review/ReviewQueue.tsx
  - frontend/app/admin/review/page.tsx
  - frontend/app/admin/social-posts/SocialPostsClient.tsx
  - frontend/app/admin/social-posts/page.tsx
  - frontend/components/admin/AdminChrome.tsx
  - frontend/components/admin/AdminGuard.tsx
  - frontend/components/admin/AdminLoginForm.tsx
  - frontend/components/admin/LogoutButton.tsx
  - frontend/lib/adminReturnTo.test.ts
  - frontend/lib/adminReturnTo.ts
  - frontend/scripts/verify-ssr.ps1
findings:
  critical: 0
  warning: 4
  info: 1
  total: 5
status: issues_found
---

# Phase 26: Code Review Report

**Reviewed:** 2026-11-22T00:00:00Z
**Depth:** standard
**Files Reviewed:** 18
**Status:** issues_found

## Summary

Reviewed the Phase 26 admin-access frontend files at standard depth, covering admin routing/layout, login/guard/session flow, paste/review/social-post admin screens, return-to sanitization, and the SSR verification script. No Critical security/data-loss defects were identified in the reviewed scope. The main gaps are inconsistent expired-session handling in the edit dialog, an overly permissive admin return-path boundary check, unvalidated external publication URLs rendered as links, and a PowerShell test-script error-handling bug that can mask failures.

## Warnings

### WR-01: Expired admin session is not redirected on EditJobDialog mutations

**File:** `frontend/app/admin/review/EditJobDialog.tsx:530-567,595-656`
**Issue:** `handleSubmit`, `handleGenerate`, and `handleSaveDraft` catch API errors and surface a generic toast/error message, but they do not detect `ApiError` 401 and call `handleAuthExpired()`. Other admin flows in the same file (`loadSocialStatus`, initial load effect, `handleRetrySocial`) and in adjacent admin screens redirect to `/admin/login?next=...` on 401. With an expired JWT, these three actions leave the admin on the dialog with a dead session and no recovery path, causing confusing repeated failures.
**Fix:**
```tsx
} catch (err) {
  if (err instanceof ApiError && err.status === 401) {
    handleAuthExpired();
    return;
  }
  const message = err instanceof Error ? err.message : "Erro ao salvar";
  toast(`Erro: ${message}`, "error");
} finally {
  setSaving(false);
}
```

Apply the same 401 guard in `handleGenerate` and `handleSaveDraft` before setting action-specific error/toast state.

### WR-02: `sanitizeAdminReturnTo` allows same-origin paths outside `/admin/*`

**File:** `frontend/lib/adminReturnTo.ts:23-36`
**Issue:** The sanitizer accepts any value whose trimmed string starts with `/admin`, then only rejects `//`, backslashes, control chars, and login-loop paths. This allows values like `/adminfoo`, `/administrator`, or other unintended same-origin paths to pass validation and be used by `router.replace(...)`. It is not an external open redirect, but it is a boundary-validation gap in a security-sensitive redirect helper.
**Fix:**
```ts
const pathname = getPathname(trimmed);
if (
  pathname !== "/admin" &&
  !pathname.startsWith("/admin/") &&
  pathname !== ADMIN_LOGIN_PATH
) {
  return null;
}

if (
  pathname === ADMIN_LOGIN_PATH ||
  pathname.startsWith(`${ADMIN_LOGIN_PATH}/`)
) {
  return "/admin";
}

return trimmed;
```

Add tests covering `/adminfoo` and `/administrator` as rejected inputs.

### WR-03: Publication URLs from API are rendered as unvalidated anchor hrefs

**File:** `frontend/app/admin/review/EditJobDialog.tsx:917-925`, `frontend/app/admin/social-posts/SocialPostsClient.tsx:220-229`
**Issue:** `socialStatus.published_url` / `item.published_url` are rendered directly into `<a href={...}>`. The value comes from API data; if it is malformed or contains an unsafe scheme, the UI will render a dangerous link. This is defense-in-depth: the backend should return trusted URLs, but the admin client should also enforce an `http:`/`https:` allowlist before rendering a clickable link.
**Fix:**
```tsx
function getSafeExternalUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}

const safePublishedUrl = getSafeExternalUrl(socialStatus.published_url);
{safePublishedUrl ? (
  <a href={safePublishedUrl} target="_blank" rel="noopener noreferrer">Ver post no Facebook</a>
) : (
  <p className="text-[14px] text-fg-muted">Publicado no Facebook. Link indisponível.</p>
)}
```

Apply the same guard in `SocialPostsClient`.

### WR-04: verify-ssr.ps1 masks unexpected success in limit-cap check

**File:** `frontend/scripts/verify-ssr.ps1:113-120`
**Issue:** The `limit=51` contract check throws `"Expected 422 for limit=51"` when the request unexpectedly succeeds, but that throw is caught by the same `catch` block. The catch then reads `$_.Exception.Response.StatusCode.value__`; for a plain thrown string/error with no HTTP response, this fails with a secondary PowerShell error and hides the real assertion. The script reports a confusing failure instead of the intended contract violation.
**Fix:**
```powershell
$got422 = $false
try {
    Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?limit=51" | Out-Null
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Assert ($status -eq 422) "Expected 422 for limit=51, got $status"
    $got422 = $true
}
Assert $got422 "Expected 422 for limit=51, but request succeeded"
```

## Info

### IN-01: Duplicate SITE_PUBLIC_URL error assignment in EditJobDialog

**File:** `frontend/app/admin/review/EditJobDialog.tsx:610-623`
**Issue:** When draft generation fails with a `SITE_PUBLIC_URL`/public-link error, the code computes `message` as `SITE_PUBLIC_URL_ERROR`, sets `socialActionError` to that message, then conditionally sets it to the same value again. The duplicate branch adds noise and makes the error path harder to read.
**Fix:**
```tsx
const raw = err instanceof ApiError ? err.message : "Não foi possível gerar o rascunho.";
const isSiteUrlIssue =
  raw.includes("SITE_PUBLIC_URL") || raw.includes("Link público indisponível");
const message = isSiteUrlIssue ? SITE_PUBLIC_URL_ERROR : raw;
setSocialActionError(message);
if (!isSiteUrlIssue) {
  toast(`Erro: ${message}`, "error");
}
```

---

_Reviewed: 2026-11-22T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
