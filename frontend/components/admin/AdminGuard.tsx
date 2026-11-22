"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { buildAdminLoginHref } from "@/lib/adminReturnTo";
import { TOKEN_KEY } from "@/lib/auth";

/**
 * Hook that protects admin routes.
 *
 * Reads the admin token from sessionStorage after mount (never during SSR)
 * and redirects to /admin/login when it is absent. Returns the token so
 * callers can use it for authenticated requests.
 */
export function useAdminGuard(): string | null {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const search = searchParams.toString();
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
      const current = `${pathname}${search ? `?${search}` : ""}`;
      router.replace(buildAdminLoginHref(current));
    }
  }, [router, pathname, search]);

  return token;
}
