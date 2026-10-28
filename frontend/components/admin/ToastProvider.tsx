"use client";

import { createContext, useCallback, useContext, useState } from "react";
import type { ReactNode } from "react";

/** Toast variant */
export type ToastVariant = "success" | "error";

/** Toast interface */
export interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
}

/** Context value for ToastProvider */
export type ToastContextValue = {
  /** Show a toast notification */
  toast: (message: string, variant?: ToastVariant) => string;
  /** Dismiss a specific toast by id */
  dismiss: (id: string) => void;
  /** Dismiss all toasts */
  dismissAll: () => void;
  /** Current toasts list */
  toasts: Toast[];
};

/** Toast dimensions and timing */
const AUTODISMISS_MS = 3000;
const MAX_VISIBLE = 3;

/** Context */
const ToastContext = createContext<ToastContextValue | undefined>(undefined);

/** Provider component */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const dismissAll = useCallback(() => {
    setToasts([]);
  }, []);

  const toast = useCallback(
    (message: string, variant: ToastVariant = "success") => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      setToasts((prev) => [
        ...prev.slice(-(MAX_VISIBLE - 1)),
        { id, message, variant },
      ]);
      window.setTimeout(() => dismiss(id), AUTODISMISS_MS);
      return id;
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={{ toast, dismiss, dismissAll, toasts }}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4"
      >
        {toasts.map((item) => (
          <div
            key={item.id}
            role="status"
            className={`pointer-events-auto w-full max-w-md rounded-lg border px-4 py-3 text-sm ${
              item.variant === "error"
                ? "border-danger bg-[rgba(248,113,113,0.12)] text-danger-soft"
                : "border-accent bg-[rgba(139,92,246,0.12)] text-fg"
            }`}
          >
            {item.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

/** Hook to use the toast context */
export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return ctx;
}
