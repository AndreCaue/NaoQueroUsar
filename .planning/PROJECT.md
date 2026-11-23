# EmpregaNoix

## Current State

**Latest shipped milestone:** v1.4 Polimento UX e Admin — **shipped 2026-11-23** (audit `tech_debt`, 6/6 requirements satisfied, 3/3 phases, 4/4 E2E flows, no critical blockers; tech debt accepted).
**Archives:** `.planning/milestones/v1.4-ROADMAP.md`, `.planning/milestones/v1.4-REQUIREMENTS.md`, `.planning/milestones/v1.4-MILESTONE-AUDIT.md`

**Previous milestones:**
- v1.3 Chatbot Inteligente de Busca de Vagas — shipped 2026-11-22 (`.planning/milestones/v1.3-ROADMAP.md`, `.planning/milestones/v1.3-REQUIREMENTS.md`, `.planning/milestones/v1.3-MILESTONE-AUDIT.md`)
- v1.2 Integração com Facebook Pages — shipped 2026-11-17 (`.planning/milestones/v1.2-ROADMAP.md`, `.planning/milestones/v1.2-REQUIREMENTS.md`)
- v1.1 EmpregaNoix — shipped 2026-11-15 (`.planning/milestones/v1.1-ROADMAP.md`, `.planning/milestones/v1.1-REQUIREMENTS.md`, `.planning/milestones/v1.1-MILESTONE-AUDIT.md`)

**v1.4 delivered:** Polimento de UX pública e fluxo admin sem perder fricção zero: login admin dedicado em `/admin/login` com redirect seguro/guard/logout/401 alinhados e entrada discreta na Política de Privacidade; controles por ambiente para anúncios e doações com validação segura; e home com `available_cities` dinâmico (published/non-expired, independente de filtros), chips de cidade ativos, limpeza de cidade obsoleta, dropdown de ordenação acessível e hover visual consistente em chips/cards/dropdown.

**Known accepted residuals (v1.4):** Phase 26 live Turnstile+backend browser smoke pending (`26-HUMAN-UAT.md`, `26-VERIFICATION.md` human_needed; code paths verified). Phase 28 VERIFICATION frontmatter human_needed but human UAT acknowledged (2026-11-22, 5/5 passed). Integration warning: `frontend/app/admin/integracoes/IntegrationsClient.tsx` missing 401 handler clearing `nqu_admin_token` and redirecting via `buildAdminLoginHref(path+search)`. Nyquist partial in Phases 26/27/28. Known deferred items at close: 7 (see `STATE.md` Deferred Items), including v1.3 CL-02 quick-task heuristic residuals.

## Current Milestone: v1.5 Integração Instagram na Revisão

**Goal:** Permitir publicar cada vaga aprovada também no Instagram, com legenda configurada na etapa de revisão, reaproveitando a base Meta/Facebook existente e mantendo as publicações independentes.

**Target features:**
- Seção Instagram na etapa de revisão ao lado do Facebook: toggle por vaga, legenda editável pré-preenchida, contador 2.200, aviso >30 hashtags, preview de imagem e status por plataforma
- Imagem obrigatória para Instagram: origem a definir (logo/card gerado/upload); fallback card padrão 1080x1080 ou 1080x1350 JPEG servido por URL pública acessível pela Meta
- Publicação via Instagram Graph API (Content Publishing) em 2 passos (container + publish), com checagem de status quando necessário; obter/armazenar `ig-user-id` a partir da Página Facebook vinculada, reaproveitando token existente
- Pipeline assíncrono, retry/backoff e idempotência, desacoplado do Facebook (falha de um não bloqueia o outro)
- Persistência/observabilidade: legenda usada, post id, permalink, status, erro, timestamps; tratamento de rate limit e limite diário; tokens/IDs via env; logs sem tokens; tratar expiração de token
- Qualidade: testes unitários/integração mockada, checklist manual Meta documentado; sem regressão no fluxo Facebook

