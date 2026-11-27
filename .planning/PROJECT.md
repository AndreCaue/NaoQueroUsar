# EmpregaNoix

## Current State

**Latest shipped milestone:** v1.5 Integração Instagram na Revisão — **shipped 2026-11-27** (audit `tech_debt`, 17/17 requirements satisfied, 5/5 phases, 11/11 plans, 17/17 integration, 4/4 E2E flows, no critical blockers; tech debt accepted).
**Archives:** `.planning/milestones/v1.5-ROADMAP.md`, `.planning/milestones/v1.5-REQUIREMENTS.md`, `.planning/milestones/v1.5-MILESTONE-AUDIT.md`

**Previous milestones:**

- v1.4 Polimento UX e Admin — shipped 2026-11-23 (`.planning/milestones/v1.4-ROADMAP.md`, `.planning/milestones/v1.4-REQUIREMENTS.md`, `.planning/milestones/v1.4-MILESTONE-AUDIT.md`)
- v1.3 Chatbot Inteligente de Busca de Vagas — shipped 2026-11-22 (`.planning/milestones/v1.3-ROADMAP.md`, `.planning/milestones/v1.3-REQUIREMENTS.md`, `.planning/milestones/v1.3-MILESTONE-AUDIT.md`)
- v1.2 Integração com Facebook Pages — shipped 2026-11-17 (`.planning/milestones/v1.2-ROADMAP.md`, `.planning/milestones/v1.2-REQUIREMENTS.md`)
- v1.1 EmpregaNoix — shipped 2026-11-15 (`.planning/milestones/v1.1-ROADMAP.md`, `.planning/milestones/v1.1-REQUIREMENTS.md`, `.planning/milestones/v1.1-MILESTONE-AUDIT.md`)

**v1.5 delivered:** Publicação Instagram por vaga na etapa de revisão, desacoplada do Facebook e com segurança operacional: prontidão Meta/IG confirmável (conta vinculada, `ig-user-id`, estados acionáveis) e base de mídia pública HTTPS com card fallback determinístico 1080x1350; seção Instagram no diálogo de revisão com toggle por vaga, legenda editável (Template C, `N/2200`, aviso >30 hashtags, CTA “link na bio”), preview da imagem exata e bloqueio aplicável só ao Instagram; pipeline assíncrono Graph 2 passos (container/status/publish) com isolamento FB/IG, reconciliação de ambiguidade sem retry cego, rate/content limit acionável sem retry storm e auditoria/status seguros; hardening automatizado (HARD-01 + regressão FB) e runbook operacional Meta/IG/Facebook com handoffs live explícitos.

**Known accepted residuals (v1.5):** Live Meta confirmations pending (IG readiness real em `/admin/integracoes`, public HTTPS media reachability pela Meta com `MEDIA_PUBLIC_BASE_URL`, OAuth reconnect para escopos IG). Nyquist PARTIAL/MISSING em fases 30/31/32/33 (advisory). Phase 32 live Meta/App Review/roles/tasks/Advanced Access handoff remains by design; 32-HUMAN-UAT 4/4 recorded but no new live Meta execution in Phase 33. Deferred items acknowledged at close: 7 (see `STATE.md` Deferred Items) — includes v1.3 CL-02 quick-task heuristic residuals re-acknowledged and Phase 29/31 UAT/verification gaps.

## Next Milestone Goals

No next milestone scoped yet. Use `/gsd-new-milestone` to define goals, research, requirements, and roadmap.

## What This Is

Plataforma pública de busca de emprego cujo diferencial é eliminar a burocracia de cadastro: qualquer pessoa vê as vagas e o contato **sem criar conta, sem login e sem etapas intermediárias**. Um board enxuto, dark mode e mobile-first, curado manualmente por um único administrador (o master), que transforma textos brutos de grupos de vagas em cards estruturados.

Slogan: "A Oportunidade é Nossa!"

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
- ✓ Prontidão Instagram confirmável em Integrações (conta IG vinculada, `ig-user-id`, estados acionáveis de reconexão/correção) — Validated in Phase 29 (META-01)
- ✓ Backend resolve/persiste `ig-user-id` reaproveitando fluxo/token Meta com erro seguro sem quebrar Facebook — Validated in Phase 29 (META-02)
- ✓ Documentação/checklist operacional Meta/Instagram (permissões/escopos, App Review/roles/tasks, setup/verificação) — Validated in Phase 29 (META-03)
- ✓ Contrato de validação/preparação de imagem Instagram com feedback pt-BR, bloqueio aplicável só ao Instagram (enforcement review/publish em 30/31) — Validated in Phase 29 (IMAG-01)
- ✓ Card fallback determinístico 1080x1350 JPEG compatível com Instagram, proveniência/versionamento — Validated in Phase 29 (IMAG-02)
- ✓ Imagem por URL pública HTTPS estável/acessível pela Meta, com validação/preview/proveniência — Validated in Phase 29 (IMAG-03)
- ✓ Publicação Instagram assíncrona e independente do Facebook (falha isolada por plataforma) — Validated in Phase 31 (PUBL-01)
- ✓ Publicação Instagram via Graph API 2 passos (container/status/publish) com timeout/erro seguro — Validated in Phase 31 (PUBL-02)
- ✓ Status/auditoria por plataforma com IDs/permalink/timestamps/erros seguros, sem tokens — Validated in Phase 31 (PUBL-03)
- ✓ Ambiguidade/retry sem duplicação cega; reconciliação antes de nova tentativa automática — Validated in Phase 31 (PUBL-04)
- ✓ Rate limit/limite diário Instagram tratados com segurança, estado acionável, sem retry storm — Validated in Phase 31 (PUBL-05)
- ✓ Hardening automatizado Instagram/Facebook: cenários HARD-01 cobertos por pytest rastreável (draft/validação IG, idempotência, retry, ambiguidade, rate limit, mapeamento de erros, FB regression gate) — Validated in Phase 32 (HARD-01; automated gate green, live Meta handoff pending)
- ✓ Documentação operacional Meta/Instagram/Facebook: env vars canônicas, checklist handoff Meta, expiração/reconexão/rotação, troubleshooting IG acionável — Validated in Phase 32 (HARD-02; doc/env/test evidence, live handoff pending)
- ✓ Seção Instagram na revisão com toggle por vaga e status independente por plataforma — Validated in Phase 30/33 (REVW-01; reconciled in Phase 33 with objective evidence)
- ✓ Legenda Instagram editável/preenchida a partir da vaga com contador `N/2200` e bloqueio >2200 — Validated in Phase 30 (REVW-02)
- ✓ Aviso de >30 hashtags e orientação CTA “link na bio” (links não clicáveis) na legenda Instagram — Validated in Phase 30 (REVW-03)
- ✓ Preview da imagem exata pretendida para publicação Instagram antes de aprovar/publicar — Validated in Phase 30 (REVW-04)

