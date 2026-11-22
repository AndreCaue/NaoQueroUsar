# Phase 26: Acesso Admin Dedicado - Pattern Map

**Mapped:** 2026-11-22
**Files analyzed:** 15
**Analogs found:** 15 / 15

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `frontend/app/admin/login/page.tsx` | page/route (client) | request-response | `frontend/app/admin/paste/page.tsx` + login branch in `frontend/app/admin/paste/ExtractForm.tsx` | role-match |
| `frontend/components/admin/AdminLoginForm.tsx` *(recommended new, discretion)* | component (client form) | request-response | `frontend/app/admin/paste/ExtractForm.tsx` (login branch, lines 164-209) | exact |
| `frontend/components/admin/AdminChrome.tsx` *(recommended new, discretion)* | layout chrome component (client) | request-response | `frontend/app/admin/layout.tsx` (header/nav, lines 22-62) | exact |
| `frontend/lib/adminReturnTo.ts` *(recommended new)* | utility | transform/pure | `frontend/lib/chatFocus.ts` | role-match |
| `frontend/lib/adminReturnTo.test.ts` *(recommended new, Wave 0)* | test | transform/pure | `frontend/lib/chatFocus.test.ts` | exact |
| `frontend/app/admin/layout.tsx` | layout (server) | request-response | itself (existing) | exact |
| `frontend/components/admin/AdminGuard.tsx` | guard hook (client) | request-response | itself (existing) | exact |
| `frontend/components/admin/LogoutButton.tsx` | component (client) | request-response | itself (existing) | exact |
| `frontend/app/admin/paste/page.tsx` | page/route (server) | request-response | itself (existing) | exact |
| `frontend/app/admin/paste/ExtractForm.tsx` | component (client form) | request-response | itself (existing) | exact |
| `frontend/app/(public)/privacidade/page.tsx` | page/route (server/static) | static content | itself (existing) | exact |
| `frontend/app/admin/review/ReviewQueue.tsx` | component (client) | request-response | itself (401 handler) | exact |
| `frontend/app/admin/review/EditJobDialog.tsx` | component (client) | request-response | itself (401 handler) | exact |
| `frontend/app/admin/social-posts/SocialPostsClient.tsx` | component (client) | request-response | itself (401 handler) | exact |
| `frontend/scripts/verify-ssr.ps1` *(optional update)* | script | batch/check | itself (existing) | exact |

## Pattern Assignments

### `frontend/app/admin/login/page.tsx` (page/route, request-response) — NEW

**Analogs:** `frontend/app/admin/paste/page.tsx` (server page shell) and `frontend/app/admin/integracoes/page.tsx` (Suspense boundary for client search params/client component).

**Page shell pattern** (`frontend/app/admin/paste/page.tsx:1-9`):
```tsx
export default async function Page() {
  const { default: ExtractForm } = await import("./ExtractForm");
  return (
    <main className="py-8">
      <h1 className="text-6xl font-bold tracking-tight mb-3">Admin — Colar vagas</h1>
      <ExtractForm />
    </main>
  );
}
```

**Suspense-for-client-component pattern** (`frontend/app/admin/integracoes/page.tsx:1-24`):
```tsx
import { Suspense } from "react";
import { IntegrationsClient } from "@/app/admin/integracoes/IntegrationsClient";

export default function Page() {
  return (
    <div>
      <h1 className="text-3xl font-semibold leading-tight tracking-tight">
        Integrações
      </h1>
      <p className="mt-2 text-fg-muted">
        Conecte sua Página do Facebook para publicar vagas automaticamente
        quando a integração estiver ativa.
      </p>

      <Suspense
        fallback={
          <p className="mt-6 text-fg-muted">Carregando integrações...</p>
        }
      >
        <IntegrationsClient />
      </Suspense>
    </div>
  );
}
```

