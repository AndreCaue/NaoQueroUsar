# Phase 23: Fechamento de débitos de auditoria e validação v1.3 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-19
**Phase:** 23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3
**Areas discussed:** CL-01 cidade/debug, CL-02 quick tasks e reconciliação, CL-03 UAT/verificação 21-22, CL-04/05 Nyquist, warnings e audit

---

## CL-01: cidade/debug

| Option | Description | Selected |
|--------|-------------|----------|
| Hardening + testes (Recomendado) | Corrigir o edge case do token `rio` no mapper/raw-text, adicionar regressões (backend e/ou frontend se aplicável) e então validar o caso reportado. | ✓ |
| Só validar 22-04 | Não alterar código além do que já existe; focar em reteste/documentação do caso reportado com os fixes atuais. | |
| Você decide | Deixa o planner escolher o menor escopo seguro com base no código atual e no risco do review. | |

**User's choice:** Hardening + testes (Recomendado)
**Notes:** Contexto considerado: fix 22-04 já existente (toolbar + fallback mapper), mas 22-REVIEW apontou risco de `\brio\b` classificar "Rio Grande do Sul"/"Rio Branco" como Rio de Janeiro.

| Option | Description | Selected |
|--------|-------------|----------|
| Fix + reteste runtime registrado (Recomendado) | Executar e registrar o reteste manual/runtime do caso reportado (toolbar/chat) nos artefatos de UAT/verificação quando o ambiente permitir; fechar o debug com evidência observada. | ✓ |
| Fix + evidência, reteste deferido | Fechar com evidência automatizada/estática disponível e registrar reteste runtime como deferimento aceito e justificado se não for executável no ambiente atual. | |
| Deferimento formal do bug | Não afirmar resolução; registrar decisão/justificativa e manter item como deferred/aceito no audit. | |

**User's choice:** Fix + reteste runtime registrado (Recomendado)
**Notes:** 22-HUMAN-UAT/22-MANUAL-UAT ainda tinham reteste pendente do caso reportado.

| Option | Description | Selected |
|--------|-------------|----------|
| Atualizar todos os artefatos (Recomendado) | Atualizar `.planning/debug/city-filter-and-chat-ignores-registered-city.md`, 22-HUMAN/MANUAL-UAT e 22-VERIFICATION conforme resultado, e refletir no `v1.3-MILESTONE-AUDIT.md`. | ✓ |
| Resumo em audit + contexto da fase | Registrar principalmente no audit/artefatos da Phase 23, com referências aos existentes. | |
| Você decide | Deixa o planner definir o conjunto mínimo de artefatos a atualizar para satisfazer CL-01/CL-05. | |

**User's choice:** Atualizar todos os artefatos (Recomendado)
**Notes:** Priorizar rastreabilidade completa para audit-open/milestone.

| Option | Description | Selected |
|--------|-------------|----------|
| Testes automatizados + docs (Recomendado) | Adicionar/ajustar testes determinísticos (mapper/parser/chat ou frontend cities) e atualizar matriz/UAT/notas relevantes. | ✓ |
| Só reteste manual documentado | Confiar em validação manual/runtime registrada, sem novos testes automatizados. | |
| Você decide | Planner escolhe a evidência proporcional ao risco da mudança. | |

**User's choice:** Testes automatizados + docs (Recomendado)
**Notes:** Evidência executável para o hardening de cidade.

---

## CL-02: quick tasks e reconciliação

| Option | Description | Selected |
|--------|-------------|----------|
| Ambas concluídas, uik final (Recomendado) | Registrar `u28` e `uik` como concluídas com evidência, deixando explícito que `uik` é o comportamento vigente que supersede `u28`. | ✓ |
| u28 superseded, uik concluída | Marcar `u28` como superseded/deferida por substituição e `uik` como concluída com evidência. | |
| Você decide | Planner define a classificação mais consistente com os artefatos existentes e o critério de audit-open. | |

**User's choice:** Ambas concluídas, uik final (Recomendado)
**Notes:** `u28` e `uik` possuem PLAN+SUMMARY; `uik` substituiu bloqueio por remoção automática do termo.

| Option | Description | Selected |
|--------|-------------|----------|
| Concluída com evidência existente (Recomendado) | Aceitar o SUMMARY/commits como evidência suficiente para fechar CL-02 sem reexecutar tudo. | ✓ |
| Revalidar agora e registrar | Rodar novamente verificações viáveis e anexar evidência atual antes de fechar. | |
| Você decide | Planner escolhe se a evidência histórica é suficiente ou se precisa de revalidação. | |

