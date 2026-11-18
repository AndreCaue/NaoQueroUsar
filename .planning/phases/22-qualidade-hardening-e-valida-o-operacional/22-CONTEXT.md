# Phase 22: Qualidade, hardening e validação operacional - Context

**Gathered:** 2026-11-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Validar, endurecer e operacionalizar o chatbot público de busca de vagas entregue nas Phases 19–21, sem regredir a experiência pública existente do board. Esta fase cobre: (1) validação e documentação do comportamento dos exemplos-alvo do MVP com lacunas explícitas (QA-01); (2) consolidação/cobertura automatizada executável dos fluxos críticos de extração/mapeamento/normalização e API de chat-search com LLM mockado, além de validação básica do fluxo de UI/E2E viável no ambiente do projeto (QA-02); e (3) controles operacionais mínimos (config/feature toggle ou kill-switch e logs/métricas básicas sem PII sensível) para desativar/ajustar o chat com segurança, garantindo que, com chat desativado ou degradado, o board público continue utilizável para busca/listagem manual (QA-03).

**Não** inclui: busca semântica/embeddings/ranking vetorial, memória/histórico persistente, recomendação personalizada, exposição de contatos no payload do chat, expansão de filtros nativos (salário/modalidade/contrato/senioridade como filtros estruturados garantidos) além do suporte limitado/aproximado já definido, nem itens de carry-over v1.2/v1.1 fora do escopo do milestone v1.3.

</domain>

<decisions>
## Implementation Decisions

### Validação dos exemplos MVP (QA-01)
- **D-01:** Abordagem **híbrida** para validar e documentar os 5 exemplos-alvo: (a) matriz versionada em `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/` (ex.: `22-MVP-EXAMPLES.md` ou nome equivalente definido no plano) descrevendo, para cada exemplo, mensagem de entrada, interpretação/`applied_params` e status por campo esperados, resultados/`limitations`/guidance esperados e lacunas explícitas; e (b) testes automatizados de cenários-alvo quando determinísticos/mapeáveis (intent/chat com LLM mockado e/ou fixtures), fornecendo evidência executável de regressão.
- **D-02:** O caso **“vagas parecidas com uma vaga”** deve ser tratado como **seed textual limitado** (consulta em linguagem natural que descreve/referencia uma vaga, com termos extraídos para `q` conforme contrato atual). A validação deve explicitar que **não há similaridade semântica/vetorial nem suporte a seed por link/ID de vaga** nesta fase; a resposta deve sinalizar aproximação/limite conforme INT/API.
- **D-03:** Para cada exemplo, a evidência “validada” deve registrar **contrato esperado + resultado observado**: entrada; interpretação esperada (campos entendidos, `field_statuses`/motivos, `applied_params`, `limitations`/`meta.guidance` quando aplicável); comportamento de resultados esperado (incluindo suporte parcial/não filtragem/ausência de resultados automáticos quando couber); e evidência observada (referência a teste automatizado e/ou execução/fixture documentada). Lacunas explícitas obrigatórias para combinações e capacidades não suportadas nativamente (ex.: Campinas fora da whitelist, salário/modalidade/contrato/senioridade aproximados, “parecidas”).

### Suíte automatizada e UI/E2E viável (QA-02)
- **D-04:** “Validação básica do fluxo de UI/E2E viável” será atendida por **roteiro manual/UAT guiado versionado** cobrindo o fluxo crítico do chat no board (abrir chat sem login, enviar mensagem, estados de carregamento/erro, ver interpretação aplicada/ignorada/aproximada e limitações, ver resultados/“carregar mais” quando aplicável, aplicar no board canônico quando aplicável, abrir detalhe e preservar fluxo de revelação sem expor contatos, atalho de busca manual em degradação/sem resultados) **+ testes automatizados de lógica pura de UI já suportada** (ex.: helpers como `chatApply`). **Não** introduzir Playwright nem configurar React Testing Library/infra nova de browser/E2E nesta fase.
- **D-05:** Para backend (extração/mapeamento/normalização e API `chat-search` com LLM mockado), o foco é **fechar lacunas e consolidar a suíte existente** (ex.: `backend/tests/test_intent_schema.py`, `test_intent_mapper.py`, `test_intent_parser.py`, `test_intent_client.py`, `test_chat_search_api.py`), adicionando apenas casos faltantes para cobrir explicitamente cenários MVP/combinações, contratos de classificação/mapeamento, privacidade (`JobPublic` sem contatos), degradação/fallback seguro, limites/proteções e equivalência determinística — evitando duplicação desnecessária de suítes.

