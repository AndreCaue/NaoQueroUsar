---
phase: 02-llm-extraction-pipeline
verified: 2026-10-20T23:23:43Z
status: gaps_found
score: 3/5 must-haves verified
overrides_applied: 0
gaps:
  - truth: "SC1 — Colar um texto com múltiplas vagas gera lista estruturada e cada vaga entra no banco com status pending; só é criada se tiver ao menos um contato"
    status: failed
    reason: "The contact gate is bypassed for empty-string contacts (CR-01, independently reproduced): the strict JSON schema allows contact_email:\"\" and _process_row only clears/None-checks grounded values, so a row with contact_email=\"\" and no phone is KEPT and sent to persistence. The DB at_least_one_contact CHECK rejects the blank contact, the single transaction rolls back, and the admin gets a 500 \"nada foi gravado\" for the ENTIRE batch — one common LLM output pattern (JSON-mode models routinely emit \"\" for empty fields) destroys every extracted row after the Groq cost is paid. This directly contradicts SC1's \"só é criada se tiver ao menos um contato\" and the phase goal's atomic multi-vaga flow."
    artifacts:
      - path: "backend/app/services/extraction/extractor.py"
        issue: "Lines 171-185: contact_email = row.contact_email keeps \"\"; the discard check `if contact_email is None and contact_phone is None` never triggers for \"\". Verified live: _process_row(ExtractedJobRaw(contact_email=\"\", contact_phone=None), ...) returns CandidateOutcome.save_needs_review with contact_email=\"\" preserved."
      - path: "backend/app/models/job.py"
        issue: "at_least_one_contact CHECK (line ~75) rejects the blank contact at flush/commit, converting a per-row defect into a whole-batch failure (extract.py:103-112 rollback → 500)."
    missing:
      - "In _process_row: contact_email = (row.contact_email or \"\").strip() or None BEFORE the grounding check (normalize_phone already returns None for \"\"), so a blank-string contact is treated as absence and the row is discarded with \"sem contato válido\" per D-05."
      - "Regression test: clean_row(contact_email=\"\", contact_phone=None) must be discarded, not persisted."
  - truth: "SC5 — O modelo é configurável via GROQ_MODEL com cadeia de fallback e erro claro (nunca hardcoded)"
    status: failed
    reason: "Partial failure (WR-02): the never-hardcoded model chain, fallback and the curated pt-BR ExtractionAPIError (naming GROQ_MODEL, \"limite de taxa\", etc.) are fully implemented and unit-tested at the client layer — but backend/app/api/v1/extract.py catches ONLY TimeoutError (504) and ValueError (422). ExtractionAPIError propagates unhandled and FastAPI returns a generic 500 \"Internal Server Error\", so the admin never sees the clear pt-BR error the success criterion requires — precisely on model failure, the moment it matters most."
    artifacts:
      - path: "backend/app/api/v1/extract.py"
        issue: "Lines 74-83: no `except ExtractionAPIError` handler; client.py raises detailed errors (lines 227-232, 245-250, 293-296, 337-341) that die at the HTTP boundary."
    missing:
      - "Catch ExtractionAPIError in the endpoint and surface exc.detail as HTTPException 503 (or 502) — one except-arm next to the existing ValueError handler, plus a test asserting the detail reaches the response."
  - truth: "SC1 (partial) — sem vagas perdidas: real jobs with real contacts must survive extraction"
    status: partial
    reason: "WR-03 independently reproduced: when the LLM canonicalizes a phone by adding the +55 country code (common model behavior despite the \"verbatim\" prompt instruction), phone grounding fails. Verified live: source \"(11) 91234-5678\" + LLM row contact_phone=\"+5511912345678\" → _process_row discards the row as \"sem contato válido\". Grounding checks is_grounded(\"+5511912345678\") and the raw digits of the LLM's string (\"5511912345678\") against the chunk digit-run — the national portion is never tried. A real job with a real contact is silently lost, contradicting the phase goal \"sem vagas perdidas\"."
    artifacts:
      - path: "backend/app/services/extraction/extractor.py"
        issue: "Lines 175-182: grounding of normalized phone lacks a national-portion fallback (digits after the +55 prefix against chunk_digits)."
    missing:
      - "Add a third grounding branch: len(national := contact_phone[3:]) >= 10 and national in chunk_digits."
      - "Test: LLM-expanded +55 phone against a source containing the national number must keep the row (save, phone as +55E.164)."
