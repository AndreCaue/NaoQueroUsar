---
phase: 23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3
verified: 2026-11-20T21:30:00Z
reverified: 2026-11-22T00:00:00Z
last_reconciled: 2026-11-22
status: gaps_closed_with_accepted_residuals
score: 6/6 success criteria verified with accepted residuals
requirements_coverage:
  CL-01: satisfied
  CL-02: satisfied_with_formal_acceptance
  CL-03: passed
  CL-04: passed
  CL-05: satisfied_with_accepted_residuals
gaps_original:
  - truth: "O debug session de cidade/chat é resolvido ou formalmente fechado com decisão registrada e o filtro de cidade/chat passa a respeitar a cidade cadastrada corretamente, sem pendências críticas abertas."
    status: failed
    reason: "23-REVIEW.md (phase artifact, status issues_found) reported CR-01 as a critical defect in `backend/app/services/intent/mapper.py`; defect was present at 2026-11-20 verification. Closed by Phase 24 (see reconciliation)."
    artifacts:
      - path: "backend/app/services/intent/mapper.py"
        issue: "Historical CR-01: candidate-present raw-text conflict bypass."
      - path: "backend/tests/test_intent_mapper.py"
        issue: "Historical: missing CR-01 regression coverage."
      - path: ".planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-REVIEW.md"
        issue: "Historical review evidence recorded CR-01 (critical), status issues_found."
    missing:
      - "Closed by Phase 24: raw-text alias/abbreviation/remoto conflicts honored with candidate present; deterministic regressions added; evidence updated."
  - truth: "As 4 quick tasks pendentes têm status definido e nenhuma permanece como `missing`/`incomplete` no `audit-open` (ou no contexto de fechamento documentado com justificativa rastreável quando heurística divergir)."
    status: partial
    reason: "Dispositions documented; audit-open heuristic residual remained for 4 known quick tasks. Formal acceptance scope handled in Phase 25 (D-01/D-03/D-04)."
    artifacts:
      - path: ".planning/STATE.md"
        issue: "Documented dispositions/evidence; heuristic audit-open classification may remain."
      - path: ".planning/REQUIREMENTS.md"
        issue: "CL-02 marked complete with evidence/deferment; formal acceptance scope recorded in Phase 25 closure artifacts."
      - path: ".planning/v1.3-MILESTONE-AUDIT.md"
        issue: "Audit records heuristic residual honestly; formal acceptance scoped to 4 known slugs with no-new-missing condition."
    missing:
      - "Formal acceptance scoped to 4 known quick-task slugs (u28/uik/krt/ttk) with evidence/disposition and no-new-missing condition; recorded in audit/REQUIREMENTS/STATE per D-03."
gaps_closed:
  - id: CR-01
    closed_by: "Phase 24 (24-01/24-03)"
    evidence:
      - ".planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-VERIFICATION.md"
      - ".planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-REVIEW.md"
      - ".planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-03-SUMMARY.md"
    summary: "Mapper uses `_detect_city_from_raw_text(raw)` as canonical raw signal; candidate-present raw conflicts (alias/abbreviation/remoto), raw-vs-candidate supported divergence, and non-whitelist-vs-supported conflicts return conflict_resolved without applying wrong city; same-canonical safe apply preserved; deterministic regressions added."
  - id: WR-01
    closed_by: "Phase 24 (24-02/24-03), with runtime/browser checks as deferred accepted by item"
    evidence:
      - ".planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-VERIFICATION.md"
      - ".planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-HUMAN-UAT.md"
    summary: "Code-scope fix: ChatPanel remains mounted during detail (`dismissible={!selectedJob}`), detail close restores focus to connected trigger or `#chat-panel-close` via `getChatDetailCloseFocusTarget`; browser/keyboard validation is deferimento aceito por item (no browser execution fabricated)."
  - id: WR-03
    closed_by: "Phase 24 (24-01)"
    evidence:
      - ".planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-VERIFICATION.md"
    summary: "Non-native influence detection uses normalized token-set membership of `applied_q`, not whole-string substring; regression covers false positive (vagabundo/vaga) and positive control (pleno)."
accepted_residuals:
  - id: D-14/WR-02
    status: deferred_accepted
    detail: "Focus trap completo no diálogo custom do chat (Tab/Shift+Tab containment) permanece residual aceito explícito; não é gap crítico aberto. Risco residual: foco pode sair do diálogo em navegação por teclado. Ação futura: implementar focus-trap/contenção dedicada com validação manual de teclado/a11y."
  - id: CL-02-audit-open-heuristic
    status: formal_acceptance_scoped
    detail: "Os 4 quick tasks conhecidos (u28/uik/krt/ttk) podem permanecer como `[missing]` por heurística do audit-open somente quando suas disposições estiverem evidenciadas/justificadas e nenhum `[missing]` novo/inesperado aparecer. ttk permanece PLAN-only/deferred justificado sem fabricação de evidência. Formalização registrada em audit/REQUIREMENTS/STATE per D-03."
  - id: runtime-ui-deferments
    status: deferred_accepted
    detail: "Retestes runtime/browser/UI não executados nesta reconciliação permanecem como deferimento aceito por item com motivo, risco residual e ação futura, conforme 22/24 artifacts; nenhuma execução manual fabricada."
