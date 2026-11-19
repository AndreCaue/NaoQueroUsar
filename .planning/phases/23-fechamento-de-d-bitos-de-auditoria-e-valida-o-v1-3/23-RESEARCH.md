# Phase 23: Fechamento de débitos de auditoria e validação v1.3 - Research

**Researched:** 2026-11-19
**Domain:** Audit/validation closure, artifact reconciliation, targeted hardening (intent city mapping + chat apply/UX), Nyquist/documentation
**Confidence:** HIGH

## User Constraints

### Locked Decisions
- **D-01:** Fazer **hardening de código + testes** do reconhecimento de cidade, não apenas revalidar 22-04. Incluir correção do edge case apontado em `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-REVIEW.md` (fallback raw-text com token `\brio\b` podendo classificar "Rio Grande do Sul"/"Rio Branco" como Rio de Janeiro no mapper de intenção) e adicionar regressões automatizadas apropriadas (backend e/ou frontend, conforme impacto).
- **D-02:** Critério de fechamento de CL-01: **fix aplicado + reteste manual/runtime registrado** do caso reportado (toolbar e chat reconhecendo/aplicando cidade cadastrada corretamente, sem marcação indevida como ignorada). O reteste deve ser executado e documentado nos artefatos de UAT/verificação quando o ambiente permitir.
- **D-03:** Rastreabilidade completa: atualizar **todos os artefatos relevantes** com a decisão/evidência final — `.planning/debug/city-filter-and-chat-ignores-registered-city.md`, `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, `22-VERIFICATION.md` (conforme resultado) e refletir a resolução no `.planning/v1.3-MILESTONE-AUDIT.md`.
- **D-04:** Evidência mínima para mudanças de código em CL-01: **testes automatizados determinísticos + atualização documental** (matriz/UAT/notas/artefatos afetados) proporcional ao risco.
- **D-05:** Cadeia Jacira (`261110-u28`, `261110-uik`): registrar **ambas como concluídas com evidência** (PLAN/SUMMARY, commits/testes existentes), deixando explícito que `261110-uik` é o **comportamento vigente** que supersede o bloqueio original de `u28`.
- **D-06:** `261111-krt` (Next 16.4.6/ESLint 9): aceitar como **concluída com evidência existente** (SUMMARY/verificação histórica), sem revalidação obrigatória salvo se o planejamento/execução identificar drift relevante.
- **D-07:** `261112-ttk` (escape hatch Turnstile teste em prod, sem SUMMARY): converter em **deferred justificado** com justificativa explícita (ex.: validação segura em produção/ambiente controlado fora do escopo local) e evidência do estado atual (PLAN existente). Não marcar como concluída sem evidência de execução.
- **D-08:** Reconciliação formal: atualizar **`.planning/STATE.md` + `.planning/v1.3-MILESTONE-AUDIT.md` + referências necessárias** (ex.: `.planning/REQUIREMENTS.md`/notas de fase/quick-task conforme aplicável) para que nenhuma das 4 tasks permaneça `missing/incomplete` no contexto de `audit-open`, citando evidência ou justificativa de deferimento por task.
- **D-09:** Fase 21: **reconciliar com UAT existente**. `21-HUMAN-UAT.md` já está completo (4/4 pass); atualizar `21-VERIFICATION.md` para sair de `human_needed` com base nessa evidência, de forma rastreável.
- **D-10:** Fase 22: executar **reteste do caso CL-01 (cidade)** exigido por D-02 e registrar resultados; para os demais itens de `22-HUMAN-UAT.md`/`22-MANUAL-UAT.md`, registrar **deferimento aceito por item** quando inviável no ambiente, em vez de tentar fechar tudo sem viabilidade. (Itens já marcados como pass em `22-HUMAN-UAT.md` devem ser preservados/reconciliados coerentemente.)
- **D-11:** Estados finais dos artefatos: levar `21-VERIFICATION.md`, `22-VERIFICATION.md`, `22-HUMAN-UAT.md` e `22-MANUAL-UAT.md` a **estados finais aceitos e rastreáveis** (coerentes com os padrões dos arquivos), documentando resultados executados e deferimentos aceitos, de modo que não permaneçam como `human_needed` / `partial` / `draft` sem resolução registrada.
- **D-12:** Política de inviabilidade: **deferimento por item com justificativa** — registrar o que foi executado, o que não foi, motivo da inviabilidade (ambiente/dados/runtime/browser/infra), risco residual e condição/ação futura para validação quando houver.
- **D-13:** Buscar **`nyquist_compliant` quando viável + desvio aceito documentado** quando não for. Criar `.planning/phases/20-api-publica-de-chat-search-resiliente/20-VALIDATION.md` (ausente) e evoluir `19-VALIDATION.md`, `21-VALIDATION.md` e `22-VALIDATION.md` conforme critérios/evidências factíveis (mapeamento de requisitos/tarefas/testes/comandos, wave 0, sign-off etc.). Para critérios não atendíveis, registrar desvio aceito com plano de ação no próprio arquivo, mantendo rastreabilidade honesta.
- **D-14:** Correções de código (quando viáveis): **corrigir `chatSearch` e `canApplyChatToBoard`; fazer a11y/foco viável**.
  - `frontend/lib/api.ts` (`chatSearch`): tratar falha de parse de JSON em resposta 200 como erro seguro tipado (`ApiError` pt-BR) em vez de exceção não normalizada.
  - `frontend/lib/chatApply.ts` (`canApplyChatToBoard`): não habilitar apply quando a cidade em `applied_params` não for normalizável para estado útil do board (evitar apply no-op para cidade-only não suportada/não-whitelist), preservando as regras canônicas existentes (`page=1`, `vaga` limpo, gating de degradado/disabled).
  - `frontend/components/board/chat/ChatPanel.tsx`, `ChatWidget.tsx`, `JobDetailDialog.tsx` e correlatos: aplicar melhorias **focadas e viáveis** de foco/a11y (ex.: foco inicial/trap no diálogo do chat quando aplicável, restauração de foco ao fechar detalhe aberto via chat). Se algum ponto não for viável sem ampliar escopo indevidamente, registrar **deferimento explícito** com justificativa.
  - Adicionar/ajustar testes determinísticos proporcionais às correções realizadas.
- **D-15:** Segurança Phase 22: **criar `SECURITY.md` da Phase 22** em `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-SECURITY.md` (ou artefato equivalente claramente referenciado) documentando controles e revisão aplicáveis ao chat-search (kill-switch/status, rate limit/limites/timeout, validação, busca determinística, privacidade/sem PII e sem contatos no payload, fallback/degradação segura, logging operacional sem conteúdo sensível) e limitações/residuais conhecidos.
- **D-16:** Auditoria final e gate: **atualizar `.planning/v1.3-MILESTONE-AUDIT.md` in-place** para refletir o estado final de cada débito (CL-01..05, debug, quick tasks, UAT/verification, Nyquist, warnings), com evidências/deferimentos aceitos, removendo/ajustando `tech_debt` e notas obsoletas conforme resolução. Validar que `gsd-sdk query audit-open` **não reporte itens novos desta fase** e que o documento permita o fechamento do milestone v1.3.

### OpenCode's Discretion
- Implementação exata do hardening do padrão `rio` no mapper (ex.: fronteiras/contexto/negações para "Rio Grande do Sul", "Rio Branco" etc.), desde que preserve detecção segura de "Rio de Janeiro"/aliases suportados e não invente cidades fora da whitelist.
- Forma concreta de tornar `canApplyChatToBoard`/mapeamento robusto a cidade não-normalizável sem quebrar casos suportados (`sao-paulo`, `rio-de-janeiro`, `belo-horizonte`, `remoto`) e sem aplicar estado vazio enganoso.
- Escopo mínimo de melhorias de foco/a11y considerado “viável” nesta fase (e registro objetivo de qualquer deferimento explícito restante).
- Estrutura/redação final dos estados aceitos em artefatos de verificação/UAT/manual/Nyquist e do `22-SECURITY.md`, desde que rastreáveis, honestos e alinhados às decisões acima.
- Forma de refletir reconciliações em `STATE.md`/`REQUIREMENTS.md` e de executar a checagem final de `audit-open` no ambiente disponível.

### Deferred Ideas (OUT OF SCOPE)
- `261112-ttk-escape-hatch-turnstile-teste-em-prod`: **deferred justificado (in-scope CL-02)** — sem SUMMARY/evidência de execução e dependente de validação segura em produção/ambiente controlado; registrar justificativa, estado atual (PLAN) e manter fora de `missing/incomplete` no audit-open.

## Project Constraints (from AGENTS.md)

- **Core value (non-regression):** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção. [VERIFIED: AGENTS.md, PROJECT.md]
- **Public board must not regress:** no new capabilities in this phase; do not break existing public search/list/detail/reveal behavior. [VERIFIED: 23-CONTEXT.md, ROADMAP.md Phase 23 boundary]
- **Contacts never exposed:** chat/search payloads and UI must not expose `contact_email`/`contact_phone`; reveal remains canonical gated flow. [VERIFIED: PROJECT.md, REQUIREMENTS.md UI-02, existing `JobPublic`/chat contracts]
- **Stack/ops constraints:** Next.js 16 App Router + Tailwind dark UI; FastAPI backend; Neon Postgres; Groq extraction/config; Turnstile anti-spam; pt-BR locale/copy; admin único. [VERIFIED: AGENTS.md]
- **GSD workflow:** project expects GSD workflow for file-changing work (not a runtime code constraint but an operational directive for execution). [VERIFIED: AGENTS.md]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CL-01 | O debug session `city-filter-and-chat-ignores-registered-city` é resolvido ou formalmente deferido com decisão registrada — filtro de cidade e chat respeitam a cidade cadastrada corretamente, com teste de regressão. | Debug/artifact inventory (diagnosed, root cause and 22-04 partial fix already present), mapper `\brio\b` false-positive hotspot in `backend/app/services/intent/mapper.py:36`, regression touchpoints `backend/tests/test_intent_mapper.py`/`test_intent_parser.py`, retest/evidence reconciliation targets `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, `22-VERIFICATION.md`, debug file, `22-MVP-EXAMPLES.md`, milestone audit. |
| CL-02 | As 4 quick tasks pendentes (`261110-u28-...`, `261110-uik-...`, `261111-krt-...`, `261112-ttk-...`) são concluídas com evidência ou convertidas em deferred justificado — nenhuma permanece `missing`/`incomplete` no `audit-open`. | Inventory shows PLAN/SUMMARY for u28/uik/krt and PLAN-only for ttk; `audit-open` currently lists all 4 as quick tasks `[missing]`; reconciliation must cite evidence/justification in `STATE.md`, `v1.3-MILESTONE-AUDIT.md`, and required references with dispositions per D-05..D-08. |
| CL-03 | Os gaps de verificação/UAT das fases 21/22 são executados e registrados (`21-VERIFICATION.md`, `22-VERIFICATION.md` saem de `human_needed`; `22-HUMAN-UAT.md` de `partial`; `22-MANUAL-UAT.md` de `draft`), com resultados documentados ou deferimento aceito para itens inviáveis no ambiente. | 21-HUMAN-UAT complete 4/4 pass vs 21-VERIFICATION human_needed (reconcilable by evidence); 22-HUMAN-UAT partial (item 1 retest pending, 2-3 pass), 22-MANUAL-UAT draft (0 executed), 22-VERIFICATION human_needed; D-10..D-12 define per-item retest/deferment and final accepted traceable states. |
| CL-04 | Os gaps Nyquist das fases 19–22 são endereçados (`20-VALIDATION.md` criado; `19/21/22-VALIDATION.md` evoluídos para `nyquist_compliant`) ou desvio aceito com plano de ação documentado. | 19/21/22 VALIDATION exist with `nyquist_compliant: false` (draft/audited-partial), 20-VALIDATION missing (and 20-VERIFICATION passed); config `workflow.nyquist_validation=true`; conventions/frontmatter and honest deviation path identified. |
| CL-05 | Avisos não-bloqueantes da auditoria tratados quando viáveis (apply no-op `canApplyChatToBoard`, foco/a11y do chat/detail, parse defensivo de `chatSearch`, `SECURITY.md` da Phase 22) e o `v1.3-MILESTONE-AUDIT.md` atualizado/refeito, permitindo o fechamento do v1.3. | Concrete code hotspots/tests for `chatApply`/`api.ts` and feasible chat/detail focus touchpoints identified; `22-SECURITY.md` absent; audit-open gate and in-place audit update required (D-14..D-16). |
</phase_requirements>

