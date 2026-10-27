"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { CITY_OPTIONS } from "@/lib/cities";
import { buildBoardHref, type Filters } from "@/lib/filters";
import { formatJobCount } from "@/lib/format";

interface BoardToolbarProps {
  filters: Filters;
  total: number;
}

const DEBOUNCE_MS = 300;

/**
 * Search, city filter, sort and live result count for the board (SRCH-01/02/03).
 *
 * All state lives in the URL: this component only writes the URL through
 * `router.replace` (no `push`, no history pollution) and the RSC re-renders
 * the list. Debounced typing + immediate commit on Enter/clear/chip change.
 */
export function BoardToolbar({ filters, total }: BoardToolbarProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const [value, setValue] = useState(filters.q);
  const lastCommittedRef = useRef(filters.q);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const commit = (patch: Partial<Filters>) => {
    const next = { ...filters, page: 1, vaga: null, ...patch };
    startTransition(() => {
      router.replace(buildBoardHref(next), { scroll: false });
    });
  };

  // Keep the input in sync with the server value without clobbering mid-typing.
  useEffect(() => {
    if (filters.q !== lastCommittedRef.current) {
      lastCommittedRef.current = filters.q;
      setValue(filters.q);
    }
  }, [filters.q]);

  // Debounced commit while typing.
  useEffect(() => {
    if (value.trim() === filters.q) {
      return;
    }
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = setTimeout(() => {
      commit({ q: value.trim() });
      lastCommittedRef.current = value.trim();
    }, DEBOUNCE_MS);
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      commit({ q: value.trim() });
      lastCommittedRef.current = value.trim();
    } else if (event.key === "Escape") {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      setValue("");
      commit({ q: "" });
      lastCommittedRef.current = "";
    }
  };

  const handleClear = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    setValue("");
    commit({ q: "" });
    lastCommittedRef.current = "";
  };

  return (
    <div
      className="sticky top-16 z-10 -mx-4 border-b border-line bg-canvas px-4 py-3 sm:mx-0 sm:px-0"
      aria-busy={isPending}
    >
      <form role="search" className="flex items-center gap-2">
        <div className="relative flex-1">
          <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-fg-muted"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            type="text"
            inputMode="search"
            enterKeyHint="search"
            autoComplete="off"
            maxLength={80}
            aria-label="Buscar vagas"
            placeholder="Busque por cargo, empresa ou palavra-chave"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={handleKeyDown}
            className="h-12 w-full rounded-lg border border-line-strong bg-canvas pl-10 pr-12 text-base text-fg placeholder:text-fg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
          />
          {value !== "" ? (
            <button
              type="button"
              aria-label="Limpar busca"
              onClick={handleClear}
              className="absolute right-1 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-md text-fg-muted transition-colors hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </button>
          ) : null}
        </div>
      </form>

      <div
        role="group"
        aria-label="Filtrar por cidade"
        className="-mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] sm:mx-0 sm:flex-wrap sm:overflow-visible"
      >
        <button
          type="button"
          aria-pressed={filters.city === null}
          onClick={() => commit({ city: null })}
          className={
            filters.city === null
              ? "min-h-11 shrink-0 rounded-full bg-accent-strong px-4 text-sm font-semibold text-white"
              : "min-h-11 shrink-0 rounded-full border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft"
          }
        >
          Todas
        </button>
        {CITY_OPTIONS.map((option) => {
          const active = filters.city === option.slug;
          return (
            <button
              key={option.slug}
              type="button"
              aria-pressed={active}
              onClick={() => commit({ city: option.slug })}
              className={
                active
                  ? "min-h-11 shrink-0 rounded-full bg-accent-strong px-4 text-sm font-semibold text-white"
                  : "min-h-11 shrink-0 rounded-full border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft"
              }
            >
              {option.label}
            </button>
          );
        })}
      </div>

      <div className="mt-3 flex items-center justify-between gap-3">
        {total > 0 ? (
          <p
            aria-live="polite"
            role="status"
            className="text-sm text-fg-muted"
          >
            {formatJobCount(total)}
          </p>
        ) : (
          <span />
        )}
        <label className="sr-only" htmlFor="board-sort">
          Ordenar por
        </label>
        <select
          id="board-sort"
          aria-label="Ordenar por"
          value={filters.sort}
          onChange={(event) =>
            commit({ sort: event.target.value as Filters["sort"] })
          }
          className="h-11 w-40 rounded-lg border border-line-strong bg-canvas px-3 text-sm text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
        >
          <option value="recentes">Mais recentes</option>
          <option value="antigas">Mais antigas</option>
        </select>
      </div>
    </div>
  );
}