**User's choice:** Concluída com evidência existente (Recomendado)
**Notes:** `261111-krt` possui PLAN+SUMMARY com verificações registradas.

| Option | Description | Selected |
|--------|-------------|----------|
| Deferred justificado (Recomendado) | Converter em item explicitamente deferido com justificativa, removendo-o de `missing/incomplete` no audit-open. | ✓ |
| Executar/validar agora se viável | Tentar concluir com evidência real nesta fase. | |
| Concluir por evidência documental | Considerar PLAN/código existente como suficiente sem execução comprovada. | |

**User's choice:** Deferred justificado (Recomendado)
**Notes:** `261112-ttk` tem apenas PLAN (sem SUMMARY) e envolve teste em produção/ambiente controlado.

| Option | Description | Selected |
|--------|-------------|----------|
| STATE + audit + referências (Recomendado) | Atualizar `.planning/STATE.md`, `.planning/v1.3-MILESTONE-AUDIT.md` e referências necessárias apontando evidência ou justificativa de deferimento por task. | ✓ |
| Só audit da fase/milestone | Registrar a decisão principalmente no audit/artefatos da Phase 23. | |
| Você decide | Planner define o conjunto mínimo de artefatos para satisfazer CL-02 sem inconsistências. | |

**User's choice:** STATE + audit + referências (Recomendado)
**Notes:** Garantir que nenhuma task permaneça `missing/incomplete` no contexto de audit-open.

---

## CL-03: UAT/verificação 21-22

| Option | Description | Selected |
|--------|-------------|----------|
| Reconciliar com UAT existente (Recomendado) | Atualizar `21-VERIFICATION.md` para refletir que os checks humanos foram concluídos com base no `21-HUMAN-UAT.md`. | ✓ |
| Reexecutar checks humanos da Fase 21 | Refazer/registrar novamente a validação humana do chat/board antes de atualizar a verificação. | |
| Você decide | Planner escolhe o caminho mínimo para reconciliar 21-VERIFICATION com as evidências disponíveis. | |

**User's choice:** Reconciliar com UAT existente (Recomendado)
**Notes:** `21-HUMAN-UAT.md` está completo (4/4 pass) enquanto `21-VERIFICATION.md` segue `human_needed`.

| Option | Description | Selected |
|--------|-------------|----------|
| Reteste CL-01 + deferimento documentado (Recomendado) | Executar/registrar o reteste do caso de cidade e documentar deferimento aceito por item para o que for inviável no ambiente. | ✓ |
| Executar todo o UAT/manual 22 | Tentar executar todos os casos de `22-HUMAN-UAT.md` e `22-MANUAL-UAT.md` com evidência completa. | |
| Apenas consolidar evidência existente/deferir | Não executar novos retestes; fechar com base no que já existe e deferir o restante. | |

**User's choice:** Reteste CL-01 + deferimento documentado (Recomendado)
**Notes:** Alinhado a CL-01 (reteste runtime registrado). Preservar/reconciliar itens já passados em 22-HUMAN-UAT.

| Option | Description | Selected |
|--------|-------------|----------|
| Estados finais aceitos e rastreáveis (Recomendado) | Atualizar artefatos para estados finais coerentes documentando resultados executados e deferimentos aceitos por item inviável. | ✓ |
| Só anexar evidência, manter status atuais | Adicionar notas/resultados sem mudar `human_needed`/`partial`/`draft`. | |
| Você decide | Planner define os estados/formatos finais compatíveis com os padrões dos artefatos e com o audit. | |

**User's choice:** Estados finais aceitos e rastreáveis (Recomendado)
**Notes:** Critério CL-03 exige que 21/22-VERIFICATION saiam de `human_needed`, 22-HUMAN-UAT de `partial` e 22-MANUAL-UAT de `draft` com resolução registrada.

| Option | Description | Selected |
|--------|-------------|----------|
| Deferimento por item com justificativa (Recomendado) | Registrar item a item o que foi executado, o que não foi, por que é inviável, risco residual e condição para validação futura. | ✓ |
| Deferimento global da fase de UAT | Uma justificativa geral para pendências restantes. | |
| Não aceitar deferimentos | Exigir execução completa de todos os itens. | |