deferred: []
---

# Phase 02: LLM Extraction Pipeline — Verification Report

**Phase Goal:** O admin cola um texto bruto com várias vagas e obtém cards estruturados com status `pending`, sem vagas perdidas nem campos inventados.
**Verified:** 2026-10-20T23:23:43Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Truths are the five ROADMAP Success Criteria (the roadmap contract), merged with PLAN frontmatter must-haves (plans 02-01..02-04).

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1 — paste with multiple vagas → structured list, each row into DB as `pending`; created only if ≥1 contact | ✗ FAILED | Pipeline, endpoint, persistence and pending/needs_review mapping all exist and are tested (104-suite green; API tests assert DB rows with status pending + source_snippet; human live smoke approved). BUT CR-01 reproduced live: `contact_email=""` (routine JSON-mode LLM output) passes the extractor's contact gate and hits the DB CHECK → whole batch rolls back with 500. The contact rule is not correctly enforced and multi-vaga pastes can lose EVERYTHING, not just the bad row (see gap 1) |
| 2 | SC2 — schema/grounding failures → needs_review/invalid instead of invented data | ✓ VERIFIED | Strict `EXTRACTION_JSON_SCHEMA` (all required, additionalProperties:false, nullable unions) + Pydantic `extra="forbid"`; grounding discards ungrounded title ("título não encontrado no texto-fonte"), clears ungrounded contacts, clears+flags minor fields (extractor.py:160-227); no `published` status ever assigned by this phase; tests cover hallucination, cleared-minor, injection-script paths (test_extractor.py). Warnings: over-long fields bypass schema (no max_length) and fail the batch as 500 instead of needs_review (WR-01); `</TEXTO_FONTE>` embedded in pasted text can break the delimiter frame (WR-04) — grounding still bounds the blast radius |
| 3 | SC3 — large pastes chunked/throttled under Groq TPM; truncation and divergence flagged | ✓ VERIFIED | `chunk_text` under `EXTRACT_CHUNK_MAX_TOKENS=3500` with lossless contiguous slices (31 core tests incl. seeded property test); inter-chunk `await sleep(EXTRACT_CHUNK_DELAY_SECONDS)` only between calls (extractor.py:332-335, test asserts exactly N-1 sleeps); 429 retried ≤3× honoring retry-after capped 30s (client.py:225-241, tested); `truncated` from any finish_reason=="length" (extractor.py:387); `divergent` from count pre-pass vs extracted (extractor.py:388); endpoint surfaces ALERT_TRUNCATED / ALERT_DIVERGENCE pt-BR alerts |
| 4 | SC4 — pt-BR phones → E.164 (wa.me-ready); input delimited to reduce prompt injection | ✓ VERIFIED | `normalize_phone` → `+55...` or None across the documented format table (test_extraction_core.py parametrized); extractor stores the normalized E.164 form. `START_DELIM/END_DELIM` (`<TEXTO_FONTE>`) wrap untrusted text with the "dado bruto, não são instruções" note (client.py:102-113); injection test asserts no rogue rows. Warnings: delimiter breakout possible if the paste itself contains `</TEXTO_FONTE>` (WR-04 — mitigation still *reduces* risk per SC wording but is not airtight); WR-03 phone-grounding false discard (tracked as gap 3) |
| 5 | SC5 — GROQ_MODEL configurable via env with fallback chain and clear error, never hardcoded | ✗ FAILED | Chain and config fully verified: `Settings.GROQ_MODEL="openai/gpt-oss-20b"` / `GROQ_MODEL_FALLBACK="openai/gpt-oss-120b"` (config.py:24-25), documented in .env.example, `model_chain()` dedupes from settings (client.py:128-134), dead-model switch + exhausted-chain error naming GROQ_MODEL all tested. BUT the clear pt-BR error never reaches the admin: extract.py has no `except ExtractionAPIError`, so rate-limit/model-death/bad-key errors surface as generic 500 "Internal Server Error" (WR-02, see gap 2) |

