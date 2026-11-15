# Phase 11: Verify Phases 7–8 & Close Reveal/Admin/Review Evidence Gaps - Research

**Researched:** 2026-11-15
**Domain:** GSD verification backfill, requirement traceability repair, audit-evidence documentation (Phase 7/8, no product behavior change)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### 07 Verification Evidence (SECR-10/11/12)
- **D-01:** `07-VERIFICATION.md` must establish evidence by **running targeted backend tests now and recording pass/fail results/snippets**, and by **citing code paths and Phase 7 artifacts** (plans/summaries/implementation). Relevant existing tests include `backend/tests/test_reveal_api.py`, `backend/tests/test_turnstile_service.py`, `backend/tests/test_ratelimit.py`, and `backend/tests/test_turnstile_live.py` (use the most relevant subset and document why).
- **D-02:** Treat **SECR-10** as **verified with an explicit operational caveat**: document implementation/config/wiring/test evidence, and clearly record the operational constraint that the Turnstile site key is inlined in the frontend bundle so Cloudflare key changes require a frontend rebuild. The caveat must be documented in the verification artifact (not hidden), matching the audit/roadmap intent.
- **D-03:** Handle **SECR-12** in `07-VERIFICATION.md` as **Phase 7 side verified + Phase 9 deferred**: verify SECR-12 evidence attributable to Phase 7 claims/controls, and explicitly state that `/admin/expire` auth-contract reconciliation and Phase 9-side evidence are owned by **Phase 12** to avoid overlap/conflict.

#### 08 Verification Evidence (ADMN-10/11/12, REVW-10/11/12)
- **D-04:** `08-VERIFICATION.md` must establish evidence by **running targeted backend/admin/extract tests now and recording results**, and by **citing API/frontend code/UI paths and Phase 8 artifacts**. Relevant existing tests include `backend/tests/test_admin_jobs.py` and `backend/tests/test_extract_api.py` (and any other directly relevant tests discovered during planning/execution).
- **D-05:** For UI-facing criteria (e.g. **ADMN-10** Turnstile indicator on login, toast/feedback, "vaga aparece imediatamente na home pública" UX), provide **code evidence + human/browser verification notes** when not exercised live. Do not claim full interactive/browser proof from source inspection alone; include a human verification section/items as needed.
- **D-06:** For **REVW-12**, verify the **implemented hard-delete contract** (repeat delete returns 404 / idempotent-in-effect behavior) with tests/code evidence, and include a short explicit note mapping this behavior to the requirement wording "exclusão duplicada é no-op" so the evidence is auditable.

#### Phase 8 Traceability Repair
- **D-07:** Repair Phase 8 traceability **in place** by editing existing artifacts where needed: `08-03-SUMMARY.md` and `CONTEXT-SUMMARY.md` (and any other Phase 8 artifact necessary for consistency) so `ADMN-12`/`REVW-12` claims are machine-checkable and cross-references are coherent.
- **D-08:** For `CONTEXT-SUMMARY.md` (planning/context recap, not an execution summary), add **YAML frontmatter with requirement references** (e.g. `phase`, `type: context-summary`, and appropriate `requirements-referenced` and/or `requirements-completed` fields) plus explicit cross-reference lines to relevant plans/summaries/`08-VERIFICATION.md` for `ADMN-12`/`REVW-12`. Do not overstate execution completion; use semantics appropriate to the artifact type while making IDs discoverable by scans.

#### Requirements Status & SECR-12 Boundary
- **D-09:** After `07-VERIFICATION.md`/`08-VERIFICATION.md` and Phase 8 traceability repairs are in place, update `.planning/REQUIREMENTS.md` to **mark `SECR-10`, `SECR-11`, `ADMN-10`, `ADMN-11`, `ADMN-12`, `REVW-10`, `REVW-11`, and `REVW-12` as verified/complete** and add traceability notes recording **Phase 11 gap-closure ownership** with pointers to the relevant verification artifacts.
- **D-10:** For **SECR-12** (shared across Phase 7 and Phase 9/Phase 12), **leave the checkbox unchecked** in Phase 11 and add a split-ownership traceability note: Phase 7 side verified in Phase 11 (`07-VERIFICATION.md`, including documented handling/caveats as applicable) and Phase 9 `/admin/expire` contract reconciliation/evidence owned by **Phase 12**. Do not claim full SECR-12 closure in Phase 11.

### OpenCode's Discretion
- Exact selection/order of targeted test commands and which result snippets to embed in `07-VERIFICATION.md`/`08-VERIFICATION.md` (as long as they are relevant and auditable).
- Exact verification document structure/sections and status wording, provided they follow established patterns (see `09-VERIFICATION.md`, `10-VERIFICATION.md`) and clearly record evidence, gaps/caveats, and human verification where applicable.
- Precise frontmatter key names/values for `CONTEXT-SUMMARY.md` beyond the requirement-ref intent in D-08, as long as `ADMN-12`/`REVW-12` are machine-discoverable and semantics are accurate.
- Exact phrasing/location of Phase 11 gap-closure ownership notes in `.planning/REQUIREMENTS.md` (checkboxes, per-requirement lines, and/or traceability sections) as long as ownership and evidence pointers are unambiguous.

