---
phase: 13-canonical-host-deploy-ops-alignment
reviewed: 2026-11-15T15:17:53Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - docs/DEPLOY.md
  - scripts/verify-deploy.ps1
  - frontend/.env.example
  - frontend/.env.local.example
  - .github/workflows/expire-cron.yml
findings:
  critical: 0
  warning: 2
  info: 0
  total: 2
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-11-15T15:17:53Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the deploy runbook, smoke-gate script, frontend env templates, and catch-up cron workflow at standard depth. No secrets were found committed, the workflow follows least-privilege and safe retry practices, and the PowerShell gate is generally defensive (explicit HTTP handling, TLS 1.2 fix for 5.1, secret non-leak checks). Two maintainability/correctness issues were identified: a malformed markdown table in the operational runbook that breaks evidence readability, and a gate logic constraint that prevents a full successful run when the manual cron endpoint is intentionally disabled/fail-closed (503) without a configured secret.

## Warnings

### WR-01: Verification log table is structurally malformed

**File:** `docs/DEPLOY.md:241`
**Issue:** The separator row of the "Registro de verificação" table contains far more columns than the header (13 `|`-delimited columns vs 6), which breaks markdown table parsing/rendering for the log. This makes operational evidence harder to read and audit in viewers/editors that rely on valid table structure, undermining the runbook's role as the source of recorded deploy evidence.
**Fix:**
```markdown
| Data (UTC) | Etapa                                               | URL / comando                                                                                  | Resultado observado                                                                                                                                                                                                        | Cold-start | Notas                                                                                                                                                                                                                                                         |
| ---------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-11-12 | Neon — projeto de produção                          | —                                                                                              | não verificado por HTTP                                                                                                                                                                                                    | —          | confirmar no painel (fora do alcance do gate)                                                                                                                                                                                                                 |
| 2026-11-12 | Render — blueprint + segredos                       | —                                                                                              | não verificado por HTTP                                                                                                                                                                                                    | —          | confirmar `alembic upgrade head` no log do deploy                                                                                                                                                                                                             |
```
Ensure every subsequent data row in the same table has exactly the same 6 columns as the header/separator (split long notes into the existing `Notas` cell rather than adding extra `|` columns).

### WR-02: Gate cannot pass when manual cron is intentionally disabled without a secret

**File:** `scripts/verify-deploy.ps1:220-235`
**Issue:** Check 7 correctly treats `503` from `POST /admin/expire` without secret as an acceptable fail-closed/manual-disabled state (warns and continues). However, check 8 unconditionally throws when `$CronSecret` is empty (`CronSecret não informado...`), so the script cannot complete with `verify-deploy: all checks passed` in a deployment where the manual catch-up trigger is intentionally unconfigured—even though check 7 already classified that state as valid. This makes the smoke gate unusable for otherwise-valid verification scenarios and conflates "secret missing" with "gate failed".
**Fix:**
```powershell
# ---------------------------------------------------------------------------
# 7. Cron SEM segredo: 401, 403 ou 503 (fail-closed; nunca 2xx)
#    503 = gatilho manual desativado (CRON_SECRET ausente) — NÃO é "aberto".
# ---------------------------------------------------------------------------
$cronAnon = Invoke-Http -Method POST -Url "$BackendUrl/api/v1/admin/expire"
$cronManualDisabled = $false
if (($cronAnon.Status -eq 401) -or ($cronAnon.Status -eq 403)) {
    Write-Pass "cron sem segredo recusado ($($cronAnon.Status))"
} elseif ($cronAnon.Status -eq 503) {
    $cronManualDisabled = $true
    Write-Warning "CRON_SECRET não configurado — POST /admin/expire responde 503 (fail-closed). O gatilho manual está desativado; a expiração depende apenas do scheduler in-process. Para habilitar o catch-up, defina CRON_SECRET no backend e em secrets.CRON_SECRET no GitHub."
    Write-Output "WARN - cron manual desativado (503 fail-closed)"
} else {
    throw "POST /admin/expire sem segredo retornou $($cronAnon.Status) (esperado 401/403/503, fail-closed). Um 2xx aqui significa endpoint destrutivo ABERTO."
}

# ---------------------------------------------------------------------------
# 8. Cron COM segredo: 200 + deleted inteiro, 2 chamadas (idempotente)
# ---------------------------------------------------------------------------
if ($cronManualDisabled -and [string]::IsNullOrWhiteSpace($CronSecret)) {
    Write-Output "WARN - check 8 ignorado: cron manual desativado (503) e CronSecret não informado"
} else {
    if ([string]::IsNullOrWhiteSpace($CronSecret)) {
        throw "CronSecret não informado. Rode com -CronSecret <CRON_SECRET> ou exporte `$env:CRON_SECRET na sessão (é o mesmo valor definido no Render e em GitHub secrets.CRON_SECRET)."
    }
    # ... existing authenticated/idempotency checks ...
}
```
Alternatively, add an explicit `-SkipCronSecretCheck` switch, but auto-skipping when check 7 already proved the endpoint is disabled/fail-closed better preserves the gate's intent.

---

_Reviewed: 2026-11-15T15:17:53Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
