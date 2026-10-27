"use client";

import { useRef, useState } from "react";

import type { JobPublic } from "@/lib/api";

import { JobCard } from "./JobCard";
import { JobDetailDialog } from "./JobDetailDialog";

interface JobGridProps {
  jobs: JobPublic[];
  initialJob?: JobPublic | null;
  /** Reserved for the `?vaga=` not-found flow that lands in 04-04. */
  initialVaga?: string | null;
}

/**
 * Client grid: owns the selected job for the single detail dialog and the
 * trigger element used to restore focus on close. Data itself arrives
 * serialized from the RSC — no client-side list fetching (D-07).
 */
export function JobGrid({ jobs, initialJob }: JobGridProps) {
  const [selected, setSelected] = useState<JobPublic | null>(
    initialJob ?? null,
  );
  const triggerRef = useRef<HTMLElement | null>(null);

  const handleOpen = (job: JobPublic, trigger: HTMLElement | null) => {
    triggerRef.current = trigger;
    setSelected(job);
  };

  const handleClose = () => {
    setSelected(null);
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
