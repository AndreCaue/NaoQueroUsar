---
status: complete
phase: 22-qualidade-hardening-e-valida-o-operacional
source:
  - 22-CONTEXT.md (D-04, D-06)
  - 22-UI-SPEC.md
  - 22-RESEARCH.md (QA-02/QA-03)
  - 21-HUMAN-UAT.md (formato análogo)
  - 22-01-PLAN.md
  - 22-02-PLAN.md
  - 23-01-SUMMARY.md
  - 23-02-SUMMARY.md
  - .planning/debug/city-filter-and-chat-ignores-registered-city.md
started: 2026-11-18
updated: 2026-11-20T00:00:00Z
mode: guided-manual
automation_scope: "Sem Playwright, sem React Testing Library/infra browser E2E nesta fase. Validação viável: roteiro manual/UAT guiado + testes automatizados de lógica pura já suportada (ex.: frontend/lib/chatApply.test.ts)."
---

# Phase 22 — Manual UAT (QA-02 / QA-03) — estado final aceito e rastreável

Roteiro guiado (preservado) para validar o fluxo crítico do chat no board público, estados **degradado** e **desativado** (kill-switch), e **não-regressão** da busca/listagem manual, filtros, paginação, detalhe e revelação canônica de contato — tudo **sem login** e sem expor contatos no chat.

**Resolução 23-03 (D-10/D-12):** nenhum item permanece pendente sem resolução. Itens não executados nesta sessão foram registrados como **deferimento aceito por item**, com motivo específico de inviabilidade, risco residual e condição/ação futura, preservando passos/expected como roteiro para execução futura. Não há reivindicação de execução runtime/UI/browser nesta reconciliação.

## Pré-requisitos e ambiente

- **Backend** em execução (ex.: `uvicorn`/ambiente local do projeto) com banco acessível/migrado para cenários que dependem de dados reais.
- **Frontend** em execução (ex.: `npm run dev`) apontando para o backend correto.
- **Dados de teste:** idealmente vagas publicadas disponíveis para validar resultados, paginação, detalhe e revelação. Se não houver dados, registrar como limitação ambiental no `result`.
- **Chat habilitado (baseline):** `CHAT_SEARCH_ENABLED=true` no backend/.env (padrão), reiniciar backend após alteração de env.
- **Chat desativado (cenário QA-03):** definir `CHAT_SEARCH_ENABLED=false` no backend/.env e **reiniciar backend** (e recarregar frontend se necessário) para refletir o estado. Após o teste, restaurar `CHAT_SEARCH_ENABLED=true` se for continuar validações com chat ativo.
- **Ferramentas opcionais:** DevTools do navegador/rede para inspecionar respostas de `/api/v1/public/chat-search`, `/api/v1/public/chat-search/status` e `/api/v1/public/jobs` (verificar ausência de contatos no chat e ausência de detalhes internos).
- **Fora de escopo:** execução automatizada browser/E2E (Playwright/RTL).

## Convenções de registro

- Para cada teste: `result` pode ser `pass | fail | blocked | skipped | deferred_accepted` com observações curtas (evidência/prints/comportamento observado) quando aplicável.
- Em falha, registrar passo, esperado vs observado e se o problema é funcional, copy/UX, ambiente/dados ou segurança/privacidade.
- Em deferimento aceito por item, registrar **motivo** (inviabilidade), **risco residual** e **condição/ação futura**.
- Não registrar conteúdo sensível/PII desnecessária nas notas.

## Tests

