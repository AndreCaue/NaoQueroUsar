# Phase 5: Admin Review Area - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-26
**Phase:** 5-admin-review-area
**Areas discussed:** Fila de revisão (status, filtros, ordenação), Interação de revisão (aprovar/editar/excluir), Texto-fonte ao lado (REVW-05), Rotas/tema/feedback da área admin

---

## Fila de revisão (status, filtros, ordenação)

| Option | Description | Selected |
|--------|-------------|----------|
| Apenas pending (Recomendado) | Fila mostra só vagas pending; needs_review/invalid em aba separada | ✓ |
| Pending + needs_review juntos | Fila única com badges diferenciando | |
| Tudo não-publicado | Inclui invalid para auditoria | |
| Mais recentes primeiro (Recomendado) | created_at DESC, tie-break id DESC | ✓ |
| Por status (needs_review primeiro) | Agrupa por necessidade de atenção | |
| Mais antigas primeiro | FIFO, created_at ASC | |
| Filtro por cidade (Recomendado) | Chips de cidade (SP, RJ, BH, Remoto); sem busca por texto | ✓ |
| Busca por texto + filtro por cidade | Busca livre + filtro por cidade | |
| Sem busca nem filtro | Fila simples ordenada por data | |
| Você decide | Delegar ao planner | |
| Paginação offset (Recomendado) | page/limit, limit 24, controles | ✓ |
| Scroll infinito / 'carregar mais' | Botão acumula itens | |
| Lista completa (sem paginação) | Carrega todos de uma vez | |

**User's choice:** Apenas pending; mais recentes primeiro; filtro por cidade; paginação offset.
**Notes:** needs_review tratado em aba separada "Precisam correção" (decidido na rodada seguinte). Sem busca por texto livre na fila admin.

---

## Interação de revisão (aprovar/editar/excluir)

| Option | Description | Selected |
|--------|-------------|----------|
| Botão 'Aprovar' por vaga (Recomendado) | Individual, status→published, sai da fila, toast | ✓ |
| Aprovação em lote | Checkbox + 'Aprovar selecionadas' | |
| Aprovar + editar antes de publicar | Abre form de edição antes de publicar | |
| Modal de edição (Recomendado) | Modal com todos os campos editáveis | ✓ |
| Edição inline na fila | Inputs editáveis diretamente na lista | |
| Página dedicada de edição | /admin/jobs/[id] | |
| Todos os campos (Recomendado) | title, company, activities, requirements, salary, benefits, city, contact_email, contact_phone | ✓ |
| Apenas campos de conteúdo | Sem contato/cidade | |
| Você decide | Delegar ao planner | |
| Hard delete com confirmação (Recomendado) | Modal 'Tem certeza?' + DELETE | ✓ |
| Soft delete / arquivar | Novo status; fora do escopo | |
| Excluir sem confirmação | Delete direto | |

**User's choice:** Aprovação individual; edição via modal com todos os campos; exclusão hard delete com confirmação.
**Notes:** needs_review em aba separada; sem ação "Rejeitar"; aprovação definitiva (sem reversão published→pending).

---

### needs_review handling

| Option | Description | Selected |
|--------|-------------|----------|
| Aba/seção separada 'Precisam correção' (Recomendado) | Duas abas: Pendentes e Precisam correção | ✓ |
| Fila única com badge de status | pending + needs_review com badges | |
| needs_review não revisável nesta fase | Fora do fluxo | |

### Rejeitar

| Option | Description | Selected |
|--------|-------------|----------|
| Não — só Aprovar/Editar/Excluir (Recomendado) | Três ações; excluir cobre o caso | ✓ |
| Sim — 'Rejeitar' marca como invalid | Status→invalid para auditoria | |
| Sim — 'Rejeitar' devolve para needs_review | published/pending→needs_review | |

### Reversível

| Option | Description | Selected |
|--------|-------------|----------|
| Não — aprovação é definitiva (Recomendado) | published não volta para pending | ✓ |
| Sim — 'Despublicar' | published→pending | |

---

