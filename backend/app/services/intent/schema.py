"""Strict schemas for NL intent extraction and deterministic mapping.

This module defines:
- LLM-candidate (untrusted) intent structures
- server-authoritative understood/applied/status contract

All models are strict (`extra="forbid"`). Fields not declared or not clearly
implied must remain ``None`` by default (no invention).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FieldStatus(str, Enum):
    """Per-field application status for the intent contract."""

    APLICADO = "aplicado"
    IGNORADO = "ignorado"
    APROXIMADO = "aproximado"


class WorkMode(str, Enum):
    REMOTO = "remoto"
    HIBRIDO = "hibrido"
    PRESENCIAL = "presencial"


class ContractType(str, Enum):
    CLT = "clt"
    PJ = "pj"
    ESTAGIO = "estagio"
    TEMPORARIO = "temporario"
    OUTROS = "outros"


class Seniority(str, Enum):
    ESTAGIO = "estagio"
    JUNIOR = "junior"
    PLENO = "pleno"
    SENIOR = "senior"
    OUTROS = "outros"


SortOrder = Literal["recentes", "antigas"]
ReasonCode = str


class IntentSalary(BaseModel):
    """Structured salary range understood from user text (BRL by default)."""

    model_config = ConfigDict(extra="forbid")

    min: int | float | None = None
    max: int | float | None = None
    currency: str | None = "BRL"


class IntentMode(BaseModel):
    """Work modality candidate with raw traceability."""

    model_config = ConfigDict(extra="forbid")

    value: WorkMode | None = None
    raw: str | None = None


class IntentContractType(BaseModel):
    """Contract type candidate with raw traceability."""

    model_config = ConfigDict(extra="forbid")

    value: ContractType | None = None
    raw: str | None = None


class IntentSeniority(BaseModel):
    """Seniority candidate with raw traceability."""

    model_config = ConfigDict(extra="forbid")

    value: Seniority | None = None
    raw: str | None = None


class IntentLLMOutput(BaseModel):
    """Untrusted LLM-candidate intent. Server decides final application."""

    model_config = ConfigDict(extra="forbid")

    q: str | None = None
    city: str | None = None
    salary: IntentSalary | None = None
    work_mode: IntentMode | None = None
    contract_type: IntentContractType | None = None
    seniority: IntentSeniority | None = None
    sort: SortOrder | None = None


class FieldAssessment(BaseModel):
    """Auditable per-field status: understood vs applied with reason."""

    model_config = ConfigDict(extra="forbid")

    field: str
    understood: Any | None = None
    applied: Any | None = None
    status: FieldStatus
    reason_code: str
    reason: str


class AppliedParams(BaseModel):
    """Deterministic params compatible with public job search."""

    model_config = ConfigDict(extra="forbid")

    q: str | None = None
    city: str | None = None
    sort: SortOrder | None = None


class UnderstoodIntent(BaseModel):
    """Normalized understood intent (safe representation, no invention)."""

    model_config = ConfigDict(extra="forbid")

    q: str | None = None
    city: str | None = None
    salary: IntentSalary | None = None
    work_mode: IntentMode | None = None
    contract_type: IntentContractType | None = None
    seniority: IntentSeniority | None = None
    sort: SortOrder | None = None


class IntentContract(BaseModel):
    """Final server-authoritative intent contract."""

    model_config = ConfigDict(extra="forbid")

    understood: UnderstoodIntent
    field_statuses: list[FieldAssessment]
    applied_params: AppliedParams
    limitations: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AppliedParams",
    "ContractType",
    "FieldAssessment",
    "FieldStatus",
    "IntentContract",
    "IntentContractType",
    "IntentLLMOutput",
    "IntentMode",
    "IntentSalary",
    "IntentSeniority",
    "ReasonCode",
    "Seniority",
    "SortOrder",
    "UnderstoodIntent",
    "WorkMode",
]
