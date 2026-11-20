---
status: resolved
trigger: "UAT gap diagnosis (Phase 22, Test 1): toolbar não reconhece cidade cadastrada usa ?q=city-name e retorna nada; chatbot marca cidade cadastrada como ignorada."
created: 2026-11-18T00:00:00Z
updated: 2026-11-20T00:00:00Z
---

## Current Focus
<!-- OVERWRITE on each update - reflects NOW -->

estado: **resolvido (causa/mitigação de código + testes determinísticos)** com reteste runtime do caso reportado registrado como **deferimento aceito por item** (inviável no ambiente desta execução).
diagnóstico: concluído (causa raiz identificada em 2026-11-18).
mitigação aplicada: 22-04 (promoção determinística de cidade suportada no toolbar + fallback raw-text SP/RJ/BH/Remoto no mapper com salvaguardas) e hardening 23-01 (remoção de `\brio\b` ambíguo, preservando detecção segura RJ via `\brj\b` e `\brio\s+de\s+janeiro\b`) com regressões determinísticas.
next_action: "nenhum (encerrado para diagnóstico/correção automatizável); revalidação runtime/integrada do caso reportado permanece como ação futura condicionada a ambiente viável (ver Resolution e deferimento aceito)."

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

- timestamp: 2026-11-20T00:00:00Z
  checked: "`backend/app/services/intent/mapper.py`, `backend/tests/test_intent_mapper.py`, `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-01-SUMMARY.md`, commits `8d0c621`/`27e1a8c`"
  found: "Hardening 23-01 removeu o padrão ambíguo `\\brio\\b` do fallback raw-text de Rio de Janeiro, mantendo detecção segura por `\\brj\\b` e `\\brio\\s+de\\s+janeiro\\b`. Regressões determinísticas cobrem falsos positivos (\"Rio Grande do Sul\", \"Rio Branco\") sem mapear para \"Rio de Janeiro\" quando não há cidade explícita, preservando casos suportados RJ."
  implication: "Risco de falso positivo apontado em `22-REVIEW.md` (WR-04) mitigado no código com evidência automatizada; whitelist permanece restrita (sem inventar cidades)."

- timestamp: 2026-11-20T00:00:00Z
  checked: "Rastreabilidade 22-04 (`frontend/lib/cities.ts`, `frontend/components/board/BoardToolbar.tsx`, `frontend/lib/cities.test.ts`, `backend/app/services/intent/mapper.py`, `backend/tests/test_intent_mapper.py`, `backend/tests/test_intent_parser.py`) + artefatos 22 (`22-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, `22-MVP-EXAMPLES.md`, `22-VERIFICATION.md`)"
  found: "Correção do caso reportado (promoção toolbar para `city=<slug>` e fallback raw-text SP/RJ/BH/Remoto com salvaguardas) já registrada/documentada em 22-04; 23-01 complementou hardening RJ. Não foi executado reteste runtime/integrado nesta sessão (ambiente indisponível)."
  implication: "**Reteste runtime/manual do caso reportado: deferimento aceito por item (inviável no ambiente atual).** Motivo: sem backend/frontend/DB/dados/navegador integrados disponíveis nesta execução. Risco residual: divergência operacional em ambiente real não observada diretamente. Condição/ação futura: revalidar item 0 de `22-MANUAL-UAT.md` e item 1 de `22-HUMAN-UAT.md` em ambiente integrado, registrando evidência do filtro `city=<slug>` e interpretação correta no chat."

## Resolution
<!-- OVERWRITE as understanding evolves -->

root_cause: "Toolbar: free-text input is always emitted as `q` (no supported-city detection/promotion to `city`), and public keyword search queries `jobs.search_text` (title/company/activities/requirements only, excluding `jobs.city`), so typing a registered city name yields `?q=city-name` with no matches. Chat: `map_intent/_resolve_city_safe` depends on LLM `candidate.city` for non-remote whitelist cities and only falls back to raw-text remote detection when `candidate.city` is absent, so omitted/misread supported cities are classified ignored (missing/not_in_whitelist) instead of applied. Hardening adicional (23-01) fechou risco residual identificado em review: fallback raw-text com `\brio\b` podia confundir nomes com \"Rio\" fora da whitelist/RJ."
fix: "Aplicado (22-04 + 23-01). 22-04: promoção determinística de texto de cidade suportada no toolbar para `city=<slug>` (limpando `q` em match exato seguro) e fallback determinístico server-side no mapper para detectar whitelist SP/RJ/BH/Remoto em `raw_text` quando `candidate.city` ausente, com salvaguardas de conflito/whitelist e `applied_params`/`field_statuses` coerentes. 23-01: hardening do fallback de Rio de Janeiro removendo `\brio\b` ambíguo e mantendo apenas sinais seguros (`\\brj\\b`, `\\brio\\s+de\\s+janeiro\\b`), evitando falsos positivos como \"Rio Grande do Sul\"/\"Rio Branco\" sem inventar cidades fora da whitelist."
verification: "Testes automatizados determinísticos adicionados/atualizados e registrados em 22-04/23-01 (ex.: `frontend/lib/cities.test.ts`, `backend/tests/test_intent_mapper.py`, `backend/tests/test_intent_parser.py`; commits de referência 22-04 e `8d0c621`/`27e1a8c` de 23-01). **Reteste runtime/manual do caso reportado (toolbar e chat em ambiente integrado com dados): deferimento aceito por item (inviável no ambiente desta execução).** Motivo: ausência de stack integrada executável (backend/frontend/DB/dados/navegador) disponível para reprodução operacional nesta sessão de fechamento documental. Risco residual: comportamento ponta a ponta em runtime real pode divergir por configuração/dados/ambiente apesar da cobertura determinística. Condição/ação futura: executar `22-MANUAL-UAT.md` item 0 e `22-HUMAN-UAT.md` item 1 em ambiente com backend+frontend+dados de vagas por cidade, registrando evidência objetiva do `city=<slug>` aplicado e da interpretação do chat sem marcação indevida como ignorada."
files_changed:
  - frontend/lib/cities.ts
  - frontend/components/board/BoardToolbar.tsx
  - frontend/lib/cities.test.ts
  - backend/app/services/intent/mapper.py
  - backend/tests/test_intent_mapper.py
  - backend/tests/test_intent_parser.py
  - .planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-01-SUMMARY.md (evidência)
  - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md (rastreabilidade)
  - .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md / 22-MANUAL-UAT.md / 22-VERIFICATION.md (reconciliação por item)
