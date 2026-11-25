# Phase 31: Independent Publish Pipeline - Context

**Gathered:** 2026-11-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Entregar a publicação Instagram de forma assíncrona, segura e independente do Facebook (PUBL-01..05). A fase cobre o pipeline backend de publicação IG via Graph API (2 passos), persistência/auditoria segura, idempotência/reconciliação contra ambiguidade, e tratamento seguro de rate/daily limits. A experiência de revisão/ajuste por vaga já foi entregue na Phase 30; esta fase consome os drafts/status por provider e os contratos de mídia/prontidão das Phases 29/30 sem regredir o fluxo Facebook/site.

</domain>

<decisions>
## Implementation Decisions

### Modelo de execução FB+IG
- **D-01:** **Ciclo por provider.** Generalizar o ciclo para iterar providers suportados (Facebook, Instagram), mantendo claim/processamento por item e isolamento por post/provider. Reaproveitar o padrão atual de `list_due_for_claim(provider=...)` / `run_social_publish_cycle`, sem acoplar falhas entre providers (PUBL-01).
- **D-02:** **Worker drena todos; retry infere provider.** `/admin/social/worker` processa todos os providers suportados em blocos independentes na mesma invocação, agregando contadores; retry/dispatch por `post_id` carrega o `social_post` e usa seu `provider`. Mantém endpoint simples e operação unificada.
- **D-03:** **Core compartilhado + handler por provider.** Manter núcleo comum de claim/attempt/log/idempotência/backoff e extrair handler/adapter por provider para conta/credenciais, payload, publisher e mapeamento de erros. Reaproveitar `SocialPublisher`/`PublishResult` e isolar bugs de IG do FB.
- **D-04:** **Resultado do worker agregado + breakdown por provider.** Manter contadores totais para compatibilidade e adicionar breakdown por provider (facebook/instagram) na resposta/log; cada provider roda em bloco isolado.
- **D-05:** **`publish_enabled=false` ignorado no claim.** `list_due_for_claim` só considera posts elegíveis com `publish_enabled=true`; posts desativados não são claimados nem mutados pelo worker. Preserva escolha intencional do admin.
- **D-06:** **Dispatch imediato independente por post/provider.** Para cada `social_post` elegível (FB/IG), disparar processamento independente (background/worker) por `post_id`; falha/timeout em um não afeta o outro. Alinha com PUBL-01 e com `process_social_post_safe(post_id)`.
- **D-07:** **IG indisponível/não pronto = falha final acionável.** Se conta IG não pronta, token inválido ou `needs_reconnect`, marcar como `failed` final (sem auto-retry) com mensagem segura em pt-BR orientando reconexão/verificação em Integrações. Evita retry storm e deixa estado claro.
- **D-08:** **Ordem sequencial por provider, isolada.** Dentro da mesma invocação do worker, processar um provider por vez (ex.: FB depois IG), cada um em bloco isolado com próprios claims/processamentos. Simples, previsível e suficiente para o volume esperado.

