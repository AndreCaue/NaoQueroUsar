import Link from "next/link";

interface PaginationProps {
  page: number;
  totalPages: number;
  prevHref: string | null;
  nextHref: string | null;
}

const BASE =
  "inline-flex h-11 min-w-11 items-center justify-center rounded-lg border px-4 text-sm font-semibold";
const ENABLED = "border-line-strong text-fg hover:border-accent hover:text-accent-soft";
const DISABLED = "border-line text-fg-muted opacity-50";

/**
 * Presentational pagination (RSC). Ends stay visible but non-interactive
 * (UI-SPEC §C) — targets are `<Link>`s so paging is a normal navigation and
 * scrolls to the results region.
 */
export function Pagination({
  page,
  totalPages,
  prevHref,
  nextHref,
}: PaginationProps) {
  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav
      aria-label="Paginação"
      className="mt-8 flex items-center justify-between gap-4"
    >
      {prevHref ? (
        <Link
          href={prevHref}
          aria-label="Página anterior"
          className={`${BASE} ${ENABLED}`}
        >
          Anterior
        </Link>
      ) : (
        <span aria-disabled="true" className={`${BASE} ${DISABLED}`}>
          Anterior
        </span>
      )}

      <span className="text-sm text-fg-muted">
        Página {page} de {totalPages}
      </span>

      {nextHref ? (
        <Link
          href={nextHref}
          aria-label="Próxima página"
          className={`${BASE} ${ENABLED}`}
        >
          Próxima
        </Link>
      ) : (
        <span aria-disabled="true" className={`${BASE} ${DISABLED}`}>
          Próxima
        </span>
      )}
    </nav>
  );
}
