---
status: diagnosed
trigger: "UAT gap diagnosis (Phase 22, Test 1): toolbar não reconhece cidade cadastrada usa ?q=city-name e retorna nada; chatbot marca cidade cadastrada como ignorada."
created: 2026-11-18T00:00:00Z
updated: 2026-11-18T00:00:00Z
---

## Current Focus
<!-- OVERWRITE on each update - reflects NOW -->

hypothesis: "Both symptoms stem from gaps in mapping user-provided city text to the supported/canonical `city` filter: (A) BoardToolbar commits free-text search only as `q` and never promotes supported city names to `city`, while public `q` search matches `jobs.search_text` (title/company/activities/requirements) and excludes `jobs.city`, so `?q=<city>` returns nothing when the city name is not in searchable text. (B) Intent mapper resolves SP/RJ/BH only from LLM `candidate.city` (or detects only remote from raw text when `candidate.city` is absent), so if extraction omits/misextracts a supported city the mapper marks it missing/not_in_whitelist and the API returns ignored/degraded interpretation with no city applied."
test: "Static code trace of toolbar/query construction, filters normalization, public jobs query, search_text composition, and intent parser/mapper/city resolution."
expecting: "Evidence shows no q->city promotion in manual toolbar path and search_text excludes city; evidence shows mapper lacks raw-text fallback for non-remote whitelist cities when candidate.city is missing."
next_action: "Return ROOT CAUSE FOUND with file-level evidence and fix direction (no code changes)."

## Symptoms
<!-- Written during gathering, then IMMUTABLE -->

expected: "Ao buscar por uma cidade correspondente a vaga cadastrada, a toolbar/filtros devem aplicar o parâmetro de cidade correto e retornar resultados; o chatbot deve reconhecer/aplicar a cidade quando cabível e não marcar como ignorada indevidamente."
actual: "O toolbar não está reconhecendo a cidade que corresponde a uma vaga cadastrada, está utilizando ?q=city-name  e retornando nada. \n\nO chat-bot também não reconhece a cidade que está cadastrada no banco retornando um status como ignorado ."
errors: "None reported"
reproduction: "Phase 22 HUMAN UAT Test 1 (.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md): buscar por cidade correspondente a vaga cadastrada via toolbar/chat."
started: "Discovered during Phase 22 human UAT (2026-11-18)"
severity: major
goal: find_root_cause_only
mode: symptoms_prefilled (UAT gap diagnosis)

## Eliminated
<!-- APPEND only - prevents re-investigating -->

- hypothesis: "Public jobs endpoint ignores a provided `city` param or resolves it incorrectly for supported slugs/canonicals."
  evidence: "`backend/app/api/v1/public.py:list_public_jobs` resolves `city=resolve_city(city)` and passes to `list_published`; `backend/app/services/cities.py` maps supported slugs/aliases to canonical DB values (São Paulo/Rio de Janeiro/Belo Horizonte/Remoto). `crud.jobs._published_filters` applies `Job.city == city` when provided. URL contract for board uses slugs via `frontend/lib/filters.ts`/`CITY_OPTIONS`."
  timestamp: 2026-11-18T00:00:00Z

- hypothesis: "Chat endpoint/UI drops contacts or bypasses deterministic search in a way that causes the reported symptom."
  evidence: "Symptom is 'status como ignorado' for city in interpretation; `chat_search` returns interpretation from `extract_and_map_intent`+mapper and deterministically queries `list_published` with `applied_params`. Ignored status originates from intent field assessment/mapping, not from result privacy/rendering path."
  timestamp: 2026-11-18T00:00:00Z

## Evidence
<!-- APPEND only - facts discovered -->

- timestamp: 2026-11-18T00:00:00Z
  checked: "`frontend/components/board/BoardToolbar.tsx` (search input and city chips behavior)"
  found: "Text input commits only `q` (`commit({ q: value.trim() })` on debounce/Enter/clear; lines ~56-91, 113-148). City is set exclusively via chip buttons calling `commit({ city: option.slug })` or `commit({ city: null })` (lines ~156-185). No code path converts typed supported city names/aliases into `city` filter."
  implication: "Typing a city name in the manual search box becomes `?q=...` (not `?city=...`), matching reported `?q=city-name`."

