# Phase 16: Geração, Revisão e Aprovação do Post Social - Context

**Gathered:** 2026-11-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Na revisão, o admin recebe um rascunho de post social (IA ou fallback por template), pode ajustar/agendar e aprovar a vaga. Ao aprovar, a vaga é publicada no site imediatamente e o `social_post` aprovado é registrado com modo/horário corretos — **falhas sociais nunca bloqueiam a publicação no site**. O post segue política configurada (por padrão sem contato direto e sem nome da empresa, apenas link público via `SITE_PUBLIC_URL` + URL da vaga). Esta fase define geração/edição/aprovação/registro; publicação real no Facebook, worker/cron, retries/idempotência operacional e UI de status/retry por vaga ficam para a Fase 17.

</domain>

<decisions>
## Implementation Decisions

### Ciclo do rascunho social
- **D-01:** O rascunho do post é gerado **sob demanda no editor** (ação explícita do revisor, ex.: "Gerar post/rascunho"), evitando chamadas ao LLM na listagem da fila de revisão.
- **D-02:** Persistência por **upsert** de um único `social_post` por vaga/provider (`job_id`, `provider='facebook'`, respeitando a unicidade existente): gerar/salvar edição/regenerar atualiza o mesmo registro mantendo `status='draft'` enquanto rascunho. "Regenerar com IA" **sobrescreve** o texto do draft atual.
- **D-03:** Geração em serviço dedicado de post social que **reaproveita a integração/configuração Groq existente** (`backend/app/services/extraction/client.py` como referência de cliente/config) com prompt específico pt-BR (tom profissional e acolhedor, emojis moderados, 3–5 hashtags, CTA com link, alvo ~700 caracteres). Se o LLM falhar ou estiver indisponível, usar **fallback por template local determinístico** a partir dos dados da vaga — a revisão nunca é bloqueada e sempre há draft utilizável.
- **D-04:** Gerar/regenerar sempre a partir do **estado atual salvo** da vaga (`Job` persistido), incluindo edições já salvas pelo revisor; não usar snapshot congelado antigo nem valores não persistidos do formulário.

### Editor e agendamento na revisão
- **D-05:** Integrar a experiência de post social como **seção dentro de `frontend/app/admin/review/EditJobDialog.tsx`** (no fluxo atual com `ReviewQueue.tsx`), mantendo contexto da vaga e do texto-fonte no mesmo lugar.
- **D-06:** Controles essenciais da seção: textarea editável do texto, **contador de caracteres (alvo ~700)**, botão **"Gerar/Regenerar com IA"** com estado de carregamento, **preview simples** do post (texto/link) e indicadores de origem/estado (gerado por IA, fallback/template, erro ao gerar com fallback aplicado).
- **D-07:** Agendamento com **toggle "Publicar agora" (padrão) vs "Agendar"**; ao agendar, selecionar data/hora interpretada em **`America/Sao_Paulo`** (fuso indicado na UI) e persistir o valor de forma inequívoca para o backend (ex.: convertido/armazenado conforme convenção de tempo do domínio).
- **D-08:** **Salvar explicitamente** o conteúdo do draft e a escolha de modo/horário no `social_post` draft (ação de salvar/ao gerar/regenerar conforme fluxo definido). A aprovação deve usar o **último estado salvo** do draft para registrar o post aprovado, evitando divergência entre o que o revisor vê e o que é registrado.

