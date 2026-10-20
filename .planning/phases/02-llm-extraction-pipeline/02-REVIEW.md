---
phase: 02-llm-extraction-pipeline
reviewed: 2026-10-20T23:12:15Z
depth: standard
files_reviewed: 24
files_reviewed_list:
  - backend/.env.example
  - backend/alembic/versions/0002_jobs_source_snippet.py
  - backend/app/api/v1/extract.py
  - backend/app/api/v1/router.py
  - backend/app/core/config.py
  - backend/app/crud/jobs.py
  - backend/app/models/job.py
  - backend/app/schemas/extract.py
  - backend/app/services/extraction/chunking.py
  - backend/app/services/extraction/client.py
  - backend/app/services/extraction/extractor.py
  - backend/app/services/extraction/grounding.py
  - backend/app/services/extraction/phones.py
  - backend/app/services/extraction/schema.py
  - backend/pyproject.toml
  - backend/tests/test_extract_api.py
  - backend/tests/test_extraction_core.py
  - backend/tests/test_extractor.py
  - backend/uv.lock
  - frontend/.env.local.example
  - frontend/app/admin/paste/ExtractForm.tsx
  - frontend/app/admin/paste/globals-admin.css
  - frontend/app/admin/paste/page.tsx
  - frontend/lib/api.ts
findings:
  critical: 1
  warning: 4
  info: 8
  total: 13
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-10-20T23:12:15Z
**Depth:** standard
**Files Reviewed:** 24
**Status:** issues_found

## Summary

Reviewed the full LLM extraction pipeline (chunking → Groq strict structured outputs with 429/fallback handling → grounding/classification → single-transaction persistence), the JWT admin gate, and the Next.js admin paste page. The overall architecture is sound: the JWT chain pins HS256 and validates `sub`/`role`; the Groq client has bounded 429 retries with `retry-after`, a dead-model fallback chain, and a schema-repair turn; persistence is genuinely all-or-nothing with rollback; grounding + strict JSON schema substantially blunt hallucination and prompt-injection.

The critical gap is at the boundary between LLM output and the database: **nothing normalizes or validates the Pydantic-extracted rows against the DB constraints/column widths before insert**, so a single imperfect row from the model (notably an empty-string `contact_email`, which strict mode happily emits) violates the `at_least_one_contact` check constraint and fails the *entire* batch with a 500 — after the Groq cost has already been paid. The same class of problem (over-long strings) causes the identical total-failure mode. Also notable: the carefully crafted pt-BR `ExtractionAPIError` messages never reach the admin (no handler → generic 500), phone grounding rejects valid contacts when the LLM adds the `+55` country code, and the EXTR-08 delimiter mitigation can be broken by a `</TEXTO_FONTE>` embedded in pasted content. `uv.lock` presence noted; content not reviewed per scope.

## Critical Issues

### CR-01: Empty-string `contact_email` bypasses D-05 discard and violates the DB check constraint, failing the whole batch with a 500

**File:** `backend/app/services/extraction/extractor.py:171-185` (also `backend/app/models/job.py:72-76`, `backend/app/api/v1/extract.py:103-112`)
**Issue:** The strict JSON schema (`schema.py:39`) allows `contact_email: ""` (any string is valid; empty included), and LLMs in JSON mode routinely emit `""` for empty optional fields. In `_process_row`:

```python
contact_email = row.contact_email          # "" stays ""
if contact_email and not is_grounded(...):  # falsy → skipped, stays ""
    contact_email = None
...
if contact_email is None and contact_phone is None:   # "" is not None → passes!
    return None, CandidateOutcome.discard, "sem contato válido"
```

