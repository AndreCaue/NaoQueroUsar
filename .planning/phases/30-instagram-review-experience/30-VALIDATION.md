---
phase: 30
slug: instagram-review-experience
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-23
---

# Phase 30 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest (repo standard). Frontend: no dedicated unit test harness detected in repo for this UI area (manual verification expected). |
| **Config file** | Backend: existing pytest configuration in repo (e.g. `pytest.ini`/`pyproject.toml`) — none new required for Phase 30 scope. |
| **Quick run command** | `cd backend && pytest -q tests/test_public_ig_media.py tests/test_ig_media_validation.py` |
| **Full suite command** | `cd backend && pytest -q` |
| **Estimated runtime** | ~30–90 seconds (varies by env) |

---

## Sampling Rate

- **After every task commit:** Run the quick backend command when backend files changed; otherwise perform targeted manual UI checks for the touched frontend area.
- **After every plan wave:** Run `cd backend && pytest -q` (and complete manual UI verification checklist for the wave).
- **Before `/gsd-verify-work`:** Full backend suite green for touched areas plus manual REVW-01..04 verification completed.
- **Max feedback latency:** ~120 seconds (backend quick/full as above).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 30-xx-01 | TBD | TBD | REVW-04 | — | Media prepare returns safe pt-BR validation errors; only admin can call prepare | integration | `cd backend && pytest -q tests/test_public_ig_media.py tests/test_ig_media_validation.py` | ✅ | ⬜ pending |
| 30-xx-02 | TBD | TBD | REVW-02 | V5 (ASVS) | IG draft caption rejected server-side when >2200 chars; Facebook flow unchanged | integration/unit | `cd backend && pytest -q` (targeted once IG draft tests added) | ❌ W0 | ⬜ pending |
| 30-xx-03 | TBD | TBD | REVW-01 | — | Dialog shows IG section below Facebook; readiness gating matches D-05 | manual | N/A | ❌ manual | ⬜ pending |
| 30-xx-04 | TBD | TBD | REVW-03 | — | UI shows >30 hashtag warning (non-blocking) and “link na bio” guidance | manual | N/A | ❌ manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Backend tests for Instagram draft/status endpoints (if added): create/get/update IG draft, provider isolation from Facebook, caption length >2200 rejected (server-side), status retrieval shape.
- [ ] (Optional) No frontend unit test framework installed; document manual verification steps in plan summaries/checklists.

*Existing backend media tests (`test_public_ig_media.py`, `test_ig_media_validation.py`) cover Phase 29 prepare/public media behavior relevant to REVW-04.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| IG section appears below Facebook in `EditJobDialog`, toggle hides/shows caption+preview (D-03/D-04) | REVW-01 | No frontend automated UI harness configured | Open admin review dialog for a job; confirm “Post para Instagram” below “Post para Facebook”; toggle on/off shows/hides controls. |
| Readiness gating: IG not ready → section visible but disabled with link to `/admin/integracoes` (D-05) | REVW-01 | Requires varied Meta/IG readiness states (manual/integration env) | With IG not ready (or mocked status), confirm disabled state, pt-BR message, and link works. |
| Caption counter `N/2200` live; save blocked at >2200; >30 hashtags shows warning (non-blocking); guidance about non-clickable links + “link na bio” shown | REVW-02, REVW-03 | Frontend UX behavior without unit test setup | Type caption, observe counter and warning thresholds; attempt to save over 2200 and confirm block + message. |
| Preview auto-loads on toggle open per D-06, shows loading/error states, blocks only IG if image invalid (D-07) | REVW-04 | Depends on media prepare endpoint + UI states | Toggle IG on, observe loading then preview or pt-BR error; confirm Facebook/site actions unaffected when IG invalid/enabled-but-blocked. |

*All other phase behaviors should be covered by backend automated tests where applicable.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies documented
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify where feasible
- [ ] Wave 0 covers missing backend test references for IG draft/status if introduced
- [ ] No watch-mode flags in commands
- [ ] Feedback latency targets noted above
- [ ] `nyquist_compliant: true` set in frontmatter after implementation evidence is collected

**Approval:** pending