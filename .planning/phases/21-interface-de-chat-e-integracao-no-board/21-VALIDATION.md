---
phase: 21
slug: interface-de-chat-e-integracao-no-board
status: audited
nyquist_compliant: false
wave_0_complete: partial
created: 2026-11-17
updated: 2026-11-20
audited: 2026-11-20
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Frontend: Vitest 2.x (`frontend/vitest.config.ts`, node env, inclui `lib/**/*.test.ts`). Backend: pytest (referência contratos API/intent das fases 19/20). |
| **Config file** | `frontend/vitest.config.ts`, `frontend/package.json`; `backend/pyproject.toml` (contexto) |
| **Quick run command** | `npm --prefix frontend run test:chat` |
| **Full suite command** | `npm --prefix frontend run test` (Vitest run; cobertura automatizada atual focada em lógica pura de chat/apply) |
| **Estimated runtime** | ~5-30 seconds (`test:chat` / testes frontend disponíveis) |

---

## Sampling Rate

- **After every task commit:** Run `npm --prefix frontend run test:chat` ao alterar lógica de chat/mapeamento (`frontend/lib/chatApply.ts` e correlatos) e lint quando aplicável.
- **After every plan wave:** Rodar suíte frontend disponível (`npm --prefix frontend run test`) + revisar evidências de UAT/validação manual para UI-01/UI-02.
- **Before `/gsd-verify-work`:** Garantir UI-03 (mapeamento/apply canônico) verde; manter gaps de automação UI-01/UI-02 explicitamente documentados como desvio aceito com plano de ação quando não viável.
- **Max feedback latency:** 120 seconds

---

## Per-task / Requirement Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-V-01 | 21-01/21-02 | UI-01 | T-21-01/T-21-06 | Entrada de chat tratada com segurança (trim/validação server-side, sem duplicar envio), estados de carregamento/erro pt-BR, sem bypass de contratos | unit/component (gap) + evidência manual/UAT | `npm --prefix frontend run test` (parcial; sem teste dedicado de componente/hook de envio) | ❌ teste automatizado dedicado de `ChatWidget`/fluxo de envio ausente | ⚠️ parcial (evidência humana registrada) |
| 21-V-02 | 21-01/21-02 | UI-02 | T-21-02/T-21-04/T-21-05 | Interpretação/resultados renderizados como texto seguro (sem HTML injection), sem contatos no payload/UI do chat e com acesso ao detalhe canônico/reveal no fluxo existente | unit/component (gap) + evidência manual/UAT | `npm --prefix frontend run test` (parcial; sem teste dedicado de renderização segura de componentes) | ❌ teste automatizado dedicado de `ChatInterpretation`/`ChatResultsList`/`ChatResultItem` ausente | ⚠️ parcial (evidência humana registrada) |
| 21-V-03 | 21-01/21-02 | UI-03 | T-21-03/T-21-07 | `applied_params` mapeados para URL/filtros canônicos (`q/city/sort`, `page=1`, `vaga` limpo) sem inventar filtros e com gating coerente | unit | `npm --prefix frontend run test:chat` | ✅ `frontend/lib/chatApply.ts`, `frontend/lib/chatApply.test.ts` | ✅ green (evidência histórica: 6/6) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Evidência principal:**
- Automação UI-03: `frontend/lib/chatApply.test.ts` via `npm --prefix frontend run test:chat` (6 testes, evidência registrada em `21-VALIDATION.md`/`21-VERIFICATION.md`).
- Reconciliação humana: `21-HUMAN-UAT.md` **complete (4/4 pass, 2026-11-17)** e `21-VERIFICATION.md` reconciliado como `passed` em 2026-11-20 (sem nova execução runtime nesta reconciliação), cobrindo UX mobile/desktop, estados de carregamento/erro/retry/paginação, transparência de interpretação/degradação e fluxo canônico aplicar/detalhe/reveal.

---

## Wave 0 Requirements

- [x] Helper/utilitário testável para mapeamento `applied_params -> Filters/buildBoardHref` coberto por `frontend/lib/chatApply.test.ts` (UI-03).
- [x] Harness/config/scripts Vitest confirmados (`frontend/vitest.config.ts`, `frontend/package.json` scripts `test`, `test:chat`).
- [ ] Testes automatizados de UI (unit/component) cobrindo envio/erros/estados do chat (UI-01).
- [ ] Testes automatizados de UI (unit/component) cobrindo renderização segura de interpretação/resultados e ausência de contatos no chat (UI-02).
- [ ] Harness/mocks frontend dedicados para `POST /api/v1/public/chat-search` visando validação determinística de componentes (UI-01/UI-02).

*Wave 0 parcialmente completo: cobertura determinística de lógica pura (UI-03) presente; gaps de automação de componentes/UI permanecem.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| UX mobile-first do painel (sheet/drawer), foco/fechamento, camadas e ausência de sobreposição com detalhe | UI-01, UI-02 | Validação visual/acessibilidade/camadas depende de inspeção em viewport real e interação humana | Abrir chat em mobile/desktop, enviar mensagem, abrir detalhe a partir do resultado, fechar detalhe e reabrir chat; confirmar estados preservados e navegação utilizável. |
| Clareza de interpretação/guidance pt-BR (aplicado/ignorado/aproximado, limitações, fallback sem resultados automáticos) | UI-02 | Semântica/copy e legibilidade não totalmente capturáveis por asserções de lógica pura | Exercitar respostas ok/degradada/sem params e conferir “Entendi…”, status por campo, bloco de limitações/guidance e atalhos (evidência registrada em `21-HUMAN-UAT.md`). |

---

## Validation Sign-Off

- [x] All requirements/tasks have `<automated>` verify or documented Wave 0 gaps/dependencies
- [x] Sampling continuity definida para lógica de chat/mapeamento (UI-03) e revisões de evidência para UI-01/UI-02
- [x] Wave 0 covers UI-03; gaps UI-01/UI-02 explicitamente registrados
- [x] No watch-mode flags
- [x] Feedback latency < 120s (subset disponível)
- [ ] `nyquist_compliant: true` set in frontmatter (não viável integralmente sem automação adicional de UI; desvio aceito documentado)

**Approval:** conditionally approved with accepted deviation (2026-11-20)

## Accepted Deviation / Plan of Action (Desvio aceito e plano de ação)

- **Situação:** `nyquist_compliant: false` mantido de forma honesta. UI-03 possui verificação automatizada determinística (`frontend/lib/chatApply.test.ts`), e UI-01/UI-02 possuem evidência humana reconciliada (`21-HUMAN-UAT.md` 4/4 pass, `21-VERIFICATION.md` passed), porém não há testes automatizados dedicados de componentes/hooks de chat para UI-01/UI-02.
- **Plano de ação:** (1) introduzir harness de testes de componentes frontend viável no projeto (ex.: Testing Library/ambiente jsdom ou equivalente aprovado) e mocks do cliente `chatSearch`; (2) cobrir fluxos UI-01 (envio, loading/erro/retry, bloqueio de duplicidade) e UI-02 (renderização segura de interpretação/resultados, ausência de contatos, acessibilidade básica de ações); (3) integrar comandos no sampling/CI local; (4) atualizar este `21-VALIDATION.md` para `nyquist_compliant: true` quando as coberturas e sign-off estiverem evidenciadas.
- **Rastreabilidade:** gaps e evidências preservados nesta auditoria (2026-11-20) sem afirmar execução automatizada de UI não existente.