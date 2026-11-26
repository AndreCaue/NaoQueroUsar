---
status: partial
phase: 32-hardening-regression-operations
source: [32-VERIFICATION.md]
started: 2026-11-26T13:30:00Z
updated: 2026-11-26T13:30:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Conectar/reconectar Meta+IG e validar prontidão live
expected: Status de integração/prontidão IG coerente em /admin/integracoes, sem exposição de segredos; Facebook permanece utilizável.
result: [pending]

### 2. Smoke publish IG real 2-passos em ambiente autorizado
expected: Publicação IG conclui com status/IDs/permalink sanitizados e logs seguros; sem duplicação.
result: [pending]

### 3. Validar reconciliação ambígua/rate limit real
expected: Estados ambíguos/rate limit ficam acionáveis; sem retry storm; reconciliação antes de republicar quando aplicável.
result: [pending]

### 4. App Review/roles/tasks/Advanced Access
expected: Permissões, papéis e status de review coerentes com operação IG.
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
