from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
import uuid
from typing import Literal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.crud.jobs import (
    approve_job,
    delete_expired_jobs,
    delete_job,
    get_job,
    list_by_status,
    update_job,
)
from app.crud.social_accounts import get_facebook_account
from app.crud.social_posts import (
    get_by_job_provider,
    get_job_social_status_item,
    list_social_post_logs,
    list_social_status_items,
    mark_scheduled,
    upsert_draft,
)
from app.deps import get_session, require_admin, require_cron_secret
from app.models.job import JobStatus
from app.models.social_post import SocialPostStatus
from app.schemas.job import JobAdmin, JobAdminListResponse, JobApproveResponse, JobUpdate
from app.schemas.social_media import InstagramMediaPrepareResponse
from app.schemas.social_posts import (
    SocialApproveOutcome,
    SocialPostDraftRequest,
    SocialPostDraftResponse,
    SocialPostLogItem,
    SocialPostLogsResponse,
    SocialPostStatusItem,
    SocialPostStatusListResponse,
    SocialRetryResponse,
    SocialWorkerResponse,
)
from app.services.cities import resolve_city
from app.services.social.image_media import prepare_instagram_media
from app.services.social.post_generation import (
    ACTIONABLE_SITE_URL_ERROR,
    SocialPostLinkError,
    brt_wall_time_to_utc,
    build_public_job_link,
    generate_draft_for_job,
    generate_instagram_draft_for_job,
    now_utc,
    sanitize_and_enforce_policy,
)
from app.services.social.publish_pipeline import process_social_post_safe, run_social_publish_cycle


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me")
async def me(claims: dict = Depends(require_admin)) -> dict:
    """Return the decoded admin claims behind a valid Bearer token (ADMN-03)."""
    return {
        "sub": claims["sub"],
        "role": claims["role"],
        "iat": claims.get("iat"),
        "exp": claims.get("exp"),
    }


# ---------------------------------------------------------------------------
# REVW-01: GET /admin/jobs — list by status, city filter, pagination
# ---------------------------------------------------------------------------


