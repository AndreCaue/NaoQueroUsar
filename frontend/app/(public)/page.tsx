import Link from "next/link";

import { JobGrid } from "@/components/board/JobGrid";
import { Pagination } from "@/components/board/Pagination";
import type { JobPublic } from "@/lib/api";
import {
  buildBoardHref,
  hasActiveFilters,
  PAGE_SIZE,
  normalizeFilters,
} from "@/lib/filters";
import { formatJobCount } from "@/lib/format";
import { fetchBoard } from "@/lib/jobs";

type BoardSearchParams = Promise<
  Record<string, string | string[] | undefined>
>;

const SECONDARY_BUTTON =
  "inline-flex h-11 items-center justify-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft";

/**
 * Public board (PUBL-01/PUBL-02, D-07/D-08).
 *
 * Server-rendered from `searchParams`: the initial HTML already carries the
 * jobs (SEO, no client fetch waterfall). `cache: "no-store"` lives in
 * `lib/jobs.ts` so the route is never frozen at build time (Pitfall 5).
 * A failed/timed-out fetch is a `BoardError` that bubbles to `error.tsx`.
 */
export default async function Page({
  searchParams,
}: {
  searchParams: BoardSearchParams;
}) {
  const sp = await searchParams;
  const filters = normalizeFilters(sp);
  const data = await fetchBoard(filters);

  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
  const filtersActive = hasActiveFilters(filters);

  // Deep link: only when the id is on the current page in this plan; 04-04 adds
  // the server-side `GET /jobs/{id}` fallback for ids outside the filter.
  const initialJob: JobPublic | null = filters.vaga
    ? (data.items.find((job) => job.id === filters.vaga) ?? null)
    : null;

  const prevHref =
    filters.page > 1
      ? buildBoardHref({ ...filters, page: filters.page - 1, vaga: null })
      : null;
  const nextHref =
    filters.page < totalPages
      ? buildBoardHref({ ...filters, page: filters.page + 1, vaga: null })
      : null;

  return (
    <div id="vagas" className="pt-8">
      <h1 className="text-[28px] font-semibold leading-tight [text-wrap:balance]">
        Vagas abertas
      </h1>
      <p className="mt-2 text-base text-fg-muted">
        Sem cadastro, sem login. Encontre e candidate-se.
      </p>

      <div className="mt-6">
        {data.total > 0 ? (
          <p role="status" aria-live="polite" className="text-sm text-fg-muted">
            {formatJobCount(data.total)}
          </p>
        ) : null}

        {data.items.length > 0 ? (
          <>
            <div className="mt-4">
              <JobGrid
                key={buildBoardHref(filters)}
                jobs={data.items}
                initialJob={initialJob}
                initialVaga={filters.vaga}
              />
            </div>
            <Pagination
              page={filters.page}
              totalPages={totalPages}
              prevHref={prevHref}
              nextHref={nextHref}
            />
          </>
        ) : data.total === 0 ? (
          <div className="mt-4 rounded-[12px] border border-line bg-surface p-8 text-center">
            {filtersActive ? (
              <>
                <h2 className="text-xl font-semibold text-fg">
                  Nenhuma vaga encontrada
                </h2>
                <p className="mt-2 text-base text-fg-muted">
                  Tente outra palavra-chave ou remova os filtros.
                </p>
                <Link href="/" className={`mt-6 ${SECONDARY_BUTTON}`}>
                  Limpar filtros
                </Link>
              </>
            ) : (
              <>
                <h2 className="text-xl font-semibold text-fg">
                  Nenhuma vaga publicada ainda
                </h2>
                <p className="mt-2 text-base text-fg-muted">
                  Novas vagas aparecem aqui assim que forem revisadas. Volte em
                  breve.
                </p>
              </>
            )}
          </div>
        ) : (
          <div className="mt-4 rounded-[12px] border border-line bg-surface p-8 text-center">
            <h2 className="text-xl font-semibold text-fg">
              Nenhuma vaga nesta página
            </h2>
            <Link
              href={buildBoardHref({ ...filters, page: 1, vaga: null })}
              className={`mt-6 ${SECONDARY_BUTTON}`}
            >
              Voltar para a primeira página
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
