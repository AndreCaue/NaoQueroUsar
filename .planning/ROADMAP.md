# Roadmap: EmpregaNoix v1.1

## Overview

Continuation of v1.0 (NQU — NaoQueroUsar) under the new EmpregaNoix brand. Milestone v1.1 focuses on completing remaining work from Phases 3, 5, and 6, finalizing the 14-day expiry/hard delete lifecycle, completing the admin review area, and preparing the rebranding from NaoQueroUsar to EmpregaNoix. The core value "Procurar um emprego, não deve dar trabalho" is preserved.

## Milestone Summary

**Milestone v1.1: EmpregaNoix**

- **Goal:** Complete remaining development work from v1.0 and prepare for production deployment under the EmpregaNoix brand — contact reveal finalization, admin review enhancements, deployment infrastructure, and rebranding.
- **Target features:** Finish Phase 3 (contact reveal + anti-spam finish), Phase 5 (admin review area finish), Phase 6 (lifecycle, trust, legal & launch completeness), BRND (rebranding).
- **Key context:** Project at v1.0 with 6 phases completed/in-progress. v1.1 continues phase numbering sequentially from 7. Research completed 2026-10-13; key gaps: Groq model retirement (resolved: `openai/gpt-oss-20b`/`120b`), Turnstile placement, pending job expiry policy, admin auth model. All carried forward and addressed in this milestone.

## Phase Numbering

- Integer phases (7, 8, 9, 10): Planned milestone work
- Decimal phases (7.1, 7.2): Urgent insertions (marked with INSERTED)
- Decimal phases appear between their surrounding integers in numeric order.

## Phases

**Phase 7: Contact Reveal & Anti-Spam Completeness** — Contact reveal finalization, Turnstile server-side verify hardening, anti-spam edge cases

**Phase 8: Admin Review Area Completeness** — Admin review queue finish, approve/edit/excluir workflow, pending job management

**Phase 9: Lifecycle, Trust, Legal & Launch Completeness** — 14-day expiry hard delete, CRON_SECRET endpoint, LGPD pages, deployment infrastructure

**Phase 10: Rebranding & Launch Preparation (EmpregaNoix)** — Renomear de NaoQueroUsar para EmpregaNoix, atualizar textos, hosts, CORS, meta tags

**Phase 11: Verify Phases 7–8 & Close Reveal/Admin/Review Evidence Gaps** — Backfill missing 07/08 verification artifacts and traceability for SECR/ADMN/REVW (audit gap closure)

**Phase 12: Reconcile Phase 9 Lifecycle/Trust Verification & Contracts** — Align 09 verification, ROADMAP contract, and LIFE/TRST/SECR evidence (audit gap closure)

**Phase 13: Canonical Host, Deploy & Ops Alignment (BRND-04 closeout)** — Resolve branded-host/env/CORS/API drift and record aligned deploy evidence (audit gap closure)

## Phase Details

### Phase 7: Contact Reveal & Anti-Spam Completeness

**Goal:** Finalizar superfície de revelar contato e endurecer anti-spam — garantir que o endpoint de reveal está plenamente server-side gated, rate-limited e que os edge cases de Turnstile são cobertos.

**Depends on:** Phase 1 (schema/expires_at), completed Phase 3 foundation

**Requirements:** SECR-10, SECR-11, SECR-12

**Success Criteria** (what must be TRUE):

1. Endpoint `POST /api/v1/public/jobs/{id}/reveal-contact` roda exclusivamente server-side — contact fields **ausentes** do payload público de lista/detalhe; só retornados após Turnstile Siteverify bem-sucedido
2. Turnstile Siteverify é chamado com `secret`, `response` (token), `remoteip` (via `CF-Connecting-IP` ou `X-Forwarded-For` primeira parte) — validação fail-closed; tokens `timeout-or-duplicate` são tratados como 403
3. Endpoint tem rate limiting por IP — excesso de requisições é bloqueado com 429 e `Retry-After` em pt-BR; knobs `REVEAL_RATE_LIMIT=10/min` e `LOGIN_RATE_LIMIT=5/min` configurados via env
4. Turnstile widget no client usa `next-turnstile@1.0.7` com `key` para remount (nenhum `resetKey` disponível); token consumido nunca pode ser reenviado; login admin também protegido por Turnstile contra credential stuffing
5. Turnstile analytics mostram validacoes não-zero em producao; chaves de teste `1x`/`2x`/`3x` aceitas em `mode=test`, chaves de producao rejeitadas por validador fail-closed