### Estados IG 2-passos/ambiguidade
- **D-09:** **Ambiguidade bloqueia para verificação/reconciliação.** Se houver timeout/resultado ambíguo após criar container IG (ou antes de confirmar publish), persistir IDs conhecidos, marcar estado ambíguo seguro sem auto-retry e exigir verificação/reconciliação antes de nova tentativa. Nunca duplicação cega (PUBL-04).
- **D-10:** **Colunas explícitas em `social_posts`.** Persistir IDs/estado IG em campos dedicados (ex.: container ID, ID final de mídia/publicação, permalink, metadados de reconciliação necessários), além dos campos atuais. `external_post_id` pode representar o ID final publicado; logs complementam auditoria.
- **D-11:** **Polling limitado quando necessário.** Após criar container, consultar status só quando necessário (não concluído/in_progress), com limite curto de tentativas/espera dentro do orçamento de timeout; se expirar sem conclusão segura, tratar como ambíguo/bloqueado (PUBL-02).
- **D-12:** **Ambíguo = `failed` + bloqueio de reconciliação.** Reusar status `failed` com erro seguro específico e metadados de reconciliação (container/IDs conhecidos, motivo bloqueado). Preserva enum atual e padrão já usado no FB, exigindo ação explícita antes de retry.
- **D-13:** **Retry manual reconcilia antes de publicar.** Ao retry manual em post IG ambíguo com `container_id` conhecido, consultar status/resultado do container ou mídia publicada antes de qualquer novo publish; se já publicado, registrar IDs/permalink e concluir; se container pronto, publicar o mesmo container; se expirado/inválido, falhar com orientação segura. Nunca criar novo container cegamente.
- **D-14:** **Orçamento limitado por tentativa.** Definir timeout por chamada HTTP e orçamento total limitado por tentativa; se estourar após ponto crítico (container criado/publicação enviada), marcar ambíguo/bloqueado para reconciliação. Evita worker preso e respeita PUBL-02.
- **D-15:** **Classificação de status do container.** `FINISHED` segue para publish; `IN_PROGRESS` entra em polling limitado; `ERROR/EXPIRED` vira falha conclusiva (nova tentativa pode criar novo container apenas quando seguro e sem ambiguidade de publish); timeout/inconclusivo vira ambíguo bloqueado.
- **D-16:** **Permalink best-effort pós-publish.** Após publish IG bem-sucedido, tentar buscar permalink em chamada separada; se falhar, manter post como publicado com ID e sem permalink (sem reverter sucesso). Atende PUBL-03 "quando disponível".
- **D-17:** **Ação admin reutiliza retry com semântica de reconciliação.** Manter ação de retry, com texto/estado deixando claro que será feita reconciliação segura (checar status/IDs antes de publicar). Aproveita endpoint/padrão atual.
- **D-18:** **Auditoria por eventos principais da tentativa.** Registrar resultado final da tentativa e resumos seguros dos passos principais (criação container, status check, publish, busca permalink), sem payloads sensíveis/tokens/segredos (PUBL-03).
- **D-19:** **Bloqueio ambíguo permanece até reconciliação.** Casos ambíguos bloqueados permanecem seguros indefinidamente até verificação/reconciliação; sem expiração automática para retry.
- **D-20:** **Reconciliação conclusiva atualiza local como publicado.** Se reconciliação detectar que container/mídia IG já foi publicado com sucesso, registrar IDs/permalink/timestamps, marcar `published`, limpar erro ambíguo e anexar log de reconciliação.

