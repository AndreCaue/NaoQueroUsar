---
phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review
verified: 2026-11-22T02:40:00Z
status: accepted_with_deferred_runtime_checks
score: 8/8 must-haves verified
reconciled: 2026-11-22
re_verification:
  previous_status: gaps_found
  previous_score: 6/8
  gaps_closed:
    - "Truth 3: slash-separated non-city queries no longer trigger false D-03 conflict_resolved; safe supported city applies (analista/pleno em sp, dev/frontend remoto, dev/frontend em sp + SP candidate)"
    - "Truth 7 edge case: ChatPanel close button now guarded by dismissible, keeping #chat-panel-close mounted/focusable while detail is open"
  gaps_remaining: []
  regressions: []
human_verification_resolutions:
  - test: "WR-01 keyboard focus restore after closing job detail opened from chat"
    expected: "Open chat by keyboard, open a job detail by keyboard, confirm ChatPanel remains mounted behind the native detail dialog, close detail by keyboard/Escape. Focus returns to originating connected trigger; if trigger is disconnected/unavailable, focus returns to #chat-panel-close. Focus never lands on document.body."
    resolution: "deferimento aceito por item — Ambiente browser/integrado indisponível nesta execução de reconciliação; validação de teclado/foco nativo requer browser real. Risco residual: regressão de foco/teclado em browser real (fechamento por Escape/controles, restauração para trigger conectado ou #chat-panel-close) pode não ser percebida até validação manual. Ação futura: revalidar em browser integrado com teclado (Tab/Shift+Tab/Escape), confirmar foco em trigger conectado ou #chat-panel-close e nunca em document.body; registrar evidência no UAT/VERIFICATION."
  - test: "WR-01 edge case: attempt to close chat while job detail is open"
    expected: "With job detail open from chat, activating 'Fechar chat' (mouse or keyboard) does not dismiss/unmount the chat panel. After closing detail, focus restores to connected trigger or #chat-panel-close, never document.body."
    resolution: "deferimento aceito por item — Ambiente browser/integrado indisponível nesta execução de reconciliação; validação de teclado/foco nativo requer browser real. Risco residual: regressão de foco/teclado em browser real com detalhe aberto (chat não deve desmontar; foco deve restaurar para trigger conectado ou #chat-panel-close) pode não ser percebida até validação manual. Ação futura: revalidar em browser integrado com teclado/mouse, confirmar que 'Fechar chat' não desmonta painel com detalhe aberto e que foco restaura para trigger conectado ou #chat-panel-close, nunca document.body; registrar evidência no UAT/VERIFICATION."
---

# Phase 24: Corrigir conflito crítico de cidade e resíduos de review Verification Report

