# NQU — NaoQueroUsar

## What This Is

Plataforma pública de busca de emprego cujo diferencial é eliminar a burocracia de cadastro: qualquer pessoa vê as vagas e o contato **sem criar conta, sem login e sem etapas intermediárias**. Um board enxuto, dark mode e mobile-first, curado manualmente por um único administrador (o master), que transforma textos brutos de grupos de vagas em cards estruturados.

Slogan: "Procurar um emprego, não deve dar trabalho"

## Core Value

Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- [x] Admin solo acessa área protegida por senha (via `.env`) / JWT — Validated in Phase 1: Backend Foundation, Data & Admin Auth (ADMN-01/02/03)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Admin cola um texto grande com várias vagas de grupos (WhatsApp/Telegram)
- [ ] LLM (Groq) extrai automaticamente os campos de cada vaga e cria cards com status `pending`
- [ ] Admin revisa: aprovar, editar por ID, excluir
- [ ] Vaga aprovada passa para status `published` e aparece na home pública
- [ ] Campos da vaga: title (obrigatório), company, activities, requirements, salary, benefits, city, contact_email e/ou contact_phone (ao menos um obrigatório), created_at, expires_at (14 dias), status
- [ ] Home pública com grade responsiva de mini-cards (mobile-first)
- [ ] Card mostra title, início das activities (expansível), salary (se houver) e botão "Ver a vaga"
- [ ] Modal de detalhes completo, mobile-friendly
- [ ] Contato oculto por padrão — botão "Mostrar contato" revela no clique (client-side)
- [ ] Barra de busca + filtro por cidade + ordenação por data (crescente/decrescente)
- [ ] Cidades iniciais: São Paulo, Rio de Janeiro, Belo Horizonte, Remoto
- [ ] Vagas expiram automaticamente após 14 dias e são apagadas do banco (hard delete)
- [ ] Tema dark mode roxo minimalista
- [ ] Botão "Doações" no canto superior direito (amarelo #facc15, discreto, hover apenas)
- [ ] Espaços reservados para ADS futuros (banner topo + sidebar + entre cards)
- [ ] Anti-spam: Cloudflare Turnstile

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
- **Motivação central:** a principal frustração com sites de emprego atuais é a burocracia de cadastro/login para sequer ver uma vaga. A NQU elimina isso.
- **Riscos conhecidos:** vagas de golpe vindas de grupos → a revisão manual do master é o gate de qualidade; exposição de contato → mitigada por ocultação padrão + revelação no clique + Turnstile.

## Constraints

- **Tech stack — Frontend:** Next.js 15 (App Router) + Tailwind CSS + dark mode — decisão fixada pelo usuário
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
| Sem cadastro/login para ver vagas e contato | Elimina a maior frustração com sites atuais (burocracia) | — Pending |
| Hard delete após 14 dias | Mantém o board limpo e o custo de armazenamento baixo | — Pending |
| Extração via LLM (Groq) + revisão manual obrigatória | Automação do trabalho pesado sem abrir mão do controle de qualidade | — Pending |
| Repo git dedicado no diretório do projeto | O diretório está dentro do repo da home; isolamento evita poluir histórico | — Pending |
| Contato revelado no clique (client-side) | Reduz scraping com fricção mínima ao usuário | — Pending |
| Servir contato via endpoint dedicado (não no payload público) | Ocultação client-side sozinha não protege contra scraping; exigido Turnstile server-side no reveal | — Pending |
| Substituir Llama aposentados por Groq `gpt-oss` | `llama-3.1-8b-instant`/`llama-3.3-70b` desativados em 2026-08-16; `openai/gpt-oss-*` suporta structured outputs estritos | — Pending |
| Usar `bcrypt` direto (sem passlib) para hash de senha | `passlib` 1.7.4 é incompatível com o `bcrypt` 5.0.0 travado; a decisão de auth permite bcrypt diretamente | — Implemented Phase 1 |

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
*Last updated: 2026-10-19 after Phase 1 completion (Backend Foundation, Data & Admin Auth)*
