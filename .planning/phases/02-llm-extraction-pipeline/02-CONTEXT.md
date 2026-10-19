# Phase 2: LLM Extraction Pipeline - Context

**Gathered:** 2026-10-19
**Status:** Ready for planning
**Source:** Discuss checkpoint (02-DISCUSS-CHECKPOINT.json — 2 of 5 areas completed by user; remaining areas resolved from roadmap success criteria + REQUIREMENTS.md)

<domain>
## Phase Boundary

Backend extraction pipeline + minimal admin paste surface: the master pastes a raw multi-job text (WhatsApp/Telegram dump), the system extracts structured jobs via Groq LLM (strict schema, chunked/throttled), validates and grounds every field against the source text, classifies outcomes (saved as `pending` / `needs_review` / discarded), and saves everything in a single atomic commit — returning a pt-BR summary with divergence/truncation alerts.

NOT in this phase: public board UI (Phase 4), admin review queue UI (Phase 5), contact reveal/Turnstile (Phase 3), expiry lifecycle (Phase 6). The review workflow only stores what Phase 5 will need (notably `source_snippet` per REVW-05).

</domain>

<decisions>
## Implementation Decisions

### Ritmo do fluxo colar→extrair
- **D-01:** Síncrono com timeout — the extraction runs synchronously in the request (admin waits), with a generous timeout; no background job + polling. (User answer: "Síncrono com timeout")
- **D-02:** Salva e mostra o resumo — after extraction the jobs are saved and the response is a summary (counts + alerts), not a pre-save preview and not a bare confirmation. (User answer: "Salva e mostra o resumo")
- **D-03:** Nada salvo + erro claro + retry (commit único) — all-or-nothing persistence. If anything fails mid-extraction, NOTHING is saved; the admin gets a clear pt-BR error and can retry. Save happens as a single DB transaction after all chunks are extracted and validated. (User answer: "Nada salvo + erro claro + retry (commit único)")
- **D-04:** Endpoint + page mínima — Phase 2 delivers a JWT-protected admin endpoint AND a minimal frontend page to paste text and see the summary. The page is deliberately minimal (dark theme per project constraints); full admin review UX is Phase 5. (User answer: "Endpoint admin protegido por JWT + page mínima no frontend")

### Destino dos casos ruins
- **D-05:** Só contato/título derrubam — a candidate WITHOUT title or WITHOUT any contact (email or phone) is NOT saved at all (discarded — reported in the summary with reason + source snippet). All other defects (minor field problems, city outside the allowed set, grounding failures on non-critical fields) → saved with status `needs_review`. (User answer: "Só contato/título derrubam (não salva); defeitos menores → needs_review")
- **D-06:** Mapeia o óbvio, resto needs_review — obvious city variants map to the clean canonical city ("SP", "São Paulo/SP" → "São Paulo"; same spirit for Rio de Janeiro, Belo Horizonte, Remoto). Cities outside the allowed set {São Paulo, Rio de Janeiro, Belo Horizonte, Remoto} → status `needs_review`, preserving the raw city text in the field. (User answer: "Mapeia o óbvio ('SP', 'São Paulo/SP') → cidade limpa; fora do conjunto → needs_review com texto bruto")
- **D-07:** Divergência: salva as extraídas + alerta forte — when detected job count ≠ extracted count, the extracted jobs are still saved (as `pending`/`needs_review` per the normal rules) AND the summary carries a strong, explicit divergence alert (counts + recommendation to re-paste remainder). The whole batch is NOT failed. (User answer: "Salva as extraídas em pending + alerta forte de divergência no resumo")
- **D-08:** Descartadas no resumo com trecho-fonte — every discarded job (no title / no contact) appears in the summary with the discard reason AND its source snippet so the master can fix and re-insert manually. This implies each extraction candidate carries a source snippet; the saved jobs also persist their snippet (column added in this phase) because REVW-05 (Phase 5) requires showing the source text beside extracted fields. (User answer: "No resumo com motivo + trecho-fonte, para o admin consertar e re-inserir")