**Out of scope (v1.5):** Stories/Reels/carrossel, agendamento, métricas/analytics, responder comentários/DMs, múltiplas contas Instagram.

**Constraints/guardrails:**
- Conta Instagram Business/Creator vinculada à Página Facebook
- Links na legenda não são clicáveis (CTA tipo "link na bio")
- Antes de implementar, confirmar documentação/permissões/limites Meta atuais; mapear permissões/App Review (ex.: instagram_basic, instagram_content_publish, pages_show_list, pages_read_engagement)
- Reaproveitar padrões existentes (app Meta, tokens, service, fila/jobs, modelo, review UI, erros/logs); sem novas abstrações desnecessárias

**Decisões em aberto (resolver no discuss-phase):**
- Origem da imagem (logo da empresa / card gerado a partir da vaga / upload na revisão)
- Formato/template/armazenamento/serving do card gerado (proporção, onde armazenar e servir)
- Biblioteca/estratégia de geração de imagem, se aplicável
- Estratégia de renovação ou alerta de expiração do token

**Candidate carry-over (evaluate during scoping/execution):**
- v1.4 tech debt: IntegrationsClient 401 recovery alignment (ADMN-01 robustness), Phase 26 live smoke, Nyquist partial 26/27/28.
- v1.3 residuals: CL-02 audit-open heuristic residual, D-14/WR-02 focus trap, runtime/browser deferments by item, Nyquist 21/22/23/25 partial, `23-06/23-07` PLANs without SUMMARYs.
- v1.2 carry-over: `PUB-01..08` traceability reconciliation, `TEST-04/DOC-01/AUD-05` handoffs.
- v1.1 carry-over: EXTR/PUBL/SRCH/UIUX caveats, canonical live smoke, DB-backed test reproducibility.

## What This Is

Plataforma pública de busca de emprego cujo diferencial é eliminar a burocracia de cadastro: qualquer pessoa vê as vagas e o contato **sem criar conta, sem login e sem etapas intermediárias**. Um board enxuto, dark mode e mobile-first, curado manualmente por um único administrador (o master), que transforma textos brutos de grupos de vagas em cards estruturados.

Slogan: "Procurar um emprego, não deve dar trabalho"

## Core Value

Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

## Requirements

### Validated

