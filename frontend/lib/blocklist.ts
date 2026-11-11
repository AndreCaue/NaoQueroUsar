/**
 * Remoção do termo residual na extração (admin paste) — regra única do frontend.
 * Espelha backend/app/services/extraction/blocklist.py: todas as ocorrências
 * são removidas, em qualquer caixa, ignorando acentos e aceitando qualquer
 * quantidade de espaços/quebras de linha entre as palavras. Cada ocorrência
 * vira UM espaço e o resto do texto é preservado — sem normalização global.
 * O padrão é montado a partir da constante, nunca do texto do usuário.
 */

export const REMOVED_TERM = "JACIRA CHAVARE";

export const TERM_REMOVED_NOTICE = `ℹ️ O termo "${REMOVED_TERM}" foi removido do texto antes da extração.`;

// Variantes acentuadas por letra (minúsculas; a maiúscula é derivada).
const LETTER_VARIANTS: Record<string, string> = {
  a: "aáàâãä",
  c: "cç",
  e: "eéèêë",
  h: "h",
  i: "iíìîï",
  j: "j",
  r: "r",
  v: "v",
};

function charClass(char: string): string {
  const variants = LETTER_VARIANTS[char.toLowerCase()] ?? char.toLowerCase();
  return `[${variants}${variants.toUpperCase()}]`;
}

const TERM_SOURCE = REMOVED_TERM.split("")
  .map((char) => (char === " " ? "\\s+" : charClass(char)))
  .join("");

export function stripBlockedTerms(text: string): string {
  if (!text) return "";
  // RegExp novo a cada chamada: evita o estado de lastIndex de uma /g compartilhada.
  const cleaned = text.replace(new RegExp(TERM_SOURCE, "g"), " ");
  return cleaned.trim() === "" ? "" : cleaned;
}
