---
phase: 05-admin-review-area
reviewed: 2026-10-28T00:20:30Z
depth: standard
files_reviewed: 20
files_reviewed_list:
  - backend/app/api/v1/admin.py
  - backend/app/crud/jobs.py
  - backend/app/schemas/job.py
  - backend/tests/test_admin_jobs.py
  - frontend/app/admin/admin.css
  - frontend/app/admin/layout.tsx
  - frontend/app/admin/page.tsx
  - frontend/app/admin/paste/ExtractForm.tsx
  - frontend/app/admin/paste/page.tsx
  - frontend/app/admin/review/DeleteConfirmDialog.tsx
  - frontend/app/admin/review/EditJobDialog.tsx
  - frontend/app/admin/review/ReviewQueue.tsx
  - frontend/app/admin/review/page.tsx
  - frontend/components/admin/AdminGuard.tsx
  - frontend/components/admin/CityChips.tsx
  - frontend/components/admin/LogoutButton.tsx
  - frontend/components/admin/ReviewRow.tsx
  - frontend/components/admin/ToastProvider.tsx
  - frontend/components/admin/icons.tsx
  - frontend/lib/api.ts
findings:
  critical: 3
  warning: 12
  info: 11
  total: 26
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-10-28T00:20:30Z
**Depth:** standard
**Files Reviewed:** 20
**Status:** issues_found

## Summary

Phase 05 delivers a working admin review area: five JWT-guarded FastAPI routes, matching CRUD helpers, an admin-only `JobAdmin` schema, and a Next.js review queue with optimistic mutations, city filter, pagination and two native `<dialog>`s. The broad architecture is sound — every admin route carries `require_admin`, no query is string-interpolated, `JobPublic` still structurally cannot leak contact data, and the code type-checks (`tsc --noEmit` clean) and the backend suite is green (I ran it: **14/14 passed**, contrary to the SUMMARY claim of 13/14).

The defects are in the details: one dialog-state bug that silently resurrects discarded edits, a logout that does not log out, plaintext admin credentials left in the working tree, and a layer of backend validation that is documented but not actually wired (dead `classmethod`s, blanket `IntegrityError` mapping, fail-open city filter). Optimistic rollback exists on paper but is superseded by an immediate refetch, so the "restore snapshot" mitigation (T-05-11) does not actually protect the UI when the refetch also fails.

**Cross-cutting note:** the phase SUMMARYs are not reliable evidence. `05-01-SUMMARY.md` claims `test_list_city_filter` is a known failing stub caused by "transaction rollback behaviour" (lines 64-68, 129-133); the test passes today and the same seed-then-`flush()` pattern is used by every other passing test, so the stated cause cannot be right. It also claims 422 handling for "invalid status" is verified — no test exercises it.

## Critical Issues

### CR-01: Edit dialog never resets when the same job is reopened — cancelled edits come back

**File:** `frontend/app/admin/review/EditJobDialog.tsx:173-181` (with `frontend/app/admin/review/ReviewQueue.tsx:316-319, 354-359`)
**Issue:** The form is reset by an effect keyed on the `job` **object identity**, not on `job.id`:

```tsx
const [form, setForm] = useState<FormState>(() => toFormState(job));
useEffect(() => { setForm(toFormState(job)); setErrors({}); }, [job]);
```

`ReviewQueue` keeps `selectedJob` alive after close (`onClose={() => setEditOpen(false)}`) and re-opens it with the *same* object reference (`setSelectedJob(job)` where `job` comes from `items`). React bails out on the identical reference, so the `[job]` effect does not re-run and the form keeps the edits the admin just discarded.

Repro: Editar vaga A → change the contact phone to an unreviewed value → **Cancelar** → Editar vaga A again → the discarded phone (and every other abandoned change) is still in the form → "Salvar alterações" persists it. The header subtitle (`job.title`) still shows the original value while the form shows the edited one, which makes the mismatch easy to miss.

This violates the explicit contract in `05-UI-SPEC.md:335` and `05-04-PLAN.md:124` ("Reset form state quando `job.id` muda"). It is not a hypothetical: reopen-after-cancel is the normal way an admin double-checks a card.

**Fix:**
```tsx
// key on the id, and reset on open as well, so Cancelar really discards
useEffect(() => {
  if (!open) return;
  setForm(toFormState(job));
  setErrors({});
}, [job?.id, open]);

// and/or force a remount from the parent:
<EditJobDialog key={selectedJob?.id ?? "none"} ... />
```

