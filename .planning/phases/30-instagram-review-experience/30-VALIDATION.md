---
phase: 30
slug: instagram-review-experience
status: partial
nyquist_compliant: false
wave_0_complete: true
created: 2026-11-23
updated: 2026-11-26
---

# Phase 30 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest (pyproject.toml). Frontend: no dedicated unit/UI test harness configured for this admin review area. |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `cd backend && pytest -q tests/test_admin_instagram_social_posts.py tests/test_public_ig_media.py tests/test_ig_media_validation.py` |
| **Full suite command** | `cd backend && pytest -q` |
| **Estimated runtime** | ~120 seconds (targeted backend suite) |

---

## Sampling Rate

- **After every task commit:** Run the quick backend command when backend files changed; otherwise perform targeted manual UI checks for the touched frontend area.
- **After every plan wave:** Run `cd backend && pytest -q` and complete manual UI verification checklist for the wave.
- **Before `/gsd-verify-work`:** Targeted backend suite green plus manual REVW-01..04 verification completed.
- **Max feedback latency:** ~120 seconds for targeted backend command.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 30-01-01 | 01 | 1 | REVW-01, REVW-02, REVW-04 | T-30-04 | `publish_enabled` and provider-widened IG draft/status contracts persist safely; admin-only endpoints remain auth-gated | integration | `cd backend && pytest -q tests/test_admin_instagram_social_posts.py tests/test_admin_social_posts.py` | ✅ | ✅ green |
| 30-01-02 | 01 | 1 | REVW-01, REVW-02, REVW-03, REVW-04 | T-30-01, T-30-02, T-30-05 | IG caption >2200 rejected server-side; IG enabled+invalid image rejected on save/generate/approve; approve guard blocks only IG-invalid enabled case; FB/site unaffected | integration | `cd backend && pytest -q tests/test_admin_instagram_social_posts.py tests/test_public_ig_media.py tests/test_ig_media_validation.py` | ✅ | ✅ green |
| 30-01-03 | 01 | 1 | REVW-01, REVW-02, REVW-04 | T-30-01, T-30-02 | Regression tests cover IG/FB isolation, 2200 limit, D-07 image guard, and approve disable/fix escape hatch | integration | `cd backend && pytest -q tests/test_admin_instagram_social_posts.py` | ✅ | ✅ green |
| 30-02-01 | 02 | 2 | REVW-01, REVW-02, REVW-03, REVW-04 | T-30-P2-01, T-30-P2-03 | Frontend API client types/functions use admin Bearer auth and preserve FB contracts while adding IG draft/status/media calls | manual/static | `cd frontend && npm run -s lint -- lib/api.ts` | ✅ | ⚠️ manual-only |
| 30-02-02 | 02 | 2 | REVW-01, REVW-02, REVW-03, REVW-04 | T-30-P2-01, T-30-P2-02, T-30-P2-04 | IG section renders below FB; readiness fail-closed visible/disabled; toggle/caption/preview states show safe pt-BR errors; IG-only blocking, FB/site unaffected | manual | N/A (no frontend UI harness) | ✅ | ⚠️ manual-only |
| 30-02-03 | 02 | 2 | REVW-01, REVW-02, REVW-03, REVW-04 | T-30-P2-04 | Hardening pass verifies D-01..D-09 copy/states, in-flight prepare guard, and manual checklist evidence recorded | manual/static | `cd frontend && npm run -s lint -- app/admin/review/EditJobDialog.tsx lib/api.ts` | ✅ | ⚠️ manual-only |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky/manual-only*

---

## Wave 0 Requirements

- [x] `backend/tests/test_admin_instagram_social_posts.py` — covers IG draft isolation, 2200-char rejection, D-07 image guard, approve guard escape hatch (REVW-01/02/04 backend contracts).
- [x] `backend/tests/test_public_ig_media.py`, `backend/tests/test_ig_media_validation.py` — existing Phase 29 media/validation coverage reused by REVW-04.
- [ ] Frontend UI harness for `EditJobDialog` Instagram section — not present; UI behaviors remain manual-only.

