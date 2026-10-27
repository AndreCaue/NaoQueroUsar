param(
    [string]$BaseUrl = "http://localhost:3100",
    [string]$BackendUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

function Get-Html {
    param([string]$Url)
    $r = Invoke-WebRequest -UseBasicParsing -Uri $Url
    return [Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
}

function Get-Asset {
    param([string]$Url)
    $r = Invoke-WebRequest -UseBasicParsing -Uri $Url
    return [Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
}

function Assert {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) {
        throw $Message
    }
}

function Get-StylesheetUrls {
    param([string]$Html)
    $matches = [regex]::Matches($Html, 'href="([^"]+\.css[^"]*)"')
    $urls = @()
    foreach ($m in $matches) {
        $href = $m.Groups[1].Value
        if ($href.StartsWith("/")) {
            $urls += ($BaseUrl.TrimEnd("/") + $href)
        } elseif ($href.StartsWith("http")) {
            $urls += $href
        }
    }
    return ($urls | Select-Object -Unique)
}

# 1. Home page SSR
$html = Get-Html "$BaseUrl/"
Assert ($html -match "Vagas abertas") "Home missing 'Vagas abertas'"
Assert ($html -match "Ver a vaga") "Home missing 'Ver a vaga'"
$adCount = ([regex]::Matches($html, "Espaço publicitário")).Count
Assert ($adCount -ge 3) "Home has fewer than 3 ad placeholders ($adCount)"
Assert (-not ($html -match "contact_email")) "Home leaks contact_email"
Assert (-not ($html -match "contact_phone")) "Home leaks contact_phone"
Assert (-not ($html -match "mailto:")) "Home leaks mailto:"
Write-Output "PASS - home SSR renders jobs, ads and no contact data"

# 1b. Positive CSS control: at least one stylesheet contains --color-canvas
$cssUrls = Get-StylesheetUrls $html
$hasCanvas = $false
foreach ($cssUrl in $cssUrls) {
    try {
        $css = Get-Asset $cssUrl
        if ($css -match "--color-canvas") { $hasCanvas = $true; break }
    } catch { }
}
Assert $hasCanvas "No stylesheet linked by / contains --color-canvas"
Write-Output "PASS - public Tailwind theme is served"

# 2. Doacoes + admin isolation
$doacoes = Get-Html "$BaseUrl/doacoes"
Assert ($doacoes -match "Doações") "Doacoes page missing 'Doações'"
Write-Output "PASS - doacoes page renders"

$admin = Get-Html "$BaseUrl/admin/paste"
Assert ($admin -match "Colar vagas") "Admin page missing 'Colar vagas'"
Assert (-not ($admin -match "Vagas abertas")) "Admin page leaks public heading"
Assert (-not ($admin -match "Espaço publicitário")) "Admin page leaks ad slot"
$adminCssUrls = Get-StylesheetUrls $admin
foreach ($cssUrl in $adminCssUrls) {
    try {
        $css = Get-Asset $cssUrl
        Assert (-not ($css -match "--color-canvas")) "Admin stylesheet leaks --color-canvas: $cssUrl"
    } catch { }
}
Write-Output "PASS - admin HTML renders its own form and no public theme"

# 3. Empty search state
$empty = Get-Html "$BaseUrl/?q=zzzzzzzz"
Assert ($empty -match "Nenhuma vaga encontrada") "Missing empty-search state"
Assert ($empty -match "Limpar filtros") "Missing clear-filters CTA"
Write-Output "PASS - empty search state"

# 4. Out of range page
$oob = Get-Html "$BaseUrl/?page=99"
Assert ($oob -match "Nenhuma vaga nesta página") "Missing out-of-range page state"
Write-Output "PASS - out-of-range page state"

# 4b. Pagination proof
$page2 = Get-Html "$BaseUrl/?page=2"
Assert ($page2 -match "Página 2 de") "Missing pagination (Página 2 de)"
Write-Output "PASS - pagination page 2"

# 5. API contract
$jobs = Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?limit=50"
Assert ($jobs.items.Count -ge 25) "API returned fewer than 25 jobs - seed not applied"
Assert ($jobs.total -ge 25) "API total fewer than 25"
$id = $jobs.items[0].id
$title = $jobs.items[0].title
$firstWord = ($title -split '\s+')[0]
Write-Output "PASS - API returns seeded jobs"

# 5b. Cap check
try {
    Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?limit=51" | Out-Null
    throw "Expected 422 for limit=51"
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Assert ($status -eq 422) "Expected 422 for limit=51, got $status"
}
Write-Output "PASS - API enforces limit cap (422)"

# 6. Deep links
$deepValid = Get-Html "$BaseUrl/?vaga=$id"
$m = [regex]::Match($deepValid, 'data-dialog-title[^>]*>(?<t>.*?)</')
Assert $m.Success "Valid deep link missing data-dialog-title"
$dialogTitle = [System.Net.WebUtility]::HtmlDecode(($m.Groups['t'].Value -replace '<[^>]+>','').Trim())
$prefix = $title.Substring(0, [Math]::Min(20, $title.Length))
Assert ($dialogTitle.Contains($prefix)) "Deep link dialog title does not match job title"
Assert (-not ($deepValid -match "contact_email")) "Deep link leaks contact_email"
Write-Output "PASS - valid deep link opens dialog"

$bogus = Get-Html "$BaseUrl/?vaga=00000000-0000-4000-8000-000000000000"
Assert ($bogus -match "Vaga não encontrada") "Bogus UUID missing not-found panel"
Assert ($bogus -match "Limpar filtros") "Bogus UUID missing clear-filters CTA"
Assert (-not ($bogus -match "contact_email")) "Bogus deep link leaks contact_email"
Write-Output "PASS - bogus UUID not-found panel"

$malformed = Get-Html "$BaseUrl/?vaga=not-a-uuid"
Assert ($malformed -match "Vaga não encontrada") "Malformed id missing not-found panel"
Assert ($malformed -match "Limpar filtros") "Malformed id missing clear-filters CTA"
Write-Output "PASS - malformed id not-found panel"

# 7. API contract
$one = Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?limit=1"
Assert ($one.items.Count -eq 1) "limit=1 did not return exactly 1 item"

$sp1 = Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?city=sao-paulo&limit=50"
$sp2 = Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?city=Sao%20Paulo&limit=50"
Assert ($sp1.total -eq $sp2.total) "City slug vs canonical totals differ"
foreach ($item in $sp1.items) {
    Assert ($item.city -eq "São Paulo") "City filter returned non-São-Paulo row"
}

$rec = Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?sort=recentes&limit=50"
for ($i = 0; $i -lt $rec.items.Count - 1; $i++) {
    Assert ([datetime]$rec.items[$i].created_at -ge [datetime]$rec.items[$i + 1].created_at) "recentes not non-increasing"
}

$ant = Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?sort=antigas&limit=50"
for ($i = 0; $i -lt $ant.items.Count - 1; $i++) {
    Assert ([datetime]$ant.items[$i].created_at -le [datetime]$ant.items[$i + 1].created_at) "antigas not non-decreasing"
}

$qenc = [uri]::EscapeDataString($firstWord)
$qres = Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?q=$qenc&limit=50"
Assert ($qres.total -ge 1) "Search by first word returned no results"

$unknown = Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?city=atlantida&limit=50"
$unfiltered = Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?limit=50"
Assert ($unknown.total -eq $unfiltered.total) "Unknown city did not fall back to unfiltered total"
Write-Output "PASS - API contract (limit, city, sort, search, unknown city)"

Write-Output "verify-ssr: all checks passed"