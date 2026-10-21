---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Phase 03 planned (5 plans, 5 waves) — ready to execute
last_updated: "2026-10-21T22:10:00.000Z"
last_activity: 2026-10-21 -- Phase 03 planning complete (5 plans written, gates green)
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 13
  completed_plans: 8
  percent: 33
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-13)

**Core value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.
**Current focus:** Phase 03 — contact-reveal-anti-spam

## Current Position

Phase: 03 (contact-reveal-anti-spam) — PLANNED
Plan: 0 of 5 (03-01 → 03-05, waves 1→5)
Status: Planning complete — ready for `/gsd-execute-phase 3`
Last activity: 2026-10-21 -- Phase 03 planning complete (5 plans written, gates green)

Progress: [░░░░░░░░░░] 0% (Phase 03 planejada; fases 01-02 concluídas)

## Performance Metrics

**Velocity:**

- Total plans completed: 4
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 4 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: Stable

*Updated after each plan completion*
| Phase 01 P01 | 15 | 2 tasks | 27 files |
| Phase 01 P02 | 35 min | 2 tasks | 6 files |
| Phase 01 P03 | 4 min | 2 tasks | 7 files |
| Phase 01 P04 | ~6min | 2 tasks | 11 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- (Roadmap) 6 fases coarse; extração (Phase 2), reveal/anti-spam (Phase 3) e lifecycle/infra (Phase 6) isoladas como HIGH RISK.
- (Research) Groq `llama-3.1-8b-instant`/`llama-3.3-70b` aposentados em 2026-08-16 — usar `openai/gpt-oss-20b`/`120b` via `GROQ_MODEL` + fallback (nunca hardcoded).
- (Research) Contatos nunca no payload público; servidos só por endpoint dedicado com Turnstile server-side (anti-scraping).
- [Phase 01]: D-06..D-13 realized: Job model + initial migration (UUID PK gen_random_uuid, 4-value job_status enum, at_least_one_contact CHECK, timestamptz with expires_at=now()+14d, pg_trgm+unaccent search_text GIN trigram, city/salary free text, no soft delete)
- [Phase 01]: D-01..D-04 realized: login returns a Bearer JWT (no cookie), single long-lived 12h token (JWT_EXPIRES_IN, no refresh), master password verified against ADMIN_PASSWORD_HASH, and login Turnstile/rate-limit deliberately deferred to Phase 3 — plan 01-03 (ADMN-01/ADMN-02/ADMN-03)
- [Phase 01]: Password hashing uses the bcrypt library directly; passlib 1.7.4 is incompatible with the locked bcrypt 5.0.0 (its backend probe raises ValueError) — 01-03 deviation (Rule 3); tracked in deferred-items.md for a future re-lock
- [Phase 01]: D-14..D-18 realized (plan 01-04): public read surface is GET /api/v1/public/jobs (offset pagination page/limit 1-50 default 20 + total count) and GET /api/v1/public/jobs/{id} (404 otherwise), always filtering status='published' AND expires_at > now(), with a contact-free JobPublic schema (no contact_email/contact_phone); search/filter/sort and contact reveal deferred to Phases 4 and 3 respectively
- [Phase 01]: D-22 realized (plan 01-04): focused pytest + pytest-asyncio suite (18 tests) + scripts/seed.py proving all five Phase 1 criteria (login ok/bad, admin 401, public contact-free list/detail, published-only non-expired, schema CHECK/enum/14-day expiry)
- [Phase 03 planning]: 5 planos em 5 ondas — 03-01 (config fail-closed + IP + pin slowapi) → 03-02 (Siteverify + limiter + DI + fixtures) → 03-03 (endpoint de reveal) → 03-04 (login protegido, back+front no mesmo plano) → 03-05 (smoke live + checkpoint de browser)
- [Phase 03 planning]: os segredos de teste do Cloudflare têm **35 chars** (`1x`/`2x`/`3x` + 31 + `AA`) — o regex de bloqueio em prod é `^[123]x[0-9A-Za-z]{31}AA$`; com `{30}` a chave always-pass passaria no validator (D-12 quebrado)
- [Phase 03 planning]: `slowapi==0.1.10` verificado no wheel — `key_func` é re-resolvido por request, bucket por URL, o param `request` é obrigatório no decorator e `init_app` registraria o handler 429 default em inglês (usamos `app.state.limiter` + handler pt-BR próprio)
- [Phase 03 planning]: `next-turnstile@1.0.7` exporta `{ Turnstile }` (nomeado) e **não** tem `resetKey` — o reset do widget é por remount via `key` do React
- [Phase 03 planning]: o conftest **não** pode definir `TURNSTILE_SECRET_KEY`/`TURNSTILE_SITE_KEY`/`REVEAL_RATE_LIMIT`/`LOGIN_RATE_LIMIT` no ambiente global — em teste `ENV="dev"` (default) e env vars têm precedência sobre os defaults, o que quebraria os testes de fail-closed do plano 03-01

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 2/3/6 flagged for possible `/gsd-research-phase` (modelo Groq vivo, strict outputs, TPM; Siteverify; scheduler externo/Neon CU-hour/Render-Railway free-tier).
- LGPD exige revisão por advogado brasileiro antes do lançamento (tarefa humana, não de código).

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Dependency hygiene | Replace `passlib[bcrypt]` with a direct `bcrypt` dependency and re-lock with `uv` (passlib 1.7.4 is incompatible with the locked bcrypt 5.0.0) | Deferred | Phase 01 (plan 01-03) |

## Session Continuity

Last session: 2026-10-21T22:10:00.000Z
Stopped at: Phase 03 planned (5 plans, 5 waves) — ready to execute
Resume file: .planning/phases/03-contact-reveal-anti-spam/03-01-PLAN.md
