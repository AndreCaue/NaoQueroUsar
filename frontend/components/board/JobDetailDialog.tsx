"use client";

import { useEffect, useRef } from "react";

import type { JobPublic } from "@/lib/api";
import { cityLabel } from "@/lib/cities";
import { formatDateBR } from "@/lib/format";

import { X } from "./icons";
import { RevealContact } from "./RevealContact";

interface JobDetailDialogProps {
  job: JobPublic;
  open: boolean;
  onClose: () => void;
}

function hasText(value: string | null): value is string {
  return Boolean(value && value.trim());
}

function DetailSection({ label, value }: { label: string; value: string }) {
  return (
    <section className="border-b border-line px-4 py-4 sm:px-6">
      <h3 className="text-sm font-normal text-fg-muted">{label}</h3>
      <p className="mt-1 whitespace-pre-wrap text-base leading-relaxed text-fg [overflow-wrap:anywhere]">
        {value}
      </p>
    </section>
  );
}

/**
 * Native `<dialog>` detail view (PUBL-03, UI-SPEC §D).
 *
 * `showModal()` gives focus trapping, ESC, `::backdrop` and an inert document
 * for free — no dialog dependency. Mobile is a bottom sheet, ≥640px a centred
 * 640px panel. Job text is rendered as JSX text nodes only: raw HTML injection
 * is never used (T-04-08), and the public payload has no contact field to leak
 * (T-04-09).
 */
export function JobDetailDialog({
  job,
  open,
  onClose,
}: JobDetailDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = `job-dialog-title-${job.id}`;
  // One close path for the X, ESC, backdrop and the reveal footer's 404 state.
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

  // Lock the document scroll while the modal is open, restoring the previous
  // inline value on close/unmount (UI-SPEC §D).
  useEffect(() => {
    if (!open) {
      return;
    }
    const root = document.documentElement;
    const previous = root.style.overflow;
    root.style.overflow = "hidden";
    return () => {
      root.style.overflow = previous;
    };
  }, [open]);

  const company = job.company?.trim() ? job.company : null;
  const city = cityLabel(job.city);
  const activities = hasText(job.activities) ? job.activities : null;
  const requirements = hasText(job.requirements) ? job.requirements : null;
  const benefits = hasText(job.benefits) ? job.benefits : null;
  const salary = hasText(job.salary) ? job.salary : null;

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
      className="mb-0 mt-auto max-h-[92dvh] w-full max-w-none flex-col overflow-hidden rounded-t-[16px] border-0 bg-surface p-0 pb-[env(safe-area-inset-bottom)] text-fg backdrop:bg-[rgba(5,2,12,.72)] open:flex sm:mb-auto sm:mt-auto sm:max-h-[88dvh] sm:max-w-[640px] sm:rounded-[16px]"
    >
      <header className="shrink-0 border-b border-line bg-surface px-4 pb-3 pt-2 sm:px-6 sm:pt-4">
        <div
          aria-hidden="true"
          className="mx-auto mb-2 h-1 w-8 rounded-full bg-line-strong sm:hidden"
        />
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2
              id={titleId}
              data-dialog-title
              className="text-xl font-semibold leading-tight [overflow-wrap:anywhere] [text-wrap:balance]"
            >
              {job.title}
            </h2>
            {company || city ? (
              <p className="mt-1 text-sm text-fg-muted [overflow-wrap:anywhere]">
                {[company, city].filter(Boolean).join(" · ")}
              </p>
            ) : null}
            {job.status === "published" ? (
              <span className="mt-2 inline-flex items-center rounded-full border border-line-strong px-2 py-0.5 text-xs font-medium text-fg-muted">
                Vaga revisada
              </span>
            ) : null}
          </div>
          <button
            type="button"
            aria-label="Fechar"
            onClick={close}
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-fg-muted transition-colors hover:bg-[rgba(167,139,250,0.08)] hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
          >
            <X size={20} />
          </button>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
        {activities ? (
          <DetailSection label="Atividades" value={activities} />
        ) : null}
        {requirements ? (
          <DetailSection label="Requisitos" value={requirements} />
        ) : null}
        {benefits ? (
          <DetailSection label="Benefícios" value={benefits} />
        ) : null}
        {salary ? <DetailSection label="Salário" value={salary} /> : null}
        <DetailSection label="Local" value={city} />

        <div className="flex flex-wrap gap-x-4 gap-y-1 px-4 py-4 text-sm text-fg-muted sm:px-6">
          <span>Publicada em {formatDateBR(job.created_at)}</span>
          <span>Encerra em {formatDateBR(job.expires_at)}</span>
        </div>
      </div>

      {/* Sticky footer: the reveal is the only filled CTA of the board
          (UI-SPEC §E). It never receives contact data from the list payload. */}
      <footer className="shrink-0 border-t border-line p-4">
        <RevealContact job={job} onClose={close} />
      </footer>
    </dialog>
  );
}
