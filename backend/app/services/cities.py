"""City / sort whitelists shared by the public and admin routes (D-05/D-06b).

The URL and the API speak slugs (``sao-paulo``), the DB stores the accented
canonical form (``São Paulo``) and the UI renders the label. Both routers must
resolve the three spellings identically, so the table lives here instead of in
one router importing another router's private helper.
"""

from typing import Final

CITY_ALIASES: Final[dict[str, str]] = {
    "sao-paulo": "São Paulo",
    "sao paulo": "São Paulo",
    "são paulo": "São Paulo",
    "rio-de-janeiro": "Rio de Janeiro",
    "rio de janeiro": "Rio de Janeiro",
    "belo-horizonte": "Belo Horizonte",
    "belo horizonte": "Belo Horizonte",
    "remoto": "Remoto",
}


def resolve_city(value: str | None) -> str | None:
    """Whitelist the city (slug/canonical/label); anything else is ``None``."""
    if not value:
        return None
    return CITY_ALIASES.get(value.strip().lower())


def resolve_sort(value: str) -> str:
    """Only ``antigas`` changes the order; everything else is ``recentes``."""
    return "antigas" if value.strip().lower() == "antigas" else "recentes"
