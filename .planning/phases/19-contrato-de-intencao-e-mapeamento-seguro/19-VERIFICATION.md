---
phase: 19-contrato-de-intencao-e-mapeamento-seguro
verified: 2026-11-17T00:00:00Z
status: passed
score: 8/8 must-haves verified
---

# Phase 19: Contrato de intenção e mapeamento seguro Verification Report

**Phase Goal:** Usuários têm suas consultas em linguagem natural convertidas em parâmetros de busca confiáveis e alinhados às capacidades reais do produto
**Verified:** 2026-11-17T00:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Consulta pt-BR produz contrato estruturado/validado com campos não declarados/implicados nulos (sem invenção) | ✓ VERIFIED | `backend/app/services/intent/schema.py`: `IntentLLMOutput` strict (`ConfigDict(extra="forbid")`) with nullable defaults (`q/city/salary/work_mode/contract_type/seniority/sort=None`); `IntentContract`/`UnderstoodIntent`/`AppliedParams`/`FieldAssessment` model the server contract. `backend/tests/test_intent_schema.py` asserts empty/defaults, absent nested fields remain `None`, extra keys rejected, and valid contract structure (`aplicado`/`aproximado`). |
| 2 | Cada parâmetro tem classificação verificável por campo (entendido, aplicado, status aplicado\|ignorado\|aproximado, reason_code/reason) | ✓ VERIFIED | `FieldAssessment` records `field`, `understood`, `applied`, `status` (`FieldStatus` enum values `aplicado/ignorado/aproximado`), `reason_code`, `reason` (`schema.py:105-114`). `IntentContract.field_statuses` carries assessments; `mapper.py` emits statuses for `q, city, salary, work_mode, contract_type, seniority, sort` in both `build_empty_intent` and `map_intent` (e.g. normalized/aplicado, not_in_whitelist/ignorado, conflict_resolved, textual_approximation_in_q/aproximado, unsupported_structured_filter/ignorado). Tests assert per-field statuses/reasons. |
| 3 | Mapeamento determinístico gera `applied_params {q, city, sort}` compatíveis com a busca pública (whitelist SP/RJ/BH/Remoto, sort explícito apenas, q normalizado) sem aplicar filtros inexistentes | ✓ VERIFIED | `mapper.py` uses `from app.services.cities import resolve_city` (`:15,67-103,294,482-485`), resolves/accepts safe whitelist cases (incl. `SP`, `home office`→`Remoto`), rejects non-whitelist (`Campinas`) and modality-as-city cases; enforces canonical whitelist-or-None on final params. Sort is explicit-only via raw-text detection (`_detect_explicit_sort`, `:46-64,248-276`) with conflicts not applied; no invented sort. `q` normalized/cleaned/composed (`:105-174,328-344,487-488`) with empty→`None`. `AppliedParams` limited to `q/city/sort` (`schema.py:117-124`). Compatible with public semantics in `app.api.v1.public`/`app.crud.jobs.list_published` (term strip/None, `resolve_city`, explicit sort handling). |
| 4 | Campos não nativos (salário/modalidade/contrato/senioridade) nunca viram filtro estruturado garantido; limites ficam explícitos por status/motivo/avisos | ✓ VERIFIED | `mapper.py` never sets native filters beyond `q/city/sort`. Salary with bounds -> understood structured, `applied=None`, `ignorado` + `unsupported_structured_filter` and limitation (`:348-375`). Modality/contract/seniority assessed as `aproximado` only when terms influence `q` (`textual_approximation_in_q`) else `ignorado`/`unsupported_structured_filter`; remoto modality can be represented via applied city rule; limitations aggregated (`:376-475`). `parser.py` preserves safe empty/no-extractable contracts. Tests cover salary ignored, seniority/contract approximated in q, and no invented filters. |
| 5 | Extração de intenção usa infraestrutura Groq/config existente de forma isolada com chamada structured strict JSON e validação server-side | ✓ VERIFIED | `backend/app/services/intent/client.py`: isolated seam (no `app.services.extraction` job coupling; comment confirms), env-driven `model_chain` from `GROQ_MODEL`/`GROQ_MODEL_FALLBACK` (`:179-184`), lazy real client with `GROQ_API_KEY`/`GROQ_TIMEOUT_SECONDS` (`:199-208`), `strict_response_format` json_schema `name=search_intent`, `strict=True` (`:187-196`), bounded parse/repair and `IntentLLMOutput.model_validate_json(strip_markdown_fences(...))` (`:212-286`), injectable `client`/`sleep`. `tests/test_intent_client.py` validates strict payload, model chain, fake-client parsing/fences. |
| 6 | Entrada do usuário é tratada como dado não confiável (delimitação/sanitização) e saídas inválidas têm caminho determinístico de recuperação/segurança sem expor falhas opacas no contrato | ✓ VERIFIED | Client wraps/sanitizes with `<CONSULTA_BUSCA>`/`</CONSULTA_BUSCA>` and instruction note (`client.py:17-23,145-164`); system prompt constrains extraction and states data-not-instruction (`:24-33`). `parser.py` catches `IntentExtractionError/ValidationError/Exception` and degrades to `build_empty_intent(..., reason_code="no_extractable_params")` (`:59-67`), avoiding opaque contract-level crash; empty input bypasses LLM (`:31-36,56-58`). Tests include injected-instruction-shaped input and client-failure degradation. |
| 7 | Entradas vazias/genéricas/sem parâmetros retornam intenção válida vazia com motivos claros, sem inventar filtros | ✓ VERIFIED | `parser.py:_is_empty_input` + `extract_and_map_intent` returns safe empty contract for `None/""/whitespace` (`reason_code="empty_input"`), and degrades to `no_extractable_params` on failures/effectively-empty mappings (`:19-67`). `mapper.build_empty_intent` sets `applied_params` all `None`, per-field statuses with clear pt-BR reason `"Nenhum parâmetro extraível informado."` and limitation `no_extractable_params` (`:197-226`). `tests/test_intent_parser.py` covers empty, generic all-null candidate, and failure cases with no invented filters. |
| 8 | API interna do módulo entrega contrato final mapeado (entendido + field_statuses + applied_params + limitações) pronto para consumo da Fase 20 | ✓ VERIFIED | `backend/app/services/intent/__init__.py` exports consolidated API: `IntentExtractionError`, `call_intent_llm`, `parse_intent`, `extract_and_map_intent`, schema types, `build_empty_intent`, `map_intent` (`__all__`). `extract_and_map_intent` returns `IntentContract` (server-authoritative) via candidate parse + `map_intent`/safe fallback. No HTTP route/DB added (service/domain scope for Phase 19). |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `backend/app/services/intent/__init__.py` | Public intent domain exports | ✓ VERIFIED | Exports schema/client/parser/mapper APIs including `extract_and_map_intent`, `parse_intent`, `call_intent_llm`, `build_empty_intent`, `map_intent`. |
| `backend/app/services/intent/schema.py` | Strict schemas for candidate + final contract | ✓ VERIFIED | 169 lines; `extra="forbid"` on all models; defines `IntentLLMOutput`, `IntentContract`, `AppliedParams`, `FieldAssessment`, `UnderstoodIntent`, enums/status/reason structures and salary/mode/contract/seniority traceability. |
| `backend/app/services/intent/mapper.py` | Deterministic normalization/mapping/classification | ✓ VERIFIED | 496 lines; `build_empty_intent`, `map_intent`, whitelist via `resolve_city`, explicit/conflict sort handling, q normalization/composition, per-field statuses, aggregated limitations, safe `applied_params`. |
| `backend/app/services/intent/client.py` | Groq intent seam (strict json_schema, wrap_untrusted, model chain, injectable) | ✓ VERIFIED | 287 lines; delimiters/sanitization, `build_messages`, `strict_response_format`, `model_chain`, `call_intent_llm`, repair/fallback, lazy real client using `GROQ_*`. |
| `backend/app/services/intent/parser.py` | Orchestration parse->candidate->map with safe degradation | ✓ VERIFIED | 67 lines; `parse_intent`, `extract_and_map_intent`, empty handling, deterministic fallback to `build_empty_intent`, effective-empty normalization. |
| `backend/tests/test_intent_schema.py` | Schema/defaults/strictness tests | ✓ VERIFIED | 136 lines; covers null defaults, extra-key rejection, valid contract, salary/currency, status values. |
| `backend/tests/test_intent_mapper.py` | Deterministic mapper behavior tests | ✓ VERIFIED | 126 lines; covers empty intent, whitelist/rejection (`SP`, `home office`, `Campinas`), explicit/conflict sort, non-native approximation/ignored, no invented city/sort. |
| `backend/tests/test_intent_client.py` | Client payload/delimitation/seam tests (no network) | ✓ VERIFIED | 154 lines; fake client, wrap/sanitize/messages, strict response format, model chain, parse/fence stripping, request params. |
| `backend/tests/test_intent_parser.py` | Parser safety/integration tests (no network/DB) | ✓ VERIFIED | 185 lines; empty/generic/coherent/injection-shaped inputs, no-call-on-empty assertions, failure degradation to safe contract. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `backend/app/services/intent/mapper.py` | `app.services.cities.resolve_city` | canonical whitelist normalization | ✓ WIRED | Imported and used for safe city resolution/final canonicalization (`mapper.py:15,93,482`); non-whitelist and conflict cases prevented from applying. |
| `backend/app/services/intent/mapper.py` | public search contract (`list_published`/`public.py` semantics) | `applied_params` `{q, city, sort}` | ✓ WIRED | Emits `AppliedParams(q=clean/None, city=canonical whitelist|None, sort=explicit only|None)`; aligns with `public.py` (`q` strip/None, `resolve_city`, `resolve_sort` usage) and `crud.jobs.list_published(session,..., q, city, sort)`. |
| `backend/app/services/intent/client.py` | `app.core.config` Groq settings (`GROQ_*`) | env-driven model chain/timeout/lazy client | ✓ WIRED | Reads `GROQ_MODEL`, `GROQ_MODEL_FALLBACK`, `GROQ_TIMEOUT_SECONDS`, `GROQ_API_KEY` via settings access (`client.py:181-183,200-208,228,251`). |
| `backend/app/services/intent/parser.py` | `backend/app/services/intent/mapper.py` | server-authoritative parse->map/fallback | ✓ WIRED | Imports/uses `build_empty_intent` and `map_intent` (`parser.py:15,57,62,64,66`); `extract_and_map_intent` returns mapped or safe-empty contract. |
| `backend/app/services/intent/parser.py` | `backend/app/services/intent/client.py` | LLM candidate extraction seam | ✓ WIRED | Imports/uses `call_intent_llm` and `IntentExtractionError` (`parser.py:14,33,61`) with injectable client/sleep. |
| `backend/app/services/intent` package | `app.services.extraction` job domain | isolation boundary | ✓ WIRED (isolated) | No imports/usage of `app.services.extraction`, `ExtractedJobRaw`, or `extract_jobs` in intent modules/tests logic; only a comment in `client.py` states "No ... coupling to job extraction schemas/extractor". |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| N/A (service/domain contract, no UI/rendered component) | - | - | - | - |