A row with `contact_email: ""` and no phone is kept as a candidate and sent to persistence. The Job model's `at_least_one_contact` CheckConstraint (`job.py:72-76`) requires a non-blank email OR non-blank phone — `""` satisfies neither, so `session.flush()`/`commit()` raises IntegrityError, `extract.py:107-112` rolls back, and the admin gets 500 "Falha ao salvar — nada foi gravado" for the *entire* extraction. The Groq calls were already paid for; one bad row poisons all rows. This contradicts D-05 ("only missing title or absence of BOTH contacts discards a row") — an empty string IS absence of contact and should discard, not crash.

**Fix:**
```python
# extractor.py, in _process_row, right after the title checks:
contact_email = (row.contact_email or "").strip() or None
if contact_email and not is_grounded(contact_email, haystack):
    contact_email = None
```
(`normalize_phone` already returns `None` for `""`, so the phone side is safe.) Add a regression test: `clean_row(contact_email="", contact_phone=None)` must be discarded with "sem contato válido", not persisted.

## Warnings

### WR-01: No length/blank validation between LLM output and DB column widths — one over-long field fails the whole transaction

**File:** `backend/app/schemas/extract.py:62-75` (vs `backend/app/models/job.py:34-42`)
**Issue:** `ExtractedJobRaw` imposes no `max_length`, but the DB columns are `String(200)` (title), `String(150)` (company), `String(80)` (salary), `String(255)` (benefits), `String(80)` (city), `String(254)` (email). Postgres raises `StringDataRightTruncation` on insert; as in CR-01 this aborts the entire single-transaction batch (extract.py:103-112 → 500, "nada foi gravado"). Informal WhatsApp job posts produce long titles/salary strings often enough that this will happen in production. Additionally, `city: ""` (schema allows any string) sails through with only a `needs_review` flag and is persisted as an empty non-null city — no DB or app check rejects it.
**Fix:** Add `max_length` to `ExtractedJobRaw` fields matching the column widths (Pydantic will then force the repair path on oversize output), or truncate defensively in `_process_row`. Treat `city=""` as missing (`needs_review` with the raw value, or discard if policy requires a city). E.g.:
```python
title: str = Field(max_length=200)
company: str | None = Field(default=None, max_length=150)
salary: str | None = Field(default=None, max_length=80)
benefits: str | None = Field(default=None, max_length=255)
city: str = Field(max_length=80)
```

### WR-02: `ExtractionAPIError` is never caught by the endpoint — curated pt-BR errors become a generic HTTP 500

**File:** `backend/app/api/v1/extract.py:74-83` (raised from `backend/app/services/extraction/client.py:64-70, 227-261, 337-342`)
**Issue:** The client raises `ExtractionAPIError` with detailed pt-BR guidance ("Limite de taxa do Groq atingido (429)…", "Falha de conexão…", "Todos os modelos falharam — verifique GROQ_MODEL…"). The endpoint only catches `TimeoutError` (→504) and `ValueError` (→422); `main.py` registers no exception handler. FastAPI's default 500 returns only "Internal Server Error", so the frontend (`lib/api.ts:58-69`) shows `Erro 500` and every carefully written admin-facing message is lost — precisely when the admin most needs it (rate limit vs dead model vs bad key).
**Fix:**
```python
from app.services.extraction.client import ExtractionAPIError
...
    except ExtractionAPIError as exc:
        raise HTTPException(status_code=503, detail=exc.detail) from exc
```
Place it next to the existing `except ValueError` block (503 is appropriate for upstream unavailability; 502 also defensible).

### WR-03: Phone grounding rejects valid contacts when the LLM expands the number with the `+55` country code