### CR-02: "Sair" on `/admin/paste` does not end the session

**File:** `frontend/components/admin/LogoutButton.tsx:11-19` interacting with `frontend/app/admin/paste/ExtractForm.tsx:19-37, 138-155`
**Issue:** `ExtractForm` holds the JWT in its own component state (`const [token, setToken] = useState<string | null>(null)`), hydrated once from `sessionStorage`. The logout button deletes only the storage entry and then calls `router.replace("/admin/paste")` — the route the user is already on. Nothing clears `ExtractForm`'s `token` state and the component is not remounted, so after clicking **Sair**:

- the authenticated "Extrair vagas" UI stays on screen;
- `extractJobs(token, …)` keeps working with the still-valid 12 h JWT (the backend has no revocation and the token is still in memory);
- only a manual page reload actually logs the admin out.

On the paste page — the admin entry point — "Sair" is therefore a functional no-op for the live session. That is a security-relevant correctness defect (shared machine, admin panel can mutate/delete public job data).

**Fix:** centralise the token (context or a `key` on the page) and clear it on logout, then hard-navigate. Minimal version:
```tsx
const handleLogout = () => {
  sessionStorage.removeItem(TOKEN_KEY);
  // remount the admin tree so no component keeps the token in state
  window.location.replace("/admin/paste");
};
```
The durable fix is a single `AdminAuthProvider` that owns `token` + `logout()` and is consumed by `ExtractForm`, `useAdminGuard` and `EditJobDialog`.

### CR-03: Plaintext admin password and debug dumps left in the backend working tree

**File:** `backend/body.json` (untracked), plus `backend/_admin.txt`, `backend/_auth.txt`, `backend/_config.txt`, `backend/_deps.txt`, `backend/_router.txt`, `backend/_sec.txt`, `backend/debug_test.py`
**Issue:** `git status` reports all of these as untracked (`??`) — i.e. **not ignored** — and `backend/body.json` contains:

```json
{"password": "senhaAdmin"}
```

These are leftovers from debugging this phase's login flow. A routine `git add -A` / `git commit -a` would commit a plaintext admin credential and a dump of the settings/auth modules. `backend/debug_test.py` is also broken (`FastAPI(...)` is used without an import), so it is not a runnable artefact anyone would notice.

**Fix:**
1. Delete them: `Remove-Item backend\_*.txt, backend\body.json, backend\debug_test.py`.
2. If `senhaAdmin` is (or ever was) the real admin password, rotate `ADMIN_PASSWORD_HASH`/password now — it has been written to disk in clear text.
3. Extend `.gitignore` with `backend/_*.txt`, `backend/body.json`, `backend/debug*.py` so ad-hoc debugging cannot leak again.

## Warnings

### WR-01: `JobUpdate`'s city/contact validators are dead code; docstring claims validation that does not exist

**File:** `backend/app/schemas/job.py:112-158` (and unused import at `:23`)
**Issue:** `_resolve_city` and `_validate_at_least_one_contact` are declared as bare `@classmethod`s — no `@field_validator` / `@model_validator` decorator — so Pydantic never calls them. Meanwhile the docstring asserts "City validation against allowed set is enforced via Literal (fails fast before DB)" and `Literal` is imported but never used. `05-01-PLAN.md:129` explicitly required `model_validator(mode="after")`; that requirement is unmet.

Contact validation survives only because the DB `CHECK at_least_one_contact` fires; city validation survives only because the router patches `payload.city` after construction. Any future caller of `JobUpdate`/`update_job` (e.g. a bulk importer) silently gets no validation, and a maintainer reading the schema will believe it is safe.

**Fix:**
```python
from pydantic import Field, field_validator, model_validator

city: str | None = Field(default=None, max_length=80)

@field_validator("city")
@classmethod
def _resolve_city(cls, value: str | None) -> str | None:
    if value is None:
        return None
    resolved = _CITY_ALIASES.get(value.strip().lower())
    if resolved is None:
        raise ValueError("Cidade inválida")
    return resolved

@model_validator(mode="after")
def _at_least_one_contact(self):
    if "contact_email" in self.model_fields_set or "contact_phone" in self.model_fields_set:
        if not (self.contact_email or "").strip() and not (self.contact_phone or "").strip():
            raise ValueError("Vaga precisa ter ao menos um contato (email ou telefone)")
    return self
```
Then delete the router-side city patch (`admin.py:126-131`) or keep it as a belt-and-braces check, and drop the unused `Literal` import.