### Aprovação da vaga e registro do post social (seguro)
- **D-09:** **Publicar a vaga no site primeiro** e tratar o registro do `social_post` aprovado como etapa **separada/best-effort**: falhas sociais (criar/atualizar/registrar `social_post`) **nunca** desfazem nem bloqueiam a publicação da vaga. Em falha social, a vaga permanece publicada e a operação deve sinalizar aviso/estado de erro social à UI.
- **D-10:** Ao aprovar, registrar o `social_post` aprovado com **`status='scheduled'`** e `scheduled_at` apropriado: **"Publicar agora" ⇒ `scheduled_at = agora`** (elegível imediato para processamento assíncrono na Fase 17); **"Agendar" ⇒ `scheduled_at` = horário futuro escolhido** (origem `America/Sao_Paulo`). O texto/modo/horário aprovados ficam registrados no `social_post`.
- **D-11:** Se **não houver draft social salvo** no momento da aprovação, **publicar a vaga no site normalmente** e **pular/avisar** sobre o registro social (sem bloquear). Se a etapa best-effort de registro social falhar, mesma regra: vaga publicada + aviso/erro social.
- **D-12:** **Congelar o texto ao aprovar/registrar** o post como `scheduled`: o conteúdo aprovado passa a ser tratado como final para envio (edição do texto desabilitada para esse registro aprovado), garantindo consistência com o que será processado/enviado na Fase 17 (em alinhamento com POST-05: texto aprovado imutável após envio e salvo).

### Conteúdo, URL pública e política do post
- **D-13:** Construir o link público da vaga como **`{SITE_PUBLIC_URL}/?vaga=<job_id>`**, reutilizando o deep-link já suportado pelo board público (`frontend/app/(public)/page.tsx` lê `vaga` UUID e abre o detalhe).
- **D-14:** Template/fallback e guia de prompt **objetivos** em pt-BR: incluir cargo/título, cidade, salário e destaques breves de atividades/benefícios quando couber; **CTA com link**; **3–5 hashtags** relevantes; **emojis moderados**; alvo **~700 caracteres**.
- **D-15 (correção explícita do usuário):** O post social **NÃO deve conter nome da empresa** e **NÃO deve conter qualquer contato** (telefone, e-mail ou similares). Deve conter apenas informações permitidas da vaga e o **link para o site**. Ajustar template/prompt/preview para omitir empresa e contatos.
- **D-16:** Tornar a política de contato **configurável via flag de ambiente no backend** (em `Settings`, documentada em `.env.example`), com **padrão desativado** (sem contato). Aplicar de forma central na geração/montagem do post.
- **D-17:** Aplicar a política de forma **central e robusta** na geração, no template/fallback e no preview: omitir empresa e contatos conforme regras (e nunca vazar contato quando desabilitado), sempre incluir link público quando aplicável. Se `SITE_PUBLIC_URL` estiver ausente/inválida para montar o link, tratar com **validação/erro acionável e claro** no fluxo de geração do draft (sem inventar link) sem bloquear a revisão/publicação da vaga no site.

### OpenCode's Discretion
- Nomes exatos de endpoints/rotas, schemas, funções e organização de módulos/arquivos (ex.: serviço de geração social em `backend/app/services/social/`, endpoints admin para draft/save/approve) desde que sigam convenções do backend/frontend e as decisões acima.
- Formato exato de persistência/conversão de fuso para `scheduled_at` (ex.: armazenar UTC derivado de `America/Sao_Paulo`) e representação de "publicar agora".
- Redação/copy exata do template/prompt, seleção de hashtags, truncamento/ajuste para ~700 caracteres e detalhes visuais da seção no `EditJobDialog`, respeitando D-14/D-15/D-17.
- Nome, formato e documentação da(s) env var(s) de configurabilidade da política (D-16) e mensagens de erro/aviso na UI e API.
- Estratégia de retorno da API de aprovação para comunicar sucesso da vaga + sucesso/aviso/falha do registro social (best-effort), sem expor segredos.
- Como desabilitar/bloquear edição de texto quando o post estiver aprovado/`scheduled` (D-12) na UI e/ou validações de backend.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo, requisitos e contexto do milestone
- `.planning/ROADMAP.md` §"Phase 16: Geração, Revisão e Aprovação do Post Social" — goal, depends_on (14,15), requisitos `POST-01..POST-06`, critérios de sucesso e limites (UI hint yes).
- `.planning/REQUIREMENTS.md` — definições de `POST-01` a `POST-06` e rastreabilidade (texto/LLM+fallback, edição/regenerar/preview/contador, agendar em `America/Sao_Paulo`, imutável após envio, política de link/sem contato, draft salvo).
- `.planning/PROJECT.md` — core value (falha social nunca bloqueia o site), decisões do milestone v1.2 (1 página/1 admin, texto por LLM editável, fire-and-forget, segredos só no backend), stack/locale e restrições.
- `.planning/STATE.md` — posição atual (fase 16), decisões acumuladas e pendências herdadas.

