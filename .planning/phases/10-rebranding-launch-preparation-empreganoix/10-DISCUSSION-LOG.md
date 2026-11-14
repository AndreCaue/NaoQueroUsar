# Phase 10: Rebranding & Launch Preparation (EmpregaNoix) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-14
**Phase:** 10-rebranding-launch-preparation-empreganoix
**Areas discussed:** Escopo do rename, Hosts e domínios, Deploy real agora, Assets de marca, Textos legais e canal de contato, Email de contato

---

## Escopo do rename

| Option | Description | Selected |
|--------|-------------|----------|
| Apenas frontend visível | Textos, labels, headings, meta tags, toasts, WhatsApp template, legal pages passam para EmpregaNoix. Backend API title/docs/README/planning/seed company/email ficam como estão (interno). | |
| Frontend + legal + email | Tudo acima + atualizar 'NQU'/'NaoQueroUsar' em privacidade/termos e email suportenqs→empreganoix. Backend title/docs/README/planning permanecem NQU. | |
| Renomeação completa | Tudo: frontend, backend FastAPI title, docs, README, pyproject description, seed company, planning artifacts, repo. Máximo esforço, risco de quebrar referências internas. | ✓ |
| Apenas meta tags + wordmark | Mínimo: title/metadata e wordmark do header. Resto fica 'NaoQueroUsar' (transição gradual). | |

**User's choice:** Renomeação completa
**Notes:** Inclui conteúdo de todos os arquivos (textos, títulos, seed, email) para "EmpregaNoix". Diretório do repo e `.planning` permanecem "NaoQueroUsar" (decisão separada).

---

## Renomeação do diretório/repo

| Option | Description | Selected |
|--------|-------------|----------|
| Não renomear diretório/repo | Manter pasta 'NaoQueroUsar' e .planning. Renomear apenas conteúdo de arquivos (textos, títulos, seed, email). Evita quebrar paths e histórico git. | ✓ |
| Renomear tudo incluindo pasta | Renomear diretório do projeto e .planning para EmpregaNoix. Alto risco: paths absolutos em scripts/docs, git remote, sessão OpenCode. | |

**User's choice:** Não renomear diretório/repo
**Notes:** Apenas conteúdo é renomeado; paths do repo mantidos.

---

## Hosts e domínios

| Option | Description | Selected |
|--------|-------------|----------|
| Novos hosts Vercel/Render | Frontend https://empreganoix.vercel.app, backend https://empreganoix.onrender.com. Configurar no Vercel/Render e atualizar CORS/ALLOWED_ORIGINS/NEXT_PUBLIC_API_URL. | ✓ |
| Manter hosts antigos + alias | Manter nao-quero-usar.vercel.app / naoquerousar.onrender.com e adicionar empreganoix como alias/redirect. Mais trabalho, duas origens. | |
| Domínio próprio agora | Comprar/configurar domínio próprio (ex.: empreganoix.com.br) para ambos. Requer DNS + custo; fora do tier gratuito. | |

**User's choice:** Novos hosts Vercel/Render
**Notes:** Hosts antigos não mantidos (sem redirect). Turnstile Hostnames atualizados para as novas origens.

---

## Deploy real agora

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, deploy real agora | Executar deploy Vercel+Render, configurar env (ENV=prod, CORS, Turnstile live, CRON_SECRET), rodar smoke gate. Fecha BRND-04 e Phase 6 deploy. | ✓ |
| Apenas preparar artefatos | Atualizar vercel.json/render.yaml/docs/env, mas manter em dev local (decisão anterior). Smoke gate não roda. Phase 6 deploy permanece aberto. | |
| Deploy só frontend (Vercel) | Frontend no Vercel apontando para backend local/túnel; backend permanece local. Híbrido para testes. | |

**User's choice:** Sim, deploy real agora
**Notes:** Revoga a decisão anterior de manter em dev local (Phase 6). Smoke gate verde é critério de aceite.

---

## Assets de marca

| Option | Description | Selected |
|--------|-------------|----------|
| Apenas wordmark textual | Sem favicon/logo novos; usar wordmark 'EmpregaNoix' textual no header/meta. Menor esforço; consistente com atual. | |
| Gerar favicon + og:image | Criar favicon simples (iniciais 'E' roxo) e og:image para compartilhamento. Requer geração de assets. | |
| Logo completo novo | Criar logo/marca completa com identidade visual. Escopo de design maior; pode ser fase separada. | ✓ |

**User's choice:** Logo completo novo
**Notes:** Inclui favicon e og:image. OpenCode gera os assets; fallback de wordmark textual se atrasar.

---

## Textos legais e canal de contato

| Option | Description | Selected |
|--------|-------------|----------|
| Atualizar tudo para EmpregaNoix | Substituir 'NQU'/'NaoQueroUsar' em privacidade/termos por 'EmpregaNoix'; email suportenqs→empreganoix. | ✓ |
| Manter nome legal NQU | Manter 'NaoQueroUsar' nos textos legais (razão social/entidade) e só atualizar frontend. Email permanece suportenqs. | |
| Atualizar textos, manter email | Textos legais passam para EmpregaNoix mas email de contato (suportenqs) fica igual. | |

**User's choice:** Atualizar tudo para EmpregaNoix
**Notes:** WhatsApp template também atualizado para "no EmpregaNoix".

---

## Email de contato

| Option | Description | Selected |
|--------|-------------|----------|
| suporteempreganoix@outlook.com | Substituir suportenqs@outlook.com pelo novo email. | |
| Manter suportenqs@outlook.com | Não mudar o email (evita criar nova caixa). | |
| Outro email | Informar o email desejado. | ✓ (free-text: empreganoix@outlook.com) |

**User's choice:** empreganoix@outlook.com
**Notes:** Email final definido pelo usuário como texto livre.

---

## OpenCode's Discretion

- Ferramenta/fluxo exato para gerar os assets de marca (favicon, og:image, logo) — image generation ou SVG manual.
- Ordem de execução das substituições (frontend primeiro, depois backend/docs/infra).
- Fallback de wordmark textual se assets não estiverem prontos no momento do deploy (não bloquear BRND-04).

## Deferred Ideas

- Domínio próprio (ex.: empreganoix.com.br) — fora desta fase.
- Redirect dos hosts antigos — não mantidos.
- Renomeação do diretório do repositório/`.planning` — não feita.
- Revisão jurídica dos textos legais — task humana.