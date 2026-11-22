# Phase 26: Acesso Admin Dedicado - Research

**Researched:** 2026-11-22
**Domain:** Next.js App Router admin routing/auth UX (frontend-only phase)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** A página dedicada de login fica em `/admin/login`, dentro do namespace admin.
- **D-02:** Após autenticar com sucesso, redirecionar para a página solicitada originalmente (return-to) quando existir; caso contrário, fallback para `/admin`.
- **D-03:** Quando um usuário sem sessão acessa uma rota admin protegida, redirecionar para `/admin/login` preservando o destino de retorno.
- **D-04:** Quando já autenticado, abrir `/admin/login` redireciona para `/admin` (ou para o retorno válido, se aplicável). Ao sair (logout), redirecionar para `/admin/login`.
- **D-05:** O link fica no rodapé do conteúdo da Política de Privacidade, abaixo do aviso final (disclaimer box).
- **D-06:** Peso visual discreto: texto pequeno e suave, cor muted/baixa ênfase, sem botão ou ícone chamativo.
- **D-07:** O texto do link é "Acesso administrativo".
- **D-08:** Apresentação em linha própria, pequena e muted, abaixo do box de aviso.
- **D-09:** Layout focado no login, sem navegação admin (sem Publicações/Integrações/Sair enquanto deslogado), com branding mínimo.
- **D-10:** Conteúdo direto e objetivo: título claro, campo de senha e botão Entrar; sem texto longo.
- **D-11:** Incluir um link discreto para voltar ao site público.
- **D-12:** Linguagem visual alinhada ao visual admin atual (tema escuro/canvas/surface/accent).

