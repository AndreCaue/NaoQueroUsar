import type { Metadata, Viewport } from "next";
import Link from "next/link";

import "./public.css";

export const metadata: Metadata = {
  title: "NaoQueroUsar — Vagas sem cadastro",
  description:
    "Encontre vagas e o contato para se candidatar em segundos. Sem conta, sem login e sem burocracia.",
};

export const viewport: Viewport = {
  themeColor: "#0f0a1a",
};

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas text-fg">
      <a
        href="#vagas"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:border focus:border-line-strong focus:bg-surface focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-accent-soft"
      >
        Ir para as vagas
      </a>

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

          <Link
            href="/doacoes"
            className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-md border border-[rgba(250,204,21,0.40)] px-3 text-sm font-semibold text-donate hover:border-donate hover:bg-[rgba(250,204,21,0.12)]"
          >
            Doações
          </Link>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1120px] flex-1 px-4 py-8 md:px-6">
        {children}
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex w-full max-w-[1120px] flex-wrap items-center justify-between gap-2 px-4 py-6 text-sm text-fg-muted md:px-6">
          <span>© 2026 NaoQueroUsar</span>
          <span>Procurar um emprego, não deve dar trabalho</span>
          {/* Phase 6 reserves this row for legal links — no dead links yet (TRST-03). */}
        </div>
      </footer>
    </div>
  );
}
