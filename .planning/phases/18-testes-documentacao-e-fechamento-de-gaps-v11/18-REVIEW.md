---
phase: 18-testes-documentacao-e-fechamento-de-gaps-v11
reviewed: 2026-11-16T00:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - backend/tests/test_facebook_publisher.py
  - backend/tests/test_social_retry_policy.py
  - backend/tests/test_social_idempotency.py
  - backend/tests/test_social_worker_claim.py
  - backend/tests/test_social_publish_pipeline.py
  - docs/TESTING-DB.md
  - docs/META-INTEGRATION-TESTING.md
  - docs/DEPLOY.md
  - backend/scripts/setup-test-db.ps1
  - backend/.env.example
  - frontend/.env.example
  - scripts/verify-deploy.ps1
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-11-16T00:00:00Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Reviewed the Phase 18 closeout scope (DB-backed/social publishing tests, env examples, PowerShell operational scripts, and deploy/testing documentation). No hardcoded production secrets or token values were found in the reviewed files; env/docs consistently use placeholders and backend-only guidance for sensitive values.

Findings focus on (1) deploy-gate script behavior that can misclassify or block the documented "manual cron disabled but fail-closed" state, (2) a test-DB setup script that can unintentionally run the full suite against the configured database when invoked with `-RunTests` and no targets, and (3) minor test-quality/correctness gaps that reduce confidence in the covered contracts.

## Warnings

### WR-01: `verify-deploy.ps1` cannot pass when `/admin/expire` is intentionally fail-closed (503, cron manual disabled)

**File:** `scripts/verify-deploy.ps1:220-235`
**Issue:** Check 7 treats `503` on unauthenticated `POST /admin/expire` as an acceptable fail-closed state (warning, no failure), but the script immediately requires a `CronSecret` and executes authenticated checks 8a/8b. In the documented "gatilho manual desativado; expiração depende apenas do scheduler in-process" case there may be no configured `CRON_SECRET`, so the gate cannot complete/pass even though check 7 explicitly allows that operational mode. This creates a contradictory/unsafe operational handoff: operators cannot obtain a clean gate result for a state the script itself documents as valid.
**Fix:**
```powershell
$cronAnon = Invoke-Http -Method POST -Url "$BackendUrl/api/v1/admin/expire"
$cronManualEnabled = $true
if (($cronAnon.Status -eq 401) -or ($cronAnon.Status -eq 403)) {
    Write-Pass "cron sem segredo recusado ($($cronAnon.Status))"
} elseif ($cronAnon.Status -eq 503) {
    Write-Warning "CRON_SECRET não configurado — POST /admin/expire responde 503 (fail-closed). O gatilho manual está desativado; a expiração depende apenas do scheduler in-process. Para habilitar o catch-up, defina CRON_SECRET no backend e em secrets.CRON_SECRET no GitHub."
    Write-Output "WARN - cron manual desativado (503 fail-closed)"
    $cronManualEnabled = $false
} else {
    throw "POST /admin/expire sem segredo retornou $($cronAnon.Status) (esperado 401/403/503, fail-closed). Um 2xx aqui significa endpoint destrutivo ABERTO."
}

# ... later
if ($cronManualEnabled) {
    if ([string]::IsNullOrWhiteSpace($CronSecret)) {
        throw "CronSecret não informado. Rode com -CronSecret <CRON_SECRET> ou exporte `$env:CRON_SECRET na sessão (é o mesmo valor definido no Render e em GitHub secrets.CRON_SECRET)."
    }
    # checks 8a/8b
} else {
    Write-Output "SKIP - cron com segredo/idempotência (gatilho manual desativado; 503 fail-closed observado)"
}
```
Also document the resulting gate semantics (pass-with-skip/warn) so evidence consumers know manual catch-up was not exercised.

### WR-02: `setup-test-db.ps1 -RunTests` without targets runs the entire pytest suite against the configured test database

**File:** `backend/scripts/setup-test-db.ps1:103-110`
**Issue:** When `-RunTests` is provided without `-PytestArgs`, the script executes `pytest -q` with no targets. `docs/TESTING-DB.md` and the script’s intent are to run targeted DB-backed subsets on an isolated disposable DB; running the full suite can unintentionally execute unrelated/slow/destructive-in-context tests, increase risk of cross-test interference, and produce misleading "DB setup failed/succeeded" signals for Phase 18 closeout evidence. The help text notes "usar com cuidado" but the default behavior remains unsafe for a script whose primary job is deterministic DB setup.
**Fix:**
```powershell
if ($RunTests) {
    if (-not $PytestArgs -or $PytestArgs.Count -eq 0) {
        Write-Error "Refusing to run full pytest suite by default. Provide -PytestArgs with explicit DB-backed targets (e.g. tests/test_reveal_api.py,tests/test_admin_jobs.py)."
        exit 5
    }
    Write-Host "==> Executando pytest..."
    & $PythonExe -m pytest -q @PytestArgs
    $testExit = $LASTEXITCODE
    if ($testExit -ne 0) {
        Write-Error "pytest finalizou com exit $testExit."
        exit $testExit
    }
    Write-Host "==> pytest finalizou com sucesso."
}
```
If a full-suite mode is truly needed, gate it behind an explicit opt-in switch (e.g. `-RunAllTests`).

### WR-03: Placeholder scaffold test provides false confidence and can mask missing worker coverage

**File:** `backend/tests/test_social_worker_claim.py:6-8`
**Issue:** `test_scaffold_phase17` unconditionally asserts `True`. In a phase-closeout test set, always-green placeholder tests inflate pass counts and can hide that meaningful assertions were never added (or regressions in test discovery/reporting). It does not validate cron-secret handling, claim/idempotency, or worker behavior.
**Fix:**
```python
# Remove the placeholder entirely, or replace with a real assertion-bearing test.
# If a module-level smoke marker is needed, prefer an explicit skip with reason:
import pytest

