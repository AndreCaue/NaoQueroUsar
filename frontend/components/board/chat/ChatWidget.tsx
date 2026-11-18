"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { chatSearch, getChatSearchStatus, ApiError } from "@/lib/api";
import type { ChatSearchResponse, JobPublic } from "@/lib/api";
import { appliedParamsToBoardFilters, canApplyChatToBoard } from "@/lib/chatApply";
import { buildBoardHref } from "@/lib/filters";
import { JobDetailDialog } from "@/components/board/JobDetailDialog";
import { ChatComposer } from "./ChatComposer";
import { ChatLauncher } from "./ChatLauncher";
import { ChatPanel } from "./ChatPanel";
import { ChatThread, type ChatTurn } from "./ChatThread";

function syncVagaParam(jobId: string | null): void {
  const params = new URLSearchParams(window.location.search);
  if (jobId) {
    params.set("vaga", jobId);
  } else {
    params.delete("vaga");
  }
  const query = params.toString();
  const path = window.location.pathname || "/";
  window.history.replaceState(null, "", query ? `${path}?${query}` : path);
}

function focusManualSearch() {
  const input = document.querySelector<HTMLInputElement>(
    'input[aria-label="Buscar vagas"]',
  );
  if (input) {
    input.scrollIntoView({ block: "center" });
    input.focus();
  } else {
    const anchor = document.getElementById("vagas");
    anchor?.scrollIntoView({ block: "start" });
  }
}

function isChatDisabledResponse(response: ChatSearchResponse): boolean {
  return response.interpretation.meta?.degradation_reason === "chat_disabled";
}

function sanitizeDisabledResponse(response: ChatSearchResponse): ChatSearchResponse {
  if (!isChatDisabledResponse(response)) return response;
  const safeGuidance =
    typeof response.interpretation.meta?.guidance === "string" &&
    response.interpretation.meta.guidance.trim().length > 0
      ? response.interpretation.meta.guidance
      : "A busca por chat está indisponível no momento. Use a busca manual para encontrar vagas.";
  return {
    ...response,
    interpretation: {
      ...response.interpretation,
      limitations: (response.interpretation.limitations ?? []).filter(
        (item) => item !== "chat_disabled",
      ),
      meta: {
        ...response.interpretation.meta,
        degraded: true,
        degradation_reason: "chat_disabled",
        guidance: safeGuidance,
      },
    },
    results: {
      ...response.results,
      items: [],
      total: 0,
    },
  };
}

