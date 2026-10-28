"""Public (contact-free) job schemas.

D-15: the public list/detail return every field EXCEPT the contact.
D-18: contact is NEVER in a public payload — the reveal is a dedicated
Phase 3 endpoint. These schemas are the structural enforcement of that
rule (PITFALLS 7): they deliberately declare no ``contact_email`` /
``contact_phone`` fields, so even if a caller passes a full ``Job`` ORM
object, ``model_validate`` cannot leak the contact into the response.

The reveal schemas at the end of this module (``RevealRequest`` and
``ContactRevealResponse``) are the **only** place in the project where the
contact fields exist (Phase 3, PUBL-05): the read surface stays contact-free
and the contact only leaves the database through the reveal endpoint.

Admin schemas (below) expose contact + source_snippet because the routes
are guarded by ``require_admin`` — contact is only visible behind auth.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from app.models.job import JobStatus


class JobPublic(BaseModel):
    """A published, non-expired job with NO contact fields (D-15, D-18)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str | None = None
    activities: str | None = None
    requirements: str | None = None
    salary: str | None = None
    benefits: str | None = None
    city: str
    status: JobStatus
    created_at: datetime
    expires_at: datetime
    # NO contact_email / contact_phone (D-18).


class JobListResponse(BaseModel):
    """Offset-paginated envelope with a total count (D-14)."""

    items: list[JobPublic]
    page: int
    limit: int
    total: int


class RevealRequest(BaseModel):
    """Body of the contact-reveal request (Phase 3, SECR-01).

    ``cf_token`` is the Turnstile token minted by the browser. It is verified
    **server-side** against Cloudflare before the contact is released — a
    client-side check would be bypassed by any scraper (PITFALLS 7).
    """

    cf_token: str = Field(min_length=1, max_length=2048)


class ContactRevealResponse(BaseModel):
    """The contact of a revealed job (Phase 3, PUBL-05).

    The phone comes back raw (E.164, as stored in Phase 2): the ``wa.me`` and
    ``mailto`` links are assembled by the frontend in Phase 4.

    ``job_id`` is part of the answer so the frontend can keep the revealed
    contact **in memory, per job**, while the tab is open (D-04) — reopening
    the same job shows the contact without asking for a new token.
    """

    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    contact_email: str | None = None
    contact_phone: str | None = None


class JobAdmin(BaseModel):
    """Admin-facing job schema with contact + source_snippet exposure.

    Contact fields are allowed here because the route is guarded by
    ``require_admin`` (Pitfall 1: contact never leaks into public payload).
    Used for ``GET /admin/jobs`` and mutation responses.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str | None = None
    activities: str | None = None
    requirements: str | None = None
    salary: str | None = None
    benefits: str | None = None
    city: str
    status: JobStatus
    contact_email: str | None = None
    contact_phone: str | None = None
    source_snippet: str | None = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


class JobUpdate(BaseModel):
    """Partial update schema for job fields via PUT /admin/jobs/{id}.

    All fields are optional — only provided fields are applied.
    City validation against allowed set is enforced via Literal (fails fast
    before DB) and normalized to canonical accented form.
    At least one contact (email or phone) must remain non-empty — enforced
    by DB CHECK and caught as ``422`` via ``IntegrityError``.
    """

    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=150)
    activities: str | None = Field(default=None)
    requirements: str | None = Field(default=None)
    salary: str | None = Field(default=None, max_length=80)
    benefits: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None)
    contact_email: str | None = Field(default=None, max_length=254)
    contact_phone: str | None = Field(default=None, max_length=30)

    @classmethod
    def _resolve_city(cls, value: str | None) -> str | None:
        """Resolve city slug/label to canonical accented form."""
        if not value:
            return None
        aliases: dict[str, str] = {
            "sao-paulo": "São Paulo",
            "sao paulo": "São Paulo",
            "são paulo": "São Paulo",
            "rio-de-janeiro": "Rio de Janeiro",
            "rio de janeiro": "Rio de Janeiro",
            "belo-horizonte": "Belo Horizonte",
            "belo horizonte": "Belo Horizonte",
            "remoto": "Remoto",
        }
        return aliases.get(value.strip().lower())

    @classmethod
    def _validate_at_least_one_contact(cls, values: dict) -> dict:
        """Pydantic model_validator: require at least one contact."""
        contact_email = values.get("contact_email")
        contact_phone = values.get("contact_phone")
        if not contact_email and not contact_phone:
            raise ValueError("Vaga precisa ter ao menos um contato (email ou telefone)")
        return values


class JobAdminListResponse(BaseModel):
    """Offset-paginated envelope for admin job list (D-14)."""

    items: list[JobAdmin]
    page: int
    limit: int
    total: int