## Summary

Phase 23 is a **closure/reconciliation + targeted hardening** phase, not a feature phase. The current repository state [VERIFIED: filesystem reads, `.planning/v1.3-MILESTONE-AUDIT.md`, `gsd-sdk query audit-open` 2026-11-19] shows v1.3 implementation largely complete but blocked from clean close by tracked debts: 1 diagnosed debug session (city recognition), 4 quick tasks reported as open by audit tooling, unresolved validation/UAT artifact states for Phases 21/22, Nyquist gaps across 19–22, and a small set of non-blocking code/a11y/security-doc warnings. Planning must sequence work so **code/test hardening and deterministic evidence** come first where required, then **artifact reconciliation** (UAT/verification/validation/debug/quick-task dispositions), then **audit/state finalization and gate check**.

Most closure inputs already exist and should be reconciled rather than recreated from scratch: Phase 21 human UAT is complete (4/4 pass) while its verification is still `human_needed`; Phase 22 has substantial automated evidence but `22-HUMAN-UAT.md`/`22-MANUAL-UAT.md`/`22-VERIFICATION.md` remain non-final and include a pending retest for the reported city case; quick tasks u28/uik/krt have PLAN+SUMMARY evidence and ttk has PLAN only (explicit deferred candidate). The main implementation risks are narrow and well-localized: `backend/app/services/intent/mapper.py` raw-text city detection still contains the `\brio\b` false-positive called out in `22-REVIEW.md`; frontend apply gating can enable a misleading no-op for non-normalizable city-only params; and `chatSearch` lacks guarded JSON parsing on 200 responses. [VERIFIED: code reads, 22-REVIEW.md, 21/22 verification artifacts]

