# Phase 24: Corrigir conflito crítico de cidade e resíduos de review - Context

**Gathered:** 2026-11-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Fechar o gap crítico de segurança/determinismo do chat-search identificado na auditoria v1.3 e resíduos de review viáveis da Phase 23, sem adicionar novas capacidades e sem regredir o board público. Esta fase cobre: (1) **CR-01/CL-01** — eliminar bypass de conflito de cidade no mapper quando há cidade candidata presente e o texto bruto expressa conflito por alias/abreviação/remoto (ex.: "sp ou rio de janeiro", "remoto ou são paulo"), garantindo que nenhuma cidade errada seja aplicada; (2) **WR-03/CL-05** — remover detecção de influência de campos não nativos baseada em substring frágil sobre `applied_q` inteiro, evitando falsa aproximação; (3) **WR-01/CL-05** — restaurar foco ao fechar detalhe de vaga aberto pelo chat para um controle montado/estável, sem perda de foco para `document.body` em fluxo de teclado. Inclui regressões automatizadas e preservação de contratos públicos/API/`JobPublic` e fluxo canônico do board.

**Fora de escopo:** novas funcionalidades de busca/chat, mudança de contrato público, busca semântica, focus trap completo do chat (WR-02/D-14, residual aceito/deferido), reconciliação de gate/audit-open CL-02 e atualização final de auditoria v1.3 (Phase 25), e carry-over v1.1/v1.2.

</domain>

<decisions>
## Implementation Decisions

### CR-01 — Política de conflito de cidade no mapper
- **D-01:** **Conflito seguro.** Quando o texto bruto indicar conflito de cidade suportada/alias/abreviação/remoto, ou quando a cidade suportada detectada no raw divergir da cidade candidata resolvida, o mapper deve retornar `city=null`, `FieldStatus.IGNORADO` e `reason_code="conflict_resolved"`. Nunca aplicar cidade errada. Exemplos obrigatórios: "sp ou rio de janeiro" com candidato SP; "remoto ou são paulo" com candidato Remoto; raw detecta SP e candidato resolve RJ.
- **D-02:** **Fonte de verdade canônica para raw.** Reutilizar `_detect_city_from_raw_text()` como sinal canônico de cidade/conflito no texto bruto (já cobre aliases, abreviações, remoto/home office e conflito). Não duplicar heurística inline frágil em `map_intent()`; a lógica inline atual deve ser substituída/integrada de forma a usar o detector canônico.
- **D-03:** **Casos limítrofes — seguro e compatível.** Mesma cidade canônica (raw SP, candidato "São Paulo") = aplicar com segurança. Candidato ausente + raw detecta exatamente 1 cidade suportada segura = pode aplicar (preservar comportamento útil atual). Candidato não-whitelist (ex.: Campinas) permanece `not_in_whitelist`/ignorado; conflito raw explícito (ex.: Campinas vs Remoto) não deve promover cidade errada. Divergência raw-vs-candidato resolvido em cidades suportadas diferentes = `conflict_resolved`.
- **D-04:** **Regressão em matriz focada.** Cobrir os exemplos do audit/review CR-01 + aliases/abreviações/remoto, acordo de mesma cidade canônica, candidato ausente, candidato não-whitelist sem regressão, e casos onde candidato presente não deve bypassar conflito raw. Não limitar apenas aos dois exemplos nomeados.

### WR-03 — Influência de campos não nativos em `applied_q`
- **D-05:** **Matching por token-set normalizado.** Detectar influência comparando tokens normalizados (`_strip_accents_lower`, split por whitespace) por membership em conjunto de tokens de `applied_q`, não por substring no string inteiro. Isso fecha falso positivo onde token curto casa dentro de palavra maior.
- **D-06:** **Escopo mínimo.** Alterar apenas a comparação de influência (substituir `k in aq` por membership em token-set), preservando extração de termos, normalização e semântica existente de status/limitações. Incluir regressão automatizada para caso que seria falso positivo por substring e continua correto por token.

### WR-01 — Restauração de foco no chat/detalhe
- **D-07:** **Manter ChatPanel montado.** Ao abrir detalhe de vaga a partir do chat, não desmontar/fechar o `ChatPanel`; manter painel montado atrás do dialog nativo para que o trigger original permaneça no DOM. O detalhe continua abrindo pelo fluxo canônico (`JobDetailDialog`/`?vaga`).
- **D-08:** **Prioridade de restauração de foco.** Ao fechar detalhe, restaurar foco para o trigger original se `trigger?.isConnected`; caso contrário, focar fallback estável montado no chat (ex.: botão fechar do painel/chat). Nunca restaurar foco para `document.body`. Não implementar focus trap custom (WR-02/D-14 permanece deferido).

### OpenCode's Discretion
- Forma exata de integrar `_detect_city_from_raw_text()` no fluxo de `map_intent()` preservando reason codes/mensagens existentes onde compatível.
- Estrutura exata do token-set WR-03 (variável local/set inline) e nomes de testes.
- Escolha do fallback estável montado em WR-01 (botão fechar do ChatPanel ou outro controle montado visível), desde que atenda D-08 e UI-SPEC.
- Se adicionar helper pequeno para foco seguro, manter escopo local sem criar abstração ampla.
- Ordem de commits/planos, desde que cada gap tenha cobertura determinística e sem regressão.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e fechamento v1.3
- `.planning/ROADMAP.md` §Phase 24 — Goal, success criteria, dependência da Phase 23 e gap closure CL-01/CL-05.
- `.planning/REQUIREMENTS.md` — CL-01 e CL-05 (pendentes para Phase 24); INT-03/API-03/UI-01/UI-02/UI-03/QA-01..03 como contratos que não podem regredir.
- `.planning/v1.3-MILESTONE-AUDIT.md` — Fonte do gap: CR-01 blocker, WR-01/WR-03 resíduos, status CL-01/CL-05 unsatisfied.
- `.planning/STATE.md` — Estado atual do milestone e contexto acumulado.

