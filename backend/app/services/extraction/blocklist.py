"""Termos bloqueados na extração (admin paste) — regra única do backend.

Regra (espelhada em frontend/lib/blocklist.ts): case-insensitive, sem
acentos (NFKD) e com espaços/quebras de linha colapsados. A comparação é
por substring em qualquer ponto do texto.

Nunca logue nem ecoe o texto colado: só o termo bloqueado aparece na
mensagem, que é exibida ao admin que fez o paste.
"""

import re
import unicodedata

BLOCKED_TERM = "JACIRA CHAVARE"

BLOCKED_TERM_ERROR = (
    'Texto bloqueado — remova "JACIRA CHAVARE" antes de extrair.'
)

_WHITESPACE = re.compile(r"\s+")


def _fold(value: str) -> str:
    """Normaliza para comparar: NFKD, sem marcas, espaços colapsados, casefold."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return _WHITESPACE.sub(" ", without_marks).strip().casefold()


_FOLDED_TERM = _fold(BLOCKED_TERM)


def is_blocked_text(text: str) -> bool:
    """True quando o texto contém o termo bloqueado (substring, qualquer caixa)."""
    if not text:
        return False
    return _FOLDED_TERM in _fold(text)
