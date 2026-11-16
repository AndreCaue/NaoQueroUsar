# Phase 17: Publicação Assíncrona, Retry, Idempotência e Status - Context

**Gathered:** 2026-11-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Entregar publicação/agendamento de posts sociais no Facebook de forma **assíncrona e resiliente** (sem duplicatas), expondo no admin o status, erro resumido, link do post publicado e ação de "Tentar novamente" para casos elegíveis.

**Em escopo (Fase 17):** disparo de tentativa assíncrona na aprovação quando aplicável e/ou processamento de itens agendados elegíveis; worker protegido acionado por cron (Render, 1-5 min) com claim/lock seguro (`FOR UPDATE SKIP LOCKED`) sem bloquear a resposta de aprovação; implementação real do `FacebookPublisher` (`POST /{page_id}/feed` com `message` e `link`); registro de `external_post_id`/`published_at` em sucesso; política de retry/backoff configurável (default 5 tentativas), classificação transitória/permanente, `next_retry_at` e erro resumido; idempotência contra concorrência/reexecução de cron/clique duplo; posts fire-and-forget (editar/fechar/expirar vaga não altera/remove post no Facebook); UI admin com badge/status social por vaga, erro resumido, link do post publicado e "Tentar novamente" para casos elegíveis (UI-01, UI-02).

**Fora de escopo:** alterações no fluxo público do site além do já existente; geração/edição do draft social (Fase 16, já concluída) exceto integrações estritamente necessárias para status/retry; sincronização de edição/remoção do post no Facebook (fire-and-forget); Instagram, múltiplas páginas/admins, métricas/insights; testes/docs de fechamento/App Review (Fase 18); fechamento dos gaps aceitos do audit v1.1 (Fase 18).

</domain>

<decisions>
## Implementation Decisions

### Disparo e processamento
- **D-01:** Para aprovação com post "Publicar agora" (`scheduled_at = agora`), a 1ª tentativa deve ser **imediata e não bloqueante** após o commit da aprovação, **com fallback no cron/worker** (1-5 min) para garantir processamento/retries/agendados mesmo se a tentativa imediata falhar.
- **D-02:** O worker acionado por cron externo (Render) deve ser **protegido reutilizando `CRON_SECRET`** no mesmo padrão operacional de `/admin/expire` (`X-Cron-Secret`/`require_cron_secret`), mantendo um único segredo de cron.
- **D-03:** A tentativa imediata pós-aprovação deve usar o **mesmo pipeline único** de claim/publicação do worker de cron (após commit, não bloqueante), compartilhando lógica de lock/claim, transições de status, logging e idempotência.
- **D-04:** Elegibilidade base do worker: processar **posts `scheduled` com `scheduled_at <= agora`** e **posts `failed` elegíveis a retry automático com `next_retry_at <= agora`** (respeitando limite/config). Não incluir por padrão recuperação automática de registros presos em `publishing`; se necessário, tratar como refinamento técnico seguro sem ampliar escopo.

### Retry e falhas
- **D-05:** Classificar falhas em **transitórias vs permanentes**: transitórias (rede, 5xx, timeout/rate limit temporário) seguem retry automático com backoff configurável até o limite; permanentes (token/permissão inválidos, erro de requisição/conteúdo confirmado, etc.) não entram em retry automático.
- **D-06:** Se a integração Facebook estiver desconectada/`needs_reconnect` ou sem token/página válido, tratar como **falha bloqueante até reconectar** (não-retryable automaticamente) com erro resumido orientando reconexão; retry automático não deve ficar em loop sem conexão válida.
- **D-07:** Ao esgotar `SOCIAL_MAX_ATTEMPTS`, o post fica em **`failed` final sem `next_retry_at` automático**; novas tentativas só via ação manual elegível ("Tentar novamente"), respeitando as mesmas regras do pipeline.
- **D-08:** O erro exibido ao admin deve ser **mensagem amigável e resumida em pt-BR**, segura (sem segredos/tokens/payloads brutos), mapeada por categoria/situação (ex.: falha temporária, reconexão necessária, limite temporário, falha definitiva).