deferred:
  - truth: "Reteste runtime/integrado do caso reportado de cidade/chat (toolbar e chat em ambiente com dados/browser) confirma comportamento correto ponta a ponta."
    addressed_in: "Fora desta execução (condição futura documentada)"
    evidence: "Debug session `status: resolved` com hardening 22-04/23-01 e testes determinísticos; fechamento de CR-01 por Phase 24; reteste runtime registrado como deferimento aceito por item em `.planning/debug/city-filter-and-chat-ignores-registered-city.md`, `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, `22-VERIFICATION.md`, `22-MVP-EXAMPLES.md`, `24-HUMAN-UAT.md`, `24-VERIFICATION.md` e `v1.3-MILESTONE-AUDIT.md`."
  - truth: "Checks manuais/runtime/UI adicionais da Fase 22 (itens aceitos por item em 22-HUMAN-UAT/22-MANUAL-UAT) executados em ambiente integrado."
    addressed_in: "Fora desta execução (condição futura documentada)"
    evidence: "`22-VERIFICATION.md` = accepted_with_deferred_runtime_checks; `22-HUMAN-UAT.md`/`22-MANUAL-UAT.md` preservam passes históricos e registram deferimentos aceitos por item com motivo, risco residual e condição/ação futura."
  - truth: "Focus-trap completo (Tab/Shift+Tab containment) no diálogo custom do chat."
    addressed_in: "Fora desta execução (deferimento residual D-14/WR-02)"
    evidence: "23-02 implementou melhorias viáveis (foco inicial ao abrir, restauração de foco ao fechar detalhe vindo de resultado do chat); 24-02 preservou montagem/fallback de foco para WR-01. D-14/WR-02 focus trap completo permanece explicitamente deferido com justificativa/risco residual/ação futura em `23-02-SUMMARY.md`, `24-REVIEW.md`, `24-VERIFICATION.md` e artefatos de fechamento."
  - truth: "Nyquist 21/22 integralmente compliant (além de desvio aceito documentado)."
    addressed_in: "Plano de ação documentado (CL-04/D-13)"
    evidence: "`21-VALIDATION.md` e `22-VALIDATION.md` mantêm `nyquist_compliant: false` com 'Desvio aceito e plano de ação' explícito; `19-VALIDATION.md` e `20-VALIDATION.md` são `nyquist_compliant: true`."
  - truth: "Quick task 261112-ttk executada com evidência de produção/ambiente controlado."
    addressed_in: "Fora do escopo local (deferimento justificado D-07)"
    evidence: "PLAN-only em `.planning/quick/261112-ttk-escape-hatch-turnstile-teste-em-prod/261112-ttk-PLAN.md`; sem SUMMARY/evidência de execução; disposição registrada em `STATE.md`, `REQUIREMENTS.md` e `v1.3-MILESTONE-AUDIT.md` sem fabricação de evidência."
---

# Phase 23: Fechamento de débitos de auditoria e validação v1.3 — Verification Report

**Phase Goal:** Resolver os débitos pendentes de auditoria, validação humana/Nyquist e hardening identificados no fechamento do v1.3, garantindo que o milestone possa ser fechado sem pendências críticas abertas e sem regredir o board público.  
**Verified:** 2026-11-20T21:30:00Z  
**Re-verified / Reconciled:** 2026-11-22T00:00:00Z  
**Status:** gaps_closed_with_accepted_residuals  
**Re-verification:** Yes — in-place reconciliation after Phase 24 gap closure (D-05/D-06/D-08)

## Re-verification / Reconciliation (2026-11-22)

Esta seção atualiza o estado de fechamento da Phase 23 **sem apagar o histórico original** abaixo. O review point-in-time `23-REVIEW.md` permanece histórico (`status: issues_found`, CR-01/WR-01/WR-03 registrados) e não foi reescrito (D-08); sua resolução é cross-referenciada aqui e nos artefatos da Phase 24.

### Evidência Phase 24 considerada

- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-VERIFICATION.md` — `status: accepted_with_deferred_runtime_checks`, **8/8 must-haves verified**. Fecha CR-01/WR-01 (escopo de código viável)/WR-03 com evidência determinística; 2 checks runtime/browser WR-01 permanecem como deferimentos aceitos por item (sem execução browser fabricada).
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-REVIEW.md` — revisão pós-gap-closure; achados não-críticos remanescentes registrados como warnings/info fora dos must-haves da Phase 24.
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-03-SUMMARY.md` e planos 24-01..03 — evidência de execução/fechamento de gaps anteriores da Phase 24.
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-HUMAN-UAT.md` — reconciliado para `status: complete` com 2 cenários WR-01 como `deferred_accepted` por item (D-09/D-10).

### Disposição reconciliada dos achados críticos/resíduos

