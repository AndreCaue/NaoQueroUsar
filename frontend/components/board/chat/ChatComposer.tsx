"use client";

import { useState } from "react";

const EXAMPLES = [
  "Dev pleno em São Paulo",
  "Frontend React remoto",
  "Estágio em marketing digital em SP",
  "Analista de dados em BH ou remoto",
] as const;

interface ChatComposerProps {
  draft: string;
  isSending: boolean;
  showExamples: boolean;
  onDraftChange: (value: string) => void;
  onSend: (message: string) => void;
}

export function ChatComposer({
  draft,
  isSending,
  showExamples,
  onDraftChange,
  onSend,
}: ChatComposerProps) {
  const [localHint, setLocalHint] = useState<string | null>(null);

  const submit = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isSending) return;
    if (trimmed.length > 400) {
      setLocalHint("Mensagem muito longa. Use até 400 caracteres.");
      return;
    }
    setLocalHint(null);
    onSend(trimmed);
  };

  return (
    <div className="border-t border-line bg-surface p-3 sm:p-4">
      {showExamples ? (
        <div className="mb-3">
          <p className="mb-2 text-sm text-fg-muted">Exemplos rápidos:</p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((example) => (
              <button
                key={example}
                type="button"
                disabled={isSending}
                onClick={() => {
                  onDraftChange(example);
                  submit(example);
                }}
                className="inline-flex min-h-11 items-center rounded-full border border-line-strong px-3 py-1 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <label htmlFor="chat-message" className="sr-only">
        Mensagem
      </label>
      <div className="flex items-end gap-2">
        <textarea
          id="chat-message"
          rows={2}
          value={draft}
          disabled={isSending}
          onChange={(e) => {
            setLocalHint(null);
            onDraftChange(e.target.value);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit(draft);
            }
          }}
          placeholder="Descreva a vaga que você procura (ex.: cargo, cidade, remoto)..."
          className="min-h-[44px] w-full resize-none rounded-lg border border-line-strong bg-canvas px-3 py-2 text-base text-fg placeholder:text-fg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-60"
        />
        <button
          type="button"
          onClick={() => submit(draft)}
          disabled={isSending || draft.trim().length === 0}
          className="inline-flex h-11 min-h-11 shrink-0 items-center justify-center rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
        >
          Enviar mensagem
        </button>
      </div>
      {localHint ? (
        <p className="mt-2 text-sm text-danger">{localHint}</p>
      ) : null}
    </div>
  );
}
