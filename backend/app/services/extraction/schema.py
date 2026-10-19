"""Strict LLM output contract for the Groq extraction pipeline.

The strict JSON schema (`EXTRACTION_JSON_SCHEMA`) is the anti-hallucination
type gate: with Groq Structured Outputs (``strict: true``) constrained
decoding guarantees the model response conforms to it structurally.
Semantic validation (allowed cities per D-06, contact sanity, etc.)
happens in the extractor orchestrator (plan 02), NOT here.

Persistence mirrors Job columns (backend/app/models/job.py): title/company/
activities/requirements/salary/benefits/city/contact_email/contact_phone,
plus source_snippet/raw_city preserved for admin review (D-08/D-06).
See 02-CONTEXT.md D-05/D-06.

Prompt delimiters (EXTR-08): the untrusted admin-pasted source text is
wrapped between START_DELIM/END_DELIM in the prompt so the model can be
told to treat it strictly as data (prompt-injection mitigation).
"""

from pydantic import BaseModel, ConfigDict, Field

START_DELIM = "<TEXTO_FONTE>"
END_DELIM = "</TEXTO_FONTE>"

EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "vagas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "company": {"type": ["string", "null"]},
                    "activities": {"type": ["string", "null"]},
                    "requirements": {"type": ["string", "null"]},
                    "salary": {"type": ["string", "null"]},
                    "benefits": {"type": ["string", "null"]},
                    "city": {"type": "string"},
                    "contact_email": {"type": ["string", "null"]},
                    "contact_phone": {"type": ["string", "null"]},
                },
                "required": [
                    "title",
                    "company",
                    "activities",
                    "requirements",
                    "salary",
                    "benefits",
                    "city",
                    "contact_email",
                    "contact_phone",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["vagas"],
    "additionalProperties": False,
}


class ExtractedJobRaw(BaseModel):
    """One LLM-extracted job row, exactly as the schema guarantees it."""

    model_config = ConfigDict(extra="forbid")

    title: str
    company: str | None = None
    activities: str | None = None
    requirements: str | None = None
    salary: str | None = None
    benefits: str | None = None
    city: str
    contact_email: str | None = None
    contact_phone: str | None = None


class ExtractionLLMOutput(BaseModel):
    """Top-level LLM response: {"vagas": [...]}."""

    model_config = ConfigDict(extra="forbid")

    vagas: list[ExtractedJobRaw] = Field(max_length=200)


class JobCandidate(ExtractedJobRaw):
    """Post-validation row: raw fields + provenance kept for admin review.

    ``source_snippet`` (D-08) anchors the candidate to the source chunk it
    came from; ``raw_city`` (D-06) preserves the un-normalized city string
    before mapping onto the allowed set.
    """

    source_snippet: str
    raw_city: str