### 0. Revalidação do caso reportado (22-04): cidade suportada no toolbar e no chat
**Pré-condição:** `CHAT_SEARCH_ENABLED=true`; existir pelo menos uma vaga publicada na cidade suportada usada no teste (ex.: "São Paulo"/`sao-paulo`, "Rio de Janeiro"/`rio-de-janeiro`, "Belo Horizonte"/`belo-horizonte` ou "Remoto"). Se não houver dados, registrar `blocked`/limitação ambiental.
**Passos (toolbar/busca manual):**
1. Abrir o board público sem autenticação.
2. No campo de busca do toolbar, digitar/enviar o nome ou alias de uma cidade suportada cadastrada (ex.: `São Paulo`, `sao paulo`, `sp`, `Rio`, `rj`, `bh`, `home office`, conforme aplicável aos dados).
3. Confirmar que o board aplica o filtro canônico `city=<slug>` na URL/estado (ex.: `?city=sao-paulo`) e que o campo `q` não permanece indevidamente com `q=<nome-da-cidade>` como única forma de filtro para esse caso.
4. Validar que as vagas cadastradas na cidade correspondente são retornadas quando aplicável e que a listagem continua utilizável.
**Passos (chat):**
5. Abrir o chat e enviar mensagem com cidade suportada cadastrada (ex.: "vagas em São Paulo" ou "vaga em sp").
6. Validar interpretação/`applied_params`/`field_statuses`: a cidade deve aparecer aplicada/normalizada quando suportada e detectada com segurança (não marcada como ignorada por `missing`/`not_in_whitelist` indevidamente nesse cenário), com guidance/limitações coerentes.
7. Confirmar que os resultados são coerentes com os parâmetros efetivamente aplicados, sem exposição de contatos no payload/UI do chat; se aplicável, aplicar no board canônico e/ou abrir detalhe pelo fluxo canônico.
**expected:** Toolbar promove texto de cidade suportada para `city=<slug>` (não apenas `q=<city-name>` indevido) e retorna vagas correspondentes; chat reconhece/aplica cidade suportada cadastrada com interpretação/status corretos e resultados coerentes sem contatos. Correções automatizadas aplicadas (22-04 + hardening 23-01); revalidação manual/runtime permanece necessária para evidência operacional.
**result:** deferred_accepted (deferimento aceito por item)
**Resolução (23-03):** não executado no ambiente desta sessão.
- **Motivo (inviabilidade):** ausência de ambiente integrado viável (backend/frontend em runtime, banco com vagas cadastradas por cidade suportada e navegador) para reproduzir o caso reportado ponta a ponta.
- **Risco residual:** comportamento operacional real do toolbar/chat (URL `city=<slug>`, resultados e interpretação sem marcação indevida como ignorada) pode divergir por configuração, dados ou integração apesar das correções 22-04/23-01 e testes determinísticos.
- **Condição/ação futura:** executar este item 0 em ambiente integrado com dados de vagas por cidade, coletando evidência objetiva (URL/estado, resposta/interpretação do chat, ausência de contatos) e atualizar `22-HUMAN-UAT.md`/`22-MANUAL-UAT.md`/`22-VERIFICATION.md` conforme resultado.

### 1. Board público e busca/listagem manual com chat habilitado (sem login)
**Pré-condição:** `CHAT_SEARCH_ENABLED=true`, frontend recarregado.
**Passos:**
1. Abrir o board público sem autenticação/login.
2. Confirmar que a listagem pública de vagas carrega (via UI; opcionalmente conferir `GET /api/v1/public/jobs` 200).
3. Usar a toolbar de busca manual: aplicar busca por texto (`q`), filtro de cidade (`city`) e ordenação (`sort`) quando aplicável; validar atualização canônica da URL/estado do board.
4. Navegar pela paginação (se houver múltiplas páginas/dados).
5. Abrir detalhe de uma vaga (`vaga`/modal canônico) a partir do board.
**expected:** Board utilizável sem login; filtros/paginação funcionam na busca/listagem manual com chat habilitado; URL/estado canônicos preservados; nenhum bloqueio causado pela presença do chat.
**result:** deferred_accepted (deferimento aceito por item)
**Resolução (23-03):** não executado no ambiente desta sessão.
- **Motivo (inviabilidade):** falta de ambiente de execução frontend+backend com dados publicados para validação manual de navegação/filtros/paginação/detalhe em browser.
- **Risco residual:** regressão de UX/integração não detectada por inspeção estática em cenários dependentes de dados e runtime.
- **Condição/ação futura:** executar roteiro em ambiente integrado com vagas publicadas, registrando evidência de carregamento, filtros/URL canônica, paginação e abertura de detalhe sem login.