### Deferred Ideas (OUT OF SCOPE)
- Phase 12: reconcile Phase 9 `/admin/expire` X-Cron-Secret-only contract, stale 09 verification/ROADMAP wording, and Phase 9-side SECR-12/LIFE lifecycle-trust evidence.
- Phase 13: canonical branded host/env/CORS/API alignment and deploy/ops evidence closure for BRND-04 and related production-alignment concerns.
- Any live production/browser verification beyond documented human notes for Phase 7/8 UI behavior (if required later, capture as execution-time evidence or future follow-up).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SECR-10 | Turnstile site key inline no bundle — mudança de chave no painel Cloudflare requer rebuild do frontend — flag de threat operacional | Code/config evidence: `frontend/app/admin/paste/ExtractForm.tsx` reads `process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY` with dev fallback; `frontend/.env.example` documents it; Next.js inlines `NEXT_PUBLIC_*` at build time. Verify with explicit operational rebuild caveat in `07-VERIFICATION.md` (D-02). |
| SECR-11 | Rate limiting por IP no endpoint de reveal e login — slowapi knobs `REVEAL_RATE_LIMIT=10/min` e `LOGIN_RATE_LIMIT=5/min` — configurados via env | Evidence in `backend/app/core/config.py`, `backend/app/core/ratelimit.py`, `backend/app/api/v1/public.py` (`@limiter.limit(reveal_limit)`), `backend/app/api/v1/auth.py` (login limit via service/wiring per Phase 3/7 artifacts), tests `backend/tests/test_ratelimit.py`, `backend/tests/test_reveal_api.py` 429 case. Run targeted rate-limit + service/reveal tests now (D-01). |
| SECR-12 | Endpoint `/admin/expire` autenticado por header `X-Cron-Secret` — fail-closed: 503 quando header ausente/incorreto | **Split ownership (D-03, D-10):** Phase 7 side can cite anti-spam/turnstile-hardening boundary context only as needed, but primary concrete implementation evidence is `backend/app/api/v1/admin.py` (`/expire` uses `Depends(require_cron_secret)`), `backend/app/deps.py` (`require_cron_secret` 503/401 fail-closed, per-IP rate-limited), and Phase 9 artifacts/tests (`test_admin_expire.py` in repo history/audit context). Phase 11 must document Phase 7-attributable evidence/caveats in `07-VERIFICATION.md` and leave global requirement unchecked with Phase 12 owning `/admin/expire` contract reconciliation. |
| ADMN-10 | Admin vê indicador de Turnstile no login (widget interaction-only) — validação visual no clique | Code/UI evidence: `frontend/app/admin/paste/ExtractForm.tsx` renders `<Turnstile ... action="login" theme="dark" appearance="always" />`, disables login without `cfToken`, shows missing-site-key message when key absent. Requires **code evidence + human/browser verification notes** (D-05), not source-only proof of live interaction. |
| ADMN-11 | Login admin persiste sessão com token Bearer JWT em header Authorization — teste em rotas protegidas | Evidence: login flow in `frontend/app/admin/paste/ExtractForm.tsx` stores token in `sessionStorage` (`TOKEN_KEY`); `frontend/lib/api.ts` sends `Authorization: Bearer ${token}` for admin calls (`extractJobs`, `listAdminJobs`, `approveJob`, `updateJob`, `deleteJob`); `frontend/components/admin/AdminGuard.tsx` guards routes; backend `backend/app/deps.py` `require_admin` validates JWT and all admin routes in `backend/app/api/v1/admin.py` depend on it. Backed by `backend/tests/test_admin_jobs.py::test_requires_auth` and login/extract tests. |
| ADMN-12 | Rota `/auth/login` protege contra credential stuffing com rate limit Turnstile server-side — SECR-03 estendida | Evidence: `backend/app/api/v1/auth.py` login flow (Phase 3/7/8 implementation), Turnstile verifier DI (`backend/app/deps.py::get_turnstile_verifier`), rate-limit knobs in config/ratelimit, tests referencing login+Turnstile in `backend/tests/test_extract_api.py` (`_get_admin_token` posts `/api/v1/auth/login` with `cf_token`), admin guard/rate-limit infra. Traceability repair needed so Phase 8 artifacts/crossrefs make ADMN-12 machine-checkable (D-07, D-08). |
| REVW-10 | Admin aprova vaga → status muda de `pending` para `published` — vaga aparece imediatamente na home pública | Evidence: `backend/app/api/v1/admin.py` approve route, `backend/app/crud/jobs.py::approve_job` sets `published` and refreshes `expires_at`; UI `frontend/app/admin/review/ReviewQueue.tsx` optimistic remove + refetch + toast "Vaga aprovada e publicada."; `backend/tests/test_admin_jobs.py::test_approve`, `test_approve_refreshes_expires_at`. "Aparece imediatamente na home pública" UX needs code+human/browser note (D-05) unless live-verified. |
| REVW-11 | Admin edita campos de uma vaga pelo ID — campos modificados persistidos com validação de contato | Evidence: `backend/app/api/v1/admin.py` PUT route, `backend/app/crud/jobs.py::update_job` partial update, `backend/app/schemas/job.py` `JobUpdate`, IntegrityError/contact validation mapping; `frontend/lib/api.ts::updateJob`; review UI `EditJobDialog` integration in `ReviewQueue.tsx`; tests `test_update`, `test_update_no_contact_422`, `test_update_bad_city_422`, `test_update_blank_title_422`. |
| REVW-12 | Admin exclui vaga — remoção hard do banco; operação idempotente (exclusão duplicada é no-op) | **Implemented contract:** hard delete in `backend/app/crud/jobs.py::delete_job` + `backend/app/api/v1/admin.py` DELETE route returns 404 when job not found (second call after deletion). Tests: `backend/tests/test_admin_jobs.py::test_delete`, `test_delete_404`. Must include explicit note mapping "repeat delete returns 404 (idempotent-in-effect)" to requirement wording "exclusão duplicada é no-op" (D-06). Traceability repair for `08-03-SUMMARY.md`/`CONTEXT-SUMMARY.md` required (D-07, D-08). |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Use GSD workflow entry points for file-changing work (`/gsd-quick`, `/gsd-debug`, `/gsd-execute-phase`); do not make direct repo edits outside a GSD workflow unless explicitly bypassed. [VERIFIED: `AGENTS.md` GSD workflow section]
- **EmpregaNoix constraints (locked):** pt-BR locale/copy, no-login public access/frictionless core value, single master admin, dark minimalist purple theme tokens, fixed stack (Next.js 16 App Router + Tailwind, FastAPI, Neon Postgres, Groq, Cloudflare Turnstile, Vercel/Render deploy model). [VERIFIED: `AGENTS.md`, `.planning/PROJECT.md`]
- **Operational/test convention:** backend pytest suite runs from `backend/` (STATE notes root invocation breaks asyncio config in this repo). [VERIFIED: `.planning/STATE.md` decision `[Phase 03] suite do backend precisa rodar a partir de backend/`]
- **Security/anti-spam posture (existing):** contacts never in public payloads; reveal/login protected server-side with Turnstile + rate limiting; fail-closed config behavior outside dev; `/admin/expire` cron-secret boundary is separate (Phase 12 ownership for contract reconciliation). [CITED: `AGENTS.md`/`PROJECT.md`/`STATE.md`/audit artifacts]

