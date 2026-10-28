"use client";

import { TOKEN_KEY } from "@/lib/auth";

/**
 * Logs out by clearing the stored JWT and hard-navigating to the login page.
 * A full reload is intentional: components such as ExtractForm keep the token
 * in memory, so a client-side route change would leave the session alive.
 */
export function LogoutButton() {
  const handleLogout = () => {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // ignore storage errors
    }
    window.location.replace("/admin/paste");
  };

  return (
    <button
      type="button"
      onClick={handleLogout}
      className="min-h-11 rounded-md px-3 text-sm font-medium text-fg-muted transition-colors hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft"
    >
      Sair
    </button>
  );
}
