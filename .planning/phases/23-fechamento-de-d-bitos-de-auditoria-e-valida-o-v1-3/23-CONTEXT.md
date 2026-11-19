# Phase 23: Fechamento de débitos de auditoria e validação v1.3 - Context

**Gathered:** 2026-11-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Fechar os débitos pendentes de auditoria, validação humana/Nyquist e hardening identificados no fechamento do v1.3, sem adicionar novas capacidades ao produto e sem regredir o board público. Esta fase cobre: (1) resolução formal do debug `city-filter-and-chat-ignores-registered-city` (CL-01), incluindo hardening do edge case apontado em review e reteste runtime registrado; (2) fechamento/reconciliação das 4 quick tasks pendentes com evidência ou deferimento justificado (CL-02); (3) execução/registro dos gaps de verificação e UAT das fases 21/22, levando os artefatos a estados finais aceitos e rastreáveis com deferimento por item quando inviável (CL-03); (4) tratamento dos gaps Nyquist 19–22 com compliance quando viável ou desvio aceito documentado (CL-04); e (5) tratamento dos avisos não-bloqueantes viáveis (código, a11y/foco quando viável, segurança Phase 22) e atualização in-place do `v1.3-MILESTONE-AUDIT.md` com gate de `audit-open` limpo para permitir fechamento do milestone (CL-05).

**Fora de escopo:** novas funcionalidades de busca/chat, mudanças de contrato além de correções/hardening necessárias para fechar os débitos, carry-over v1.1/v1.2 (PUB-01..08, handoffs TEST-04/DOC-01/AUD-05, lacunas EXTR/PUBL/SRCH/UIUX) e qualquer ampliação não exigida por CL-01..CL-05.

</domain>

<decisions>
## Implementation Decisions