## Texto-fonte ao lado (REVW-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Lado a lado em desktop, empilhado em mobile (Recomendado) | Painel campos + snippet sticky; mobile accordion | ✓ |
| Snippet colapsável abaixo (accordion) | Sempre abaixo, colapsado por padrão | |
| Duas abas: 'Campos' e 'Texto-fonte' | Alterna entre campos e snippet | |
| Sem destaque automático (Recomendado) | Snippet texto puro; conferência visual | ✓ |
| Destaque dos termos encontrados | Sublinha termos encontrados | |
| Você decide | Delegar ao planner | |
| Somente leitura (Recomendado) | Snippet não editável | ✓ |
| Editável | Admin pode corrigir o snippet | |
| Mostrar placeholder 'sem texto-fonte' (Recomendado) | Exibe placeholder itálico/cinza | ✓ |
| Ocultar o painel de snippet | Painel não renderiza se vazio | |

**User's choice:** Lado a lado desktop/empilhado mobile; sem destaque; somente leitura; placeholder quando vazio.
**Notes:** source_snippet é a referência de grounding (Phase 2 D-08); não deve ser alterado.

---

## Rotas, tema e feedback da área admin

| Option | Description | Selected |
|--------|-------------|----------|
| Hub /admin com links (Recomendado) | /admin (dashboard) com links para paste e review | ✓ |
| Rotas independentes sem hub | Sem /admin raiz | |
| Tudo em /admin/paste | Uma página com abas | |
| Manter CSS plano (herdado) (Recomendado) | Admin continua globals-admin.css | |
| Adotar Tailwind v4 no admin (novo route group) | Migração para Tailwind v4, paridade visual | ✓ |
| Híbrido | Tailwind só na fila nova | |
| Toast + atualização otimista (Recomendado) | Toast pt-BR + fila otimista + revalidação | ✓ |
| Feedback inline | Banner no topo da fila | |
| Você decide | Delegar ao planner | |
| Guard client-side com redirecionamento (Recomendado) | Sem token → redireciona para login | ✓ |
| Middleware Next.js (server-side) | Exige cookie httpOnly (fora do escopo) | |
| Sem guard no front | Só backend bloqueia | |

**User's choice:** Hub /admin; Tailwind v4 no admin (override da herança Phase 4); toast + atualização otimista; guard client-side.
**Notes:** Migração de paste + fila juntos para Tailwind (decidido na rodada seguinte); toast implementado como componente próprio simples.

---

### Migração Tailwind

| Option | Description | Selected |
|--------|-------------|----------|
| Migrar paste + fila juntos (Recomendado) | Unifica estilo; globals-admin.css substituído | ✓ |
| Tailwind só na fila nova | Paste fica em CSS plano | |
| Você decide | Delegar ao planner | |

### Toast

| Option | Description | Selected |
|--------|-------------|----------|
| Componente próprio simples (Recomendado) | Sem dependência externa | ✓ |
| Biblioteca (sonner/react-hot-toast) | Adiciona dep de toast | |

---

## OpenCode's Discretion

- Estrutura de arquivos/componentes da fila e do modal de edição.
- Mecânica exata do toast (posicionamento, animação, z-index) e da atualização otimista.
- Comportamento do hub /admin quando não autenticado.
- Paginação visual (controles vs "Ver mais") na fila admin.
- Empty state e loading (skeleton) da fila.
- Validação client-side do form de edição (zod) e mensagens de erro (body.detail verbatim).
- Se a aba "Precisam correção" é rota separada ou tab client-side.

## Deferred Ideas

- Aprovação em lote (checkbox + "Aprovar selecionadas") — descartado nesta fase.
- Ação "Rejeitar" (→invalid ou →needs_review) — descartado; excluir cobre.
- Reversão published→pending ("Despublicar") — descartado; aprovação definitiva.
- Destaque automático de termos no snippet — descartado; conferência visual.
- Soft delete / arquivar — fora do escopo (hard delete).
- Busca por texto livre na fila admin — descartado (filtro por cidade basta).
- Middleware Next.js server-side para proteção admin — descartado.
- Biblioteca de toast externa — descartado; componente próprio.
- PIX real / páginas legais / badge "Vaga revisada" / report — Phase 6.
- Ciclo de vida / expiração hard-delete 14 dias — Phase 6.
- Chaves reais do Cloudflare + wiring de deploy — Phase 6.