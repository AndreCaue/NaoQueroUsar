# Requirements: EmpregaNoix v1.2

**Defined:** 2026-11-15
**Core Value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção. (Integração social não pode bloquear publicação no site.)

## v1.2 Requirements

Requirements for milestone v1.2 — Integração com Facebook Pages (publicação automática de vagas aprovadas). Cada requisito mapeia para fases do roadmap.

### Fundação Social, Dados & Configuração

- [x] **SOC-01**: Migração cria `social_accounts` com provider, page_id, page_name, token criptografado em repouso, status (`connected`/`needs_reconnect`/`disconnected`), `connected_at`, `token_checked_at`
- [x] **SOC-02**: Migração cria `social_posts` com FK `job_id`, provider, text, status (`draft`/`scheduled`/`publishing`/`published`/`failed`/`cancelled`), `scheduled_at`, attempts, `next_retry_at`, `last_error`, `external_post_id`, `published_at`, timestamps; índice único `(job_id, provider)` para idempotência
- [x] **SOC-03**: Migração opcional cria `social_post_logs` (histórico de tentativas com resposta resumida da API) se adotado pela implementação
- [x] **SOC-04**: `page_access_token` é criptografado em repouso (ex.: Fernet com chave em env `SOCIAL_TOKEN_ENCRYPTION_KEY`); segredos/tokens nunca em logs, respostas de API ou frontend
- [x] **SOC-05**: Interface `SocialPublisher` definida (contrato para publicação); `FacebookPublisher` implementa agora; arquitetura permite `InstagramPublisher` futuro sem reescrever fluxo
- [x] **SOC-06**: Config/envs documentadas em `.env.example`: `META_APP_ID`, `META_APP_SECRET`, `META_GRAPH_VERSION`, `META_OAUTH_REDIRECT_URI`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, `SOCIAL_WORKER_SECRET`, `SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS`, `SITE_PUBLIC_URL` (e demais necessárias)

### OAuth Meta & Integrações (Admin)

- [ ] **META-01**: Backend expõe endpoints OAuth Meta: iniciar (gera `state` anti-CSRF e redireciona), callback (valida `state`, troca code→user token→long-lived token, lista páginas via `/me/accounts`, obtém page access token), desconectar, status
- [ ] **META-02**: Permissões mínimas solicitadas: `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`; usa versão fixa/configurável da Graph API (`META_GRAPH_VERSION`, estável confirmada na doc)
- [ ] **META-03**: Fluxo suporta seleção da Página quando houver mais de uma; salva apenas uma única Página/conexão (único admin)
- [ ] **META-04**: Page token derivado de long-lived user token é validado (ex.: `/debug_token`); token inválido/expirado marca conta `needs_reconnect` e gera alerta no painel
- [ ] **META-05**: App Secret e tokens permanecem somente no backend; nenhuma credencial exposta ao frontend
- [x] **META-06**: Tela/seção admin "Integrações" permite conectar/desconectar Facebook, exibe status da conexão, nome da página e alerta de reconexão necessária

### Geração e Edição do Texto do Post (Revisão)

- [x] **POST-01**: Reutiliza integração LLM existente para gerar texto do post a partir dos dados estruturados da vaga (tom profissional e acolhedor, pt-BR, emojis moderados, até ~700 caracteres, destaque cargo/cidade/salário se informado/benefícios, CTA com link, 3–5 hashtags) terminando com link da vaga
- [x] **POST-02**: Fallback por template estático se LLM falhar (revisão nunca bloqueada); texto gerado ao entrar em revisão e salvo como `draft`
- [x] **POST-03**: Revisor pode editar o texto antes de aprovar (campo editável, contador de caracteres, botão "regenerar com IA", preview simples)
- [x] **POST-04**: Revisor escolhe "publicar agora / agendar" com data e hora (fuso `America/Sao_Paulo`); padrão imediata; agendamento respeita horário escolhido
- [x] **POST-05**: Texto aprovado é imutável após envio e fica salvo em `social_posts`
- [x] **POST-06**: Por padrão o post não inclui contato direto da vaga, apenas link para o site (`SITE_PUBLIC_URL` + URL pública da vaga); comportamento configurável conforme implementação documentada

### Publicação, Worker, Retry & Idempotência

- [ ] **PUB-01**: `FacebookPublisher.publish(post)` cria post via `POST /{page_id}/feed` com `message` e `link` (URL pública da vaga)
- [ ] **PUB-02**: Aprovação publica a vaga no site mesmo se o Facebook estiver fora/indisponível (falha social nunca derruba/bloqueia fluxo do site)
- [ ] **PUB-03**: Publicação imediata é tentada de forma assíncrona após aprovação (sem bloquear resposta); cron cobre falhas
- [ ] **PUB-04**: Worker por polling (endpoint protegido por segredo e/ou script) acionado por Cron Job do Render (1–5 min) processa `social_posts` elegíveis (`scheduled`/failed retryable, `scheduled_at`/`next_retry_at <= now`) usando `SELECT ... FOR UPDATE SKIP LOCKED`
- [ ] **PUB-05**: Retry automático com backoff exponencial configurável por env (`SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS`); padrão 5 tentativas (5min/15min/1h/3h/6h)
- [ ] **PUB-06**: Erros transitórios (rede, 5xx, rate limit) → retry com backoff; erros permanentes (token inválido, permissão revogada, conteúdo rejeitado) → falha sem retry com sinalização clara
- [ ] **PUB-07**: Idempotência: nunca criar post duplicado (checar status/`external_post_id` antes de enviar, lock de linha/unique constraint; resistente a cron concorrente e clique duplo)
- [ ] **PUB-08**: Post é fire-and-forget — editar, fechar ou expirar a vaga não atualiza nem remove o post no Facebook

