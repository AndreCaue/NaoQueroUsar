---
phase: 04-public-board-frontend
artifact: plan-check
verdict: PASS WITH CONCERNS
revision_loop: 3
blockers: 0
warnings: 3
info: 4
checked_at: 2026-10-23
plans_checked: 6
---

# Phase 4 — Plan Verification (pre-execution, loop 3)

**Verdict: PASS WITH CONCERNS** — no blocker remains. `B-04` is resolved end to end, the seven previously-resolved blockers still hold, and the loop-3 edits introduced no new contradiction. Concerns are documentation/verification-robustness items only; execution can proceed.

**Re-check scope:** `B-04` end-to-end; regression spot-check of `B-01/B-02/B-03/B-05/B-07`; loop-3 contradiction scan (`jobs`/`items`, ad placement, `Página N de`, `data-dialog-title`); remaining HIGH+ issues.

## Loop 3 disposition — B-04 RESOLVED

`?vaga=not-a-uuid` now reaches the server-rendered panel on a correct execution:

| Step | Plan | Evidence | Result |
|------|------|----------|--------|
| Parse | 04-03 t1 | `normalizeFilters` keeps `vaga` = first value, trimmed, capped 64, **even when not a UUID**; `toApiParams` omits it | raw survives |
| Fetch boundary | 04-04 t3 | `rawVaga = filters.vaga?.trim() \|\| null`; `vaga = isUuid(rawVaga) ? rawVaga : null`; `malformedVaga = Boolean(rawVaga && !vaga)`; `fetchJob` only inside the `vaga` branch | **no `GET /jobs/{id}` for a malformed id** |
| Render | 04-04 t3 | panel when `malformedVaga \|\| (vaga && initialJob === null)`; title `Vaga não encontrada`, link `Limpar filtros`, in the RSC tree above `JobGrid` | **present in SSR HTML** |
| State rewrite | 04-05 t2 | explicit bullet requires keeping the same condition above the grid; toolbar `commit` always sets `page: 1, vaga: null` | preserved |
| Gate | 04-06 t2 check 6 | malformed asserts `Vaga não encontrada` + `Limpar filtros`; bogus UUID asserts the same panel; valid extracts `data-dialog-title` | executable proof |

- **Valid UUID outside the filter (D-10a):** any valid `vaga` is resolved via `fetchJob` → `GET /api/v1/public/jobs/{id}` regardless of page membership; a found job seeds `useState(initialJob ?? null)`, so the dialog markup is in the SSR HTML.
- **Valid-but-missing UUID:** `fetchJob` maps `404 → null`, so `(vaga && initialJob === null)` renders the same panel.
- **Plain `/`:** `filters.vaga` is null → no panel and no `fetchJob`; the board is unaffected.

## Regression spot-check (loop-2 RESOLVED blockers)

| ID | Status | Evidence in current plans |
|----|--------|--------------------------|
| B-01 | ✅ still holds | 04-06 check 5 uses `limit=50`; check 5b requests `limit=51` and expects `422`; 04-02 keeps `le=50`. |
| B-02 | ✅ still holds | 04-06 check 7 asserts `recentes` non-increasing and `antigas` non-decreasing; 04-02 keeps `asc()`/`desc()` plus the `id` tie-break. |
| B-03 | ✅ still holds | `Colar vagas` exists in `frontend/app/admin/paste/page.tsx:5`; 04-06 check 2 fetches every admin-linked stylesheet and rejects `--color-canvas`; `globals-admin.css` has no token. |
| B-05 | ✅ still holds | 04-02 seed default **30** (cap 1..60) > `PAGE_SIZE` 24; check 4b asserts the `Página 2 de` prefix; UAT step 7 uses `<N>`. |
| B-07 | ✅ still holds | 04-01 uses `Push-Location frontend` and `Test-Path`/`node -e` probes inside `frontend/`; no root `npm ls`. |

`B-04`, `B-06`, `B-08` remain resolved as recorded in loop 2.

## Loop-3 contradiction scan

