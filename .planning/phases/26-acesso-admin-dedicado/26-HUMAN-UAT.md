---
status: partial
phase: 26-acesso-admin-dedicado
source: [26-VERIFICATION.md]
started: 2026-11-22T21:38:00Z
updated: 2026-11-22T21:38:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Login admin completo pela página dedicada
expected: Ao acessar /admin/login deslogado, ver formulário dedicado (sem Publicações/Integrações/Sair). Com NEXT_PUBLIC_TURNSTILE_SITE_KEY e backend configurados, informar senha válida, concluir Turnstile, clicar Entrar e ser redirecionado para /admin ou para o next sanitizado (ex.: /admin/review?next=...). /admin/login autenticado redireciona para /admin/next seguro; logout limpa sessão e leva a /admin/login.
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
