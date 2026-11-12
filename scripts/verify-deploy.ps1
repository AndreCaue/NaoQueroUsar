#Requires -Version 5.1
<#
.SYNOPSIS
  Gate de fumaça pós-deploy (produção) do NaoQueroUsar.

.DESCRIPTION
  Valida o deploy de produção de ponta a ponta:
    1.  GET  /api/v1/health            -> 200, status=ok, env=prod, turnstile.mode=live
                                          (-AllowTestTurnstile aceita mode=test somente
                                           com turnstile.test_override=true)
    2.  Preflight CORS permitido       -> Access-Control-Allow-Origin == origem do frontend
    3.  Preflight CORS negado          -> 400 ou header ausente/diferente de https://evil.example
    4.  Board (/)                      -> 200, contém "Vagas abertas", NÃO vaza contatos
    5.  Legal (/privacidade + /termos-de-uso)
                                       -> 200, LGPD + canal de contato, aviso de
                                          intermediário, sem texto provisório
    6.  API pública                    -> 200, JSON com items/total
    7.  Cron sem segredo               -> 401/403 (recusado) ou 503 (gatilho manual desativado, fail-closed)
    8.  Cron com segredo (idempotente) -> 200 + "deleted" inteiro, 2x
    9.  Não vazamento                  -> secret não aparece no board nem no health
    10. Cold-start (informativo)       -> usa a latência do PRIMEIRO request
                                          (health), não de um request já aquecido

  Compatível com Windows PowerShell 5.1. Salve/edite como UTF-8 **com BOM** —
  o parser de 5.1 precisa do BOM para decodificar corretamente os acentos.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 `
    -FrontendUrl https://<seu-projeto>.vercel.app `
    -BackendUrl  https://<backend>.onrender.com `
    -CronSecret  <CRON_SECRET>
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$FrontendUrl,

    [Parameter(Mandatory = $true)]
    [string]$BackendUrl,

    # Segredo do cron (mesmo valor de CRON_SECRET no backend / secrets.CRON_SECRET no GitHub).
    # Padrão: lê $env:CRON_SECRET da sessão. Sem segredo, o check 8 falha com instrução.
    [string]$CronSecret = $env:CRON_SECRET,

    # DESVIO TEMPORARIO (2026-11-12): aceita o check 1 com turnstile.mode=test
    # (chave publica de teste do Cloudflare) SOMENTE se o backend tambem
    # declarar ALLOW_TEST_TURNSTILE=true no /health. Sem este switch o gate
    # continua exigindo mode=live. Use apenas enquanto nao houver chaves live.
    [switch]$AllowTestTurnstile
)

$ErrorActionPreference = "Stop"

# Windows PowerShell 5.1 pode herdar TLS 1.0 de .NET antigo; Render/Vercel só
# aceitam TLS 1.2+. Fixar aqui evita "Could not create SSL/TLS secure channel".
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$FrontendUrl = $FrontendUrl.TrimEnd('/')
$BackendUrl = $BackendUrl.TrimEnd('/')

function Write-Pass {
    param([string]$Message)
    Write-Output "PASS - $Message"
}

function Assert {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

# Invoke-Http: nunca aborta em 4xx/5xx. Retorna Status (int), Headers
# (hashtable case-insensitive) e Body (string UTF-8). Erros de rede (DNS,
# TLS, timeout, conexão recusada) continuam lançando exceção — são falhas reais.
function Invoke-Http {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Url,
        [hashtable]$Headers = @{}
    )

    $request = [System.Net.HttpWebRequest]::Create($Url)
    $request.Method = $Method
    $request.Timeout = 60000
    $request.ReadWriteTimeout = 60000
    $request.AllowAutoRedirect = $false
    $request.ContentLength = 0

    foreach ($name in $Headers.Keys) {
        $request.Headers[$name] = $Headers[$name]
    }

    $response = $null
    try {
        $response = $request.GetResponse()
    } catch [System.Net.WebException] {
        if ($null -ne $_.Exception.Response) {
            $response = $_.Exception.Response  # 4xx/5xx: tratar como resposta normal
        } else {
            throw  # falha de rede/TLS/DNS: aborta o check com a exceção original
        }
    }

    try {
        $status = [int]$response.StatusCode
        $headers = @{}
        foreach ($key in $response.Headers.AllKeys) {
            $headers[$key] = $response.Headers[$key]
        }
        $memory = New-Object System.IO.MemoryStream
        $stream = $response.GetResponseStream()
        $stream.CopyTo($memory)
        $bodyText = [Text.Encoding]::UTF8.GetString($memory.ToArray())
        return [pscustomobject]@{ Status = $status; Headers = $headers; Body = $bodyText }
    } finally {
        $response.Close()
    }
}