*Existing backend infrastructure covers automated backend requirements for Phase 30; frontend UI behavior has no automated harness.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| IG section appears below "Post para Facebook" in `EditJobDialog`; toggle and IG status are independent | REVW-01 | No frontend automated UI harness configured | Open admin review dialog for a job; confirm "Post para Instagram" below "Post para Facebook"; toggle on/off and observe independent IG state. |
| Readiness-not-ready: section visible but disabled with pt-BR explanation and link to `/admin/integracoes` | REVW-01 | Requires Meta/IG readiness states and UI rendering | With IG not ready, confirm section is visible (not hidden), disabled, shows explanation and "Abrir Integrações" link to `/admin/integracoes`. |
| Live caption counter `N/2200 caracteres`; save blocked at >2200 with actionable pt-BR error | REVW-02 | Frontend UX behavior without unit test setup | Edit caption, observe live counter; exceed 2200 chars and confirm blocking error and IG save blocked. |
| >30 hashtags shows non-blocking warning; guidance states links are not clickable and CTA is "link na bio" | REVW-03 | UI-only/non-blocking by design; no frontend harness | Add >30 hashtags and confirm non-blocking warning; confirm helper text includes non-clickable links + "link na bio". |
| Preview auto-loads on open/toggle-on, shows loading/error/invalid/valid states; invalid image blocks only IG save/approve-with-IG-enabled; FB/site unaffected | REVW-04 | Depends on visual UI states and integration flow | Toggle IG on, observe "Preparando imagem do Instagram..." then preview or pt-BR error; confirm exact prepared image URL renders when valid; confirm IG-only block message and Facebook/site actions unaffected. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies documented
- [x] Sampling continuity: no 3 consecutive tasks without automated verify where feasible (frontend tasks are explicitly manual-only)
- [x] Wave 0 covers all MISSING backend references; frontend harness gap documented
- [x] No watch-mode flags in commands
- [x] Feedback latency targets noted above
- [ ] `nyquist_compliant: true` set in frontmatter (blocked by manual-only frontend UI coverage)

**Approval:** partial — backend automated coverage green; UI manual verification required

---

## Validation Audit 2026-11-26

| Metric | Count |
|--------|-------|
| Gaps found | 4 |
| Resolved (automated/backend) | 0 new tests added; existing automated backend coverage confirmed green |
| Escalated to manual-only | 4 |

### Findings

- **REVW-01 (PARTIAL):** Backend IG draft/status/provider isolation and readiness contract support covered by `backend/tests/test_admin_instagram_social_posts.py` (8 collected; 4 Phase 30-focused + 4 later Phase 31/32-safe extensions in same file). UI section/toggle/readiness rendering remains manual-only.
- **REVW-02 (PARTIAL):** Server-side 2200-char rejection covered by `test_instagram_caption_over_2200_rejected`; template C generation covered by `test_instagram_social_post_get_generate_save_isolated_from_facebook`. Live counter/UI block UX remains manual-only.
- **REVW-03 (MISSING → manual-only):** >30 hashtag warning and "link na bio"/non-clickable guidance are UI-only by design; no frontend harness. Kept as Manual-Only.
- **REVW-04 (PARTIAL):** D-07/IMAG-01 guard covered by `test_instagram_enabled_requires_valid_image_on_save`, `test_approve_blocked_by_invalid_instagram_then_allowed_when_disabled`, and Phase 29 media tests (`test_public_ig_media.py`, `test_ig_media_validation.py`). Exact-image preview UI states remain manual-only.

### Evidence

- Targeted command: `cd backend && pytest -q tests/test_admin_instagram_social_posts.py tests/test_public_ig_media.py tests/test_ig_media_validation.py`
- Result: **15 passed in 119.59s**
- Frontend harness: none configured for `EditJobDialog` (lint/static only; manual checklist recorded in `30-02-SUMMARY.md`).

### User Decision

- Selected: **"Mark UI gaps manual-only (Recommended)"** at audit gate.
