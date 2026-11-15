# Phase 15: OAuth Meta e Integrações no Admin - Context

**Gathered:** 2026-11-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Permitir que o admin único conecte uma única Página do Facebook pelo painel do EmpregaNoix, com fluxo OAuth Meta seguro no backend (início autenticado, callback com validação de `state` anti-CSRF, troca de tokens, seleção de página, validação de token/página) e estado de conexão confiável exposto na UI de Integrações — sem expor segredos, tokens ou credenciais ao frontend/logs.

**Em escopo (Fase 15):** endpoints backend de OAuth/integração Meta (iniciar, callback, status, validar/verificar, confirmar seleção de página quando aplicável, desconectar/reconectar), solicitação de permissões mínimas com `META_GRAPH_VERSION` configurável, suporte a múltiplas páginas retornadas por `/me/accounts` com persistência de **apenas 1 página/conexão**, validação de token/página (ex.: `/debug_token`) com transição para `needs_reconnect` em falhas definitivas, e tela/seção admin "Integrações" com status/nome da página, alertas e ações de conectar/desconectar/reconectar/verificar.

**Fora de escopo:** geração/edição/aprovação de posts sociais e integração com revisão (Fase 16), publicação real, worker/cron, retries/idempotência operacional e UI de status/retry por vaga (Fase 17), testes/docs de fechamento/App Review (Fase 18), Instagram, múltiplas páginas simultâneas, múltiplos admins, sincronização de conteúdo de posts e qualquer lógica que exponha segredos ao cliente.

</domain>

<decisions>
## Implementation Decisions

### Fluxo OAuth e callback
- **D-01:** Gerar e validar `state` anti-CSRF como **token assinado/stateless com expiração** no backend (sem persistência em tabela para o `state`), rejeitando callback com assinatura inválida, expirado ou adulterado.
- **D-02:** Experiência em **redirect na mesma aba**: ação "Conectar" inicia endpoint backend autenticado que redireciona ao Meta; o callback processa no backend e redireciona de volta à página de Integrações com resultado seguro (sucesso/erro/cancelamento/etapa pendente).
- **D-03:** Em cancelamento ou falha no callback/troca de tokens, **redirecionar com erro seguro** para a UI de Integrações (indicador/código genérico, sem segredos/tokens); nada deve ser persistido como conectado. Logs no backend devem conter apenas detalhes seguros.
- **D-04:** Modelo de proteção: **início autenticado + callback validado por `state`**. `/oauth/start` (ou equivalente) exige admin autenticado (JWT, conforme padrão atual). `/oauth/callback` aceita redirect do navegador sem `Authorization` Bearer, mas só conclui a operação se o `state` assinado/TTL for válido, executando troca/validação/persistência inteiramente no backend.

### Seleção e persistência da página
- **D-05:** Se `/me/accounts` retornar múltiplas páginas, exigir **escolha explícita na UI** antes de salvar; se retornar uma única página elegível, o fluxo pode concluir automaticamente após validação (mantendo a garantia de salvar apenas 1 página).
- **D-06:** Ao concluir nova conexão/seleção ou reconexão com conexão já existente, **substituir a conexão ativa** para manter uma única página/conexão vigente (1 página/1 admin), atualizando página/tokens/metadados conforme aplicável.
- **D-07:** Ao desconectar, **remover credenciais e marcar desconectado**: limpar/remover o token criptografado utilizável e atualizar/remover o registro de forma que nenhum segredo reutilizável permaneça e a UI indique ausência de conexão.
- **D-08:** Para suportar seleção explícita quando houver múltiplas páginas, usar **etapa pendente intermediada pelo backend**: o callback cria estado pendente seguro (lista de páginas disponíveis sem tokens, associada ao fluxo) e redireciona a UI para carregar/confirmar a seleção via endpoint autenticado antes de persistir tokens/conexão final.

### Status, validação e reconexão
- **D-09:** Validar token/página **no callback (ao concluir/confirmar conexão)** e **sob demanda** quando o admin abrir/atualizar status ou acionar "Verificar agora" em Integrações (sem jobs periódicos nesta fase).
- **D-10:** Política de transição para `needs_reconnect`: marcar apenas em **falhas definitivas** confirmadas (token inválido/expirado, permissões revogadas/insuficientes, página inacessível). **Falhas transitórias** (rede, 5xx, timeout/rate limit temporário na verificação) não devem derrubar uma conexão previamente válida; devem retornar erro de verificação seguro para a UI.
- **D-11:** Endpoint(s) de status devem expor **payload completo e seguro** para a UI (sem tokens/segredos): estado (`connected`/`needs_reconnect`/`disconnected`), identificador e nome da página (quando houver), datas relevantes (ex.: conectado/verificado), indicação de seleção pendente se aplicável, e alerta/motivo resumido seguro em erro/reconexão.
- **D-12:** Ações de recuperação/verificação: oferecer **"Reconectar"** (reinicia fluxo OAuth e, ao concluir, substitui a conexão ativa conforme D-06) e **"Verificar agora"** (revalida sob demanda e atualiza status/alerta conforme D-09/D-10).

