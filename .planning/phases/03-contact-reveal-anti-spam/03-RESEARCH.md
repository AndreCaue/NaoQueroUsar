# Phase 03: Contact Reveal & Anti-Spam — Research

**Researched:** 2026-10-20
**Domain:** Cloudflare Turnstile server-side verification (Siteverify), per-IP rate limiting, contact-reveal API surface
**Confidence:** HIGH (Turnstile/API facts verified against official docs today; rate-limit lib verified against PyPI/Context7; proxy-IP behavior per platform docs/support threads)

## Summary

Phase 3 turns the anti-scraping theory of the project research into a server-side contract: contacts leave the database **only** through a dedicated `POST /api/v1/public/jobs/{id}/reveal-contact`, gated by (1) a per-IP rate limit that runs *first*, (2) an existing published/non-expired job lookup, and (3) a live Cloudflare Siteverify call with a fresh, single-use token. The admin `/auth/login` gets the same two gates (Turnstile + rate limit) to kill credential stuffing. All Turnstile mechanics that the roadmap flagged as unknown are now resolved from official Cloudflare docs (updated Sep 16 2026): tokens live **300 s**, are **single-use**, replay/expiry both surface as `timeout-or-duplicate`, Siteverify takes exactly `secret`/`response`/`remoteip`/`idempotency_key`, and Cloudflare publishes **always-pass / always-fail / duplicate-spit test keys** that work on `localhost` — which makes the whole phase testable without a real widget.

The two non-obvious engineering traps are (a) **client IP behind the platform proxy**: uvicorn's proxy-header middleware only trusts `127.0.0.1` by default and slowapi's built-in `get_remote_address` just returns `request.client.host`, which collapses every visitor into one rate-limit bucket (or hands a spoofable key) unless we write our own key function; and (b) **fail-open config**: if `TURNSTILE_SECRET_KEY` is empty and we don't explicitly fail closed, the phase silently ships zero protection (the exact "Turnstile analytics show zero validations" failure the project PITFALLS doc warns about). Rate limiting uses **slowapi 0.1.10** (thin wrapper over `limits`, in-memory backend — fine for the single-worker free-tier deploy); Siteverify uses the already-installed **httpx 0.28.1**.

**Primary recommendation:** implement one `app/services/turnstile.py` (httpx Siteverify client with idempotency key + action/hostname checks) and one `app/core/client_ip.py` (header-priority IP resolver), wire both into a slowapi `Limiter(key_func=...)` on `reveal-contact` and `/auth/login`, and ship the login widget (`next-turnstile`) in the same phase so SECR-03 is end-to-end real, not just an API check that locks the master out.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Turnstile widget rendering (login today, reveal button in Phase 4) | Browser / Client | — | Widget issues the token; pure client concern. Phase 3 only adds it to the existing admin login Client Component. |
| Token submission with form data | Browser / Client | — | Client sends `cf_token` alongside password / reveal request; never validates locally. |
| Siteverify call (secret key, error-code policy) | API / Backend | — | Secret must never leave the server; this is the entire security boundary (SECR-01/03). |
| Per-IP rate limiting (reveal + login) | API / Backend | — | Enforcement point is the server that sees real client IPs (SECR-02). |
| Client-IP resolution behind Vercel→Railway/Render edge | API / Backend | CDN / Edge (platform) | Platform edge sets/overwrites `X-Real-IP`/`XFF`; backend must parse them correctly. |
| Contact payload exposure policy | API / Backend | — | Contact-free schemas already enforce PUBL-05; reveal endpoint is the only writer of contact data. |
| Auth session (JWT issuance/validation) | API / Backend | — | Already built in Phase 1; Phase 3 only hardens the login entry point. |
| Turnstile widget secrets config | Frontend (site key, `NEXT_PUBLIC_*`) | API (secret key) | Split keys: site key public, secret key server-only. |

## Phase Requirements

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SECR-01 | Cloudflare Turnstile validado no servidor antes de revelar o contato | Siteverify contract (endpoint, params, 300 s/single-use, error codes) — "Standard Stack" + "Code Examples"; dependency-injection seam for tests (Validation Architecture) |
| SECR-02 | Endpoint de revelação tem rate limiting por IP | slowapi setup (Context7-verified), custom `key_func` for proxy IPs — "Architecture Patterns" + Pitfall 2 |
| SECR-03 | Turnstile também protege o login do admin contra credential stuffing | Same service + limiter applied to `/auth/login`; login widget integration (`next-turnstile`) — "Code Examples" + Pitfall 8 |
| PUBL-05 | Contato servido por endpoint dedicado, ausente do payload público | Already enforced by Phase 1 `JobPublic` schema + 6 tests; reveal endpoint contract defined in "Architecture Patterns" (Contract) |
</phase_requirements>

## Project Constraints (from AGENTS.md)

Extracted directives the planner must not violate:

