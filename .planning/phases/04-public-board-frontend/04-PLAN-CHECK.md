---
phase: 04-public-board-frontend
artifact: plan-check
verdict: BLOCK
revision_loop: 1
blockers: 8
warnings: 9
info: 3
checked_at: 2026-10-22
plans_checked: 6
---

# Phase 4 — Plan Verification (pre-execution)

**Goal verified against:** ROADMAP "Qualquer visitante encontra uma vaga e o contato para se candidatar em segundos, no mobile, sem cadastro nem login."

**Verdict: BLOCK** — the six plans cover all 11 requirements and the wave graph is sound, but the phase gate (`verify-ssr.ps1`), one backend test, and the wave-1 verification commands cannot pass as written, and one requirement (PUBL-02 pagination) has no executable proof. Eight blockers, all mechanically fixable. Execution would burn a revision loop at best, or mark a failing gate as passed at worst.

---

## Dimension Results

| # | Dimension | Result | Note |
|---|-----------|--------|------|
| 1 | Requirement coverage | ✅ PASS | All 11 IDs in plan frontmatter; every success criterion maps to tasks |
| 2 | Task completeness | ❌ FAIL | Structure complete, but B-01…B-04, B-06, B-07 make `<verify>` blocks unsatisfiable |
| 3 | Dependency correctness | ✅ PASS | 04-01→04-03→04-04→04-05→04-06; 04-02 wave 1. `0002_jobs_source_snippet` revision id confirmed |
| 4 | Key links planned | ⚠️ ISSUES | fetch→board, dialog→grid, reveal→dialog wired; Tailwind→admin isolation has no working check (B-03) |
| 5 | Scope sanity | ⚠️ WARNING | 04-03 = 11 files, 04-04 = 9 files (threshold 10) |
| 6 | Verification derivation | ✅ PASS | Truths are user-observable; artifacts map to truths |
| 7 | Context compliance | ⚠️ ISSUES | D-01…D-13 honored; one copy string drifts from D-06c (W-03) |
| 7b | Scope reduction | ✅ PASS | No "v1 / static for now / wire later" language; every D-xx fully delivered |
| 7c | Architectural tier compliance | ✅ PASS | All 10 capabilities land in the tier named by RESEARCH §Architectural Responsibility Map |
| 8 | Nyquist compliance | ✅ PASS | Every auto task has `<automated>`; no E2E-suite/watch commands; no Wave-0 `MISSING`; 04-06 task 3 is a checkpoint (exempt). VALIDATION.md map is stale (W-02) |
| 9 | Cross-plan data contracts | ✅ PASS | `Filters`/`PAGE_SIZE` single source in `lib/filters.ts`; 04-05 re-uses, does not redeclare; `lib/api.ts` extended, never forked |
| 10 | AGENTS.md compliance | ✅ PASS | Next 15 not upgraded; no new frontend runner (D-12a); pt-BR; locked palette |
| 11 | Research resolution | ❌ FAIL | `04-RESEARCH.md:595` `## Open Questions` — 3 questions, none RESOLVED (B-08) |
| 12 | Pattern compliance | ✅ PASS | No-analog files reference UI-SPEC §Copywriting / RESEARCH; `ExtractForm.tsx`, `lib/api.ts`, `scripts/seed.py` analogs cited |

---

## Blockers

### B-01 `verify-ssr.ps1` requests `limit=100`; backend caps `le=50`
- Plan: 04-06, task 2 (`frontend/scripts/verify-ssr.ps1`, check 5)
- Evidence: plan text `$jobs = Invoke-RestMethod "$BackendUrl/api/v1/public/jobs?limit=100"`. Backend contract is preserved by 04-02 task 2 itself: "Keep the default `limit=20` and `le=50` untouched" (`backend/app/api/v1/public.py`). FastAPI returns **422**, and `$ErrorActionPreference = "Stop"` aborts the script before checks 6 and 7 ever run.
- Fix: use `limit=50` (and lower the `-ge 3` floor to `-ge 1`), or page twice. Add an explicit assertion that `limit=51` returns 422 so the cap is documented.

