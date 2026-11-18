# Phase 21: Interface de chat e integração no board - Context

**Gathered:** 2026-11-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Entregar a interface de chat no board público para que qualquer pessoa, em mobile ou desktop e sem login, envie uma consulta em linguagem natural e use o endpoint público de chat-search (Phase 20) com transparência sobre o que foi entendido/aplicado/ignorado/aproximado. A fase cobre o acesso/UX do chat no board, a exibição da interpretação e dos resultados (formato público, sem contatos), a navegação para o detalhe/fluxo canônico de revelação de contato a partir dos resultados, e a aplicação/ajuste da busca entendida nos filtros/URL canônicos do board.

**Não** inclui: mudanças no contrato/backend do `POST /api/v1/public/chat-search` além do consumo do contrato existente, busca semântica/embeddings, histórico persistente/conta, autenticação, p��s-filtros avançados ou ranking especial, nem suíte de testes/E2E/controles operacionais completos (Phase 22 / QA-*), exceto decisões de UI necessárias para suportar estados claros e fallback seguro.

</domain>

<decisions>
## Implementation Decisions

### Entrada e formato do chat
- **D-01:** Acesso via **botão flutuante discreto** no board público que abre o chat em painel responsivo: **bottom sheet no mobile** e **drawer/modal adequado no desktop**, mantendo o board como contexto principal.
- **D-02:** A conversa, interpretação e resultados do chat são **mantidos em memória enquanto a aba/página estiver aberta** (estado de sessão do cliente). Fechar/reabrir o painel não apaga; **recarregar a página** reinicia o estado.
- **D-03:** Estado inicial vazio exibe **campo de mensagem com placeholder/instrução breve em pt-BR** e **2–4 exemplos curtos clicáveis** (ex.: consultas típicas de cargo/local/modalidade) para facilitar o primeiro uso.
- **D-04:** Durante envio/espera da resposta, mostrar **indicador visível no thread** (“buscando/interpretando”), **bloquear envio duplicado** até concluir e, em falha, exibir **erro pt-BR claro com ação de tentar novamente** (respeitando estados de carregamento/erro exigidos).

### Exibição da interpretação e resultados
- **D-05:** Interpretação apresentada como **resumo em linguagem natural (“Entendi…”) + status por campo** (chips/linhas indicando aplicado, ignorado, aproximado e motivo conforme contrato), com **limitações/guidance em bloco de aviso separado e legível**.
- **D-06:** Resultados no chat exibidos como **lista compacta de cards/itens empilhados**, cada um com **título, empresa, local e salário quando disponível**, otimizados para painel estreito/mobile e sem expor contatos.
- **D-07:** Navegação de resultados no chat: mostrar **primeira página** retornada e permitir **“Carregar mais”** sob demanda (usando paginação da API) para buscar páginas seguintes dentro do próprio chat.
- **D-08:** Em degradação (LLM indisponível/timeout/sem parâmetros extraíveis) ou sem vagas, exibir **mensagem de guidance/limitações destacada** conforme resposta da API, deixar explícito quando **não houve resultados automáticos**, e oferecer **atalho claro para busca/filtros manuais do board**.

### Aplicar busca no board canônico
- **D-09:** “Aplicar no board” **substitui `q`, `city` e `sort`** pelos `applied_params` efetivos, **limpa `vaga`** e **reseta `page` para 1** na URL canônica, refletindo fielmente a interpretação suportada.
- **D-10:** Após aplicar, **fechar/minimizar o chat** para mostrar o board atualizado (conversa permanece preservada na sessão conforme D-02).
- **D-11:** Ação “Aplicar no board” fica **disponível quando houver parâmetros aplicáveis/úteis** para refletir no board; em respostas **degradadas ou sem parâmetros aplicáveis**, priorizar guidance e atalho para busca manual em vez de aplicar estado vazio.
- **D-12:** Quando houver **aproximações/limites** mas aplicação for possível, exibir **texto curto junto à ação** indicando suporte parcial (ex.: alguns critérios aproximados/não filtrados), além do bloco de interpretação.

