"use client";

import { useRef, useState } from "react";

import type { JobPublic } from "@/lib/api";

import { JobCard } from "./JobCard";
import { JobDetailDialog } from "./JobDetailDialog";

interface JobGridProps {
  jobs: JobPublic[];
  initialJob?: JobPublic | null;
}

/**
 * Write/remove `?vaga=` without an RSC round-trip (D-09).
 *
 * `history.replaceState` keeps `q`/`city`/`sort`/`page` intact so a copied URL
 * is still the filtered board plus the open job; closing removes only `vaga`
 * and falls back to `/` when nothing else is left.
 */
function syncVagaParam(jobId: string | null): void {
  const params = new URLSearchParams(window.location.search);
  if (jobId) {
    params.set("vaga", jobId);
  } else {
    params.delete("vaga");
  }
  const query = params.toString();
  const path = window.location.pathname || "/";
  window.history.replaceState(null, "", query ? `${path}?${query}` : path);
}

/**
 * Client grid: owns the selected job for the single detail dialog and the
 * trigger element used to restore focus on close. Data itself arrives
 * serialized from the RSC — no client-side list fetching (D-07).
 *
 * The dialog is seeded from `initialJob` in the `useState` initializer (not a
 * mount effect), so a `?vaga=` deep link ships its dialog markup in the SSR
 * HTML and is open on first paint.
 */
export function JobGrid({ jobs, initialJob }: JobGridProps) {
  const [selected, setSelected] = useState<JobPublic | null>(
    initialJob ?? null,
  );
  const triggerRef = useRef<HTMLElement | null>(null);

  const handleOpen = (job: JobPublic, trigger: HTMLElement | null) => {
    triggerRef.current = trigger;
    setSelected(job);
    syncVagaParam(job.id);
  };

  const handleClose = () => {
    setSelected(null);
    syncVagaParam(null);
    const trigger = triggerRef.current;
    // Wait for the dialog to be removed before returning focus so the card
    // does not fight the browser's own focus restoration.
    window.requestAnimationFrame(() => trigger?.focus());
  };

  return (
    <>
      <ul className="grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2 sm:gap-6 lg:grid-cols-2 xl:grid-cols-3">
        {jobs.map((job) => (
          <li key={job.id} className="h-full">
            <JobCard job={job} onOpen={handleOpen} />
          </li>
        ))}
      </ul>
      {selected ? (
        <JobDetailDialog job={selected} open onClose={handleClose} />
      ) : null}
    </>
  );
}