- **`jobs` vs `items`:** ✅ 04-06 interfaces/action use `jobs` and state “there is no `items` prop”; only the API JSON uses `items` (`data.items`, `$jobs.items`).
- **Ad-slot placement:** ✅ header is **outside/above** the two-column wrapper (full container width, 728px centered); sidebar is in the `lg` right column; inline slots live inside the content column. Loop-2 `I-02` resolved.
- **`Página N de`:** ✅ `Pagination` copy, 04-06 check 4b prefix, and UAT step 7 prefix agree.
- **`data-dialog-title`:** ✅ attribute created in 04-03, preserved in 04-04, styled in 04-06 `public.css`, and extracted by check 6.

## Remaining concerns (non-blocking — no HIGH+)

- **W-02 (carried).** 04-03 still lists 13 files (context text says 11). Cohesive vertical slice, below the 15-file blocker line; stay inside the list.
- **W-03 (carried).** `04-VALIDATION.md` is still `status: draft`, `nyquist_compliant: false`, with a stale per-task map. Regenerate after execution; does not block the gate.
- **W-07 (new).** 04-05's automated verify does not re-assert `malformedVaga`/the panel; the phase gate check 6 is the safety net. Acceptable for execution, but worth asserting if 04-05 is revised.
- **Info.** UI-SPEC `W-05` is fixed in the working tree (lines 248/259 annotated for D-06b/D-10a) but is uncommitted.
- **Info.** 04-06 check 6 references `$deepValid` without showing its assignment; implement it explicitly (`$deepValid = Get-Html "$BaseUrl/?vaga=$id"`). The title regex is element-scoped but still regex-brittle.
- **Info.** No gate/UAT case exercises a valid UUID **outside** the active filter (`?vaga=<id>&city=remoto`). The implementation resolves unconditionally, so D-10a is covered by construction; an explicit UAT case would strengthen the proof.
- **I-01 (carried).** `npm install`, `npm run build/lint`, `alembic upgrade head` against Neon, and the live servers remain execution-time preconditions.

## DISPOSITION

**PASS WITH CONCERNS.** Proceed to `/gsd-execute-phase 4`. Re-open the checker only if execution changes the `vaga` parsing/fetch boundary or the phase gate.

---

# Loop 2 report (historical — superseded by Loop 3)

> The `B-04` finding below was fixed in commit `7f9355c` and re-verified above. The rest of this section is preserved as the loop-2 record.

**Goal verified against:** ROADMAP "Qualquer visitante encontra uma vaga e o contato para se candidatar em segundos, no mobile, sem cadastro nem login."

**Verdict: BLOCK** — the loop-1 revision fixes seven of the eight blockers. The remaining blocker is `B-04`: the revision fixed the **valid** `?vaga=<uuid>` deep link by rendering the dialog from `initialJob`, but the **malformed** `?vaga=not-a-uuid` path still cannot reach the server-rendered not-found panel. The phase gate (`verify-ssr.ps1` check 6) and UAT step 8 would fail on a correct execution of the current plans.

---

## Dimension Results

| # | Dimension | Result | Note |
|---|-----------|--------|------|
| 1 | Requirement coverage | ✅ PASS | All 11 IDs in plan frontmatter; every success criterion maps to tasks |
| 2 | Task completeness | ✅ PASS | All auto tasks have files/action/verify/done; B-04 is a logic contradiction, not a missing field |
| 3 | Dependency correctness | ✅ PASS | `04-01 → 04-03 → 04-04 → 04-05 → 04-06`; `04-02` wave 1; no cycles or missing refs |
| 4 | Key links planned | ❌ ISSUES | Valid deep-link dialog is wired; malformed deep-link → panel link is broken (B-04) |
| 5 | Scope sanity | ⚠️ WARNING | `04-03` lists 13 files (threshold 10); `04-04` lists 9 |
| 6 | Verification derivation | ✅ PASS | Truths are user-observable; artifacts map to truths |
| 7 | Context compliance | ✅ PASS | D-01…D-13 honored; UI-SPEC drift is a documentation warning (W-05), not a plan contradiction |
| 7b | Scope reduction | ✅ PASS | No “v1 / static for now / wire later” language |
| 7c | Architectural tier compliance | ✅ PASS | Capabilities land in the tiers named by RESEARCH §Architectural Responsibility Map |
| 8 | Nyquist compliance | ✅ PASS | Every auto task has `<automated>`; no E2E/watch commands; no Wave-0 `MISSING`; `04-06` checkpoint exempt. VALIDATION map is stale (W-03) |
| 9 | Cross-plan data contracts | ✅ PASS | `Filters`/`PAGE_SIZE` stay in `lib/filters.ts`; `04-05` consumes, does not re-declare; `lib/api.ts` is extended, not forked |
| 10 | AGENTS.md compliance | ✅ PASS | Next 15 not upgraded; no new frontend runner; pt-BR; locked palette |
| 11 | Research resolution | ✅ PASS | `04-RESEARCH.md:595` is `## Open Questions (RESOLVED 2026-10-22)` |
| 12 | Pattern compliance | ✅ PASS | No-analog files reference UI-SPEC/RESEARCH; analogs cited for `ExtractForm.tsx`, `lib/api.ts`, `scripts/seed.py` |

