# Roadmap: EmpregaNoix

## Milestones

- ✅ **v1.1 EmpregaNoix** — Phases 7–13 (shipped 2026-11-15, audit `gaps_found` accepted) — [Archive](./milestones/v1.1-ROADMAP.md)
- 🚧 **v1.2 Integração com Facebook Pages** — Phases 14–18 (in progress)

## Phases

**Phase Numbering:**
- Continues from v1.1 (ended at Phase 13). v1.2 starts at Phase 14.
- Integer phases (14, 15, 16...): Planned milestone work.
- Prior phase history (1–13) remains in `.planning/phases/` and milestone archives.

- [x] **Phase 14: Fundação Social, Dados e Configuração** - Criar base de dados, segurança de tokens e contratos de publicação social (Facebook-first, extensível) (completed 2026-11-15)
- [x] **Phase 15: OAuth Meta e Integrações no Admin** - Conectar/desconectar página do Facebook com fluxo OAuth seguro e status operacional visível (completed 2026-11-15)
- [ ] **Phase 16: Geração, Revisão e Aprovação do Post Social** - Produzir rascunho de post com IA/template, permitir edição/agendamento na revisão e integrar aprovação sem bloquear o site
- [ ] **Phase 17: Publicação Assíncrona, Retry, Idempotência e Status** - Publicar/agendar no Facebook via worker resiliente e expor status/erros/retry no admin
- [ ] **Phase 18: Testes, Documentação e Fechamento de Gaps v1.1** - Cobrir fluxos críticos com testes/docs operacionais e fechar/registrar evidências dos gaps aceitos do audit v1.1

## Phase Details

### Phase 14: Fundação Social, Dados e Configuração
**Goal**: O backend possui a fundação persistente e segura para integração social (Facebook agora, Instagram futuro), com configuração explícita e sem exposição de segredos.
**Depends on**: Phase 13 (v1.1 shipped baseline)
**Requirements**: SOC-01, SOC-02, SOC-03, SOC-04, SOC-05, SOC-06
**Success Criteria** (what must be TRUE):
  1. Migrações Alembic criam `social_accounts` e `social_posts` com campos/status/índices necessários (incluindo unicidade `(job_id, provider)` e metadados de retry/publicação); `social_post_logs` existe se adotado.
  2. Tokens de página são armazenados criptografados em repouso (chave via env) e nunca aparecem em logs, payloads de API ou frontend.
  3. Existe contrato `SocialPublisher` e implementação inicial `FacebookPublisher` (stub/estrutura pronta para publicação) sem acoplar o fluxo a um provider específico.
  4. `.env.example` e config documentam as variáveis Meta/social/worker/site (`META_*`, `SOCIAL_*`, `SITE_PUBLIC_URL` etc.) alinhadas às convenções do backend.
**Plans**: TBD

### Phase 15: OAuth Meta e Integrações no Admin
**Goal**: O admin único consegue conectar uma única Página do Facebook pelo painel, com estado de conexão confiável e credenciais protegidas no backend.
**Depends on**: Phase 14
**Requirements**: META-01, META-02, META-03, META-04, META-05, META-06
**Success Criteria** (what must be TRUE):
  1. Admin autenticado consegue iniciar OAuth, concluir callback com validação de `state` anti-CSRF, trocar code→tokens e persistir a conexão da Página selecionada.
  2. O fluxo solicita permissões mínimas e usa `META_GRAPH_VERSION` configurável; quando há múltiplas páginas, apenas uma é selecionada/salva.
  3. Token/página são validados (ex.: `/debug_token`); token inválido/expirado marca a conta como `needs_reconnect` e o backend não expõe segredos ao frontend.
  4. A área admin de Integrações exibe status, nome da página e ações de conectar/desconectar/reconectar com alerta quando reconexão é necessária.
**Plans:** 3/3 plans complete

Plans:
- [x] 15-01-PLAN.md — OAuth/Meta backend foundation (state, pending selection, schemas, services)
- [x] 15-02-PLAN.md — Meta integrations API routes and callback flow
- [x] 15-03-PLAN.md — Admin Integrações UI and human verification (approved)

**UI hint**: yes

