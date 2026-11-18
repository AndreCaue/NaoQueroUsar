# Phase 21: Interface de chat e integração no board - Research

**Researched:** 2026-11-17
**Domain:** Next.js App Router client UI (chat drawer/bottom sheet), integração com API pública de chat-search e com fluxo canônico do board
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Entrada e formato do chat
- **D-01:** Acesso via **botão flutuante discreto** no board público que abre o chat em painel responsivo: **bottom sheet no mobile** e **drawer/modal adequado no desktop**, mantendo o board como contexto principal.
- **D-02:** A conversa, interpretação e resultados do chat são **mantidos em memória enquanto a aba/página estiver aberta** (estado de sessão do cliente). Fechar/reabrir o painel não apaga; **recarregar a página** reinicia o estado.
- **D-03:** Estado inicial vazio exibe **campo de mensagem com placeholder/instrução breve em pt-BR** e **2–4 exemplos curtos clicáveis** (ex.: consultas típicas de cargo/local/modalidade) para facilitar o primeiro uso.
- **D-04:** Durante envio/espera da resposta, mostrar **indicador visível no thread** (“buscando/interpretando”), **bloquear envio duplicado** até concluir e, em falha, exibir **erro pt-BR claro com ação de tentar novamente** (respeitando estados de carregamento/erro exigidos).

#### Exibição da interpretação e resultados
- **D-05:** Interpretação apresentada como **resumo em linguagem natural (“Entendi…”) + status por campo** (chips/linhas indicando aplicado, ignorado, aproximado e motivo conforme contrato), com **limitações/guidance em bloco de aviso separado e legível**.
- **D-06:** Resultados no chat exibidos como **lista compacta de cards/itens empilhados**, cada um com **título, empresa, local e salário quando disponível**, otimizados para painel estreito/mobile e sem expor contatos.
- **D-07:** Navegação de resultados no chat: mostrar **primeira página** retornada e permitir **“Carregar mais”** sob demanda (usando paginação da API) para buscar páginas seguintes dentro do próprio chat.
- **D-08:** Em degradação (LLM indisponível/timeout/sem parâmetros extraíveis) ou sem vagas, exibir **mensagem de guidance/limitações destacada** conforme resposta da API, deixar explícito quando **não houve resultados automáticos**, e oferecer **atalho claro para busca/filtros manuais do board**.

#### Aplicar busca no board canônico
- **D-09:** “Aplicar no board” **substitui `q`, `city` e `sort`** pelos `applied_params` efetivos, **limpa `vaga`** e **reseta `page` para 1** na URL canônica, refletindo fielmente a interpretação suportada.
- **D-10:** Após aplicar, **fechar/minimizar o chat** para mostrar o board atualizado (conversa permanece preservada na sessão conforme D-02).
- **D-11:** Ação “Aplicar no board” fica **disponível quando houver parâmetros aplicáveis/úteis** para refletir no board; em respostas **degradadas ou sem parâmetros aplicáveis**, priorizar guidance e atalho para busca manual em vez de aplicar estado vazio.
- **D-12:** Quando houver **aproximações/limites** mas aplicação for possível, exibir **texto curto junto à ação** indicando suporte parcial (ex.: alguns critérios aproximados/não filtrados), além do bloco de interpretação.

#### Abrir detalhe a partir do chat
- **D-13:** Abrir vaga a partir do chat pelo **fluxo canônico via `?vaga=<id>`/detalhe existente**, reutilizando `JobDetailDialog`/`RevealContact` e comportamento atual de resolução/deep link (board permanece a fonte do detalhe e da revelação).
- **D-14:** Ao abrir o detalhe a partir do chat, **fechar/minimizar o painel de chat** para evitar sobreposição de camadas; ao fechar o detalhe o usuário retorna ao board e pode reabrir o chat com estado preservada.
- **D-15:** Cada resultado do chat é um **item/card inteiro clicável com indicação clara** (“Ver detalhes”) para acionar a abertura canônica.
- **D-16:** Resultados do chat exibem apenas campos públicos permitidos (**título, empresa, local, salário quando disponível** — `JobPublic`), **nunca contatos**; revelação de contato ocorre exclusivamente no fluxo existente do detalhe.

### OpenCode's Discretion
- Posicionamento exato, ícone/rotulagem, animação, foco/acessibilidade e comportamento de foco/ESC do botão flutuante e do painel (sheet/drawer/modal), desde que mobile-first, sem login e com estados claros.
- Copy pt-BR final de placeholders, exemplos sugeridos, labels de status (aplicado/ignorado/aproximado), mensagens de erro/loading e textos de guidance/atalhos, alinhados ao contrato da API.
- Implementação do estado em memória (componente/página/contexto), estratégia de “Carregar mais” (append/substituição interna) e composição visual dos itens compactos, respeitando D-01..D-16 e o design system existente.
- Mapeamento fino de `applied_params` nulos para URL (omitir `q`/`city` quando nulos, `sort` conforme suporte canônico) e integração com `buildBoardHref`/`normalizeFilters`/`router.replace` sem quebrar o board.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | Usuário acessa uma interface de chat simples (drawer/modal), mobile-first e sem login, a partir do board público, com envio de mensagem, estados de carregamento/erro e boa percepção de performance. | D-01..D-04, integração client-side no board público, cliente `POST /api/v1/public/chat-search`, padrões de loading/erro e bloqueio de envio duplicado, painel responsivo bottom sheet/drawer. |
| UI-02 | A interface exibe os parâmetros entendidos/aplicados/ignorados-aproximados e apresenta resultados relevantes (título, empresa, local, salário quando disponível, acesso ao detalhe/link) reutilizando o fluxo atual de detalhe e revelação de contato (contatos nunca expostos no payload do chat). | D-05..D-08, D-13..D-16, consumo de `interpretation`/`results` (`JobPublic`), render de `field_statuses`/`limitations`/`meta.guidance`, reuso de `JobDetailDialog`/`RevealContact` e `?vaga`. |
| UI-03 | Usuário pode aplicar/ajustar a busca entendida no board canônico (URL/filtros existentes) quando aplicável, preservando o comportamento atual de busca/listagem sem fricção. | D-09..D-12, mapeamento de `applied_params` para `buildBoardHref`/`normalizeFilters`, navegação `router.replace`, reset `page/vaga`, fechamento do chat. |
</phase_requirements>