### Controles operacionais e kill-switch (QA-03)
- **D-06:** Adotar **kill-switch/configuração fim-a-fim** via env/config lido pelo backend: quando o chat estiver desativado, o endpoint de chat-search deve responder de forma **segura e controlada** (estado desativado/guidance pt-BR para busca manual, sem vazar detalhes internos) e o frontend deve **consultar/sinalizar esse estado e ocultar ou desabilitar a entrada do chat**. A implementação deve garantir que desativar/ajustar o chat **não afete** a listagem/busca manual do board público. (Mecanismo exato de sinalização ao frontend — ex.: endpoint/config pública, flag embutida ou equivalente viável — fica a critério da implementação desde que atenda ao comportamento.)
- **D-07:** Observabilidade mínima: **logs estruturados de evento/resultado sem PII sensível**. Não registrar conteúdo da mensagem do usuário nem dados pessoais/contatos. Registrar, no mínimo viável, sinais operacionais como outcome (sucesso, degradado, desativado, erro controlado), motivo/código de degradação ou desativação, latência/duração, indicadores agregados seguros (ex.: contagem de resultados/total quando aplicável) e status/causa operacional relevante (incluindo rate limit/timeout) para diagnóstico e ajuste. Métricas externas/infra de agregação obrigatória estão fora do escopo desta decisão.

### OpenCode's Discretion
- Nomes, localização exata e formato dos artefatos de validação (arquivo de matriz QA-01, roteiro manual QA-02), desde que versionados em `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/` e rastreáveis aos requisitos.
- Seleção precisa dos casos de teste a adicionar/consolidar (evitando duplicação) e organização de fixtures/mocks para cenários MVP e combinações.
- Nomes/valores exatos de env/config do kill-switch, forma de expor estado ao frontend, shape de resposta “chat desativado” (compatível com UX segura/guidance) e detalhes de implementação dos logs estruturados (campos/formato) desde que sem PII e úteis operacionalmente.
- Pequenos ajustes de copy pt-BR e estados de UI necessários para refletir “desativado” com orientação para busca manual, preservando o contrato público e o comportamento canônico do board.
- Critério exato de “executável/viável no ambiente do projeto” para comandos de teste/documentação de pré-requisitos, sem prometer execução de suites dependentes de infraestrutura indisponível.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos, escopo e estado do projeto
- `.planning/PROJECT.md` — Core value (fricção zero, sem login, contatos protegidos), constraints/stack, estado atual (Phase 21 completa com UAT humano pendente) e princípio de contatos nunca expostos no chat.
- `.planning/REQUIREMENTS.md` — QA-01, QA-02, QA-03 (escopo desta fase) e INT-01..INT-03, API-01..API-03, UI-01..UI-03 (comportamentos/contratos a validar sem regressão).
- `.planning/ROADMAP.md` §Phase 22 — Goal, depends on Phase 21, success criteria 1–4 (exemplos MVP validados/documentados, suíte automatizada, controles operacionais, board utilizável com chat desativado/degradado).
- `.planning/STATE.md` — Decisões v1.3 vigentes, riscos a observar (filtros não nativos, custos/latência Groq, preservação de fricção zero/sem contatos) e contexto de verificação/handoffs.

