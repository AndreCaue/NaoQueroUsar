---
status: partial
phase: 16-geracao-revisao-e-aprovacao-do-post-social
source: [16-VERIFICATION.md]
started: 2026-11-16T00:00:00Z
updated: 2026-11-16T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Fluxo completo de rascunho social no admin
expected: Ao abrir uma vaga em revisão, a seção "Post para Facebook" permite gerar/regenerar, editar, ver contador/prévia/origem, salvar explicitamente, alternar "Publicar agora"/"Agendar publicação" com data/hora em America/Sao_Paulo, e reflete estados "Alterações não salvas" e "Texto bloqueado após aprovação" quando aplicável (além de loading, fallback quando aplicável e erro acionável de SITE_PUBLIC_URL).
result: [pending]

### 2. Aprovação site-first com feedback social
expected: Aprovar vaga com draft salvo registra/agenda social e mostra toast de sucesso social; aprovar sem draft publica a vaga e mostra warning de rascunho ausente; falha de registro social (simulada) mantém vaga publicada e mostra warning sem tratar como falha de publicação do site.
result: [pending]

### 3. Execução dos testes de integração DB-backed
expected: `cd backend && python -m pytest -q tests/test_admin_social_posts.py tests/test_social_post_generation.py tests/test_social_post_policy.py -x` passa em ambiente com banco de testes migrado.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