## Summary

Phase 21 é uma **fase de integração frontend client-side** sobre contratos já entregues: o endpoint público `POST /api/v1/public/chat-search` (Phase 20) retorna `interpretation` (`IntentContract`: `understood`, `field_statuses`, `applied_params`, `limitations`, `meta`) + `results` pagináveis (`items: JobPublic[]`, `page`, `limit`, `total`) sem contatos. O board público já é server-rendered com URL canônica (`q/city/sort/page/vaga`) e componentes client para toolbar, grid, `JobDetailDialog` e `RevealContact`. O trabalho de planejamento deve focar em (1) montar o acesso/painel do chat no board sem quebrar SSR/SEO, (2) tipar/consumir o contrato real de chat-search no cliente com estados claros e fallback honesto, (3) renderizar interpretação e resultados públicos compactos, (4) integrar “Carregar mais”, “Aplicar no board” e abertura de detalhe canônico respeitando contatos protegidos e decisões D-01..D-16.

**[VERIFIED: codebase grep/read]** Não há implementação existente de chat no frontend (`frontend/**chat*` inexistente; sem chamadas a `chat-search`). `backend/app/api/v1/public.py` expõe `/chat-search` com rate limit `chat_search_limit`, validação de `message/page/limit` via `ChatSearchRequest`, fallback degradado 200 (sem resultados automáticos) e guidance pt-BR em `meta.guidance`/`limitations`. `backend/app/core/config.py` define `CHAT_SEARCH_RATE_LIMIT`, `CHAT_SEARCH_MAX_MESSAGE_CHARS=400`, `CHAT_SEARCH_INTENT_TIMEOUT_SECONDS=12`.

**Primary recommendation:** Implementar o chat como feature client isolada (ex.: `components/board/chat/*` + helper em `lib/api.ts`) montada no board público, com estado de sessão em memória, cliente tipado para o envelope real, UI fiel a `field_statuses/limitations/meta/applied_params`, paginação por append de páginas, navegação canônica via `buildBoardHref` e abertura de detalhe reutilizando `JobDetailDialog`/`RevealContact` sem incluir contatos no estado/render do chat.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Acesso flutuante e painel responsivo (sheet/drawer) | Browser / Client | — | Interação local, foco/ESC/animação e estado de abertura/fechamento são puramente de UI (D-01, discrição). |
| Estado de conversa/sessão em memória (D-02) | Browser / Client | — | Persistência apenas enquanto aba aberta; sem backend/histórico persistente. |
| Envio de mensagem, loading/erro/retry, “Carregar mais” | Browser / Client | API / Backend (consumido) | Orquestração de requests e UX; backend já fornece contrato/proteções. |
| Extração de intenção, mapeamento seguro, busca determinística | API / Backend | Database / Storage (indireto via `list_published`) | Já implementado e imutável nesta fase; frontend apenas consome `interpretation+results`. |
| Render de interpretação (aplicado/ignorado/aproximado/guidance) | Browser / Client | — | Apresentação fiel do contrato server-authoritative. |
| Lista compacta de resultados públicos (sem contatos) | Browser / Client | — | `results.items` já são `JobPublic`; UI não deve adicionar/revelar contatos. |
| Aplicar busca no board canônico (`q/city/sort/page/vaga`) | Browser / Client | Frontend routing (Next `router`) | Escrita da URL canônica via helpers existentes (`buildBoardHref`/`normalizeFilters`, `router.replace`). |
| Detalhe da vaga e revelação de contato | Browser / Client (componentes existentes) | API / Backend (`/public/jobs/{id}`, `/reveal-contact`) | Reuso obrigatório de `JobDetailDialog`/`RevealContact` (D-13/D-16); contatos só no fluxo de detalhe. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| Next.js (App Router) | 16.4.6 (repo) | Framework frontend, roteamento e composição RSC/client | Stack fixada do projeto; board público e navegação `router.replace` já baseados nele. [VERIFIED: frontend/package.json, AGENTS.md] | HIGH |
| React | 19.1.1 (repo) | Componentes client, estado em memória, efeitos controlados | Usado em todo o board (`useState`, `useTransition`, refs). [VERIFIED: frontend/package.json] | HIGH |
| TypeScript | 5.9.2 (repo) | Tipagem do contrato de chat-search e integração segura | `frontend/lib/api.ts` e componentes já tipados; essencial para modelar `IntentContract`/envelope sem inferências. [VERIFIED: frontend/package.json, frontend/lib/api.ts] | HIGH |
| Tailwind CSS | 4.3.3 (repo) + tokens de `public.css` | Estilização dark/purple, layout responsivo mobile-first | Design system público já definido em `app/(public)/public.css`/classes utilitárias; manter consistência visual. [VERIFIED: frontend/package.json, frontend/app/(public)/public.css] | HIGH |
| Fetch API (browser) | nativa | Chamada `POST /api/v1/public/chat-search` | Padrão já usado em `lib/api.ts` (`revealContact`, `reportJob`) com `AbortSignal.timeout` e `ApiError/RevealError`. [VERIFIED: frontend/lib/api.ts] | HIGH |