## Summary

Phase 11 is a **verification-and-traceability closure phase**, not a feature phase. Planning must produce two new artifacts (`.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md`, `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md`), repair Phase 8 traceability in place (`08-03-SUMMARY.md`, `CONTEXT-SUMMARY.md`), and update `.planning/REQUIREMENTS.md` with Phase 11 ownership notes and split handling for SECR-12. [VERIFIED: `11-CONTEXT.md`, `.planning/ROADMAP.md` Phase 11, `.planning/v1.1-MILESTONE-AUDIT.md`]

Existing evidence is substantial in code/tests/summaries: Phase 7 has reveal/Turnstile/rate-limit implementation and targeted tests (`test_reveal_api.py`, `test_turnstile_service.py`, `test_ratelimit.py`, opt-in `test_turnstile_live.py`); Phase 8 has admin CRUD/extract implementation and tests (`test_admin_jobs.py`, `test_extract_api.py`) plus frontend admin/review UI with Turnstile login widget, Bearer-token persistence/usage, toasts, and optimistic approve/delete flows. The main work is to **run and record targeted test evidence now**, map it requirement-by-requirement, document caveats/human checks honestly, and fix machine-discoverable traceability gaps. [VERIFIED: codebase inspection + test runs below]

**Primary recommendation:** Plan 2-3 tightly scoped tasks: (1) collect/execute Phase 7 targeted evidence and author `07-VERIFICATION.md` with SECR-10 caveat + SECR-12 split note, (2) collect/execute Phase 8 targeted evidence + repair `08-03-SUMMARY.md`/`CONTEXT-SUMMARY.md` and author `08-VERIFICATION.md` with honest UI/human notes and REVW-12 idempotency mapping, (3) update `REQUIREMENTS.md` checkboxes/traceability (SECR-12 left unchecked). Keep all edits documentation/traceability-only.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Reveal/contact anti-spam evidence (SECR-10/11) | API / Backend | Frontend Client (Turnstile widget/build-time key) | Server-side Siteverify, rate limiting, and contact gating live in FastAPI/services; site key exposure/rebuild caveat is frontend build concern. [VERIFIED: backend reveal/turnstile/ratelimit modules + `ExtractForm.tsx`] |
| Admin auth/review CRUD evidence (ADMN/REVW) | API / Backend | Frontend Client (admin UI flows/toasts) | JWT auth, admin routes, CRUD semantics, and validation are backend-owned; queue UX/Turnstile indicator/toasts are frontend-owned evidence surfaces. [VERIFIED: `backend/app/api/v1/admin.py`, `deps.py`, frontend admin components] |
| Requirement/verification traceability closure | Project Planning Artifacts (`.planning/*`) | — | Phase goal is auditability: VERIFICATION files, summary/context frontmatter, and REQUIREMENTS traceability are the primary outputs. [VERIFIED: `11-CONTEXT.md`, `ROADMAP.md`] |