### OpenCode's Discretion
- Copy exata do título/subtexto da página de login, desde que direta e objetiva.
- Implementação técnica do parâmetro de retorno (nome/validação/sanitização) e regras de fallback seguro.
- Espaçamento, tipografia e detalhes responsivos, mantendo o peso visual discreto definido.
- Microcopy de loading/erro além dos padrões já existentes, sem alterar o contrato de autenticação.
- Estrutura exata de componentes/arquivos para separar login do fluxo de paste, respeitando os comportamentos decididos.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADMN-01 | Admin acessa login em página dedicada, separada da página de paste/revisão | New `/admin/login` page + extracted login form; remove login responsibility from `ExtractForm`; AdminGuard/logout/401 redirects aligned to `/admin/login`; admin layout chrome conditional for login route |
| ADMN-02 | Usuário encontra um link discreto para login admin na página de Política de Privacidade | Add muted, small, own-line `Link` to `/admin/login` below the final disclaimer box in `frontend/app/(public)/privacidade/page.tsx` |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- **Tech stack — Frontend:** Next.js 16 (App Router, `16.4.6`) + Tailwind CSS + dark mode — fixed. [VERIFIED: frontend/package.json]
- **Tech stack — Backend:** FastAPI (Python) — fixed. [VERIFIED: AGENTS.md]
- **Anti-spam:** Cloudflare Turnstile (gratuito) — login must keep Turnstile server-side verification. [VERIFIED: backend/app/api/v1/auth.py]
- **Idioma/Locale:** Português (Brasil), datas e textos em pt-BR. [VERIFIED: AGENTS.md]
- **Design:** dark mode minimalista; roxo principal (#8b5cf6 / #a78bfa); fundos escuros (#0f0a1a / #1a1025); botão Doações amarelo (#facc15) discreto. [VERIFIED: AGENTS.md, admin.css]
- **Operação:** admin único (master); sem multiusuário. [VERIFIED: AGENTS.md]
- **Auth contract:** `POST /api/v1/auth/login` with `password` + `cf_token`, returns `TokenResponse { access_token, token_type, expires_in }`. No auth contract changes. [VERIFIED: frontend/lib/api.ts, backend/app/schemas/auth.py]
- **Session:** `sessionStorage` key `nqu_admin_token` (`TOKEN_KEY`). [VERIFIED: frontend/lib/auth.ts]
- **GSD workflow:** do not make direct repo edits outside a GSD workflow unless user explicitly asks to bypass. [VERIFIED: AGENTS.md]

## Summary

Phase 26 is a frontend-only admin UX/routing refactor. The backend auth contract is already correct and must not change: `POST /api/v1/auth/login` requires `password` and `cf_token`, verifies Turnstile server-side with `expected_action="login"`, rate-limits, then validates the admin password and returns a JWT. [VERIFIED: backend/app/api/v1/auth.py, backend/app/schemas/auth.py, backend/app/core/security.py]

The current login UI is embedded inside `frontend/app/admin/paste/ExtractForm.tsx`, which mixes two responsibilities: Turnstile/password login and text extraction. Protected admin routes rely on `useAdminGuard()` redirecting to `/admin/paste` when no token is present, and logout/401 handlers hard-navigate to `/admin/paste`. The admin layout (`frontend/app/admin/layout.tsx`) wraps every `/admin/*` route with nav, Publicações/Integrações links, and `LogoutButton`. [VERIFIED: codebase read]

**Primary recommendation:** Extract a dedicated login form/component for `/admin/login`, make `AdminGuard` the single redirect authority for unauthenticated protected routes with a sanitized `next` return path, convert `ExtractForm` to extraction-only behind guard, and make the admin chrome conditional so `/admin/login` has no admin nav while keeping the admin theme/metadata/providers. Add the discrete privacy-page link as a plain Next `<Link>`. No backend change, no auth contract change.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Login page UI (`/admin/login`) | Browser / Client | Frontend Server (SSR shell) | Page is interactive (password, Turnstile widget, sessionStorage, redirect) but served through Next App Router. [VERIFIED: Next.js App Router pattern; similar to existing admin pages] |
| Return-to capture/sanitization | Browser / Client | — | Guard and login page run client-side; sanitization must happen before `router.replace`/`window.location` navigation. [VERIFIED: AdminGuard/LogoutButton patterns] |
| Admin session persistence | Browser / Client | — | Session is `sessionStorage` token `nqu_admin_token`, read after mount. [VERIFIED: frontend/lib/auth.ts, ExtractForm.tsx, AdminGuard.tsx] |
| Login credential/Turnstile verification | API / Backend | — | Backend remains authority for rate limit, Turnstile verify, password check, JWT issuance. [VERIFIED: backend/app/api/v1/auth.py] |
| Discreet public admin entry point | Frontend Server (SSR) / Static content | Browser / Client | Privacy page is a server component with static content; adding a Next `<Link>` is sufficient. [VERIFIED: frontend/app/(public)/privacidade/page.tsx] |
| Protected admin navigation shell | Frontend Server (SSR layout) | Browser / Client | Layout is server component exporting metadata/viewport; chrome visibility can be delegated to a client component using pathname. [VERIFIED: frontend/app/admin/layout.tsx] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| Next.js App Router | 16.4.6 | Routing, layouts, pages, navigation | Project-fixed; already used for admin/public routes. | HIGH [VERIFIED: frontend/package.json] |
| React | 19.1.1 | Client components/hooks | Project-fixed; existing admin pages use client hooks. | HIGH [VERIFIED: frontend/package.json] |
| Tailwind CSS | 4.3.3 | Admin/public styling | Project-fixed; admin tokens already defined in `admin.css`. | HIGH [VERIFIED: frontend/package.json, admin.css] |
| next-turnstile | 1.0.7 | Turnstile widget | Already used in `ExtractForm` login flow; reuse for dedicated login. | HIGH [VERIFIED: frontend/package.json, ExtractForm.tsx] |
| TypeScript | 5.9.2 | Type safety | Project-fixed. | HIGH [VERIFIED: frontend/package.json] |

### Supporting
| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| `next/link` | Next 16.4.6 | Internal navigation | Privacy-page link and "voltar ao site público". | HIGH [VERIFIED: codebase usage] |
| `next/navigation` | Next 16.4.6 | `useRouter`, `usePathname`, `useSearchParams` | Guard redirect, login redirect, conditional admin chrome. | HIGH [VERIFIED: existing admin components] |
| Vitest | 2.1.9 | Unit tests for pure TS helpers | Add tests for return-to sanitization/helper logic if extracted to `lib/`. | HIGH [VERIFIED: frontend/package.json, vitest.config.ts] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Client-side guard redirect (`useAdminGuard`) | Next.js middleware/server-side auth gate | Middleware would be cleaner for SSR gating but current auth is `sessionStorage` (client-only). Moving to cookies/middleware would change auth architecture, out of scope and risky for this phase. [VERIFIED: auth.ts sessionStorage; D-01..D-04 scope] |
| Conditional admin chrome by pathname | Route groups `(protected)` / `(auth)` with separate layouts | Route groups are clean but require moving files/paths and more churn. Conditional chrome is lower-risk if carefully scoped to `/admin/login`. Either satisfies D-09; choose lowest-churn pattern that keeps layout metadata/server behavior intact. [ASSUMED: based on Next App Router layout nesting rules] |
| Reuse login logic in new component | Keep login inside ExtractForm and mount conditionally | Would not cleanly satisfy "página dedicada" and "paste não exige mais formulário de login como fluxo principal"; increases coupling. [VERIFIED: SC1, SC4, D-01] |

**Installation:**
```bash
# No new packages required.
```

**Version verification:** Existing `frontend/package.json` pins the required packages (`next@16.4.6`, `next-turnstile@1.0.7`, `react@19.1.1`, `vitest@^2.1.9`). Do not add dependencies for this phase. [VERIFIED: frontend/package.json]

## Architecture Patterns

### Recommended Project Structure
```text
frontend/
├── app/
│   ├── admin/
│   │   ├── layout.tsx                 # server layout: metadata/viewport/css/providers; renders conditional chrome
│   │   ├── login/
│   │   │   └── page.tsx               # dedicated login page (client or client wrapper)
│   │   └── paste/
│   │       ├── page.tsx               # paste page remains extraction entry
│   │       └── ExtractForm.tsx        # extraction-only after refactor
│   └── (public)/
│       └── privacidade/page.tsx       # discreet admin link below disclaimer
├── components/admin/
│   ├── AdminGuard.tsx                 # redirect unauthenticated -> /admin/login?next=...
│   ├── AdminChrome.tsx                # optional: pathname-aware header/nav wrapper
│   ├── AdminLoginForm.tsx             # optional: reusable login form
│   └── LogoutButton.tsx               # logout -> /admin/login
└── lib/
    ├── api.ts                         # loginAdmin contract unchanged
    ├── auth.ts                        # TOKEN_KEY unchanged
    └── adminReturnTo.ts               # optional: sanitize/build return-to helper
```

### Pattern 1: Dedicated Login Page with Return-To
**What:** `/admin/login` renders only login-focused UI; on success it stores token and redirects to a sanitized `next` destination or `/admin`.
**When to use:** D-01, D-02, D-04, D-09, D-10.
**Example:**
```typescript
// Source: codebase pattern from ExtractForm.tsx + AdminGuard.tsx [VERIFIED: codebase read]
const next = sanitizeAdminReturnTo(searchParams.get("next"));
const token = await loginAdmin(password, cfToken);
sessionStorage.setItem(TOKEN_KEY, token);
router.replace(next ?? "/admin");
```

### Pattern 2: AdminGuard as Redirect Authority
**What:** Protected admin client pages call `useAdminGuard()`; guard reads token after mount, redirects missing session to `/admin/login?next=<current admin path>`.
**When to use:** All protected admin routes (`/admin`, `/admin/paste`, `/admin/review`, `/admin/social-posts`, `/admin/integracoes`).
**Example:**
```typescript
// Source: adapted from frontend/components/admin/AdminGuard.tsx [VERIFIED: codebase read]
const path = usePathname();
const search = useSearchParams().toString();
const next = sanitizeAdminReturnTo(`${path}${search ? `?${search}` : ""}`);
if (!stored) router.replace(`/admin/login?next=${encodeURIComponent(next ?? "/admin")}`);
```

### Pattern 3: Conditional Admin Chrome
**What:** Keep `app/admin/layout.tsx` as server layout (metadata/viewport/css/ToastProvider), but move header/nav rendering into a client component that hides admin nav on `/admin/login`.
**When to use:** Needed to satisfy D-09 because Next layouts nest and `/admin/login` is under `/admin`.
**Example:**
```typescript
// Source: Next App Router client pathname pattern [ASSUMED: standard Next pattern; verify during implementation]
"use client";
const pathname = usePathname();
const isLogin = pathname === "/admin/login";
return isLogin ? <MinimalBrand>{children}</MinimalBrand> : <FullAdminNav>{children}</FullAdminNav>;
```

### Anti-Patterns to Avoid
- **Changing backend auth contract:** Do not alter `/api/v1/auth/login`, schemas, JWT, Turnstile server verification, or rate limiting. Phase scope and constraints forbid it. [VERIFIED: CONTEXT, auth.py]
- **Open redirect return-to:** Do not `router.replace(next)` for arbitrary `next` values. Accept only internal admin paths; fallback to `/admin`. [VERIFIED: security best practice; D-02/D-03 require safe fallback]
- **Login page inside full admin nav:** Do not leave `/admin/login` under unchanged `admin/layout.tsx` header/nav. It violates D-09. [VERIFIED: layout.tsx + D-09]
- **Duplicating login logic in ExtractForm and login page:** Extract/reuse logic; keep one source for Turnstile/login/error behavior. [VERIFIED: D-01, SC4]
- **Using `window.location` for normal in-app redirect after login when router suffices:** Prefer `router.replace` for normal success flow; keep hard reload only where session-in-memory cleanup is intentional (logout already uses hard replace). [ASSUMED: consistent with existing LogoutButton rationale]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Turnstile widget lifecycle | Custom Cloudflare script integration | `next-turnstile` `Turnstile` component as already used | Existing code already handles verify/expire/error and remount-by-key for single-use tokens. [VERIFIED: ExtractForm.tsx, package.json] |
| JWT/password verification | Any frontend or new backend auth logic | Existing `loginAdmin` + backend `/auth/login` | Contract already implemented and secured server-side. [VERIFIED: api.ts, auth.py] |
| Admin session key | New storage key/scheme | `TOKEN_KEY` from `frontend/lib/auth.ts` | Avoids breaking existing guarded pages and handlers. [VERIFIED: auth.ts, multiple consumers] |
| Styling system | New CSS framework/theme tokens | Existing Tailwind + `admin.css` tokens | D-12 requires visual alignment with current admin theme. [VERIFIED: admin.css] |

**Key insight:** This phase is mostly flow decomposition and redirect correctness. Reuse the existing auth primitives and focus on safe routing/state transitions.

## Common Pitfalls

### Pitfall 1: `/admin/login` inherits admin nav
**What goes wrong:** Login page shows Publicações/Integrações/Sair while logged out.
**Why it happens:** `frontend/app/admin/layout.tsx` currently wraps all children in the admin header.
**How to avoid:** Make chrome pathname-aware or restructure layout. Verify `/admin/login` renders no admin nav and still has admin theme/providers.
**Warning signs:** Login page visually looks like dashboard shell; LogoutButton appears before auth.
**Confidence:** HIGH [VERIFIED: layout.tsx, D-09]

### Pitfall 2: Open redirect via `next` parameter
**What goes wrong:** Attacker crafts `/admin/login?next=https://evil.example` and user is redirected off-site after login.
**Why it happens:** Naive `router.replace(nextParam)`.
**How to avoid:** Sanitize return-to: allow only same-origin admin paths beginning with `/admin` (optionally `/admin/...`), reject protocol-relative `//`, backslashes, and non-admin targets; fallback `/admin`.
**Warning signs:** Any code passing raw query param to router.replace/window.location.
**Confidence:** HIGH [VERIFIED: OWASP open redirect class; D-02/D-03 require return-to]

### Pitfall 3: Login redirect loop / wrong destination
**What goes wrong:** Authenticated user hits `/admin/login` and bounces; or unauthenticated user loses intended page.
**Why it happens:** Guard/login both redirect without considering existing token and sanitized next.
**How to avoid:** Encode D-02/D-03/D-04 as explicit table-driven checks; cover next present/absent/invalid/authenticated/unauthenticated.
**Warning signs:** `/admin/login?next=/admin/login` loops; authenticated user sees login form.
**Confidence:** HIGH [VERIFIED: D-02/D-03/D-04]

### Pitfall 4: 401 handlers still send to `/admin/paste`
**What goes wrong:** Expired session lands on paste page (which no longer has login) or confusing flow.
**Why it happens:** Multiple admin components have hardcoded `/admin/paste` in 401 handling.
**How to avoid:** Grep and update all admin-session-expired redirects: `ReviewQueue.tsx`, `EditJobDialog.tsx`, `SocialPostsClient.tsx`, `AdminGuard.tsx`, `LogoutButton.tsx`.
**Warning signs:** `rg "/admin/paste"` still shows redirect targets in frontend source.
**Confidence:** HIGH [VERIFIED: grep results]

### Pitfall 5: ExtractForm still owns login UI
**What goes wrong:** Paste page continues to behave as login entry, violating SC4/ADMN-01.
**Why it happens:** `ExtractForm.tsx` currently renders login form when `!token`.
**How to avoid:** Remove login branch from ExtractForm or reduce it to guarded extraction-only; move login UX to `/admin/login`.
**Warning signs:** Paste page contains password field/Turnstile/login button after phase.
**Confidence:** HIGH [VERIFIED: ExtractForm.tsx, SC4]

### Pitfall 6: `useSearchParams()` suspense/static rendering surprises
**What goes wrong:** Build/runtime warning or unexpected behavior when reading search params in client page/component.
**Why it happens:** Next App Router treats `useSearchParams()` specially; depending on usage, may require Suspense boundary.
**How to avoid:** Isolate search-param reading in a small client component wrapped by `<Suspense>` when needed, or read `next` in an effect from `window.location.search` only where safe. Prefer the simplest pattern consistent with Next 16 behavior.
**Warning signs:** Next build warnings about CSR bailout / missing suspense with useSearchParams.
**Confidence:** MEDIUM [ASSUMED: common Next App Router behavior; confirm during implementation/build]

## Code Examples

### Existing Login Contract (Reuse)
```typescript
// Source: frontend/lib/api.ts [VERIFIED]
export async function loginAdmin(password: string, cfToken: string): Promise<string> {
  const res = await fetch(`${API}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password, cf_token: cfToken }),
  });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  const body = (await res.json()) as { access_token?: string };
  if (!body.access_token) throw new Error("Token não recebido");
  return body.access_token;
}
```

### Existing Guard Redirect (Current Behavior to Replace)
```typescript
// Source: frontend/components/admin/AdminGuard.tsx [VERIFIED]
setToken(stored);
if (!stored) {
  router.replace("/admin/paste");
}
```

### Return-To Sanitizer (Recommended)
```typescript
// Source: recommended pattern for D-02/D-03 [ASSUMED: implementation detail; security pattern HIGH]
export function sanitizeAdminReturnTo(value: string | null | undefined): string | null {
  if (!value) return null;
  if (!value.startsWith("/admin")) return null;
  if (value.startsWith("//")) return null;
  if (value.includes("\\")) return null;
  if (value.startsWith("/admin/login")) return "/admin"; // avoid loop; or preserve only safe non-login targets
  return value;
}
```

### Privacy Page Discreet Link Placement
```tsx
// Source: frontend/app/(public)/privacidade/page.tsx insertion point [VERIFIED]
<div className="mt-12 rounded-md border border-line bg-surface p-4 text-sm leading-relaxed text-fg-muted">
  <p>...aviso final...</p>