**File:** `backend/app/services/extraction/extractor.py:175-182`
**Issue:** Grounding for a normalized phone checks `is_grounded("+5511912345678", haystack)` — but the source chunk contains only what humans wrote, e.g. `(11) 91234-5678`, whose normalized form is `11912345678` (no `+55`). The digit fallback then checks `raw_digits = _digits(row.contact_phone)` — the digits of the *LLM's* string, i.e. `5511912345678` — against `chunk_digits`; that substring is absent because the source never wrote the country code. Result: a perfectly real contact is cleared, and if there is no email the job is **discarded** as "sem contato válido". The system prompt asks for verbatim contacts, but models frequently canonicalize phone formats anyway, so this will silently drop valid jobs. (Weaker inverse risk: `chunk_digits` is the whole chunk's digit run with no separators, so a fabricated number whose digits straddle the seam of two adjacent numbers can also pass.)
**Fix:** Also test the national portion (digits after the `+55` prefix) against the chunk digits:
```python
if contact_phone is not None:
    raw_digits = _digits(row.contact_phone)
    national = contact_phone[3:]  # strip "+55"
    grounded = (
        is_grounded(contact_phone, haystack)
        or (bool(raw_digits) and raw_digits in chunk_digits)
        or (len(national) >= 10 and national in chunk_digits)
    )
```

### WR-04: EXTR-08 prompt-injection mitigation breaks if the pasted text contains the closing delimiter

