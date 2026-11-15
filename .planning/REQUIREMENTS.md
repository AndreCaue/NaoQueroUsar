# Requirements: EmpregaNoix v1.1

**Defined:** 2026-11-12
**Core Value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

## v1.1 Requirements

Requirements for this milestone continuation. Each maps to roadmap phases. Continuing from v1.0 REQ-IDs.

### Admin & Autenticação (continuado)

- [x] **ADMN-10**: Admin vê indicador de Turnstile no login (widget interaction-only) — validação visual no clique *(Phase 11 gap closure: verificado em `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md` — evidência de código/widget + nota de verificação humana/browser; caveats/ambiente documentados)*
- [x] **ADMN-11**: Login admin persiste sessão com token Bearer JWT em header Authorization — teste em rotas protegidas *(Phase 11 gap closure: verificado em `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md`; ver também traceabilidade reparada em `08-03-SUMMARY.md` / `CONTEXT-SUMMARY.md`)*
- [x] **ADMN-12**: Rota `/auth/login` protege contra credential stuffing com rate limit Turnstile server-side — SECR-03 estendida *(Phase 11 gap closure: evidência/traceabilidade em `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md`, `08-03-SUMMARY.md`, `CONTEXT-SUMMARY.md`)*

### Ingestão & Extração (continuado)

- [ ] **EXTR-10**: Admin cola texto com vagas → extração bem-sucedida em chunks ≤6K tokens — nenhum job perdido por truncamento
- [ ] **EXTR-11**: Cada vaga extraída valida ao menos um contato (email ou telefone) antes de entrar no banco — regra de negócio enforcada
- [ ] **EXTR-12**: Fallback de modelo Groq: se modelo primary falha com 404/deprecatção, retry com modelo secondary via `GROQ_MODEL` cadeia — nunca saída silenciosa vazia

### Revisão Admin (continuado)

- [x] **REVW-10**: Admin aprova vaga → status muda de `pending` para `published` — vaga aparece imediatamente na home pública *(Phase 11 gap closure: verificado em `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md` — evidência de código/fluxo + nota de verificação humana/browser para UX imediata)*
- [x] **REVW-11**: Admin edita campos de uma vaga pelo ID — campos modificados persistidos com validação de contato *(Phase 11 gap closure: verificado em `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md`)*
- [x] **REVW-12**: Admin exclui vaga — remoção hard do banco; operação idempotente (exclusão duplicada é no-op) *(Phase 11 gap closure: evidência em `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md` com mapeamento explícito `repeat delete returns 404 (idempotent-in-effect) -> exclusão duplicada é no-op`; traceabilidade em `08-03-SUMMARY.md` / `CONTEXT-SUMMARY.md`)*

### Board Público (continuado e finalizado)

- [ ] **PUBL-10**: Visitante lista vagas publicadas em grade responsiva mobile-first, sem cadastro ou login — todas as features v1.0 funcionais
- [ ] **PUBL-11**: Card mostra title, início das activities (expansível), salary (se houver) e botão "Ver a vaga" — mobile-first, toque-friendly
- [ ] **PUBL-12**: Modal de detalhes completo, mobile-friendly — focus trap, scroll-lock, safe-area insets; contato oculto por padrão
- [ ] **PUBL-13**: Contato fica oculto por padrão e é revelado pelo botão "Mostrar contato" — Turnstile server-side verify obrigatório, single-use token
- [ ] **PUBL-14**: Visitante se candidata via WhatsApp (`wa.me`) e/ou email a partir do detalhe da vaga — links gerados corretamente com DDD + número

### Busca & Filtros (continuado e finalizado)

- [ ] **SRCH-10**: Busca por palavra-chave é insensível a acento e caixa — "sao paulo" == "São Paulo" e "analista" == "Analista"
- [ ] **SRCH-11**: Filtro por cidade: São Paulo, Rio de Janeiro, Belo Horizonte, Remoto — chips persistentes na URL
- [ ] **SRCH-12**: Ordenação por data de publicação (mais recentes por padrão; crescente/decrescente) — estado persiste na URL

### Anti-spam & Segurança (continuado)