| Item | Disposição 2026-11-22 | Evidência | Residual |
|------|------------------------|-----------|----------|
| CR-01 (city conflict bypass) | **Fechado em código por Phase 24** | `24-VERIFICATION.md` truths 1-4; mapper usa `_detect_city_from_raw_text(raw)` como sinal canônico; conflitos alias/abreviação/remoto com candidato presente, divergência raw-vs-candidato suportado e conflitos não-whitelist-vs-suportado tratados como `conflict_resolved`; mesma cidade canônica segura; regressões determinísticas (33 testes intent pass). | Reteste runtime integrado/browser permanece deferimento aceito por item (sem execução fabricada). |
| WR-01 (focus restore/chat detail) | **Fechado no escopo viável de código por Phase 24** | `24-VERIFICATION.md` truths 6-7; ChatPanel montado durante detalhe (`dismissible={!selectedJob}`); foco retorna a trigger conectado ou `#chat-panel-close` via `getChatDetailCloseFocusTarget`; sem `document.body.focus()`. | 2 checks keyboard/browser em `24-HUMAN-UAT.md`/`24-VERIFICATION.md` são deferimento aceito por item (ambiente browser indisponível). |
| WR-03 (non-native influence substring) | **Fechado por Phase 24** | `24-VERIFICATION.md` truth 5; token-set normalizado de `applied_q`; regressão falso positivo/positivo. | Nenhum residual crítico aberto. |
| D-14/WR-02 (focus trap completo) | **Residual aceito explícito / deferido** | 23-02/23-REVIEW/24-REVIEW/24-VERIFICATION registram ausência de focus trap completo. | Não é gap crítico aberto. Risco residual: foco pode sair do diálogo custom; ação futura: focus-trap/contenção dedicada + validação manual teclado/a11y. |
| CL-02 (audit-open quick tasks heuristic) | **Satisfeito com aceite formal escopo-limite (D-01/D-03/D-04, formalização 25-02/audit)** | `STATE.md`, `REQUIREMENTS.md`, `v1.3-MILESTONE-AUDIT.md`, quick task PLAN/SUMMARY (u28/uik/krt) e PLAN-only ttk. | Aceite formal limitado aos 4 slugs conhecidos (u28, uik, krt, ttk) somente se disposições evidenciadas/justificadas e nenhum `[missing]` novo/inesperado; ttk permanece PLAN-only sem evidência fabricada. |

### Atualização de status por critério (reconciliado)

| # | Critério | Status reconciliado 2026-11-22 | Nota |
|---|----------|--------------------------------|------|
| 1 | Debug cidade/chat resolvido; filtro respeita cidade cadastrada | ✓ SATISFIED (code/evidence) with accepted runtime residual | CR-01 fechado por Phase 24 com testes determinísticos; reteste runtime integrado permanece deferimento aceito por item. |
| 2 | 4 quick tasks com status definido / gate audit-open reconciliado | ✓ SATISFIED with formal acceptance (scoped) | Disposições evidenciadas/justificadas; heurística audit-open aceita formalmente apenas para os 4 slugs conhecidos, sem novos missing (D-01/D-03/D-04). |
| 3 | Gaps de verificação/UAT fases 21/22 reconciliados | ✓ VERIFIED | Sem alteração material; evidência 23-03 preservada. |
| 4 | Nyquist 19–22 endereçado | ✓ VERIFIED | 20 criado; 19/20 compliant; 21/22 desvio aceito com plano (D-13). |
| 5 | Avisos não-bloqueantes tratados quando viáveis | ✓ VERIFIED with accepted residuals | Correções viáveis em 23-02/24-01/24-02; D-14/WR-02 focus trap completo permanece residual aceito explícito; runtime/browser checks por item como deferred_accepted. |
| 6 | Audit-open sem itens novos desta fase / audit atualizado para fechamento | ✓ VERIFIED with scoped formal acceptance | 23-VERIFICATION/24-VERIFICATION/24-HUMAN-UAT reconciliados; qualquer `[missing]` remanescente limitado aos 4 quick tasks conhecidos deve ter aceite formal escopo-limite no audit/REQUIREMENTS/STATE (25-02). Nenhum novo missing aceito por padrão. |

## Original Verification (2026-11-20T21:30:00Z) — preserved history

> **Historical snapshot:** The content below is preserved from the original 2026-11-20 verification for audit trail. Findings marked failed/partial below were re-evaluated in the reconciliation section above using Phase 24 evidence.

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria, merged with plan must_haves)

