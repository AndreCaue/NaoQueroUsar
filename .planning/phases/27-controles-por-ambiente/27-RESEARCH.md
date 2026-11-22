# Phase 27: Controles por Ambiente - Research

**Researched:** 2026-11-22
**Domain:** Next.js App Router env-driven feature flags / public UI config (frontend-only phase)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Quando a flag única de anúncios no `.env` estiver ausente ou vazia, o padrão é **mostrar anúncios** (comportamento atual preservado). O operador precisa desativar explicitamente para ocultar.
- **D-02:** Quando a flag estiver desativada, **todos os espaços publicitários** não aparecem na interface pública: header (`AdSlot` variant `header`), sidebar (`AdSlot` variant `sidebar`) e inline no grid (`AdSlot` variant `inline` inserido pelo `JobGrid`). Quando ativada, voltam a ser exibidos normalmente (SC1/SC2).
- **D-03:** O controle é único/uniforme — não há exceção por placement nesta fase.
- **D-04:** Quando o link de doação estiver configurado no `.env`, o botão "Doações" do header abre o link configurado **diretamente em nova aba** (`target="_blank"` + `rel="noopener noreferrer"`), sem passar pela página interna `/doacoes` (SC3).
- **D-05:** Quando o link de doação estiver ausente ou desabilitado, o botão "Doações" mantém comportamento seguro: leva para a página interna `/doacoes` (comportamento atual), sem destino inválido (SC4).
- **D-06:** A página interna `/doacoes` continua existindo e acessível mesmo quando o link externo estiver configurado (útil para acesso direto/bookmarks/SEO). O botão do header aponta para o externo quando configurado; a página em si não precisa redirecionar.