### Idempotência e duplicatas
- **D-09:** Usar **claim atômico no banco** para concorrência: selecionar elegíveis com `FOR UPDATE SKIP LOCKED` e transicionar para `publishing` na transação de claim antes de chamar a Graph API, evitando processamento paralelo do mesmo post.
- **D-10:** Se o registro já possuir `external_post_id` (ou já estiver `published`), tentativas futuras (cron, imediata, manual, reexecução) devem ser **no-op idempotente**: não reenviar à Graph API e reconciliar estado/timestamps de forma segura.
- **D-11:** Em caso **ambíguo** (possível sucesso remoto sem confirmação local, ex.: timeout antes de persistir `external_post_id`), **priorizar evitar duplicata**: não republicar automaticamente; registrar estado/erro seguro e exigir verificação/retry manual consciente conforme elegibilidade.
- **D-12:** O botão "Tentar novamente" deve passar pelo **mesmo fluxo idempotente** de claim/processamento do worker, respeitando elegibilidade e ignorando cliques repetidos/itens já em processamento ou publicados.

### Status e ações no admin (UI-01, UI-02)
- **D-13:** Status social por vaga deve ser visível no **fluxo admin de revisão/edição** e, para acompanhamento pós-aprovação, em uma **nova visão/lista simples no admin de posts/vagas sociais** (agendados, publicados, falhos etc.), permitindo consultar status/erro/link e acionar retry quando elegível.
- **D-14:** Exibir **badges/rótulos pt-BR para todos os estados relevantes**: sem rascunho, rascunho, agendado, publicando, publicado (com link do post quando disponível), falhou (com erro resumido) e cancelado, quando aplicável.
- **D-15:** "Tentar novamente" deve ficar disponível apenas para **falhas elegíveis com integração conectada e post não publicado**; desabilitar/ocultar (com orientação quando pertinente) para publicado, em processamento, agendado futuro normal, sem conexão/reconexão necessária ou casos não elegíveis pelas regras do pipeline.

### OpenCode's Discretion
- Nomes/paths exatos de endpoints (ex.: endpoint de worker cron, endpoint de retry manual, endpoint/listagem de status social) e formato de payloads/respostas, desde que protegidos, consistentes e sem expor segredos.
- Estratégia concreta de agendamento da tentativa imediata não bloqueante (BackgroundTasks, task no loop, etc.) e granularidade de batches/limites por ciclo do worker, mantendo claim atômico e baixo impacto.
- Mapeamento detalhado de códigos/erros da Graph API para categorias transitória/permanente/ambígua e textos pt-BR finais, preservando segurança e utilidade.
- Uso de `social_post_logs` (granularidade de tentativas/eventos), estrutura de mensagens de `last_error` e campos auxiliares de auditoria/observabilidade dentro do schema existente.
- Implementação da URL/link do post publicado na UI (derivação a partir de `external_post_id`/page ou campo armazenado), desde que confiável e segura.
- Composição visual exata (componentes, posicionamento de badges/lista, estados de loading/empty/erro) alinhada aos padrões do admin.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo, requisitos e estado do milestone
- `.planning/ROADMAP.md` §"Phase 17: Publicação Assíncrona, Retry, Idempotência e Status" — goal, depends_on (16), requisitos `PUB-01..PUB-08`, `UI-01..UI-02`, critérios de sucesso (async+cron, `FOR UPDATE SKIP LOCKED`, retry/backoff, idempotência, UI status/retry).
- `.planning/REQUIREMENTS.md` — definições de `PUB-01`..`PUB-08` e `UI-01`..`UI-02` e rastreabilidade v1.2.
- `.planning/PROJECT.md` — core value, decisões v1.2 (Facebook only, 1 página/1 admin, falha social não bloqueia site, fire-and-forget, retry/backoff configurável + retry manual, texto imutável após envio, segredos/tokens só no backend criptografados) e stack/constraints.
- `.planning/STATE.md` — foco atual (Phase 17), decisões acumuladas e pendências herdadas (carry-over v1.1, convenções do repo).

