# Phase 25: Reconciliar gates de fechamento e revalidar auditoria v1.3 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-22
**Phase:** 25-reconciliar-gates-de-fechamento-e-revalidar-auditoria-v1-3
**Areas discussed:** Política do gate audit-open/CL-02, Estratégia de reconciliação de verificação, Fechamento dos cenários 24-HUMAN-UAT, Forma final do v1.3-MILESTONE-AUDIT.md

---

## Política do gate audit-open / CL-02

| Option | Description | Selected |
|--------|-------------|----------|
| Aceitar só heurística dos 4 quick tasks (Recomendado) | Formaliza aceitação explícita apenas para os 4 quick tasks `[missing]` pré-existentes, com escopo/justificativa/evidência. Os outros itens do audit-open (23/24 verification, 24-HUMAN-UAT) devem ser reconciliados nesta fase via SC2/SC3, não “aceitos” como heurística CL-02. | ✓ |
| Aceitar todo o audit-open atual como residual formal | Registra aceitação formal para todos os 7 itens atuais do audit-open, incluindo verification/UAT gaps. Mais simples, mas pode mascarar pendências que o roadmap já esperava reconciliar. | |
| Exigir audit-open totalmente limpo | Só fecha se o comando não reportar nenhum item. Pode exigir mudanças fora do controle da heurística (quick tasks) ou execução runtime/browser para UAT/verificação. | |

**User's choice:** Aceitar só heurística dos 4 quick tasks (Recomendado)
**Notes:** Os 4 quick tasks conhecidos são u28, uik, krt, ttk. Demais itens audit-open devem ser reconciliados por estado final rastreável.

| Option | Description | Selected |
|--------|-------------|----------|
| Audit + REQUIREMENTS + STATE (Recomendado) | Atualiza `v1.3-MILESTONE-AUDIT.md` com seção de gate/aceitação explícita (escopo, justificativa, evidência por task, comando observado), mantém disposições em `STATE.md` e nota em `REQUIREMENTS.md` CL-02. Rastreabilidade completa e coerente com padrão Phase 23. | ✓ |
| Somente no v1.3-MILESTONE-AUDIT.md | Registra a aceitação formal apenas no audit. Menos duplicação, mas deixa STATE/REQUIREMENTS sem referência explícita ao gate heurístico residual. | |
| Audit + artefato dedicado de fechamento | Cria um artefato específico de fechamento/gate (ex.: nota em Phase 25) além do audit. Mais explícito, mas adiciona mais um documento para manter consistente. | |

**User's choice:** Audit + REQUIREMENTS + STATE (Recomendado)
**Notes:** Nenhum.

| Option | Description | Selected |
|--------|-------------|----------|
| Complete com aceite formal explícito (Recomendado) | CL-02 permanece completo/satisfeito nos artefatos, com nota clara: disposições evidenciadas/justificadas; residual de heurística `audit-open` formalmente aceito com escopo e justificativa; sem fabricar evidência (ttk continua PLAN-only/deferred). | ✓ |
| Complete, mas só com ressalva “gate heurístico” | Marca completo, mas linguagem mais cautelosa em todo lugar. Pode deixar ambiguidade se não definir claramente que o aceite é formal e suficiente para fechamento. | |
| Bloqueado até audit-open parar de reportar | Mantém CL-02 insatisfeito enquanto a heurística reportar missing. Contradiz SC1 do roadmap e pode travar fechamento por limitação de ferramenta. | |

**User's choice:** Complete com aceite formal explícito (Recomendado)
**Notes:** Sem fabricar evidência para ttk.

| Option | Description | Selected |
|--------|-------------|----------|
| Só os 4 slugs conhecidos, com evidência/disposição (Recomendado) | Aceite formal se aplica apenas a 261110-u28, 261110-uik, 261111-krt, 261112-ttk; cada um com evidência ou deferimento justificado citado; nenhum outro item `[missing]` novo/inesperado. Qualquer novo item bloqueia. | ✓ |
| Qualquer quick task missing pode ser aceito se documentado | Permite aceitar novos quick tasks missing desde que haja justificativa. Flexível, mas abre brecha para fechar gate com pendências não analisadas. | |
| Aceitar os 4 e ignorar contagem total | Aceita os 4 conhecidos sem verificar se surgiram outros missing. Simples, mas frágil a regressões/novos itens. | |

**User's choice:** Só os 4 slugs conhecidos, com evidência/disposição (Recomendado)
**Notes:** Condição objetiva de aceite CL-02.

---

## Estratégia de reconciliação de verificação