### CL-01 — Debug de cidade/chat (`city-filter-and-chat-ignores-registered-city`)
- **D-01:** Fazer **hardening de código + testes** do reconhecimento de cidade, não apenas revalidar 22-04. Incluir correção do edge case apontado em `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-REVIEW.md` (fallback raw-text com token `\brio\b` podendo classificar "Rio Grande do Sul"/"Rio Branco" como Rio de Janeiro no mapper de intenção) e adicionar regressões automatizadas apropriadas (backend e/ou frontend, conforme impacto).
- **D-02:** Critério de fechamento de CL-01: **fix aplicado + reteste manual/runtime registrado** do caso reportado (toolbar e chat reconhecendo/aplicando cidade cadastrada corretamente, sem marcação indevida como ignorada). O reteste deve ser executado e documentado nos artefatos de UAT/verificação quando o ambiente permitir.
- **D-03:** Rastreabilidade completa: atualizar **todos os artefatos relevantes** com a decisão/evidência final — `.planning/debug/city-filter-and-chat-ignores-registered-city.md`, `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, `22-VERIFICATION.md` (conforme resultado) e refletir a resolução no `.planning/v1.3-MILESTONE-AUDIT.md`.
- **D-04:** Evidência mínima para mudanças de código em CL-01: **testes automatizados determinísticos + atualização documental** (matriz/UAT/notas/artefatos afetados) proporcional ao risco.

### CL-02 — Quick tasks pendentes e reconciliação
- **D-05:** Cadeia Jacira (`261110-u28`, `261110-uik`): registrar **ambas como concluídas com evidência** (PLAN/SUMMARY, commits/testes existentes), deixando explícito que `261110-uik` é o **comportamento vigente** que supersede o bloqueio original de `u28`.
- **D-06:** `261111-krt` (Next 16.4.6/ESLint 9): aceitar como **concluída com evidência existente** (SUMMARY/verificação histórica), sem revalidação obrigatória salvo se o planejamento/execução identificar drift relevante.
- **D-07:** `261112-ttk` (escape hatch Turnstile teste em prod, sem SUMMARY): converter em **deferred justificado** com justificativa explícita (ex.: validação segura em produção/ambiente controlado fora do escopo local) e evidência do estado atual (PLAN existente). Não marcar como concluída sem evidência de execução.
- **D-08:** Reconciliação formal: atualizar **`.planning/STATE.md` + `.planning/v1.3-MILESTONE-AUDIT.md` + referências necessárias** (ex.: `.planning/REQUIREMENTS.md`/notas de fase/quick-task conforme aplicável) para que nenhuma das 4 tasks permaneça `missing/incomplete` no contexto de `audit-open`, citando evidência ou justificativa de deferimento por task.

### CL-03 — Verificação e UAT das fases 21/22
- **D-09:** Fase 21: **reconciliar com UAT existente**. `21-HUMAN-UAT.md` já está completo (4/4 pass); atualizar `21-VERIFICATION.md` para sair de `human_needed` com base nessa evidência, de forma rastreável.
- **D-10:** Fase 22: executar **reteste do caso CL-01 (cidade)** exigido por D-02 e registrar resultados; para os demais itens de `22-HUMAN-UAT.md`/`22-MANUAL-UAT.md`, registrar **deferimento aceito por item** quando inviável no ambiente, em vez de tentar fechar tudo sem viabilidade. (Itens já marcados como pass em `22-HUMAN-UAT.md` devem ser preservados/reconciliados coerentemente.)
- **D-11:** Estados finais dos artefatos: levar `21-VERIFICATION.md`, `22-VERIFICATION.md`, `22-HUMAN-UAT.md` e `22-MANUAL-UAT.md` a **estados finais aceitos e rastreáveis** (coerentes com os padrões dos arquivos), documentando resultados executados e deferimentos aceitos, de modo que não permaneçam como `human_needed` / `partial` / `draft` sem resolução registrada.
- **D-12:** Política de inviabilidade: **deferimento por item com justificativa** — registrar o que foi executado, o que não foi, motivo da inviabilidade (ambiente/dados/runtime/browser/infra), risco residual e condição/ação futura para validação quando houver.

### CL-04 — Nyquist (fases 19–22)
- **D-13:** Buscar **`nyquist_compliant` quando viável + desvio aceito documentado** quando não for. Criar `.planning/phases/20-api-publica-de-chat-search-resiliente/20-VALIDATION.md` (ausente) e evoluir `19-VALIDATION.md`, `21-VALIDATION.md` e `22-VALIDATION.md` conforme critérios/evidências factíveis (mapeamento de requisitos/tarefas/testes/comandos, wave 0, sign-off etc.). Para critérios não atendíveis, registrar desvio aceito com plano de ação no próprio arquivo, mantendo rastreabilidade honesta.

### CL-05 — Warnings não-bloqueantes, segurança e auditoria final
- **D-14:** Correções de código (quando viáveis): **corrigir `chatSearch` e `canApplyChatToBoard`; fazer a11y/foco viável**.
  - `frontend/lib/api.ts` (`chatSearch`): tratar falha de parse de JSON em resposta 200 como erro seguro tipado (`ApiError` pt-BR) em vez de exceção não normalizada.
  - `frontend/lib/chatApply.ts` (`canApplyChatToBoard`): não habilitar apply quando a cidade em `applied_params` não for normalizável para estado útil do board (evitar apply no-op para cidade-only não suportada/não-whitelist), preservando as regras canônicas existentes (`page=1`, `vaga` limpo, gating de degradado/disabled).
  - `frontend/components/board/chat/ChatPanel.tsx`, `ChatWidget.tsx`, `JobDetailDialog.tsx` e correlatos: aplicar melhorias **focadas e viáveis** de foco/a11y (ex.: foco inicial/trap no diálogo do chat quando aplicável, restauração de foco ao fechar detalhe aberto via chat). Se algum ponto não for viável sem ampliar escopo indevidamente, registrar **deferimento explícito** com justificativa.
  - Adicionar/ajustar testes determinísticos proporcionais às correções realizadas.
- **D-15:** Segurança Phase 22: **criar `SECURITY.md` da Phase 22** em `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-SECURITY.md` (ou artefato equivalente claramente referenciado) documentando controles e revisão aplicáveis ao chat-search (kill-switch/status, rate limit/limites/timeout, validação, busca determinística, privacidade/sem PII e sem contatos no payload, fallback/degradação segura, logging operacional sem conteúdo sensível) e limitações/residuais conhecidos.
- **D-16:** Auditoria final e gate: **atualizar `.planning/v1.3-MILESTONE-AUDIT.md` in-place** para refletir o estado final de cada débito (CL-01..05, debug, quick tasks, UAT/verification, Nyquist, warnings), com evidências/deferimentos aceitos, removendo/ajustando `tech_debt` e notas obsoletas conforme resolução. Validar que `gsd-sdk query audit-open` **não reporte itens novos desta fase** e que o documento permita o fechamento do milestone v1.3.

### OpenCode's Discretion
- Implementação exata do hardening do padrão `rio` no mapper (ex.: fronteiras/contexto/negações para "Rio Grande do Sul", "Rio Branco" etc.), desde que preserve detecção segura de "Rio de Janeiro"/aliases suportados e não invente cidades fora da whitelist.
- Forma concreta de tornar `canApplyChatToBoard`/mapeamento robusto a cidade não-normalizável sem quebrar casos suportados (`sao-paulo`, `rio-de-janeiro`, `belo-horizonte`, `remoto`) e sem aplicar estado vazio enganoso.
- Escopo mínimo de melhorias de foco/a11y considerado “viável” nesta fase (e registro objetivo de qualquer deferimento explícito restante).
- Estrutura/redação final dos estados aceitos em artefatos de verificação/UAT/manual/Nyquist e do `22-SECURITY.md`, desde que rastreáveis, honestos e alinhados às decisões acima.
- Forma de refletir reconciliações em `STATE.md`/`REQUIREMENTS.md` e de executar a checagem final de `audit-open` no ambiente disponível.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo, requisitos e auditoria do milestone
- `.planning/PROJECT.md` — Core value (fricção zero, sem login, contatos protegidos), constraints e estado v1.3.
- `.planning/ROADMAP.md` — Phase 23 goal, depends on 22, success criteria 1–6 e escopo CL-01..CL-05.
- `.planning/REQUIREMENTS.md` — CL-01..CL-05 (fechamento v1.3) e requisitos INT/API/UI/QA já completos que não podem regredir.
- `.planning/STATE.md` — Contexto atual, decisões v1.3, deferred items/quick tasks pendentes e bloqueios conhecidos.
- `.planning/v1.3-MILESTONE-AUDIT.md` — Débitos/tech_debt, gaps Nyquist, integração e warnings a resolver/atualizar (fonte principal de fechamento).

### Debug e evidências de validação (fases 21/22)
- `.planning/debug/city-filter-and-chat-ignores-registered-city.md` — Diagnóstico do bug de cidade (toolbar `q` vs `city`, mapper sem fallback raw-text para SP/RJ/BH quando `candidate.city` ausente).
- `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-VERIFICATION.md` — Status `human_needed` a reconciliar com UAT existente.
- `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-HUMAN-UAT.md` — UAT humano completo (4/4 pass), evidência para reconciliação da fase 21.
- `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-VALIDATION.md` — Nyquist parcial (UI-03 coberto; gaps UI-01/UI-02) a evoluir/desviar documentadamente.
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-VERIFICATION.md` — Verificação `human_needed`; itens manuais/runtime pendentes e notas operacionais.
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md` — UAT parcial com reteste pendente do caso de cidade (CL-01) e itens já passados.
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` — Roteiro draft (7 casos) para execução/deferimento por item.
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` — Matriz QA-01 e rastreabilidade do fix 22-04/limites MVP.
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-VALIDATION.md` — Nyquist draft/parcial da fase 22 a evoluir/desviar documentadamente.
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-REVIEW.md` — Achado de risco `\brio\b` no fallback raw-text do mapper (hardening CL-01).

### Nyquist pendente (fases 19/20)
- `.planning/phases/19-contrato-de-intencao-e-mapeamento-seguro/19-VALIDATION.md` — Nyquist draft/parcial (`nyquist_compliant: false`) a evoluir/desviar documentadamente.
- `.planning/phases/20-api-publica-de-chat-search-resiliente/20-VERIFICATION.md` — Contexto de verificação da fase 20 (20-VALIDATION.md ausente; deve ser criado em CL-04).

### Quick tasks (evidência/disposição CL-02)
- `.planning/quick/261110-u28-bloquear-a-expressao-jacira-chavare-ao-c/261110-u28-PLAN.md` — Plano da quick task u28.
- `.planning/quick/261110-u28-bloquear-a-expressao-jacira-chavare-ao-c/261110-u28-SUMMARY.md` — Evidência de conclusão de u28 (comportamento depois supersedido por uik).
- `.planning/quick/261110-uik-remover-jacira-chavare-do-texto-colado-s/261110-uik-PLAN.md` — Plano da quick task uik.
- `.planning/quick/261110-uik-remover-jacira-chavare-do-texto-colado-s/261110-uik-SUMMARY.md` — Evidência de conclusão de uik (estado final vigente).
- `.planning/quick/261111-krt-atualizar-next-16-4-6-eslint-9/261111-krt-PLAN.md` — Plano da quick task krt.
- `.planning/quick/261111-krt-atualizar-next-16-4-6-eslint-9/261111-krt-SUMMARY.md` — Evidência histórica de conclusão de krt.
- `.planning/quick/261112-ttk-escape-hatch-turnstile-teste-em-prod/261112-ttk-PLAN.md` — Plano existente de ttk (sem SUMMARY; candidato a deferimento justificado).

### Código e testes impactados (CL-01 / CL-05)
- `backend/app/services/intent/mapper.py` — Mapeamento de cidade/intenção; fallback raw-text e padrões (`_detect_city_from_raw_text`, `_RAW_TEXT_CITY_PATTERNS`) alvo do hardening CL-01.
- `backend/tests/test_intent_mapper.py` — Regressões de mapeamento de intenção/cidade.
- `backend/tests/test_intent_parser.py` — Regressões do parser/fluxo de intenção relacionadas.
- `backend/app/api/v1/public.py` — Contrato/fluxo `chat-search` e controles (contexto para segurança/observabilidade documentada).
- `frontend/lib/cities.ts` — Resolução/promoção de texto de cidade suportada no board (`resolveCitySlugFromText`).
- `frontend/lib/cities.test.ts` — Testes de resolução de cidade no frontend.
- `frontend/components/board/BoardToolbar.tsx` — Promoção de cidade digitada para filtro canônico `city=<slug>`.
- `frontend/lib/chatApply.ts` — Gating/mapeamento de `applied_params` para board canônico (`canApplyChatToBoard`, `appliedParamsToBoardFilters`).
- `frontend/lib/chatApply.test.ts` — Cobertura de regras de apply/gating.
- `frontend/lib/api.ts` — Cliente `chatSearch`/status e tratamento de erros (parse JSON defensivo em 200).
- `frontend/components/board/chat/ChatWidget.tsx` — Orquestração do chat, apply, abertura de detalhe e foco/comportamento.
- `frontend/components/board/chat/ChatPanel.tsx` — Container/dialog do chat (foco/a11y).
- `frontend/components/board/chat/ChatResultsList.tsx` — Ações/resultados do chat (contexto de apply/manual).
- `frontend/components/board/JobDetailDialog.tsx` — Fluxo canônico de detalhe/reveal e restauração de foco relacionada.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Intent mapper determinístico:** `backend/app/services/intent/mapper.py` já possui `_resolve_city_safe` e fallback raw-text (`_detect_city_from_raw_text`) para whitelist; ponto direto para hardening do token `rio` com salvaguardas e testes em `backend/tests/test_intent_mapper.py`/`test_intent_parser.py`.
- **Normalização de cidade no frontend:** `frontend/lib/cities.ts` (`resolveCitySlugFromText`) + `BoardToolbar.tsx` já promovem texto exato suportado para `city=<slug>`; testes puros em `frontend/lib/cities.test.ts`.
- **Apply canônico do chat:** `frontend/lib/chatApply.ts` centraliza `appliedParamsToBoardFilters` e `canApplyChatToBoard`; `frontend/lib/chatApply.test.ts` cobre regras existentes (degraded/disabled, mapeamento). Base para eliminar apply no-op de cidade não-normalizável.
- **Cliente chat-search:** `frontend/lib/api.ts` já padroniza `ApiError`, timeout e erros de transporte/status; falta apenas endurecer parse de JSON em respostas 200 de `chatSearch`.
- **Artefatos de validação/hardening existentes:** VERIFICATION/HUMAN-UAT/MANUAL-UAT/VALIDATION/MVP/REVIEW nas fases 21/22 fornecem estrutura e histórico para reconciliação, Nyquist e documentação de deferimentos.

### Established Patterns
- **Busca determinística e contratos públicos:** LLM apenas extrai parâmetros; resultados via `list_published`/`JobPublic` sem contatos no chat; `applied_params`/`field_statuses`/limitations server-authoritative.
- **URL canônica do board:** `normalizeFilters`/`buildBoardHref` com `q/city/sort/page/vaga` e resets esperados (`page=1`, `vaga` limpo ao aplicar).
- **Evidência honesta:** documentar lacunas/deferimentos explicitamente (suporte parcial, itens inviáveis, desvios Nyquist) sem afirmar capacidades/validações inexistentes.
- **Testes determinísticos e seams mockados:** backend pytest (intent/chat/rate limit) e frontend Vitest para lógica pura; mudanças devem ser proporcionais e rastreáveis.

### Integration Points
- **Correções CL-01:** mapper/backend + testes de intent; possível ajuste de expectativas/documentação em artefatos 22 (UAT/manual/verification/MVP) e debug/audit.
- **Correções CL-05:** `frontend/lib/api.ts`, `frontend/lib/chatApply.ts` (+ testes), componentes de chat/dialog para a11y/foco quando viável.
- **Documentação/fechamento:** criação/atualização de `.planning/phases/20-api-publica-de-chat-search-resiliente/20-VALIDATION.md`, `19/21/22-VALIDATION.md`, `22-SECURITY.md`, reconciliação de 21/22 VERIFICATION/UAT/MANUAL-UAT, debug session, `STATE.md`, `REQUIREMENTS.md` (se necessário para rastreabilidade) e `.planning/v1.3-MILESTONE-AUDIT.md`.
- **Gate final:** checagem operacional `gsd-sdk query audit-open` e consistência entre decisões, evidências e status dos artefatos.

</code_context>

<specifics>
## Specific Ideas

- **Achado concreto a tratar:** `22-REVIEW.md` registrou que o fallback raw-text com padrão `\brio\b` pode confundir "Rio Grande do Sul"/"Rio Branco" com "Rio de Janeiro"; o hardening deve cobrir esse tipo de falso positivo sem perder casos válidos suportados.
- **Inconsistência de artefatos a reconciliar:** `21-HUMAN-UAT.md` está completo (4/4 pass) enquanto `21-VERIFICATION.md` ainda está `human_needed` — usar a evidência existente para fechar de forma rastreável (D-09).
- **Estado atual de 22:** `22-HUMAN-UAT.md` parcial (inclui reteste pendente do caso de cidade) e `22-MANUAL-UAT.md` draft; CL-01 exige reteste runtime registrado do caso de cidade, e os demais itens podem seguir deferimento por item com justificativa se inviáveis (D-02, D-10, D-12).
- **Quick task `261112-ttk`:** possui apenas PLAN (sem SUMMARY) e envolve teste em produção; decisão é **deferimento justificado** com evidência/referência, não conclusão sem execução comprovada (D-07).
- **Warnings de auditoria a fechar quando viáveis:** `canApplyChatToBoard` (apply no-op para cidade não-normalizável), parse defensivo de JSON em `chatSearch`, robustez de foco/a11y do chat/detail, e `SECURITY.md` da Phase 22 (D-14, D-15).

</specifics>

<deferred>
## Deferred Ideas

- `261112-ttk-escape-hatch-turnstile-teste-em-prod`: **deferred justificado (in-scope CL-02)** — sem SUMMARY/evidência de execução e dependente de validação segura em produção/ambiente controlado; registrar justificativa, estado atual (PLAN) e manter fora de `missing/incomplete` no audit-open.

</deferred>

---

*Phase: 23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3*
*Context gathered: 2026-11-19*
