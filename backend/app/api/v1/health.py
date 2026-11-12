from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
def health():
    """Liveness probe — public, so it reports *status*, never secrets (D-14).

    The ``turnstile`` block answers the operational question "is the anti-spam
    protection actually on?": ``mode`` tells whether the effective secret is a
    real one (``live``), one of Cloudflare's public test keys (``test``) or
    missing altogether (``disabled``), and ``configured``/``site_key_configured``
    are plain booleans. ``test_override`` indicam se o operador ligou o escape
    hatch ``ALLOW_TEST_TURNSTILE`` (chave de teste aceita fora de dev). The
    secret itself never leaves the backend (T-03-06).
    """
    settings = get_settings()
    secret = settings.effective_turnstile_secret

    return {
        "status": "ok",
        "env": settings.ENV,
        "turnstile": {
            "configured": bool(secret),
            "mode": settings.turnstile_mode,
            "site_key_configured": bool(settings.TURNSTILE_SITE_KEY.strip()),
            # Escape hatch explícito: ``true`` só aparece quando o operador
            # religou ENV=prod com uma chave de TESTE do Cloudflare
            # (ALLOW_TEST_TURNSTILE=true). Nunca revela a chave em si.
            "test_override": settings.ALLOW_TEST_TURNSTILE,
        },
    }
