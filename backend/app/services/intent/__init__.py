"""Intent extraction/mapping domain (NL query -> safe search contract)."""

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

# Mapper/public API exports are added by Task 2 (kept import-safe meanwhile).
try:  # pragma: no cover - populated in Task 2
    from app.services.intent.mapper import build_empty_intent, map_intent
except Exception:  # pragma: no cover
    build_empty_intent = None  # type: ignore[assignment]
    map_intent = None  # type: ignore[assignment]

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
