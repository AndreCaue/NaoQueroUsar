from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from app.core.config import get_settings

from .publisher import SocialPublisher
from .types import PublishFailureCategory, PublishResult, SocialPostPayload

_GENERIC_PERMANENT_ERROR = (
    "Não foi possível publicar no Instagram. Revise a integração ou o conteúdo e tente novamente."
)
_TRANSIENT_ERROR = "Falha temporária ao publicar no Instagram. Uma nova tentativa será feita automaticamente."
_AMBIGUOUS_ERROR = (
    "Não foi possível confirmar a publicação no Instagram. Verifique antes de tentar novamente para evitar duplicidade."
)
_RATE_LIMIT_ERROR = (
    "O Instagram bloqueou temporariamente novas publicações por limite da plataforma. "
    "Aguarde e tente novamente mais tarde."
)
_CONTENT_LIMIT_ERROR = (
    "O limite diário de publicação do Instagram foi atingido. "
    "Aguarde a janela da plataforma antes de tentar novamente."
)


def _safe_text(value: str | None, max_len: int = 500) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lower = text.lower()
    if "access_token" in lower or "token=" in lower or "bearer " in lower:
        return _GENERIC_PERMANENT_ERROR
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def _extract_graph_error(body: Any) -> dict[str, Any]:
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            return err
    return {}


def _is_rate_limit_error(*, status_code: int | None, body: Any) -> tuple[bool, str | None]:
    err = _extract_graph_error(body)
    code = err.get("code")
    subcode = err.get("error_subcode")
    msg = str(err.get("message") or "").lower()
    err_type = str(err.get("type") or "").lower()
    user_title = str(err.get("error_user_title") or "").lower()
    user_msg = str(err.get("error_user_msg") or "").lower()
    blob = " ".join([msg, err_type, user_title, user_msg])

    if (
        code == 2207042
        or subcode == 2207042
        or "2207042" in blob
        or "content_publishing_limit" in blob
        or "content publishing limit" in blob
    ):
        return True, "ig_content_publishing_limit"
    if status_code == 429:
        return True, "ig_rate_limit_blocked"
    if "rate limit" in blob or "application request limit" in blob or "user request limit" in blob:
        return True, "ig_rate_limit_blocked"
    # Common IG publishing throttle codes/messages can be surfaced as code 4/32/613 etc.
    if code in {4, 17, 32, 613} and ("limit" in blob or "too many" in blob or "rate" in blob):
        return True, "ig_rate_limit_blocked"
    return False, None


def _rate_limit_result(
    *,
    error_code: str | None,
    container_id: str | None = None,
    published_media_id: str | None = None,
) -> PublishResult:
    code = error_code or "ig_rate_limit_blocked"
    msg = _CONTENT_LIMIT_ERROR if code == "ig_content_publishing_limit" else _RATE_LIMIT_ERROR
    return PublishResult(
        ok=False,
        category=PublishFailureCategory.permanent,
        error_message=msg,
        container_id=container_id,
        published_media_id=published_media_id,
        error_code=code,
    )


