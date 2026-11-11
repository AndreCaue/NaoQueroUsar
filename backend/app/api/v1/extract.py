"""Admin extraction endpoint (D-01, D-02, D-03, D-04, D-05, D-07, D-08).

Synchronous in-request extraction per D-01: the handler calls
``extract_jobs`` inside ``asyncio.timeout(EXTRACT_TIMEOUT_SECONDS)`` and
returns the completed ``ExtractSummaryResponse`` on success, or a pt-BR 504
on timeout. No background job and no polling.

Persistence is exactly one transaction (D-03): ``bulk_create_pending``
only flushes; this module performs a single ``await session.commit()``
after inserting all ``result.kept`` rows. If commit fails the session is
rolled back and the response becomes a pt-BR 500 with "nada foi gravado".
Discarded rows are never inserted (D-05) but are returned in the summary.
"""

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.crud.jobs import bulk_create_pending
from app.db.session import get_session
from app.deps import require_admin
from app.models.job import JobStatus
from app.schemas.extract import (
    ALERT_DISCARDED,
    ALERT_DIVERGENCE,
    ALERT_MAX_JOBS,
    ALERT_TRUNCATED,
    DiscardedJob,
    ExtractRequest,
    ExtractSummaryResponse,
)
from app.services.extraction.blocklist import TERM_REMOVED_ALERT, strip_blocked_terms
from app.services.extraction.client import ExtractionAPIError
from app.services.extraction.extractor import CandidateOutcome, extract_jobs

router = APIRouter(prefix="/admin", tags=["admin-extract"])


def _outcome_to_status(outcome: CandidateOutcome) -> JobStatus:
    if outcome == CandidateOutcome.save:
        return JobStatus.pending
    if outcome == CandidateOutcome.save_needs_review:
        return JobStatus.needs_review
    # Should not happen because discarded rows are never passed to persistence.
    return JobStatus.invalid


@router.post("/extract", response_model=ExtractSummaryResponse)
async def extract_admin(
    payload: ExtractRequest,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> ExtractSummaryResponse:
    settings = get_settings()

    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Serviço de extração indisponível — GROQ_API_KEY não configurado.",
        )

    text_bytes = payload.text.encode("utf-8")
    if len(text_bytes) > settings.EXTRACT_MAX_TEXT_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                "Texto muito grande — limite de "
                f"{settings.EXTRACT_MAX_TEXT_BYTES} bytes. "
                "Cole um trecho menor ou divida o envio."
            ),
        )

    cleaned_text = strip_blocked_terms(payload.text)
    if not cleaned_text.strip():
        # O texto era só o termo removido — nada para extrair. Mensagem
        # própria (não confundir com corpo vazio do Pydantic) e sem Groq.
        raise HTTPException(
            status_code=422,
            detail=(
                "O texto continha apenas o termo removido — "
                "cole o conteúdo da vaga."
            ),
        )

    term_removed = cleaned_text != payload.text

    try:
        async with asyncio.timeout(settings.EXTRACT_TIMEOUT_SECONDS):
            result = await extract_jobs(cleaned_text, settings)
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Extração excedeu o tempo limite — tente com um texto menor",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ExtractionAPIError as exc:
        # WR-02: the client already carries a curated pt-BR message (rate limit,
        # dead model, bad key…). 503 = upstream (Groq) unavailable.
        raise HTTPException(status_code=503, detail=exc.detail) from exc

    rows: list[dict[str, Any]] = []
    for candidate, outcome in result.kept:
        rows.append(
            {
                "title": candidate.title,
                "company": candidate.company,
                "activities": candidate.activities,
                "requirements": candidate.requirements,
                "salary": candidate.salary,
                "benefits": candidate.benefits,
                "city": candidate.city,
                "contact_email": candidate.contact_email,
                "contact_phone": candidate.contact_phone,
                "status": _outcome_to_status(outcome),
                "source_snippet": candidate.source_snippet,
            }
        )

    if rows:
        try:
            await bulk_create_pending(session, rows)
            await session.commit()
        except Exception as exc:
            await session.rollback()
            raise HTTPException(
                status_code=500,
                detail="Falha ao salvar — nada foi gravado, tente novamente",
            ) from exc
    # If there are no rows to persist, we still return the summary with
    # zero saved counts (and no commit needed).

    saved_pending = sum(1 for _, outcome in result.kept if outcome == CandidateOutcome.save)
    saved_needs_review = sum(
        1 for _, outcome in result.kept if outcome == CandidateOutcome.save_needs_review
    )

    discarded_list = [
        DiscardedJob(reason=d.get("reason", ""), snippet=d.get("snippet", ""))
        for d in result.discarded
    ]

    alerts: list[str] = []
    if term_removed:
        alerts.append(TERM_REMOVED_ALERT)
    if result.divergent and result.detected_count is not None:
        alerts.append(
            ALERT_DIVERGENCE.format(
                detected_count=result.detected_count,
                extracted_count=result.extracted_count,
            )
        )
    if result.truncated:
        alerts.append(ALERT_TRUNCATED)
    if discarded_list:
        alerts.append(ALERT_DISCARDED.format(n=len(discarded_list)))
    # Surface the "excedeu o limite" overflow as a separate alert when present.
    if any(
        (d.get("reason") == "excedeu o limite" or "limite" in (d.get("reason") or "").lower())
        for d in result.discarded
    ):
        # Avoid duplicating if the count alert already implies it; append when
        # the overflow marker is the distinguishing case.
        if ALERT_MAX_JOBS not in alerts:
            alerts.append(ALERT_MAX_JOBS)

    return ExtractSummaryResponse(
        saved_pending=saved_pending,
        saved_needs_review=saved_needs_review,
        discarded=discarded_list,
        divergent=result.divergent,
        detected_count=result.detected_count,
        extracted_count=result.extracted_count,
        truncated=result.truncated,
        model_used=result.model_used,
        chunks=result.chunks,
        alerts=alerts,
    )