export function ChatWidget() {
  const router = useRouter();
  const [chatEnabled, setChatEnabled] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [activeQuery, setActiveQuery] = useState<string | null>(null);
  const [activeTurnId, setActiveTurnId] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<ChatSearchResponse | null>(null);
  const [items, setItems] = useState<JobPublic[]>([]);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [total, setTotal] = useState(0);
  const [selectedJob, setSelectedJob] = useState<JobPublic | null>(null);

  const requestSeq = useRef(0);
  const activeRequestRef = useRef(0);
  const idRef = useRef(0);
  const detailTriggerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const status = await getChatSearchStatus();
        if (cancelled) return;
        if (status.enabled === false) {
          setChatEnabled(false);
          setIsOpen(false);
        } else {
          setChatEnabled(true);
        }
      } catch {
        // Fail safe without blocking the board; backend remains authoritative on send.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const canApply = useMemo(() => {
    if (!lastResponse) return false;
    return canApplyChatToBoard(lastResponse.interpretation);
  }, [lastResponse]);

  const handleManualSearch = () => {
    setIsOpen(false);
    focusManualSearch();
  };

  const runSend = async (message: string) => {
    const trimmed = message.trim();
    if (!trimmed || isSending) return;
    if (!chatEnabled) {
      setIsOpen(false);
      focusManualSearch();
      return;
    }
    const turnId = `turn-${++idRef.current}`;
    const seq = ++requestSeq.current;
    activeRequestRef.current = seq;

    setSendError(null);
    setIsSending(true);
    setIsOpen(true);
    setActiveQuery(trimmed);
    setActiveTurnId(turnId);
    setLastResponse(null);
    setItems([]);
    setPage(1);
    setLimit(20);
    setTotal(0);
    setTurns((prev) => [...prev, { id: turnId, user: trimmed, status: "loading" }]);

    try {
      const response = await chatSearch({ message: trimmed, page: 1, limit: 20 });
      if (activeRequestRef.current !== seq) return;

      if (isChatDisabledResponse(response)) {
        const disabledResponse = sanitizeDisabledResponse(response);
        setChatEnabled(false);
        setIsOpen(false);
        setLastResponse(disabledResponse);
        setItems([]);
        setPage(disabledResponse.results.page ?? 1);
        setLimit(disabledResponse.results.limit ?? 20);
        setTotal(0);
        setActiveQuery(null);
        setActiveTurnId(null);
        setSendError(null);
        setTurns((prev) =>
          prev.map((t) =>
            t.id === turnId
              ? { ...t, status: "done", response: disabledResponse, error: undefined }
              : t,
          ),
        );
        setDraft("");
        focusManualSearch();
        return;
      }

      setLastResponse(response);
      setItems(response.results.items ?? []);
      setPage(response.results.page ?? 1);
      setLimit(response.results.limit ?? 20);
      setTotal(response.results.total ?? 0);
      setTurns((prev) =>
        prev.map((t) =>
          t.id === turnId ? { ...t, status: "done", response, error: undefined } : t,
        ),
      );
      setDraft("");
    } catch (err) {
      if (activeRequestRef.current !== seq) return;
      const messageErr =
        err instanceof ApiError && err.message
          ? err.message
          : "Não foi possível buscar agora.";
      const safeMessage = messageErr || "Não foi possível buscar agora.";
      setSendError(safeMessage);
      setTurns((prev) =>
        prev.map((t) =>
          t.id === turnId ? { ...t, status: "error", error: safeMessage } : t,
        ),
      );
    } finally {
      if (activeRequestRef.current === seq) {
        setIsSending(false);
      }
    }
  };

  const handleRetry = (message: string) => {
    if (isSending) return;
    void runSend(message);
  };

  const handleLoadMore = async () => {
    if (!activeQuery || !activeTurnId || !lastResponse) return;
    if (isLoadingMore || isSending) return;
    if (items.length >= total) return;

    const queryAtStart = activeQuery;
    const turnAtStart = activeTurnId;
    const nextPage = page + 1;
    const seq = ++requestSeq.current;
    activeRequestRef.current = seq;
    setIsLoadingMore(true);

    try {
      const response = await chatSearch({
        message: queryAtStart,
        page: nextPage,
        limit,
      });
      if (activeRequestRef.current !== seq) return;
      if (activeQuery !== queryAtStart || activeTurnId !== turnAtStart) return;
      if (isChatDisabledResponse(response)) {
        const disabledResponse = sanitizeDisabledResponse(response);
        setChatEnabled(false);
        setIsOpen(false);
        setLastResponse(disabledResponse);
        setItems([]);
        setPage(disabledResponse.results.page ?? nextPage);
        setLimit(disabledResponse.results.limit ?? limit);
        setTotal(0);
        setActiveQuery(null);
        setActiveTurnId(null);
        setSendError(null);
        focusManualSearch();
        return;
      }
      setLastResponse((prev) => prev ?? response);
      setItems((prev) => [...prev, ...(response.results.items ?? [])]);
      setPage(response.results.page ?? nextPage);
      setLimit(response.results.limit ?? limit);
      setTotal(response.results.total ?? total);
    } catch (err) {
      if (activeRequestRef.current !== seq) return;
      if (activeQuery !== queryAtStart || activeTurnId !== turnAtStart) return;
      const msg =
        err instanceof ApiError && err.message
          ? err.message
          : "Não foi possível buscar agora.";
      setSendError(msg || "Não foi possível buscar agora.");
    } finally {
      if (activeRequestRef.current === seq) {
        setIsLoadingMore(false);
      }
    }
  };

  const handleApplyToBoard = () => {
    if (!lastResponse) return;
    if (!canApplyChatToBoard(lastResponse.interpretation)) return;
    const filters = appliedParamsToBoardFilters(
      lastResponse.interpretation.applied_params,
    );
    const href = buildBoardHref({ ...filters, page: 1, vaga: null });
    router.replace(href, { scroll: false });
    setIsOpen(false);
  };

  const handleOpenDetail = (job: JobPublic, trigger?: HTMLElement | null) => {
    detailTriggerRef.current = trigger ?? null;
    setIsOpen(false);
    setSelectedJob(job);
    syncVagaParam(job.id);
  };

  const handleCloseDetail = () => {
    setSelectedJob(null);
    syncVagaParam(null);
    const trigger = detailTriggerRef.current;
    window.requestAnimationFrame(() => trigger?.focus());
  };

  if (!chatEnabled) {
    return selectedJob ? (
      <JobDetailDialog job={selectedJob} open onClose={handleCloseDetail} />
    ) : null;
  }

  return (
    <>
      {!isOpen && !selectedJob ? (
        <ChatLauncher
          onOpen={() => {
            if (!chatEnabled) return;
            setIsOpen(true);
          }}
        />
      ) : null}
      <ChatPanel
        open={isOpen}
        titleId="chat-panel-title"
        onClose={() => setIsOpen(false)}
        composer={
          <ChatComposer
            draft={draft}
            isSending={isSending}
            showExamples={turns.length === 0}
            onDraftChange={setDraft}
            onSend={(msg) => void runSend(msg)}
          />
        }
      >
        <ChatThread
          turns={turns}
          activeTurnId={activeTurnId}
          items={items}
          total={total}
          isLoadingMore={isLoadingMore}
          canApply={canApply}
          onRetry={handleRetry}
          onLoadMore={() => void handleLoadMore()}
          onApplyToBoard={handleApplyToBoard}
          onOpenDetail={(job) => handleOpenDetail(job, null)}
          onManualSearch={handleManualSearch}
        />
        {sendError ? (
          <p className="sr-only" aria-live="polite">
            {sendError}
          </p>
        ) : null}
      </ChatPanel>
      {selectedJob ? (
        <JobDetailDialog job={selectedJob} open onClose={handleCloseDetail} />
      ) : null}
    </>
  );
}
