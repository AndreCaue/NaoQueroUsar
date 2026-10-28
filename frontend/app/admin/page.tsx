"use client";

import Link from "next/link";

import { useAdminGuard } from "@/components/admin/AdminGuard";

const cardClass =
  "group rounded-[12px] border border-line bg-surface p-6 transition-colors hover:border-accent focus-visible:border-accent";

export default function AdminPage() {
  useAdminGuard();

  return (
    <div>
      <h1 className="mb-2 text-3xl font-semibold leading-tight tracking-tight">
        Painel admin
      </h1>
      <p className="mb-8 text-fg-muted">
        Curadoria de vagas: extraia, revise e publique.
      </p>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Link href="/admin/paste" className={cardClass}>
          <h2 className="mb-2 text-xl font-semibold">Colar vagas</h2>
          <p className="mb-4 text-fg-muted">
            Cole um texto bruto e extraia vagas de emprego automaticamente.
          </p>
          <span className="inline-flex items-center gap-2 text-sm text-accent-soft group-hover:text-accent">
            Abrir extração
          </span>
        </Link>

        <Link href="/admin/review" className={cardClass}>
          <h2 className="mb-2 text-xl font-semibold">Revisar vagas</h2>
          <p className="mb-4 text-fg-muted">
            Aprove, edite ou exclua vagas pendentes antes de publicá-las.
          </p>
          <span className="inline-flex items-center gap-2 text-sm text-accent-soft group-hover:text-accent">
            Abrir fila de revisão
          </span>
        </Link>
      </div>
    </div>
  );
}