**Primary recommendation:** Plan 2–4 focused waves: (1) CL-01/CL-05 deterministic code+tests hardening and minimal feasible a11y/focus fixes, (2) CL-02/CL-03/CL-04 artifact reconciliation (including 22 retest/deferments and Nyquist/SECURITY docs), (3) audit/state/requirements/doc updates plus `gsd-sdk query audit-open` verification and `v1.3-MILESTONE-AUDIT.md` in-place closure — with every non-executable runtime check recorded as an explicit per-item accepted deferral, never left `draft/partial/human_needed` without resolution text.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Intent/city extraction fallback and safeguards | API / Backend | — | `backend/app/services/intent/mapper.py` deterministically maps untrusted NL/candidate data to safe `applied_params`/statuses; city whitelist normalization is server-authoritative. [VERIFIED: mapper.py, intent tests] |
| Public chat-search contract, protections, deterministic search | API / Backend | Database / Storage | `backend/app/api/v1/public.py` orchestrates intent→`list_published` and returns `JobPublic` results without contacts; DB query semantics stay canonical. [VERIFIED: public.py] |
| Toolbar city promotion / board canonical URL behavior | Browser / Client | — | `BoardToolbar.tsx` + `lib/cities.ts`/`filters.ts` own URL/query normalization and UI interaction. [VERIFIED: BoardToolbar.tsx, cities.ts] |
| Chat interpretation/apply/detail UX and a11y | Browser / Client | — | `ChatWidget/ChatPanel/ChatResultsList`, `chatApply.ts`, `JobDetailDialog.tsx` control dialog behavior, apply gating, and canonical detail/open flow. [VERIFIED: component reads] |
| Validation/UAT/Nyquist/audit reconciliation | Process / Planning Artifacts | — | Closure requires updating `.planning/*` artifacts, debug/session disposition, and audit-open state; no product behavior change by itself. [VERIFIED: CONTEXT, audit-open output] |
| Operational/security posture documentation for Phase 22 | Process / Documentation | API / Backend | `22-SECURITY.md` documents implemented controls/limitations (kill-switch, rate/limits, timeout, privacy/logging, fallback) evidenced in backend code/tests/artifacts. [VERIFIED: D-15, public.py, 22 artifacts] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python + FastAPI backend | per repo (`backend/`, pytest) | Intent mapping, public chat-search contract, deterministic tests | Existing implementation and all CL-01 backend touchpoints live here. [VERIFIED: backend code/tests] |
| TypeScript + Next.js (App Router) frontend | 16.4.6 (repo state) | Board/chat UI, client helpers/tests (Vitest) | Existing UI and CL-05 touchpoints are in `frontend/` with Vitest for pure logic. [VERIFIED: AGENTS.md, 22 artifacts, `frontend/package.json` context in quick task krt] |
| Pydantic v2 / pytest | repo-standard | Schema/contract validation and deterministic backend tests | Used throughout intent/chat tests and services. [VERIFIED: test files/imports] |
| Vitest (node env) | repo-standard | Frontend pure-logic/unit tests (`lib/**/*.test.ts`) | Existing pattern for `chatApply.test.ts`, `cities.test.ts`. [VERIFIED: 21-VALIDATION, test files] |
| gsd-sdk CLI | installed in environment | Phase/audit queries and artifact workflow support | `init.phase-op` and `audit-open` outputs are required evidence for planning/closure. [VERIFIED: command outputs] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Markdown planning artifacts (`.planning/**`) | n/a | Verification/UAT/validation/debug/audit reconciliation | Primary deliverables for CL-02..CL-05 closure evidence. [VERIFIED: artifact inventory] |
| Git commits | repo history | Traceability for fixes/reconciliations | Record evidence links (especially quick tasks and code fixes) when claiming completion. [VERIFIED: summaries cite commits] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Reconcile existing 21/22 artifacts with honest per-item deferment | Force-complete all manual/browser/runtime UAT now | D-10/D-12 explicitly allow accepted per-item deferment when infeasible; forcing false completion would violate "honest, traceable" closure. [VERIFIED: 23-CONTEXT D-10/D-11/D-12] |
| Minimal targeted a11y fixes in existing chat/dialog components | Introduce new dialog/focus library or broad refactor | Library/refactor risks regressions and scope creep; phase requires "viável" focused fixes or explicit deferment. [VERIFIED: D-14, no deps constraint implied] |

