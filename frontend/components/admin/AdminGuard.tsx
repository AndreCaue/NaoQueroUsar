"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useRouter } from "next/navigation";

const TOKEN_KEY = "nqu_admin_token";

/**
 * Hook that protects admin routes.
 *
 * Reads the admin token from sessionStorage after mount (never during SSR)
 * and redirects to /admin/paste when it is absent. Returns the token so
 * callers can use it for authenticated requests.
 */
export function useAdminGuard(): string | null {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = sessionStorage.getItem(TOKEN_KEY);
    } catch {
      // ignore storage errors
    }
    setToken(stored);
    if (!stored) {
      router.replace("/admin/paste");
    }
  }, [router]);

  return token;
}

/** Component wrapper: renders children only after the guard effect runs. */
export function AdminGuard({ children }: { children: ReactNode }) {
  useAdminGuard();
  return <>{children}</>;
}