</div>
<p className="mt-3 text-xs text-fg-muted/80">
  <Link href="/admin/login" className="hover:text-fg-muted">Acesso administrativo</Link>
</p>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Login embedded in `/admin/paste` ExtractForm | Dedicated `/admin/login` page with return-to | Phase 26 | Cleaner separation of concerns, satisfies ADMN-01/SC4 |
| Guard/logout/401 redirect to `/admin/paste` | Guard/logout/401 redirect to `/admin/login` | Phase 26 | Consistent auth entry point; paste remains protected content page |
| No public admin entry link | Discreet "Acesso administrativo" on Privacy page | Phase 26 | Satisfies ADMN-02 without adding prominent public CTA |

**Deprecated/outdated:**
- `ExtractForm` as login owner: becomes legacy behavior after Phase 26. [VERIFIED: CONTEXT, SC4]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `useSearchParams()` in `/admin/login` may need a Suspense boundary or careful client isolation in Next 16.4.6 App Router. | Common Pitfalls / Architecture Patterns | Build warning or hydration/render bailout; easy to fix by wrapping client child in Suspense. |
| A2 | Conditional chrome in `admin/layout.tsx` via client pathname component is lower-risk than route-group restructuring. | Architecture Patterns | If layout/SSR boundaries behave badly, fallback is route-group split with file moves. |
| A3 | `next` should be limited to paths starting with `/admin` and not `/admin/login` to avoid loops/open redirect. | Code Examples / Pitfalls | Over-restrictive sanitization could drop legitimate return targets; under-restrictive creates security issue. |