- timestamp: 2026-11-18T00:00:00Z
  checked: "`frontend/lib/filters.ts`, `frontend/lib/cities.ts`"
  found: "`normalizeFilters` accepts `city` only when slug is in `CITY_SLUGS` (`city: CITY_SLUGS.has(rawCity) ? rawCity : null`), trims/slices `q`, and does not infer `city` from `q`. `toApiParams`/`buildBoardHref` serialize `q` and `city` independently. Supported slugs/options: sao-paulo, rio-de-janeiro, belo-horizonte, remoto."
  implication: "Manual text entry is preserved as keyword query param; no normalization layer promotes a city term typed into `q`."

- timestamp: 2026-11-18T00:00:00Z
  checked: "`backend/app/api/v1/public.py:list_public_jobs`, `backend/app/crud/jobs.py:_published_filters/list_published`, `backend/app/services/cities.py`"
  found: "Public jobs endpoint strips `q` and resolves `city` separately (`term=q.strip() or None`, `city=resolve_city(city)`) then calls `list_published(..., q=term, city=..., sort=...)`. `_published_filters` applies `Job.city == city` for structured city filter and applies `q` via `Job.search_text.like(pattern)` over normalized `search_text` (see `backend/app/models/job.py: search_text`; migrations 0001/0003 build/search_text from title/company/activities/requirements). `search_text` does not include `Job.city`."
  implication: "A supported city typed as `q` is searched only in title/company/activities/requirements, not against the `jobs.city` column. If the city name is absent from those fields, results are empty despite matching registered jobs by city."

- timestamp: 2026-11-18T00:00:00Z
  checked: "`backend/app/services/intent/mapper.py:_resolve_city_safe`, `map_intent`; `backend/app/services/intent/parser.py`; `backend/app/api/v1/public.py:chat_search`"
  found: "`chat_search` relies on `extract_and_map_intent` (LLM candidate -> deterministic map). `_resolve_city_safe(raw_city, raw_text)` handles supported city resolution when `raw_city` is provided (remote/home-office, rejects hibrido/presencial, abbr/alias normalization for sp/rj/bh/rio/sao paulo/belo horizonte, then `resolve_city`). When `raw_city` is falsy, fallback only detects unequivocal remote mentions in raw text and returns `("Remoto","normalized")`; otherwise returns `(None,"missing")`. There is no raw-text fallback detection for São Paulo/Rio de Janeiro/Belo Horizonte when the LLM candidate omits `city`. `map_intent` sets city ignored with reason `missing` ("Cidade não informada...") or `not_in_whitelist` ("Cidade fora da whitelist suportada; não aplicada.") / `conflict_resolved` as applicable."
  implication: "If the LLM fails to extract/populate a supported non-remote city into `candidate.city` (or returns an unhandled variant while candidate text clearly indicates a supported city), mapper will not infer it from `raw_text` and will mark city as ignored (commonly missing/not_in_whitelist), matching 'status como ignorado' even for cities registered/supported by the product."

- timestamp: 2026-11-18T00:00:00Z
  checked: "`backend/app/services/extraction/extractor.py` (ALLOWED_CITIES/normalize_city), `backend/app/schemas/job.py:JobUpdate`, `backend/app/services/cities.py`"
  found: "Extraction/admin flows constrain/normalize supported public cities to canonical accented values (ALLOWED_CITIES/resolve_city) for supported cases; admin `JobUpdate` resolves city via `resolve_city` or rejects invalid. DB/public filter compares against canonical city value (`Job.city == canonical`)."
  implication: "Primary chat issue indicated by code is intent extraction/mapping coverage (especially missing raw-text fallback for SP/RJ/BH), not routine DB storage mismatch for supported whitelist cities. A data-shape mismatch remains possible for edge/manual/legacy records but is not evidenced here."

## Resolution
<!-- OVERWRITE as understanding evolves -->

root_cause: "Toolbar: free-text input is always emitted as `q` (no supported-city detection/promotion to `city`), and public keyword search queries `jobs.search_text` (title/company/activities/requirements only, excluding `jobs.city`), so typing a registered city name yields `?q=city-name` with no matches. Chat: `map_intent/_resolve_city_safe` depends on LLM `candidate.city` for non-remote whitelist cities and only falls back to raw-text remote detection when `candidate.city` is absent, so omitted/misread supported cities are classified ignored (missing/not_in_whitelist) instead of applied."
fix: "Not applied (diagnosis-only)."
verification: "Not applicable (diagnosis-only)."
files_changed: []
