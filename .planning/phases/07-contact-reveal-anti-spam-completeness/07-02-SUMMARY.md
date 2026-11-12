---
phase: 07-contact-reveal-anti-spam-completeness
plan: 02
subsystem: api
tags: [turnstile, endpoint, security, rate-limit]

# Dependency graph
requires:
  - phase: 07-contact-reveal-anti-spam-completeness/07-01
    provides: Turnstile fail-closed Settings, REVEAL_RATE_LIMIT, LOGIN_RATE_LIMIT, slowapi pinning
provides:
  - POST /api/v1/public/jobs/{id}/reveal-contact endpoint gated by Turnstile
  - Dev mode: default always-pass with test keys (1x/2x/3x)
  - Prod mode: fail-closed validation, 403 on verification failure
  - Rate limit 10/min por IP via slowapi

# Tech tracking
tech-stack:
  added: []
  patterns: [endpoint gated por Turnstile, slowapi decorator com reveal_limit, dependency_overrides para fake verifier]

key-files:
  created:
    - backend/tests/test_reveal_contact.py (suíte completa de testes)
  modified:
    - backend/app/api/v1/public.py (endpoint reveal-contact com validação Turnstile)
    - backend/app/core/ratelimit.py (reveal_limit, rate_limit_exceeded_handler, SafeLimiter)

key-decisions:
  - Order of checks: rate limit → job lookup → Turnstile verify → return contact (D-03)
  - Failed verification é SEMPRE 403, nunca degraded a 200 (D-13)
  - Token com action='login' recusa no endpoint de reveal (T-03-03)
  - hostname do Siteverify NÃO checado (binding por action já impede reuso)

requirements-completed: [SECR-10, SECR-11, SECR-12]

# Tech tracking
tech-stack:
  added: []
  patterns: [endpoint gated por Turnstile, slowapi decorator com reveal_limit, dependency_overrides para fake verifier]

# Metrics
duration: 20 min
completed: 2026-11-12
---

# Phase 7 Plan 02: Endpoint Implementation + Tests Summary

**Substantive one-liner:** Endpoint POST /api/v1/public/jobs/{id}/reveal-contact com validação Turnstile server-side, rate limit 10/min por IP e testes cobrindo dev/prod modes, 403/429/404 error handling.

## Performance

- **Duration:** 20 min
- **Started:** 2026-11-12T14:45:00-03:00
- **Completed:** 2026-11-12T15:05:00-03:00
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- `POST /api/v1/public/jobs/{job_id}/reveal-contact` endpoint implemented
- Endpoint order: rate limit (slowapi decorator) → job lookup (get_published, 404 if not found/expirated) → Turnstile verification → return contact fields
- Dev mode: token vazio ou 1x/2x/3x → always-pass, contact fields retornados
- Prod mode: secret ausente → 500 "TURNSTILE_SECRET_KEY não configurada (D-11)"; token inválido → 403 "Turnstile verification failed (D-11)"
- Rate limit 10/min por IP via slowapi `reveal_limit()` lida pelo `SafeLimiter`
- 429 response com body `{"detail": "Muitas tentativas. Aguarde alguns segundos e tente novamente."}` e header `Retry-After`
- `backend/tests/test_reveal_contact.py` com 10 testes cobrindo: 404 (job não existe), 403 (token rejeitado/unavailable/action mismatch), 422 (token ausente), 429 (rate limit excedido), 200 (contact retornado), payload público sem contato
- Testes usam `fake_turnstile` através de `dependency_overrides` — 100% offline, não toca Cloudflare
- Rate limit bucket keyed por IP via `resolve_client_ip` (D-10), não por URL (D-05/D-08)

## Files Created/Modified

- `backend/app/api/v1/public.py` — endpoint `reveal_contact` com validação Turnstile, rate limit, job lookup
- `backend/tests/test_reveal_api.py` — suíte de 10 testes unitários offline para o endpoint reveal-contact
- `backend/app/core/ratelimit.py` — `SafeLimiter` class, `reveal_limit()`, `login_limit()`, `rate_limit_exceeded_handler` com 429 pt-BR

## Decisions Made

- Check order deliberado: rate limit primeiro (para economizar cota Cloudflare), depois job lookup (para evitar chamada em id inexistente), depois Siteverify
- Verification fail-closed: sem secret em prod = 500; token inválido = 403; nunca retorna contato sem verify bem-sucedido
- Token action binding: token mintado para flow 'login' é recusado no endpoint de reveal (T-03-03)
- hostname do Siteverify deliberately não checado: action binding já impede reuso de token entre flows

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

Phase 7 Plan 03 (Application Wiring) is ready to proceed. Endpoint is functional with tests green.

---

*Phase: 07-contact-reveal-anti-spam-completeness*
*Completed: 2026-11-12*