# Roadmap: EmpregaNoix

## Milestones

- ✅ **v1.1 EmpregaNoix** — Phases 7–13 (shipped 2026-11-15, audit `gaps_found` accepted) — [Archive](./milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Integração com Facebook Pages** — Phases 14–18 (shipped 2026-11-17, audit missing / gaps+handoffs accepted) — [Archive](./milestones/v1.2-ROADMAP.md)
- 🚧 **v1.3 Chatbot Inteligente de Busca de Vagas** — Phases 19–23 (in progress)

## Phases

- [x] **Phase 19: Contrato de intenção e mapeamento seguro** - Extrair intenção pt-BR em JSON estrito e mapear com segurança para a busca existente
- [x] **Phase 20: API pública de chat-search resiliente** - Expor endpoint público protegido que combina extração e busca determinística sem expor contatos (completed 2026-11-17)
- [x] **Phase 21: Interface de chat e integração no board** - Oferecer chat mobile-first no board com interpretação transparente e aplicação na busca canônica (completed 2026-11-18)
- [x] **Phase 22: Qualidade, hardening e validação operacional** - Validar exemplos MVP, cobrir fluxos críticos e garantir controles operacionais mínimos (completed 2026-11-18)
- [x] **Phase 23: Fechamento de débitos de auditoria e validação v1.3** - Resolver débitos de auditoria, validação humana/Nyquist e hardening pendentes antes do fechamento do milestone (completed 2026-11-20)
- [x] **Phase 24: Corrigir conflito crítico de cidade e resíduos de review** - Fechar CR-01/CL-01 e resíduos de código viáveis do CL-05 sem regredir chat/board público (gap closure planned) (completed 2026-11-22)
- [ ] **Phase 25: Reconciliar gates de fechamento e revalidar auditoria v1.3** - Fechar CL-02/gate audit-open e atualizar verificação/auditoria para re-audit do milestone

## Phase Details

### Phase 19: Contrato de intenção e mapeamento seguro

**Goal**: Usuários têm suas consultas em linguagem natural convertidas em parâmetros de busca confiáveis e alinhados às capacidades reais do produto
**Depends on**: Phase 18 (v1.2 shipped)
**Requirements**: INT-01, INT-02, INT-03
**Success Criteria** (what must be TRUE):

  1. Usuário que descreve uma vaga em pt-BR recebe uma interpretação estruturada que reflete apenas o que foi declarado/implicado, sem invenção de filtros
  2. Consultas com variações de escrita/ordem e instruções conflitantes resultam em extração validada com defaults seguros (campos não informados permanecem nulos/omitidos conforme contrato)
  3. Cada parâmetro entendido é classificado de forma verificável como aplicado, ignorado ou aproximado, com normalização segura para busca existente (`q`, cidade whitelist SP/RJ/BH/Remoto, `sort` permitido)
  4. Campos sem suporte nativo não são apresentados como filtros garantidos; a resposta deixa explícito o limite de aplicação

**Plans**: 2/2 plans complete

Plans:

- [x] 19-01-PLAN.md — Contrato/schemas de intenção + mapper determinístico seguro (testes puros)
- [x] 19-02-PLAN.md — Seam Groq de extração + parser/orquestrador e contrato final (testes fake-client)

### Phase 20: API pública de chat-search resiliente

**Goal**: Usuários e o frontend público podem obter resultados de busca por chat via um endpoint seguro, rápido o suficiente e consistente com o contrato público atual
**Depends on**: Phase 19
**Requirements**: API-01, API-02, API-03
**Success Criteria** (what must be TRUE):

  1. Usuário (via cliente autorizado do board) envia uma mensagem e recebe interpretação + resultados pagináveis/limitados no formato público (`JobPublic`, com `total`), sem contatos expostos no payload
  2. Os resultados retornados refletem busca determinística equivalente à lógica pública existente (`GET /api/v1/public/jobs` / `list_published`) para os parâmetros efetivamente aplicados
  3. Requisições abusivas ou inválidas são contidas por proteções ativas (rate limit por IP, limites de tamanho/tempo) e retornam erros pt-BR seguros sem vazar detalhes internos
  4. Em falha/timeout/indisponibilidade do LLM, o usuário recebe fallback controlado com orientação para busca manual/keyword em vez de erro opaco
  5. Quando filtros não nativos (ex.: salário, modalidade, tipo de contrato/senioridade) forem solicitados, a resposta aplica apenas estratégia limitada/explicitamente aproximada e sinaliza suporte parcial sem afirmar filtragem inexistente

**Plans**: 2 plans

Plans:
**Wave 1**

- [x] 20-01-PLAN.md — Contrato/schemas, knobs e endpoint público chat-search com intent→busca determinística, proteções e fallback seguro (API-01, API-02, API-03)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 20-02-PLAN.md — Testes automatizados do chat-search (equivalência, privacidade, degradação e limites) com LLM mockado (API-01, API-02, API-03)

### Phase 21: Interface de chat e integração no board

**Goal**: Qualquer pessoa consegue usar o chat no board público, entender o que o sistema aplicou e chegar aos detalhes das vagas sem fricção
**Depends on**: Phase 20
**Requirements**: UI-01, UI-02, UI-03
**Success Criteria** (what must be TRUE):

  1. Usuário abre um chat simples (drawer/modal) no board público, em mobile ou desktop, sem login, envia mensagem e vê estados claros de carregamento e erro
  2. Usuário vê os parâmetros entendidos/aplicados/ignorados-aproximados e uma lista de resultados com título, empresa, local, salário quando disponível e acesso ao detalhe/link
  3. A partir dos resultados do chat, o usuário acessa o fluxo atual de detalhe e revelação de contato, sem que contatos apareçam no payload/resposta do chat
  4. Usuário pode aplicar/ajustar a busca entendida no board canônico (URL/filtros existentes) quando aplicável, mantendo o comportamento atual de busca/listagem

**Plans**: TBD
**UI hint**: yes

### Phase 22: Qualidade, hardening e validação operacional

**Goal**: O chatbot de busca opera de forma validada, observável e controlável sem regredir a experiência pública existente
**Depends on**: Phase 21
**Requirements**: QA-01, QA-02, QA-03
**Success Criteria** (what must be TRUE):

  1. Os exemplos-alvo do MVP têm comportamento validado e documentado (incluindo combinações e lacunas explícitas): dev pleno SP salário >= 8k; remoto frontend React preferência CLT; vagas parecidas com uma vaga (abordagem limitada/seed conforme suportado); analista de dados Campinas ou remoto 6–10k; estágio marketing digital em SP
  2. Existe suíte automatizada executável cobrindo extração/mapeamento/normalização e API de chat-search (com LLM mockado), além de validação básica do fluxo de UI/E2E viável no ambiente do projeto
  3. Operadores dispõem de controles mínimos (config/feature toggle ou kill-switch e logs/métricas básicas sem PII sensível) que permitem desativar/ajustar o chat com segurança sem regredir o board público
  4. Com o chat desativado ou degradado, o board público existente continua utilizável para busca/listagem manual

**Plans**: TBD

### Phase 23: Fechamento de débitos de auditoria e validação v1.3

**Goal**: Resolver os débitos pendentes de auditoria, validação humana/Nyquist e hardening identificados no fechamento do v1.3, garantindo que o milestone possa ser fechado sem pendências críticas abertas e sem regredir o board público.
**Depends on**: Phase 22
**Requirements**: CL-01, CL-02, CL-03, CL-04, CL-05
**Success Criteria** (what must be TRUE):

  1. O debug session `city-filter-and-chat-ignores-registered-city` (diagnosed) é investigado até a causa raiz e resolvido ou formalmente deferido/fechado com decisão registrada — o filtro de cidade e o chat passam a respeitar a cidade cadastrada corretamente.
  2. As 4 quick tasks pendentes (`261110-u28`, `261110-uik`, `261111-krt`, `261112-ttk`) têm status definido e documentado (concluídas com evidência ou deferred com justificativa rastreável), com nenhuma permanecendo sem disposição documentada. Se `gsd-sdk query audit-open` ainda reportar essas 4 tasks pré-existentes como `[missing]` por heurística, o residual pode ser formalmente aceito no gate/audit de fechamento do milestone quando as disposições estiverem evidenciadas/justificadas, sem itens novos desta fase e sem fabricar evidência (`261112-ttk` permanece deferred justificado, PLAN-only).
  3. Os gaps de verificação/UAT das fases 21 e 22 são executados e registrados: `21-VERIFICATION.md` e `22-VERIFICATION.md` saem de `human_needed`, `22-HUMAN-UAT.md` sai de `partial` e `22-MANUAL-UAT.md` sai de `draft`, com cenários executados e resultados documentados (ou deferimento aceito e registrado para itens impossíveis de executar no ambiente).
  4. Os gaps Nyquist das fases 19–22 são endereçados: `20-VALIDATION.md` criado e `19/21/22-VALIDATION.md` evoluídos de `partial` para `nyquist_compliant` (ou desvio aceito e documentado com plano de ação).
  5. Os avisos não-bloqueantes da auditoria são tratados quando viáveis: `canApplyChatToBoard` não habilita apply no-op para cidade não-normalizável (UI-03), robustez de foco/a11y do chat/detail, parse defensivo de JSON em `chatSearch`, e `SECURITY.md` da Phase 22 (ou `/gsd-secure-phase 22`).
  6. Após as correções, `gsd-sdk query audit-open` não reporta itens novos nesta fase e o `v1.3-MILESTONE-AUDIT.md` é atualizado (ou substituído por novo audit) refletindo a resolução dos débitos, permitindo o fechamento do milestone v1.3.

**Plans:** 5/5 plans complete

Plans:
**Wave 1**

- [x] 23-01-PLAN.md — Hardening do mapper de cidade (fallback `\brio\b`) e regressões determinísticas (CL-01)
- [x] 23-02-PLAN.md — Correções frontend CL-05: parse defensivo chatSearch, gating de apply sem no-op e foco/a11y viável

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 23-03-PLAN.md — Reconciliação CL-01/CL-03: debug, 21/22 verification-UAT/manual e MVP com estados finais rastreáveis

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 23-04-PLAN.md — Nyquist 19–22 e 22-SECURITY.md (CL-04, CL-05)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 23-05-PLAN.md — Reconciliação quick tasks/STATE/REQUIREMENTS e atualização do audit + gate audit-open (CL-02, CL-05)

### Phase 24: Corrigir conflito crítico de cidade e resíduos de review

**Goal**: Eliminar o bypass crítico de detecção de conflito de cidade no mapper (CR-01) e fechar resíduos de código viáveis da revisão da Phase 23, preservando o comportamento determinístico e seguro do chat/board público
**Depends on**: Phase 23
**Requirements**: CL-01, CL-05
**Gap Closure:** Closes gaps from v1.3 milestone audit
**Success Criteria** (what must be TRUE):

  1. Consultas com conflito de cidade expresso por alias/abreviação/remoto (ex.: "sp ou rio de janeiro", "remoto ou são paulo") não aplicam cidade incorreta quando o candidato LLM traz cidade presente; o mapper sinaliza conflito/ignora com segurança
  2. Detecção de influência de campos não nativos não usa substring frágil sobre `applied_q` inteiro de forma a causar falsa aproximação (WR-03), com regressão automatizada
  3. Fechar detalhe do chat restaura foco para controle montado/estável (WR-01), sem perda de foco para `document.body` em fluxo teclado
  4. Testes automatizados cobrindo CR-01/WR-01/WR-03 passam; contratos públicos/API/JobPublic e fluxo canônico do board permanecem sem regressão

**Plans:** 3/3 plans complete

Plans:
- [x] 24-01-PLAN.md — Mapper determinístico: CR-01 conflito de cidade canônico e WR-03 influência não nativa por token-set (CL-01, CL-05)
- [x] 24-02-PLAN.md — ChatWidget/ChatPanel: painel montado no detalhe e restauração de foco estável sem document.body (CL-05)
- [x] 24-03-PLAN.md — Gap closure: '/' não-cidade no mapper D-03 e guarda dismissible do botão fechar chat para fallback D-08 (CL-01, CL-05)

### Phase 25: Reconciliar gates de fechamento e revalidar auditoria v1.3

**Goal**: Tornar o fechamento do v1.3 rastreável e limpo, reconciliando o residual de gate CL-02 e atualizando evidências de verificação/auditoria após as correções
**Depends on**: Phase 24
**Requirements**: CL-02, CL-05
**Gap Closure:** Closes gaps from v1.3 milestone audit
**Success Criteria** (what must be TRUE):

  1. CL-02 possui disposição final rastreável: quick tasks 261110-u28/uik/krt/261112-ttk permanecem evidenciadas/justificadas sem fabricar evidência; se `gsd-sdk query audit-open` ainda reportar heurística `[missing]` pré-existente, o gate/audit registra aceitação formal explícita com escopo e justificativa
  2. Artefatos de verificação/auditoria refletem o estado pós-fix (23-VERIFICATION ou verificação das fases de gap closure, conforme aplicável) com evidência atualizada para CL-01/CL-02/CL-05
  3. `v1.3-MILESTONE-AUDIT.md` é atualizado para refletir resolução dos débitos críticos e estado de re-audit; milestone fica pronto para `/gsd-audit-milestone`
  4. Residual aceito D-14/WR-02 (focus trap completo) permanece explicitamente documentado como deferimento, sem ser confundido com gap aberto

**Plans:** TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 19. Contrato de intenção e mapeamento seguro | 2/2 | Complete | 2026-11-17 |
| 20. API pública de chat-search resiliente | 2/2 | Complete    | 2026-11-18 |
| 21. Interface de chat e integração no board | 2/2 | Complete    | 2026-11-18 |
| 22. Qualidade, hardening e validação operacional | 3/3 | Complete    | 2026-11-18 |
| 23. Fechamento de débitos de auditoria e validação v1.3 | 5/5 | Complete   | 2026-11-20 |
| 24. Corrigir conflito crítico de cidade e resíduos de review | 3/3 | Complete   | 2026-11-22 |
| 25. Reconciliar gates de fechamento e revalidar auditoria v1.3 | 0/TBD | Not started | - |
