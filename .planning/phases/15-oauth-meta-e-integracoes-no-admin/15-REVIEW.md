---
phase: 15-oauth-meta-e-integracoes-no-admin
reviewed: 2026-11-15T00:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - backend/alembic/versions/0005_social_oauth_pending.py
  - backend/app/api/v1/integrations.py
  - backend/app/api/v1/router.py
  - backend/app/models/__init__.py
  - backend/app/models/social_oauth_pending.py
  - backend/app/schemas/social_integrations.py
  - backend/app/services/social/meta_oauth.py
  - backend/tests/test_integrations_api.py
  - backend/tests/test_meta_oauth_flow.py
  - backend/tests/test_meta_oauth_security.py
  - backend/tests/test_meta_oauth_validation.py
  - frontend/app/admin/integracoes/IntegrationsClient.tsx
  - frontend/app/admin/integracoes/page.tsx
  - frontend/app/admin/layout.tsx
  - frontend/app/admin/page.tsx
  - frontend/lib/api.ts
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-11-15T00:00:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed the Meta/Facebook OAuth integration implementation across backend migration/model/schema/service/API, admin frontend UI/navigation, API client types, and new offline-oriented tests. The overall flow is directionally sound (signed state, encrypted pending payload/token handling, admin-guarded endpoints, safe redirect/error handling), but there is a concrete frontend/backend contract mismatch that can leave the integrations UI in an incomplete connected state after page selection, plus a UX edge case that can strand users in a pending-selection state and several quality issues in service/tests that reduce maintainability and test effectiveness.

## Warnings

### WR-01: Page-confirmation response contract mismatch drops connected-page details in UI

**File:** `frontend/lib/api.ts:547-562`, `frontend/app/admin/integracoes/IntegrationsClient.tsx:222-238`, `backend/app/api/v1/integrations.py:180-197`, `backend/app/services/social/meta_oauth.py:494-533`
**Issue:** `POST /api/v1/admin/integrations/meta/select-page` is declared to return `MetaActionResponse` (`status`, `message`, optional `pending_selection`) on the backend, but the frontend types `confirmMetaPageSelection` as returning `MetaIntegrationStatus` and immediately stores that response in UI state (`setStatus(nextStatus)`) without refreshing. After a successful confirmation, the UI will lack `provider/page_id/page_name/connected_at/token_checked_at/alert`, so the connected view can render placeholders (`—`) and lose context until a manual refresh/reload.
**Fix:**
```ts
// frontend/lib/api.ts
export async function confirmMetaPageSelection(
  token: string,
  payload: MetaSelectPageRequest,
): Promise<MetaIntegrationStatus | MetaActionResponse> {
  const res = await fetch(`${API}/api/v1/admin/integrations/meta/select-page`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as MetaIntegrationStatus | MetaActionResponse;
}
```

```tsx
// frontend/app/admin/integracoes/IntegrationsClient.tsx
const data = await confirmMetaPageSelection(token, payload);
if (isStatusPayload(data)) {
  setStatus(data);
} else {
  await refresh({ keepLoading: true });
}
setPendingPages([]);
setSelectedPageId("");
```

Alternatively (preferred for consistency), make the backend endpoint return `MetaIntegrationStatus` like `GET /meta/status` after a successful selection.

### WR-02: Pending selection cannot be recovered when backend reports pending state without a `pending` nonce in the URL

**File:** `frontend/app/admin/integracoes/IntegrationsClient.tsx:69-75`, `frontend/app/admin/integracoes/IntegrationsClient.tsx:121-136`, `frontend/app/admin/integracoes/IntegrationsClient.tsx:283-286`
**Issue:** The UI only loads pending pages when `pendingNonce` is present in the query string (`?pending=...`). If the user refreshes/navigates to `/admin/integracoes` without that param while `getMetaIntegrationStatus` returns `pending_selection: true`, `refresh()` clears local pending data and never enters the selection flow because `inSelectionFlow` also requires `pendingNonce`. This can strand the admin in a state where selection is pending server-side but not actionable from the UI until they restart OAuth or backend state expires.
**Fix:**
```tsx
// Option A (preferred): have backend status/pending endpoints expose a recoverable pending nonce/token-safe handle
// and have the client request pending pages using that handle when status.pending_selection is true.

// Option B: preserve pending nonce in client state once seen and avoid clearing it on plain refresh.
const [pendingNonceState, setPendingNonceState] = useState<string | null>(pendingNonce);
useEffect(() => {
  if (pendingNonce) setPendingNonceState(pendingNonce);
}, [pendingNonce]);

const effectivePendingNonce = pendingNonce ?? pendingNonceState;
const shouldLoadPending =
  (result === "select_page" && Boolean(effectivePendingNonce)) ||
  status.pending_selection; // requires a way to resolve the nonce when only status is known
```
At minimum, detect `status.pending_selection && !pendingNonce` and show an explicit recovery action/banner ("Seleção pendente encontrada. Reconecte para continuar.") instead of silently dropping into disconnected/normal states.

### WR-03: New Meta OAuth/integration tests contain placeholder or tautological assertions that do not verify the stated behavior

