---
status: draft
phase: 22-qualidade-hardening-e-valida-o-operacional
source:
  - 22-CONTEXT.md (D-04, D-06)
  - 22-UI-SPEC.md
  - 22-RESEARCH.md (QA-02/QA-03)
  - 21-HUMAN-UAT.md (formato análogo)
  - 22-01-PLAN.md
  - 22-02-PLAN.md
started: 2026-11-18
updated: 2026-11-18
mode: guided-manual
automation_scope: "Sem Playwright, sem React Testing Library/infra browser E2E nesta fase. Validação viável: roteiro manual/UAT guiado + testes automatizados de lógica pura já suportada (ex.: frontend/lib/chatApply.test.ts)."
---

# Phase 22 — Manual UAT (QA-02 / QA-03)

Roteiro guiado para validar o fluxo crítico do chat no board público, estados **degradado** e **desativado** (kill-switch), e **não-regressão** da busca/listagem manual, filtros, paginação, detalhe e revelação canônica de contato — tudo **sem login** e sem expor contatos no chat.

## Pré-requisitos e ambiente

- **Backend** em execução (ex.: `uvicorn`/ambiente local do projeto) com banco acessível/migrado para cenários que dependem de dados reais.
- **Frontend** em execução (ex.: `npm run dev`) apontando para o backend correto.
- **Dados de teste:** idealmente vagas publicadas disponíveis para validar resultados, paginação, detalhe e revelação. Se não houver dados, registrar como limitação ambiental no `result`.
- **Chat habilitado (baseline):** `CHAT_SEARCH_ENABLED=true` no backend/.env (padrão), reiniciar backend após alteração de env.
- **Chat desativado (cenário QA-03):** definir `CHAT_SEARCH_ENABLED=false` no backend/.env e **reiniciar backend** (e recarregar frontend se necessário) para refletir o estado. Após o teste, restaurar `CHAT_SEARCH_ENABLED=true` se for continuar validações com chat ativo.
- **Ferramentas opcionais:** DevTools do navegador/rede para inspecionar respostas de `/api/v1/public/chat-search`, `/api/v1/public/chat-search/status` e `/api/v1/public/jobs` (verificar ausência de contatos no chat e ausência de detalhes internos).
- **Fora de escopo:** execução automatizada browser/E2E (Playwright/RTL).

## Convenções de registro

- Para cada teste: preencher `result:` com `pass | fail | blocked | skipped` e observações curtas (evidência/prints/comportamento observado).
- Em falha, registrar passo, esperado vs observado e se o problema é funcional, copy/UX, ambiente/dados ou segurança/privacidade.
- Não registrar conteúdo sensível/PII desnecessária nas notas.

## Tests

### 1. Board público e busca/listagem manual com chat habilitado (sem login)
**Pré-condição:** `CHAT_SEARCH_ENABLED=true`, frontend recarregado.
**Passos:**
1. Abrir o board público sem autenticação/login.
2. Confirmar que a listagem pública de vagas carrega (via UI; opcionalmente conferir `GET /api/v1/public/jobs` 200).
3. Usar a toolbar de busca manual: aplicar busca por texto (`q`), filtro de cidade (`city`) e ordenação (`sort`) quando aplicável; validar atualização canônica da URL/estado do board.
4. Navegar pela paginação (se houver múltiplas páginas/dados).
5. Abrir detalhe de uma vaga (`vaga`/modal canônico) a partir do board.
**expected:** Board utilizável sem login; filtros/paginação funcionam na busca/listagem manual com chat habilitado; URL/estado canônicos preservados; nenhum bloqueio causado pela presença do chat.
**result:** [pending]

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
**result:** [pending]

### 3. Revelação de contato canônica e privacidade no chat
**Pré-condição:** vaga com contato disponível e fluxo de revelação funcional no ambiente.
**Passos:**
1. A partir de resultado do chat, abrir detalhe canônico da vaga.
2. Executar fluxo de revelação de contato pelo mecanismo canônico do board (ex.: componente/ação de revelar contato, respeitando requisitos do fluxo como Turnstile quando aplicável no ambiente).
3. Inspecionar UI e payloads/respostas do chat (`/api/v1/public/chat-search`) para confirmar ausência de `contact_email`/`contact_phone`/contatos.
**expected:** Contatos **nunca** expostos no payload/UI do chat; revelação de contato ocorre apenas no fluxo canônico de detalhe/board. Chat não vaza PII/contatos.
**result:** [pending]

