"use client";

import type { JobPublic } from "@/lib/api";
import { cityLabel } from "@/lib/cities";

interface ChatResultItemProps {
  job: JobPublic;
  onOpen: (job: JobPublic, trigger?: HTMLElement | null) => void;
}

export function ChatResultItem({ job, onOpen }: ChatResultItemProps) {
  const company = job.company?.trim() || null;
  const salary = job.salary?.trim() || null;

  return (
    <button
      type="button"
      onClick={(e) => onOpen(job, e.currentTarget)}
      className="w-full rounded-lg border border-line bg-surface p-3 text-left transition-colors hover:border-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
    >
      <div className="flex min-h-11 flex-col gap-1">
        <p className="text-base font-semibold text-fg [overflow-wrap:anywhere]">
          {job.title}
        </p>
        {company ? (
          <p className="text-sm text-fg-muted [overflow-wrap:anywhere]">{company}</p>
        ) : null}
        <p className="text-sm text-fg-muted">
          Local: {cityLabel(job.city)}
        </p>
        {salary ? (
          <p className="text-sm text-fg-muted">Salário: {salary}</p>
        ) : null}
        <span className="mt-1 inline-flex text-sm font-semibold text-accent-soft">
          Ver detalhes
        </span>
      </div>
    </button>
  );
}
