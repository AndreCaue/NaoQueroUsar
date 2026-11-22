# Phase 25: Reconciliar gates de fechamento e revalidar auditoria v1.3 - Context

**Gathered:** 2026-11-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Tornar o fechamento do v1.3 rastreável e limpo após as correções das Phases 23–24, reconciliando o residual de gate CL-02 e atualizando evidências de verificação/auditoria para re-audit do milestone. Esta fase cobre: (1) **CL-02** — disposição final rastreável das 4 quick tasks pré-existentes reportadas por heurística no `gsd-sdk query audit-open`, com aceite formal explícito apenas para esses slugs conhecidos quando evidência/disposição existir, sem fabricar evidência; (2) **reconciliação de artefatos de verificação/UAT pós-fix** para refletir estado após Phase 24 (CL-01/CL-02/CL-05), incluindo 23-VERIFICATION, 24-VERIFICATION e 24-HUMAN-UAT, de modo que gaps reais sejam reconciliados e residuals aceitos fiquem explícitos; (3) **atualização in-place do `v1.3-MILESTONE-AUDIT.md`** para estado de re-audit, com débitos críticos resolvidos, residuals aceitos separados e prontidão para `/gsd-audit-milestone`; (4) **D-14/WR-02 (focus trap completo)** permanece explicitamente documentado como deferimento aceito, nunca como gap aberto.

**Fora de escopo:** novas funcionalidades de produto, mudanças de contrato público/API/`JobPublic`, expansão de busca/chat, execução de validação runtime/browser fora do ambiente disponível (exceto registro honesto de deferimento por item), fabricar evidência para quick task/validação, reabrir carry-over v1.1/v1.2, ou transformar residual aceito D-14/WR-02 em implementação de focus trap completo.

</domain>

<decisions>
## Implementation Decisions

### Política do gate audit-open / CL-02
- **D-01:** **Aceite formal limitado à heurística dos 4 quick tasks.** O `gsd-sdk query audit-open` pode ser considerado reconciliado para CL-02 se os únicos `[missing]` forem os 4 slugs pré-existentes conhecidos: `261110-u28-bloquear-a-expressao-jacira-chavare-ao-c`, `261110-uik-remover-jacira-chavare-do-texto-colado-s`, `261111-krt-atualizar-next-16-4-6-eslint-9`, `261112-ttk-escape-hatch-turnstile-teste-em-prod`. Cada um deve ter evidência ou deferimento justificado citado. **Nenhum outro item `[missing]` novo/inesperado** pode ser aceito por essa política; item novo bloqueia.
- **D-02:** **Demais itens do audit-open são reconciliação real, não aceite CL-02.** Os itens atuais não-CL-02 reportados pelo audit-open (23-VERIFICATION `gaps_found`, 24-VERIFICATION `human_needed`, 24-HUMAN-UAT `unknown` com 2 cenários pendentes) devem ser reconciliados nesta fase via atualização de artefatos/estados finais rastreáveis (SC2/SC3), não tratados como residual heurístico CL-02.
- **D-03:** **Registro da aceitação formal em três lugares.** Documentar a aceitação CL-02 em `v1.3-MILESTONE-AUDIT.md` (seção de gate/aceitação explícita com escopo, justificativa, evidência por task e comando observado), `REQUIREMENTS.md` (nota em CL-02) e `STATE.md` (estado/reconciliação). Manter coerência com o padrão de reconciliação da Phase 23.
- **D-04:** **CL-02 completo com aceite formal explícito.** CL-02 permanece completo/satisfeito nos artefatos de fechamento, com nota clara: disposições evidenciadas/justificadas; residual heurístico `audit-open` formalmente aceito com escopo e justificativa; sem fabricar evidência. `261112-ttk` permanece PLAN-only/deferred justificado.

### Estratégia de reconciliação de verificação
- **D-05:** **`23-VERIFICATION.md` atualizado in-place com re-verificação datada.** Adicionar seção de re-verificação/reconciliação citando evidência da Phase 24 (24-VERIFICATION, testes determinísticos, 24-REVIEW/artefatos aplicáveis). Preservar histórico original; atualizar status/score/gaps para refletir CR-01/WR-01/WR-03 resolvidos pela Phase 24 e residuals aceitos explícitos.
- **D-06:** **Status final de 23-VERIFICATION: `gaps_closed_with_accepted_residuals`.** Reflete que gaps críticos de código foram fechados pela Phase 24, mas permanecem residuals aceitos/documentados (CL-02 heurística aceita, D-14/WR-02 focus trap deferido, deferimentos runtime/UI por item quando aplicável). Não mascarar residuals como ausência de risco.
- **D-07:** **`24-VERIFICATION.md` reconciliado para estado final aceito com deferimentos por item.** Preservar as 8/8 truths verificadas e evidência automatizada; registrar os 2 checks de teclado/browser como deferimentos aceitos por item (motivo, risco residual, ação futura), seguindo padrão D-12/22-VERIFICATION. Não rebaixar para `passed` sem qualificação nem manter `human_needed` como pendência aberta não reconciliada.
- **D-08:** **`23-REVIEW.md` permanece histórico.** Não reescrever o review point-in-time (`issues_found`, CR-01/WR-01/WR-03). A resolução é cross-referenciada em 23-VERIFICATION re-verificada, 24-VERIFICATION, e `v1.3-MILESTONE-AUDIT.md`.

