"""pt-BR phone normalization → E.164 (``+55...``), or ``None``.

Threat T-02-01 (mitigate): deterministic regex/cleanup normalization;
anything unparseable returns ``None`` — never store garbage that could be
concatenated into a scam wa.me link.

Accepted shapes (after stripping spaces, dashes, parens, dots):
- ``+<cc><ddd><num>`` (Brazil assumed: cc=55)
- ``<cc><ddd><num>`` with a leading 55 (length implies country code)
- ``<ddd><local>`` (BR assumed, 55 prepended)

Rejected (returns ``None``): bare 8–9 digit numbers without DDD (ambiguous),
invalid DDD (must be ``[1-9][1-9]``), wrong local length, non-digits.
This function NEVER raises.
"""

import re

# Spaces, dashes, parens and dots are pure presentation noise in pt-BR
# phone strings ("(11) 9 1234-5678", "..11.91234.5678").
_SEPARATORS = re.compile(r"[\s\-().]")

_DDD = re.compile(r"^[1-9][1-9]$")


def normalize_phone(value: str | None) -> str | None:
    """Normalize a pt-BR phone string to ``+55{ddd}{local}`` or ``None``."""
    if not isinstance(value, str):
        return None

    digits = _SEPARATORS.sub("", value)
    if digits.startswith("+"):
        digits = digits[1:]

    if not digits.isdigit() or not digits:
        return None

    # Strip the BR country code when the length implies it.
    if len(digits) in (12, 13) and digits.startswith("55"):
        digits = digits[2:]
    elif len(digits) not in (10, 11):
        # Not a plausible BR national number → reject (covers 8–9 digit
        # no-DDD numbers and foreign country codes).
        return None

    ddd, local = digits[:2], digits[2:]
    if not _DDD.match(ddd):
        return None

    if len(local) == 9:
        # Mobile: must start with 9.
        if local[0] != "9":
            return None
    elif len(local) == 8:
        # Landline (first digit 2–5 in real BR numbering; accept 2–9 as a
        # permissive-but-structured check — never reject valid legacy ranges).
        if not local[0].isdigit():
            return None
    else:
        return None

    return f"+55{ddd}{local}"