**If any assumption becomes load-bearing during planning:** confirm with a quick Next 16 build/dev check before finalizing plan.

## Open Questions (RESOLVED)

1. **Where should the return-to helper live?**
   - What we know: AdminGuard, login page, and possibly 401 handlers need consistent behavior. [VERIFIED: D-02/D-03/D-04, grep results]
   - What's unclear: Put in `lib/` (pure, testable) or duplicate small logic in components.
   - Recommendation: Create `frontend/lib/adminReturnTo.ts` with pure sanitize/build helpers; unit test with Vitest (fits existing lib test setup).
   - **RESOLVED:** Use `frontend/lib/adminReturnTo.ts` as a pure, testable helper shared by login, guard, and 401/logout redirect flows; cover it with Vitest unit tests. This matches 26-01 Task 1.

2. **Should 401 handlers preserve return-to?**
   - What we know: D-03 explicitly requires return-to for protected-route access without session. D-04 covers logout to `/admin/login`. 401 handlers currently do hard replace to `/admin/paste`.
   - What's unclear: Whether expired-session redirect must preserve current page as next.
   - Recommendation: Preserve return-to when the handler has access to current location (`window.location.pathname + search`) and sanitize it; otherwise fallback to `/admin/login`. This improves UX and aligns with D-03 intent without changing auth contract.
   - **RESOLVED:** Preserve sanitized return-to on 401 handlers when current location is available (`window.location.pathname + search`), otherwise fallback to `/admin/login` (or safe `/admin` via helper). This matches 26-02 Task 2.

