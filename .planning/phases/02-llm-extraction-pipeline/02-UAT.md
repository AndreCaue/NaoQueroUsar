---
status: testing
phase: 02-llm-extraction-pipeline
source:
  - .planning/phases/02-llm-extraction-pipeline/02-01-SUMMARY.md
  - .planning/phases/02-llm-extraction-pipeline/02-02-SUMMARY.md
  - .planning/phases/02-llm-extraction-pipeline/02-03-SUMMARY.md
  - .planning/phases/02-llm-extraction-pipeline/02-04-SUMMARY.md
started: 2025-10-20T00:00:00Z
updated: 2025-10-20T12:00:00Z
---


## Current Test

number: 6
name: Extract API Authentication and Validation
expected: |
  POST /api/v1/admin/extract requires JWT authentication (Bearer). Missing/invalid token returns 401. text min_length enforced (422). Byte cap enforced (413). If GROQ_API_KEY missing, returns 503. Timeout returns 504. ValueError maps to 422.
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: |
  Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application from scratch. Server boots without errors, any seed/migration completes, and a primary query (health check, homepage load, or basic API call) returns live data.
result: pass

### 2. Phone Normalization (pt-BR -> E.164)
expected: |
  Unit-level behavior is correct: pt-BR phone numbers normalize to +55 E.164. Test with (11) 91234-5678 -> +5511912345678, landline 11 2345-6789 -> +551123456789, reject bare 8-9 digit without DDD as ambiguous (no DDD). The extraction pipeline accepts normalized numbers in candidates.
result: pass

### 3. Groq Extraction with Strict JSON Schema
expected: |
  The extractor validates LLM responses against the strict EXTRACTION_JSON_SCHEMA (required fields, no extra properties). Malformed/extra-key responses are rejected and trigger the single repair attempt. The system never hardcodes the Groq model chain - it uses GROQ_MODEL/GROQ_MODEL_FALLBACK from environment.
result: pass

### 4. Chunking Losslessness and Budget Limits
expected: |
  chunk_text produces contiguous exact slices under EXTRACT_CHUNK_MAX_TOKENS. Joining chunks reconstructs the original content (losslessness). When a paragraph boundary is chosen as the cut, the boundary is preserved correctly; pacing delays only occur between chunks for multi-chunk inputs.
result: pass

### 5. Grounding and City Mapping
expected: |
  Fields are grounded against the source text (accent/case/emoji-insensitive). City accepts raw value OR canonical mapping (e.g. SP maps to Sao Paulo) while truly absent cities cause the row to be flagged needs_review. D-05 discard logic applies only when title is missing/ungrounded OR both contacts absent.
result: pass

### 6. Extract API Authentication and Validation
expected: |
  POST /api/v1/admin/extract requires JWT authentication (Bearer). Missing/invalid token returns 401. text min_length enforced (422). Byte cap enforced (413). If GROQ_API_KEY missing, returns 503. Timeout returns 504. ValueError maps to 422.
result: [pending]

### 7. Atomic Persistence and Summary
expected: |
  Kept candidates are inserted in a single transaction (bulk_create_pending flushes only, caller commits). On exception, rollback occurs and API returns 500 with message about nothing being written. source_snippet is stored on persisted jobs. Discarded candidates are never persisted - only returned in the summary with reason and snippet.
result: [pending]

### 8. Admin Paste UI Flow
expected: |
  Visit /admin/paste. Log in with admin password -> JWT stored (state + sessionStorage, persists on reload). Paste raw text and submit. See pt-BR summary with count badges, alerts (divergence/truncation/discarded/max-jobs), and discarded entries shown with reason+snippet. Can click Nova extração to reset summary while keeping token. UI uses dark theme and renders without build errors.
result: [pending]

### 9. End-to-End Extraction from Paste to DB
expected: |
  From the admin paste UI with GROQ_API_KEY configured and backend running, submit a realistic WhatsApp/Telegram-style paste containing multiple jobs. Extraction completes, summary shows counts, and persisted jobs appear in the DB with status pending/needs_review and source_snippet populated. No secrets leak to frontend.
result: [pending]

### 10. Error Handling and Alert Surfaces
expected: |
  Divergence (detected vs extracted counts for multi-chunk) surfaces an alert. Truncation when hitting chunk/token limits surfaces an alert. MAX_JOBS overflow produces a single 'excedeu o limite' discarded entry and corresponding alert. Model dead/exhaustion and rate-limit conditions produce clear pt-BR error messages via the API helper.
result: [pending]

## Summary

total: 10
passed: 5
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps

[none yet]