**File:** `backend/app/services/extraction/client.py:102-113` (delimiters from `schema.py:21-22`)
**Issue:** The untrusted text is wrapped verbatim: `f"{START_DELIM}\n{text}\n{END_DELIM}\n\n{INSTRUCTION_NOTE}"`. Content sourced from third-party WhatsApp/Telegram groups (treated as untrusted in the project's own threat model) may itself contain `</TEXTO_FONTE>`, which closes the data region early; everything after it in the paste is then positioned as prompt content following the "isto é dado bruto" note, i.e. free to be read as instructions. Blast radius is bounded (strict schema blocks new fields; grounding discards rows whose title/contacts are absent from the chunk) — but a malicious ad can still sabotage extraction of *other* ads in the same chunk, and because grounding is chunk-level, a phone number physically present in the attacker's own text will pass grounding even if attached to another employer's row (wrong-contact scam vector). The `test_prompt_injection_paste_produces_no_rogue_row` test doesn't exercise the breakout (it uses a scripted model).
**Fix:** Neutralize the delimiters in the input before wrapping, e.g.:
```python
def _sanitize_delims(text: str) -> str:
    return text.replace(START_DELIM, "<TEXTO>").replace(END_DELIM, "</TEXTO>")
```
and wrap the sanitized text. Document that grounding is chunk-level, so cross-row contact contamination within a chunk remains possible (a per-row anchoring pass would be the deeper fix, if ever needed).

## Info

### IN-01: `estimate_job_count` accepts a `sleep` parameter it never uses

**File:** `backend/app/services/extraction/extractor.py:236`
**Issue:** `sleep: Callable[...] = asyncio.sleep` is declared and forwarded by `extract_jobs` (line 323) but never referenced in the function body (lines 245–289) — the count call is made without pacing or retry sleeps. Misleading seam: a reader (or future edit) will assume pacing applies here.
**Fix:** Remove the parameter, or document why the pre-pass call needs no pacing.

### IN-02: A new `AsyncGroq` client (and httpx pool) is constructed per chunk and never closed

**File:** `backend/app/services/extraction/extractor.py:247, 336-338`; `backend/app/services/extraction/client.py:287-288`
**Issue:** With the production path (`client=None`), each `call_extraction` call builds a fresh `AsyncGroq` (its own connection pool), and `estimate_job_count` builds another. None are closed; on `asyncio.timeout` cancellation the in-flight client is abandoned mid-request. Correctness impact is minor (GC reclaims them; the request-scoped 504 still works), but it defeats connection reuse across chunks and leaks sockets under repeated admin use.
**Fix:** Build the client once in `extract_jobs` when `client is None` and pass it down:
```python
if client is None:
    client = _build_real_client(settings)
```
(`_build_real_client` is already imported locally in `estimate_job_count`.)

### IN-03: Dead landline validation and doc/code mismatch in `normalize_phone`

**File:** `backend/app/services/extraction/phones.py:54-58`
**Issue:** After the digits-only check, `local[0].isdigit()` is always true, so the `return None` inside that branch is unreachable. The comment claims landline first digit "2–5 in real BR numbering; accept 2–9", but the code accepts `0` and `1` as well (e.g. DDD 11 + `0345-6789`). Harmless (permissive), but the dead branch and stale comment will mislead the next maintainer.
**Fix:** Either enforce the documented policy (`if local[0] not in "23456789": return None`) or simplify to just the length check and fix the comment.

### IN-04: `EXTRACT_MAX_JOBS` overflow accounting is off by one and the dropped raw row is lost

**File:** `backend/app/services/extraction/extractor.py:362-385`
**Issue:** When `len(kept) >= cap`, `kept` is trimmed to `cap - 1` to make room for the overflow marker entry, so one extra real row is dropped beyond the reported count (`"{overflow} linha(s) descartada(s)"` under-counts by 1); in that branch `dropped_rows` is empty, so the marker's `raw` payload is `{}`. The invariant `len(kept)+len(discarded) <= cap` does hold (verified for several kept/discarded combinations), so this is a reporting nit, not a cap breach.
**Fix:** When `len(kept) >= cap`, keep the last kept row's `model_dump()` as `first_dropped` and report `overflow + 1`, or restructure so the marker does not consume a slot (e.g., allow `cap` real rows and treat the marker as metadata outside the cap).

### IN-05: `model_used` reports only the first successful chunk's model

**File:** `backend/app/services/extraction/extractor.py:341-342`
**Issue:** `if not model_used: model_used = raw.model_used` keeps the model from the first chunk only. With multi-chunk pastes where the primary dies mid-run (dead-model chain), later chunks run on the fallback but the summary still claims the first model. Cosmetic observability issue for the admin.
**Fix:** Acceptable as-is for v1; if desired, report the distinct set of models used.

### IN-06: `updated_at` never updates — no `onupdate` and no trigger

**File:** `backend/app/models/job.py:56-60`
**Issue:** `updated_at` has only a `server_default=now()`; nothing sets it on UPDATE (no SQLAlchemy `onupdate`, no DB trigger in migrations). It permanently equals `created_at`, which will mislead the Phase 5 review/edit flow.
**Fix:** `mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=text("now()"))`.

### IN-07: `passlib[bcrypt]` declared but unused — code imports `bcrypt` directly

**File:** `backend/pyproject.toml:15` (vs `backend/app/core/security.py:21`)
**Issue:** `security.py` deliberately uses the `bcrypt` library directly (documented deviation from passlib 1.7.4 incompatibility), but `pyproject.toml` still declares `passlib[bcrypt]>=1.7.4` and does not declare `bcrypt` itself. The working import currently rides on a transitive dependency; a lockfile/dependency cleanup could silently break auth.
**Fix:** Replace `"passlib[bcrypt]>=1.7.4,<2.0.0"` with an explicit `"bcrypt>=4.0,<6.0"` (matching the pinned bcrypt 5.x in the lockfile).

### IN-08: Admin form is a dead end once the stored token expires — no logout/re-login path

**File:** `frontend/app/admin/paste/ExtractForm.tsx:76-92` (token at 17-26, 35-39)
**Issue:** The login form renders only when `!token`; the token is read from `sessionStorage` on mount and never cleared. After the 12h JWT expiry, every extract request 401s ("Não autenticado") and the UI offers no way back to the login form except manually clearing sessionStorage (or closing the tab, which drops sessionStorage). Minor, but a guaranteed functional dead-end on long-lived admin sessions.
**Fix:** On a 401 from `extractJobs`, clear the stored token and re-render the login form (e.g., in `handleSubmit`'s catch, check for "Não autenticado"/401 and call `setToken(null)` + `sessionStorage.removeItem(TOKEN_KEY)`), or add a "Sair" button.

---

_Reviewed: 2026-10-20T23:12:15Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
