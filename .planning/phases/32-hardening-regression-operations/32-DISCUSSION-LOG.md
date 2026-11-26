# Phase 32: Hardening, Regression & Operations - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-26
**Phase:** 32-hardening-regression-operations
**Areas discussed:** Regressão Facebook, Cobertura HARD-01, Docs operacionais, Evidência/handoff

---

## Regressão Facebook

### Q1: Para a regressão/caracterização do Facebook, qual deve ser o artefato principal?

| Option | Description | Selected |
|--------|-------------|----------|
| Estender testes atuais (Recommended) | Ampliar `test_facebook_publisher.py` e `test_social_publish_pipeline.py` com casos explícitos de regressão/contrato FB, reaproveitando padrões já existentes. | ✓ |
| Suite caracterização dedicada | Criar arquivo/módulo dedicado de caracterização FB (snapshots/contratos) separado dos testes atuais, focado em congelar comportamento. | |
| Gate mínimo + docs | Manter cobertura atual como gate mínimo e documentar explicitamente o que está protegido; adicionar só gaps críticos. | |

**User's choice:** Estender testes atuais (Recommended)
**Notes:** Nenhuma nota adicional.

### Q2: Quais fluxos Facebook devem ser tratados como gate de não-regressão?

| Option | Description | Selected |
|--------|-------------|----------|
| Ciclo completo FB (Recommended) | Draft/geração, aprovação/site-first, publish assíncrono, status/logs seguros, retry/idempotência e reconexão/erro seguro — tudo que o IG não pode quebrar. | ✓ |
| Só publish/retry | Focar no pipeline de publicação/retry/idempotência FB; assumir draft/review/UI como já cobertos. | |
| Você decide | Deixo o OpenCode selecionar os fluxos FB críticos com base no código e requisitos HARD-01. | |

**User's choice:** Ciclo completo FB (Recommended)
**Notes:** Nenhuma nota adicional.

### Q3: O nível de rigidez das asserções de regressão FB deve ser qual?

| Option | Description | Selected |
|--------|-------------|----------|
| Contrato comportamental (Recommended) | Assertar comportamentos/estados/campos críticos e mensagens seguras; evitar snapshot frágil de texto inteiro quando não essencial. | ✓ |
| Contrato estrito/payload | Congelar payloads/shapes/mensagens exatas mais rigidamente (mais sensível a mudanças intencionais). | |
| Misto por camada | Estrito no publisher/payload Graph e comportamental no pipeline/UI/status. | |

**User's choice:** Contrato comportamental (Recommended)
**Notes:** Nenhuma nota adicional.

### Q4: Como o gate de regressão FB deve ser sinalizado para release/validação?

| Option | Description | Selected |
|--------|-------------|----------|
| Pytest normal + evidência (Recommended) | Rodar na suíte pytest normal; VERIFICATION/HARD-02 deixa claro quais testes formam o gate FB e seu resultado. | ✓ |
| Marker/seleção dedicada | Adicionar marker (ex. facebook_regression) ou comando dedicado além da suíte normal para execução explícita de gate. | |
| Você decide | OpenCode define o mecanismo mais simples que torne o gate auditável. | |

**User's choice:** Pytest normal + evidência (Recommended)
**Notes:** Usuário optou por avançar para próxima área sem perguntas adicionais.

---

## Cobertura HARD-01

### Q1: Para HARD-01, qual camada de testes automatizados você quer priorizar?

| Option | Description | Selected |
|--------|-------------|----------|
| Backend-first, gaps reais (Recommended) | Focar em pytest backend (draft/validação, publisher/pipeline, idempotência, retry, ambiguidade, rate limit, mapeamento de erros). Frontend só se gap crítico e infra já existir. | ✓ |
| Backend + frontend crítico | Incluir também testes frontend (Vitest/RTL) para comportamentos IG críticos da revisão/status, além do backend. Pode exigir setup adicional. | |
| Você decide | OpenCode escolhe a camada com melhor custo/risco com base no estado atual do repo. | |

**User's choice:** Backend-first, gaps reais (Recommended)
**Notes:** Nenhuma nota adicional.

### Q2: Como interpretar "draft/validação Instagram" no HARD-01?

