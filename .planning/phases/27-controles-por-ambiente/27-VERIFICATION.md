---
phase: 27-controles-por-ambiente
verified: 2026-11-22T23:06:37Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
---

# Phase 27: Controles por Ambiente Verification Report

**Phase Goal:** Operador controla exibição de anúncios e destino de doações por variáveis de ambiente, sem remover código.
**Verified:** 2026-11-22T23:06:37Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | D-01: Com `NEXT_PUBLIC_ADS_ENABLED` ausente/vazio/não explicitamente desativado, os 3 espaços publicitários (header, sidebar, inline) aparecem na interface pública. | ✓ VERIFIED | `frontend/lib/publicEnv.ts:3-8` `parseAdsEnabled` retorna `true` para `undefined`, vazio/whitespace e valores não desativados. `frontend/lib/publicEnv.test.ts:6-17` cobre default/unknown. `AdSlot` renderiza markup quando `isAdsEnabled()` true (`frontend/components/board/AdSlot.tsx:15-27`); `page.tsx` renderiza header/sidebar condicionalmente (`:71,:169`); `JobGrid.tsx:73-75` renderiza inline `AdSlot`. |
| 2 | D-02/D-03: Com flag explicitamente desativada (`false/0/off/no/disabled`, case-insensitive, trimmed), nenhum espaço publicitário aparece no DOM público; controle único/uniforme para header, sidebar e inline. | ✓ VERIFIED | `publicEnv.ts:1,6,4` usa allowlist explícita com `trim().toLowerCase()`. `publicEnv.test.ts:19-32` cobre valores e case/trim. Gate central em `AdSlot.tsx:15` `if (!isAdsEnabled()) return null;` cobre todas as variantes. `page.tsx:56,71,74-79,169-173` condiciona header/aside/layout; `JobGrid.tsx` mantém inline `AdSlot` sem condicional por placement, dependente do gate central. `grep` confirma "Espaço publicitário" apenas em `AdSlot.tsx` e `verify-ssr.ps1`. |
| 3 | D-04: Com `NEXT_PUBLIC_DONATION_URL` absoluta http/https válida, botão Doações abre URL em nova aba com `rel="noopener noreferrer"`. | ✓ VERIFIED | `publicEnv.ts:15-25` aceita apenas `http:`/`https:` via `new URL()` e normaliza `toString()`. `layout.tsx:4,35,60-69` resolve `getDonationUrl()` e renderiza `<a href={donationUrl} target="_blank" rel="noopener noreferrer" className={DONATE_CLASS}>Doações</a>`. `publicEnv.test.ts:42-50` cobre URLs válidas/normalização. |
| 4 | D-05: Com URL de doação ausente/vazia/inválida/javascript:/data:/relativa/malformada, botão Doações aponta para `/doacoes` sem `target="_blank"`. | ✓ VERIFIED | `publicEnv.ts:17,20,22-24` retorna `null` para ausente/inválido/esquema não-http(s)/parse error. `layout.tsx:70-73` fallback `<Link href="/doacoes" className={DONATE_CLASS}>Doações</Link>`. `publicEnv.test.ts:36-61` cobre `javascript:`, `data:`, `//evil.example`, `ftp:`, `not-a-url`, `/doacoes`, vazios. |
| 5 | D-06: A página `/doacoes` continua acessível independentemente da configuração de doação. | ✓ VERIFIED | `frontend/app/(public)/doacoes/page.tsx` permanece intacto com `export default function DoacoesPage()`, heading `Doações` e CTA de volta (`:8-25`). Nenhum redirect/env gate adicionado. `verify-ssr.ps1:80-82` mantém check `Assert ($doacoes -match "Doações")`. |
| 6 | Controles por ambiente sem remoção de código; comportamento seguro por padrão. | ✓ VERIFIED | `AdSlot`, `/doacoes`, `JobGrid` inline insertion e estilos de Doações permanecem no código; comportamento é condicionado por helpers. Defaults: ads visíveis quando ausente/unknown (`D-01`), doação inválida cai para `/doacoes` (`D-05`). Sem segredos `NEXT_PUBLIC_*` adicionados; env docs atualizados. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `frontend/lib/publicEnv.ts` | `parseAdsEnabled`, `isAdsEnabled`, `parseDonationUrl`, `getDonationUrl` | ✓ VERIFIED | 30 linhas. Exports presentes, static `process.env.NEXT_PUBLIC_*` access, allowlist explícita, validação `http/https` por `new URL()`. |
| `frontend/lib/publicEnv.test.ts` | Unit tests for ADS-01/DONA-01 parsing and URL validation | ✓ VERIFIED | 62 linhas, 7 testes, cobre D-01/D-04/D-05, case/trim, URLs inseguras. `npx vitest run lib/publicEnv.test.ts` => 7 passed. |
| `frontend/components/board/AdSlot.tsx` | Central ad gate returning null when ads disabled | ✓ VERIFIED | Importa `isAdsEnabled`, retorna `null` quando desabilitado, preserva `role="complementary"` e `aria-label="Espaço publicitário"`. |
| `frontend/app/(public)/layout.tsx` | Donation button with external-link or `/doacoes` fallback | ✓ VERIFIED | Usa `getDonationUrl()`, renderiza `<a target="_blank" rel="noopener noreferrer">` para URL válida ou `<Link href="/doacoes">` fallback; label/classes preservadas. |
| `frontend/scripts/verify-ssr.ps1` | Env-aware ad assertion for SSR verification | ✓ VERIFIED | Param `-AdsEnabled`, `Get-AdsEnabled` com mesma semântica D-01, asserts `>=3` quando habilitado e `==0` quando desabilitado; mantém demais checks. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `frontend/components/board/AdSlot.tsx` | `frontend/lib/publicEnv.ts` | `import isAdsEnabled` / call | ✓ WIRED | `AdSlot.tsx:1` importa, `:15` chama `isAdsEnabled()`. |
| `frontend/app/(public)/layout.tsx` | `frontend/lib/publicEnv.ts` | `import getDonationUrl` / call | ✓ WIRED | `layout.tsx:4` importa, `:35` chama `getDonationUrl()`, resultado controla render. |
| `frontend/components/board/JobGrid.tsx` | `frontend/components/board/AdSlot.tsx` | Inline `AdSlot` render; gate inside AdSlot | ✓ WIRED | `JobGrid.tsx:7,74` renderiza `<AdSlot variant="inline" />`; ocultação depende do gate central em `AdSlot`. |
| `frontend/app/(public)/page.tsx` | `frontend/components/board/AdSlot.tsx` | Header/sidebar `AdSlot`; aside conditional when ads enabled | ✓ WIRED | `page.tsx:3,71,171` usa `AdSlot`; `:56,169` condiciona por `adsEnabled`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `frontend/components/board/AdSlot.tsx` | env flag | `process.env.NEXT_PUBLIC_ADS_ENABLED` via `publicEnv` | N/A (env config, not dynamic data fetch) | ✓ N/A |
| `frontend/app/(public)/layout.tsx` | donation URL | `process.env.NEXT_PUBLIC_DONATION_URL` via `publicEnv` | N/A (env config, validated) | ✓ N/A |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Public env helper unit tests (ADS-01/DONA-01/D-01/D-04/D-05) | `cd frontend; npx vitest run lib/publicEnv.test.ts --reporter=verbose` | 1 file passed, 7 tests passed | ✓ PASS |
| Task commits recorded in SUMMARY exist | `git log --oneline --max-count=5 -- frontend/lib/publicEnv.ts frontend/lib/publicEnv.test.ts frontend/components/board/AdSlot.tsx frontend/app/(public)/layout.tsx frontend/app/(public)/page.tsx frontend/.env.example frontend/.env.local.example frontend/scripts/verify-ssr.ps1` | Found `8570cf5`, `5846c55`, `c3d2c71`, `044ae17` | ✓ PASS |
| Ad placeholder string confined to AdSlot/verify script | `git grep -n "Espaço publicitário" -- frontend` | Matches only `AdSlot.tsx` (aria/label) and `verify-ssr.ps1` (assertions) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| ADS-01 | `27-01-PLAN.md` | Espaços publicitários podem ser ocultados por flag única no `.env` (sem remover código, apenas controle de exibição) | ✓ SATISFIED | `publicEnv.ts` parse/isAdsEnabled; `AdSlot.tsx` central gate; `page.tsx` conditional header/sidebar/aside; `JobGrid.tsx` inline uses gated AdSlot; `.env.example/.env.local.example` document `NEXT_PUBLIC_ADS_ENABLED`; `verify-ssr.ps1` env-aware. REQUIREMENTS.md marks ADS-01 Phase 27 Complete. |
| DONA-01 | `27-01-PLAN.md` | Botão de Doações abre link configurado no `.env` quando configurado; comportamento seguro quando ausente/desabilitado | ✓ SATISFIED | `publicEnv.ts` parse/getDonationUrl accepts only absolute http/https; `layout.tsx` renders external `<a target="_blank" rel="noopener noreferrer">` or internal `/doacoes` fallback; `/doacoes` page preserved; env docs include `NEXT_PUBLIC_DONATION_URL`; tests cover unsafe URLs. REQUIREMENTS.md marks DONA-01 Phase 27 Complete. |

