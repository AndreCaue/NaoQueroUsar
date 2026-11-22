"use client";

import { useState, type ClipboardEvent } from "react";

import { useAdminGuard } from "@/components/admin/AdminGuard";
import {
  ApiError,
  extractJobs,
  type ExtractSummary,
} from "@/lib/api";
import { buildAdminLoginHref } from "@/lib/adminReturnTo";
import { TOKEN_KEY } from "@/lib/auth";
import { TERM_REMOVED_NOTICE, stripBlockedTerms } from "@/lib/blocklist";

export default function ExtractForm() {
  const token = useAdminGuard();
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<ExtractSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

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
      if (err instanceof ApiError && err.status === 401) {
        try {
          sessionStorage.removeItem(TOKEN_KEY);
        } catch {
          // ignore storage errors
        }
        window.location.replace(
          buildAdminLoginHref(
            `${window.location.pathname}${window.location.search}`,
          ),
        );
        return;
      }
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
    setNotice(null);
  };

  // Colar conteúdo com o termo não é recusado: o termo sai e o resto entra
  // no cursor. Sem o termo, o paste nativo segue intocado.
  const handlePaste = (e: ClipboardEvent<HTMLTextAreaElement>) => {
    const pasted = e.clipboardData.getData("text");
    const cleaned = stripBlockedTerms(pasted);
    if (cleaned === pasted) return;

    e.preventDefault();
    const el = e.currentTarget;
    const start = el.selectionStart ?? text.length;
    const end = el.selectionEnd ?? start;
    const next = text.slice(0, start) + cleaned + text.slice(end);
    setText(next);
    setNotice(TERM_REMOVED_NOTICE);
    const caret = start + cleaned.length;
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(caret, caret);
    });
  };

  const isSubmitDisabled = loading || !token || !stripBlockedTerms(text).trim();

  return (
    <div className="max-w-[720px] mx-auto p-6 bg-surface border border-line rounded-lg">
      <main className="space-y-8">
        <div>
          <h2 className="text-xl font-semibold">Extrair vagas</h2>
          <label>
            Texto bruto
            <textarea
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                if (notice) setNotice(null);
              }}
              onPaste={handlePaste}
              rows={8}
              minLength={1}
              placeholder="Cole aqui o texto com uma ou mais vagas..."
              disabled={loading}
              className="min-h-[96px] resize-y w-full rounded-lg border border-line-strong bg-canvas px-3 text-base text-fg placeholder:text-fg-muted"
            />
          </label>
          {notice && (
            <div
              role="status"
              className="rounded-lg border border-line-strong bg-canvas p-3 text-fg-muted"
            >
              {notice}
            </div>
          )}
          <button
            className="min-h-11 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white hover:bg-accent-strong-hover"
            onClick={handleSubmit}
            disabled={isSubmitDisabled}
          >
            {loading
              ? "Extraindo... isso pode levar até ~2 minutos para textos grandes"
              : "Extrair vagas"}
          </button>

          {error && (
            <div className="bg-[rgba(248,113,113,0.1)] border border-danger text-danger-soft rounded-lg p-3">
              {error}
            </div>
          )}

          {summary && (
            <div>
              <h3 className="text-xl font-semibold">Resumo</h3>
              <div>
                <span className="badge">
                  salvas em revisão pendente: {summary.saved_pending}
                </span>
                <span className="badge">
                  needs_review: {summary.saved_needs_review}
                </span>
              </div>

              {summary.alerts && summary.alerts.length > 0 && (
                <div className="bg-[rgba(248,113,113,0.1)] border border-danger text-danger-soft rounded-lg p-3">
                  <ul>
                    {summary.alerts.map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </div>
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

              <button
                className="min-h-11 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white hover:bg-accent-strong-hover"
                onClick={handleReset}
              >
                Nova extração
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