### WR-02: Every `IntegrityError` on update is reported as "missing contact"

**File:** `backend/app/api/v1/admin.py:132-140` (schema allowing the bad inputs: `backend/app/schemas/job.py:124,130`)
**Issue:** The `except IntegrityError` block assumes the only possible constraint failure is `at_least_one_contact`. But `JobUpdate` also accepts `title: null`, `title: "   "`, `city: null` and over-length values that the model column rejects. Verified paths:

- `PUT {"title": null}` → NOT NULL violation → 422 *"Vaga precisa ter ao menos um contato"* (wrong);
- `PUT {"title": "   "}` → `title_not_blank` CHECK → same wrong message;
- `PUT {"city": null}` → NOT NULL violation → same wrong message.

The admin is told to fix the contact when the real problem is the title/city, and the message is generated by a DB constraint rather than the schema.

**Fix:** validate at the schema (WR-01) so these never reach the DB, require `title` to be non-blank (`Field(min_length=1)` + strip validator, reject `None` when the field is present), and narrow the DB error mapping by constraint name:
```python
except IntegrityError as exc:
    await session.rollback()
    if "at_least_one_contact" in str(exc.orig):
        raise HTTPException(
            status_code=422,
            detail="Vaga precisa ter ao menos um contato (email ou telefone)",
        )
    raise HTTPException(status_code=422, detail="Dados inválidos para a vaga") from exc
```

### WR-03: No server-side validation of `contact_email` / `contact_phone`

**File:** `backend/app/schemas/job.py:131-132`
**Issue:** Only `max_length` is enforced. `{"contact_email": "lixo"}` or `{"contact_phone": "abc"}` is accepted and written to the DB; that value is then returned by the public reveal endpoint (`ContactRevealResponse`) and rendered as a `mailto:`/`wa.me` link. The only format validation in the system lives in `EditJobDialog.tsx:216-221` — a client-side check that any direct API call bypasses.

**Fix:** use `EmailStr` (email-validator is already a FastAPI dep) or an explicit validator, and validate the phone (E.164/at least N digits) before persisting — the extraction pipeline already produces E.164, so the admin surface should not be looser than the importer.

### WR-04: Unknown `city` on the admin list fails open (returns every city)

**File:** `backend/app/api/v1/admin.py:54` + `backend/app/api/v1/public.py:40-44`
**Issue:** `_resolve_city` returns `None` for anything outside the alias table, and `list_jobs` passes that straight to `list_by_status`, which then applies **no** city filter. `GET /admin/jobs?city=curitiba` returns the full pending queue with `200`, indistinguishable from "filter cleared". For the public endpoint this is documented, correct behaviour; for an admin filter it silently lies about the result set. `05-01-SUMMARY.md:133` goes further and claims "422 rejection for unknown cities" — no such path exists.

**Fix:** reject unknown values in the admin route:
```python
resolved_city = None
if city:
    resolved_city = _resolve_city(city)
    if resolved_city is None:
        raise HTTPException(status_code=422, detail="Cidade inválida")
```

### WR-05: Approve has no status precondition and does not touch `expires_at`

**File:** `backend/app/api/v1/admin.py:94-107`, `backend/app/crud/jobs.py:133-137`
**Issue:** `approve_job` sets `status = published` unconditionally. Two consequences:

1. The documented contract ("pending/needs_review → published") is not enforced: an already-published (or `invalid`) row is silently "approved" again with `200`. There is no 409/422 for a row that is not in a reviewable state.
2. `expires_at` is never refreshed. `expires_at` is seeded at insert time as `now() + 14 days` (`models/job.py:61-65`) and the admin list deliberately has no expiry filter (`05-RESEARCH.md` A6), so a job that sat in the queue for more than 14 days can be approved into `published` with `expires_at` already in the past. `GET /public/jobs` filters `expires_at > now()`, so the job is invisible forever while the UI shows **"Vaga aprovada e publicada."** — i.e. the toast lies.

Lifecycle work is deferred to Phase 6, but this is the one Phase-5-driven way to create an invisible published row; it should either refresh `expires_at` on approve or be written down as a hard prerequisite for Phase 6.

