import Link from "next/link";

import { AdSlot } from "@/components/board/AdSlot";
import { BoardToolbar } from "@/components/board/BoardToolbar";
import { JobGrid } from "@/components/board/JobGrid";
import { Pagination } from "@/components/board/Pagination";
import {
  buildBoardHref,
  hasActiveFilters,
  isUuid,
  PAGE_SIZE,
  normalizeFilters,
} from "@/lib/filters";
import { fetchBoard, fetchJob } from "@/lib/jobs";

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

  // D-10a/B-04: `normalizeFilters` is still the only parser, but the raw value
  // is validated at the fetch boundary so a malformed id can reach the
  // server-rendered not-found panel instead of being silently dropped.
  const rawVaga = filters.vaga?.trim() || null;
  const vaga = rawVaga && isUuid(rawVaga) ? rawVaga : null;
  const malformedVaga = Boolean(rawVaga && !vaga);

  // A valid id resolves in parallel with the list: a shared link must open the
  // job even when the current filter/page would not include it.
  const [data, initialJob] = vaga
    ? await Promise.all([fetchBoard(filters), fetchJob(vaga)])
    : [await fetchBoard(filters), null];

  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
  const filtersActive = hasActiveFilters(filters);

  const notFound = malformedVaga || Boolean(vaga && initialJob === null);

  const prevHref =
    filters.page > 1
      ? buildBoardHref({ ...filters, page: filters.page - 1, vaga: null })
      : null;
  const nextHref =
    filters.page < totalPages
      ? buildBoardHref({ ...filters, page: filters.page + 1, vaga: null })
      : null;

  return (
    <div className="pt-8">
      <AdSlot variant="header" />

      <div className="mt-6 lg:grid lg:grid-cols-[minmax(0,1fr)_300px] lg:gap-6 lg:items-start">
        <div id="vagas" className="min-w-0">
          <h1 className="text-[28px] font-semibold leading-tight [text-wrap:balance]">
            Vagas abertas
          </h1>
          <p className="mt-2 text-base text-fg-muted">
            Sem cadastro, sem login. Encontre e candidate-se.
          </p>

          <div className="mt-6">
            <BoardToolbar filters={filters} total={data.total} />

            {/* Server-rendered not-found panel (B-04): malformed and
            valid-but-missing ids both land here, and a plain board visit never
            does. It carries no reveal footer and no contact data. The board
            stays rendered underneath so the visitor still has jobs. */}
        {notFound ? (
          <section
            role="status"
            className="mt-4 rounded-[16px] border border-line bg-surface p-6 text-center"
          >
            <h2 className="text-xl font-semibold text-fg">
              Vaga não encontrada
            </h2>
            <p className="mt-2 text-base text-fg-muted">
              Esta vaga não está mais disponível ou o link está incorreto.
            </p>
            <Link href="/" className={`mt-6 ${SECONDARY_BUTTON}`}>
              Limpar filtros
            </Link>
          </section>
        ) : null}

        {data.items.length > 0 ? (
          <>
            <div className="mt-4">
              <JobGrid
                key={[filters.q, filters.city, filters.sort, filters.page].join("|")}
                jobs={data.items}
                initialJob={initialJob}
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
        <aside className="hidden lg:block">
          <AdSlot variant="sidebar" />
        </aside>
      </div>
    </div>
  );
}
