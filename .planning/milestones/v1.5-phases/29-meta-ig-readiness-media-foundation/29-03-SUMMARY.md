---
phase: 29-meta-ig-readiness-media-foundation
plan: 03
subsystem: ui
tags: [instagram, meta, integrations, nextjs, react, docs, ops]

# Dependency graph
requires:
  - phase: 29-meta-ig-readiness-media-foundation
    provides: Additive Meta Instagram readiness/status contracts and verify/connect behavior from 29-01
provides:
  - Admin Integrations UI with additive Instagram readiness states and actionable pt-BR copy
  - Frontend Meta integration types extended with MetaInstagramReadiness
  - META-03 operational checklist covering IG scopes, linkage, media env, troubleshooting, and manual handoff
  - Doc smoke test guarding required Phase 29 IG operations contract strings
affects: [30, 31]

# Tech tracking
tech-stack:
  added: []
  patterns: [additive IG readiness panel in Integrations, safe pt-BR actionable IG states, explicit manual Meta verification handoff]

key-files:
  created:
    - backend/tests/test_docs_meta_instagram.py
  modified:
    - frontend/lib/api.ts
    - frontend/app/admin/integracoes/IntegrationsClient.tsx
    - frontend/app/admin/integracoes/page.tsx
    - docs/META-INTEGRATION-TESTING.md

key-decisions:
  - "Instagram readiness is rendered as an additive panel inside connected/needs_reconnect Facebook states; Facebook status remains authoritative (D-15)"
  - "Unknown IG readiness falls back to verify-first action unless Facebook is already needs_reconnect, keeping guidance actionable without inventing raw errors"
  - "META-03 live Meta validation is documented as explicit handoff and must not be marked approved without real execution evidence"

patterns-established:
  - "Integrations IG readiness UI: allowlisted fields only (state, ig_user_id, ig_username, safe message), no tokens/secrets/raw Graph errors"
  - "Ops doc smoke tests: lightweight string-contract assertions for required Meta/IG setup and handoff boundaries"

requirements-completed: [META-01, META-03]

# Metrics
duration: 5min
completed: 2026-11-23
---

# Phase 29 Plan 03: Meta/IG Readiness & Media Foundation Summary

**Additive Instagram readiness UX in Admin Integrations with actionable pt-BR reconnect/verify states and META-03 ops documentation for IG scopes, linkage, media env, and manual handoff.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-11-23T16:43:03Z
- **Completed:** 2026-11-23T16:48:29Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Extended frontend Meta integration contracts with `MetaInstagramReadiness` and additive `instagram` fields while preserving existing Facebook status/action behavior.
- Added an additive Instagram readiness panel to Integrations for connected/needs_reconnect Facebook states, with exact UI-SPEC pt-BR copy, safe fallback handling, and disconnect copy reflecting FB+IG impact.
- Documented META-03 Instagram readiness/media operations (scopes, Page↔IG linkage, `MEDIA_PUBLIC_BASE_URL`, troubleshooting, security, manual checklist) and added a doc smoke test.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend frontend Meta integration types and IG readiness UI** - `01b2538` (feat)
2. **Task 2: Write META-03 operational docs and doc smoke test** - `a26c904` (test, RED) + `ab69701` (docs, GREEN)

**Plan metadata:** recorded in final docs commit for 29-03

## Files Created/Modified
- `frontend/lib/api.ts` - Adds `MetaInstagramReadiness` types and additive `instagram` fields on Meta integration status/action responses.
- `frontend/app/admin/integracoes/IntegrationsClient.tsx` - Renders additive IG readiness states, actionable reconnect/verify behavior, and FB+IG disconnect impact copy.
- `frontend/app/admin/integracoes/page.tsx` - Updates Integrations page supporting text to mention Instagram readiness.
- `docs/META-INTEGRATION-TESTING.md` - Adds META-03 IG permissions, linkage prerequisites, media env, troubleshooting, checklist, and explicit manual handoff boundary.
- `backend/tests/test_docs_meta_instagram.py` - Smoke test guarding required IG ops doc contract strings and handoff boundary.

## Decisions Made
- Followed D-15: IG readiness is additive and actionable in Integrations; missing IG linkage/permissions does not render Facebook as disconnected.
- Kept IG UI to allowlisted safe fields and pt-BR messages; unknown/transient states guide admin to verify or reconnect without exposing raw errors/tokens.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Aligned disconnected empty-state copy with Instagram readiness visibility**
- **Found during:** Task 1 (Extend frontend Meta integration types and IG readiness UI)
- **Issue:** Disconnected Integrations state mentioned Facebook auto-publish only, which missed the new IG readiness context and could obscure the additive readiness flow.
- **Fix:** Updated disconnected empty-state body to the UI-SPEC-aligned copy: "Conecte uma Página para habilitar a integração. Após conectar, você verá aqui a prontidão do Instagram para publicação."
- **Files modified:** frontend/app/admin/integracoes/IntegrationsClient.tsx
- **Verification:** `cd frontend && npx eslint app/admin/integracoes/IntegrationsClient.tsx app/admin/integracoes/page.tsx lib/api.ts`
- **Committed in:** 01b2538 (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Small UX consistency fix aligned with UI-SPEC/META-01; no scope creep.

## Issues Encountered
- ESLint reported 2 pre-existing `react-hooks/set-state-in-effect` warnings in `IntegrationsClient.tsx`; command exited 0 and no new errors were introduced.

## User Setup Required

**External services require manual configuration.** Phase 29 IG readiness/media validation requires:
- Meta app permissions include `instagram_basic` and `instagram_content_publish`
- Target Facebook Page linked to an Instagram Business/Creator account
- `MEDIA_PUBLIC_BASE_URL` configured as public HTTPS backend base URL
- Public `/api/v1/public/ig-media/*` reachable by Meta over HTTPS

Live Meta validation is a manual handoff: **não marcar como aprovado sem execução real**.

## Next Phase Readiness
- Phase 30 can build Instagram review UX on top of additive IG readiness contracts and existing media validation/prepare foundation.
- Phase 31 can rely on readiness and public media contracts, but live Meta permission/linkage/media-fetch verification remains an operational prerequisite.

## Self-Check: PASSED

- FOUND: .planning/phases/29-meta-ig-readiness-media-foundation/29-03-SUMMARY.md
- FOUND: frontend/lib/api.ts
- FOUND: frontend/app/admin/integracoes/IntegrationsClient.tsx
- FOUND: frontend/app/admin/integracoes/page.tsx
- FOUND: docs/META-INTEGRATION-TESTING.md
- FOUND: backend/tests/test_docs_meta_instagram.py
- FOUND: 01b2538 feat(29-03): add Instagram readiness UI to integrations
- FOUND: a26c904 test(29-03): add META-03 Instagram ops doc smoke test
- FOUND: ab69701 docs(29-03): document Instagram readiness and media operations

---
*Phase: 29-meta-ig-readiness-media-foundation*
*Completed: 2026-11-23*
