const SKELETON_CARDS = Array.from({ length: 6 }, (_, index) => index);

/**
 * Grid skeleton for the first RSC load (UI-SPEC §C) — same box model as the
 * real cards so nothing jumps when the jobs land. No spinner; `animate-pulse`
 * is disabled by `public.css` under `prefers-reduced-motion`.
 */
export default function Loading() {
  return (
    <div aria-busy="true" className="pt-8">
      <p className="sr-only">Carregando vagas</p>

      <div className="h-7 w-52 animate-pulse rounded bg-line" />
      <div className="mt-3 h-4 w-72 animate-pulse rounded bg-line" />

      <div className="mt-6 grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2 sm:gap-6 lg:grid-cols-2 xl:grid-cols-3">
        {SKELETON_CARDS.map((index) => (
          <div
            key={index}
            className="flex h-full flex-col gap-3 rounded-[12px] border border-line bg-surface p-4"
          >
            <div className="h-4 w-2/5 animate-pulse rounded bg-line" />
            <div className="h-6 w-3/5 animate-pulse rounded bg-line" />
            <div className="mt-1 h-4 w-1/2 animate-pulse rounded bg-line" />
            <div className="mt-1 h-3 w-full animate-pulse rounded bg-line" />
            <div className="h-3 w-4/5 animate-pulse rounded bg-line" />
            <div className="mt-auto h-11 w-full animate-pulse rounded-lg bg-line" />
          </div>
        ))}
      </div>
    </div>
  );
}