**Orphaned requirements check:** REQUIREMENTS.md Traceability maps ADS-01 and DONA-01 to Phase 27; both are declared in `27-01-PLAN.md` frontmatter `requirements`. No orphaned Phase 27 requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `frontend/lib/publicEnv.ts` | - | No TODO/placeholder/empty impl patterns found | ℹ️ Info | None |
| `frontend/components/board/AdSlot.tsx` | 15 | `return null` when ads disabled | ℹ️ Info | Intentional env gate per ADS-01/D-02, not a stub. |
| `frontend/app/(public)/layout.tsx` | - | No anti-patterns found | ℹ️ Info | None |
| `frontend/scripts/verify-ssr.ps1` | - | No anti-patterns found | ℹ️ Info | None |

### Human Verification Required

None. Core behaviors are verifiable in code and unit tests: env parsing semantics, central ad gate, conditional rendering, external anchor attributes, safe fallback, `/doacoes` accessibility, and env-aware SSR script. Optional manual smoke (browser new-tab behavior, visual layout with env toggles) may be performed during UAT but is not required to confirm goal achievement.

### Gaps Summary

No gaps found. Must-haves D-01..D-06 are implemented, wired, and supported by passing unit tests. Requirement IDs ADS-01 and DONA-01 are accounted for and satisfied.

---

_Verified: 2026-11-22T23:06:37Z_
_Verifier: OpenCode (gsd-verifier)_
