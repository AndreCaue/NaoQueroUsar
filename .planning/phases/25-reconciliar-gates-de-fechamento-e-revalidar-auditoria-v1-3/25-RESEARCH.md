# Phase 25: Reconciliar gates de fechamento e revalidar auditoria v1.3 - Research

**Researched:** 2026-11-22
**Domain:** GSD milestone-closure reconciliation (planning artifacts, verification/UAT gates, audit trail)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Política do gate audit-open / CL-02
- **D-01:** **Aceite formal limitado à heurística dos 4 quick tasks.** O `gsd-sdk query audit-open` pode ser considerado reconciliado para CL-02 se os únicos `[missing]` forem os 4 slugs pré-existentes conhecidos: `261110-u28-bloquear-a-expressao-jacira-chavare-ao-c`, `261110-uik-remover-jacira-chavare-do-texto-colado-s`, `261111-krt-atualizar-next-16-4-6-eslint-9`, `261112-ttk-escape-hatch-turnstile-teste-em-prod`. Cada um deve ter evidência ou deferimento justificado citado. **Nenhum outro item `[missing]` novo/inesperado** pode ser aceito por essa política; item novo bloqueia.
- **D-02:** **Demais itens do audit-open são reconciliação real, não aceite CL-02.** Os itens atuais não-CL-02 reportados pelo audit-open (23-VERIFICATION `gaps_found`, 24-VERIFICATION `human_needed`, 24-HUMAN-UAT `unknown` com 2 cenários pendentes) devem ser reconciliados nesta fase via atualização de artefatos/estados finais rastreáveis (SC2/SC3), não tratados como residual heurístico CL-02.
- **D-03:** **Registro da aceitação formal em três lugares.** Documentar a aceitação CL-02 em `v1.3-MILESTONE-AUDIT.md` (seção de gate/aceitação explícita com escopo, justificativa, evidência por task e comando observado), `REQUIREMENTS.md` (nota em CL-02) e `STATE.md` (estado/reconciliação). Manter coerência com o padrão de reconciliação da Phase 23.
- **D-04:** **CL-02 completo com aceite formal explícito.** CL-02 permanece completo/satisfeito nos artefatos de fechamento, com nota clara: disposições evidenciadas/justificadas; residual heurístico `audit-open` formalmente aceito com escopo e justificativa; sem fabricar evidência. `261112-ttk` permanece PLAN-only/deferred justificado.

#### Estratégia de reconciliação de verificação
- **D-05:** **`23-VERIFICATION.md` atualizado in-place com re-verificação datada.** Adicionar seção de re-verificação/reconciliação citando evidência da Phase 24 (24-VERIFICATION, testes determinísticos, 24-REVIEW/artefatos aplicáveis). Preservar histórico original; atualizar status/score/gaps para refletir CR-01/WR-01/WR-03 resolvidos pela Phase 24 e residuals aceitos explícitos.
- **D-06:** **Status final de 23-VERIFICATION: `gaps_closed_with_accepted_residuals`.** Reflete que gaps críticos de código foram fechados pela Phase 24, mas permanecem residuals aceitos/documentados (CL-02 heurística aceita, D-14/WR-02 focus trap deferido, deferimentos runtime/UI por item quando aplicável). Não mascarar residuals como ausência de risco.
- **D-07:** **`24-VERIFICATION.md` reconciliado para estado final aceito com deferimentos por item.** Preservar as 8/8 truths verificadas e evidência automatizada; registrar os 2 checks de teclado/browser como deferimentos aceitos por item (motivo, risco residual, ação futura), seguindo padrão D-12/22-VERIFICATION. Não rebaixar para `passed` sem qualificação nem manter `human_needed` como pendência aberta não reconciliada.
- **D-08:** **`23-REVIEW.md` permanece histórico.** Não reescrever o review point-in-time (`issues_found`, CR-01/WR-01/WR-03). A resolução é cross-referenciada em 23-VERIFICATION re-verificada, 24-VERIFICATION, e `v1.3-MILESTONE-AUDIT.md`.