| Option | Description | Selected |
|--------|-------------|----------|
| Backend/schemas/serviços (Recommended) | Cobrir geração/normalização de draft IG, validações (2200, hashtags/mídia onde aplicável), contratos de API/schemas e erros seguros. Alinha com testes pytest existentes. | ✓ |
| Incluir UI admin também | Além do backend, validar no frontend contador 2200, aviso >30 hashtags, bloqueios e estados de preview/toggle. | |
| Misto mínimo | Backend obrigatório; UI apenas para 1-2 comportamentos críticos se já houver harness de teste frontend. | |

**User's choice:** Backend/schemas/serviços (Recommended)
**Notes:** Primeira resposta veio como "Unanswered"; pergunta foi repetida uma vez e o usuário confirmou a opção recomendada.

### Q3: Qual critério define que HARD-01 está "coberto o suficiente"?

| Option | Description | Selected |
|--------|-------------|----------|
| Cenários HARD-01 rastreados (Recommended) | Cada cenário nomeado em HARD-01 mapeado para testes automatizados claros (ou gap explícito justificado), com evidência em VERIFICATION. Sem meta de % arbitrária. | ✓ |
| Cobertura por arquivo/meta % | Definir meta quantitativa (ex.: cobertura mínima em módulos sociais). Pode gerar esforço em métricas sem foco em risco. | |
| Você decide | OpenCode define o critério de suficiência auditável e proporcional. | |

**User's choice:** Cenários HARD-01 rastreados (Recommended)
**Notes:** Nenhuma nota adicional.

### Q4: Quando houver trade-off, o que deve ganhar prioridade na HARD-01?

| Option | Description | Selected |
|--------|-------------|----------|
| Risco operacional IG/FB (Recommended) | Priorizar ambiguidade/duplicação, rate limit, reconciliação, idempotência, erros seguros e não-regressão FB. Casos felizes redundantes ficam em segundo plano. | ✓ |
| Cobertura uniforme | Distribuir esforço igualmente entre todos os cenários nomeados, mesmo os de menor risco. | |
| Velocidade de fechamento | Cobrir o mínimo que fecha HARD-01 rápido, aceitando deixar lacunas menores para depois. | |

**User's choice:** Risco operacional IG/FB (Recommended)
**Notes:** Usuário optou por avançar para próxima área sem perguntas adicionais.

---

## Docs operacionais

### Q1: Como materializar a documentação HARD-02?

| Option | Description | Selected |
|--------|-------------|----------|
| Expandir doc existente (Recommended) | Evoluir `docs/META-INTEGRATION-TESTING.md` como fonte única operacional (IG readiness + publish pipeline + troubleshooting), evitando duplicação. | ✓ |
| Novo runbook dedicado | Criar doc novo focado em operação IG (ex. `docs/INSTAGRAM-PUBLISH-OPERATIONS.md`) e manter o doc Meta atual como referência cruzada. | |
| Dividir por tema | Separar em docs menores (env vars, troubleshooting, checklist Meta) com índice; mais navegável, mas mais arquivos para manter. | |

**User's choice:** Expandir doc existente (Recommended)
**Notes:** Primeira resposta veio como "Unanswered"; pergunta foi repetida uma vez e o usuário confirmou a opção recomendada.

### Q2: Qual profundidade para troubleshooting dos estados de publicação Instagram?

| Option | Description | Selected |
|--------|-------------|----------|
| Tabela acionável (Recommended) | Por estado/sintoma: significado, causa provável, ação do admin, se pode retry/reconciliar, e quando escalar. Cobre Phase 31 (ambíguo, rate limit, needs_reconnect etc.). | ✓ |
| Runbook passo a passo | Procedimentos detalhados por incidente com sequência de comandos/verificações; mais completo, mais pesado para manter. | |
| Mínimo normativo | Apenas listar estados e significado básico; deixa detalhes operacionais para leitura de código/logs. | |

**User's choice:** Tabela acionável (Recommended)
**Notes:** Nenhuma nota adicional.

### Q3: Como documentar env vars e expiração/reconexão de token?

| Option | Description | Selected |
|--------|-------------|----------|
| Canônica + segurança (Recommended) | Tabela alinhada a `backend/.env.example`: finalidade, obrigatório/opcional, formato, riscos; seção clara de expiração/reconexão (`needs_reconnect`) e rotação segura. | ✓ |
| Só lista de env vars | Listar variáveis e exemplos, sem orientação operacional profunda de token/reconexão. | |
| Você decide | OpenCode define o nível de detalhe suficiente para operação segura. | |