**File:** `backend/tests/test_meta_oauth_flow.py:236-277`, `backend/tests/test_meta_oauth_validation.py:119-160`, `backend/tests/test_integrations_api.py:129-135`
**Issue:** Several tests added in this change do not reliably assert the contracts their names describe. Examples: `test_single_page_auto_completes_and_multi_page_creates_pending_selection_contract` only checks attribute existence; `test_callback_multi_page_redirects_with_select_page_and_pending_nonce` accepts empty location and broad status ranges; `test_reconnect_replaces_existing_active_connection` does not exercise reconnect/replace behavior; `test_callback_and_confirm_validate_with_debug_token_before_persisting` asserts `"debug_token" in "debug_token"`; `test_oauth_callback_is_not_bearer_protected_but_validated_by_state` contains a tautological marker assertion. These tests can pass without validating regressions in OAuth flow, callback redirect contracts, or validation behavior.
**Fix:**
```python
# Example: make the callback contract test deterministic by mocking service outcome
@pytest.mark.asyncio
async def test_callback_multi_page_redirects_with_select_page_and_pending_nonce(client, monkeypatch):
    from app.api.v1 import integrations as integrations_api

    async def _fake_complete(*args, **kwargs):
        return {"result": "select_page", "pending_nonce": "opaque-nonce-123"}

    monkeypatch.setattr(integrations_api, "complete_oauth_callback", _fake_complete)

    resp = await client.get(
        "/api/v1/admin/integrations/meta/oauth/callback",
        params={"state": "s", "code": "c"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["location"] == "/admin/integracoes?result=select_page&pending=opaque-nonce-123"
```
Replace placeholder assertions with concrete mocked service interactions and exact status/redirect/body checks for each named contract.

## Info

### IN-01: `disconnect_meta` contains dead/no-op token-handling code before deleting the account

**File:** `backend/app/services/social/meta_oauth.py:398-412`
**Issue:** The function assigns `account.page_access_token` using an obfuscated `encrypt_token(... if False else account.page_access_token)` expression and then immediately deletes the account and flushes. The no-op assignment and misleading inline comment increase cognitive load and obscure the actual behavior (record removal).
**Fix:**
```python
async def disconnect_meta(session: AsyncSession) -> MetaActionResponse:
    stmt = select(SocialAccount).where(SocialAccount.provider == "facebook")
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    if account is not None:
        await session.delete(account)

    await session.execute(
        delete(SocialOAuthPending).where(SocialOAuthPending.provider == "facebook")
    )
    await session.flush()
    return MetaActionResponse(
        status="disconnected",
        message="Integração com Facebook desconectada.",
        pending_selection=False,
    )
```

### IN-02: Duplicated Meta integration TypeScript types increase drift risk with backend schemas

**File:** `frontend/lib/api.ts:452-494`
**Issue:** The API client defines `MetaIntegrationStatus`, `MetaPendingSelectionResponse`, `MetaActionResponse`, etc. locally while the backend also defines canonical Pydantic schemas. The current confirm-response mismatch (WR-01) shows these contracts can drift without a shared source or explicit alignment checks.
**Fix:**
```ts
// Keep a single source of truth for response/request shapes where possible.
// If codegen is not available, add a small contract note and align function return types
// to endpoint response_model values (e.g. select-page/verify/disconnect -> actual schema).
export type MetaIntegrationStatus = {
  provider: "facebook";
  status: "connected" | "needs_reconnect" | "disconnected";
  page_id: string | null;
  page_name: string | null;
  connected_at: string | null;
  token_checked_at: string | null;
  pending_selection: boolean;
  alert: { code: string; message: string } | null;
};
```
Consider generating frontend types from OpenAPI or centralizing API response typing helpers to prevent endpoint/type divergence.

### IN-03: Unused imports/locals in Meta OAuth service

**File:** `backend/app/services/social/meta_oauth.py:40-41`, `backend/app/services/social/meta_oauth.py:347-348`
**Issue:** `_safe_error` and `_SAFE_CALLBACK_ERROR` are defined but unused, and `_cleanup_facebook_connections` is defined but not referenced in the reviewed flow. These unused symbols add noise and make it harder to identify the active code paths during maintenance.
**Fix:**
```python
# Remove unused helpers/constants if not planned for immediate use, or wire them into the
# callback/error mapping paths they were intended to support.
# Example: delete `_safe_error`, `_SAFE_CALLBACK_ERROR`, and `_cleanup_facebook_connections`
# if they remain unused after this phase.
```

### IN-04: Test fixtures/helpers are duplicated across Meta OAuth/integration test modules

**File:** `backend/tests/test_integrations_api.py:12-95`, `backend/tests/test_meta_oauth_flow.py:17-95`, `backend/tests/test_meta_oauth_security.py:12-95`, `backend/tests/test_meta_oauth_validation.py:12-95`
**Issue:** The same dummy session/result, fake Turnstile verifier, app/client overrides, and login helper patterns are repeated in multiple test files. This duplication makes future contract changes error-prone and increases the chance that tests diverge in setup behavior.
**Fix:**
```python
# Move shared fixtures/helpers to backend/tests/conftest.py or a dedicated helper module.
# Example:
# - dummy_db_session fixture
# - app/client fixtures with dependency overrides
# - admin login helper
# Then keep each test file focused on scenario-specific assertions/mocks.
```

---
_Reviewed: 2026-11-15T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