#### Fechamento dos cenários 24-HUMAN-UAT
- **D-09:** **Deferimento aceito por item para os 2 cenários pendentes.** Os cenários WR-01 de `24-HUMAN-UAT.md` (foco teclado ao fechar detalhe aberto pelo chat; tentativa de fechar chat com detalhe aberto) são fechados como deferimentos aceitos por item, com motivo (ambiente browser/integrado indisponível nesta execução), risco residual, e condição/ação futura. Não afirmar execução manual não realizada.
- **D-10:** **`24-HUMAN-UAT.md` com status final `complete` (com deferimentos aceitos).** Mesmo padrão de `22-HUMAN-UAT.md`: status final rastreável `complete`, cenários pendentes resolvidos por deferimento aceito por item, sem estado ambíguo `partial`.
- **D-11:** **Expectativa de saída do audit-open por reconciliação.** Atualizar 24-HUMAN-UAT/24-VERIFICATION para estados finais aceitos/rastreáveis de modo que o scanner `audit-open` não os reporte mais como gaps abertos. Se ainda reportar por comportamento heurístico inesperado, documentar explicitamente o residual com escopo/justificativa; não aplicar aceite formal CL-02 por padrão a esses itens.

#### Forma final do v1.3-MILESTONE-AUDIT.md
- **D-12:** **Status final do audit: `passed` com residuals aceitos.** O `v1.3-MILESTONE-AUDIT.md` deve ficar closure-ready/pronto para `/gsd-audit-milestone`: requisitos v1.3 satisfeitos ou formalmente aceitos com evidência; débitos críticos resolvidos; residuals não-bloqueantes explicitamente documentados. Não manter `gaps_found` após resolução dos débitos críticos.
- **D-13:** **CL-01, CL-02 e CL-05 satisfeitos com evidência e residuals separados.** Na tabela de requisitos, marcar CL-01/CL-02/CL-05 como satisfeitos/fechados com evidência curta (Phase 24 fix determinístico + reconciliação; aceite formal CL-02; correções CL-05 viáveis + residual D-14/WR-02). Mover itens críticos resolvidos para histórico fechado/resolvido; manter apenas residuals aceitos em `tech_debt`/`accepted_residuals`.
- **D-14:** **Atualizar scores e status por fase com consistência interna.** Phase 23: `gaps_closed_with_accepted_residuals`. Phase 24: aceito com deferimentos runtime/keyboard por item. Atualizar scores (requirements/phases/integration/flows conforme evidência), resumo de Nyquist e listas de gaps para refletir estado pós-fix. Não manter scores antigos inconsistentes com o texto.
- **D-15:** **D-14/WR-02 residual aceito explícito e prontidão para re-audit.** D-14/WR-02 (focus trap completo no chat) fica somente em seção de residual aceito/tech debt com justificativa, risco residual e ação futura; nunca em gaps abertos. O audit declara explicitamente que débitos críticos foram resolvidos e que o milestone está pronto para `/gsd-audit-milestone`.

### OpenCode's Discretion
- Redação exata das seções de re-verificação/reconciliação nos artefatos, desde que preserve histórico, datas, evidências e semântica das decisões.
- Forma do estado final aceito de `24-VERIFICATION.md` (nome de status equivalente a `accepted_with_deferred_runtime_checks`/padrão 22) desde que rastreável e não ambíguo.
- Estrutura interna do `v1.3-MILESTONE-AUDIT.md` (seções/tabelas) desde que mantenha consistência de frontmatter/scores/gaps/tech_debt e clareza de re-audit.
- Nível de detalhe das notas em `STATE.md` e `REQUIREMENTS.md`, desde que citem os 4 slugs, evidência/disposição e condição “nenhum `[missing]` novo”.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

## Summary

Phase 25 is a documentation/reconciliation phase, not a product-code phase. The work is to make v1.3 closure traceable and clean by reconciling residual gate noise (CL-02 quick-task heuristic `[missing]`), updating post-fix verification/UAT artifacts for Phases 23/24, and refreshing `v1.3-MILESTONE-AUDIT.md` in-place for re-audit readiness. The critical code defects that previously blocked closure (CR-01/WR-01/WR-03) are already fixed in Phase 24 with deterministic evidence [VERIFIED: `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-VERIFICATION.md`, `24-REVIEW.md`, `24-03-SUMMARY.md` cited by 24-VERIFICATION]. What remains is artifact-state reconciliation and honest residual handling.

The current `gsd-sdk query audit-open` baseline (2026-11-22) reports 7 items: 4 quick tasks `[missing]` (u28/uik/krt/ttk), 1 UAT gap (`24-HUMAN-UAT.md` unknown, 2 pending), and 2 verification gaps (`23-VERIFICATION.md` gaps_found, `24-VERIFICATION.md` human_needed) [VERIFIED: `gsd-sdk query audit-open` executed 2026-11-22]. Per D-01/D-02, only the 4 known quick-task slugs may receive formal CL-02 heuristic acceptance if their dispositions are evidenced/justified and no new `[missing]` appears; the other 3 items require real artifact reconciliation, not CL-02 blanket acceptance.

