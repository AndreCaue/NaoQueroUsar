"use client";

import { Suspense } from "react";

import { SocialPostsClient } from "@/app/admin/social-posts/SocialPostsClient";

export default function Page() {
  return (
    <div>
      <h1 className="text-3xl font-semibold leading-tight tracking-tight">
        Publicações no Facebook
      </h1>
      <p className="mt-2 text-fg-muted">
        Acompanhe o status, erros e links das publicações sociais das vagas.
      </p>
      <Suspense fallback={<p className="text-fg-muted">Carregando...</p>}>
        <SocialPostsClient />
      </Suspense>
    </div>
  );
}