Phase 19 delivers backend intent schemas/mapping/client/parser (no HTTP endpoint/UI rendering). Level 4 component data-flow checks are not applicable.

### Behavioral Spot-Checks

Step 7b: SKIPPED (no runnable HTTP entrypoint for intent in this phase; Phase 20 wires endpoint). Behavior is covered by static code evidence and pure/fake-seam tests present (`test_intent_schema.py`, `test_intent_mapper.py`, `test_intent_client.py`, `test_intent_parser.py`).

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| SKIPPED | - | No Phase 19 runnable endpoint; service seam only | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| INT-01 | `19-01-PLAN.md`, `19-02-PLAN.md` | NL pt-BR consulta extraída em parâmetros estruturados JSON estrito e validado, sem inventar não declarado/implicado | ✓ SATISFIED | Strict `IntentLLMOutput`/contract schemas with nullable defaults and `extra="forbid"`; Groq seam requests strict `json_schema` and validates via Pydantic; mapper preserves "understood" safely and never invents applied filters (whitelist/explicit-only/conflict-safe). |
| INT-02 | `19-01-PLAN.md`, `19-02-PLAN.md` | Extração usa provider LLM configurável de baixo custo (Groq/config existente) com validação server-side, defaults nulos/seguros e robustez a variações pt-BR/instruções conflitantes | ✓ SATISFIED | `client.py` reuses `GROQ_*` config/model chain/timeout with injectable seam, strict schema + bounded repair/fallback; untrusted query delimitation/sanitization and system constraints; `parser.py`/`mapper.py` enforce server-authoritative safe defaults/degradation. |
| INT-03 | `19-01-PLAN.md`, `19-02-PLAN.md` | Normaliza e mapeia com segurança para busca existente (`q`, cidade whitelist SP/RJ/BH/Remoto, `sort` permitido), separando/relatando aplicado, ignorado ou aproximado e limites | ✓ SATISFIED | Deterministic `map_intent` builds auditable per-field statuses and `applied_params{q,city,sort}` via `resolve_city`, explicit-only sort, conflict handling, q normalization, and explicit non-native limitation signaling (aproximado em `q` ou ignorado). |