**Primary recommendation:** Plan Phase 25 as an artifact-reconciliation wave: (1) reconcile 24-HUMAN-UAT and 24-VERIFICATION to final accepted/deferred-by-item states so the scanner no longer treats them as open gaps; (2) add a dated in-place re-verification section to 23-VERIFICATION promoting it to `gaps_closed_with_accepted_residuals` with Phase 24 evidence while preserving history; (3) update `v1.3-MILESTONE-AUDIT.md`, `REQUIREMENTS.md`, and `STATE.md` with explicit CL-02 formal acceptance scope, D-14/WR-02 residual separation, and re-audit readiness; (4) rerun `gsd-sdk query audit-open` and document the exact outcome honestly.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CL-02 | Quick tasks reconciliadas com evidência ou deferimento justificado: u28/uik/krt concluídas com evidência (uik vigente supersede u28) e ttk como deferred justificado (PLAN-only, sem SUMMARY/evidência de execução; validação segura em produção/ambiente controlado fora do escopo local), com nenhuma permanecendo sem disposição documentada no contexto de fechamento. Se `gsd-sdk query audit-open` ainda reportar essas 4 tasks pré-existentes como `[missing]` por heurística, o residual pode ser formalmente aceito no gate/audit de fechamento do milestone quando as disposições estiverem evidenciadas/justificadas, sem itens novos desta fase e sem fabricar evidência. | D-01..D-04, D-11, audit-open baseline evidence, quick-task artifact inventory, REQUIREMENTS/STATE/audit three-place registration pattern |
| CL-05 | Avisos não-bloqueantes tratados quando viáveis (`chatSearch` parse defensivo, `canApplyChatToBoard` sem no-op para cidade-only não normalizável, melhorias focadas de foco/a11y com residual de focus-trap explicitamente deferido/propagado, `22-SECURITY.md` criado) e `v1.3-MILESTONE-AUDIT.md` atualizado in-place para fechamento rastreável do milestone. | D-05..D-08, D-12..D-15: Phase 24 already delivered viable CR-01/WR-01/WR-03 code fixes; Phase 25 closes CL-05 by reconciling verification/audit text, preserving D-14/WR-02 as accepted residual (not open gap), and updating milestone audit in-place |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- **GSD workflow enforcement:** Before using Edit, Write, or other file-changing tools, work through a GSD command so planning artifacts and execution context stay in sync. [VERIFIED: `AGENTS.md`]
- **Use GSD entry points:** `/gsd-quick` for small fixes/docs/ad-hoc, `/gsd-debug` for investigation, `/gsd-execute-phase` for planned phase work; do not bypass workflow unless user explicitly asks. [VERIFIED: `AGENTS.md`]
- **Core product constraints remain binding:** pt-BR, dark minimal UI, no login/friction for public users, contacts never exposed in chat payload, admin-only master flow, fixed stack decisions (Next.js 16.4.x, FastAPI, Neon, Groq, Turnstile). [VERIFIED: `AGENTS.md`, `PROJECT.md` section in AGENTS]
- **No regression rule:** Phase 25 must not change public/API/JobPublic contracts or introduce product behavior changes; it reconciles artifacts only. [ASSUMED - consistent with phase boundary; confirm during planning]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CL-02 quick-task disposition evidence | Planning/artifact tier (`.planning/quick/*`, `STATE.md`, `REQUIREMENTS.md`, milestone audit) | Tooling/ops tier (`gsd-sdk query audit-open`) | Disposition is documentary evidence; audit-open is a scanner signal to interpret, not the source of truth for fabricated execution. [VERIFIED: D-01..D-04, quick task files, audit-open output] |
| Phase 23 post-fix reconciliation | Planning/artifact tier (`23-VERIFICATION.md`) | Code evidence tier (`24-VERIFICATION`, intent/chat tests) | 23-VERIFICATION must reflect reality after Phase 24 code fixes while preserving historical record. [VERIFIED: D-05/D-06/D-08] |
| Phase 24 runtime/UAT residual closure | Planning/artifact tier (`24-HUMAN-UAT.md`, `24-VERIFICATION.md`) | Human/browser runtime tier (future) | No browser runtime available now; residuals become accepted-by-item deferments with explicit risk/future action. [VERIFIED: D-07/D-09/D-10/D-12 pattern] |
| Milestone re-audit readiness | Planning/artifact tier (`v1.3-MILESTONE-AUDIT.md`) | Roadmap/requirements/state traceability | Audit is the closure gate consumed by `/gsd-audit-milestone`; it must separate resolved gaps from accepted residuals. [VERIFIED: D-12..D-15, ROADMAP SC3] |
| D-14/WR-02 focus trap residual | UI/product debt tier (deferred) | Audit/verification documentation tier | Full focus trap remains intentionally deferred; Phase 25 documents it as accepted residual only. [VERIFIED: D-15, 23/24 context, 24-REVIEW WR-02] |

