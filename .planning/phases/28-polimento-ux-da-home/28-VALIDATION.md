---
phase: 28
slug: polimento-ux-da-home
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-22
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest + pytest-asyncio/httpx ASGITransport; Frontend: Vitest ^2.1.9 (node env) |
| **Config file** | Backend: `backend/tests/conftest.py`; Frontend: `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm test -- --run lib/cities.test.ts` |
| **Full suite command** | `cd backend && pytest tests/test_public_api.py tests/test_public_search.py -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm test -- --run lib/cities.test.ts`
- **After every plan wave:** Run `cd backend && pytest tests/test_public_api.py tests/test_public_search.py -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 28-??-?? | TBD | TBD | CITY-01 | T-28-01 | `JobListResponse` extends only with `available_cities`; no contact fields exposed; active cities independent of `q` and limited to published/non-expired jobs | integration | `cd backend && pytest tests/test_public_api.py tests/test_public_search.py -q -k available_cities` | ❌ W0 | ⬜ pending |
| 28-??-?? | TBD | TBD | CITY-01 | T-28-02 | Obsolete selected city is cleared/canonicalized; broad board state returned without stale empty dead-end | integration/manual | `cd backend && pytest tests/test_public_search.py -q -k obsolete_city` | ❌ W0 | ⬜ pending |
| 28-??-?? | TBD | TBD | UIUX-01 | N/A | Sort control is accessible button+listbox with keyboard/Escape/outside-click/focus-return behavior; hover/focus visible | manual/a11y | Manual keyboard + hover checklist on `/` | ❌ manual | ⬜ pending |
| 28-??-?? | TBD | TBD | UIUX-01 | N/A | City chips and job cards show specified hover/focus states with no layout shift; reduced-motion respected | manual/visual | Manual desktop pointer:fine hover on chips/cards | ❌ manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_public_api.py` or `backend/tests/test_public_search.py` — add `available_cities` contract tests (D-01/D-02/D-04), asserting stable slug order, independence from `q`, published/non-expired semantics, and no contact leakage.
- [ ] `backend/tests/test_public_search.py` (or chosen backend test file) — add obsolete selected city cleanup/canonicalization coverage if handled server-side (D-03).
- [ ] `frontend/lib/cities.test.ts` or `frontend/lib/filters.test.ts` — cover active-city slug/order mapping and obsolete-city URL cleanup helper if extracted.
- [ ] Frontend component test harness gap: `frontend/vitest.config.ts` currently includes only `lib/**/*.test.ts` in node env; automated BoardToolbar/JobCard interaction tests would require harness/config expansion (optional, planner decides).

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Custom sort dropdown hover/focus/keyboard/a11y behavior | UIUX-01 | No frontend component test harness configured; visual and ARIA interaction behavior is easiest to verify in browser | On `/`, tab to sort trigger, open with Enter/Space, move with Arrow keys, select option, verify Escape/outside click close and focus returns to trigger; verify hover/focus styling on trigger/options. |
| City chip and job card hover intensity/layout stability | UIUX-01 | Visual hover/focus feedback and layout-shift absence are not covered by current node-only Vitest setup | On desktop pointer:fine, hover active/inactive city chips and job cards; confirm accent language, no dimension/layout shift, focus-visible ring still present. |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
