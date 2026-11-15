---
phase: 10-rebranding-launch-preparation-empreganoix
reviewed: 2026-11-14T00:00:00Z
depth: standard
files_reviewed: 21
files_reviewed_list:
  - frontend/app/(public)/layout.tsx
  - frontend/app/(public)/doacoes/page.tsx
  - frontend/app/(public)/privacidade/page.tsx
  - frontend/app/(public)/termos-de-uso/page.tsx
  - frontend/app/admin/layout.tsx
  - frontend/lib/contacts.ts
  - frontend/.env.example
  - frontend/app/icon.svg
  - backend/app/main.py
  - backend/pyproject.toml
  - backend/alembic.ini
  - backend/alembic/versions/0001_initial_jobs.py
  - backend/scripts/seed.py
  - backend/README.md
  - README.md
  - AGENTS.md
  - docs/DEPLOY.md
  - render.yaml
  - scripts/verify-deploy.ps1
  - backend/tests/test_cors.py
  - backend/tests/test_brand_rename.py
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-11-14T00:00:00Z
**Depth:** standard
**Files Reviewed:** 21
**Status:** issues_found

## Summary

Reviewed the Phase 10 rebranding/launch-preparation source set (frontend public/admin layouts and legal pages, contact helpers, env/docs/deploy artifacts, backend app/bootstrap/config/migration/seed, and deploy/brand-guard tests). No clear correctness or exploitable security defects were identified in the reviewed application logic at standard depth.

Findings are limited to operational/documentation accuracy and rebrand/guardrail consistency: one misleading deploy-runbook entry for scheduler configuration and one legacy package identifier left behind after the brand rename. Two low-impact maintainability observations are also noted.

## Warnings

### WR-01: `SCHEDULER_ENABLED` description contradicts configured value in deploy runbook

**File:** `docs/DEPLOY.md:83`
**Issue:** The Render environment table documents `SCHEDULER_ENABLED` with value `true` ("padrão, já no blueprint") but states "Desliga o APScheduler in-process; o cron de catch-up continua". This inverts the actual meaning implied by the flag name/value and can lead operators to misconfigure production (disabling the in-process scheduler when they intend to keep it on, or vice versa), weakening expiry coverage during cold-start windows.
**Fix:**
```md
| `SCHEDULER_ENABLED` | `true` (padrão, já no blueprint) | Mantém o APScheduler in-process ativo (sweep diário). Defina `false` para desativá-lo e depender apenas do cron de catch-up do GitHub Actions. |
```

### WR-02: Legacy package name remains after EmpregaNoix rebrand

**File:** `backend/pyproject.toml:2`
**Issue:** The backend project is declared as `name = "nqu-backend"` while the product/description and the rest of the repository have been renamed to EmpregaNoix. This legacy identifier is a branding inconsistency that can confuse packaging, tooling output, and future automation that keys off the project name.
**Fix:**
```toml
[project]
name = "empreganoix-backend"
version = "0.1.0"
description = "EmpregaNoix backend"
```

## Info

### IN-01: Brand-rename guard only scans `frontend/` and `backend/`

**File:** `backend/tests/test_brand_rename.py:37`
**Issue:** `test_no_leftover_brand` asserts against `ROOT / "frontend"` and `ROOT / "backend"` only. Legacy brand tokens in root/deploy/docs/tooling paths (e.g. `docs/`, `scripts/`, `README.md`, `AGENTS.md`, `render.yaml`) are outside this guard's scope, so regressions there would not be caught by the test despite the rename affecting those areas.
**Fix:**
```python
def test_no_leftover_brand():
    roots = [ROOT / "frontend", ROOT / "backend", ROOT / "docs", ROOT / "scripts"]
    files = [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "render.yaml"]
    offenders = []
    for root in roots:
        offenders += _scan(root)
    for path in files:
        if path.exists():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for needle in NEEDLES:
                if needle in text:
                    offenders.append((str(path), needle))
    assert not offenders, offenders
```

### IN-02: Public legal pages expose a direct admin path in navigation

**File:** `frontend/app/(public)/privacidade/page.tsx:23`, `frontend/app/(public)/termos-de-uso/page.tsx:23`
**Issue:** Both public-facing legal pages include a "Painel Admin" link to `/admin/paste` in their header navigation. While admin endpoints remain protected, advertising the admin entry point to all visitors is unnecessary surface disclosure and slightly confusing UX for candidates. Consider removing this link from public pages or limiting it to authenticated/admin contexts.
**Fix:**
```tsx
<nav>
  <ul className="flex gap-6 text-sm">
    <li>
      <a href="/privacidade" className="hover:text-accent-strong transition-colors">
        Política de Privacidade
      </a>
    </li>
    <li>
      <a href="/termos-de-uso" className="hover:text-accent-strong transition-colors">
        Termos de Uso
      </a>
    </li>
  </ul>
</nav>
```

---

_Reviewed: 2026-11-14T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