**Apply:** Create `/admin/login` as a focused login page (D-01, D-09, D-10). If using `useSearchParams()` for `next`, isolate in a client component wrapped by `<Suspense>` (RESEARCH Pitfall 6). Keep copy direct/objective (Discretion). Include discreet "voltar ao site público" link (D-11). Do not render admin nav; relies on conditional chrome in layout (D-09).

---

### `frontend/components/admin/AdminLoginForm.tsx` (component, request-response) — NEW (recommended)

**Analog:** `frontend/app/admin/paste/ExtractForm.tsx` login branch.

**Imports / Turnstile setup** (`frontend/app/admin/paste/ExtractForm.tsx:1-22`):
```tsx
"use client";

import { useEffect, useState, type ClipboardEvent } from "react";
import { Turnstile } from "next-turnstile";
import {
  ApiError,
  loginAdmin,
  extractJobs,
  type ExtractSummary,
} from "@/lib/api";
import { TOKEN_KEY } from "@/lib/auth";
import { TERM_REMOVED_NOTICE, stripBlockedTerms } from "@/lib/blocklist";

// The site key is a public value (the secret never reaches the browser).
// Outside production we fall back to Cloudflare's public always-pass test key
// so local dev works without a Cloudflare account. In production the env var
// is mandatory: without it the widget does not render and the login stays
// blocked — fail closed (D-15).
const TURNSTILE_SITE_KEY =
  process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ||
  (process.env.NODE_ENV === "production" ? "" : "1x00000000000000000000AA");
```

**Turnstile reset pattern** (`frontend/app/admin/paste/ExtractForm.tsx:45-52`):
```tsx
  // next-turnstile has no reset API: the widget is remounted with a new React
  // key, which removes the old widget and renders a fresh one — the consumed
  // token is never sent twice (D-19/T-03-18).
  const resetTurnstile = () => {
    setCfToken(null);
    setTurnstileKey((k) => k + 1);
  };
```

**Login handler pattern** (`frontend/app/admin/paste/ExtractForm.tsx:76-98`):
```tsx
  const handleLogin = async () => {
    if (!cfToken) return;
    setError(null);
    setSummary(null);
    setLoading(true);
    try {
      const t = await loginAdmin(password, cfToken);
      setToken(t);
      try {
        window.sessionStorage.setItem(TOKEN_KEY, t);
      } catch {
        // ignore storage errors
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao autenticar";
      setError(msg);
      // The token was consumed by the backend (or refused) — a new one is
      // needed for the next attempt.
      resetTurnstile();
    } finally {
      setLoading(false);
    }
  };
```

**Login UI pattern** (`frontend/app/admin/paste/ExtractForm.tsx:158-209`):
```tsx
  const isLoginDisabled = loading || !password.trim() || !cfToken;
  ...
        {!token && (
          <div>
            <h2 className="text-xl font-semibold">Login</h2>
            <label>
              Senha do admin
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                className="h-12 w-full rounded-lg border border-line-strong bg-canvas px-3 text-base text-fg placeholder:text-fg-muted focus-visible outline-accent-soft"
              />
            </label>
            {TURNSTILE_SITE_KEY ? (
              <div className="overflow-hidden max-w-full">
                <Turnstile
                  key={turnstileKey}
                  siteKey={TURNSTILE_SITE_KEY}
                  action="login"
                  theme="dark"
                  appearance="always"
                  onVerify={(token) => setCfToken(token)}
                  onExpire={() => setCfToken(null)}
                  onError={() => setCfToken(null)}
                />
              </div>
            ) : (
              <div className="bg-[rgba(248,113,113,0.1)] border border-danger text-danger-soft rounded-lg p-3">
                Configuração ausente: defina PUBLIC_TURNSTILE_SITE_KEY
              </div>
            )}
            <button
              className="min-h-11 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white hover:bg-accent-strong-hover"
              onClick={handleLogin}
              disabled={isLoginDisabled}
            >
              {loading ? "Entrando..." : "Entrar"}
            </button>

            {error && (
              <div className="bg-[rgba(248,113,113,0.1)] border border-danger text-danger-soft rounded-lg p-3">
                {error}
              </div>
            )}
          </div>
        )}
```