### Abrir detalhe a partir do chat
- **D-13:** Abrir vaga a partir do chat pelo **fluxo canônico via `?vaga=<id>`/detalhe existente**, reutilizando `JobDetailDialog`/`RevealContact` e comportamento atual de resolução/deep link (board permanece a fonte do detalhe e da revelação).
- **D-14:** Ao abrir o detalhe a partir do chat, **fechar/minimizar o painel de chat** para evitar sobreposição de camadas; ao fechar o detalhe o usuário retorna ao board e pode reabrir o chat com estado preservado.
- **D-15:** Cada resultado do chat é um **item/card inteiro clicável com indicação clara** (“Ver detalhes”) para acionar a abertura canônica.
- **D-16:** Resultados do chat exibem apenas campos públicos permitidos (**título, empresa, local, salário quando disponível** — `JobPublic`), **nunca contatos**; revelação de contato ocorre exclusivamente no fluxo existente do detalhe.

### OpenCode's Discretion
- Posicionamento exato, ícone/rotulagem, animação, foco/acessibilidade e comportamento de foco/ESC do botão flutuante e do painel (sheet/drawer/modal), desde que mobile-first, sem login e com estados claros.
- Copy pt-BR final de placeholders, exemplos sugeridos, labels de status (aplicado/ignorado/aproximado), mensagens de erro/loading e textos de guidance/atalhos, alinhados ao contrato da API.
- Implementação do estado em memória (componente/página/contexto), estratégia de “Carregar mais” (append/substituição interna) e composição visual dos itens compactos, respeitando D-01..D-16 e o design system existente.
- Mapeamento fino de `applied_params` nulos para URL (omitir `q`/`city` quando nulos, `sort` conforme suporte canônico) e integração com `buildBoardHref`/`normalizeFilters`/`router.replace` sem quebrar o board.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos, escopo e decisões do milestone
- `.planning/PROJECT.md` — Core value (fricção zero, sem login, contatos protegidos), stack/constraints e princípio de contatos nunca expostos no chat.
- `.planning/REQUIREMENTS.md` — UI-01..UI-03 (escopo desta fase), API-01..API-03/INT-01..INT-03 (contrato e capacidades consumidas), QA-01..QA-03 (validação posterior).
- `.planning/ROADMAP.md` §Phase 21 — Goal, depends on Phase 20, success criteria 1–4 e `**UI hint**: yes`.
- `.planning/STATE.md` — Decisões v1.3 vigentes: LLM só extrai parâmetros; busca determinística reutiliza `/api/v1/public/jobs`/`list_published` e `JobPublic`; campos não nativos = suporte limitado/aproximado sinalizado.

### Dependências de produto/contrato (fases anteriores)
- `.planning/phases/19-contrato-de-intencao-e-mapeamento-seguro/19-CONTEXT.md` — Contrato de intenção, classificação por campo, `applied_params (q/city/sort)`, normalização segura e degradação.
- `.planning/phases/20-api-publica-de-chat-search-resiliente/20-CONTEXT.md` — Contrato `POST /api/v1/public/chat-search`, envelope `interpretation + results` (`ChatSearchResults` pagináveis), proteções, fallback/guidance, suporte parcial.

### Backend/API e schemas consumidos (referência do contrato real)
- `backend/app/api/v1/public.py` — Implementação do endpoint `POST /chat-search`, orquestração intent→busca determinística, respostas degradadas/guidance e erros seguros.
- `backend/app/schemas/chat.py` — `ChatSearchRequest`, `ChatSearchResponse`, `ChatSearchResults` (shape de request/response a consumir no frontend).
- `backend/app/services/intent/schema.py` — `IntentContract`, `AppliedParams`, `FieldAssessment` e metadados/limitações usados na interpretação exibida.
- `backend/app/schemas/job.py` — `JobPublic`/`JobListResponse` (campos públicos; contatos ausentes).

