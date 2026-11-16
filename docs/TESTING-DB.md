# Banco de testes reprodutível (Postgres/Alembic)

Este guia descreve como preparar um banco Postgres **dedicado a testes** e executar as suítes DB-backed do backend sem segredos reais versionados.

## Objetivo e contrato

- As suítes DB-backed resolvem a URL nesta ordem (ver `backend/tests/conftest.py`): `TEST_DATABASE_URL` (env) → `TEST_DATABASE_URL` (`backend/.env`) → `DATABASE_URL` (env) → `DATABASE_URL` (`backend/.env`).
- Para testes DB-backed, o schema **deve estar migrado** (`alembic upgrade head`). Sem migrações aplicadas, o erro típico no setup/fixtures é: `relation "jobs" does not exist`.
- Use **apenas** um banco de teste isolado (nunca o banco de produção/desenvolvimento com dados reais). As fixtures limpam/isolam dados de testes (`DELETE FROM jobs` e rollback transacional), mas o alvo deve ser descartável.

## Pré-requisitos

- Python 3.11+ e dependências do backend instaladas (`cd backend; uv sync` ou ambiente equivalente).
- Acesso a um Postgres vazio/dedicado (local, container ou Neon de teste).
- Driver/URL assíncrona compatível com o projeto: `postgresql+asyncpg://...` (preferir conexão pooled quando aplicável; `ssl=require` em Neon).

## Variáveis de ambiente (placeholders, sem segredos reais)

Defina **uma** das variáveis abaixo apontando para o DB de testes:

```powershell
# PowerShell (sessão atual) — placeholders
$env:TEST_DATABASE_URL = "postgresql+asyncpg://USER:PASSWORD@ep-XXXX-pooler.REGION.aws.neon.tech/TESTDBNAME?ssl=require"
# (opcional/fallback usado por testes e Alembic via Settings)
$env:DATABASE_URL = $env:TEST_DATABASE_URL
```

```bash
# bash (exemplo)
export TEST_DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@HOST:5432/empreganoix_test?sslmode=require'
export DATABASE_URL="$TEST_DATABASE_URL"
```

> **Nunca** commite credenciais/tokens reais. Use `.env` local (ignorado pelo git) ou variáveis da sessão/CI secret store.

## Aplicar migrações no DB de testes

O Alembic do backend lê a URL de `Settings().DATABASE_URL` (`backend/alembic/env.py`). Para migrar o banco de testes, aponte `DATABASE_URL` para a URL de teste e rode:

```powershell
cd backend
$env:DATABASE_URL = $env:TEST_DATABASE_URL
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Critério de sucesso: comando finaliza sem erro e o schema (incluindo `jobs`, `social_*`, etc.) está presente.

## Script auxiliar (reprodutível)

Há um script parametrizado sem segredos embutidos:

```powershell
# Apenas migra (valida TEST_DATABASE_URL/DATABASE_URL)
powershell -ExecutionPolicy Bypass -File backend\scripts\setup-test-db.ps1

# Migra e executa subconjunto DB-backed
powershell -ExecutionPolicy Bypass -File backend\scripts\setup-test-db.ps1 -RunTests `
  -PytestArgs "tests/test_reveal_api.py","tests/test_admin_jobs.py"
```

Consulte `Get-Help .\backend\scripts\setup-test-db.ps1 -Detailed` para parâmetros.

## Executar subconjuntos DB-backed relevantes

Após `alembic upgrade head` no DB de testes:

```powershell
cd backend
$env:TEST_DATABASE_URL = "postgresql+asyncpg://USER:PASSWORD@HOST/DB_TEST?ssl=require" # placeholder
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_reveal_api.py `
  tests/test_admin_jobs.py `
  tests/test_extract_api.py `
  tests/test_admin_social_publish.py `
  tests/test_admin_social_retry_api.py `
  tests/test_public_search.py -x
```

> Observação: alguns testes/suítes podem ser condicionais ao ambiente/fixtures; execute os subconjuntos que correspondem ao escopo em validação. Em ambientes sem `TEST_DATABASE_URL`/`DATABASE_URL` configurado, `conftest.py` marca testes DB-dependentes como skip (exceto módulos explicitamente DB-independentes).

## Critérios de sucesso

- `alembic upgrade head` executa com sucesso no `DATABASE_URL` de teste.
- `pytest` dos subconjuntos-alvo conclui sem falha de setup por schema ausente.
- Nenhum segredo real foi gravado no repositório.

## Troubleshooting

### `relation "jobs" does not exist`

- **Causa:** banco de testes sem migrações aplicadas (ou URL apontando para banco errado).
- **Correção:** confirme `TEST_DATABASE_URL`/`DATABASE_URL` do DB de teste correto e rode `alembic upgrade head` no `backend` com `DATABASE_URL` apontando para ele; reexecute o pytest.
- **Verificação rápida:** conecte ao DB e confira existência da tabela `jobs` (via psql/cliente), ou reexecute o comando de migração.

### `TEST_DATABASE_URL/DATABASE_URL not set` (skips)

- **Causa:** variável ausente no ambiente/sessão.
- **Correção:** exporte `TEST_DATABASE_URL` (ou `DATABASE_URL`) antes de rodar pytest/alembic.

### Erros de conexão/SSL/credenciais

- **Causa:** URL/host/usuário/senha/região incorretos ou política SSL do provedor.
- **Correção:** valide placeholders e parâmetros (`ssl=require`/`sslmode=require` conforme cliente), e use credenciais fornecidas pelo ambiente seguro (não commitadas).

## Evidência e rastreabilidade

- Documentar comandos executados, DB alvo (sem segredos), data/commit e resultado em artefatos de handoff/verificação da fase (`18-HANDOFFS.md` e verificações relacionadas).
- Não afirmar “passou” sem execução registrada; quando bloqueado por infra/credenciais, manter status **evidência parcial + handoff rastreável** com passos e critérios objetivos.