**Apply:** Reuse Turnstile setup, reset-by-key, `loginAdmin` contract, error/loading/disabled states. On success, store `TOKEN_KEY` in sessionStorage then redirect via `router.replace(sanitizeAdminReturnTo(next) ?? "/admin")` (D-02). If already authenticated on mount, redirect per D-04. Keep auth contract unchanged (`password`, `cf_token`).

---

### `frontend/components/admin/AdminChrome.tsx` (component, request-response) — NEW (recommended)

**Analog:** `frontend/app/admin/layout.tsx` header/nav structure.

**Current admin shell** (`frontend/app/admin/layout.tsx:17-63`):
```tsx
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ToastProvider>
      <div className="flex min-h-screen flex-col bg-canvas text-fg">
        <header className="sticky top-0 z-40 border-b border-line bg-canvas">
          <div className="mx-auto flex h-16 w-full max-w-[1120px] items-center justify-between gap-4 px-4 md:px-6">
            <div className="flex items-center gap-4">
              <Link href="/" className="text-xl font-semibold text-fg">
                EmpregaNoix
                <span aria-hidden="true" className="text-accent-soft">
                  .
                </span>
              </Link>
              <span className="hidden text-sm font-normal text-fg-muted md:inline">
                Procurar um emprego, não deve dar trabalho
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Link
                href="/admin/social-posts"
                className="text-sm text-fg-muted transition-colors hover:text-fg focus-visible:text-fg"
              >
                Publicações
              </Link>
              <Link
                href="/admin/integracoes"
                className="text-sm text-fg-muted transition-colors hover:text-fg focus-visible:text-fg"
              >
                Integrações
              </Link>
              <LogoutButton />
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1120px] flex-1 px-4 py-8 md:px-6">
          {children}
        </main>
      </div>
    </ToastProvider>
  );
}
```

**Apply:** Make chrome pathname-aware (D-09). On `/admin/login`, hide Publicações/Integrações/Sair; keep minimal branding and admin theme tokens. Keep `layout.tsx` as server component exporting metadata/viewport/css/providers; delegate chrome to client component using `usePathname()`. Verify login page has no admin nav while logged out.

---

### `frontend/lib/adminReturnTo.ts` (utility, transform) — NEW (recommended)

**Analog:** `frontend/lib/chatFocus.ts` (small pure function, exported, testable).

**Pure utility pattern** (`frontend/lib/chatFocus.ts:1-8`):
```ts
export function getChatDetailCloseFocusTarget(
  trigger: HTMLElement | null | undefined,
  fallback: HTMLElement | null | undefined,
): HTMLElement | null {
  if (trigger?.isConnected) return trigger;
  if (fallback?.isConnected) return fallback;
  return null;
}
```

**Apply:** Implement `sanitizeAdminReturnTo(value: string | null | undefined): string | null` (and optionally `buildAdminLoginHref(next)` helper). Security rules (RESEARCH Pitfall 2/A3): allow only internal paths starting with `/admin`, reject `//`, reject backslashes, reject/normalize `/admin/login` to avoid loop, fallback `null`/`/admin`. Never pass raw `next` to `router.replace`.

---

### `frontend/lib/adminReturnTo.test.ts` (test, transform) — NEW (Wave 0)

**Analog:** `frontend/lib/chatFocus.test.ts`.

**Vitest unit test pattern** (`frontend/lib/chatFocus.test.ts:1-43`):
```ts
import { describe, expect, it, vi } from "vitest";

import { getChatDetailCloseFocusTarget } from "./chatFocus";

describe("getChatDetailCloseFocusTarget", () => {
  it("returns trigger when trigger.isConnected is true", () => {
    const trigger = { isConnected: true, focus: vi.fn() } as unknown as HTMLElement;
    const fallback = { isConnected: true, focus: vi.fn() } as unknown as HTMLElement;

    expect(getChatDetailCloseFocusTarget(trigger, fallback)).toBe(trigger);
  });
  ...
});
```

