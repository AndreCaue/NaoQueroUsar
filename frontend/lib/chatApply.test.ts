import { describe, expect, it } from "vitest";

import type { ChatInterpretation } from "@/lib/api";
import {
  appliedParamsToBoardFilters,
  canApplyChatToBoard,
} from "@/lib/chatApply";

function interpretation(overrides: {
  degraded?: boolean;
  degradationReason?: string;
  q?: string | null;
  city?: string | null;
  sort?: "recentes" | "antigas" | null;
}): ChatInterpretation {
  const meta: ChatInterpretation["meta"] = {};
  if (overrides.degraded) meta.degraded = true;
  if (overrides.degradationReason) {
    meta.degradation_reason = overrides.degradationReason;
    if (overrides.degradationReason === "chat_disabled") {
      meta.degraded = true;
    }
  }
  return {
    understood: {},
    field_statuses: [],
    applied_params: {
      q: overrides.q ?? null,
      city: overrides.city ?? null,
      sort: overrides.sort ?? null,
    },
    limitations: [],
    meta,
  };
}

describe("appliedParamsToBoardFilters", () => {
  it("maps q/city/sort and forces page 1 and vaga null", () => {
    expect(
      appliedParamsToBoardFilters({
        q: "react",
        city: "sao-paulo",
        sort: "antigas",
      }),
    ).toEqual({
      q: "react",
      city: "sao-paulo",
      sort: "antigas",
      page: 1,
      vaga: null,
    });
  });

  it("turns null q/city into empty q and null city", () => {
    expect(
      appliedParamsToBoardFilters({ q: null, city: null, sort: "recentes" }),
    ).toEqual({ q: "", city: null, sort: "recentes", page: 1, vaga: null });
  });

  it("normalizes unknown city to null", () => {
    expect(
      appliedParamsToBoardFilters({
        q: "dev",
        city: "campinas",
        sort: "recentes",
      }),
    ).toEqual({ q: "dev", city: null, sort: "recentes", page: 1, vaga: null });
  });

  it("defaults null sort to recentes", () => {
    expect(
      appliedParamsToBoardFilters({ q: "qa", city: null, sort: null }),
    ).toEqual({ q: "qa", city: null, sort: "recentes", page: 1, vaga: null });
  });
});

describe("canApplyChatToBoard", () => {
  it("returns false when degraded or all empty/default", () => {
    expect(canApplyChatToBoard(interpretation({ degraded: true, q: "react" }))).toBe(
      false,
    );
    expect(
      canApplyChatToBoard(interpretation({ q: null, city: null, sort: null })),
    ).toBe(false);
    expect(
      canApplyChatToBoard(interpretation({ q: " ", city: null, sort: "recentes" })),
    ).toBe(false);
  });

  it("returns false when degradation_reason is chat_disabled", () => {
    expect(
      canApplyChatToBoard(
        interpretation({
          degraded: true,
          degradationReason: "chat_disabled",
          q: "react",
          city: "sao-paulo",
          sort: "antigas",
        }),
      ),
    ).toBe(false);
    expect(
      canApplyChatToBoard(
        interpretation({
          degradationReason: "chat_disabled",
          q: "react",
        }),
      ),
    ).toBe(false);
  });

  it("returns true when q, whitelisted city, or sort antigas is present", () => {
    expect(canApplyChatToBoard(interpretation({ q: "react" }))).toBe(true);
    expect(canApplyChatToBoard(interpretation({ city: "sao-paulo" }))).toBe(true);
    expect(canApplyChatToBoard(interpretation({ sort: "antigas" }))).toBe(true);
  });
});
