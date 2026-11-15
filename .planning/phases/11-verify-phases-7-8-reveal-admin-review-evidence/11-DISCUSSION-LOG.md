# Phase 11: Verify Phases 7–8 & Close Reveal/Admin/Review Evidence Gaps - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-15
**Phase:** 11-verify-phases-7-8-reveal-admin-review-evidence
**Areas discussed:** 07 verification evidence, 08 verification evidence, Phase 8 traceability repair, REQ status & SECR-12 boundary

---

## 07 verification evidence

### Q1: How should 07-VERIFICATION.md establish evidence for SECR-10/11/12?

| Option | Description | Selected |
|--------|-------------|----------|
| Run targeted tests + cite (Recommended) | Re-run the most relevant backend tests now and record pass/fail output snippets plus code/plan-summary pointers. Gives fresh, auditable proof while still linking source artifacts. | ✓ |
| Cite existing evidence only | Reference existing tests, code paths, and 07 summaries/commits without executing pytest now. Faster, but verification relies on previously recorded state rather than a fresh run. | |
| Code inspection only | Verify by reading routes/services/config and documenting behavior; treat automated tests as not re-run in this artifact. Useful if execution is impractical, but weaker audit evidence. | |

**User's choice:** Run targeted tests + cite (Recommended)
**Notes:** Relevant existing tests identified include `backend/tests/test_reveal_api.py`, `test_turnstile_service.py`, `test_ratelimit.py`, `test_turnstile_live.py`.

### Q2: How should 07-VERIFICATION.md treat SECR-10 operational rebuild caveat?

| Option | Description | Selected |
|--------|-------------|----------|
| Verified with operational caveat (Recommended) | Mark SECR-10 evidence as present (widget/config/wiring/tests) but explicitly document the rebuild-required constraint as an operational caveat/human-process note in the artifact. Matches the roadmap goal to "document the SECR-10 operational rebuild caveat". | ✓ |
| Mark SECR-10 partial/gap_found | Treat the rebuild constraint as unresolved until a real key-rotation/rebuild is demonstrated. Stricter, but may leave Phase 11 unable to close the audit gap without production operations. | |
| Code-only satisfied, ops out of scope | Mark SECR-10 satisfied for implementation evidence and omit/soften the operational caveat. Risks not satisfying the audit/roadmap requirement to document the caveat. | |

**User's choice:** Verified with operational caveat (Recommended)
**Notes:** SECR-10 site key is inlined in frontend bundle; Cloudflare key change requires frontend rebuild.

### Q3: How should 07-VERIFICATION.md handle SECR-12 scope/boundary?

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 7 side + defer Phase 9 (Recommended) | Verify SECR-12 evidence attributable to Phase 7 (e.g. Turnstile/rate-limit security controls claimed there) and explicitly document that `/admin/expire` auth-contract reconciliation/evidence is owned by Phase 12 to avoid overlap/conflict. | ✓ |
| Verify full SECR-12 end-to-end now | Include `/admin/expire` X-Cron-Secret-only contract evidence in Phase 11 too. More complete, but duplicates Phase 12 scope and may conflict with its reconciliation task. | |
| Defer SECR-12 entirely to Phase 12 | Exclude SECR-12 from 07-VERIFICATION and leave it for Phase 12. Simpler boundary, but likely misses Phase 11’s stated success criterion to verify SECR-10/11/12 for Phase 7. | |

**User's choice:** Phase 7 side + defer Phase 9 (Recommended)
**Notes:** SECR-12 spans audit context across Phase 7/9; Phase 12 owns `/admin/expire` contract reconciliation.

---

## 08 verification evidence

### Q1: How should 08-VERIFICATION.md establish evidence for ADMN-10/11/12 and REVW-10/11/12?

