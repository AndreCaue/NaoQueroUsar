import { normalizeFilters, type Filters } from "@/lib/filters";
import type { ChatAppliedParams, ChatInterpretation } from "@/lib/api";

export function appliedParamsToBoardFilters(applied: ChatAppliedParams): Filters {
  const normalized = normalizeFilters({
    q: (applied.q ?? "").trim(),
    city: (applied.city ?? "").trim().toLowerCase(),
    sort: applied.sort ?? "recentes",
    page: "1",
    vaga: "",
  });
  return { ...normalized, page: 1, vaga: null };
}

export function canApplyChatToBoard(interpretation: ChatInterpretation): boolean {
  if (
    interpretation.meta?.degraded === true ||
    interpretation.meta?.degradation_reason === "chat_disabled"
  ) {
    return false;
  }
  const p = interpretation.applied_params;
  const hasQ = typeof p.q === "string" && p.q.trim().length > 0;
  const hasCity = typeof p.city === "string" && p.city.trim().length > 0;
  const hasSort = p.sort === "antigas";
  return hasQ || hasCity || hasSort;
}
