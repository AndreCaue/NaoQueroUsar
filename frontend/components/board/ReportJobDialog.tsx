"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { ApiError, reportJob } from "@/lib/api";

import { X } from "./icons";

interface ReportJobDialogProps {
  jobId: string;
  open: boolean;
  onClose: () => void;
}

type Phase = "idle" | "submitting" | "success" | "error";

const MAX_REASON = 500;

const DESCRIPTION =
  "Se você acredita que esta vaga é suspeita ou tem informações incorretas, envie um reporte. Não é necessário identificar-se.";
const SUCCESS_COPY = "Reporte enviado. Obrigado pela colaboração.";
const ERROR_COPY =
  "Não foi possível enviar o reporte. Tente novamente.";
const RATE_LIMIT_COPY =
  "Muitas tentativas. Aguarde alguns segundos e tente novamente.";

const PRIMARY_BUTTON =
  "inline-flex h-12 w-full items-center justify-center rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50";
const GHOST_BUTTON =
  "inline-flex h-11 items-center justify-center rounded-lg px-4 text-sm font-semibold text-fg-muted transition-colors hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft";

/**
 * Anonymous report dialog (TRST-02, UI-SPEC §B).
 *
 * Opens as a second native `<dialog>` on top of the job detail — focus trap,
 * ESC and backdrop come for free, and ESC closes this dialog without closing
 * the detail underneath (top-layer order). The reason is optional and never
 * leaves the browser except as the POST body; the backend only logs it.
 * State machine: `idle → submitting → success | error` (`error` offers
 * "Tentar novamente", which returns to `idle`).
 */
export function ReportJobDialog({
  jobId,
  open,
  onClose,
}: ReportJobDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = `report-dialog-title-${jobId}`;
  const [phase, setPhase] = useState<Phase>("idle");
  const [reason, setReason] = useState("");
  const [errorCopy, setErrorCopy] = useState(ERROR_COPY);

  const close = () => dialogRef.current?.close();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    if (open && !dialog.open) {
      dialog.showModal();
      dialog.focus();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  // Reopening always starts from a clean form: feedback from the previous
  // attempt is not carried into a new report.
  useEffect(() => {
    if (!open) {
      setPhase("idle");
      setReason("");
      setErrorCopy(ERROR_COPY);
    }
  }, [open]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (phase === "submitting" || phase === "success") {
      return;
    }
    setPhase("submitting");
    try {
      const trimmed = reason.trim();
      await reportJob(jobId, trimmed ? trimmed : undefined);
      setPhase("success");
    } catch (error) {
      setErrorCopy(
        error instanceof ApiError && error.status === 429
          ? RATE_LIMIT_COPY
          : ERROR_COPY,
      );
      setPhase("error");
    }
  }

  return (
    <dialog
      ref={dialogRef}
      tabIndex={-1}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) {
          dialogRef.current?.close();
        }
      }}
      className="mb-0 mt-auto max-h-[92dvh] w-full max-w-none flex-col overflow-hidden rounded-t-[16px] border-0 bg-surface p-0 pb-[env(safe-area-inset-bottom)] text-fg backdrop:bg-[rgba(5,2,12,.72)] open:flex sm:mb-auto sm:mt-auto sm:max-h-[88dvh] sm:max-w-[480px] sm:rounded-[16px]"
    >
      <header className="flex shrink-0 items-start justify-between gap-4 border-b border-line px-4 pb-3 pt-4 sm:px-6">
        <h2
          id={titleId}
          className="text-xl font-semibold leading-tight [text-wrap:balance]"
        >
          Reportar esta vaga
        </h2>
        <button
          type="button"
          aria-label="Fechar"
          onClick={close}
          className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-fg-muted transition-colors hover:bg-[rgba(167,139,250,0.08)] hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
        >
          <X size={20} />
        </button>
      </header>

      {phase === "success" ? (
        <div className="flex flex-col gap-4 px-4 py-6 sm:px-6">
          <p
            role="status"
            className="rounded-lg border border-line-strong bg-surface p-4 text-base leading-relaxed text-fg"
          >
            {SUCCESS_COPY}
          </p>
          <button type="button" onClick={close} className={PRIMARY_BUTTON}>
            Fechar
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col">
          <div className="flex flex-col gap-4 overflow-y-auto px-4 py-4 sm:px-6">
            <p className="text-sm leading-relaxed text-fg-muted [overflow-wrap:anywhere]">
              {DESCRIPTION}
            </p>

            <div className="flex flex-col gap-1">
              <label
                htmlFor={`report-reason-${jobId}`}
                className="text-sm font-medium text-fg"
              >
                Motivo (opcional)
              </label>
              <textarea
                id={`report-reason-${jobId}`}
                name="reason"
                rows={4}
                maxLength={MAX_REASON}
                value={reason}
                disabled={phase === "submitting"}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Descreva brevemente o motivo..."
                className="w-full resize-none rounded-lg border border-line-strong bg-transparent p-3 text-base leading-relaxed text-fg placeholder:text-fg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:opacity-50"
              />
              <p className="self-end text-xs text-fg-muted">
                {reason.length}/{MAX_REASON}
              </p>
            </div>

            {phase === "error" ? (
              <p
                role="alert"
                className="rounded-lg border border-danger bg-[rgba(248,113,113,0.10)] p-3 text-sm leading-relaxed text-danger-soft [overflow-wrap:anywhere]"
              >
                {errorCopy}
              </p>
            ) : null}
          </div>

          <footer className="flex shrink-0 flex-col gap-2 border-t border-line p-4 sm:flex-row sm:items-center sm:justify-end">
            {phase === "error" ? (
              <button
                type="button"
                onClick={() => setPhase("idle")}
                className={GHOST_BUTTON}
              >
                Tentar novamente
              </button>
            ) : (
              <button
                type="button"
                onClick={close}
                disabled={phase === "submitting"}
                className={GHOST_BUTTON}
              >
                Cancelar
              </button>
            )}
            <button
              type="submit"
              disabled={phase === "submitting"}
              className={`${PRIMARY_BUTTON} sm:w-auto sm:min-w-44`}
            >
              {phase === "submitting" ? "Enviando..." : "Enviar reporte"}
            </button>
          </footer>
        </form>
      )}
    </dialog>
  );
}
