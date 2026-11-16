---
status: partial
phase: 18-testes-documentacao-e-fechamento-de-gaps-v11
source: [18-VERIFICATION.md]
started: 2026-11-16T00:00:00Z
updated: 2026-11-16T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Reexecutar suítes DB-backed em banco de testes migrado
expected: Subconjuntos DB-backed relevantes (ex.: test_reveal_api.py, test_admin_jobs.py, test_extract_api.py, test_public_search.py, test_admin_social_publish.py, test_admin_social_retry_api.py, test_social_worker_claim.py e afins) executam sem falha de setup por `relation "jobs" does not exist` após `alembic upgrade head` no `TEST_DATABASE_URL`.
result: [pending]

### 2. Validação humana/browser dos fluxos públicos e admin
expected: Board/cards/modal/reveal, busca/filtro/ordenação, tema dark/roxo, botão 'Doações' `#facc15`, slots de ads e fluxos admin/revisão/status social comportam-se conforme aceite; contato não vaza antes do reveal.
result: [pending]

### 3. Smoke/runtime canônico com gate parametrizado
expected: `powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 -FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com` conclui checks aplicáveis conforme `docs/DEPLOY.md`/handoff, preservando T-06-01 (`/admin/expire` com `X-Cron-Secret`, fail-closed).
result: [pending]

### 4. Roteiro manual Meta (TEST-04) com app/página em modo desenvolvimento
expected: Conexão OAuth, geração/edição/regeneração/aprovação (agora/agendar), status/retry/erros/link e não-bloqueio do site validados ponta a ponta conforme `docs/META-INTEGRATION-TESTING.md`; App Review/modo Live checklist tratado com credenciais/revisão reais.
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
