"use client";

import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

interface ChatPanelProps {
  open: boolean;
  titleId: string;
  onClose: () => void;
  children: ReactNode;
  composer: ReactNode;
}

export function ChatPanel({
  open,
  titleId,
  onClose,
  children,
  composer,
}: ChatPanelProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  useEffect(() => {
    if (!open) return;
    closeButtonRef.current?.focus();
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-stretch sm:justify-end">
      <button
        type="button"
        aria-label="Fechar chat"
        onClick={onClose}
        className="absolute inset-0 bg-[rgba(5,2,12,0.72)]"
      />
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative z-10 flex h-[85dvh] w-full max-w-none flex-col overflow-hidden rounded-t-[16px] border border-line bg-surface text-fg sm:m-4 sm:h-[calc(100dvh-2rem)] sm:max-w-[420px] sm:rounded-[16px]"
      >
        <header className="flex shrink-0 items-center justify-between border-b border-line px-4 py-3">
          <h2 id={titleId} className="text-[20px] font-semibold leading-[1.2] text-fg">
            Buscar vagas no chat
          </h2>
          <button
            type="button"
            ref={closeButtonRef}
            onClick={onClose}
            className="inline-flex h-11 min-h-11 items-center justify-center rounded-lg px-3 text-sm font-semibold text-fg-muted transition-colors hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
          >
            Fechar chat
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-3 sm:p-4">
          {children}
        </div>
        {composer}
      </section>
    </div>
  );
}