**User's choice:** Canônica + segurança (Recommended)
**Notes:** Nenhuma nota adicional.

### Q4: Qual formato do checklist manual Meta no HARD-02?

| Option | Description | Selected |
|--------|-------------|----------|
| Handoff explícito (Recommended) | Checklist manual marcado como handoff (não executar sem credenciais/autorização), com critérios de evidência e campos para registrar resultado sanitizado. Sem fabricar execução. | ✓ |
| Checklist simples | Lista de passos a validar, sem estrutura formal de evidência/handoff. | |
| Você decide | OpenCode define formato auditável alinhado ao roadmap. | |

**User's choice:** Handoff explícito (Recommended)
**Notes:** Usuário optou por avançar para próxima área sem perguntas adicionais.

---

## Evidência/handoff

### Q1: Onde deve ficar a evidência principal de validação da Phase 32?

| Option | Description | Selected |
|--------|-------------|----------|
| VERIFICATION + matriz (Recommended) | Concentrar em `32-VERIFICATION.md` com matriz cenário→evidência (automatizada/handoff), comandos/resultados e status claro. Docs operacionais referenciam, mas não duplicam status. | ✓ |
| Doc operacional como fonte | Registrar evidência principalmente em `docs/META-INTEGRATION-TESTING.md` ou doc HARD-02; VERIFICATION só resume. Pode misturar operação com status de fase. | |
| Artefato dedicado de evidência | Criar arquivo específico (ex. `32-VALIDATION-EVIDENCE.md`) além de VERIFICATION; mais explícito, mais um artefato para manter. | |

**User's choice:** VERIFICATION + matriz (Recommended)
**Notes:** Nenhuma nota adicional.

### Q2: Como itens manuais Meta devem aparecer na evidência?

| Option | Description | Selected |
|--------|-------------|----------|
| Handoff explícito bloqueado (Recommended) | Marcar como `handoff/manual`, com pré-condições, responsável/ambiente necessário e "não executado/não evidenciado nesta sessão" quando aplicável. Nunca marcar aprovado sem execução real. | ✓ |
| Checklist pendente simples | Listar itens manuais como pendentes sem estrutura detalhada de pré-condição/evidência. Menos auditável. | |
| Você decide | OpenCode escolhe formato auditável que não fabrica evidência. | |

**User's choice:** Handoff explícito bloqueado (Recommended)
**Notes:** Nenhuma nota adicional.

### Q3: Qual granularidade do mapeamento HARD-01 na evidência?

| Option | Description | Selected |
|--------|-------------|----------|
| Por cenário HARD-01 (Recommended) | Cada cenário nomeado (draft/validação, idempotência, retry, ambiguidade, rate limit, mapeamento de erros, regressão FB) mapeado para testes/arquivos/comandos. | ✓ |
| Por grupo amplo | Agrupar em blocos grandes (IG tests, FB tests, docs). Mais simples, menos rastreável. | |
| Por teste individual | Listar cada função de teste; máximo rastreio, mas pode ficar verboso/frágil. | |

**User's choice:** Por cenário HARD-01 (Recommended)
**Notes:** Nenhuma nota adicional.

### Q4: Como evidenciar a regressão Facebook como gate?

| Option | Description | Selected |
|--------|-------------|----------|
| Bloco explícito no VERIFICATION (Recommended) | Seção dedicada "Facebook Regression Gate" com fluxos cobertos, testes/arquivos, resultado e conclusão de não-regressão observada. | ✓ |
| Só listado nos testes gerais | Incluir testes FB na lista geral sem destacar como gate. Atende parcialmente a sinalização. | |
| Você decide | OpenCode escolhe a forma mais auditável e simples. | |

**User's choice:** Bloco explícito no VERIFICATION (Recommended)
**Notes:** Usuário optou por fechar contexto sem perguntas adicionais.

---

## OpenCode's Discretion

Nenhuma área foi explicitamente delegada como "você decide" nas respostas finais; OpenCode mantém discrição apenas em detalhes de implementação listados em CONTEXT.md (nomes exatos de testes, fixtures/mocks, estrutura editorial do doc, forma da matriz), desde que cumpram as decisões travadas.

## Deferred Ideas

None — discussion stayed within phase scope.
