# Phase 18 — Handoffs e Evidências Operacionais (TEST-04, DOC-01, AUD-05)

**Status geral:** artefatos de setup/documentação produzidos no repositório; execuções que dependem de credenciais reais, app/página Meta, browser humano ou hosts canônicos provisionados permanecem como **handoff rastreável** (evidência parcial quando não executadas nesta sessão). Não afirmar pass sem execução registrada.

## DB de testes reprodutível (D-02, AUD-05)

- **Estado:** `handoff rastreável` (setup reprodutível documentado/scriptado; execução DB-backed não realizada nesta sessão por ausência de `TEST_DATABASE_URL`/banco de testes migrado disponível).
- **Artefatos:** `docs/TESTING-DB.md`, `backend/scripts/setup-test-db.ps1`, contrato em `backend/tests/conftest.py` (`TEST_DATABASE_URL`/`DATABASE_URL`, `alembic upgrade head`, troubleshooting `relation "jobs" does not exist`).
- **Pré-requisitos:** Postgres de testes isolado (local/container/Neon de teste), Python/venv do backend, URL `postgresql+asyncpg://...` definida como `TEST_DATABASE_URL` (ou `DATABASE_URL`) sem segredos commitados.
- **Passos/comandos:**
  ```powershell
  # 1) Migrar schema no DB de testes
  cd backend
  $env:DATABASE_URL = $env:TEST_DATABASE_URL
  .\.venv\Scripts\python.exe -m alembic upgrade head

  # 2) Executar subconjuntos DB-backed relevantes
  .\.venv\Scripts\python.exe -m pytest -q `
    tests/test_reveal_api.py tests/test_admin_jobs.py tests/test_extract_api.py `
    tests/test_admin_social_publish.py tests/test_admin_social_retry_api.py tests/test_public_search.py -x

  # Alternativa reproduzível (script)
  powershell -ExecutionPolicy Bypass -File backend\scripts\setup-test-db.ps1 -RunTests `
    -PytestArgs "tests/test_reveal_api.py","tests/test_admin_jobs.py","tests/test_extract_api.py","tests/test_admin_social_publish.py","tests/test_admin_social_retry_api.py","tests/test_public_search.py"
  ```
- **Critério de aceite:** `alembic upgrade head` conclui sem erro no DB de testes e os subconjuntos-alvo executam sem falha de setup por `relation "jobs" does not exist` (skips aceitáveis apenas quando `HAS_DB` false). Registrar comando, data, commit e resumo pass/fail.

## Smoke canônico (gate `scripts/verify-deploy.ps1`) — handoff operacional

- **Estado:** `handoff rastreável` (não executado contra hosts canônicos nesta sessão).
- **Pré-requisitos:** hosts canônicos provisionados/alinhados (`https://empreganoix.vercel.app`, `https://empreganoix.onrender.com`), envs/segredos configurados (`CRON_SECRET` para checks de cron), CORS/Turnstile coerentes com origem canônica. Não expor segredos em logs/histórico.
- **Passos/comando:**
  ```powershell
  $env:CRON_SECRET = "<CRON_SECRET>"   # segredo real apenas no ambiente seguro, não versionar
  powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 `
    -FrontendUrl https://empreganoix.vercel.app `
    -BackendUrl https://empreganoix.onrender.com
  ```
- **Critério de aceite:** script finaliza com `verify-deploy: all checks passed` (health/CORS, superfícies públicas/legais, cron fail-closed/idempotente com `X-Cron-Secret` T-06-01 preservado, sem vazamento). Registrar data, hosts, resultado por check e observações em evidência operacional (ex.: `docs/DEPLOY.md` registro) sem reescrever histórico.
- **Nota:** o gate é parametrizado; execução em hosts legados/históricos só para reproduzir evidência mapeada, sem substituir o alvo canônico.

## Verificações humanas/browser — handoff

- **Estado:** `handoff rastreável` (pendente).
- **Pré-requisitos:** frontend+backend acessíveis (local ou deploy), dados de teste/vagas publicadas e pendentes conforme cenário, widget Turnstile configurado quando aplicável, credenciais de admin de teste.
- **Passos (roteiro objetivo):**
  1. **Público (`/`)**: validar board/cards/busca/filtro/ordenação, modal de vaga, ausência de contato antes do reveal, slots de ads e CTA "Doações" `#facc15` em tema escuro.
  2. **Reveal de contato**: acionar "Mostrar contato" com Turnstile válido; confirmar exibição de telefone/email/WhatsApp/mailto apenas após verificação; confirmar falhas tratadas (token inválido/expirado/rate limit) sem vazamento.
  3. **Admin/revisão**: login protegido, revisão/aprovação/edição conforme fluxos existentes (incl. ADMN-10/REVW-10 pendentes de prova interativa), e status social/retry quando aplicável.
- **Critério de aceite:** cada fluxo observado atende ao comportamento esperado sem exposição de contato/segredos; capturar evidências (prints/notas com data/ambiente/commit) e registrar resultado por item.

## Meta integração real / app em modo desenvolvimento (TEST-04) — handoff

- **Estado:** `handoff rastreável` (roteiro e checklist documentados; execução com app/página Meta reais não realizada nesta sessão por depender de credenciais/ambiente externo).
- **Artefato:** `docs/META-INTEGRATION-TESTING.md`.
- **Pré-requisitos:** app Meta e Página em modo desenvolvimento configurados, permissões mínimas (`pages_show_list`, `pages_manage_posts`, `pages_read_engagement`), `META_*`/`SOCIAL_TOKEN_ENCRYPTION_KEY`/`SITE_PUBLIC_URL`/cron (`CRON_SECRET`) configurados no backend de teste, redirect URI compatível, admin autenticado.
- **Passos:** seguir roteiro TEST-04 em `docs/META-INTEGRATION-TESTING.md` (conectar OAuth, gerar/editar/regenerar rascunho, aprovar publicar agora/agendar, validar status/retry/erros/link sem afetar site) e checklist App Review/modo Live.
- **Critério de aceite:** conexão/status corretos, post registrado/publicado ou agendado conforme escolha, falhas sociais não bloqueiam publicação no site, erros seguros/sem segredos, idempotência/retry respeitados; App Review/modo Live só concluídos com credenciais/revisão real (registrar evidência separada).

## Reconciliação de rastreabilidade (AUD-05)

- `18-AUDIT-MATRIX.md`, `REQUIREMENTS.md` e artefatos de verificação correlatos devem refletir status honesto: **fechado/validado** apenas com evidência executada; **evidência parcial + handoff** quando dependente de runtime/DB/browser/credenciais. (Atualização de `STATE.md`/`ROADMAP.md` é responsabilidade do orquestrador fora de worktree paralelo.)
