# Roadmap: EmpregaNoix

## Milestones

- ✅ **v1.1 EmpregaNoix** — Phases 7–13 (shipped 2026-11-15, audit `gaps_found` accepted) — [Archive](./milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Integração com Facebook Pages** — Phases 14–18 (shipped 2026-11-17, audit missing / gaps+handoffs accepted) — [Archive](./milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Chatbot Inteligente de Busca de Vagas** — Phases 19–25 (shipped 2026-11-22, audit `tech_debt` accepted) — [Archive](./milestones/v1.3-ROADMAP.md)
- ✅ **v1.4 Polimento UX e Admin** — Phases 26–28 (shipped 2026-11-23, audit `tech_debt` accepted) — [Archive](./milestones/v1.4-ROADMAP.md)
- 🚧 **v1.5 Integração Instagram na Revisão** — Phases 29–32 (in progress)

## Phases

<details>
<summary>✅ v1.3 Chatbot Inteligente de Busca de Vagas (Phases 19–25) — SHIPPED 2026-11-22</summary>

- [x] Phase 19: Contrato de intenção e mapeamento seguro (2/2 plans) — completed 2026-11-17
- [x] Phase 20: API pública de chat-search resiliente (2/2 plans) — completed 2026-11-18
- [x] Phase 21: Interface de chat e integração no board (2/2 plans) — completed 2026-11-18
- [x] Phase 22: Qualidade, hardening e validação operacional (3/3 plans) — completed 2026-11-18
- [x] Phase 23: Fechamento de débitos de auditoria e validação v1.3 (5/5 plans) — completed 2026-11-20
- [x] Phase 24: Corrigir conflito crítico de cidade e resíduos de review (3/3 plans) — completed 2026-11-22
- [x] Phase 25: Reconciliar gates de fechamento e revalidar auditoria v1.3 (2/2 plans) — completed 2026-11-22

</details>

<details>
<summary>✅ v1.4 Polimento UX e Admin (Phases 26–28) — SHIPPED 2026-11-23</summary>

- [x] Phase 26: Acesso Admin Dedicado (2/2 plans) — completed 2026-11-22
- [x] Phase 27: Controles por Ambiente (1/1 plans) — completed 2026-11-22
- [x] Phase 28: Polimento UX da Home (3/3 plans) — completed 2026-11-23

</details>

### 🚧 v1.5 Integração Instagram na Revisão (In Progress)

**Milestone Goal:** Permitir publicar cada vaga aprovada também no Instagram, com legenda configurada na etapa de revisão, reaproveitando a base Meta/Facebook existente e mantendo as publicações independentes.

- [x] **Phase 29: Meta/IG Readiness & Media Foundation** - Prontidão Meta/Instagram e base de imagem pública segura para publicação (3/3 plans) (completed 2026-11-23)
- [x] **Phase 30: Instagram Review Experience** - Seção Instagram na revisão com controles, validações e preview (completed 2026-11-25)
- [ ] **Phase 31: Independent Publish Pipeline** - Publicação assíncrona Instagram desacoplada do Facebook com segurança operacional
- [ ] **Phase 32: Hardening, Regression & Operations** - Cobertura automatizada, regressão Facebook e documentação operacional

## Phase Details

### Phase 29: Meta/IG Readiness & Media Foundation
**Goal**: Admin e sistema têm prontidão Instagram confirmável e uma base de mídia pública válida para o fluxo de publicação.
**Depends on**: Phase 28
**Requirements**: META-01, META-02, META-03, IMAG-01, IMAG-02, IMAG-03
**Success Criteria** (what must be TRUE):
  1. Admin vê em Integrações se a Página selecionada está pronta para Instagram, incluindo conta IG Business/Creator vinculada, `ig-user-id` resolvido e estado acionável de reconexão/correção quando algo faltar.
  2. Backend resolve e persiste `ig-user-id` reaproveitando o fluxo/token Meta existente, e falhas de linkage ausente/inválido aparecem como erro seguro sem quebrar a integração Facebook.
  3. Sistema expõe contrato de validação/preparação de imagem Instagram com feedback claro em pt-BR para imagem ausente/inválida/URL pública inválida, deixando explícito que o bloqueio se aplica apenas ao Instagram; Phase 30 aplica enforcement na revisão e Phase 31 revalida antes de publicar (sem bloquear Facebook/site).
  4. Quando não houver imagem de origem disponível, o sistema gera um card fallback determinístico da vaga em formato compatível com Instagram e o admin consegue visualizar a imagem exata pretendida por URL pública HTTPS acessível pela Meta.
  5. Existe documentação/checklist operacional da configuração Meta/Instagram (permissões/escopos, premissas de App Review/roles/tasks, setup/verificação) disponível para execução manual.
**Plans:** 3/3 plans complete
- [x] 29-01-PLAN.md — IG readiness foundation: SocialAccount IG fields, migration 0006, media contracts, Meta status/verify IG readiness, META-01/02 tests
- [x] 29-02-PLAN.md — Deterministic IG card rendering, versioned public HTTPS media serving, validation/provenance contracts
- [x] 29-03-PLAN.md — Admin Integrations IG readiness UX and Meta/IG operational documentation

**UI hint**: yes
**Research flags / decisions**: Discuss-phase decisions remain open — image origin (logo/card gerado/upload), card format/storage/serving, image generation strategy, token renewal/alert strategy. Confirm current Meta permissions/App Review/Advanced Access assumptions before live rollout. Keep Graph version config-driven.

### Phase 30: Instagram Review Experience
**Goal**: Admin revisa e ajusta a publicação Instagram por vaga com feedback claro antes de aprovar.
**Depends on**: Phase 29
**Requirements**: REVW-01, REVW-02, REVW-03, REVW-04
**Success Criteria** (what must be TRUE):
  1. Admin vê na revisão uma seção Instagram ao lado do Facebook, com toggle por vaga e status independente por plataforma.
  2. Admin edita legenda Instagram pré-preenchida a partir da vaga, vê contador ao vivo `N/2200` e não consegue salvar/aprovar legenda acima do limite.
  3. Admin recebe aviso quando a legenda passa de 30 hashtags e orientação clara de que links na legenda não são clicáveis, com CTA no estilo “link na bio”.
  4. Admin visualiza antes de aprovar/publicar o preview da imagem exata que será enviada ao Instagram e não consegue aprovar/publicar Instagram sem imagem válida (contrato IMAG-01 da Phase 29), sem bloquear Facebook/site.
**Plans**: TBD
**UI hint**: yes
**Research flags / decisions**: Caption prefill must be Instagram-tuned (not blind Facebook reuse). Image source selection/preview depends on Phase 29 media decisions; keep UX ready for fallback card and future source extensions without new abstractions.

### Phase 31: Independent Publish Pipeline
**Goal**: Publicação Instagram ocorre de forma assíncrona, segura e independente do Facebook.
**Depends on**: Phase 30
**Requirements**: PUBL-01, PUBL-02, PUBL-03, PUBL-04, PUBL-05
**Success Criteria** (what must be TRUE):
  1. Ao aprovar/publicar uma vaga com Instagram habilitado, o processamento Instagram e Facebook segue de forma independente: falha em uma plataforma não bloqueia nem corrompe a outra.
  2. Sistema publica no Instagram pelo fluxo Graph API em 2 passos (criar container, checar status quando necessário, publicar), com comportamento seguro em timeout/erro.
  3. Admin consegue consultar resultado por plataforma com status, erro seguro acionável, IDs/permalink quando disponíveis, e histórico/auditoria sem exposição de tokens ou segredos.
  4. Retentativas e falhas ambíguas não causam duplicação cega de post; casos ambíguos ficam em estado seguro que exige verificação/reconciliação antes de nova tentativa automática.
  5. Limites de rate/diário do Instagram são tratados com segurança (sem retry storm), exibindo estado acionável ao admin quando publicação estiver bloqueada por limite.
**Plans**: TBD
**Research flags / decisions**: Treat `content_publishing_limit` as runtime authority; classify 2207042/rate-limit distinctly. Keep Graph version config-driven. Token renewal/alert strategy remains an open discuss-phase decision; at minimum map auth failures to reconnect-required actionable state.

### Phase 32: Hardening, Regression & Operations
**Goal**: Integração Instagram é verificável, observável e segura de operar sem regressão no fluxo Facebook.
**Depends on**: Phase 31
**Requirements**: HARD-01, HARD-02
**Success Criteria** (what must be TRUE):
  1. Suíte automatizada cobre os cenários críticos de Instagram (draft/validação, idempotência, retry, ambiguidade, rate limit, mapeamento de erro) e inclui caracterização/regressão do fluxo Facebook.
  2. Operador tem documentação operacional completa para env vars, checklist manual Meta, expiração/reconexão de token e troubleshooting de estados de publicação Instagram.
  3. Evidências de validação deixam claro o que foi coberto por testes automatizados e o que requer checklist/manual Meta, sem afirmar execução manual não realizada.
**Plans**: TBD
**Research flags / decisions**: Manual Meta verification/App Review steps are expected handoffs, not fabricated evidence. Include Facebook regression characterization as a release gate.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 19. Contrato de intenção e mapeamento seguro | v1.3 | 2/2 | Complete | 2026-11-17 |
| 20. API pública de chat-search resiliente | v1.3 | 2/2 | Complete | 2026-11-18 |
| 21. Interface de chat e integração no board | v1.3 | 2/2 | Complete | 2026-11-18 |
| 22. Qualidade, hardening e validação operacional | v1.3 | 3/3 | Complete | 2026-11-18 |
| 23. Fechamento de débitos de auditoria e validação v1.3 | v1.3 | 5/5 | Complete | 2026-11-20 |
| 24. Corrigir conflito crítico de cidade e resíduos de review | v1.3 | 3/3 | Complete | 2026-11-22 |
| 25. Reconciliar gates de fechamento e revalidar auditoria v1.3 | v1.3 | 2/2 | Complete | 2026-11-22 |
| 26. Acesso Admin Dedicado | v1.4 | 2/2 | Complete | 2026-11-22 |
| 27. Controles por Ambiente | v1.4 | 1/1 | Complete | 2026-11-22 |
| 28. Polimento UX da Home | v1.4 | 3/3 | Complete | 2026-11-23 |
| 29. Meta/IG Readiness & Media Foundation | v1.5 | 3/3 | Complete    | 2026-11-23 |
| 30. Instagram Review Experience | v1.5 | 2/2 | Complete   | 2026-11-25 |
| 31. Independent Publish Pipeline | v1.5 | 0/TBD | Not started | - |
| 32. Hardening, Regression & Operations | v1.5 | 0/TBD | Not started | - |