| # | Truth / Success Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Debug `city-filter-and-chat-ignores-registered-city` investigado até causa raiz e resolvido/fechado com decisão registrada; filtro de cidade e chat respeitam a cidade cadastrada corretamente. | ✗ FAILED (critical gap remains) | Debug finalizado como `status: resolved` com evidência 22-04/23-01, hardening RJ (`\brio\b` removido; mantidos `\brj\b` e `\brio\s+de\s+janeiro\b` em `backend/app/services/intent/mapper.py`) e regressões determinísticas em `backend/tests/test_intent_mapper.py` (inclui "Rio Grande do Sul"/"Rio Branco"). **Porém** `23-REVIEW.md` (issues_found, critical=1) registra CR-01 ainda presente: conflito cidade no raw text com aliases/abreviações/remoto não é respeitado quando `candidate.city` existe, podendo aplicar cidade incorreta (`backend/app/services/intent/mapper.py` ~309-364). Reteste runtime do caso reportado está como deferimento aceito por item (documentado), não como evidência de execução. |
| 2 | As 4 quick tasks pendentes têm status definido (concluídas com evidência ou deferred com justificativa) e não permanecem `missing`/`incomplete` no `audit-open`. | ⚠️ PARTIAL | Disposições documentadas em `.planning/STATE.md`, `.planning/REQUIREMENTS.md` e `.planning/v1.3-MILESTONE-AUDIT.md`: `261110-u28` concluída/supersedida por `261110-uik` com PLAN+SUMMARY; `261110-uik` concluída (vigente) com PLAN+SUMMARY; `261111-krt` concluída com PLAN+SUMMARY; `261112-ttk` deferred justificado (PLAN-only, sem SUMMARY/execução). **Porém** `gsd-sdk query audit-open` (2026-11-20) ainda reporta as 4 como `[missing]` (resíduo heurístico reconhecido em 23-05/audit). |
| 3 | Gaps de verificação/UAT das fases 21 e 22 executados e registrados: 21-VERIFICATION e 22-VERIFICATION saem de `human_needed`; 22-HUMAN-UAT sai de `partial`; 22-MANUAL-UAT sai de `draft`, com resultados/deferimentos aceitos por item. | ✓ VERIFIED | `21-VERIFICATION.md` → `status: passed` reconciliado com `21-HUMAN-UAT.md` (4/4 pass). `22-VERIFICATION.md` → `status: accepted_with_deferred_runtime_checks` com reconciliação a `22-HUMAN-UAT.md`/`22-MANUAL-UAT.md`. `22-HUMAN-UAT.md` → `status: complete` (passes preservados; item CL-01 e residual D-14 como deferimentos aceitos por item). `22-MANUAL-UAT.md` → `status: complete` (itens 0–6 resolvidos por deferimento aceito por item). |
| 4 | Gaps Nyquist 19–22 endereçados: 20-VALIDATION criado e 19/21/22-VALIDATION evoluídos para compliant ou desvio aceito documentado com plano de ação. | ✓ VERIFIED | `20-VALIDATION.md` criado (`nyquist_compliant: true`). `19-VALIDATION.md` evoluído para `nyquist_compliant: true`. `21-VALIDATION.md` e `22-VALIDATION.md` mantêm `nyquist_compliant: false` com "Desvio aceito e plano de ação" explícito (honesto, conforme D-13). |
| 5 | Avisos não-bloqueantes tratados quando viáveis: `canApplyChatToBoard` sem apply no-op para cidade não-normalizável, foco/a11y viável, parse defensivo de JSON em `chatSearch`, e `22-SECURITY.md` (ou equivalente). | ✓ VERIFIED (com residual deferido documentado) | `frontend/lib/api.ts`: `chatSearch` faz parse defensivo de 200 com `ApiError("Resposta inválida do servidor.", 0)`. `frontend/lib/chatApply.ts`: gating por filtros normalizados (`normalized.city !== null` etc.), evitando no-op para cidade-only não-normalizável; `frontend/lib/chatApply.test.ts` cobre `campinas -> false`. Chat: foco inicial no diálogo (`ChatPanel` close button ref/focus) e propagação/restauração de foco ao fechar detalhe vindo de resultado (`ChatResultItem`/`ChatResultsList`/`ChatThread`/`ChatWidget`). `22-SECURITY.md` criado (`status: verified`, `threats_open: 0`). **Residual explícito/deferido:** focus-trap completo do diálogo custom (D-14) e avisos adicionais de review WR-01/WR-02/WR-03 permanecem não resolvidos no código (ver Anti-Patterns/Gaps). |
| 6 | Após correções, `audit-open` não reporta itens novos desta fase e `v1.3-MILESTONE-AUDIT.md` atualizado refletindo resolução dos débitos para fechamento do v1.3. | ✓ VERIFIED (com resíduo heurístico pré-existente documentado) | `v1.3-MILESTONE-AUDIT.md` atualizado in-place para `status: passed` (closure-ready) refletindo CL-01..CL-05, resoluções, deferimentos/deviations aceitos e gate audit-open. `gsd-sdk query audit-open` não indica novos itens introduzidos pela fase 23, mas mantém 4 quick tasks pré-existentes como `[missing]` por heurística — residual explicitamente documentado em 23-05/audit. |

**Score (original 2026-11-20):** 4/6 success criteria verified (2 partial/failed due to open critical review finding and heuristic gate residual)

