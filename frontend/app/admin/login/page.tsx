import { Suspense } from "react";

import { AdminLoginForm } from "@/components/admin/AdminLoginForm";

export default function AdminLoginPage() {
  return (
    <main className="py-8">
      <Suspense fallback={<p className="text-fg-muted">Carregando...</p>}>
        <AdminLoginForm />
      </Suspense>
    </main>
  );
}
