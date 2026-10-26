import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.client_ip import UNKNOWN_IP, resolve_client_ip
from app.core.ratelimit import limiter, reveal_limit
from app.crud import get_published, list_published
from app.db.session import get_session
from app.deps import get_turnstile_verifier
from app.schemas.job import (
    ContactRevealResponse,
    JobListResponse,
    JobPublic,
    RevealRequest,
)
from app.services.turnstile import TurnstileVerifier, turnstile_error_detail

# Mounted by router.py without an extra prefix, so these resolve to
# /api/v1/public/jobs and /api/v1/public/jobs/{id}. NO auth dependency:
# the public read surface is anonymous by design (D-16).
router = APIRouter(prefix="/public", tags=["public"])

# ``city`` aliases accepted from the URL (D-05/D-06b): the slug, the canonical
# DB spelling and the accented label all resolve to the value actually stored
# in ``jobs.city`` — which is the accented form of ``ALLOWED_CITIES`` in
# ``app/services/extraction/extractor.py``. Unknown values are ignored (200).
_CITY_ALIASES: dict[str, str] = {
    "sao-paulo": "São Paulo",
    "sao paulo": "São Paulo",
    "são paulo": "São Paulo",
    "rio-de-janeiro": "Rio de Janeiro",
    "rio de janeiro": "Rio de Janeiro",
    "belo-horizonte": "Belo Horizonte",
    "belo horizonte": "Belo Horizonte",
    "remoto": "Remoto",
}


def _resolve_city(value: str | None) -> str | None:
    """Whitelist the city (slug/canonical/label); anything else is ``None``."""
    if not value:
        return None
    return _CITY_ALIASES.get(value.strip().lower())


def _resolve_sort(value: str) -> str:
    """Only ``antigas`` changes the order; everything else is ``recentes``."""
    return "antigas" if value.strip().lower() == "antigas" else "recentes"


@router.get("/jobs", response_model=JobListResponse)
async def list_public_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    q: str | None = Query(None, max_length=80),
    city: str | None = Query(None, max_length=40),
    sort: str = Query("recentes", max_length=20),
    session: AsyncSession = Depends(get_session),
) -> JobListResponse:
    """List published, non-expired jobs (contact-free), filtered and sorted.

    ``q`` searches title + company + activities + requirements, accent- and
    case-insensitively (SRCH-01/D-03). ``city`` is an independent filter
    combined with AND — it never replaces ``q`` (SRCH-02/D-05). ``sort`` is
    ``recentes`` (default) or ``antigas`` (SRCH-03/D-06). Unknown ``city``
    values are ignored and unknown ``sort`` values fall back to ``recentes`` —
    a bad URL never produces a 400. Items and ``total`` share one predicate
    list (04-RESEARCH Pattern 3).
    """
    term = q.strip() if q else None
    if not term:
        term = None

    items, total = await list_published(
        session,
        page=page,
        limit=limit,
        q=term,
        city=_resolve_city(city),
        sort=_resolve_sort(sort),
    )
    return JobListResponse(
        items=[JobPublic.model_validate(job) for job in items],
        page=page,
        limit=limit,
        total=total,
    )



@router.get("/jobs/{job_id}", response_model=JobPublic)
async def get_public_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> JobPublic:
    """Return public detail for a published, non-expired job; 404 otherwise (D-17)."""
    # Phase boundary (D-18): no reveal/contact endpoint here — that is Phase 3.
    job = await get_published(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return JobPublic.model_validate(job)


@router.post("/jobs/{job_id}/reveal-contact", response_model=ContactRevealResponse)
@limiter.limit(reveal_limit)
async def reveal_contact(
    request: Request,
    job_id: uuid.UUID,
    payload: RevealRequest,
    session: AsyncSession = Depends(get_session),
    verifier: TurnstileVerifier = Depends(get_turnstile_verifier),
) -> ContactRevealResponse:
    """Reveal the contact of a published job behind the anti-bot gate.

    This is the **only** way a contact leaves the database (PUBL-05): the
    public list/detail stay contact-free.

    The order of the checks is the contract (D-03):

    1. **rate limit** — applied by the decorator, per resolved IP (D-05/D-10);
    2. **job lookup** — ``published`` and not expired, otherwise 404. It comes
       *before* the Turnstile call so a made-up UUID never spends a Cloudflare
       verification;
    3. **Siteverify** — the token is checked server-side, with the ``reveal``
       action binding (a token minted for ``login`` is refused);
    4. **200** — the contact, raw.

    A failed verification is **always** a 403, never a degraded 200 (D-13):
    the copy distinguishes "the challenge was refused" from "the verification
    itself is unavailable" (``turnstile_error_detail``).

    The Siteverify ``hostname`` is deliberately **not** checked: it changes
    between localhost and production, and the action binding already prevents
    a token from being reused across flows. Phase 4 must not invent that
    check.
    """
    job = await get_published(session, job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail="Vaga não encontrada ou expirada."
        )

    ip = resolve_client_ip(request)
    result = await verifier.verify(
        payload.cf_token,
        None if ip == UNKNOWN_IP else ip,
        expected_action="reveal",
        idempotency_key=str(uuid.uuid4()),
    )
    if not result.success:
        raise HTTPException(
            status_code=403, detail=turnstile_error_detail(result.error_codes)
        )

    return ContactRevealResponse(
        job_id=job.id,
        contact_email=job.contact_email,
        contact_phone=job.contact_phone,
    )