---

## Loop-1 Blocker Resolution

| ID | Status | Evidence |
|----|--------|----------|
| B-01 | ✅ RESOLVED | `04-06` check 5 now uses `limit=50`; check 5b requests `limit=51` and expects 422. Backend still enforces `limit: Query(20, ge=1, le=50)` (`backend/app/api/v1/public.py:28`). |
| B-02 | ✅ RESOLVED | `04-06` check 7 asserts `sort=recentes` is non-increasing and `sort=antigas` is non-decreasing. `04-02` orders `asc()` only for `antigas`, with an id tie-break. |
| B-03 | ✅ RESOLVED | The real sentinel `Colar vagas` exists in `frontend/app/admin/paste/page.tsx:5`; `.admin-page` and `.admin-panel` exist in `ExtractForm.tsx:98-99` and `globals-admin.css:9,18`. Built `.next/server/app/admin/paste.html` links `/_next/static/css/7f10d5f8f9a1f9ae.css`, which does **not** contain `--color-canvas`. The check is non-vacuous. The loop-1 claim that `admin-page` did not exist was wrong. |
| B-04 | ❌ **NOT RESOLVED** | The valid-UUID half is fixed (`useState(initialJob ?? null)` server-renders the dialog). The malformed half is still a dead path: `normalizeFilters` sets `vaga` **only when `isUuid()`** (`04-03:152`), so `?vaga=not-a-uuid` becomes `null`. `page.tsx` renders the not-found panel only when `filters.vaga` is truthy and `initialJob === null` (`04-04:195-200`). Gate check 6 and UAT step 8 expect `Vaga nao encontrada` + `Limpar filtros` for `?vaga=not-a-uuid` (`04-06:140,165`); the panel never renders. `04-04:25,222` also promise malformed-id handling, so the plan contradicts itself. |
| B-05 | ✅ RESOLVED (warning W-04) | `04-02` seed default is **30**, cap `1..60`; `PAGE_SIZE` is 24. `04-06` check 4b requests `/?page=2` and asserts `Pagina 2 de`. UAT step 7 uses page 2. |
| B-06 | ✅ RESOLVED | `04-04` test is now `test_cors_exposes_retry_after_on_actual_response`: `GET /api/v1/public/jobs?limit=1` with `Origin: http://localhost:3000`, assert `access-control-expose-headers` contains `retry-after`. It explicitly does **not** assert expose-headers on `OPTIONS`. `main.py` gets `expose_headers=["Retry-After"]`; `config.py` defaults `CORS_ORIGINS` to `http://localhost:3000` and `.env` has no override. |
| B-07 | ✅ RESOLVED | `04-01` tasks use `Push-Location frontend; …; Pop-Location`. The Tailwind probe uses `Test-Path` + `node -e` against `frontend/node_modules`, not `npm ls` from the repo root. |
| B-08 | ✅ RESOLVED | `04-RESEARCH.md` line 595 is `## Open Questions (RESOLVED 2026-10-22)`; all three questions have inline resolutions. Placeholder `Busque por cargo, empresa ou palavra-chave` is consistent in RESEARCH, UI-SPEC line 177, CONTEXT D-06c, and `04-05`. |

---

## Blocker

### B-04 Malformed `?vaga=` still cannot reach the server-rendered not-found panel