**Phase Goal:** Eliminar o bypass crítico de detecção de conflito de cidade no mapper (CR-01) e fechar resíduos de código viáveis da revisão da Phase 23, preservando o comportamento determinístico e seguro do chat/board público
**Verified:** 2026-11-22T02:40:00Z
**Status:** accepted_with_deferred_runtime_checks (reconciled 2026-11-22; 2 runtime/browser checks deferred accepted by item)
**Re-verification:** Yes — after gap closure (24-03); reconciled 2026-11-22 for final closure state (D-07/D-09/D-10/D-11)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Consultas com conflito de cidade por alias/abreviação/remoto (ex.: "sp ou rio de janeiro", "remoto ou são paulo") não aplicam cidade quando há candidato presente; mapper usa `_detect_city_from_raw_text()` como sinal canônico de raw (D-02) e retorna city=null, status ignorado e reason_code conflict_resolved (D-01). | ✓ VERIFIED | `backend/app/services/intent/mapper.py:310` uses `_detect_city_from_raw_text(raw)` as canonical raw signal; `:356-360` returns `conflict_resolved` on raw conflict; `:361-365` handles raw-vs-candidate supported divergence. `tests/test_intent_mapper.py` has `test_candidate_present_raw_text_city_conflicts_cr01` covering "sp ou rio de janeiro", "remoto ou são paulo", "sp ou rj", "bh ou remoto", "home office ou belo horizonte". `pytest tests/test_intent_mapper.py tests/test_intent_schema.py tests/test_intent_parser.py` → 33 passed. |
| 2 | Divergência entre cidade suportada detectada no raw e cidade candidata resolvida em cidade suportada diferente resulta em conflict_resolved, sem aplicar cidade errada (D-03). | ✓ VERIFIED | `mapper.py:361-365` emits `conflict_resolved` when `raw_detected_city` and `resolved_candidate_city` differ. `test_raw_vs_candidate_supported_divergence_conflict_cr01` covers `raw="vaga em sp"` + candidate RJ. Regression suite passes. |
| 3 | Mesma cidade canônica (raw SP, candidato 'São Paulo') aplica com segurança; candidato ausente com 1 cidade suportada segura no raw continua aplicando; candidato não-whitelist permanece not_in_whitelist e conflito explícito entre cidade não-whitelist e cidade suportada (ex.: Campinas vs Remoto) não promove cidade errada (D-03). | ✓ VERIFIED | Prior gap closed by 24-03. `mapper.py:315-336` narrows `/` handling: `has_nl_conflict_sep` matches only `ou/or/vs`; `has_slash_city_alt` requires slash adjacent to supported city mention; `split_pattern` is conditional. Spot checks: `analista/pleno em sp` absent candidate → `São Paulo/aplicado/normalized`; `dev/frontend remoto` → `Remoto/aplicado/normalized`; `dev/frontend em sp` with candidate SP → `São Paulo/aplicado/normalized`. D-03 conflicts preserved: `campinas ou remoto` with Campinas candidate → `None/ignorado/conflict_resolved`; `curitiba ou sao paulo` with Curitiba candidate → `None/ignorado/conflict_resolved`. `test_slash_non_city_terms_do_not_trigger_city_conflict_cr01` present. |
| 4 | Regressão determinística em matriz focada cobre exemplos CR-01 + aliases/abreviações/remoto, acordo de mesma cidade canônica, candidato ausente, candidato não-whitelist sem regressão e casos onde candidato presente não deve bypassar conflito raw (D-04). | ✓ VERIFIED | `test_intent_mapper.py` contains CR-01 matrix tests: `test_candidate_present_raw_text_city_conflicts_cr01`, `test_raw_vs_candidate_supported_divergence_conflict_cr01`, `test_same_canonical_city_and_safe_fallbacks_cr01`, `test_non_whitelist_vs_supported_conflict_guard_cr01`, `test_slash_non_city_terms_do_not_trigger_city_conflict_cr01`. Intent suite: 33 passed. |
| 5 | Detecção de influência de campos não nativos usa membership em token-set normalizado de applied_q, não substring no string inteiro; regressão cobre falso positivo por substring (D-05, D-06, WR-03). | ✓ VERIFIED | `mapper.py:483` builds `aq_tokens = set(_strip_accents_lower(applied_q).split())`; `:487` checks `k in aq_tokens`. `test_non_native_influence_uses_token_set_not_substring_wr03` covers `vagabundo`/`vaga` false positive → `ignorado/unsupported_structured_filter` and positive control `pleno` → `aproximado/textual_approximation_in_q`. |
| 6 | Abrir detalhe de vaga a partir do chat não desmonta o ChatPanel; o painel permanece montado atrás do dialog nativo enquanto o detalhe está aberto (D-07). | ✓ VERIFIED | `ChatWidget.tsx:283-287` `handleOpenDetail` sets trigger, selected job, syncs `?vaga=`, and does not call `setIsOpen(false)`. `ChatWidget.tsx:319-324` renders `ChatPanel` with `open={isOpen}` and `dismissible={!selectedJob}` independent of detail; `JobDetailDialog` rendered at `:353-355`. |
| 7 | Ao fechar o detalhe, o foco retorna ao trigger original se trigger.isConnected; caso contrário retorna ao fallback estável montado no chat (botão fechar do ChatPanel). Nunca foca document.body (D-08). | ✓ VERIFIED | `chatFocus.ts` exports `getChatDetailCloseFocusTarget` returning connected trigger, connected fallback, or `null` (never body). `ChatWidget.tsx:289-301` computes target from trigger + `#chat-panel-close` and calls `target?.focus()` in `requestAnimationFrame`; no `document.body.focus()`. `ChatPanel.tsx:65-70` keeps close button mounted/focusable with `id="chat-panel-close"`, `onClick={dismissible ? onClose : undefined}`, `aria-disabled={!dismissible || undefined}`, no HTML `disabled`. `ChatPanel.tsx:26,49-51` guard Escape/backdrop by `dismissible`. `chatFocus.test.ts` covers connected/disconnected/null/undefined. Browser keyboard flow remains a deferred runtime check by item below. |
| 8 | Fluxo canônico de detalhe/reveal e contratos públicos (JobPublic, sem contatos no chat, URL canônica q/city/sort/page/vaga) permanecem sem regressão. | ✓ VERIFIED | `ChatWidget.tsx` preserves `chatSearch`, `canApplyChatToBoard`, `appliedParamsToBoardFilters`, `buildBoardHref`, `syncVagaParam`, and `JobDetailDialog` flow. No API/schema/contact-surface changes in phase files. Intent schema/parser/mapper suites pass (33); chatApply/chatFocus suites pass (11). |