### Evidências e decisões anteriores
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-REVIEW.md` — Achados CR-01, WR-01, WR-02, WR-03 com arquivos/linhas e sugestão de correção.
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-CONTEXT.md` — Decisões D-01/D-14 e residual focus trap deferido; hardening anterior de cidade.
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-VERIFICATION.md` — Evidência de gaps remanescentes pós-Phase 23.
- `.planning/debug/city-filter-and-chat-ignores-registered-city.md` — Contexto do debug de cidade (resolvido com deferral runtime aceito; CR-01 é defeito remanescente distinto).

### Specs e pesquisa da Phase 24
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-UI-SPEC.md` — Contrato visual/interação aprovado; WR-01 foco montado/estável, sem focus trap custom, sem mudança de copy/contrato.
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-RESEARCH.md` — Análise de causa raiz CR-01/WR-01/WR-03, padrões, pitfalls e mapa de testes.

### Código alvo
- `backend/app/services/intent/mapper.py` — `map_intent()`, `_detect_city_from_raw_text()`, `_resolve_city_safe()`, detecção de influência não nativa; alvo CR-01 e WR-03.
- `backend/tests/test_intent_mapper.py` — Regressões determinísticas do mapper; principal alvo de novos casos.
- `frontend/components/board/chat/ChatWidget.tsx` — Orquestração open/close detail e foco; alvo WR-01.
- `frontend/components/board/chat/ChatPanel.tsx` — Semântica de dialog do chat; verificar compatibilidade com painel montado e fallback de foco.
- `frontend/components/board/chat/ChatThread.tsx` — Propagação de trigger para abertura de detalhe.
- `frontend/components/board/chat/ChatResultsList.tsx` — Encadeamento de trigger.
- `frontend/components/board/chat/ChatResultItem.tsx` — Origem do trigger clicável/teclável.
- `frontend/components/board/JobDetailDialog.tsx` — Dialog nativo canônico de detalhe/reveal.
- `frontend/lib/chatApply.ts` e `frontend/lib/chatApply.test.ts` — Contrato de apply canônico; preservar sem regressão.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_detect_city_from_raw_text()` em `backend/app/services/intent/mapper.py`: já detecta cidades suportadas por aliases/abreviações/remoto e retorna `conflict_resolved`; base canônica para CR-01.
- `_resolve_city_safe()` / `resolve_city()`: normalização whitelist segura para candidato; deve ser combinada com sinal raw sem confiar cegamente no candidato.
- `backend/tests/test_intent_mapper.py`: suíte determinística existente com padrões de asserção para `applied_params`, `field_statuses`, `limitations` e `meta.reason_codes`.
- `ChatWidget` já propaga `detailTriggerRef` e tenta restaurar foco em `requestAnimationFrame`; precisa apenas de ajuste de montagem/fallback estável.
- `JobDetailDialog` usa `<dialog>.showModal()` nativo; WR-01 deve trabalhar com esse comportamento, não substituí-lo.

### Established Patterns
- **Server-authoritative intent mapping:** candidato LLM é não confiável; mapper decide `applied_params`, `field_statuses`, limitações e reason codes.
- **Deterministic gap closure:** regressão primeiro/ajuste focado, sem ampliar escopo. Phase 23 usou esse padrão.
- **Chat público sem contatos:** preservar `JobPublic` e fluxo canônico de detalhe/reveal.
- **URL canônica do board:** `q/city/sort/page/vaga` via `buildBoardHref`/`normalizeFilters`; chat apply não deve regredir.
- **A11y residual explícito:** WR-02/D-14 (focus trap completo) é deferido; não expandir.

### Integration Points
- **CR-01/WR-03:** `backend/app/services/intent/mapper.py` + `backend/tests/test_intent_mapper.py` (possível ajuste colateral em `test_intent_parser.py` apenas se contrato/razões mudarem de forma esperada).
- **WR-01:** `frontend/components/board/chat/ChatWidget.tsx` (principal), possivelmente `ChatPanel.tsx` para fallback de foco; cadeia de trigger em `ChatThread.tsx`/`ChatResultsList.tsx`/`ChatResultItem.tsx` já existe.
- **Verificação:** pytest mapper/intent; vitest chatApply e/ou verificação manual de teclado conforme harness disponível.

</code_context>

<specifics>
## Specific Ideas

- Casos CR-01 nomeados pela auditoria/review: `"vaga em sp ou rio de janeiro"` com candidato `SP` não pode aplicar São Paulo; `"vaga remoto ou são paulo"` com candidato `Remoto` não pode aplicar Remoto.
- Usar `_detect_city_from_raw_text()` evita duplicar tabela de aliases e mantém consistência com hardening 23-01.
- WR-01 deve preservar a UX atual do chat e do detalhe; o painel pode permanecer montado atrás do dialog nativo, que já é modal.
- WR-03 deve ser correção mínima: trocar substring por membership em token-set normalizado, com regressão clara.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

### Reviewed Todos (not folded)
None — `gsd-sdk query todo.match-phase "24"` returned 0 matches.

</deferred>

---

*Phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review*
*Context gathered: 2026-11-21*