### Phase 8: Admin Review Area Completeness

**Goal:** Terminar área de revisão admin — fila `pending`, aprovar/editar/excluir vagas com texto-fonte ao lado, publicar, com o fluxo completo colar → extrair → revisar → aprovar funcionando.

**Depends on:** Phase 1 (auth), Phase 2 (extração), Phase 4 (tema)

**Requirements:** ADMN-10, ADMN-11, ADMN-12, REVW-10, REVW-11, REVW-12

**Success Criteria** (what must be TRUE):

1. Admin autenticado (JWT no header Authorization) vê a fila de vagas com status `pending` — cards com preview do texto-fonte ao lado dos campos extraídos
2. Admin aprova uma vaga — status muda para `published` e ela passa a aparecer na home pública imediatamente; edição de campos pelo ID também persiste com validação de regra de ao menos um contato
3. Admin exclui uma vaga — remoção hard do banco; operação idempotente (exclusão duplicada é no-op); fluxo completo colar → extrair → revisar → aprovar funciona de ponta a ponta consumindo o endpoint de extração da Fase 2
4. A área admin é protegida: acesso sem sessão autenticada é negado (401); rota `/admin/extract` e rotas de CRUD exigem `Authorization: Bearer <token>`
5. Toast notifications e feedback visual para ações de approve/edit/delete; admin vê quais vagas foram descartadas vs aprovadas

**Cross-cutting constraints:** must_haves.truths entries appearing in 2+ plans:
- D-01: Autorização via JWT Bearer token em todas as rotas admin
- D-02: Ordenação padrão por `created_at DESC` com tie-break em `id DESC`
- D-E2E-01: Extração bem-sucedida retorna summary válido mesmo com 0 vagas salvas
- D-E2E-02: Auto-deduplicação de pastas pelo hash normalizado (lowercase, acentos removidos, espaços collapsed)
- D-E2E-05: Exclusão é hard delete e idempotente (404 na segunda chamada)
- D-E2E-06: Feedback via toast próprio, sem dependência de bibliotecas externas

**Wave dependencies:**
- **Wave 1** (08-01): Admin queue view e proteção de rota — bloqueia waves 2 e 3
- **Wave 2** (08-02): Ações de approve/editar — depende da wave 1 (lista autenticada)
- **Wave 3** (08-03): Ação de delete + integração E2E — depende das waves 1 e 2

### Phase 9: Lifecycle, Trust, Legal & Launch Completeness

**Goal:** Garantir que o board se mantenha honesto e seguro — vagas somem em 14 dias de forma confiável, e a plataforma tem postura de confiança/legal e deploy prontos para lançar.

**Depends on:** Phase 1 (schema/expires_at), Phase 4 (board público)

**Requirements:** LIFE-10, LIFE-11, LIFE-12, TRST-10, TRST-11, TRST-12

**Success Criteria** (what must be TRUE):

1. Cada vaga nasce com `expires_at` = `created_at` + 14 dias; server_default verificado no modelo e migration; `expires_at` é `timestamptz` computed em UTC via `NOW()` do banco; vaga futura NÃO é deletada por cron
2. Vagas `published` expiradas são hard-deleted por endpoint `/admin/expire` protegido exclusivamente por header `X-Cron-Secret` (um Bearer JWT de admin NÃO é aceito — T-06-01) — declaração idempotente em UTC; chamada duplicada não causa erro; nenhuma vaga futura é apagada
3. Vagas `pending` não revisadas também expiram após 14 dias — mesma regra de 14 dias aplicada; tabela não cresce indefinidamente
4. Páginas de privacidade (`/privacidade`), termos (`/termos-de-uso`) e aviso LGPD `"somos apenas meio de divulgação"` existem e são acessíveis; política pt-BR com 13 sections (Privacidade) e 10 sections (Termos de Uso/foro Americana/SP)
5. Visitante pode denunciar uma vaga via endpoint `/jobs/{id}/report` — motivo opcional (máx 500 chars), logs estruturados sem persistir reports; badge "Vaga revisada" aparece em vaga com status `published` e aprovada pelo master
6. Frontend (Vercel) e backend (Render) estão deployados com CORS travado à origem do front e segredos configurados por env; cold-start documentado; path de leitura pública permanece rápido quando backend está acordando (first request ~1-2s acceptable)

