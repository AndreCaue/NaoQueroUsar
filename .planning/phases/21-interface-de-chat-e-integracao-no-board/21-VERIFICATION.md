---
phase: 21-interface-de-chat-e-integracao-no-board
verified: 2026-11-17T21:55:00Z
status: human_needed
score: 4/4 must-haves verified
re_verification: false
---

# Phase 21: Interface de chat e integração no board — Verification Report

**Phase Goal:** Qualquer pessoa consegue usar o chat no board público, entender o que o sistema aplicou e chegar aos detalhes das vagas sem fricção
**Verified:** 2026-11-17T21:55:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Usuário abre um chat simples (drawer/modal) no board público, em mobile ou desktop, sem login, envia mensagem e vê estados claros de carregamento e erro | ✓ VERIFIED | `frontend/app/(public)/page.tsx` mounts `<ChatWidget />` (line 165). `frontend/components/board/chat/ChatLauncher.tsx` exposes `aria-label="Abrir busca por chat"` and toggles open. `ChatPanel.tsx` renders responsive dialog/sheet container (`items-end` mobile, `sm:*` drawer sizing), title `Buscar vagas no chat`, close `Fechar chat`, Escape handling. `ChatComposer.tsx` has placeholder `Descreva a vaga que você procura...`, `Enviar mensagem`, 4 example chips, trims/blocks empty, disables send while `isSending`. `ChatWidget.tsx` calls `chatSearch({ message, page: 1, limit: 20 })`, sets loading turn and `Interpretando sua busca...` (ChatThread), blocks duplicate in-flight via `isSending`/request sequencing, maps failures to pt-BR error with `Tentar novamente` retry path. No auth/login required in chat flow. Responsive/focus UX still needs human confirmation. |
| 2 | Usuário vê os parâmetros entendidos/aplicados/ignorados-aproximados e uma lista de resultados com título, empresa, local, salário quando disponível e acesso ao detalhe/link | ✓ VERIFIED | `ChatInterpretation.tsx` renders `Entendi: ...` summary, iterates `interpretation.field_statuses` with labels `Aplicado`/`Ignorado`/`Aproximado`, reasons and entendido/aplicado values, and separate `Limites desta busca` block for `limitations`/`meta.guidance`. `ChatResultsList.tsx` + `ChatResultItem.tsx` render compact public items: `job.title`, company when present, `Local: {cityLabel(job.city)}`, salary when present, and `Ver detalhes` affordance. Empty/degraded states implemented (`Nenhuma vaga encontrada`, `Não houve resultados automáticos.`). |
| 3 | A partir dos resultados do chat, o usuário acessa o fluxo atual de detalhe e revelação de contato, sem que contatos apareçam no payload/resposta do chat | ✓ VERIFIED | `ChatWidget.tsx` stores selected `JobPublic`, minimizes chat, syncs `?vaga` via `history.replaceState`, and renders `<JobDetailDialog job={selectedJob} open onClose={handleCloseDetail} />` (canonical flow with `RevealContact` inside dialog). `ChatResultItem` click opens detail; close clears selection and removes only `vaga`. Chat contracts in `frontend/lib/api.ts` define `ChatSearchResults.items: JobPublic[]` and no `contact_*` fields in chat types/client. Grep: no `contact_email|contact_phone|/reveal-contact|dangerouslySetInnerHTML` in `frontend/components/board/chat` or `frontend/app/(public)/page.tsx`. |
| 4 | Usuário pode aplicar/ajustar a busca entendida no board canônico (URL/filtros existentes) quando aplicável, mantendo o comportamento atual de busca/listagem | ✓ VERIFIED | `frontend/lib/chatApply.ts` + `chatApply.test.ts` map `applied_params` via `normalizeFilters`, force `page: 1` and `vaga: null`, and gate apply with `canApplyChatToBoard` (blocks degraded; allows q/hasCity/sort `antigas` in implementation). `ChatWidget.tsx` computes filters with `appliedParamsToBoardFilters`, builds canonical href with `buildBoardHref`, calls `router.replace(href, { scroll: false })`, and minimizes chat while preserving in-memory state. `ChatResultsList.tsx` shows `Aplicar no board` only when `canApply` and renders partial-support note `Alguns critérios podem ser aproximados ou não filtrados.` when applicable; manual-search shortcut available. Automated mapping tests pass (`npm --prefix frontend run test:chat`, 6/6). |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/vitest.config.ts` | Vitest config for frontend unit tests | ✓ VERIFIED | Exists; `environment: "node"`, `include: ["lib/**/*.test.ts"]`, `@` alias configured. |
| `frontend/lib/api.ts` | Typed chat-search models/client for POST `/api/v1/public/chat-search` | ✓ VERIFIED | Exports `ChatFieldStatus`, `ChatFieldAssessment`, `ChatAppliedParams`, `ChatInterpretation`, `ChatSearchResults`, `ChatSearchRequest`, `ChatSearchResponse`, `chatSearch`; posts JSON with `AbortSignal.timeout(15_000)`, throws `ApiError` on non-2xx and transport/timeout (status 0). No contact fields in chat types. Substantive (839 lines total file) and used by chat UI. |
| `frontend/lib/chatApply.ts` | Pure mapping/gating from `applied_params` to canonical board Filters | ✓ VERIFIED | Exports `appliedParamsToBoardFilters` (uses `normalizeFilters`, returns `page: 1`, `vaga: null`) and `canApplyChatToBoard`; used by `ChatWidget`/`ChatResultsList`. |
| `frontend/lib/chatApply.test.ts` | Automated verification for UI-03 mapping rules | ✓ VERIFIED | 6 Vitest cases covering mapping/reset/null/default normalization and degraded/non-useful/applicable scenarios; passes in current environment. |
| `frontend/package.json` | Test scripts/harness deps | ✓ VERIFIED | Contains `"test": "vitest run"`, `"test:chat": "vitest run lib/chatApply.test.ts"`, and `vitest` devDependency. |
| `frontend/app/(public)/page.tsx` | Public board integration mounting chat widget | ✓ VERIFIED | Imports and renders `<ChatWidget />` in board page without altering server-rendered board/listing fetch flow. |
| `frontend/components/board/chat/ChatWidget.tsx` | Client-owned session state + orchestration | ✓ VERIFIED | 238 lines; in-memory state for turns/results/pagination/selection; `chatSearch` send/load-more; request-seq guards against stale overwrites; `buildBoardHref` + `appliedParamsToBoardFilters` + `canApplyChatToBoard` apply flow; `JobDetailDialog` integration and `vaga` URL sync; no `localStorage/sessionStorage`. |
| `frontend/components/board/chat/ChatPanel.tsx` | Responsive panel container with preserved visibility behavior | ✓ VERIFIED | Contains `Buscar vagas no chat`, `Fechar chat`, responsive classes, open/close visibility toggle (no conversation reset). |
| `frontend/components/board/chat/ChatInterpretation.tsx` | Entendi/field-status and separate limitations+guidance rendering | ✓ VERIFIED | Contains `Entendi`, `Aplicado`, `Ignorado`, `Aproximado`, and `Limites desta busca`. |
| `frontend/components/board/chat/ChatResultsList.tsx` | Compact results, load-more, conditional apply/manual actions | ✓ VERIFIED | Contains `Carregar mais vagas`, `Aplicar no board`, partial-support note, empty/degraded/manual-search handling. |
| `frontend/components/board/chat/ChatResultItem.tsx` | Public-only clickable result opening canonical detail | ✓ VERIFIED | Shows title/company/local/salary-when-available and `Ver detalhes`; uses `cityLabel`; no contact fields. |
| `frontend/components/board/chat/ChatLauncher.tsx`, `ChatThread.tsx`, `ChatComposer.tsx` | Entry, thread/state rendering, input/send/examples | ✓ VERIFIED | Present and wired in widget/thread flow with required copy/states (`Abrir busca por chat`, `Interpretando sua busca...`, retry/manual-search, examples/placeholders/send CTA). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `ChatWidget.tsx` | `frontend/lib/api.ts` (`chatSearch`) | initial send + load-more calls | ✓ WIRED | `chatSearch({ message, page: 1, limit: 20 })` and paginated `chatSearch({ message: activeQuery, page: nextPage, limit })`; responses update interpretation/items/total. |
| `ChatWidget.tsx` | `frontend/lib/chatApply.ts` + `frontend/lib/filters.ts` | apply-to-board mapping and navigation | ✓ WIRED | `canApplyChatToBoard(...)` gates action; `appliedParamsToBoardFilters(...)` + `buildBoardHref({ ...filters, page: 1, vaga: null })` + `router.replace(href, { scroll:false })`. |
| `ChatWidget.tsx` | `frontend/components/board/JobDetailDialog.tsx` | open selected `JobPublic` result in canonical detail | ✓ WIRED | `selectedJob` state + `<JobDetailDialog job={selectedJob} open onClose={handleCloseDetail} />`; `?vaga` synced via `replaceState`; dialog owns `RevealContact` flow. |
| `frontend/lib/api.ts` (`chatSearch`) | `/api/v1/public/chat-search` | browser fetch POST JSON | ✓ WIRED | `fetch(\`${API}/api/v1/public/chat-search\`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload), signal: AbortSignal.timeout(15_000) })` with non-2xx/transport handling. |
| `frontend/lib/chatApply.ts` | `frontend/lib/filters.ts` (`normalizeFilters`) | canonical normalization/reset semantics | ✓ WIRED | `normalizeFilters({ q, city, sort, page: "1", vaga: "" })` then returns `{ ...normalized, page: 1, vaga: null }`. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| UI-01 | 21-01, 21-02 | Chat simples (drawer/modal), mobile-first e sem login no board público, com envio de mensagem, estados de carregamento/erro e boa percepção de performance | ✓ SATISFIED (code + automated checks; UX perception human) | Launcher/panel/composer/thread mounted on public board; send/loading (`Interpretando sua busca...`), duplicate-send guard, pt-BR error + retry; in-memory session state; `test:chat` green. `.planning/REQUIREMENTS.md` still marks Pending (traceability/docs update outside this verification artifact). |
| UI-02 | 21-01, 21-02 | Exibir parâmetros entendidos/aplicados/ignorados-aproximados e resultados relevantes com acesso ao detalhe/link, reutilizando fluxo atual sem expor contatos no payload do chat | ✓ SATISFIED | `ChatInterpretation` status/reasons/limitations/guidance; `ChatResultsList/ChatResultItem` show título/empresa/local/salário quando disponível and `Ver detalhes`; chat types/items are `JobPublic` only; no contact/reveal endpoints in chat components; detail opened via `JobDetailDialog`. |
| UI-03 | 21-01, 21-02 | Aplicar/ajustar busca entendida no board canônico (URL/filtros existentes) quando aplicável, preservando comportamento atual | ✓ SATISFIED (with minor edge-case note) | `appliedParamsToBoardFilters` + `buildBoardHref` + `router.replace`; apply gated by `canApplyChatToBoard`; canonical reset `page=1`, `vaga` cleared; partial-support note shown. Edge case: `canApplyChatToBoard` treats any non-empty `city` string as applicable before whitelist normalization, so an unknown city can enable apply and normalize to a default/no-op URL (see warnings). |

**Orphaned requirements for Phase 21:** None detected (ROADMAP Phase 21 owns UI-01..UI-03; both plans declare all three).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `frontend/lib/chatApply.ts` | 15-21 | Apply-eligibility uses any non-empty `city` (`hasCity`) instead of verifying whitelist/useful normalized outcome | ⚠️ Warning | Unknown/unsupported city with no other useful params can enable `Aplicar no board` but normalize to default board filters (misleading no-op apply in edge cases). Core whitelisted/normal cases covered by tests. |
| `frontend/components/board/chat/ChatPanel.tsx` | 21-66 | Custom dialog without focus trap/initial focus management (review WR-01) | ⚠️ Warning | Keyboard/screen-reader focus may leave modal panel while open; core open/close/minimize behavior still works. |
| `frontend/components/board/chat/ChatWidget.tsx` | 183-195, 224 | Detail trigger not propagated, so focus restore target can be null (review WR-02) | ⚠️ Warning | After closing detail opened from chat, focus may not return to originating result control. |
| `frontend/lib/api.ts` | 811-838 | `chatSearch` parses success JSON without guarded parse-failure mapping (review WR-03) | ℹ️ Info | Malformed 200 response would throw raw parse error instead of normalized `ApiError`; non-2xx/transport paths are handled. |
| `frontend/components/board/chat/ChatComposer.tsx` | 29-41, 68-97 | 400-char limit enforced on submit only; no `maxLength`/live counter (review WR-04) | ℹ️ Info | UX friction only; server remains authoritative. |

### Human Verification Required

### 1. Mobile/desktop chat panel behavior and layering

**Test:** On mobile viewport and desktop, open chat from launcher, send a query, open a result detail, close detail, and reopen chat.
**Expected:** Bottom-sheet-like behavior on small screens and constrained drawer/panel on desktop; chat does not obscure critical board controls when closed; chat minimizes when detail opens and reopens with preserved conversation/results/interpretation; no overlay/focus traps blocking interaction.
**Why human:** Visual layout, responsive breakpoints, overlay layering, and focus ergonomics cannot be fully proven from static code.

### 2. Loading, error, retry, and pagination flow

**Test:** Send a valid query (and simulate slow/failing backend if possible), observe in-flight state, trigger retry, then use `Carregar mais vagas` on a multi-page result.
**Expected:** "Interpretando sua busca..." shown while waiting, send/load-more controls prevent duplicate in-flight actions, failures show clear pt-BR error with `Tentar novamente`, and additional pages append correctly without losing current interpretation.
**Why human:** Runtime/network timing and perceived behavior require live interaction.

### 3. Interpretation transparency and degraded/manual fallback

**Test:** Exercise responses that include aplicado/ignorado/aproximado fields, limitations/guidance, degraded/no-auto-results, and zero-results cases.
**Expected:** "Entendi..." summary, per-field statuses/reasons, separate "Limites desta busca" guidance, "Não houve resultados automáticos." or "Nenhuma vaga encontrada" states as applicable, and `Usar busca manual` shortcut behaves usefully without exposing contacts.
**Why human:** Requires real API response variety and judgment on clarity/fidelity of pt-BR guidance.

### 4. Apply-to-board canonical navigation and canonical detail/reveal

**Test:** From a non-degraded response with applicable params, click `Aplicar no board`; separately open a chat result detail and reveal contact in the dialog.
**Expected:** Board URL updates canonically (replaces `q/city/sort`, resets `page=1`, clears `vaga`) and board remains usable; opening detail uses canonical dialog/`?vaga` behavior and contact reveal works only in detail flow (never shown in chat).
**Why human:** End-to-end navigation, URL/runtime behavior, and canonical reveal interaction need browser verification.

### Gaps Summary

No blocking codebase gaps found for Phase 21 must-haves. The chat UI, typed client/mapping helpers, interpretation/results rendering, canonical apply flow, and canonical detail integration are present and wired in code, with targeted automated mapping tests passing (`frontend: npm run test:chat` = 6/6). Remaining items are human-verification needs (responsive/focus/layering and live flow behavior) and non-blocking warnings noted in anti-patterns/review (notably focus management, apply-eligibility edge case for unknown cities, and minor client robustness/copy constraints).

---

_Verified: 2026-11-17T21:55:00Z_
_Verifier: OpenCode (gsd-verifier)_