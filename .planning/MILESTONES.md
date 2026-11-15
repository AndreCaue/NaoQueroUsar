# Milestones

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

