---
gsd_state_version: 1.0
milestone: v1.5
milestone_name: Integração Instagram na Revisão
status: executing
stopped_at: Phase 31 context gathered
last_updated: "2026-11-25T22:42:28.039Z"
last_activity: 2026-11-25 -- Phase 31 planning complete
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 8
  completed_plans: 6
  percent: 50
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-11-23)

**Core value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.
**Current focus:** Phase 30 — instagram-review-experience

## Current Position

Phase: 30 (instagram-review-experience) — EXECUTING
Plan: 3 of 3 (gap closure 30-03 complete)
Status: Ready to execute
Last activity: 2026-11-25 -- Phase 31 planning complete

Progress: [██████████] 100%

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
| Phase 29 P01 | 8min | 3 tasks | 15 files |
| Phase 29 P02 | 25min | 3 tasks | 12 files |
| Phase 29 P03 | 5min | 2 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- v1.5 roadmap: 4 phases (29-32), coarse granularity, continuing numbering from v1.4. All 17 v1.5 requirements mapped (META/IMAG/REVW/PUBL/HARD).
- Research SUMMARY.md suggested 4 phases; adopted with same dependency chain and explicit discuss-phase decision callouts.
- Instagram publish must remain independent from Facebook (no regression, no coupling). Site-first/best-effort social patterns from v1.2 remain relevant.
- Open decisions (resolve in discuss-phase/plan-time, not silently assumed): image origin (logo/card gerado/upload), card format/storage/serving, image generation strategy, token renewal/alert strategy.
- Meta permission/App Review/Advanced Access assumptions must be confirmed before live rollout; keep Graph API version config-driven.
- Ambiguous IG publish outcomes must never trigger blind auto-retry; rate-limit handling must avoid retry storms and treat `content_publishing_limit` as runtime authority.
- v1.3/v1.4 accepted residuals remain accepted carry-over unless explicitly pulled into scope.
- [Phase ?]: 29-01: IG readiness additive on SocialAccount; FB status authoritative, IG refreshed on connect/verify (D-13/D-14/D-15)
- [Phase 29]: Public IG media serves exact job_id+version hash and rebuilds only when requested version matches current job hash
- [Phase 29]: IG media hash uses only card-relevant job fields; contact-only edits do not invalidate version hash
- [Phase 29]: Integrations UI shows additive IG readiness with actionable pt-BR states; META-03 live Meta verification is explicit handoff (D-15)

### Pending Todos

None.

### Blockers/Concerns

- **v1.5 open decisions:** Image origin, card format/storage/serving, image generation strategy, and token renewal/alert strategy must be resolved during discuss/plan phases.
- **Meta platform verification:** Permissions/scopes/App Review/roles/tasks/Page↔IG linkage assumptions need confirmation against current Meta dashboard/app mode before live rollout.
- **v1.3 accepted residuals:** CL-02 audit-open heuristic may report u28/uik/krt/ttk `[missing]` (formally accepted, scoped; ttk PLAN-only deferred). D-14/WR-02 focus trap completo deferred. Runtime/browser/Nyquist residuals accepted per evidence.
- **Process debt:** `23-06-PLAN.md` and `23-07-PLAN.md` exist without SUMMARYs (stale gap-closure drafts superseded by Phases 24/25).
- **Carry-over (out of v1.5 scope unless pulled in):** v1.4 IntegrationsClient 401 recovery alignment, Phase 26 live smoke, Nyquist partial 26/27/28; v1.2 PUB-01..08 traceability, TEST-04/DOC-01/AUD-05 handoffs; v1.1 EXTR/PUBL/SRCH/UIUX caveats, canonical live smoke, DB-backed test reproducibility.

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

Last session: 2026-11-25T21:49:30.720Z
Stopped at: Phase 31 context gathered
Resume file: .planning/phases/31-independent-publish-pipeline/31-CONTEXT.md
Next: Re-verify Phase 30 (`/gsd-verify-work 30` or `/gsd-execute-phase 30` verification flow) then proceed to Phase 31 planning