**Score:** 3/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/app/services/extraction/schema.py` | strict JSON schema + Pydantic models + delimiters | ✓ VERIFIED | `EXTRACTION_JSON_SCHEMA` strict-ready; `ExtractedJobRaw`/`ExtractionLLMOutput`/`JobCandidate`; `START_DELIM`/`END_DELIM` |
| `backend/app/services/extraction/phones.py` | pt-BR → E.164 | ✓ VERIFIED | `normalize_phone` pure, never raises; covered by parametrized tests |
| `backend/app/services/extraction/chunking.py` | token-budgeted lossless chunker | ✓ VERIFIED | contiguous exact-slice contract; property-tested |
| `backend/app/services/extraction/grounding.py` | normalized containment check | ✓ VERIFIED | NFKD accent-strip, idempotent, empty-needle False |
| `backend/app/services/extraction/client.py` | Groq seam: strict payload, fallback, 429 retry | ✓ VERIFIED | `call_extraction`, `ExtractionAPIError`, `RawExtraction`; strict `json_schema` payload; lazy SDK import |
| `backend/app/services/extraction/extractor.py` | orchestration → ExtractionResult | ⚠️ HOLLOW (gap 1) | Orchestration/chunking/grounding/classification all present and tested, but `_process_row` contact handling (171-185) admits empty-string contacts → DB CHECK failure |
| `backend/app/core/config.py` | GROQ_* + EXTRACT_* settings | ✓ VERIFIED | All 9 fields with exact plan defaults |
| `backend/.env.example` | documented vars | ✓ VERIFIED | Full `# --- Groq / Extração (Phase 2) ---` section |
| `backend/alembic/versions/0002_jobs_source_snippet.py` | source_snippet column migration | ✓ VERIFIED | revision `0002_jobs_source_snippet`, down_revision `0001_initial_jobs`, add/drop column confirmed |
| `backend/app/models/job.py` | `source_snippet` on Job | ✓ VERIFIED | Line 50, Text nullable; `at_least_one_contact` CHECK present |
| `backend/app/schemas/extract.py` | ExtractRequest/ExtractSummaryResponse/DiscardedJob + ALERT_* | ✓ VERIFIED | Contract per plan; alerts wired into endpoint |
| `backend/app/crud/jobs.py` | `bulk_create_pending` flush-only single-transaction | ✓ VERIFIED | add+flush, no commit; caller commits once (D-03) |
| `backend/app/api/v1/extract.py` | JWT-protected sync endpoint | ⚠️ PARTIAL | Auth (require_admin), 503/413/422/504 mapping, atomic commit/rollback, alerts all present; missing `ExtractionAPIError` handler (gap 2) |
| `backend/app/api/v1/router.py` | mount extract router | ✓ VERIFIED | `from app.api.v1 import ... extract` + `include_router(extract.router)` |
| `frontend/lib/api.ts` | typed loginAdmin/extractJobs on NEXT_PUBLIC_API_URL | ✓ VERIFIED | Lines 19/21/48; ExtractSummary interface mirrors backend |
| `frontend/app/admin/paste/page.tsx` + `ExtractForm.tsx` + `globals-admin.css` | minimal dark admin page | ✓ VERIFIED | All exist; `npm run build` exits 0 (re-run here); dark theme vars; login→paste→summary flow; no Tailwind, no secrets |
| `backend/tests/test_extraction_core.py` / `test_extractor.py` / `test_extract_api.py` | unit + fake-client + API coverage | ✓ VERIFIED | All imported symbols exercised; full suite **104 passed** (re-run here, no Phase 1 regressions) |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `extractor.py` | `client.py` | `await call_extraction(...)` per chunk | ✓ WIRED | extractor.py:336-338; grep ≥2; dead_models shared |
| `extractor.py` | `schema/chunking/grounding/phones` | plan-01 contracts | ✓ WIRED | imports at lines 41-52; all consumed in `_process_row`/`extract_jobs` |
| `api/v1/extract.py` | `extractor.py` | `await extract_jobs(...)` under asyncio.timeout | ✓ WIRED | Line 76 inside `async with asyncio.timeout(...)` |
| `api/v1/extract.py` | `crud/jobs.py` | `bulk_create_pending` + one commit | ✓ WIRED | Lines 105-106; rollback path tested |
| `api/v1/router.py` | `extract.py` | `include_router(extract.router)` | ✓ WIRED | Line 9 |
| `frontend/lib/api.ts` | `/api/v1/auth/login` + `/api/v1/admin/extract` | `fetch(${NEXT_PUBLIC_API_URL}/...)` | ✓ WIRED | Both helpers build URLs from env with localhost fallback |
| `client.py` | `schema.py` | `EXTRACTION_JSON_SCHEMA` in strict payload | ✓ WIRED | strict_response_format() lines 90-99 |
| `api/v1/extract.py` | `client.py` (ExtractionAPIError) | *(expected: catch → 503)* | ✗ NOT WIRED | No import/handler — curated errors die as generic 500 (gap 2) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| ExtractForm summary | `summary` state | `extractJobs` → live FastAPI → `extract_jobs` → Groq (real DB persistence of kept rows) | Yes — human live smoke observed real Groq extraction + DB rows with status/source_snippet | ✓ FLOWING (human-approved 2026-10-20) |
| Endpoint response | `result.kept` / `result.discarded` | Groq strict-mode rows → grounding/classification | Yes — FakeGroq-proven plumbing; no static/hardcoded returns; discarded never persisted | ✓ FLOWING |
| Extractor → DB | `rows` list | `result.kept` mapped to Job kwargs incl. status + source_snippet | Yes — real single-transaction insert; rollback path tested | ✓ FLOWING |
| `estimate_job_count` | `detected_count` | Live Groq `{"count": n}` pre-pass (multi-chunk only) | Yes — real call, best-effort None on failure (tested) | ✓ FLOWING |