**Vitest config constraint** (`frontend/vitest.config.ts:13-18`):
```ts
  test: {
    environment: "node",
    include: ["lib/**/*.test.ts"],
    globals: false,
  },
```

**Apply:** Place at `frontend/lib/adminReturnTo.test.ts` so existing Vitest config picks it up. Cover: valid `/admin/*` paths, preserves query string, rejects absolute URLs/protocol-relative/backslashes/non-admin paths, maps `/admin/login` to safe fallback or `/admin`, null/undefined/empty fallback. Run: `cd frontend && npm test -- --run lib/adminReturnTo.test.ts`.

---

### `frontend/app/admin/layout.tsx` (layout, request-response) — MODIFY

**Analog:** itself. Current file is the source of truth for admin shell (see AdminChrome section above).

**Server layout metadata/provider pattern** (`frontend/app/admin/layout.tsx:1-16`):
```tsx
import type { Metadata, Viewport } from "next";
import Link from "next/link";

import "./admin.css";
import { LogoutButton } from "@/components/admin/LogoutButton";
import { ToastProvider } from "@/components/admin/ToastProvider";

export const metadata: Metadata = {
  title: "EmpregaNoix - Painel admin",
  description: "Painel de administração - curadoria de vagas",
};

export const viewport: Viewport = {
  themeColor: "#0f0a1a",
};
```

**Apply:** Preserve metadata, viewport, `admin.css` import, `ToastProvider`. Move nav/header rendering to a client `AdminChrome` (or equivalent) that hides admin nav on `/admin/login` (D-09). Keep admin theme available on login page (D-12).

---

### `frontend/components/admin/AdminGuard.tsx` (guard hook, request-response) — MODIFY

**Analog:** itself.

**Current guard** (`frontend/components/admin/AdminGuard.tsx:1-33`):
```tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { TOKEN_KEY } from "@/lib/auth";

/**
 * Hook that protects admin routes.
 *
 * Reads the admin token from sessionStorage after mount (never during SSR)
 * and redirects to /admin/paste when it is absent. Returns the token so
 * callers can use it for authenticated requests.
 */
export function useAdminGuard(): string | null {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = sessionStorage.getItem(TOKEN_KEY);
    } catch {
      // ignore storage errors
    }
    setToken(stored);
    if (!stored) {
      router.replace("/admin/paste");
    }
  }, [router]);

  return token;
}
```

**Apply:** Change redirect target to `/admin/login` (D-03). Capture current admin path + search as sanitized `next` (use `usePathname()` + `useSearchParams()` or `window.location`). Avoid open redirect by sanitizing with `adminReturnTo` helper. Keep sessionStorage read-after-mount pattern to avoid SSR mismatch. Keep return type `string | null`.

---

### `frontend/components/admin/LogoutButton.tsx` (component, request-response) — MODIFY

**Analog:** itself.

**Current logout** (`frontend/components/admin/LogoutButton.tsx:1-29`):
```tsx
"use client";

import { TOKEN_KEY } from "@/lib/auth";

/**
 * Logs out by clearing the stored JWT and hard-navigating to the login page.
 * A full reload is intentional: components such as ExtractForm keep the token
 * in memory, so a client-side route change would leave the session alive.
 */
export function LogoutButton() {
  const handleLogout = () => {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // ignore storage errors
    }
    window.location.replace("/admin/paste");
  };

  return (
    <button
      type="button"
      onClick={handleLogout}
      className="min-h-11 rounded-md px-3 text-sm font-medium text-fg-muted transition-colors hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
    >
      Sair
    </button>
  );
}
```

**Apply:** Change hard redirect to `/admin/login` (D-04). Keep hard reload rationale (clears in-memory token in client components). Keep TOKEN_KEY removal and ignore storage errors.

---

### `frontend/app/admin/paste/page.tsx` (page/route, request-response) — MODIFY

**Analog:** itself; also protected page pattern in `frontend/app/admin/review/page.tsx`.