| Option | Description | Selected |
|--------|-------------|----------|
| Atualizar 23-VERIFICATION in-place com re-verificação (Recomendado) | Adicionar seção de re-verificação/reconciliação datada citando evidência da Phase 24 (24-VERIFICATION, testes, review). Atualiza status/score/gaps para refletir CR-01/WR-01/WR-03 resolvidos, mantendo histórico e residuals aceitos explícitos. Alinha com padrão de reconciliação da Phase 23. | ✓ |
| Manter 23-VERIFICATION histórico e criar 23 gap-closure VERIFICATION | Preserva 23-VERIFICATION como snapshot histórico imutável e cria novo artefato de verificação de gap closure. Mais puro historicamente, mas adiciona outro artefato e pode confundir qual é canônico. | |
| Usar apenas 24-VERIFICATION como evidência pós-fix | Não altera 23-VERIFICATION; aponta 24-VERIFICATION/audit como fonte de verdade pós-fix. Simples, mas deixa 23-VERIFICATION em `gaps_found` contradizendo o estado real pós-Phase-24. | |

**User's choice:** Atualizar 23-VERIFICATION in-place com re-verificação (Recomendado)
**Notes:** Preservar histórico original.

| Option | Description | Selected |
|--------|-------------|----------|
| Aceitar com deferimentos por item (Recomendado) | Reconciliar para estado final aceito rastreável (ex.: `accepted_with_deferred_runtime_checks`/padrão 22), preservando as 8/8 truths e registrando os 2 checks como deferimentos aceitos por item com motivo/risco residual/ação futura. Coerente com D-12. | ✓ |
| Manter human_needed até execução manual | Não muda status até alguém executar os 2 cenários em browser. Mais rigoroso, mas pode travar fechamento do milestone no ambiente atual. | |
| Rebaixar para passed com nota informal | Marca como passed porque o código está verificado e deixa os checks manuais como nota. Arriscado: pode confundir evidência automatizada com validação humana não executada. | |

**User's choice:** Aceitar com deferimentos por item (Recomendado)
**Notes:** Aplica-se a `24-VERIFICATION.md`.

| Option | Description | Selected |
|--------|-------------|----------|
| gaps_closed_with_accepted_residuals (Recomendado) | Reflete que os gaps críticos de código (CR-01/WR-01/WR-03) foram fechados pela Phase 24, mas permanecem residuals aceitos/documentados (CL-02 heurística aceita, D-14/WR-02 focus trap, runtime/UI deferido por item). Histórico preservado. | ✓ |
| passed | Marca como passed. Simples, mas pode esconder que ainda existem residuals aceitos (heurística CL-02, D-14/WR-02, deferimentos runtime). Exige texto muito cuidadoso. | |
| accepted_with_deferred_items | Usa linguagem de aceite/deferimento (similar a 22). Bom para residuals, mas pode soar como se os gaps de código não tivessem sido corrigidos, quando na verdade foram fechados na Phase 24. | |

**User's choice:** gaps_closed_with_accepted_residuals (Recomendado)
**Notes:** Status final para `23-VERIFICATION.md`.

| Option | Description | Selected |
|--------|-------------|----------|
| Manter histórico, só cross-referenciar (Recomendado) | Não reescreve o review point-in-time. A reconciliação em 23-VERIFICATION/24-VERIFICATION/audit cita que os achados foram resolvidos pela Phase 24. Preserva integridade histórica do review. | ✓ |
| Atualizar 23-REVIEW com resolução dos achados | Edita o review para marcar CR-01/WR-01/WR-03 resolvidos. Mais “atual”, mas altera um artefato de review histórico e pode confundir o que foi observado na época. | |

**User's choice:** Manter histórico, só cross-referenciar (Recomendado)
**Notes:** Aplica-se a `23-REVIEW.md`.

---

## Fechamento dos cenários 24-HUMAN-UAT

| Option | Description | Selected |
|--------|-------------|----------|
| Deferimento aceito por item (Recomendado) | Marcar cada cenário como deferimento aceito com motivo (ambiente browser/integrado indisponível), risco residual, e condição/ação futura. Status final do UAT fica rastreável/complete com deferimentos, alinhado ao padrão D-12/22-HUMAN-UAT. | ✓ |
| Execução manual obrigatória antes de fechar v1.3 | Mantém cenários pending até alguém validar em browser real. Maior confiança, mas pode bloquear fechamento do milestone no ambiente atual. | |
| Fechar como “não aplicável / coberto por testes” | Marca como coberto por testes determinísticos e fecha sem deferimento runtime. Arriscado: testes helper não provam comportamento real de foco/dialog nativo no browser. | |

**User's choice:** Deferimento aceito por item (Recomendado)
**Notes:** 2 cenários WR-01 pendentes em `24-HUMAN-UAT.md`.

| Option | Description | Selected |
|--------|-------------|----------|
| complete (com deferimentos aceitos) (Recomendado) | Mesmo padrão de `22-HUMAN-UAT.md`: status final `complete`, com cada cenário pendente resolvido como deferimento aceito por item e rastreabilidade explícita. Evita estado ambíguo `partial`. | ✓ |
| partial-accepted | Sinaliza que não foi executado manualmente, mas foi aceito. Mais explícito sobre não-execução, porém foge do padrão já usado na Phase 22. | |

**User's choice:** complete (com deferimentos aceitos) (Recomendado)
**Notes:** Status final para `24-HUMAN-UAT.md`.