**Score:** 8/8 must-haves verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/intent/mapper.py` | Deterministic city mapping with canonical raw conflict signal and token-set non-native influence | ✓ VERIFIED | Contains `_detect_city_from_raw_text(raw)` (310), D-03 guard with `has_slash_city_alt` (317-323), conditional split (335), `aq_tokens` membership (483-487). No old generic `|/` separator patterns. |
| `backend/tests/test_intent_mapper.py` | Deterministic CR-01 and WR-03 regressions | ✓ VERIFIED | Contains CR-01 matrix, D-03 non-whitelist-vs-supported guards, slash non-city regression, and WR-03 token-set regression. |
| `frontend/components/board/chat/ChatWidget.tsx` | Detail-open keeps panel mounted; detail-close restores focus safely | ✓ VERIFIED | Imports `getChatDetailCloseFocusTarget`; no `setIsOpen(false)` in `handleOpenDetail`; passes `dismissible={!selectedJob}`; focus restore uses helper + `requestAnimationFrame`; never focuses body. |
| `frontend/components/board/chat/ChatPanel.tsx` | Mounted panel with dismissible guard and stable focus fallback | ✓ VERIFIED | `id="chat-panel-close"`; close button and backdrop guarded by `dismissible`; `aria-disabled` used instead of HTML `disabled`; Escape guarded. |
| `frontend/lib/chatFocus.ts` | Pure focus target helper | ✓ VERIFIED | Exports `getChatDetailCloseFocusTarget`; returns trigger/fallback/null by `isConnected`. |
| `frontend/lib/chatFocus.test.ts` | Deterministic WR-01 helper coverage | ✓ VERIFIED | 4 Vitest cases pass. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/services/intent/mapper.py` | `backend/tests/test_intent_mapper.py` | `map_intent(..., raw_text=...)` assertions for conflict/safe apply | WIRED | CR-01/WR-03 regressions exercise mapper behavior; 33 intent tests pass. |
| `backend/app/services/intent/mapper.py` | `_detect_city_from_raw_text` | canonical raw city/conflict signal | WIRED | Called at `:310`; result drives conflict/divergence/guard logic. |
| `frontend/components/board/chat/ChatWidget.tsx` | `frontend/lib/chatFocus.ts` | `getChatDetailCloseFocusTarget(...)` | WIRED | Imported `:9`, used `:294`. |
| `frontend/components/board/chat/ChatWidget.tsx` | `frontend/components/board/chat/ChatPanel.tsx` | `dismissible={!selectedJob}` | WIRED | Passed `:321`; ChatPanel enforces dismissible on Escape/backdrop/close button. |
| `frontend/components/board/chat/ChatResultItem.tsx` | `frontend/components/board/chat/ChatWidget.tsx` | `onOpenDetail(job, trigger)` | WIRED | Existing propagation path preserved (ChatWidget passes handler to ChatThread `:344`); no phase regression observed. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|-------------|--------|--------------------|--------|
| `backend/app/services/intent/mapper.py` | `applied_city`, `city_reason_code` | `_detect_city_from_raw_text(raw)` + `_resolve_city_safe(candidate.city, raw)` + D-03 guards | Yes - deterministic from raw/candidate input | ✓ FLOWING |
| `frontend/components/board/chat/ChatWidget.tsx` | focus target / selected job | React state, `detailTriggerRef`, DOM `isConnected`, `#chat-panel-close` | Yes - real UI state/DOM | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Intent mapper/schema/parser regressions | `cd backend; python -m pytest -q tests/test_intent_mapper.py tests/test_intent_schema.py tests/test_intent_parser.py` | 33 passed | ✓ PASS |
| Chat focus/apply helper regressions | `cd frontend; npm run test -- lib/chatApply.test.ts lib/chatFocus.test.ts` | 2 files, 11 passed | ✓ PASS |
| Previous gap: slash non-city safe apply | Python spot-check: `analista/pleno em sp`, `dev/frontend remoto`, `dev/frontend em sp`+SP | All apply safe supported city (`São Paulo`/`Remoto`, `aplicado`, `normalized`) | ✓ PASS |
| D-03 non-whitelist-vs-supported conflicts preserved | Python spot-check: `campinas ou remoto` + Campinas, `curitiba ou sao paulo` + Curitiba | Both `None/ignorado/conflict_resolved` | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CL-01 | 24-01, 24-03 | Resolver conflito crítico de cidade no mapper com decisão/evidência registrada; reteste runtime documentado quando inviável | ✓ SATISFIED (code/evidence) | CR-01 candidate-present raw conflicts, divergence, and slash false-positive gap are covered by deterministic mapper code/tests and spot checks. REQUIREMENTS.md traceability still marks CL-01 Pending at milestone level pending closure workflow; this verification provides phase evidence. |
| CL-05 | 24-01, 24-02, 24-03 | Tratar avisos não-bloqueantes viáveis/resíduos de review, com residual explicitamente deferido quando aplicável | ✓ SATISFIED (phase scope) | WR-03 token-set fixed; WR-01 focus restore/fallback guarded in code with helper tests; D-14 focus trap remains explicitly deferred per context/plan. 24-REVIEW has additional non-must-have findings noted below as warnings. |