**Current paste page** (`frontend/app/admin/paste/page.tsx:1-9`):
```tsx
export default async function Page() {
  const { default: ExtractForm } = await import("./ExtractForm");
  return (
    <main className="py-8">
      <h1 className="text-6xl font-bold tracking-tight mb-3">Admin — Colar vagas</h1>
      <ExtractForm />
    </main>
  );
}
```

**Protected page analog** (`frontend/app/admin/review/page.tsx:1-17`):
```tsx
"use client";

import { ReviewQueue } from "@/app/admin/review/ReviewQueue";

export default function Page() {
  return (
    <div>
      <h1 className="text-[20px] font-semibold leading-tight [overflow-wrap:anywhere] [text-wrap:balance]">
        Revisão de vagas
      </h1>
      <p className="mt-1 text-[14px] text-fg-muted">
        Confira o texto-fonte ao lado e aprove para publicar.
      </p>
      <ReviewQueue />
    </div>
  );
}
```

**Apply:** Paste remains extraction entry (SC4), but it must no longer be the login flow. After ExtractForm becomes extraction-only, guard protection should be enforced via `useAdminGuard()` either in page/client wrapper or in ExtractForm (choose one clear owner; avoid double redirects). Keep route `/admin/paste` working.

---

### `frontend/app/admin/paste/ExtractForm.tsx` (component, request-response) — MODIFY

**Analog:** itself. The extraction branch is the pattern to keep; login branch is the pattern to remove.

**Extraction/session patterns to keep** (`frontend/app/admin/paste/ExtractForm.tsx:53-75,100-136,211-306`):
```tsx
  // IN-08: one place clears every trace of the admin session — token in memory
  // and in sessionStorage, pasted text and any stale summary/error.
  const clearSession = () => {
    setToken(null);
    setPassword("");
    setText("");
    setSummary(null);
    setError(null);
    setNotice(null);
    try {
      window.sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // ignore storage errors
    }
  };

  const handleLogout = () => {
    clearSession();
    // The login form comes back with a fresh widget, so a new Turnstile token
    // is required for the next login (the old one was single-use).
    resetTurnstile();
  };
...
  const handleSubmit = async () => {
    const cleaned = stripBlockedTerms(text); // defesa final: nada de termo vai à API
    if (!token || !cleaned.trim()) return;
    if (cleaned !== text) {
      setText(cleaned);
      setNotice(TERM_REMOVED_NOTICE);
    }
    setError(null);
    setSummary(null);
    setLoading(true);
    try {
      const res = await extractJobs(token, cleaned);
      setSummary(res);
    } catch (err) {
      // IN-08: an expired/invalid JWT must drop the session instead of leaving
      // the form stuck retrying with a dead token (clearSession first — it
      // resets the error state, so the message is set afterwards).
      if (err instanceof ApiError && err.status === 401) {
        clearSession();
        resetTurnstile();
        setError("Sessão expirada — entre novamente.");
        return;
      }
      const msg = err instanceof Error ? err.message : "Erro ao extrair";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };
```

**Apply:** Remove embedded login form/Turnstile login state as main flow (ADMN-01, SC4). Keep extraction behavior, blocklist paste sanitization, 401 session expiry handling. Update 401 handling to redirect to `/admin/login` (and preserve return-to if feasible) instead of leaving dead form; align with shared 401 pattern. If logout remains, route to `/admin/login`. Prefer obtaining token via `useAdminGuard()` or existing sessionStorage read; avoid duplicating login UI.

---

### `frontend/app/(public)/privacidade/page.tsx` (page/route, static content) — MODIFY

**Analog:** itself.

**Insertion point below final disclaimer box** (`frontend/app/(public)/privacidade/page.tsx:193-204`):
```tsx
        <div className="mt-12 rounded-md border border-line bg-surface p-4 text-sm leading-relaxed text-fg-muted">
          <p>
            Somos apenas meio de divulgação. As vagas são obtidas de grupos
            públicos de WhatsApp e o contato é disponibilizado após validação
            anti-bot. Não armazenamos dados de candidatura e não nos
            responsabilizamos por interações entre candidatos e empresas.
          </p>
        </div>
      </div>
    </article>
  );
}
```