### Contrato e implementação do chatbot (dependências diretas)
- `.planning/phases/19-contrato-de-intencao-e-mapeamento-seguro/19-CONTEXT.md` — Contrato de intenção, classificação por campo, `applied_params` (`q/city/sort`), normalização segura e degradação.
- `.planning/phases/20-api-publica-de-chat-search-resiliente/20-CONTEXT.md` — Contrato `POST /api/v1/public/chat-search`, envelope `interpretation + results` pagináveis (`JobPublic`, sem contatos), proteções, fallback/guidance e suporte parcial.
- `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-CONTEXT.md` — UX do chat (drawer/modal), interpretação/limitações, aplicação no board canônico, abertura de detalhe/reveal canônico e estados preservados.
- `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-VERIFICATION.md` — Evidência de verificação e itens humanos/avisos remanescentes da UI (útil para roteiro QA-02/QA-01).
- `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-HUMAN-UAT.md` — Roteiro de UAT humano pendente da Phase 21 (base para validação básica/manual guiada).

### Backend — API, intent, config e proteções
- `backend/app/api/v1/public.py` — Endpoint `POST /chat-search`, orquestração intent→busca determinística, respostas degradadas/guidance, erros seguros e ponto de integração do kill-switch/observabilidade.
- `backend/app/services/intent/schema.py` — `IntentContract`, `AppliedParams`, `FieldAssessment`, enums/metadados (contrato esperado nos cenários MVP).
- `backend/app/services/intent/parser.py` — `extract_and_map_intent`, `parse_intent`, `build_empty_intent` e degradação segura.
- `backend/app/services/intent/mapper.py` — Mapeamento determinístico server-authoritative (whitelist cidade/sort, composição de `q`, conflitos, limitações/aproximações).
- `backend/app/services/intent/client.py` — Seam Groq de intent e comportamento sob falha/timeout (alvo de mock em testes).
- `backend/app/schemas/chat.py` — Request/response do chat-search (`ChatSearchRequest`, `ChatSearchResponse`, `ChatSearchResults`).
- `backend/app/schemas/job.py` — `JobPublic`/`JobListResponse` (garantia de ausência de contatos).
- `backend/app/crud/jobs.py` e `backend/app/services/cities.py` — Equivalência determinística com `list_published` e normalização `city/sort`.
- `backend/app/core/config.py` e `.env.example` — Settings/env (knobs Groq/rate limit/timeout) — base para kill-switch/config operacional.
- `backend/app/core/ratelimit.py` — Padrão de rate limit por IP+endpoint e erros pt-BR.

### Frontend — chat, board canônico e testes existentes
- `frontend/app/(public)/page.tsx` — Integração do chat no board público.
- `frontend/components/board/chat/` — `ChatWidget.tsx`, `ChatPanel.tsx`, `ChatLauncher.tsx`, `ChatThread.tsx`, `ChatComposer.tsx`, `ChatInterpretation.tsx`, `ChatResultsList.tsx`, `ChatResultItem.tsx` (UX/estados, apply, detalhe, guidance).
- `frontend/lib/api.ts` — Cliente/tipos do chat-search e contratos públicos.
- `frontend/lib/chatApply.ts` e `frontend/lib/chatApply.test.ts` — Mapeamento/gating `applied_params`→board canônico e cobertura automatizada existente.
- `frontend/lib/filters.ts` — Contrato canônico `q/city/sort/page/vaga`.
- `frontend/components/board/JobDetailDialog.tsx`, `frontend/components/board/RevealContact.tsx`, `frontend/components/board/JobGrid.tsx` — Fluxo canônico de detalhe/revelação (não regressão).
- `frontend/vitest.config.ts` e `frontend/package.json` — Infra atual de testes frontend (Vitest node, scripts).