### Fechamento dos cenários 24-HUMAN-UAT
- **D-09:** **Deferimento aceito por item para os 2 cenários pendentes.** Os cenários WR-01 de `24-HUMAN-UAT.md` (foco teclado ao fechar detalhe aberto pelo chat; tentativa de fechar chat com detalhe aberto) são fechados como deferimentos aceitos por item, com motivo (ambiente browser/integrado indisponível nesta execução), risco residual, e condição/ação futura. Não afirmar execução manual não realizada.
- **D-10:** **`24-HUMAN-UAT.md` com status final `complete` (com deferimentos aceitos).** Mesmo padrão de `22-HUMAN-UAT.md`: status final rastreável `complete`, cenários pendentes resolvidos por deferimento aceito por item, sem estado ambíguo `partial`.
- **D-11:** **Expectativa de saída do audit-open por reconciliação.** Atualizar 24-HUMAN-UAT/24-VERIFICATION para estados finais aceitos/rastreáveis de modo que o scanner `audit-open` não os reporte mais como gaps abertos. Se ainda reportar por comportamento heurístico inesperado, documentar explicitamente o residual com escopo/justificativa; não aplicar aceite formal CL-02 por padrão a esses itens.

### Forma final do v1.3-MILESTONE-AUDIT.md
- **D-12:** **Status final do audit: `passed` com residuals aceitos.** O `v1.3-MILESTONE-AUDIT.md` deve ficar closure-ready/pronto para `/gsd-audit-milestone`: requisitos v1.3 satisfeitos ou formalmente aceitos com evidência; débitos críticos resolvidos; residuals não-bloqueantes explicitamente documentados. Não manter `gaps_found` após resolução dos débitos críticos.
- **D-13:** **CL-01, CL-02 e CL-05 satisfeitos com evidência e residuals separados.** Na tabela de requisitos, marcar CL-01/CL-02/CL-05 como satisfeitos/fechados com evidência curta (Phase 24 fix determinístico + reconciliação; aceite formal CL-02; correções CL-05 viáveis + residual D-14/WR-02). Mover itens críticos resolvidos para histórico fechado/resolvido; manter apenas residuals aceitos em `tech_debt`/`accepted_residuals`.
- **D-14:** **Atualizar scores e status por fase com consistência interna.** Phase 23: `gaps_closed_with_accepted_residuals`. Phase 24: aceito com deferimentos runtime/keyboard por item. Atualizar scores (requirements/phases/integration/flows conforme evidência), resumo de Nyquist e listas de gaps para refletir estado pós-fix. Não manter scores antigos inconsistentes com o texto.
- **D-15:** **D-14/WR-02 residual aceito explícito e prontidão para re-audit.** D-14/WR-02 (focus trap completo no chat) fica somente em seção de residual aceito/tech debt com justificativa, risco residual e ação futura; nunca em gaps abertos. O audit declara explicitamente que débitos críticos foram resolvidos e que o milestone está pronto para `/gsd-audit-milestone`.

### OpenCode's Discretion
- Redação exata das seções de re-verificação/reconciliação nos artefatos, desde que preserve histórico, datas, evidências e semântica das decisões.
- Forma do estado final aceito de `24-VERIFICATION.md` (nome de status equivalente a `accepted_with_deferred_runtime_checks`/padrão 22) desde que rastreável e não ambíguo.
- Estrutura interna do `v1.3-MILESTONE-AUDIT.md` (seções/tabelas) desde que mantenha consistência de frontmatter/scores/gaps/tech_debt e clareza de re-audit.
- Nível de detalhe das notas em `STATE.md` e `REQUIREMENTS.md`, desde que citem os 4 slugs, evidência/disposição e condição “nenhum `[missing]` novo”.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e fechamento do milestone
- `.planning/ROADMAP.md` §Phase 25 — Goal, success criteria, dependência da Phase 24, gap closure CL-02/CL-05.
- `.planning/REQUIREMENTS.md` — CL-02 e CL-05 (alvo desta fase), CL-01/CL-03/CL-04 como contexto de fechamento; INT/API/UI/QA não podem regredir.
- `.planning/v1.3-MILESTONE-AUDIT.md` — Audit atual `gaps_found` a atualizar in-place; fonte de gaps CL-01/CL-02/CL-05, scores e tech debt.
- `.planning/STATE.md` — Estado atual, decisões acumuladas, quick tasks e deferred items; deve refletir reconciliação final.

