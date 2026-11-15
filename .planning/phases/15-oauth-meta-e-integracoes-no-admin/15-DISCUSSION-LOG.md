# Phase 15: OAuth Meta e Integrações no Admin - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-15
**Phase:** 15-oauth-meta-e-integracoes-no-admin
**Areas discussed:** Fluxo OAuth e callback, Seleção e persistência da página, Status, validação e reconexão, Tela Integrações no admin

---

## Fluxo OAuth e callback

| Option | Description | Selected |
|--------|-------------|----------|
| State assinado stateless (Recomendado) | Gerar `state` assinado/expirável no backend sem persistir em tabela; validar assinatura e TTL no callback. | ✓ |
| State persistido no backend | Salvar nonce no banco/cache com expiração e one-time use no callback. | |
| OpenCode decide | Escolha da estratégia de `state` a critério da implementação. | |

**User's choice:** State assinado stateless (Recomendado)
**Notes:** Nenhuma nota adicional.

| Option | Description | Selected |
|--------|-------------|----------|
| Redirect mesma aba (Recomendado) | "Conectar" redireciona ao Meta; callback processa no backend e retorna à tela de Integrações com status. | ✓ |
| Popup + fechamento automático | OAuth em popup com comunicação de resultado e fechamento automático. | |
| OpenCode decide | Interação de navegação/retorno a critério da implementação. | |

**User's choice:** Redirect mesma aba (Recomendado)
**Notes:** Nenhuma nota adicional.

| Option | Description | Selected |
|--------|-------------|----------|
| Redirecionar com erro seguro (Recomendado) | Em erro/cancelamento, redirecionar para Integrações com indicador seguro; sem persistir conexão; logs seguros. | ✓ |
| Página de erro intermediária no backend | Página simples servida pelo backend com resultado e link de retorno. | |
| OpenCode decide | Forma de reportar falhas a critério da implementação. | |

**User's choice:** Redirecionar com erro seguro (Recomendado)
**Notes:** Sempre sem expor tokens/segredos.

| Option | Description | Selected |
|--------|-------------|----------|
| Início autenticado + callback por state (Recomendado) | `/oauth/start` exige JWT admin; `/oauth/callback` aceita redirect do navegador e valida `state` assinado/TTL no backend. | ✓ |
| Callback também exige sessão admin no navegador | Além de `state`, exigir sessão/cookie admin no callback. | |
| OpenCode decide | Modelo de proteção início/callback a critério da implementação. | |

**User's choice:** Início autenticado + callback por state (Recomendado)
**Notes:** Compatível com callback via redirect do navegador (sem Bearer da SPA).

---

## Seleção e persistência da página

| Option | Description | Selected |
|--------|-------------|----------|
| Escolha explícita na UI (Recomendado) | Listar páginas na tela de Integrações para o admin selecionar e confirmar antes de persistir. | ✓ |
| Auto-selecionar se única; exigir escolha se múltiplas | Conectar automaticamente só quando houver 1 página elegível. | |
| OpenCode decide | Mecanismo de seleção a critério da implementação. | |

**User's choice:** Escolha explícita na UI (Recomendado)
**Notes:** Requisito de salvar apenas 1 página.

| Option | Description | Selected |
|--------|-------------|----------|
| Substituir a conexão ativa (Recomendado) | Atualizar/substituir registro ativo para manter uma única conexão vigente. | ✓ |
| Desconectar antes de salvar nova | Exigir desconexão prévia antes de persistir outra página. | |
| OpenCode decide | Reconciliação com conexão existente a critério da implementação. | |

**User's choice:** Substituir a conexão ativa (Recomendado)
**Notes:** Alinhado a 1 página/1 admin.

| Option | Description | Selected |
|--------|-------------|----------|
| Remover credenciais e marcar desconectado (Recomendado) | Limpar/remover token criptografado e deixar estado desconectado sem segredos reutilizáveis. | ✓ |
| Manter registro mas invalidar uso | Preservar metadados removendo/invalidando token. | |
| OpenCode decide | Estratégia de desconexão segura a critério da implementação. | |

**User's choice:** Remover credenciais e marcar desconectado (Recomendado)
**Notes:** Nunca expor segredos.

| Option | Description | Selected |
|--------|-------------|----------|
| Etapa pendente via backend (Recomendado) | Callback cria estado pendente seguro no backend; UI carrega/confirma seleção via endpoint autenticado. | ✓ |
| Retornar opções no redirect da UI | Levar dados mínimos de seleção no retorno do redirect. | |
| OpenCode decide | Transporte seguro da etapa de seleção a critério da implementação. | |

**User's choice:** Etapa pendente via backend (Recomendado)
**Notes:** Evitar expor tokens/dados sensíveis na URL.

