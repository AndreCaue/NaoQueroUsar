/**
 * City map for the public board (D-05/D-06b).
 *
 * The URL and the API speak **slugs** (`sao-paulo`); the UI shows the accented
 * **label** (`São Paulo`); the database stores the accented **canonical** value
 * (`São Paulo`) — see 04-02: `ALLOWED_CITIES` in the extractor is accented.
 * `cityLabel` also accepts the unaccented spelling so stale links or future
 * payloads still render the right label.
 */
export type CitySlug =
  | "sao-paulo"
  | "rio-de-janeiro"
  | "belo-horizonte"
  | "remoto";

export interface CityOption {
  slug: CitySlug;
  label: string;
  canonical: string;
}

export const CITY_OPTIONS: readonly CityOption[] = [
  { slug: "sao-paulo", label: "São Paulo", canonical: "São Paulo" },
  { slug: "rio-de-janeiro", label: "Rio de Janeiro", canonical: "Rio de Janeiro" },
  { slug: "belo-horizonte", label: "Belo Horizonte", canonical: "Belo Horizonte" },
  { slug: "remoto", label: "Remoto", canonical: "Remoto" },
];

/** Case- and accent-insensitive comparison key. */
function fold(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();
}

/** Canonical (or label, or slug) → accented label; unknown values unchanged. */
export function cityLabel(canonical: string): string {
  if (!canonical) {
    return "";
  }
  const key = fold(canonical);
  const found = CITY_OPTIONS.find(
    (option) =>
      fold(option.canonical) === key ||
      fold(option.label) === key ||
      fold(option.slug) === key,
  );
  return found ? found.label : canonical;
}

/** URL slug → city option; `null`/unknown slugs have no option. */
export function cityBySlug(slug: string | null): CityOption | undefined {
  if (!slug) {
    return undefined;
  }
  const key = slug.trim().toLowerCase();
  return CITY_OPTIONS.find((option) => option.slug === key);
}
