"use client";

import { useAdminGuard } from "@/components/admin/AdminGuard";
import { useToast } from "@/components/admin/ToastProvider";
import Link from "next/link";

export default function AdminPage() {
  const token = useAdminGuard();

  const { toast } = useToast();

  const handleLogout = () => {
    sessionStorage.removeItem("nqu_admin_token");
    toast("Logout realizado", "success");
    if (typeof window !== "undefined") {
      window.location.href = "/admin/paste";
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-fg">
      <header className="sticky top-0 z-40 border-b border-line bg-canvas">
        <div className="mx-auto max-w-[1120px] h-16 items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-xl font-semibold text-fg">
              NaoQueroUsar
              <span aria-hidden="true" className="text-accent-soft">
                .
              </span>
            </Link>
            <span className="hidden text-sm font-normal text-fg-muted md:inline">
              Procurar um emprego, não deve dar trabalho
            </span>
          </div>

          <div className="flex items-center gap-2">
            {token ? (
              <button
                className="ghost hover:text-fg rounded-md px-3 py-1.5 text-sm font-medium"
                onClick={handleLogout}
              >
                Sair
              </button>
            ) : (
              <button
                className="bg-accent hover:text-fg rounded-md px-3 py-1.5 text-sm font-medium"
                onClick={() => {
                  sessionStorage.setItem("nqu_admin_token", "dummy");
                  toast("Autenticado", "success");
                }}
              >
                Entrar
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1120px] px-4 py-8 md:px-6">
        <h1 className="text-6xl font-bold tracking-tight mb-3">Painel admin</h1>
        <p className="text-fg-muted mb-8">Curadoria de vagas: extraia, revise e publique.</p>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Paste card */}
          <Link
            href="/admin/paste"
            className="group bg-surface border border-line rounded-lg p-6 hover:border-accent transition-colors duration-200"
          >
            <h2 className="text-xl font-semibold mb-2">Colar vagas</h2>
            <p className="text-fg-muted mb-4">
              Cole um texto bruto e extraia vagas de emprego automaticamente
            </p>
            <svg
              className="w-6 h-6 text-accent-soft group-hover:text-accent"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="17 3 12 8 7 3" />
              <line x1="12" y1="8" x2="12" y2="8" />
              <line x1="7" y1="3" x2="12" y2="8" />
              <line x1="17" y1="3" x2="12" y2="8" />
            </svg>
          </Link>

          {/* Review card */}
          <Link
            href="/admin/review"
            className="group bg-surface border border-line rounded-lg p-6 hover:border-accent transition-colors duration-200"
          >
            <h2 className="text-xl font-semibold mb-2">Revisar vagas</h2>
            <p className="text-fg-muted mb-4">
              Aprova, edite ou exclua vagas pendentes antes de publicá-las
            </p>
            <svg
              className="w-6 h-6 text-accent-soft group-hover:text-accent"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="17 3 12 8 7 3" />
              <line x1="12" y1="8" x2="12" y2="8" />
              <line x1="7" y1="3" x2="12" y2="8" />
              <line x1="17" y1="3" x2="12" y2="8" />
            </svg>
          </Link>
        </div>
      </main>
    </div>
  );
}