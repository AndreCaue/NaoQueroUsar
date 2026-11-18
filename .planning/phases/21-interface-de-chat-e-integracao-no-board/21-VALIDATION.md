---
phase: 21
slug: interface-de-chat-e-integracao-no-board
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-17
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Frontend: Vitest 5.0.4 (unit/component) e Playwright 1.64.0 (E2E) conforme stack; Backend de referência: pytest 9.1.1 (contrato chat-search já coberto em Phase 20) |
| **Config file** | Verificar `frontend/vitest.config*`, `frontend/playwright.config*` e scripts em `frontend/package.json` (Wave 0 confirma/ajusta) |
| **Quick run command** | `npm --prefix frontend run lint` e/ou testes unitários focados do chat (`npm --prefix frontend test -- --run <chat-tests>` quando houver) |
| **Full suite command** | Suíte frontend configurada (Vitest) + E2E/fluxo público do chat (Playwright) quando viável no ambiente |
| **Estimated runtime** | ~30-120 seconds (ajustar após Wave 0) |

---

## Sampling Rate

- **After every task commit:** Run checks rápidos relevantes (lint/typecheck/testes unitários focados do chat quando existirem)
- **After every plan wave:** Run suíte de testes da feature do chat (unit/component + e2e/smoke dos fluxos UI-01..UI-03) em ambiente viável
- **Before `/gsd-verify-work`:** Fluxos UI-01..UI-03 verdes (automatizados quando viáveis) e validação manual dos estados críticos
- **Max feedback latency:** 120 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-W0-01 | W0 | 0 | UI-01 | V5/Tampering | Entrada tratada (trim/limites coerentes), sem duplicar envio, erros exibidos com segurança | unit/e2e harness | `npm --prefix frontend test -- --run <chat-client-or-hook>` | ❌ W0 | ⬜ pending |
| 21-W0-02 | W0 | 0 | UI-02 | V4/Info Disclosure | Resultados/interpretação renderizados sem contatos e sem HTML injection; reveal só no detalhe | unit/e2e harness | `npm --prefix frontend test -- --run <chat-results-interpretation>` | ❌ W0 | ⬜ pending |
| 21-W0-03 | W0 | 0 | UI-03 | V5 | `applied_params` mapeados para URL canônica (`q/city/sort`, `page=1`, sem `vaga`) sem inventar filtros | unit | `npm --prefix frontend test -- --run <apply-board-mapping>` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Testes automatizados da UI de chat (unit/component e/ou e2e) cobrindo UI-01..UI-03 — inexistentes hoje
- [ ] Harness/mocks para `POST /api/v1/public/chat-search` no frontend (resposta ok, degradada, erro 429/4xx/timeout) para validação determinística
- [ ] Confirmar existência de configs/scripts reais de Vitest/Playwright no frontend e ajustar comandos de execução
- [ ] Helper/utilitário testável para mapeamento `applied_params -> Filters/buildBoardHref` (normalização city/slug, sort suportado, `page=1`, limpar `vaga`)

*Nota: cobertura completa de QA-01..QA-03 é responsabilidade da Phase 22; esta fase deve viabilizar validação básica alinhada a UI-01..UI-03 quando o ambiente permitir.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| UX mobile-first do painel (bottom sheet mobile/drawer ou modal desktop), foco/fechamento e ausência de sobreposição com detalhe | UI-01, UI-02 | Validação visual/acessibilidade e camadas dependem de inspeção em dispositivo/viewport | Abrir chat em mobile e desktop, enviar mensagem, abrir detalhe a partir do resultado, fechar detalhe e reabrir chat; confirmar estados preservados (D-02/D-14) |
| Clareza de interpretação/guidance pt-BR (aplicado/ignorado/aproximado, limitações, fallback sem resultados automáticos) | UI-02 | Semântica/copy e legibilidade não são totalmente capturáveis por asserção simples | Forçar respostas ok/degradada/sem params via mock/API e conferir “Entendi…”, status por campo, bloco de limitações/guidance e atalhos |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
