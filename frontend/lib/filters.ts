import { CITY_OPTIONS } from "@/lib/cities";

/**
 * Board URL contract (SRCH-01/02/03, D-05/D-06).
 *
 * `q`, `city`, `sort`, `page` and `vaga` all live in the URL — never in
 * localStorage. This module is the ONLY place URL params are parsed, so the
 * whitelist/clamp rules have a single home.
 */
export const PAGE_SIZE = 24;

export type Sort = "recentes" | "antigas";

export interface Filters {
  q: string;
  city: string | null;
  sort: Sort;
  page: number;
  /** Raw `?vaga=` value, preserved even when malformed (B-04). */
  vaga: string | null;
}

type RawSearchParams = Record<string, string | string[] | undefined>;

const CITY_SLUGS = new Set<string>(CITY_OPTIONS.map((option) => option.slug));

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export function normalizeFilters(input: RawSearchParams): Filters {
  const rawQ = first(input.q)?.trim() ?? "";
  const rawCity = first(input.city)?.trim().toLowerCase() ?? "";
  const rawSort = first(input.sort)?.trim().toLowerCase() ?? "";
  const rawPage = Number.parseInt(first(input.page) ?? "", 10);
  const rawVaga = first(input.vaga)?.trim() ?? "";

  return {
    q: rawQ.slice(0, 80),
    city: CITY_SLUGS.has(rawCity) ? rawCity : null,
    sort: rawSort === "antigas" ? "antigas" : "recentes",
    page: Number.isFinite(rawPage) && rawPage >= 1 ? rawPage : 1,
    // Deliberately NOT validated here: the page's fetch boundary decides what
    // a malformed id means, so the server-rendered not-found panel stays
    // reachable instead of the parser silently dropping the param.
    vaga: rawVaga ? rawVaga.slice(0, 64) : null,
  };
}

/** Generic UUID shape check (any version, case-insensitive). */
export function isUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
    value,
  );
}

/** Filters → query params for `GET /api/v1/public/jobs`. `vaga` is local-only. */
export function toApiParams(filters: Filters): Record<string, string> {
  const params: Record<string, string> = {
    sort: filters.sort,
    page: String(filters.page),
  };
  if (filters.q) {
    params.q = filters.q;
  }
  if (filters.city) {
    params.city = filters.city;
  }
  return params;
}

/** Canonical, shareable board href — defaults are omitted. */
export function buildBoardHref(filters: Filters): string {
  const params = new URLSearchParams();
  if (filters.q) {
    params.set("q", filters.q);
  }
  if (filters.city) {
    params.set("city", filters.city);
  }
  if (filters.sort !== "recentes") {
    params.set("sort", filters.sort);
  }
  if (filters.page > 1) {
    params.set("page", String(filters.page));
  }
  if (filters.vaga) {
    params.set("vaga", filters.vaga);
  }
  const query = params.toString();
  return query ? `/?${query}` : "/";
}

export function hasActiveFilters(filters: Filters): boolean {
  return Boolean(filters.q || filters.city);
}
