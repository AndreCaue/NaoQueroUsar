"use client";

import { createContext, useContext, ReactNode, useState } from "react";

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

  const addToast = (message: string, variant: ToastVariant = "success") => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setToasts((prev) => {
      // Remove oldest if at max capacity
      if (prev.length >= MAX_VISIBLE) {
        setToasts((old) => old.slice(1));
      }
      const newToast: Toast = { id, message, variant };
      setToasts((old) => [...old, newToast]);
      return [...prev, newToast];
    });
    return id;
  };

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const dismissAll = () => {
    setToasts([]);
  };

  return (
    <ToastContext.Provider value={{ toast: addToast, dismiss, dismissAll, toasts }}>
      {children}
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

/** Hook to use the admin guard context (companion to AdminGuard) */
export function useAdminGuardContext() {
  const ctx = useContext(AdminGuardContext);
  if (!ctx) {
    throw new Error("useAdminGuard must be used within an AdminGuardContext");
  }
  return ctx;
}

/** Context for AdminGuard */
const AdminGuardContext = createContext<{
  token: string | null;
  setToken: (token: string | null) => void;
} | undefined>(undefined);

/** AdminGuard component wrapper */
export function AdminGuard({ children }: { children: ReactNode }) {
  const { token, setToken } = useAdminGuardContext();

  // We need to use useEffect here, but AdminGuard is a component
  // The hook useAdminGuard is the one that uses useEffect
  return children;
}