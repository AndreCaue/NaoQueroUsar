---
status: complete
phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review
source: [24-VERIFICATION.md]
started: 2026-11-21T23:45:00Z
updated: 2026-11-22T00:00:00Z
reconciled: 2026-11-22
---

## Current Test

[reconciled — no pending browser/runtime tests; 2 WR-01 scenarios closed as deferred_accepted by item]

## Resolved / Deferred Items

### 1. WR-01 keyboard focus restore
- **expected:** Open chat by keyboard, open job detail by keyboard, close detail via Escape/dialog close. Focus returns to connected trigger or `#chat-panel-close` fallback; never `document.body`; ChatPanel remains mounted behind native dialog.
- **result:** deferred (aceito por item)
- **reason:** deferimento aceito por item
- Motivo: Ambiente browser/integrado indisponível nesta execução de reconciliação; validação de teclado/foco nativo requer browser real.
- Risco residual: Regressão de foco/teclado em ambiente browser real (detalhe aberto pelo chat, fechamento por Escape/controles, tentativa de fechar chat com detalhe aberto) pode não ser percebida até validação manual.
- Ação futura: Revalidar em ambiente browser integrado com teclado (Tab/Shift+Tab/Escape), confirmando que foco retorna ao trigger conectado ou `#chat-panel-close` e nunca cai em `document.body`; registrar evidência no UAT/VERIFICATION.

### 2. Close chat while detail open
- **expected:** With detail open, attempt to activate "Fechar chat" by mouse/keyboard. Chat does not dismiss/unmount; after detail close, focus restores to connected trigger or `#chat-panel-close`, never `document.body`.
- **result:** deferred (aceito por item)
- **reason:** deferimento aceito por item
- Motivo: Ambiente browser/integrado indisponível nesta execução de reconciliação; validação de teclado/foco nativo requer browser real.
- Risco residual: Regressão de foco/teclado em ambiente browser real (detalhe aberto pelo chat, fechamento por Escape/controles, tentativa de fechar chat com detalhe aberto) pode não ser percebida até validação manual.
- Ação futura: Revalidar em ambiente browser integrado com teclado (Tab/Shift+Tab/Escape), confirmando que foco retorna ao trigger conectado ou `#chat-panel-close` e nunca cai em `document.body`; registrar evidência no UAT/VERIFICATION.

## Summary

total: 2
passed: 0
issues: 0
pending: 0
skipped: 0
blocked: 0
deferred_accepted: 2

## Gaps

Nenhum gap crítico aberto. Os 2 itens WR-01 (keyboard/browser) permanecem como deferimentos aceitos por item, com motivo, risco residual e ação futura registrados acima.
