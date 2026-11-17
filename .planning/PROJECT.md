# EmpregaNoix

## Current State

**Latest shipped milestone:** v1.2 Integração com Facebook Pages — **shipped 2026-11-17** (archived with **known gaps/handoffs accepted**; no v1.2 milestone audit).  
**Archives:** `.planning/milestones/v1.2-ROADMAP.md`, `.planning/milestones/v1.2-REQUIREMENTS.md`  
**Previous milestone:** v1.1 EmpregaNoix — shipped 2026-11-15 (`.planning/milestones/v1.1-ROADMAP.md`, `.planning/milestones/v1.1-REQUIREMENTS.md`, `.planning/milestones/v1.1-MILESTONE-AUDIT.md`)

**v1.2 delivered (with caveats):** fundação social segura (modelos/migrações/tokens criptografados/`SocialPublisher`), OAuth Meta e Integrações admin, geração/revisão/aprovação de post social (LLM/fallback, site-first), publicação assíncrona resiliente com retry/idempotência/status/retry no admin, e testes/docs/handoffs de fechamento rastreável. **Pendências aceitas:** reconciliação de rastreabilidade `PUB-01..08`, handoffs reais para `TEST-04`/`DOC-01`/`AUD-05`, verificações humanas/runtime/canônicas e débitos carry-over do v1.1.

**v1.3 in progress:** Phase 19 complete (contrato INT seguro). Phase 20 complete — endpoint público `POST /api/v1/public/chat-search` entregue com interpretação+resultados `JobPublic` pagináveis (sem contatos), busca determinística equivalente a `list_published` para `applied_params`, proteções/rate limit/timeout e fallback 200 degradado seguro com sinalização de suporte parcial (`API-01/02/03`). Restam UI de chat no board (Phase 21) e qualidade/hardening/validação operacional (Phase 22).

## Current Milestone: v1.3 Chatbot Inteligente de Busca de Vagas

**Goal:** Permitir que qualquer pessoa encontre vagas descrevendo o que procura em linguagem natural, com resposta rápida e sem fricção — reaproveitando a busca/filtros existentes e mantendo baixo custo operacional.

**Target features:**
- Extração de intenção/parâmetros em linguagem natural para JSON estruturado e validado (cargo/senioridade, cidade whitelist, modalidade, faixa salarial, tipo de contrato, palavras-chave, ordenação), sem inventar dados
- Aplicação dos parâmetros na busca pública existente (`GET /api/v1/public/jobs` / `crud.list_published`) com normalização segura; estratégia incremental para campos não nativos hoje (ex.: salário/modalidade/contrato via mapeamento textual/pós-filtro ou extensão controlada de filtros)
- Endpoint público de chat-search com proteção básica (rate limit/timeout) e respostas com interpretação + resultados (`JobPublic`, sem expor contatos no payload público)
- Interface de chat simples no frontend público (drawer/modal mobile-first) exibindo parâmetros entendidos e lista de vagas (título, empresa, local, salário quando disponível, acesso ao detalhe/link), suportando combinações de filtros
- Cobertura dos exemplos de uso do MVP definidos para o milestone (com lacunas explícitas documentadas quando um parâmetro não for totalmente suportado pelo backend atual)

**Carry-over/prioridades paralelas (se decidido em requisitos):** reconciliação `PUB-01..08`, handoffs `TEST-04/DOC-01/AUD-05`, lacunas v1.1 (EXTR/PUBL/SRCH/UIUX) e débitos operacionais/testes podem ser incluídos conforme escopo aprovado.

**Constraints mantidas:** acesso público sem login/fricção, operação admin única, falhas sociais nunca bloqueiam publicação do site. LLM não recebe centenas de vagas; apenas extrai parâmetros. Preferência por soluções gratuitas/baixo custo e boa performance.

## What This Is

Plataforma pública de busca de emprego cujo diferencial é eliminar a burocracia de cadastro: qualquer pessoa vê as vagas e o contato **sem criar conta, sem login e sem etapas intermediárias**. Um board enxuto, dark mode e mobile-first, curado manualmente por um único administrador (o master), que transforma textos brutos de grupos de vagas em cards estruturados.

Slogan: "Procurar um emprego, não deve dar trabalho"

## Core Value

Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

## Requirements

### Validated

<!-- Shipped and confirmed valuable (high-confidence, with noted caveats where applicable). -->