**Wave dependencies:**
- **Wave 1** (09-01): Provas de lifecycle/trust no backend — DDL de 14 dias, sweep para todos os status, report 500/no-persistência e correção documental T-06-01 — bloqueia waves 2 e 3
- **Wave 2** (09-02): Páginas legais dentro do shell público, aviso de intermediário e verificação do badge/relatório — depende da wave 1
- **Wave 3** (09-03): CORS fail-closed, hardening do blueprint Render e gate de fumaça com o aviso exato — depende das waves 1 e 2

### Phase 10: Rebranding & Launch Preparation (EmpregaNoix)

**Goal:** Renomear a aplicação de NaoQueroUsar para EmpregaNoix em todo o frontend e infraestrutura, garantindo consistência de marca e configurações de deploy.

**Depends on:** All previous phases (3–9)

**Requirements:** BRND-01, BRND-02, BRND-03, BRND-04

**Success Criteria** (what must be TRUE):

1. Todo o texto do frontend (labels, headings, buttons, mensagens) atualizado de "NaoQueroUsar" / "NQU" para "EmpregaNoix" — incluindo meta tags, headings, alertas, Toast messages, favicons, textos estáticos
2. Slogan mantido "Procurar um emprego, não deve dar trabalho" — refletido na nova marca; atualizado em todos os lugares onde aparecia a referência antiga
3. Cores da marca consistentes: roxo principal `#8b5cf6` / `#a78bfa` para texto, fundos escuros `#0f0a1a` / `#1a1025`, botão Doações amarelo `#facc15` discreto — aplicados no novo build Tailwind v4 com `@theme` variables
4. Hosts atualizados: backend `https://empreganoix.onrender.com`, frontend `https://empreganoix.vercel.app`; CORS configurado para origens `https://empreganoix.vercel.app`; `NEXT_PUBLIC_API_BASE_URL` apontando para o novo host Render; `ALLOWED_ORIGINS` atualizado no backend
5. Deploy Vercel + Render executado com sucesso; smoke gate verde: health 200, env=prod, Turnstile mode=live, CORS preflight 200 com `Access-Control-Allow-Origin`; `CRON_SECRET` configurado em ambos os hosts; cold-start UX documentada

### Phase 11: Verify Phases 7–8 & Close Reveal/Admin/Review Evidence Gaps

**Goal:** Backfill missing phase-level verification and traceability so reveal, admin, and review requirements are auditable with concrete evidence.

**Depends on:** Phases 7, 8 (completed implementation) and `.planning/v1.1-MILESTONE-AUDIT.md`

**Requirements:** SECR-10, SECR-11, SECR-12, ADMN-10, ADMN-11, ADMN-12, REVW-10, REVW-11, REVW-12

**Gap Closure:** Closes audit gaps for missing `07-VERIFICATION.md`/`08-VERIFICATION.md`, incomplete Phase 8 summary/context frontmatter, and unverified/misaligned requirement evidence for Phase 7–8 scope.

**Success Criteria** (what must be TRUE):

1. `07-VERIFICATION.md` exists and verifies SECR-10/11/12 evidence for Phase 7 (server-side reveal gating, Turnstile Siteverify fail-closed behavior including timeout-or-duplicate handling, per-IP rate limiting with pt-BR 429/`Retry-After`, login Turnstile protection) and documents the SECR-10 operational rebuild caveat.
2. `08-VERIFICATION.md` exists and verifies ADMN-10/11/12 and REVW-10/11/12 (Turnstile-gated/rate-limited admin login, JWT-protected admin routes/queue, approve/edit/delete flows including hard delete/idempotent contract and required UI/acceptance behavior).
3. Phase 8 artifact traceability is repaired where needed (e.g. `08-03-SUMMARY.md`, `CONTEXT-SUMMARY.md` frontmatter/cross-references for `ADMN-12`, `REVW-12`) so requirement completion claims are machine-checkable.
4. `.planning/REQUIREMENTS.md` checkboxes/traceability for the above REQ-IDs reflect verified status and gap-closure ownership for Phase 11.

### Phase 12: Reconcile Phase 9 Lifecycle/Trust Verification & Contracts

**Goal:** Align Phase 9 verification artifacts and planning contracts with the implemented lifecycle, trust, and cron-secret-only security behavior.

**Depends on:** Phase 9 (completed implementation, including 09-04 evidence) and `.planning/v1.1-MILESTONE-AUDIT.md`

**Requirements:** LIFE-10, LIFE-11, LIFE-12, LIFE-13, TRST-11, SECR-12