**Installation:** No new packages expected. Use existing backend/frontend toolchains. [ASSUMED: based on current tests/patterns; confirm if an environment is missing deps]

**Version verification:** Not re-verified against registries in this session (closure phase; repo/toolchain versions treated as established). [ASSUMED]

## Architecture Patterns

### Recommended Project Structure
```text
.planning/
├── debug/                       # debug session lifecycle/status
├── phases/{NN-name}/            # PLAN/SUMMARY/VERIFICATION/UAT/MANUAL-UAT/VALIDATION/SECURITY/REVIEW artifacts
├── quick/{id-slug}/             # quick task PLAN/SUMMARY evidence
├── v1.3-MILESTONE-AUDIT.md      # milestone debt/gate source updated in-place
├── STATE.md / REQUIREMENTS.md   # reconciliation and traceability
backend/app/services/intent/     # deterministic mapper/parser (CL-01)
backend/tests/                   # pytest regressions (CL-01 and existing intent/chat)
frontend/lib/                    # pure helpers/tests (chatApply, api, cities)
frontend/components/board/chat/  # chat UX/a11y touchpoints (CL-05)
frontend/components/board/       # canonical detail dialog/focus behavior
```

### Pattern 1: Deterministic, whitelist-safe city resolution (server + client assist)
**What:** Server mapper resolves cities only via safe whitelist/canonical rules and explicit raw-text detection; client toolbar promotes exact supported city text to canonical `city=<slug>` and clears `q` for that case. [VERIFIED: `mapper.py`, `cities.ts`, `BoardToolbar.tsx`]
**When to use:** CL-01 hardening must preserve safe detection for supported SP/RJ/BH/Remoto and avoid inventing/non-whitelist application. [VERIFIED: D-01, INT-03/requirements, mapper safeguards]
**Example:**
```python
# Source: backend/app/services/intent/mapper.py [VERIFIED: file]
_RAW_TEXT_CITY_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    ("São Paulo", (re.compile(r"\bsp\b"), re.compile(r"\bsao\s+paulo\b"))),
    ("Rio de Janeiro", (re.compile(r"\brj\b"), re.compile(r"\brio\b"), re.compile(r"\brio\s+de\s+janeiro\b"))),  # CL-01 hotspot: bare \brio\b
    ...
)
# _resolve_city_safe(...) falls back to _detect_city_from_raw_text(raw_text) when candidate.city absent
```
```ts
// Source: frontend/lib/chatApply.ts [VERIFIED: file]
export function canApplyChatToBoard(interpretation: ChatInterpretation): boolean {
  if (interpretation.meta?.degraded === true || interpretation.meta?.degradation_reason === "chat_disabled") return false;
  const hasCity = typeof p.city === "string" && p.city.trim().length > 0; // currently too permissive for no-op case
  return hasQ || hasCity || hasSort;
}
```

### Pattern 2: Honest artifact reconciliation over forced green status
**What:** Reconcile evidence-backed states (e.g. 21 UAT complete => 21 verification can be closed with evidence) and record per-item accepted deferments with justification/risk/next action where execution is infeasible; do not leave unresolved `human_needed/partial/draft` states without recorded resolution. [VERIFIED: D-09..D-12, 21/22 artifact states]
**When to use:** CL-02/CL-03/CL-04 and final audit closure. [VERIFIED: 23-CONTEXT]
**Example:**
```markdown
# Source pattern: .planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md [VERIFIED: file]
# Items can be pass/pending with explicit reason/history; final closure must make status/entries traceably resolved or accepted-deferred per item.
```

### Pattern 3: Deterministic tests for pure logic + seam-mocked backend contracts
**What:** Use pytest for intent/chat mapping/contract behaviors and Vitest for frontend pure helpers (`lib/chatApply.ts`, `lib/cities.ts`) with minimal, focused assertions. [VERIFIED: existing test files, 21/22 validation artifacts]
**When to use:** CL-01 mapper regressions and CL-05 chatApply/api parsing behavior changes (where feasible as pure/unit logic). [VERIFIED: D-04, D-14]

