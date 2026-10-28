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

import re
import uuid
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.job import JobStatus
from app.services.cities import resolve_city


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

    All fields are optional — only provided fields are applied. ``title`` and
    ``city`` cannot be blanked and ``city`` is normalized to its canonical
    accented form (slug/label/canonical all accepted). Contact fields are
    trimmed, format-checked and empty strings collapse to ``None``; clearing
    both contacts in one payload is rejected here, and the DB CHECK remains
    the final guard for a partial clear.
    """

    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=150)
    activities: str | None = Field(default=None)
    requirements: str | None = Field(default=None)
    salary: str | None = Field(default=None, max_length=80)
    benefits: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=80)
    contact_email: str | None = Field(default=None, max_length=254)
    contact_phone: str | None = Field(default=None, max_length=30)

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Título é obrigatório")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Título é obrigatório")
        return stripped

    @field_validator("city")
    @classmethod
    def _resolve_city_field(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Cidade é obrigatória")
        resolved = resolve_city(value)
        if resolved is None:
            raise ValueError("Cidade inválida")
        return resolved

    @field_validator("contact_email")
    @classmethod
    def _validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", stripped):
            raise ValueError("E-mail inválido")
        return stripped

    @field_validator("contact_phone")
    @classmethod
    def _validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if len(re.sub(r"\D", "", stripped)) < 8:
            raise ValueError("Telefone inválido")
        return stripped

    @model_validator(mode="after")
    def _at_least_one_contact(self) -> "JobUpdate":
        provided = self.model_fields_set
        if "contact_email" in provided and "contact_phone" in provided:
            if self.contact_email is None and self.contact_phone is None:
                raise ValueError(
                    "Vaga precisa ter ao menos um contato (email ou telefone)"
                )
        return self


class JobAdminListResponse(BaseModel):
    """Offset-paginated envelope for admin job list (D-14)."""

    items: list[JobAdmin]
    page: int
    limit: int
    total: int