## Standard Stack

### Core (relevant to this phase)

| Library/Tool | Version/State | Purpose | Why Standard Here |
|--------------|---------------|---------|-------------------|
| pytest + pytest-asyncio + httpx | Project-locked in `backend/pyproject.toml` / venv | Execute targeted backend evidence tests | Existing repo test harness and offline fakes (`FakeTurnstileVerifier`, ASGI transport) are canonical for auditable behavior claims. [VERIFIED: `backend/tests/conftest.py`, targeted runs] |
| FastAPI + SQLAlchemy async | Existing backend stack | Source-of-truth behavior for reveal/admin/expire routes and CRUD contracts | Verification must cite real handlers/deps/services/CRUD, not plans alone. [VERIFIED: inspected modules] |
| Next.js 16 + React client components | Existing frontend stack | UI evidence for admin Turnstile widget, auth persistence, toasts, review actions | ADMN-10/REVW-10 UI claims require code + human/browser notes. [VERIFIED: frontend admin files] |
| Markdown + YAML frontmatter (GSD artifacts) | Repo convention | Verification reports and machine-discoverable traceability | `09-VERIFICATION.md`/`10-VERIFICATION.md` and summary frontmatter patterns are established. [VERIFIED: artifact inspection] |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cd backend; .\.venv\Scripts\python.exe -m pytest ...` | Run backend tests with correct asyncio/config context | All backend targeted test execution (D-01/D-04, STATE convention). [VERIFIED] |
| `rg`/file inspection | Locate requirement IDs/frontmatter/crossrefs and code anchors | Traceability repair and evidence mapping. [ASSUMED standard local tooling] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Running targeted tests now + recording snippets | Citing existing summaries only | Rejected by D-01/D-04; weaker audit freshness. |
| Full backend suite run | Targeted subset | Full suite is slower and DB/env-sensitive; phase asks for relevant targeted evidence with rationale. |

**Installation:** None required for planning/research; backend venv and pytest already present in repo (`backend/.venv`). [VERIFIED: environment probe]

## Architecture Patterns

### System Architecture Diagram (verification evidence flow)

```text
[Phase 7/8 implementation + summaries]
      |                         |
      v                         v
[Code paths/tests] -----> [Targeted pytest execution (now)]
      |                         |
      +-----------+-------------+
                  v
      [07-VERIFICATION.md / 08-VERIFICATION.md]
                  |
                  v
[Phase 8 traceability repair: 08-03-SUMMARY.md, CONTEXT-SUMMARY.md]
                  |
                  v
      [.planning/REQUIREMENTS.md updates + Phase 11 ownership notes]
                  |
                  v
          [Audit re-check readiness]
