export default async function Page() {
  const { default: ExtractForm } = await import("./ExtractForm");
  return (
    <main>
      <h1>Admin — Colar vagas</h1>
      <ExtractForm />
    </main>
  );
}