## Standard Stack

### Core
| Library/Tool | Version/Source | Purpose | Why Standard | Confidence |
|-------------|----------------|---------|--------------|------------|
| GSD planning artifacts | Repo `.planning/*` markdown/YAML frontmatter | Source of truth for phase/milestone closure | Existing project workflow; all prior reconciliations use it | HIGH |
| `gsd-sdk query audit-open` | gsd-sdk CLI (installed in environment) | Operational gate scan for missing/open closure artifacts | Explicitly named by SC1/SC6/D-01/D-11; observed current baseline | HIGH |
| Git working tree | repo-local | Evidence/history preservation | Artifacts are versioned; no fabrication | HIGH |

### Supporting
| Tool | Version | Purpose | When to Use | Confidence |
|------|---------|---------|-------------|------------|
| `gsd-sdk query commit` | gsd-sdk CLI | Commit docs/planning artifacts per phase convention | After artifact reconciliation, if commit_docs true | HIGH |
| ripgrep/Read/Grep | local tools | Verify strings/statuses/evidence references before claiming reconciliation | During plan execution and verification | HIGH |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| In-place artifact reconciliation | New parallel "final" files | In-place is explicitly required by D-05/D-12 and keeps canonical paths stable; new files would fragment audit trail |
| Accepting all audit-open items as CL-02 | Strict reconciliation by item type | Blanket acceptance would hide real open UAT/verification gaps; D-01/D-02 forbid it |
| Marking 24-VERIFICATION `passed` | `accepted_with_deferred_runtime_checks` / equivalent qualified state | Plain `passed` would hide browser/runtime deferments; D-07 requires qualified final state |

**Installation:**
```bash
# No new packages. Use existing repo tools and gsd-sdk.
```

**Version verification:** Not applicable - no dependency changes. [VERIFIED: phase boundary, config]

## Architecture Patterns

### System Architecture Diagram

```text
[Phase 24 code fixes + summaries/reviews]
        |  (evidence)
        v
[Phase 25 reconciliation planner/executor]
        |-------------------------------|-------------------------------|
        v                               v                               v
[23-VERIFICATION.md]          [24-VERIFICATION.md]             [24-HUMAN-UAT.md]
 in-place re-verification      qualified accepted state          complete w/ accepted deferments
 (D-05/D-06)                   (D-07)                            (D-09/D-10)
        \                               |                               /
         \                              v                              /
          --------------------> [v1.3-MILESTONE-AUDIT.md] <-------------
                                  passed + accepted residuals (D-12..D-15)
                                        |
                        ----------------+----------------
                        v                                 v
                 [REQUIREMENTS.md CL-02/CL-05]      [STATE.md reconciliation]
                        \                                 /
                         +-------> [gsd-sdk audit-open] <------+
                                      observed outcome
                                only known 4 quick [missing] may be
                                formally accepted if no new missing (D-01/D-11)
```

### Pattern 1: In-place reconciliation with preserved history
**What:** Add dated reconciliation/re-verification sections to existing artifacts; update frontmatter/status/scores; keep original findings/history intact.
**When to use:** 23-VERIFICATION, v1.3-MILESTONE-AUDIT, any artifact where prior state is audit evidence.
**Example:**
```markdown
## Re-verification / Reconciliation (2026-11-22)

**Supersedes status for closure:** gaps_closed_with_accepted_residuals
**Reason:** CR-01/WR-01/WR-03 closed by Phase 24 deterministic evidence; residuals accepted by item.

| Prior gap | Phase 24 evidence | Current disposition |
|-----------|-------------------|---------------------|
| CR-01 ... | 24-VERIFICATION truth 1/2/3, intent tests | closed |
```
[ASSUMED - pattern derived from 23-CONTEXT D-07/D-12 and existing 22/23 artifacts; exact wording discretionary]