### Anti-Patterns to Avoid
- **Claiming runtime/manual closure without execution evidence:** D-02/D-10/D-12 require recorded retest or explicit per-item accepted deferment with reason/risk/next action. [VERIFIED: 23-CONTEXT]
- **Marking ttk "concluída" without execution evidence:** D-07 requires deferred justificado with current state (PLAN) cited. [VERIFIED: 23-CONTEXT]
- **Hardening `rio` by over-broad blocking that breaks supported "Rio"/"RJ"/"Rio de Janeiro" cases:** must preserve safe supported detection and whitelist-only application. [VERIFIED: D-01, OpenCode discretion]
- **Breaking canonical board URL/reset semantics:** apply fixes must preserve `page=1`, cleared `vaga`, supported `q/city/sort`, and no deceptive empty apply. [VERIFIED: UI-03, D-14]
- **Exposing contacts or internals in chat/search/error handling:** parse/error handling and docs must remain safe and contact-free. [VERIFIED: AGENTS.md, D-14/D-15]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| City whitelist normalization | Ad-hoc per-call string checks scattered in UI/backend | Existing canonical helpers/patterns (`resolve_city` backend, `resolveCitySlugFromText`/`normalizeFilters` frontend) and mapper safeguards | Avoids drift/invented cities and preserves consistent supported-set behavior. [VERIFIED: mapper.py, cities.ts, chatApply.ts] |
| Frontend error/status typing for HTTP transport | Generic untyped throws/`console` parsing in components | Existing `ApiError`/typed client helpers in `frontend/lib/api.ts` | Keeps pt-BR user-safe errors and consistent caller handling. [VERIFIED: api.ts patterns] |
| Closure evidence | Vague notes in chat only | Existing artifact formats (VERIFICATION/UAT/MANUAL-UAT/VALIDATION/debug/audit) with explicit statuses/evidence | Audit-open/milestone closure depends on traceable file states. [VERIFIED: audit-open, D-03/D-08/D-11/D-16] |

**Key insight:** This phase succeeds by tightening and reconciling existing contracts/artifacts, not by introducing new subsystems.

## Common Pitfalls

### Pitfall 1: `audit-open` remains non-clean after doc edits
**What goes wrong:** STATE/audit text is updated but `gsd-sdk query audit-open` still reports the same categories/items, blocking closure gate. [VERIFIED: current audit-open shows 9 items]
**Why it happens:** `audit-open` appears to derive open items from artifact/file statuses and quick-task/debug records (e.g. quick tasks listed as `missing`, debug `diagnosed`, UAT `partial/draft`, verification `human_needed`). [VERIFIED: audit-open JSON/report 2026-11-19]
**How to avoid:** Plan explicit reconciliation steps for each item category and re-run `gsd-sdk query audit-open` as a verification checkpoint. If tool semantics require specific status/file conventions, align artifacts to those conventions while preserving honest evidence/deferment text. [ASSUMED: exact quick-task "missing" heuristic not fully reverse-engineered from source here; verify during execution]
**Warning signs:** Audit text says resolved but `counts.total > 0` or same items persist.

### Pitfall 2: CL-01 "fixed" only for one path
**What goes wrong:** Mapper false positive is patched but toolbar/chat/runtime case not actually retested and documented, or one artifact remains stale. [VERIFIED: D-02/D-03 scope]
**Why it happens:** 22-04 already changed multiple layers; Phase 23 adds a narrow backend hardening plus closure evidence.
**How to avoid:** Treat CL-01 as code+tests + runtime retest + synchronized artifact updates (debug, 22 HUMAN/MANUAL/VERIFICATION/MVP-EXAMPLES as relevant, audit). [VERIFIED: D-01..D-04]
**Warning signs:** Mapper tests pass but 22 artifacts still say retest pending with no final disposition.

### Pitfall 3: Apply gating fix creates regressions for valid cases
**What goes wrong:** Fixing non-normalizable city-only apply disables valid supported flows (`sao-paulo`, `rio-de-janeiro`, `belo-horizonte`, `remoto`) or breaks sort-only/q cases. [VERIFIED: D-14, discretion]
**Why it happens:** `chatApply` currently decides from raw `applied_params`; `appliedParamsToBoardFilters` normalizes separately.
**How to avoid:** Base gating on normalized/useful board outcome (or equivalent robust check), keep degraded/disabled gating, and extend `frontend/lib/chatApply.test.ts` with both positive and no-op-negative cases. [VERIFIED: existing patterns/tests]
**Warning signs:** "Aplicar no board" disappears for supported city/sort cases or still appears for `city="campinas"` only.

### Pitfall 4: Nyquist artifacts become performative/inconsistent
**What goes wrong:** Frontmatter set to compliant without evidence, or commands/tasks don’t match repo reality. [VERIFIED: existing 19/21/22 draft/partial patterns]
**Why it happens:** Closure pressure and mixed executed/manual evidence.
**How to avoid:** Follow observed repo conventions (frontmatter + infrastructure/sampling/per-task/manual/sign-off/audit sections), set `nyquist_compliant` honestly, and document accepted deviations with plan-of-action where criteria aren’t truly satisfiable. [VERIFIED: 19/21/22 VALIDATION files; D-13]
**Warning signs:** `nyquist_compliant: true` but wave 0/manual gaps unresolved and no deviation rationale.

### Pitfall 5: A11y/focus changes regress chat detail flow
**What goes wrong:** Focus trap/initial focus added but close/minimize/detail transitions trap users or lose focus restoration. [VERIFIED: existing warnings in 21-VERIFICATION/22-REVIEW context]
**Why it happens:** Chat panel is custom dialog; detail uses native `<dialog>` and chat currently tracks `detailTriggerRef` but opens detail without passing trigger.
**How to avoid:** Prefer minimal, testable/focused adjustments (initial focus target, Escape/close consistency, pass/restore trigger where feasible). Defer explicitly if robust trap implementation would broaden scope/risk. [VERIFIED: D-14 discretion]

## Code Examples