### Supporting
| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| `next/navigation` (`useRouter`) | incluso no Next | Aplicar busca no board canônico | “Aplicar no board” deve usar `router.replace(buildBoardHref(...), { scroll: false })` como em `BoardToolbar`. [VERIFIED: frontend/components/board/BoardToolbar.tsx] | HIGH |
| Helpers existentes `lib/filters`, `lib/cities`, `lib/format` | n/a (internos) | Montar URL, normalizar `applied_params`, labels/formatos pt-BR | Sempre que aplicar filtros, exibir cidade (`cityLabel`) e manter formato de datas/salário consistentes. [VERIFIED: codebase] | HIGH |
| Componentes existentes `JobDetailDialog`, `RevealContact`, `JobGrid.syncVagaParam` (conceito) | n/a (internos) | Fluxo canônico de detalhe e reveal | Abrir vaga a partir do chat (D-13..D-16) sem duplicar lógica de contato. [VERIFIED: frontend/components/board/*] | HIGH |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Estado em memória em client component/provider local | `localStorage`/persistência | Violaria D-02 (reload deve reiniciar) e adiciona risco de persistir conteúdo sensível/obsoleto. [VERIFIED: 21-CONTEXT.md D-02] |
| Reuso de `<dialog>`/CSS tokens existentes para sheet/drawer | Biblioteca externa de sheet/drawer | Projeto não possui dependência de UI primitives; adicionar lib aumenta bundle/risco sem necessidade comprovada. Preferir composição com padrões já usados (`<dialog>`, utilitários Tailwind, tokens). [ASSUMED] |
| Cliente dedicado em `lib/api.ts` com tipos do envelope | `fetch` inline em componentes sem tipos | Perde consistência e segurança de contrato; `lib/api.ts` já concentra base URL, parse de erro e padrões. [VERIFIED: frontend/lib/api.ts] |

**Installation:**
```bash
# Nenhuma nova dependência prevista para esta fase.
# Reusar Next/React/TypeScript/Tailwind e utilitários existentes do frontend.
```

**Version verification:** Versões acima são as **instaladas no repositório** (`frontend/package.json`, `AGENTS.md`) — base canônica para planejamento desta fase. [VERIFIED: frontend/package.json, AGENTS.md]

## Architecture Patterns

### System Architecture Diagram

```text
[Usuário no board público (mobile/desktop)]
        |
        v
[Botão flutuante] --abre/fecha--> [ChatPanel (client, estado em memória)]
        |                                   |
        | envia message/page/limit          | renderiza interpretation+results
        v                                   v
[chatSearch() em lib/api.ts] <----HTTP----> [POST /api/v1/public/chat-search]
                                                |
                                                v
                                    [Intent + busca determinística já existentes]

Ações a partir do chat:
- "Aplicar no board" (se aplicável) -> monta href canônico com applied_params -> router.replace -> fecha/minimiza chat -> board RSC refaz listagem
- "Ver detalhes" em item JobPublic   -> fecha/minimiza chat -> abre detalhe canônico (?vaga / JobDetailDialog)
- No detalhe                         -> RevealContact revela contato (somente aqui)
- Fechar detalhe                     -> volta ao board; reabrir chat preserva estado (D-02)
```

### Recommended Project Structure
```text
frontend/
├── app/(public)/page.tsx                 # monta/injeta o acesso ao chat no board (ponto de integração)
├── components/board/
│   ├── JobDetailDialog.tsx               # reuso (D-13)
│   ├── RevealContact.tsx                 # reuso exclusivo do contato (D-16)
│   ├── JobGrid.tsx                       # referência: sync de ?vaga / diálogo
│   └── chat/                             # NOVO (sugerido): UI do chat
│       ├── ChatLauncher.tsx              # botão flutuante
│       ├── ChatPanel.tsx                 # sheet/drawer, thread, composer, estados
│       ├── ChatInterpretation.tsx        # "Entendi..." + status por campo + limitations/guidance
│       ├── ChatResultsList.tsx           # itens compactos + "Carregar mais" + "Aplicar no board"
│       └── ChatResultItem.tsx            # item clicável (título/empresa/local/salário)
├── lib/
│   ├── api.ts                            # adicionar tipos/função client chatSearch + erros
│   ├── filters.ts                        # reuso: buildBoardHref/normalizeFilters
│   ├── cities.ts                         # reuso: cityLabel
│   └── format.ts                         # reuso: formatação
```

### Pattern 1: Cliente tipado para `POST /api/v1/public/chat-search`
**What:** Definir tipos frontend espelhando o contrato real (`ChatSearchRequest`, `ChatSearchResponse`, `IntentContract`/`FieldAssessment`/`AppliedParams`, `ChatSearchResults`) e expor uma função `chatSearch(...)` em `lib/api.ts` usando `resolveApiBase()`/`API` já existente.
**When to use:** Toda chamada do chat (envio inicial e “Carregar mais”). [VERIFIED: backend/app/schemas/chat.py, backend/app/services/intent/schema.py, frontend/lib/api.ts]
**Example:**
```typescript
// Source: contrato verificado em backend/app/schemas/chat.py e intent/schema.py [VERIFIED: codebase]
export interface ChatSearchRequest { message: string; page?: number; limit?: number; }

export interface ChatAppliedParams { q: string | null; city: string | null; sort: "recentes" | "antigas" | null; }
export type ChatFieldStatus = "aplicado" | "ignorado" | "aproximado";
export interface ChatFieldAssessment {
  field: string; understood: unknown; applied: unknown;
  status: ChatFieldStatus; reason_code: string; reason: string;
}
export interface ChatInterpretation {
  understood: Record<string, unknown>;
  field_statuses: ChatFieldAssessment[];
  applied_params: ChatAppliedParams;
  limitations: string[];
  meta: Record<string, unknown> & { degraded?: boolean; degradation_reason?: string; guidance?: string };
}
export interface ChatSearchResults { items: JobPublic[]; page: number; limit: number; total: number; }
export interface ChatSearchResponse { interpretation: ChatInterpretation; results: ChatSearchResults; }

// Chamada (padrão análogo a reveal/report em lib/api.ts): POST JSON, parse detail pt-BR em erro, timeout finito.
```

### Pattern 2: Estado de sessão em memória com preservação ao minimizar (D-02, D-10, D-14)
**What:** Manter mensagens/thread, última resposta/interpretação, itens acumulados e paginação em estado React vivo enquanto a aba existir; “fechar/minimizar” apenas alterna visibilidade do painel, **não** desmonta o estado da conversa. Recarregar a página reinicia.
**When to use:** Comportamento obrigatório do chat. [VERIFIED: 21-CONTEXT.md D-02/D-10/D-14]
**Example:**
```typescript
// Source: padrão de estado client em componentes do board + D-02 [VERIFIED: codebase + CONTEXT.md]
const [isOpen, setIsOpen] = useState(false);
const [messages, setMessages] = useState<ChatMessage[]>([]);
const [draft, setDraft] = useState("");
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
const [lastResponse, setLastResponse] = useState<ChatSearchResponse | null>(null);
// Minimizar: setIsOpen(false). Reabrir: setIsOpen(true) — estado preservado.
```

### Pattern 3: Mapeamento `applied_params` → URL canônica (D-09, D-11, D-12)
**What:** Construir `Filters` canônicos a partir de `interpretation.applied_params`: `q` = string ou `""` (omitir via `buildBoardHref`), `city` = `applied_params.city` **normalizado para slug aceito por `normalizeFilters`** quando suportado, senão `null`; `sort` = `"antigas"` se aplicado, caso contrário `"recentes"`; `page=1`; `vaga=null`. Navegar com `router.replace(buildBoardHref(next), { scroll: false })` e fechar/minimizar chat.
**When to use:** Clique em “Aplicar no board” quando houver parâmetros aplicáveis/úteis. [VERIFIED: frontend/lib/filters.ts, frontend/lib/cities.ts, frontend/components/board/BoardToolbar.tsx]
**Example:**
```typescript
// Source: frontend/lib/filters.ts + frontend/lib/cities.ts [VERIFIED: codebase]
function toBoardFilters(applied: ChatAppliedParams): Filters {
  const rawCity = (applied.city ?? "").trim().toLowerCase();
  // normalizar para slugs de CITY_OPTIONS/normalizeFilters (ex.: "são paulo"/"remoto" -> slug equivalente quando aplicável)
  const candidate = normalizeFilters({ q: applied.q ?? "", city: rawCity, sort: applied.sort ?? "recentes", page: "1" });
  return { ...candidate, page: 1, vaga: null };
}
// aplicar: router.replace(buildBoardHref(toBoardFilters(resp.interpretation.applied_params)), { scroll: false }); setIsOpen(false);
```

### Pattern 4: Abertura canônica de detalhe a partir do chat (D-13..D-16)
**What:** Cada resultado (`JobPublic`) deve abrir o detalhe pelo fluxo canônico (`?vaga=<id>`) reutilizando `JobDetailDialog` e `RevealContact`. Fechar/minimizar chat antes/durante a abertura para evitar sobreposição.
**When to use:** Clique em item de resultado do chat. [VERIFIED: frontend/app/(public)/page.tsx, frontend/components/board/JobGrid.tsx, frontend/components/board/JobDetailDialog.tsx]
**Example:**
```typescript
// Source: frontend/components/board/JobGrid.tsx (syncVagaParam) [VERIFIED: codebase]
// Opção A (canônica de URL): setIsOpen(false); history.replaceState/URL update para ?vaga=<id> e acionar exibição do diálogo.
// Opção B (reuso direto do componente): setIsOpen(false); renderizar <JobDetailDialog job={item} open onClose={...} /> no container do chat,
// garantindo restore de foco e sync de ?vaga conforme comportamento existente.
// Em ambos os casos: item vindo de JobPublic (sem contato) e reveal só no detalhe.
```

### Pattern 5: “Carregar mais” com paginação do envelope (D-07)
**What:** Guardar `page/limit/total` e itens acumulados por consulta ativa. Ao carregar mais, requisitar `page + 1` com a **mesma `message`** da consulta corrente e append de `results.items`, atualizando `interpretation`/meta conforme resposta (ou mantendo a interpretação original se o contrato não mudar por página — definir de forma consistente). Desabilitar ação quando `items.length >= total` ou durante loading.
**When to use:** Resultados paginados no chat. [VERIFIED: backend/app/api/v1/public.py paginação determinística; CONTEXT.md D-07]

### Anti-Patterns to Avoid
- **Expor/armazenar contatos no chat:** Nunca adicionar campos de contato ao estado, render ou tipos do chat; usar apenas `JobPublic` e `RevealContact` no detalhe. [VERIFIED: REQUIREMENTS UI-02, CONTEXT D-16, PROJECT core value]
- **Aplicar estado vazio em respostas degradadas:** Se `applied_params` efetivamente nulos/sem utilidade ou `meta.degraded`/sem resultados automáticos, não oferecer “Aplicar no board” como ação primária equivalente; priorizar guidance/atalho manual (D-08, D-11). [VERIFIED: CONTEXT.md, backend fallback]
- **Montar chat como Server Component ou acoplar a fetch RSC:** Chat depende de interação, timers, fetch no browser e estado efêmero; deve ser `"use client"` e não bloquear render do board. [VERIFIED: padrões de BoardToolbar/JobGrid]
- **Quebrar contrato de URL:** Não inventar params; usar apenas `q/city/sort/page/vaga` via `buildBoardHref`/`normalizeFilters` e resetar `page=1`, limpar `vaga` ao aplicar (D-09). [VERIFIED: frontend/lib/filters.ts]
- **Sobrepor chat e detalhe simultaneamente:** Respeitar D-14 (fechar/minimizar chat ao abrir detalhe). [VERIFIED: CONTEXT.md]
- **Bloquear UI sem feedback ou permitir duplo envio:** D-04 exige indicador visível e bloqueio de envio duplicado. [VERIFIED: CONTEXT.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Montagem de URL canônica do board | Concatenação manual de query string | `buildBoardHref`, `normalizeFilters`, `toApiParams` (`frontend/lib/filters.ts`) | Evita regressão em defaults/omissões/whitelist (`city/sort/page/vaga`). [VERIFIED: codebase] |
| Labels de cidade e consistência visual | Tabelas de cidade ad-hoc | `cityLabel`/`CITY_OPTIONS` (`frontend/lib/cities.ts`) e `formatDateBR` (`frontend/lib/format.ts`) | Mantém acentuação/slug e formato pt-BR consistentes com o board. [VERIFIED: codebase] |
| Fluxo de revelação de contato | Novo fetch/modal de contato no chat | `JobDetailDialog` + `RevealContact` + endpoints existentes | Segurança e anti-bot/anti-enumeração já implementados; contatos nunca no chat. [VERIFIED: codebase, REQUIREMENTS] |
| Parsing/normalização de erro HTTP client | Lógica duplicada espalhada | Padrões de `readError`/`ApiError`/tratamento de timeout em `lib/api.ts` | Consistência de mensagens e tratamento de 429/4xx/timeout. [VERIFIED: frontend/lib/api.ts] |
| Interpretação da resposta do chat | Inferir campos não presentes | Tipos espelhando schemas backend (`IntentContract`, `JobPublic`) | Contrato server-authoritative; evita afirmar suporte inexistente. [VERIFIED: backend schemas] |

**Key insight:** Esta fase é majoritariamente **composição e fidelidade de contrato** (UI + integração) — o risco está em divergir do fluxo canônico, expor contato indevidamente ou mentir sobre parâmetros aplicados/aproximados.

## Common Pitfalls

### Pitfall 1: Contato vaza no chat
**What goes wrong:** Renderizar/logar/armazenar campos de contato vindos de objetos indevidos ou de fetch de detalhe no contexto do chat.
**Why it happens:** Reuso apressado de tipos/componentes ou tentativa de “facilitar” o reveal.
**How to avoid:** Tipar resultados do chat como `JobPublic[]` apenas; nunca chamar reveal no chat; reuso exclusivo via `JobDetailDialog`/`RevealContact`. Revisar estado React/props para garantir ausência de `contact_*`. [VERIFIED: PROJECT, REQUIREMENTS UI-02, D-16]
**Warning signs:** Tipos do chat incluem contato, chamadas a `/reveal-contact` fora do detalhe, ou atributos/data-* com contato.

### Pitfall 2: “Aplicar no board” não reflete `applied_params` reais
**What goes wrong:** Aplicar cidade/sort não suportados, manter `page/vaga` antigos, ou usar `q`/`sort` nulos incorretamente.
**Why it happens:** Mapeamento ad-hoc sem passar por normalização canônica.
**How to avoid:** Derivar filtros via helpers (`normalizeFilters`/`buildBoardHref`), omitir `q/city` quando nulos, mapear sort suportado (`recentes`/`antigas`, default seguro), forçar `page=1` e `vaga=null` (D-09). [VERIFIED: CONTEXT D-09, frontend/lib/filters.ts]
**Warning signs:** URL com params inválidos, board não atualiza como esperado, ou filtros “fantasma”.

### Pitfall 3: Oferecer aplicar/mostrar resultados em degradação
**What goes wrong:** Botão “Aplicar” ativo ou lista tratada como resultados interpretados quando `meta.degraded`/`degradation_reason` indica fallback ou `applied_params` são nulos.
**Why it happens:** UI decide por `items.length` ou `total` ignorando interpretação.
**How to avoid:** Basear comportamento em contrato: checar `degraded/degradation_reason`, `guidance`, `limitations`, `field_statuses` e efetividade de `applied_params` (D-08, D-11, D-12). Mostrar guidance destacada e atalho para busca manual. [VERIFIED: backend/app/api/v1/public.py, CONTEXT]
**Warning signs:** “Nenhum resultado” sem orientação, ou aplicação de filtros vazios após timeout LLM.

### Pitfall 4: Race condition, duplo envio e paginação inconsistente
**What goes wrong:** Respostas antigas sobrescrevem a mais recente; múltiplas páginas carregadas fora de ordem; envios duplicados no loading.
**Why it happens:** Falta de bloqueio/identificação de request ativa.
**How to avoid:** Desabilitar submit/enter durante request (D-04), usar controle de request id/abort, associar “Carregar mais” à consulta/resposta corrente e à mesma `message`. Tratar timeout/rede com retry claro. [VERIFIED: CONTEXT D-04; padrão AbortSignal em lib/api.ts]
**Warning signs:** Spinner some mas conteúdo muda depois; itens duplicados ao paginar.

### Pitfall 5: Conflito de camadas chat/detalhe e foco/acessibilidade
**What goes wrong:** Chat e `<dialog>` de detalhe sobrepostos; foco perdido ao fechar; ESC fecha elemento errado.
**Why it happens:** Dois overlays com gerenciamento próprio.
**How to avoid:** Ao abrir detalhe a partir do chat, minimizar/fechar painel (D-14) e preservar estado para reabertura; seguir padrão de foco/restore já usado em `JobGrid`/`JobDetailDialog` quando aplicável; garantir targets >= 44px e navegação por teclado. [VERIFIED: CONTEXT D-14, JobGrid/JobDetailDialog]
**Warning signs:** Usuário não consegue interagir com detalhe, ou chat reabre vazio.

### Pitfall 6: Divergência de copy/semântica da interpretação
**What goes wrong:** UI rotula “aplicado/aproximado/ignorado” diferente do contrato ou omite motivos/limitations.
**Why it happens:** “Resumir” demais a resposta estruturada.
**How to avoid:** Renderizar a partir de `field_statuses` (status/motivo/entendido vs aplicado) e exibir `limitations`/`meta.guidance` em bloco separado (D-05, D-08). [VERIFIED: backend intent schema/parser/mapper]
**Warning signs:** Usuário não entende por que um critério não filtrou; mensagens contradizem API.

## Code Examples

### Requisição client ao chat-search (padrão de erro/timeout do projeto)
```typescript
// Source: padrão verificado em frontend/lib/api.ts (fetch, readError, AbortSignal.timeout) [VERIFIED: codebase]
export async function chatSearch(payload: ChatSearchRequest): Promise<ChatSearchResponse> {
  const res = await fetch(`${API}/api/v1/public/chat-search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(15_000),
  });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as ChatSearchResponse;
}
```

### Aplicar `applied_params` no board canônico
```typescript
// Source: frontend/lib/filters.ts, frontend/lib/cities.ts, frontend/components/board/BoardToolbar.tsx [VERIFIED: codebase]
import { buildBoardHref, normalizeFilters, type Filters } from "@/lib/filters";

function appliedToFilters(applied: { q: string | null; city: string | null; sort: "recentes" | "antigas" | null }): Filters {
  return normalizeFilters({
    q: applied.q ?? "",
    city: applied.city ?? "",
    sort: applied.sort ?? "recentes",
    page: "1",
    vaga: "",
  });
}
// uso: router.replace(buildBoardHref({ ...appliedToFilters(applied), vaga: null, page: 1 }), { scroll: false });
```

### Renderização fiel da interpretação (contrato)
```typescript
// Source: backend/app/services/intent/schema.py + public.py _chat_degraded_contract/_apply_approx_guidance [VERIFIED: codebase]
const { interpretation } = response;
const guidance = typeof interpretation.meta?.guidance === "string" ? interpretation.meta.guidance : null;
const isDegraded = Boolean(interpretation.meta?.degraded);
// Exibir: "Entendi..." + lista de interpretation.field_statuses (field/status/reason/applied)
// Bloco separado: interpretation.limitations e guidance (quando presentes)
// "Aplicar no board": apenas se !isDegraded && houver applied_params úteis (D-11)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Busca apenas por filtros/keywords manuais no board | Consulta NL → `POST /api/v1/public/chat-search` → interpretação + resultados determinísticos | v1.3 (Phases 19-20, concluídas) | UI de chat pode expor busca assistida sem mudar backend nesta fase. [VERIFIED: STATE.md, REQUIREMENTS] |
| Contato visível/entregue no card/lista (anti-padrão) | Contato revelado somente em detalhe via `RevealContact` protegido | Padrão consolidado no projeto (v1.1+) | Chat deve permanecer contact-free e reutilizar detalhe. [VERIFIED: PROJECT, schemas/componentes] |

**Deprecated/outdated:**
- Qualquer abordagem que envie corpus de vagas ao LLM ou prometa filtros estruturados inexistentes (salário/modalidade/contrato/senioridade) como garantidos — fora de escopo e contrária ao contrato. [VERIFIED: REQUIREMENTS out-of-scope, intent mapper/public.py]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Um bottom sheet/drawer responsivo pode ser implementado de forma acessível com composição de componentes existentes (`<dialog>`/CSS/tokens Tailwind) sem adicionar nova dependência de UI primitives. | Standard Stack / Architecture Patterns | Se acessibilidade/foco/ESC ficar complexa, pode ser necessário ajustar composição (ainda sem backend). Baixo impacto de escopo; exige cuidado em implementação/testes manuais. |
| A2 | Para abrir detalhe a partir do chat, a forma mais simples e canônica será renderizar `JobDetailDialog` com o `JobPublic` retornado (e sincronizar `?vaga`/foco) minimizando o chat, em vez de acoplar ao estado interno do `JobGrid` da lista RSC. | Architecture Patterns / Code Examples | Se houver requisito implícito de seleção compartilhada com o grid, pode ser preciso refatorar integração; validar contra comportamento de deep-link existente. |
| A3 | `normalizeFilters`/`buildBoardHref` aceitam `city` em formas compatíveis com `applied_params.city` canônico quando normalizado para slug/valor esperado; caso contrário, o mapeamento deve converter explicitamente para slug de `CITY_OPTIONS`. | Architecture Patterns (aplicar no board) | Filtro de cidade pode ser descartado silenciosamente se mapeamento estiver incorreto; cobrir com verificação manual/automatizada viável. |

## Open Questions

1. **Ponto de montagem do chat e coordenação com `JobGrid`/`?vaga`**
   - What we know: `page.tsx` (RSC) compõe `BoardToolbar`/`JobGrid` e resolve `?vaga` inicial; `JobGrid` controla `selected` e `syncVagaParam`. D-13 exige fluxo canônico e reuso de `JobDetailDialog`/`RevealContact`. [VERIFIED: codebase]
   - What's unclear: Melhor estratégia de integração: (a) container client no `page.tsx`/layout público que instancia chat e, ao abrir detalhe, aciona navegação/estado compartilhado; ou (b) chat renderiza seu próprio `JobDetailDialog` sincronizando URL/foco.
   - Recommendation: Preferir composição que **reutiliza os componentes** e garante `?vaga`/deep-link consistente (atualizar URL e fechar chat), minimizando acoplamento com internals do RSC; detalhar no plano com base no comportamento observado de `JobGrid`.

2. **Heurística exata de “parâmetros aplicáveis/úteis” para habilitar “Aplicar no board” (D-11)**
   - What we know: Backend fornece `applied_params` finais e pode devolver degradado/sem params; guidance/meta indicam fallback. [VERIFIED: backend/public.py, intent schema]
   - What's unclear: Casos-limite (ex.: apenas `sort` default, `q` composto por aproximações textuais, todos campos ignorados/aproximados mas `q` não nulo).
   - Recommendation: Habilitar quando não degradado e `applied_params` produz diferença útil/segura no board (pelo menos `q` ou `city` ou `sort` explicitamente aplicável conforme contrato), sempre com nota de suporte parcial quando houver aproximações (D-12). Validar contra exemplos reais de resposta.

3. **Estratégia de “Carregar mais” e identidade da consulta**
   - What we know: API pagina por `message/page/limit` e retorna `total`; D-07 pede carregar páginas seguintes. [VERIFIED: schemas/public.py, CONTEXT]
   - What's unclear: Se o usuário edita mensagem após resultados, deve iniciar nova “consulta” limpando acumulação anterior.
   - Recommendation: Tratar cada submissão bem-sucedida como consulta ativa (vincular itens/página à `message` e/ou id interno); “Carregar mais” atua apenas sobre a consulta ativa.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend dev/build/test | ✓ | `v24.14.1` | — |
| npm | Frontend deps/scripts | ✓ | `11.12.1` | — |
| Python | Backend dev/test | ✓ | `3.14.3` | — |
| `pip` | Backend deps (se necessário) | ✗ (não no PATH como `pip`) | — | Usar `python -m pip` se/onde aplicável |
| Groq/LLM externo | Execução real do chat-search em runtime | ? (não verificável estaticamente; requer env/serviço) | — | Backend já degrada com guidance (D-08); UI deve refletir fallback |

**Missing dependencies with no fallback:**
- None identificado para implementar a UI desta fase no repositório (contrato backend e stack frontend presentes). [VERIFIED: codebase]

**Missing dependencies with fallback:**
- `pip` ausente no PATH (usar `python -m pip`). [VERIFIED: environment probe]
- Disponibilidade real do LLM em execução: fallback controlado já previsto pelo backend; frontend deve tratar respostas degradadas/erros. [VERIFIED: backend/public.py, config]

## Validation Architecture

> `workflow.nyquist_validation` está habilitado em `.planning/config.json` (ausente = habilitado; valor `true` confirmado). [VERIFIED: .planning/config.json]

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Backend: pytest 9.1.1 + httpx/ASGI (stack do projeto). Frontend: Vitest 5.0.4 (unit) e Playwright 1.64.0 (E2E) previstos na stack/documentação. [VERIFIED: AGENTS.md/STACK] [ASSUMED: presença/config exata de scripts/arquivos de teste FE a confirmar no plano] |
| Config file | Backend: configs pytest do projeto (se existentes). Frontend: configs Vitest/Playwright se presentes. [ASSUMED: verificar arquivos `vitest.config*`, `playwright.config*`, `pytest.ini/pyproject`] |
| Quick run command | Backend alvo (quando aplicável): `python -m pytest <tests_do_chat_api> -x` (ajustar ao layout real). Frontend unit (se configurado): `npm --prefix frontend test -- --run` ou comando Vitest equivalente. [ASSUMED: comando exato depende dos scripts/configs presentes] |
| Full suite command | Backend: `python -m pytest` (conforme ambiente). Frontend: suíte Vitest/Playwright configurada no repo. [ASSUMED] |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Abrir/fechar chat (sheet/drawer), enviar mensagem sem login, loading visível, bloqueio de duplicado, erro pt-BR com retry | e2e/smoke (preferível) + unit de estado/cliente | Playwright fluxo público do chat (se harness disponível) e/ou Vitest de componente/hook | ❌ Wave 0 (testes de UI de chat não encontrados) [VERIFIED: ausência de arquivos chat no frontend] |
| UI-02 | Render de interpretação (aplicado/ignorado/aproximado) + limitações/guidance; resultados compactos sem contatos; abrir detalhe canônico e reveal só no detalhe | e2e/integration UI + unit de mapeamento/render | Playwright: resposta mockada/ambiente controlado; Vitest: render de estados contratuais | ❌ Wave 0 |
| UI-03 | “Aplicar no board” atualiza URL canônica (`q/city/sort`, `page=1`, limpa `vaga`), fecha chat e preserva comportamento de listagem | e2e/smoke + unit de helper de mapeamento | Playwright navegação/URL; Vitest para `applied_params -> Filters/buildBoardHref` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** Executar checks rápidos relevantes ao que foi alterado (ex.: lint/typecheck frontend `npm --prefix frontend run lint` / build/typecheck conforme scripts disponíveis; testes unitários focados se existirem). [ASSUMED: comandos exatos a confirmar]
- **Per wave merge:** Conjunto de testes da feature (unit + integração/e2e do chat) em ambiente viável.
- **Phase gate:** Fluxos UI-01..UI-03 verdes (automatizados quando viáveis) antes de `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] Testes automatizados da UI de chat (unit/component e/ou e2e) cobrindo UI-01..UI-03 — inexistentes hoje. [VERIFIED]
- [ ] Harness/mocks para `POST /api/v1/public/chat-search` no frontend (resposta ok, degradada, erro 429/4xx/timeout) para validação determinística. [ASSUMED necessidade]
- [ ] Confirmar existência de configs/scripts reais de Vitest/Playwright no frontend e ajustar comandos (stack os prevê, mas config local deve ser verificada no planejamento). [ASSUMED]

*(Nota: cobertura completa de QA-01..QA-03 é responsabilidade da Phase 22; esta fase deve viabilizar validação básica alinhada a UI-01..UI-03 quando o ambiente permitir.)*

## Security Domain

> `security_enforcement` não está explicitamente desabilitado em `.planning/config.json` (ausente = habilitado). [VERIFIED: .planning/config.json]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (fluxo público sem login) | Manter ausência de auth; não introduzir credenciais/tokens de usuário. [VERIFIED: PROJECT/REQUIREMENTS] |
| V3 Session Management | no (apenas estado em memória de aba) | Não persistir sessão/conversa em storage/URL; reload limpa estado (D-02). [VERIFIED: CONTEXT] |
| V4 Access Control | parcial | Respeitar superfícies públicas: contatos nunca no payload/UI do chat; reveal apenas via fluxo existente protegido por Turnstile/rate limit no backend. [VERIFIED: backend/api, RevealContact] |
| V5 Input Validation | yes | Validar/tratar entrada do usuário no cliente (trim, limites coerentes com `CHAT_SEARCH_MAX_MESSAGE_CHARS=400`), tratar respostas/erros como não confiáveis para render (sem HTML injection), confiar na validação server-side. [VERIFIED: backend schema/config, JobDetailDialog renderiza texto] |
| V6 Cryptography | no (nenhum segredo/cripto novo no cliente) | Não manipular segredos; usar `NEXT_PUBLIC_*` apenas para config pública existente. [VERIFIED: padrões atuais] |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Exposição indevida de contato no chat (payload, estado, DOM) | Information Disclosure | Usar somente `JobPublic`; sem chamadas de reveal no chat; reuso de `JobDetailDialog/RevealContact`. [VERIFIED] |
| XSS via renderização de conteúdo retornado (mensagem/guidance/campos) | Tampering / Elevation (client-side) | Renderizar como texto/JSX (padrão existente), nunca `dangerouslySetInnerHTML`; não confiar em strings da API para markup. [VERIFIED: componentes existentes] |
| Abuso/custo/latência do endpoint público de chat-search | Denial of Service | Respeitar bloqueio de duplicados e UX de retry; backend já aplica rate limit/timeout/tamanho (D-04, API-02). Não implementar bypass. [VERIFIED: backend config/public.py] |
| Confusão de origem/URL de API em cliente | Spoofing / Info Disclosure | Reusar `resolveApiBase()`/`API` de `lib/api.ts`; não hardcodar endpoints alternativos. [VERIFIED: frontend/lib/api.ts] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-CONTEXT.md` - decisões travadas D-01..D-16 e discrição. [VERIFIED: codebase read]
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` - requisitos UI-01..UI-03, goal/success criteria e decisões v1.3. [VERIFIED]
- `.planning/phases/19-contrato-de-intencao-e-mapeamento-seguro/19-CONTEXT.md`, `.planning/phases/20-api-publica-de-chat-search-resiliente/20-CONTEXT.md` - contrato de intenção e API consumida. [VERIFIED]
- `backend/app/api/v1/public.py`, `backend/app/schemas/chat.py`, `backend/app/services/intent/schema.py`, `backend/app/schemas/job.py`, `backend/app/core/config.py` - contrato HTTP real, envelope, campos públicos, limites e fallback. [VERIFIED]
- `frontend/app/(public)/page.tsx`, `frontend/lib/filters.ts`, `frontend/lib/jobs.ts`, `frontend/lib/api.ts`, `frontend/components/board/{BoardToolbar,JobGrid,JobDetailDialog,RevealContact,JobCard}.tsx`, `frontend/lib/{cities,format}.ts`, `frontend/app/(public)/public.css`, `frontend/package.json` - padrões de integração, URL canônica, UI/detalhe/reveal, tokens e dependências instaladas. [VERIFIED]
- `.planning/config.json` - `nyquist_validation: true`, `commit_docs: true`. [VERIFIED]
- Probe de ambiente local: `node v24.14.1`, `npm 11.12.1`, `python 3.14.3`, `pip` ausente no PATH. [VERIFIED: shell]

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - baseado em dependências/arquivos reais do repositório e stack fixada.
- Architecture: HIGH - derivado de contratos backend e padrões frontend verificados; alguns detalhes de composição (montagem exata do overlay compartilhado) marcados como questões/assunções.
- Pitfalls: HIGH - ancorados em decisões de produto, contrato server-authoritative e riscos concretos de integração/segurança observados no código.

**Research date:** 2026-11-17
**Valid until:** 2026-12-17 (contratos internos e UI do projeto; revisar se schemas/fluxos canônicos mudarem)
