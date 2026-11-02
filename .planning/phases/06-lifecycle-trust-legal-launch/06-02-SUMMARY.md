---
phase: 06-lifecycle-trust-legal-launch
plan: 02
subsystem: trust/report
tags: [report, badge, trust, public-api, structured-log, ui-spec]

# Dependency graph
requires:
  - phase: 01-backend-foundation-data-admin-auth
    provides: FastAPI public router, get_published/list_published CRUD, Settings, rate-limit/client-ip helpers
  - phase: 03-contact-reveal-anti-spam
    provides: reveal-contact flow in JobDetailDialog footer (untouched by this plan), SafeLimiter patterns
  - phase: 04-public-board-frontend
    provides: JobCard / JobDetailDialog patterns, public.css tokens, board icons
  - phase: 06-lifecycle-trust-legal-launch
    plan: 01
    provides: Settings/config pattern (CRON_SECRET) used as reference; suite baseline 226 passed
provides:
  - POST /api/v1/public/jobs/{id}/report — anonymous accept-and-log endpoint (no table, no 404 oracle)
  - ReportRequest schema (reason optional, max 500 chars)
  - "Vaga revisada" badge on JobCard and JobDetailDialog (derived from status === 'published')
  - ReportJobDialog (native <dialog>, idle/submitting/success/error) integrated in the modal footer
  - reportJob() in frontend/lib/api.ts
