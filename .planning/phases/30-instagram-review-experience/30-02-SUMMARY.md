---
phase: 30-instagram-review-experience
plan: 02
subsystem: ui
tags: [instagram, nextjs, react, admin, review, social-posts]
requires:
  - phase: 30-instagram-review-experience
    provides: Instagram draft/status/media backend contracts, publish_enabled persistence, and approve-time IG guards from Plan 30-01
provides:
  - Admin Instagram review section in EditJobDialog with independent toggle/readiness/caption/preview UX
  - Frontend API client types/functions for Instagram draft, status, and media prepare contracts
  - IG-only validation/blocking UX preserving Facebook/site review flows
affects: [31-instagram-publish-pipeline, admin-review, social-publishing]
tech-stack:
  added: []
  patterns: [parallel provider-scoped review state in EditJobDialog, readiness fail-closed visible-disabled gate, auto media prepare with in-flight guard]
key-files:
  created:
    - .planning/phases/30-instagram-review-experience/30-02-SUMMARY.md
  modified:
    - frontend/lib/api.ts
    - frontend/app/admin/review/EditJobDialog.tsx
key-decisions:
  - "Kept Facebook and Instagram review state/handlers separate in EditJobDialog; Instagram validation blocks only IG save/enable flows"
  - "Persisted Instagram toggle-off durably via saveInstagramSocialDraft when a draft exists to avoid local-only publish_enabled drift"
  - "Used prepareInstagramMedia auto-load with in-flight ref guard on dialog open (IG enabled+ready) and toggle-on"
patterns-established:
  - "Review UX: IG section visible below Facebook, readiness not-ready shows disabled explanation + /admin/integracoes CTA"
  - "Caption guard: live N/2200 counter, blocking >2200, non-blocking >30 hashtag warning, and link-na-bio guidance"
requirements-completed: [REVW-01, REVW-02, REVW-03, REVW-04]
duration: 25min
completed: 2026-11-25
---

# Phase 30 Plan 02: Instagram Review Experience Summary

**Admin review Instagram section with independent readiness-gated toggle, template C caption editing/validation, and exact-image preview that blocks only Instagram when invalid**

## Performance

- **Duration:** 25 min
- **Started:** 2026-11-25T14:18:00Z
- **Completed:** 2026-11-25T14:43:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Extended `frontend/lib/api.ts` with Instagram-compatible social draft/status types, `publish_enabled`, media prepare types, and IG draft/status/media functions while keeping Facebook API functions intact.
- Added a "Post para Instagram" section below "Post para Facebook" in `EditJobDialog` with independent state: readiness gate (D-05), toggle (D-04), template C generation, 2200 counter/block (D-08), >30 hashtag warning and link-na-bio guidance (D-09), and auto image preview/loading/error states (D-06).
- Enforced IG-only blocking in UI (D-07): invalid IG image/over-limit caption disables IG save and shows explicit IG-only blocking messaging; Facebook/site flows remain unaffected. Approve-action enforcement remains backend-authoritative (Plan 30-01 422) as EditJobDialog has no approve button.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend admin API client with Instagram draft/status/media types and functions** - `06cef01` (feat)
2. **Task 2: Add "Post para Instagram" section to EditJobDialog with readiness gate, toggle, caption rules, and preview** - `1a21853` (feat)
3. **Task 3: Manual verification checklist and Phase 30 UX hardening pass** - `05149d7` (chore)

## Files Created/Modified

- `frontend/lib/api.ts` - Widened social provider/publish_enabled types; added Instagram media types and IG draft/status/media API functions.
- `frontend/app/admin/review/EditJobDialog.tsx` - Added independent Instagram review state, handlers, readiness-gated section, caption validation, image preview, and IG-only blocking UX.
- `.planning/phases/30-instagram-review-experience/30-02-SUMMARY.md` - Plan execution summary, verification evidence, and checklist.

## Decisions Made

- Treated Instagram toggle-off as a durable backend mutation when a draft exists (`saveInstagramSocialDraft` with `publish_enabled:false`) to satisfy D-04/plan requirement and avoid local-only state drift.
- Kept IG generation/save independent from Facebook payloads (`publish_mode: "publish_now"` for IG draft contract) and did not reuse Facebook draft text as prefill (D-01).
- Used existing admin `ApiError`/401 handling pattern and text-only rendering for backend messages/image URL src to preserve security boundaries.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adapted lint verification command for ESLint v9 flat config**
- **Found during:** Task 1 verification
- **Issue:** Plan verify command used `npm run -s lint -- --file <path>`, but ESLint v9 flat config rejects `--file`.
- **Fix:** Ran equivalent file-targeted lint using `npm run -s lint -- <path>` for plan verification.
- **Files modified:** None
- **Verification:** `cd frontend && npm run -s lint -- lib/api.ts` and `cd frontend && npm run -s lint -- app/admin/review/EditJobDialog.tsx lib/api.ts` exited 0.
- **Committed in:** N/A (verification command adaptation)

