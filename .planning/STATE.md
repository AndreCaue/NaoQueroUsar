---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Chatbot Inteligente de Busca de Vagas
status: planning
stopped_at: Phase 21 context gathered
last_updated: "2026-11-18T00:01:39.433Z"
last_activity: 2026-11-18
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 4
  completed_plans: 4
  percent: 50
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-11-17)

**Core value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.
**Current focus:** Phase 21 — interface de chat e integracao no board

## Current Position

Phase: 21
Plan: Not started
Status: Ready to plan
Last activity: 2026-11-18

Progress: [██▌-------] 25%

## Performance Metrics

**Velocity (v1.2, as tracked):**

- Total plans completed (v1.2): 16
- Timeline: 2026-11-15 → 2026-11-17
- Git range (approx): `v1.1..HEAD`

**By Phase:**

| Phase | Plans | Status |
|-------|-------|--------|
| 14 | 3/3 | Complete |
| 15 | 3/3 | Complete |
| 16 | 3/3 | Complete |
| 17 | 3/3 | Complete |
| 18 | 4/4 | Complete |
| 19 | 2/2 | Complete |

*Historical/v1.1 metrics preserved in archives and prior history.*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- v1.3 scope: chatbot NL → extração de parâmetros → busca existente → UI de chat (INT/API/UI/QA-01..03). Carry-over v1.2/v1.1 explicitamente fora deste milestone.
- LLM extrai apenas parâmetros (nunca recebe corpus de vagas); busca determinística reutiliza `GET /api/v1/public/jobs` / `list_published` e `JobPublic` (sem contatos no chat).
- Campos não nativos (salário/modalidade/contrato/senioridade) tratados como suporte limitado/aproximado e sinalizado, sem afirmar filtragem inexistente.
- Roadmap v1.3: 4 phases (19–22), coarse granularity, 100% coverage (12/12).
- Phase 19: contrato de intenção estrito + mapeamento determinístico server-authoritative (`q/city/sort`), seam Groq isolado com prompt seguro/fallback determinístico; campos não nativos nunca viram filtro estruturado garantido.

### Pending Todos

None tracked.

### Blockers/Concerns

- **v1.2 close accepted gaps (out of v1.3 scope):** reconcile `PUB-01..08` traceability/evidence; execute real handoffs for `TEST-04`, `DOC-01`, `AUD-05` (Meta dev/live, DB-backed reproducible runs, canonical/browser/runtime smoke, human verifications).
- **Carried from v1.1 (accepted, out of v1.3 scope):** EXTR-10/11/12, PUBL-10/11/12/13/14, SRCH-10/11/12, UIUX-10/11/12 unsatisfied in audited scope; canonical-host live smoke/provisioning pending; DB-backed test reproducibility issues (`relation "jobs" does not exist` in recorded runs); see `.planning/milestones/v1.1-MILESTONE-AUDIT.md`.
- **v1.3 risks to watch:** fidelidade de filtros não nativos (salário/modalidade/contrato), limites/custos/latência Groq em endpoint público, e preservação do fluxo público sem fricção/sem exposição de contatos.

### Quick Tasks Completed

None yet.

## Deferred Items

Items acknowledged/deferred at or before v1.2 close (2026-11-17):

| Category | Item | Status |
|----------|------|--------|
| audit | v1.2 milestone audit missing; completion proceeded with known gaps/handoffs accepted | accepted |
| requirements | PUB-01..PUB-08 traceability/evidence reconciliation pending (Phase 17 artifacts exist) | pending |
| requirements | TEST-04, DOC-01, AUD-05 real execution/human/runtime handoffs pending | partial+handoff |
| audit | v1.1-MILESTONE-AUDIT gaps carried (EXTR/PUBL/SRCH/UIUX unsatisfied in audited scope, etc.) | deferred/accepted |
| ops | Live canonical-host smoke/provisioning on `empreganoix.vercel.app` / `empreganoix.onrender.com` | pending handoff |
| testing | Reproducible migrated test DB for DB-backed suites (`jobs` relation) | deferred |
| quick_task | 261110-u28-bloquear-a-expressao-jacira-chavare-ao-c | incomplete |
| quick_task | 261110-uik-remover-jacira-chavare-do-texto-colado-s | incomplete |
| quick_task | 261111-krt-atualizar-next-16-4-6-eslint-9 | incomplete |
| quick_task | 261112-ttk-escape-hatch-turnstile-teste-em-prod | incomplete |

## Session Continuity

Last session: 2026-11-18T00:01:39.395Z
Stopped at: Phase 21 context gathered
Resume file: .planning/phases/21-interface-de-chat-e-integracao-no-board/21-CONTEXT.md