### Decisões e base das fases anteriores (obrigatório respeitar)
- `.planning/phases/14-fundacao-social-dados-e-configuracao/14-CONTEXT.md` — modelo `social_posts`/status/enums/índices/uniqueness, `SocialPublisher`/stub, crypto/config/env sociais e padrões de domínio.
- `.planning/phases/15-oauth-meta-e-integracoes-no-admin/15-CONTEXT.md` — 1 página/1 admin, estados de conexão (`connected/needs_reconnect/disconnected`), UI de Integrações e princípios de segurança (sem segredos no cliente).

### Backend — revisão, aprovação, dados sociais e LLM/config
- `backend/app/api/v1/admin.py` — endpoints admin atuais (listar/obter/aprovar/editar/deletar jobs), proteção `require_admin`, fluxo de aprovação `PATCH /admin/jobs/{job_id}/approve`.
- `backend/app/crud/jobs.py` — `approve_job` (publica e renova expiração 14 dias), `update_job`, `list_by_status`/consultas de revisão; ponto de integração para evolução do fluxo de aprovação/registro social.
- `backend/app/models/job.py` — modelo/campos da vaga usados como fonte do texto do post.
- `backend/app/models/social_post.py` — `SocialPost`, `SocialPostStatus` (`draft/scheduled/publishing/published/failed/cancelled`), campos `text/scheduled_at/attempts/next_retry_at/last_error/external_post_id/published_at` e unicidade `(job_id, provider)`.
- `backend/app/models/social_post_log.py`, `backend/app/models/social_account.py` — modelos/logs/conta social existentes (contexto de domínio).
- `backend/app/services/social/` — `publisher.py`, `types.py`, `facebook.py` (stub), `crypto.py`, `meta_oauth.py`, `__init__.py` (contratos e organização do domínio social).
- `backend/app/services/extraction/client.py`, `backend/app/services/extraction/extractor.py` — integração Groq/LLM e padrões de chamada/reuso a considerar para geração de texto do post.
- `backend/app/core/config.py` — `Settings` (inclui `SITE_PUBLIC_URL`, `META_*`, `SOCIAL_*`, `GROQ_*`) e validações; local para flag configurável da política de post.
- `backend/.env.example` — documentação de variáveis de ambiente; manter alinhada a novas configs desta fase.
- `backend/app/schemas/` (e schemas sociais/job/admin existentes) — convenções de payloads/respostas.
- `backend/alembic/` e `backend/alembic/versions/` — histórico de migrações (avaliar se fase 16 exige alterações de schema; não assumir sem necessidade).

