# Phase 32: Hardening, Regression & Operations - Context

**Gathered:** 2026-11-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Tornar a integração Instagram verificável, observável e segura de operar sem regressão no fluxo Facebook (HARD-01, HARD-02). Esta fase entrega: (1) suíte automatizada cobrindo cenários críticos de Instagram (draft/validação, idempotência, retry, ambiguidade, rate limit, mapeamento de erro) e caracterização/regressão do fluxo Facebook como gate de release; (2) documentação operacional completa para env vars, checklist manual Meta, expiração/reconexão de token e troubleshooting de estados de publicação Instagram; (3) evidências de validação que separam claramente cobertura automatizada de handoff/manual Meta, sem fabricar execução manual. Não adiciona novas capacidades de produto (Stories/Reels/carrossel, agendamento, métricas, múltiplas contas, inbox).

</domain>

<decisions>
## Implementation Decisions

### Regressão Facebook (gate de não-regressão)
- **D-01:** Artefato principal = **estender testes atuais** (`backend/tests/test_facebook_publisher.py`, `backend/tests/test_social_publish_pipeline.py` e outros testes FB/sociais relevantes) com casos explícitos de regressão/contrato FB, reaproveitando padrões existentes. Não criar suíte paralela de snapshot desconectada sem necessidade.
- **D-02:** Escopo do gate = **ciclo completo FB**. Cobrir draft/geração, aprovação/site-first, publish assíncrono, status/logs seguros, retry/idempotência e reconexão/erro seguro — tudo que a integração IG não pode quebrar.
- **D-03:** Rigidez das asserções = **contrato comportamental**. Assertar comportamentos, estados, campos críticos e mensagens seguras; evitar snapshots frágeis de texto/payload inteiro quando não essenciais. Mudanças intencionais devem exigir atualização consciente do teste.
- **D-04:** Sinalização do gate = **pytest normal + evidência**. A regressão FB roda na suíte pytest normal; `32-VERIFICATION.md`/evidência HARD-02 deve identificar claramente quais testes/arquivos formam o gate FB e seu resultado.

### Cobertura HARD-01 (suíte automatizada)
- **D-05:** Camada prioritária = **backend-first, gaps reais**. Focar em pytest backend (draft/validação, publisher/pipeline, idempotência, retry, ambiguidade, rate limit, mapeamento de erros). Incluir frontend (Vitest/RTL) apenas se houver gap crítico e infra/harness já existente; não criar infraestrutura frontend de testes do zero nesta fase sem necessidade clara.
- **D-06:** Interpretação de "draft/validação Instagram" = **backend/schemas/serviços**. Cobrir geração/normalização de draft IG, validações (limite 2200, hashtags/mídia/regras aplicáveis), contratos de API/schemas e erros seguros. Alinha com testes pytest existentes. Comportamento UI admin (contador/aviso/bloqueio/preview) não é alvo primário de HARD-01 salvo gap crítico já testável.
- **D-07:** Critério de suficiência = **cenários HARD-01 rastreados**. Cada cenário nomeado em HARD-01 deve ser mapeado para teste(s) automatizado(s) claro(s), arquivo/comando e resultado; gaps devem ser explícitos e justificados. Sem meta de percentual de cobertura arbitrária.
- **D-08:** Prioridade em trade-offs = **risco operacional IG/FB**. Priorizar ambiguidade/duplicação, rate limit, reconciliação, idempotência, erros seguros e não-regressão FB antes de casos felizes redundantes.

### Docs operacionais (HARD-02)
- **D-09:** Forma do artefato = **expandir doc existente**. Evoluir `docs/META-INTEGRATION-TESTING.md` como fonte única operacional (Meta/FB + IG readiness + IG publish pipeline + troubleshooting), evitando duplicação. Manter referências cruzadas necessárias.
- **D-10:** Troubleshooting de estados IG = **tabela acionável**. Para cada estado/sintoma: significado, causa provável, ação do admin, se pode retry/reconciliar, pré-condições, e quando escalar. Cobrir estados Phase 31 (ex.: `published`, `failed`, ambíguo/reconciliação requerida, `ig_rate_limit_blocked`/`content_publishing_limit`, `needs_reconnect`, `publish_enabled=false`, permalink ausente, container/publish inconclusivo).
- **D-11:** Env vars e token = **canônica + segurança**. Incluir tabela alinhada a `backend/.env.example` com finalidade, obrigatório/opcional, formato, riscos e comportamento quando ausente/inválido; seção clara de expiração/reconexão (`needs_reconnect`), rotação segura e nunca expor segredos em logs/docs/evidências.
- **D-12:** Checklist manual Meta = **handoff explícito**. Checklist marcado como handoff (não executar sem credenciais/autorização), com pré-condições, passos, critérios de evidência e campos para registrar resultado sanitizado. Não fabricar execução.

