# Requirements: EmpregaNoix

**Defined:** 2026-11-23
**Core Value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

## v1.5 Requirements

Requirements for milestone v1.5: Integração Instagram na Revisão. Each maps to roadmap phases.

### IG Readiness & Meta

- [x] **META-01**: Admin vê no Integrações o estado de prontidão do Instagram para a Página Facebook selecionada (conta IG Business/Creator vinculada, `ig-user-id` resolvido/armazenado, permissões/escopos necessários presentes) com estado acionável de reconexão/correção.
- [x] **META-02**: Backend resolve e persiste `ig-user-id` a partir da Página Facebook vinculada reutilizando o fluxo/token Meta existente; linkage ausente/inválido é tratado com erro seguro e não quebra a integração Facebook.
- [ ] **META-03**: Projeto documenta permissões/escopos Meta atuais, premissas de App Review/Advanced Access/roles/tasks e checklist manual de setup/verificação Instagram.

### Mídia / Imagem Pública

- [x] **IMAG-01**: Publicação no Instagram exige imagem válida; sistema fornece contrato/validação com feedback claro em pt-BR e bloqueio aplicável apenas ao Instagram (contrato/preparação na Phase 29, enforcement na revisão na Phase 30, revalidação no publish na Phase 31).
- [x] **IMAG-02**: Sistema gera card fallback determinístico a partir dos dados da vaga (1080x1080 ou 1080x1350, JPEG sRGB, <8MB, proporção compatível 4:5–1.91:1) quando não houver imagem de origem selecionada/disponível.
- [x] **IMAG-03**: A imagem usada no Instagram é servida por URL pública HTTPS estável, acessível pela Meta (sem auth, não localhost/privada/efêmera), com validação, preview e proveniência registrada.

### Review UI Instagram

- [ ] **REVW-01**: Diálogo de revisão exibe seção Instagram ao lado do Facebook com toggle por vaga e status independente por plataforma.
- [ ] **REVW-02**: Admin edita legenda Instagram pré-preenchida a partir dos dados da vaga; UI mostra contador ao vivo `N/2200` e bloqueia legenda acima do limite.
- [ ] **REVW-03**: UI da legenda Instagram avisa quando há >30 hashtags e orienta que links na legenda não são clicáveis, usando CTA tipo “link na bio” (URL não é CTA clicável principal).
- [ ] **REVW-04**: Admin visualiza preview da imagem exata pretendida para publicação no Instagram antes de aprovar/publicar.

### Publish / Segurança Operacional

- [ ] **PUBL-01**: Aprovação/publicação processa Instagram e Facebook de forma independente; falha em uma plataforma não bloqueia nem corrompe a outra.
- [ ] **PUBL-02**: Backend implementa publicação Instagram Graph API (Content Publishing) em 2 passos assíncronos (criar container, checar status quando necessário, publicar) com versão Graph configurável e tratamento seguro de timeout.
- [ ] **PUBL-03**: Pipeline persiste legenda usada, IDs de container/post, permalink quando disponível, status, erro seguro, tentativas e timestamps; logs não expõem tokens/segredos.
- [ ] **PUBL-04**: Retry/backoff é idempotente e seguro contra ambiguidade; resultado ambíguo/timeout não dispara auto-retry cego que possa duplicar post.
- [ ] **PUBL-05**: Rate limit e limite diário de publicação Instagram são tratados com segurança (consulta/runtime authority como `content_publishing_limit` quando aplicável, classificação segura de 2207042/rate limit, sem retry storm) com status acionável ao admin.

### Qualidade / Hardening

- [ ] **HARD-01**: Testes automatizados cobrem draft/validação Instagram, publisher/pipeline (idempotência, retry, ambiguidade, rate limit, mapeamento de erros) e caracterização/regressão do fluxo Facebook.
- [ ] **HARD-02**: Documentação operacional inclui env vars, checklist manual Meta, orientação de expiração/reconexão de token e troubleshooting de estados de publicação Instagram.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Social Publishing

- **SOC2-01**: Agendamento de publicação Instagram/Facebook.
- **SOC2-02**: Suporte a Stories/Reels/carrossel/vídeo.
- **SOC2-03**: Métricas/analytics de engajamento do Instagram.
- **SOC2-04**: Múltiplas contas Instagram / seleção por conta.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Stories, Reels, carrossel/vídeo | Fora do milestone v1.5; formatos/containers/UX diferentes e complexidade alta. |
| Agendamento de posts | Fora do milestone v1.5; adiciona complexidade de fila/tempo/edição pós-agendamento. |
| Métricas/analytics do Instagram | Fora do milestone v1.5; não é núcleo da descoberta de vagas. |
| Responder comentários ou DMs | Fora do milestone v1.5; superfície operacional/compliance diferente. |
| Publicação em múltiplas contas Instagram | Fora do milestone v1.5; modelo atual é admin único/página única. |
| Auto-publicação IG por padrão sem validação explícita | Risco de falhas/publicações ruins por constraints de mídia/conta; manter controle por vaga. |
| Reuso cego da legenda Facebook no Instagram | Instagram tem constraints/UX diferentes (link não clicável, hashtags, tom). |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| META-01 | Phase 29 | Complete |
| META-02 | Phase 29 | Complete |
| META-03 | Phase 29 | Pending |
| IMAG-01 | Phase 29, Phase 30, Phase 31 | Complete |
| IMAG-02 | Phase 29 | Complete |
| IMAG-03 | Phase 29 | Complete |
| REVW-01 | Phase 30 | Pending |
| REVW-02 | Phase 30 | Pending |
| REVW-03 | Phase 30 | Pending |
| REVW-04 | Phase 30 | Pending |
| PUBL-01 | Phase 31 | Pending |
| PUBL-02 | Phase 31 | Pending |
| PUBL-03 | Phase 31 | Pending |
| PUBL-04 | Phase 31 | Pending |
| PUBL-05 | Phase 31 | Pending |
| HARD-01 | Phase 32 | Pending |
| HARD-02 | Phase 32 | Pending |

**Coverage:**
- v1.5 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---
*Requirements defined: 2026-11-23*
*Last updated: 2026-11-23 after v1.5 roadmap creation (phases 29-32)*