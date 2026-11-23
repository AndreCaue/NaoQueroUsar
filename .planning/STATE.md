---
gsd_state_version: 1.0
milestone: v1.5
milestone_name: Integração Instagram na Revisão
status: planning
last_updated: "2026-11-23T11:02:46.726Z"
last_activity: 2026-11-23
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-11-23)

**Core value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.
**Current focus:** Planning next milestone

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-11-23 — Milestone v1.5 started

## Performance Metrics

**Velocity (v1.3):**

- Phases: 7 (19-25)
- Plans completed: 19
- Summaries: 20
- Timeline: 2026-11-17 → 2026-11-22
- Commits (v1.2..HEAD): 159
- Git diff: 313 files changed, +28139/-31792

**By Phase:**

| Phase | Plans | Status |
|-------|-------|--------|
| 19 | 2/2 | Complete |
| 20 | 2/2 | Complete |
| 21 | 2/2 | Complete |
| 22 | 3/3 | Complete |
| 23 | 5/5 | Complete |
| 24 | 3/3 | Complete |
| 25 | 2/2 | Complete |
| 26 | 2/2 | Complete |
| 27 | 1/1 | Complete |
| 28 | 3/3 | Complete |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting next work:

- v1.3 shipped with audit `tech_debt` (no critical blockers). Accepted residuals: CL-02 audit-open heuristic for 4 known quick tasks; D-14/WR-02 focus trap; runtime/browser deferments by item; Nyquist partial in 21/22/23/25.
- LLM extracts only parameters; deterministic search reuses `list_published`/`JobPublic`; chat never exposes contacts.
- Non-native chat fields remain limited/approximate and explicitly signaled.
- v1.4 roadmap: 3 phases (26-28), coarse granularity; ADMN-02 depends on ADMN-01 within Phase 26.
- Phase 28-02: Obsolete selected city cleaned in RSC via redirect to broad board URL when absent from available_cities.
- Phase 28-02: BoardToolbar renders only active city chips from board payload with token-based hover classes (no layout shift).
- Phase 28-03: SortDropdown uses custom button+listbox with aria-activedescendant, keyboard/outside-click/Escape handling, and focus return to trigger.
- Phase 28-03: Home hover feedback stays token-consistent (accent border/text + subtle accent/10 tint) with no layout-shifting hover styles.

### Pending Todos

None.

### Blockers/Concerns

- **v1.3 accepted residuals:** CL-02 audit-open heuristic may report u28/uik/krt/ttk `[missing]` (formally accepted, scoped; ttk PLAN-only deferred). D-14/WR-02 focus trap completo deferred. Runtime/browser/Nyquist residuals accepted per evidence.
- **Process debt:** `23-06-PLAN.md` and `23-07-PLAN.md` exist without SUMMARYs (stale gap-closure drafts superseded by Phases 24/25).
- **Carry-over (out of v1.3 scope):** v1.2 PUB-01..08 traceability, TEST-04/DOC-01/AUD-05 handoffs; v1.1 EXTR/PUBL/SRCH/UIUX caveats, canonical live smoke, DB-backed test reproducibility.

### Deferred Items

Items acknowledged and deferred at milestone v1.4 close on 2026-11-22:

| Category | Item | Status |
|----------|------|--------|
| quick_task | 261110-u28-bloquear-a-expressao-jacira-chavare-ao-c | missing (known v1.3 CL-02 heuristic residual; formally accepted) |
| quick_task | 261110-uik-remover-jacira-chavare-do-texto-colado-s | missing (known v1.3 CL-02 heuristic residual; formally accepted) |
| quick_task | 261111-krt-atualizar-next-16-4-6-eslint-9 | missing (known v1.3 CL-02 heuristic residual; formally accepted) |
| quick_task | 261112-ttk-escape-hatch-turnstile-teste-em-prod | missing (known v1.3 CL-02 heuristic residual; PLAN-only deferred, formally accepted) |
| uat_gap | Phase 26 26-HUMAN-UAT.md | partial (1 pending: live Turnstile/backend browser smoke) |
| verification_gap | Phase 26 26-VERIFICATION.md | human_needed (live smoke pending; no code gaps) |
| verification_gap | Phase 28 28-VERIFICATION.md | human_needed (human UAT acknowledged 2026-11-22, 5/5 passed) |

### Quick Tasks Completed

| Task | Disposition | Evidence |
|------|-------------|----------|
| 261110-u28-bloquear-a-expressao-jacira-chavare-ao-c | concluded (superseded behavior) | `.planning/quick/261110-u28-bloquear-a-expressao-jacira-chavare-ao-c/261110-u28-PLAN.md`, `261110-u28-SUMMARY.md` |
| 261110-uik-remover-jacira-chavare-do-texto-colado-s | concluded (vigente) | `.planning/quick/261110-uik-remover-jacira-chavare-do-texto-colado-s/261110-uik-PLAN.md`, `261110-uik-SUMMARY.md` |
| 261111-krt-atualizar-next-16-4-6-eslint-9 | concluded (historical evidence) | `.planning/quick/261111-krt-atualizar-next-16-4-6-eslint-9/261111-krt-PLAN.md`, `261111-krt-SUMMARY.md` |
| 261112-ttk-escape-hatch-turnstile-teste-em-prod | deferred justificado (not executed) | `.planning/quick/261112-ttk-escape-hatch-turnstile-teste-em-prod/261112-ttk-PLAN.md` (PLAN-only) |

## Session Continuity

Last session: 2026-11-22T22:24:51Z
Stopped at: Completed 28-03-PLAN.md
Resume file: None

## Operator Next Steps

- Start the next milestone with /gsd-new-milestone
