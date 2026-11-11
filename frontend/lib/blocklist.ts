/**
 * Termos bloqueados na extração (admin paste) — regra única do frontend.
 * Espelha backend/app/services/extraction/blocklist.py: case-insensitive,
 * sem acentos (NFKD) e com espaços/quebras de linha colapsados. A comparação
 * é por substring em qualquer ponto do texto. Trocar o termo = trocar aqui e
 * no módulo Python, nada mais.
 */

export const BLOCKED_TERM = "JACIRA CHAVARE";

export const BLOCKED_TERM_ERROR = `Texto bloqueado — remova "${BLOCKED_TERM}" antes de extrair.`;

function fold(value: string): string {
  return value
    .normalize("NFKD")
    // Marcas combinantes latinas (U+0300–U+036F). NÃO use \p{M}: o tsconfig
    // do projeto tem target ES2017 e Unicode property escapes exigem ES2018.
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

const FOLDED_TERM = fold(BLOCKED_TERM);

export function isBlockedText(text: string): boolean {
  return fold(text).includes(FOLDED_TERM);
}