- ✓ Admin solo acessa área protegida por senha (via `.env`) / JWT — Validated in Phase 1 (ADMN-01/02/03)
- ✓ Fundação social de integração Facebook (modelos/migração `social_*`, crypto Fernet de tokens, contrato `SocialPublisher`/stub Facebook, config/env `.env.example`) — Validated in Phase 14 (SOC-01..SOC-06)
- ✓ OAuth Meta e Integrações no admin (conectar/desconectar/status, `state` anti-CSRF, troca/validação de tokens, seleção de página única, alertas de reconexão) — Validated in Phase 15 (META-01..META-06)
- ✓ Geração, revisão e aprovação do post social (draft LLM/fallback, edição/regeneração/preview, agendamento BRT, approve site-first com registro social best-effort/imutável, política/link público) — Validated in Phase 16 (POST-01..POST-06; human/UAT items noted)
- ✓ Pipeline assíncrono de publicação social com status/retry no admin (worker/cron, claim/lock, retry/backoff, idempotência, visibilidade/ações operacionais) — Implemented in Phase 17 (UI-01..UI-02 complete; `PUB-01..08` traceability reconciliation pending in archive)
- ✓ Contrato de intenção pt-BR + mapeamento determinístico seguro para busca pública (`q`, cidade whitelist SP/RJ/BH/Remoto, `sort`), classificação auditável por campo e seam Groq isolado com fallback seguro — Validated in Phase 19 (INT-01/02/03)
- ✓ Endpoint público de chat-search resiliente (`POST /api/v1/public/chat-search`) com interpretação transparente, busca determinística equivalente (`list_published`/`JobPublic`, sem contatos), proteções (rate limit/validação/timeout) e fallback 200 degradado seguro com sinalização de suporte parcial — Validated in Phase 20 (API-01/02/03)
- ✓ Interface de chat no board público (drawer/modal mobile-first), sem login, com interpretação/parâmetros/limitações, resultados públicos com detalhe/reveal canônico e apply-to-board canônico — Validated in Phase 21 (UI-01/02/03), UAT reconciliado
- ✓ Qualidade/hardening/validação operacional do chatbot: exemplos MVP validados/documentados, testes automatizados com LLM mockado + UI viável, kill-switch/status/logging sem PII sensível, 22-SECURITY.md — Validated in Phase 22 (QA-01/02/03) com deferimentos runtime/browser aceitos por item
- ✓ Fechamento de auditoria v1.3: CL-01..CL-05 reconciliados com evidência/aceite formal; CR-01/WR-03/WR-01 viável fechados; audit `tech_debt` sem blockers críticos — Validated in Phases 23-25 (CL-01..05)
- ✓ Login admin dedicado em `/admin/login`, separado do paste/revisão, com redirect seguro `next`, guard/logout/401 alinhados para `/admin/login` — Validated in Phase 26 (ADMN-01; human smoke recorded in 26-HUMAN-UAT.md)
- ✓ Entrada admin discreta na Política de Privacidade apontando para `/admin/login` — Validated in Phase 26 (ADMN-02; human smoke recorded in 26-HUMAN-UAT.md)
- ✓ Controles por ambiente para anúncios e doações (flag única de ads + URL de doação http/https com fallback seguro para `/doacoes`) — Validated in Phase 27 (ADS-01, DONA-01)
- ✓ Filtro de cidades na home mostra apenas cidades com vagas publicadas/ativas no momento — Validated in Phase 28 (CITY-01)
- ✓ Hover/feedback visual em dropdown recentes/antigos, cards e filtros de cidades — Validated in Phase 28 (UIUX-01)

### Active

None yet — requirements for v1.5 will be defined in `.planning/REQUIREMENTS.md` during milestone initialization.

### Out of Scope

- Instagram, geração de imagem, sincronização de edição/remoção do post, múltiplas Páginas, métricas/insights de engajamento — fora do milestone v1.2 (arquitetura deve prever extensão)
- Login/cadastro de usuário comum — secundário e opcional, não entra no MVP (o diferencial é justamente não exigir conta)
- Renovação de vagas expiradas — fora de escopo; expiração é definitiva (ciclo completo)
- Controle de duplicidade de vagas — não previsto; curadoria manual cobre
- Múltiplos administradores / papéis de usuário — apenas o master posta/aprova
- Monetização ativa (doações reais e ADS contratados) — baixa prioridade; apenas o botão e os placeholders no MVP
- Submissão pública de vagas por terceiros — não no MVP
- LLM ler/rankear centenas de vagas (corpus no prompt) — custo/latência/alucinação; LLM apenas extrai parâmetros
- Memória de conversa longa/histórico persistente avançado — fora do MVP v1.3
- Recomendação personalizada baseada em perfil do usuário — requer identidade/dados adicionais
- Aplicação automática em vagas / integração LinkedIn/WhatsApp — fora do MVP
- Expor contatos no payload do chat — viola fluxo atual de revelação

## Context

- **Origem das vagas:** textos soltos e brutos compartilhados em grupos de WhatsApp/Telegram. A extração por LLM precisa lidar com texto desestruturado, múltiplas vagas por mensagem, emojis e formatação inconsistente.
- **Volume esperado:** 100–500 vagas publicadas por mês — curadoria manual é viável, mas o fluxo de colar → extrair → revisar → publicar precisa ser rápido.
- **Custo:** operar próximo de zero usando tiers gratuitos (Neon Postgres, Groq, Vercel, Cloudflare Turnstile).
- **Público:** candidatos brasileiros (foco inicial em SP, RJ, BH e Remoto), majoritariamente mobile.
- **Motivação central:** a principal frustração com sites de emprego atuais é a burocracia de cadastro/login para sequer ver uma vaga.
- **Riscos conhecidos / estado atual:** revisão manual do master como gate de qualidade; mitigação de scraping via ocultação + Turnstile; pendências operacionais/evidências carry-over (v1.1/v1.2/v1.3) e residuals v1.4 aceitos documentados nos archives/audits.