- [x] **SECR-10**: Turnstile site key inline no bundle — mudança de chave no painel Cloudflare requer rebuild do frontend — flag de threat operacional *(Phase 11 gap closure: verificado com caveat operacional em `.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md`; `NEXT_PUBLIC_TURNSTILE_SITE_KEY` é embutida no bundle em build time e exige rebuild/redeploy ao trocar a chave)*
- [x] **SECR-11**: Rate limiting por IP no endpoint de reveal e login — slowapi knobs REVEAL_RATE_LIMIT=10/min e LOGIN_RATE_LIMIT=5/min — configurados via env *(Phase 11 gap closure: evidência em `.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md`)*
- [x] **SECR-12**: Endpoint `/admin/expire` autenticado por header `X-Cron-Secret` — fail-closed: 503 quando header ausente/incorreto *(Phase 12 reconciliation — split ownership preservada: lado Phase 7 verificado em `.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md`; lado Phase 9 (`/admin/expire` X-Cron-Secret-only, fail-closed 503 quando não configurado/ausente/incorreto, T-06-01) verificado em `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md`. Phase 13 fecha o resíduo de alinhamento/evidência ops canônica (deploy/hosts) com mapeamento canônico↔legado e matriz D-10 em `docs/DEPLOY.md` (linhas de cron fail-closed/idempotência `X-Cron-Secret`, T-06-01 preservado), sem reabrir contrato; execução real em hosts canônicos pendente / handoff operacional documentado quando aplicável. Sem alegação além de código/contrato reconciliado e evidência ops mapeada/registrada.)*

### Ciclo de Vida (continuado e finalizado)

- [x] **LIFE-10**: Vagas recebem `expires_at` = `created_at` + 14 dias — server_default no modelo e migration verificado *(Phase 12 reconciliation: DB-owned `expires_at = created_at + 14 days` (`timestamptz`, `server_default`, index) verificado em `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md`)*
- [x] **LIFE-11**: Job agendado faz hard delete de vagas `published` expiradas, de forma idempotente e em UTC — APScheduler em processo FastAPI *(Phase 12 reconciliation: sweep hard-delete status-agnostic/idempotente orientado pelo relógio do banco verificado em `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md`)*
- [x] **LIFE-12**: Vagas `pending` não revisadas também expiram após 14 dias — mesma regra de 14 dias aplicada *(Phase 12 reconciliation: expiração de `pending` e demais status pela mesma regra de 14 dias verificada em `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md`)*
- [x] **LIFE-13**: Expiração disparada por endpoint protegido por `CRON_SECRET`, com passe de recuperação (catch-up) — endpoint `/admin/expire` aceita somente `X-Cron-Secret` (Bearer JWT admin NÃO é aceito - T-06-01) *(Phase 12 reconciliation — split ownership preservada: lado code/contract (`/admin/expire` aceita somente `X-Cron-Secret`, Bearer JWT admin não aceito, T-06-01, fail-closed/idempotente) verificado em `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md`. Phase 13 fecha o resíduo de alinhamento/evidência ops canônica (deploy/hosts) com mapeamento canônico↔legado e matriz D-10 em `docs/DEPLOY.md` (catch-up `/admin/expire`, idempotência, `X-Cron-Secret`, T-06-01 preservado), sem reabrir contrato; execução real em hosts canônicos pendente / handoff operacional documentado quando aplicável.)*

### Tema & UI (continuado e finalizado)

- [ ] **UIUX-10**: Tema dark minimalista roxo com contraste WCAG AA — texto em `#a78bfa` sobre fundo `#1a1025`; botão Doações amarelo `#facc15` discreto, efeito apenas no hover
- [ ] **UIUX-11**: Botão "Doações" no canto superior direito (amarelo `#facc15`), discreto, hover apenas — posição top-right, visível em mobile
- [ ] **UIUX-12**: Espaços reservados para ADS futuros (banner topo + sidebar + entre cards) — placeholders implementados no layout, sem AD real ainda

### Confiança & Legal (continuado e finalizado)

- [x] **TRST-10**: Páginas de privacidade, termos e aviso "somos apenas meio de divulgação" (LGPD) — existentes e acessíveis em `/privacidade` e `/termos-de-uso`
- [x] **TRST-11**: Visitante pode denunciar uma vaga — endpoint `/jobs/{id}/report` aceita motivo opcional (máx 500 chars), emite logs estruturados sem persistir reports *(Phase 12 reconciliation: report endpoint com motivo opcional (máx 500 chars), logs estruturados, sem persistência e com throttling/comportamento verificado em `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md`)*
- [x] **TRST-12**: Badge "Vaga revisada" aparece em vaga com status `published` e aprovada pelo master — deriva apenas de status=published no JobCard e JobDetailDialog

