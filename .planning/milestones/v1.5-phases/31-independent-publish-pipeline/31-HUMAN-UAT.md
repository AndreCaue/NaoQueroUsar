---
status: partial
phase: 31-independent-publish-pipeline
source: [31-VERIFICATION.md]
started: 2026-11-25T23:59:00Z
updated: 2026-11-25T23:59:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Publicação Instagram real (2 passos) com credenciais Meta válidas
expected: Ao aprovar/publicar uma vaga com Instagram habilitado, o backend cria container, consulta status quando necessário e publica a mídia; status final exibe IDs/permalink e histórico seguro sem tokens.
result: [pending]

### 2. Independência FB x IG em falha real de uma plataforma
expected: Forçando falha no Instagram (ex.: mídia/conta/limite), o Facebook e a publicação do site permanecem íntegros; forçando falha no Facebook, o Instagram não é corrompido.
result: [pending]

### 3. Rate limit/limite diário Instagram em runtime
expected: Ao receber 2207042/content_publishing_limit/rate limit da Meta, UI mostra estado acionável em pt-BR, sem retry storm e sem duplicação cega.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
