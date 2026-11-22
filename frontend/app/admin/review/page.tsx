"use client";

import { Suspense } from "react";

import { ReviewQueue } from "@/app/admin/review/ReviewQueue";

export default function Page() {
  return (
    <div>
      <h1 className="text-[20px] font-semibold leading-tight [overflow-wrap:anywhere] [text-wrap:balance]">
        Revisão de vagas
      </h1>
      <p className="mt-1 text-[14px] text-fg-muted">
        Confira o texto-fonte ao lado e aprove para publicar.
      </p>
      <Suspense fallback={<p className="text-fg-muted">Carregando...</p>}>
        <ReviewQueue />
      </Suspense>
    </div>
  );
}
