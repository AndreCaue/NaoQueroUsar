# Phase 10: Rebranding & Launch Preparation (EmpregaNoix) - Pattern Map

**Mapped:** 2026-11-14
**Files analyzed:** 39 (new + modified)
**Analogs found:** 33 / 39 (6 brand-asset files have no in-repo analog — use RESEARCH.md Pattern 2)

## File Classification

### New files (created)

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `frontend/app/icon.png` | asset (favicon source 512×512) | static | (none — no favicon exists) | no-analog |
| `frontend/app/apple-icon.png` | asset (180×180) | static | `frontend/app/icon.png` (reuse) | role-match |
| `frontend/app/opengraph-image.png` | asset (1200×630) | static | (none) | no-analog |
| `frontend/public/logo.svg` (optional) | asset (horizontal logo) | static | (none) | no-analog |
| `frontend/public/logo-mark.svg` (optional) | asset (mark 32×32) | static | `frontend/public/logo.svg` | role-match |
| `frontend/public/favicon.ico` (optional) | asset (32×32 retrocompat) | static | `frontend/app/icon.png` | role-match |
| `backend/tests/test_brand_rename.py` (Wave 0 gap, optional) | test | request-response | `backend/tests/test_cors.py` | role-match |

### Modified files — Frontend

| Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------|------|-----------|----------------|---------------|
| `frontend/app/(public)/layout.tsx` | layout (metadata + wordmark) | request-response (RSC) | itself (modify in place) | exact |
| `frontend/app/(public)/page.tsx` | page (RSC) | request-response | itself | exact |
| `frontend/app/(public)/privacidade/page.tsx` | page (RSC, legal) | request-response | `frontend/app/(public)/termos-de-uso/page.tsx` | exact |
| `frontend/app/(public)/termos-de-uso/page.tsx` | page (RSC, legal) | request-response | `frontend/app/(public)/privacidade/page.tsx` | exact |
| `frontend/app/(public)/doacoes/page.tsx` | page (RSC) | request-response | `frontend/app/(public)/privacidade/page.tsx` (metadata pattern) | role-match |
| `frontend/app/admin/layout.tsx` | layout (metadata + wordmark) | request-response (RSC) | `frontend/app/(public)/layout.tsx` | exact |
| `frontend/lib/contacts.ts` | utility (link builders) | transform | itself | exact |
| `frontend/.env.example` | config | static | itself | exact |
| `frontend/app/layout.tsx` | root layout | request-response (RSC) | itself | exact |

### Modified files — Backend

| Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------|------|-----------|----------------|---------------|
| `backend/app/main.py` | app factory (FastAPI title) | request-response | itself | exact |
| `backend/pyproject.toml` | config | static | itself | exact |
| `backend/alembic.ini` | config | static | itself | exact |
| `backend/alembic/versions/0001_initial_jobs.py` | migration | batch (DDL) | itself (comment only) | exact |
| `backend/scripts/seed.py` | script (seed data) | CRUD | itself | exact |
| `backend/README.md` | docs | static | itself | exact |
| `backend/tests/test_cors.py` | test | request-response | itself | exact |

### Modified files — Docs / Infra / Planning

| Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------|------|-----------|----------------|---------------|
| `README.md` (root) | docs | static | itself | exact |
| `AGENTS.md` | docs (GSD block) | static | itself | exact |
| `docs/DEPLOY.md` | docs (runbook) | static | itself | exact |
| `render.yaml` | config (infra) | static | itself | exact |
| `scripts/verify-deploy.ps1` | script (smoke gate) | request-response | itself | exact |
| `.planning/PROJECT.md` | docs | static | itself | exact |
| `.planning/REQUIREMENTS.md` | docs | static | itself | exact |
| `.planning/ROADMAP.md` | docs | static | itself | exact |
| `.planning/STATE.md` | docs | static | itself | exact |
| `.planning/research/*.md` | docs (optional) | static | itself | exact |

## Pattern Assignments

### `frontend/app/(public)/layout.tsx` (layout, request-response RSC)

**Analog:** itself (modify in place) — pattern is the existing metadata export + wordmark.

**Imports pattern** (lines 1-4):
```typescript
import type { Metadata, Viewport } from "next";
import Link from "next/link";

import "./public.css";
```

**Metadata pattern** (lines 6-10) — update `title` only; `description` already correct:
```typescript
export const metadata: Metadata = {
  title: "NaoQueroUsar — Vagas sem cadastro",
  description:
    "Encontre vagas e o contato para se candidatar em segundos. Sem conta, sem login e sem burocracia.",
};
```
After rename:
```typescript
export const metadata: Metadata = {
  title: "EmpregaNoix — Vagas sem cadastro",
  description:
    "Encontre vagas e o contato para se candidatar em segundos. Sem conta, sem login e sem burocracia.",
};
```

