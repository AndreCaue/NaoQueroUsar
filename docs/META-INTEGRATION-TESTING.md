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

- Nunca registrar tokens, segredos, `SOCIAL_TOKEN_ENCRYPTION_KEY`, `CRON_SECRET` ou payloads sensíveis em docs, screenshots ou logs.
- Manter evidências sanitizadas (IDs públicos de página/IG podem aparecer quando necessários para operação; tokens não).
- Em caso de incidente, usar **Reconectar**/desconectar e rotacionar segredos no backend/provedor conforme procedimento seguro.