### OpenCode's Discretion
- **Rate limit e limite diário (PUBL-05, não discutido):** usuário não selecionou esta área. OpenCode tem discrição na implementação, mas DEVE satisfazer PUBL-05: tratar `content_publishing_limit` como autoridade de runtime quando aplicável, classificar 2207042/rate limit com segurança, sem retry storm, e expor estado acionável ao admin. Preferir padrão conservador alinhado a `PublishFailureCategory` e backoff existente.
- **Status e auditoria no admin (PUBL-03, superfície UI não discutida):** usuário não selecionou esta área. OpenCode tem discrição no formato exato da UI/API admin, mas DEVE satisfazer PUBL-03: status por plataforma, erro seguro acionável, IDs/permalink quando disponíveis, tentativas/timestamps e histórico/auditoria sem exposição de tokens/segredos. Reaproveitar padrões de `ReviewQueue`/status social existentes.
- Nomes exatos de colunas/campos novos em `social_posts`, schemas e migrations, desde que atendam PUBL-03/PUBL-04 e sejam claros.
- Orçamento numérico exato de timeout/polling/backoff e limites de tentativas por chamada, desde que seguros e configuráveis quando apropriado.
- Shape exato do breakdown por provider no worker response, preservando compatibilidade com consumidores atuais.
- Wording pt-BR exato de erros/ações de reconciliação, desde que claro, seguro e acionável.
- Estratégia interna de reconciliar "já publicado" (campos Graph consultados, ordem de checks), desde que não crie duplicação.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` §"Phase 31: Independent Publish Pipeline" — Goal, depends_on Phase 30, requisitos PUBL-01..05, critérios de sucesso e notas de pesquisa.
- `.planning/REQUIREMENTS.md` §"Publicação Assíncrona / Pipeline" — Contrato normativo PUBL-01..05; traceability para Phase 31.
- `.planning/PROJECT.md` — Core value, restrições v1.5, independência IG/Facebook, sem novas abstrações desnecessárias, decisões em aberto/carry-over.
- `.planning/STATE.md` — Posição atual, foco em Phase 30/31, blockers/concerns v1.5 (Meta verification, decisões abertas, residuals aceitos).

### Decisões upstream (obrigatório)
- `.planning/phases/29-meta-ig-readiness-media-foundation/29-CONTEXT.md` — Contratos de prontidão IG, `ig-user-id`, mídia pública HTTPS versionada/hash, bloqueio só IG, alerta+reconexão.
- `.planning/phases/30-instagram-review-experience/30-CONTEXT.md` — Draft/status IG por provider, `publish_enabled`, template C, validação 2200/hashtags/link-na-bio, preview exato, independência FB/IG na revisão.

### Pesquisa e guardrails v1.5
- `.planning/research/SUMMARY.md` — Síntese v1.5, riscos e recomendações de pipeline/Graph.
- `.planning/research/ARCHITECTURE.md` — Padrões de integração e componentes IG/publish.
- `.planning/research/PITFALLS.md` — Armadilhas: ambiguidade/duplicação, rate limit, token/scopes, mídia/URL pública.
- `.planning/research/STACK.md` — Restrições de stack/bibliotecas para IG/media.
- `.planning/research/FEATURES.md` — Expectativas de comportamento e diferenciação.

### Código social/publicação existente (pontos de extensão)
- `backend/app/services/social/publish_pipeline.py` — Pipeline atual FB-only: claim, processamento, classificação transient/permanent/ambiguous/unknown, backoff, logs sanitizados, idempotência por `external_post_id`.
- `backend/app/services/social/publisher.py` — Protocolo `SocialPublisher` e contrato de publish.
- `backend/app/services/social/facebook.py` — Implementação FB atual e mapeamento seguro de erros Graph.
- `backend/app/services/social/types.py` — `PublishResult`, `PublishFailureCategory`, `SocialPostPayload`.
- `backend/app/models/social_post.py` — Modelo por `(job_id, provider)`, status, `publish_enabled`, attempts/retry/error/external_post_id/timestamps.
- `backend/app/models/social_post_log.py` — Log de tentativas por `social_post_id`.
- `backend/app/crud/social_posts.py` — Claim/list/due/status/retry-state helpers por provider.
- `backend/app/schemas/social_posts.py` — Contratos de draft/status/retry/worker (já incluem provider instagram).
- `backend/app/api/v1/admin.py` — Endpoints admin de social status/retry/worker e fluxos de aprovação/dispatch.
- `backend/app/core/config.py` — `META_GRAPH_VERSION`, `SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS`, segredos/chaves sociais.
- `backend/app/core/scheduler.py` — Padrão de scheduler in-process/isolamento operacional (referência; não acoplar expiry ao publish sem necessidade).

### Mídia/prontidão IG (dependências de implementação)
- `backend/app/services/social/image_media.py` — Validação/preparo de mídia IG; revalidação antes de publish deve respeitar IMAG-01 (bloqueio só IG).
- `backend/app/services/social/meta_oauth.py` — Fluxo/token Meta, status seguro, padrões de erro/reconexão.
- `backend/app/models/social_account.py` — Estado de conexão IG/prontidão/token criptografado.
- `backend/app/api/v1/integrations.py` — Superfície de integração/status/reconexão.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/social/publish_pipeline.py`: claim atômico, transição para `publishing`, classificação de falhas, backoff configurável, idempotência por `external_post_id`, tratamento ambíguo sem auto-retry, logs sanitizados. Melhor base para generalização provider-aware.
- `backend/app/services/social/publisher.py` + `types.py`: contrato `SocialPublisher.publish` e `PublishResult/PublishFailureCategory` já permitem handler/publisher por provider.
- `backend/app/crud/social_posts.py`: helpers de claim/status/retry-state e `list_due_for_claim` com provider/lock; ponto natural para filtro `publish_enabled` e semântica de reconciliação.
- `backend/app/models/social_post.py` / `social_post_log.py`: persistência já existente por provider e auditoria por tentativa; extensão por colunas explícitas alinha com D-10.
- `backend/app/api/v1/admin.py`: worker/retry/status endpoints e dispatch por `post_id`; já integra com `process_social_post_safe`.
- `backend/app/services/social/image_media.py` e prontidão IG (Phase 29): contratos para revalidar imagem/prontidão antes de publish, sem bloquear Facebook/site.

