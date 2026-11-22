# Milestones

## v1.3 Chatbot Inteligente de Busca de Vagas (Shipped: 2026-11-22)

**Phases:** 19–25 (7 phases) | **Plans:** 19 completed | **Summaries:** 20
**Git range:** `v1.2..HEAD` (159 commits, 313 files changed, +28139/-31792)
**Audit:** `.planning/milestones/v1.3-MILESTONE-AUDIT.md` — **tech_debt** (17/17 requirements satisfied, 7/7 phases, no critical blockers; accepted residuals documented)

**Delivered:** Chatbot público de busca de vagas em linguagem natural (pt-BR) no board, sem login/fricção: extração de intenção estruturada e mapeamento determinístico seguro para busca existente, endpoint público `chat-search` resiliente com fallback/guardrails, UI de chat integrada ao fluxo canônico com interpretação transparente, e fechamento/hardening de auditoria com residuals explicitamente aceitos.

**Key accomplishments:**
1. Contrato de intenção pt-BR estrito + mapper determinístico server-authoritative (`q`, cidade whitelist SP/RJ/BH/Remoto, `sort`), com classificação aplicado/ignorado/aproximado e seam Groq isolado com fallback seguro — Phases 19, 24.
2. Endpoint público `POST /api/v1/public/chat-search` reutilizando `list_published`/`JobPublic` (sem contatos), com proteções (rate limit/tamanho/timeout), erros pt-BR seguros e fallback degradado controlado — Phase 20.
3. Chat drawer/modal mobile-first no board público, sem login, com interpretação transparente, resultados públicos, detalhe/reveal canônico preservado e apply-to-board via URL/filtros existentes — Phase 21.
4. Qualidade/hardening operacional: exemplos MVP validados/documentados, testes automatizados com LLM mockado, kill-switch/status/logging sem PII sensível e 22-SECURITY.md — Phase 22.
5. Fechamento de auditoria v1.3: reconciliação CL-01..CL-05, correções CR-01/WR-03/WR-01 viável, Nyquist/audit artifacts reconciliados e aceite formal CL-02 com residuals rastreáveis — Phases 23-25.

**Known gaps / deferred at close (accepted):**
- CL-02: `gsd-sdk query audit-open` pode reportar 4 quick tasks `[missing]` por heurística (u28/uik/krt/ttk) — aceite formal limitado a esses slugs, com evidência/justificativa; `261112-ttk` permanece PLAN-only deferred sem evidência de execução fabricada. Qualquer `[missing]` novo/inesperado bloqueia.
- D-14/WR-02: focus trap completo (Tab/Shift+Tab containment) no diálogo custom do chat — residual aceito explícito, não gap crítico aberto.
- Deferimentos runtime/browser/ambiente por item em UAT/verificação (sem execução fabricada); Nyquist parcial/desvio aceito em fases 21/22/23/25.
- Processo: `23-06-PLAN.md` e `23-07-PLAN.md` existem sem SUMMARYs (rascunhos stale de gap closure supersedidos pelas Phases 24/25) — dívida de processo documental.
- Carry-over fora do escopo v1.3: v1.2/v1.1 (PUB-01..08, TEST-04/DOC-01/AUD-05, EXTR/PUBL/SRCH/UIUX, smoke canônico/live, DB-backed test reproducibility).

**Archives:** [v1.3-ROADMAP.md](./milestones/v1.3-ROADMAP.md), [v1.3-REQUIREMENTS.md](./milestones/v1.3-REQUIREMENTS.md), [v1.3-MILESTONE-AUDIT.md](./milestones/v1.3-MILESTONE-AUDIT.md)

## v1.2 Integração com Facebook Pages (Shipped: 2026-11-17)

**Phases:** 14–18 (5 phases) | **Plans:** 16 | **Summaries:** 16  
**Git range:** `v1.1..HEAD` (`64034b0` baseline tag context not present locally as parent marker; 118 commits, 159 files changed in range)  
**Audit:** `.planning/v1.2-MILESTONE-AUDIT.md` — **not found** (completion proceeded anyway; gaps/handoffs accepted)

**Delivered (with known gaps/handoffs):** Implemented Facebook Pages integration foundation for approved jobs — secure social data/config, Meta OAuth/admin integrations, LLM/template social draft review/approval (site-first), async publishing worker with retry/idempotency/status/retry UI, and expanded tests/docs plus v1.1 gap-closure evidence artifacts.

