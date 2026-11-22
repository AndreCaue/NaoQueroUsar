# Phase 28: Polimento UX da Home - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-22
**Phase:** 28-polimento-ux-da-home
**Areas discussed:** Fonte das cidades ativas, Comportamento do filtro dinâmico, Hover do sort Recentes/Antigos, Intensidade do hover visual

---

## Fonte das cidades ativas / Comportamento do filtro dinâmico

| Option | Description | Selected |
|--------|-------------|----------|
| Global (Recomendado) | Mostra cidades com qualquer vaga publicada/ativa no board, independente de `q`. Mais estável; evita chips sumindo enquanto o usuário digita. | ✓ |
| Segue a busca atual | Mostra só cidades que têm resultados para o `q` atual. Mais contextual, mas o conjunto de chips muda durante a busca. | |
| Você decide | Deixa a OpenCode escolher o comportamento mais coerente com a UX atual do board. | |

**User's choice:** Global (Recomendado)
**Notes:** O filtro deve refletir cidades ativas no geral, não depender da busca textual.

| Option | Description | Selected |
|--------|-------------|----------|
| Ocultar (Recomendado) | Remove o chip da cidade. Cumpre literalmente CITY-01 e mantém o filtro enxuto. | ✓ |
| Mostrar desabilitada | Mantém o chip visível, mas desabilitado/acinzentado. Sinaliza a cidade, porém ocupa espaço. | |
| Você decide | Deixa a OpenCode escolher a apresentação mais clara. | |

**User's choice:** Ocultar (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Limpar filtro (Recomendado) | Remove `city` da URL e mostra o board sem filtro de cidade, evitando tela vazia por filtro obsoleto. `normalizeFilters` já centraliza parsing da URL. | ✓ |
| Manter e mostrar vazio | Mantém a seleção e exibe o estado vazio/“nenhuma vaga encontrada”, preservando a URL compartilhada. | |
| Você decide | Deixa a OpenCode definir o fallback mais seguro. | |

**User's choice:** Limpar filtro (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Junto do board (Recomendado) | Incluir `available_cities` na resposta de `GET /public/jobs`. Uma carga, sempre consistente com os dados publicados/ativos usados no board. | ✓ |
| Consulta separada | Criar endpoint público dedicado para cidades ativas. Reutilizável, mas adiciona outra requisição/contrato. | |
| Você decide | Deixa a OpenCode escolher a forma mais simples e consistente. | |

**User's choice:** Junto do board (Recomendado)
**Notes:** Nenhuma.

---

## Hover do sort Recentes/Antigos

| Option | Description | Selected |
|--------|-------------|----------|
| Dropdown custom (Recomendado) | Trocar por dropdown custom acessível (listbox/button), permitindo hover estilizado nas opções e mantendo o visual dark/roxo. Exige cuidado com teclado/ARIA. | ✓ |
| Manter nativo | Mantém `<select>` atual: hover garantido no controle, mas opções seguem o estilo nativo do sistema (pode não cumprir o critério literalmente). | |
| Você decide | Deixa a OpenCode escolher o equilíbrio entre fidelidade ao critério e simplicidade. | |

**User's choice:** Dropdown custom (Recomendado)
**Notes:** Critério da fase menciona hover nas opções do dropdown; custom atende literalmente.

| Option | Description | Selected |
|--------|-------------|----------|
| Listbox simples (Recomendado) | Botão que abre lista abaixo, opção ativa marcada, hover/focus visíveis, fecha ao selecionar/clicar fora/Escape. Padrão familiar. | ✓ |
| Popover compacto | Menu compacto com o mesmo conteúdo, menos altura visual; mantém seleção atual e feedback de hover. | |
| Você decide | Deixa a OpenCode definir o padrão, desde que acessível e consistente. | |

**User's choice:** Listbox simples (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Borda accent (Recomendado) | No hover, borda/realce vai para `accent`/`accent-soft`, alinhado aos chips e ao input. Estado ativo/aberto pode manter destaque. | ✓ |
| Realce sutil | Mudança mais discreta (ex.: borda um pouco mais clara), sem chamar tanta atenção. | |
| Você decide | Deixa a OpenCode alinhar com o restante da UI. | |

**User's choice:** Borda accent (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Consistente com chips (Recomendado) | Usa a mesma linguagem visual (accent, borda/texto, fundo sutil) para opções/hover, reforçando consistência. | ✓ |
| Estilo próprio de menu | Opções com estilo de menu/lista (ex.: fundo surface elevado), diferente dos chips, mas ainda no tema. | |
| Você decide | Deixa a OpenCode escolher o estilo mais coerente. | |

**User's choice:** Consistente com chips (Recomendado)
**Notes:** Nenhuma.

---

## Intensidade do hover visual

| Option | Description | Selected |
|--------|-------------|----------|
| Médio (Recomendado) | Borda accent + leve mudança de fundo/sombra sutil no card. Feedback claro sem fugir do visual minimalista. | ✓ |
| Sutil | Mantém principalmente a borda accent (como hoje), com ajuste leve se necessário. Mais discreto. | |
| Destaque | Borda accent + fundo/sombra mais evidente. Mais visível, porém menos minimalista. | |

**User's choice:** Médio (Recomendado)
**Notes:** Aplicar aos cards de vaga.

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, leve (Recomendado) | Escurece levemente o fundo accent do chip ativo no hover, mantendo legibilidade e indicando interatividade. | ✓ |
| Não, manter estático | Chip ativo permanece igual no hover; apenas chips inativos têm feedback. | |
| Você decide | Deixa a OpenCode escolher o comportamento mais claro. | |

**User's choice:** Sim, leve (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Reforçar leve (Recomendado) | Mantém borda/texto accent e adiciona um fundo sutil no hover para deixar o feedback mais perceptível. | ✓ |
| Manter atual | Preserva o hover atual de borda/texto accent, sem fundo extra. | |
| Você decide | Deixa a OpenCode ajustar com base no tema. | |

**User's choice:** Reforçar leve (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Consistente (Recomendado) | Mesma linguagem (accent, transição suave, foco visível), com intensidade adaptada por componente. Reforça coesão do board. | ✓ |
| Por componente | Cada elemento pode ter seu próprio estilo de hover, desde que atenda aos critérios da fase. | |
| Você decide | Deixa a OpenCode definir a consistência ideal. | |

**User's choice:** Consistente (Recomendado)
**Notes:** Nenhuma.

---

## OpenCode's Discretion

O usuário não selecionou "Você decide" nas perguntas; a OpenCode ficou com discrição apenas em detalhes de implementação documentados no CONTEXT.md (nome exato do campo de cidades ativas, query/shape interno, ARIA detalhado do listbox, valores exatos de sombra/fundo/transição dentro dos tokens existentes).

## Deferred Ideas

None — discussion stayed within phase scope.