3. **Should `/admin/paste` remain directly accessible when logged out?**
   - What we know: SC4 says paste page should not require login form as main flow. Paste is an admin tool and currently guarded behavior is mixed in ExtractForm.
   - What's unclear: Whether paste page should self-guard via `useAdminGuard`.
   - Recommendation: Yes. Make paste extraction require authenticated session and let AdminGuard redirect to `/admin/login?next=/admin/paste`.
   - **RESOLVED:** Yes. `/admin/paste` remains a protected admin route and must self-guard via `useAdminGuard`; unauthenticated access redirects to `/admin/login?next=/admin/paste`. ExtractForm becomes extraction-only for authenticated sessions. This matches 26-01 Task 3 and 26-02 Task 1.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend build/tests | ✓ | `v24.14.1` | — |
| npm | Frontend package scripts | ✓ | `11.12.1` | — |
| Python | Backend (not required by this phase) | ✓ | `3.14.3` | — |
| git | Repo operations | ✓ | `2.53.0.windows.2` | — |

**Missing dependencies with no fallback:**
- None identified for Phase 26. [VERIFIED: local tool probe]

**Missing dependencies with fallback:**
- None. [VERIFIED: local tool probe]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 2.1.9 + TypeScript 5.9.2 | 
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm test -- --run lib/adminReturnTo.test.ts` |
| Full suite command | `cd frontend && npm test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADMN-01 | Admin can open dedicated login page separated from paste/review; unauthenticated protected access redirects to `/admin/login` with safe return-to; authenticated login lands on return-to or `/admin`; logout goes `/admin/login`; paste has no login form as main flow | unit (return-to helper) + manual/E2E smoke | `cd frontend && npm test -- --run lib/adminReturnTo.test.ts` | ❌ Wave 0 |
| ADMN-02 | Privacy page shows discreet "Acesso administrativo" link below final disclaimer leading to `/admin/login` | manual/E2E smoke (or component test if setup added) | `cd frontend && npm run build` | ❌ Wave 0 for automated UI assertion |