| Option | Description | Selected |
|--------|-------------|----------|
| Run backend tests + cite code/UI (Recommended) | Run targeted backend/admin/extract tests and cite API/frontend code paths. For UI-only behaviors not covered by automated tests, document code evidence and mark any remaining runtime/browser checks as human/visual verification notes. | ✓ |
| Cite existing evidence only | Reference tests, summaries, and implementation files without re-running commands now. Faster, but no fresh execution proof. | |
| Require browser/manual proof for UI claims | Treat UI criteria (toasts, immediate public visibility flow, Turnstile widget indicator) as needing explicit manual verification evidence recorded in the artifact, in addition to code/tests. Most thorough, but may leave gaps if not executed. | |

**User's choice:** Run backend tests + cite code/UI (Recommended)
**Notes:** Relevant existing tests identified include `backend/tests/test_admin_jobs.py` and `test_extract_api.py`.

### Q2: How should 08-VERIFICATION.md treat REVW-12 wording vs implementation?

| Option | Description | Selected |
|--------|-------------|----------|
| Verify implemented contract + note wording (Recommended) | Document hard delete with repeat call returning 404 as the implemented/idempotent-in-effect behavior, cite tests/code, and add a short note mapping it to the requirement’s "no-op" intent so evidence is explicit and auditable. | ✓ |
| Require strict no-op response semantics | Treat 404-on-repeat as not satisfying "no-op" and mark REVW-12 partial until API returns a success/no-content no-op on duplicate delete. May require code change outside this gap-closure phase. | |
| Mark satisfied without discussion | Record REVW-12 satisfied based on hard delete behavior only, without calling out the 404-vs-no-op nuance. Less precise for future audits. | |

**User's choice:** Verify implemented contract + note wording (Recommended)
**Notes:** Audit/implementation indicate repeat delete returns 404.

### Q3: How should UI-facing Phase 8 criteria be recorded if not live-tested?

| Option | Description | Selected |
|--------|-------------|----------|
| Code evidence + human verification notes (Recommended) | Cite the implementing frontend components/flows as evidence and list the UI behaviors as human/browser verification items when not exercised live. Clear and audit-safe. | ✓ |
| Satisfy from source inspection only | Mark UI criteria verified based on code paths/props/messages alone, without separate human verification items. Faster, but weaker confidence for visual/interactive behavior. | |
| Attempt frontend build/lint as proxy | Run frontend build/lint/typecheck (if available) as additional evidence, while still noting that visual interaction may need manual confirmation. Useful proxy but not a substitute for UX proof. | |

**User's choice:** Code evidence + human verification notes (Recommended)
**Notes:** Applies to criteria such as ADMN-10 Turnstile indicator, toast feedback, and immediate public visibility UX.

---

## Phase 8 traceability repair

### Q1: How should 08-03-SUMMARY.md and CONTEXT-SUMMARY.md be repaired?

| Option | Description | Selected |
|--------|-------------|----------|
| Edit in place, add/fix frontmatter (Recommended) | Update the existing Phase 8 files in place: ensure 08-03-SUMMARY frontmatter/cross-references are correct and add machine-checkable frontmatter/cross-references to CONTEXT-SUMMARY.md for ADMN-12/REVW-12. Directly satisfies the audit request. | ✓ |
| Edit 08-03 only, leave CONTEXT-SUMMARY narrative | Only adjust 08-03-SUMMARY.md (and other true summaries) and avoid adding frontmatter to CONTEXT-SUMMARY.md, treating it as non-canonical. May not fully satisfy the audit’s explicit file callout. | |
| Create a new traceability note instead of edits | Leave historical Phase 8 files unchanged and add a supplemental traceability document in Phase 11 mapping ADMN-12/REVW-12. Preserves history but may not be considered "machine-checkable" in the locations the audit flagged. | |

**User's choice:** Edit in place, add/fix frontmatter (Recommended)
**Notes:** `08-03-SUMMARY.md` currently has frontmatter including `requirements-completed: [ADMN-12, REVW-12]`; `CONTEXT-SUMMARY.md` is narrative-only and needs machine-checkable refs/cross-references.

### Q2: What machine-checkable form should CONTEXT-SUMMARY.md use?