### 2. Fluxo crítico do chat habilitado (envio, estados, interpretação, resultados, aplicar, detalhe)
**Pré-condição:** `CHAT_SEARCH_ENABLED=true`; status do chat habilitado (`GET /api/v1/public/chat-search/status` retorna `enabled: true`).
**Passos:**
1. Abrir o chat (launcher/painel visível quando habilitado).
2. Enviar uma mensagem NL (ex.: "dev em São Paulo") e observar estado de carregamento enquanto aguarda resposta.
3. Ao receber resposta, validar área de interpretação: parâmetros/campos entendidos e status por campo (`aplicado`, `ignorado`, `aproximado`) com motivos/limitações e `meta.guidance` quando houver.
4. Validar lista de resultados do chat (cards/itens) e, se houver mais resultados, acionar **"carregar mais"**.
5. Quando aplicável (resposta não degradada e com parâmetros aplicáveis), usar ação de aplicar no board canônico e confirmar atualização de filtros/URL e resultados do board.
6. Abrir detalhe de uma vaga a partir de um resultado do chat e validar fluxo canônico.
**expected:** Estados de carregamento/erro tratados com segurança; interpretação e limitações exibidas de forma transparente (pt-BR, sem internos); resultados pagináveis com "carregar mais" quando aplicável; aplicação no board canônico funciona apenas quando aplicável; abertura de detalhe preserva fluxo canônico.
**result:** deferred_accepted (deferimento aceito por item)
**Resolução (23-03):** não executado no ambiente desta sessão.
- **Motivo (inviabilidade):** validação depende de backend/frontend integrados, provider/LLM ou seam operacional do chat em runtime, dados de resultados e interação de browser (loading, paginação, apply, abertura de detalhe).
- **Risco residual:** falhas de integração, copy/estados, paginação ou navegação canônica podem não se manifestar em testes/lógica isolada.
- **Condição/ação futura:** executar em ambiente integrado com chat habilitado e dados, validando estados, interpretação/limitações, "carregar mais", aplicar no board e detalhe canônico com evidência.

### 3. Revelação de contato canônica e privacidade no chat
**Pré-condição:** vaga com contato disponível e fluxo de revelação funcional no ambiente.
**Passos:**
1. A partir de resultado do chat, abrir detalhe canônico da vaga.
2. Executar fluxo de revelação de contato pelo mecanismo canônico do board (ex.: componente/ação de revelar contato, respeitando requisitos do fluxo como Turnstile quando aplicável no ambiente).
3. Inspecionar UI e payloads/respostas do chat (`/api/v1/public/chat-search`) para confirmar ausência de `contact_email`/`contact_phone`/contatos.
**expected:** Contatos **nunca** expostos no payload/UI do chat; revelação de contato ocorre apenas no fluxo canônico de detalhe/board. Chat não vaza PII/contatos.
**result:** deferred_accepted (deferimento aceito por item)
**Resolução (23-03):** não executado no ambiente desta sessão.
- **Motivo (inviabilidade):** requer vaga com contato revelável, fluxo canônico (incluindo possíveis requisitos de Turnstile/configuração) e inspeção de rede/UI em runtime integrado.
- **Risco residual:** regressão de privacidade/fluxo de revelação em contexto real não observada diretamente nesta reconciliação documental.
- **Condição/ação futura:** validar em ambiente integrado com dados e configuração de reveal, confirmando ausência de contatos no chat e revelação apenas no detalhe canônico; registrar evidência de UI/rede.

