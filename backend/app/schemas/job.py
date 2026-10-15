"""Public (contact-free) job schemas.

D-15: the public list/detail return every field EXCEPT the contact.
D-18: contact is NEVER in a public payload — the reveal is a dedicated
Phase 3 endpoint. These schemas are the structural enforcement of that
rule (PITFALLS 7): they deliberately declare no ``contact_email`` /
``contact_phone`` fields, so even if a caller passes a full ``Job`` ORM
object, ``model_validate`` cannot leak the contact into the response.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

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