### Active

None yet — define with `/gsd-new-milestone`.

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

| Decision                                                                                                                | Rationale                                                                                                                | Outcome                                                                                               |
| ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| Sem cadastro/login para ver vagas e contato                                                                             | Elimina a maior frustração com sites atuais (burocracia)                                                                 | ✓ Good (core value mantido)                                                                           |
| Hard delete após 14 dias                                                                                                | Mantém o board limpo e o custo de armazenamento baixo                                                                    | ⚠️ Revisit (contrato/semântica reconciliados em v1.1; validar operação em produção canônica)          |
| Extração via LLM (Groq) + revisão manual obrigatória                                                                    | Automação do trabalho pesado sem abrir mão do controle de qualidade                                                      | ⚠️ Revisit (aceitação EXTR-10/11/12 não fechada no audit v1.1)                                        |
| Repo git dedicado no diretório do projeto                                                                               | O diretório está dentro do repo da home; isolamento evita poluir histórico                                               | ✓ Good                                                                                                |
| Contato revelado no clique (client-side)                                                                                | Reduz scraping com fricção mínima ao usuário                                                                             | ⚠️ Revisit (v1.1 endureceu reveal server-side/Turnstile; evidências runtime/browser ainda caveatadas) |
| Servir contato via endpoint dedicado (não no payload público)                                                           | Ocultação client-side sozinha não protege contra scraping; exigido Turnstile server-side no reveal                       | ✓ Good (direção implementada/reconciliada; validar em runtime canônico)                               |
| Substituir Llama aposentados por Groq `gpt-oss`                                                                         | `llama-3.1-8b-instant`/`llama-3.3-70b` desativados em 2026-08-16; `openai/gpt-oss-*` suporta structured outputs estritos | ✓ Good                                                                                                |
| Usar `bcrypt` direto (sem passlib) para hash de senha                                                                   | `passlib` 1.7.4 é incompatível com o `bcrypt` 5.0.0 travado; a decisão de auth permite bcrypt diretamente                | ✓ Good                                                                                                |
| Chat NL usa LLM só para extração de parâmetros; busca determinística reutiliza `list_published`/`JobPublic`             | Evita custo/latência/alucinação de enviar corpus ao LLM; preserva contrato público sem contatos                          | ✓ Good (v1.3)                                                                                         |
| Campos não nativos no chat tratados como limitado/aproximado e sinalizado                                               | Evita afirmar filtragem inexistente e mantém honestidade de produto                                                      | ✓ Good (v1.3)                                                                                         |
| Residuals de fechamento v1.3 aceitos explicitamente (CL-02 heuristic, D-14/WR-02, deferimentos runtime/Nyquist parcial) | Fecha milestone com rastreabilidade sem fabricar evidência                                                               | ⚠️ Revisit (acompanhar em milestone futuro se necessário)                                             |
| Publicação Instagram desacoplada do Facebook (site-first/best-effort, isolamento por provider) | Falha/rate-limit/ambiguidade em uma plataforma não pode bloquear nem corromper a outra; preserva contrato público e fluxo admin | ✓ Good (v1.5, PUBL-01/04/05) |
| Card fallback determinístico 1080x1350 JPEG + URL pública HTTPS versionada para mídia IG | Meta precisa de URL pública acessível; versionamento por hash evita mídia stale e mantém proveniência/preview exatos | ✓ Good (v1.5, IMAG-01/02/03) |
| Ambiguidade IG não dispara auto-retry cego; rate/content limit tratado como estado acionável | Evita duplicação acidental e retry storm; exige reconciliação segura antes de nova tentativa | ✓ Good (v1.5, PUBL-04/05) |
| Reconciliação de auditoria por evidência objetiva (Phase 33) | Fecha bookkeeping sem fabricar execução live; preserva histórico e separa handoffs operacionais | ✓ Good (v1.5) |

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

_Last updated: 2026-11-27 after v1.5 milestone completion (audit tech_debt; 17/17 requirements satisfied, 7 deferred items acknowledged)_
