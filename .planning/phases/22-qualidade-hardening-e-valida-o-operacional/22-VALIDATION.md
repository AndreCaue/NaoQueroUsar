---
phase: 22
slug: qualidade-hardening-e-valida-o-operacional
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-18
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest 9.1.1 + pytest-asyncio (auto); Frontend: Vitest ^2.1.9 (node, `lib/**/*.test.ts`) |
| **Config file** | `backend/pyproject.toml`, `backend/tests/conftest.py`; `frontend/vitest.config.ts`, `frontend/package.json` |
| **Quick run command** | `cd backend && pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py` (pure intent subset; see DB-harness caveat) and/or `cd frontend && npm run test:chat` |
| **Full suite command** | `cd backend && pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py tests/test_chat_search_api.py tests/test_ratelimit.py` (DB-gated where applicable); `cd frontend && npm test` |
| **Estimated runtime** | ~30–90 seconds for targeted mocked/pure suites (DB-backed subset depends on local test DB) |

---

## Sampling Rate

- **After every task commit:** Run the smallest relevant quick command for touched scope (backend intent/chat mocked tests and/or `cd frontend && npm run test:chat` / `npm test` when frontend logic touched). Use pure/fixture-independent subsets when DB is unavailable.
- **After every plan wave:** Run `cd backend && pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py tests/test_chat_search_api.py tests/test_ratelimit.py` (DB-gated subset) + `cd frontend && npm test`.
- **Before `/gsd-verify-work`:** Targeted phase suites green in a capable environment (DB-backed where applicable) + `22-MVP-EXAMPLES.md` and `22-MANUAL-UAT.md` completed with contrato esperado/observado evidence.
- **Max feedback latency:** 120 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 22-XX-01 | TBD | TBD | QA-01 | — | Exemplos MVP validados com lacunas explícitas (sem inventar filtros/semântica/link; Campos não nativos aproximados/sinalizados) | integration/unit (mocked) + documented matrix | `cd backend && pytest -q tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_chat_search_api.py -k "mvp or campinas or salary or parecid or remoto or estagio"` | ❌ W0 | ⬜ pending |
| 22-XX-02 | TBD | TBD | QA-02 | V5/V4 (input/rate-limit) | Extração/mapeamento/normalização e chat-search com LLM mockado: equivalência `list_published`, `JobPublic` sem contatos, degradação/fallback, limites | unit/integration + pure UI logic | `cd backend && pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py tests/test_chat_search_api.py tests/test_ratelimit.py`; `cd frontend && npm test` | ✅ partial | ⬜ pending |
| 22-XX-03 | TBD | TBD | QA-03 | V4 (abuse/availability), info disclosure | Kill-switch fim-a-fim seguro/controlado, board/manual search intactos, logs estruturados sem PII (outcome/motivo/latência/contagens) | integration/unit + manual | `cd backend && pytest -q tests/test_chat_search_api.py -k "disabled or kill_switch or logging"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` — matriz QA-01 (D-01/D-02/D-03, 5 exemplos + lacunas explícitas, contrato esperado + observado)
- [ ] `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` — roteiro manual/UAT guiado QA-02/QA-03 (D-04), inclui chat desativado/degradado e não-regressão do board/reveal
- [ ] `backend/tests/test_chat_search_api.py` — estender com disabled/kill-switch, logging estruturado sem PII (`caplog`), e lacunas MVP/combinações (QA-01/02/03)
- [ ] `backend/tests/test_intent_mapper.py`, `test_intent_parser.py`, `test_intent_schema.py`, `test_intent_client.py` — consolidar/estender casos determinísticos MVP/classificação (D-02/D-05)
- [ ] `frontend/lib/*.test.ts` (somente se helpers puros novos para status/gating) — lógica viável QA-02 (D-04)
- [ ] `backend/tests/conftest.py` (opcional) — whitelist de testes puros de intent como DB-independentes se confirmados sem fixtures
- [ ] Dependências de ambiente (se necessário): `cd backend && pip install -e ".[dev]"`; `cd frontend && npm ci`

*DB-backed execution evidence is prerequisite-gated when `TEST_DATABASE_URL`/`DATABASE_URL` or migrated schema is unavailable; do not claim execution without environment.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fluxo UI/E2E viável do chat no board (abrir sem login, enviar, loading/erro, interpretação/limitações, resultados/carregar mais, aplicar no board, detalhe/reveal canônico, busca manual em degradação/sem resultados) | QA-02 | Playwright/RTL não serão introduzidos nesta fase (D-04); validação viável por roteiro guiado + lógica pura automatizada | Executar `22-MANUAL-UAT.md` cobrindo estados normal, degradado e desativado; confirmar contatos nunca no chat e reveal canônico preservado |
| Kill-switch fim-a-fim percebido na UI e não-regressão do board público com chat desligado | QA-03 | Comportamento de integração/config operacional e UX (launcher oculto, board utilizável) depende de ambiente/config real | Desativar via env/config, reiniciar/recargar conforme mecanismo, verificar endpoint controlado/sem internos e UI sem launcher/painel; confirmar `GET /public/jobs`, filtros, paginação, detalhe e busca manual funcionam |
| Evidência contrato esperado + observado por exemplo MVP (matriz) | QA-01 | Consolida resultados automatizados e observações/fixtures documentadas com lacunas explícitas | Preencher/revisar `22-MVP-EXAMPLES.md` com referências a testes/execuções e lacunas (Campinas, campos não nativos, “parecidas” seed textual) |

*All phase behaviors have automated verification where feasible via mocked/pure tests; remaining items require guided manual evidence per D-04/D-01/D-03.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
