---
phase: 03-contact-reveal-anti-spam
slug: contact-reveal-anti-spam
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-21
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `03-RESEARCH.md` → "Validation Architecture" (HIGH confidence).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-asyncio (`asyncio_mode = "auto"`) |
| **Config file** | `backend/pyproject.toml` → `[tool.pytest.ini_options]` (`testpaths=["tests"]`) |
| **Quick run command** | `backend\.venv\Scripts\python.exe -m pytest -q` (Windows, from repo root) |
| **Full suite command** | `backend\.venv\Scripts\python.exe -m pytest -q` (single suite; 104 tests today) |
| **Frontend build** | `cd frontend; npm run build` |
| **Estimated runtime** | ~5 seconds backend suite; ~30 s frontend build |

> `uv` is **not installed** in this environment (deferred tooling debt) — always call the
> venv interpreter directly, never `uv run`.

---

## Sampling Rate

- **After every task commit:** `backend\.venv\Scripts\python.exe -m pytest -q`
- **After every plan wave:** `backend\.venv\Scripts\python.exe -m pytest -q` (must stay green with the 104 pre-existing tests)
- **Before `/gsd-verify-work`:** full suite green + `cd frontend; npm run build` exits 0
- **Max feedback latency:** ~10 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | SECR-02 (partial) | T-03-01 | Non-dev startup fails without a real Turnstile secret; test keys rejected outside dev | unit | `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_security_config.py -q` | ❌ Wave 0 | ⬜ pending |
| 03-01-02 | 01 | 1 | SECR-02 (partial) | T-03-02 | Rate-limit key = X-Real-IP → rightmost public XFF → client host → `unknown`; never leftmost XFF | unit | `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_client_ip.py -q` | ❌ Wave 0 | ⬜ pending |
| 03-02-01 | 02 | 2 | SECR-01 (partial) | T-03-03, T-03-04, T-03-05 | Siteverify success/failure taxonomy, action binding, fail-closed on network/5xx/invalid JSON; token/secret never logged | unit | `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_turnstile_service.py -q` | ❌ Wave 0 | ⬜ pending |
| 03-02-02 | 02 | 2 | SECR-02 (partial) | T-03-07, T-03-08 | Limiter wired to the app; 429 body carries pt-BR `detail` + `Retry-After`; limiter store reset between tests | unit | `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_ratelimit.py -q` | ❌ Wave 0 | ⬜ pending |
| 03-02-03 | 02 | 2 | SECR-01 (partial) | T-03-06 | `/health` reports Turnstile status without leaking the secret; test fixtures isolate the limiter store | unit | `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_health.py -q` | ❌ Wave 0 | ⬜ pending |
| 03-03-01 | 03 | 3 | SECR-01, SECR-02, PUBL-05 | T-03-09, T-03-10, T-03-11, T-03-12, T-03-13, T-03-14 | Reveal returns contact only after a successful Siteverify; 404 before Siteverify; 403 on failure; 429 on excess | integration (ASGI) | `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_reveal_api.py -q` | ❌ Wave 0 | ⬜ pending |
| 03-04-01 | 04 | 4 | SECR-03 | T-03-15, T-03-16, T-03-19, T-03-20 | Login runs rate limit → Siteverify → bcrypt; missing/invalid token = 403; bad password = 401 | integration (ASGI) | `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_auth.py -q` | ⚠️ exists, needs new cases | ⬜ pending |
| 03-04-02 | 04 | 4 | SECR-03 | T-03-17, T-03-18 | Widget token is required before submit, cleared on expire/error, reset after a failed login | build | `cd frontend; npm run build` | ⚠️ exists, needs new code | ⬜ pending |
| 03-05-01 | 05 | 5 | SECR-01 | T-03-24 | Real Siteverify call succeeds with the always-pass test secret, fails with `2x…`, fails closed with `3x…` | manual smoke (script) | `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_turnstile_live.py -q` | ❌ Wave 0 | ⬜ pending |
| 03-05-02 | 05 | 5 | ALL | T-03-21, T-03-22 | Full backend suite + frontend build stay green after the phase; no secret in versioned files | regression | `backend\.venv\Scripts\python.exe -m pytest -q` | ✅ | ⬜ pending |
| 03-05-03 | 05 | 5 | SECR-01, SECR-03 | T-03-03, T-03-15 | Browser login with a real Turnstile widget (localhost + dummy site key) succeeds end to end | manual | human checkpoint (steps in 03-05-PLAN.md) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Threat Register Index