### Evidência/handoff de validação
- **D-13:** Local/formato principal = **`32-VERIFICATION.md` + matriz**. Concentrar evidência em `32-VERIFICATION.md` com matriz cenário→evidência (automatizada/handoff), comandos/resultados e status claro. Docs operacionais podem ser referenciados, mas não devem duplicar status de fase.
- **D-14:** Itens manuais Meta = **handoff explícito bloqueado**. Marcar como `handoff/manual`, com pré-condições, ambiente/responsável necessário e "não executado/não evidenciado nesta sessão" quando aplicável. Nunca marcar aprovado sem execução real.
- **D-15:** Granularidade HARD-01 = **por cenário HARD-01**. Mapear cada cenário nomeado (draft/validação IG, idempotência, retry, ambiguidade, rate limit, mapeamento de erros, caracterização/regressão FB) para testes/arquivos/comandos e evidência.
- **D-16:** Gate FB na evidência = **bloco explícito no VERIFICATION**. Incluir seção dedicada "Facebook Regression Gate" com fluxos cobertos, testes/arquivos, resultado e conclusão de não-regressão observada.

### OpenCode's Discretion
- Nomes exatos de arquivos de teste novos/extensões, desde que sigam convenções pytest existentes e facilitem rastreabilidade HARD-01.
- Estratégia de fixtures/mocks para cenários Graph IG/FB (timeouts, 2207042/content_publishing_limit, ambiguidade, reconciliação), desde que não exponham segredos e cubram os cenários exigidos.
- Se algum gap HARD-01 exige pequeno ajuste de contrato interno para testabilidade, permitido apenas se não alterar comportamento de produto e sem regressão FB/site.
- Estrutura editorial final do `docs/META-INTEGRATION-TESTING.md` (seções/tabelas/âncoras), desde que preserve conteúdo útil existente e cumpra D-09..D-12.
- Forma exata da matriz em `32-VERIFICATION.md` (colunas/ordem), desde que cumpra D-13..D-16 e deixe claro automatizado vs handoff.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` §"Phase 32: Hardening, Regression & Operations" — Goal, depends_on Phase 31, requisitos HARD-01/HARD-02, critérios de sucesso, plano TBD e nota de handoff manual Meta.
- `.planning/REQUIREMENTS.md` §"Qualidade / Hardening" — Contrato normativo HARD-01/HARD-02 e traceability Phase 32.
- `.planning/PROJECT.md` — Core value, restrições v1.5, decisões v1.2/v1.3/v1.4 relevantes (site-first, best-effort, não fabricar evidência), out of scope.
- `.planning/STATE.md` — Posição atual (Phase 32 ready), blockers/concerns carry-over, residuals aceitos que não viram escopo automático.

### Decisões upstream (contratos que HARD-01/HARD-02 devem proteger)
- `.planning/phases/29-meta-ig-readiness-media-foundation/29-CONTEXT.md` — Prontidão IG, `ig-user-id`, mídia pública HTTPS versionada, bloqueio só IG, alerta+reconexão (D-01..D-16).
- `.planning/phases/30-instagram-review-experience/30-CONTEXT.md` — Draft/status IG por provider, toggle/preview/validação na revisão, independência FB/IG (D-01..D-09).
- `.planning/phases/31-independent-publish-pipeline/31-CONTEXT.md` — Pipeline IG 2 passos, ambiguidade/reconciliação, rate limit/runtime authority, auditoria segura, independência por provider (D-01..D-20).
- `.planning/phases/31-independent-publish-pipeline/31-VERIFICATION.md` — Evidência de conclusão PUBL-01..05, gaps inexistentes, ressalva de bookkeeping em REQUIREMENTS.md.

### Documentação/operação existente
- `docs/META-INTEGRATION-TESTING.md` — Doc operacional atual (Meta/FB, cron, App Review, prontidão IG, checklist handoff). Base obrigatória para HARD-02 (expandir, não duplicar sem motivo).
- `backend/.env.example` — Fonte canônica de env vars; HARD-02 deve alinhar documentação e cobrir segurança/comportamento esperado.

### Código e testes relevantes (pontos de caracterização/regressão)
- `backend/app/services/social/publish_pipeline.py` — Núcleo provider-aware claim/process/retry/reconciliação/rate limit/logs seguros.
- `backend/app/services/social/instagram.py` — Publisher IG Graph 2 passos, polling, classificação segura de erros/rate limit/ambiguidade.
- `backend/app/services/social/facebook.py` — Publisher FB; base do gate de não-regressão.
- `backend/app/services/social/post_generation.py` — Geração/normalização de draft social; relevante para "draft/validação IG".
- `backend/app/services/social/image_media.py` — Validação/preparo de mídia IG.
- `backend/app/crud/social_posts.py` — Claim elegível, retry-state, reconciliação, status/logs seguros.
- `backend/app/api/v1/admin.py` — Endpoints admin de worker/retry/status/logs/approve dispatch; contratos operacionais.
- `backend/app/schemas/social_posts.py` — Contratos de status/retry/worker/logs seguros.
- `backend/app/core/config.py` — Env/config de Meta/social/IG/media.
- `backend/tests/test_facebook_publisher.py` — Caracterização FB existente (estender para gate).
- `backend/tests/test_social_publish_pipeline.py` — Pipeline FB/IG, ambiguidade, reconciliação, rate limit, isolamento por provider.
- `backend/tests/test_instagram_publisher.py` — Contrato IG publisher.
- `backend/tests/test_integrations_instagram.py` — Integração/admin/estado IG.
- `backend/tests/test_ig_media_validation.py` — Validação de mídia IG.
- `backend/tests/test_social_post_generation.py` — Geração de draft social.
- `backend/tests/test_meta_oauth_instagram.py` — OAuth/readiness IG.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/tests/test_facebook_publisher.py`, `backend/tests/test_social_publish_pipeline.py`: base natural para gate de regressão FB (D-01/D-02), já alinhados a padrões pytest/fixtures do repo.
- `backend/tests/test_instagram_publisher.py`, `backend/tests/test_social_publish_pipeline.py`: já cobrem parte de PUBL-02/04/05; HARD-01 deve preencher gaps rastreados, não duplicar cegamente.
- `backend/tests/test_integrations_instagram.py`, `backend/tests/test_meta_oauth_instagram.py`, `backend/tests/test_ig_media_validation.py`, `backend/tests/test_social_post_generation.py`: ativos para draft/validação/readiness e cenários HARD-01 backend.
- `docs/META-INTEGRATION-TESTING.md`: já contém setup Meta/FB, cron/worker, App Review, prontidão IG, env vars e checklist handoff; HARD-02 deve evoluir este doc.
- `backend/.env.example`: lista canônica de env vars; referência direta para tabela HARD-02.

