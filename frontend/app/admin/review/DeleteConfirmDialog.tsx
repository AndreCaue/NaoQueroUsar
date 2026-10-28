"use client";

import { useEffect, useRef, useState } from "react";

import { Spinner, Trash } from "@/components/admin/icons";

export interface DeleteConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  loading?: boolean;
}

/**
 * DeleteConfirmDialog — confirmação de exclusão hard delete (REVW-04).
 *
 * `<dialog>` nativo, 480px, centralizado. Enquanto exclui, "Excluir vaga"
 * vira "Excluindo..." (disabled), Cancelar fica desabilitado e ESC/backdrop
 * não fecham.
 */
export function DeleteConfirmDialog({
  open,
  onClose,
  onConfirm,
  loading = false,
}: DeleteConfirmDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [deleting, setDeleting] = useState(false);
  const busy = loading || deleting;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      dialog.focus();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const root = document.documentElement;
    const previous = root.style.overflow;
    root.style.overflow = "hidden";
    return () => {
      root.style.overflow = previous;
    };
  }, [open]);

  const close = () => dialogRef.current?.close();

  const handleConfirm = async () => {
    if (busy) return;
    setDeleting(true);
    try {
      await onConfirm();
      close();
    } catch {
      // The caller surfaces the error via toast; keep the dialog open.
    } finally {
      setDeleting(false);
    }
  };

  return (
    <dialog
      ref={dialogRef}
      tabIndex={-1}
      aria-labelledby="delete-job-title"
      onClose={onClose}
      onCancel={(event) => {
        if (busy) event.preventDefault();
      }}
      onClick={(event) => {
        if (busy) return;
        if (event.target === dialogRef.current) close();
      }}
      className="mb-0 mt-auto w-full max-w-none rounded-t-[16px] border border-line bg-surface p-0 text-fg backdrop:bg-[rgba(5,2,12,.72)] open:block sm:mb-auto sm:mt-auto sm:max-w-[480px] sm:rounded-[16px]"
    >
      <div className="p-6">
        <h2
          id="delete-job-title"
          className="mb-3 text-[20px] font-semibold leading-tight"
        >
          Excluir esta vaga?
        </h2>
        <p className="mb-6 text-[14px] text-fg-muted">
          Esta ação é permanente. A vaga será removida do banco e não aparecerá
          mais no painel.
        </p>

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={close}
            disabled={busy}
            className="min-h-11 rounded-lg border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={busy}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-danger px-4 text-sm font-semibold text-danger transition-colors hover:bg-[rgba(248,113,113,0.12)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy ? <Spinner size={16} /> : <Trash size={16} />}
            {busy ? "Excluindo..." : "Excluir vaga"}
          </button>
        </div>
      </div>
    </dialog>
  );
}

export default DeleteConfirmDialog;
