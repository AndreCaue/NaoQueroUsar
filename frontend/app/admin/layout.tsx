import type { Metadata, Viewport } from "next";
import Link from "next/link";

import "./admin.css";
import { LogoutButton } from "@/components/admin/LogoutButton";
import { ToastProvider } from "@/components/admin/ToastProvider";

export const metadata: Metadata = {
  title: "NaoQueroUsar - Painel admin",
  description: "Painel de administração - curadoria de vagas",
};

export const viewport: Viewport = {
  themeColor: "#0f0a1a",
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ToastProvider>
      <div className="flex min-h-screen flex-col bg-canvas text-fg">
        <header className="sticky top-0 z-40 border-b border-line bg-canvas">
          <div className="mx-auto flex h-16 w-full max-w-[1120px] items-center justify-between gap-4 px-4 md:px-6">
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
              <LogoutButton />
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1120px] flex-1 px-4 py-8 md:px-6">
          {children}
        </main>
      </div>
    </ToastProvider>
  );
}
