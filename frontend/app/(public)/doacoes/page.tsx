import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Doações — NaoQueroUsar",
};

export default function DoacoesPage() {
  return (
    <section className="max-w-[640px]">
      <h1 className="text-[28px] font-semibold leading-tight [text-wrap:balance]">
        Doações
      </h1>
      <p className="mt-4 text-base leading-normal text-fg">
        Em breve você poderá apoiar o NaoQueroUsar por PIX. Enquanto isso,
        compartilhe as vagas com quem está procurando emprego.
      </p>
      <Link
        href="/"
        className="mt-8 inline-flex min-h-11 items-center justify-center rounded-md border border-line-strong px-4 text-sm font-semibold text-fg hover:border-accent hover:text-accent-soft"
      >
        Voltar para as vagas
      </Link>
    </section>
  );
}