### Pattern 2: Accepted deferment by item
**What:** For runtime/browser checks that cannot be executed, record each item with motivo, risco residual, condição/ação futura; set artifact to final accepted/complete state.
**When to use:** 24-VERIFICATION human checks, 24-HUMAN-UAT pending scenarios, any residual not executable locally.
**Example:**
```markdown
| Item | Status | Motivo | Risco residual | Ação futura |
|------|--------|--------|----------------|-------------|
| WR-01 keyboard focus restore | deferred_accepted | Browser integrado indisponível nesta execução | Regressão de foco em ambiente real | Revalidar em browser com teclado/Escape e registrar evidência |
```
[VERIFIED: pattern exists in `22-HUMAN-UAT.md` and `22-VERIFICATION.md`]

### Pattern 3: Formal heuristic acceptance with scope guard
**What:** Accept a tool heuristic only for explicitly named known items, with command output, evidence/disposition per item, and "no new missing" condition.
**When to use:** CL-02 audit-open quick-task `[missing]` residual.
**Example:**
```markdown
### CL-02 Audit-Open Formal Acceptance
- Command observed: `gsd-sdk query audit-open` (2026-11-22)
- Accepted residual scope: only the 4 known quick slugs listed below
- Condition: no other `[missing]`/new unexpected item
- ttk: PLAN-only deferred justificado, no execution evidence fabricated
```
[VERIFIED: D-01/D-03/D-04; observed audit-open command]

### Anti-Patterns to Avoid
- **Blanket-accepting audit-open:** Do not mark 24-HUMAN-UAT/24-VERIFICATION as "accepted because audit-open is noisy" under CL-02; D-02 requires real reconciliation. [VERIFIED: D-02]
- **Fabricating runtime evidence:** Do not claim browser/keyboard checks passed. Use deferred-by-item. [VERIFIED: D-07/D-09, AGENTS/project honesty rules]
- **Rewriting 23-REVIEW.md:** It is historical point-in-time evidence. [VERIFIED: D-08]
- **Promoting 24-VERIFICATION to plain passed:** This hides keyboard/browser deferment. [VERIFIED: D-07]
- **Leaving D-14/WR-02 in open gaps:** It is accepted residual only. [VERIFIED: D-15]
- **Inconsistent scores/frontmatter:** Audit/verification frontmatter must match body text. [VERIFIED: D-14, current 23-VERIFICATION/milestone audit pattern]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Closure evidence tracking | New scripts/databases | Existing markdown artifacts with dated sections/tables | Project closure workflow already audit-driven; scripts add moving parts and no requirement asks for them |
| Runtime keyboard validation | Fake "passed" entries or speculative screenshots | Accepted deferment-by-item records | Honesty constraint; browser not available in this execution [VERIFIED: D-07/D-09] |
| Audit-open interpretation | Ad-hoc mental rule | D-01/D-02 scope guard encoded in audit/STATE/REQUIREMENTS text | Prevents future agents from misclassifying new missing items as accepted |
| Status taxonomy | Freeform statuses per file | Existing patterns: `complete`, `accepted_with_deferred_runtime_checks` (or equivalent), `gaps_closed_with_accepted_residuals`, audit `passed` with accepted residuals | Keeps scanner/human interpretation consistent [VERIFIED: 22/23/24 artifacts] |

**Key insight:** This phase's main risk is evidence integrity, not technical implementation. The planner should optimize for traceable, internally consistent artifact states.

## Common Pitfalls

### Pitfall 1: Reconciling the wrong audit-open items under CL-02
**What goes wrong:** Planner treats 24-HUMAN-UAT/24-VERIFICATION gaps as CL-02 heuristic residual and only writes acceptance text.
**Why it happens:** Current audit-open shows 7 items and Phase 25 name emphasizes CL-02.
**How to avoid:** Split work by D-01 vs D-02. First reconcile non-CL-02 items by changing their artifact states; only then apply CL-02 formal acceptance to the 4 known quick slugs if still `[missing]`.
**Warning signs:** Plan has no tasks editing `24-HUMAN-UAT.md`/`24-VERIFICATION.md`/`23-VERIFICATION.md` but claims audit-open clean.

### Pitfall 2: 23-VERIFICATION loses historical truth
**What goes wrong:** Old CR-01/WR-01/WR-03 findings overwritten/deleted; future auditors cannot see what was found and when.
**Why it happens:** Desire to make status green.
**How to avoid:** Preserve original report body; add dated re-verification section; update frontmatter/status/score with explicit supersession note. Keep 23-REVIEW unchanged. [VERIFIED: D-05/D-08]
**Warning signs:** 23-REVIEW edited; 23-VERIFICATION no longer mentions CR-01 as prior finding.

