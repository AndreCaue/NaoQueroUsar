import type { Metadata, Viewport } from "next";

import "./admin.css";
import { AdminChrome } from "@/components/admin/AdminChrome";
import { ToastProvider } from "@/components/admin/ToastProvider";

export const metadata: Metadata = {
  title: "EmpregaNoix - Painel admin",
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
      <AdminChrome>{children}</AdminChrome>
    </ToastProvider>
  );
}
