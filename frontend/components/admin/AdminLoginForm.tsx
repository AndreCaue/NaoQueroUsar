"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Turnstile } from "next-turnstile";
import { useEffect, useState } from "react";

import { sanitizeAdminReturnTo } from "@/lib/adminReturnTo";
import { ApiError, loginAdmin } from "@/lib/api";
import { TOKEN_KEY } from "@/lib/auth";

const TURNSTILE_SITE_KEY =
  process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ||
  (process.env.NODE_ENV === "production" ? "" : "1x00000000000000000000AA");

export function AdminLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cfToken, setCfToken] = useState<string | null>(null);
  const [turnstileKey, setTurnstileKey] = useState(0);
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(TOKEN_KEY);
      if (stored) {
        router.replace(sanitizeAdminReturnTo(searchParams.get("next")) ?? "/admin");
        return;
      }
    } catch {
      // ignore storage errors
    }
    setCheckingSession(false);
  }, [router, searchParams]);

  const resetTurnstile = () => {
    setCfToken(null);
    setTurnstileKey((k) => k + 1);
  };

  const handleLogin = async () => {
    if (!cfToken) return;
    setError(null);
    setLoading(true);
    try {
      const t = await loginAdmin(password, cfToken);
      sessionStorage.setItem(TOKEN_KEY, t);
      router.replace(sanitizeAdminReturnTo(searchParams.get("next")) ?? "/admin");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Não foi possível entrar. Verifique a senha e tente novamente.");
      }
      resetTurnstile();
    } finally {
      setLoading(false);
    }
  };

  if (checkingSession) {
    return <p className="text-fg-muted">Carregando...</p>;
  }

  return (
    <div className="mx-auto w-full max-w-[420px]">
      <div className="rounded-lg border border-line bg-surface p-6">
        <h1 className="text-xl font-semibold">Acesso administrativo</h1>
        <p className="mt-2 text-sm text-fg-muted">Entre com a senha de administrador.</p>

        <div className="mt-6 space-y-4">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-fg">Senha do admin</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Digite sua senha"
              disabled={loading}
              className="h-12 w-full rounded-lg border border-line-strong bg-canvas px-3 text-base text-fg placeholder:text-fg-muted"
              autoComplete="current-password"
            />
          </label>

          {TURNSTILE_SITE_KEY ? (
            <div className="max-w-full overflow-hidden">
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
            <div className="rounded-lg border border-danger bg-[rgba(248,113,113,0.1)] p-3 text-danger-soft">
              Configuração ausente: defina NEXT_PUBLIC_TURNSTILE_SITE_KEY
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="rounded-lg border border-danger bg-[rgba(248,113,113,0.1)] p-3 text-danger-soft"
            >
              {error}
            </div>
          )}

          <button
            type="button"
            onClick={handleLogin}
            disabled={loading || !password.trim() || !cfToken}
            className="min-h-11 w-full rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white hover:bg-accent-strong-hover disabled:opacity-50"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>

          <div className="pt-2">
            <Link href="/" className="text-sm text-fg-muted hover:text-fg">
              Voltar ao site
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