### UI de Status Social & Operações

- [ ] **UI-01**: Listagem/detalhe da vaga no admin exibe badge de status social (agendado, publicado, falhou etc.), mensagem de erro resumida, link para post publicado (quando disponível)
- [ ] **UI-02**: Botão manual "tentar novamente" no painel para posts elegíveis; ação respeita idempotência e regras de retry

### Testes & Documentação

- [ ] **TEST-01**: Testes unitários cobrem geração de texto (LLM mockado), classificação de erros e cálculo de backoff
- [ ] **TEST-02**: Testes de integração cobrem `FacebookPublisher` e OAuth com Graph API mockada (sem chamadas reais em CI)
- [ ] **TEST-03**: Testes de concorrência do worker (`SKIP LOCKED`) e idempotência (sem duplicatas)
- [ ] **TEST-04**: Roteiro de teste manual documentado para Página real com app Meta em modo desenvolvimento
- [ ] **DOC-01**: Documentação inclui setup do app Meta, variáveis de ambiente, configuração do cron no Render (novo ou reaproveitado) e checklist de App Review/modo Live

### Carry-over: Fechamento de Gaps do Audit v1.1 (aceitos)

- [ ] **AUD-01**: Fechar/validar requisitos de extração **EXTR-10/11/12** (chunking ≤6K sem perda, regra de ao menos um contato no ingest, fallback de modelo Groq sem saída silenciosa vazia) com evidência verificável
- [ ] **AUD-02**: Fechar/validar requisitos públicos **PUBL-10/11/12/13/14** (board/cards/modal/reveal/candidatura) no escopo auditado com evidência
- [ ] **AUD-03**: Fechar/validar requisitos de busca/filtro/ordenação **SRCH-10/11/12** com evidência
- [ ] **AUD-04**: Fechar/validar requisitos de UI/tema/ads **UIUX-10/11/12** com evidência
- [~] **AUD-05**: Backfill rastreável criado em `.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-VERIFICATION.md` (D-03) e caveats de 07/08 reconciliados com cross-ref/estado atual; rastreabilidade ancorada em `18-AUDIT-MATRIX.md` e audit v1.1. **Evidência parcial+handoff:** DB-backed suites ainda bloqueadas (`relation "jobs" does not exist`), verificações humanas/browser e smoke/runtime canônico permanecem pendentes (não fechado sem prova).

## v2 Requirements (Future)

- Instagram publishing (`InstagramPublisher`) e fluxos específicos de mídia/conta
- Geração de imagem para posts sociais
- Sincronização de edição/remoção do post quando a vaga muda/expira
- Múltiplas páginas/contas e múltiplos administradores para social
- Métricas/insights de engajamento dos posts

## Out of Scope

| Feature | Reason |
|---------|--------|
| Instagram, imagem, sync edição/remoção, múltiplas páginas, métricas | Explicitamente fora do v1.2 (decisão do milestone) |
| Login/cadastro de usuário comum | Diferencial do produto é acesso sem conta |
| Renovação de vagas expiradas | Expiração definitiva por design |
| Submissão pública de vagas por terceiros | Não previsto no escopo atual |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SOC-01 | Phase 14 | Complete |
| SOC-02 | Phase 14 | Complete |
| SOC-03 | Phase 14 | Complete |
| SOC-04 | Phase 14 | Complete |
| SOC-05 | Phase 14 | Complete |
| SOC-06 | Phase 14 | Complete |
| META-01 | Phase 15 | Complete |
| META-02 | Phase 15 | Complete |
| META-03 | Phase 15 | Complete |
| META-04 | Phase 15 | Complete |
| META-05 | Phase 15 | Complete |
| META-06 | Phase 15 | Complete |
| POST-01 | Phase 16 | Complete |
| POST-02 | Phase 16 | Complete |
| POST-03 | Phase 16 | Complete |
| POST-04 | Phase 16 | Complete |
| POST-05 | Phase 16 | Complete |
| POST-06 | Phase 16 | Complete |
| PUB-01 | Phase 17 | Pending |
| PUB-02 | Phase 17 | Pending |
| PUB-03 | Phase 17 | Pending |
| PUB-04 | Phase 17 | Pending |
| PUB-05 | Phase 17 | Pending |
| PUB-06 | Phase 17 | Pending |
| PUB-07 | Phase 17 | Pending |
| PUB-08 | Phase 17 | Pending |
| UI-01 | Phase 17 | Complete |
| UI-02 | Phase 17 | Complete |
| TEST-01 | Phase 18 | Pending |
| TEST-02 | Phase 18 | Pending |
| TEST-03 | Phase 18 | Pending |
| TEST-04 | Phase 18 | Pending |
| DOC-01 | Phase 18 | Pending |
| AUD-01 | Phase 18 | Pending |
| AUD-02 | Phase 18 | Pending |
| AUD-03 | Phase 18 | Pending |
| AUD-04 | Phase 18 | Pending |
| AUD-05 | Phase 18 | Evidência parcial+handoff (18-03: `11-VERIFICATION.md`, caveats 07/08 reconciliados, `18-AUDIT-MATRIX.md`) |

---
*Requirements defined: 2026-11-15 for v1.2 Integração com Facebook Pages*
*Last updated: 2026-11-16 — Phase 18 Plan 03: AUD-05 reconciliado como evidência parcial+handoff com backfill `11-VERIFICATION.md` e referências em `18-AUDIT-MATRIX.md` (sem fechar lacunas dependentes de runtime/DB/browser no escuro)*