- **Plans:** `04-03` task 1, `04-04` task 3, `04-06` task 2 / UAT step 8.
- **Evidence chain:**
  1. `04-03:152` — `vaga` only when `isUuid()`. A non-UUID input is discarded.
  2. `04-04:195` — `const vaga = filters.vaga && isUuid(filters.vaga) ? filters.vaga : null;`; for `not-a-uuid`, this is `null`.
  3. `04-04:200` — panel renders only when `filters.vaga` is present **and** `initialJob === null`. `filters.vaga` is `null`, so the panel is skipped.
  4. `04-06:140` — gate asserts malformed `?vaga=not-a-uuid` contains `Vaga nao encontrada` + `Limpar filtros`.
  5. `04-06:165` (UAT 8) — human gate expects the same panel.
- **Impact:** `verify-ssr.ps1` fails at check 6; the human UAT also fails. This prevents the phase gate from passing even if every other plan is executed correctly.
- **Why it slipped:** `04-04`’s automated verify only greps source for `isUuid`, `Vaga nao encontrada`, and `Limpar filtros`; it does not exercise the malformed branch. The only behavioral proof is the phase gate.
- **Fix (localized):** Preserve the raw `vaga` value in `Filters` (for example `vaga: string | null` = trimmed raw value, with `toApiParams` still omitting it), or add a `vagaRaw` field. In `page.tsx`, validate only at the fetch boundary:
  ```ts
  const rawVaga = filters.vaga;
  const vaga = rawVaga && isUuid(rawVaga) ? rawVaga : null;
  const malformedVaga = Boolean(rawVaga && !vaga);
  ```
  Then render the not-found panel when `malformedVaga || (vaga && initialJob === null)`, while only calling `fetchJob(vaga)` for a valid UUID. Keep the gate and UAT assertions as-is; they are correct.
- **Do not** solve this by deleting the malformed assertion: `04-04` must_haves and the plan’s own `<done>` explicitly require malformed IDs to render the panel.

---

## Warnings

- **W-01 (04-06 interfaces) — `JobGrid` prop name drift.** `04-06:75,98` says `JobGrid` receives `items` and renders inline ads using `items.length`, but `04-03:186` and `04-04:209` define the prop as `jobs`. The action says “keep the existing card rendering”, so an implementer may follow `jobs`, but the interface text is wrong and can cause a compile error if copied literally. Align on `jobs` (or change all plans consistently).
- **W-02 (04-03 scope) — 13 files.** `files_modified` lists 13 files, above the 10-file warning line. The slice is cohesive (filters, API, cards, dialog, page, loading/error), so it is acceptable if execution stays inside the listed files; otherwise split.
- **W-03 (04-VALIDATION.md) — stale Nyquist map.** Frontmatter still has `status: draft`, `nyquist_compliant: false`, `wave_0_complete: false`; per-task ids do not match the six plans, `04-02` is mapped to frontend card rendering, and `04-06` has no rows. Regenerate after B-04 is fixed.
- **W-04 (04-06 UAT step 7) — exact pagination copy is brittle.** The seed default is 30, but `backend/scripts/seed.py` already inserts one published row and `seed_public_demo.py` deletes only its marker rows. A fresh run gives 31 published rows, so `Pagina 1 de 2` is true today, but any extra published rows (or a non-clean test DB) make the exact `de 2` copy fail. Prefer asserting `Pagina 1 de` / `Pagina 2 de` or use a clean seed.
- **W-05 (UI-SPEC drift) — line 259 says “Nenhum `GET /jobs/{id}` no fluxo do board”, but CONTEXT D-10a requires server-side resolution for shared links; line 248 says the front sends the city **label**, while CONTEXT D-06b/D-05 and `04-03` send the **slug**. The plans correctly follow the later CONTEXT decisions (the backend accepts slug, label, and canonical), but the UI-SPEC should be annotated/updated so the acceptance contract is not contradictory. Not a blocker because CONTEXT is authoritative.
- **W-06 (04-06 check 6) — valid deep-link title assertion is not truly anchored.** The check asserts `data-dialog-title` (strong) and that the HTML contains the first 20 chars of the title (weak: the card also contains the title). The `data-dialog-title` marker is sufficient proof that the dialog markup was server-rendered; either extract the `data-dialog-title` element and assert its text, or drop the redundant title substring assertion.

---

## Info

