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

const CITY_TEXT_TO_SLUG: ReadonlyMap<string, CitySlug> = (() => {
  const entries: Array<[string, CitySlug]> = [];
  for (const option of CITY_OPTIONS) {
    entries.push([fold(option.slug), option.slug]);
    entries.push([fold(option.label), option.slug]);
    entries.push([fold(option.canonical), option.slug]);
  }
  const aliases: Array<[string, CitySlug]> = [
    ["sp", "sao-paulo"],
    ["sao paulo", "sao-paulo"],
    ["rj", "rio-de-janeiro"],
    ["rio", "rio-de-janeiro"],
    ["rio de janeiro", "rio-de-janeiro"],
    ["bh", "belo-horizonte"],
    ["belo horizonte", "belo-horizonte"],
    ["remoto", "remoto"],
    ["home office", "remoto"],
    ["home-office", "remoto"],
    ["trabalho remoto", "remoto"],
  ];
  for (const [alias, slug] of aliases) {
    entries.push([fold(alias), slug]);
  }
  return new Map(entries);
})();

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

/**
 * Resolve free text to a supported city slug (exact, accent/case-insensitive).
 * Matches slugs/labels/canonicals and safe aliases; returns null for non-matches.
 */
export function resolveCitySlugFromText(
  value: string | null | undefined,
): CitySlug | null {
  if (typeof value !== "string") {
    return null;
  }
  const key = fold(value);
  if (!key) {
    return null;
  }
  return CITY_TEXT_TO_SLUG.get(key) ?? null;
}
