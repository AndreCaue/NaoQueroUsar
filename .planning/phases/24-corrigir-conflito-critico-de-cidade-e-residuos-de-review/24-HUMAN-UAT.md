---
status: partial
phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review
source: [24-VERIFICATION.md]
started: 2026-11-21T23:45:00Z
updated: 2026-11-21T23:45:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. WR-01 keyboard focus restore
expected: Open chat by keyboard, open job detail by keyboard, close detail via Escape/dialog close. Focus returns to connected trigger or `#chat-panel-close` fallback; never `document.body`; ChatPanel remains mounted behind native dialog.
result: [pending]

### 2. Close chat while detail open
expected: With detail open, attempt to activate "Fechar chat" by mouse/keyboard. Chat does not dismiss/unmount; after detail close, focus restores to connected trigger or `#chat-panel-close`, never `document.body`.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