## Required Artifacts (spot-checked against phase must_haves)

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `backend/app/services/intent/mapper.py` | Hardening do fallback raw-text de cidade e mapeamento seguro | ⚠️ PARTIAL | Contém `_RAW_TEXT_CITY_PATTERNS` sem `re.compile(r"\brio\b")` e com `("Rio de Janeiro", (re.compile(r"\brj\b"), re.compile(r"\brio\s+de\s+janeiro\b")))` (23-01 satisfeito). **Mas** CR-01 permanece: conflito raw-text com aliases/abreviações/remoto pode ser ignorado quando há `candidate.city`. |
| `backend/tests/test_intent_mapper.py` | Regressões para falsos positivos "Rio"/RJ seguro e demais salvaguardas | ⚠️ PARTIAL | Contém `Rio Grande do Sul`, `Rio Branco` e `test_absent_candidate_raw_text_rio_false_positive_safeguards`; cobre RJ seguro (`rio de janeiro`, `rj`) e salvaguardas existentes. Não cobre cenários CR-01 (candidato presente + conflito raw-text por alias/abreviação/remoto). |
| `frontend/lib/api.ts` | `chatSearch` com parse defensivo de JSON em 200 | ✓ VERIFIED | `try { return (await res.json()) as ChatSearchResponse; } catch { throw new ApiError("Resposta inválida do servidor.", 0); }` presente; tratamento de timeout/transporte e erros HTTP preservado. |
| `frontend/lib/chatApply.ts` | Gating de apply por utilidade normalizada (sem no-op para cidade não-normalizável) | ✓ VERIFIED | `appliedParamsToBoardFilters` preservado; `canApplyChatToBoard` usa `normalized = appliedParamsToBoardFilters(...)` e retorna `normalized.q.trim().length > 0 || normalized.city !== null || normalized.sort === "antigas"` com bloqueio de degradado/`chat_disabled`. |
| `frontend/lib/chatApply.test.ts` | Cobertura determinística (inclui `campinas` -> false) | ✓ VERIFIED | Contém `interpretation({ city: "campinas" })` com expectativa `false`; casos degradado/chat_disabled/vazios e positivos suportados preservados. |
| `frontend/components/board/chat/ChatPanel.tsx` | Foco inicial viável no diálogo ao abrir | ✓ VERIFIED | `closeButtonRef`, `closeButtonRef.current?.focus()` em `useEffect([open])`, `ref={closeButtonRef}` no botão "Fechar chat"; sem focus-trap completo (deferido). |
| `frontend/components/board/chat/ChatWidget.tsx` | Propagação de trigger para restauração de foco ao fechar detalhe | ⚠️ PARTIAL | Propaga trigger (`onOpenDetail={(job, trigger) => handleOpenDetail(job, trigger ?? null)}`) e tenta `trigger?.focus()` em `handleCloseDetail`. **WR-01:** ao abrir detalhe o painel é fechado (`ChatPanel` desmonta quando `open=false`), então o trigger original pode estar desmontado e foco pode não ser restaurado corretamente. |
| `frontend/components/board/chat/ChatThread.tsx` | Assinatura de `onOpenDetail` com trigger propagada | ✓ VERIFIED | `onOpenDetail: (job: JobPublic, trigger?: HTMLElement | null) => void` repassado a `ChatResultsList`. |
| `frontend/components/board/chat/ChatResultsList.tsx` | Assinatura de `onOpenDetail` com trigger propagada | ✓ VERIFIED | `onOpenDetail: (job: JobPublic, trigger?: HTMLElement | null) => void` repassado a `ChatResultItem`. |
| `frontend/components/board/chat/ChatResultItem.tsx` | Clique envia trigger de origem | ✓ VERIFIED | `onOpen: (job: JobPublic, trigger?: HTMLElement | null) => void` e `onClick={(e) => onOpen(job, e.currentTarget)}`. |
| `.planning/debug/city-filter-and-chat-ignores-registered-city.md` | Disposição final rastreável do CL-01 | ✓ VERIFIED | `status: resolved` (não `diagnosed`), `## Resolution` com causa/fix/verificação, referências a 22-04/23-01, reteste runtime como deferimento aceito por item com risco residual e ação futura. |
| `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-VERIFICATION.md` | Reconciliação final fase 21 com 21-HUMAN-UAT | ✓ VERIFIED | `status: passed`, cita `21-HUMAN-UAT.md` e `4/4`, reconciliação documental sem nova execução runtime. |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md` | Estado final aceito/rastreável (não partial) | ✓ VERIFIED | `status: complete`, passes preservados, item CL-01 e residual D-14 resolvidos como deferimentos aceitos por item. |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` | Estado final aceito/rastreável (não draft) | ✓ VERIFIED | `status: complete`, sem `[pending]`, itens 0–6 como deferimentos aceitos por item com motivo/risco/ação futura. |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-VERIFICATION.md` | Estado final aceito/rastreável (não human_needed) | ✓ VERIFIED | `status: accepted_with_deferred_runtime_checks`, cita `22-HUMAN-UAT.md` e `22-MANUAL-UAT.md`, registra deferimentos/residuais. |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` | Rastreabilidade CL-01 atualizada sem remover lacunas mandatórias | ✓ VERIFIED | Contém atualizações 22-04/23-01 e reteste CL-01 como deferimento aceito por item; preserva lacunas mandatórias (`seed textual limitado`, sem semântica/vetorial/link/ID, `Campinas` fora da whitelist, campos não nativos aproximados/sinalizados). |
| `.planning/phases/20-api-publica-de-chat-search-resiliente/20-VALIDATION.md` | Nyquist fase 20 criado | ✓ VERIFIED | Existe; `nyquist_compliant: true`; contém `API-01` e `backend/tests/test_chat_search_api.py`; sign-off presente. |
| `.planning/phases/19-contrato-de-intencao-e-mapeamento-seguro/19-VALIDATION.md` | Nyquist fase 19 evoluído | ✓ VERIFIED | `nyquist_compliant: true`, caminhos reais `backend/tests/test_intent_*`, sem `tests/services/intent`. |
| `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-VALIDATION.md` | Nyquist fase 21 evoluído (compliance/desvio honesto) | ✓ VERIFIED | `nyquist_compliant: false` com `Accepted Deviation / Plan of Action`; sign-off presente. |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-VALIDATION.md` | Nyquist fase 22 evoluído (compliance/desvio honesto) | ✓ VERIFIED | `nyquist_compliant: false` com `Accepted Deviation / Plan of Action`; sign-off presente. |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-SECURITY.md` | Revisão de segurança fase 22 | ✓ VERIFIED | Existe; `phase: 22`, `threats_open: 0`, `status: verified`; contém trust boundaries, threat register, accepted risks, sign-off e controles citados (`CHAT_SEARCH_ENABLED`, rate limit, timeout, sem contatos/`contact_email`/sem PII em logging conforme documento). |
| `.planning/STATE.md` | Disposições quick tasks e estado reconciliado | ✓ VERIFIED (documental) | Registra u28/uik/krt concluídas com evidência e ttk como `deferred justificado` (PLAN-only); progresso/posição atualizados para fase 23 concluída. |
| `.planning/REQUIREMENTS.md` | Traceability/status CL-01..CL-05 consistente | ✓ VERIFIED (documental) | CL-01..CL-05 marcados `[x]` e `Complete` na traceability; notas refletem hardening/evidência/deferimentos. |
| `.planning/v1.3-MILESTONE-AUDIT.md` | Auditoria in-place de fechamento v1.3 | ✓ VERIFIED (documental) | `status: passed` (closure-ready), cobre CL-01..CL-05, Nyquist 19-22, correções CL-05, deferimentos/deviations aceitos e resultado do `audit-open`. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `backend/app/services/intent/mapper.py` | `backend/tests/test_intent_mapper.py` | `map_intent(..., raw_text=...)` e asserts de `applied_params`/`field_statuses` | ✓ WIRED | Testes exercitam fallback raw-text e salvaguardas (inclui Rio GS/Rio Branco e RJ seguro). |
| `frontend/lib/chatApply.ts` | `frontend/lib/filters.ts` | `normalizeFilters` + `appliedParamsToBoardFilters` | ✓ WIRED | Gating de apply deriva de filtros normalizados úteis; `canApplyChatToBoard` consome `appliedParamsToBoardFilters`. |
| `frontend/components/board/chat/ChatResultItem.tsx` → `ChatResultsList.tsx` → `ChatThread.tsx` → `ChatWidget.tsx` | detalhe/foco de origem | `onOpenDetail(job, trigger)` propagado até `handleOpenDetail(job, trigger ?? null)` | ✓ WIRED (propagação) / ⚠️ PARTIAL (efeito de foco) | Cadeia de props/tipos atualizada; restauração efetiva ao fechar detalhe é limitada por desmontagem do painel (WR-01). |
| `frontend/lib/api.ts` `chatSearch` | API pública `/api/v1/public/chat-search` | `fetch` POST + parse defensivo 200 | ✓ WIRED | Contrato de chamada preservado; parse inválido em 200 agora falha com erro pt-BR seguro. |
| Reconciliação documental fase 23 | Artefatos 21/22/debug/Nyquist/SECURITY/STATE/REQUIREMENTS/AUDIT | Atualizações cruzadas citadas em summaries e artefatos | ✓ WIRED (documental) | 21-VERIFICATION referencia 21-HUMAN-UAT; 22-VERIFICATION referencia 22-HUMAN-UAT/22-MANUAL-UAT; debug/audit/STATE/REQUIREMENTS refletem 23-01..23-05. |