### 1) CL-01 mapper hotspot and safe hardening target
```python
# Source: backend/app/services/intent/mapper.py [VERIFIED: file]
_RAW_TEXT_CITY_PATTERNS = (
    ("São Paulo", (re.compile(r"\bsp\b"), re.compile(r"\bsao\s+paulo\b"))),
    ("Rio de Janeiro", (re.compile(r"\brj\b"), re.compile(r"\brio\b"), re.compile(r"\brio\s+de\s+janeiro\b"))),
    ("Belo Horizonte", (re.compile(r"\bbh\b"), re.compile(r"\bbelo\s+horizonte\b"))),
    ("Remoto", (re.compile(r"\bremoto\b"), re.compile(r"\bhome[\s-]?office\b"), re.compile(r"\btrabalho\s+remoto\b"))),
)
# Recommended direction [ASSUMED: implementation choice within D-01/discretion]:
# - remove/replace bare \brio\b with stricter matching so "rio grande do sul"/"rio branco" do not map to Rio de Janeiro
# - keep supported cases (rj, rio de janeiro, and only safe "rio" forms if intentionally retained)
# - add negative and positive regression tests in backend/tests/test_intent_mapper.py (and parser contract cases if needed)
```

### 2) CL-05 `canApplyChatToBoard` no-op prevention
```ts
// Source: frontend/lib/chatApply.ts [VERIFIED: file]
export function canApplyChatToBoard(interpretation: ChatInterpretation): boolean {
  if (interpretation.meta?.degraded === true || interpretation.meta?.degradation_reason === "chat_disabled") return false;
  const p = interpretation.applied_params;
  const hasQ = typeof p.q === "string" && p.q.trim().length > 0;
  const hasCity = typeof p.city === "string" && p.city.trim().length > 0; // too permissive alone
  const hasSort = p.sort === "antigas";
  return hasQ || hasCity || hasSort;
}
// Recommended direction [ASSUMED: implementation choice within D-14/discretion]:
// derive usefulness from normalized board filters (appliedParamsToBoardFilters) so unknown/non-normalizable city-only does not enable apply.
```

```ts
// Source pattern: frontend/lib/chatApply.test.ts [VERIFIED: file]
// Add case: interpretation({ city: "campinas" }) => canApplyChatToBoard false (city-only not normalizable/useful)
// Keep existing true cases: q present, whitelisted city slug, sort antigas.
```

### 3) CL-05 defensive JSON parse in `chatSearch`
```ts
// Source: frontend/lib/api.ts [VERIFIED: file]
// Current (200 path): return (await res.json()) as ChatSearchResponse;
// Recommended: mirror getChatSearchStatus/revealContact defensive handling
try {
  return (await res.json()) as ChatSearchResponse;
} catch {
  throw new ApiError("Resposta inválida do servidor.", 0);
}
```