### Pitfall 3: Qualified deferment downgraded to ambiguous pass/fail
**What goes wrong:** 24-VERIFICATION becomes `passed` despite unexecuted keyboard/browser checks, or remains `human_needed` after explicit accepted deferment.
**Why it happens:** Over-simplifying status.
**How to avoid:** Use final accepted-with-deferred-runtime-checks pattern from 22-VERIFICATION, adapted to Phase 24. [VERIFIED: D-07]
**Warning signs:** No per-item motivo/risco/ação futura for the 2 WR-01 checks.

### Pitfall 4: Audit scores inconsistent with body
**What goes wrong:** `v1.3-MILESTONE-AUDIT.md` frontmatter says `gaps_found` or old scores while body says passed/ready.
**Why it happens:** Partial edits.
**How to avoid:** Update frontmatter, phase table, requirements table, integration/flows, Nyquist, tech_debt/accepted_residuals, conclusion, and audit-open gate section together. [VERIFIED: D-12/D-14]
**Warning signs:** `status: gaps_found` remains; CL-01/CL-02/CL-05 still unsatisfied; Phase 23 still `gaps_found` in table.

### Pitfall 5: ttk accidentally treated as executed
**What goes wrong:** SUMMARY invented or audit text implies production validation done.
**Why it happens:** Desire to clear `[missing]`.
**How to avoid:** Keep ttk as PLAN-only deferred justificado; cite `261112-ttk-PLAN.md`; explicitly state no SUMMARY/execution evidence. [VERIFIED: D-04, ttk dir contains only PLAN]
**Warning signs:** Any claim of Render/Vercel/Turnstile execution evidence for ttk.

### Pitfall 6: Requirement/status regressions during reconciliation
**What goes wrong:** CL-05 or CL-01 accidentally flipped back to Pending/unsatisfied in REQUIREMENTS.md or audit, or CL-02 marked complete without the required formal-acceptance note.
**Why it happens:** Bulk edits across many artifacts.
**How to avoid:** Treat REQUIREMENTS.md as authoritative traceability: CL-01 and CL-05 are currently `[x]`/Complete; CL-02 is `[ ]`/Pending and must become satisfied only with D-03/D-04 formal acceptance wording. Preserve D-14/WR-02 residual separation. [VERIFIED: `.planning/REQUIREMENTS.md` lines for CL-01/CL-02/CL-05; D-04/D-13/D-15]
**Warning signs:** CL-05 unchecked; CL-02 checked with no acceptance scope; D-14/WR-02 appears in open gaps.

## Code Examples

Phase 25 has no product code to implement. The "code" is artifact structure. Use these verified reference patterns:

### Accepted deferment row (from 22-HUMAN-UAT pattern)
```markdown
| # | Cenário | Status | Motivo | Risco residual | Ação futura |
|---|---------|--------|--------|----------------|-------------|
| 1 | ... | deferred_accepted | Ambiente browser/integrado indisponível nesta execução | ... | Revalidar em ambiente integrado com teclado/browser ... |
```
[VERIFIED: `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md`]

### Verification frontmatter reconciliation (from 22-VERIFICATION pattern)
```yaml
---
phase: 24-corrigir-conflito-critico-de-cidade-e-residuos-de-review
status: accepted_with_deferred_runtime_checks
score: 8/8 must-haves verified
human_verification_resolutions:
  - test: "..."
    resolution: "deferred accepted by item ..."
---
```
[VERIFIED: pattern observed in `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-VERIFICATION.md`; adapt names carefully]

### Audit-open command capture
```bash
gsd-sdk query audit-open
```
[VERIFIED: executed 2026-11-22; returns 7 items baseline]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Phase 23 closure treated as final | Phase 24 closed CR-01/WR-01/WR-03 in code; Phase 25 reconciles artifacts/gates | 2026-11-21/22 | Closure evidence must reflect post-fix reality [VERIFIED: 24-VERIFICATION, ROADMAP Phase 24 complete] |
| 24-HUMAN-UAT `partial` pending | Final `complete` with accepted deferments by item | Phase 25 target | Removes ambiguous open UAT state [VERIFIED: D-10] |
| 24-VERIFICATION `human_needed` | Qualified accepted final state with deferred runtime checks | Phase 25 target | Keeps runtime honesty while allowing closure [VERIFIED: D-07] |
| v1.3 audit `gaps_found` | `passed` with accepted residuals, ready for `/gsd-audit-milestone` | Phase 25 target | Milestone can re-audit without critical open gaps [VERIFIED: D-12/D-15] |