affects: [06-03-legal-pages, 06-04-deploy-and-launch, phase-6-verification, master log review routine]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Accept-and-log: public report endpoint answers {\"status\": \"ok\"} for any well-formed payload — never 404, so it cannot be used as a job-existence oracle (TRST-02/D-06)"
    - "Log injection defence: report reason collapsed to a single line (whitespace/control chars) and truncated to 500 chars before logging; only job_id, reason and resolved IP are logged — no personal data (T-06-05)"
    - "Badge derived from status, never stored: no model/schema change for 'Vaga revisada' (D-05)"
    - "Second native <dialog> as sibling of the detail dialog (top-layer order: ESC closes the report first, detail stays open)"

key-files:
  created:
    - backend/tests/test_report_api.py
    - frontend/components/board/ReportJobDialog.tsx
  modified:
    - backend/app/api/v1/public.py
    - backend/app/schemas/job.py
    - frontend/lib/api.ts
    - frontend/components/board/JobCard.tsx
    - frontend/components/board/JobDetailDialog.tsx

key-decisions:
  - "Report endpoint does NOT query the database: existence/published checks would either leak job existence (404 vs 200) or add a pointless read — accept-and-log is the prerequisite for 'no enumeration oracle' and keeps the endpoint log-only (T-06-04)"
  - "Report fields travel in the log message itself (key=value): the project's plain-text formatter drops extra={} fields, and greppable single lines were preferred over introducing a JSON formatter in this plan"
  - "No rate limit on /report in this plan: the threat model (T-06-04) dispositions log-only with 'consider future rate limit' — flagged below for the launch checklist, not implemented (no new env knobs, no scope creep)"
  - "reportJob payload sends {} (not null) when no reason is given: FastAPI treats the body as optional, and {} round-trips cleanly through ReportRequest"
  - "Badge renders as an inline-flex pill with w-fit in the card so it never stretches or pushes the Ver a vaga CTA (UI-SPEC §A positioning rule)"
  - "Report dialog is a sibling of the detail <dialog>, not a child: top-layer ordering makes ESC close the report first without closing the detail, and avoids nested-dialog quirks"

patterns-established:
  - "Public anonymous write-ish endpoints: validate shape with Pydantic, answer 200 {\"status\": \"ok\"}, log — never leak existence"
  - "Optional anonymous form dialog: native <dialog> + idle/submitting/success/error + role=\"status\"/role=\"alert\" feedback, reset-on-close"

requirements-completed: [TRST-01, TRST-02]

# Metrics
duration: ~25min (estimated from session; not machine-timed)
completed: 2026-11-02
---

# Phase 6 Plan 02: Trust & Report Summary

**"Vaga revisada" badge (published-only, zero schema change) plus an anonymous accept-and-log report endpoint and native-dialog report UI wired into the job detail modal**

## Performance

- **Duration:** ~25 min (estimated)
- **Started:** 2026-11-02 (session start, before first read)
- **Completed:** 2026-11-02T20:30:29Z
- **Tasks:** 3
- **Files modified:** 7 (2 created, 5 modified)

## Accomplishments

- `POST /api/v1/public/jobs/{id}/report` answers `{"status": "ok"}` for any well-formed payload — anonymous, no DB read, no table, no migration; the report never reveals whether the job exists (TRST-02, D-06, T-06-06).
- Structured single-line log (`job_report job_id=… reason=… ip=…`) with the reason stripped of control characters and truncated to 500 chars — a report cannot forge log lines or smuggle personal data (T-06-05).
- `ReportRequest` schema caps `reason` at 500 chars; whitespace-only reasons collapse to absent; >500 chars is rejected with 422.
- Badge "Vaga revisada" rendered on `JobCard` (under the title) and `JobDetailDialog` (header block) iff `job.status === 'published'` — derived, never stored (TRST-01, D-05).
- `ReportJobDialog` (new): native `<dialog>`, optional textarea with live `n/500` counter, idle/submitting/success/error states, `role="status"`/`role="alert"` feedback, and "Tentar novamente" on error — copy verbatim from UI-SPEC.
- Job detail footer: secondary outline "Reportar vaga" button below the reveal CTA; the reveal flow is untouched. The report dialog opens as a sibling top-layer dialog — ESC closes it first, the detail stays open.
- Verification: backend suite **231 passed, 3 skipped** (5 new report tests); `tsc --noEmit` clean; `next lint` clean; `next build` succeeds.

## Task Commits

1. **Task 1: Endpoint público de report com log estruturado** — `6c7509d` (feat)
2. **Task 2: Badge "Vaga revisada" em JobCard e JobDetailDialog** — `60f58fb` (feat)
3. **Task 3: ReportJobDialog + integração no modal + reportJob no client** — `202d8b5` (feat)

## Files Created/Modified

- `backend/app/api/v1/public.py` — `report_job` route, `_log_safe()` helper (single-line, truncated), module logger
- `backend/app/schemas/job.py` — `ReportRequest` (reason optional, max 500, strip validator)
- `backend/tests/test_report_api.py` *(new)* — 5 tests: no-body accept, log shape (job_id, single-line, reason present), 500-char cap → 422, unknown id → 200, whitespace-only → reason=None
- `frontend/lib/api.ts` — `reportJob(jobId, reason?)`; trims, sends `{}` when empty; `ApiError` with backend `detail` on non-2xx
- `frontend/components/board/ReportJobDialog.tsx` *(new)* — the report dialog
- `frontend/components/board/JobCard.tsx` — badge under the title (`w-fit`)
- `frontend/components/board/JobDetailDialog.tsx` — badge in header, "Reportar vaga" footer button, `ReportJobDialog` sibling, fragment wrapper

## Decisions Made

- **No DB read in the report endpoint.** Any "check the job exists" branch reintroduces an existence oracle (404 vs 200) for zero operational gain — the master reviews reports against the board anyway. Accept-and-log is the pragmatic reading of the plan's own "melhor aceitar e logar".
- **Log fields in the message, not only `extra={}`.** `app/core/logging.py` uses a plain-text formatter without a JSON formatter; `extra` fields would be silently dropped. `key=value` in the message is greppable and survives the current formatter.
- **No rate limit on `/report`.** The phase threat model (T-06-04) dispositions log-only with "consider future rate limit" — the endpoint does no work and writes no row. Flagged for the launch checklist below instead of adding an unplanned limiter + env knob.
- **Sibling dialog, not nested.** A `<dialog>` inside `<dialog>` works but complicates the outer dialog's backdrop/ESC handling; the sibling keeps both close paths independent (top-layer order).
- **Badge styling.** UI-SPEC allows `text-accent-soft` or `text-fg-muted`; `text-fg-muted` + `border-line-strong` was chosen to keep the badge quieter than the CTA and the accent.

## Deviations from Plan

None — plan executed as written. Two small judgement calls within the plan's discretion: (1) the endpoint skips the DB entirely rather than "verificar se job existe" (the plan explicitly offered "aceitar e logar" and the context notes forbid enumerating jobs); (2) log fields are inlined in the message because the project's formatter would drop `extra={}`. Neither changes the contract.

## Issues Encountered

- PowerShell does not accept bash `VAR=$(...)` syntax — the worktree branch check was re-run in PowerShell syntax (base matched `02ea9a8`, no reset needed).
- `cd backend && …` is invalid in PowerShell — commands were run with `workdir` instead.
- Commit `202d8b5` message contains a stray fragment ("Rate limit-free,") from an editing slip; content is accurate, left as-is (no history rewrite).

## User Setup Required

None. No new env vars, no migration, no keys.

## Known Stubs

None — every path is wired: the form posts to the real endpoint, the endpoint logs, the badge derives from real `status`.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: unauthenticated-endpoint-surface | backend/app/api/v1/public.py | New anonymous `POST /api/v1/public/jobs/{id}/report` — log-only (no DB read, no row written), no personal data beyond resolved IP, registered as T-06-04/T-06-05 in the plan's threat model; recommend a `REPORT_RATE_LIMIT` knob in `06-04` if the log ever shows abuse |

## Launch Checklist Reminder (for 06-04)

- Review `job_report` lines in the backend logs as part of the master routine — there is no admin UI for reports by design (D-06).
- If abuse appears, add a slowapi `report_limit` mirroring `reveal_limit` (in-memory, per-IP) — do not reach for Redis at this scale.

## Verification

- `cd backend && .venv\Scripts\python.exe -m pytest -q` → **231 passed, 3 skipped** (pre-existing skips: live Turnstile opt-in); the only warning is the pre-existing `SAWarning` in `test_extract_api.py` (unrelated, untouched).
- `npx tsc --noEmit` → clean; `npm run lint` → no warnings or errors; `npm run build` → success (8/8 pages).
- Plan verify greps: `Vaga revisada` in `JobCard.tsx` (L51) and `JobDetailDialog.tsx` (L120); `reportJob` in `lib/api.ts` (L293); `Reportar vaga` in `JobDetailDialog.tsx` (L169).
- Badge appears iff `status === 'published'`; report flow never touches RevealContact; no model/schema changes for the badge.

## Self-Check: PASSED

- Created files exist: `backend/tests/test_report_api.py`, `frontend/components/board/ReportJobDialog.tsx` ✓
- Commits exist: `6c7509d`, `60f58fb`, `202d8b5` ✓
- No modifications to `.planning/STATE.md` or `.planning/ROADMAP.md` (STATE.md shows a pre-existing orchestrator modification, untouched and uncommitted) ✓
- No deletions introduced by any task commit ✓

---
*Phase: 06-lifecycle-trust-legal-launch*
*Completed: 2026-11-02*