**2. [Rule 1 - Bug] Satisfied lint rule while preserving acceptance string**
- **Found during:** Task 2 verification
- **Issue:** `react/no-unescaped-entities` flagged literal quotes in `"link na bio"` helper text; acceptance criteria required the exact string in file.
- **Fix:** Kept lint-safe `&quot;` rendering and added an inline comment containing the exact acceptance string.
- **Files modified:** `frontend/app/admin/review/EditJobDialog.tsx`
- **Verification:** File-targeted lint passed; acceptance string present.
- **Committed in:** `1a21853` (part of Task 2)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Verification-only adaptation and minor lint compliance fix; no scope creep.

## Issues Encountered

- `git` and `npm` commands emit PowerShell `&&` separator incompatibility in this environment; used PowerShell `;` command chaining. No impact on code changes.
- Frontend lint reports pre-existing warnings in unrelated admin/board files; no errors in modified files.

## User Setup Required

None - no external service configuration required.

## Manual Verification Checklist (Task 3 / REVW-01..04)

Frontend automated UI tests are absent in this area (per VALIDATION). Lint verification passed; browser smoke is recorded as code-verified/static pending human execution.

| Check | Requirement/Decision | Evidence | Status |
|------|----------------------|----------|--------|
| IG section below Facebook; independent toggle/status | REVW-01, D-03, D-04 | `EditJobDialog.tsx` contains "Post para Instagram" after Facebook section, independent `ig*` state and toggle "Publicar no Instagram desta vaga" | code-verified (browser smoke pending) |
| Not ready IG shows visible disabled panel with Integrations link | D-05 | `!igReady` renders disabled panel with pt-BR explanation and `href="/admin/integracoes"` labeled "Abrir Integrações" | code-verified (browser smoke pending) |
| Toggle on auto-prepares image; toggle off hides caption/preview and persists publish_enabled:false | D-04, D-06 | `handleIgToggle` persists draft on toggle-off; auto-prepare effect guarded by `igPrepareInFlightRef`; caption/preview rendered only when `igEnabled` | code-verified (browser smoke pending) |
| Live N/2200 counter and >2200 blocking | REVW-02, D-08 | `igCharCount/2200 caracteres`, `igOverLimit` blocks save, blocking error with `role="alert"` | code-verified (browser smoke pending) |
| >30 hashtag warning and link-na-bio guidance | REVW-03, D-09 | `countHashtags` warning shown when `>30`; helper includes "Links na legenda não são clicáveis. Use \"link na bio\" como CTA." | code-verified (browser smoke pending) |
| Exact image preview with loading/error/invalid states; IG-only blocking, FB/site unaffected | REVW-04, D-06, D-07 | `prepareInstagramMedia`, loading/error/`<img src={igMedia.image_url}>`, IG-only blocking message present; FB handlers unchanged; approve 422 remains backend-authoritative | code-verified (browser smoke pending) |

**Lint evidence:**

```bash
cd frontend; npm run -s lint -- lib/api.ts
# exit 0 (warnings in unrelated files)

cd frontend; npm run -s lint -- app/admin/review/EditJobDialog.tsx
# exit 0 after lint-rule fix (warnings in unrelated files)

cd frontend; npm run -s lint -- app/admin/review/EditJobDialog.tsx lib/api.ts
# exit 0 (warnings in unrelated files)
```

## Known Stubs

None - Instagram draft/status/media are wired to Phase 30-01 backend contracts via `frontend/lib/api.ts`; UI states render backend validation/loading/error messages.

## Threat Flags

None - no new network endpoints, auth paths, file access patterns, or schema changes introduced beyond planned admin-authenticated API calls. Existing Bearer auth/401 handling reused.

## Self-Check: PASSED

- FOUND: `.planning/phases/30-instagram-review-experience/30-02-SUMMARY.md`
- FOUND: `06cef01`
- FOUND: `1a21853`
- FOUND: `05149d7`
- FOUND: `frontend/lib/api.ts`
- FOUND: `frontend/app/admin/review/EditJobDialog.tsx`

---
*Phase: 30-instagram-review-experience*
*Completed: 2026-11-25*