### Decisões das fases anteriores (base obrigatória)
- `.planning/phases/14-fundacao-social-dados-e-configuracao/14-CONTEXT.md` — fundação social: `social_accounts`/`social_posts`/`social_post_logs`, enums/status, crypto Fernet, `SocialPublisher`/`PublishResult`/stub `FacebookPublisher`, config/env (`META_*`, `SOCIAL_*`, `SITE_PUBLIC_URL`, `SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS`, `SOCIAL_WORKER_SECRET`).
- `.planning/phases/15-oauth-meta-e-integracoes-no-admin/15-CONTEXT.md` — OAuth Meta, 1 página/1 admin, estados de conta (`connected`/`needs_reconnect`/`disconnected`), validação sob demanda e UI de Integrações sem exposição de segredos.
- `.planning/phases/16-geracao-revisao-e-aprovacao-do-post-social/16-CONTEXT.md` — draft/revisão/agendamento (`America/Sao_Paulo`), approve site-first com registro social best-effort, `scheduled`/`scheduled_at` (imediato = agora), texto final ao aprovar, política de conteúdo/link público, deep-link `/?vaga=<job_id>`.

### Backend — modelos, persistência e serviços sociais
- `backend/app/models/social_post.py` — `SocialPost`/`SocialPostStatus` (`draft/scheduled/publishing/published/failed/cancelled`), campos operacionais (`attempts`, `next_retry_at`, `last_error`, `external_post_id`, `published_at`, `scheduled_at`) e índices/unique `(job_id, provider)`.
- `backend/app/models/social_account.py` — conta Meta conectada/`needs_reconnect`, `page_id/page_name`, token criptografado em repouso.
- `backend/app/models/social_post_log.py` — log/auditoria de tentativas/resultados (se adotado para PUB/observabilidade).
- `backend/app/crud/social_posts.py` — operações atuais de draft/upsert/schedule; ponto natural para extensões de claim/status/retry/consulta.
- `backend/app/services/social/publisher.py`, `backend/app/services/social/types.py`, `backend/app/services/social/facebook.py` — contrato `SocialPublisher`, `PublishResult`/categorias e stub `FacebookPublisher` a implementar (Fase 17).
- `backend/app/services/social/crypto.py`, `backend/app/services/social/meta_oauth.py`, `backend/app/services/social/post_generation.py` — crypto/tokens, validação/estado Meta e geração de conteúdo (contexto e reutilização segura).

### Backend — API, auth operacional, scheduler e config
- `backend/app/api/v1/admin.py` — fluxo atual de aprovação site-first + registro social best-effort, endpoints de draft social, endpoint cron protegido `POST /admin/expire` (`require_cron_secret`) e convenções admin.
- `backend/app/deps.py` — `require_admin`, `require_cron_secret` e dependências de proteção.
- `backend/app/core/scheduler.py` — padrão de `AsyncIOScheduler`/drain/startup-shutdown usado para expiry (referência de execução in-process e integração com lifespan).
- `backend/app/core/config.py` e `backend/.env.example` — `CRON_SECRET`, `SCHEDULER_ENABLED`, `SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS`, `SOCIAL_WORKER_SECRET`, `META_*`, `SITE_PUBLIC_URL` e validações.

### Frontend admin — revisão/integrações e cliente de API
- `frontend/app/admin/review/ReviewQueue.tsx`, `frontend/app/admin/review/EditJobDialog.tsx`, `frontend/app/admin/review/page.tsx`, `frontend/components/admin/ReviewRow.tsx` — fluxo atual de revisão/aprovação/edição e ponto de integração para status/retry social por vaga.
- `frontend/app/admin/integracoes/IntegrationsClient.tsx`, `frontend/app/admin/integracoes/page.tsx` — padrões de status/alertas/ações da integração Meta (reconexão).
- `frontend/lib/api.ts` — tipos/chamadas admin existentes (`approveJob`, draft social, integrações Meta) a estender para status/listagem/retry social.