## Data-Flow Trace (Level 4)

Nível 4 não aplicável como critério primário desta fase: escopo principal foi hardening backend pontual, hardening frontend de contrato/gating/foco, e reconciliação documental/auditoria. Não houve novos componentes de renderização de dados dinâmicos com nova fonte de dados introduzidos além das correções verificadas em helpers/componentes existentes.

## Behavioral Spot-Checks

| Behavior | Command / Check | Result | Status |
|---|---|---|---|
| `chatSearch` defensive parse (200 inválido) | `node --input-type=commonjs -e "const fs=require('fs'); const s=fs.readFileSync('frontend/lib/api.ts','utf8'); const i=s.indexOf('export async function chatSearch'); const j=s.indexOf('export async function getChatSearchStatus', i); process.exit(i>=0 && j>i && s.slice(i,j).includes('Resposta inválida do servidor.') ? 0 : 1)"` | matched in `chatSearch` body | ✓ PASS |
| `canApplyChatToBoard` normalized gating (no `hasCity` string-only gate) | `node --input-type=commonjs -e "const fs=require('fs'); const s=fs.readFileSync('frontend/lib/chatApply.ts','utf8'); process.exit(s.includes('appliedParamsToBoardFilters(interpretation.applied_params)') && s.includes('normalized.city !== null') && !s.includes('const hasCity') ? 0 : 1)"` | matched | ✓ PASS |
| `campinas` city-only not applyable | `node --input-type=commonjs -e "const fs=require('fs'); process.exit(fs.readFileSync('frontend/lib/chatApply.test.ts','utf8').includes('interpretation({ city: \"campinas\" })') ? 0 : 1)"` | matched | ✓ PASS |
| Chat trigger propagation wired to widget handler | `node --input-type=commonjs -e "const fs=require('fs'); process.exit(fs.readFileSync('frontend/components/board/chat/ChatWidget.tsx','utf8').includes('onOpenDetail={(job, trigger) => handleOpenDetail(job, trigger ?? null)}') ? 0 : 1)"` | matched | ✓ PASS |
| Mapper no longer uses bare `\\brio\\b` for RJ raw-text fallback | `node --input-type=commonjs -e "const fs=require('fs'); const s=fs.readFileSync('backend/app/services/intent/mapper.py','utf8'); process.exit(s.includes('re.compile(r\"\\\\brj\\\\b\")') && s.includes('re.compile(r\"\\\\brio\\\\s+de\\\\s+janeiro\\\\b\")') && !s.includes('re.compile(r\"\\\\brio\\\\b\")') ? 0 : 1)"` | matched | ✓ PASS |
| Phase 23 targeted frontend/backend test commands claimed in summaries (`vitest run lib/chatApply.test.ts`, `pytest -q tests/test_intent_mapper.py`, `tsc --noEmit`) | Not re-executed in this verification session | environment/runtime re-execution not performed | ? SKIP (requires runtime/tool execution in project env) |