## Constraints

- **Tech stack — Frontend:** Next.js 16 (App Router, `16.4.6`) + Tailwind CSS + dark mode — decisão fixada pelo usuário (major subida de 15 → 16 em 2026-11-11 por exigência de segurança do build Vercel)
- **Tech stack — Backend:** FastAPI (Python) — decisão fixada pelo usuário
- **Banco:** Neon (Postgres gratuito) — decisão fixada pelo usuário
- **LLM de extração:** Groq, modelo gratuito — `openai/gpt-oss-20b` (padrão) com `openai/gpt-oss-120b` como fallback, via env `GROQ_MODEL`
- **Anti-spam:** Cloudflare Turnstile (gratuito) — decisão fixada pelo usuário
- **Deploy:** Vercel (frontend) + local inicialmente; depois Railway/Render (backend) — decisão fixada pelo usuário
- **Idioma/Locale:** Português (Brasil), datas e textos em pt-BR
- **Design:** dark mode minimalista; roxo principal (#8b5cf6 / #a78bfa); fundos escuros (#0f0a1a / #1a1025); botão Doações amarelo (#facc15) discreto
- **Operação:** admin único (master); sem multiusuário

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Sem cadastro/login para ver vagas e contato | Elimina a maior frustração com sites atuais (burocracia) | ✓ Good (core value mantido) |
| Hard delete após 14 dias | Mantém o board limpo e o custo de armazenamento baixo | ⚠️ Revisit (contrato/semântica reconciliados em v1.1; validar operação em produção canônica) |
| Extração via LLM (Groq) + revisão manual obrigatória | Automação do trabalho pesado sem abrir mão do controle de qualidade | ⚠️ Revisit (aceitação EXTR-10/11/12 não fechada no audit v1.1) |
| Repo git dedicado no diretório do projeto | O diretório está dentro do repo da home; isolamento evita poluir histórico | ✓ Good |
| Contato revelado no clique (client-side) | Reduz scraping com fricção mínima ao usuário | ⚠️ Revisit (v1.1 endureceu reveal server-side/Turnstile; evidências runtime/browser ainda caveatadas) |
| Servir contato via endpoint dedicado (não no payload público) | Ocultação client-side sozinha não protege contra scraping; exigido Turnstile server-side no reveal | ✓ Good (direção implementada/reconciliada; validar em runtime canônico) |
| Substituir Llama aposentados por Groq `gpt-oss` | `llama-3.1-8b-instant`/`llama-3.3-70b` desativados em 2026-08-16; `openai/gpt-oss-*` suporta structured outputs estritos | ✓ Good |
| Usar `bcrypt` direto (sem passlib) para hash de senha | `passlib` 1.7.4 é incompatível com o `bcrypt` 5.0.0 travado; a decisão de auth permite bcrypt diretamente | ✓ Good |
| Chat NL usa LLM só para extração de parâmetros; busca determinística reutiliza `list_published`/`JobPublic` | Evita custo/latência/alucinação de enviar corpus ao LLM; preserva contrato público sem contatos | ✓ Good (v1.3) |
| Campos não nativos no chat tratados como limitado/aproximado e sinalizado | Evita afirmar filtragem inexistente e mantém honestidade de produto | ✓ Good (v1.3) |
| Residuals de fechamento v1.3 aceitos explicitamente (CL-02 heuristic, D-14/WR-02, deferimentos runtime/Nyquist parcial) | Fecha milestone com rastreabilidade sem fabricar evidência | ⚠️ Revisit (acompanhar em milestone futuro se necessário) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-11-23 after v1.5 milestone start (Integração Instagram na Revisão)*