### Comportamento público relacionado
- `frontend/app/(public)/page.tsx` — deep-link público `?vaga=<job_id>` (base para `link` do post via `SITE_PUBLIC_URL`).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SocialPost` (`backend/app/models/social_post.py`): estados, `attempts/next_retry_at/last_error/external_post_id/published_at/scheduled_at`, índices operacionais e unique `(job_id, provider)` — base direta para claim, retry e UI de status.
- `SocialPostLog` e `SocialAccount` (`backend/app/models/*`): trilha de tentativas e estado de conexão/token criptografado para bloqueios por `needs_reconnect`.
- `SocialPublisher`/`PublishResult`/`PublishFailureCategory` (`backend/app/services/social/{publisher,types}.py`): contrato async e tipagem para classificar sucesso/falha e registrar resultado.
- `FacebookPublisher` stub (`backend/app/services/social/facebook.py`): ponto de implementação real do `POST /{page_id}/feed` sem acoplamento externo ao restante do fluxo.
- `crud/social_posts.py`: padrão de acesso com `flush` e controle de transação no chamador; já possui upsert/schedule — extensível para claim/retry/consulta.
- `admin.py` + `deps.require_cron_secret`: aprovação site-first best-effort já implementada e padrão de endpoint operacional protegido por cron (`X-Cron-Secret`).
- `core/scheduler.py`: `AsyncIOScheduler` no loop da app, job idempotente, pause/drain no shutdown — referência para tentativa imediata/pipeline in-process compatível.
- `ReviewQueue.tsx`/`EditJobDialog.tsx` + `frontend/lib/api.ts`: padrões de UI/feedback/toasts, fetch admin autenticado e integração do draft/aprovação social.

### Established Patterns
- Segredos/tokens e chamadas sensíveis permanecem no backend; UI consome apenas estados/erros seguros.
- Aprovação de vaga é **site-first** e independente de falhas sociais (best-effort separado) — deve ser preservado.
- Jobs sociais fire-and-forget: alterações posteriores na vaga não sincronizam/removem publicação no Facebook.
- Config centralizada em `Settings` com defaults/validação (`SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS` CSV, `CRON_SECRET`, `SITE_PUBLIC_URL`).
- SQLAlchemy 2 async + transações explícitas; operações de fila/concorrência devem usar locks/claims no Postgres conforme requisitos.

### Integration Points
- **Claim/dispatch:** novo(s) serviço(s)/CRUD para selecionar elegíveis e transicionar para `publishing` com `FOR UPDATE SKIP LOCKED`, reutilizado por cron e disparo imediato pós-aprovação.
- **Publicação real:** implementar `FacebookPublisher.publish` consumindo conta/página conectada e token descriptografado com segurança, enviando `message` + `link` e retornando `external_post_id`/categoria de falha.
- **Endpoints:** worker cron protegido por `CRON_SECRET`, retry manual elegível, e consulta/listagem de status social por vaga para suportar UI-01/UI-02 e visão pós-aprovação.
- **UI admin:** enriquecer revisão/edição com badges/erro/link e adicionar visão/lista simples de posts/vagas sociais para acompanhamento e retry após saída da fila.
- **Observabilidade:** registrar tentativas/resultados (ex.: `social_post_logs`/`last_error`/contadores) de forma segura para auditoria e diagnóstico.

</code_context>

<specifics>
## Specific Ideas

- "Publicar agora" deve priorizar entrega rápida: tentativa imediata não bloqueante após aprovação + cron como fallback/rede de segurança.
- Erros para o admin devem ser claros em pt-BR e orientativos (ex.: reconectar integração quando aplicável), sem vazar detalhes sensíveis.
- "Tentar novamente" deve ser seguro contra cliques repetidos e não criar duplicatas; elegível principalmente para falhas com conta conectada e post ainda não publicado.
- A nova visão pós-aprovação deve ser simples e operacional (lista de posts/vagas sociais com status, erro resumido, link e retry elegível), sem virar um painel complexo de analytics (fora de escopo).

</specifics>

<deferred>
## Deferred Ideas

- Instagram, múltiplas páginas/admins, métricas/insights de engajamento e sincronização de edição/remoção de posts — fora do milestone v1.2.
- Recuperação automática avançada de itens presos em `publishing` (timeout/orfãos) não foi selecionada como requisito desta discussão; avaliar apenas se necessário para robustez sem ampliar escopo.
- Testes automatizados/manuais abrangentes, documentação operacional (setup Meta/envs/cron/App Review) e fechamento de gaps/evidências do audit v1.1 — Phase 18.

</deferred>

---

*Phase: 17-publicacao-assincrona-retry-idempotencia-e-status*
*Context gathered: 2026-11-16*
