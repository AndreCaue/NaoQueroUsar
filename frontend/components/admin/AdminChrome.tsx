"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { LogoutButton } from "@/components/admin/LogoutButton";

export function AdminChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLogin = pathname === "/admin/login";

  if (isLogin) {
    return (
      <div className="flex min-h-screen flex-col bg-canvas text-fg">
        <header className="sticky top-0 z-40 border-b border-line bg-canvas">
          <div className="mx-auto flex h-16 w-full max-w-[1120px] items-center gap-4 px-4 md:px-6">
            <Link href="/" className="text-xl font-semibold text-fg">
              EmpregaNoix
              <span aria-hidden="true" className="text-accent-soft">
                .
              </span>
            </Link>
            <span className="hidden text-sm font-normal text-fg-muted md:inline">
              Procurar um emprego, não deve dar trabalho
            </span>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1120px] flex-1 px-4 py-8 md:px-6">
          {children}
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-canvas text-fg">
      <header className="sticky top-0 z-40 border-b border-line bg-canvas">
        <div className="mx-auto flex h-16 w-full max-w-[1120px] items-center justify-between gap-4 px-4 md:px-6">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-xl font-semibold text-fg">
              EmpregaNoix
              <span aria-hidden="true" className="text-accent-soft">
                .
              </span>
            </Link>
            <span className="hidden text-sm font-normal text-fg-muted md:inline">
              Procurar um emprego, não deve dar trabalho
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/admin/social-posts"
              className="text-sm text-fg-muted transition-colors hover:text-fg focus-visible:text-fg"
            >
              Publicações
            </Link>
            <Link
              href="/admin/integracoes"
              className="text-sm text-fg-muted transition-colors hover:text-fg focus-visible:text-fg"
            >
              Integrações
            </Link>
            <LogoutButton />
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1120px] flex-1 px-4 py-8 md:px-6">
        {children}
      </main>
    </div>
  );
}