### B-02 `sort=antigas` direction asserted backwards
- Plan: 04-06, task 2 (check 7)
- Evidence: script asserts "`sort=antigas` returns `created_at` **non-increasing**". 04-02 task 2 orders with `Job.created_at.asc() if sort == "antigas"` → oldest first → **non-decreasing**. The gate would fail on a correct implementation.
- Fix: assert `$jobs.items[i].created_at -ge $jobs.items[i+1].created_at` for `sort=recentes` and `-le` for `sort=antigas`.

### B-03 `admin-page` sentinel does not exist anywhere
- Plan: 04-06, task 2 (check 2); invalidates 04-01 `must_haves.truths[2]`
- Evidence: `frontend/app/admin/paste/page.tsx` renders `<main>` with no class; `Select-String -Pattern "admin-page"` across `04-0*-PLAN.md` matches **only** 04-06's assertion — no task adds the class. `GET /admin/paste` can never contain `admin-page`, so check 2 throws. The real Preflight-isolation claim therefore has **no working verification** (the only surviving check, "does not contain `Vagas abertas`", is weak).
- Fix: choose one — (a) add `className="admin-page"` to `frontend/app/admin/paste/page.tsx` in 04-01 task 2 (add the file to `files_modified`) and keep the assertion, or (b) drop `admin-page` and assert the admin form still renders (plain-ASCII substring, e.g. `Colar vagas`) **and** that `--color-canvas` / `sr-only` are absent from the admin HTML (Tailwind signature).

