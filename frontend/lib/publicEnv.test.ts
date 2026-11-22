import { describe, expect, it } from "vitest";

import { parseAdsEnabled, parseDonationUrl } from "@/lib/publicEnv";

describe("parseAdsEnabled", () => {
  it("returns true when absent or empty (D-01 default visible)", () => {
    expect(parseAdsEnabled(undefined)).toBe(true);
    expect(parseAdsEnabled("")).toBe(true);
    expect(parseAdsEnabled("   ")).toBe(true);
  });

  it("returns true for explicit truthy or unknown values", () => {
    expect(parseAdsEnabled("true")).toBe(true);
    expect(parseAdsEnabled("1")).toBe(true);
    expect(parseAdsEnabled("yes")).toBe(true);
    expect(parseAdsEnabled("anything")).toBe(true);
  });

  it("returns false for explicit disable values", () => {
    expect(parseAdsEnabled("false")).toBe(false);
    expect(parseAdsEnabled("0")).toBe(false);
    expect(parseAdsEnabled("off")).toBe(false);
    expect(parseAdsEnabled("no")).toBe(false);
    expect(parseAdsEnabled("disabled")).toBe(false);
  });

  it("is case-insensitive and trims disable values", () => {
    expect(parseAdsEnabled(" FALSE ")).toBe(false);
    expect(parseAdsEnabled("Off")).toBe(false);
    expect(parseAdsEnabled("NO")).toBe(false);
    expect(parseAdsEnabled(" Disabled ")).toBe(false);
  });
});

describe("parseDonationUrl", () => {
  it("returns null when absent or empty", () => {
    expect(parseDonationUrl(undefined)).toBeNull();
    expect(parseDonationUrl("")).toBeNull();
    expect(parseDonationUrl("   ")).toBeNull();
  });

  it("accepts absolute http/https URLs and normalizes them", () => {
    expect(parseDonationUrl("https://example.com/doar")).toBe(
      "https://example.com/doar",
    );
    expect(parseDonationUrl("http://example.com")).toBe("http://example.com/");
    expect(parseDonationUrl("  https://example.com/doar  ")).toBe(
      "https://example.com/doar",
    );
  });

  it("rejects unsafe, relative, or malformed URLs", () => {
    expect(parseDonationUrl("javascript:alert(1)")).toBeNull();
    expect(
      parseDonationUrl("data:text/html,<script>alert(1)</script>"),
    ).toBeNull();
    expect(parseDonationUrl("//evil.example")).toBeNull();
    expect(parseDonationUrl("ftp://example.com")).toBeNull();
    expect(parseDonationUrl("not-a-url")).toBeNull();
    expect(parseDonationUrl("/doacoes")).toBeNull();
  });
});
