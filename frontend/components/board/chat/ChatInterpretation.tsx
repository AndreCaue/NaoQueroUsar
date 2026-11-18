"use client";

import type { ChatInterpretation as ChatInterpretationData } from "@/lib/api";

function statusLabel(status: string): string {
  if (status === "aplicado") return "Aplicado";
  if (status === "ignorado") return "Ignorado";
  return "Aproximado";
}

function statusClasses(status: string): string {
  if (status === "aplicado") {
    return "border-accent/50 text-accent-soft";
  }
  if (status === "ignorado") {
    return "border-line-strong text-fg-muted";
  }
  return "border-line-strong text-fg";
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function buildEntendiSummary(interpretation: ChatInterpretationData): string {
  const parts: string[] = [];
  const { applied_params } = interpretation;
  if (applied_params.q) parts.push(`busca por "${applied_params.q}"`);
  if (applied_params.city) parts.push(`em ${applied_params.city}`);
  if (applied_params.sort === "antigas") parts.push("ordenado por mais antigas");
  if (parts.length === 0) return "Entendi: sua busca";
  return `Entendi: ${parts.join(", ")}.`;
}

interface ChatInterpretationProps {
  interpretation: ChatInterpretationData;
}

export function ChatInterpretation({ interpretation }: ChatInterpretationProps) {
  const guidance =
    typeof interpretation.meta?.guidance === "string"
      ? interpretation.meta.guidance
      : null;
  const limitations = interpretation.limitations ?? [];

  return (
    <div className="space-y-3 rounded-lg border border-line bg-canvas p-3">
      <p className="text-base text-fg">{buildEntendiSummary(interpretation)}</p>

      {interpretation.field_statuses.length > 0 ? (
        <div className="space-y-2">
          {interpretation.field_statuses.map((field, idx) => (
            <div
              key={`${field.field}-${idx}`}
              className="rounded-md border border-line p-2"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold text-fg">{field.field}</span>
                <span
                  className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs ${statusClasses(field.status)}`}
                >
                  {statusLabel(field.status)}
                </span>
              </div>
              {field.reason ? (
                <p className="mt-1 text-sm text-fg-muted">{field.reason}</p>
              ) : null}
              <p className="mt-1 text-xs text-fg-muted">
                Entendido: {formatValue(field.understood)} · Aplicado:{" "}
                {formatValue(field.applied)}
              </p>
            </div>
          ))}
        </div>
      ) : null}

      {limitations.length > 0 || guidance ? (
        <div className="rounded-md border border-line-strong bg-surface p-3">
          <p className="text-sm font-semibold text-fg">Limites desta busca</p>
          {limitations.length > 0 ? (
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-fg-muted">
              {limitations.map((item, idx) => (
                <li key={`${item}-${idx}`}>{item}</li>
              ))}
            </ul>
          ) : null}
          {guidance ? (
            <p className="mt-2 text-sm text-fg-muted">{guidance}</p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