**Fix:**
```python
if job.status not in (JobStatus.pending, JobStatus.needs_review):
    raise HTTPException(status_code=409, detail="Vaga não está na fila de revisão")
job.status = JobStatus.published
job.expires_at = datetime.now(timezone.utc) + timedelta(days=14)
await session.flush()
```

### WR-06: API error extraction discards FastAPI's validation payloads, and 401 is indistinguishable

**File:** `frontend/lib/api.ts:284-319, 322-342, 345-369, 372-390`
**Issue:** All five helpers use the same block:
```ts
const body = await res.json();
if (body && typeof body.detail === "string") detail = body.detail;
```
FastAPI returns `detail` as an **array** for `RequestValidationError` (invalid UUID, `title` > 200 chars, `contact_email` > 254, `benefits` > 255, wrong body shape). Those requests therefore surface as the generic `"Erro 422"` — the admin cannot tell which field is wrong, and there is no client-side `maxLength` mirroring the schema (`EditJobDialog.tsx:83-91, 120-127`). A 401 is also flattened into a plain `Error`, so no helper can trigger a re-login (see WR-07).

**Fix:**
```ts
async function readError(res: Response): Promise<string> {
  const fallback = `Erro ${res.status}`;
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      return body.detail.map((d: any) => `${d.loc?.slice(1).join(".")}: ${d.msg}`).join("; ");
    }
  } catch { /* non-JSON */ }
  return fallback;
}
// and surface status so callers can do: if (err.status === 401) logout();
```

### WR-07: Token handling is duplicated and validity is never checked

**File:** `frontend/components/admin/AdminGuard.tsx:16-34`, `frontend/app/admin/paste/ExtractForm.tsx:7, 28-37`, `frontend/components/admin/LogoutButton.tsx:13`, `frontend/app/admin/review/EditJobDialog.tsx:10, 52-58`
**Issue:** The literal `"nqu_admin_token"` appears in four files (three exports of `TOKEN_KEY` plus a hard-coded string in `LogoutButton`), and `EditJobDialog` re-reads `sessionStorage` itself instead of receiving the token from `useAdminGuard`/props. Separately, the guard only checks *presence*: after the 12 h JWT expires, `/admin/review` renders, the fetch 401s, and the queue shows "Não foi possível carregar a fila: Não autenticado" with a "Tentar novamente" button that can never succeed — there is no redirect back to login and no automatic sign-out. The only escape is the header's "Sair", which (CR-02) is unreliable on the paste page.

**Fix:** export `TOKEN_KEY` from one module (or a small `lib/auth.ts`), pass `token` into `EditJobDialog`, and treat 401 as a session end: clear the token and `router.replace("/admin/paste")` (optionally validating the stored token once via `/api/v1/admin/me`, which already exists and is currently unused by the frontend).

### WR-08: `AdminGuard` component is dead code that guards nothing

