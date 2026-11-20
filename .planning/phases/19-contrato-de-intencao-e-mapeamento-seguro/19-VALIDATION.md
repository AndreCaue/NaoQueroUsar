---
phase: 19
slug: contrato-de-intencao-e-mapeamento-seguro
status: audited
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-17
updated: 2026-11-20
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + pytest-asyncio (backend, repo padrão) |
| **Config file** | `backend/pyproject.toml`, `backend/tests/conftest.py` |
| **Quick run command** | `cd backend && python -m pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py` |
| **Full suite command** | `cd backend && python -m pytest -q` |
| **Estimated runtime** | ~30-90 seconds (subset intent puro/seam mockado) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py` (ou subconjunto mais próximo do escopo alterado).
- **After every plan wave:** Run `cd backend && python -m pytest -q` (ou suíte intent completa) em ambiente capaz.
- **Before `/gsd-verify-work`:** Evidência automatizada/histórica dos requisitos INT-01..03 consistente com `19-VERIFICATION.md` e artefatos do domínio intent.
- **Max feedback latency:** 120 seconds

---

## Per-task / Requirement Verification Map

| ID | Plan/Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|----|-----------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 19-V-01 | 19-01/19-02 | INT-01 | V5 (untrusted NL/input) | Consulta pt-BR produz contrato estruturado/validado estrito (JSON/schema) sem inventar campos não declarados/implicados; defaults nulos seguros | unit | `cd backend && python -m pytest -q tests/test_intent_schema.py tests/test_intent_parser.py tests/test_intent_client.py` | ✅ `backend/tests/test_intent_schema.py`, `backend/tests/test_intent_parser.py`, `backend/tests/test_intent_client.py` | ✅ green (evidência `19-VERIFICATION.md`: passed) |
| 19-V-02 | 19-01/19-02 | INT-02 | V5 / prompt/input safety | Extração usa seam Groq/config existente isolado (strict JSON, validação server-side, delimitação/sanitização de entrada não confiável) com recuperação/fallback determinístico seguro | unit (fake seam, sem rede) | `cd backend && python -m pytest -q tests/test_intent_client.py tests/test_intent_parser.py` | ✅ `backend/tests/test_intent_client.py`, `backend/tests/test_intent_parser.py`, `backend/app/services/intent/client.py`, `backend/app/services/intent/parser.py` | ✅ green (evidência histórica) |
| 19-V-03 | 19-01/19-02 | INT-03 | Integrity/Tampering | Mapeamento determinístico e server-authoritative gera `applied_params {q, city, sort}` compatíveis com busca pública (whitelist SP/RJ/BH/Remoto, sort explícito), classifica por campo (aplicado/ignorado/aproximado + reason) e nunca aplica filtros inexistentes | unit | `cd backend && python -m pytest -q tests/test_intent_mapper.py tests/test_intent_parser.py` | ✅ `backend/tests/test_intent_mapper.py`, `backend/tests/test_intent_parser.py`, `backend/app/services/intent/mapper.py`, `backend/app/services/cities.py` | ✅ green (evidência `19-VERIFICATION.md`: passed) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Evidência principal:** `.planning/phases/19-contrato-de-intencao-e-mapeamento-seguro/19-VERIFICATION.md` (`status: passed`, score 8/8 must-haves) e artefatos/summaries da fase (`19-01-SUMMARY.md`, `19-02-SUMMARY.md`). Testes determinísticos de intent presentes no repositório (`backend/tests/test_intent_schema.py`, `backend/tests/test_intent_mapper.py`, `backend/tests/test_intent_parser.py`, `backend/tests/test_intent_client.py`).

---

## Wave 0 Requirements

- [x] `backend/tests/test_intent_schema.py` — schema/defaults/strictness/validação de contrato (INT-01).
- [x] `backend/tests/test_intent_mapper.py` — mapeamento determinístico, whitelist/cidade, sort explícito, classificação por campo e limites não nativos (INT-03).
- [x] `backend/tests/test_intent_parser.py` — orquestração parse→candidate→map com degradação segura, entrada vazia/genérica e seam fake sem rede/DB (INT-01/02/03).
- [x] `backend/tests/test_intent_client.py` — seam Groq isolado (strict json_schema, delimitação/sanitização, model chain, parsing/repair) com fake client sem rede (INT-02).
- [x] `backend/app/services/intent/` (`schema.py`, `mapper.py`, `client.py`, `parser.py`, `__init__.py`) — API interna/contrato final para consumo da Fase 20.

*Wave 0 existente e rastreável; não há dependência de diretórios legados de intent fora de `backend/tests/test_intent_*`.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| N/A | — | Escopo da fase 19 é backend/service/contrato (schemas, mapper determinístico, seam isolado, parser) coberto por testes automatizados e inspeção de artefatos | Consultar `19-VERIFICATION.md` e reexecutar `cd backend && python -m pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py`. |

*All phase behaviors have automated verification (conforme evidência disponível).*

---

## Validation Sign-Off

- [x] All requirements/tasks have `<automated>` verify or Wave 0 dependencies satisfied (evidência existente)
- [x] Sampling continuity: estratégia definida para subset intent determinístico
- [x] Wave 0 covers all MISSING references (testes/artefatos presentes; caminhos corrigidos)
- [x] No watch-mode flags
- [x] Feedback latency < 120s (subset alvo)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (retrospective audit, 2026-11-20; caminhos corrigidos e evidência alinhada a `19-VERIFICATION.md`)

## Audit Update 2026-11-20

- Substituídos caminhos obsoletos legados do domínio intent pelos arquivos reais `backend/tests/test_intent_*` e comandos executáveis no repositório.
- Mapa de verificação preenchido para INT-01/INT-02/INT-03 com base em `19-VERIFICATION.md` (passed), summaries e presença dos testes/artefatos.
- Wave 0 marcado como completo conforme realidade do código/testes; sem afirmação de nova execução nesta edição.