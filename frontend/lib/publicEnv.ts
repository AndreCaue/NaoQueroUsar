const ADS_DISABLED_VALUES = new Set(["false", "0", "off", "no", "disabled"]);

export function parseAdsEnabled(value: string | undefined): boolean {
  const normalized = value?.trim().toLowerCase();
  if (!normalized) return true; // D-01: absent/empty => show ads
  if (ADS_DISABLED_VALUES.has(normalized)) return false;
  return true; // any other value preserves current behavior
}

export function isAdsEnabled(): boolean {
  // Static property access required for Next.js NEXT_PUBLIC inlining in client bundles.
  return parseAdsEnabled(process.env.NEXT_PUBLIC_ADS_ENABLED);
}

export function parseDonationUrl(value: string | undefined): string | null {
  const normalized = value?.trim();
  if (!normalized) return null;
  try {
    const parsed = new URL(normalized);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return null;
    return parsed.toString();
  } catch {
    return null;
  }
}

export function getDonationUrl(): string | null {
  // Static property access required for Next.js NEXT_PUBLIC inlining in client bundles.
  return parseDonationUrl(process.env.NEXT_PUBLIC_DONATION_URL);
}
