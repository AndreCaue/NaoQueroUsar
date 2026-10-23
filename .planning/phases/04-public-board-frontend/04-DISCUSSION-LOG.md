# Phase 4: Public Board Frontend - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-22
**Phase:** 4-public-board-frontend
**Areas discussed:** Fatiamento da entrega, Busca sem acento (SRCH-01), Renderização e URL do board, Botão Doações + ADS reais

---

## Fatiamento da entrega

| Option | Description | Selected |
|--------|-------------|----------|
| Uma fase, 5-6 planos | Ondas: fundação Tailwind/route group → board+card → modal+reveal → busca/filtros/URL → tema+ADS+Doações | ✓ |
| Três sub-fases (4a/4b/4c) | 4a board/modal/reveal, 4b busca/filtros, 4c tema/ADS | |
| Duas sub-fases (4a/4b) | Core (board+modal+reveal) e resto | |
| Cortar busca/filtros agora | Só PUBL-01..06; SRCH/UIUX-02/03 adiadas | |

**User's choice:** Uma fase, 5-6 planos.
**Notes:** Evita mexer no ROADMAP com sub-fases; os 11 requisitos fecham juntos.

---

## Dados para verificação no browser

| Option | Description | Selected |
|--------|-------------|----------|
| Seed local dev-only | Script que insere vagas `published` com contatos fake, só em dev | ✓ |
| Só fixture + UPDATE manual | pytest + `UPDATE status='published'` manual | |
| Antecipar aprovação da Phase 5 | Trazer o botão publicar para esta fase | |
| Endpoint dev-only de seed | Superfície HTTP extra quando `ENV=dev` | |

**User's choice:** Seed local dev-only.
**Notes:** A aprovação de vaga é Phase 5, então sem seed não há como ver o board no browser.

---

## Busca sem acento (SRCH-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Coluna normalizada `search_text` | Preenchida na escrita; ILIKE na coluna; portável, indexável | ✓ |
| Extensão `unaccent` na query | `unaccent(lower(col)) ILIKE unaccent(lower(:q))` | |
| Coluna + `pg_trgm` GIN | Normalização + índice trigram para escala grande | |

**User's choice:** Coluna normalizada `search_text`.
**Notes:** Descoberta durante a análise: a migration `0001_initial_jobs.py` **já criou** `search_text`, o trigger `immutable_unaccent(lower(...))` e o índice GIN `pg_trgm` parcial. A escolha fica implementada por esse mecanismo existente — a única lacuna é o trigger omitir `requirements` (fechada por uma migration `0003` + backfill). Nenhuma normalização em Python.

---

## Busca: campos

| Option | Description | Selected |
|--------|-------------|----------|
| Título+empresa+atividades+requisitos, AND com cidade | Cidade tem filtro próprio e combina por AND | ✓ |
| Só título + empresa | Mais previsível, não acha termos da descrição | |
| Todos os campos, cidade via `q` | Menos previsível | |

**User's choice:** Título+empresa+atividades+requisitos, AND com cidade.

---

## Renderização e URL

| Option | Description | Selected |
|--------|-------------|----------|
| SSR + modal com deep-link `?vaga=` | RSC no servidor; dialog grava `?vaga=<id>`; link compartilhável | ✓ |
| SSR + página `/vagas/[id]` | Melhor SEO por vaga, mas muda PUBL-03 (modal) | |
| SSR + modal sem deep-link | Simples, nada compartilhável por vaga | |
| Client-side puro | Sem SSR, HTML inicial vazio | |

**User's choice:** SSR + modal com deep-link `?vaga=`.

---

## Cache da lista

| Option | Description | Selected |
|--------|-------------|----------|
| Sem cache (`no-store`) | Sempre fresco; sem explosão de variantes com filtros | ✓ |
| ISR 60s | Mais rápido, até 60 s defasado | |
| Cache com tag + revalidate na Phase 5 | Melhor dos dois mundos, exige wiring futuro | |

**User's choice:** Sem cache — sempre fresco.

---

## Doações

| Option | Description | Selected |
|--------|-------------|----------|
| Página mínima `/doacoes` | Rota estática honesta, linkável, PIX em Phase 6 | ✓ |
| Modal "em breve" na home | Sem rota nova, não linkável | |
| Link externo de doação | Sai do domínio; exige página existente | |

**User's choice:** Página mínima `/doacoes`.

---

## ADS

| Option | Description | Selected |
|--------|-------------|----------|
| Só placeholders reservados | Caixas tracejadas com altura fixa, sem script | ✓ |
| Placeholders + flag `NEXT_PUBLIC_ADS_ENABLED` | Pronto para plugar depois | |
| AdSense real agora | Conta, script de terceiro, consentimento LGPD | |

**User's choice:** Só placeholders reservados.

---

## OpenCode's Discretion

- Tailwind v4 no route group `(public)` para isolar o Preflight do `/admin/*`; sem shadcn; ícones SVG inline (aprovado no `04-UI-SPEC.md`).
- Estrutura de componentes/arquivos, nomes de helpers de fetch, variável de API no servidor.
- Formato e volume do seed dev-only.
- Paginação visual, skeleton e wiring de foco/aria do `<dialog>`.
- Mecânica do backfill da migration `0003`.

## Deferred Ideas

- Aprovação/edição de vagas no admin — Phase 5.
- PIX real / doações completas — Phase 6.
- AdSense + consentimento LGPD + política de privacidade — Phase 6.
- Sitemap / JSON-LD / OG images — não requisitado.
- Chaves reais do Cloudflare e env de deploy — Phase 6.
- Limiter distribuído — Phase 6.
- Rota `/vagas/[id]` dedicada — descartada em favor do deep-link no modal.
- Busca fuzzy por similaridade (`pg_trgm`) — complexidade antecipada.
