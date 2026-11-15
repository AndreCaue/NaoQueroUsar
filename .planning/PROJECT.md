# EmpregaNoix

## Current State

**Latest shipped milestone:** v1.1 EmpregaNoix — **shipped 2026-11-15** (archived with **accepted audit gaps**).  
**Audit:** `.planning/v1.1-MILESTONE-AUDIT.md` (`gaps_found`) — user elected to complete milestone and record gaps/tech debt.  
**Archives:** `.planning/milestones/v1.1-ROADMAP.md`, `.planning/milestones/v1.1-REQUIREMENTS.md`

**Current milestone:** None. Define the next milestone with `/gsd-new-milestone` (fresh requirements/roadmap).

## What This Is

Plataforma pública de busca de emprego cujo diferencial é eliminar a burocracia de cadastro: qualquer pessoa vê as vagas e o contato **sem criar conta, sem login e sem etapas intermediárias**. Um board enxuto, dark mode e mobile-first, curado manualmente por um único administrador (o master), que transforma textos brutos de grupos de vagas em cards estruturados.

Slogan: "Procurar um emprego, não deve dar trabalho"

## Core Value

Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

## Requirements

### Validated

<!-- Shipped and confirmed valuable (high-confidence). -->

- [x] Admin solo acessa área protegida por senha (via `.env`) / JWT — Validated in Phase 1: Backend Foundation, Data & Admin Auth (ADMN-01/02/03)
- [~] v1.1 scope (Phases 7–13): implementação/reconciliação avançada em reveal/anti-spam, revisão admin, lifecycle/trust/legal, rebranding e alinhamento canônico de deploy/ops — **com lacunas aceitas** (ver audit/archives). Não tratar como totalmente validado.

### Active

<!-- Next milestone scope (to be defined). -->

- [ ] Definir e executar próximos incrementos via `/gsd-new-milestone` (fechar gaps de EXTR/PUBL/SRCH/UIUX, evidências DB/browser/canônicas pendentes, e demais itens do audit conforme prioridade)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

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
*Last updated: 2026-11-15 after v1.1 milestone completion (EmpregaNoix, audit gaps accepted)*