### 4. Estados degradado e sem resultados (guidance pt-BR + busca manual)
**Pré-condição:** chat habilitado; conseguir provocar cenário degradado/timeout/sem parâmetros extraíveis (pode exigir simulação de falha de provider, mensagem ambígua/vazia de parâmetros úteis, ou fixture de ambiente).
**Passos:**
1. Enviar mensagem que resulte em resposta degradada ou sem parâmetros extraíveis (ex.: timeout/indisponibilidade do LLM, ou mensagem sem filtros aplicáveis conforme contrato).
2. Observar guidance/mensagem segura em pt-BR, sinalização de limitação/degradação e ausência de resultados automáticos quando aplicável.
3. Enviar consulta válida sem correspondências (se dados permitirem) para validar estado de sem resultados.
4. Usar atalho/ação de **busca manual** a partir do chat/estado exibido e confirmar retorno ao fluxo manual do board.
**expected:** Guidance pt-BR segura e útil (sem detalhes internos/traceback/provider), estados degradado/sem resultados claros, e atalho para busca manual funcional.
**result:** deferred_accepted (deferimento aceito por item)
**Resolução (23-03):** não executado no ambiente desta sessão.
- **Motivo (inviabilidade):** depende de simulação controlada de timeout/indisponibilidade/ausência de parâmetros extraíveis e de dados que produzam "sem resultados" em ambiente integrado.
- **Risco residual:** copy, transições de UI e caminhos de fallback manual podem apresentar comportamento divergente em runtime não exercitado.
- **Condição/ação futura:** executar cenários degradado/sem resultados em ambiente controlado (simulando falhas/inputs conforme contrato) e validar guidance pt-BR segura e retorno à busca manual.

### 5. Chat desativado por kill-switch (QA-03/D-06) sem regressão do board
**Pré-condição:** alterar `CHAT_SEARCH_ENABLED=false` no backend/.env, reiniciar backend e recarregar frontend.
**Passos:**
1. Confirmar sinal operacional: `GET /api/v1/public/chat-search/status` retorna `{"enabled": false}`.
2. Verificar UI pública: launcher/painel de chat **não** deve ser exibido/aberto (ou, se houver superfície, apresentar guidance segura sem interação insegura) conforme contrato implementado.
3. (Opcional, verificação de API) Chamar `POST /api/v1/public/chat-search` com payload válido e confirmar resposta controlada segura: `meta.degraded=true`, `degradation_reason="chat_disabled"`, guidance pt-BR para busca manual, `applied_params` nulos, `results.items=[]` e `total=0`, sem contatos e sem internos (traceback/exception/provider).
4. Validar não-regressão do board manual: `GET /api/v1/public/jobs` continua funcional; usar filtros/busca manual, paginação, abrir detalhe e fluxo de revelação canônica normalmente.
**expected:** Chat efetivamente desativado de ponta a ponta (status/sinal e comportamento seguro); UI sem launcher/painel quando desativado confirmado; API controlada sem internos/LLM/DB side effects expostos; **busca/listagem manual, filtros, paginação, detalhe e revelação** permanecem intactos e utilizáveis sem login.
**result:** deferred_accepted (deferimento aceito por item)
**Resolução (23-03):** não executado no ambiente desta sessão.
- **Motivo (inviabilidade):** requer alteração de configuração/env e restart/reload coordenado de backend e frontend para observar efeito fim-a-fim (status/UI/API) e validar não-regressão do board.
- **Risco residual:** comportamento operacional do kill-switch (ocultação UI, resposta controlada e ausência de bloqueio do board) pode diferir em ambiente real por configuração/deploy.
- **Condição/ação futura:** executar com `CHAT_SEARCH_ENABLED=false` em ambiente controlado, coletando evidência de `/chat-search/status`, resposta de `POST /chat-search`, UI sem launcher/painel e board manual íntegro; restaurar configuração ao final.

