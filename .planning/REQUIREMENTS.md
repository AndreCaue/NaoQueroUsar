# Requirements: EmpregaNoix — NQU v1.1

**Defined:** 2026-11-12
**Core Value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

## v1.1 Requirements

Requirements for this milestone continuation. Each maps to roadmap phases. Continuing from v1.0 REQ-IDs.

### Admin & Autenticação (continuado)

- [ ] **ADMN-10**: Admin vê indicador de Turnstile no login (widget interaction-only) — validação visual no clique
- [ ] **ADMN-11**: Login admin persiste sessão com token Bearer JWT em header Authorization — teste em rotas protegidas
- [ ] **ADMN-12**: Rota `/auth/login` protege contra credential stuffing com rate limit Turnstile server-side — SECR-03 estendida

### Ingestão & Extração (continuado)

- [ ] **EXTR-10**: Admin cola texto com vagas → extração bem-sucedida em chunks ≤6K tokens — nenhum job perdido por truncamento
- [ ] **EXTR-11**: Cada vaga extraída valida ao menos um contato (email ou telefone) antes de entrar no banco — regra de negócio enforcada
- [ ] **EXTR-12**: Fallback de modelo Groq: se modelo primary falha com 404/deprecatção, retry com modelo secondary via `GROQ_MODEL` cadeia — nunca saída silenciosa vazia

### Revisão Admin (continuado)

- [ ] **REVW-10**: Admin aprova vaga → status muda de `pending` para `published` — vaga aparece imediatamente na home pública
- [ ] **REVW-11**: Admin edita campos de uma vaga pelo ID — campos modificados persistidos com validação de contato
- [ ] **REVW-12**: Admin exclui vaga — remoção hard do banco; operação idempotente (exclusão duplicada é no-op)

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

- [ ] **SECR-10**: Turnstile site key inline no bundle — mudança de chave no painel Cloudflare requer rebuild do frontend — flag de threat operacional
- [ ] **SECR-11**: Rate limiting por IP no endpoint de reveal e login — slowapi knobs REVEAL_RATE_LIMIT=10/min e LOGIN_RATE_LIMIT=5/min — configurados via env
- [ ] **SECR-12**: Endpoint `/admin/expire` autenticado por header `X-Cron-Secret` — fail-closed: 503 quando header ausente/incorreto

### Ciclo de Vida (continuado e finalizado)

- [ ] **LIFE-10**: Vagas recebem `expires_at` = `created_at` + 14 dias — server_default no modelo e migration verificado
- [ ] **LIFE-11**: Job agendado faz hard delete de vagas `published` expiradas, de forma idempotente e em UTC — APScheduler em processo FastAPI
- [ ] **LIFE-12**: Vagas `pending` não revisadas também expiram após 14 dias — mesma regra de 14 dias aplicada
- [ ] **LIFE-13**: Expiração disparada por endpoint protegido por `CRON_SECRET`, com passe de recuperação (catch-up) — endpoint `/admin/expire` aceita header Bearer JWT admin ou `X-Cron-Secret`

### Tema & UI (continuado e finalizado)

- [ ] **UIUX-10**: Tema dark minimalista roxo com contraste WCAG AA — texto em `#a78bfa` sobre fundo `#1a1025`; botão Doações amarelo `#facc15` discreto, efeito apenas no hover
- [ ] **UIUX-11**: Botão "Doações" no canto superior direito (amarelo `#facc15`), discreto, hover apenas — posição top-right, visível em mobile
- [ ] **UIUX-12**: Espaços reservados para ADS futuros (banner topo + sidebar + entre cards) — placeholders implementados no layout, sem AD real ainda

### Confiança & Legal (continuado e finalizado)

- [ ] **TRST-10**: Páginas de privacidade, termos e aviso "somos apenas meio de divulgação" (LGPD) — existentes e acessíveis em `/privacidade` e `/termos-de-uso`
- [ ] **TRST-11**: Visitante pode denunciar uma vaga — endpoint `/jobs/{id}/report` aceita motivo opcional (máx 500 chars), emite logs estruturados sem persistir reports
- [ ] **TRST-12**: Badge "Vaga revisada" aparece em vaga com status `published` e aprovada pelo master — deriva apenas de status=published no JobCard e JobDetailDialog

### Rebranding & Branding (novo para v1.1)

- [ ] **BRND-01**: Aplicativo renomeado de "NaoQueroUsar" para "EmpregaNoix" em todo o frontend (textos, labels, headings, meta tags)
- [ ] **BRND-02**: Slogan mantido "Procurar um emprego, não deve dar trabalho" — atualizado para refletir a nova marca
- [ ] **BRND-03**: Cores da marca mantidas (roxo #8b5cf6 / #a78bfa, amarelo #facc15 para doações) — consistência visual em todo o app
- [ ] **BRND-04**: Domínio e hosts atualizados — backend `https://empreganoix.onrender.com`, frontend `https://empreganoix.vercel.app`; CORS configurado para origens EmpregaNoix

## v1.1 Summary

- **v1.1 requirements total**: 28 total
- **Mapped to phases**: 28 (100%)
- **Unmapped**: 0 ✓

**Per Phase:**
- Phase 3 — Contact Reveal & Anti-Spam: SECR-10, SECR-11, SECR-12, LIFE-10, LIFE-11, LIFE-12, PUBL-10..14, SRCH-10..12 (13 requirements)
- Phase 5 — Admin Review Area: ADMN-10..12, REVW-10..12, PUBL-10..14 (9 requirements)
- Phase 6 — Lifecycle, Trust, Legal & Launch: LIFE-10..13, TRST-10..12, BRND-01..04 (9 requirements)

---

*Requirements defined: 2026-11-12*
*Last updated: 2026-11-12 after milestone v1.1 EmpregaNoix definition*