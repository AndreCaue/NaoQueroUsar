"use client";

import { useAdminGuard } from "@/components/admin/AdminGuard";
import { ReviewQueue } from "@/app/admin/review/ReviewQueue";

export default function Page() {
  useAdminGuard();

  return (
    <div>
      <h1 className="text-[20px] font-semibold leading-tight [overflow-wrap:anywhere] [text-wrap:balance]">
        Revisão de vagas
      </h1>
      <p className="text-[14px] text-fg-muted mt-1">
        Confira o texto-fonte ao lado e aprove para publicar.
      </p>
      <ReviewQueue />
    </div>
  );
}