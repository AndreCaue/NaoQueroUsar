<#
.SYNOPSIS
  Prepara o banco de testes (Alembic) e opcionalmente executa pytest.

.DESCRIPTION
  Script reprodutível e parametrizado para setup de DB de testes do backend.
  - Valida presença de TEST_DATABASE_URL ou DATABASE_URL (sem defaults secretos).
  - Aponta DATABASE_URL para a URL de teste e executa `alembic upgrade head`.
  - Opcionalmente executa pytest com os alvos informados.

  Compatível com Windows PowerShell 5.1+ / PowerShell 7+.
  NÃO embute credenciais/tokens. Forneça a URL via parâmetro ou variável de ambiente.

.PARAMETER DatabaseUrl
  URL do banco de testes (postgresql+asyncpg://...). Se omitida, usa $env:TEST_DATABASE_URL
  ou, como fallback, $env:DATABASE_URL. Nunca usa valor padrão secreto.

.PARAMETER PythonExe
  Caminho do interpretador Python/venv. Padrão: backend\.venv\Scripts\python.exe (relativo ao repo).

.PARAMETER RunTests
  Quando presente, executa pytest após aplicar migrações.

.PARAMETER PytestArgs
  Argumentos/alvos do pytest (ex.: tests/test_reveal_api.py). Usado apenas com -RunTests.
  Se -RunTests for informado sem -PytestArgs, executa pytest sem alvos específicos (usar com cuidado).

.PARAMETER BackendDir
  Diretório do backend. Padrão: <repo>\backend.

.EXAMPLE
  $env:TEST_DATABASE_URL = "postgresql+asyncpg://USER:PASSWORD@HOST/TESTDB?ssl=require"
  powershell -ExecutionPolicy Bypass -File backend\scripts\setup-test-db.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File backend\scripts\setup-test-db.ps1 -RunTests `
    -PytestArgs "tests/test_reveal_api.py","tests/test_admin_jobs.py"
#>
[CmdletBinding()]
param(
    [string]$DatabaseUrl,
    [string]$PythonExe,
    [switch]$RunTests,
    [string[]]$PytestArgs,
    [string]$BackendDir
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $BackendDir -or [string]::IsNullOrWhiteSpace($BackendDir)) {
    $BackendDir = Join-Path $repoRoot "backend"
}

# Resolve URL: parâmetro > TEST_DATABASE_URL > DATABASE_URL (sem default secreto)
if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    if (-not [string]::IsNullOrWhiteSpace($env:TEST_DATABASE_URL)) {
        $DatabaseUrl = $env:TEST_DATABASE_URL
    } elseif (-not [string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
        $DatabaseUrl = $env:DATABASE_URL
    }
}

if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    Write-Error @"
Nenhuma URL de banco de testes encontrada.
Defina TEST_DATABASE_URL (recomendado) ou DATABASE_URL, ou passe -DatabaseUrl.
Exemplo (placeholder, sem segredo real):
  `$env:TEST_DATABASE_URL = "postgresql+asyncpg://USER:PASSWORD@HOST/TESTDB?ssl=require"
"@
    exit 2
}

if (-not $PythonExe -or [string]::IsNullOrWhiteSpace($PythonExe)) {
    $PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"
}
if (-not (Test-Path $PythonExe)) {
    Write-Error "Python não encontrado em '$PythonExe'. Informe -PythonExe ou crie o venv do backend."
    exit 3
}
if (-not (Test-Path $BackendDir)) {
    Write-Error "Diretório do backend não encontrado: '$BackendDir'"
    exit 4
}

Push-Location $BackendDir
try {
    # Alembic usa Settings().DATABASE_URL (backend/alembic/env.py)
    $env:DATABASE_URL = $DatabaseUrl
    # Mantém TEST_DATABASE_URL coerente para execuções de pytest subsequentes
    if ([string]::IsNullOrWhiteSpace($env:TEST_DATABASE_URL)) {
        $env:TEST_DATABASE_URL = $DatabaseUrl
    }

    Write-Host "==> Aplicando migrações (alembic upgrade head) no banco de testes..."
    & $PythonExe -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha ao executar 'alembic upgrade head' (exit $LASTEXITCODE). Verifique URL, conectividade e estado do schema."
        exit $LASTEXITCODE
    }
    Write-Host "==> Migrações aplicadas com sucesso."

    if ($RunTests) {
        Write-Host "==> Executando pytest..."
        if ($PytestArgs -and $PytestArgs.Count -gt 0) {
            & $PythonExe -m pytest -q @PytestArgs
        } else {
            & $PythonExe -m pytest -q
        }
        $testExit = $LASTEXITCODE
        if ($testExit -ne 0) {
            Write-Error "pytest finalizou com exit $testExit."
            exit $testExit
        }
        Write-Host "==> pytest finalizou com sucesso."
    }
}
finally {
    Pop-Location
}

Write-Host "Concluído."
exit 0
