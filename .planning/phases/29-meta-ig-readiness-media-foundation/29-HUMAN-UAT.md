---
status: partial
phase: 29-meta-ig-readiness-media-foundation
source: [29-VERIFICATION.md]
started: 2026-11-23T17:15:00Z
updated: 2026-11-23T17:15:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Confirmar prontidão Instagram real no Meta
expected: Em /admin/integracoes, com Página Facebook conectada e conta Instagram Business/Creator vinculada, o status mostra "Instagram pronto para publicação" com ig_user_id/username; estados missing_linkage e missing_permissions aparecem de forma acionável quando aplicável.
result: [pending]

### 2. Validar URL pública HTTPS de mídia acessível pela Meta
expected: Com MEDIA_PUBLIC_BASE_URL configurada para backend público HTTPS, POST /api/v1/admin/jobs/{job_id}/instagram/media/prepare retorna image_url pública; GET nessa URL sem auth retorna image/jpeg e é acessível externamente pela Meta.
result: [pending]

### 3. Confirmar reconexão/reautorização para escopos IG
expected: Uma conexão Facebook existente sem escopos IG novos exibe estado acionável e, após Reconectar e autorizar, passa a ready sem quebrar o estado Facebook.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