### 6. Privacidade operacional e higiene de UI (verificação manual)
**Pré-condição:** acesso a DevTools/rede/logs locais conforme disponível.
**Passos:**
1. Revisar respostas visíveis do chat no navegador: confirmar ausência de contatos e de mensagens internas técnicas.
2. Se houver acesso a logs locais do backend durante os testes, confirmar que eventos operacionais não expõem conteúdo da mensagem do usuário nem PII/contatos (validação automatizada complementar existe via testes; aqui é checagem manual oportunística).
**expected:** Nenhum contato no chat; mensagens ao usuário seguras em pt-BR; sem exposição manual óbvia de PII/conteúdo sensível em superfícies observadas.
**result:** deferred_accepted (deferimento aceito por item)
**Resolução (23-03):** não executado no ambiente desta sessão.
- **Motivo (inviabilidade):** checagem oportunística depende de sessão runtime com DevTools/rede e acesso a logs locais do backend durante interações reais.
- **Risco residual:** exposições pontuais de PII/conteúdo sensível ou detalhes internos em runtime não verificadas manualmente nesta sessão (há cobertura automatizada parcial/complementar, mas não substitui observação oportunística).
- **Condição/ação futura:** executar inspeção manual de rede/UI/logs em ambiente integrado durante cenários de chat (sucesso/degradação/desativado), registrando ausência de contatos e de PII/conteúdo sensível em superfícies observadas.

## Deferred A11y Residual (propagado de 23-02, D-14)

- **Sub-item:** focus-trap completo no diálogo custom do chat (contenção de ciclo Tab/Shift+Tab).
- **Implementado (viável, 23-02):** foco inicial no diálogo ao abrir e restauração de foco ao fechar detalhe aberto a partir de resultado do chat.
- **Justificativa:** trap/contenção de foco robusto em diálogo custom aumenta complexidade e risco de regressão de interação/teclado; escopo de 23-02 limitou-se a melhorias focadas e viáveis.
- **Risco residual:** usuários de teclado/leitor de tela podem mover foco para elementos fora do diálogo enquanto ele estiver aberto.
- **Condição/ação futura:** introduzir focus-trap/contenção dedicada (ou primitiva com gerenciamento de foco) no componente de chat com validação manual de teclado/a11y antes de considerar o sub-item encerrado.

## Summary

total: 7
passed: 0
issues: 0
pending: 0
skipped: 0
blocked: 0
deferred_accepted: 7

## Gaps

- [x] Item 0 (CL-01 toolbar/chat cidade): **deferimento aceito por item** — motivo: ambiente integrado indisponível (backend/frontend/DB/dados/navegador). Risco residual: divergência operacional ponta a ponta apesar de correções 22-04/23-01 e testes determinísticos. Condição/ação futura: revalidar em ambiente integrado com vagas por cidade e registrar evidência objetiva.
- [x] Itens 1–6 (fluxo crítico, privacidade/reveal, degradação/sem resultados, kill-switch, higiene operacional): **deferimento aceito por item** — motivo: dependência de runtime integrado, configuração/restart, dados/fixtures, simulação de falhas e inspeção de browser/rede/logs não disponíveis nesta sessão. Risco residual: regressões de UX/integração/privacidade operacional não observadas diretamente. Condição/ação futura: executar roteiro completo em ambiente integrado/controlado por item, registrando evidências e atualizando artefatos.
- [x] Residual D-14 (23-02): focus-trap completo do diálogo custom do chat — **deferimento aceito** (sub-item) — justificativa: viabilidade/risco de escopo em 23-02; risco residual: foco pode sair do diálogo via teclado; condição/ação futura: implementar contenção de foco dedicada com validação manual de teclado/a11y.

## Notas de execução

- **Reconciliação 23-03:** nenhum teste manual foi executado nesta sessão; todos os itens foram resolvidos documentalmente por deferimento aceito por item (D-12) com rastreabilidade para 22-04/23-01/23-02 e debug CL-01.
- Registrar data/hora, ambiente (local/staging), commit/base testado e quaisquer limitações de dados/infra em execuções futuras.
- Se `CHAT_SEARCH_ENABLED=false` for usado, restaurar para `true` ao final quando apropriado.
- Este roteiro não substitui evidência automatizada; complementa QA-02/QA-03 onde browser/E2E automatizado não é viável. Referências: `22-HUMAN-UAT.md`, `22-VERIFICATION.md`, `23-01-SUMMARY.md`, `23-02-SUMMARY.md`.
