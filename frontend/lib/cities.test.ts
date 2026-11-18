import { describe, expect, it } from "vitest";

import { resolveCitySlugFromText } from "@/lib/cities";

describe("resolveCitySlugFromText", () => {
  it("resolves supported cities by label/canonical/slug case and accent insensitively", () => {
    expect(resolveCitySlugFromText("São Paulo")).toBe("sao-paulo");
    expect(resolveCitySlugFromText("sao paulo")).toBe("sao-paulo");
    expect(resolveCitySlugFromText("SAO-PAULO")).toBe("sao-paulo");
    expect(resolveCitySlugFromText("Rio de Janeiro")).toBe("rio-de-janeiro");
    expect(resolveCitySlugFromText("Belo Horizonte")).toBe("belo-horizonte");
    expect(resolveCitySlugFromText("Remoto")).toBe("remoto");
  });

  it("resolves common aliases and abbreviations", () => {
    expect(resolveCitySlugFromText("sp")).toBe("sao-paulo");
    expect(resolveCitySlugFromText("rj")).toBe("rio-de-janeiro");
    expect(resolveCitySlugFromText("rio")).toBe("rio-de-janeiro");
    expect(resolveCitySlugFromText("bh")).toBe("belo-horizonte");
    expect(resolveCitySlugFromText("home office")).toBe("remoto");
    expect(resolveCitySlugFromText("home-office")).toBe("remoto");
    expect(resolveCitySlugFromText("trabalho remoto")).toBe("remoto");
  });

  it("returns null for non-matching, partial, or non-whitelist text", () => {
    expect(resolveCitySlugFromText("campinas")).toBeNull();
    expect(resolveCitySlugFromText("dev")).toBeNull();
    expect(resolveCitySlugFromText("sao")).toBeNull();
    expect(resolveCitySlugFromText("")).toBeNull();
    expect(resolveCitySlugFromText("   ")).toBeNull();
    expect(resolveCitySlugFromText(null)).toBeNull();
    expect(resolveCitySlugFromText(undefined)).toBeNull();
  });
});