function Get-HeaderValue {
    param($Response, [string]$Name)
    if ($Response.Headers.ContainsKey($Name)) {
        return [string]$Response.Headers[$Name]
    }
    return $null
}

# ---------------------------------------------------------------------------
# 1. Health: deploy de produção de verdade, com Turnstile LIVE
#    O cronômetro começa AQUI porque este é o primeiro request ao backend:
#    num deploy com cold-start, é esta chamada que paga o boot.
# ---------------------------------------------------------------------------
$firstRequestClock = [System.Diagnostics.Stopwatch]::StartNew()
$health = Invoke-Http -Method GET -Url "$BackendUrl/api/v1/health"
$firstRequestClock.Stop()
$firstRequestSeconds = [math]::Round($firstRequestClock.Elapsed.TotalSeconds, 1)

Assert ($health.Status -eq 200) "Health retornou $($health.Status) em $BackendUrl/api/v1/health (esperado 200)"
$healthJson = $health.Body | ConvertFrom-Json
Assert ($healthJson.status -eq "ok") "Health sem status=ok (veio: $($healthJson.status))"
Assert ($healthJson.env -eq "prod") "Health sem env=prod (veio: $($healthJson.env)). Verifique ENV no Render."
$turnstileMode = $healthJson.turnstile.mode
if ($turnstileMode -eq "live") {
    Write-Pass "health 200, env=prod, turnstile.mode=live"
} elseif ($AllowTestTurnstile -and $turnstileMode -eq "test" -and $healthJson.turnstile.test_override -eq $true) {
    Write-Warning "DESVIO TEMPORARIO: backend em ENV=prod usando chave de TESTE do Cloudflare (ALLOW_TEST_TURNSTILE=true). Qualquer token e aceito. Troque pelas chaves live e desligue o flag assim que possivel (D-12)."
    Write-Output "WARN - health 200, env=prod, turnstile.mode=test (escape hatch explicito)"
} else {
    throw "Health sem turnstile.mode=live (veio: $turnstileMode). Chave de teste/ausente em producao. Se for um desvio consciente, suba o backend com ALLOW_TEST_TURNSTILE=true e rode o gate com -AllowTestTurnstile."
}

# ---------------------------------------------------------------------------
# 2. Preflight CORS permitido: origem EXATA do frontend
# ---------------------------------------------------------------------------
$corsOk = Invoke-Http -Method OPTIONS -Url "$BackendUrl/api/v1/public/jobs?limit=1" -Headers @{
    "Origin"                         = $FrontendUrl
    "Access-Control-Request-Method"  = "GET"
}
$allowOrigin = Get-HeaderValue $corsOk "Access-Control-Allow-Origin"
Assert ($null -ne $allowOrigin) "CORS preflight permitido não retornou Access-Control-Allow-Origin (status $($corsOk.Status)). Confira CORS_ORIGINS no Render."
Assert ($allowOrigin -eq $FrontendUrl) "CORS preflight permitido retornou Access-Control-Allow-Origin='$allowOrigin' (esperado '$FrontendUrl'). Sem barra final e sem *."
Write-Pass "CORS preflight permitido ($allowOrigin)"

# ---------------------------------------------------------------------------
# 3. Preflight CORS negado: origem estranha recusada
# ---------------------------------------------------------------------------
$corsBad = Invoke-Http -Method OPTIONS -Url "$BackendUrl/api/v1/public/jobs?limit=1" -Headers @{
    "Origin"                         = "https://evil.example"
    "Access-Control-Request-Method"  = "GET"
}
$badAllowOrigin = Get-HeaderValue $corsBad "Access-Control-Allow-Origin"
$corsRecusado = ($corsBad.Status -eq 400) -or ($null -eq $badAllowOrigin) -or ($badAllowOrigin -ne "https://evil.example")
Assert $corsRecusado "CORS preflight aceitou https://evil.example (status $($corsBad.Status), Access-Control-Allow-Origin='$badAllowOrigin'). CORS_ORIGINS está permissivo demais."
Write-Pass "CORS preflight negado para https://evil.example (status $($corsBad.Status))"

