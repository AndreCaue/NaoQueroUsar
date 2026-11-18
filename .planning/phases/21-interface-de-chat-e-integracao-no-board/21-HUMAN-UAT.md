---
status: partial
phase: 21-interface-de-chat-e-integracao-no-board
source: [21-VERIFICATION.md]
started: 2026-11-17T21:55:00Z
updated: 2026-11-17T21:55:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Mobile/desktop chat panel behavior and layering
expected: On mobile viewport and desktop, open chat from launcher, send a query, open a result detail, close detail, and reopen chat. Bottom-sheet-like behavior on small screens and constrained drawer/panel on desktop; chat does not obscure critical board controls when closed; chat minimizes when detail opens and reopens with preserved conversation/results/interpretation; no overlay/focus traps blocking interaction.
result: [pending]

### 2. Loading, error, retry, and pagination flow
expected: Send a valid query (and simulate slow/failing backend if possible), observe in-flight state, trigger retry, then use `Carregar mais vagas` on a multi-page result. "Interpretando sua busca..." shown while waiting, send/load-more controls prevent duplicate in-flight actions, failures show clear pt-BR error with `Tentar novamente`, and additional pages append correctly without losing current interpretation.
result: [pending]

### 3. Interpretation transparency and degraded/manual fallback
expected: Exercise responses that include aplicado/ignorado/aproximado fields, limitations/guidance, degraded/no-auto-results, and zero-results cases. "Entendi..." summary, per-field statuses/reasons, separate "Limites desta busca" guidance, "Não houve resultados automáticos." or "Nenhuma vaga encontrada" states as applicable, and `Usar busca manual` shortcut behaves usefully without exposing contacts.
result: [pending]

### 4. Apply-to-board canonical navigation and canonical detail/reveal
expected: From a non-degraded response with applicable params, click `Aplicar no board`; separately open a chat result detail and reveal contact in the dialog. Board URL updates canonically (replaces `q/city/sort`, resets `page=1`, clears `vaga`) and board remains usable; opening detail uses canonical dialog/`?vaga` behavior and contact reveal works only in detail flow (never shown in chat).
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