pytestmark = pytest.mark.skip(reason="Scaffold removed; covered by concrete worker tests below")
```
At minimum, delete `test_scaffold_phase17` so CI/evidence reflects only substantive checks.

## Info

### IN-01: Facebook publisher tests couple to Portuguese error-message substrings, making them brittle to safe copy changes

**File:** `backend/tests/test_facebook_publisher.py:97`, `backend/tests/test_facebook_publisher.py:140`, `backend/tests/test_facebook_publisher.py:165`
**Issue:** Assertions validate failure classification primarily by checking for localized message fragments (`"automática"/"tempor"`, `"duplic"/"confirmar"`, `"não foi possível publicar"/"revise"`). This is reasonable for user-facing safety, but small copy edits (or accent/wording normalization) can break tests without changing the actual contract (category/idempotency/retry guidance). The core contract under test is `result.ok` and `result.category`.
**Fix:**
```python
assert result.ok is False
assert result.category == PublishFailureCategory.transient
assert result.error_message  # non-empty safe message
# Optionally assert a stable code/key if the implementation exposes one,
# or centralize expected pt-BR copy in a shared constant used by both code and tests.
```
Keep one dedicated test for user-facing copy if wording is a hard requirement.

### IN-02: Deploy verification record includes historical absolute hosts/URLs that can drift from the canonical state-alvo if reinterpreted as current

**File:** `docs/DEPLOY.md:245-266`
**Issue:** The document clearly labels canônico vs legado/histórico and states not to rewrite history, but the "Registro de verificação" table mixes outcomes across multiple hosts/dates (including failures on canônico and passes on legacy). Without careful reading, operators may misread a legacy PASS row as current canônico readiness. This is a documentation clarity/handoff risk rather than a security issue.
**Fix:**
```markdown
<!-- Add an explicit note directly above the table -->
> **Atenção:** linhas históricas não implicam readiness atual do host canônico.
> Só considerar "pronto" quando houver execução PASS registrada explicitamente
> para os alvos canônicos (`empreganoix.vercel.app` / `empreganoix.onrender.com`)
> na mesma janela de mudança.
```
Optionally add a dedicated `Status canônico atual` row/field updated only after canonical-host verification.

---
_Reviewed: 2026-11-16T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