### OpenCode's Discretion
- Nome exato das variáveis de ambiente, formato aceito (ex.: `true/false/1/0`) e validação/sanitização de valores.
- Onde declarar cada variável (frontend `.env`/Vercel para UI pública; manter convenção `NEXT_PUBLIC_*` apenas quando necessário no client bundle, sem segredos).
- Comportamento de layout quando anúncios ocultos (colapso de espaço vs preservação) desde que os espaços publicitários não apareçam na interface pública.
- Validação do link de doação (ex.: aceitar apenas URL absoluta http/https) para garantir comportamento seguro quando valor inválido.
- Ajustes mínimos na página `/doacoes` para refletir o estado configurado, se útil, sem alterar o escopo da fase.
- Atualização de testes/scripts afetados (ex.: `frontend/scripts/verify-ssr.ps1` assume "Espaço publicitário") para cobrir os dois estados de ambiente.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADS-01 | Espaços publicitários podem ser ocultados por flag única no `.env` (sem remover código, apenas controle de exibição) | Central gate in `AdSlot.tsx` reading `NEXT_PUBLIC_ADS_ENABLED` via testable helper; default-show semantics preserve current behavior; covers header/sidebar/inline placements; verify-ssr updated for env states |
| DONA-01 | Botão de Doações abre link configurado no `.env` quando configurado; comportamento seguro quando ausente/desabilitado | `NEXT_PUBLIC_DONATION_URL` read in public layout; sanitized http/https-only URL helper; external `<a target="_blank" rel="noopener noreferrer">` when valid, internal `<Link href="/doacoes">` fallback otherwise; `/doacoes` remains accessible |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- **Tech stack — Frontend:** Next.js 16 (App Router, `16.4.6`) + Tailwind CSS + dark mode — fixed. [VERIFIED: frontend/package.json]
- **Backend:** FastAPI (Python) — no backend change expected for this phase. [VERIFIED: CONTEXT/codebase scope]
- **Idioma/Locale:** Português (Brasil), datas e textos em pt-BR. [VERIFIED: AGENTS.md]
- **Design:** dark mode minimalista; roxo principal (#8b5cf6 / #a78bfa); fundos escuros (#0f0a1a / #1a1025); botão Doações amarelo (#facc15) discreto. [VERIFIED: AGENTS.md, frontend/app/(public)/public.css]
- **Operação:** admin único (master); sem multiusuário. [VERIFIED: AGENTS.md]
- **Env convention:** `NEXT_PUBLIC_*` vars are embedded in browser bundle — no secrets. `BACKEND_API_URL` is server-runtime. [VERIFIED: frontend/.env.example]
- **Deploy:** Vercel (frontend). `NEXT_PUBLIC_*` changes require rebuild/redeploy. [VERIFIED: frontend/.env.example comment]
- **Core value:** fricção zero para candidato — env controls must not add friction/steps to public job seeking. [VERIFIED: PROJECT.md]
- **GSD workflow:** do not make direct repo edits outside a GSD workflow unless user explicitly asks to bypass. [VERIFIED: AGENTS.md]

## Summary

Phase 27 is a small frontend-only configuration phase. The codebase already has a single ad placeholder component (`frontend/components/board/AdSlot.tsx`) used in all three public placements (header in `page.tsx`, sidebar in `page.tsx`, inline in `JobGrid.tsx`), and a single donation button in the public layout (`frontend/app/(public)/layout.tsx`) that currently links to `/doacoes`. No backend, database, or auth changes are needed. [VERIFIED: codebase read]

The main implementation decision is where to read env vars so they work in both Server and Client Components. `AdSlot` has no `"use client"` directive today but is imported by `JobGrid.tsx`, which is a Client Component — so `AdSlot` code is included in the client bundle. That means the ads flag must be a `NEXT_PUBLIC_*` env var read via static `process.env.NEXT_PUBLIC_*` access (Next.js inlines these at build). The donation URL is read in `layout.tsx` (Server Component), so it could be server-only, but making it `NEXT_PUBLIC_*` is harmless (no secret), consistent, and easy to document. [VERIFIED: JobGrid.tsx `"use client"`, AdSlot.tsx no directive, layout.tsx server component; ASSUMED/HIGH: Next.js static NEXT_PUBLIC inlining behavior]

**Primary recommendation:** Add two testable helpers in `frontend/lib/publicEnv.ts` — `isAdsEnabled()` (default true, explicit disable only) and `getDonationUrl()` (returns sanitized absolute http/https URL or null). Gate `AdSlot` centrally to return `null` when ads disabled. In layout, render `<a target="_blank" rel="noopener noreferrer">` when donation URL is valid, otherwise keep `<Link href="/doacoes">`. Update `.env.example`/`.env.local.example` and `verify-ssr.ps1` to cover both states.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Ads visibility flag evaluation | Browser / Client + Frontend SSR | — | `AdSlot` renders in server (`page.tsx`) and client (`JobGrid.tsx`) contexts; `NEXT_PUBLIC_*` is inlined at build and available in both. [VERIFIED: codebase; ASSUMED/HIGH: Next.js inlining] |
| Donation destination resolution | Frontend Server (SSR) | Browser / Client (only if later reused) | Header button lives in `app/(public)/layout.tsx`, a Server Component; server can read env at render. [VERIFIED: layout.tsx] |
| Safe URL validation for donation | Browser / Client + Frontend SSR | — | Pure string/URL parsing helper; same logic usable in any tier. [VERIFIED: simple TS helper pattern] |
| Public `/doacoes` fallback page | Frontend Server (SSR/static) | — | Existing page remains accessible; no redirect required (D-06). [VERIFIED: doacoes/page.tsx, D-06] |
| Operator configuration | Deploy/Env config (Vercel/local `.env`) | — | Env vars set outside code; rebuild required for `NEXT_PUBLIC_*`. [VERIFIED: .env.example] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| Next.js App Router | 16.4.6 | App Router, env inlining, Server/Client components | Project-fixed; phase uses built-in env behavior. | HIGH [VERIFIED: frontend/package.json] |
| React | 19.1.1 | Component rendering | Project-fixed. | HIGH [VERIFIED: frontend/package.json] |
| TypeScript | 5.9.2 | Typed helpers | Project-fixed. | HIGH [VERIFIED: frontend/package.json] |
| Vitest | 2.1.9 | Unit tests for env parsing/URL validation helpers | Existing frontend test runner; fits `lib/**/*.test.ts` node pattern. | HIGH [VERIFIED: frontend/package.json, vitest.config.ts] |

### Supporting
| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| `next/link` | Next 16.4.6 | Internal fallback donation link | When donation URL is absent/invalid (D-05). | HIGH [VERIFIED: layout.tsx current usage] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `NEXT_PUBLIC_*` env vars | Server-only env + prop drilling / runtime config endpoint | Server-only cannot be read in Client Components like `JobGrid`'s AdSlot path without plumbing; adds complexity for a simple flag. NEXT_PUBLIC is appropriate because values are not secrets. [VERIFIED: codebase component boundaries] |
| Central gate in `AdSlot` | Conditional rendering at every call site (`page.tsx`, `JobGrid.tsx`) | Spreads logic, easy to miss a placement, violates D-03 single control intent. AdSlot is already the single component. [VERIFIED: CONTEXT D-02/D-03, code_context] |
| `getDonationUrl()` returning `null` fallback | Throw/error on invalid URL | Invalid config must be safe (D-05/SC4), not crash public page. | HIGH |
| New env parsing dependency (zod/env schema) | Small hand-written helpers | Scope is two env vars; adding dependency is overkill. Helpers are trivial and testable. | HIGH |

**Installation:**
```bash
# No new packages required.
```

**Version verification:** All required packages already present in `frontend/package.json`. No version changes. [VERIFIED: frontend/package.json]

## Architecture Patterns

### Recommended Project Structure

```text
frontend/
├── .env.example                        # document new NEXT_PUBLIC_* vars
├── .env.local.example                  # local defaults (optional: include commented defaults)
├── scripts/
│   └── verify-ssr.ps1                  # accommodate ads-on/ads-off behavior
├── lib/
│   ├── publicEnv.ts                    # NEW: isAdsEnabled(), getDonationUrl(), parsing helpers
│   └── publicEnv.test.ts               # NEW: unit tests for env parsing/URL validation
├── components/board/
│   ├── AdSlot.tsx                      # gate: return null when ads disabled
│   └── JobGrid.tsx                     # no change needed if AdSlot gates itself
└── app/(public)/
    ├── layout.tsx                      # donation button: external <a> or internal <Link>
    ├── page.tsx                        # no change needed if AdSlot gates itself
    └── doacoes/page.tsx                 # remains accessible (D-06); optional copy tweak only
```

### Pattern 1: Central AdSlot Gate (D-01/D-02/D-03)
**What:** `AdSlot` checks the ads-enabled flag once and returns `null` when disabled. All placements collapse automatically because component renders nothing.
**When to use:** All ad rendering; no per-placement logic.
**Example:**
```typescript
// Source: adapted from frontend/components/board/AdSlot.tsx [VERIFIED: codebase read]
import { isAdsEnabled } from "@/lib/publicEnv";

export function AdSlot({ variant }: { variant: AdSlotVariant }) {
  if (!isAdsEnabled()) return null;
  return (
    <div role="complementary" aria-label="Espaço publicitário" className={...}>
      <span className="text-sm font-normal text-[#b8a9cc]">Espaço publicitário</span>
    </div>
  );
}
```

### Pattern 2: Safe Donation URL Resolution (D-04/D-05/D-06)
**What:** Resolve donation URL from env; accept only absolute `http:`/`https:`. Invalid/absent => null. Layout renders external anchor for valid URL, internal Next Link for null.
**When to use:** Header Doações button.
**Example:**
```typescript
// Source: pattern based on layout.tsx [VERIFIED: codebase read]
import Link from "next/link";
import { getDonationUrl } from "@/lib/publicEnv";

const donationUrl = getDonationUrl();
const donateClass = "inline-flex min-h-11 min-w-11 items-center justify-center rounded-md border border-[rgba(250,204,21,0.40)] px-3 text-sm font-semibold text-donate hover:border-donate hover:bg-[rgba(250,204,21,0.12)]";

{donationUrl ? (
  <a href={donationUrl} target="_blank" rel="noopener noreferrer" className={donateClass}>
    Doações
  </a>
) : (
  <Link href="/doacoes" className={donateClass}>
    Doações
  </Link>
)}
```

### Pattern 3: Testable Env Parsing Helpers
**What:** Pure functions that take optional string input (for tests) and default to `process.env.*` in production. Enables node/Vitest testing without React rendering.
**When to use:** Flag parsing and donation URL validation.
**Example:**
```typescript
// Recommended shape [ASSUMED: standard testable-env-helper pattern; fits existing lib test style]
export function parseAdsEnabled(value: string | undefined): boolean {
  const v = value?.trim().toLowerCase();
  if (!v) return true; // D-01: absent/empty => show
  if (["false", "0", "off", "no", "disabled"].includes(v)) return false;
  return true; // any other value preserves current behavior
}

export function isAdsEnabled(): boolean {
  return parseAdsEnabled(process.env.NEXT_PUBLIC_ADS_ENABLED);
}

export function parseDonationUrl(value: string | undefined): string | null {
  const v = value?.trim();
  if (!v) return null;
  try {
    const u = new URL(v);
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    return u.toString();
  } catch {
    return null;
  }
}

export function getDonationUrl(): string | null {
  return parseDonationUrl(process.env.NEXT_PUBLIC_DONATION_URL);
}
```

### Pattern 4: Static NEXT_PUBLIC Access (build-time inlining)
**What:** Read `process.env.NEXT_PUBLIC_ADS_ENABLED` as a static property access, not dynamic `process.env[name]`.
**When to use:** Any client-bundled code.
**Example:**
```typescript
// GOOD - statically inlined by Next.js [ASSUMED/HIGH: Next.js behavior]
const raw = process.env.NEXT_PUBLIC_ADS_ENABLED;

// BAD - dynamic access is NOT inlined in client bundles [ASSUMED/HIGH]
const raw = process.env["NEXT_PUBLIC_ADS_ENABLED"];
```

### Anti-Patterns to Avoid
- **Per-placement conditionals:** Don't add `if (adsEnabled)` in `page.tsx`, `JobGrid.tsx`, and `layout.tsx` separately for ads. Gate in `AdSlot`. [VERIFIED: D-03, CONTEXT code_context]
- **Hiding ads with CSS only:** `hidden`/`display:none` would leave markup/accessibility labels in DOM and may confuse SSR checks; returning `null` is cleaner and satisfies "não aparecem na interface pública". [VERIFIED: D-02 wording]
- **Dynamic env access for NEXT_PUBLIC:** `process.env[name]` won't be inlined in client bundle. [ASSUMED/HIGH: Next.js documented behavior]
- **Accepting invalid donation URLs:** `javascript:`, `data:`, relative URLs, malformed strings must fall back to `/doacoes`, never be rendered as href. [VERIFIED: D-05, security best practice]
- **Removing `/doacoes` or redirecting it:** D-06 explicitly requires the page to remain accessible. [VERIFIED: D-06]
- **Adding secrets to NEXT_PUBLIC:** Both vars are non-secret display/config values. Keep it that way. [VERIFIED: .env.example warning]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| URL validation | Regex-only URL parser | `new URL()` + protocol allowlist (`http:`/`https:`) | Handles parsing edge cases, encoding, ports; protocol check blocks dangerous schemes. [VERIFIED: standard Web API] |
| Feature flag service / remote config | DB-backed flag system, LaunchDarkly, etc. | Simple env var + pure helper | Single operator, two toggles, no runtime admin UI needed. [VERIFIED: phase scope] |
| Client runtime env injection | Custom `/api/config` endpoint | `NEXT_PUBLIC_*` build-time inlining | No secret, no runtime mutation needed; fits Vercel deploy model. [VERIFIED: .env.example pattern] |

**Key insight:** This phase is configuration plumbing, not a feature-flag platform. Two env vars, two helpers, one central component gate, one conditional link — keep it boring.

## Common Pitfalls

### Pitfall 1: NEXT_PUBLIC inlining misunderstood
**What goes wrong:** Operator changes env var on Vercel but UI doesn't change; or dev expects runtime change after build.
**Why it happens:** `NEXT_PUBLIC_*` is embedded at build time. [ASSUMED/HIGH]
**How to avoid:** Document clearly in `.env.example` and deployment notes: "requer rebuild/redeploy ao alterar". Same note already exists for `NEXT_PUBLIC_API_URL`.
**Warning signs:** Works locally with dev server restart but not in production after env edit without redeploy.
**Confidence:** HIGH [VERIFIED: .env.example existing comment; ASSUMED/HIGH: Next.js core behavior]

### Pitfall 2: AdSlot hidden but verify-ssr.ps1 still hard-asserts 3 ads
**What goes wrong:** SSR verification script fails when ads are intentionally disabled.
**Why it happens:** `frontend/scripts/verify-ssr.ps1` line 46-47 asserts `Espaço publicitário` count >= 3. [VERIFIED: verify-ssr.ps1]
**How to avoid:** Make script env-aware. Read `$env:NEXT_PUBLIC_ADS_ENABLED` (or accept a param); when disabled, assert count is 0 and no ad markup; when enabled/default, keep current >= 3 assertion. Also assert `/doacoes` and donation button behavior if practical.
**Warning signs:** CI/manual verify-ssr fails after setting flag off.
**Confidence:** HIGH [VERIFIED: verify-ssr.ps1 read]

### Pitfall 3: Invalid donation URL becomes unsafe href
**What goes wrong:** `javascript:alert(1)` or malformed value rendered as link target.
**Why it happens:** Directly interpolating env value into `href`.
**How to avoid:** `parseDonationUrl` accepts only absolute `http:`/`https:` URLs via `new URL()`; all other values return `null` => internal `/doacoes` fallback.
**Warning signs:** No URL validation test; helper returns raw string.
**Confidence:** HIGH [VERIFIED: D-05/SC4; standard web security]

### Pitfall 4: Hiding ads breaks grid semantics/layout unexpectedly
**What goes wrong:** Inline ad removal causes odd spacing or invalid HTML assumptions.
**Why it happens:** Inline ad currently renders a `<div>` inside a `<ul>` fragment in `JobGrid` — already slightly unusual. Returning `null` removes it cleanly. [VERIFIED: JobGrid.tsx, AdSlot.tsx]
**How to avoid:** Prefer `AdSlot` returning `null` (no DOM). Do not replace with empty spacer unless explicitly desired. Visually verify mobile/desktop grid after hiding.
**Warning signs:** Empty `<li>` or leftover wrapper with margins.
**Confidence:** HIGH [VERIFIED: code read]

### Pitfall 5: Dynamic process.env access prevents client inlining
**What goes wrong:** Flag always appears enabled/undefined in client bundle; ads never hide in JobGrid.
**Why it happens:** Next.js only inlines static `process.env.NEXT_PUBLIC_X` property access. [ASSUMED/HIGH]
**How to avoid:** Use `process.env.NEXT_PUBLIC_ADS_ENABLED` directly in helper (static access). Test helper with explicit string args; smoke test client-rendered inline ad in browser.
**Warning signs:** Server-rendered header/sidebar ads hide but inline JobGrid ads remain.
**Confidence:** HIGH [ASSUMED: Next.js standard behavior; easy to confirm in build output]

### Pitfall 6: Donation button styling diverges between `<a>` and `<Link>`
**What goes wrong:** External and fallback states look different.
**Why it happens:** Two different elements with duplicated class strings edited separately.
**How to avoid:** Extract shared `donateClassName` const in layout or reuse same string. Keep same text "Doações", same classes, only element/href/target/rel differ.
**Warning signs:** Visual regression in header.
**Confidence:** HIGH [VERIFIED: layout.tsx current class]

## Code Examples

### Current AdSlot (gate point)
```typescript
// Source: frontend/components/board/AdSlot.tsx [VERIFIED]
export function AdSlot({ variant }: { variant: AdSlotVariant }) {
  return (
    <div role="complementary" aria-label="Espaço publicitário" className={`${BASE} ${VARIANTS[variant]}`}>
      <span className="text-sm font-normal text-[#b8a9cc]">Espaço publicitário</span>
    </div>
  );
}
```

### Current Donation Button (layout)
```tsx
// Source: frontend/app/(public)/layout.tsx [VERIFIED]
<Link
  href="/doacoes"
  className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-md border border-[rgba(250,204,21,0.40)] px-3 text-sm font-semibold text-donate hover:border-donate hover:bg-[rgba(250,204,21,0.12)]"
>
  Doações
</Link>
```

### Current verify-ssr ad assertion (must be env-aware)
```powershell
# Source: frontend/scripts/verify-ssr.ps1 [VERIFIED]
$adCount = ([regex]::Matches($html, "Espaço publicitário")).Count
Assert ($adCount -ge 3) "Home has fewer than 3 ad placeholders ($adCount)"
```

### Env naming recommendation (discretion, concrete)
```bash
# .env.example additions (recommended names) [ASSUMED: naming at discretion]
# Ads: show by default (D-01). Set to false/0/off/no/disabled to hide all ad slots.
NEXT_PUBLIC_ADS_ENABLED=true

# Donation URL: absolute http(s) URL. When set and valid, header button opens it in new tab.
# When absent/empty/invalid, header button goes to /doacoes (safe fallback).
NEXT_PUBLIC_DONATION_URL=
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ad placeholders always rendered | Ad placeholders gated by env flag, default visible | Phase 27 | Operator can hide ads without code removal (ADS-01) |
| Doações button always links to `/doacoes` | Doações button uses configured external URL when valid, else `/doacoes` | Phase 27 | Operator can point donations to real destination (DONA-01) |

**Deprecated/outdated:**
- None. This is additive configuration, not a library migration.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Next.js statically inlines `process.env.NEXT_PUBLIC_*` property access in client bundles; dynamic access is not inlined. | Architecture Patterns / Pitfalls | If behavior differs in Next 16.4.6, inline ad hiding in client JobGrid could fail. Low risk - long-standing Next.js behavior; verify with quick build smoke. |
| A2 | `AdSlot` returning `null` from a Client Component import path is sufficient; no `"use client"` directive needed on AdSlot itself. | Architecture Patterns | Low - component has no hooks/browser APIs; returning null is valid in both contexts. |
| A3 | `NEXT_PUBLIC_*` env changes require Vercel rebuild/redeploy. | Pitfalls / Env | Low - already documented in `.env.example`; standard Vercel behavior. |
| A4 | Recommended env names (`NEXT_PUBLIC_ADS_ENABLED`, `NEXT_PUBLIC_DONATION_URL`) are acceptable; naming is at discretion. | Code Examples | Low - planner can rename; helpers isolate the name. |

## Open Questions (RESOLVED)

1. **Should `verify-ssr.ps1` be parameterized or env-driven for ads state?**
   - What we know: Script currently hardcodes `>= 3` ad placeholders. [VERIFIED: verify-ssr.ps1]
   - What's unclear: Whether operators/CI run it with env var set, or prefer explicit param.
   - Recommendation: Support both: optional `-AdsEnabled` param, defaulting to `$env:NEXT_PUBLIC_ADS_ENABLED` parsing with default-show semantics. Keeps manual use simple.
   - **RESOLVED (2026-11-22, Plan 27-01):** Support both. `verify-ssr.ps1` accepts optional `-AdsEnabled` param defaulting to `$env:NEXT_PUBLIC_ADS_ENABLED`, with D-01 default-show semantics.

2. **Should `/doacoes` display the configured external link when present?**
   - What we know: D-06 requires page accessible; discretion allows minimal adjustments. [VERIFIED: CONTEXT]
   - What's unclear: Product value vs scope creep.
   - Recommendation: Keep minimal — no required change. Optional nice-to-have: if external URL configured, show a button/link on `/doacoes` too. Planner may skip to stay tight.
   - **RESOLVED (2026-11-22, Plan 27-01):** Keep `/doacoes` unchanged/minimal. Page remains accessible per D-06; no external-link copy added in this phase.

3. **Collapse behavior when ads hidden (spacing)?**
   - What we know: Discretion allows collapse vs preserve space, as long as ad spaces don't appear. [VERIFIED: CONTEXT discretion]
   - What's unclear: Visual preference.
   - Recommendation: Collapse (return `null`, no placeholder). Simpler, no empty dashed boxes; matches "não aparecem". Verify with quick visual smoke.
   - **RESOLVED (2026-11-22, Plan 27-01):** Collapse. `AdSlot` returns `null` when disabled; `page.tsx` conditionally omits header/sidebar ad and aside to avoid empty 300px desktop gutter.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend build/tests | ✓ | (local dev machine) | — |
| npm | Frontend deps/scripts | ✓ | (local dev machine) | — |
| Next.js | App runtime/build | ✓ | 16.4.6 [VERIFIED: package.json] | — |
| Vitest | Unit tests | ✓ | 2.1.9 [VERIFIED: package.json] | — |
| PowerShell | verify-ssr.ps1 | ✓ | Windows environment | — |

**Missing dependencies with no fallback:**
- None identified.

**Missing dependencies with fallback:**
- None identified.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 2.1.9 |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npx vitest run lib/publicEnv.test.ts` |
| Full suite command | `cd frontend && npm test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADS-01 | `parseAdsEnabled`: absent/empty/true/1/garbage => true; false/0/off/no/disabled (case-insensitive, trimmed) => false | unit | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ❌ Wave 0 |
| ADS-01 | `isAdsEnabled` reads static `NEXT_PUBLIC_ADS_ENABLED` defaulting to show | unit (via parse helper) | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ❌ Wave 0 |
| DONA-01 | `parseDonationUrl`: valid http/https absolute URL => normalized URL; empty/absent/invalid/javascript:/data:/relative => null | unit | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ❌ Wave 0 |
| DONA-01 | `getDonationUrl` reads static `NEXT_PUBLIC_DONATION_URL` | unit (via parse helper) | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ❌ Wave 0 |
| ADS-01 | Public board hides/shows 3 ad placements according to env | smoke/manual + verify-ssr | `powershell -File frontend/scripts/verify-ssr.ps1` (env-aware after update) | ❌ Wave 0 update |
| DONA-01 | Header Doações button opens external URL in new tab when configured; falls back to `/doacoes` when absent/invalid | manual smoke | Browser check on running app | manual-only |

### Sampling Rate
- **Per task commit:** `cd frontend && npx vitest run lib/publicEnv.test.ts`
- **Per wave merge:** `cd frontend && npm test && npm run build`
- **Phase gate:** Full frontend tests green + build green before `/gsd-verify-work`; manual smoke for ads off/on and donation external/fallback

### Wave 0 Gaps
- [ ] `frontend/lib/publicEnv.ts` — env parsing and donation URL validation helpers
- [ ] `frontend/lib/publicEnv.test.ts` — covers ADS-01/DONA-01 parsing/validation semantics
- [ ] Update `frontend/scripts/verify-ssr.ps1` — env-aware ad assertions (enabled default vs disabled)
- [ ] Framework install: none — Vitest already installed

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth changes. |
| V3 Session Management | no | No session changes. |
| V4 Access Control | no | Public UI display toggles only. |
| V5 Input Validation | yes | Validate donation URL: allow only absolute `http:`/`https:`; reject `javascript:`, `data:`, malformed, relative. Treat invalid as absent (D-05). |
| V6 Cryptography | no | No crypto/secrets. |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| `javascript:` / `data:` URL in env-configured href | Tampering / XSS-adjacent navigation | Parse with `new URL()` and allowlist protocols `http:` and `https:` only; fallback to `/doacoes`. [VERIFIED: D-05] |
| Reverse-tabnabbing on `_blank` link | Spoofing / Tampering | Always include `rel="noopener noreferrer"` on external donation link. [VERIFIED: D-04] |
| Operator misconfiguration causing broken UX | Denial of service (UX) | Safe default: ads show when flag absent/invalid; donation falls back to internal page when URL absent/invalid. [VERIFIED: D-01, D-05] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/27-controles-por-ambiente/27-CONTEXT.md` - locked decisions D-01..D-06, discretion, canonical refs, code context.
- `.planning/REQUIREMENTS.md` - ADS-01, DONA-01.
- `.planning/ROADMAP.md` - Phase 27 goal, success criteria.
- `frontend/components/board/AdSlot.tsx` - current ad placeholder component, single gate point. [VERIFIED: code read]
- `frontend/app/(public)/page.tsx` - header/sidebar AdSlot usage. [VERIFIED: code read]
- `frontend/components/board/JobGrid.tsx` - inline AdSlot insertion, client component boundary. [VERIFIED: code read]
- `frontend/app/(public)/layout.tsx` - donation button current `Link href="/doacoes"`. [VERIFIED: code read]
- `frontend/app/(public)/doacoes/page.tsx` - existing safe fallback page. [VERIFIED: code read]
- `frontend/app/(public)/public.css` - `--color-donate` token. [VERIFIED: code read]
- `frontend/.env.example`, `frontend/.env.local.example` - env conventions, NEXT_PUBLIC rebuild warning. [VERIFIED: code read]
- `frontend/scripts/verify-ssr.ps1` - ad/donation assertions needing env awareness. [VERIFIED: code read]
- `frontend/lib/jobs.ts` - server env reading pattern (`BACKEND_API_URL ?? NEXT_PUBLIC_*`). [VERIFIED: code read]
- `frontend/package.json`, `frontend/vitest.config.ts` - test stack and constraints. [VERIFIED: code read]

### Secondary (MEDIUM confidence)
- Next.js env variable behavior (`NEXT_PUBLIC_*` build-time inlining, static access requirement) - long-standing framework behavior; aligns with existing `.env.example` comments. [ASSUMED/HIGH based on established Next.js behavior; not re-verified via Context7 in this session]

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in project; no new deps.
- Architecture: HIGH - codebase read confirms component boundaries and single gate point; NEXT_PUBLIC inlining assumption is standard but marked.
- Pitfalls: HIGH - derived from actual codebase (verify-ssr hard assert, client/server component boundary, URL validation).

**Research date:** 2026-11-22
**Valid until:** 2026-12-22 (stable domain; Next.js env semantics stable)