### B-04 Bogus deep-link assertion targets client-only state
- Plan: 04-06, task 2 (check 6) → 04-04, task 3
- Evidence: `verify-ssr.ps1` does a plain HTTP GET (no JS). `JobGrid` holds `notFound` in `useState` and sets it in a mount effect ("On first mount: if `initialJob` → `setSelected`; else if `initialVaga` → `setNotFound(true)`"). The SSR HTML for `?vaga=<bogus>` contains no dialog, so `contains "Vaga não encontrada"` always fails. Symmetrically, the **valid** deep-link assertion ("contains first 20 chars of `$title`") is satisfied by the card title, not the dialog — a vacuous pass.
- Fix: make the not-found state server-rendered (`page.tsx` passes `initialJob === null && filters.vaga` → render the dialog's not-found markup in the RSC tree), **or** replace both assertions with SSRF-safe ones (`200`, no `contact_email`/`mailto:`, grid state untouched) and leave the not-found copy to UAT step 8.

### B-05 Pagination (PUBL-02) cannot be exercised by any check
- Plans: 04-02 task 3 (`--count` default 18, cap 1..24) + 04-03 task 2 (`PAGE_SIZE = 24`, `Pagination` renders nothing when `totalPages <= 1`) + 04-06 UAT step 7
- Evidence: UAT step 1 seeds **18** rows; step 7 requires "**With >24 seeded rows**, page 2 keeps `q`/`city`/`sort`". The seed caps at **24**, and `PAGE_SIZE` is **24** → at most one page, ever. `verify-ssr.ps1` never checks `?page=2`. PUBL-02's pagination therefore has zero executable proof, and UAT step 7 is unimplementable as written.
- Fix: raise seed default to 30 (`--count 30`, cap 60) **and** add a `verify-ssr.ps1` check: `GET /?page=2` contains `Página 2 de`; keep UAT step 7 consistent with the new count.

### B-06 CORS test asserts an expose-header on a preflight response
- Plan: 04-04, task 1 (`backend/tests/test_public_api.py::test_cors_preflight_exposes_retry_after`)
- Evidence: Starlette's `CORSMiddleware.preflight_response` sets `Allow-Origin` / `Allow-Methods` / `Allow-Headers` / `Max-Age` only; `Access-Control-Expose-Headers` is added by `simple_response`. The planned `OPTIONS` assertion fails, blocking the task's `<automated>` gate.
- Fix: `GET /api/v1/public/jobs?limit=1` with `Origin: http://localhost:3000` and assert `access-control-expose-headers` contains `retry-after`; optionally keep a separate `OPTIONS` test asserting `access-control-allow-methods` contains `POST`.

### B-07 Wave-1 verification commands run in the wrong directory (and one is a false green)
- Plan: 04-01, tasks 1, 2, 3
- Evidence (executed from repo root, which has **no `package.json`** — `Test-Path package.json` → `False`):
  - `npm ls tailwindcss --depth=0` → resolves the **ancestor** profile at `C:\Users\AndreC`, prints `tailwindcss@3.4.19`, **exit 0**. The verify would pass while `frontend/` has no Tailwind at all.
  - `node -e "readFileSync('postcss.config.mjs')"` → ENOENT → exit 1 (task 1 still fails, but on the wrong half).
  - `npm run lint` → `npm error Missing script: "lint"`, **exit 1** (measured) → tasks 2 and 3 fail.
- Fix: wrap every command in `Push-Location frontend; …; Pop-Location` (the pattern 04-02…04-06 already use), and change the Tailwind probe to `npm ls tailwindcss @tailwindcss/postcss --depth=0 --prefix .` inside `frontend/` with an exact `4.3.3` string assertion.

### B-08 `04-RESEARCH.md` ships unresolved open questions
- File: `04-RESEARCH.md:595` — `## Open Questions` (no `(RESOLVED)` suffix), 3 items:
  1. whether `q` should also match city (recommendation: keep D-03, change the placeholder — **flag to the user**);
  2. accented vs unaccented city chip labels — implemented by 04-03 (`lib/cities.ts`, accented labels + canonical wire value) but never confirmed/recorded;
  3. frontend test runner — resolved implicitly by D-12a.
- Evidence of drift: RESEARCH claims UI-SPEC's placeholder is `Busque por cargo, empresa ou cidade`; UI-SPEC line 177 actually says `Busque por cargo, empresa ou palavra-chave`; CONTEXT D-06c says `Buscar por cargo, …`. Plans follow UI-SPEC. Three artifacts, three strings.
- Fix: mark the section `## Open Questions (RESOLVED)`, resolve 1 and 3 inline, and record the city-label decision (accented display, canonical wire) in `04-CONTEXT.md` or the UAT. Then add one line to 04-06's UAT confirming the chip labels, so the deviation from UI-SPEC's literal strings is accepted rather than accidental.

---

## Warnings

- **W-01 (04-06 t2) — PS 5.1 encoding hazard.** `verify-ssr.ps1` compares accented literals (`Espaço publicitário`, `Doações`, `não`, `Página`) against UTF-8 HTML. Windows PowerShell 5.1 parses BOM-less `.ps1` as ANSI; this repo already shows mojibake (`Admin �?" Colar vagas`, `Token nA�o recebido`, `Doa��es` in ROADMAP). Save the file as **UTF-8 with BOM** and state it in the task, or assert on ASCII-only substrings.
- **W-02 (04-VALIDATION.md) — stale Nyquist map.** Per-task ids (`04-01-01`…`04-05-02`) do not match the six plans; 04-02 is mapped to frontend card rendering; 04-06 has no rows; frontmatter `status: draft`, `nyquist_compliant: false`, `wave_0_complete: false`. Regenerate after the fixes.
- **W-03 (04-05 t1) — copy drift on the search placeholder.** CONTEXT D-06c `Buscar por cargo, empresa ou palavra-chave` vs UI-SPEC/plan `Busque por cargo, …`. Reconcile the imperative and annotate the loser.
- **W-04 (04-03 t2) — "Ver mais/Ver menos" (PUBL-02) is never exercised.** Implemented behind `activities.length > 160`; no `verify-ssr` check (client-only) and no UAT step. Add a UAT instruction ("expand a long card, `aria-expanded` flips, clamp removed").
- **W-05 (UIUX-01) — WCAG AA has no named check.** UAT step 10 covers focus visibility only; no contrast assertion or manual contrast step exists. Add "sample `--color-fg-muted`, `--color-accent-soft`, `--color-donate` against `--color-canvas` ≥ 4.5:1" to UAT, or state that UI-SPEC approval is the evidence.
- **W-06 (UIUX-02) — "efeito só no hover" unverified.** Implementation is `@media (hover: hover)` + `hover:`; UAT step 11 only checks navigation to `/doacoes`. Add "hover shows background tint; no glow/animation when idle".
- **W-07 (scope) — 04-03 touches 11 files, 04-04 touches 9.** Above the 10-file warning line; both are single-feature slices, so acceptable if execution stays inside the listed files.
- **W-08 (04-01 t3, 04-06 t3/t4) — route-group build path is version-fragile.** `.next\server\app\(public)\doacoes\page.js`; verified convention only for a non-group route (`.next/server/app/admin/paste/page.js` exists). Prefer `.next\server\app\(public)\doacoes.html` **or** a `routes-manifest.json` / `prerender-manifest.json` assertion.
- **W-09 (04-02 t1) — the migration's own mitigation is untested.** 0003 disables `jobs_updated_at` around the backfill, but no test asserts `updated_at` is unchanged after the migration. Add: capture `updated_at`, run the backfill `UPDATE`, assert equality; assert the trigger is re-enabled (`pg_trigger.tgenabled = 'O'`).

## Info

- **I-01** `04-RESEARCH.md` still suggests `uv run pytest`; `04-VALIDATION.md` and all plans correctly use `.\.venv\Scripts\python.exe`. Remove the stale hint.
- **I-02** 04-05 t1 greps the literal `'300'` to prove debouncing — true for the wrong reason (also matches comments). Assert `setTimeout(…, 300)` or a named constant.
- **I-03** 04-06 t1's `$ad -match "script|dangerouslySetInnerHTML"` is substring-based; `aria-describedby` or a comment mentioning "description" would trip it. Anchor to `<script` / `dangerouslySetInnerHTML`.

---

## Requirement Coverage (goal-backward)

| Req | Delivering tasks | Executable proof | Status |
|-----|------------------|------------------|--------|
| PUBL-01 | 04-03 t2, 04-05 t2 | build + SSR check 1 ("Ver a vaga") | ✅ |
| PUBL-02 | 04-03 t2 | pagination: **none** (B-05); expandable: none (W-04) | ❌ |
| PUBL-03 | 04-03 t3, 04-04 t2 | grep for contact fields; SSR checks 1/6 | ⚠️ (B-04) |
| PUBL-04 | 04-04 t1/t2 | literal `wa.me`/`mailto` copy; UAT 8 | ✅ (manual) |
| PUBL-06 | 04-03/04-04 classes | UAT 5 (390/1024/1280) | ✅ (manual) |
| SRCH-01 | 04-02 t1/t2, 04-05 t1 | `pytest tests/test_public_search.py` | ✅ (strongest layer) |
| SRCH-02 | 04-02 t2, 04-05 t1 | pytest city matrix + SSR check 7 | ⚠️ (B-01) |
| SRCH-03 | 04-02 t2, 04-05 t1 | pytest sort/tie-break; SSR check 7 | ⚠️ (B-02) |
| UIUX-01 | 04-01 t2, 04-06 t1/t2 | token grep + build; AA unverified (W-05) | ⚠️ |
| UIUX-02 | 04-01 t2/t3 | UAT 11 (navigation only, W-06) | ⚠️ |
| UIUX-03 | 04-06 t1 | SSR check 1 (`Espaço publicitário` ×≥3) | ✅ |

Locked decisions: D-01…D-13 all have an implementing task; no deferred idea was pulled in; no tier mismatch.

---

## Revision Gate

Loop **1 of 3**. Return to `gsd-planner` with B-01…B-08. All are localized edits (one script, one test, one seed constant, three command prefixes, one sentinel class, one RESEARCH section) — no re-architecture. If loop 3 is exhausted, escalate to the user with the surviving blockers rather than executing.