@router.get("/jobs", response_model=JobAdminListResponse)
async def list_jobs(
    status: str = Query("pending"),
    city: str | None = Query(None, max_length=40),
    page: int = Query(1, ge=1, le=10_000),
    limit: int = Query(24, ge=1, le=100),
    sort: Literal["recentes", "antigas"] = Query("recentes"),
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdminListResponse:
    """List admin jobs filtered by status, city, pagination and sort.

    ``status`` default ``pending``; allowed ``pending`` / ``needs_review``.
    Unknown status or city → 422 (an admin filter must never fail open and
    silently return every city). Sort ``recentes`` (default) or ``antigas``
    with id tie-break. Returns ``JobAdminListResponse`` with contact +
    source_snippet.
    """
    if status not in ("pending", "needs_review"):
        raise HTTPException(status_code=422, detail="Status inválido")
    resolved_city = None
    if city:
        resolved_city = resolve_city(city)
        if resolved_city is None:
            raise HTTPException(status_code=422, detail="Cidade inválida")
    items, total = await list_by_status(
        session,
        JobStatus(status),
        page=page,
        limit=limit,
        city=resolved_city,
        sort=sort,
    )
    return JobAdminListResponse(
        items=[JobAdmin.model_validate(j) for j in items],
        page=page,
        limit=limit,
        total=total,
    )


# ---------------------------------------------------------------------------
# REVW-05: GET /admin/jobs/{job_id} — retrieve a job by ID
# ---------------------------------------------------------------------------


@router.get("/jobs/{job_id}", response_model=JobAdmin)
async def get_job_detail(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdmin:
    """Retrieve a job by ID (admin only, contact + source_snippet exposed)."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return JobAdmin.model_validate(job)


@router.post("/jobs/{job_id}/instagram/media/prepare", response_model=InstagramMediaPrepareResponse)
async def prepare_job_instagram_media(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> InstagramMediaPrepareResponse:
    """Prepare/validate the exact intended Instagram image for a job (IMAG-01/02/03)."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    result = await prepare_instagram_media(session, job_id, settings)
    await session.commit()
    return result


# ---------------------------------------------------------------------------
# REVW-02: PATCH /admin/jobs/{id}/approve — pending/needs_review → published
# ---------------------------------------------------------------------------


@router.patch("/jobs/{job_id}/approve", response_model=JobApproveResponse)
async def approve(
    job_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JobApproveResponse:
    """Approve a reviewable job: publica vaga no site e registra social best-effort."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    if job.status not in (JobStatus.pending, JobStatus.needs_review):
        raise HTTPException(
            status_code=409,
            detail="Vaga não está na fila de revisão",
        )

    ig_post = await get_by_job_provider(session, job_id, provider="instagram")
    if ig_post is not None and bool(getattr(ig_post, "publish_enabled", True)):
        ig_caption = (ig_post.text or "").strip()
        if len(ig_caption) > IG_CAPTION_MAX_CHARS:
            raise HTTPException(
                status_code=422,
                detail=(
                    "A legenda do Instagram excede 2200 caracteres. "
                    "Corrija ou desative a publicação no Instagram desta vaga para aprovar."
                ),
            )
        ig_media = await prepare_instagram_media(session, job_id, settings=settings)
        if not ig_media.validation.valid:
            raise HTTPException(
                status_code=422,
                detail=(
                    "A imagem do Instagram é inválida ou não está disponível. "
                    "Corrija ou desative a publicação no Instagram desta vaga para aprovar. "
                    "O Facebook e o site não são bloqueados."
                ),
            )

    # Site-first: sucesso da vaga independe do registro/dispatch social.
    await approve_job(session, job)
    await session.commit()
    await session.refresh(job)

    # Guarda os dados antes do processamento social, que pode executar rollback.
    job_response = JobAdmin.model_validate(job)

    social_outcome = SocialApproveOutcome(
        status="skipped",
        code="no_draft",
        message="Nenhum rascunho social salvo",
    )
    dispatch_post_ids: list[uuid.UUID] = []

    try:
        draft = await get_by_job_provider(
            session,
            job_id,
            provider="facebook",
        )

        if draft is None:
            social_outcome = SocialApproveOutcome(
                status="skipped",
                code="no_draft",
                message="Nenhum rascunho social salvo",
            )

        elif draft.status == SocialPostStatus.scheduled:
            social_outcome = SocialApproveOutcome(
                status="registered",
                code=None,
                message=None,
            )
            if draft.scheduled_at is not None and draft.scheduled_at <= now_utc():
                dispatch_post_ids.append(draft.id)

        elif draft.status == SocialPostStatus.draft:
            final_scheduled_at = (
                draft.scheduled_at
                if draft.scheduled_at is not None
                else now_utc()
            )

            await mark_scheduled(
                session,
                draft,
                text=draft.text,
                scheduled_at=final_scheduled_at,
            )
            await session.commit()

            social_outcome = SocialApproveOutcome(
                status="registered",
                code=None,
                message=None,
            )

            if final_scheduled_at <= now_utc():
                dispatch_post_ids.append(draft.id)

        else:
            social_outcome = SocialApproveOutcome(
                status="warning",
                code="social_registration_failed",
                message="Não foi possível registrar o post social agora",
            )

    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass

        social_outcome = SocialApproveOutcome(
            status="warning",
            code="social_registration_failed",
            message="Não foi possível registrar o post social agora",
        )

    # IG independent dispatch (D-06, PUBL-01): never affects FB/site outcome.
    try:
        ig_draft = await get_by_job_provider(
            session,
            job_id,
            provider="instagram",
        )
        if ig_draft is not None:
            if ig_draft.status == SocialPostStatus.scheduled:
                if ig_draft.scheduled_at is not None and ig_draft.scheduled_at <= now_utc():
                    dispatch_post_ids.append(ig_draft.id)
            elif ig_draft.status == SocialPostStatus.draft and bool(
                getattr(ig_draft, "publish_enabled", True)
            ):
                final_ig_scheduled_at = (
                    ig_draft.scheduled_at
                    if ig_draft.scheduled_at is not None
                    else now_utc()
                )
                await mark_scheduled(
                    session,
                    ig_draft,
                    text=ig_draft.text,
                    scheduled_at=final_ig_scheduled_at,
                )
                await session.commit()
                if final_ig_scheduled_at <= now_utc():
                    dispatch_post_ids.append(ig_draft.id)
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass

    for dispatch_post_id in dispatch_post_ids:
        try:
            background_tasks.add_task(
                process_social_post_safe,
                dispatch_post_id,
            )
        except Exception:
            pass

    return JobApproveResponse(
        job=job_response,
        social=social_outcome,
    )



# ---------------------------------------------------------------------------
# REVW-03: PUT /admin/jobs/{id} — edit all fields
# ---------------------------------------------------------------------------


@router.put("/jobs/{job_id}", response_model=JobAdmin)
async def update(
    job_id: uuid.UUID,
    payload: JobUpdate,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobAdmin:
    """Edit a job (partial update — only provided fields are applied).

    ``JobUpdate`` normalizes/validates title, city, email and phone before the
    DB. ``IntegrityError`` is the last-resort guard: only the contact CHECK
    maps to the contact message; anything else (NOT NULL, blank title) maps to
    a generic "Dados inválidos" instead of blaming the contact.
    """
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    try:
        await update_job(session, job, payload)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "at_least_one_contact" in str(exc.orig):
            raise HTTPException(
                status_code=422,
                detail="Vaga precisa ter ao menos um contato (email ou telefone)",
            ) from exc
        raise HTTPException(
            status_code=422, detail="Dados inválidos para a vaga"
        ) from exc
    await session.refresh(job)
    return JobAdmin.model_validate(job)


# ---------------------------------------------------------------------------
# REVW-04: DELETE /admin/jobs/{id} — hard delete
# ---------------------------------------------------------------------------


@router.delete("/jobs/{job_id}", status_code=204)
async def delete(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> None:
    """Hard delete a job."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    await delete_job(session, job)
    await session.commit()


# ---------------------------------------------------------------------------
# Phase 17: Worker cron, status/lista e retry manual (PUB-02..04, PUB-07, UI-01, UI-02)
# ---------------------------------------------------------------------------


def _facebook_account_status_value(account) -> object | None:
    return getattr(account, "status", None) if account is not None else None


@router.post("/social/worker", response_model=SocialWorkerResponse)
async def social_worker(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_cron_secret),
) -> SocialWorkerResponse:
    """Processa lote de posts sociais elegíveis (cron Render, idempotente)."""
    # `session` injetada para consistência de dependências; pipeline usa sessões próprias.
    _ = session
    counters = await run_social_publish_cycle() or {}
    defaults = {
        "claimed": 0,
        "processed": 0,
        "published": 0,
        "retried": 0,
        "failed_final": 0,
        "skipped": 0,
        "idempotent": 0,
    }
    defaults.update({k: int(v) for k, v in counters.items() if k in defaults})
    by_provider = counters.get("by_provider")
    return SocialWorkerResponse(status="ok", **defaults, by_provider=by_provider)


@router.get("/social-posts", response_model=SocialPostStatusListResponse)
async def list_social_posts(
    provider: Literal["facebook", "instagram"] | None = Query(None),
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialPostStatusListResponse:
    """Lista visão operacional simples de posts/vagas sociais (provider-aware)."""
    _ = claims
    account = await get_facebook_account(session)
    items = await list_social_status_items(
        session,
        account_status=_facebook_account_status_value(account),
        provider=provider,
    )
    return SocialPostStatusListResponse(items=items, total=len(items))


@router.get("/jobs/{job_id}/social-status", response_model=SocialPostStatusItem)
async def get_job_social_status(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialPostStatusItem:
    """Retorna status social seguro por vaga para revisão/edição."""
    _ = claims
    account = await get_facebook_account(session)
    item, job_exists = await get_job_social_status_item(
        session,
        job_id,
        account_status=_facebook_account_status_value(account),
        provider="facebook",
    )
    if not job_exists or item is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return item


def _safe_retry_provider(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"facebook", "instagram"}:
        return normalized
    return "__invalid__"


async def _retry_job_social_post_impl(
    *,
    job_id: uuid.UUID,
    provider: str | None,
    session: AsyncSession,
) -> SocialRetryResponse:
    fb_post = await get_by_job_provider(session, job_id, provider="facebook")
    ig_post = await get_by_job_provider(session, job_id, provider="instagram")
    existing = [p for p in (fb_post, ig_post) if p is not None]
    if not existing:
        job = await get_job(session, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        # Keep legacy-safe shape: no post => not eligible, no mutation.
        fb_account = await get_facebook_account(session)
        item, _ = await get_job_social_status_item(
            session,
            job_id,
            account_status=_facebook_account_status_value(fb_account),
            provider="facebook",
        )
        return SocialRetryResponse(
            outcome="not_eligible",
            item=item,
            message="Nenhum post social registrado para esta vaga.",
        )

    provider_norm = _safe_retry_provider(provider)
    if provider_norm == "__invalid__":
        raise HTTPException(status_code=400, detail="Provedor social inválido.")

    # Deterministic target resolution by post_id (job social_post row) and its provider.
    if len(existing) == 1:
        target_post = existing[0]
    else:
        if provider_norm is None:
            raise HTTPException(
                status_code=409,
                detail="Há publicações sociais para mais de um provedor nesta vaga. Informe o provedor para tentar novamente.",
            )
        target_post = fb_post if provider_norm == "facebook" else ig_post
        if target_post is None:
            raise HTTPException(
                status_code=409,
                detail="A publicação social solicitada não foi encontrada para este provedor.",
            )

    target_provider = (getattr(target_post, "provider", "") or "").strip().lower()
    if provider_norm is not None and provider_norm != target_provider:
        raise HTTPException(
            status_code=409,
            detail="O provedor informado não corresponde à publicação social resolvida. Nenhuma tentativa foi executada.",
        )
    if provider_norm is None and target_provider != "facebook":
        raise HTTPException(
            status_code=409,
            detail="Informe o provedor da publicação social para tentar novamente com segurança.",
        )

    fb_account = await get_facebook_account(session)
    account_status = _facebook_account_status_value(fb_account) if target_provider == "facebook" else None
    item, job_exists = await get_job_social_status_item(
        session,
        job_id,
        account_status=account_status,
        provider=target_provider,
    )
    if not job_exists or item is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    if item.status in {"published", "publishing"} or not item.can_retry:
        outcome = "noop" if item.status in {"published", "publishing"} else "not_eligible"
        return SocialRetryResponse(
            outcome=outcome,
            item=item,
            message=item.retry_block_reason or "Nenhuma nova tentativa necessária.",
        )

    # D-17/PUBL-04: IG reconciliation-required posts reuse this same retry action;
    # pipeline performs reconciliation-before-publish (ig_reconciliation_required).
    counters = await run_social_publish_cycle(post_id=target_post.id, limit=1) or {}
    refreshed_item, _ = await get_job_social_status_item(
        session,
        job_id,
        account_status=_facebook_account_status_value(await get_facebook_account(session)) if target_provider == "facebook" else None,
        provider=target_provider,
    )
    if refreshed_item is None:
        refreshed_item = item

    if counters.get("idempotent", 0) > 0 or refreshed_item.status in {"published", "publishing"}:
        outcome = "noop"
        message = "Nenhuma nova tentativa foi necessária. Status atualizado."
    elif counters.get("processed", 0) > 0 or counters.get("claimed", 0) > 0:
        outcome = "retried"
        message = "Nova tentativa iniciada/processada."
    else:
        outcome = "not_eligible"
        message = (
            refreshed_item.retry_block_reason
            or item.retry_block_reason
            or "Post não elegível para retry."
        )

    return SocialRetryResponse(outcome=outcome, item=refreshed_item, message=message)


@router.post("/jobs/{job_id}/social-post/retry", response_model=SocialRetryResponse)
async def retry_job_social_post(
    job_id: uuid.UUID,
    provider: Literal["facebook", "instagram"] | None = Query(None),
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialRetryResponse:
    """Retry manual idempotente para post social elegível da vaga (provider-aware)."""
    _ = claims
    return await _retry_job_social_post_impl(
        job_id=job_id,
        provider=provider,
        session=session,
    )


@router.post("/jobs/{job_id}/instagram/social-post/retry", response_model=SocialRetryResponse)
async def retry_job_instagram_social_post(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialRetryResponse:
    """Wrapper IG do retry provider-aware (compat/additive)."""
    _ = claims
    return await _retry_job_social_post_impl(
        job_id=job_id,
        provider="instagram",
        session=session,
    )


@router.get("/jobs/{job_id}/social-post/logs", response_model=SocialPostLogsResponse)
async def get_job_social_post_logs(
    job_id: uuid.UUID,
    provider: Literal["facebook", "instagram"] = Query("facebook"),
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialPostLogsResponse:
    """Retorna histórico seguro de auditoria do post social por vaga/provider."""
    _ = claims
    items, job_exists, _post_exists = await list_social_post_logs(
        session,
        job_id=job_id,
        provider=provider,
        limit=50,
    )
    if not job_exists:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return SocialPostLogsResponse(
        job_id=job_id,
        provider=provider,
        items=items,
        total=len(items),
    )


# ---------------------------------------------------------------------------
# POST-03/04/05/06: Social post draft (D-01..D-08, D-12, D-17)
# ---------------------------------------------------------------------------



def _draft_publish_mode(post) -> Literal["publish_now", "schedule"]:
    return "schedule" if getattr(post, "scheduled_at", None) is not None else "publish_now"


def _draft_response(
    post,
    *,
    origin: Literal["llm", "template_fallback"] = "template_fallback",
    warning: str | None = None,
) -> SocialPostDraftResponse:
    frozen = post.status != SocialPostStatus.draft
    return SocialPostDraftResponse(
        job_id=post.job_id,
        provider=post.provider or "facebook",
        status=post.status.value,
        text=post.text,
        publish_mode=_draft_publish_mode(post),
        publish_enabled=bool(getattr(post, "publish_enabled", True)),
        scheduled_at=post.scheduled_at,
        origin=origin,
        saved=True,
        frozen=frozen,
        warning=warning,
    )


def _resolve_draft_schedule(
    publish_mode: str,
    scheduled_date: str | None,
    scheduled_time: str | None,
):
    if publish_mode == "publish_now":
        return None
    if publish_mode == "schedule":
        if not scheduled_date or not scheduled_time:
            raise HTTPException(
                status_code=422,
                detail="Escolha uma data e hora válidas para agendar.",
            )
        try:
            return brt_wall_time_to_utc(scheduled_date, scheduled_time)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail="Escolha uma data e hora válidas para agendar.",
            ) from exc
    raise HTTPException(status_code=422, detail="Modo de publicação inválido.")


IG_CAPTION_MAX_CHARS = 2200
IG_CAPTION_TOO_LONG_DETAIL = "Legenda do Instagram deve ter no máximo 2200 caracteres."
IG_IMAGE_INVALID_DETAIL = (
    "Corrija a imagem do Instagram ou desative a publicação no Instagram desta vaga. "
    "O Facebook e o site não são bloqueados."
)


async def _validate_instagram_publish_ready(
    session: AsyncSession,
    job_id: uuid.UUID,
    settings: Settings,
    *,
    caption: str,
    publish_enabled: bool,
) -> None:
    if len(caption) > IG_CAPTION_MAX_CHARS:
        raise HTTPException(status_code=422, detail=IG_CAPTION_TOO_LONG_DETAIL)
    if publish_enabled:
        result = await prepare_instagram_media(session, job_id, settings)
        if not result.validation.valid:
            raise HTTPException(
                status_code=422,
                detail=result.validation.message or IG_IMAGE_INVALID_DETAIL,
            )


@router.get("/jobs/{job_id}/social-post", response_model=SocialPostDraftResponse)
async def get_job_social_post(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialPostDraftResponse:
    """Consulta rascunho social salvo por vaga/provider (facebook)."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    post = await get_by_job_provider(session, job_id, provider="facebook")
    if post is None:
        raise HTTPException(status_code=404, detail="Rascunho social não encontrado")
    return _draft_response(post)


@router.post(
    "/jobs/{job_id}/social-post/generate",
    response_model=SocialPostDraftResponse,
)
async def generate_job_social_post(
    job_id: uuid.UUID,
    payload: SocialPostDraftRequest | None = None,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> SocialPostDraftResponse:
    """Gera/regenera draft social sob demanda a partir do Job persistido (D-01..D-04)."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    existing = await get_by_job_provider(session, job_id, provider="facebook")
    if existing is not None and existing.status != SocialPostStatus.draft:
        raise HTTPException(status_code=409, detail="Texto aprovado e bloqueado para envio.")

    req = payload or SocialPostDraftRequest()
    scheduled_at = _resolve_draft_schedule(
        req.publish_mode, req.scheduled_date, req.scheduled_time
    )

    try:
        generated = await generate_draft_for_job(job, settings=settings)
    except SocialPostLinkError as exc:
        raise HTTPException(status_code=422, detail=ACTIONABLE_SITE_URL_ERROR) from exc

    try:
        post = await upsert_draft(
            session,
            job_id,
            text=generated.text,
            scheduled_at=scheduled_at,
            provider="facebook",
        )
    except ValueError as exc:
        if str(exc) == "frozen":
            raise HTTPException(
                status_code=409, detail="Texto aprovado e bloqueado para envio."
            ) from exc
        raise

    await session.commit()
    await session.refresh(post)
    return _draft_response(post, origin=generated.origin, warning=generated.warning)


@router.put("/jobs/{job_id}/social-post", response_model=SocialPostDraftResponse)
async def save_job_social_post(
    job_id: uuid.UUID,
    payload: SocialPostDraftRequest,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> SocialPostDraftResponse:
    """Salva explicitamente o draft social e modo/horário (D-08)."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    existing = await get_by_job_provider(session, job_id, provider="facebook")
    if existing is not None and existing.status != SocialPostStatus.draft:
        raise HTTPException(status_code=409, detail="Texto aprovado e bloqueado para envio.")

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="Texto do rascunho é obrigatório.")

    scheduled_at = _resolve_draft_schedule(
        payload.publish_mode, payload.scheduled_date, payload.scheduled_time
    )

    try:
        link = build_public_job_link(job_id, settings=settings)
    except SocialPostLinkError as exc:
        raise HTTPException(status_code=422, detail=ACTIONABLE_SITE_URL_ERROR) from exc

    safe_text = sanitize_and_enforce_policy(text, job, link=link, settings=settings)

    try:
        post = await upsert_draft(
            session,
            job_id,
            text=safe_text,
            scheduled_at=scheduled_at,
            provider="facebook",
        )
    except ValueError as exc:
        if str(exc) == "frozen":
            raise HTTPException(
                status_code=409, detail="Texto aprovado e bloqueado para envio."
            ) from exc
        raise

    await session.commit()
    await session.refresh(post)
    return _draft_response(post)


@router.get(
    "/jobs/{job_id}/instagram/social-post",
    response_model=SocialPostDraftResponse,
)
async def get_job_instagram_social_post(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialPostDraftResponse:
    """Consulta rascunho social Instagram salvo por vaga/provider (instagram)."""
    _ = claims
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    post = await get_by_job_provider(session, job_id, provider="instagram")
    if post is None:
        raise HTTPException(status_code=404, detail="Rascunho social não encontrado")
    return _draft_response(post)


@router.post(
    "/jobs/{job_id}/instagram/social-post/generate",
    response_model=SocialPostDraftResponse,
)
async def generate_job_instagram_social_post(
    job_id: uuid.UUID,
    payload: SocialPostDraftRequest | None = None,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> SocialPostDraftResponse:
    """Gera rascunho Instagram determinístico (template C) para revisão (D-01/D-02)."""
    _ = claims
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    existing = await get_by_job_provider(session, job_id, provider="instagram")
    if existing is not None and existing.status != SocialPostStatus.draft:
        raise HTTPException(status_code=409, detail="Texto aprovado e bloqueado para envio.")

    req = payload or SocialPostDraftRequest()
    scheduled_at = _resolve_draft_schedule(
        req.publish_mode, req.scheduled_date, req.scheduled_time
    )
    if req.publish_enabled is not None:
        effective_publish_enabled = bool(req.publish_enabled)
    elif existing is not None:
        effective_publish_enabled = bool(getattr(existing, "publish_enabled", True))
    else:
        effective_publish_enabled = False

    generated = await generate_instagram_draft_for_job(job, settings=settings)
    await _validate_instagram_publish_ready(
        session,
        job_id,
        settings,
        caption=generated.text,
        publish_enabled=effective_publish_enabled,
    )

    try:
        post = await upsert_draft(
            session,
            job_id,
            text=generated.text,
            scheduled_at=scheduled_at,
            provider="instagram",
            publish_enabled=effective_publish_enabled,
        )
    except ValueError as exc:
        if str(exc) == "frozen":
            raise HTTPException(
                status_code=409, detail="Texto aprovado e bloqueado para envio."
            ) from exc
        raise

    await session.commit()
    await session.refresh(post)
    return _draft_response(post, origin=generated.origin, warning=generated.warning)


@router.put(
    "/jobs/{job_id}/instagram/social-post",
    response_model=SocialPostDraftResponse,
)
async def save_job_instagram_social_post(
    job_id: uuid.UUID,
    payload: SocialPostDraftRequest,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> SocialPostDraftResponse:
    """Salva rascunho Instagram com validações de revisão (D-07/D-08/D-09)."""
    _ = claims
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    existing = await get_by_job_provider(session, job_id, provider="instagram")
    if existing is not None and existing.status != SocialPostStatus.draft:
        raise HTTPException(status_code=409, detail="Texto aprovado e bloqueado para envio.")

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="Texto do rascunho é obrigatório.")
    if len(text) > IG_CAPTION_MAX_CHARS:
        raise HTTPException(status_code=422, detail=IG_CAPTION_TOO_LONG_DETAIL)

    scheduled_at = _resolve_draft_schedule(
        payload.publish_mode, payload.scheduled_date, payload.scheduled_time
    )
    if payload.publish_enabled is not None:
        effective_publish_enabled = bool(payload.publish_enabled)
    elif existing is not None:
        effective_publish_enabled = bool(getattr(existing, "publish_enabled", True))
    else:
        effective_publish_enabled = False

    await _validate_instagram_publish_ready(
        session,
        job_id,
        settings,
        caption=text,
        publish_enabled=effective_publish_enabled,
    )

    try:
        post = await upsert_draft(
            session,
            job_id,
            text=text,
            scheduled_at=scheduled_at,
            provider="instagram",
            publish_enabled=effective_publish_enabled,
        )
    except ValueError as exc:
        if str(exc) == "frozen":
            raise HTTPException(
                status_code=409, detail="Texto aprovado e bloqueado para envio."
            ) from exc
        raise

    await session.commit()
    await session.refresh(post)
    return _draft_response(post)


@router.get(
    "/jobs/{job_id}/instagram/social-status",
    response_model=SocialPostStatusItem,
)
async def get_job_instagram_social_status(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> SocialPostStatusItem:
    """Retorna status social Instagram por vaga para revisão/admin."""
    _ = claims
    item, job_exists = await get_job_social_status_item(
        session,
        job_id,
        account_status=None,
        provider="instagram",
    )
    if not job_exists or item is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return item


# ---------------------------------------------------------------------------
# LIFE-04: POST /admin/expire — manual / catch-up expiry sweep (D-02)
# ---------------------------------------------------------------------------


@router.post("/expire")
async def expire_jobs(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_cron_secret),
) -> dict:
    """Hard delete every expired job and return how many rows went away.

    This is the same sweep the APScheduler clock runs at 03:00 UTC, exposed so
    a free-tier host that spun down (or an external cron service) can trigger
    the catch-up on demand (LIFE-04). It is authenticated by ``X-Cron-Secret``
    instead of the admin Bearer token: a cron caller has no admin session, and
    the two credentials must not be interchangeable (T-06-01).

    Idempotent: a second call with nothing expired answers ``deleted: 0``.

    Rate-limited per resolved IP (10/minute, IN-05) at the cron dependency
    (``require_cron_secret``) — slowapi cannot wrap this route's handler for
    the probe vector because FastAPI resolves dependencies first and the
    401/503 short-circuit would bypass the limit. Under the limit the
    503 (unconfigured) and 401 (wrong secret) semantics are unchanged; over
    the limit the caller gets the shared 429 (pt-BR, ``Retry-After``).
    """
    deleted = await delete_expired_jobs(session)
    await session.commit()
    return {"deleted": deleted, "status": "ok"}
