# Requirements: NQU — NaoQueroUsar

**Defined:** 2026-10-13
**Core Value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Admin & Autenticação

- [x] **ADMN-01**: Master faz login na área admin com senha definida via variável de ambiente
- [x] **ADMN-02**: Sessão admin autenticada por JWT persiste durante o uso
- [x] **ADMN-03**: Rotas administrativas bloqueiam acesso não autenticado

### Ingestão & Extração

- [ ] **EXTR-01**: Admin cola um texto grande contendo várias vagas de uma só vez
- [ ] **EXTR-02**: LLM extrai automaticamente os campos de cada vaga em uma lista estruturada
- [ ] **EXTR-03**: Extração usa schema estrito com validação; saídas inválidas viram `needs_review`/`invalid`
- [ ] **EXTR-04**: Sistema faz chunking e throttling para respeitar os limites de taxa do Groq
- [ ] **EXTR-05**: Telefones em pt-BR são normalizados (E.164) para links `wa.me` confiáveis
- [ ] **EXTR-06**: Cada vaga extraída entra no banco com status `pending`
- [ ] **EXTR-07**: Vaga só é criada se tiver ao menos um contato (email ou telefone)
- [ ] **EXTR-08**: Texto de entrada é delimitado para reduzir risco de prompt injection
- [ ] **EXTR-09**: Sistema detecta truncamento (`finish_reason`) e divergência entre vagas detectadas e extraídas

### Revisão Admin

- [ ] **REVW-01**: Admin visualiza a fila de vagas com status `pending`
- [ ] **REVW-02**: Admin aprova uma vaga, mudando seu status para `published`
- [ ] **REVW-03**: Admin edita os campos de uma vaga pelo seu ID
- [ ] **REVW-04**: Admin exclui uma vaga
- [ ] **REVW-05**: Admin vê o trecho do texto-fonte ao lado dos campos extraídos (auxílio de conferência)

### Board Público

- [ ] **PUBL-01**: Visitante lista vagas publicadas em grade responsiva mobile-first, sem cadastro ou login
- [ ] **PUBL-02**: Card mostra título, início das atividades (expansível), salário (quando houver) e botão "Ver a vaga"
- [ ] **PUBL-03**: Visitante abre modal de detalhes completo, mobile-friendly
- [ ] **PUBL-04**: Contato fica oculto por padrão e é revelado pelo botão "Mostrar contato"
- [x] **PUBL-05**: Contato é servido por endpoint dedicado e não aparece no payload público da lista
- [ ] **PUBL-06**: Visitante se candidata via WhatsApp (`wa.me`) e/ou email

### Busca & Filtros

- [ ] **SRCH-01**: Busca por palavra-chave é insensível a acento e caixa (ex.: "sao paulo" == "São Paulo")
- [ ] **SRCH-02**: Filtro por cidade: São Paulo, Rio de Janeiro, Belo Horizonte, Remoto
- [ ] **SRCH-03**: Ordenação por data de publicação (mais recentes por padrão; crescente/decrescente)

### Anti-spam & Segurança

- [x] **SECR-01**: Cloudflare Turnstile é validado no servidor antes de revelar o contato
- [x] **SECR-02**: Endpoint de revelação de contato tem rate limiting por IP
- [x] **SECR-03**: Turnstile também protege o login do admin contra credential stuffing

### Ciclo de Vida

- [ ] **LIFE-01**: Vaga recebe `expires_at` = `created_at` + 14 dias
- [ ] **LIFE-02**: Job agendado faz hard delete de vagas `published` expiradas, de forma idempotente e em UTC
- [ ] **LIFE-03**: Vagas `pending` não revisadas também expiram após 14 dias
- [ ] **LIFE-04**: Expiração é disparada por endpoint protegido por `CRON_SECRET`, com passe de recuperação (catch-up)

### Tema & UI

- [ ] **UIUX-01**: Tema dark minimalista roxo com contraste WCAG AA (usar `#a78bfa` para texto)
- [ ] **UIUX-02**: Botão "Doações" no canto superior direito (amarelo `#facc15`), discreto, efeito apenas no hover
- [ ] **UIUX-03**: Espaços reservados para ADS (banner topo, sidebar, entre cards)

### Confiança & Legal