### Tela Integrações no admin
- **D-13:** Criar **nova página dedicada de Integrações** com item de navegação claro no admin (consistente com a estrutura atual em `frontend/app/admin/*` e layout), em vez de embutir em tela existente.
- **D-14:** A UI deve representar **estados completos com CTAs claros**: desconectado (Conectar), seleção de página pendente (listar/confirmar página), conectado (exibir nome/status da página, Verificar agora, Desconectar), requer reconexão (alerta + Reconectar), além de loading/erros de ação.
- **D-15:** A ação **"Desconectar" exige confirmação** na UI antes de chamar o backend.
- **D-16:** Ao retornar do redirect do OAuth (sucesso, erro, cancelamento ou seleção pendente), exibir **banner/alerta contextual** ao carregar, atualizar o status exibido e manter feedback consistente com os padrões visuais/componentes do admin.

### OpenCode's Discretion
- Nomes, paths e formato exato dos endpoints/routes backend e frontend para OAuth/integrações (desde que respeitem proteção, escopo e ausência de segredos no cliente).
- Formato interno do `state` assinado, TTL, claims mínimos e segredo/chave usados para assinatura/verificação (seguro, server-side).
- Mecanismo de armazenamento temporário da etapa pendente de seleção (em memória/processo, DB, cache ou estrutura assinada efêmera) desde que não exponha tokens, tenha expiração/limpeza adequada e suporte o fluxo autenticado de confirmação.
- Campos exatos retornados por `/debug_token`/Graph usados para decidir validade, permissões e `needs_reconnect`, e redação de mensagens de erro/alerta resumidas e seguras.
- Estrutura de módulos/serviços/schemas no backend (ex.: service de OAuth/Meta, integração em router admin ou router dedicado) e composição de componentes/hooks na UI admin, seguindo convenções existentes.
- Copy, ícones e detalhes visuais da tela de Integrações, desde que alinhados ao tema/padrões do admin e aos estados/ações definidos.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` §"Phase 15: OAuth Meta e Integrações no Admin" — goal, depends_on (Phase 14), requisitos `META-01..META-06`, success criteria e `UI hint: yes`.
- `.planning/REQUIREMENTS.md` — definições e rastreabilidade de `META-01` a `META-06` (OAuth Meta, seleção de página, validação/`needs_reconnect`, tela de Integrações, segredos só no backend).
- `.planning/PROJECT.md` — core value, decisões/constraints do milestone v1.2 (Facebook only, 1 página/1 admin, OAuth no painel, falha social não bloqueia o site, tokens/segredos só no backend criptografados) e stack/locale fixos.
- `.planning/STATE.md` — foco atual (Phase 15), posição do milestone e contexto herdado.

### Decisões e fundação social (Phase 14 — base obrigatória)
- `.planning/phases/14-fundacao-social-dados-e-configuracao/14-CONTEXT.md` — decisões travadas de fundação: enums nativos, `social_accounts`/`social_posts`/`social_post_logs`, criptografia Fernet explícita, contrato `SocialPublisher`/stub Facebook, config/env sociais.
- `.planning/phases/14-fundacao-social-dados-e-configuracao/14-RESEARCH.md` — padrões de implementação/segurança/validação para domínio social no backend (schema, crypto, settings, contratos).

### Backend — convenções, auth, config e domínio social existente
- `backend/app/core/config.py` — `Settings` e validações existentes; campos Meta/social já presentes (`META_APP_ID`, `META_APP_SECRET`, `META_GRAPH_VERSION`, `META_OAUTH_REDIRECT_URI`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, etc.).
- `backend/app/api/v1/admin.py` — convenções de rotas admin protegidas (`require_admin`), paginação/filtros/erros e respostas.
- `backend/app/deps.py` — dependências de autenticação/autorização e segredos operacionais (ex.: `require_admin`, `require_cron_secret`).
- `backend/app/models/social_account.py` — modelo `SocialAccount`/`SocialAccountStatus` (`connected`, `needs_reconnect`, `disconnected`), token criptografado em repouso, campos de página e timestamps.
- `backend/app/models/__init__.py` — registro/exportação de modelos.
- `backend/app/services/social/crypto.py` — encrypt/decrypt de tokens e tratamento seguro de falhas (base para persistência/uso de page token).
- `backend/app/services/social/` — organização do domínio social (contrato/tipos/stub) a preservar/estender sem acoplamento indevido.
- `backend/app/api/v1/router.py` — composição de routers da API v1.
- `backend/.env.example` — documentação de variáveis Meta/social; manter alinhamento com `META_*`/`SOCIAL_*`/`SITE_PUBLIC_URL`.

### Frontend admin — integração de UI
- `frontend/app/admin/layout.tsx` — layout/navegação atual do admin (ponto de encaixe para item "Integrações").
- `frontend/app/admin/page.tsx` — página inicial/admin dashboard atual.
- `frontend/app/admin/paste/page.tsx` e `frontend/app/admin/review/page.tsx` — padrões existentes de páginas admin, composição e UX.
- `frontend/app/admin/admin.css` — estilos/tema do admin.
- `frontend/components/admin/` — componentes reutilizáveis do admin (ex.: toasts, controles), se aplicável ao padrão de feedback/ações.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/models/social_account.py`: `SocialAccount` + `SocialAccountStatus` já modelam provider/page_id/page_name/token criptografado/status/timestamps — base direta para persistir conexão, marcar `needs_reconnect` e expor status.
- `backend/app/services/social/crypto.py`: serviço dedicado de criptografia de tokens (Fernet, erros seguros) para armazenar/ler `page_access_token` sem vazamento.
- `backend/app/core/config.py`: `Settings` já inclui `META_*`, `META_GRAPH_VERSION`, `META_OAUTH_REDIRECT_URI` e validações de formato/segredos — reutilizar para OAuth/Graph sem novas fontes de config.
- `backend/app/api/v1/admin.py` + `backend/app/deps.py`: padrão de endpoints protegidos por `require_admin` e tratamento de erros/respostas — base para rotas autenticadas de início/status/seleção/desconexão.
- `frontend/app/admin/layout.tsx`, `frontend/app/admin/admin.css`, `frontend/components/admin/*`: shell, tema e utilitários (ex.: `ToastProvider`, `LogoutButton`) para nova página de Integrações com feedback consistente.