- **Stack (user-locked):** Next.js (App Router) + Tailwind + dark mode; FastAPI (Python); Neon Postgres; Groq LLM (`openai/gpt-oss-20b` default / `120b` fallback, never hardcoded); **Cloudflare Turnstile (free)** for anti-spam; Vercel (frontend) + Railway/Render (backend) deploy; pt-BR everything.
- **Design:** dark minimalista; roxo `#8b5cf6`/`#a78bfa`; fundos `#0f0a1a`/`#1a1025`; botão Doações `#facc15` discreto.
- **Operação:** admin único (master), sem multiusuário; **sem cadastro/login para visitantes** (contato serve sem fricção).
- **Stack versions (research/STACK.md, pinned):** FastAPI 0.143.0, uvicorn 0.54.0, httpx 0.28.1, Pydantic 2.14.1, pytest 9.1.1, `next-turnstile` 1.0.7 — reuse, don't re-choose.
- **Workflow:** GSD commands gate file changes (`/gsd-execute-phase` for phase work); no direct repo edits outside a GSD workflow.
- **Architecture (research/ARCHITECTURE.md is canonical):** endpoint shape `POST /public/jobs/{id}/reveal-contact` with `{cf_token}` → `{contact_email?, contact_phone?}`; layered `api/v1 → services → crud → schemas/models`.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `slowapi` | **0.1.10** (PyPI, released 2026-06-13) `[VERIFIED: pypi registry]` | Rate-limit decorator for FastAPI/Starlette (429 + headers) | Thin wrapper over `limits` (5.8.0) — the ecosystem-standard rate-limiting engine; supports sync+async endpoints, memory/Redis/memcached backends, dynamic limits per key `[VERIFIED: Context7 /laurents/slowapi]` |
| `limits` | 5.8.0 (transitive) `[VERIFIED: pypi registry]` | Fixed-window/moving-window algorithms, storage backends | Do not hand-roll window math, eviction, `Retry-After` |
| `httpx` | 0.28.1 (already in `pyproject.toml`/venv) `[VERIFIED: local probe]` | Call `https://challenges.cloudflare.com/turnstile/v0/siteverify` | Async, timeout control; STACK.md already assigns it to Turnstile verify |
| Cloudflare Turnstile (free plan) | — | Widget + Siteverify | User-locked; **Free plan = unlimited challenges/verifications, 20 widgets** `[CITED: developers.cloudflare.com/turnstile/plans/]` |
| `next-turnstile` | **1.0.7** (npm; last publish 2025-08-31) `[VERIFIED: npm registry]` | React `<Turnstile>` widget for the admin login form | STACK.md standard; peer deps `next>=12, react>=16` — compatible with installed Next 15.5.3 / React 19.1.1 `[VERIFIED: npm registry]` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Cloudflare test keys | constants | Local/CI Turnstile behavior control | Dev (`1x…AA` always-pass + `3x…AA` duplicate-spit) and pytest; never in prod config `[CITED: developers.cloudflare.com/turnstile/troubleshooting/testing/]` |
| pytest / pytest-asyncio | 9.1.1 / ≥1 (installed) | API + service tests (104 tests already collect in 2.7 s) `[VERIFIED: local probe]` | Every task in this phase |
| FastAPI dependency override | built-in | Swap Siteverify for a stub in API tests | Same pattern as `get_session` override in `tests/conftest.py` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `slowapi` (recommended) | `fastapi-limiter` 0.2.0 `[VERIFIED: pypi registry]` | Requires **Redis** — no Redis in this deploy (free tier, no infra). Rejected. |
| `slowapi` | `aiolimiter` 1.3.0 `[VERIFIED: pypi registry]` | Leaky-bucket primitive only: no HTTP keying, no 429 handler/headers — you'd hand-roll the HTTP layer. Rejected. |
| `slowapi` | Hand-rolled in-memory counter middleware | Zero deps, but you own window/eviction/`Retry-After`/test-reset logic — exactly what `limits` already does. Rejected (see Don't Hand-Roll). |
| App-level Siteverify (httpx) | `next-turnstile`'s server `validateTurnstileToken()` | That helper runs in Node — our backend is Python. Keep Siteverify in FastAPI only (single enforcement point). |
| Header parsing in 3 places | One `app/core/client_ip.py` | Same resolver feeds rate-limit key, Siteverify `remoteip`, and abuse logs. Required for consistency. |

**Installation:**

```bash
# backend (uv is NOT available in this environment — see Environment Availability)
python -m pip --python backend\.venv\Scripts\python.exe install slowapi==0.1.10
# also add "slowapi==0.1.10" to backend/pyproject.toml [project].dependencies
# frontend
cd frontend && npm install next-turnstile@1.0.7
```

**Version verification:** every version in the Core table was confirmed against the registry on 2026-10-20 (`pypi.org/pypi/<pkg>/json`, `registry.npmjs.org`, `pip --python … --dry-run`) — not from training data.

## Architecture Patterns

### Request Flow

```
Browser (frontend on Vercel)                      FastAPI (Railway/Render)
─────────────────────────────                     ─────────────────────────
[existing] GET /public/jobs ───────────────────►  JobPublic schema → NO contact fields
[existing] GET /public/jobs/{id} ──────────────►  JobPublic → NO contact fields
                                                 (PUBL-05 already enforced + tested)

[Phase 4] click "Mostrar contato"
          Turnstile widget → cf-turnstile-response token
[Phase 4] POST /public/jobs/{id}/reveal-contact ─► ① rate limiter (key = resolved client IP)
              { cf_token }                            │ exceeded → 429 (Retry-After)
                                                     ▼
                                                  ② get_published(id) → miss → 404
                                                     ▼
                                                  ③ httpx → challenges.cloudflare.com
                                                     /turnstile/v0/siteverify
                                                     {secret, response, remoteip,
                                                      idempotency_key}
                                                     │ success=false (incl.
                                                     │ timeout-or-duplicate) → 403
                                                     ▼
                                                  ④ action/hostname checks (optional cfg)
                                                     ▼
                                                  200 { contact_email?, contact_phone? }

[Phase 3] admin login (ExtractForm, "use client")
          Turnstile widget (action="login") → token
          POST /api/v1/auth/login ───────────────► ① same rate limiter → 429
              { password, cf_token }                ② Siteverify → 403 on failure
                                                    ③ bcrypt verify → 200 JWT / 401
```

### API Contract (defines Phase 3 ↔ Phase 4 boundary)

```
POST /api/v1/public/jobs/{job_id}/reveal-contact      # canonical path: research/ARCHITECTURE.md L282
Request:  { "cf_token": "<turnstile token, ≤2048 chars>" }
200  { "contact_email": "...", "contact_phone": "..." }   # at least one present (DB CHECK)
404  job unknown / not published / expired                 # same get_published filter as detail
403  Turnstile failed (incl. timeout-or-duplicate)         # pt-BR detail, error-codes logged
429  rate limit exceeded (slowapi handler + Retry-After)
422  body invalid (missing/non-string cf_token)

POST /api/v1/auth/login                                     # changed in this phase
Request:  { "password": "...", "cf_token": "<token>" }      # cf_token NEW (SECR-03)
200 TokenResponse | 403 Turnstile failed | 429 | 401 senha inválida
```

Status-code choice note: **404 before Siteverify** (job lookup costs nothing, Siteverify costs an external call — don't pay Cloudflare for IDs that don't exist), **rate limit before both** (protects Siteverify from flooding).

### Recommended Project Structure (new/changed files only)

```
backend/app/
├── core/
│   ├── client_ip.py        # NEW: X-Real-IP → rightmost non-private XFF → request.client.host
│   └── ratelimit.py        # NEW: Limiter instance (key_func = client_ip, env-driven limits)
├── services/
│   └── turnstile.py        # NEW: async Siteverify client (httpx), result dataclass, action/hostname checks
├── api/v1/
│   ├── public.py           # CHANGED: + POST /jobs/{id}/reveal-contact
│   └── auth.py             # CHANGED: require Turnstile token (SECR-03)
├── schemas/
│   ├── job.py              # NEW: RevealRequest / ContactRevealResponse (contact fields live ONLY here)
│   └── auth.py             # CHANGED: LoginRequest gains cf_token
├── deps.py                 # CHANGED: get_turnstile_verifier (overridable dependency)
└── core/config.py          # CHANGED: TURNSTILE_* + RATE_LIMIT_* settings
frontend/
├── lib/api.ts              # CHANGED: loginAdmin(password, cfToken)
└── app/admin/paste/ExtractForm.tsx  # CHANGED: render <Turnstile>, pass token, reset on expiry
```

### Pattern 1: Server-side Turnstile verification (the security boundary)

**What:** backend is the *only* caller of Siteverify; client token is untrusted input until Cloudflare says otherwise.
**When to use:** every endpoint that releases sensitive data (reveal) or accepts credentials (login).
**Source:** official docs `[CITED: https://developers.cloudflare.com/turnstile/get-started/server-side-validation/]`

```python
# app/services/turnstile.py — pattern source: Cloudflare "Validate the token" (Python sample), async-ified
import uuid
import httpx

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

async def verify_turnstile(token: str, secret: str, remoteip: str | None,
                           *, expected_action: str | None = None,
                           idempotency_key: str | None = None) -> dict:
    data = {"secret": secret, "response": token}
    if remoteip:
        data["remoteip"] = remoteip
    if idempotency_key:                      # makes retries safe: a repeat call with the
        data["idempotency_key"] = idempotency_key   # same key does NOT burn the token twice
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(SITEVERIFY_URL, data=data)
            r.raise_for_status()
            result = r.json()
    except httpx.HTTPError:
        return {"success": False, "error-codes": ["internal-error"]}   # fail CLOSED
    if result.get("success") and expected_action and result.get("action") != expected_action:
        return {"success": False, "error-codes": ["action-mismatch"]}  # reject swapped tokens
    return result
```

Facts this pattern encodes (all `[CITED: developers.cloudflare.com/turnstile/get-started/server-side-validation/`, page updated **2026-09-16**]:

- Token **valid 300 s**, **single use**; replay *and* expiry both return **`timeout-or-duplicate`** (also returned for expired tokens per docs: "the `error-codes` field will include `timeout-or-duplicate`").
- Siteverify params are exactly `secret`, `response`, `remoteip` (optional), `idempotency_key` (optional UUID). **There is no `sitekey` parameter** — `research/ARCHITECTURE.md` L468 suggests passing one; official params table does not include it (extra fields are simply ignored — harmless but do not rely on it).
- Accepts `application/x-www-form-urlencoded` **and** JSON; always returns JSON. Max token length **2048 chars**.
- Recommended checks beyond `success`: `action` (≤32 chars, `[A-Za-z0-9_-]`) and `hostname` — set `data-action="reveal"` / `"login"` client-side and assert it server-side to prevent token cross-use between the two flows.
- Errors: `missing-input-secret`, `invalid-input-secret`, `missing-input-response`, `invalid-input-response`, `bad-request`, `timeout-or-duplicate`, `internal-error`.
- Best practices from the same page: rate-limit against validation flooding; set a finite timeout; never expose the secret; only the backend calls Siteverify.

### Pattern 2: Proxy-aware IP keying (rate limit + remoteip must agree)

**What:** one resolver used by slowapi `key_func`, Siteverify `remoteip`, and logs.
**When to use:** always — behind Railway/Render the raw socket peer is a platform proxy.

```
priority:  X-Real-IP (Railway edge OVERWRITES it per request; client cannot forge)
        →  X-Forwarded-For rightmost entry that is not private/loopback
           (handles Railway single-value overwrite AND Render, which appends its proxy IP)
        →  request.client.host (uvicorn ProxyHeadersMiddleware, if trusted)
        →  "unknown" (shared bucket — safe fallback)
```

Evidence:
- uvicorn: `--proxy-headers` is **enabled by default** but trusts only `forwarded-allow-ips` = `127.0.0.1` / `::1` (or `$FORWARDED_ALLOW_IPS`); it returns the **first untrusted hop from the right** `[CITED: https://uvicorn.dev/settings/]` + `[CITED: github.com/encode/uvicorn ProxyHeadersMiddleware]`.
- Railway (official support reply, **2026-10-10**): "Our HTTP edge **overwrites** X-Forwarded-For, X-Real-IP, X-Forwarded-Proto and X-Forwarded-Host on every request, including your *.up.railway.app domain. Any copy the client sends is replaced, not appended… **For rate limiting, we recommend keying on X-Real-IP**" `[CITED: station.railway.com/questions/express-rate-limiting-security-trusted-ad01e74d]` (MEDIUM-HIGH: official staff, but support-forum not spec doc; a 2026-03 incident thread shows header behavior has regressed before).
- Render: its reverse proxy does **not** strip client-supplied `X-Forwarded-For`; it appends, so leftmost is spoofable; community guidance is to skip the appended proxy entry `[CITED: community.render.com/t/accessing-client-ips-in-a-node-express-app/36282]` (MEDIUM — community, staff-marked "Solved" with a Cloudflare-specific workaround).
- MDN parsing rules (rightmost trustworthy hop, never leftmost for security use) `[CITED: developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-For]`.

**Do not** use slowapi's defaults: `get_remote_address` returns raw `request.client.host`; `get_ipaddr` returns the whole raw `X-Forwarded-For` header string (spoofable + not a single IP) `[CITED: github.com/laurentS/slowapi/blob/master/slowapi/util.py]`.

### Pattern 3: slowapi wiring (Context7-verified)

**What:** limiter as app state + exception handler + per-route decorator.
**Source:** `[CITED: Context7 /laurents/slowapi → github.com/laurents/slowapi docs/index.md]`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_client_ip, headers_enabled=True, storage_uri="memory://")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # → 429 JSON