### 4) Feasible focus touchpoint (chat -> detail)
```tsx
// Source: frontend/components/board/chat/ChatWidget.tsx [VERIFIED: file]
const handleOpenDetail = (job: JobPublic, trigger?: HTMLElement | null) => {
  detailTriggerRef.current = trigger ?? null;
  ...
};
// Current call: onOpenDetail={(job) => handleOpenDetail(job, null)}
// Feasible improvement: pass originating trigger element/ref from ChatResultItem/ChatResultsList so onClose restores focus usefully.
// If broader focus-trap work in ChatPanel is risky, record explicit deferment with justification (D-14).
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Phase 21/22 work treated as "code complete enough" with pending human/runtime sign-off | Closure requires final accepted, traceable artifact states (or explicit per-item accepted deferments) and audit-open gate cleanliness | Phase 23 scope (2026-11-19) [VERIFIED: ROADMAP/CONTEXT] | Planning must budget reconciliation/documentation as first-class work, not afterthought. |
| City detection relied on candidate city and limited raw-text fallback; toolbar typed text stayed in `q` | 22-04 added toolbar promotion and raw-text whitelist fallback for absent candidate (current codebase state) | 22-04 / existing repo state [VERIFIED: code + debug/22 artifacts] | Phase 23 hardens remaining false-positive edge (`\brio\b`) and closes evidence loop. |
| Quick tasks tracked as pending in STATE/audit context | Must be dispositioned with evidence or justified deferral so none remain missing/incomplete in audit-open context | Phase 23 CL-02 [VERIFIED: CONTEXT, audit-open] | Requires explicit, cited dispositions and possible artifact/status alignment. |

**Deprecated/outdated:**
- Treating `22-REVIEW` warning WR-04 (`\brio\b`) as informational only: now in-scope hardening for CL-01. [VERIFIED: D-01, 22-REVIEW.md]
- Leaving 20 without Nyquist artifact: `20-VALIDATION.md` must be created (or deviated with documented plan, per D-13). [VERIFIED: D-13, phase dir listing]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Exact `gsd-sdk query audit-open` heuristics for marking quick tasks as `missing` (despite PLAN/SUMMARY presence) are not fully determined from available artifacts in this session; reconciliation must be verified against the command output after changes. | Common Pitfalls / Planning notes | Updates to STATE/audit docs may not clear quick-task items if tool expects specific file/status metadata; may require iterative artifact alignment. |
| A2 | Existing backend/frontend dev dependencies (pytest, Vitest, Node/Python env) are available in the execution environment for targeted deterministic tests. | Standard Stack / Environment Availability | Targeted regressions cannot be run; plan must record infeasibility and adjust evidence claims accordingly. |
| A3 | Runtime/browser environment and representative test data may be unavailable for all 22 manual/UAT items, so per-item accepted deferment (D-12) will likely be needed beyond the CL-01 retest. | CL-03 planning / Pitfalls | Forcing full execution claims would be dishonest; artifacts must explicitly capture residual risk and future validation conditions. |

## Open Questions (RESOLVED)

1. **What exact artifact/file-state changes make quick tasks disappear from `gsd-sdk query audit-open`?** — **RESOLVED**
   - What we know: audit-open currently lists all 4 as `quick_tasks` with `status: "missing"` and empty metadata, while u28/uik/krt have PLAN+SUMMARY and ttk has PLAN only. [VERIFIED: audit-open JSON, quick dirs]
   - Resolution (D-05..D-08, D-16): do not assume internal heuristics; execute explicit reconciliation in STATE/REQUIREMENTS/v1.3-MILESTONE-AUDIT.md (and references as needed) with evidence or justified deferral per task, then re-run `gsd-sdk query audit-open` and iteratively align permitted artifacts minimally and honestly if items persist. ttk remains PLAN-only deferred justificado (no fabricated SUMMARY/execution).

2. **Can the CL-01 runtime retest (toolbar + chat, registered city) be executed in the available environment during this phase?** — **RESOLVED**
   - What we know: D-02 requires executed and documented retest when environment permits; 22 artifacts currently show retest pending. [VERIFIED: D-02, 22-HUMAN-UAT/MANUAL-UAT]
   - Resolution (D-02, D-03, D-10, D-12): attempt runtime retest during execution and record objective evidence in debug/UAT/verification artifacts when feasible; if infeasible, record explicit per-item accepted deferral with motivo de inviabilidade (ambiente/dados/runtime/browser/infra), risco residual, e condição/ação futura. Do not leave retest pending without recorded resolution.

3. **How much focus/a11y remediation is "viável" without scope/risk creep in custom chat dialog?** — **RESOLVED**
   - What we know: gaps noted (initial focus/trap in chat dialog, focus restore when opening detail from chat). Native dialog exists for job detail; ChatPanel is custom. [VERIFIED: component reads, prior verification/review notes]
   - Resolution (D-14): implement minimal, high-value, low-risk fixes (initial focus on chat dialog open and reliable trigger propagation/focus restore when opening detail from chat). If a complete focus trap or other complex focus management is not viable without scope/risk creep, record an explicit accepted deferral with justificativa, risco residual, e condição/ação futura in the reconciliation artifacts (23-02/23-03 outputs and 22 UAT/verification/audit as applicable), without unsafe partial implementation.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `git` + repo workspace | Code/doc edits, evidence/traceability | ✓ [VERIFIED] | not probed | — |
| `gsd-sdk` CLI | `init.phase-op`, `audit-open`, closure gate checks | ✓ [VERIFIED] | not probed | Manual artifact inspection (lower confidence for gate parity) |
| Python + pytest (backend test env) | CL-01 intent regression tests and existing backend suites | ? [ASSUMED] | unknown in this session | Run targeted tests if available; if not, document inability honestly and do not claim execution |
| Node/npm + Vitest (frontend) | CL-05 `chatApply`/frontend pure-logic tests | ? [ASSUMED] | unknown in this session | Same as above |
| Running backend/frontend + browser + seeded DB data | CL-01 runtime retest, 22 manual/UAT execution items | ? [ASSUMED] | n/a | Per-item accepted deferment with justification/risk/next action (D-12) |
| Local DB/migrations for DB-backed backend tests | Some existing chat-search suites (historically env-gated) | ? [ASSUMED] | n/a | Prefer pure intent/mapping suites for CL-01; record DB-backed limitations if encountered |

**Missing dependencies with no fallback:**
- None confirmed from static research. [ASSUMED]

**Missing dependencies with fallback:**
- Runtime/browser/DB/manual-UAT environment and possibly local test runners/DB-backed setup (fallback: deterministic code/tests where possible + explicit, traceable deferment per item). [ASSUMED]

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json` (key present). Section included. [VERIFIED: config read]

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Backend: pytest (+ pytest-asyncio where used by repo). Frontend: Vitest (node env, `frontend/lib/**/*.test.ts`). [VERIFIED: 19/21/22 VALIDATION files, test files] |
| Config file | `backend/pyproject.toml`, `backend/tests/conftest.py`; `frontend/vitest.config.ts`, `frontend/package.json`. [VERIFIED: VALIDATION artifacts] |
| Quick run command | `cd backend && python -m pytest -q tests/test_intent_mapper.py tests/test_intent_parser.py` (CL-01); `cd frontend && npm run test:chat` and/or targeted cities/chatApply tests (CL-05). [ASSUMED: commands consistent with repo patterns; adjust to actual scripts/paths] |
| Full suite command | Targeted phase-relevant suites: backend intent/chat tests as environment allows; `cd frontend && npm test` (or equivalent). Manual/UAT/Nyquist evidence required for non-automatable items. [ASSUMED] |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CL-01 | Raw-text city fallback must not map "Rio Grande do Sul"/"Rio Branco" (and similar) to Rio de Janeiro; must still map supported RJ forms safely; toolbar/chat city case remains correct per documented retest | unit (pytest, deterministic) + manual/runtime retest evidence | `cd backend && python -m pytest -q tests/test_intent_mapper.py tests/test_intent_parser.py` | ✅ tests exist (extend) [VERIFIED] |
| CL-02 | 4 quick tasks dispositioned with evidence or justified deferral; no missing/incomplete in audit-open context | manual/artifact reconciliation + audit-open check | `gsd-sdk query audit-open` | n/a (docs/state) [VERIFIED] |
| CL-03 | 21/22 verification & UAT/manual artifacts moved to final accepted traceable states (with per-item deferments where needed) | manual/artifact reconciliation + evidence review | `gsd-sdk query audit-open` | ✅ artifacts exist (update) [VERIFIED] |
| CL-04 | Nyquist artifacts 19–22 compliant or accepted-deviation documented; 20-VALIDATION created | manual/artifact authoring/reconciliation | n/a (file-based) | ❌ `20-VALIDATION.md` Wave 0 gap [VERIFIED] |
| CL-05 | `canApplyChatToBoard` avoids no-op for non-normalizable city-only; `chatSearch` maps 200 JSON parse failure to safe `ApiError` pt-BR; feasible a11y/focus improvements; 22-SECURITY.md created; audit updated | unit (Vitest/TS logic where applicable) + code review + manual UX check (as feasible) | `cd frontend && npm run test:chat` (and/or targeted vitest file) | ✅ `chatApply.test.ts` exists (extend); `api.ts` helper currently untested as unit file ❓ [ASSUMED]; ❌ `22-SECURITY.md` Wave 0 gap [VERIFIED] |

