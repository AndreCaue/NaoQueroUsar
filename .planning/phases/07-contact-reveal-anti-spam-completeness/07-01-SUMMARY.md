---
phase: 07-contact-reveal-anti-spam-completeness
plan: 01
subsystem: api
tags: [turnstile, security, config, rate-limit]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Job model with contact fields, auth (JWT), Turnstile config, slowapi rate limit
provides:
  - Turnstile fail-closed Settings with validator
  - Rate limit knobs (REVEAL_RATE_LIMIT, LOGIN_RATE_LIMIT)
  - Config extensions for ENV=dev/prod distinction

# Tech tracking
tech-stack:
  added: []
  patterns: [pydantic model_validator fail-closed, module-level regex for test key validation, effective_turnstile_secret property]

key-files:
  created:
    - backend/app/core/config.py (Turnstile validator, DEV_TURNSTILE_SECRET, _TURNSTILE_TEST_KEY_RE, effective_turnstile_secret)
  modified:
    - backend/.env.example (Turnstile/rate-limit block)
    - backend/pyproject.toml (slowapi==0.1.10 added)

key-decisions:
  - Fail-closed Turnstile: secret obrigatoria fora de dev (D-11), chaves de teste bloqueadas fora de dev (D-12)
  - Dev default pass: chaves 1x/2x/3x sao always-pass em dev (D-12)
  - ALLOW_TEST_TURNSTILE escape hatch: desvio temporario, desligar quando chaves live existirem

patterns-established:
  - "Rule: Cloudflare test keys pattern must be 35 chars (1x + 31 chars + AA); {30} regex quebraria D-12"
  - "Property: effective_turnstile_secret returns dev fallback in dev, empty string em prod sem secret"

requirements-completed: [SECR-10, SECR-11, SECR-12]

# Metrics
duration: 15 min
completed: 2026-11-12
---

# Phase 7 Plan 01: Phase Prompt with Research & Verification Summary

**Substantive one-liner:** Fail-closed Turnstile Settings com validator pydantic, chaves de teste 35-char validadas, knobs de rate limit expostos — D-06 a D-12 implementados.

## Performance

- **Duration:** 15 min
- **Started:** 2026-11-12T14:30:00-03:00
- **Completed:** 2026-11-12T14:45:00-03:00
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `import re` e `from pydantic import model_validator` adicionados em `backend/app/core/config.py`
- 5 novos campos em `Settings`: `TURNSTILE_SECRET_KEY`, `TURNSTILE_SITE_KEY`, `TURNSTILE_TIMEOUT_SECONDS`, `REVEAL_RATE_LIMIT`, `LOGIN_RATE_LIMIT`
- `DEV_TURNSTILE_SECRET = "1x0000000000000000000000000000000AA"` constante de módulo
- `_TURNSTILE_TEST_KEY_RE = re.compile(r"^[123]x[0-9A-Za-z]{31}AA$")` regex de validação
- `effective_turnstile_secret` property: dev fallback para chave publica, prod validação rigorosa
- `backend/.env.example` atualizado com bloco Turnstile/rate-limit
- `slowapi==0.1.10` adicionado e pinado em `backend/pyproject.toml`
- Validador `@model_validator(mode="after") _validate_turnstile`: falha fechada fora de dev
- Propriedade `turnstile_mode`: `live` | `test` | `disabled`

## Files Created/Modified

- `backend/app/core/config.py` — validador Turnstile fail-closed, constantes, propriedades
- `backend/.env.example` — bloco Turnstile/rate-limit no final do arquivo
- `backend/pyproject.toml` — `slowapi==0.1.10` adicionado às dependências

## Decisions Made

- Fail-closed: sem TURNSTILE_SECRET_KEY em prod impede o startup (D-11)
- Chaves de teste (1x/2x/3x) bloqueadas fora de dev, a menos que ALLOW_TEST_TURNSTILE=true (D-12)
- Em dev, secret vazio faz fallback para a chave publica always-pass do Cloudflare (D-12)
- `ALLOW_TEST_TURNSTILE` e um desvio temporario — deve ser desligado quando chaves live estiverem configuradas

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

Phase 7 Plan 02 (Endpoint Implementation) is ready to proceed. Config foundation is complete and validated.

---

*Phase: 07-contact-reveal-anti-spam-completeness*
*Completed: 2026-11-12*