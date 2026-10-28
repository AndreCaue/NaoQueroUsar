"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
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
  const timersRef = useRef(new Map<string, ReturnType<typeof setTimeout>>());

  const clearTimer = useCallback((id: string) => {
    const timer = timersRef.current.get(id);
    if (timer !== undefined) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const dismiss = useCallback(
    (id: string) => {
      clearTimer(id);
      setToasts((prev) => prev.filter((item) => item.id !== id));
    },
    [clearTimer],
  );

  const scheduleDismiss = useCallback(
    (id: string, delay = AUTODISMISS_MS) => {
      clearTimer(id);
      const timer = setTimeout(() => {
        timersRef.current.delete(id);
        setToasts((prev) => prev.filter((item) => item.id !== id));
      }, delay);
      timersRef.current.set(id, timer);
    },
    [clearTimer],
  );

  const dismissAll = useCallback(() => {
    timersRef.current.forEach((timer) => clearTimeout(timer));
    timersRef.current.clear();
    setToasts([]);
  }, []);

  const toast = useCallback(
    (message: string, variant: ToastVariant = "success") => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      setToasts((prev) => [
        ...prev.slice(-(MAX_VISIBLE - 1)),
        { id, message, variant },
      ]);
      scheduleDismiss(id);
      return id;
    },
    [scheduleDismiss],
  );

  // Clear timers for toasts that were dropped by MAX_VISIBLE.
  useEffect(() => {
    const ids = new Set(toasts.map((item) => item.id));
    timersRef.current.forEach((timer, id) => {
      if (!ids.has(id)) {
        clearTimeout(timer);
        timersRef.current.delete(id);
      }
    });
  }, [toasts]);

  // Clear every pending timer when the provider unmounts.
  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach((timer) => clearTimeout(timer));
      timers.clear();
    };
  }, []);

  return (
    <ToastContext.Provider value={{ toast, dismiss, dismissAll, toasts }}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4">
        {toasts.map((item) => (
          <div
            key={item.id}
            role={item.variant === "error" ? "alert" : "status"}
            onMouseEnter={() => clearTimer(item.id)}
            onMouseLeave={() => scheduleDismiss(item.id)}
            onFocus={() => clearTimer(item.id)}
            onBlur={() => scheduleDismiss(item.id)}
            className={`pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-lg border px-4 py-3 text-sm ${
              item.variant === "error"
                ? "border-danger bg-[rgba(248,113,113,0.12)] text-danger-soft"
                : "border-accent bg-[rgba(139,92,246,0.12)] text-fg"
            }`}
          >
            <span className="flex-1">{item.message}</span>
            <button
              type="button"
              onClick={() => dismiss(item.id)}
              aria-label="Fechar notificação"
              className="-mr-1 -mt-1 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-current opacity-70 transition-opacity hover:opacity-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-current"
            >
              <span aria-hidden="true" className="text-lg leading-none">
                ×
              </span>
            </button>
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
