"use client";

import { useState } from "react";

import type { JobPublic } from "@/lib/api";
import { cityLabel } from "@/lib/cities";
import { formatDateBR } from "@/lib/format";

import { MapPin } from "./icons";

interface JobCardProps {
  job: JobPublic;
  onOpen: (job: JobPublic, trigger: HTMLElement | null) => void;
}

const COLLAPSE_THRESHOLD = 160;

/**
 * Board card (PUBL-02, UI-SPEC §A).
 *
 * The whole article is NOT clickable — only `Ver a vaga` opens the dialog, so
 * scrolling on mobile never opens it by accident. `Ver mais` expands the
 * activities preview in place (local state, resets when the grid remounts on a
 * filter change).
 */
export function JobCard({ job, onOpen }: JobCardProps) {
  const [expanded, setExpanded] = useState(false);

  const activities = job.activities?.trim() ? job.activities : null;
  const canExpand = Boolean(
    activities && activities.length > COLLAPSE_THRESHOLD,
  );
  const activitiesId = `activities-${job.id}`;
  const company = job.company?.trim() ? job.company : null;
  const salary = job.salary?.trim() ? job.salary : null;

  return (
    <article className="flex h-full flex-col gap-3 rounded-[12px] border border-line bg-surface p-4 transition-colors hover:border-accent focus-within:border-accent">
      {company ? (
        <p className="text-sm text-fg-muted [overflow-wrap:anywhere]">
          {company}
        </p>
      ) : null}

      <h2 className="line-clamp-2 text-xl font-semibold leading-tight [overflow-wrap:anywhere] [text-wrap:balance]">
        {job.title}
      </h2>

      {job.status === "published" ? (
        <span className="inline-flex w-fit items-center rounded-full border border-line-strong px-2 py-0.5 text-xs font-medium text-fg-muted">
          Vaga revisada
        </span>
      ) : null}

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-fg-muted">
        <span className="inline-flex items-center gap-1">
          <MapPin size={16} />
          {cityLabel(job.city)}
        </span>
        {salary ? (
          <span>
            Salário:{" "}
            <span className="font-semibold text-fg">{salary}</span>
          </span>
        ) : null}
      </div>

      {activities ? (
        <div className="flex flex-col gap-1">
          <p
            id={activitiesId}
            className={`text-base leading-relaxed [overflow-wrap:anywhere] ${
              expanded ? "" : "line-clamp-2 sm:line-clamp-3"
            }`}
          >
            {activities}
          </p>
          {canExpand ? (
            <button
              type="button"
              aria-expanded={expanded}
              aria-controls={activitiesId}
              onClick={() => setExpanded((value) => !value)}
              className="inline-flex min-h-11 items-center self-start text-sm font-semibold text-accent-soft hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
            >
              {expanded ? "Ver menos" : "Ver mais"}
            </button>
          ) : null}
        </div>
      ) : null}

      <p className="text-sm text-fg-muted">
        Publicada em {formatDateBR(job.created_at)}
      </p>

      <div className="mt-auto pt-1">
        <button
          type="button"
          onClick={(event) => onOpen(job, event.currentTarget)}
          aria-label={`Ver a vaga: ${job.title}`}
          className="inline-flex h-11 w-full items-center justify-center rounded-lg border border-line-strong text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
        >
          Ver a vaga
        </button>
      </div>
    </article>
  );
}
