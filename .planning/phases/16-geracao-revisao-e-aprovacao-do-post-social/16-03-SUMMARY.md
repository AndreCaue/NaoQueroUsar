---
phase: 16-geracao-revisao-e-aprovacao-do-post-social
plan: 03
subsystem: frontend-admin-review
tags: [frontend, admin, social-draft, review, facebook, api-client]
dependency_graph:
  requires:
    - 16-02 (admin social draft endpoints and approve envelope)
  provides:
    - Typed frontend client for social draft lifecycle and approve envelope
    - EditJobDialog "Post para Facebook" review/edit/save/schedule UI
    - ReviewQueue site-first approve feedback with social outcome toasts
  affects:
    - frontend/lib/api.ts
    - frontend/app/admin/review/EditJobDialog.tsx
    - frontend/app/admin/review/ReviewQueue.tsx
tech_stack:
  added: []
  patterns:
    - Admin fetch helpers with Bearer auth and ApiError/readError
    - Native dialog/modal state with async action guards and confirmation
    - Optimistic approve with rollback on request failure and outcome-based toasts
key_files:
  created: []
  modified:
    - frontend/lib/api.ts
    - frontend/app/admin/review/EditJobDialog.tsx
    - frontend/app/admin/review/ReviewQueue.tsx
decisions:
  - Treated GET /social-post 404 as empty draft state (`null`) in the client to render the empty-state flow without surfacing a load error.
  - Kept social approve warnings on the existing toast error variant (text always states "Vaga publicada no site...") because the shared toast API only supports success/error.
  - Used explicit save/regenerate actions with dirty tracking and last-saved snapshot so approval relies on the saved draft contract (D-08).
metrics:
  duration: ~20 min
  completed: 2026-11-15
  tasks: 2
  files: 3
---

# Phase 16 Plan 03: Admin social post review UI Summary

**One-liner:** Admin review now loads/generates/saves Facebook post drafts in EditJobDialog and handles approve responses as a site-first `{job,social}` envelope with distinct social outcome toasts.

## What Was Built

- **`frontend/lib/api.ts`**: added Phase 16 social draft types (`SocialPublishMode`, `SocialDraftOrigin`, `SocialApproveStatus`, `SocialPostDraft`, `SocialApproveOutcome`, `JobApproveResponse`, request payloads), changed `approveJob` to return `JobApproveResponse`, and added `getSocialDraft`/`generateSocialDraft`/`saveSocialDraft` with Bearer auth and `ApiError` handling (`/social-post`, `/social-post/generate`, GET 404 mapped to `null`).
- **`frontend/app/admin/review/EditJobDialog.tsx`**: added a `Post para Facebook` section with draft load/empty state, generate/regenerate (with overwrite confirmation), editable textarea, live `{n}/700 caracteres` counter and helper, `Prévia do post`, origin/fallback/saved/unsaved/frozen indicators, `Publicar agora`/`Agendar publicação` controls with BRT date/time inputs and validation, explicit save flow, actionable `SITE_PUBLIC_URL` messaging, frozen read-only behavior, and unsaved-draft reminder. Preview/content rendered as text only (`whitespace-pre-wrap`, no HTML injection).
- **`frontend/app/admin/review/ReviewQueue.tsx`**: updated optimistic approve to consume `result.job`/`result.social`, keep site-first success semantics, and emit outcome-specific toasts for `registered`, `skipped` ("Nenhum rascunho social salvo — publicação no Facebook não foi registrada."), and `warning` ("Não foi possível registrar o post social agora.") without treating social issues as site publish failure; rollback behavior remains on approve request failure.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Atualizar API client frontend para draft social e contrato de approve | ad18cd3 | frontend/lib/api.ts |
| 2 | Seção "Post para Facebook" no EditJobDialog com estados/UI-SPEC e tratamento de approve no ReviewQueue | ad18cd3 | frontend/app/admin/review/EditJobDialog.tsx, frontend/app/admin/review/ReviewQueue.tsx |

## Verification

- `cd frontend; npm run lint` — **passed** (exit 0, existing repo warnings only; new set-state-in-effect warnings in `EditJobDialog.tsx` follow existing admin pattern).
- `cd frontend; npm run build` — **failed (pre-existing, out of scope)** during prerender of `/admin/integracoes` with `useSearchParams() should be wrapped in a suspense boundary` (unrelated route; no files in that route modified by this plan). TypeScript compilation completed before the prerender/export error.
- Acceptance checks present in source: `JobApproveResponse`, `getSocialDraft`, `generateSocialDraft`, `saveSocialDraft`, `Promise<JobApproveResponse>` for `approveJob`, `/social-post/generate`, `/social-post`, `Post para Facebook`, `Gerar rascunho`, `Regenerar com IA`, `Salvar rascunho`, `/700 caracteres`, `Prévia do post`, `Publicar agora`, `Agendar publicação`, `America/Sao_Paulo`, `Texto bloqueado após aprovação`, `Alterações não salvas`, and ReviewQueue social outcome strings/`result.job`+`result.social` branching.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written for implementation scope.

### Scope/Environment Notes

**1. [Out-of-scope pre-existing issue] Frontend production build prerender failure on unrelated route**
- **Found during:** Task 2 verification
- **Issue:** `next build` fails on `/admin/integracoes` (`useSearchParams()` suspense boundary) unrelated to this plan's files.
- **Action:** Not fixed (out of scope per destructive/scope boundary rules). Documented here; lint and code-level contract checks for modified files passed.
- **Files modified:** none

**2. [Process note] Task commits combined**
- **Found during:** Task 1 commit
- **Issue:** `ad18cd3` included all three plan-modified frontend files, combining Task 1 and Task 2 changes.
- **Action:** Kept commit as-is (contains complete intended work), recorded accurately in commit table.

## Threat Flags

None detected beyond planned mitigations (admin Bearer-auth helpers reused; preview/text rendered as plain text; frozen/unsaved states surfaced; approve feedback distinguishes site vs social outcome).

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: frontend/lib/api.ts
- FOUND: frontend/app/admin/review/EditJobDialog.tsx
- FOUND: frontend/app/admin/review/ReviewQueue.tsx
- FOUND: .planning/phases/16-geracao-revisao-e-aprovacao-do-post-social/16-03-SUMMARY.md
- FOUND: ad18cd3 (task implementation commit)
- NOTE: `frontend` build blocked by pre-existing `/admin/integracoes` prerender issue (unrelated).