Note: the end-to-end data source is the real Groq API, which cannot be exercised by the verifier. The live human smoke (plan 02-04 task 2, approved 2026-10-20) observed real extraction producing DB rows; all intermediate plumbing is proven by the FakeGroq test harness.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full backend suite | `python -m pytest backend/tests -q` | **104 passed**, 1 warning (SAWarning in rollback test) | ✓ PASS |
| CR-01 reproduction: empty-string contact | `_process_row(row with contact_email="", contact_phone=None)` | Kept as `save_needs_review`, `contact_email=""` preserved → will hit DB CHECK | ✗ FAIL (gap 1) |
| Both-blank-strings contact | `_process_row(row with email="", phone="")` | Kept as `save_needs_review` | ✗ FAIL (gap 1) |
| WR-03 reproduction: +55-expanded phone | `_process_row` with source `(11) 91234-5678`, LLM `+5511912345678` | Discarded "sem contato válido" — real contact lost | ✗ FAIL (gap 3) |
| Env config wiring | grep config.py/.env.example | All GROQ_*/EXTRACT_* present with plan defaults | ✓ PASS |
| Router mounting | grep router.py | `extract` imported + `include_router` | ✓ PASS |
| Migration chain | grep 0002 migration | revision `0002_jobs_source_snippet`, down → `0001_initial_jobs`, add/drop source_snippet | ✓ PASS |
| Public payload leak-safe | grep schemas/job.py | No contact/source_snippet in JobPublic (Phase 1 guarantee intact) | ✓ PASS |
| Frontend build | `npm run build` (frontend/) | Exit 0, static prerender emitted | ✓ PASS |
| Frontend seam | grep lib/api.ts | `NEXT_PUBLIC_API_URL`, `loginAdmin`, `extractJobs` present | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| EXTR-01 | 02-03, 02-04 | Admin cola texto grande com várias vagas de uma só vez | ✓ SATISFIED | Byte-capped sync endpoint + /admin/paste UI + approved live smoke; robustness caveat: CR-01 can fail whole batches (tracked as gap 1) |
| EXTR-02 | 02-02 | LLM extrai campos de cada vaga em lista estruturada | ✓ SATISFIED | `extract_jobs` → `ExtractionResult`; strict structured outputs; FakeGroq happy-path + multi-chunk tests |
| EXTR-03 | 02-01, 02-02 | Schema estrito com validação; saídas inválidas → needs_review/invalid | ⚠️ PARTIAL | Strict schema + Pydantic + repair turn + grounding→needs_review/discard all exist. But two invalid-output classes escape the design: blank-string contact (gap 1 → 500, not discard) and over-long fields (WR-01 → 500, not needs_review) |
| EXTR-04 | 02-02 | Chunking e throttling para respeitar limites do Groq | ✓ SATISFIED | Token-budgeted chunks, inter-chunk delay, retry-after-honoring 429 backoff, dead-model switch — all tested |
| EXTR-05 | 02-01 | Telefones pt-BR normalizados (E.164) para wa.me | ✓ SATISFIED | `normalize_phone` table-tested; normalized value persisted |
| EXTR-06 | 02-03 | Cada vaga extraída entra no banco com status pending | ✓ SATISFIED | `save→pending`, `save_needs_review→needs_review` mapping; API test asserts DB row status pending + source_snippet |
| EXTR-07 | 02-03 | Vaga só é criada se tiver ao menos um contato | ✗ BLOCKED | Rule implemented (extractor discard + DB CHECK) but broken for empty-string contacts (gap 1, CR-01 reproduced): instead of discarding, the batch crashes. The gate does not hold for the most common LLM empty-field pattern |
| EXTR-08 | 02-01 | Texto de entrada delimitado para reduzir prompt injection | ✓ SATISFIED | `<TEXTO_FONTE>` delimiters + data-only instruction + strict schema + injection test. Warning: breakout possible if paste contains the closing delimiter (WR-04) — mitigation reduces but does not eliminate the risk |
| EXTR-09 | 02-02 | Detecta truncamento (finish_reason) e divergência detectadas vs extraídas | ✓ SATISFIED | `truncated`/`divergent` flags + count pre-pass (multi-chunk) + tested + surfaced as pt-BR alerts |

