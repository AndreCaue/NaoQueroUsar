"use client";

import { useEffect } from "react";

/**
 * Board error boundary (UI-SPEC §C). Rendered inside the public shell, so the
 * header/footer survive a failed fetch.
 *
 * `fetchBoard` throws `BoardError` with `message` equal to the kind
 * (`"timeout" | "http" | "network"`); Next may forward that message as-is in
 * dev and replace it with a digest in production, so the timeout check also
 * accepts any message that mentions a timeout.
 */
export default function PublicError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  const isTimeout =
    error.message === "timeout" || /timeout/i.test(error.message);

  const title = isTimeout
    ? "O servidor está acordando."
    : "Não foi possível carregar as vagas.";
  const body = isTimeout
    ? "Tente novamente em alguns instantes."
    : "Verifique sua conexão e tente novamente.";

  return (
    <div className="pt-8">
      <div
        role="alert"
        className="rounded-[12px] border border-danger bg-[rgba(248,113,113,0.10)] p-8 text-center"
      >
        <h2 className="text-xl font-semibold text-danger-soft">{title}</h2>
        <p className="mt-2 text-base text-danger-soft">{body}</p>
        <button
          type="button"
          onClick={reset}
          className="mt-6 inline-flex h-11 items-center justify-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
        >
          Tentar novamente
        </button>
      </div>
    </div>
  );
}
