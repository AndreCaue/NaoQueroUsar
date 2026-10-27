"use client";

import { useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";

const TOKEN_KEY = "nqu_admin_token";

/**
 * Hook that protects admin routes.
 * Reads the admin token from sessionStorage.
 * If the token is absent, redirects to /admin/paste.
 * Returns the current token value for use in components.
 */
export function useAdminGuard(): string | null {
  const router = useRouter();

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(TOKEN_KEY);
      if (!stored) {
        router.replace("/admin/paste");
      }
    } catch {
      // ignore storage errors
    }
  }, [router]);

  // Also return what's in storage (could be set by login)
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

/** Optional component wrapper that re-exports the hook logic */
export function AdminGuard({ children }: { children: ReactNode }) {
  const token = useAdminGuard();

  // If no token, redirect immediately (server-side or client-side)
  if (!token) {
    const router = useRouter();
    router.replace("/admin/paste");
  }

  return children;
}