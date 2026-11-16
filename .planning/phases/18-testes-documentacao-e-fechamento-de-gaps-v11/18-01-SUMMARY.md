---
phase: 18-testes-documentacao-e-fechamento-de-gaps-v11
plan: 01
subsystem: audit-evidence
tags: [audit, requirements, extraction, public, search, uiux, tests, handoff]
dependency_graph:
  requires: []
  provides:
    - "Rastreabilidade de fechamento AUD-01..AUD-04 (EXTR-10/11/12, PUBL-10/11/12/13/14, SRCH-10/11/12, UIUX-10/11/12)"
    - "18-AUDIT-MATRIX.md com status por requisito, evidências estáticas e handoffs objetivos"
  affects:
    - ".planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-02-PLAN.md"
    - ".planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-03-PLAN.md"
    - ".planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-04-PLAN.md"
tech_stack:
  added: []
  patterns:
    - "Auditoria híbrida D-01/D-04: validar código/testes existentes, correção pontual só para lacuna real, handoff explícito quando execução depender de DB/browser/runtime canônico"
key_files:
  created:
    - ".planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-AUDIT-MATRIX.md"
  modified: []
decisions:
  - "Nenhuma correção de código/teste aplicada: inspeção estática não identificou lacunas reais nos contratos EXTR/PUBL/SRCH/UIUX; fechamento registrado como evidência parcial+handoff onde depende de DB migrado, browser humano ou host canônico."
  - "Execução direcionada de pytest registrada honestamente (86 passed, 1 setup error por schema ausente `jobs`) sem inflar status de validação."
metrics:
  duration: "n/a (subagent)"
  completed: "2026-11-16"
  tasks: 2
  files: 1
---

# Phase 18 Plan 01: Auditoria EXTR/PUBL/SRCH/UIUX e Matriz de Fechamento Summary

**One-liner:** Matriz rastreável AUD-01..AUD-04 criada com evidência estática de código/testes para EXTR/PUBL/SRCH/UIUX e handoffs objetivos para bloqueios de DB/browser/canônico, sem correções de contrato desnecessárias.

## Objective

Executar a etapa (1) de D-04 para EXTR/PUBL/SRCH/UIUX: auditar comportamento e evidências atuais, aplicar correções pontuais somente onde houver lacuna real e produzir matriz rastreável de fechamento (D-01, D-04).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Auditar EXTR/PUBL/SRCH/UIUX e construir matriz de evidência/fechamento | be2891d | `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-AUDIT-MATRIX.md` |
| 2 | Aplicar correções/testes pontuais apenas para lacunas reais identificadas na auditoria | be2891d | `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-AUDIT-MATRIX.md` (registro de evidência/handoff; sem correções de código) |

## What Was Built

- `18-AUDIT-MATRIX.md` cobrindo **EXTR-10/11/12, PUBL-10/11/12/13/14, SRCH-10/11/12, UIUX-10/11/12** com colunas de critério, código/teste inspecionado, evidência, gap, ação, status e referências.
- Evidência estática principal:
  - **EXTR:** chunking/limites/timeout/alertas de truncamento-divergência (`extract.py`, `extractor.py`, `client.py`), regra de ao menos um contato e grounding/descartes, fallback de modelos Groq e erros pt-BR explícitos (testes `test_extractor.py`, `test_extraction_core.py`, `test_extract_api.py`).
  - **PUBL:** board público sem auth, payload contact-free, detalhe/modal, reveal server-side com Turnstile+rate limit e links de candidatura pós-reveal (`public.py`, páginas/componentes públicos, `test_public_api.py`, `test_reveal_api.py`, `test_report_api.py`).
  - **SRCH:** busca `q`, filtro cidade com aliases/AND e ordenação determinística (`public.py`, `BoardToolbar.tsx`, `test_public_search.py`).
  - **UIUX:** tokens/tema dark roxo, botão "Doações" com `#facc15`/`--color-donate`, slots `AdSlot` header/sidebar/inline (`public.css`, `layout.tsx`, `AdSlot.tsx`, `page.tsx`, `JobGrid.tsx`).
- Contratos preservados confirmados por inspeção: sem login público, segredos backend-only, e referências `X-Cron-Secret`/`T-06-01` mantidas em `scripts/verify-deploy.ps1` e `docs/DEPLOY.md`.

## Verification

- **Plan verify (Task 2) executado:**
  - `cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_extractor.py tests/test_extraction_core.py tests/test_extract_api.py tests/test_public_api.py tests/test_public_search.py tests/test_reveal_api.py tests/test_report_api.py -x`
  - **Resultado:** `86 passed, 1 error` (exit 1)
  - **Bloqueio:** erro de setup DB-dependent `tests/test_extract_api.py::test_extract_requires_auth` com `sqlalchemy.exc.ProgrammingError: relation "jobs" does not exist` (DB configurado sem schema/migrações aplicadas). Não tratado como regressão de código do escopo auditado.
- **Matrix checks:** `18-AUDIT-MATRIX.md` existe e contém todos os IDs auditados (EXTR/PUBL/SRCH/UIUX) e tokens de status (`validado`, `correção aplicada`, `evidência parcial+handoff`).
- **Preserved contracts:** `scripts/verify-deploy.ps1` e `docs/DEPLOY.md` continuam com `X-Cron-Secret`; `docs/DEPLOY.md` continua com `T-06-01`.

## Deviations from Plan

None - plan executed as intended for this environment. No real code/test gaps requiring correction were identified during audit; all audited requirements were recorded with evidence and explicit handoff where execution prerequisites (migrated DB / browser / canonical runtime) were unavailable.

## Authentication Gates

None.

## Threat Flags

None. No new unplanned security-relevant surface introduced; audit focused on evidence/traceability and preserved existing gates/contracts.

## Known Stubs

None.

## Deferred Issues / Handoffs

1. **DB de testes migrado (AUD-01..AUD-03 backend):** aplicar `alembic upgrade head` no DB de testes e reexecutar a suíte direcionada do plano até exit 0 para fechar evidência automatizada DB-backed.
2. **Verificação humana/browser (PUBL/UIUX):** validar `/` e `/admin` quanto a board/cards/modal/reveal, busca/filtro/ordenação, tema dark/roxo, "Doações" `#facc15` e slots de ads.
3. **Smoke/runtime canônico:** permanece handoff operacional fora desta sessão.

## Self-Check

- FOUND: `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-AUDIT-MATRIX.md`
- FOUND: `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-01-SUMMARY.md`
- FOUND: commit `be2891d` (`docs(18-01): create audit matrix for EXTR/PUBL/SRCH/UIUX gap closure`)

## Self-Check: PASSED
