"""Intent extraction/mapping domain (NL query -> safe search contract)."""

from app.services.intent.mapper import build_empty_intent, map_intent
from app.services.intent.schema import (
    AppliedParams,
    ContractType,
    FieldAssessment,
    FieldStatus,
    IntentContract,
    IntentContractType,
    IntentLLMOutput,
    IntentMode,
    IntentSalary,
    IntentSeniority,
    ReasonCode,
    Seniority,
    SortOrder,
    UnderstoodIntent,
    WorkMode,
)

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
    "build_empty_intent",
    "map_intent",
]