```

### Pattern 1: Evidence-backed verification artifact (mirror 09/10)
**What:** Requirement/truth-centric report with frontmatter/status, observable truths, required artifacts, key links/evidence, requirement coverage, anti-patterns/gaps/caveats, and human verification section.
**When to use:** Backfilling `07-VERIFICATION.md` and `08-VERIFICATION.md`.
**Evidence anchors:** `09-VERIFICATION.md` includes score/gaps/human verification/requirements coverage tables and explicit gap items; `10-VERIFICATION.md` shows passed structure with truths/artifacts/key links/requirements and noted non-blocking deviations. [VERIFIED]

### Pattern 2: Honest UI verification (code + human notes)
**What:** Cite implementing UI/API code paths and recorded test results, but list interactive/browser-only acceptance as human verification items unless actually exercised live now.
**When to use:** ADMN-10 indicator/interaction, toast/feedback behavior, "vaga aparece imediatamente na home pública" UX (REVW-10). [VERIFIED: D-05]

### Pattern 3: Split requirement ownership without false closure
**What:** Record partial/split verification in requirement-scoped verification + REQUIREMENTS traceability note while keeping shared checkbox state accurate.
**When to use:** SECR-12 (Phase 7 side documented in Phase 11, Phase 9 `/admin/expire` contract reconciliation owned by Phase 12; checkbox remains unchecked). [VERIFIED: D-03, D-10]

### Pattern 4: In-place traceability repair with machine-discoverable IDs
**What:** Edit existing Phase 8 artifacts (not replace history) to add/correct frontmatter and cross-reference lines so `ADMN-12`/`REVW-12` are discoverable by scans, with semantics appropriate to artifact type.
**When to use:** `08-03-SUMMARY.md` and `CONTEXT-SUMMARY.md` (D-07, D-08). [VERIFIED]

### Anti-Patterns to Avoid
- **Overclaiming UI/browser proof from static code:** violates D-05 and weakens audit trust.
- **Marking SECR-12 fully complete in Phase 11:** violates D-03/D-10 and ROADMAP boundary.
- **Citing summaries without fresh targeted test results:** violates D-01/D-04.
- **Rewriting Phase 8 history wholesale:** use in-place repair preserving artifact intent and correctness (D-07).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test evidence execution | Ad-hoc manual assertions only | Existing pytest suites/harness (`backend/tests/*`, `conftest.py` fakes/fixtures) | Repeatable, offline-capable where designed, aligns with repo conventions. [VERIFIED] |
| Verification report format | New arbitrary format | Mirror `09-VERIFICATION.md` / `10-VERIFICATION.md` sections and tables | Auditor/planner already consume this structure. [VERIFIED] |
| Requirement traceability semantics | Ambiguous prose-only notes | Frontmatter IDs + explicit crossrefs + REQUIREMENTS checkbox/traceability notes | Machine-checkable and unambiguous (D-07..D-10). [VERIFIED] |

## Common Pitfalls

### Pitfall 1: DB-dependent tests fail in unprepared environment
**What goes wrong:** `test_reveal_api.py`, `test_admin_jobs.py`, `test_extract_api.py` rely on DB fixtures/`jobs` table; running without migrated test DB yields skips/errors (observed: relation `jobs` does not exist). [VERIFIED: local probe]
**Why it happens:** `backend/tests/conftest.py` provisions engine/session against `TEST_DATABASE_URL`/`DATABASE_URL` and clears `jobs` per test. [VERIFIED]
**How to avoid:** Plan execution to (a) record offline targeted tests immediately (`test_turnstile_service.py`, `test_ratelimit.py`, `test_turnstile_live.py` skip rationale), and (b) run DB-backed targeted tests from `backend/` against a configured/migrated Postgres test DB, documenting exact env prerequisites/results.
**Warning signs:** pytest collection skip "TEST_DATABASE_URL/DATABASE_URL not set" or `ProgrammingError: relation "jobs" does not exist`.

### Pitfall 2: Claiming live Turnstile/Siteverify behavior from offline fakes
**What goes wrong:** Offline tests prove wiring/fail-closed logic but not real Cloudflare round-trip.
**Why it happens:** `test_turnstile_live.py` is opt-in (`TURNSTILE_LIVE=1`) and skipped by default. [VERIFIED]
**How to avoid:** Include `test_turnstile_live.py` in selected subset rationale: record skip-by-default behavior now unless explicitly run with network/env approval; do not claim live Cloudflare validation unless executed.

### Pitfall 3: SECR-12 scope bleed into Phase 12
**What goes wrong:** Checkbox/narrative implies full closure including `/admin/expire` contract reconciliation.
**Why it happens:** Requirement spans Phase 7 and Phase 9/12 concerns.
**How to avoid:** Apply D-03/D-10 exactly: Phase 7-side evidence in `07-VERIFICATION.md`, Phase 12 owns reconciliation, checkbox remains unchecked with split note.

### Pitfall 4: CONTEXT-SUMMARY.md semantics overstated
**What goes wrong:** Added frontmatter implies execution completion for a planning recap artifact.
**Why it happens:** Summaries often use `requirements-completed`.
**How to avoid:** Use artifact-appropriate frontmatter keys/values (e.g. `type: context-summary`, `requirements-referenced`) while making `ADMN-12`/`REVW-12` machine-discoverable and cross-referenced (D-08 discretion, but semantics must be accurate).

### Pitfall 5: REVW-12 wording mismatch
**What goes wrong:** Evidence states "404 on repeat delete" but auditor expects "no-op".
**Why it happens:** Implementation is hard-delete + 404 on missing row (idempotent-in-effect at API contract level).
**How to avoid:** Include explicit mapping note in `08-VERIFICATION.md` per D-06.

## Code Examples

### Targeted backend test commands (run from `backend/`) [VERIFIED: local run convention + executed probes]

```bash
# Phase 7 - offline, no DB required
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_turnstile_service.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ratelimit.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_turnstile_live.py -q  # opt-in; skipped without TURNSTILE_LIVE=1

# Phase 7/8 - DB-backed (requires configured+migrated TEST_DATABASE_URL/DATABASE_URL)
.\.venv\Scripts\python.exe -m pytest tests/test_reveal_api.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_admin_jobs.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_extract_api.py -q
```

### Recorded local probe results (2026-11-15, this workspace) [VERIFIED]

```text
tests/test_turnstile_service.py  -> 23 passed in 0.14s
tests/test_ratelimit.py          -> 12 passed in 0.13s
tests/test_turnstile_live.py     -> 3 skipped in 0.03s (opt-in; TURNSTILE_LIVE not set)

tests/test_reveal_api.py         -> 10 errors in 37.90s
  sqlalchemy.exc.ProgrammingError: relation "jobs" does not exist [SQL: DELETE FROM jobs]
  (test DB not migrated in this environment; conftest requires usable Postgres schema)
```

### Phase 8 traceability repair targets (in-place) [VERIFIED: inspected files]

```yaml
# 08-03-SUMMARY.md currently HAS frontmatter including:
requirements-completed:
  - ADMN-12
  - REVW-12
# Audit concern was machine-checkability/cross-reference coherence in Phase 8 artifacts set;
# planner should verify/fix any missing crossrefs/consistency and ensure discoverability.

# CONTEXT-SUMMARY.md currently has NO YAML frontmatter (starts at line 1 with prose).
# D-08 requires adding artifact-appropriate frontmatter + cross-reference lines for ADMN-12/REVW-12.
```

### Concrete code anchors for evidence mapping [VERIFIED]

```text
SECR-10/11 (Phase 7 side):
- backend/app/core/config.py (TURNSTILE_* knobs, fail-closed validation, turnstile_mode)
- backend/app/core/ratelimit.py (resolve_client_ip keying, endpoint bucket, pt-BR 429/Retry-After)
- backend/app/core/client_ip.py (proxy-aware IP resolution)
- backend/app/services/turnstile.py (Siteverify, fail-closed, action binding, pt-BR copy)
- backend/app/api/v1/public.py::reveal_contact (rate limit -> lookup -> verify -> 200/403/404)
- backend/app/deps.py::get_turnstile_verifier (DI seam, offline-testable)
- frontend/app/admin/paste/ExtractForm.tsx (NEXT_PUBLIC_TURNSTILE_SITE_KEY in bundle; rebuild caveat)

ADMN-10/11/12, REVW-10/11/12 (Phase 8 side):
- backend/app/api/v1/admin.py (require_admin on admin routes, list/approve/put/delete, 409/422/404 semantics)
- backend/app/deps.py::require_admin (Bearer JWT validation, 401 challenge)
- backend/app/crud/jobs.py (approve refreshes expires_at, partial update, hard delete 404-if-missing/idempotent-in-effect, list/get)
- backend/app/schemas/job.py (JobAdmin/JobUpdate validation contracts)
- frontend/lib/api.ts (Bearer Authorization headers, admin CRUD/extract helpers, ApiError handling)
- frontend/app/admin/review/ReviewQueue.tsx (optimistic approve/delete, toasts, refetch, 401 session handling)
- frontend/components/admin/AdminGuard.tsx, ToastProvider.tsx, ReviewRow/Edit/Delete dialogs
- backend/tests/test_admin_jobs.py, backend/tests/test_extract_api.py
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| "Phase complete" claims from summaries only | Phase-level `*-VERIFICATION.md` with requirement/truth/artifact evidence + gaps/human checks | Milestone audit/gap-closure workflow (v1.1 Phases 9-11) | Audit can distinguish implemented vs verified; Phase 11 must backfill 07/08. [VERIFIED: audit, 09/10 patterns] |
| Ambiguous REQ checkbox updates | Checkbox + explicit traceability/ownership notes (including split ownership like SECR-12) | Phase 11 scope decisions (D-09/D-10) | Prevents false full closure while preserving auditable partial progress. [VERIFIED] |

**Deprecated/outdated for this phase:** treating UI source inspection as sufficient proof for interactive acceptance (must include human/browser notes per D-05). [VERIFIED]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Standard local search tool `rg` is available for machine-discoverability checks during execution (not required for writing this research doc) | Supporting / Execution guidance | Low; can substitute PowerShell `Select-String`. |

## Open Questions

1. **DB-backed targeted test execution environment for Phase 11 evidence runs**
   - What we know: `test_reveal_api.py`, `test_admin_jobs.py`, `test_extract_api.py` are the most relevant DB-backed suites; conftest needs `TEST_DATABASE_URL`/`DATABASE_URL` and migrated schema. Local probe failed with missing `jobs` relation. [VERIFIED]
   - What's unclear: Which configured Neon/test database and migration state will be available to the executing agent/session when running tests "now" for the verification artifacts.
   - Recommendation: Planner should include an explicit prerequisite/check task (resolve DB URL, ensure schema/migrations applied) before claiming DB-backed results; if unavailable, record attempted command + failure as environment evidence and mark affected truths/human follow-up honestly (without fabricating passes).

2. **Exact REQUIREMENTS.md traceability edit style (global table vs per-entry notes)**
   - What we know: File currently has checkbox list + notes in summary sections; D-09/D-10 require unambiguous Phase 11 ownership pointers and SECR-12 split note.
   - What's unclear: Whether maintainers prefer inline notes next to each requirement line, a new Phase 11 gap-closure traceability subsection, or both.
   - Recommendation: Apply minimal, consistent edits that satisfy unambiguity and are easy to grep (e.g. append `(Phase 11: 07-VERIFICATION.md ...)`/`(Phase 11/Phase 12 split ...)` on affected lines plus a short "Gap Closure (Phase 11)" note block if helpful).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python venv (`backend/.venv`) | Backend pytest execution | ✓ | Present (`python.exe`, `pytest.exe`) | — |
| `pytest` / test deps in venv | Targeted backend tests | ✓ | Usable (23/12 passed on offline suites) | — |
| Postgres test DB with migrated schema | `test_reveal_api.py`, `test_admin_jobs.py`, `test_extract_api.py` | ✗ (in probed state) | Schema missing `jobs` relation on probed connection | Use configured/migrated `TEST_DATABASE_URL`; if blocked, record environment limitation and run only offline subset now |
| Network access to Cloudflare Siteverify | `test_turnstile_live.py` real round-trip | Not exercised (opt-in) | `TURNSTILE_LIVE` unset -> skipped | Keep skipped with rationale; run only with explicit approval/env |
| Node/frontend toolchain | UI/browser verification | Not required for this doc task | — | Provide code evidence + human/browser verification notes (D-05) |

**Missing dependencies with no fallback:**
- None that fully block producing verification/traceability artifacts; DB-backed test execution evidence is partially blocked in this environment until a migrated test DB is available.

**Missing dependencies with fallback:**
- Migrated Postgres test DB for DB-backed pytest subsets -> configure/use prepared test DB, or document blocked execution with captured command/error.
- Live Turnstile network verification -> keep `test_turnstile_live.py` skipped (opt-in) and rely on offline service tests + documented caveat.

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json` (absent would also be treated as enabled). Include this section.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (backend), httpx ASGI clients/offline fakes |
| Config file | `backend/pyproject.toml` (pytest config expected by repo convention); tests run from `backend/` |
| Quick run command | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_turnstile_service.py tests/test_ratelimit.py -q` |
| Full suite command | `cd backend; .\.venv\Scripts\python.exe -m pytest -q` (requires valid migrated test DB) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SECR-10 | Turnstile secret/site-key fail-closed config semantics + rebuild-caveat context evidence | unit/config + manual doc caveat | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_turnstile_service.py -q` (service behavior) + code inspection of config/frontend | ✅ (`test_turnstile_service.py`, config/frontend files exist); operational rebuild caveat is manual/documented |
| SECR-11 | Reveal/login rate limiting by IP, pt-BR 429/Retry-After, env-tunable knobs | unit/integration (ASGI/offline) + DB-backed reveal 429 | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_ratelimit.py tests/test_reveal_api.py -q` | ✅ (`test_ratelimit.py`, `test_reveal_api.py`) |
| SECR-12 | Phase 7-side anti-spam evidence mapping; `/admin/expire` X-Cron-Secret-only fail-closed contract reconciliation deferred to Phase 12 | integration/doc split | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_admin_jobs.py -q -k auth` (auth baseline) + inspect `deps.require_cron_secret`/Phase 9 tests; **no Phase 11 closure test for Phase 9 contract** | ✅ partial evidence exists; full closure owned by Phase 12 |
| ADMN-10 | Turnstile indicator/widget presence and interaction-only login UX | manual/browser + code inspection | N/A automated UI interaction in repo; cite `frontend/app/admin/paste/ExtractForm.tsx` | ✅ code exists; browser proof manual |
| ADMN-11 | JWT login persists token and authorizes protected admin routes | integration/API | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_admin_jobs.py tests/test_extract_api.py -q` | ✅ |
| ADMN-12 | `/auth/login` protected against credential stuffing (Turnstile server-side + rate limit) | integration/API + code inspection | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_extract_api.py -q` (auth/login path in helper) + inspect `auth` route/service wiring | ✅ partial; may need additional targeted auth tests if present |
| REVW-10 | Approve pending -> published, visible in public flow | integration/API + manual/browser UX note | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_admin_jobs.py -q -k approve` | ✅ tests exist; immediate-public-appearance UX manual note |
| REVW-11 | Edit job fields with contact validation | integration/API | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_admin_jobs.py -q -k update` | ✅ |
| REVW-12 | Hard delete; repeat delete returns 404 (idempotent-in-effect) mapped to "exclusão duplicada é no-op" | integration/API | `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_admin_jobs.py -q -k delete` | ✅ |

### Sampling Rate
- **Per task commit:** Run the smallest relevant targeted pytest subset for the artifact being produced (e.g. Phase 7 offline set for `07-VERIFICATION.md`, `-k approve/update/delete` for REVW mapping) from `backend/`.
- **Per wave/plan batch:** Re-run all targeted commands cited in both verification docs (offline + available DB-backed subsets) and re-check `rg`/frontmatter presence for repaired IDs.
- **Phase gate:** `07-VERIFICATION.md` and `08-VERIFICATION.md` exist with recorded results/snippets and caveats; traceability repairs present; `REQUIREMENTS.md` updated per D-09/D-10; any unrun DB-backed tests explicitly documented with reason before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] **Environment/setup prerequisite:** provision/configure a migrated Postgres test database for DB-backed targeted tests (`TEST_DATABASE_URL`/`DATABASE_URL`) — current probed environment cannot execute DB-backed suites (`relation "jobs" does not exist`).
- [ ] **Evidence capture artifact:** create `.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-TEST-EVIDENCE.md` or embed command transcripts/snippets directly in verification docs (planner choice) to satisfy D-01/D-04 "recorded results/snippets".

*(No new automated test framework install appears necessary; pytest/venv already available.)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | Yes | Bearer JWT admin auth (`require_admin`), login flow protected by Turnstile/rate limiting; evidence-only phase must not weaken controls. [VERIFIED] |
| V3 Session Management | Partial (token persistence UX) | Frontend stores JWT in `sessionStorage` and clears on 401/logout flows; document as implemented behavior, not as change target. [VERIFIED] |
| V4 Access Control | Yes | Admin routes require `require_admin`; cron endpoint uses separate `require_cron_secret` fail-closed dependency (Phase 12 contract reconciliation out of scope). [VERIFIED] |
| V5 Input Validation | Yes | Pydantic schemas / route validation / DB integrity checks (`at_least_one_contact`, status/city validation) evidenced in tests. [VERIFIED] |
| V6 Cryptography | Indirect | JWT signing/verification handled via existing backend security utilities/libs (not hand-rolled in this phase). [VERIFIED/ASSUMED by existing stack] |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Contact scraping / unauthorized reveal | Information Disclosure | Server-side Turnstile Siteverify + per-IP rate limit + contact-free public payloads + 404-before-verify ordering. [VERIFIED] |
| Credential stuffing on admin login | Elevation of Privilege / DoS | Turnstile gate + login rate limiting + fail-closed verification behavior. [VERIFIED] |
| Unauthorized admin CRUD access | Elevation of Privilege | `Authorization: Bearer <token>` required via `require_admin` on admin routes; 401 on missing/invalid token. [VERIFIED] |
| False audit closure of security-sensitive requirement | Repudiation / Process risk | Explicit caveats, split ownership notes (SECR-12), and human verification items for UI claims. [VERIFIED: D-02/D-03/D-05/D-10] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-CONTEXT.md` — locked decisions D-01..D-10, scope boundaries
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/v1.1-MILESTONE-AUDIT.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, `AGENTS.md` — goals, gaps, requirement states, conventions
- Phase 7/8 artifacts: `07-01..03-PLAN.md`, `07-01..03-SUMMARY.md`, `08-CONTEXT.md`, `08-DISCUSSION-LOG.md`, `08-RESEARCH.md`, `08-01..03-PLAN.md`, `08-01..03-SUMMARY.md`, `CONTEXT-SUMMARY.md`
- Verification patterns: `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md`, `.planning/phases/10-rebranding-launch-preparation-empreganoix/10-VERIFICATION.md`
- Code/tests (inspected): `backend/app/api/v1/public.py`, `backend/app/api/v1/admin.py`, `backend/app/deps.py`, `backend/app/core/config.py`, `backend/app/core/ratelimit.py`, `backend/app/core/client_ip.py`, `backend/app/services/turnstile.py`, `backend/app/crud/jobs.py`, `backend/tests/test_reveal_api.py`, `backend/tests/test_turnstile_service.py`, `backend/tests/test_ratelimit.py`, `backend/tests/test_turnstile_live.py`, `backend/tests/test_admin_jobs.py`, `backend/tests/test_extract_api.py`, `backend/tests/conftest.py`, `frontend/app/admin/paste/ExtractForm.tsx`, `frontend/app/admin/review/ReviewQueue.tsx`, `frontend/lib/api.ts`, `frontend/components/admin/AdminGuard.tsx`, `frontend/components/admin/ToastProvider.tsx`
- Local command execution (2026-11-15): targeted pytest runs from `backend/` for `test_turnstile_service.py`, `test_ratelimit.py`, `test_turnstile_live.py`, and probe of `test_reveal_api.py`

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - derived from inspected repo stack/config/tests and established GSD artifact patterns
- Architecture: HIGH - verification/traceability flow and evidence anchors are explicit in CONTEXT/ROADMAP/audit and existing artifacts
- Pitfalls: HIGH - DB/env behavior and test opt-in skip confirmed by conftest inspection and local command results

**Research date:** 2026-11-15
**Valid until:** 2026-12-15 (stable internal audit/verification process; revalidate if Phase 7/8 code or requirement text changes)