| Option | Description | Selected |
|--------|-------------|----------|
| Add frontmatter with requirements refs (Recommended) | Add YAML frontmatter (e.g. `phase`, `type: context-summary`, `requirements-referenced`/`requirements-completed` as appropriate) plus explicit ADMN-12/REVW-12 cross-reference lines to plans/summaries/08-VERIFICATION. Makes IDs discoverable by simple scans without overstating execution. | ✓ |
| Mirror SUMMARY frontmatter exactly | Give CONTEXT-SUMMARY the same `requirements-completed: [ADMN-12, REVW-12]` structure as plan summaries. Maximizes machine detection but may blur the distinction between context recap and completed execution artifact. | |
| Cross-reference text only, no frontmatter | Add clearly labeled ADMN-12/REVW-12 references in the body but no YAML frontmatter. Human-readable, but may not satisfy "machine-checkable frontmatter/cross-references" as strictly. | |

**User's choice:** Add frontmatter with requirements refs (Recommended)
**Notes:** Semantics should remain appropriate for a planning/context recap artifact.

---

## REQ status & SECR-12 boundary

### Q1: How should REQUIREMENTS.md update SECR-10/11 and ADMN/REVW-10/11/12?

| Option | Description | Selected |
|--------|-------------|----------|
| Mark verified + note Phase 11 ownership (Recommended) | Check these requirements as complete in REQUIREMENTS.md and record traceability/gap-closure ownership to Phase 11 (with pointers to 07/08-VERIFICATION). Clearly closes the audit gap for those items. | ✓ |
| Leave unchecked, add evidence notes only | Keep checkboxes unchecked and only add traceability notes pointing to Phase 11 artifacts. Conservative, but may not reflect "verified status" as the roadmap criterion requests. | |
| Mark complete without ownership notes | Check the boxes but skip explicit Phase 11 gap-closure ownership/traceability detail. Simpler, but weaker audit trail. | |

**User's choice:** Mark verified + note Phase 11 ownership (Recommended)
**Notes:** Applies to `SECR-10, SECR-11, ADMN-10, ADMN-11, ADMN-12, REVW-10, REVW-11, REVW-12`.

### Q2: How should Phase 11 update SECR-12?

| Option | Description | Selected |
|--------|-------------|----------|
| Unchecked + split ownership note (Recommended) | Leave SECR-12 unchecked until Phase 12 reconciles the Phase 9 contract, but add traceability noting Phase 11 verified the Phase 7 side (07-VERIFICATION.md) and Phase 12 owns remaining contract/ops closure. Avoids overlap and false completion. | ✓ |
| Mark checked as Phase 11 closed SECR-12 | Check SECR-12 now based on Phase 7-side evidence and document Phase 11 ownership only. Risks conflicting with Phase 12’s explicit reconciliation responsibility. | |
| No SECR-12 change in Phase 11 | Defer all SECR-12 traceability/status updates to Phase 12. Clean boundary, but Phase 11 would not reflect its own Phase 7-side verification contribution. | |

**User's choice:** Unchecked + split ownership note (Recommended)
**Notes:** Phase 11 verifies Phase 7 side in `07-VERIFICATION.md`; Phase 12 owns `/admin/expire` X-Cron-Secret-only contract reconciliation.

---

## OpenCode's Discretion

- Exact targeted test command selection/order and which result snippets to embed in `07-VERIFICATION.md`/`08-VERIFICATION.md`.
- Exact verification report structure/section headings and status wording, aligned with existing repo verification artifacts (e.g. 09/10) and auditable evidence standards.
- Precise frontmatter key names/values for `CONTEXT-SUMMARY.md` (beyond making ADMN-12/REVW-12 discoverable with accurate semantics).
- Exact phrasing/location of Phase 11 gap-closure ownership notes in `.planning/REQUIREMENTS.md`.

## Deferred Ideas

- Phase 12: reconcile Phase 9 `/admin/expire` X-Cron-Secret-only contract, stale 09 verification/ROADMAP wording, and Phase 9-side SECR-12/LIFE lifecycle-trust evidence.
- Phase 13: canonical branded host/env/CORS/API alignment and deploy/ops evidence closure for BRND-04 and related production-alignment concerns.
- Any live production/browser verification beyond documented human notes for Phase 7/8 UI behavior.