---

## Status, validação e reconexão

| Option | Description | Selected |
|--------|-------------|----------|
| Callback + verificação sob demanda (Recomendado) | Validar ao conectar/confirmar e ao abrir/atualizar status ou acionar "Verificar agora". | ✓ |
| Apenas no callback (lazy) | Validar só na conexão e confiar no estado salvo depois. | |
| OpenCode decide | Pontos de validação a critério da implementação. | |

**User's choice:** Callback + verificação sob demanda (Recomendado)
**Notes:** Sem jobs periódicos nesta fase.

| Option | Description | Selected |
|--------|-------------|----------|
| Só falhas definitivas viram reconexão (Recomendado) | `needs_reconnect` para inválido/expirado/permissões revogadas/página inacessível; falhas transitórias retornam erro sem derrubar conexão válida. | ✓ |
| Qualquer falha exige reconexão | Tratar qualquer erro de validação como `needs_reconnect`. | |
| OpenCode decide | Política de classificação/transição a critério da implementação. | |

**User's choice:** Só falhas definitivas viram reconexão (Recomendado)
**Notes:** Distinguir erro temporário de falha definitiva.

| Option | Description | Selected |
|--------|-------------|----------|
| Status completo para a UI (Recomendado) | Retornar estado, id/nome da página, datas, seleção pendente se houver e alerta/motivo resumido. | ✓ |
| Status mínimo | Retornar apenas essencial (estado e nome da página). | |
| OpenCode decide | Payload de status seguro a critério da implementação. | |

**User's choice:** Status completo para a UI (Recomendado)
**Notes:** Sempre sem tokens/segredos.

| Option | Description | Selected |
|--------|-------------|----------|
| Reconectar via OAuth + verificar agora (Recomendado) | "Reconectar" refaz OAuth/substitui conexão; "Verificar agora" revalida sob demanda. | ✓ |
| Apenas Reconectar | Expor somente reconexão/refazer OAuth. | |
| OpenCode decide | Ações de recuperação/verificação a critério da implementação. | |

**User's choice:** Reconectar via OAuth + verificar agora (Recomendado)
**Notes:** Cobrir recuperação e diagnóstico.

---

## Tela Integrações no admin

| Option | Description | Selected |
|--------|-------------|----------|
| Nova página com item de navegação (Recomendado) | Página dedicada de Integrações integrada ao layout/menu do admin. | ✓ |
| Seção dentro de uma página admin existente | Embutir Integrações em tela já existente. | |
| OpenCode decide | Encaixe na estrutura/navegação admin a critério da implementação. | |

**User's choice:** Nova página com item de navegação (Recomendado)
**Notes:** Consistente com seções atuais do admin.

| Option | Description | Selected |
|--------|-------------|----------|
| Estados completos com CTAs claros (Recomendado) | Desconectado, seleção pendente, conectado, requer reconexão, com loading/erro e ações correspondentes. | ✓ |
| Estados essenciais apenas | Apenas conectado/desconectado/requer reconexão. | |
| OpenCode decide | Conjunto de estados/CTAs a critério da implementação. | |

**User's choice:** Estados completos com CTAs claros (Recomendado)
**Notes:** Incluir etapa de seleção pendente quando aplicável.

| Option | Description | Selected |
|--------|-------------|----------|
| Confirmar antes de desconectar (Recomendado) | Diálogo/confirmação antes de executar desconexão. | ✓ |
| Desconectar imediatamente | Ação no primeiro clique com feedback. | |
| OpenCode decide | Exigência de confirmação a critério da implementação. | |

**User's choice:** Confirmar antes de desconectar (Recomendado)
**Notes:** Reduz desconexões acidentais.

| Option | Description | Selected |
|--------|-------------|----------|
| Banner/alerta contextual ao carregar (Recomendado) | Exibir resultado do retorno OAuth (sucesso/erro/cancelamento/seleção pendente) com banner/alerta e atualização de status. | ✓ |
| Apenas atualizar status silenciosamente | Sem mensagem explícita do retorno. | |
| OpenCode decide | Comunicação do resultado do callback a critério da implementação. | |

**User's choice:** Banner/alerta contextual ao carregar (Recomendado)
**Notes:** Seguir padrão visual/feedback do admin.

---

## OpenCode's Discretion

Paths/formato exato de endpoints e rotas; formato/TTL/assinatura do `state` stateless; mecanismo de armazenamento temporário da seleção pendente (seguro, expirável, sem tokens); campos exatos de validação Graph/`debug_token` e redação de alertas; organização de módulos/serviços/schemas/componentes; copy e detalhes visuais alinhados ao admin.

## Deferred Ideas

None — discussion stayed within phase scope.