**Orphaned requirements for Phase 19:** None. REQUIREMENTS traceability maps INT-01/INT-02/INT-03 to Phase 19 only, and both plans declare all three.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `backend/app/services/intent/client.py` | 4 | Comment mentions "extractor" (boundary note: no coupling) | ℹ️ Info | Not a stub; documents isolation. No extraction-domain imports/usages found in intent package. |

No blocker/warning anti-patterns detected in phase artifacts (`schema.py`, `mapper.py`, `client.py`, `parser.py`, tests). Implementations are substantive (validation, deterministic mapping, LLM seam, safe degradation) with matching tests.

### Human Verification Required

None. Phase 19 scope is backend service/contract logic (schemas, deterministic mapper, isolated LLM seam, parser) verifiable via code inspection and existing automated test artifacts; no UI/visual/real-time behavior introduced.

### Gaps Summary

No gaps found. Must-haves for INT-01/INT-02/INT-03 are implemented as a strict, auditable, server-authoritative intent contract with safe public-search mapping (`q/city/sort` whitelist/explicit-only), explicit aplicado/ignorado/aproximado classifications, and deterministic safe handling for empty/generic/untrusted/failure cases. Ready for Phase 20 to consume the internal API (`extract_and_map_intent`/contract).

---

_Verified: 2026-11-17T00:00:00Z_
_Verifier: OpenCode (gsd-verifier)_