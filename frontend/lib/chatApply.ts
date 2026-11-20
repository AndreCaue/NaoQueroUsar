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
  const normalized = appliedParamsToBoardFilters(interpretation.applied_params);
  return (
    normalized.q.trim().length > 0 ||
    normalized.city !== null ||
    normalized.sort === "antigas"
  );
}