def _is_transient_status(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


class InstagramPublisher(SocialPublisher):
    """Publisher Instagram via Graph API (2-step: container + publish)."""

    async def publish(self, post: SocialPostPayload | object | None = None) -> PublishResult:
        if not isinstance(post, SocialPostPayload):
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

        provider = str(getattr(post, "provider", "") or "").strip().lower()
        message = (post.message or "").strip()
        image_url = str(getattr(post, "image_url", "") or "").strip()
        ig_user_id = str(getattr(post, "ig_user_id", "") or "").strip()
        page_access_token = str(getattr(post, "page_access_token", "") or "")
        if provider != "instagram" or not message or not image_url or not ig_user_id or not page_access_token:
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

        settings = get_settings()
        graph_version = str(getattr(settings, "META_GRAPH_VERSION", "v21.0") or "v21.0").strip() or "v21.0"
        http_timeout = float(getattr(settings, "IG_PUBLISH_HTTP_TIMEOUT_SECONDS", 20.0) or 20.0)
        max_poll_attempts = max(1, int(getattr(settings, "IG_STATUS_POLL_MAX_ATTEMPTS", 5) or 5))
        poll_delay = max(0.0, float(getattr(settings, "IG_STATUS_POLL_DELAY_SECONDS", 2.0) or 2.0))
        max_attempt_seconds = float(getattr(settings, "IG_PUBLISH_MAX_ATTEMPT_SECONDS", 45.0) or 45.0)
        deadline = time.monotonic() + max_attempt_seconds

        base = f"https://graph.facebook.com/{graph_version}"
        container_id: str | None = None
        published_media_id: str | None = None

        def _budget_exceeded() -> bool:
            return time.monotonic() >= deadline

        try:
            async with httpx.AsyncClient(timeout=http_timeout) as client:
                # Step 1: create container
                try:
                    create_resp = await client.post(
                        f"{base}/{ig_user_id}/media",
                        data={
                            "image_url": image_url,
                            "caption": message,
                            "access_token": page_access_token,
                        },
                    )
                except httpx.TimeoutException:
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.ambiguous,
                        error_message=_AMBIGUOUS_ERROR,
                        container_id=container_id,
                        error_code="ig_timeout_ambiguous",
                    )
                except httpx.RequestError:
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.transient,
                        error_message=_TRANSIENT_ERROR,
                        container_id=container_id,
                    )

                create_body = _safe_json(create_resp)
                is_rl, rl_code = _is_rate_limit_error(status_code=create_resp.status_code, body=create_body)
                if is_rl:
                    return _rate_limit_result(error_code=rl_code, container_id=container_id)

                if create_resp.status_code < 400 and isinstance(create_body, dict) and create_body.get("id"):
                    container_id = str(create_body["id"])
                elif _is_transient_status(create_resp.status_code):
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.transient,
                        error_message=_TRANSIENT_ERROR,
                        container_id=container_id,
                    )
                elif create_resp.status_code >= 400:
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.permanent,
                        error_message=_GENERIC_PERMANENT_ERROR,
                        container_id=container_id,
                    )
                else:
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.ambiguous,
                        error_message=_AMBIGUOUS_ERROR,
                        container_id=container_id,
                    )

                # Step 1b: status check / bounded polling (D-11/D-15)
                status_code = await self._wait_container_ready(
                    client,
                    base=base,
                    container_id=container_id,
                    access_token=page_access_token,
                    max_poll_attempts=max_poll_attempts,
                    poll_delay=poll_delay,
                    deadline=deadline,
                )
                if status_code["kind"] == "rate_limit":
                    return _rate_limit_result(
                        error_code=status_code.get("error_code"),
                        container_id=container_id,
                    )
                if status_code["kind"] == "ambiguous":
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.ambiguous,
                        error_message=_AMBIGUOUS_ERROR,
                        container_id=container_id,
                        error_code="ig_status_ambiguous",
                    )
                if status_code["kind"] == "transient":
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.transient,
                        error_message=_TRANSIENT_ERROR,
                        container_id=container_id,
                    )
                if status_code["kind"] == "error":
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.permanent,
                        error_message=_GENERIC_PERMANENT_ERROR,
                        container_id=container_id,
                        error_code=status_code.get("error_code"),
                    )
                # FINISHED

                if _budget_exceeded():
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.ambiguous,
                        error_message=_AMBIGUOUS_ERROR,
                        container_id=container_id,
                        error_code="ig_budget_ambiguous",
                    )

                # Step 2: publish container
                try:
                    publish_resp = await client.post(
                        f"{base}/{ig_user_id}/media_publish",
                        data={
                            "creation_id": container_id,
                            "access_token": page_access_token,
                        },
                    )
                except httpx.TimeoutException:
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.ambiguous,
                        error_message=_AMBIGUOUS_ERROR,
                        container_id=container_id,
                        error_code="ig_publish_timeout_ambiguous",
                    )
                except httpx.RequestError:
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.ambiguous,
                        error_message=_AMBIGUOUS_ERROR,
                        container_id=container_id,
                        error_code="ig_publish_request_ambiguous",
                    )

                publish_body = _safe_json(publish_resp)
                is_rl, rl_code = _is_rate_limit_error(status_code=publish_resp.status_code, body=publish_body)
                if is_rl:
                    return _rate_limit_result(error_code=rl_code, container_id=container_id)

                if publish_resp.status_code < 400 and isinstance(publish_body, dict) and publish_body.get("id"):
                    published_media_id = str(publish_body["id"])
                elif _is_transient_status(publish_resp.status_code):
                    # publish step is critical - unknown if accepted
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.ambiguous,
                        error_message=_AMBIGUOUS_ERROR,
                        container_id=container_id,
                        error_code="ig_publish_http_ambiguous",
                    )
                elif publish_resp.status_code >= 400:
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.permanent,
                        error_message=_GENERIC_PERMANENT_ERROR,
                        container_id=container_id,
                        error_code="ig_publish_failed",
                    )
                else:
                    return PublishResult(
                        ok=False,
                        category=PublishFailureCategory.ambiguous,
                        error_message=_AMBIGUOUS_ERROR,
                        container_id=container_id,
                        error_code="ig_publish_ambiguous",
                    )

                # Step 3: best-effort permalink (D-16)
                permalink = await self._fetch_permalink_best_effort(
                    client,
                    base=base,
                    media_id=published_media_id,
                    access_token=page_access_token,
                )
                return PublishResult(
                    ok=True,
                    external_post_id=published_media_id,
                    container_id=container_id,
                    published_media_id=published_media_id,
                    permalink=permalink,
                )
        except Exception:
            # Any unexpected failure after critical step is ambiguous if container exists.
            if container_id:
                return PublishResult(
                    ok=False,
                    category=PublishFailureCategory.ambiguous,
                    error_message=_AMBIGUOUS_ERROR,
                    container_id=container_id,
                    published_media_id=published_media_id,
                    error_code="ig_unexpected_ambiguous",
                )
            return PublishResult(
                ok=False,
                category=PublishFailureCategory.permanent,
                error_message=_GENERIC_PERMANENT_ERROR,
            )

    async def _wait_container_ready(
        self,
        client: httpx.AsyncClient,
        *,
        base: str,
        container_id: str,
        access_token: str,
        max_poll_attempts: int,
        poll_delay: float,
        deadline: float,
    ) -> dict[str, Any]:
        attempts = 0
        while True:
            if time.monotonic() >= deadline:
                return {"kind": "ambiguous", "error_code": "ig_budget_ambiguous"}
            attempts += 1
            try:
                resp = await client.get(
                    f"{base}/{container_id}",
                    params={"fields": "status_code,status,id", "access_token": access_token},
                )
            except httpx.TimeoutException:
                return {"kind": "ambiguous", "error_code": "ig_status_timeout_ambiguous"}
            except httpx.RequestError:
                # status unknown; if we have container, caller should treat as ambiguous
                return {"kind": "ambiguous", "error_code": "ig_status_request_ambiguous"}

            body = _safe_json(resp)
            is_rl, rl_code = _is_rate_limit_error(status_code=resp.status_code, body=body)
            if is_rl:
                return {"kind": "rate_limit", "error_code": rl_code}
            if _is_transient_status(resp.status_code):
                if attempts >= max_poll_attempts or time.monotonic() >= deadline:
                    return {"kind": "ambiguous", "error_code": "ig_status_transient_ambiguous"}
                await asyncio.sleep(min(poll_delay, max(0.0, deadline - time.monotonic())))
                continue
            if resp.status_code >= 400:
                return {"kind": "error", "error_code": "ig_status_http_error"}

            status = ""
            if isinstance(body, dict):
                status = str(body.get("status_code") or body.get("status") or "").upper().strip()
            if status == "FINISHED":
                return {"kind": "finished"}
            if status == "PUBLISHED":
                # container already published; let publish step be reconciled by caller? For normal flow, treat as finished/published handled.
                return {"kind": "finished", "status": status}
            if status in {"ERROR", "EXPIRED"}:
                return {"kind": "error", "error_code": f"ig_container_{status.lower()}"}
            if status == "IN_PROGRESS" or not status:
                if attempts >= max_poll_attempts or time.monotonic() >= deadline:
                    return {"kind": "ambiguous", "error_code": "ig_status_inconclusive"}
                await asyncio.sleep(min(poll_delay, max(0.0, deadline - time.monotonic())))
                continue
            # Unknown status - be conservative
            if attempts >= max_poll_attempts or time.monotonic() >= deadline:
                return {"kind": "ambiguous", "error_code": "ig_status_unknown"}
            await asyncio.sleep(min(poll_delay, max(0.0, deadline - time.monotonic())))

    async def _fetch_permalink_best_effort(
        self,
        client: httpx.AsyncClient,
        *,
        base: str,
        media_id: str,
        access_token: str,
    ) -> str | None:
        try:
            resp = await client.get(
                f"{base}/{media_id}",
                params={"fields": "id,permalink", "access_token": access_token},
            )
        except Exception:
            return None
        body = _safe_json(resp)
        if resp.status_code < 400 and isinstance(body, dict):
            permalink = body.get("permalink")
            if isinstance(permalink, str) and permalink.strip():
                return _safe_text(permalink.strip(), 500)
        return None


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None
