export default async function Page() {
  const { default: ExtractForm } = await import("./ExtractForm");
  return (
    <main className="py-8">
      <h1 className="text-6xl font-bold tracking-tight mb-3">Admin — Colar vagas</h1>
      <ExtractForm />
    </main>
  );
}