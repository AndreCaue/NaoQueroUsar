---
phase: 23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3
plan: 02
subsystem: frontend-chat
tags: [frontend, chat, a11y, hardening, cl-05]
dependency_graph:
  requires:
    - frontend/lib/filters.ts (normalizeFilters canonical board semantics)
    - frontend/lib/cities.ts (supported city normalization context)
  provides:
    - Defensive 200 JSON parsing for chatSearch with safe pt-BR ApiError
    - Board-apply gating based on normalized useful chat params
    - Focused chat dialog/detail focus handling improvements
  affects:
    - frontend/lib/api.ts
    - frontend/lib/chatApply.ts
    - frontend/lib/chatApply.test.ts
    - frontend/components/board/chat/*
tech_stack:
  added: []
  patterns:
    - Defensive response parsing for public chat endpoint success path
    - Apply eligibility derived from normalized canonical board filters
    - Trigger propagation for focus restoration across chat result -> detail flow
key_files:
  created:
    - .planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-02-SUMMARY.md
  modified:
    - frontend/lib/api.ts
    - frontend/lib/chatApply.ts
    - frontend/lib/chatApply.test.ts
    - frontend/components/board/chat/ChatPanel.tsx
    - frontend/components/board/chat/ChatWidget.tsx
    - frontend/components/board/chat/ChatThread.tsx
    - frontend/components/board/chat/ChatResultsList.tsx
    - frontend/components/board/chat/ChatResultItem.tsx
decisions:
  - "canApplyChatToBoard now treats only normalized useful board params (q/cidade suportada/sort antigas) as applyable, blocking city-only non-normalizable no-op cases like `campinas`."
  - "Chat a11y scope kept focused/viable: initial dialog focus and result-trigger focus restoration implemented; full custom focus trap deferred explicitly as non-viable in this pass."
metrics:
  duration: "11 min"
  completed: "2026-11-20T17:18:00-03:00"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 8
---

# Phase 23 Plan 02: Fechamento CL-05 (chat hardening/foco) Summary

Defensive chatSearch 200 parsing, normalized apply gating, and focused chat focus/a11y improvements to close feasible CL-05 frontend gaps without regressing canonical board or privacy behavior.

## Objective

Apply focused frontend corrections and hardening for CL-05 (D-14): defensive JSON parsing in `chatSearch`, correct `canApplyChatToBoard` gating without no-op apply for non-normalizable city-only input, and viable focus/a11y improvements in the chat flow without scope expansion.

## Tasks Completed

| # | Task | Commit | Key files |
|---|------|--------|-----------|
| 1 | Endurecer chatSearch e canApplyChatToBoard com testes determinísticos | `c210fe0` | `frontend/lib/api.ts`, `frontend/lib/chatApply.ts`, `frontend/lib/chatApply.test.ts` |
| 2 | Aplicar melhorias focadas e viáveis de foco/a11y no chat/detail | `03a6182` | `frontend/components/board/chat/ChatPanel.tsx`, `frontend/components/board/chat/ChatWidget.tsx`, `frontend/components/board/chat/ChatThread.tsx`, `frontend/components/board/chat/ChatResultsList.tsx`, `frontend/components/board/chat/ChatResultItem.tsx` |

## Implementation Details

- **`chatSearch` (200):** Added defensive JSON parsing with `try/catch`; invalid JSON now throws `ApiError("Resposta inválida do servidor.", 0)` while preserving existing timeout/transport and non-2xx handling (`readError`).
- **`canApplyChatToBoard`:** Now derives usefulness from `appliedParamsToBoardFilters(...)` normalization (`normalized.q.trim().length > 0 || normalized.city !== null || normalized.sort === "antigas"`) after preserving degraded/`chat_disabled` gating, preventing apply for city-only non-normalizable inputs (e.g. `campinas`) while keeping supported cases.
- **Tests:** Added deterministic coverage for `interpretation({ city: "campinas" }) -> false`; preserved degraded/chat_disabled/empty-default negatives and supported positives (`q`, supported city slug, `sort: "antigas"`).
- **Chat focus/a11y (viable):** `ChatPanel` now sets initial focus to the "Fechar chat" button on open; `ChatResultItem`/`ChatResultsList`/`ChatThread`/`ChatWidget` propagate the originating trigger so closing a detail opened from chat restores focus to that result trigger. Dialog semantics (`role="dialog"`, `aria-modal`, `aria-labelledby`), Escape handling, backdrop close, and canonical chat/apply/detail flow remain intact.

## Verification

- `cd frontend && npx vitest run lib/chatApply.test.ts` — passed (7 tests)
- `cd frontend && npx tsc --noEmit --pretty false` — passed
- Sanity checks:
  - `frontend/lib/api.ts` contains `Resposta inválida do servidor.` in `chatSearch` defensive parse
  - `frontend/components/board/chat/ChatWidget.tsx` no longer contains `onOpenDetail={(job) => handleOpenDetail(job, null)}`

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Threat Flags

None.

## D-14 Disposição (foco/a11y)

**Disposição (b) — deferimento aceito para sub-item não viável sem ampliar escopo/risco:**

- **Implementado (viável, sem sub-item pendente):** foco inicial no diálogo do chat ao abrir (foco no botão "Fechar chat") e propagação/restauração de foco ao fechar detalhe aberto a partir de resultado do chat (`trigger` propagado de `ChatResultItem` → `ChatResultsList` → `ChatThread` → `ChatWidget.handleOpenDetail`, com restauração em `handleCloseDetail`).
- **Sub-item deferido:** *focus-trap completo* no diálogo custom do chat (contenção de ciclo Tab/Shift+Tab dentro do diálogo).
  - **Justificativa:** implementação de trap/focus containment robusto em diálogo custom aumenta complexidade e risco de regressão de interação/teclado; a ação do plano limitou explicitamente a melhorias focadas e viáveis, sem focus-trap complexo/custom.
  - **Risco residual:** usuários de teclado/leitor de tela podem mover foco para elementos fora do diálogo enquanto ele estiver aberto.
  - **Condição/ação futura:** avaliar introdução de focus-trap/contenção dedicada no componente de chat (ou primitiva com gerenciamento de foco) com validação manual de teclado/a11y antes de fechamento.
- **Propagação explícita (residual):** este deferimento residual deve ser propagado para os artefatos de reconciliação da fase 22 em 23-03 (`22-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, `22-VERIFICATION.md`, conforme aplicável) e, se ainda residual, refletido no fechamento de auditoria em 23-05 (`v1.3-MILESTONE-AUDIT.md`).

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-02-SUMMARY.md`
- FOUND: `frontend/lib/api.ts`
- FOUND: `frontend/lib/chatApply.ts`
- FOUND: `frontend/lib/chatApply.test.ts`
- FOUND: `frontend/components/board/chat/ChatPanel.tsx`
- FOUND: `frontend/components/board/chat/ChatWidget.tsx`
- FOUND: `frontend/components/board/chat/ChatThread.tsx`
- FOUND: `frontend/components/board/chat/ChatResultsList.tsx`
- FOUND: `frontend/components/board/chat/ChatResultItem.tsx`
- FOUND commit: `c210fe0`
- FOUND commit: `03a6182`

## Commits

- `c210fe0` — `fix(23-02): harden chatSearch parsing and apply gating`
- `03a6182` — `fix(23-02): improve chat focus handling and detail return focus`