### 4. Estados degradado e sem resultados (guidance pt-BR + busca manual)
**Pré-condição:** chat habilitado; conseguir provocar cenário degradado/timeout/sem parâmetros extraíveis (pode exigir simulação de falha de provider, mensagem ambígua/vazia de parâmetros úteis, ou fixture de ambiente).
**Passos:**
1. Enviar mensagem que resulte em resposta degradada ou sem parâmetros extraíveis (ex.: timeout/indisponibilidade do LLM, ou mensagem sem filtros aplicáveis conforme contrato).
2. Observar guidance/mensagem segura em pt-BR, sinalização de limitação/degradação e ausência de resultados automáticos quando aplicável.
3. Enviar consulta válida sem correspondências (se dados permitirem) para validar estado de sem resultados.
4. Usar atalho/ação de **busca manual** a partir do chat/estado exibido e confirmar retorno ao fluxo manual do board.
**expected:** Guidance pt-BR segura e útil (sem detalhes internos/traceback/provider), estados degradado/sem resultados claros, e atalho para busca manual funcional.
**result:** [pending]

### 5. Chat desativado por kill-switch (QA-03/D-06) sem regressão do board
**Pré-condição:** alterar `CHAT_SEARCH_ENABLED=false` no backend/.env, reiniciar backend e recarregar frontend.
**Passos:**
1. Confirmar sinal operacional: `GET /api/v1/public/chat-search/status` retorna `{"enabled": false}`.
2. Verificar UI pública: launcher/painel de chat **não** deve ser exibido/aberto (ou, se houver superfície, apresentar guidance segura sem interação insegura) conforme contrato implementado.
3. (Opcional, verificação de API) Chamar `POST /api/v1/public/chat-search` com payload válido e confirmar resposta controlada segura: `meta.degraded=true`, `degradation_reason="chat_disabled"`, guidance pt-BR para busca manual, `applied_params` nulos, `results.items=[]` e `total=0`, sem contatos e sem internos (traceback/exception/provider).
4. Validar não-regressão do board manual: `GET /api/v1/public/jobs` continua funcional; usar filtros/busca manual, paginação, abrir detalhe e fluxo de revelação canônica normalmente.
**expected:** Chat efetivamente desativado de ponta a ponta (status/sinal e comportamento seguro); UI sem launcher/painel quando desativado confirmado; API controlada sem internos/LLM/DB side effects expostos; **busca/listagem manual, filtros, paginação, detalhe e revelação** permanecem intactos e utilizáveis sem login.
**result:** [pending]

### 6. Privacidade operacional e higiene de UI (verificação manual)
**Pré-condição:** acesso a DevTools/rede/logs locais conforme disponível.
**Passos:**
1. Revisar respostas visíveis do chat no navegador: confirmar ausência de contatos e de mensagens internas técnicas.
2. Se houver acesso a logs locais do backend durante os testes, confirmar que eventos operacionais não expõem conteúdo da mensagem do usuário nem PII/contatos (validação automatizada complementar existe via testes; aqui é checagem manual oportunística).
**expected:** Nenhum contato no chat; mensagens ao usuário seguras em pt-BR; sem exposição manual óbvia de PII/conteúdo sensível em superfícies observadas.
**result:** [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps

- [ ] (preencher durante execução) 
- [ ] (preencher durante execução)

## Notas de execução

- Registrar data/hora, ambiente (local/staging), commit/base testado e quaisquer limitações de dados/infra.
- Se `CHAT_SEARCH_ENABLED=false` foi usado, restaurar para `true` ao final quando apropriado.
- Este roteiro não substitui evidência automatizada; complementa QA-02/QA-03 onde browser/E2E automatizado não é viável nesta fase.
