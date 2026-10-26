import type { Viewport } from "next";

import "./globals.css";

export const viewport: Viewport = {
  themeColor: "#0f0a1a",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