### OpenCode's Discretion
- Chunk size, inter-chunk delay values, retry/backoff counts (bounded; must respect free-tier RPM 30 / TPM 8K with safety margin)
- Exact prompt wording (must include EXTR-08 delimiters and pt-BR instructions)
- Grounding-check algorithm details (accent/case-insensitive containment; which fields are critical vs clearable)
- Timeout default and its env var name
- Exact shape of the summary response JSON (must include: saved counts by status, discarded list with reason+snippet, divergence alert, truncation flag, model used)
- How job-count detection pre-pass is implemented (cheap count call vs heuristic)
- Minimal paste page structure/UX details beyond: password/token login → textarea → button → summary display, dark theme
- Test doubles strategy for the Groq client (no live API calls in tests)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Stack & architecture
- `AGENTS.md` — fixed stack, Groq model correction (gpt-oss-20b/120b via GROQ_MODEL), theme constraints
- `.planning/research/ARCHITECTURE.md` — layered pattern: api/v1 → services (groq_extractor) → crud; `POST /admin/extract` contract sketch (line ~295); Pattern 5 (strict LLM JSON extraction with repair)
- `.planning/research/STACK.md` — library versions (groq SDK 1.7.0, Pydantic 2.14.1, httpx)

### Pitfalls (mandatory for this phase)
- `.planning/research/PITFALLS.md` — Pitfall 1 (retired models → env+fallback), Pitfall 2 (malformed JSON → strict structured outputs), Pitfall 4 (chunking under TPM), Pitfall 5 (phone normalization), Pitfall 6 (prompt injection → delimiters + schema enforcement), Pitfall 10 (free-tier rate limits)

### Phase 1 implementation (patterns to replicate)
- `.planning/phases/01-backend-foundation-data-admin-auth/01-*-SUMMARY.md` — how routers/deps/tests were built
- `backend/app/deps.py` — `require_admin` Bearer JWT dependency (reuse for extract endpoint)
- `backend/app/models/job.py` — Job model, `JobStatus` enum (pending/published/needs_review/invalid), `at_least_one_contact` CHECK
- `backend/app/crud/jobs.py` — async session CRUD style
- `backend/tests/conftest.py` — pytest harness (test DB, rolled-back transactions, dependency overrides)

### Requirements
- `.planning/REQUIREMENTS.md` — EXTR-01..EXTR-09 (lines 18–26); REVW-05 dependency note (line 34)

</canonical_refs>

<specifics>
## Specific Ideas

- Free-tier Groq limits verified 2026-10-19: `openai/gpt-oss-20b`/`120b` → 30 RPM, 1.000 RPD, 8.000 TPM, 200.000 TPD. Chunks must stay well under TPM (research guidance: ≤4–6K tokens per call) with inter-request delay and `retry-after`-honoring backoff on 429.
- Strict Structured Outputs (`response_format: {type: "json_schema", json_schema: {..., strict: true}}`) is SUPPORTED on both gpt-oss models (verified 2026-10-19) — use it; requires all fields `required` + `additionalProperties: false` (nullable via `type: ["string","null"]`). Still validate server-side with Pydantic (strict mode can't enforce semantic rules).
- Model config: `GROQ_MODEL` env (default `openai/gpt-oss-20b`) with fallback chain (`openai/gpt-oss-120b`); clear pt-BR error naming the env var when both fail — never hardcode a single model.
- Phone normalization: pt-BR variants ((11) 9 1234-5678, 11 91234-5678, +55...) → E.164 (`+5511912345678`) stored in `contact_phone`; frontend Phase 4 builds wa.me links from it.
- Grounding: verify extracted strings (title, company, salary, contacts, city) appear in the source chunk (normalized: lowercase, strip accents/emoji/whitespace). Ungrounded critical field (title/contact) → discard (D-05); ungrounded minor field → clear field + `needs_review`.
- Max jobs per extraction and max text size caps to prevent abuse/overspend (research recommendation: ~50 jobs, ~256KB).
- Injection test paste ("ignore previous instructions...") must produce no rogue record.

</specifics>

<deferred>
## Deferred Ideas

None — PRD/discuss covers phase scope; remaining discuss areas (texto grande, texto-fonte, grounding) are fully determined by roadmap success criteria + EXTR requirements recorded above.

</deferred>

---

*Phase: 02-llm-extraction-pipeline*
*Context gathered: 2026-10-19 from discuss checkpoint + roadmap (discuss-phase left 3 areas incomplete; resolved from success criteria with details delegated to OpenCode's Discretion)*
