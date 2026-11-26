# Integração Meta/Facebook — roteiro de teste manual e operação (TEST-04, DOC-01)

Este documento descreve como configurar e validar a integração social (Facebook Pages) em **modo desenvolvimento**, além de checklists operacionais para cron/Render e App Review/modo Live. Não contém segredos reais.

## 1) Setup do app Meta e Página em modo desenvolvimento

### Pré-requisitos

- Conta Meta/Business com acesso de administrador à Página do Facebook de teste.
- App Meta criado no [Meta for Developers](https://developers.facebook.com/) com produto/capacidades de Login do Facebook e permissões para páginas conforme necessário.
- Backend acessível (local ou deploy de teste) com variáveis Meta/social configuradas e `SITE_PUBLIC_URL` definido para gerar o link público da vaga (`/?vaga=<job_id>`).
- Frontend/admin acessível para o fluxo de conexão em `/admin/integracoes`.
- URL de callback OAuth registrada no app Meta compatível com `META_OAUTH_REDIRECT_URI` (ex.: `https://<backend>/api/v1/admin/integrations/meta/oauth/callback` ou equivalente conforme roteamento/deploy).

### Permissões mínimas

Solicitar/validar no fluxo OAuth as permissões:
- `pages_show_list` — listar páginas administradas para seleção.
- `pages_manage_posts` — publicar posts na Página selecionada.
- `pages_read_engagement` — leitura/engajamento conforme escopo da integração.

Usar versão fixa/configurável da Graph API via `META_GRAPH_VERSION` (ex.: `v21.0`, alinhada ao ambiente validado).

### Variáveis de ambiente relacionadas (backend, placeholders)

Configurar no ambiente seguro (Render/local `.env`, nunca versionado):
- `META_APP_ID` / `META_APP_SECRET`
- `META_GRAPH_VERSION`
- `META_OAUTH_REDIRECT_URI`
- `SOCIAL_TOKEN_ENCRYPTION_KEY` (chave Fernet válida)
- `SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS` (retry/backoff)
- `SITE_PUBLIC_URL` (base pública do site para o link do post)
- `CRON_SECRET` (protege endpoints operacionais/cron, incluindo worker social e expiração; contrato fail-closed/T-06-01 preservado)
- `SOCIAL_WORKER_SECRET` (reservado/documentado; se o deploy usar segregação futura, manter coerente — hoje o worker/cron protegido usa `X-Cron-Secret`/`CRON_SECRET` no backend)

Frontend: apenas variáveis públicas necessárias (`NEXT_PUBLIC_API_URL`, `BACKEND_API_URL`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`). **Nunca** expor `META_APP_SECRET`, tokens, `SOCIAL_TOKEN_ENCRYPTION_KEY` ou segredos de cron no frontend.

### Seleção de página (1 página / 1 admin)

- Conectar via OAuth no admin; se houver múltiplas páginas, selecionar **uma única Página** (comportamento suportado pelo fluxo atual).
- Confirmar status conectado, nome da página e ausência de alerta de reconexão.

## 2) Roteiro manual TEST-04 (app/página em modo desenvolvimento)

> Execução real depende de credenciais/app Meta e Página de teste. Quando indisponível, manter como **handoff rastreável** com este roteiro e critérios.

### 2.1 Conectar integração
1. Acessar admin → Integrações.
2. Iniciar conexão Facebook (OAuth), autenticar na Meta e conceder permissões mínimas.
3. Selecionar a Página (se solicitado) e concluir callback.
- **Critério de aceite:** status `connected` (ou equivalente seguro), página exibida, sem segredos no frontend/logs visíveis.

### 2.2 Gerar, editar e regenerar rascunho social
1. Ir à revisão/edição de uma vaga elegível e abrir seção de publicação social.
2. Gerar rascunho (LLM/template conforme implementação), editar texto e usar "regenerar com IA" quando disponível.
3. Validar contador/preview e presença do link público (`SITE_PUBLIC_URL` + `/?vaga=<job_id>`); política padrão sem contato direto/empresa no post.
- **Critério de aceite:** rascunho salvo/atualizável, texto editável, link público correto, sem vazar segredos.

### 2.3 Aprovar com publicar agora / agendar
1. Escolher "Publicar agora" ou "Agendar" (data/hora em `America/Sao_Paulo`).
2. Aprovar/publicar a vaga no site.
- **Critério de aceite (site-first):** vaga publicada no site independentemente de falha/indisponibilidade do Facebook. Registro social criado/atualizado conforme fluxo (best-effort assíncrono).

### 2.4 Validar status, retry, erros e link
1. Acompanhar status no admin (badges/erro resumido/link do post publicado, visão de posts sociais).
2. Para falhas elegíveis com integração conectada, acionar "Tentar novamente" e confirmar comportamento idempotente/no-op quando não elegível.
3. Simular/observar reconexão necessária (`needs_reconnect`) quando aplicável e seguir orientação segura.
- **Critério de aceite:** estados e mensagens pt-BR seguros (sem tokens/payloads brutos), sem duplicidade de publicação, retry respeita elegibilidade/regras do pipeline, link do post aparece quando disponível.

### 2.5 Não impactar o site público
- **Critério de aceite:** falhas sociais, delays ou indisponibilidade da Graph API **não** bloqueiam/derrubam publicação no site nem removem/alteram posts de forma síncrona indevida (fire-and-forget conforme contrato).

### Rollback/segurança operacional
- Revogar/desconectar integração em caso de incidente; rotacionar segredos/tokens no provedor e no backend (nunca no frontend).
- Não registrar tokens/códigos OAuth em issues/docs; manter evidências sanitizadas.

## 3) Configuração de cron no Render (publicação social e expiração)

- **Expiração (existente):** `POST /api/v1/admin/expire` protegido por `X-Cron-Secret` (`CRON_SECRET`) — contrato fail-closed/idempotente preservado (T-06-01). Configurar job/cron para chamar o endpoint canônico conforme `docs/DEPLOY.md`.
- **Worker social (Phase 17):** `POST /api/v1/admin/social/worker` protegido por `X-Cron-Secret` (`CRON_SECRET`), processa posts elegíveis de forma idempotente (claim `FOR UPDATE SKIP LOCKED`).
  - **Opção A:** reaproveitar agendamento/infra de cron existente adicionando chamada separada ao worker (1–5 min conforme necessidade) com o mesmo segredo.
  - **Opção B:** criar job de cron dedicado no Render para o worker, mantendo `CRON_SECRET` consistente e seguro.
- **Checklist:** segredo configurado apenas no backend/Render/GitHub (conforme uso), endpoints respondem 401/503 sem credencial válida (fail-closed), execuções idempotentes, logs sem segredos.

## 4) Checklist App Review / modo Live (Meta)

> Itens abaixo podem exigir credenciais reais e submissão/revisão pela Meta; marcar como **handoff** quando não executável.

- [ ] App em modo desenvolvimento validado com usuários/página de teste e permissões mínimas (`pages_show_list`, `pages_manage_posts`, `pages_read_engagement`).
- [ ] `META_GRAPH_VERSION`, redirect URI, domínios/URLs e configurações do app consistentes com o ambiente.
- [ ] Política de privacidade/termos e telas exigidas pela Meta revisadas e acessíveis (quando aplicável ao produto).
- [ ] Descrições de uso das permissões preparadas (publicar vagas na Página mediante ação/admin, sem automações indevidas).
- [ ] Evidências (capturas/vídeo) do fluxo OAuth, seleção de página e publicação/status no admin preparadas para revisão.
- [ ] Troca para modo Live / App Review solicitada e aprovada **apenas** após testes reais bem-sucedidos e com credenciais de produção seguras.
- [ ] `SITE_PUBLIC_URL`, chaves/segredos e cron configurados no ambiente de produção canônico; smoke operacional executado.

**Critério de aceite (documentação):** roteiro e checklist completos, reproduzíveis e seguros (sem segredos). **Critério de aceite (execução real):** somente com evidência registrada em ambiente autorizado.

## 5) Prontidão Instagram e mídia IG (META-03 / Phase 29)

Esta seção complementa a integração Facebook existente com a base de prontidão Instagram (IG) e mídia pública para publicação futura. **A prontidão IG é aditiva:** ela não deve quebrar nem apresentar a conexão Facebook como desconectada quando apenas o Instagram não estiver pronto.

### 5.1 Permissões e escopos

O fluxo Meta/OAuth deve solicitar/validar as permissões necessárias para Facebook e Instagram:

- `pages_show_list`
- `pages_manage_posts`
- `pages_read_engagement`
- `instagram_basic`
- `instagram_content_publish`

**Reconexão/reautorização:** conexões Facebook existentes podem não ter os escopos IG novos. Nesses casos, o admin deve ver estado acionável e usar **Reconectar** para reautorizar com as permissões necessárias.

### 5.2 Pré-requisitos de vínculo Página ↔ Instagram

- A Página do Facebook selecionada deve estar vinculada a uma conta Instagram Business/Creator.
- O admin deve ter os papéis/tarefas necessários na Página/conta vinculada.
- A verificação de prontidão usa o probe Graph conceitual `/{page-id}?fields=instagram_business_account{id,username}` (implementado no backend; referência operacional).
- Se não houver vínculo, a UI deve orientar correção sem expor erros brutos da Graph.

### 5.3 Variáveis de ambiente (mídia IG)

Além das variáveis Meta já documentadas, configurar:

- `MEDIA_PUBLIC_BASE_URL`: base pública HTTPS explícita do backend para servir mídia IG acessível pela Meta. **Não usar localhost/IP privado** e **não inferir** de `SITE_PUBLIC_URL`. Exemplo: `https://api.seudominio.com`.
- Demais variáveis Meta sociais: `META_APP_ID`, `META_APP_SECRET`, `META_GRAPH_VERSION`, `META_OAUTH_REDIRECT_URI`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, `SITE_PUBLIC_URL` conforme aplicável.

Notas operacionais:
- Geração de card IG usa Pillow no backend com fontes empacotadas no repositório; não requer R2/S3 no v1.5.
- O endpoint público de mídia deve estar acessível sem autenticação por HTTPS público para que a Meta consiga buscar a imagem.

### 5.4 Estados de prontidão IG e troubleshooting

| Estado | Significado | Ação do admin (pt-BR segura) |
|--------|-------------|------------------------------|
| `ready` | Página conectada e IG vinculado/pronto | Confirmar username/ID exibido; usar Verificar agora se necessário |
| `missing_linkage` | Página sem conta Instagram Business/Creator vinculada | Vincular conta IG Business/Creator à Página no Meta e depois usar **Reconectar** ou verificar conforme orientação |
| `missing_permissions` | Escopos IG ausentes/insuficientes | Usar **Reconectar** para reautorizar concedendo `instagram_basic` e `instagram_content_publish` |
| `needs_reconnect` | Token/conexão IG precisa renovação/reconexão | Usar **Reconectar** para renovar a conexão com segurança |
| `unknown` | Verificação indisponível/transitória | Usar Verificar agora; se persistir, usar **Reconectar** |

Mensagens devem ser acionáveis em pt-BR e não expor tokens, segredos ou payloads brutos da Graph.

### 5.5 Checklist manual (handoff)

Execução real depende de credenciais/app Meta e Página de teste. Registrar evidência separadamente; **não marcar como aprovado sem execução real**.

- [ ] Conectar Página Facebook no `/admin/integracoes` com app/permissões corretas.
- [ ] Confirmar que a UI mostra prontidão IG aditiva (Facebook conectado permanece visível mesmo com IG não pronto).
- [ ] Validar estado `missing_linkage` com mensagem acionável quando a Página não tiver Instagram Business/Creator vinculado.
- [ ] Validar estado `missing_permissions` com CTA **Reconectar** quando escopos IG estiverem ausentes.
- [ ] Validar fluxo **Reconectar** e atualização de prontidão após reautorização.
- [ ] Confirmar que `MEDIA_PUBLIC_BASE_URL` aponta para backend público HTTPS e que a URL de mídia IG é acessível pela Meta (sem auth, sem localhost/privado).
- [ ] Confirmar que falhas de prontidão IG não bloqueiam/regredem comportamento Facebook.

### 5.6 Segurança operacional

- **Nunca expor tokens**, segredos, `SOCIAL_TOKEN_ENCRYPTION_KEY`, `CRON_SECRET` ou payloads sensíveis em logs, docs, screenshots ou evidências. Nunca registrar payloads brutos da Graph.
- Manter evidências sanitizadas (IDs públicos de página/IG podem aparecer quando necessários para operação; tokens não).
- Em caso de incidente, usar **Reconectar**/desconectar e rotacionar segredos no backend/provedor conforme procedimento seguro.
- Expiração/reconexão: quando a integração indicar `needs_reconnect`, o admin deve usar **Reconectar** em `/admin/integracoes`. Rotação de token/segredo deve ser feita apenas no backend/provedor (env/secret manager), nunca no frontend.

## 6) Variáveis de ambiente canônicas e segurança (Phase 31/32, D-11)

Fonte canônica: `backend/.env.example` e `backend/app/core/config.py`. Use placeholders seguros; nunca versionar segredos reais.

| Variável | Obrigatória? | Finalidade | Formato/Exemplo seguro (placeholder) | Comportamento quando ausente/inválida | Risco/Nota de segurança |
|---|---|---|---|---|---|
| `META_APP_ID` | Sim (para OAuth Meta) | Identifica app Meta no fluxo OAuth/Graph. | `123456789012345` | Fluxo OAuth/integração Meta não funciona; endpoints/config dependentes falham ou ficam indisponíveis. | Não é segredo como token, mas evite expor em evidências públicas desnecessárias. |
| `META_APP_SECRET` | Sim (para OAuth Meta) | Segredo do app Meta para troca/validação OAuth. | `replace_with_meta_app_secret` | OAuth/token exchange falha; integração não conecta. | **Segredo**. Nunca expor em logs/docs/frontend/evidências. Rotacionar no provedor e backend. |
| `META_GRAPH_VERSION` | Sim (default configurável) | Versão da Graph API usada por FB/IG. | `v21.0` | Config usa default; versão inválida pode causar erros de API. | Manter alinhado ao app/ambiente validado; mudanças exigem validação. |
| `META_OAUTH_REDIRECT_URI` | Sim (OAuth) | Callback OAuth registrado no app Meta. | `https://api.seudominio.com/api/v1/admin/integrations/meta/oauth/callback` | OAuth falha/retorno inválido. | Deve ser HTTPS pública válida em produção; não incluir segredos. |
| `SOCIAL_TOKEN_ENCRYPTION_KEY` | Sim (quando tokens sociais persistidos) | Chave Fernet para criptografar tokens sociais no backend. | `replace_with_valid_fernet_key` | Tokens não podem ser criptografados/decriptados com segurança; operações sociais falham (fail-safe). | **Segredo crítico**. Nunca expor tokens. Rotação exige plano de recriptografia/reconexão; nunca no frontend. |
| `SOCIAL_MAX_ATTEMPTS` | Sim (default) | Máximo de tentativas automáticas do pipeline social. | `5` | Valor inválido (`<=0`) falha validação de config. | Ajustar com cautela para evitar retry storm. |
| `SOCIAL_RETRY_DELAYS` | Sim (default) | Backoff/retry delays em segundos (CSV). | `300,900,3600,10800,21600` | Formato inválido falha validação de config. | Lista CSV de inteiros > 0; tuning afeta carga/retry storm. |
| `SITE_PUBLIC_URL` | Sim (para links públicos) | Base pública do site para link da vaga (`/?vaga=<job_id>`). | `https://seudominio.com` | Geração/link público falha ou fica inválido. | URL pública; não usar para inferir `MEDIA_PUBLIC_BASE_URL`. |
| `MEDIA_PUBLIC_BASE_URL` | Sim (para IG media) | Base HTTPS pública explícita para servir mídia IG acessível pela Meta. | `https://api.seudominio.com` | Validação falha se ausente/inválida para fluxos que exigem mídia IG pública; config rejeita localhost/privado. | **Nunca localhost/IP privado**. Não inferir do request. Exposição é intencional apenas para endpoint público de mídia, sem segredos. |
| `CRON_SECRET` | Sim (cron/worker) | Protege endpoints operacionais (`/admin/expire`, `/admin/social/worker`) via `X-Cron-Secret`. | `replace_with_long_random_secret` | Endpoints protegidos respondem fail-closed (401/503 conforme contrato). | **Segredo**. Nunca expor em logs/docs/frontend. Rotacionar no backend e no executor de cron. |
| `SOCIAL_WORKER_SECRET` | Opcional/reservado | Reservado para segregação futura; manter coerente com operação se usado. | `replace_with_worker_secret` | Sem efeito se não usado pelo deploy; incoerência pode causar falha operacional futura. | Tratar como segredo quando preenchido. Não expor. |
| `IG_PUBLISH_HTTP_TIMEOUT_SECONDS` | Sim (default) | Timeout HTTP por chamada IG publish/status/permalink. | `20.0` | Valor `<=0` falha validação de config. | Budget operacional: valores baixos aumentam ambiguidade/timeout; valores altos prendem worker. |
| `IG_STATUS_POLL_MAX_ATTEMPTS` | Sim (default) | Máximo de polls de status do container IG. | `5` | Valor `<=0` falha validação de config. | Budget operacional: limita espera; evitar loops longos. |
| `IG_STATUS_POLL_DELAY_SECONDS` | Sim (default) | Delay entre polls de status IG. | `2.0` | Valor `<=0` falha validação de config. | Budget operacional: balancear latência e carga. |
| `IG_PUBLISH_MAX_ATTEMPT_SECONDS` | Sim (default) | Orçamento total por tentativa de publish/reconciliação IG. | `45.0` | Valor `<=0` falha validação de config. | Budget operacional: ao estourar após passo crítico, fluxo deve ficar ambíguo/bloqueado para reconciliação segura. |

**Orientação de expiração/reconexão/rotação:** se status indicar `needs_reconnect`, reconectar em `/admin/integracoes`. Rotação de `META_APP_SECRET`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, `CRON_SECRET` e tokens deve ser feita no backend/provedor com procedimento seguro; após rotação, validar reconexão e não expor valores em evidências.

## 7) Troubleshooting publicação Instagram (Phase 31)

Tabela acionável para operação segura. **Sem auto-retry cego. Sem retry storm.** Para ambiguidade, reconciliar antes de publicar.

| Estado/Sintoma | Significado | Causa provável | Ação do admin | Retry/Reconciliar? | Pré-condições | Escalar quando |
|---|---|---|---|---|---|---|
| `published` | Publicação IG confirmada. | Fluxo 2-passos concluiu com ID/mídia publicada. | Conferir status/permalink/IDs seguros no admin. | Não necessário. | Integração pronta, mídia válida, publish concluído. | Se UI mostrar publicado mas Meta não refletir após verificação autorizada. |
| `failed` (falha conclusiva segura) | Falha confirmada sem ambiguidade crítica de duplicação. | Erro permanente, mídia inválida, conta não pronta, ou configuração inválida. | Ler erro seguro pt-BR; corrigir causa (mídia, integração, config) e tentar novamente apenas quando aplicável. | Retry manual apenas se erro não for bloqueio/rate limit e pré-condições resolvidas. | Conta/prontidão ok; causa corrigida. | Erro persistente após correção e evidência sanitizada coletada. |
| Ambíguo/reconciliação requerida (`ig_reconciliation_required=true`, `needs_reconciliation`, container/publish inconclusivo) | Resultado IG inconclusivo após passo crítico; pode já ter publicado. | Timeout/rede/erro após criar container ou publicar; status não conclusivo. | **Não criar nova tentativa cega.** Usar retry/reconciliação segura no admin: o sistema deve checar IDs/container antes de publicar. | **Reconciliar antes de publicar**. Retry manual seguro somente com reconciliação. | `container_id`/IDs conhecidos quando disponíveis; integração pronta. | Repetir inconclusão, IDs inconsistentes, ou falta de evidência conclusiva após reconciliação. |
| `ig_rate_limit_blocked` / `content_publishing_limit` (2207042/runtime authority) | Bloqueio por limite/rate limit do Instagram. | Limite da plataforma atingido (runtime authority). | Aguardar janela indicada/razoável da plataforma; não insistir em retries. | **Não** fazer auto-retry/retry storm. Tentar manualmente só após espera. | Aguardar janela; confirmar integração pronta. | Bloqueio persiste além da janela esperada com evidência sanitizada. |
| `needs_reconnect` / integração não pronta | Conta/token/escopo/prontidão IG indisponível. | Token expirado, falta de permissão/escopo, vínculo IG ausente, conexão inválida. | Ir em `/admin/integracoes`, usar **Reconectar**/verificar prontidão; corrigir vínculo/permissões. | Não publicar antes de reconectar/verificar. Após pronto, retry conforme estado. | Admin com acesso; app/página/IG corretos. | Reconexão repetidamente falha com conta/permissões aparentemente corretas. |
| `publish_enabled=false` (não elegível por escolha do admin) | Instagram desativado intencionalmente para a vaga/provider. | Admin optou por não publicar no Instagram. | Se desejar publicar, habilitar IG na revisão e garantir mídia/legenda válidas. | Não é retry de falha; é nova elegibilidade/dispatch conforme fluxo. | Draft/revisão válida e aprovação/fluxo permitido. | Se habilitado e ainda não elegível, verificar validação/mídia/estado do post. |
| Permalink ausente após publish | Publicação concluída, mas permalink não recuperado. | Falha best-effort na busca de permalink após publish bem-sucedido. | Tratar como publicado se ID externo/mídia confirmado; verificar permalink depois em ambiente autorizado. | Não republicar cegamente. | Post publicado com ID seguro. | Necessidade operacional de permalink e API não retorna após tentativas autorizadas. |
| Container criado mas publish inconclusivo/timeout | Passo crítico executado sem confirmação final. | Timeout/erro após create container ou publish. | Tratar como ambíguo: reconciliar por IDs conhecidos antes de qualquer nova tentativa. | **Reconciliar antes de publicar**; sem auto-retry cego. | `container_id` conhecido; acesso à integração. | Reconciliar não confirma estado final. |

## 8) Checklist manual Meta (handoff explícito)

> **Handoff manual:** Execução real depende de credenciais/app Meta, Página/IG de teste, papéis/tarefas e autorização. **Não executado / não evidenciado nesta sessão** quando não houver execução real. **Não marcar como aprovado sem execução real.**

### Pré-condições
- Acesso autorizado ao app Meta, Página FB e conta IG Business/Creator vinculada.
- Variáveis canônicas configuradas no ambiente alvo (ver seção 6).
- Operador identificado e janela de mudança/evidência definida.

### Passos e critérios de evidência sanitizada
1. Conectar/reconectar integração em `/admin/integracoes` e validar prontidão IG.
2. Validar estados acionáveis (`needs_reconnect`, `missing_permissions`, `missing_linkage`, ready).
3. Executar fluxo de revisão/publicação IG em ambiente autorizado (quando aplicável) e observar status/logs seguros.
4. Verificar tratamento de erro/limite/reconciliação sem exposição de segredos.

### Registro (preencher ao executar)
| Item | Ambiente | Responsável | Data | Resultado | Evidência sanitizada | Executado nesta sessão? (sim/não) |
|---|---|---|---|---|---|---|
| OAuth/conexão Meta+IG |  |  |  |  |  | Não executado / não evidenciado nesta sessão |
| Prontidão IG (ready/missing/reconnect) |  |  |  |  |  | Não executado / não evidenciado nesta sessão |
| Publish IG 2-passos real |  |  |  |  |  | Não executado / não evidenciado nesta sessão |
| Reconciliação ambígua/rate limit real |  |  |  |  |  | Não executado / não evidenciado nesta sessão |

**Critério:** marcar "aprovado" somente com execução real e evidência sanitizada anexada. Caso contrário, manter como handoff.
