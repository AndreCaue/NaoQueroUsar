"use client";

import { CITY_OPTIONS, type CitySlug } from "@/lib/cities";

const chipBase =
  "min-h-11 shrink-0 rounded-full px-4 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent-soft)]";
const chipActive = "bg-accent-strong font-semibold text-white";
const chipIdle =
  "border border-line-strong text-fg hover:border-accent hover:text-accent-soft";

/**
 * City filter chips for admin review queue (REVW-01).
 * Single-select: "Todas" + CITY_OPTIONS. Slugs are sent to the admin API,
 * which resolves slug/canonical/label server-side.
 */
export function CityChips({
  selected,
  onChange,
}: {
  selected: CitySlug | null;
  onChange: (slug: CitySlug | null) => void;
}) {
  return (
    <div
      role="group"
      aria-label="Filtrar por cidade"
      className="-mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] sm:mx-0 sm:flex-wrap sm:overflow-visible"
    >
      <button
        type="button"
        aria-pressed={selected === null}
        onClick={() => onChange(null)}
        className={`${chipBase} ${selected === null ? chipActive : chipIdle}`}
      >
        Todas
      </button>
      {CITY_OPTIONS.map((option) => {
        const active = selected === option.slug;
        return (
          <button
            key={option.slug}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(option.slug)}
            className={`${chipBase} ${active ? chipActive : chipIdle}`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
