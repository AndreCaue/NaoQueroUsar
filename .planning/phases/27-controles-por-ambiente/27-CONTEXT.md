# Phase 27: Controles por Ambiente - Context

**Gathered:** 2026-11-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase entrega controles operacionais por variáveis de ambiente para anúncios e doações, sem remover código. Escopo: ocultar/exibir espaços publicitários por flag única no `.env` e configurar o destino do botão Doações por link no `.env`, com comportamento seguro quando ausente/desabilitado. Não inclui novos formatos de anúncio, monetização ativa, processamento financeiro interno, nem redesign de layout.

</domain>

<decisions>
## Implementation Decisions

### Anúncios (flag única de ambiente)
- **D-01:** Quando a flag única de anúncios no `.env` estiver ausente ou vazia, o padrão é **mostrar anúncios** (comportamento atual preservado). O operador precisa desativar explicitamente para ocultar.
- **D-02:** Quando a flag estiver desativada, **todos os espaços publicitários** não aparecem na interface pública: header (`AdSlot` variant `header`), sidebar (`AdSlot` variant `sidebar`) e inline no grid (`AdSlot` variant `inline` inserido pelo `JobGrid`). Quando ativada, voltam a ser exibidos normalmente (SC1/SC2).
- **D-03:** O controle é único/uniforme — não há exceção por placement nesta fase.

### Doações (link por ambiente)
- **D-04:** Quando o link de doação estiver configurado no `.env`, o botão "Doações" do header abre o link configurado **diretamente em nova aba** (`target="_blank"` + `rel="noopener noreferrer"`), sem passar pela página interna `/doacoes` (SC3).
- **D-05:** Quando o link de doação estiver ausente ou desabilitado, o botão "Doações" mantém comportamento seguro: leva para a página interna `/doacoes` (comportamento atual), sem destino inválido (SC4).
- **D-06:** A página interna `/doacoes` continua existindo e acessível mesmo quando o link externo estiver configurado (útil para acesso direto/bookmarks/SEO). O botão do header aponta para o externo quando configurado; a página em si não precisa redirecionar.

### OpenCode's Discretion
- Nome exato das variáveis de ambiente, formato aceito (ex.: `true/false/1/0`) e validação/sanitização de valores.
- Onde declarar cada variável (frontend `.env`/Vercel para UI pública; manter convenção `NEXT_PUBLIC_*` apenas quando necessário no client bundle, sem segredos).
- Comportamento de layout quando anúncios ocultos (colapso de espaço vs preservação) desde que os espaços publicitários não apareçam na interface pública.
- Validação do link de doação (ex.: aceitar apenas URL absoluta http/https) para garantir comportamento seguro quando valor inválido.
- Ajustes mínimos na página `/doacoes` para refletir o estado configurado, se útil, sem alterar o escopo da fase.
- Atualização de testes/scripts afetados (ex.: `frontend/scripts/verify-ssr.ps1` assume "Espaço publicitário") para cobrir os dois estados de ambiente.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` §"Phase 27: Controles por Ambiente" — Goal, depends on Phase 26, requirements ADS-01/DONA-01, success criteria.
- `.planning/REQUIREMENTS.md` §"Configuração por Ambiente" — ADS-01 (flag única no `.env` para ocultar espaços publicitários, sem remover código) e DONA-01 (botão Doações abre link configurado no `.env`; comportamento seguro quando ausente/desabilitado).
- `.planning/PROJECT.md` §"Current Milestone: v1.4 Polimento UX e Admin" — contexto do milestone; manter fricção zero do candidato.

### Anúncios (código atual)
- `frontend/components/board/AdSlot.tsx` — componente único de placeholder publicitário; variantes `header`, `sidebar`, `inline`; `aria-label="Espaço publicitário"`.
- `frontend/app/(public)/page.tsx` — usa `<AdSlot variant="header" />` acima do board e `<AdSlot variant="sidebar" />` no aside desktop.
- `frontend/components/board/JobGrid.tsx` — client component; insere `<AdSlot variant="inline" />` a cada 6 vagas (`(index + 1) % 6 === 0`).

### Doações (código atual)
- `frontend/app/(public)/layout.tsx` — header público com botão "Doações" atual como `Link href="/doacoes"`; ponto principal de aplicação do D-04/D-05.
- `frontend/app/(public)/doacoes/page.tsx` — página interna atual com placeholder "Em breve..." e CTA de volta para vagas; deve permanecer acessível (D-06).
- `frontend/app/(public)/public.css` — token `--color-donate: #facc15` usado pelo botão Doações.

### Convenções de ambiente/config
- `frontend/.env.example` — convenções de env frontend, aviso de `NEXT_PUBLIC_*` embutido no bundle, `BACKEND_API_URL` runtime server-side, comentários de deploy Vercel.
- `frontend/.env.local.example` — defaults locais mínimos.
- `backend/.env.example` — convenções de env backend (referência de estilo; ads/doações são UI pública, avaliar onde faz mais sentido).

### Verificação/testes afetados
- `frontend/scripts/verify-ssr.ps1` — já verifica presença de "Espaço publicitário" e "Doações"; precisará acomodar o comportamento controlado por env.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/components/board/AdSlot.tsx`: ponto único para renderização de anúncios; ideal para aplicar a flag sem espalhar condicionais pelos consumidores.
- `frontend/app/(public)/layout.tsx`: já possui o botão Doações com estilo estabelecido (`text-donate`, borda amarela discreta); reaproveitar estilo ao trocar destino/comportamento.
- `frontend/app/(public)/doacoes/page.tsx`: fallback interno seguro já existe; atende D-05 sem criar nova rota.

### Established Patterns
- Env frontend público usa `NEXT_PUBLIC_*` para valores acessíveis no browser; `BACKEND_API_URL` é lido server-side em runtime (`frontend/lib/jobs.ts`).
- `AdSlot` é componente simples sem `"use client"`; usado por `page.tsx` (Server Component) e `JobGrid.tsx` (Client Component).
- Layout público (`frontend/app/(public)/layout.tsx`) é Server Component — decisões de env podem ser avaliadas server-side quando possível.
- Padrão visual: dark mode, roxo principal, amarelo discreto para doações (`#facc15` / `--color-donate`).

### Integration Points
- `frontend/components/board/AdSlot.tsx` — gate central da flag de anúncios (D-01/D-02/D-03).
- `frontend/components/board/JobGrid.tsx` — verificar impacto de ocultar inline ads no grid/keys.
- `frontend/app/(public)/page.tsx` — header/sidebar ads; garantir ausência visual quando desativado.
- `frontend/app/(public)/layout.tsx` — comportamento do botão Doações por env (D-04/D-05).
- `frontend/app/(public)/doacoes/page.tsx` — manter acessível; possível ajuste de copy conforme estado, a critério de implementação.
- `frontend/.env.example` e docs de deploy — documentar novas variáveis.

</code_context>

<specifics>
## Specific Ideas

No specific product references — seguir as decisões capturadas, os critérios de sucesso da fase e os padrões visuais existentes.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 27-controles-por-ambiente*
*Context gathered: 2026-11-22*