**Apply:** Add a small, muted, own-line link below the disclaimer box (D-05, D-06, D-08). Text exactly "Acesso administrativo" (D-07). Use `next/link` to `/admin/login`. Keep visual weight discreet (e.g., `text-xs`, muted color, simple hover); no button/icon/callout.

---

### `frontend/app/admin/review/ReviewQueue.tsx` (component, request-response) — MODIFY

**Analog:** itself (401 handler).

**401 handler** (`frontend/app/admin/review/ReviewQueue.tsx:26-38`):
```tsx
/** A 401 means the JWT expired: end the session instead of looping on retry. */
function handleAuthError(err: unknown): boolean {
  if (err instanceof ApiError && err.status === 401) {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // ignore storage errors
    }
    window.location.replace("/admin/paste");
    return true;
  }
  return false;
}
```

**Apply:** Replace `/admin/paste` with `/admin/login` (D-03/D-04 flow consistency). Prefer preserving return-to (`window.location.pathname + window.location.search`, sanitized) when possible. Keep hard navigation to clear in-memory state.

---

### `frontend/app/admin/review/EditJobDialog.tsx` (component, request-response) — MODIFY

**Analog:** itself (401 handler).

**401 handler** (`frontend/app/admin/review/EditJobDialog.tsx:332-339`):
```tsx
  const handleAuthExpired = () => {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // ignore
    }
    window.location.replace("/admin/paste");
  };
```

**Apply:** Same as ReviewQueue: redirect to `/admin/login`, keep token clear, keep hard navigation. Preserve return-to if feasible.

---

### `frontend/app/admin/social-posts/SocialPostsClient.tsx` (component, request-response) — MODIFY

**Analog:** itself (401 handler).

**401 handler** (`frontend/app/admin/social-posts/SocialPostsClient.tsx:53-64`):
```tsx
  const handleAuthError = useCallback((err: unknown): boolean => {
    if (err instanceof ApiError && err.status === 401) {
      try {
        sessionStorage.removeItem(TOKEN_KEY);
      } catch {
        // ignore
      }
      window.location.replace("/admin/paste");
      return true;
    }
    return false;
  }, []);
```

**Apply:** Same 401 redirect update to `/admin/login`; preserve safe return-to when feasible.

---

### `frontend/scripts/verify-ssr.ps1` (script, batch/check) — MODIFY (optional)

**Analog:** itself.

**Current admin checks hardcoded to /admin/paste** (`frontend/scripts/verify-ssr.ps1:70-82`):
```powershell
$admin = Get-Html "$BaseUrl/admin/paste"
Assert ($admin -match "Colar vagas") "Admin page missing 'Colar vagas'"
Assert (-not ($admin -match "Vagas abertas")) "Admin page leaks public heading"
Assert (-not ($admin -match "Espaço publicitário")) "Admin page leaks ad slot"
$adminCssUrls = Get-StylesheetUrls $admin
foreach ($cssUrl in $adminCssUrls) {
    try {
        $css = Get-Asset $cssUrl
        Assert (-not ($css -match "--color-canvas")) "Admin stylesheet leaks --color-canvas: $cssUrl"
    } catch { }
}
Write-Output "PASS - admin HTML renders its own form and no public theme"
```

**Apply:** If SSR smoke script remains in phase scope, update for `/admin/login` presence and ensure `/admin/paste` no longer behaves as login page. Adjust assertions carefully to match new intended SSR/HTML behavior (login page may be client-heavy; verify against actual rendered HTML).

## Shared Patterns

### Admin session key and storage

**Source:** `frontend/lib/auth.ts:1-2`
```ts
/** Single source of truth for the admin session storage key. */
export const TOKEN_KEY = "nqu_admin_token";
```
**Apply to:** AdminLoginForm/login page, AdminGuard, LogoutButton, ExtractForm, all 401 handlers. Never introduce a new token key.