### Evidências de verificação/UAT a reconciliar
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-VERIFICATION.md` — `gaps_found` pré-Phase-24; deve receber re-verificação in-place.
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-REVIEW.md` — Review histórico `issues_found` (CR-01/WR-01/WR-03); manter histórico, cross-referenciar resolução.
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-VERIFICATION.md` — `human_needed`, 8/8 truths; base para reconciliar CL-01/WR-01/WR-03 e deferimentos runtime.
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-HUMAN-UAT.md` — 2 cenários WR-01 pendentes; fechar por deferimento aceito por item.
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-REVIEW.md` — Evidência de review pós-gap closure (sem achados críticos registrados no fluxo da fase).

### Quick tasks / gate CL-02
- `.planning/quick/261110-u28-bloquear-a-expressao-jacira-chavare-ao-c/261110-u28-PLAN.md` — Evidência/escopo original u28.
- `.planning/quick/261110-u28-bloquear-a-expressao-jacira-chavare-ao-c/261110-u28-SUMMARY.md` — Evidência de conclusão u28 (supersedida por uik).
- `.planning/quick/261110-uik-remover-jacira-chavare-do-texto-colado-s/261110-uik-PLAN.md` — Plano uik.
- `.planning/quick/261110-uik-remover-jacira-chavare-do-texto-colado-s/261110-uik-SUMMARY.md` — Evidência de conclusão uik (vigente).
- `.planning/quick/261111-krt-atualizar-next-16-4-6-eslint-9/261111-krt-PLAN.md` — Plano krt.
- `.planning/quick/261111-krt-atualizar-next-16-4-6-eslint-9/261111-krt-SUMMARY.md` — Evidência de conclusão krt.
- `.planning/quick/261112-ttk-escape-hatch-turnstile-teste-em-prod/261112-ttk-PLAN.md` — PLAN-only; base para deferimento justificado sem fabricar execução.

### Decisões e contratos prévios
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-CONTEXT.md` — Padrões D-07/D-12/D-13/D-14/D-16 para evidência honesta, deferimento por item, Nyquist e atualização in-place de audit.
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-CONTEXT.md` — Fechamento de CR-01/WR-01/WR-03 e escopo de gap closure.
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md` — Padrão de UAT `complete` com deferimentos aceitos por item.
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-VERIFICATION.md` — Padrão de verificação aceita com checks runtime deferidos.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `gsd-sdk query audit-open`: gate operacional observado; hoje reporta 7 itens (4 quick tasks `[missing]`, 1 UAT gap Phase 24, 2 verification gaps 23/24). Usar como evidência de comando, não como única fonte sem interpretação.
- Artefatos Phase 23 de reconciliação: `23-VERIFICATION.md`, `22-HUMAN-UAT.md`, `22-VERIFICATION.md`, `v1.3-MILESTONE-AUDIT.md` já seguem padrão de deferimento/aceite explícito.
- Artefatos Phase 24: `24-VERIFICATION.md` (8/8 truths, `human_needed`), `24-HUMAN-UAT.md` (2 pendentes), `24-REVIEW.md` e summaries/planos com evidência determinística.

### Established Patterns
- **Evidência honesta, sem fabricação:** ttk permanece PLAN-only; runtime/browser não executado deve ser deferimento aceito por item (D-12/D-07).
- **Reconciliação in-place rastreável:** atualizar artefatos existentes com datas/status/evidência, preservando histórico quando apropriado.
- **Residuals aceitos separados de gaps abertos:** D-14/WR-02 e deferimentos runtime ficam em tech debt/accepted residuals, não em gaps críticos.
- **Gate audit-open heurístico:** pode divergir da realidade documental; aceitar formalmente apenas com escopo explícito e sem novos missing.

### Integration Points
- `.planning/v1.3-MILESTONE-AUDIT.md`: principal artefato de fechamento/re-audit.
- `.planning/phases/23-.../23-VERIFICATION.md`, `.planning/phases/24-.../24-VERIFICATION.md`, `.planning/phases/24-.../24-HUMAN-UAT.md`: reconciliação de estado pós-fix.
- `.planning/STATE.md`, `.planning/REQUIREMENTS.md`: rastreabilidade de CL-02/CL-05 e gate.
- `.planning/quick/2611*-*/`: evidência/disposição das 4 quick tasks CL-02.

</code_context>

<specifics>
## Specific Ideas

- Estado observado do `gsd-sdk query audit-open` em 2026-11-22: 7 itens totais — 4 quick tasks `[missing]` (u28/uik/krt/ttk), 1 UAT gap (`24-HUMAN-UAT.md` unknown, 2 pending), 2 verification gaps (`23-VERIFICATION.md` gaps_found, `24-VERIFICATION.md` human_needed).
- SC1 do ROADMAP já autoriza aceite formal explícito para o residual heurístico dos 4 quick tasks se disposições estiverem evidenciadas/justificadas, sem fabricar evidência.
- Phase 24 fechou CR-01/WR-01/WR-03 em código com evidência determinística; os 2 itens pendentes em 24-HUMAN-UAT são validação browser/teclado WR-01.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 25-reconciliar-gates-de-fechamento-e-revalidar-auditoria-v1-3*
*Context gathered: 2026-11-22*
