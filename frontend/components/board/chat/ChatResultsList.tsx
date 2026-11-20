"use client";

import type { ChatInterpretation, JobPublic } from "@/lib/api";
import { ChatResultItem } from "./ChatResultItem";

interface ChatResultsListProps {
  interpretation: ChatInterpretation;
  items: JobPublic[];
  total: number;
  isLoadingMore: boolean;
  canApply: boolean;
  onLoadMore: () => void;
  onApplyToBoard: () => void;
  onOpenDetail: (job: JobPublic, trigger?: HTMLElement | null) => void;
  onManualSearch: () => void;
}

export function ChatResultsList({
  interpretation,
  items,
  total,
  isLoadingMore,
  canApply,
  onLoadMore,
  onApplyToBoard,
  onOpenDetail,
  onManualSearch,
}: ChatResultsListProps) {
  const isDegraded = interpretation.meta?.degraded === true;
  const hasPartialSupport =
    interpretation.field_statuses?.some((f) => f.status === "aproximado") ||
    (interpretation.limitations?.length ?? 0) > 0;
  const hasMore = items.length < total;

  if (!isDegraded && items.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-canvas p-4">
        <p className="text-base font-semibold text-fg">Nenhuma vaga encontrada</p>
        <p className="mt-1 text-sm text-fg-muted">
          Não encontramos vagas com o que foi aplicado. Ajuste sua mensagem ou use a
          busca manual.
        </p>
        <button
          type="button"
          onClick={onManualSearch}
          className="mt-3 inline-flex min-h-11 items-center justify-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
        >
          Usar busca manual
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {isDegraded ? (
        <div className="rounded-lg border border-line-strong bg-canvas p-4">
          <p className="text-base font-semibold text-fg">Não houve resultados automáticos.</p>
          <p className="mt-1 text-sm text-fg-muted">
            Use a orientação acima e ajuste sua busca para tentar novamente.
          </p>
          <button
            type="button"
            onClick={onManualSearch}
            className="mt-3 inline-flex min-h-11 items-center justify-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
          >
            Usar busca manual
          </button>
        </div>
      ) : null}

      {items.length > 0 ? (
        <div className="space-y-2">
          {items.map((job) => (
            <ChatResultItem key={job.id} job={job} onOpen={onOpenDetail} />
          ))}
        </div>
      ) : null}

      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        {items.length > 0 && hasMore ? (
          <button
            type="button"
            onClick={onLoadMore}
            disabled={isLoadingMore}
            className="inline-flex min-h-11 items-center justify-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoadingMore ? "Carregando..." : "Carregar mais vagas"}
          </button>
        ) : null}

        {canApply ? (
          <div className="flex flex-col gap-1">
            <button
              type="button"
              onClick={onApplyToBoard}
              className="inline-flex min-h-11 items-center justify-center rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
            >
              Aplicar no board
            </button>
            {hasPartialSupport ? (
              <p className="text-xs text-fg-muted">
                Alguns critérios podem ser aproximados ou não filtrados.
              </p>
            ) : null}
          </div>
        ) : null}

        {!canApply && !isDegraded && items.length > 0 ? (
          <button
            type="button"
            onClick={onManualSearch}
            className="inline-flex min-h-11 items-center justify-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
          >
            Usar busca manual
          </button>
        ) : null}
      </div>
    </div>
  );
}
