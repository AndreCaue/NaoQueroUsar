# Phase 24: Corrigir conflito crítico de cidade e resíduos de review - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-21
**Phase:** 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review
**Areas discussed:** Política de conflito CR-01, Matching de influência WR-03, Estratégia de foco WR-01

---

## Política de conflito CR-01

### Q1: Comportamento em conflito raw-text vs cidade candidata

| Option | Description | Selected |
|--------|-------------|----------|
| Conflito seguro (Recomendado) | Se raw-text detectar conflito, ou se a cidade suportada detectada no raw divergir da cidade candidata resolvida, aplicar city=null com status ignorado e reason conflict_resolved. Nunca aplicar cidade errada. | ✓ |
| Priorizar candidato se whitelist | Se candidate.city resolver para whitelist, aplicar candidato mesmo com ambiguidade no raw, exceto conflitos óbvios já detectados. | |
| You decide | Deixa o OpenCode escolher a regra determinística mais segura. | |

**User's choice:** Conflito seguro (Recomendado)
**Notes:** Alinhar com 24-RESEARCH/23-REVIEW; fechar CR-01 sem aplicar cidade errada.

### Q2: Fonte de verdade para sinal de cidade no raw

| Option | Description | Selected |
|--------|-------------|----------|
| Usar _detect_city_from_raw_text (Recomendado) | Reutilizar detecção canônica existente (aliases, abreviações, remoto/home office, conflito). | ✓ |
| Estender heurística inline atual | Adicionar mais tokens/regex no bloco inline de map_intent. | |
| You decide | OpenCode escolhe a abordagem determinística mais simples e segura. | |

**User's choice:** Usar _detect_city_from_raw_text (Recomendado)
**Notes:** Evitar duplicação de lógica e assimetria de alias/remoto.

### Q3: Casos limítrofes

| Option | Description | Selected |
|--------|-------------|----------|
| Seguro e compatível (Recomendado) | Mesma cidade canônica aplica; candidato ausente + 1 cidade suportada pode aplicar; candidato não-whitelist permanece not_in_whitelist; conflito raw explícito não promove cidade errada. | ✓ |
| Conservador máximo | Qualquer ambiguidade/divergência raw/candidato resulta em city=null ignorado. | |
| You decide | OpenCode fixa política determinística mais segura sem regredir casos suportados. | |

**User's choice:** Seguro e compatível (Recomendado)
**Notes:** Preservar comportamento útil existente sem reabrir CR-01.

### Q4: Cobertura de regressão CR-01

| Option | Description | Selected |
|--------|-------------|----------|
| Matriz focada (Recomendado) | Exemplos do audit + aliases/abreviações/remoto + mesma cidade canônica + candidato ausente + não-whitelist. | ✓ |
| Só casos do audit | Testa apenas exemplos nomeados em CR-01. | |
| You decide | OpenCode define matriz mínima suficiente. | |

**User's choice:** Matriz focada (Recomendado)
**Notes:** Cobrir buracos de alias/remoto/precedência sem explosão de casos.

---

## Matching de influência WR-03

### Q1: Estratégia de matching

| Option | Description | Selected |
|--------|-------------|----------|
| Token-set normalizado (Recomendado) | Comparar tokens normalizados (`_strip_accents_lower`, split por whitespace) por membership em conjunto, não substring no string inteiro. | ✓ |
| Boundary regex/acento-aware | Usar regex com limites de palavra sobre texto normalizado. | |
| You decide | OpenCode escolhe comparação determinística mais segura. | |

**User's choice:** Token-set normalizado (Recomendado)
**Notes:** Simples, determinístico, alinhado ao padrão atual.

### Q2: Escopo da mudança

| Option | Description | Selected |
|--------|-------------|----------|
| Só comparação por token (Recomendado) | Trocar `k in aq` por membership em token-set de `applied_q`, preservando extração/normalização existente. | ✓ |
| Refatorar influência inteira | Reescrever toda heurística de influência de campos não nativos. | |
| You decide | OpenCode aplica a menor mudança segura. | |

**User's choice:** Só comparação por token (Recomendado)
**Notes:** Minimizar risco e fechar WR-03 com regressão clara.

---

## Estratégia de foco WR-01

### Q1: Estratégia de montagem/foco ao abrir detalhe

| Option | Description | Selected |
|--------|-------------|----------|
| Manter painel montado (Recomendado) | Não fechar/desmontar ChatPanel ao abrir detalhe; trigger original permanece montado; ao fechar detalhe, foca trigger se conectado, senão fallback estável montado. | ✓ |
| Fechar painel + fallback estável | Fecha painel ao abrir detalhe e restaura foco para fallback sempre montado/reabre painel ao fechar detalhe. | |
| You decide | OpenCode escolhe estratégia mais simples e estável. | |

**User's choice:** Manter painel montado (Recomendado)
**Notes:** Alinha com 24-UI-SPEC; dialog nativo já é modal.

### Q2: Prioridade de restauração de foco

| Option | Description | Selected |
|--------|-------------|----------|
| Trigger original, senão fallback (Recomendado) | Tenta focar trigger de origem se `isConnected`; senão foca controle estável montado no chat. Nunca `document.body`. | ✓ |
| Sempre botão fechar do chat | Sempre foca botão fechar do chat ao fechar detalhe. | |
| You decide | OpenCode escolhe prioridade mais acessível e estável. | |

**User's choice:** Trigger original, senão fallback (Recomendado)
**Notes:** WR-02/D-14 (focus trap completo) permanece deferido.

---

## OpenCode's Discretion

- Forma exata de integrar `_detect_city_from_raw_text()` no fluxo de `map_intent()` preservando reason codes/mensagens compatíveis.
- Estrutura exata do token-set WR-03 e nomes/organização dos testes.
- Escolha do fallback estável montado em WR-01 (botão fechar do ChatPanel ou controle equivalente), desde que montado/visível e sem `document.body`.
- Ordem de planos/commits, mantendo escopo focado e regressões determinísticas.

## Deferred Ideas

None — discussion stayed within phase scope. WR-02/D-14 (focus trap completo do chat) permanece residual deferido já reconhecido por roadmap/auditoria.