### Sampling Rate
- **Per task commit:** `cd frontend && npm test -- --run lib/adminReturnTo.test.ts` (if helper extracted) and targeted lint/typecheck as applicable
- **Per wave merge:** `cd frontend && npm test && npm run build`
- **Phase gate:** Full frontend suite green + build green before `/gsd-verify-work`; manual smoke for login redirect flow and privacy link

### Wave 0 Gaps
- [ ] `frontend/lib/adminReturnTo.test.ts` — covers safe return-to sanitization, loop prevention, fallback.
- [ ] Component/E2E harness for admin login flow — current Vitest config only includes `lib/**/*.test.ts` with `environment: "node"`; no React Testing Library/Playwright config found. [VERIFIED: vitest.config.ts, glob for playwright/e2e]
- [ ] Optional: `frontend/scripts/verify-ssr.ps1` update/check for `/admin/login` presence and `/admin/paste` no-login behavior (if script remains in scope).

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Keep existing backend password+Turnstile+JWT flow; do not weaken client checks. [VERIFIED: auth.py] |
| V3 Session Management | yes | Keep token in `sessionStorage` `nqu_admin_token`; clear on logout/401; hard reload on logout where needed. [VERIFIED: auth.ts, LogoutButton.tsx, 401 handlers] |
| V4 Access Control | yes | Client guard redirect for admin pages; backend still enforces auth on admin APIs. [VERIFIED: useAdminGuard usage, API 401 handlers] |
| V5 Input Validation | yes | Validate/sanitize `next` return-to param as internal admin path only. [ASSUMED: standard open-redirect defense] |
| V6 Cryptography | no (no change) | Backend owns JWT/bcrypt; phase must not touch crypto. [VERIFIED: security.py] |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Open redirect via login `next` param | Spoofing / Elevation via phishing flow | Allowlist internal `/admin/...` paths, reject absolute/protocol-relative/backslash/invalid targets, fallback `/admin`. |
| Auth bypass confusion by stale client state | Elevation of privilege (UI confusion) | Keep backend 401 as authority; on 401 clear token and redirect to login. |
| Session fixation/leak via URL token | Information disclosure | Never put JWT in query params; keep session in sessionStorage only. |
| Login brute force / bot | Denial of service / Spoofing | Preserve existing Turnstile + rate limit + password verification order in backend. [VERIFIED: auth.py] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/26-acesso-admin-dedicado/26-CONTEXT.md` — locked decisions D-01..D-12, discretion, deferred ideas.
- `.planning/REQUIREMENTS.md` §Acesso Admin — ADMN-01, ADMN-02.
- `.planning/ROADMAP.md` §Phase 26 — goal, success criteria, UI hint.
- `frontend/app/admin/layout.tsx` — current admin shell/nav/logout.
- `frontend/app/admin/paste/ExtractForm.tsx` — embedded login + extraction, Turnstile, sessionStorage, 401 handling.
- `frontend/components/admin/AdminGuard.tsx` — current unauthenticated redirect to `/admin/paste`.
- `frontend/components/admin/LogoutButton.tsx` — current hard replace to `/admin/paste`.
- `frontend/lib/api.ts` — `loginAdmin` contract, `ApiError`.
- `frontend/lib/auth.ts` — `TOKEN_KEY`.
- `frontend/app/(public)/privacidade/page.tsx` — disclaimer box insertion point.
- `frontend/app/admin/review/ReviewQueue.tsx`, `frontend/app/admin/review/EditJobDialog.tsx`, `frontend/app/admin/social-posts/SocialPostsClient.tsx` — 401 hard redirects to `/admin/paste`.
- `backend/app/api/v1/auth.py`, `backend/app/schemas/auth.py`, `backend/app/core/security.py` — auth contract and security behavior.
- `frontend/package.json`, `frontend/vitest.config.ts` — test/runtime stack reality.

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified from package.json and existing codebase.
- Architecture: HIGH - verified from current routes/layouts/components; minor Next `useSearchParams` behavior note marked ASSUMED.
- Pitfalls: HIGH - grounded in observed code paths and standard open-redirect/session-flow risks.

**Research date:** 2026-11-22
**Valid until:** 2026-12-22 (stable internal routing/auth UX; recheck if admin auth model changes)