**Wordmark pattern** (lines 33-37) — swap literal only:
```tsx
<Link href="/" className="text-xl font-semibold text-fg">
  NaoQueroUsar
  <span aria-hidden="true" className="text-accent-soft">
    .
  </span>
</Link>
```

**Copyright pattern** (line 59):
```tsx
<span>© 2026 NaoQueroUsar</span>
```

**Optional — metadataBase / og (D-05, new assets):** add once `opengraph-image.png` exists:
```typescript
export const metadata: Metadata = {
  title: "EmpregaNoix — Vagas sem cadastro",
  description: "...",
  metadataBase: new URL("https://empreganoix.vercel.app"),
  openGraph: {
    title: "EmpregaNoix — Vagas sem cadastro",
    description: "...",
    url: "https://empreganoix.vercel.app",
    images: ["/opengraph-image.png"],
  },
  icons: { icon: "/icon.png", apple: "/apple-icon.png" },
};
```

---

### `frontend/app/admin/layout.tsx` (layout, request-response RSC)

**Analog:** `frontend/app/(public)/layout.tsx` (same wordmark/metadata structure).

**Metadata pattern** (lines 8-11):
```typescript
export const metadata: Metadata = {
  title: "NaoQueroUsar - Painel admin",
  description: "Painel de administração - curadoria de vagas",
};
```
After rename: `title: "EmpregaNoix - Painel admin"`.

**Wordmark pattern** (lines 28-32) — same as public layout (swap `NaoQueroUsar` → `EmpregaNoix`).

---

### `frontend/lib/contacts.ts` (utility, transform)

**Analog:** itself.

**WhatsApp template pattern** (line 16):
```typescript
export function messageFor(title: string): string {
  return `Olá! Vi a vaga "${title}" no NaoQueroUsar e quero me candidatar.`;
}
```
After rename:
```typescript
export function messageFor(title: string): string {
  return `Olá! Vi a vaga "${title}" no EmpregaNoix e quero me candidatar.`;
}
```

Note: `mailtoHref` subject (`Candidatura: ${title}`) is brand-free — no change.

---

### `frontend/app/(public)/privacidade/page.tsx` & `frontend/app/(public)/termos-de-uso/page.tsx` (page, RSC, legal)

**Analog:** each other (identical badge/email pattern).

**Metadata pattern** (privacidade lines 6-10):
```typescript
export const metadata: Metadata = {
  title: "Política de Privacidade — NaoQueroUsar",
  description:
    "Política de privacidade da plataforma NQU — NaoQueroUsar. Como coletamos, usamos e protegemos seus dados.",
};
```
After: `title: "Política de Privacidade — EmpregaNoix"`, `description: "Política de privacidade da plataforma EmpregaNoix. Como coletamos, usamos e protegemos seus dados."`

**Badge wordmark pattern** (line 18):
```tsx
<span className="text-2xl font-bold">NQU</span>
```
After: `<span className="text-2xl font-bold">EmpregaNoix</span>`

**Controller/razão pattern** (line 51):
```tsx
O site <strong>NQU</strong> é operado por{" "}
<strong>André Cauê G.C</strong>, ...
```
After: `O site <strong>EmpregaNoix</strong> é operado por ...`

**Occurrences to replace in body:** all `NQU`/`NaoQueroUsar` textual references (13 sections privacidade, 10 sections termos) → `EmpregaNoix`; `suportenqs@outlook.com` → `empreganoix@outlook.com` (lines 199, 225 privacidade; line 181 termos).

**Rule:** preserve 100% of legal wording; only swap brand strings + e-mail. Do not rewrite content.

---

### `frontend/app/(public)/doacoes/page.tsx` (page, RSC)

**Analog:** `frontend/app/(public)/privacidade/page.tsx` (metadata pattern).

**Metadata pattern** (lines 4-6):
```typescript
export const metadata: Metadata = {
  title: "Doações — NaoQueroUsar",
};
```
After: `title: "Doações — EmpregaNoix"`.

**Body pattern** (lines 14-16):
```tsx
<p className="mt-4 text-base leading-normal text-fg">
  Em breve você poderá apoiar o NaoQueroUsar por PIX. Enquanto isso,
  compartilhe as vagas com quem está procurando emprego.
</p>
```
After: `Em breve você poderá apoiar o EmpregaNoix por PIX. Enquanto isso, compartilhe as vagas com quem está procurando emprego.`

