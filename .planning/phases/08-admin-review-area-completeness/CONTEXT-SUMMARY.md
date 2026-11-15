---
phase: 08-admin-review-area-completeness
type: context-summary
requirements-referenced:
  - ADMN-12
  - REVW-12
---

Created: .planning/phases/08-admin-review-area-completeness/08-CONTEXT.md

## Decisions Captured

### Full End-to-End Flow
- **E2E_Flow_01**: Valid outcome when extraction returns 0 valid jobs: return summary with saved_pending=0, discarded=[...], appropriate alerts; frontend shows "Nenhuma vaga encontrada no texto"
- **E2E_Flow_02**: Auto-deduplication: if same text is pasted, suppress duplicate and notify admin
- **E2E_Flow_03**: Block edit if both contacts cleared: show error "Vaga precisa ter ao menos um contato (email ou telefone)" (422)
- **E2E_Flow_04**: Post-approve UI: optimistic update — immediately remove approved item from pending queue; then refetch in background
- **D-01**: Fila principal exibe apenas vagas `pending`; `needs_review` em aba separada
- **D-02**: Ordenação padrão: mais recentes primeiro (`created_at DESC`), tie-break por `id DESC`
- **D-03**: Filtro por cidade: chips SP, RJ, BH, Remoto; sem busca por texto livre
- **D-E2E-03**: Edicao bloqueada se ambos contatos limpos; erro 422 "Vaga precisa ter ao menos um contato"
- **D-E2E-05**: Exclusao hard delete; idempotente naturalmente (404 na segunda chamada) (traceability context for REVW-12/ADMN-12)
- **D-E2E-06**: Toast notifications proprio + atualizacao otimista da fila
- **D-E2E-07**: Area admin protegida: Authorization Bearer JWT; 401 sem autenticacao
- **D-E2E-08**: Painel admin adota Tailwind v4, paridade visual com publico
- **D-E2E-09**: Hub /admin com links para /admin/paste e /admin/review
- **D-E2E-10**: Pos-aprovacao: otimista update remove item da fila imediatamente

## Traceability (Phase 11 repair)

- Referenced requirements (discoverable): **ADMN-12**, **REVW-12** (context/decision recap; not an execution-completion claim).
- Evidence/cross-reference artifacts:
  - `.planning/phases/08-admin-review-area-completeness/08-CONTEXT.md`
  - `.planning/phases/08-admin-review-area-completeness/08-03-PLAN.md`
  - `.planning/phases/08-admin-review-area-completeness/08-03-SUMMARY.md`
  - `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md` (Phase 11 backfill verification for ADMN-12/REVW-12, including delete contract mapping: `DELETE /api/v1/admin/jobs/{job_id}` hard delete; repeat call returns 404 / idempotent-in-effect)

---

## ▶ Next Up — NQU NaoQueroUsar

**Phase 8: Admin Review Area Completeness** — Terminar área de revisão admin — fila pending, aprovar/editar/excluir vagas com texto-fonte ao lado, publicar, com o fluxo completo colar → extrair → revisar → aprovar funcionando

/gsd-plan-phase 8 .planning

**Also available:**
- /gsd-ui-phase 8 .planning for UI design contracts
- review/edit CONTEXT.md before continuing