- [ ] **TRST-01**: Vaga publicada exibe badge "Vaga revisada"
- [ ] **TRST-02**: Visitante pode denunciar uma vaga (report)
- [ ] **TRST-03**: Páginas de privacidade, termos e aviso "somos apenas meio de divulgação" (LGPD)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Descoberta & Alcance

- **SEO-01**: URLs dedicadas por vaga com JSON-LD `JobPosting` (Google Jobs)
- **SEO-02**: Sitemap de vagas publicadas

### Retenção

- **ALRT-01**: Alertas de novas vagas por email/WhatsApp
- **SAVE-01**: Buscas salvas

### Navegação

- **MAP-01**: Mapa / geolocalização de vagas
- **FCT-01**: Facets adicionais (faixa salarial, tipo de vaga)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Contas/login de usuário comum | Contraria o diferencial (sem burocracia de cadastro) |
| Renovação de vagas expiradas | Fora de escopo; expiração é definitiva (ciclo completo) |
| Controle de duplicidade de vagas | Curadoria manual cobre; volume 100–500/mês |
| Múltiplos admins / papéis de usuário | Apenas o master posta/aprova |
| Submissão pública de vagas | Não no MVP; curadoria solo é o gate de qualidade |
| Chat/ATS/currículo dentro da plataforma | Não é o core (board de divulgação) |
| Monetização ativa (vagas destaque pagas, ADS reais) | Baixa prioridade no MVP; apenas placeholders |
| Scraping/agregação de outros boards | Modelo é curadoria manual, não agregação |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ADMN-01 | Phase 1 | Complete |
| ADMN-02 | Phase 1 | Complete |
| ADMN-03 | Phase 1 | Complete |
| EXTR-01 | Phase 2 | Pending |
| EXTR-02 | Phase 2 | Pending |
| EXTR-03 | Phase 2 | Pending |
| EXTR-04 | Phase 2 | Pending |
| EXTR-05 | Phase 2 | Pending |
| EXTR-06 | Phase 2 | Pending |
| EXTR-07 | Phase 2 | Pending |
| EXTR-08 | Phase 2 | Pending |
| EXTR-09 | Phase 2 | Pending |
| SECR-01 | Phase 3 | Complete |
| SECR-02 | Phase 3 | Complete |
| SECR-03 | Phase 3 | Complete |
| PUBL-05 | Phase 3 | Complete |
| PUBL-01 | Phase 4 | Pending |
| PUBL-02 | Phase 4 | Pending |
| PUBL-03 | Phase 4 | Pending |
| PUBL-04 | Phase 4 | Pending |
| PUBL-06 | Phase 4 | Pending |
| SRCH-01 | Phase 4 | Pending |
| SRCH-02 | Phase 4 | Pending |
| SRCH-03 | Phase 4 | Pending |
| UIUX-01 | Phase 4 | Pending |
| UIUX-02 | Phase 4 | Pending |
| UIUX-03 | Phase 4 | Pending |
| REVW-01 | Phase 5 | Pending |
| REVW-02 | Phase 5 | Pending |
| REVW-03 | Phase 5 | Pending |
| REVW-04 | Phase 5 | Pending |
| REVW-05 | Phase 5 | Pending |
| LIFE-01 | Phase 6 | Pending |
| LIFE-02 | Phase 6 | Pending |
| LIFE-03 | Phase 6 | Pending |
| LIFE-04 | Phase 6 | Pending |
| TRST-01 | Phase 6 | Pending |
| TRST-02 | Phase 6 | Pending |
| TRST-03 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 39 total
- Mapped to phases: 39
- Unmapped: 0 ✓

**Per Phase:**
- Phase 1 — Backend Foundation, Data & Admin Auth: ADMN-01, ADMN-02, ADMN-03 (3)
- Phase 2 — LLM Extraction Pipeline (HIGH RISK): EXTR-01..09 (9)
- Phase 3 — Contact Reveal & Anti-Spam (HIGH RISK): SECR-01, SECR-02, SECR-03, PUBL-05 (4)
- Phase 4 — Public Board Frontend: PUBL-01..04, PUBL-06, SRCH-01..03, UIUX-01..03 (11)
- Phase 5 — Admin Review Area: REVW-01..05 (5)
- Phase 6 — Lifecycle, Trust, Legal & Launch (HIGH RISK): LIFE-01..04, TRST-01..03 (7)

---
*Requirements defined: 2026-10-13*
*Last updated: 2026-10-13 after roadmap creation (traceability + coverage 39/39)*