# ---------------------------------------------------------------------------
# 4. Board: 200, com "Vagas abertas", sem vazar contatos no HTML
# ---------------------------------------------------------------------------
$board = Invoke-Http -Method GET -Url "$FrontendUrl/"
Assert ($board.Status -eq 200) "Board retornou $($board.Status) em $FrontendUrl/ (esperado 200)"
Assert ($board.Body -match [regex]::Escape("Vagas abertas")) "Board não contém 'Vagas abertas' — o SSR pode ter falhado"
Assert ($board.Body -notmatch 'contact_email') "Board vaza contact_email no HTML"
Assert ($board.Body -notmatch 'contact_phone') "Board vaza contact_phone no HTML"
Assert ($board.Body -notmatch 'mailto:') "Board vaza mailto: no HTML"
Write-Pass "board 200 sem contact_email/contact_phone/mailto:"

# ---------------------------------------------------------------------------
# 5. Legal: /privacidade (LGPD + canal) e /termos-de-uso (aviso de intermediário)
#    O aviso "somos apenas meio de divulgação" vive nos Termos desde que a
#    Política passou a ser o texto final do operador — não procurar por
#    "intermedi" em /privacidade (falso negativo).
# ---------------------------------------------------------------------------
$legal = Invoke-Http -Method GET -Url "$FrontendUrl/privacidade"
Assert ($legal.Status -eq 200) "/privacidade retornou $($legal.Status) (esperado 200)"
Assert ($legal.Body -imatch 'LGPD') "/privacidade não contém 'LGPD'"
Assert ($legal.Body -imatch '[\w.+-]+@[\w-]+\.[A-Za-z]{2,}') "/privacidade não contém um canal de contato por e-mail (LGPD)"
Assert ($legal.Body -notmatch 'Lorem ipsum|provisóri|\[Seu Nome|\[seu e-mail') "/privacidade ainda contém texto provisório/placeholder"

$terms = Invoke-Http -Method GET -Url "$FrontendUrl/termos-de-uso"
Assert ($terms.Status -eq 200) "/termos-de-uso retornou $($terms.Status) (esperado 200)"
Assert ($terms.Body -imatch 'intermedi') "/termos-de-uso não contém o aviso de intermediário ('intermedi')"
Assert ($terms.Body -notmatch 'Lorem ipsum|provisóri|\[sua cidade|\[Seu Nome') "/termos-de-uso ainda contém texto provisório/placeholder"
Write-Pass "/privacidade 200 (LGPD + canal) e /termos-de-uso 200 (aviso de intermediário)"


# ---------------------------------------------------------------------------
# 6. API pública: 200 com envelope items/total
# ---------------------------------------------------------------------------
$api = Invoke-Http -Method GET -Url "$BackendUrl/api/v1/public/jobs?limit=1"
Assert ($api.Status -eq 200) "API pública retornou $($api.Status) (esperado 200)"
$apiJson = $api.Body | ConvertFrom-Json
Assert ($null -ne $apiJson.items) "API pública sem 'items' no JSON"
Assert ($null -ne $apiJson.total) "API pública sem 'total' no JSON"
Write-Pass "API pública 200 com items/total (total=$($apiJson.total))"

# ---------------------------------------------------------------------------
# 7. Cron SEM segredo: 401, 403 ou 503 (fail-closed; nunca 2xx)
#    503 = gatilho manual desativado (CRON_SECRET ausente) — NÃO é "aberto".
# ---------------------------------------------------------------------------
$cronAnon = Invoke-Http -Method POST -Url "$BackendUrl/api/v1/admin/expire"
if (($cronAnon.Status -eq 401) -or ($cronAnon.Status -eq 403)) {
    Write-Pass "cron sem segredo recusado ($($cronAnon.Status))"
} elseif ($cronAnon.Status -eq 503) {
    Write-Warning "CRON_SECRET não configurado — POST /admin/expire responde 503 (fail-closed). O gatilho manual está desativado; a expiração depende apenas do scheduler in-process. Para habilitar o catch-up, defina CRON_SECRET no backend e em secrets.CRON_SECRET no GitHub."
    Write-Output "WARN - cron manual desativado (503 fail-closed)"
} else {
    throw "POST /admin/expire sem segredo retornou $($cronAnon.Status) (esperado 401/403/503, fail-closed). Um 2xx aqui significa endpoint destrutivo ABERTO."
}