- [x] Admin solo acessa área protegida por senha (via `.env`) / JWT — Validated in Phase 1: Backend Foundation, Data & Admin Auth (ADMN-01/02/03)
- [x] Fundação social de integração Facebook (modelos/migração `social_*`, crypto Fernet de tokens, contrato `SocialPublisher`/stub Facebook, config/env `.env.example`) — Validated in Phase 14 (SOC-01..SOC-06)
- [x] OAuth Meta e Integrações no admin (conectar/desconectar/status, `state` anti-CSRF, troca/validação de tokens, seleção de página única, alertas de reconexão) — Validated in Phase 15 (META-01..META-06)
- [x] Geração, revisão e aprovação do post social (draft LLM/fallback, edição/regeneração/preview, agendamento BRT, approve site-first com registro social best-effort/imutável, política/link público) — Validated in Phase 16 (POST-01..POST-06; human/UAT items noted)
- [x] Pipeline assíncrono de publicação social com status/retry no admin (worker/cron, claim/lock, retry/backoff, idempotência, visibilidade/ações operacionais) — Implemented in Phase 17 (UI-01..UI-02 complete; `PUB-01..08` traceability reconciliation pending in archive)
- [x] Contrato de intenção pt-BR + mapeamento determinístico seguro para busca pública (`q`, cidade whitelist, sort explícito), classificação auditável por campo e seam Groq isolado com fallback seguro — Validated in Phase 19 (INT-01/02/03)
- [x] Endpoint público de chat-search resiliente (`POST /api/v1/public/chat-search`) com interpretação transparente, busca determinística equivalente (`list_published`/`JobPublic`, sem contatos), proteções (rate limit/validação/timeout) e fallback 200 degradado seguro com sinalização de suporte parcial — Validated in Phase 20 (API-01/02/03)
- [~] Cobertura automatizada/docs/fechamento rastreável de gaps (v1.2 carry-over v1.1) — Phase 18 complete with **partial+handoff** (`TEST-04`, `DOC-01`, `AUD-05`, runtime/canonical/human evidence pending)
- [~] v1.1 scope (Phases 7–13) — **accepted gaps/caveats** remain (see v1.1/v1.2 archives and audit artifacts); not fully validated.

### Active

- [ ] Implementar interface de chat no board público (drawer/modal mobile-first) consumindo `chat-search`, exibindo interpretação/parâmetros e resultados com acesso ao detalhe (UI, Phase 21)
- [ ] Qualidade, hardening e validação operacional do chatbot (QA, Phase 22): cenários MVP, limites/custos/latência, resiliência e regressão do fluxo público sem fricção
- [ ] (A definir) Incluir ou não itens de carry-over/hardening (PUB-01..08, handoffs v1.2, lacunas v1.1) no escopo do milestone

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Instagram, geração de imagem, sincronização de edição/remoção do post, múltiplas Páginas, métricas/insights de engajamento — fora do milestone v1.2 (arquitetura deve prever extensão)
- Login/cadastro de usuário comum — secundário e opcional, não entra no MVP (o diferencial é justamente não exigir conta)
- Renovação de vagas expiradas — fora de escopo; expiração é definitiva (ciclo completo)
- Controle de duplicidade de vagas — não previsto; curadoria manual cobre
- Múltiplos administradores / papéis de usuário — apenas o master posta/aprova
- Monetização ativa (doações reais e ADS contratados) — baixa prioridade; apenas o botão e os placeholders no MVP
- Submissão pública de vagas por terceiros — não no MVP

## Context

- **Origem das vagas:** textos soltos e brutos compartilhados em grupos de WhatsApp/Telegram. A extração por LLM precisa lidar com texto desestruturado, múltiplas vagas por mensagem, emojis e formatação inconsistente.
- **Volume esperado:** 100–500 vagas publicadas por mês — curadoria manual é viável, mas o fluxo de colar → extrair → revisar → publicar precisa ser rápido.
- **Custo:** operar próximo de zero usando tiers gratuitos (Neon Postgres, Groq, Vercel, Cloudflare Turnstile).
- **Público:** candidatos brasileiros (foco inicial em SP, RJ, BH e Remoto), majoritariamente mobile.
- **Motivação central:** a principal frustração com sites de emprego atuais é a burocracia de cadastro/login para sequer ver uma vaga.
- **Riscos conhecidos / estado atual:** revisão manual do master como gate de qualidade; mitigação de scraping via ocultação + Turnstile; **pendências operacionais/evidências** registradas no audit v1.1 (smoke canônico/execução real, DB de testes, verificações humanas/browser, requisitos EXTR/PUBL/SRCH/UIUX não fechados no escopo auditado).

## Constraints

- **Tech stack — Frontend:** Next.js 16 (App Router, `16.4.6`) + Tailwind CSS + dark mode — decisão fixada pelo usuário (major subida de 15 → 16 em 2026-11-11 por exigência de segurança do build Vercel)
- **Tech stack — Backend:** FastAPI (Python) — decisão fixada pelo usuário
- **Banco:** Neon (Postgres gratuito) — decisão fixada pelo usuário
- **LLM de extração:** Groq, modelo gratuito — `openai/gpt-oss-20b` (padrão) com `openai/gpt-oss-120b` como fallback, via env `GROQ_MODEL` — *corrigido pós-pesquisa: `llama-3.1-8b-instant`/`llama-3.3-70b` foram aposentados em 2026-08-16*
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
| Substituir Llama aposentados por Groq `gpt-oss` | `llama-3.1-8b-instant`/`llama-3.3-70b` desativados em 2026-08-16; `openai/gpt-oss-*` suporta structured outputs estritos | ✓ Good (configuração atualizada; fallback/aceitação detalhada pendente no audit) |
| Usar `bcrypt` direto (sem passlib) para hash de senha | `passlib` 1.7.4 é incompatível com o `bcrypt` 5.0.0 travado; a decisão de auth permite bcrypt diretamente | ✓ Good |

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
*Last updated: 2026-11-17 after completing Phase 20 (API pública de chat-search resiliente)*
