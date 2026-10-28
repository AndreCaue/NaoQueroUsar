"use client";

import { useState } from "react";

import type { JobAdmin } from "@/lib/api";
import { cityLabel } from "@/lib/cities";
import { formatDateBR } from "@/lib/format";

import { Check, Pencil, Spinner, Trash } from "./icons";

/**
 * ReviewRow — linha da fila de revisão admin (REVW-01).
 *
 * Card bg-surface, borda line, radius 12px, padding 16px.
 * Ações com texto: Aprovar (primário), Editar (secundário),
 * Excluir (destrutivo) — alvos de 44px.
 * Enquanto uma ação corre, a linha fica opaca e o botão acionado mostra
 * spinner + texto "Aprovando..."/"Excluindo...".
 */
export interface ReviewRowProps {
  job: JobAdmin;
  onApprove: () => Promise<void> | void;
  onEdit: () => void;
  onDelete: () => void;
  loading?: boolean;
}

type PendingAction = "approve" | "delete" | null;

const STATUS_LABELS: Record<JobAdmin["status"], string> = {
  pending: "Pendente",
  published: "Publicada",
  needs_review: "Necessita revisão",
  invalid: "Inválida",
};

const secondaryButton =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft disabled:opacity-50 disabled:cursor-not-allowed";

export function ReviewRow({
  job,
  onApprove,
  onEdit,
  onDelete,
  loading = false,
}: ReviewRowProps) {
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const busy = loading || pendingAction !== null;

  const handleApprove = async () => {
    if (busy) return;
    setPendingAction("approve");
    try {
      await onApprove();
    } finally {
      setPendingAction(null);
    }
  };

  const handleDelete = () => {
    if (busy) return;
    onDelete();
  };

  const statusLabel = STATUS_LABELS[job.status];

  return (
    <article
      className={`flex h-full flex-col gap-3 rounded-[12px] border border-line bg-surface p-4 transition-colors hover:border-accent focus-within:border-accent ${
        busy ? "pointer-events-none opacity-60" : ""
      }`}
      aria-busy={busy}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h2 className="min-w-0 text-[20px] font-semibold leading-tight [overflow-wrap:anywhere] [text-wrap:balance]">
          {job.title}
        </h2>
        <span className="shrink-0 rounded-full bg-[rgba(139,92,246,0.12)] px-3 py-1 text-[14px] text-accent-soft">
          {statusLabel}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-fg-muted">
        {job.company ? <p className="line-clamp-1">{job.company}</p> : null}
        <span className="inline-flex items-center gap-1">
          <svg
            aria-hidden="true"
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.75}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
            <circle cx="12" cy="10" r="2.5" />
          </svg>
          {job.city ? cityLabel(job.city) : "—"}
        </span>
      </div>

      <p className="text-[14px] text-fg-muted">
        Criada em {formatDateBR(job.created_at)}
      </p>

      {job.salary ? (
        <p className="text-sm text-fg-muted">
          Salário: <span className="font-semibold text-fg">{job.salary}</span>
        </p>
      ) : null}

      <div className="mt-auto flex flex-wrap gap-2 pt-1">
        <button
          type="button"
          onClick={handleApprove}
          disabled={busy}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {pendingAction === "approve" ? (
            <Spinner size={16} />
          ) : (
            <Check size={16} />
          )}
          {pendingAction === "approve" ? "Aprovando..." : "Aprovar"}
        </button>

        <button
          type="button"
          onClick={onEdit}
          disabled={busy}
          className={secondaryButton}
        >
          <Pencil size={16} />
          Editar
        </button>

        <button
          type="button"
          onClick={handleDelete}
          disabled={busy}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-danger px-4 text-sm text-danger transition-colors hover:bg-[rgba(248,113,113,0.12)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Trash size={16} />
          Excluir
        </button>
      </div>
    </article>
  );
}

export default ReviewRow;
