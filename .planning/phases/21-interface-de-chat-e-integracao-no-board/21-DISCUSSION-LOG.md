# Phase 21: Interface de chat e integração no board - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-17
**Phase:** 21-interface-de-chat-e-integracao-no-board
**Areas discussed:** Entrada e formato do chat, Exibição da interpretação e resultados, Aplicar busca no board canônico, Abrir detalhe a partir do chat

---

## Entrada e formato do chat

| Option | Description | Selected |
|--------|-------------|----------|
| Botão flutuante + sheet/modal responsivo | Um botão flutuante discreto abre um painel: bottom sheet no mobile e drawer/modal no desktop. | ✓ |
| Botão na barra/ferramentas do board | Botão “Buscar com chat” integrado ao topo abre o painel; disputa espaço com a toolbar atual. | |
| Página/rota dedicada de chat | Tela própria de chat com navegação de ida/volta; adiciona fricção. | |

**User's choice:** Botão flutuante + sheet/modal responsivo (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Manter enquanto a aba estiver aberta | Conversa/interpretação/resultados preservados em memória; fechar não apaga, reload reinicia. | ✓ |
| Limpar ao fechar o painel | Reinicia ao reabrir. | |
| Limpar apenas ao aplicar/recomeçar busca | Mantém até nova busca explícita/limpar. | |

**User's choice:** Manter enquanto a aba estiver aberta (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Campo de mensagem + exemplos curtos clicáveis | Placeholder/instrução breve em pt-BR e 2–4 sugestões clicáveis. | ✓ |
| Apenas campo de mensagem e placeholder | Interface mínima sem sugestões. | |
| Tela de boas-vindas com explicação maior | Texto introdutório antes do input. | |

**User's choice:** Campo de mensagem + exemplos curtos clicáveis (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Indicador no thread + input bloqueado até responder | Estado “buscando/interpretando”, bloqueia envio duplicado, erro pt-BR com tentar novamente. | ✓ |
| Permitir novas mensagens em fila/cancelamento | Envio concorrente/substituição com maior complexidade. | |

**User's choice:** Indicador no thread + input bloqueado até responder (Recommended)
**Notes:** Usuário optou por seguir para a próxima área após 4 decisões.

---

## Exibição da interpretação e resultados

| Option | Description | Selected |
|--------|-------------|----------|
| Resumo em linguagem natural + status por campo | “Entendi…” + lista/chips por campo (aplicado/ignorado/aproximado e motivo) e bloco separado de limitações/guidance. | ✓ |
| Apenas parâmetros aplicados visíveis | Oculta ignorados/aproximados (menos transparente). | |
| Visualização técnica/JSON-like simplificada | Mais próxima do contrato, porém densa no mobile. | |

**User's choice:** Resumo em linguagem natural + status por campo (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Lista compacta de cards | Itens empilhados com título, empresa, local, salário (quando houver) + ação de detalhe. | ✓ |
| Reutilizar cards completos do board no chat | Consistente, mas ocupa muito espaço no painel. | |
| Apenas links/títulos das vagas | Mínimo, sem contexto antes do detalhe. | |

**User's choice:** Lista compacta de cards (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Primeira página + botão “Carregar mais” | Busca próximas páginas no chat sob demanda. | ✓ |
| Apenas primeira página + incentivo a aplicar no board | Amostra inicial e navegação completa no board canônico. | |
| Paginação completa dentro do chat | Controles anterior/próxima no painel. | |

**User's choice:** Primeira página + botão “Carregar mais” (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Mensagem de guidance destacada + atalho para busca manual | Destaca limitações/guidance, explicita ausência de resultados automáticos quando degradado e oferece ação de busca manual. | ✓ |
| Apenas texto de erro/aviso simples | Sem ações claras de recuperação. | |

**User's choice:** Mensagem de guidance destacada + atalho para busca manual (Recommended)
**Notes:** — 

---

## Aplicar busca no board canônico

| Option | Description | Selected |
|--------|-------------|----------|
| Substituir q/city/sort e ir para página 1 | Aplica `applied_params`, limpa `vaga` e reseta `page` para 1. | ✓ |
| Mesclar com filtros atuais | Preserva campos não definidos pelo chat; pode divergir da interpretação. | |

**User's choice:** Substituir q/city/sort e ir para página 1 (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Fechar/minimizar o chat e mostrar o board atualizado | Aplica na URL e fecha painel; conversa preservada na sessão. | ✓ |
| Manter o chat aberto sobre o board | Permite comparar, mas adiciona sobreposição. | |

**User's choice:** Fechar/minimizar o chat e mostrar o board atualizado (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Quando houver parâmetros aplicáveis/úteis para refletir no board | Em degradação/sem parâmetros aplicáveis, prioriza guidance e busca manual. | ✓ |
| Sempre disponível, aplicando o estado retornado | Pode resetar filtros sem ganho. | |

**User's choice:** Quando houver parâmetros aplicáveis/úteis para refletir no board (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Texto curto junto ao botão indicando suporte parcial | Nota próxima à ação quando houver aproximações/limites relevantes. | ✓ |
| Confiar apenas no bloco de interpretação acima | UI mais limpa, menor ênfase no momento da ação. | |

**User's choice:** Texto curto junto ao botão indicando suporte parcial (Recommended)
**Notes:** — 

---

## Abrir detalhe a partir do chat

| Option | Description | Selected |
|--------|-------------|----------|
| Usar o fluxo canônico via `?vaga=`/detalhe existente | Atualiza URL e reutiliza `JobDetailDialog`/`RevealContact`; comportamento consistente/deep link. | ✓ |
| Abrir um detalhe próprio dentro do chat | Diálogo separado no chat, sem depender de `vaga` na URL. | |

**User's choice:** Usar o fluxo canônico via `?vaga=`/detalhe existente (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Fechar/minimizar para destacar o detalhe | Evita sobreposição; reabrir chat mantém estado preservado. | ✓ |
| Permanecer aberto em segundo plano | Chat atrás do diálogo de detalhe. | |

**User's choice:** Fechar/minimizar para destacar o detalhe (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Card/item inteiro clicável com indicação clara | Alvo amplo com apoio “Ver detalhes”. | ✓ |
| Apenas um botão/link “Ver detalhes” | Controle explícito, menor área de toque. | |

**User's choice:** Card/item inteiro clicável com indicação clara (Recommended)
**Notes:** — 

| Option | Description | Selected |
|--------|-------------|----------|
| Título, empresa, local e salário quando disponível | Alinha a UI-02 e `JobPublic`; contato apenas no detalhe/revelação. | ✓ |
| Título, empresa e local apenas | Omite salário na lista do chat. | |

**User's choice:** Título, empresa, local e salário quando disponível (Recommended)
**Notes:** — 

---

## OpenCode's Discretion

Posicionamento/ícone/rotulagem/animação e acessibilidade (foco, ESC) do botão flutuante e painel; copy pt-BR final; implementação do estado em memória e da paginação “Carregar mais”; composição visual dos itens compactos; mapeamento fino de `applied_params` para URL via utilitários canônicos.

## Deferred Ideas

None — discussion stayed within phase scope.
