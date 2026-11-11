"""Remoção do termo residual na extração (admin paste) — regra única do backend.

Regra (espelhada em frontend/lib/blocklist.ts): todas as ocorrências do termo
são removidas, em qualquer caixa, ignorando acentos e aceitando qualquer
quantidade de espaços/quebras de linha entre as palavras. Cada ocorrência é
substituída por UM espaço e o restante do texto é preservado byte a byte —
nenhuma normalização global é aplicada.

O padrão é construído a partir da constante ``REMOVED_TERM`` (nunca de input
do usuário), então não há risco de injeção de padrão nem de ReDoS.

Nunca logue nem ecoe o texto colado: a mensagem cita apenas o termo.
"""

import re

REMOVED_TERM = "JACIRA CHAVARE"

TERM_REMOVED_ALERT = (
    'ℹ️ O termo "JACIRA CHAVARE" foi removido do texto antes da extração.'
)

# Variantes acentuadas aceitas por letra (minúsculas; a maiúscula é derivada).
_LETTER_VARIANTS = {
    "a": "aáàâãä",
    "c": "cç",
    "e": "eéèêë",
    "h": "h",
    "i": "iíìîï",
    "j": "j",
    "r": "r",
    "v": "v",
}


def _char_class(char: str) -> str:
    """Classe de caracteres que aceita a letra em caixa baixa, alta e acentuada."""
    variants = _LETTER_VARIANTS.get(char.lower(), char.lower())
    return f"[{variants}{variants.upper()}]"


_TERM_PATTERN = re.compile(
    "".join(r"\s+" if char == " " else _char_class(char) for char in REMOVED_TERM)
)


def strip_blocked_terms(text: str) -> str:
    """Remove todas as ocorrências do termo; cada uma vira um único espaço.

    Devolve ``""`` quando o texto é só o termo (ou ficou só com espaços),
    preservando o restante exatamente como veio do admin.
    """
    if not text:
        return ""
    cleaned = _TERM_PATTERN.sub(" ", text)
    return "" if not cleaned.strip() else cleaned
