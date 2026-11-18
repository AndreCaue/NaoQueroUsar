"use client";

import type { ChatSearchResponse, JobPublic } from "@/lib/api";
import { ChatInterpretation } from "./ChatInterpretation";
import { ChatResultsList } from "./ChatResultsList";

export interface ChatTurn {
  id: string;
  user: string;
  status: "loading" | "done" | "error";
  response?: ChatSearchResponse;
  error?: string;
}

interface ChatThreadProps {
  turns: ChatTurn[];
  activeTurnId: string | null;
  items: JobPublic[];
  total: number;
  isLoadingMore: boolean;
  canApply: boolean;
  onRetry: (message: string) => void;
  onLoadMore: () => void;
  onApplyToBoard: () => void;
  onOpenDetail: (job: JobPublic) => void;
  onManualSearch: () => void;
}

export function ChatThread({
  turns,
  activeTurnId,
  items,
  total,
  isLoadingMore,
  canApply,
  onRetry,
  onLoadMore,
  onApplyToBoard,
  onOpenDetail,
  onManualSearch,
}: ChatThreadProps) {
  if (turns.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-canvas p-4">
        <p className="text-[20px] font-semibold leading-[1.2] text-fg">
          Encontre vagas conversando
        </p>
        <p className="mt-2 text-base text-fg-muted">
          Diga o cargo, cidade ou formato que você procura. Toque em um exemplo
          para começar.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {turns.map((turn) => {
        const isActive = turn.id === activeTurnId;
        return (
          <div key={turn.id} className="space-y-3">
            <div className="flex justify-end">
              <div className="max-w-[90%] rounded-lg border border-line-strong bg-surface px-3 py-2 text-sm text-fg [overflow-wrap:anywhere]">
                {turn.user}
              </div>
            </div>

            {turn.status === "loading" ? (
              <div className="rounded-lg border border-line bg-canvas p-3 text-sm text-fg-muted">
                Interpretando sua busca...
              </div>
            ) : null}

            {turn.status === "error" ? (
              <div className="rounded-lg border border-danger/40 bg-canvas p-3">
                <p className="text-sm text-danger">
                  {turn.error || "Não foi possível buscar agora."}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => onRetry(turn.user)}
                    className="inline-flex min-h-11 items-center justify-center rounded-lg border border-accent px-4 text-sm font-semibold text-accent-soft transition-colors hover:border-accent-soft hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
                  >
                    Tentar novamente
                  </button>
                  <button
                    type="button"
                    onClick={onManualSearch}
                    className="inline-flex min-h-11 items-center justify-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
                  >
                    Usar busca manual
                  </button>
                </div>
              </div>
            ) : null}

            {turn.status === "done" && turn.response ? (
              <div className="space-y-3">
                <ChatInterpretation interpretation={turn.response.interpretation} />
                {isActive ? (
                  <ChatResultsList
                    interpretation={turn.response.interpretation}
                    items={items}
                    total={total}
                    isLoadingMore={isLoadingMore}
                    canApply={canApply}
                    onLoadMore={onLoadMore}
                    onApplyToBoard={onApplyToBoard}
                    onOpenDetail={onOpenDetail}
                    onManualSearch={onManualSearch}
                  />
                ) : (
                  <p className="text-sm text-fg-muted">
                    Resultados desta busca não estão ativos. Envie uma nova
                    mensagem para atualizar.
                  </p>
                )}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
