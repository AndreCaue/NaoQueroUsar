/**
 * Date/count formatting for the board (UI-SPEC §Typography/§Data contract).
 *
 * Dates are ALWAYS absolute `dd/mm/aaaa` in America/Sao_Paulo: relative dates
 * ("há 2 dias") depend on the client clock and would diverge between the RSC
 * HTML and the browser (hydration mismatch — Pitfall 8).
 */
const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: "America/Sao_Paulo",
});

export function formatDateBR(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return dateFormatter.format(date);
}

export function formatJobCount(count: number): string {
  return count === 1 ? "1 vaga encontrada" : `${count} vagas encontradas`;
}