---

### `backend/app/main.py` (app factory, request-response)

**Analog:** itself.

**Title pattern** (line 35):
```python
app = FastAPI(title="NQU API", lifespan=lifespan)
```
After: `app = FastAPI(title="EmpregaNoix API", lifespan=lifespan)`

No other change — CORS still driven by `settings.cors_origins_list` (env-driven, no hardcoded host).

---

### `backend/scripts/seed.py` (script, CRUD)

**Analog:** itself.

**Company pattern** (line 29):
```python
company="NQU Seed",
```
After: `company="EmpregaNoix Seed",`

---

### `backend/pyproject.toml` / `backend/alembic.ini` / migration / README (config/docs)

**Analog:** themselves (mechanical string swap).

- `pyproject.toml` line 2: `name = "nqu-backend"` → `name = "empreganoix-backend"` (discretionary; prefer keeping `nqu-backend` if CI/lock depend on it); line 4: `description = "NQU backend"` → `description = "EmpregaNoix backend"`.
- `alembic.ini` line 1: `# Alembic configuration for the NQU backend.` → `# Alembic configuration for the EmpregaNoix backend.`
- `backend/alembic/versions/0001_initial_jobs.py` line 7: `Creates the `jobs` data contract for NQU:` → `... for EmpregaNoix:` (comment only — migration is forward-only, never edit schema).
- `backend/README.md`: `NQU Backend` → `EmpregaNoix Backend`.
- `README.md` (root) line 1: `# NQU — NaoQueroUsar` → `# EmpregaNoix`.
- `AGENTS.md` line 4: `**NQU — NaoQueroUsar**` → `**EmpregaNoix**`.

---

### `backend/tests/test_cors.py` (test, request-response)

**Analog:** itself (update host examples for consistency, keep assertions).

**Parametrize pattern** (lines 66-69):
```python
@pytest.mark.parametrize(
    "origin",
    ["", "*", "https://nao-quero-usar.vercel.app/", "nao-quero-usar.vercel.app"],
)
```
After (consistency, BRND-04): replace `https://nao-quero-usar.vercel.app/` → `https://empreganoix.vercel.app/` and `nao-quero-usar.vercel.app` → `empreganoix.vercel.app`.

**Accept pattern** (lines 80-87):
```python
settings = _settings(
    ENV="prod",
    CORS_ORIGINS=" https://nao-quero-usar.vercel.app , https://admin.example ",
    TURNSTILE_SECRET_KEY="z" * 35,
)
assert settings.cors_origins_list == [
    "https://nao-quero-usar.vercel.app",
    "https://admin.example",
]
```
After: swap the host string to `https://empreganoix.vercel.app`. Behavior assertions stay identical.

---

### `frontend/.env.example` (config, static)

**Analog:** itself.

Line 1: `# Frontend — variáveis de ambiente (NQU)` → `# Frontend — variáveis de ambiente (EmpregaNoix)`.

---

### `render.yaml` / `scripts/verify-deploy.ps1` / `docs/DEPLOY.md` (config/script/docs)

**Analog:** themselves.

- `render.yaml` line 1: `# Blueprint do backend NQU no Render (free tier).` → `# Blueprint do backend EmpregaNoix no Render (free tier).`; line 37: `name: nqu-backend` → `name: empreganoix-backend` (optional — service name; renaming changes the URL, so keep `nqu-backend` if the existing Render service is already named that way; rename only if creating a new service).
- `scripts/verify-deploy.ps1` line 4: `Gate de fumaça pós-deploy (produção) do NaoQueroUsar.` → `... do EmpregaNoix.`
- `docs/DEPLOY.md` line 1: `# Deploy — NaoQueroUsar (NQU)` → `# Deploy — EmpregaNoix`; host examples `nao-quero-usar.vercel.app` / `naoquerousar.onrender.com` → `empreganoix.vercel.app` / `empreganoix.onrender.com`.

---

### `frontend/app/icon.png` / `apple-icon.png` / `opengraph-image.png` (new assets)

**Analog:** none in repo. Use RESEARCH.md Pattern 2 (Next.js file-based metadata).

**Pattern (from RESEARCH.md):** place files in `frontend/app/`:
- `frontend/app/icon.png` — source 512×512 (Next generates 16/32/48/192 `<link rel="icon">`).
- `frontend/app/apple-icon.png` — 180×180 (`<link rel="apple-touch-icon">`).
- `frontend/app/opengraph-image.png` — 1200×630 (`<meta property="og:image">`).

