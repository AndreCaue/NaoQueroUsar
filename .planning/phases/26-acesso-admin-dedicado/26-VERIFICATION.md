---
phase: 26-acesso-admin-dedicado
verified: 2026-11-22T18:37:19-03:00
status: human_needed
score: 7/7 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Login admin completo pela página dedicada"
    expected: "Ao acessar /admin/login deslogado, ver formulário dedicado (sem Publicações/Integrações/Sair). Com NEXT_PUBLIC_TURNSTILE_SITE_KEY e backend configurados, informar senha válida, concluir Turnstile, clicar Entrar e ser redirecionado para /admin ou para o next sanitizado (ex.: /admin/review?next=...)."
    why_human: "Turnstile e autenticação real dependem de chave/site key válida, backend ativo e interação de browser; não é possível validar o fluxo completo de ponta a ponta apenas por inspeção estática/build."
---

# Phase 26: Acesso Admin Dedicado Verification Report

**Phase Goal:** Admin acessa login por página dedicada e o ponto de entrada público permanece discreto.
**Verified:** 2026-11-22T18:37:19-03:00
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Admin consegue abrir `/admin/login` como página dedicada, separada de paste/revisão, sem nav admin enquanto deslogado. | ✓ VERIFIED | `frontend/app/admin/login/page.tsx` renderiza `AdminLoginForm` em `<Suspense>`; `frontend/components/admin/AdminChrome.tsx` oculta Publicações/Integrações/Sair quando `pathname === "/admin/login"`; `frontend/app/admin/layout.tsx` usa `AdminChrome`; build Next.js inclui rota `/admin/login`. |
| 2 | Login dedicado autentica via contrato existente e redireciona com `next` sanitizado (ou `/admin`). | ✓ VERIFIED | `AdminLoginForm.tsx` chama `loginAdmin(password, cfToken)`, grava `TOKEN_KEY` em `sessionStorage`, e faz `router.replace(sanitizeAdminReturnTo(searchParams.get("next")) ?? "/admin")`; também redireciona usuário já autenticado ao montar. `frontend/lib/api.ts` exporta `loginAdmin(password, cfToken)`. |
| 3 | Acesso não autenticado a rota admin protegida redireciona para `/admin/login?next=<destino sanitizado>`. | ✓ VERIFIED | `frontend/components/admin/AdminGuard.tsx` usa `usePathname/useSearchParams`, calcula caminho atual e faz `router.replace(buildAdminLoginHref(current))` quando não há token. `frontend/lib/adminReturnTo.ts` aceita apenas caminhos `/admin`, rejeita `//`, `\`, externos, vazios/nulos e mapeia `/admin/login*` para `/admin`. Testes unitários passam (6/6). |
| 4 | Logout limpa sessão e navega para `/admin/login`; handlers 401 de admin redirecionam para `/admin/login` com return-to seguro. | ✓ VERIFIED | `frontend/components/admin/LogoutButton.tsx` remove `nqu_admin_token` e faz `window.location.replace("/admin/login")`. `ExtractForm.tsx`, `ReviewQueue.tsx`, `EditJobDialog.tsx`, `SocialPostsClient.tsx` removem token em 401 e usam `buildAdminLoginHref(window.location.pathname + window.location.search)`. Grep em `frontend/**/*.{ts,tsx,ps1}` não encontrou redirect de auth para `/admin/paste` (apenas link de navegação em `app/admin/page.tsx` e checagem de rota no script SSR). |
| 5 | Página de paste/revisão não exige formulário de login como fluxo principal; extração é protegida por guard. | ✓ VERIFIED | `frontend/app/admin/paste/ExtractForm.tsx` usa `useAdminGuard()`, não importa `loginAdmin`/`next-turnstile`, não contém campos de senha/Turnstile/Sair; mantém extração com `extractJobs`. `frontend/app/admin/paste/page.tsx` preserva shell SSR "Admin — Colar vagas" e envolve `ExtractForm` em `<Suspense>`. `ReviewQueue` continua protegido por `useAdminGuard()`. |
| 6 | Usuário encontra link discreto "Acesso administrativo" na Política de Privacidade apontando para `/admin/login`. | ✓ VERIFIED | `frontend/app/(public)/privacidade/page.tsx` importa `Link`, adiciona `<p className="mt-3 text-xs text-fg-muted/80">` abaixo do disclaimer final com `href="/admin/login"` e label exata `Acesso administrativo`. |
| 7 | Regressões de App Router/Suspense cobertas para callers de `useAdminGuard` com `useSearchParams`. | ✓ VERIFIED | `frontend/app/admin/page.tsx`, `frontend/app/admin/review/page.tsx`, `frontend/app/admin/social-posts/page.tsx` envolvem conteúdo guardado em `<Suspense>`. `frontend/app/admin/integracoes/page.tsx` já possuía Suspense (não modificado). `npm run build` passou. |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `frontend/lib/adminReturnTo.ts` | Pure sanitize/build helpers for admin return-to | ✓ VERIFIED | 42 linhas; exporta `sanitizeAdminReturnTo` e `buildAdminLoginHref`; rejeita externo/protocol-relative/backslash/control chars; previne loop `/admin/login*`. |
| `frontend/lib/adminReturnTo.test.ts` | Unit coverage for return-to sanitization | ✓ VERIFIED | 39 linhas; 6 testes cobrindo caminhos válidos, loop, rejeições e href encoding; `vitest --run` passou. |
| `frontend/app/admin/login/page.tsx` | Dedicated /admin/login route | ✓ VERIFIED | 13 linhas; rota dedicada com `Suspense` e `AdminLoginForm`. |
| `frontend/components/admin/AdminLoginForm.tsx` | Client login form with Turnstile, password, redirect | ✓ VERIFIED | 134 linhas; "use client"; Turnstile `action="login"`; `loginAdmin`; `sessionStorage.setItem(TOKEN_KEY, t)`; `sanitizeAdminReturnTo`; mensagens/copy do UI-SPEC. |
| `frontend/components/admin/AdminChrome.tsx` | Pathname-aware admin shell chrome | ✓ VERIFIED | 75 linhas; oculta nav no login; mostra Publicações/Integrações/LogoutButton nas demais rotas admin. |
| `frontend/components/admin/AdminGuard.tsx` | Guard redirect to `/admin/login?next=...` | ✓ VERIFIED | 38 linhas; usa `buildAdminLoginHref`; sem `/admin/paste`. |
| `frontend/components/admin/LogoutButton.tsx` | Logout hard replace to `/admin/login` | ✓ VERIFIED | 29 linhas; `window.location.replace("/admin/login")`. |
| `frontend/app/admin/paste/ExtractForm.tsx` | Extraction-only admin form guarded by useAdminGuard | ✓ VERIFIED | 178 linhas; `useAdminGuard()`, `buildAdminLoginHref` em 401, sem login/Turnstile/senha/Sair. |
| `frontend/app/(public)/privacidade/page.tsx` | Discreet admin login entry point | ✓ VERIFIED | Contém link discreto `Acesso administrativo` para `/admin/login` abaixo do disclaimer. |
| `frontend/app/admin/review/ReviewQueue.tsx` | 401 handler redirecting to /admin/login | ✓ VERIFIED | `handleAuthError` usa `buildAdminLoginHref`; sem `/admin/paste`. |
| `frontend/app/admin/review/EditJobDialog.tsx` | 401 handler redirecting to /admin/login | ✓ VERIFIED | `handleAuthExpired` usa `buildAdminLoginHref`; sem `/admin/paste`. |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | 401 handler redirecting to /admin/login | ✓ VERIFIED | `handleAuthError` usa `buildAdminLoginHref`; sem `/admin/paste`. |
| `frontend/scripts/verify-ssr.ps1` | SSR smoke updated for login route | ✓ VERIFIED | Mantém check `/admin/paste`; adiciona check tolerante `/admin/login` com marcador `Acesso administrativo|Entrar|Carregando`. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `frontend/components/admin/AdminGuard.tsx` | `frontend/lib/adminReturnTo.ts` | `buildAdminLoginHref` | ✓ WIRED | Importa e chama helper no redirect de token ausente. |
| `frontend/components/admin/AdminLoginForm.tsx` | `frontend/lib/api.ts` | `loginAdmin(password, cfToken)` | ✓ WIRED | Importa e chama `loginAdmin`; contrato exportado em `api.ts:170`. |
| `frontend/components/admin/AdminLoginForm.tsx` | `frontend/lib/adminReturnTo.ts` | `sanitizeAdminReturnTo` | ✓ WIRED | Sanitiza `next` ao montar e após login antes de `router.replace`. |
| `frontend/app/admin/layout.tsx` | `frontend/components/admin/AdminChrome.tsx` | render `<AdminChrome>` | ✓ WIRED | Layout server preserva metadata/providers e delega chrome. |
| `frontend/app/admin/paste/ExtractForm.tsx` | `frontend/components/admin/AdminGuard.tsx` | `useAdminGuard()` | ✓ WIRED | Extração depende de token do guard; sem login embutido. |
| `frontend/app/admin/review/ReviewQueue.tsx` | `frontend/lib/adminReturnTo.ts` | 401 redirect | ✓ WIRED | `buildAdminLoginHref` usado no `handleAuthError`. |
| `frontend/app/(public)/privacidade/page.tsx` | `/admin/login` | Next `<Link>` | ✓ WIRED | Link discreto abaixo do disclaimer final. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `AdminLoginForm.tsx` | `next` / `token` | `searchParams.get("next")`, `loginAdmin()` response, `sessionStorage` | Yes - redirect target sanitizado; token vem da API e é persistido em sessão | ✓ FLOWING |
| `AdminGuard.tsx` | `token` / `current` path | `sessionStorage.getItem(TOKEN_KEY)`, `pathname + searchParams` | Yes - caminho atual calculado e sanitizado para redirect | ✓ FLOWING |
| `ExtractForm.tsx` | `token`, `summary` | `useAdminGuard()`, `extractJobs(token, cleaned)` | Yes - extração usa token real e resposta da API | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Return-to helper unit tests | `cd frontend; npm test -- --run lib/adminReturnTo.test.ts` | 1 file passed, 6 tests passed | ✓ PASS |
| Next.js production build / route registration | `cd frontend; npm run build` | Build/typecheck passed; rotas incluem `/admin/login` e `/admin/paste` | ✓ PASS |
| Stale admin auth redirect to `/admin/paste` | `grep /admin/paste frontend/**/*.{ts,tsx,ps1}` | Apenas `app/admin/page.tsx` (link de navegação) e `scripts/verify-ssr.ps1` (checagem de rota) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| ADMN-01 | 26-01-PLAN.md, 26-02-PLAN.md | Admin acessa login em página dedicada, separada da página de paste/revisão | ✓ SATISFIED | `/admin/login` dedicado com `AdminLoginForm` + `AdminChrome` sem nav; `AdminGuard`/`LogoutButton`/401 handlers apontam para `/admin/login`; `ExtractForm` não tem login embutido; build passou. |
| ADMN-02 | 26-02-PLAN.md | Usuário encontra um link discreto para login admin na página de Política de Privacidade | ✓ SATISFIED | `privacidade/page.tsx` tem link discreto `Acesso administrativo` para `/admin/login` abaixo do disclaimer, estilo `text-xs text-fg-muted/80`. |

Orphaned requirements for Phase 26: None (REQUIREMENTS.md maps only ADMN-01, ADMN-02 to Phase 26).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| — | — | None detected in phase-modified files | ℹ️ Info | Scanned modified admin/auth/privacy files for TODO/FIXME/placeholder/empty return stubs; no blocking anti-pattern found. `return null` in `AdminLoginForm`/guard paths are control-flow guards, not stub UI. |

### Human Verification Required

### 1. Login admin completo pela página dedicada

**Test:** Com frontend e backend rodando e `NEXT_PUBLIC_TURNSTILE_SITE_KEY` configurado, acessar `/admin/review` deslogado; confirmar redirect para `/admin/login?next=%2Fadmin%2Freview`; autenticar com senha válida; depois visitar `/admin/login` autenticado e por fim clicar em `Sair`.
**Expected:** Deslogado cai em login dedicado sem nav admin; login bem-sucedido retorna ao `next` sanitizado ou `/admin`; `/admin/login` autenticado redireciona para `/admin`/next seguro; logout limpa sessão e leva a `/admin/login`.
**Why human:** Turnstile real, senha válida e backend ativo exigem ambiente integrado e interação de browser.

### Gaps Summary

No automated gaps found. Codebase evidence supports all phase must-haves and both requirement IDs. Status is `human_needed` only because live Turnstile/backend browser smoke cannot be fully proven programmatically in this verification pass.

---

_Verified: 2026-11-22T18:37:19-03:00_
_Verifier: OpenCode (gsd-verifier)_