### Established Patterns
- Backend FastAPI com SQLAlchemy 2 async, Pydantic Settings e validações fail-safe; segredos sensíveis nunca retornados em payloads/logs.
- Domínio social isolado em `backend/app/services/social/` e modelos em `backend/app/models/`, conforme fundação da Fase 14.
- Admin frontend em Next.js App Router sob `frontend/app/admin/` com layout compartilhado e páginas por seção (`paste`, `review`).
- Integração OAuth deve respeitar: 1 página/1 admin, Graph API versionada por config, permissões mínimas e criptografia em repouso (decisões de projeto/fases anteriores).

### Integration Points
- `backend/app/api/v1/` (router/admin ou router dedicado de integrações): expor endpoints OAuth Meta (start/callback/status/verify/select/disconnect) protegidos conforme D-04 e conectados ao modelo `social_accounts`.
- `backend/app/models/` + persistência: criar/atualizar/substituir conexão ativa, limpar token em desconexão e registrar transições de status (`connected`/`needs_reconnect`/`disconnected`).
- `backend/app/services/social/`: adicionar lógica de OAuth/validação Meta (chamadas Graph, `/debug_token`, resolução de page token/seleção pendente) encapsulada, reutilizando crypto/config.
- `frontend/app/admin/integracoes/` (ou rota equivalente em pt-BR/inglês consistente): nova UI e integração com endpoints de status/ações; adicionar entrada no `frontend/app/admin/layout.tsx`.
- Fluxo de retorno do callback: redirecionar para a rota de Integrações com sinalização segura de resultado para renderizar banner/alerta contextual (D-16).

</code_context>

<specifics>
## Specific Ideas

- Sem referências visuais externas específicas; seguir os padrões existentes do painel admin e aplicar feedback claro por estado (banners/alertas, CTAs de Conectar/Selecionar página/Verificar agora/Reconectar/Desconectar com confirmação).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 15-oauth-meta-e-integracoes-no-admin*
*Context gathered: 2026-11-15*
