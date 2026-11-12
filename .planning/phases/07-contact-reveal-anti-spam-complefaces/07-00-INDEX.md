---
title: Phase 7 Plan Index
---

# Phase 7: Contact Reveal & Anti-Spam Completeness

## Plans Created

| Plan ID | Title | Size | Status |
|---------|-------|------|--------|
| `07-01-PLAN.md` | Phase Prompt with Research & Verification | 16,414 bytes | ✅ Complete |
| `07-02-PLAN.md` | Endpoint Implementation + Tests | 12,196 bytes | ✅ Complete |
| `07-03-PLAN.md` | Application Wiring + Rate Limit Handler | 5,071 bytes | ✅ Complete |

## Files Summary

```
.planning/phases/07-contact-reveal-anti-spam-completeness/
├─ 07-01-PLAN.md    - Phase prompt (config, tasks, threat model, gates)
├─ 07-02-PLAN.md    - Endpoint implementation (Turnstile verify, dev/prod modes)
├─ 07-03-PLAN.md    - App wiring (limiter, router, 429 handler)
└─ 07-00-INDEX.md   - This index
```

## State Updates

### `.planning/STATE.md`
- `total_phases: 6 → 7`
- Added Phase 7 progress row: `| 07 | 0 | 0 | — | Phase 7: Contact Reveal & Anti-Spam Completeness`

### `.planning/config.json`
- No changes needed (workflow uses SDK queries for init context)

## Plan Details

### 07-01-PLAN.md (Phase Prompt)
**Objective:** Build the contact reveal server-side gated surface for Phase 7
- **Tasks:** 3 TDD-mode tasks
- **Config:** Turnstile fail-closed Settings (D-06/D-07/D-11/D-12)
- **Rate limits:** REVEAL_RATE_LIMIT=10/min, LOGIN_RATE_LIMIT=5/min
- **Threat model:** STRIDE analysis T-07-01 through T-07-03
- **Success criteria:** D-06 through D-12 implemented, endpoint functional, tests green

### 07-02-PLAN.md (Endpoint Implementation)
**Objective:** Implement `POST /api/v1/public/jobs/{job_id}/reveal-contact`
- **Dev mode:** Default always-pass with `1x`/`2x`/`3x` test keys (D-12)
- **Prod mode:** Fail-closed - 500 if secret missing, 403 if verification fails
- **Rate limit:** 10/min per IP via slowapi, 429 with pt-BR message + Retry-After
- **Tests:** 7 test cases covering dev/prod modes, rate limit, error codes
- **Consumes:** 07-01 config (Settings with TURNSTILE_* fields, slowapi pinning)

### 07-03-PLAN.md (Application Wiring)
**Objective:** Wire the public router into FastAPI main app
- **Limiter:** Slowapi global limiter (10/min by IP or URL key)
- **Router:** `app.include_router(api_router, prefix="/api/v1")` 
- **Handler:** RateLimitExceeded → 429 with `{error, retry_after}` + `Retry-After` header
- **Verification:** `create_app()` boots without errors, endpoint available

## Execution Workflow

The three plan files are structured for the GSD `execute-phase` workflow:

**Wave grouping:** All 3 plans have `wave: 1` and `depends_on: []`, meaning they can be executed in parallel in wave 1.

**Execution command (when GSD SDK is available):**
```
/gsd-execute-phase 7
```
or
```
/gsd-plan-phase 7 --execute
```

**What the workflow does:**
1. Discovers `*-PLAN.md` files in `.planning/phases/07-contact-reveal-anti-spam-completeness/`
2. Groups them into waves (all in wave 1)
3. Spawns `gsd-executor` subagents for each plan
4. Each subagent loads the full execute-plan context and executes the tasks
5. Handles checkpoints, verification loops (max 3 iterations), and state updates
6. Commits progress and generates SUMMARY.md files

**Per-plan execution would involve:**
- 07-01: Setting up config, running security config tests
- 07-02: Implementing the endpoint, running reveal contact tests
- 07-03: Wiring main.py, verifying app boots, testing rate limit

## Next Steps

The plans are complete and ready for execution. To proceed with execution:

1. **Via GSD command:** Run `/gsd-execute-phase 7` from the project root
2. **Manual execution:** Follow the execute-phase.md workflow steps manually
3. **Review & iterate:** Review the plans, then run individual task execution

The plans follow the exact same format as phases 1-6 and are fully integrated with the project's existing decisions (D-06 through D-12, slowapi, resolve_client_ip, Turnstile test keys).

---
*Phase 7 plan index generated as part of Phase 7 setup. All plans follow the project's GSD conventions and are ready for execution.*