| Option | Description | Selected |
|--------|-------------|----------|
| Reconciliar artefatos para sair do audit-open (Recomendado) | Atualizar 24-HUMAN-UAT/24-VERIFICATION para estados finais aceitos/rastreáveis de modo que o scanner não os reporte mais como gaps abertos. Se ainda reportar, tratar como bug/heurística a documentar explicitamente. | ✓ |
| Aceitar formalmente como residual mesmo se scanner reportar | Aplica aceite formal tipo CL-02 também para UAT/verification gaps. Mais permissivo, mas enfraquece o sinal do audit-open e pode mascarar reconciliação incompleta. | |

**User's choice:** Reconciliar artefatos para sair do audit-open (Recomendado)
**Notes:** Não aplicar aceite formal CL-02 por padrão a esses itens.

---

## Forma final do v1.3-MILESTONE-AUDIT.md

| Option | Description | Selected |
|--------|-------------|----------|
| passed com residuals aceitos (Recomendado) | Status `passed`/closure-ready: todos os requisitos v1.3 satisfeitos ou formalmente aceitos com evidência; débitos críticos resolvidos; residuals não-bloqueantes (D-14/WR-02, deferimentos runtime, Nyquist 21/22 desvio aceito, ttk PLAN-only) listados explicitamente em tech_debt/accepted residuals. Pronto para `/gsd-audit-milestone`. | ✓ |
| gaps_found, mas só com residuals aceitos | Mantém `gaps_found` mesmo com aceite formal. Conservador, mas contradiz “débitos críticos resolvidos” e pode bloquear o fluxo de fechamento desnecessariamente. | |
| tech_debt (sem gaps críticos) | Usa status intermediário para sinalizar residuals. Pode ser útil se o ecossistema GSD tratar `tech_debt` distintamente; precisa garantir que o milestone seja considerado pronto para re-audit/fechamento. | |

**User's choice:** passed com residuals aceitos (Recomendado)
**Notes:** Audit final closure-ready.

| Option | Description | Selected |
|--------|-------------|----------|
| Satisfeitos com evidência e residuals separados (Recomendado) | Marcar CL-01/CL-02/CL-05 como satisfeitos/fechados na tabela de requisitos, com evidência curta (Phase 24/23 reconciliação, aceite formal CL-02). Mover itens críticos resolvidos para “resolved/closed”; manter apenas residuals aceitos em `tech_debt`/`accepted_residuals`. | ✓ |
| Satisfeitos, mas manter histórico de gaps no corpo | Marca satisfeitos na tabela, mas mantém seção de gaps antiga intacta com anotação “resolvido”. Mais histórico, porém pode deixar leitura ambígua sobre o estado atual. | |
| Parcial/accepted no score, sem “satisfied” pleno | Evita dizer “satisfied”, usa “accepted/partial”. Conservador, mas conflita com a decisão de status `passed` e com a resolução real dos débitos críticos. | |

**User's choice:** Satisfeitos com evidência e residuals separados (Recomendado)
**Notes:** Aplica-se a CL-01, CL-02, CL-05.

| Option | Description | Selected |
|--------|-------------|----------|
| Atualizar scores e status por fase (Recomendado) | Phase 23: `gaps_closed_with_accepted_residuals`; Phase 24: `accepted_with_deferred_runtime_checks` (ou equivalente). Atualiza scores (requirements 17/17 ou 17/17 com aceites formais, phases/flows/integration coerentes), Nyquist summary e lista de gaps para refletir estado pós-fix. | ✓ |
| Atualizar só texto, manter scores antigos | Mantém scores/gaps antigos para histórico e adiciona notas. Fácil, mas o audit fica internamente inconsistente e confuso para re-audit. | |

**User's choice:** Atualizar scores e status por fase (Recomendado)
**Notes:** Manter consistência interna do audit.

| Option | Description | Selected |
|--------|-------------|----------|
| Residual aceito explícito + “ready for re-audit” (Recomendado) | D-14/WR-02 fica apenas em seção de residual aceito/tech debt com justificativa, risco residual e ação futura; nunca em gaps abertos. Audit declara explicitamente que débitos críticos foram resolvidos e milestone está pronto para `/gsd-audit-milestone`. | ✓ |
| Residual aceito, mas sem declarar prontidão | Documenta D-14/WR-02 corretamente, mas evita dizer “pronto para re-audit”. Mais cauteloso, porém enfraquece o sinal de fechamento pedido pelo SC3. | |

**User's choice:** Residual aceito explícito + “ready for re-audit” (Recomendado)
**Notes:** D-14/WR-02 (focus trap completo) nunca em gaps abertos.

---

## OpenCode's Discretion

Nenhuma área foi explicitamente delegada como "you decide" durante a discussão; decisões menores de redação/estrutura foram registradas em CONTEXT.md na seção "OpenCode's Discretion".

## Deferred Ideas

Nenhuma — a discussão permaneceu dentro do escopo da Phase 25.