@app.post("/api/v1/public/jobs/{job_id}/reveal-contact")   # route decorator MUST be ABOVE
@limiter.limit(settings.REVEAL_RATE_LIMIT)                 # the limit decorator
async def reveal_contact(job_id: uuid.UUID, request: Request, payload: RevealRequest, ...):
    ...  # endpoint MUST declare a `request: Request` param or slowapi raises at decoration time
```

Verified details `[VERIFIED: Context7 /laurents/slowapi]` + `[CITED: github.com/laurentS/slowapi/blob/master/slowapi/extension.py]`:
- `headers_enabled` defaults to **False** → pass `True` to emit `RateLimit-*` / `Retry-After` headers on 429.
- The endpoint signature **must** include `request: Request` (else `Exception` at import).
- Route decorator order: `@app.post(...)` above `@limiter.limit(...)`.
- Default storage is in-memory; `storage_uri` accepts `redis://` (not available here). `in_memory_fallback`, `retry_after`, dynamic `limit_value` callables exist if needed.
- 429 body: `{"error": "Rate limit exceeded: …"}` — wrap with a custom handler for a pt-BR message (OpenCode's discretion).

### Anti-Patterns to Avoid

- **Client-side-only reveal** ("hidden div"): trivially scraped — the whole reason this phase exists (PITFALLS 7).
- **Fail-open Turnstile**: empty secret + `if secret: verify` ships a bypass. Fail closed when `ENV != dev`; log loudly (`Turnstile analytics zero validations` = detection signal).
- **Caching "token OK"**: tokens are single-use by design; re-validating a consumed token must 403, never serve cached success.
- **Trusting `request.client.host` or leftmost XFF** behind Railway/Render: spoofable or collapses all users into one bucket.
- **Rate-limiting only successful verifies**: bots would flood Siteverify for free — count *attempts*.
- **Changing `/auth/login` shape without the frontend**: `loginAdmin(password)` in `frontend/lib/api.ts` would 422 the moment `cf_token` becomes required — update both in the same plan.
- **Global mutable test leakage**: slowapi's in-memory store persists across tests — reset the limiter in a fixture or every rate-limit test will poison the next.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limiting (windows, counters, eviction, 429/`Retry-After`) | `dict[ip, deque[timestamps]]` middleware | `slowapi` + `limits` | Window semantics, storage eviction, header injection, per-route/dynamic limits, and test reset are already solved; hand-rolled counters leak memory under scan traffic |
| Turnstile Siteverify client | `requests.post` scattered in routers + ad-hoc JSON parsing | `app/services/turnstile.py` over `httpx` (one function, error-code taxonomy, idempotency key, timeout, fail-closed) | Error codes (`timeout-or-duplicate` vs `invalid-input-response`) demand different UX; idempotency key semantics are subtle |
| Client IP resolution behind proxies | Reaching for `X-Forwarded-For.split(",")[0]` | `app/core/client_ip.py` priority chain (Pattern 2) | Leftmost is the classic spoof; rightmost needs private-range skipping; Railway/Render differ |
| Turnstile widget rendering | Raw `<script src="challenges.cloudflare.com/turnstile/v0/api.js">` + `turnstile.render` in React | `next-turnstile@1.0.7` (STACK.md standard) | Script lifecycle, token expiry/expired-callback, explicit render, response field handling, TS types |

**Key insight:** this phase's value is *correctness of the enforcement*, not the amount of code — a 40-line bespoke limiter that is subtly wrong (shared bucket, spoofable key, no eviction) defeats SECR-02 entirely.

## Common Pitfalls

### Pitfall 1: Token expired before submit (5-minute window) → user-visible failure loop
**What goes wrong:** visitor opens the modal, waits >5 min, clicks reveal; Siteverify returns `timeout-or-duplicate` → 403 even though the human is legitimate.
**Why it happens:** tokens expire at 300 s; widget default `refresh-expired: auto` only helps when the widget is mounted and noticed the expiry.
**How to avoid:** Phase 4 must mount the widget at reveal time (or refresh via `turnstile.reset()`), handle `expired-callback`, and treat 403 as "please retry" (pt-BR), not a bug.
**Warning signs:** 403 rate spiking for single users; `timeout-or-duplicate` dominating logs.

### Pitfall 2: Rate limiter keyed on the proxy IP
**What goes wrong:** everyone shares one bucket (one visitor triggers 429 for the whole site) **or** a bot forges `X-Forwarded-For` to get unlimited buckets.
**Why it happens:** slowapi `get_remote_address` = `request.client.host`; uvicorn only trusts proxy headers from `127.0.0.1` by default; Render appends to XFF without stripping.
**How to avoid:** custom `key_func` per Pattern 2; verify in a deployed smoke test that two different clients get different keys.
**Warning signs:** production 429s for unrelated users; `key=…` logs showing a private IP for every request.

### Pitfall 3: Fail-open configuration
**What goes wrong:** `TURNSTILE_SECRET_KEY` unset/typo'd → code path skips verification → reveal/login unprotected with no visible error.
**Why it happens:** `if secret:` guards written for dev convenience.
**How to avoid:** pydantic-settings validation: in `ENV != "dev"`, empty secret = startup failure (fail fast, consistent with D-05) or request rejection (fail closed); dev may use Cloudflare's public always-pass test secret.
**Warning signs:** Turnstile dashboard shows zero token validations (PITFALLS.md detection item).

### Pitfall 4: Single-use misunderstanding (double verification)
**What goes wrong:** retry logic re-posts the same token after a network timeout → Cloudflare already consumed it → `timeout-or-duplicate`.
**Why it happens:** Siteverify is not idempotent per token unless you pass `idempotency_key`.
**How to avoid:** generate one `uuid4()` per user submission, pass it as `idempotency_key`, retry only with the *same* key (docs' advanced pattern).
**Warning signs:** `internal-error`/`timeout-or-duplicate` bursts during network flakiness.

### Pitfall 5: Rate limiting doesn't cover Siteverify flooding / failed attempts
**What goes wrong:** attacker hammers the reveal endpoint with garbage tokens; your limiter is per-route-success or the login route has none → you eat Cloudflare round-trips and DB lookups.
**How to avoid:** apply the limiter decorator to **both** `reveal-contact` and `/auth/login`, counting all attempts before any other work; consider a cost >1 for reveal (slowapi `cost=` param).
**Warning signs:** outbound request volume to `challenges.cloudflare.com` disproportionate to traffic.

### Pitfall 6: `next-turnstile` imported from a Server Component
**What goes wrong:** `Build error: `useState` is not a function` / "attempted to call a Server Component".
**Why it happens:** `next-turnstile@1.0.7`'s published `dist/client/Turnstile.js` has **no `"use client"` directive** (inspected via unpkg) `[VERIFIED: unpkg dist inspection]` — the directive must come from the consuming file.
**How to avoid:** import `<Turnstile>` only inside `"use client"` files (`ExtractForm.tsx` already is; the Phase 4 reveal button must be too).

### Pitfall 7: Test/prod key confusion
**What goes wrong:** production secret rejects the dummy token (`XXXX.DUMMY.TOKEN.XXXX`) so UI tests fail in prod, **or** test secret `1x…AA` ships to prod and everything auto-passes (zero protection).
**Why it happens:** test secrets accept *only* dummy tokens and production secrets accept *only* real tokens `[CITED: developers.cloudflare.com/turnstile/troubleshooting/testing/]`.
**How to avoid:** env-driven keys (`.env` dev/test vs Vercel/Railway prod), never hardcoded; CI uses `1x0000000000000000000000000000000AA` only.

## Code Examples

### 1. Reveal endpoint (FastAPI + slowapi + Turnstile service)

```python
# Pattern sources: research/ARCHITECTURE.md L282 (contract) + Cloudflare server-side validation docs
class RevealRequest(BaseModel):
    cf_token: str = Field(min_length=1, max_length=2048)   # 2048 = Siteverify token cap (docs)

@router.post("/jobs/{job_id}/reveal-contact", response_model=ContactRevealResponse)
@limiter.limit("{settings.REVEAL_RATE_LIMIT}")   # or string from settings closure
async def reveal_contact(
    job_id: uuid.UUID,
    payload: RevealRequest,
    request: Request,                              # REQUIRED by slowapi
    session: AsyncSession = Depends(get_session),
    verify: Verifier = Depends(get_turnstile_verifier),   # overridable in tests
) -> ContactRevealResponse:
    job = await get_published(session, job_id)     # published + not expired (D-17)
    if job is None:
        raise HTTPException(404, "Vaga não encontrada")
    result = await verify(payload.cf_token, get_client_ip(request), expected_action="reveal")
    if not result.success:
        log_turnstile_failure(job_id, result.error_codes, get_client_ip(request))
        raise HTTPException(403, "Verificação anti-bot falhou — tente novamente")
    return ContactRevealResponse(contact_email=job.contact_email,
                                 contact_phone=job.contact_phone)
```

### 2. Login hardening (SECR-03)

```python
@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(payload: LoginRequest, request: Request,
                verify: Verifier = Depends(get_turnstile_verifier)) -> TokenResponse:
    result = await verify(payload.cf_token, get_client_ip(request), expected_action="login")
    if not result.success:
        raise HTTPException(403, "Verificação anti-bot falhou — tente novamente")
    if not authenticate_password(payload.password):
        raise HTTPException(401, "Senha inválida")
    token, expires_in = create_access_token()
    return TokenResponse(access_token=token, expires_in=expires_in)
```

### 3. Frontend login widget (client)

```tsx
// frontend/app/admin/paste/ExtractForm.tsx — file already starts with "use client"
import { Turnstile } from "next-turnstile";
const [cfToken, setCfToken] = useState<string | null>(null);

<Turnstile
  siteKey={process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? ""}
  action="login"                                   // must match server expected_action
  theme="dark"                                      // admin paste UI is dark
  onVerify={(t) => setCfToken(t)}
  onExpire={() => setCfToken(null)}                 // stale token must be cleared
/>
// handleLogin → loginAdmin(password, cfToken)  (lib/api.ts: body { password, cf_token })
// disable the button while !cfToken; reset the widget after a failed login
```

Source: `next-turnstile` README props table `[VERIFIED: npm registry readme]` (`siteKey`, `onVerify`, `onExpire`, `action`, `theme`, `appearance`, `execution`, …).

### 4. Test seam (mirrors existing conftest style)

```python
# tests/conftest.py — same pattern as app.dependency_overrides[get_session]
os.environ["TURNSTILE_SECRET_KEY"] = "1x0000000000000000000000000000000AA"  # before app import
os.environ["REVEAL_RATE_LIMIT"] = "3/minute"        # keeps the 429 test fast

@pytest.fixture
def fake_turnstile(app):                            # success/failure/duplicate switches
    def _install(outcome="ok"):
        app.dependency_overrides[get_turnstile_verifier] = lambda: stub(outcome)
    return _install
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Cloudflare docs path `turnstile/concepts/siteverify/` (404 today) | `turnstile/get-started/server-side-validation/` | docs restructure (page updated 2026-09-16) | Cite the new URL; old links in notes are dead |
| Assumption "verify with `sitekey` param" (research/ARCHITECTURE.md L468) | Siteverify accepts only `secret`/`response`/`remoteip`/`idempotency_key` | current official params table | Don't add a `sitekey` field; harmless-but-wrong code |
| Railway XFF "append + take leftmost" (older staff answers) | Railway **overwrites** `X-Forwarded-For`/`X-Real-IP` and recommends keying on `X-Real-IP` | official reply 2026-10-10 (after a 2026-03 regression/fix incident) | Prefer `X-Real-IP`; keep XFF fallback for Render |
| Turnstile free tier "1M solves/month" folklore (training data) | Free = **unlimited** challenges & verifications, 20 widgets, 10 hostnames/widget | plans page updated 2026-08-14 | No quota worry at 100–500 jobs/month scale |
| Rate limiting via Redis/Celery-style infra | `slowapi`+`limits` in-memory, single worker | current free-tier topology | Zero new infra; revisit on multi-worker scaling |

**Deprecated/outdated:**
- `llama-3.1-8b-instant`/`llama-3.3-70b` (project already corrected) — irrelevant here but reinforces "verify current docs" habit.
- `research/STACK.md` still describes Groq models as `llama-*` in one table — stale; do not propagate (Phase 2 research corrected it).

## Runtime State Inventory

Not applicable — Phase 3 is additive (new endpoint, new config keys, one schema field). No rename/migration/runtime re-registration. Existing state explicitly reviewed:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None (no schema change; contacts already stored, now *served*) | none |
| Live service config | `.env` has no `TURNSTILE_*` keys yet `[VERIFIED: local probe]` | add keys to `backend/.env`, `.env.example`, Vercel `NEXT_PUBLIC_TURNSTILE_SITE_KEY`, Railway/Render secrets (Phase 6 deploy wiring) |
| OS-registered state | None | none |
| Secrets/env vars | `TURNSTILE_SECRET_KEY` (new, backend-only), `NEXT_PUBLIC_TURNSTILE_SITE_KEY` (new, public), `REVEAL_RATE_LIMIT`/`LOGIN_RATE_LIMIT` (new, optional) | create; never commit |
| Build artifacts | `frontend/.next` cache, `backend` `__pycache__` | none (rebuild naturally) |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python venv `backend\.venv` | running tests/app | ✓ | 3.11.17 | — |
| pip (via `python -m pip --python …`) | installing `slowapi` | ✓ **verified dry-run resolves slowapi 0.1.10 + limits 5.8.0** `[VERIFIED: local probe]` | pip 25.0.1 (global) | — |
| `uv` (README/plan docs say `uv sync` / `uv run`) | refreshing `uv.lock` | ✗ **MISSING** | — | edit `pyproject.toml` manually + `pip --python` install; optionally `python -m pip install uv` then `uv lock` (not verified) |
| pytest | validation | ✓ | 9.1.1, **104 tests collect in 2.7 s** `[VERIFIED: local probe]` | — |
| httpx | Siteverify | ✓ | 0.28.1 | — |
| Node/npm | installing `next-turnstile` | ✓ | node 22.18.0 / npm 10.9.3 | — |
| Test DB (`TEST_DATABASE_URL` → Neon) | API tests | ✓ (key present in `backend/.env`) `[VERIFIED: local probe]` | — | suite self-skips cleanly if absent |
| Cloudflare account + Turnstile widget (site key/secret) | real-widget dev & prod | ✗ **not created yet** (human task) | — | **Cloudflare test keys** work immediately on localhost for dev/CI `[CITED: testing docs]` |
| Redis (for distributed limiter) | not required | ✗ | — | in-memory limiter (single worker) |

**Missing dependencies with no fallback:** Cloudflare account — blocks *real* key testing only; all code, tests, and local dev proceed with published test keys (`1x…AA` always-pass, `3x…AA` returns `timeout-or-duplicate`, `2x…AA` always-fail).
**Missing dependencies with fallback:** `uv` → `pip --python` (verified) — note `uv.lock` drift as a deferred hygiene item.

## Validation Architecture

> `workflow.nyquist_validation` is **true** in `.planning/config.json` → section included.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-asyncio (`asyncio_mode = "auto"`) |
| Config file | `backend/pyproject.toml` → `[tool.pytest.ini_options]` (testpaths=`tests`) |
| Quick run command | `backend\.venv\Scripts\python.exe -m pytest -q` (Windows) / `.venv/bin/python -m pytest -q` (posix) |
| Full suite command | same (single suite; 104 tests today, ~seconds) |
| Note | `uv run pytest` is what docs say, but `uv` is missing — use the venv interpreter |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| SECR-01 | reveal without/with invalid token → 403; valid token → 200 with contact; Siteverify stubbed | integration (ASGI) | `… -m pytest tests/test_reveal_api.py -x` | ❌ Wave 0 |
| SECR-01 | Siteverify client: success, `timeout-or-duplicate`, action mismatch, network error → fail-closed | unit | `… -m pytest tests/test_turnstile_service.py -x` | ❌ Wave 0 |
| SECR-02 | N+1 reveals from one IP → 429 with `Retry-After`/`RateLimit-*`; other IP still 200 | integration | `… -m pytest tests/test_reveal_api.py -k rate -x` | ❌ Wave 0 |
| SECR-03 | login missing/invalid `cf_token` → 403; valid → 200 JWT; bad password still 401; login 429 after N | integration | `… -m pytest tests/test_auth.py -x` (extend existing) | ⚠️ exists, needs new cases |
| PUBL-05 | list/detail payloads contain no `contact_email`/`contact_phone`; contact reachable **only** via reveal | integration | `… -m pytest tests/test_public_api.py tests/test_reveal_api.py -x` | ✅ first half exists (6 tests), reveal half ❌ |

### Sampling Rate

- **Per task commit:** `backend\.venv\Scripts\python.exe -m pytest -q`
- **Per wave merge:** full suite (same command) — must stay green including the 104 existing tests
- **Phase gate:** full suite green before `/gsd-verify-work`; plus the 4 success criteria walked manually with test keys (PITFALLS checklist: Siteverify actually called, `timeout-or-duplicate` handled)

### Wave 0 Gaps

- [ ] `backend/tests/test_reveal_api.py` — SECR-01/SECR-02/PUBL-05 reveal cases
- [ ] `backend/tests/test_turnstile_service.py` — Siteverify client unit tests (mocked httpx)
- [ ] `backend/tests/conftest.py` additions — Turnstile env vars set **before app import** (settings are cached at import, same as Phase 1 trick), rate-limit reset fixture (in-memory limiter is process-global), `fake_turnstile` dependency-override fixture
- [ ] `backend/.env` + `.env.example` — `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`, `REVEAL_RATE_LIMIT`, `LOGIN_RATE_LIMIT`
- [ ] Install: `python -m pip --python backend\.venv\Scripts\python.exe install slowapi==0.1.10` + `pyproject.toml` edit
- [ ] Frontend: `npm install next-turnstile@1.0.7` in `frontend/`

## Security Domain

> `security_enforcement` not set in config → treated as **enabled**.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | **yes** | Turnstile token + per-IP rate limit in front of bcrypt verify (SECR-03); existing bcrypt+JWT (Phase 1) unchanged |
| V3 Session Management | no (Phase 1, unchanged) | Bearer JWT, 12 h expiry |
| V4 Access Control | **yes** | Contact release gated: published/non-expired lookup + successful Siteverify; contact fields exist only in `ContactRevealResponse`, never `JobPublic` |
| V5 Input Validation | **yes** | Pydantic v2: `cf_token` required, ≤2048 chars (Siteverify cap), `job_id` UUID path validation; `action`/`hostname` equality checks on the Siteverify response |
| V6 Cryptography | no local crypto | TLS in transit (platform HTTPS); no hand-rolled crypto; secret key stored in env only |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Contact scraping (list/detail/reveal harvesting) | Information Disclosure | Contact-free schemas (done) + Siteverify + per-IP 429 + opaque UUIDs (D-06) + short payloads; abuse logging |
| Credential stuffing / password spraying on `/auth/login` | Spoofing | Turnstile (action=`login`) + rate limit **before** password check; 401 body never echoes the password |
| Turnstile token replay / cross-flow reuse | Spoofing | Cloudflare single-use (`timeout-or-duplicate`) + `action` binding (`reveal` vs `login`) |
| Rate-limit bypass by IP spoofing (`X-Forwarded-For`) | Elevation of Privilege | Platform-overwritten `X-Real-IP` first; rightmost non-private XFF; never leftmost |
| Siteverify flooding (cost/availability of your own gate) | Denial of Service | Limiter counts all attempts on both routes; finite 10 s Siteverify timeout; fail-closed on errors |
| Secret key leakage | Information Disclosure | Secret only in backend env (never `NEXT_PUBLIC_*`, never in repo); site key is public by design |
| Fail-open bypass via misconfig | Tampering | Startup validation in non-dev env (Pitfall 3); monitor Turnstile analytics for zero validations |
| Contact enumeration | Information Disclosure | 404 for non-published/expired jobs (no existence oracle); UUIDs unguessable |

## Open Questions

1. **Enforcement when `TURNSTILE_SECRET_KEY` is empty** (dev machines, CI without keys)
   - What we know: test keys work on localhost without a Cloudflare account `[CITED: testing docs]`; fail-open silently nullifies the phase (PITFALLS detection item).
   - What's unclear: whether the project wants a hard startup failure in `ENV != dev` or an explicit `TURNSTILE_ENFORCE=false` escape hatch.
   - Recommendation: **fail closed in prod (pydantic-settings requires the key when `ENV != "dev"`)**, dev defaults to Cloudflare's public always-pass secret. *Confirm with user (Assumption A2).*

2. **Rate-limit numbers**
   - What we know: nothing in REQUIREMENTS.md fixes values; slowapi takes any `N/minute` string (dynamic per-env supported).
   - What's unclear: desired strictness (humans reveal 1–3 times/session; login is rare).
   - Recommendation: reveal `10/minute`, login `5/minute` per IP, both env-tunable (`REVEAL_RATE_LIMIT`, `LOGIN_RATE_LIMIT`). *Confirm (Assumption A1).*

3. **Who creates the Cloudflare Turnstile widget** (account, hostname allowlist, keys)
   - What we know: needs a human with a Cloudflare dashboard session; free plan, ~2 min.
   - What's unclear: scheduling — must happen before real-widget manual verification (test keys cover everything else).
   - Recommendation: human task in Phase 3's UAT checklist (or defer real keys to Phase 6 deploy if Phase 3 accepts test keys for its gate).

4. **Deploy target (Railway vs Render) affects IP-priority docs but not code**
   - Recommendation: implement the platform-agnostic priority chain (Pattern 2); revisit at Phase 6 deploy wiring. Both platforms covered.

5. **Should `cf_token` be required on login unconditionally, or only after N failed attempts (progressive)?**
   - Recommendation: **unconditional** — SECR-03 wording is absolute, and the widget is cheap; progressive gating adds state and complexity for a single-master login. *Confirm (Assumption A4).*

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Rate limits `10/minute` (reveal) and `5/minute` (login) per IP are reasonable defaults | Standard Stack / Open Questions | Too strict → legit users 429 (UX); too loose → weaker SECR-02. Env-tunable, so cheap to change |
| A2 | Missing Turnstile secret in prod should fail closed; dev may use Cloudflare test keys | Pitfall 3 / Open Questions | Fail-open = phase silently ineffective; hard failure could surprise dev setup if user prefers test-key default |
| A3 | Deployment runs a **single worker/process** (free tier), so in-memory `limits` storage is sufficient | Standard Stack | Multi-worker multiplies allowed requests N× and resets on deploy; would need Redis/DB-backed storage (not available today) |
| A4 | Phase 3 includes the small frontend change (login widget + `loginAdmin(password, cfToken)`), since SECR-03 can't be true otherwise | Architecture Patterns | If planner scopes Phase 3 backend-only, login breaks (422) until Phase 4/5 — must be sequenced explicitly |
| A5 | ASVS category applicability as mapped (V2/V4/V5 in scope; V3/V6 out) | Security Domain | Low — controls listed are the ones this phase actually implements |
| A6 | Platform edge terminates TLS so the browser→backend hop is HTTPS without extra work | Security Domain | Low for local/dev; verify at deploy (Phase 6) |

## Sources

### Primary (HIGH confidence)
- [https://developers.cloudflare.com/turnstile/get-started/server-side-validation/](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/) — Siteverify endpoint/params, 300 s expiry, single-use, error-code table, idempotency_key, best practices (page updated **2026-09-16**; fetched 2026-10-20)
- [https://developers.cloudflare.com/turnstile/troubleshooting/testing/](https://developers.cloudflare.com/turnstile/troubleshooting/testing/) — test site/secret keys, dummy token behavior, `timeout-or-duplicate` test case (fetched 2026-10-20)
- [https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/widget-configurations/](https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/widget-configurations/) — widget params (`action`, `cdata`, theme, refresh/expired behavior, response field)
- [https://developers.cloudflare.com/turnstile/plans/](https://developers.cloudflare.com/turnstile/plans/) — free plan = unlimited verifications (updated 2026-08-14)
- Context7 `/laurents/slowapi` — FastAPI wiring, decorator semantics, `limit()` signature; `slowapi/extension.py` defaults (`headers_enabled=False`, `storage_uri`)
- Local probes: `pip --python --dry-run slowapi` (resolves 0.1.10), venv contents, `pytest --collect-only` (104 tests), `.env` key list, `next-turnstile` dist via unpkg (no `"use client"`)

### Secondary (MEDIUM confidence)
- [https://uvicorn.dev/settings/](https://uvicorn.dev/settings/) + uvicorn `ProxyHeadersMiddleware` source — proxy-header defaults (`127.0.0.1`/`::1`, first-untrusted-from-right)
- [station.railway.com official support replies (2026-10-10, 2026-03)](https://station.railway.com/questions/express-rate-limiting-security-trusted-ad01e74d) — Railway edge overwrites `X-Forwarded-For`/`X-Real-IP`; recommends `X-Real-IP` for rate limiting (staff answer, support-forum not spec)
- [community.render.com thread](https://community.render.com/t/accessing-client-ips-in-a-node-express-app/36282) — Render proxy appends to XFF (client-supplied entries survive)
- [MDN X-Forwarded-For](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-For) — parsing/selection rules for security use
- PyPI registry JSON (slowapi 0.1.10 / limits 5.8.0 / fastapi-limiter 0.2.0 / aiolimiter 1.3.0) and npm registry (next-turnstile 1.0.7, @marsidev/react-turnstile 1.6.2) — versions/dates

### Tertiary (LOW — flagged for validation)
- Render XFF behavior is a single community thread (staff "Solved" reply pointed elsewhere) — validate empirically when the deploy target is picked (Phase 6).
- Railway header behavior changed at least once in 2026 (regression/fix) — re-check at deploy; code's priority chain tolerates either "overwrite" or "append".

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — Turnstile facts from official docs fetched today; slowapi from Context7 + PyPI + source inspection; install path verified by dry-run
- Architecture: **HIGH** for endpoint contract/ordering/patterns (canonical ARCHITECTURE.md + official docs); **MEDIUM** for proxy-IP specifics (platform support threads, not spec docs)
- Pitfalls: **HIGH** — each pitfall tied to a verified mechanism (300 s token window, slowapi `request.client.host`, missing `"use client"`, fail-open config)

**Research date:** 2026-10-20
**Valid until:** ~2026-11-20 (Cloudflare docs and Railway header behavior are the moving parts; re-check both if execution slips past 30 days)