### Testes automatizados existentes (base para consolidar QA-02)
- `backend/tests/test_intent_schema.py`, `backend/tests/test_intent_mapper.py`, `backend/tests/test_intent_parser.py`, `backend/tests/test_intent_client.py` — Cobertura de contrato/mapeamento/parser/cliente de intent.
- `backend/tests/test_chat_search_api.py` — Cobertura do endpoint público de chat-search (equivalência/privacidade/degradação/limites com LLM mockado).
- `backend/tests/test_ratelimit.py`, `backend/tests/test_client_ip.py` — Padrões de proteção/identificação de cliente.
- `frontend/lib/chatApply.test.ts` — Cobertura de mapeamento UI→board.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Intent + chat-search já modularizados:** `backend/app/services/intent/{schema,mapper,parser,client}.py`, `backend/app/schemas/chat.py`, `backend/app/api/v1/public.py` — base para cenários MVP determinísticos com LLM mockado e para inserir kill-switch/observabilidade no boundary correto.
- **Suíte backend relevante existente:** `backend/tests/test_intent_*.py` e `backend/tests/test_chat_search_api.py` já exercitam extração/mapeamento/normalização e API pública com mocks — consolidar/estender em vez de duplicar (D-05).
- **Chat UI e mapeamento canônico:** `frontend/components/board/chat/*`, `frontend/lib/api.ts`, `frontend/lib/chatApply.ts`, `frontend/lib/filters.ts`, `JobDetailDialog`/`RevealContact`/`JobGrid` — fluxo canônico (URL, detalhe, revelação) que deve permanecer intacto; `chatApply.test.ts` + `vitest.config.ts` são o padrão viável de automação UI atual.
- **Padrões de config/proteção:** `backend/app/core/config.py`, `backend/app/core/ratelimit.py`, `.env.example` — pontos naturais para flag operacional e knobs sem introduzir infra nova.

### Established Patterns
- **LLM só extrai parâmetros; busca determinística reutiliza `list_published`/contrato público (`JobPublic`) sem contatos** — validações e kill-switch não podem violar isso.
- **Campos não nativos = suporte limitado/aproximado e sinalizado** (nunca afirmar filtragem inexistente); degradação/fallback controlado em pt-BR.
- **URL canônica do board** (`q/city/sort/page/vaga`) como fonte de verdade via `normalizeFilters`/`buildBoardHref`/`router.replace`.
- **Testes backend em pytest com mocks/fakes** para seams externos (Groq) e foco em contrato/segurança; frontend com Vitest em ambiente `node` para lógica pura.

### Integration Points
- **Kill-switch/config:** `backend/app/core/config.py` (+ `.env.example`) → enforcement em `backend/app/api/v1/public.py` (chat-search) e sinalização consumível por `frontend/lib/api.ts`/`frontend/components/board/chat/*` para ocultar/desabilitar entrada sem impactar board.
- **Observabilidade sem PII:** logging estruturado no fluxo do chat-search (parser/client/orquestração/resposta) com campos de outcome/latência/motivo/status, excluindo conteúdo de mensagem e dados sensíveis.
- **Artefatos QA:** matriz/roteiro em `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/`; casos automatizados adicionados às suítes existentes em `backend/tests/` e, se aplicável, `frontend/lib/*.test.ts` dentro da infra atual.
- **Não-regressão:** board público/listagem manual (`frontend/app/(public)/page.tsx`, toolbar/grid/filtros) deve permanecer funcional com chat desligado/degradado.

</code_context>

<specifics>
## Specific Ideas

- Exemplos-alvo QA-01 a cobrir explicitamente: (1) dev pleno SP salário >= 8k; (2) remoto frontend React preferência CLT; (3) vagas parecidas com uma vaga (**seed textual limitado**, sem semântica/link); (4) analista de dados Campinas ou remoto 6–10k; (5) estágio marketing digital em SP — incluindo combinações e lacunas (Campinas fora da whitelist; salário/modalidade/contrato/senioridade não filtrados nativamente, apenas aproximados/sinalizados quando aplicável).
- Formato de evidência preferido: matriz legível por exemplo com **contrato esperado + resultado observado** e referência cruzada a testes/execuções quando houver.
- UI/E2E “viável”: roteiro manual/UAT guiado versionado (reaproveitando/estendendo o espírito de `21-HUMAN-UAT.md`) em vez de adicionar Playwright/RTL nesta fase.
- Operação: toggle fim-a-fim com comportamento seguro e orientação para busca manual; logs úteis sem PII (sem texto da consulta do usuário).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 22-qualidade-hardening-e-valida-o-operacional*
*Context gathered: 2026-11-17*
