# Phase 18: Testes, Documentação e Fechamento de Gaps v1.1 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-16
**Phase:** 18-testes-documentacao-e-fechamento-de-gaps-v11
**Areas discussed:** Fechamento dos gaps v1.1 (AUD/EXTR/PUBL/SRCH/UIUX)

---

## Fechamento dos gaps v1.1 (AUD/EXTR/PUBL/SRCH/UIUX)

### Estratégia principal (AUD-01..05)

| Option | Description | Selected |
|--------|-------------|----------|
| Híbrido: validar e corrigir lacunas reais (Recomendado) | Auditar cada requisito contra código/testes atuais; implementar correção pontual quando faltar comportamento; quando já estiver ok, produzir evidência rastreável e atualizar status/artefatos (incluindo equivalente rastreável para 11-VERIFICATION). | ✓ |
| Foco em evidência e reconciliação | Priorizar verificações, artefatos de evidência e atualização de REQUIREMENTS/STATE/traceability; fazer mudanças de código só se forem mínimas e necessárias para a evidência refletir a realidade. | |
| Foco em correções e endurecimento de código/testes | Tratar os gaps como trabalho de implementação/testabilidade primeiro (corrigir comportamentos/aceites faltantes), consolidando documentação e reconciliação de status depois. | |

**User's choice:** Híbrido: validar e corrigir lacunas reais (Recomendado)
**Notes:** Aplicar aos gaps EXTR-10..12, PUBL/SRCH/UIUX, itens parciais SECR/ADMN/REVW/LIFE/TRST/BRND e à ausência de `11-VERIFICATION.md`, respeitando que o sucesso aceita "fechados/validados ou possuem evidência verificável e estado atualizado conforme resultado".

### Tratamento de bloqueios de evidência (DB de testes, humano/browser, canônico)

| Option | Description | Selected |
|--------|-------------|----------|
| Tornar reprodutível no repo + registrar handoffs (Recomendado) | Criar/setup documentado e reproduzível para DB de testes com migrações (para rodar suites DB-backed localmente/CI quando possível), gerar evidência do que rodar aqui, e deixar smoke canônico/humano-browser como handoff operacional com checklist, comandos e critérios explícitos. | ✓ |
| Executar/verificar tudo que for possível agora, resto como handoff | Priorizar rodar testes/smokes/validações no ambiente atual e registrar resultados reais; quando infra/credenciais/host canônico impedirem, documentar bloqueio com evidência e próximos passos rastreáveis. | |
| Apenas documentação e artefatos de evidência (sem setup novo) | Não adicionar setup de DB/migração para testes nesta fase; focar em documentar procedimentos, consolidar evidências existentes e explicitar o que permanece pendente de execução humana/operacional. | |

**User's choice:** Tornar reprodutível no repo + registrar handoffs (Recomendado)
**Notes:** Endereça suites DB-backed bloqueadas por `jobs` ausente e handoffs canônicos/humanos-browser com rastreabilidade.

### Artefato `11-VERIFICATION.md` e consolidação de evidências

| Option | Description | Selected |
|--------|-------------|----------|
| Criar/backfill `11-VERIFICATION.md` na Fase 11 (Recomendado) | Adicionar o arquivo ausente em `.planning/phases/11-.../11-VERIFICATION.md` com evidências rastreáveis já existentes (summaries, 07/08/12/13), e atualizar verificações/traceability relacionadas quando necessário. | ✓ |
| Criar artefato equivalente de reconciliação na Fase 18 | Manter a pasta da Fase 11 como está e produzir na Fase 18 um documento/VERIFICATION equivalente que cubra explicitamente a lacuna da 11 e referencie todas as evidências cruzadas. | |
| Ambos: backfill da 11 + resumo consolidado na Fase 18 | Criar `11-VERIFICATION.md` onde falta e também registrar na Fase 18 um fechamento/auditoria consolidada dos gaps com links para todos os artefatos e status finais. | |

**User's choice:** Criar/backfill `11-VERIFICATION.md` na Fase 11 (Recomendado)
**Notes:** Incluir tratamento dos caveats de 07/08 conforme evidências disponíveis.

### Prioridade/ordem e critério de fechamento com runtime/infra indisponível

| Option | Description | Selected |
|--------|-------------|----------|
| Priorizar correções/evidências locais e automatizáveis (Recomendado) | 1) Fechar EXTR/PUBL/SRCH/UIUX e gaps verificáveis localmente com código+testes+artefatos; 2) backfill 11-VERIFICATION/caveats 07-08; 3) preparar DB de testes reprodutível e registrar handoffs canônicos/humanos com critérios objetivos. Marcar requisito como fechado/validado só com evidência disponível; caso contrário “evidência parcial + handoff rastreável” com status explícito. | ✓ |
| Priorizar reconciliação documental completa primeiro | Consolidar todos os artefatos/traceability/VERIFICATIONs e status no papel primeiro, depois executar correções locais/testes onde possível. Itens dependentes de runtime ficam documentados como pendentes com plano de verificação. | |
| Tentar cobrir tudo igualmente em paralelo | Avançar em código, testes, docs e reconciliação de forma balanceada; aceitar que alguns itens fiquem com evidência parcial desde que todos tenham artefato/status atualizado ao final da fase. | |

**User's choice:** Priorizar correções/evidências locais e automatizáveis (Recomendado)
**Notes:** Status explícito obrigatório quando não houver evidência de execução/runtime disponível.

---

## OpenCode's Discretion

- Forma exata do setup reprodutível de DB de testes/migrações e sua integração com pytest/CI.
- Detalhamento de testes automatizados sociais (TEST-01..03), roteiro manual Meta (TEST-04) e documentação operacional (DOC-01), desde que atendam aos critérios de sucesso da fase.
- Estrutura dos artefatos de evidência/reconciliação além do backfill de `11-VERIFICATION.md`, e escopo de correções pontuais necessárias para tornar evidências verdadeiras sem ampliar escopo.

## Deferred Ideas

- Execução real em hosts canônicos, validações humanas/browser completas e testes com app/página Meta reais: handoffs rastreáveis quando ambiente/credenciais indisponíveis.
- Capacidades fora do milestone v1.2 (Instagram, múltiplas páginas/admins, métricas, sync edição/remoção, imagem em post): fora de escopo.