### Rebranding & Branding (novo para v1.1)

- [x] **BRND-01**: Aplicativo renomeado de "NaoQueroUsar" para "EmpregaNoix" em todo o frontend (textos, labels, headings, meta tags)
- [x] **BRND-02**: Slogan mantido "Procurar um emprego, não deve dar trabalho" — atualizado para refletir a nova marca
- [x] **BRND-03**: Cores da marca mantidas (roxo #8b5cf6 / #a78bfa, amarelo #facc15 para doações) — consistência visual em todo o app
- [x] **BRND-04**: Domínio e hosts atualizados — backend `https://empreganoix.onrender.com`, frontend `https://empreganoix.vercel.app`; CORS configurado para origens EmpregaNoix *(Phase 13 — alinhamento contratual canônico de host/env/CORS/API fechado com evidência em `docs/DEPLOY.md`: state-alvo canônico `https://empreganoix.vercel.app` / `https://empreganoix.onrender.com`, mapeamento canônico↔legado/histórico e matriz D-10 cobrindo health/env/Turnstile, preflight CORS, `/admin/expire` auth/idempotência (fail-closed, `X-Cron-Secret`, T-06-01 preservado) e superfícies públicas/admin chave. Execução real em hosts canônicos pendente / handoff operacional documentado em `docs/DEPLOY.md`; alvo contratual mantido sem troca silenciosa por hosts legados.)*

## v1.1 Summary

- **v1.1 requirements total**: 28 total
- **Mapped to phases**: 28 (100%)
- **Unmapped**: 0 ✓

**Per Phase (original v1.1 mapping):**
- Phase 3 — Contact Reveal & Anti-Spam: SECR-10, SECR-11, SECR-12, LIFE-10, LIFE-11, LIFE-12, PUBL-10..14, SRCH-10..12 (13 requirements)
- Phase 5 — Admin Review Area: ADMN-10..12, REVW-10..12, PUBL-10..14 (9 requirements)
- Phase 6 — Lifecycle, Trust, Legal & Launch: LIFE-10..13, TRST-10..12, BRND-01..04 (9 requirements)

**Gap Closure (audit 2026-11-15, `.planning/v1.1-MILESTONE-AUDIT.md`):**
- Phase 11 — Verify Phases 7–8 & Close Reveal/Admin/Review Evidence Gaps: SECR-10, SECR-11, SECR-12, ADMN-10, ADMN-11, ADMN-12, REVW-10, REVW-11, REVW-12 (status reset to Pending/unverified pending verification backfill)
- Phase 12 — Reconcile Phase 9 Lifecycle/Trust Verification & Contracts: LIFE-10, LIFE-11, LIFE-12, LIFE-13, TRST-11, SECR-12 (reconciled in `09-VERIFICATION.md`/traceability; residual canonical-host/deploy evidence for LIFE-13/SECR-12 closed in Phase 13 ops alignment/mapeamento)
- Phase 13 — Canonical Host, Deploy & Ops Alignment (BRND-04 closeout): BRND-04, SECR-12, LIFE-13 fechados para alinhamento contratual/ops com evidência mapeada em `docs/DEPLOY.md` (state-alvo canônico, mapeamento canônico↔legado, matriz D-10, handoff), preservando histórico de verificação anterior e T-06-01; execução real em hosts canônicos pendente / handoff operacional documentado quando aplicável (sem swap silencioso do canônico)

*Note: Phase 7–10 in ROADMAP supersede earlier phase numbering references for v1.1 execution; gap closure phases 11–13 address remaining audit verification/contract/ops gaps.*

---

*Requirements defined: 2026-11-12*
*Last updated: 2026-11-15 after Phase 13 canonical host/deploy & ops alignment (BRND-04/SECR-12/LIFE-13 closed for ops-scope alignment with evidence in `docs/DEPLOY.md`; prior verification history and T-06-01 preserved; execução real em hosts canônicos pendente / handoff operacional documentado quando aplicável)*