**Deprecated/outdated:**
- Treating 23-REVIEW CR-01/WR-01/WR-03 as open code gaps after Phase 24: outdated for closure, but review remains historical record. [VERIFIED: D-08, 24-VERIFICATION]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `accepted_with_deferred_runtime_checks` (or a clearly equivalent qualified name) is acceptable for 24-VERIFICATION as long as it is traceable and not ambiguous. | D-07 / Status taxonomy | Audit-open or human reviewers may expect exact prior string; mitigate by matching 22-VERIFICATION pattern closely and stating equivalence in text. |
| A2 | Updating 24-HUMAN-UAT to `status: complete` with deferred accepted items and updating 24-VERIFICATION to a qualified accepted final state will remove those two items from `gsd-sdk query audit-open`. | D-11 | Scanner may key off different fields; if so, document unexpected heuristic residual explicitly without CL-02 blanket acceptance. |
| A3 | Phase 25 can mark CL-05 complete in REQUIREMENTS traceability once audit/verification reconciliation is updated, because viable code fixes already landed in 23/24 and remaining focus trap is explicitly deferred residual. | Requirements coverage | Traceability reviewers may want narrower wording; mitigate by citing evidence and residual separation clearly. |
| A4 | No code/runtime changes are needed; all required evidence already exists in repo artifacts and command outputs. | Scope | If planner finds missing evidence references, may need small additional doc lookups, but must not fabricate execution. |

## Open Questions (RESOLVED)

1. **RESOLVED: Will `audit-open` drop 23/24 verification/UAT items after status reconciliation?**
   - What we knew: Current baseline reports them as `gaps_found`/`human_needed`/`unknown`. D-11 expects reconciliation to remove them. [VERIFIED: audit-open output, D-11]
   - What was unclear: Exact scanner heuristics/fields used by `gsd-sdk query audit-open`. [ASSUMED]
   - Resolution: Plans reconcile 24-HUMAN-UAT/24-VERIFICATION/23-VERIFICATION to the 22-HUMAN-UAT / 22-VERIFICATION accepted-deferment patterns, then run `gsd-sdk query audit-open` after edits. If any non-CL-02 residual remains unexpectedly, it is treated as a blocking reconciliation gap or explicitly documented outside CL-02 scope; **never** blanket-accepted under CL-02 unless it is one of the 4 known quick slugs (D-01/D-02/D-11).

2. **RESOLVED: What exact frontmatter fields does audit-open use for UAT/verification?**
   - What we knew: 24-HUMAN-UAT currently `partial` with `result: [pending]`; 24-VERIFICATION currently `human_needed` with `human_verification` section. [VERIFIED: files]
   - What was unclear: Minimal field set for "closed/accepted".
   - Resolution: Do not guess scanner internals. Mirror 22-HUMAN-UAT (`status: complete`, per-item deferred accepted, no pending scenarios) and 22-VERIFICATION (`status: accepted_with_deferred_runtime_checks` or clearly equivalent qualified name, reconciliation/resolution sections, preserved truths/evidence) as closely as possible, then verify with post-edit `gsd-sdk query audit-open`. Any unexpected field-sensitivity is handled by the same D-11 guard: reconcile/document explicitly, no CL-02 blanket acceptance.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `gsd-sdk` CLI | audit-open baseline and post-reconciliation gate check | ✓ | CLI help available; command executed successfully | — |
| Git repo / filesystem | reading/updating planning artifacts | ✓ | Windows workspace, git repo present | — |
| Node/Python/test runtimes | Not required for this phase | ✓ (present in env) | Not needed | No execution required; cite existing deterministic evidence |
| Browser/integrated runtime | WR-01 keyboard checks in 24-HUMAN-UAT / 24-VERIFICATION | ✗ (not used in this research/execution context) | — | Accepted deferment by item per D-07/D-09 |

**Missing dependencies with no fallback:**
- None for Phase 25 documentation reconciliation.

**Missing dependencies with fallback:**
- Browser/integrated runtime — fallback is explicit deferred acceptance by item with motivo, risco residual, ação futura (no fabricated execution). [VERIFIED: D-07/D-09/D-12]

## Validation Architecture