## Requirements Coverage

| Requirement | Source Plan(s) | Description (closure) | Status | Evidence |
|---|---|---|---|---|
| CL-01 | 23-01, 23-03 | Debug de cidade/chat resolvido com decisão/evidência; hardening aplicado e reteste runtime documentado/deferido por item | ⚠️ PARTIAL | Debug `resolved` com decisão/deferimento rastreável; 23-01 fix/testes para `Rio Grande do Sul`/`Rio Branco` presentes. **Gap:** 23-REVIEW CR-01 crítico ainda presente no mapper (conflitos raw-text alias/abreviação/remoto com candidato presente podem aplicar cidade errada). |
| CL-02 | 23-05 | 4 quick tasks reconciliadas com evidência ou deferimento justificado | ⚠️ PARTIAL | Disposições em `STATE.md`/`REQUIREMENTS.md`/`v1.3-MILESTONE-AUDIT.md` rastreáveis (u28/uik/krt evidenciadas; ttk PLAN-only deferred). **Heurística:** `audit-open` ainda lista 4 `[missing]` (documentado). |
| CL-03 | 23-03 | Gaps de verificação/UAT 21/22 reconciliados em estados finais aceitos e rastreáveis | ✓ SATISFIED | `21-VERIFICATION` passed (4/4 UAT), `22-VERIFICATION` accepted_with_deferred_runtime_checks, `22-HUMAN-UAT` complete, `22-MANUAL-UAT` complete com deferimentos por item e passes preservados. |
| CL-04 | 23-04 | Nyquist 19–22 endereçado (20 criado; 19/20 compliant; 21/22 compliant ou desvio aceito com plano) | ✓ SATISFIED | `20-VALIDATION` criado (compliant), `19-VALIDATION` compliant, `21/22-VALIDATION` não-compliant com "Desvio aceito e plano de ação" explícito (D-13). |
| CL-05 | 23-02, 23-04, 23-05 | Avisos não-bloqueantes tratados quando viáveis (chatSearch parse defensivo, apply sem no-op cidade não-normalizável, foco/a11y viável, 22-SECURITY, audit atualizado) | ⚠️ PARTIAL | Fixes viáveis presentes (`api.ts`, `chatApply.ts/.test.ts`, foco inicial/propagação de trigger), `22-SECURITY.md` e `v1.3-MILESTONE-AUDIT.md` atualizados. **Residuals:** focus-trap completo explicitamente deferido (D-14); 23-REVIEW WR-01/WR-02/WR-03 ainda observáveis no estado atual do código. |

