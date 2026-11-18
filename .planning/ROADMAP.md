# Roadmap: EmpregaNoix

## Milestones

- ✅ **v1.1 EmpregaNoix** — Phases 7–13 (shipped 2026-11-15, audit `gaps_found` accepted) — [Archive](./milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Integração com Facebook Pages** — Phases 14–18 (shipped 2026-11-17, audit missing / gaps+handoffs accepted) — [Archive](./milestones/v1.2-ROADMAP.md)
- 🚧 **v1.3 Chatbot Inteligente de Busca de Vagas** — Phases 19–22 (in progress)

## Phases

- [x] **Phase 19: Contrato de intenção e mapeamento seguro** - Extrair intenção pt-BR em JSON estrito e mapear com segurança para a busca existente
- [x] **Phase 20: API pública de chat-search resiliente** - Expor endpoint público protegido que combina extração e busca determinística sem expor contatos (completed 2026-11-17)
- [ ] **Phase 21: Interface de chat e integração no board** - Oferecer chat mobile-first no board com interpretação transparente e aplicação na busca canônica
- [ ] **Phase 22: Qualidade, hardening e validação operacional** - Validar exemplos MVP, cobrir fluxos críticos e garantir controles operacionais mínimos

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

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 19. Contrato de intenção e mapeamento seguro | 2/2 | Complete | 2026-11-17 |
| 20. API pública de chat-search resiliente | 2/2 | Complete    | 2026-11-18 |
| 21. Interface de chat e integração no board | 0/0 | Not started | - |
| 22. Qualidade, hardening e validação operacional | 0/0 | Not started | - |
