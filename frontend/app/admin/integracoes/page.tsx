import { Suspense } from "react";
import { IntegrationsClient } from "@/app/admin/integracoes/IntegrationsClient";

export default function Page() {
  return (
    <div>
      <h1 className="text-3xl font-semibold leading-tight tracking-tight">
        Integrações
      </h1>
      <p className="mt-2 text-fg-muted">
        Conecte sua Página do Facebook para publicar vagas automaticamente
        quando a integração estiver ativa.
      </p>

      <Suspense
        fallback={
          <p className="mt-6 text-fg-muted">Carregando integrações...</p>
        }
      >
        <IntegrationsClient />
      </Suspense>
    </div>
  );
}