### Established Patterns
- **Isolamento por provider/post:** `SocialPost` é único por `(job_id, provider)`; IG e FB devem evoluir independentemente (PUBL-01).
- **Segurança operacional:** mensagens seguras pt-BR, sem tokens/segredos em logs/respostas; classificação de falhas conservadora.
- **Idempotência e ambiguidade:** tentativas ambíguas não viram retry cego; `external_post_id` impede republicação quando confirmado.
- **Config-driven:** versão Graph e parâmetros de retry vêm de env/config (`META_GRAPH_VERSION`, `SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS`).
- **Site-first / social best-effort:** falhas sociais não devem corromper publicação no site nem fluxo Facebook.

### Integration Points
- `backend/app/services/social/publish_pipeline.py`: generalizar para FB+IG, handlers por provider, reconciliação ambígua IG, rate-limit classification segura, breakdown por provider.
- Novo publisher IG (em `backend/app/services/social/`, nome em discrição): fluxo Graph 2 passos (container, status check, publish), permalink best-effort, mapeamento seguro de erros/timeouts.
- `backend/app/crud/social_posts.py` + `schemas/social_posts.py` + `models/social_post.py` + migration Alembic: campos explícitos IG/reconciliação, elegibilidade `publish_enabled`, semântica de retry/reconcile.
- `backend/app/api/v1/admin.py` e `frontend/lib/api.ts`/UI admin status: expor status/auditoria por plataforma (PUBL-03) e ação retry com semântica de reconciliação (D-17), sem quebrar Facebook.
- `backend/app/core/config.py` / `.env.example` (se necessário): quaisquer knobs seguros de polling/timeout/rate limit; manter Graph version configurável.

</code_context>

<specifics>
## Specific Ideas

- "Publicações no Facebook e IG devem ser independentes" — reforçado pelo usuário no contexto de Phase 30 e travado por PUBL-01.
- Usuário priorizou segurança contra duplicação: ambiguidade/timeout não deve gerar auto-retry cego; reconciliação deve aproveitar IDs conhecidos e atualizar local quando já publicado.
- Para casos ambíguos, reusar ação de retry com semântica clara de reconciliação (não criar superfície operacional desnecessária).

</specifics>

<deferred>
## Deferred Ideas

- **Rate limit e limite diário (PUBL-05) — área não discutida nesta sessão.** Requisitos permanecem obrigatórios; implementação fica em discrição do OpenCode/planner, desde que cumpra PUBL-05.
- **Status e auditoria no admin (PUBL-03) — superfície UI detalhada não discutida.** Requisitos permanecem obrigatórios; planner deve definir mínima UI/API útil e segura.
- Qualquer evolução para agendamento avançado, múltiplas contas IG, Stories/Reels/carrossel, métricas/analytics ou inbox de comentários/DMs — fora do escopo v1.5.

</deferred>

---

*Phase: 31-independent-publish-pipeline*
*Context gathered: 2026-11-25*
