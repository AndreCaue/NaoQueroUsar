from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings

from .publisher import SocialPublisher
from .types import PublishFailureCategory, PublishResult, SocialPostPayload

_GENERIC_PERMANENT_ERROR = (
    "Não foi possível publicar este post. Revise a integração ou o conteúdo e tente novamente."
)
_TRANSIENT_ERROR = "Falha temporária ao publicar. Uma nova tentativa será feita automaticamente."
_AMBIGUOUS_ERROR = (
    "Não foi possível confirmar a publicação. Verifique antes de tentar novamente para evitar duplicidade."
)


def _is_definitive_graph_error(status_code: int, body: Any) -> bool:
    if status_code not in {400, 401, 403}:
        return False
    if not isinstance(body, dict):
        return False
    err = body.get("error")
    if not isinstance(err, dict):
        return False
    code = err.get("code")
    err_subcode = err.get("error_subcode")
    err_type = str(err.get("type") or "").lower()
    msg = str(err.get("message") or "").lower()
    # Heurística segura para erros definitivos comuns de auth/permissão/conteúdo/request.
    definitive_codes = {100, 102, 190, 200, 10, 2500}
    if code in definitive_codes or err_subcode in {458, 459, 460, 463, 467, 492}:
        return True
    if err_type in {"oauthexception", "graphmethodexception"} and status_code in {401, 403}:
        return True
    keywords = (
        "permission",
        "permissions",
        "access token",
        "invalid parameter",
        "unsupported post request",
        "duplicate",
        "content",
    )
    return any(k in msg for k in keywords)


class FacebookPublisher(SocialPublisher):
    """Publisher real do Facebook via Graph API (backend-only)."""

    async def publish(self, post: SocialPostPayload | object | None = None) -> PublishResult:
        if not isinstance(post, SocialPostPayload):
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

        message = (post.message or "").strip()
        page_id = (post.page_id or "").strip()
        page_access_token = post.page_access_token or ""
        if not message or not page_id or not page_access_token:
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

        settings = get_settings()
        url = f"https://graph.facebook.com/{settings.META_GRAPH_VERSION}/{page_id}/feed"
        data: dict[str, str] = {"message": post.message, "access_token": page_access_token}
        if post.link:
            data["link"] = post.link

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, data=data)
        except httpx.TimeoutException:
            # Timeout antes/depois do envio é tratado como ambíguo por segurança (D-11).
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.ambiguous,
                error_message=_AMBIGUOUS_ERROR,
            )
        except httpx.RequestError:
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.transient,
                error_message=_TRANSIENT_ERROR,
            )

        try:
            body = response.json()
        except ValueError:
            body = None

        if response.status_code < 400 and isinstance(body, dict) and body.get("id"):
            return PublishResult(ok=True, external_post_id=str(body["id"]))

        if response.status_code == 429 or response.status_code >= 500:
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.transient,
                error_message=_TRANSIENT_ERROR,
            )

        if _is_definitive_graph_error(response.status_code, body):
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

        # Resposta de erro não conclusiva: pode ser ambígua; evitar auto-retry agressivo.
        if 400 <= response.status_code < 500:
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

        return PublishResult(
            ok=False,
            category=PublishFailureCategory.ambiguous,
            error_message=_AMBIGUOUS_ERROR,
        )
