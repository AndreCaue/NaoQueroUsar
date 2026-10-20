"use client";

import { useEffect, useState } from "react";
import { loginAdmin, extractJobs, type ExtractSummary } from "@/lib/api";
import "./globals-admin.css";

const TOKEN_KEY = "nqu_admin_token";

export default function ExtractForm() {
  const [token, setToken] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<ExtractSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  const handleLogin = async () => {
    setError(null);
    setSummary(null);
    setLoading(true);
    try {
      const t = await loginAdmin(password);
      setToken(t);
      try {
        window.sessionStorage.setItem(TOKEN_KEY, t);
      } catch {
        // ignore storage errors
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao autenticar";
      setError(msg);
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

  const isLoginDisabled = loading || !password.trim();
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
            <button className="admin-btn" onClick={handleLogin} disabled={isLoginDisabled}>
              {loading ? "Entrando..." : "Entrar"}
            </button>
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
