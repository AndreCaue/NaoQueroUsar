import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

function readFrontendFile(...segments: string[]): string {
  return readFileSync(path.resolve(process.cwd(), ...segments), "utf8");
}

describe("Phase 27 UI/env contracts", () => {
  it("27-TBD-04: layout Doações external link uses target blank and noopener noreferrer (D-04/T-27-02)", () => {
    const layout = readFrontendFile("app", "(public)", "layout.tsx");

    // Contract: donation URL comes from validated env helper
    expect(layout).toContain('import { getDonationUrl } from "@/lib/publicEnv";');
    expect(layout).toContain("const donationUrl = getDonationUrl();");

    // Contract: external configured URL opens in new tab with reverse-tabnabbing protection
    expect(layout).toContain("<a");
    expect(layout).toContain("href={donationUrl}");
    expect(layout).toContain('target="_blank"');
    expect(layout).toContain('rel="noopener noreferrer"');

    // Contract: unsafe/absent falls back to internal route
    expect(layout).toContain('<Link href="/doacoes"');
    expect(layout).toContain("Doações");
  });

  it("27-TBD-05: verify-ssr.ps1 is env-aware for ads enabled/disabled (ADS-01)", () => {
    const script = readFrontendFile("scripts", "verify-ssr.ps1");

    // Contract: script accepts env-driven AdsEnabled input with D-01 default semantics
    expect(script).toContain(
      '[string]$AdsEnabled = $env:NEXT_PUBLIC_ADS_ENABLED',
    );
    expect(script).toContain("function Get-AdsEnabled");
    expect(script).toContain(
      '@("false", "0", "off", "no", "disabled") -notcontains $normalized',
    );
    expect(script).toContain("$adsOn = Get-AdsEnabled $AdsEnabled");

    // Contract: enabled mode requires ad placeholders; disabled mode requires zero
    expect(script).toContain(
      'Assert ($adCount -ge 3) "Home has fewer than 3 ad placeholders ($adCount)"',
    );
    expect(script).toContain(
      'Assert ($adCount -eq 0) "Home should have 0 ad placeholders when ads disabled ($adCount)"',
    );
  });
});
