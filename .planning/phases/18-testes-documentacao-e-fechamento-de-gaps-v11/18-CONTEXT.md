# Phase 18: Testes, Documentação e Fechamento de Gaps v1.1 - Context

**Gathered:** 2026-11-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Entregar cobertura automatizada/manual e documentação operacional para a integração social (Facebook) e fechar/registrar, com evidência rastreável, os gaps aceitos do audit v1.1.

**Em escopo (Fase 18):** testes unitários/de integração/mock e de concorrência/idempotência para fluxos sociais críticos (geração/classificação/backoff, OAuth/publicação com Graph API mockada, worker `SKIP LOCKED`/idempotência) sem chamadas reais em CI (TEST-01..TEST-03); roteiro de teste manual para Página/app Meta em modo desenvolvimento (TEST-04); documentação operacional de setup Meta, envs, cron Render e checklist App Review/modo Live, com `.env.example`/docs alinhados (DOC-01); fechar/validar ou produzir evidência verificável e estado atualizado para EXTR-10/11/12, PUBL-10/11/12/13/14, SRCH-10/11/12 e UIUX-10/11/12 (AUD-01..AUD-04); tratar lacunas de verificação/evidência do audit v1.1 aceitas (ex.: `11-VERIFICATION.md` ou equivalente rastreável, caveats 07/08, e handoffs priorizados como DB de testes reprodutível e verificações humanas/browser/canônicas) com artefatos e rastreabilidade explícitos (AUD-05).

**Fora de escopo:** novas capacidades de produto/integração (Instagram, múltiplas páginas/admins, métricas, sync de edição/remoção, geração de imagem, novas features públicas/admin além do necessário para fechar lacunas auditadas), mudanças que reabram contratos preservados (ex.: T-06-01 `/admin/expire` somente `X-Cron-Secret`), ou reescrita ampla de fases concluídas sem necessidade comprovada pela evidência.

</domain>

<decisions>
## Implementation Decisions

### Fechamento dos gaps v1.1 (AUD-01..05, EXTR/PUBL/SRCH/UIUX)
- **D-01:** Adotar estratégia **híbrida: validar e corrigir lacunas reais**. Para cada requisito/lacuna auditada, comparar comportamento e código/testes atuais; implementar correção pontual quando faltar comportamento/aceite; quando já estiver atendido, produzir evidência rastreável e atualizar status/artefatos de forma coerente com a realidade.
- **D-02:** Tratar bloqueios de evidência de forma **reprodutível no repositório + handoffs explícitos**: criar/setup documentado e reproduzível para DB de testes com migrações (permitindo rodar suites DB-backed localmente e, quando viável, em CI), registrar evidências do que for executado neste ambiente, e manter smoke canônico e verificações humanas/browser como **handoff operacional** com checklist, comandos e critérios objetivos.
- **D-03:** Tratar a lacuna do artefato da Fase 11 com **backfill de `11-VERIFICATION.md` na própria Fase 11** (`.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-VERIFICATION.md`), consolidando evidências rastreáveis já existentes (plans/summaries, verificações 07/08/12/13 e artefatos correlatos) e atualizando verificações/traceability relacionadas quando necessário (incluindo caveats de 07/08).
- **D-04:** Prioridade/ordem de execução: **(1)** fechar EXTR/PUBL/SRCH/UIUX e lacunas verificáveis localmente com código + testes + artefatos; **(2)** backfill de `11-VERIFICATION.md` e tratamento dos caveats 07/08; **(3)** preparar DB de testes reprodutível e registrar handoffs canônicos/humanos com critérios objetivos. Critério de fechamento: marcar requisito/lacuna como **fechado/validado** somente com evidência disponível; quando depender de runtime/infra/credenciais indisponíveis aqui (ex.: smoke no host canônico, validação browser humana, app/página Meta real), registrar como **evidência parcial + handoff rastreável** com status explícito, passos e critérios de aceite.

### Cobertura automatizada social/worker e documentação operacional (TEST-01..04, DOC-01)
- **D-05:** Estas áreas estão no escopo da fase (ROADMAP/REQUIREMENTS), mas **não foram detalhadas na discussão**. O planejador/pesquisador deve derivar a abordagem concreta a partir dos requisitos, do código/testes/docs existentes e das decisões D-01..D-04: cobrir geração/classificação/backoff, OAuth/publicação com Graph API mockada e concorrência/idempotência do worker sem chamadas reais em CI; produzir roteiro manual Meta em modo dev e documentação operacional (setup Meta, envs, cron Render, checklist App Review/modo Live, alinhamento de `.env.example`/docs). Reutilizar e estender a base existente (`backend/tests`, `docs/DEPLOY.md`, `scripts/verify-deploy.ps1`, `.github/workflows`) sempre que adequado.