### Frontend admin e link público
- `frontend/app/admin/review/ReviewQueue.tsx` — fila de revisão, ações otimistas de aprovar/editar/excluir e consumo de `approveJob`.
- `frontend/app/admin/review/EditJobDialog.tsx` — modal de edição de vaga (campos, validação, snippet de origem); ponto de integração da seção de post social (D-05).
- `frontend/app/admin/review/page.tsx` — entrada da revisão.
- `frontend/app/admin/integracoes/IntegrationsClient.tsx`, `frontend/app/admin/integracoes/page.tsx` — padrões da UI admin de integrações sociais (estados/feedback) a manter coerentes.
- `frontend/lib/api.ts`, `frontend/lib/*` — chamadas/admin helpers e tipos usados pelo review.
- `frontend/app/(public)/page.tsx`, `frontend/components/board/JobGrid.tsx`, `frontend/components/board/JobDetailDialog.tsx` — comportamento atual de deep-link público `?vaga=<job_id>` (base para URL do post, D-13).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/extraction/client.py` (+ `extractor.py`): infraestrutura/configuração de chamadas Groq existente — base para reutilizar credenciais/modelo/padrões no serviço de geração de post, com prompt/saída próprios do domínio social.
- `backend/app/models/social_post.py` (`SocialPostStatus`, campos de agendamento/publicação, unicidade `(job_id, provider)`): persistência pronta para draft/aprovado (`scheduled`) e evolução futura do worker.
- `backend/app/services/social/` (`SocialPublisher`, `types.py`, stub `FacebookPublisher`): contratos e organização do domínio social a estender sem acoplar provider.
- `backend/app/core/config.py` e `backend/.env.example`: superfície central para `SITE_PUBLIC_URL` e novas flags documentadas (política de conteúdo), com validações.
- `frontend/app/admin/review/EditJobDialog.tsx` + `ReviewQueue.tsx`: shell de edição/revisão, toasts, estados de loading/erro e padrões de interação (aprovar/editar/salvar) para embutir a seção de post.
- Deep-link público `?vaga=<job_id>` em `frontend/app/(public)/page.tsx`: forma já suportada de apontar para uma vaga específica.

### Established Patterns
- Backend FastAPI + SQLAlchemy 2 async; serviços encapsulados em `backend/app/services/` por domínio; segredos/config apenas no backend.
- Aprovação atual de vaga é endpoint admin dedicado (`approve_job` publica e renova expiração); qualquer extensão deve preservar "vaga publicada no site" mesmo com falhas sociais (best-effort separado).
- Frontend admin em Next.js App Router sob `frontend/app/admin/` com componentes client-side para ações e feedback.
- Horários de agendamento definidos pelo requisito em `America/Sao_Paulo` (UI) com persistência consistente no backend.

### Integration Points
- `backend/app/api/v1/admin.py` (+ schemas/router): novos endpoints/ajustes para gerar/salvar draft e registrar post aprovado no fluxo de aprovação, retornando estado/avisos sociais sem bloquear sucesso da vaga.
- `backend/app/crud/` ou camada de serviço social: upsert/consulta de `social_post` draft por `(job_id, provider)`, transição para `scheduled` com `scheduled_at`/texto aprovados e tratamento best-effort.
- `backend/app/services/social/` (novo módulo de geração de conteúdo): montagem de prompt/template, aplicação da política (sem empresa, sem contato por padrão, link obrigatório/validado), uso de Groq com fallback.
- `frontend/lib/api.ts` + `EditJobDialog.tsx`/`ReviewQueue.tsx`: chamadas para gerar/salvar draft e refletir resultado da aprovação (vaga publicada + status/aviso do social).
- `backend/.env.example` e `backend/app/core/config.py`: flag de política de conteúdo documentada e lida centralmente.

</code_context>

<specifics>
## Specific Ideas

- Correção do usuário (obrigatória): o post em rede social **não deve conter nome da empresa nem qualquer tipo de contato (telefone/e-mail)**; em vez disso deve haver **link para redirecionar para o site**. Isso se sobrepõe a qualquer sugestão de incluir empresa no texto.
- Padrão de link acordado: `SITE_PUBLIC_URL/?vaga=<job_id>` (deep-link já suportado pelo frontend).
- Agendamento padrão imediato, com opção de agendar em `America/Sao_Paulo`; preview simples e contador ~700 no editor.

</specifics>

<deferred>
## Deferred Ideas

- Publicação real no Facebook, worker/cron com `FOR UPDATE SKIP LOCKED`, retries/backoff, classificação de erros, idempotência operacional e "tentar novamente" (Fase 17).
- Badges/status social por vaga, erro resumido e link do post publicado na listagem/detalhe admin (UI-01/UI-02, Fase 17).
- Testes automatizados/manuais e documentação operacional/App Review (Fase 18), e carry-over de gaps v1.1.

[Áreas não aprofundadas nesta discussão, a tratar no planejamento/pesquisa dentro do escopo da Fase 16: contrato exato dos endpoints de draft/save/approve e payloads de resposta/avisos, UX detalhada de estados de erro/loading quando `SITE_PUBLIC_URL` ausente, e nome/formato exato da env var de política de conteúdo (mantendo padrão sem contato).]

</deferred>

---

*Phase: 16-geracao-revisao-e-aprovacao-do-post-social*
*Context gathered: 2026-11-15*
