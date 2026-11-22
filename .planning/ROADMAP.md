# Roadmap: EmpregaNoix

## Milestones

- ✅ **v1.1 EmpregaNoix** — Phases 7–13 (shipped 2026-11-15, audit `gaps_found` accepted) — [Archive](./milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Integração com Facebook Pages** — Phases 14–18 (shipped 2026-11-17, audit missing / gaps+handoffs accepted) — [Archive](./milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Chatbot Inteligente de Busca de Vagas** — Phases 19–25 (shipped 2026-11-22, audit `tech_debt` accepted) — [Archive](./milestones/v1.3-ROADMAP.md)
- 🚧 **v1.4 Polimento UX e Admin** — Phases 26–28 (in progress)

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

### 🚧 v1.4 Polimento UX e Admin (In Progress)

**Milestone Goal:** Melhorar a experiência pública e o fluxo admin com ajustes de UX, controle por ambiente e acesso admin dedicado — sem perder a fricção zero do candidato.

- [x] **Phase 26: Acesso Admin Dedicado** - Login admin em página dedicada com entrada discreta pela Política de Privacidade (completed 2026-11-22)
- [x] **Phase 27: Controles por Ambiente** - Anúncios e doações controlados por variáveis de ambiente (completed 2026-11-22)
- [ ] **Phase 28: Polimento UX da Home** - Filtro de cidades dinâmico e feedback visual de hover na home

## Phase Details

### Phase 26: Acesso Admin Dedicado
**Goal**: Admin acessa login por página dedicada e o ponto de entrada público permanece discreto.
**Depends on**: Phase 25
**Requirements**: ADMN-01, ADMN-02
**Success Criteria** (what must be TRUE):
  1. Admin consegue abrir uma página de login dedicada, separada da página de paste/revisão.
  2. Admin consegue autenticar-se pela página dedicada e acessar o fluxo admin protegido normalmente.
  3. Usuário encontra na página de Política de Privacidade um link discreto que leva à página de login admin.
  4. A página de paste/revisão não exige mais interação com formulário de login como fluxo principal para acessar a área protegida.
**Plans**: TBD
**UI hint**: yes

### Phase 27: Controles por Ambiente
**Goal**: Operador controla exibição de anúncios e destino de doações por variáveis de ambiente, sem remover código.
**Depends on**: Phase 26
**Requirements**: ADS-01, DONA-01
**Success Criteria** (what must be TRUE):
  1. Quando a flag única de anúncios no `.env` está desativada, os espaços publicitários não aparecem na interface pública.
  2. Quando a flag única de anúncios no `.env` está ativada, os espaços publicitários voltam a ser exibidos normalmente.
  3. Quando o link de doação está configurado no `.env`, o botão Doações abre o link configurado.
  4. Quando o link de doação está ausente ou desabilitado, o botão Doações tem comportamento seguro e não leva a destino inválido.
**Plans:** 1/1 plans complete

Plans:
- [x] 27-01-PLAN.md — Controles por ambiente para anúncios e doações

### Phase 28: Polimento UX da Home
**Goal**: Candidato vê apenas filtros úteis e recebe feedback visual claro nos elementos interativos da home.
**Depends on**: Phase 27
**Requirements**: CITY-01, UIUX-01
**Success Criteria** (what must be TRUE):
  1. Usuário vê no filtro de cidades somente cidades que possuem vagas publicadas/ativas no momento.
  2. Usuário recebe feedback visual de hover ao passar o mouse sobre opções do dropdown recentes/antigos.
  3. Usuário recebe feedback visual de hover ao passar o mouse sobre cards de vaga.
  4. Usuário recebe feedback visual de hover ao passar o mouse sobre filtros de cidades.
**Plans**: TBD
**UI hint**: yes

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
| 26. Acesso Admin Dedicado | v1.4 | 2/2 | Complete    | 2026-11-22 |
| 27. Controles por Ambiente | v1.4 | 1/1 | Complete    | 2026-11-22 |
| 28. Polimento UX da Home | v1.4 | 0/TBD | Not started | - |