### OpenCode's Discretion
- Forma exata do setup reprodutível de DB de testes/migrações (ex.: script, compose/serviço local, instruções de `alembic upgrade`, fixtures/config de pytest, integração com CI) desde que reproduzível, documentado e sem exigir segredos reais.
- Estrutura, localização e granularidade dos artefatos de evidência/reconciliação (além do backfill obrigatório de `11-VERIFICATION.md` na Fase 11), formato de atualização de status em `REQUIREMENTS.md`/`STATE.md`/verificações e nível de detalhe dos checklists/handoffs.
- Nível e organização dos testes TEST-01..03 e do roteiro/documentação TEST-04/DOC-01, desde que atendam aos critérios de sucesso e não dependam de chamadas reais em CI.
- Necessidade e escopo de correções de código pontuais para tornar requisitos/evidências verdadeiros, preservando contratos existentes e evitando mudanças fora do escopo da fase.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo, requisitos e estado
- `.planning/ROADMAP.md` §"Phase 18: Testes, Documentação e Fechamento de Gaps v1.1" — goal, depends_on (17), requisitos `TEST-01..TEST-04`, `DOC-01`, `AUD-01..AUD-05`, critérios de sucesso e hints de UI.
- `.planning/REQUIREMENTS.md` — definições e rastreabilidade de `TEST-01..TEST-04`, `DOC-01`, `AUD-01..AUD-05` (e estado atual dos requisitos v1.1/v1.2 relevantes).
- `.planning/PROJECT.md` — core value, constraints, decisões v1.2, carry-over aceito do audit v1.1 e riscos/pendências.
- `.planning/STATE.md` — posição atual (pronto para Fase 18), decisões acumuladas, blockers/concerns e deferred items herdados.

### Audit v1.1 e lacunas a fechar (obrigatório)
- `.planning/milestones/v1.1-MILESTONE-AUDIT.md` — gaps, requisitos unsatisfied/partial, fases `gaps_found`, integração/fluxos at-risk, ausência de `11-VERIFICATION.md`, caveats 07/08, handoffs canônicos/humanos/browser e debt de DB de testes.
- `.planning/v1.1-MILESTONE-AUDIT.md` — cópia/registro de auditoria no root de planning (consultar se utilizado como fonte ativa no repo).

### Evidências e artefatos de fases relacionadas (reconciliação/backfill)
- `.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/` — pasta alvo do backfill obrigatório `11-VERIFICATION.md`; ler `11-CONTEXT.md`, `11-RESEARCH.md`, `11-VALIDATION.md`, `11-01-PLAN.md`, `11-01-SUMMARY.md`, `11-02-PLAN.md`, `11-02-SUMMARY.md`, `11-03-PLAN.md`, `11-03-SUMMARY.md`.
- `.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md` — gaps/caveats (DB-backed env-blocked, checks humanos/browser) a tratar/evidenciar conforme D-02/D-03/D-04.
- `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md` — gaps/caveats (DB-backed env-blocked, checks humanos/browser/UX) a tratar/evidenciar conforme D-02/D-03/D-04.
- `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-VERIFICATION.md` — estado de verificação da integração social (must-haves verificados, `human_needed` operacional), referência para escopo de testes/docs restantes.
- `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-CONTEXT.md` — decisões e contratos da publicação social (fire-and-forget, idempotência, retry, UX/status) a respeitar nos testes/docs.

### Deploy, operação e documentação existente
- `docs/DEPLOY.md` — runbook/state-alvo canônico↔legado, matriz D-10, handoff/risco/rollback, gate `verify-deploy.ps1`, cron/segredos/CORS/Turnstile/cold-start; base para DOC-01 e registro de evidências/handoffs.
- `scripts/verify-deploy.ps1` — gate de fumaça parametrizado (health, CORS, cron idempotente, superfícies públicas/legais, no-leak) para evidência local/operacional mapeada.
- `.github/workflows/` — workflows existentes (incluindo cron/catch-up quando aplicável) relevantes para testes/docs de operação.
- `backend/.env.example`, `frontend/.env.example` (e variantes existentes) — alinhamento de variáveis documentadas (Meta/social/worker/site/cron/Turnstile etc.) exigido por SOC-06/DOC-01.