No orphaned requirements: REQUIREMENTS.md maps exactly EXTR-01..09 to Phase 2; all nine appear in plan frontmatter (02-01: EXTR-03/05/08; 02-02: EXTR-02/03/04/09; 02-03: EXTR-01/06/07; 02-04: EXTR-01).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `extractor.py` | 171-185 | Empty-string contact not normalized → DB CHECK → whole-batch 500 (CR-01, reproduced) | 🛑 Blocker | Breaks SC1/EXTR-07; one bad row destroys all rows of the extraction |
| `api/v1/extract.py` | 74-83 | `ExtractionAPIError` never caught → curated pt-BR errors become generic 500 (WR-02) | ⚠️ Warning | SC5 "erro claro" not observable end-to-end; admin sees "Internal Server Error" on rate-limit/model failure |
| `extractor.py` | 175-182 | Phone grounding lacks national-portion fallback → +55-expanded valid contacts discarded (WR-03, reproduced) | ⚠️ Warning | Real jobs with real contacts silently lost — contradicts "sem vagas perdidas" |
| `schema.py` | 62-75 | No `max_length` on ExtractedJobRaw fields vs DB String(200/150/80/255/254) (WR-01) | ⚠️ Warning | Over-long LLM output → StringDataRightTruncation → whole-batch 500; `city=""` persisted as empty non-null |
| `client.py` | 108 | Verbatim wrap of pasted text; pasted `</TEXTO_FONTE>` breaks the data frame (WR-04) | ⚠️ Warning | Prompt-injection mitigation weakened for adversarial pastes; grounding bounds but does not eliminate cross-row contact contamination within a chunk |
| `extractor.py` | 236 | `estimate_job_count` accepts unused `sleep` param (IN-01) | ℹ️ Info | Misleading seam |
| `extractor.py` | 247, 336 | New AsyncGroq client per chunk, never closed (IN-02) | ℹ️ Info | Socket/pool leak under repeated admin use |
| `phones.py` | 54-58 | Dead landline branch, stale comment (IN-03) | ℹ️ Info | Maintainer confusion only |
| `extractor.py` | 362-385 | MAX_JOBS overflow off-by-one reporting, empty raw payload (IN-04) | ℹ️ Info | Reporting nit; cap invariant holds |
| `models/job.py` | 56-60 | `updated_at` has no `onupdate` (IN-06) | ℹ️ Info | Will mislead Phase 5 edit flow |
| `pyproject.toml` | 15 | passlib declared but bcrypt used directly (IN-07, also Phase 1 finding) | ℹ️ Info | Latent dependency break |