### Sampling Rate
- **Per task commit:** Run the smallest relevant deterministic command for touched scope (mapper/chatApply tests) and re-check affected artifact consistency. [ASSUMED]
- **Per wave merge:** Re-run targeted backend/frontend tests touched by the wave and refresh reconciliation artifacts. [ASSUMED]
- **Phase gate:** Targeted automated tests green where runnable, CL-01 retest/deferments recorded, 21/22/19–22 artifacts finalized per decisions, `gsd-sdk query audit-open` clean of new Phase 23 items (and tracked debts resolved per D-16), `v1.3-MILESTONE-AUDIT.md` updated in-place. [VERIFIED: D-02/D-11/D-12/D-13/D-16]

### Wave 0 Gaps
- [ ] `.planning/phases/20-api-publica-de-chat-search-resiliente/20-VALIDATION.md` — create (CL-04). [VERIFIED missing]
- [ ] `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-SECURITY.md` — create/referencable security review artifact (CL-05/D-15). [VERIFIED missing]
- [ ] `backend/tests/test_intent_mapper.py` (and possibly `test_intent_parser.py`) — add negative regressions for `\brio\b` false positives and preserve valid RJ cases (CL-01). [VERIFIED files exist, coverage gap]
- [ ] `frontend/lib/chatApply.test.ts` — add non-normalizable city-only no-op case(s) and keep supported-case coverage (CL-05). [VERIFIED file exists, coverage gap]
- [ ] Reconciliation edits to existing artifacts: `19/21/22-VALIDATION.md`, `21/22-VERIFICATION.md`, `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, debug session, `STATE.md`, `REQUIREMENTS.md` (if needed), `v1.3-MILESTONE-AUDIT.md` (CL-01..CL-05). [VERIFIED]

## Security Domain

> `security_enforcement` not explicitly false in config; included as relevant to public chat endpoint and CL-05/D-15 documentation (not greenfield auth work). [VERIFIED: config]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | limited/no (public chat) | Not applicable to public chat-search; admin auth unchanged/out of scope. [VERIFIED: scope] |
| V3 Session Management | no | No session added. [VERIFIED] |
| V4 Access Control | partial | Public endpoints remain unauthenticated by design; contacts revealed only via canonical gated reveal flow, never in chat payloads. [VERIFIED: JobPublic/chat contracts, D-14/D-15] |
| V5 Input Validation | yes | Server-side validation/limits/rate limiting/timeout and safe degraded responses for chat-search; defensive client parse/error handling. [VERIFIED: public.py, api.ts, D-14] |
| V6 Cryptography | no | No crypto changes in scope. [VERIFIED] |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed/ambiguous NL causing unsafe city inference (false positives) | Tampering / Integrity of query intent | Deterministic whitelist-only mapping with strict/raw-text safeguards and regression tests; never invent non-whitelist cities. [VERIFIED: mapper design, CL-01] |
| Malformed 200 JSON from client fetch path causing untyped failure/leakage of internals | Information Disclosure / Reliability | Treat parse failure as typed safe `ApiError` (pt-BR), no raw exception/content surfaced. [VERIFIED target: D-14, api.ts pattern in status fetch] |
| Misleading UI action applying empty/no-op filters (unsupported city-only) | Spoofing/UX integrity | Gate apply by useful normalized canonical params; preserve canonical URL/reset semantics. [VERIFIED: D-14, filters/chatApply] |
| Abuse/cost/availability pressure on public chat endpoint | DoS / Elevation of cost | Keep existing rate limits, size/timeout, kill-switch/status, degraded safe fallback, no-PII structured logging (document in 22-SECURITY.md). [VERIFIED: public.py, D-15] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-CONTEXT.md` — locked decisions/discretion/deferred scope [VERIFIED]
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/v1.3-MILESTONE-AUDIT.md` — phase goal, CL requirements, current state, debts [VERIFIED]
- `gsd-sdk query init.phase-op "23"` and `gsd-sdk query audit-open` (2026-11-19) — phase paths/config flags and current open-item inventory [VERIFIED]
- Phase 21/22/19/20 artifact files read in-session (`*-VERIFICATION.md`, `*-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, `*-VALIDATION.md`, `22-MVP-EXAMPLES.md`, `22-REVIEW.md`, debug session) — statuses, evidence, gaps [VERIFIED]
- Quick task dirs `261110-u28`, `261110-uik`, `261111-krt`, `261112-ttk` (PLAN/SUMMARY presence/content) — dispositions/evidence [VERIFIED]
- Code/tests: `backend/app/services/intent/mapper.py`, `backend/tests/test_intent_mapper.py`, `backend/tests/test_intent_parser.py`, `backend/app/api/v1/public.py`, `frontend/lib/cities.ts`, `frontend/lib/cities.test.ts`, `frontend/components/board/BoardToolbar.tsx`, `frontend/lib/chatApply.ts`, `frontend/lib/chatApply.test.ts`, `frontend/lib/api.ts`, `frontend/components/board/chat/ChatWidget.tsx`, `ChatPanel.tsx`, `ChatResultsList.tsx`, `frontend/components/board/JobDetailDialog.tsx` [VERIFIED]
- `.planning/config.json` — `workflow.nyquist_validation: true` [VERIFIED]
- `AGENTS.md` — project constraints/directives [VERIFIED]

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None (no external web/library research required for this closure phase).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - based on existing repo code/tests/artifacts and verified CLI outputs.
- Architecture: HIGH - touchpoints and data/ownership boundaries verified directly in code and planning docs.
- Pitfalls: HIGH - derived from current audit-open state, explicit review findings (WR-04), and artifact status mismatches observed in files.

**Research date:** 2026-11-19
**Valid until:** 2026-12-19 (planning artifacts/code touchpoints may change if phase work starts; re-check `audit-open` and target files before planning/execution)