**Orphaned requirements for Phase 23:** None detected (ROADMAP maps CL-01..CL-05 to Phase 23; all five appear in PLAN frontmatter across 23-01..23-05 and are present in REQUIREMENTS traceability).

## Anti-Patterns Found

| File | Line(s) | Pattern | Severity | Impact |
|---|---:|---|---|---|
| `backend/app/services/intent/mapper.py` | ~309-364 | CR-01: candidate-present path can bypass raw-text alias/abbreviation/remoto conflict detection and apply wrong city | 🛑 Blocker | Incorrect city filter may be applied in conflicting inputs; undermines "cidade/chat respeitam a cidade cadastrada corretamente" and leaves a critical review finding open. |
| `frontend/components/board/chat/ChatWidget.tsx` / `ChatPanel.tsx` | ~282-294 (widget), ~40 (panel unmount when closed) | WR-01: focus restoration target can be unmounted after closing panel to open detail | ⚠️ Warning | Focus may not return to originating result; keyboard/a11y flow degraded (overlaps deferred focus work). |
| `frontend/components/board/chat/ChatPanel.tsx` | ~23-75 | WR-02 / D-14 residual: no focus trap and no restore-to-launcher on close (dialog custom) | ⚠️ Warning | Focus can move outside dialog while open; residual explicitly deferred/documented but still present. |
| `backend/app/services/intent/mapper.py` | ~446-459 | WR-03: non-native influence detection uses substring matching over full `applied_q` | ⚠️ Warning | Possible misclassification of non-native field influence/limitations (quality/observability of interpretation), not a privacy/contact leak. |

## Human Verification Required

Runtime/browser/integrated checks already identified by the phase were reconciled as **accepted per-item deferrals** with justification, residual risk, and future action (not silent gaps):

1. **CL-01 runtime retest do caso reportado (toolbar + chat, ambiente integrado com dados/browser)**  
   **Test:** Reproduzir o cenário reportado em ambiente integrado e validar aplicação de `city=<slug>` correto e interpretação de cidade sem marcação indevida como ignorada.  
   **Expected:** Cidade cadastrada respeitada ponta a ponta (board e chat).  
   **Why human:** Requer stack integrada, dados reais, browser/UX e observação operacional; não executável nesta sessão de verificação.

2. **Roteiro manual/UAT fase 22 (itens reconciliados em 22-HUMAN-UAT/22-MANUAL-UAT)**  
   **Test:** Executar itens deferidos em ambiente integrado/controlado (kill-switch UI/runtime, degradação/sem resultados, privacidade operacional oportunística, etc.).  
   **Expected:** Comportamento conforme contratos documentados, sem regressão do board público.  
   **Why human:** Dependente de runtime, configuração/restart, dados/fixtures, simulação de falhas e inspeção browser/rede/logs.

3. **Acessibilidade de foco no diálogo do chat (incluindo residual focus-trap)**  
   **Test:** Validar navegação por teclado/leitor de tela (Tab/Shift+Tab, abertura/fechamento, retorno de foco) em ambiente browser real.  
   **Expected:** Foco contido e restaurado consistentemente.  
   **Why human:** Comportamento de foco é dependente de runtime/DOM/navegador e não totalmente verificável por inspeção estática.

## Gaps Summary

A fase 23 avançou substancialmente no fechamento documental e em hardenings viáveis: 23-01 corrigiu o falso positivo específico de `\brio\b` (com regressões), 23-02 aplicou parse defensivo em `chatSearch`, corrigiu o gating de apply para evitar no-op em cidade-only não normalizável e implementou melhorias focadas de foco com propagação de trigger, 23-03/23-04/23-05 reconciliaram debug/UAT/verificações/Nyquist/segurança/STATE/REQUIREMENTS/auditoria com rastreabilidade e deferimentos aceitos explícitos.

**Bloqueadores/gaps remanescentes para meta de "sem pendências críticas abertas":**
1. **CR-01 (crítico, código):** `backend/app/services/intent/mapper.py` ainda pode aplicar cidade incorreta quando há candidato presente e conflito raw-text expresso por alias/abreviação/remoto fora do pré-check atual. `23-REVIEW.md` registra o achado e o estado atual do código confirma que a correção proposta não foi aplicada.
2. **Gate audit-open não limpo (heurístico, mas ainda aberto na saída do comando):** `gsd-sdk query audit-open` continua reportando 4 quick tasks como `[missing]`, apesar das disposições documentadas (incluindo ttk PLAN-only deferred sem fabricação de evidência). Isso mantém ambiguidade no fechamento automático/heurístico.

Itens de runtime/UI/Nyquist/focus-trap integral foram tratados como **deferimentos/deviations aceitos e documentados** (quando aplicável) e não devem ser reinterpretados como execução realizada.

---

_Verified: 2026-11-20T21:30:00Z_  
_Reconciled: 2026-11-22T00:00:00Z_  
_Verifier: Claude (gsd-verifier); reconciled by OpenCode (gsd-executor, Phase 25)_