### Frontend — board canônico, URL e integração atual (padrões a reutilizar)
- `frontend/app/(public)/page.tsx` — Board server-rendered, fetch paralelo lista+vaga, tratamento de `?vaga`/not-found e layout onde o acesso ao chat deve ser integrado.
- `frontend/lib/filters.ts` — Contrato de URL `q/city/sort/page/vaga`, `normalizeFilters`, `buildBoardHref`, `toApiParams` (fonte única para aplicar busca canônica).
- `frontend/lib/jobs.ts` — Fetch server-side do board/detalhe (`fetchBoard`, `fetchJob`) e comportamento de cache/timeout.
- `frontend/lib/api.ts` — Cliente browser/API types (`JobPublic`, `JobListResponse`), helpers e padrões de erro; ponto natural para chamada client ao chat-search.
- `frontend/components/board/BoardToolbar.tsx` — Padrão de escrita de filtros via `router.replace` + `buildBoardHref` (reuso conceitual para aplicar/aplicar+fechar).
- `frontend/components/board/JobGrid.tsx` — Sincronização de `?vaga` (`syncVagaParam`/replaceState) e abertura do diálogo de detalhe.
- `frontend/components/board/JobDetailDialog.tsx` — Diálogo nativo `<dialog>`, apresentação de campos públicos e footer com revelação/ação secundária.
- `frontend/components/board/RevealContact.tsx` — Fluxo canônico de revelação de contato (deve permanecer exclusivo no detalhe).
- `frontend/lib/cities.ts` e `frontend/lib/format.ts` — Labels/formatação de cidade e datas/salário para consistência visual dos resultados.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `JobDetailDialog` + `RevealContact` + `JobGrid.syncVagaParam`: fluxo canônico de detalhe/`?vaga` e revelação de contato — deve ser reutilizado ao abrir vaga a partir do chat (D-13/D-16).
- `BoardToolbar` + `lib/filters.ts` (`buildBoardHref`, `normalizeFilters`, `PAGE_SIZE`): contrato e mecanismo de escrita de URL/filtros — base para “Aplicar no board” com `applied_params` (D-09).
- `lib/api.ts` tipos/padrões (`JobPublic`, `JobListResponse`, tratamento de erro) e `lib/jobs.ts`/`fetchJob`: modelos de request/parse e resolução de detalhe público.
- `backend/app/schemas/chat.py` e `backend/app/services/intent/schema.py`: shape canônico de `interpretation/results` para tipar/normalizar a resposta no cliente sem inferir campos.
- Componentes/estilos do board (`JobCard`, `AdSlot` não aplicável ao chat, tokens/classes de `app/(public)/public.css` e layout): referência para lista compacta consistente e mobile-first.

### Established Patterns
- **URL como fonte de verdade** para busca/listagem/detalhe (`q/city/sort/page/vaga`) via `normalizeFilters`/`buildBoardHref`; navegação de filtros com `router.replace(..., { scroll: false })` sem poluir histórico.
- **Server-rendered board + interações client-side** pontuais (toolbar, grid/dialog, reveal) — chat deve integrar-se sem quebrar SSR/SEO do board.
- **Contrato público sem contatos**: list/detail/chat expõem apenas dados públicos; contato só via reveal protegido no detalhe.
- **Respostas seguras/degradadas em pt-BR** no backend (guidance/limitations/meta) — UI deve refletir fielmente sem inventar suporte.

### Integration Points
- `frontend/app/(public)/page.tsx` (ou layout/composição do board público): ponto para montar o botão flutuante e o container do chat visível no board.
- Cliente de chat (novo componente/hook): chamada `POST /api/v1/public/chat-search` com `message/page/limit`, gestão de estado em memória (D-02), render de interpretação+resultados e paginação “carregar mais”.
- Ponte chat→board: construir/aplicar href canônico a partir de `applied_params` (omitindo nulos, sort suportado) e acionar navegação/fechamento (D-09..D-12).
- Ponte chat→detalhe: acionar fluxo de `vaga`/detalhe canônico para abrir `JobDetailDialog`/`RevealContact` com item `JobPublic` retornado (D-13..D-16), sem contato no estado do chat.

</code_context>

<specifics>
## Specific Ideas

- Painel responsivo: **bottom sheet no mobile** e drawer/modal no desktop, acionado por botão flutuante discreto.
- Primeira abertura com **exemplos curtos clicáveis** de consultas pt-BR para reduzir fricção.
- Interpretação com **“Entendi…” + status por campo** e bloco separado de limitações/guidance; em fallback/degradação, destacar orientação e **atalho para busca manual**.
- Resultados como **itens compactos (título/empresa/local/salário quando houver)**, item inteiro clicável, com **“Carregar mais”** e ação **“Aplicar no board”** quando aplicável (com nota de suporte parcial se houver aproximações).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 21-interface-de-chat-e-integracao-no-board*
*Context gathered: 2026-11-17*