No TODO/FIXME/placeholder stubs; no console.log-only implementations; no hardcoded-empty data flowing to rendering. The `str | None = None` Pydantic defaults mirror the strict schema's required-nullable contract (intentional, not stubs).

### Independent Assessment of the Review Findings

The 02-REVIEW.md findings were **not taken at face value** — CR-01 and WR-03 were reproduced live against the installed venv (see Spot-Checks), and WR-02/WR-04 were confirmed by direct code reading of the exact lines cited. All four are real. Classification against the phase must-haves:

- **CR-01 → BLOCKER (gap 1).** Directly falsifies SC1's contact gate and EXTR-07. It is not deferred anywhere: no later phase touches the extractor. The fix is two lines plus a regression test.
- **WR-02 → gap 2 (SC5 partial).** The client-layer error contract is fully implemented and tested; only the HTTP surfacing arm is missing. Small fix, high observability impact.
- **WR-03 → gap 3 (partial, "sem vagas perdidas").** Model-behavior-dependent but common enough (models canonicalize phone formats routinely) to count against the phase goal's explicit "sem vagas perdidas" wording.
- **WR-01 (over-length fields) and WR-04 (delimiter breakout)** are genuine robustness weaknesses recorded as warnings; neither falsifies a roadmap truth on its own (SC2's "não publicar inventados" still holds — grounding and the discard/needs_review machinery work for the tested classes; nothing is ever auto-published in this phase). Recommended to fix alongside gap 1 since they share the persistence-boundary root cause.
- The 8 Info findings do not affect any must-have.

### Human Verification Required (post-fix)

The plan-02-04 live smoke (login → paste → real Groq extraction → summary → DB rows with status/source_snippet) was human-approved on 2026-10-20 and stands as the end-to-end evidence for SC1's happy path. After the gaps are closed, re-run:

#### 1. Live re-smoke with an empty-contact paste

**Test:** Via `/admin/paste` (or curl with JWT), extract a paste where one vaga has NO contact and another has a normal one.
**Expected:** 200 summary: the contact-less vaga appears in `discarded` with "sem contato válido"; the other is saved `pending`; NO 500.
**Why human:** Requires a live GROQ_API_KEY and running backend; the verifier cannot call Groq.

#### 2. Live model-failure error surfacing

**Test:** Temporarily set `GROQ_MODEL` to a nonexistent model name (and fallback too), trigger an extraction.
**Expected:** A pt-BR error naming `GROQ_MODEL` in the UI (after gap 2 fix), not "Erro 500"/"Internal Server Error".
**Why human:** Needs a real Groq 400 model-not-found response.

### Gaps Summary

Three gaps block or partially block the phase goal, one root-cause family at the LLM-output→DB boundary:

1. **Contact-gate bypass (CR-01)** — empty-string `contact_email`/`contact_phone` pass `_process_row` and detonate the single transaction against the DB CHECK, losing the entire extraction. Falsifies SC1 + EXTR-07. Fix: strip-or-None before the contact gate + regression test.
2. **Error surfacing (WR-02)** — `ExtractionAPIError` is raised with excellent pt-BR detail and swallowed by the endpoint, so SC5's "erro claro" is not observable. Fix: one `except ExtractionAPIError → 503` arm + test.
3. **Phone-grounding false discard (WR-03)** — LLM-expanded `+55` phones fail grounding and real jobs are dropped, against "sem vagas perdidas". Fix: national-portion grounding branch + test.

Everything else — chunking/throttling/429 handling, strict schema + repair, grounding machinery, truncation/divergence detection, E.164 normalization, delimiters, model-chain configurability, atomic persistence, JWT gate, the admin page, and the 104-test suite — is present, substantive, wired, and (where data is dynamic) flowing. No regressions to Phase 1 guarantees (public payload still contact-free; suite fully green). The architecture is sound; the gaps are narrow, localized, and cheap to close — then this phase should pass re-verification cleanly.

---

_Verified: 2026-10-20T23:23:43Z_
_Verifier: OpenCode (gsd-verifier)_
