# Phase 27: Controles por Ambiente - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-22
**Phase:** 27-controles-por-ambiente
**Areas discussed:** Padrão da flag de anúncios, Doações sem link configurado, Abertura do link de doação

---

## Padrão da flag de anúncios

### Pergunta 1: Padrão quando flag ausente/vazia

| Option | Description | Selected |
|--------|-------------|----------|
| Mostrar anúncios (Recomendado) | Preserva o comportamento atual do site. Operador precisa desativar explicitamente para ocultar; evita sumir anúncios por esquecimento de config. | ✓ |
| Ocultar anúncios | Padrão seguro: só exibe quando a flag estiver explicitamente ativada. Requer configuração para voltar a mostrar. | |

**User's choice:** Mostrar anúncios (Recomendado)
**Notes:** Nenhuma.

### Pergunta 2: Escopo da flag única

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, todos (Recomendado) | Um único controle liga/desliga todos os AdSlot (header em page.tsx, sidebar em page.tsx, inline em JobGrid.tsx). Mais simples de operar. | ✓ |
| Todos, exceto algum específico | Permite exceções. Descrever qual espaço deve se comportar diferente. | |

**User's choice:** Sim, todos (Recomendado)
**Notes:** Usuário optou por avançar para próxima área após essas perguntas.

---

## Doações sem link configurado

### Pergunta 1: Comportamento do botão quando ausente/desabilitado

| Option | Description | Selected |
|--------|-------------|----------|
| Ir para /doacoes interna (Recomendado) | Mantém o comportamento atual: botão leva à página /doacoes ("Em breve..."). Seguro, sem destino inválido, e preserva a página existente. | ✓ |
| Ocultar o botão | Remove o botão Doações do header quando não houver link configurado. Interface mais limpa, mas elimina o CTA. | |
| Botão visível, sem navegação inválida | Botão aparece mas não abre link externo; pode mostrar estado desabilitado ou manter na página atual. Descrever comportamento desejado. | |

**User's choice:** Ir para /doacoes interna (Recomendado)
**Notes:** Nenhuma.

### Pergunta 2: Página `/doacoes` quando link externo configurado

| Option | Description | Selected |
|--------|-------------|----------|
| Manter página (Recomendado) | Mantém /doacoes acessível (útil para acesso direto/SEO/bookmarks). O botão pode apontar para o link externo, mas a página continua existindo. | ✓ |
| Redirecionar para link externo | Se alguém acessar /doacoes e houver link configurado, redireciona para o link externo de doação. | |
| You decide | Deixa a decisão para o OpenCode/planning, dentro do comportamento seguro. | |

**User's choice:** Manter página (Recomendado)
**Notes:** Usuário optou por avançar para próxima área.

---

## Abertura do link de doação

### Pergunta 1: Como abrir o link configurado

| Option | Description | Selected |
|--------|-------------|----------|
| Nova aba (Recomendado) | Abre o link externo em nova aba (`target="_blank"` + `rel="noopener noreferrer"`). Usuário não perde o board; padrão comum para links externos. | ✓ |
| Mesma aba | Navega na mesma aba para o link configurado. Mais simples, mas tira o usuário do EmpregaNoix. | |

**User's choice:** Nova aba (Recomendado)
**Notes:** Nenhuma.

### Pergunta 2: Destino do botão do header quando configurado

| Option | Description | Selected |
|--------|-------------|----------|
| Direto para link externo (Recomendado) | Atende SC3 literalmente: "botão Doações abre o link configurado". Menos cliques; /doacoes continua existindo para acesso direto. | ✓ |
| Ir para /doacoes com CTA externo | Botão leva para /doacoes, e a página mostra/botão abre o link externo. Mantém contexto interno, mas adiciona um passo. | |

**User's choice:** Direto para link externo (Recomendado)
**Notes:** Usuário concluiu a área após essas perguntas.

---

## OpenCode's Discretion

- Nome exato das variáveis de ambiente, formato aceito (`true/false/1/0`, etc.) e validação/sanitização.
- Onde declarar cada variável (frontend `.env`/Vercel; convenção `NEXT_PUBLIC_*` apenas quando necessário).
- Comportamento de layout quando anúncios ocultos (colapso de espaço), desde que espaços não apareçam.
- Validação do link de doação (URL absoluta http/https) para comportamento seguro em valor inválido.
- Ajustes mínimos na página `/doacoes` conforme estado configurado, se útil.
- Atualização de testes/scripts afetados (ex.: `frontend/scripts/verify-ssr.ps1`).

## Deferred Ideas

None — discussion stayed within phase scope.