### Login API contract (unchanged)

**Source:** `frontend/lib/api.ts:167-186`
```ts
/**
 * Login admin via password + Cloudflare Turnstile token.
 * Returns JWT access_token stored in sessionStorage as "nqu_admin_token".
 */
export async function loginAdmin(password: string, cfToken: string): Promise<string> {
  const res = await fetch(`${API}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password, cf_token: cfToken }),
  });

  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }

  const body = (await res.json()) as { access_token?: string };
  if (!body.access_token) {
    throw new Error("Token não recebido");
  }
  return body.access_token;
}
```
**Apply to:** Dedicated admin login form/page only. Do not change backend contract or payload shape.

### Turnstile login widget (single-use token, remount-by-key)

**Source:** `frontend/app/admin/paste/ExtractForm.tsx:14-22,45-52,177-190`
```tsx
const TURNSTILE_SITE_KEY =
  process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ||
  (process.env.NODE_ENV === "production" ? "" : "1x00000000000000000000AA");
...
const resetTurnstile = () => {
  setCfToken(null);
  setTurnstileKey((k) => k + 1);
};
...
<Turnstile
  key={turnstileKey}
  siteKey={TURNSTILE_SITE_KEY}
  action="login"
  theme="dark"
  appearance="always"
  onVerify={(token) => setCfToken(token)}
  onExpire={() => setCfToken(null)}
  onError={() => setCfToken(null)}
/>
```
**Apply to:** AdminLoginForm. Preserve fail-closed missing key in production, dark theme, action `login`, and token reset on error/expire/consumed attempt.

### 401 expired-session hard redirect

**Source:** `frontend/app/admin/review/ReviewQueue.tsx:26-38`
```tsx
/** A 401 means the JWT expired: end the session instead of looping on retry. */
function handleAuthError(err: unknown): boolean {
  if (err instanceof ApiError && err.status === 401) {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // ignore storage errors
    }
    window.location.replace("/admin/paste");
    return true;
  }
  return false;
}
```
**Apply to:** `ReviewQueue.tsx`, `EditJobDialog.tsx`, `SocialPostsClient.tsx`, and any extraction 401 handling retained in `ExtractForm.tsx`. Change destination to `/admin/login`; add sanitized return-to where location is available.

### Admin visual theme tokens

**Source:** `frontend/app/admin/admin.css:9-26,38-42`
```css
@theme {
  --color-canvas: #0f0a1a;
  --color-surface: #1a1025;
  --color-line: #2a1f3d;
  --color-line-strong: #6d5a91;
  --color-fg: #e2e8f0;
  --color-fg-muted: #b8a9cc;
  --color-accent: #8b5cf6;
  --color-accent-soft: #a78bfa;
  --color-accent-strong: #7c3aed;
  --color-accent-strong-hover: #6d28d9;
  --color-danger: #f87171;
  --color-danger-soft: #fecaca;
  --color-donate: #facc15;
  --radius-card: 12px;
  --radius-dialog: 16px;
}
...
  :focus-visible {
    outline: 2px solid var(--color-accent-soft);
    outline-offset: 2px;
  }
```
**Apply to:** `/admin/login` UI and any new admin chrome component. Must align with existing admin dark/purple theme (D-12).

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| — | — | — | All phase-scoped files have close analogs in the existing frontend codebase. The only truly new behavior is safe `next` return-to sanitization; `frontend/lib/adminReturnTo.ts` can follow the small pure-utility pattern from `frontend/lib/chatFocus.ts` and be validated by Vitest. |

## Metadata

**Analog search scope:** `frontend/app/admin/**/*`, `frontend/components/admin/**/*`, `frontend/lib/**/*`, `frontend/app/(public)/privacidade/page.tsx`, `frontend/scripts/**/*`
**Files scanned:** ~35 (targeted glob/read/grep across admin routes, admin components, lib utils/tests, privacy page, SSR script)
**Pattern extraction date:** 2026-11-22
