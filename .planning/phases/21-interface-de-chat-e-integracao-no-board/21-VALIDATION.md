---
phase: 21
slug: interface-de-chat-e-integracao-no-board
status: audited
nyquist_compliant: false
wave_0_complete: partial
created: 2026-11-17
audited: 2026-11-17
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Frontend: Vitest 2.x (repo `frontend/package.json`) com config `frontend/vitest.config.ts` (node env, inclui `lib/**/*.test.ts`); E2E Playwright não configurado/executado nesta auditoria. Backend: pytest (referência Phase 20) |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `npm --prefix frontend run test:chat` |
| **Full suite command** | `npm --prefix frontend run test` (Vitest run; atualmente cobre `lib/chatApply.test.ts`) |
| **Estimated runtime** | ~5-15 seconds (test:chat) |

---

## Sampling Rate

- **After every task commit:** Run `npm --prefix frontend run test:chat` (quando alterando lógica de chat/mapping) e lint quando aplicável.
- **After every plan wave:** Rodar suíte frontend disponível (`npm --prefix frontend run test`) + validação manual dos fluxos UI-01..UI-03.
- **Before `/gsd-verify-work` / merge:** Garantir mapeamento UI-03 verde; completar gaps UI-01/UI-02 (component/hook) ou documentar exceções.
- **Max feedback latency:** 120 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-W0-01 | W0 | 0 | UI-01 | V5/Tampering | Entrada tratada (trim/limites coerentes), sem duplicar envio, erros exibidos com segurança | unit/component | (sem arquivo dedicado) — sugerido: testes de `ChatWidget`/`chatSearch` client com mocks | ❌ ausente | ⬜ pending |
| 21-W0-02 | W0 | 0 | UI-02 | V4/Info Disclosure | Resultados/interpretação renderizados sem contatos e sem HTML injection; reveal só no detalhe | unit/component | (sem arquivo dedicado) — sugerido: testes de `ChatInterpretation`/`ChatResultsList`/`ChatResultItem` | ❌ ausente | ⬜ pending |
| 21-W0-03 | W0 | 0 | UI-03 | V5 | `applied_params` mapeados para URL canônica (`q/city/sort`, `page=1`, sem `vaga`) sem inventar filtros | unit | `npm --prefix frontend run test:chat` | ✅ `frontend/lib/chatApply.test.ts` | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Nota (auditoria 2026-11-17):** `npm --prefix frontend run test:chat` executado com sucesso (6 testes). Gaps restantes são testes automatizados de UI para componentes do chat (UI-01/UI-02).

---

## Wave 0 Requirements

- [x] Helper/utilitário testável para mapeamento `applied_params -> Filters/buildBoardHref` coberto por `chatApply.test.ts` (UI-03)
- [ ] Testes automatizados da UI de chat (unit/component) cobrindo comportamento de envio/erros (UI-01) e renderização segura de interpretação/resultados (UI-02)
- [ ] Harness/mocks para `POST /api/v1/public/chat-search` no frontend para validação determinística (UI-01/UI-02)
- [x] Config/scripts Vitest confirmados (`frontend/vitest.config.ts`, `package.json` scripts)

*Nota: cobertura completa de QA-01..QA-03 é responsabilidade da Phase 22.*

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
- [ ] Wave 0 covers all MISSING references (parcial: UI-03 coberto; UI-01/UI-02 pendentes)
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [x] `nyquist_compliant: false` set in frontmatter (gaps restantes documentados)

**Approval:** pending

## Validation Audit 2026-11-17

| Metric | Count |
|--------|-------|
| Gaps found (initial state) | 3 (W0-01, W0-02, W0-03) |
| Resolved | 1 (W0-03 via `frontend/lib/chatApply.test.ts`, 6/6 passing) |
| Escalated / still missing | 2 (W0-01, W0-02 — no automated UI/component tests) |

**Commands run:** `npm --prefix frontend run test:chat` → PASS (6 tests).
