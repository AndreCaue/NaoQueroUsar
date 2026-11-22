# Requirements: EmpregaNoix

**Defined:** 2026-11-22
**Core Value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

## v1.4 Requirements

Requirements for milestone v1.4 Polimento UX e Admin. Each maps to roadmap phases.

### Filtro de Cidades

- [ ] **CITY-01**: Usuário vê no filtro de cidades da home apenas cidades que possuem vagas publicadas/ativas no momento

### Acesso Admin

- [x] **ADMN-01**: Admin acessa login em página dedicada, separada da página de paste/revisão
- [x] **ADMN-02**: Usuário encontra um link discreto para login admin na página de Política de Privacidade

### Configuração por Ambiente

- [ ] **ADS-01**: Espaços publicitários podem ser ocultados por flag única no `.env` (sem remover código, apenas controle de exibição)
- [ ] **DONA-01**: Botão de Doações abre link configurado no `.env` quando configurado; comportamento seguro quando ausente/desabilitado

### UX Visual

- [ ] **UIUX-01**: Usuário recebe feedback visual de hover em dropdown recentes/antigos, cards de vaga e filtros de cidades

## Future Requirements

### Carry-over / Hardening (avaliar em milestones futuros)

- **CARRY-01**: Reconciliar `PUB-01..08` e handoffs `TEST-04/DOC-01/AUD-05` (v1.2)
- **CARRY-02**: Endereçar lacunas v1.1 aceitas (EXTR/PUBL/SRCH/UIUX) e débitos operacionais/testes
- **CARRY-03**: Endereçar residuals v1.3 aceitos (D-14/WR-02 focus trap, deferimentos runtime/browser, Nyquist 21/22/23/25, CL-02 heuristic residual)
- **CARRY-04**: Limpar dívida de processo `23-06/23-07` PLANs sem SUMMARYs

## Out of Scope

| Feature | Reason |
|---------|--------|
| Login/cadastro de usuário comum | Diferencial do produto é fricção zero para candidato |
| Controle de anúncios por slot individual | v1.4 pede flag única; granularidade por slot é complexidade desnecessária agora |
| Sistema de doação/payment processing interno | MVP usa link externo configurado por env; sem processamento financeiro no app |
| Redesign completo da home/admin | Escopo é polimento pontual, não reescrita visual |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CITY-01 | Phase 28 | Pending |
| ADMN-01 | Phase 26 | Complete |
| ADMN-02 | Phase 26 | Complete |
| ADS-01 | Phase 27 | Pending |
| DONA-01 | Phase 27 | Pending |
| UIUX-01 | Phase 28 | Pending |

**Coverage:**
- v1.4 requirements: 6 total
- Mapped to phases: 6
- Unmapped: 0 ✓

---
*Requirements defined: 2026-11-22*
*Last updated: 2026-11-22 after v1.4 requirements definition*