**Orphaned requirements for Phase 24:** None. REQUIREMENTS.md maps CL-01 and CL-05 to Phase 24; all Phase 24 plans declare CL-01/CL-05.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/app/services/intent/mapper.py` | 315-354 | D-03 guard handles `ou/or/vs` and supported-city-adjacent `/`, but not explicit `e`/comma city alternatives | ⚠️ Warning | Not in Phase 24 must-have matrix; observed during verification: `raw="vaga em sp e curitiba"` with absent candidate currently applies `São Paulo/normalized`. This is a safety gap similar to CR-01 class but outside stated Phase 24 truths/SC. Recommend tracking separately. |
| `frontend/components/board/chat/ChatPanel.tsx` | 45-80 | Custom dialog has no focus trap (WR-02/D-14) | ℹ️ Info | Explicitly deferred by Phase 24 context/decisions; native `JobDetailDialog` remains modal boundary. Not a Phase 24 gap. |

### Human Verification Resolutions (deferred accepted by item)

### 1. WR-01 keyboard focus restore

**Test:** Open chat by keyboard, open a job detail from a chat result by keyboard, then close the detail by Escape or dialog close control.
**Expected:** ChatPanel remains mounted behind the native detail dialog while detail is open. On detail close, focus returns to the originating connected trigger, or to `#chat-panel-close` if trigger is unavailable. Focus never lands on `document.body`.
**Resolution:** deferimento aceito por item — Ambiente browser/integrado indisponível nesta execução de reconciliação; validação de teclado/foco nativo requer browser real. Risco residual: regressão de foco/teclado em browser real pode não ser percebida até validação manual. Ação futura: revalidar em browser integrado com teclado/Escape e registrar evidência no UAT/VERIFICATION, confirmando foco em trigger conectado ou `#chat-panel-close` e nunca em `document.body`.

### 2. Chat Close Control While Detail Open

**Test:** Open chat, open a job detail from chat, then attempt to activate "Fechar chat" by mouse and keyboard while detail remains open. Close the detail afterward.
**Expected:** Chat does not dismiss/unmount while detail is open. After detail closes, focus returns to connected trigger or `#chat-panel-close`; never `document.body`.
**Resolution:** deferimento aceito por item — Ambiente browser/integrado indisponível nesta execução de reconciliação; validação de teclado/foco nativo requer browser real. Risco residual: regressão de foco/camadas em browser real com detalhe aberto pode não ser percebida até validação manual. Ação futura: revalidar em browser integrado com teclado/mouse, confirmando que "Fechar chat" não desmonta painel com detalhe aberto e que foco restaura para trigger conectado ou `#chat-panel-close`, nunca `document.body`; registrar evidência no UAT/VERIFICATION.

## Reconciliation (2026-11-22)

- Reconciled per D-07/D-09/D-10/D-11: the two WR-01 runtime/browser checks are closed as **deferimentos aceitos por item** (motivo, risco residual, ação futura), with no manual browser execution claimed.
- Automated/code evidence remains authoritative for the 8/8 must-haves verified; status is qualified as `accepted_with_deferred_runtime_checks`, not downgraded to plain `passed` and not left as open `human_needed`.
- `24-HUMAN-UAT.md` is reconciled to `status: complete` with the same two WR-01 items recorded as `deferred_accepted` by item.

### Gaps Summary

No code gaps found against Phase 24 must-haves. The two gaps from the previous verification were closed by Plan 24-03: slash-separated non-city queries no longer produce false D-03 `conflict_resolved`, and ChatPanel close action is guarded by `dismissible` while preserving a mounted/focusable D-08 fallback. Automated regressions pass (33 intent tests, 11 frontend helper tests). The remaining WR-01 keyboard/browser checks are reconciled as deferred accepted by item (no browser execution performed in this reconciliation).

---

_Verified: 2026-11-22T02:40:00Z_
_Reconciled: 2026-11-22_
_Verifier: OpenCode (gsd-verifier / gsd-executor reconciliation)_