**File:** `frontend/components/admin/AdminGuard.tsx:36-40`
**Issue:**
```tsx
export function AdminGuard({ children }: { children: ReactNode }) {
  useAdminGuard();
  return <>{children}</>;
}
```
The docstring says it "renders children only after the guard effect runs", but children render unconditionally on the first paint (the hook's redirect is async, and no gating value is used). A future author who wires `AdminGuard` into a layout expecting protection gets none. It is also currently unreferenced (`grep` shows only the hook is used).

**Fix:** either delete it, or gate for real:
```tsx
export function AdminGuard({ children, fallback = null }: { children: ReactNode; fallback?: ReactNode }) {
  const token = useAdminGuard();
  return token ? <>{children}</> : <>{fallback}</>;
}
```

### WR-09: Toast implementation deviates from its own spec and is not dismissible

**File:** `frontend/components/admin/ToastProvider.tsx:29-31, 47-58, 60-83`
**Issue:** `05-UI-SPEC.md:212, 351-353` requires a manual `×` button (`aria-label="Fechar notificação"`), hover-pauses the timer, a 3 px coloured left border + icon per variant, and desktop placement bottom-right. The implementation:

- has **no dismiss control at all** (`dismiss`/`dismissAll` are exposed in the context but no UI consumes them);
- auto-dismisses at 3 s unconditionally — no hover/focus pause, which is the WCAG 2.2.1 (Timing Adjustable) failure mode for error text the admin must read and act on;
- renders errors with `role="status"` (polite) instead of `role="alert"`, so a failed approve/delete may not be announced promptly;
- is always bottom-center and has no icon / no 4 px left border per variant;
- schedules `window.setTimeout` with no cleanup, so timers outlive the provider on unmount.

**Fix:** add the `×` button wired to `dismiss(id)`, pause the timer on `onMouseEnter`/`onFocus` (store the timeout handle in a ref per toast), and use `role="alert"` for `variant === "error"`.

### WR-10: Edit dialog puts focus on the dialog, not the first field

**File:** `frontend/app/admin/review/EditJobDialog.tsx:183-192`
**Issue:** `dialog.showModal(); dialog.focus();` moves focus to the `<dialog tabIndex={-1}>` element. `05-UI-SPEC.md:335` requires "foco vai para o primeiro campo (`title`)". A keyboard/screen-reader user lands on an unnamed container and must Tab through the header before reaching the form; the dialog also has `aria-labelledby` only, so the initial announcement is thin.

**Fix:**
```tsx
useEffect(() => {
  const dialog = dialogRef.current;
  if (!dialog) return;
  if (open && !dialog.open) {
    dialog.showModal();
    titleInputRef.current?.focus();   // ref on the "Título" input
  } else if (!open && dialog.open) {
    dialog.close();
  }
}, [open]);
```

### WR-11: Optimistic rollback is superseded by the refetch — the snapshot does not protect the UI

**File:** `frontend/app/admin/review/ReviewQueue.tsx:132-159, 161-187, 62-97`
**Issue:** On failure both mutation handlers do:
```tsx
setItems(snapshot);
setTotal(previousTotal);
reload();            // -> setRefreshKey -> effect -> setLoading(true) -> refetch
```
The restored snapshot is immediately replaced by the loading skeleton and then by the server response, so the snapshot restore is decorative. If the refetch itself fails (the same network outage that broke the mutation), the fetch effect's `catch` runs `setItems([])` and sets `error`, so the queue is blanked and the admin loses the row they were working on — exactly the state T-05-11 ("Snapshot + rollback + refetch") claims to prevent. There is also no per-mutation in-flight guard, so two approvals in flight each capture a pre-mutation `snapshot`; if the first fails, restoring it re-adds the row the second just deleted.

**Fix:** make rollback the source of truth and refetch only after it succeeds:
```tsx
catch (err) {
  setItems(snapshot);
  setTotal(previousTotal);
  setCounts(previousCounts);
  toast(`Erro: ${message}`, "error");
  return;                     // no reload(): the snapshot IS the recovery
}
// on success: reload() to resync total/pagination
```
and skip a mutation whose id is already pending (a `Set<string>` ref of in-flight ids).

### WR-12: Test suite is green but does not cover what the SUMMARY claims it covers

**File:** `backend/tests/test_admin_jobs.py` (whole file)
**Issue:** I ran `python -m pytest tests/test_admin_jobs.py -q` → **14 passed** in 75 s. That contradicts `05-01-SUMMARY.md` (13/14, "test_list_city_filter" a known stub, "code is correct, verified by the 13 passing tests"). The claimed root cause ("transaction rollback behaviour") cannot explain a city-specific failure — every other test uses the identical `db_session.add(...)` + `flush()` + API-call pattern. The SUMMARY is not evidence.

Beyond the inaccurate narrative, these behaviours ship untested:

| Untested behaviour | Risk |
|---|---|
| `status` not in `{pending, needs_review}` → 422 (`admin.py:52`) | SUMMARY claims it is verified |
| `sort=antigas` ordering / id tie-break (`crud/jobs.py:109-111`) | REVW-01 sort is unverified |
| `PUT` cannot change `status` (extra field ignored) | silently different from the TS type (IN-04) |
| `PUT {"title": null}` / `{"title": "  "}` / `{"city": null}` | currently returns a misleading contact 422 (WR-02) |
| approve on non-reviewable status, and `expires_at` after approve | WR-05 |
| `GET /admin/jobs/{id}` without a token | `test_requires_auth` claims "all routes" but omits it |
| unknown `city` filter | WR-04 |

`_login` also hard-asserts `body["expires_in"] == 43200` (`:34`), coupling the suite to the JWT lifetime configuration.

**Fix:** add the missing cases (one test each; the existing fixtures make them cheap), delete the "known stub" paragraph from the SUMMARY, and assert `expires_in > 0` rather than the literal 43200.

## Info

### IN-01: Unused import, private cross-module coupling, duplicated alias table

**File:** `backend/app/api/v1/admin.py:10`, `backend/app/schemas/job.py:139-149`
**Issue:** `_CITY_ALIASES` is imported and never used (only `_resolve_city` is). The admin router reaches into another router module for a *private* helper (`app.api.v1.public._resolve_city`), and `JobUpdate` carries a third copy of the same alias table.
**Fix:** move `_CITY_ALIASES`/`resolve_city` into `app/services/cities.py` (or `app/core/cities.py`) and import it from both routers; drop the unused import.

### IN-02: Stale docstring in `me()`

**File:** `backend/app/api/v1/admin.py:15-27`
**Issue:** "The full admin review routes (list/approve/edit/delete) belong to Phase 5 — do NOT add them here." They are now added directly below.
**Fix:** trim the docstring to describe `/admin/me` only.

### IN-03: `DeleteConfirmDialog.loading` is never supplied

**File:** `frontend/app/admin/review/DeleteConfirmDialog.tsx:11, 21-29` / `ReviewQueue.tsx:361-365`
**Issue:** The public `loading` prop is dead — the parent never passes it; the internal `deleting` flag is what actually drives "Excluindo...". Two sources of truth for one state.
**Fix:** remove `loading` from the props (or have `ReviewQueue` pass its own `deleting` state and drop the internal one).

### IN-04: TS `JobUpdate` advertises fields the backend ignores

**File:** `frontend/lib/api.ts:51-63`
**Issue:** `status?: JobStatus` and `source_snippet?: string | null` are declared, but `JobUpdate` on the backend has neither field and Pydantic's default `extra="ignore"` silently drops them. A future caller sending `status: "published"` gets a 200 with the status unchanged.
**Fix:** delete both fields from the interface (or add them server-side with explicit handling).

### IN-05: Tab counts mix filtered and global numbers; tab copy/visual differs from the spec

**File:** `frontend/app/admin/review/ReviewQueue.tsx:78, 100-118, 265-285`
**Issue:** The active tab's badge is set from the **city-filtered** `result.total`, while the inactive tab's badge is fetched without a city filter. The label "Pendentes (N)" therefore means two different things depending on which tab is selected. Also `05-UI-SPEC.md:313` specifies the labels "Pendentes"/"Precisam correção" and a filled `#7c3aed` active tab; the code uses "Necessita revisão" and an underline.
**Fix:** either apply `city` to both count queries, or label the badge as filtered; align copy/visuals with the UI-SPEC.

### IN-06: Skeleton and tablist accessibility gaps

**File:** `frontend/app/admin/review/ReviewQueue.tsx:199-208, 260-286`
**Issue:** `05-UI-SPEC.md:320` requires an `sr-only` "Carregando fila"; only `aria-busy`/`aria-live` are present. `role="tab"` buttons have no `aria-controls` pointing at a `role="tabpanel"` and the list is not wrapped in one, so screen readers announce tabs with no associated panel.
**Fix:** add `<span className="sr-only">Carregando fila</span>`, give the list `role="tabpanel" id="review-panel"` + `aria-labelledby`, and reference it from each tab.

### IN-07: City slug matching has no accent folding

**File:** `frontend/app/admin/review/EditJobDialog.tsx:28-36`
**Issue:** `slugFromCanonical` compares `toLowerCase()` only, while `lib/cities.ts` already exports a `fold()`-based matcher (`cityLabel`). A row stored as "Sao Paulo" (unaccented) or any city outside `CITY_OPTIONS` yields `citySlug: ""`, and `validate()` then blocks saving *any* field ("Selecione uma cidade") until the admin changes the city.
**Fix:** reuse the shared folding helper, and if no option matches, surface the raw value as a selectable "current" entry instead of forcing a change.

### IN-08: `invalid` jobs would be labelled "Pendente"

**File:** `frontend/components/admin/ReviewRow.tsx:58-59`
**Issue:** `statusLabel` is a binary `needs_review ? … : "Pendente"`, so `published` or `invalid` rows render as "Pendente". Today `invalid` is never persisted (`extract.py:45-46`), but the component is a shared review primitive.
**Fix:** map all four `JobStatus` values explicitly.

### IN-09: `sort` unvalidated, `page` unbounded

**File:** `backend/app/api/v1/admin.py:39-41`
**Issue:** `sort` accepts any string ≤ 20 chars and silently falls back to `recentes` (unlike `status`, which 422s) — inconsistent. `page` has no upper bound, so `page=1000000` builds a very large `OFFSET`.
**Fix:** validate `sort` with `Literal["recentes","antigas"]` (or reuse `_resolve_sort`) and cap `page`.

### IN-10: Two guards on the review route

**File:** `frontend/app/admin/review/page.tsx:7` + `frontend/app/admin/review/ReviewQueue.tsx:38`
**Issue:** `useAdminGuard()` runs twice for one route (two `sessionStorage` reads, two effects, two potential redirects). Harmless but redundant, and it masks the fact that the guard provides no gating (WR-08).
**Fix:** keep the guard in one place (the page) and pass `token` down, or move it into the layout.

### IN-11: Brittle auth test shape

**File:** `backend/tests/test_admin_jobs.py:411-443`
**Issue:** The PUT/DELETE 401 assertions send **no body**, relying on Starlette resolving the security dependency before body validation; a FastAPI change could turn these into 422s. `GET /admin/jobs/{id}` and `/admin/me` are not covered at all despite the docstring saying "All admin job routes".
**Fix:** send a valid body with invalid/missing credentials, and add the two omitted routes.

---

_Reviewed: 2026-10-28T00:20:30Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_

---

## Post-review resolution

The frontmatter above is the review snapshot (`issues_found`). The findings
below were addressed in `804b550` (backend) and the follow-up frontend commit;
this section records what changed and what remains.

| Finding | Resolution |
|---|---|
| CR-01 | `EditJobDialog` resets on `[job, open]` and focuses the title input on open. |
| CR-02 | `LogoutButton` clears `TOKEN_KEY` and hard-navigates, killing in-memory tokens. |
| CR-03 | Debug dumps (`backend/_*.txt`, `body.json`, `debug_test.py`) deleted. If `senhaAdmin` was ever a real credential, rotate it. |
| WR-01/WR-03 | `JobUpdate` validators are wired: title/city/email/phone, blank-city and both-contacts-cleared rejection. |
| WR-02 | Only the contact CHECK maps to the contact message; other `IntegrityError`s return "Dados inválidos". |
| WR-04 | Unknown admin city filter → 422 (fail closed). |
| WR-05 | Approve requires `pending`/`needs_review` (409) and refreshes `expires_at` to now + 14 days. |
| WR-06 | `readError` flattens FastAPI validation arrays; `ApiError` keeps the status. Client `maxLength` mirrors `JobUpdate`. |
| WR-07 | Single `TOKEN_KEY` in `lib/auth.ts`; `EditJobDialog` receives the token by prop; a 401 clears the token and returns to `/admin/paste`. |
| WR-08 | Dead `AdminGuard` component removed. |
| WR-09 | Toast has a dismiss button, `role="alert"` for errors, hover/focus pause and timer cleanup on unmount. |
| WR-10 | Edit dialog focuses the first field. |
| WR-11 | Optimistic rollback restores list/total/badges without a refetch; mutations are serialized via a ref. |
| WR-12 | Tests extended to 20: invalid status/city, sort, approve 409/TTL, blank title, detail + `/admin/me` auth, `expires_in > 0`. |
| IN-01/IN-02 | Shared `app/services/cities.py`; stale docstrings trimmed. |
| IN-03/IN-04 | Dead `loading` prop and unknown `JobUpdate` fields removed. |
| IN-05/IN-06 | Counts respect the city filter; labels/active tab aligned to the UI-SPEC; `sr-only` loading + `tabpanel` wiring. |
| IN-07 | Accent-folding city match; a legacy city outside `CITY_OPTIONS` no longer blocks unrelated edits. |
| IN-08 | All four `JobStatus` labels mapped. |
| IN-09 | `sort: Literal["recentes","antigas"]`, `page <= 10_000`. |
| IN-10/IN-11 | One guard on the review route; auth test covers detail + `/admin/me`. |

Verification after the fixes: backend `pytest -q` → 215 passed / 3 skipped;
`frontend` `tsc --noEmit` clean and `next build` succeeds.