**Key accomplishments:**
1. Built secure social foundation (migrations/models, Fernet token encryption, `SocialPublisher` contract, env/config docs) — Phase 14.
2. Delivered Meta OAuth connect/disconnect/status flow and admin Integrações UI with safe state handling — Phase 15.
3. Added social post draft generation/review/approval (LLM+fallback, edit/regenerate/schedule, site-first approve, policy/link handling) — Phase 16.
4. Implemented resilient async publishing pipeline (claim/lock, retry/backoff, idempotency, cron/status/retry APIs and admin visibility/actions) — Phase 17.
5. Produced automated coverage, operational docs/runbooks, and auditable gap-closure/handoff artifacts for social flow and v1.1 carry-over — Phase 18.

**Known gaps / deferred at close (accepted):**
- No `v1.2-MILESTONE-AUDIT.md`; `gsd-sdk audit-open` reported 11 open items at pre-flight (legacy verification/uat gaps and incomplete quick tasks).
- `PUB-01..PUB-08` remain unchecked/pending in archived v1.2 requirements traceability/body despite Phase 17 completion artifacts — traceability/evidence reconciliation required.
- `TEST-04`, `DOC-01`, `AUD-05` partial+handoff (real Meta dev/live execution, DB-backed reproducible runs, canonical browser/runtime smoke, and human verifications pending).
- Phase 16/17/18 verification contexts include `human_needed` items; runtime/canonical validations not fully executed in this environment.
- Carried v1.1 gaps/debt remain (EXTR/PUBL/SRCH/UIUX unsatisfied in audited scope, prior env/ops caveats).

**Archives:** [v1.2-ROADMAP.md](./milestones/v1.2-ROADMAP.md), [v1.2-REQUIREMENTS.md](./milestones/v1.2-REQUIREMENTS.md)

## v1.1 EmpregaNoix (Shipped: 2026-11-15)

**Phases:** 7–13 (7 phases) | **Plans:** 21 | **Summaries:** 22  
**Git range:** recent milestone commits through `64034b0` (see repo history)  
**Audit:** `.planning/v1.1-MILESTONE-AUDIT.md` — **gaps_found** (accepted at completion)

**Delivered (with accepted gaps):** Continued v1.0 work under EmpregaNoix brand: contact reveal/anti-spam hardening, admin review flow completion and evidence backfill, lifecycle/trust/legal contract reconciliation, rebranding, and canonical host/deploy-ops alignment (contractual/mapped evidence).

**Key accomplishments:**
1. Hardened public contact reveal and anti-spam (server-side Turnstile-gated reveal, fail-closed/rate-limited paths) — Phase 7.
2. Completed admin review workflow and traceability/evidence backfill (JWT-protected login/queue, approve/edit/delete) — Phases 8 & 11.
3. Reconciled lifecycle/trust/legal contracts (DB-owned 14-day expiry, X-Cron-Secret-only `/admin/expire` per T-06-01, legal/report surfaces) — Phases 9 & 12.
4. Rebranded to EmpregaNoix and aligned canonical host/deploy/ops guidance with mapped evidence and handoff — Phases 10 & 13.
5. Closed audit-driven verification/traceability gaps where possible, with residual caveats explicitly documented.

**Known gaps / tech debt (accepted):**
- Unsatisfied reqs in audited scope: EXTR-10/11/12, PUBL-10/11/12/13/14, SRCH-10/11/12, UIUX-10/11/12.
- Partial/caveated reqs: ADMN-10/11/12, REVW-10/11/12, SECR-10/11/12, LIFE-10/11/12/13, TRST-11, BRND-04 (env-blocked DB tests, human/browser checks, ops handoff).
- Missing `11-VERIFICATION.md`; Phases 7–8 verifications `gaps_found`; Nyquist missing/partial.
- Canonical-host live smoke/provisioning execution pending (handoff); test DB reproducibility issues noted in audit.

**Archives:** [v1.1-ROADMAP.md](./milestones/v1.1-ROADMAP.md), [v1.1-REQUIREMENTS.md](./milestones/v1.1-REQUIREMENTS.md), [v1.1-MILESTONE-AUDIT.md](./milestones/v1.1-MILESTONE-AUDIT.md)