**Gap Closure:** Closes audit gaps for stale/gaps_found `09-VERIFICATION.md`, ROADMAP `/admin/expire` auth contract drift (T-06-01), and unverified/unchecked lifecycle-trust requirements.

**Success Criteria** (what must be TRUE):

1. ROADMAP Phase 9 criterion/contract text no longer states `/admin/expire` accepts Bearer JWT admin; it explicitly reflects **X-Cron-Secret-only** protection (fail-closed) consistent with implementation, tests, and docs.
2. `09-VERIFICATION.md` is reconciled with current repository state and evidence (DB-owned `expires_at` 14-day UTC, status-agnostic idempotent expiry sweep, cron-secret-only endpoint, report endpoint log-only/capped/throttled behavior, legal pages/badge), with any remaining human-gated production checks explicitly documented.
3. Lifecycle/ops readiness flow is no longer broken by contract/documentation mismatch; evidence references are current and traceable.
4. `.planning/REQUIREMENTS.md` checkboxes/traceability for `LIFE-10..13`, `TRST-11`, and Phase 9 side of `SECR-12` reflect verified status and gap-closure ownership for Phase 12.

### Phase 13: Canonical Host, Deploy & Ops Alignment (BRND-04 closeout)

**Goal:** Eliminate canonical branded-host and deploy configuration drift so production operations, CORS, and evidence match the intended EmpregaNoix contract.

**Depends on:** Phase 10 (rebrand/deploy artifacts) and `.planning/v1.1-MILESTONE-AUDIT.md`

**Requirements:** BRND-04, SECR-12, LIFE-13

**Gap Closure:** Closes audit gaps for canonical host mismatch (`empreganoix.vercel.app` / `empreganoix.onrender.com` vs recorded deployed hosts), env/CORS/API alignment risk, and lifecycle/ops deploy-readiness flow caveats.

**Success Criteria** (what must be TRUE):

1. Intended canonical production domains are confirmed and consistently applied across frontend API base config, backend allowed origins/CORS, deploy config, and operator docs (`docs/DEPLOY.md`, `render.yaml`, Vercel/Render env guidance as applicable).
2. Deploy/smoke evidence is recorded for the aligned hosts (or explicitly documented with canonical mapping), covering health/env/Turnstile mode, CORS preflight, cron endpoint auth/idempotency, and key public/admin surfaces as relevant.
3. BRND-04 operational caveat is resolved or explicitly closed with evidence; lifecycle/ops readiness flow is no longer at risk from host/env drift.
4. `.planning/REQUIREMENTS.md` and roadmap notes reflect BRND-04 closure status and any SECR-12/LIFE-13 production-alignment evidence tied to Phase 13.

## Progress

**Execution Order:** Phases execute in numeric order: 7 → 8 → 9 → 10 → 11 → 12 → 13

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 7. Contact Reveal & Anti-Spam Completeness | 3/3 | ✓ Complete | 2026-11-12 |
| 8. Admin Review Area Completeness | 3/3 | ✓ Complete | 2026-11-13 |
| 9. Lifecycle, Trust, Legal & Launch Completeness | 4/4 | ✓ Complete | 2026-11-15 |
| 10. Rebranding & Launch Preparation (EmpregaNoix) | 4/4 | ✓ Complete | 2026-11-14 |
| 11. Verify Phases 7–8 & Close Reveal/Admin/Review Evidence Gaps | 0/TBD | Not started | - |
| 12. Reconcile Phase 9 Lifecycle/Trust Verification & Contracts | 0/TBD | Not started | - |
| 13. Canonical Host, Deploy & Ops Alignment (BRND-04 closeout) | 0/TBD | Not started | - |

## Commit History Note

This roadmap continues from the v1.0 roadmap (Phases 1–6, completed 2026-10-15 through 2026-11-12). v1.1 phases 7–10 complete the remaining work and rebranding under the EmpregaNoix name. All v1.0 requirements (ADMN-01/02/03, EXTR-01/.../09, REVW-01/.../05, PUBL-01/.../06, SRCH-01/.../03, UIUX-01/.../03, SECR-01/.../03, LIFE-01/.../04, TRST-01/.../03) remain mapped from the previous milestone; v1.1 adds new REQ-IDs BRND-01/04 and continues the remaining ADMN-10/12, REVW-10/12, EXTR-10/12, PUBL-10/14, SRCH-10/12, SECR-10/12, LIFE-10/12, TRST-10/12 from the incomplete portions of v1.0 phases.

---

*Roadmap defined: 2026-11-12*
*Milestone v1.1: EmpregaNoix*