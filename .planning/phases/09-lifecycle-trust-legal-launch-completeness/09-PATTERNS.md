# Phase 9 — Pattern Map

> Stand-in for `gsd-pattern-mapper` (subagent limit reached). Every analog below
> was read from the current tree; executors must copy these conventions instead
> of inventing new ones.

---

## File → closest analog

| New / modified file | Closest existing analog | Convention to copy |
|---------------------|-------------------------|--------------------|
| `backend/tests/test_cors.py` (new) | `backend/tests/test_public_api.py:88-124` | `async def` tests using the `client` fixture, `Origin` header, assert `access-control-allow-origin` echo |
| `backend/tests/test_schema.py` (extend) | `test_schema.py:44-57` (`test_expires_at_defaults_to_14_days`) | Use `db_session`, `text()` from SQLAlchemy for DDL probes, assert exact strings |
| `backend/tests/test_admin_expire.py` (extend) | `test_admin_expire.py:29-48` (`_make_job` / `_expired` / `_live` helpers), `:132-155` | Build `Job(...)` rows with `expires_at`, call `POST /api/v1/admin/expire` with `X-Cron-Secret`, assert JSON |
| `backend/app/core/config.py` (extend) | `_validate_turnstile` model validator (`config.py:73-98`) and `cors_origins_list` (`:114-117`) | Add a second `@model_validator(mode="after")`; raise `ValueError` with a pt-BR message; never log secrets |
| `frontend/app/(public)/privacidade/page.tsx` (rewrite body) | `frontend/app/(public)/doacoes/page.tsx` (public shell page) | RSC, no `<main>`/`<header>`/`<footer>`, tokens from `public.css`, `export const metadata` |
| `frontend/app/(public)/termos-de-uso/page.tsx` (rewrite body) | same as above | Same; preserve legal copy verbatim |
| `frontend/app/(public)/layout.tsx` footer | Current footer at `:57-68` | `Link` + `min-h-11 inline-flex items-center hover:text-accent-soft` |
| `render.yaml` | Existing service block (`envVars` list) | Add `- key: SCHEDULER_ENABLED` / `value: "true"`; keep secrets `sync: false` |
| `scripts/verify-deploy.ps1` check 5 | Existing `Assert` lines `:191-201` | `Assert ($terms.Body -imatch '…')` with a pt-BR failure message |

---

## Backend test conventions

```python
# test_public_api.py:110-121 — CORS preflight pattern
resp = await client.options(
    f"/api/v1/public/jobs/{uuid.uuid4()}/reveal-contact",
    headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    },
)
assert resp.status_code == 200
assert "POST" in resp.headers.get("access-control-allow-methods", "").upper()
```

- Tests are async without an explicit marker (`asyncio_mode=auto` in
  `backend/pyproject.toml`).
- `client` comes from `conftest.py`; `db_session` is rolled back per test;
  `reset_rate_limiter` is autouse.
- Run pytest **from `backend/`** or `asyncio_mode` is lost and the whole suite
  errors out.
- Rows require at least one contact (`contact_phone` or `contact_email`) — the
  `_make_job` helper already handles this.
- Use `JobStatus.pending` / `.needs_review` / `.invalid` / `.published` (enum),
  not raw strings.

## Config validator conventions

```python
# config.py:73-98 — the shape to follow
@model_validator(mode="after")
def _validate_turnstile(self) -> "Settings":
    if self.ENV != "dev":
        ...
        raise ValueError("mensagem pt-BR (D-12)")
    return self
```

- Validators are **after** validators that mutate nothing and return `self`.
- Production-only rules gate on `self.ENV != "dev"`.
- Messages are pt-BR and reference the decision id.
- Tests construct `Settings(...)` directly (see `tests/test_security_config.py`)
  rather than relying on the cached `get_settings()`.

## Frontend page conventions

```tsx
// doacoes/page.tsx — public shell page (no nested landmarks)
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Doações — NaoQueroUsar",
  description: "…",
};

export default function Page() {
  return (
    <section className="mx-auto w-full max-w-3xl py-4">
      <h1 className="text-2xl font-semibold text-fg">…</h1>
      <h2 className="mt-6 text-xl font-semibold text-fg">1. …</h2>
    </section>
  );
}
```

- Tokens only: `bg-canvas`, `text-fg`, `text-fg-muted`, `border-line`,
  `border-line-strong`, `text-accent-soft`, `bg-surface`.
- Never `bg-gray-900`, `text-white`, `border-gray-700`, `text-accent-strong`.
- `(public)/layout.tsx` already provides `<main class="max-w-[1120px]">`; pages
  must not add another `<main>`/`<header>`/`<footer>`.
- Internal links use `next/link`.
- Footer links keep `min-h-11 inline-flex items-center` for the 44 px target.

## PowerShell / repo commands

- Separate commands with `;` (not `&&`).
- Run backend commands with `workdir` set to `backend`.
- Verify strings with `Select-String -Path <file> -Pattern <regex>`.
- No new npm/Python dependencies in this phase.
