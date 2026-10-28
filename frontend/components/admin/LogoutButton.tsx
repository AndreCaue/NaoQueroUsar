"use client";

import { useRouter } from "next/navigation";

import { useToast } from "@/components/admin/ToastProvider";

export function LogoutButton() {
  const router = useRouter();
  const { toast } = useToast();

  const handleLogout = () => {
    try {
      sessionStorage.removeItem("nqu_admin_token");
    } catch {
      // ignore storage errors
    }
    toast("Sessão encerrada.", "success");
    router.replace("/admin/paste");
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
