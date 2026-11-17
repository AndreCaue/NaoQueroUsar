---
status: complete
phase: 17-publicacao-assincrona-retry-idempotencia-e-status
source: [17-VERIFICATION.md]
started: 2026-11-16T14:30:00Z
updated: 2026-11-17T00:04:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Publicação real no Facebook (imediata e agendada)
expected: Com integração Meta conectada e app/página válidos, aprovar vaga com "publicar agora" gera tentativa assíncrona e registra published com external_post_id/published_at; agendar para horário futuro é processado pelo worker/cron no horário e publica uma única vez.
result: pass

### 2. Worker cron protegido em ambiente operacional
expected: POST /api/v1/admin/social/worker com X-Cron-Secret válido processa elegíveis (1-5 min) e retorna resumo idempotente sem expor segredos; ausência/segredo inválido/secret não configurado respeitam 401/503 conforme configuração.
result: pass

### 3. Cenários reais de erro/retry da Graph API
expected: Falhas transitórias exibem "Falha temporária..." e reagemendam conforme backoff; token/permissão/reconexão necessária orientam reconexão sem loop automático; resultado ambíguo ou recuperação pós-claim exige verificação consciente sem auto-retry/duplicata.
result: pass

### 4. UX admin ponta a ponta (revisão, diálogo, lista social, retry)
expected: Badges/erros/links/horários pt-BR aparecem corretamente; Tentar novamente só ativa para elegíveis com feedback idempotente; bloqueios ambíguos/reconexão exibem orientação correta; refresh/401 funcionam em sessão expirada.
result: pass

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
