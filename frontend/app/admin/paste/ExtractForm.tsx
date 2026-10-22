"use client";

import { useEffect, useState } from "react";
import { Turnstile } from "next-turnstile";
import { loginAdmin, extractJobs, type ExtractSummary } from "@/lib/api";
import "./globals-admin.css";

const TOKEN_KEY = "nqu_admin_token";

// The site key is a public value (the secret never reaches the browser).
// Outside production we fall back to Cloudflare's public always-pass test key
// so local dev works without a Cloudflare account. In production the env var
// is mandatory: without it the widget does not render and the login stays
// blocked — fail closed (D-15).
const TURNSTILE_SITE_KEY =
  process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ||
  (process.env.NODE_ENV === "production" ? "" : "1x00000000000000000000AA");

export default function ExtractForm() {
  const [token, setToken] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<ExtractSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cfToken, setCfToken] = useState<string | null>(null);
  const [turnstileKey, setTurnstileKey] = useState(0);

  useEffect(() => {
    try {
      const stored = window.sessionStorage.getItem(TOKEN_KEY);
      if (stored) {
        setToken(stored);
      }
    } catch {
      // ignore storage errors
    }
  }, []);

  // next-turnstile has no reset API: the widget is remounted with a new React
  // key, which removes the old widget and renders a fresh one — the consumed
  // token is never sent twice (D-19/T-03-18).
  const resetTurnstile = () => {
    setCfToken(null);
    setTurnstileKey((k) => k + 1);
  };

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

  const handleSubmit = async () => {
    if (!token || !text.trim()) return;
    setError(null);
    setSummary(null);
    setLoading(true);
    try {
      const res = await extractJobs(token, text);
      setSummary(res);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao extrair";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSummary(null);
    setText("");
    setError(null);
  };

  const isLoginDisabled = loading || !password.trim() || !cfToken;
  const isSubmitDisabled = loading || !token || !text.trim();

  return (
    <div className="admin-page">
      <main className="admin-panel">
        {!token && (
          <div>
            <h2>Login</h2>
            <label>
              Senha do admin
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </label>
            {TURNSTILE_SITE_KEY ? (
              <div className="admin-turnstile">
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
              <div className="admin-error">
                Configuração ausente: defina NEXT_PUBLIC_TURNSTILE_SITE_KEY
              </div>
            )}
            <button className="admin-btn" onClick={handleLogin} disabled={isLoginDisabled}>
              {loading ? "Entrando..." : "Entrar"}
            </button>

            {error && <div className="admin-error">{error}</div>}
          </div>
        )}

        {token && (
          <div>
            <h2>Extrair vagas</h2>
            <label>
              Texto bruto
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={8}
                minLength={1}
                placeholder="Cole aqui o texto com uma ou mais vagas..."
                disabled={loading}
              />
            </label>
            <button className="admin-btn" onClick={handleSubmit} disabled={isSubmitDisabled}>
              {loading ? "Extraindo... isso pode levar até ~2 minutos para textos grandes" : "Extrair vagas"}
            </button>

            {error && <div className="admin-error">{error}</div>}

            {summary && (
              <div>
                <h3>Resumo</h3>
                <div>
                  <span className="badge">
                    salvas em revisão pendente: {summary.saved_pending}
                  </span>
                  <span className="badge">
                    needs_review: {summary.saved_needs_review}
                  </span>
                </div>

                {summary.alerts && summary.alerts.length > 0 && (
                  <ul className="admin-alert">
                    {summary.alerts.map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                )}

                {summary.discarded && summary.discarded.length > 0 && (
                  <div>
                    <h4>Descartadas</h4>
                    {summary.discarded.map((d, i) => (
                      <details key={i} className="discard">
                        <summary>{d.reason}</summary>
                        <pre>{d.snippet}</pre>
                      </details>
                    ))}
                  </div>
                )}

                <button className="admin-btn" onClick={handleReset}>
                  Nova extração
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
