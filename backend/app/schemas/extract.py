"""Contracts for POST /api/v1/admin/extract (D-01, D-02, D-07).

The endpoint (app/api/v1/extract.py) is the only surface that imports these;
the extraction core (app/services/extraction) never depends on HTTP schemas.

``alerts`` carries human-readable pt-BR warnings assembled from the
``ALERT_*`` format templates below (D-07): divergence alert, truncation
alert and the discarded-count notice. Templates are module constants so
tests can match them verbatim instead of hardcoding duplicated strings.
"""

from pydantic import BaseModel, Field

# --- pt-BR alert format templates (D-07) -----------------------------------
ALERT_DIVERGENCE = (
    "⚠️ Divergência: o texto indica {detected_count} vaga(s), "
    "mas {extracted_count} foram extraídas — confira se falta conteúdo "
    "e cole o restante."
)
ALERT_TRUNCATED = (
    "⚠️ Resposta truncada pelo modelo (finish_reason=length) — "
    "cole o restante em um novo envio."
)
ALERT_DISCARDED = "{n} vaga(s) descartada(s) — veja os motivos abaixo."
ALERT_MAX_JOBS = (
    "⚠️ O envio excedeu o limite de vagas por extração — parte do conteúdo "
    "foi descartado; cole o restante em um novo envio."
)


class ExtractRequest(BaseModel):
    """Raw pasted text from the admin (source of truth for extraction)."""

    text: str = Field(min_length=1)


class DiscardedJob(BaseModel):
    """One discarded candidate in the summary — reason + source anchor."""

    reason: str
    snippet: str


class ExtractSummaryResponse(BaseModel):
    """pt-BR summary returned after a synchronous extraction (D-01, D-02).

    Persisted counts by status (save path), the discarded list (never in
    the DB), the divergence/truncation flags plus pre-formatted alerts,
    and the model that actually answered.
    """

    saved_pending: int
    saved_needs_review: int
    discarded: list[DiscardedJob]
    divergent: bool
    detected_count: int | None
    extracted_count: int
    truncated: bool
    model_used: str
    chunks: int
    alerts: list[str]