> `workflow.nyquist_validation` is enabled in `.planning/config.json` (`true`). [VERIFIED: config]

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None required for this phase (artifact reconciliation only) |
| Config file | none — existing repo test configs unchanged |
| Quick run command | `gsd-sdk query audit-open` |
| Full suite command | `gsd-sdk query audit-open` + targeted artifact consistency checks (`rg -n "status:|gaps_found|human_needed|partial|CL-02|D-14/WR-02" .planning/...`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CL-02 | 4 known quick tasks have evidence/deferment; any remaining audit-open `[missing]` limited to those 4 with explicit formal acceptance; no new missing | smoke/manual-doc | `gsd-sdk query audit-open` | ✅ command available |
| CL-05 | Verification/audit artifacts reflect post-fix state; D-14/WR-02 documented only as accepted residual; audit ready for re-audit | smoke/manual-doc | `rg -n "gaps_closed_with_accepted_residuals|accepted_with_deferred_runtime_checks|passed" .planning/phases/23-*/23-VERIFICATION.md .planning/phases/24-*/24-VERIFICATION.md .planning/v1.3-MILESTONE-AUDIT.md` | ✅ files exist |

### Sampling Rate
- **Per task commit:** `gsd-sdk query audit-open` after each reconciliation group (or at minimum after all artifact edits)
- **Per wave merge:** Same command plus consistency grep for statuses/scores/CL-02/CL-05/D-14
- **Phase gate:** Audit-open outcome documented honestly; `v1.3-MILESTONE-AUDIT.md` internally consistent and marked ready for `/gsd-audit-milestone`

### Wave 0 Gaps
- [ ] No new test framework/files needed — phase produces planning artifacts only.
- [ ] Optional: create a tiny checklist in plan verification steps; no code test scaffolding.

*(No automated code-test Wave 0 required; validation is artifact-state and gate-command verification.)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth/code changes; artifact edits only |
| V3 Session Management | no | No session/runtime changes |
| V4 Access Control | no | No access-control code changes |
| V5 Input Validation | no (code) / yes (process integrity) | Do not fabricate evidence; preserve historical records; cite command outputs and file paths |
| V6 Cryptography | no | No crypto changes |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Evidence fabrication / false closure | Tampering / Repudiation | Per-item deferred acceptance, cite existing artifacts/commands, keep ttk PLAN-only, preserve 23-REVIEW history [VERIFIED: D-04/D-08/D-09] |
| Gate laundering (hiding real gaps under CL-02) | Tampering | D-01 scope guard: only 4 known quick slugs; any new `[missing]` blocks [VERIFIED: D-01/D-02] |
| Residual misclassification (D-14/WR-02 becomes open gap or hidden) | Information Disclosure / Process failure | Keep D-14/WR-02 only in accepted residual/tech debt with risk/future action [VERIFIED: D-15] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/25-reconciliar-gates-de-fechamento-e-revalidar-auditoria-v1-3/25-CONTEXT.md` - locked decisions D-01..D-15
- `.planning/ROADMAP.md` - Phase 25 goal/success criteria
- `.planning/REQUIREMENTS.md` - CL-01..CL-05 definitions/traceability
- `.planning/STATE.md` - current position, quick task dispositions, deferred items
- `.planning/v1.3-MILESTONE-AUDIT.md` - current gaps_found audit to update in-place
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-VERIFICATION.md` - current gaps_found state
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-REVIEW.md` - historical issues_found review
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-VERIFICATION.md` - 8/8 truths, human_needed
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-HUMAN-UAT.md` - partial, 2 pending
- `.planning/phases/24-corrigir-conflito-critico-de-cidade-e-residuos-de-review/24-REVIEW.md` - non-blocking residuals context
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-HUMAN-UAT.md` - complete-with-deferred pattern
- `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-VERIFICATION.md` - accepted_with_deferred_runtime_checks pattern
- `.planning/phases/23-fechamento-de-d-bitos-de-auditoria-e-valida-o-v1-3/23-CONTEXT.md` - D-07/D-12/D-13/D-14/D-16 prior patterns
- `.planning/quick/261110-u28-.../{PLAN,SUMMARY}.md`, `.planning/quick/261110-uik-.../{PLAN,SUMMARY}.md`, `.planning/quick/261111-krt-.../{PLAN,SUMMARY}.md`, `.planning/quick/261112-ttk-.../PLAN.md` - quick task evidence/disposition
- `gsd-sdk query audit-open` (executed 2026-11-22) - live baseline: 7 items, 4 quick missing, 1 UAT gap, 2 verification gaps

### Secondary (MEDIUM confidence)
- `.planning/config.json` - workflow/commit_docs/nyquist flags affecting planning behavior

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new tech; existing GSD artifacts/tools verified in repo
- Architecture: HIGH - reconciliation flow directly derived from D-01..D-15 and observed artifact states
- Pitfalls: HIGH - grounded in current audit-open baseline and prior Phase 22/23 reconciliation patterns

**Research date:** 2026-11-22
**Valid until:** 2026-12-22 (stable internal workflow; revalidate if audit-open semantics or artifact statuses change)