### Established Patterns
- **Site-first / social best-effort / independência FB↔IG:** falhas sociais não bloqueiam site; falha de uma plataforma não corrompe a outra. Gate FB deve proteger isso.
- **Erros seguros pt-BR, sem segredos:** logs/respostas não expõem tokens/segredos/payloads brutos; evidência e docs devem seguir o mesmo padrão.
- **Handoff manual explícito:** roadmap/Phase 29 estabeleceram que verificação Meta real/App Review é handoff, não evidência fabricada.
- **Pytest backend como suíte principal:** HARD-01 backend-first alinha com padrão existente; frontend não possui harness evidente para estes fluxos.
- **Provider-aware social posts:** modelo por `(job_id, provider)`, status/auditoria por plataforma, reconciliação e bloqueios acionáveis.

### Integration Points
- `backend/tests/*social*`, `backend/tests/*instagram*`, `backend/tests/*facebook*`: extensão de cobertura HARD-01 e gate FB.
- `docs/META-INTEGRATION-TESTING.md`: expansão HARD-02 (troubleshooting estados IG Phase 31, env vars canônicas, token/reconexão, checklist handoff).
- `.planning/phases/32-hardening-regression-operations/32-VERIFICATION.md` (a ser criado na execução/verificação da fase): matriz de evidência automatizada vs handoff e bloco explícito de gate FB.
- `backend/.env.example` e `backend/app/core/config.py`: alinhamento de env vars documentadas/testadas quando houver gap de cobertura.

</code_context>

<specifics>
## Specific Ideas

- "Caracterização/regressão do fluxo Facebook" deve ser tratada como gate real de release, não apenas uma nota informal: ciclo completo FB, contrato comportamental, rodando no pytest normal e destacado na evidência.
- HARD-01 prioriza risco operacional (ambiguidade/duplicação, rate limit, reconciliação, idempotência, mapeamento de erro) antes de casos felizes redundantes.
- HARD-02 deve reaproveitar `docs/META-INTEGRATION-TESTING.md` e adicionar troubleshooting acionável dos estados IG introduzidos na Phase 31, sem transformar o doc em dump de logs/código.
- Evidência deve ser auditável: o que foi automatizado, o que é handoff manual Meta, e o que não foi executado — sem ambiguidade.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 32-hardening-regression-operations*
*Context gathered: 2026-11-26*
