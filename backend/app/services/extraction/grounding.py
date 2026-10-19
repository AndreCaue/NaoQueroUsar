"""Normalized-containment grounding check for LLM-extracted candidates.

Threat model (plan 02-01): LLM output is untrusted even under strict mode.
A candidate field is only "grounded" when its normalized text literally
appears in the normalized source chunk (accent/case/emoji-insensitive),
which blocks pure hallucinations before persistence.

Normalization rules:
- NFKD normalize and drop combining marks (``São`` → ``sao``)
- lowercase
- keep ``a-z 0-9 @ . + _`` and ``-``→dropped, everything else removed
  (contacts/salaries need ``@``, ``+``, ``.``, digits)
- collapse whitespace runs to a single space, strip ends

``normalize_for_grounding`` is idempotent: ``f(f(x)) == f(x)``.
"""

import unicodedata

_KEEP = frozenset("abcdefghijklmnopqrstuvwxyz0123456789@.+_")


def normalize_for_grounding(text: str) -> str:
    """Accent/case/punctuation-insensitive normalization for containment checks."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    kept = "".join(
        ch for ch in stripped.lower() if ch in _KEEP or ch.isspace()
    )
    return " ".join(kept.split())


def is_grounded(needle: str, haystack_normalized: str) -> bool:
    """True when the normalized needle appears in an already-normalized haystack.

    ``needle`` is normalized the same way as the haystack; an empty/blank
    needle is never grounded.
    """
    normalized_needle = normalize_for_grounding(needle)
    if not normalized_needle:
        return False
    return normalized_needle in haystack_normalized