# ---------------------------------------------------------------------------
# 8. Cron COM segredo: 200 + deleted inteiro, 2 chamadas (idempotente)
# ---------------------------------------------------------------------------
if ([string]::IsNullOrWhiteSpace($CronSecret)) {
    throw "CronSecret não informado. Rode com -CronSecret <CRON_SECRET> ou exporte `$env:CRON_SECRET na sessão (é o mesmo valor definido no Render e em GitHub secrets.CRON_SECRET)."
}
$cronFirst = Invoke-Http -Method POST -Url "$BackendUrl/api/v1/admin/expire" -Headers @{ "X-Cron-Secret" = $CronSecret }
Assert ($cronFirst.Status -eq 200) "POST /admin/expire com segredo retornou $($cronFirst.Status) (esperado 200). $($cronFirst.Body)"
$cronFirstJson = $cronFirst.Body | ConvertFrom-Json
$deletedFirst = $cronFirstJson.deleted
$deletedFirstNum = 0
Assert ($null -ne $deletedFirst) "Resposta do cron sem campo 'deleted': $($cronFirst.Body)"
Assert ([int]::TryParse([string]$deletedFirst, [ref]$deletedFirstNum)) "Campo 'deleted' não é inteiro: $deletedFirst"
Assert ($deletedFirstNum -ge 0) "Campo 'deleted' negativo: $deletedFirstNum"
Write-Pass "cron com segredo 200 (deleted=$deletedFirstNum)"

$cronSecond = Invoke-Http -Method POST -Url "$BackendUrl/api/v1/admin/expire" -Headers @{ "X-Cron-Secret" = $CronSecret }
Assert ($cronSecond.Status -eq 200) "Segunda chamada ao cron retornou $($cronSecond.Status) (esperado 200). $($cronSecond.Body)"
$cronSecondJson = $cronSecond.Body | ConvertFrom-Json
$deletedSecond = $cronSecondJson.deleted
$deletedSecondNum = 0
Assert ($null -ne $deletedSecond) "Segunda resposta do cron sem campo 'deleted': $($cronSecond.Body)"
Assert ([int]::TryParse([string]$deletedSecond, [ref]$deletedSecondNum)) "Campo 'deleted' (2a chamada) não é inteiro: $deletedSecond"
Assert ($deletedSecondNum -ge 0) "Campo 'deleted' (2a chamada) negativo: $deletedSecondNum"
Write-Pass "cron idempotente (2a chamada deleted=$deletedSecondNum)"

# ---------------------------------------------------------------------------
# 9. Não vazamento: o segredo não aparece no board nem no health
# ---------------------------------------------------------------------------
if (-not [string]::IsNullOrWhiteSpace($CronSecret)) {
    Assert ($board.Body -notmatch [regex]::Escape($CronSecret)) "Vazamento: CRON_SECRET aparece no HTML do board"
    Assert ($health.Body -notmatch [regex]::Escape($CronSecret)) "Vazamento: CRON_SECRET aparece na resposta de /api/v1/health"
    Assert ($legal.Body -notmatch [regex]::Escape($CronSecret)) "Vazamento: CRON_SECRET aparece na página /privacidade"
    Assert ($terms.Body -notmatch [regex]::Escape($CronSecret)) "Vazamento: CRON_SECRET aparece na página /termos-de-uso"
    Write-Pass "cron secret não vazou no board, health, /privacidade ou /termos-de-uso"
}

# ---------------------------------------------------------------------------
# 10. Cold-start (informativo — nunca falha por latência)
#     Usa a latência do PRIMEIRO request (health), medida no check 1: medir o
#     "primeiro request" aqui, depois de 5+ chamadas ao backend, só mediria o
#     caminho aquecido e nunca observaria o cold-start que o aviso descreve.
#     Para o número refletir o spin-down, rode este gate como o primeiro
#     tráfego após ~20 min de ociosidade do Render.
# ---------------------------------------------------------------------------
Write-Output "INFO - latência do primeiro request (health): ${firstRequestSeconds}s"
if ($firstRequestSeconds -gt 15) {
    Write-Warning "Latência do primeiro request acima de 15 s — acima do timeout de 15 s do frontend (frontend/lib/jobs.ts). O board mostrará 'O servidor está acordando.' + 'Tentar novamente'. Considere plano pago, ping externo opcional ou ajustar o timeout documentado."
}
Write-Pass "cold-start medido (${firstRequestSeconds}s no primeiro request)"


Write-Output "verify-deploy: all checks passed"