### Phase 16: Geração, Revisão e Aprovação do Post Social
**Goal**: Na revisão, o admin recebe um rascunho de post (IA ou fallback), pode ajustar/agendar e aprovar a vaga com criação do registro social sem que falhas sociais afetem a publicação no site.
**Depends on**: Phase 14, Phase 15
**Requirements**: POST-01, POST-02, POST-03, POST-04, POST-05, POST-06
**Success Criteria** (what must be TRUE):
  1. Ao abrir/revisar uma vaga, o sistema gera (reutilizando LLM existente) ou monta por template fallback um rascunho pt-BR editável com CTA/link da vaga, salvo como `draft`.
  2. O revisor pode editar, regenerar, ver preview/contador e escolher publicar agora ou agendar (padrão imediato) em `America/Sao_Paulo`.
  3. Aprovar a vaga publica no site imediatamente e registra o `social_post` aprovado (texto imutável após envio) com modo/horário corretos; se a geração/envio social falhar, a vaga do site permanece publicada.
  4. O conteúdo do post segue política configurada (por padrão sem contato direto, apenas link público via `SITE_PUBLIC_URL` + URL da vaga).
**Plans:** 3 plans

Plans:
- [ ] 16-01-PLAN.md — Backend draft foundation (geração LLM/fallback, política/link/BRT, schemas/CRUD/config)
- [ ] 16-02-PLAN.md — APIs admin de draft e approve site-first com registro social best-effort
- [ ] 16-03-PLAN.md — UI admin de revisão (seção Post para Facebook) e feedback de aprovação social
**UI hint**: yes

### Phase 17: Publicação Assíncrona, Retry, Idempotência e Status
**Goal**: Posts sociais são enviados/agendados de forma assíncrona e resiliente (sem duplicatas), e o admin consegue acompanhar e retentar com segurança.
**Depends on**: Phase 16
**Requirements**: PUB-01, PUB-02, PUB-03, PUB-04, PUB-05, PUB-06, PUB-07, PUB-08, UI-01, UI-02
**Success Criteria** (what must be TRUE):
  1. Aprovação dispara tentativa assíncrona (quando aplicável) e/ou agenda elegível; worker protegido acionado por cron (Render, 1–5 min) processa itens com `FOR UPDATE SKIP LOCKED` sem bloquear a resposta de aprovação.
  2. `FacebookPublisher` publica via `POST /{page_id}/feed` com `message` e `link`; sucesso registra `external_post_id`/`published_at` e falhas transitórias/permanentes seguem política de retry/backoff configurável (default 5 tentativas) com `next_retry_at`/erro resumido.
  3. Idempotência impede duplicatas em concorrência, reexecução de cron ou clique duplo (checagem de estado/ID externo + lock/constraint); posts são fire-and-forget (editar/fechar/expirar vaga não altera/remove post no Facebook).
  4. Admin vê badge/status social, erro resumido e link do post publicado por vaga, e pode acionar "tentar novamente" apenas para casos elegíveis respeitando as mesmas regras.
**Plans**: TBD
**UI hint**: yes

### Phase 18: Testes, Documentação e Fechamento de Gaps v1.1
**Goal**: A integração social e o carry-over prioritário do v1.1 têm cobertura automatizada/manual documentada e evidências rastreáveis para operação e aceite.
**Depends on**: Phase 17
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, DOC-01, AUD-01, AUD-02, AUD-03, AUD-04, AUD-05
**Success Criteria** (what must be TRUE):
  1. Suíte automatizada cobre geração/classificação/backoff, OAuth/publicação com Graph API mockada e cenários de concorrência/idempotência do worker sem chamadas reais em CI.
  2. Existe roteiro manual para teste com Página/app Meta em modo desenvolvimento e documentação operacional de setup Meta, envs, cron Render e checklist App Review/modo Live (incluindo `.env.example`/docs alinhados).
  3. Requisitos EXTR-10/11/12, PUBL-10/11/12/13/14, SRCH-10/11/12 e UIUX-10/11/12 são fechados/validados ou possuem evidência verificável e estado atualizado conforme resultado.
  4. Lacunas de verificação/evidência do audit v1.1 (ex.: `11-VERIFICATION.md` ou equivalente rastreável, caveats 07/08 e handoffs priorizados como DB de testes/verificações humanas-browser-canônicas) são tratadas com artefatos e rastreabilidade explícitos.
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 14. Fundação Social, Dados e Configuração | 3/3 | Complete    | 2026-11-15 |
| 15. OAuth Meta e Integrações no Admin | 3/3 | Complete    | 2026-11-15 |
| 16. Geração, Revisão e Aprovação do Post Social | 0/3 | Planned | - |
| 17. Publicação Assíncrona, Retry, Idempotência e Status | 0/0 | Not started | - |
| 18. Testes, Documentação e Fechamento de Gaps v1.1 | 0/0 | Not started | - |

## Coverage

- v1.2 requirements mapped: 37/37 ✓
- Mapped: SOC 6, META 6, POST 6, PUB 8, UI 2, TEST 4, DOC 1, AUD 5
- Orphaned requirements: none