No code change needed beyond dropping the files; Next auto-generates tags. Optional explicit metadata in `frontend/app/(public)/layout.tsx` (see excerpt above) if `metadataBase`/`og:url` must be pinned to `https://empreganoix.vercel.app`.

**Fallback (D-05):** if assets lag, keep wordmark textual and accept Next's default globe favicon; deploy not blocked.

---

### `backend/tests/test_brand_rename.py` (optional Wave 0 gap)

**Analog:** `backend/tests/test_cors.py` (pytest style + conftest `client` fixture).

**Pattern to copy** (test file skeleton):
```python
"""Brand rename guard (BRND-01): no leftover 'NaoQueroUsar'/'NQU'/'suportenqs'."""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def test_no_leftover_brand_in_frontend():
    frontend = ROOT / "frontend"
    offenders = []
    for p in frontend.rglob("*"):
        if p.is_file() and p.suffix in {".ts", ".tsx", ".js", ".jsx", ".css", ".example"}:
            text = p.read_text(encoding="utf-8", errors="ignore")
            for needle in ("NaoQueroUsar", "suportenqs"):
                if needle in text:
                    offenders.append((str(p), needle))
    assert not offenders, offenders
```

(Recommended to keep as a grep/CI assertion rather than a pytest, per RESEARCH.md Validation Architecture; either is acceptable.)

## Shared Patterns

### Brand wordmark (textual fallback)
**Source:** `frontend/app/(public)/layout.tsx` lines 33-37 and `frontend/app/admin/layout.tsx` lines 28-32
**Apply to:** all layouts (public + admin) — keep wordmark textual `EmpregaNoix` + `.` accent-soft even after logo asset arrives (fallback).
```tsx
<Link href="/" className="text-xl font-semibold text-fg">
  EmpregaNoix
  <span aria-hidden="true" className="text-accent-soft">
    .
  </span>
</Link>
```

### Metadata per route
**Source:** `frontend/app/(public)/layout.tsx` lines 6-10
**Apply to:** every `page.tsx`/`layout.tsx` with a `title` referencing the brand.
```typescript
export const metadata: Metadata = {
  title: "EmpregaNoix — Vagas sem cadastro",
  description: "...",
};
```

### Host/CORS is env-driven (no hardcoded host)
**Source:** `backend/app/main.py` lines 37-46 + `backend/app/core/config.py` (CORS fail-closed, T-09-13)
**Apply to:** BRND-04 — hosts change via dashboard env vars + rebuild; no code host strings. Smoke gate verifies `Access-Control-Allow-Origin == https://empreganoix.vercel.app`.

### Legal-page preservation rule
**Source:** `frontend/app/(public)/privacidade/page.tsx` + `frontend/app/(public)/termos-de-uso/page.tsx`
**Apply to:** both legal pages — swap only brand strings (`NQU`/`NaoQueroUsar` → `EmpregaNoix`) and e-mail (`suportenqs@outlook.com` → `empreganoix@outlook.com`); preserve 100% of legal wording and structure.

### Migration forward-only
**Source:** `backend/alembic/versions/0001_initial_jobs.py` (comment only)
**Apply to:** migration file — only the docstring comment changes; never edit schema or history.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `frontend/app/icon.png` | asset | static | No favicon/icon exists in repo yet — use RESEARCH.md Pattern 2 (Next.js file-based metadata). |
| `frontend/app/opengraph-image.png` | asset | static | No og:image exists — use RESEARCH.md Pattern 2. |
| `frontend/public/logo.svg` | asset | static | No logo asset exists — D-05 allows textual wordmark fallback; generate via image tool or keep fallback. |
| `frontend/public/logo-mark.svg` | asset | static | Optional; depends on logo.svg. |
| `frontend/public/favicon.ico` | asset | static | Optional retrocompat; reuse icon.png. |

## Metadata

**Analog search scope:** `frontend/`, `backend/`, `docs/`, `scripts/`, `.planning/` (content only; directory names untouched per D-01).
**Files scanned:** 39 (rename inventory from 10-RESEARCH.md + 10-UI-SPEC Component Inventory).
**Pattern extraction date:** 2026-11-14
**Notes:** This phase is ~90% mechanical rename + config + deploy. No new runtime dependencies, no new React components, no schema changes. Brand assets are the only genuinely new files and have no in-repo analog — follow RESEARCH.md Pattern 2 (file-based metadata) and the D-05 fallback. Hosts/CORS/env changes are dashboard config, not code.