### Código e testes existentes (base de validação/correção)
- `backend/app/services/social/` — geração, política, OAuth Meta, crypto, publisher/Graph, pipeline/claim/retry/idempotência (alvos de TEST-01..03).
- `backend/app/api/v1/admin.py`, `backend/app/api/v1/integrations.py` (se presente), `backend/app/deps.py`, `backend/app/core/config.py`, `backend/app/core/scheduler.py` — fluxos admin/social/OAuth/worker/cron e configuração.
- `backend/app/models/` e `backend/alembic/` — schema/migrações (incluindo `social_*` e `jobs`) relevantes para evidência de DB de testes reprodutível.
- `backend/tests/` — suíte existente (social, Meta/OAuth, publish/retry/idempotency, worker claim, admin/public/reveal/expiry etc.) a reutilizar/estender conforme D-01/D-02/D-05.
- `frontend/app/admin/`, `frontend/lib/api.ts`, `frontend/app/(public)/` — superfícies admin/públicas relacionadas a status social, revisão e requisitos UIUX/PUBL/SRCH a validar/evidenciar.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/tests/test_social_*`, `test_meta_oauth_*`, `test_facebook_publisher.py`, `test_admin_social_*`, `test_social_worker_claim.py`, `test_social_idempotency.py`, `test_social_retry_policy.py`: base ampla para TEST-01..03 (mocks, políticas, pipeline, APIs) a estender/corrigir conforme gaps reais.
- `backend/tests/test_public_*`, `test_reveal_api.py`, `test_report_api.py`, `test_admin_jobs.py`, `test_extract_api.py`, `test_expiry_sweep_integration.py`: base para evidenciar/validar requisitos PUBL/SRCH/UIUX/EXTR/SECR/ADMN/REVW/LIFE/TRST onde aplicável.
- `docs/DEPLOY.md` e `scripts/verify-deploy.ps1`: documentação operacional e gate de fumaça já estruturados (canônico↔legado, T-06-01, matriz/handoff) para evolução DOC-01/AUD-05.
- Artefatos de verificação/summaries/plans em `.planning/phases/07,08,11,12,13,17`: evidências primárias para backfill de `11-VERIFICATION.md` e reconciliação de caveats/traceability.
- `backend/alembic/` + modelos SQLAlchemy: fonte de verdade para tornar o DB de testes migrado/reprodutível (D-02).

### Established Patterns
- **Site-first e fire-and-forget social:** falhas sociais não bloqueiam publicação no site; posts não são sincronizados/removidos após alterações na vaga (preservar em testes/correções).
- **Segurança:** segredos/tokens apenas no backend, criptografados em repouso, nunca em logs/payloads/UI; endpoints operacionais protegidos (ex.: cron por `X-Cron-Secret`, admin por auth existente).
- **Evidência rastreável > afirmação implícita:** audit v1.1 exige artefatos/traceability explícitos; D-04 define status fechado/validado vs evidência parcial + handoff.
- **Contratos preservados:** manter T-06-01 (`/admin/expire` somente `X-Cron-Secret`, fail-closed/idempotente) e distinção state-alvo canônico vs hosts legados evidenciados.

### Integration Points
- **Requisitos/auditoria:** `.planning/REQUIREMENTS.md`, `.planning/milestones/v1.1-MILESTONE-AUDIT.md`, verificações 07/08/11/12/13/17 e `STATE.md`/`ROADMAP.md` para fechamento e atualização de status.
- **Backfill Fase 11:** criação de `11-VERIFICATION.md` em `.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/` referenciando evidências existentes.
- **Infra de testes:** configuração de execução DB-backed (migrações Alembic, env/test DB) integrada a `backend/tests`/pytest e, se aplicável, CI.
- **Docs/ops:** `docs/DEPLOY.md`, `backend/.env.example`, guias/roteiros Meta/App Review/cron Render e possíveis adições de documentação operacional.

</code_context>

<specifics>
## Specific Ideas

- Usuário selecionou discutir apenas **Fechamento dos gaps v1.1 (AUD/EXTR/PUBL/SRCH/UIUX)**; áreas de testes automatizados sociais (TEST-01..03) e documentação/roteiro manual Meta (TEST-04, DOC-01) permanecem em escopo, mas seus detalhes de implementação ficam a critério do planejamento dentro de D-01..D-05.
- Preferência explícita por backfill do arquivo ausente **na Fase 11** (`11-VERIFICATION.md`) em vez de apenas um equivalente solto na Fase 18.
- Quando não for possível executar runtime/infra aqui, não “fechar no escuro”: produzir handoff rastreável com checklist/comandos/critérios objetivos e status explícito.

</specifics>

<deferred>
## Deferred Ideas

- Execução operacional real em hosts canônicos (provisionamento/smoke `scripts/verify-deploy.ps1` no state-alvo), validações humanas/browser completas e testes com app/página Meta reais/credenciais de produção: permanecem como handoffs quando o ambiente/credenciais não estiverem disponíveis nesta sessão, com evidência e critérios registrados (dentro de AUD-05/DOC-01/TEST-04, não como novas capacidades).
- Novas capacidades fora do milestone (Instagram, múltiplas páginas/admins, métricas, sync de edição/remoção, imagem em post): fora de escopo.

</deferred>

---
*Phase: 18-testes-documentacao-e-fechamento-de-gaps-v11*
*Context gathered: 2026-11-16*
