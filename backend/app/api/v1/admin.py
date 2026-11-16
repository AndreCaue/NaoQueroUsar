from fastapi import APIRouter, Depends, HTTPException, Query
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
from app.crud.social_posts import get_by_job_provider, mark_scheduled, upsert_draft
from app.deps import get_session, require_admin, require_cron_secret
from app.models.job import JobStatus
from app.models.social_post import SocialPostStatus
from app.schemas.job import JobAdmin, JobAdminListResponse, JobApproveResponse, JobUpdate
from app.schemas.social_posts import (
    SocialApproveOutcome,
    SocialPostDraftRequest,
    SocialPostDraftResponse,
)
from app.services.cities import resolve_city
from app.services.social.post_generation import (
    ACTIONABLE_SITE_URL_ERROR,
    SocialPostLinkError,
    brt_wall_time_to_utc,
    build_public_job_link,
    generate_draft_for_job,
    now_utc,
    sanitize_and_enforce_policy,
)

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


# ---------------------------------------------------------------------------
# REVW-02: PATCH /admin/jobs/{id}/approve — pending/needs_review → published
# ---------------------------------------------------------------------------


@router.patch("/jobs/{job_id}/approve", response_model=JobApproveResponse)
async def approve(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> JobApproveResponse:
    """Approve a reviewable job: publica vaga no site e registra social best-effort (D-09..D-11)."""
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    if job.status not in (JobStatus.pending, JobStatus.needs_review):
        raise HTTPException(
            status_code=409, detail="Vaga não está na fila de revisão"
        )

    # Site-first: sucesso da vaga independe do registro social.
    await approve_job(session, job)
    await session.commit()
    await session.refresh(job)

    social_outcome = SocialApproveOutcome(
        status="skipped",
        code="no_draft",
        message="Nenhum rascunho social salvo",
    )

    try:
        draft = await get_by_job_provider(session, job_id, provider="facebook")
        if draft is None:
            social_outcome = SocialApproveOutcome(
                status="skipped",
                code="no_draft",
                message="Nenhum rascunho social salvo",
            )
        elif draft.status == SocialPostStatus.scheduled:
            social_outcome = SocialApproveOutcome(status="registered", code=None, message=None)
        elif draft.status == SocialPostStatus.draft:
            final_scheduled_at = draft.scheduled_at if draft.scheduled_at is not None else now_utc()
            await mark_scheduled(
                session,
                draft,
                text=draft.text,
                scheduled_at=final_scheduled_at,
            )
            await session.commit()
            social_outcome = SocialApproveOutcome(status="registered", code=None, message=None)
        else:
            # Estados não-draft e não-scheduled não são registráveis como aprovação atual
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

    return JobApproveResponse(job=JobAdmin.model_validate(job), social=social_outcome)


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
        provider="facebook",
        status=post.status.value,
        text=post.text,
        publish_mode=_draft_publish_mode(post),
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