Each plan owns its own `<threat_model>`; the IDs below are the canonical cross-reference for this phase.

| Plan | Threat IDs | Theme |
|------|-----------|-------|
| 03-01 | T-03-01, T-03-02 | Startup fail-fast na chave do Turnstile · chave do rate limit (IP resolvido) |
| 03-02 | T-03-03, T-03-04, T-03-05, T-03-06, T-03-07, T-03-08 | Spoofing (binding por `action`) · DoS (fail closed) · log sem segredo · `/health` sem segredo · handler 429 pt-BR · store do limiter isolado entre testes |
| 03-03 | T-03-09, T-03-10, T-03-11, T-03-12, T-03-13, T-03-14 | Contato só no schema de reveal · `action="reveal"` · 404 antes do 403 · IDs falsos não gastam cota · `idempotency_key` por submissão · 403/429 auditáveis |
| 03-04 | T-03-15, T-03-16, T-03-17, T-03-18, T-03-19, T-03-20 | Senha nunca comparada sem token · token de `reveal` não abre o login · nenhum segredo no browser · token consumido não é reenviado · rate limit no login · tentativa registrada |
| 03-05 | T-03-21, T-03-22, T-03-23, T-03-24 | `.env` gitignored · segredo ausente do front · smoke live opt-in · `3x…` falha fechado |

---

## Wave 0 Requirements

Wave 0 is folded into the plans that need each artifact (no separate scaffolding plan):

- [ ] `backend/tests/test_security_config.py` — plan 03-01, task 1
- [ ] `backend/tests/test_client_ip.py` — plan 03-01, task 2
- [ ] `backend/tests/test_turnstile_service.py` — plan 03-02, task 1
- [ ] `backend/tests/test_ratelimit.py` — plan 03-02, task 2
- [ ] `backend/tests/test_health.py` — plan 03-02, task 3
- [ ] `backend/tests/test_reveal_api.py` — plan 03-03, task 2
- [ ] `backend/tests/test_turnstile_live.py` — plan 03-05, task 1 (opt-in via `TURNSTILE_LIVE=1`)
- [ ] `backend/tests/conftest.py` — Turnstile env vars **before** app import, `app`/`client`/`fake_turnstile` fixtures, limiter reset — plan 03-02, task 3
- [ ] `backend/tests/test_auth.py` — extend with the Turnstile cases — plan 03-04, task 1
- [ ] `backend/.env` + `backend/.env.example` — `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`, `TURNSTILE_TIMEOUT_SECONDS`, `REVEAL_RATE_LIMIT`, `LOGIN_RATE_LIMIT` — plan 03-01, task 1
- [ ] `frontend/.env.local.example` — `NEXT_PUBLIC_TURNSTILE_SITE_KEY` — plan 03-04, task 2
- [ ] Install `slowapi==0.1.10` into `backend\.venv` + pin in `backend/pyproject.toml` — plan 03-01, task 1
- [ ] Install `next-turnstile@1.0.7` in `frontend/` — plan 03-04, task 2

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real Siteverify round-trip against Cloudflare | SECR-01 | Needs outbound network + a Cloudflare test secret; the app-level stub cannot prove the real endpoint is called | plan 03-05, task 1 (`test_turnstile_live.py`, opt-in via `TURNSTILE_LIVE=1`; o segredo `3x…` prova a falha fechada) |
| Admin login with a live Turnstile widget in the browser | SECR-01, SECR-03 | The widget renders Cloudflare's iframe; only a browser proves the token reaches the backend | plan 03-05, task 3 (checkpoint steps) |
| "Cloudflare dashboard shows validations > 0" | SECR-01 | Requires a **real** Cloudflare account + widget (deferred to Phase 6 by the user's decision) | Not verifiable in Phase 3 — record as a Phase 6 item, do not block the phase |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