**User's choice:** Deferimento por item com justificativa (Recomendado)
**Notes:** Política para itens inviáveis em ambiente (browser/runtime/dados/infra).

---

## CL-04/05: Nyquist, warnings e audit

| Option | Description | Selected |
|--------|-------------|----------|
| Compliance quando viável + desvio documentado (Recomendado) | Criar `20-VALIDATION.md` e evoluir 19/21/22 buscando `nyquist_compliant` onde factível; registrar desvio aceito com plano de ação quando não atendível. | ✓ |
| Apenas desvios aceitos documentados | Não perseguir compliance formal; registrar desvio aceito/plano de ação em todos os arquivos aplicáveis. | |
| Você decide | Planner define o equilíbrio por fase conforme evidência existente. | |

**User's choice:** Compliance quando viável + desvio documentado (Recomendado)
**Notes:** 20-VALIDATION.md ausente; 19/21/22 com `nyquist_compliant: false`.

| Option | Description | Selected |
|--------|-------------|----------|
| Corrigir parse + canApply; a11y viável (Recomendado) | Endurecer `chatSearch` (JSON 200 malformado), corrigir `canApplyChatToBoard` (evitar no-op) e fazer melhorias focadas de foco/a11y quando viáveis; deferir explicitamente o que não for viável. | ✓ |
| Corrigir os 3 completamente | Exigir correção completa de parse, canApply e acessibilidade/foco do chat/detail. | |
| Só documentar/deferir warnings de código | Não alterar código; registrar justificativa de não atendimento/deferimento no audit. | |

**User's choice:** Corrigir parse + canApply; a11y viável (Recomendado)
**Notes:** Warnings da auditoria: `chatSearch` sem parse defensivo em 200, `canApplyChatToBoard` pode habilitar apply no-op para cidade não-normalizável, e gaps de foco/a11y no chat/detail.

| Option | Description | Selected |
|--------|-------------|----------|
| Criar SECURITY.md da Phase 22 (Recomendado) | Produzir `22-SECURITY.md` documentando controles/revisão aplicáveis ao chat e limitações conhecidas. | ✓ |
| Executar/alinhar a secure-phase 22 | Seguir o fluxo de `/gsd-secure-phase 22` como base e registrar o resultado/artefato gerado. | |
| Deferir com justificativa | Registrar por que a revisão/artefato de segurança não será concluído agora e qual ação futura recomendada. | |

**User's choice:** Criar SECURITY.md da Phase 22 (Recomendado)
**Notes:** `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/SECURITY.md` (ou 22-SECURITY.md) ausente.

| Option | Description | Selected |
|--------|-------------|----------|
| Atualizar audit in-place + checar audit-open (Recomendado) | Atualizar `.planning/v1.3-MILESTONE-AUDIT.md` com status final por débito e validar que `gsd-sdk query audit-open` não reporte itens novos desta fase. | ✓ |
| Criar novo audit e substituir referência | Gerar novo arquivo de auditoria v1.3 e atualizar referências. | |
| Você decide | Planner define a forma de atualização desde que reflita fielmente a resolução e permita fechamento do v1.3. | |

**User's choice:** Atualizar audit in-place + checar audit-open (Recomendado)
**Notes:** Gate final de fechamento do milestone v1.3.

---

## OpenCode's Discretion

- Implementação exata do hardening do padrão `rio` no fallback raw-text (fronteiras/contexto/negações para "Rio Grande do Sul", "Rio Branco" etc.) sem perder casos suportados e sem inferir cidades fora da whitelist.
- Forma de tornar `canApplyChatToBoard`/mapeamento robusto a cidade não-normalizável sem quebrar casos suportados (`sao-paulo`, `rio-de-janeiro`, `belo-horizonte`, `remoto`) nem gerar apply vazio enganoso.
- Escopo mínimo de melhorias de foco/a11y considerado viável nesta fase e registro objetivo de qualquer deferimento explícito restante.
- Estrutura/redação final dos estados aceitos em VERIFICATION/UAT/MANUAL-UAT/VALIDATION e do `22-SECURITY.md`, desde que rastreáveis e honestos.
- Forma de reconciliar `STATE.md`/`REQUIREMENTS.md` e executar a checagem final de `audit-open`.

## Deferred Ideas

None — discussion stayed within phase scope. (`261112-ttk` tratado como deferred justificado dentro de CL-02, não como ideia fora de escopo.)