- **I-01 — Execution preconditions not fully proven.** `tsc` and `next` binaries work, and the venv has `alembic`, `pytest`, `dotenv`, and `asyncpg`, but `npm install`, `alembic upgrade head` against the Neon test DB, and `npm run build/lint` were not executed in this review. Network access and the test branch must be available during execution.
- **I-02 (04-06 task 1) — header ad placement wording is ambiguous.** The action says insert the header AdSlot above the `h1`, then says the left column keeps `h1/subtitle/...`. If the two-column wrapper begins before the `h1`, the header slot may land inside the left column instead of spanning the container. Place the header slot outside the two-column wrapper if the intended 728px centered header is full-width.
- **I-03 (04-06 interfaces) — grid breakpoint drift.** `04-06:75` says `sm:grid-cols-2 xl:grid-cols-3`, while `04-03:186` creates `sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3`. The action says keep the existing grid, so this is documentation drift only; align the interface text.

---

## Requirement Coverage (goal-backward)

| Req | Delivering tasks | Executable proof | Status |
|-----|------------------|------------------|--------|
| PUBL-01 | 04-03 t2, 04-05 t2 | build + SSR check 1 (`Vagas abertas`, `Ver a vaga`) | ✅ |
| PUBL-02 | 04-03 t2, 04-05 t2 | SSR check 4b (`?page=2`), UAT 7; expand covered by UAT 9b | ✅ (W-04) |
| PUBL-03 | 04-03 t3, 04-04 t2 | SSR check 6 (no `contact_email`; deep links) | ⚠️ B-04 |
| PUBL-04 | 04-04 t1/t2 | reveal contract + UAT 8 | ✅ |
| PUBL-06 | 04-03/04-04 responsive classes | UAT 5 (390/1024/1280) | ✅ |
| SRCH-01 | 04-02 t1/t2, 04-05 t1 | `pytest tests/test_public_search.py` | ✅ |
| SRCH-02 | 04-02 t2, 04-05 t1 | pytest city matrix + SSR check 7 | ✅ (B-01 fixed) |
| SRCH-03 | 04-02 t2, 04-05 t1 | pytest sort/tie-break + SSR check 7 | ✅ (B-02 fixed) |
| UIUX-01 | 04-01 t2, 04-06 t1/t2 | contrast UAT 13; BOM/probe checks | ✅ |
| UIUX-02 | 04-01 t2/t3, 04-06 t2 | UAT 11, 14 (hover-only) | ✅ |
| UIUX-03 | 04-06 t1 | SSR check 1 (`Espaco publicitario` x >= 3) | ✅ |

All 11 requirements have at least one delivering task and at least one proof path. The only failing proof path is the malformed deep-link branch in `PUBL-03`.

---

## Contract Checks

- **List contract:** `04-02` accepts `q` (max 80), `city` (max 40; slug, canonical, or accented label), `sort` (max 20; only `antigas` changes order), `page >= 1`, `limit <= 50`. The frontend sends `q`, city **slug**, `sort`, `page`, `limit=24`. `JobListResponse {items,page,limit,total}` and `JobPublic` match the frontend types.
- **Reveal contract:** `POST /api/v1/public/jobs/{jobId}/reveal-contact` with `{cf_token}`; 200 returns `{job_id, contact_email, contact_phone}`. `RevealContact` uses that shape and does not persist contact values.
- **CORS:** `main.py` has `allow_origins=settings.cors_origins_list`; `config.py` default `CORS_ORIGINS="http://localhost:3000"`; `.env` has no override. The new test uses a real `GET`, not `OPTIONS`.
- **Valid deep link:** a valid UUID absent from the current page is resolved via `fetchJob`; `initialJob` seeds the dialog state, so the dialog markup is in SSR HTML. This resolves the valid half of the original B-04.
- **Invalid deep link:** a valid-but-missing UUID reaches the panel (`filters.vaga` present, `initialJob === null`). A **malformed** value does not (B-04).

---

## Revision Gate

Loop **2 of 3**. One blocker remains. The fix is localized to the `vaga` parsing/validation boundary in `04-03`/`04-04`; no re-architecture is needed. If loop 3 still leaves the malformed path broken, escalate to the user with B-04 rather than executing a phase gate that cannot pass.
