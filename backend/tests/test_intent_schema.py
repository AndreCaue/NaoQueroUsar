"""Schema tests for the intent contract (INT-01/INT-03 foundation).

Validates strict Pydantic models, nullable defaults, enum/status literals,
and the server-facing contract shapes used by the intent mapper.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.intent import (
    AppliedParams,
    FieldAssessment,
    FieldStatus,
    IntentContract,
    IntentLLMOutput,
    IntentSalary,
    UnderstoodIntent,
)


def test_intent_llm_output_empty_object_has_null_defaults() -> None:
    candidate = IntentLLMOutput.model_validate({})

    assert candidate.q is None
    assert candidate.city is None
    assert candidate.salary is None
    assert candidate.work_mode is None
    assert candidate.contract_type is None
    assert candidate.seniority is None
    assert candidate.sort is None


def test_intent_llm_output_absent_optional_nested_fields_are_none() -> None:
    candidate = IntentLLMOutput.model_validate({"q": "dev react", "city": "SP"})

    assert candidate.q == "dev react"
    assert candidate.city == "SP"
    assert candidate.salary is None
    assert candidate.work_mode is None
    assert candidate.contract_type is None
    assert candidate.seniority is None
    assert candidate.sort is None


def test_intent_llm_output_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        IntentLLMOutput.model_validate({"q": "vaga", "hacker_field": "x"})


def test_field_assessment_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        FieldAssessment.model_validate(
            {
                "field": "q",
                "understood": "dev",
                "applied": "dev",
                "status": "aplicado",
                "reason_code": "normalized",
                "reason": "ok",
                "unexpected": True,
            }
        )


def test_intent_contract_accepts_complete_valid_structure() -> None:
    contract = IntentContract(
        understood=UnderstoodIntent(
            q="dev react",
            city="São Paulo",
            salary=None,
            work_mode=None,
            contract_type=None,
            seniority=None,
            sort=None,
        ),
        field_statuses=[
            FieldAssessment(
                field="city",
                understood="SP",
                applied="São Paulo",
                status="aplicado",
                reason_code="normalized",
                reason="Cidade normalizada para a whitelist.",
            ),
            FieldAssessment(
                field="seniority",
                understood={"value": "pleno", "raw": "pleno"},
                applied={"q_terms": ["pleno"]},
                status="aproximado",
                reason_code="textual_approximation_in_q",
                reason="Senioridade usada como termo textual em q.",
            ),
        ],
        applied_params=AppliedParams(q="dev react", city="São Paulo", sort=None),
        limitations=["non_native_fields_limited"],
    )

    assert contract.applied_params.q == "dev react"
    assert contract.applied_params.city == "São Paulo"
    assert contract.applied_params.sort is None
    assert {fs.status for fs in contract.field_statuses} == {"aplicado", "aproximado"}


def test_intent_salary_accepts_numeric_bounds_and_brl_currency() -> None:
    salary = IntentSalary(min=8000, max=None, currency="BRL")

    assert salary.min == 8000
    assert salary.max is None
    assert salary.currency == "BRL"


def test_intent_salary_default_currency_is_brl_when_constructed_without_currency() -> None:
    salary = IntentSalary(min=3500)

    assert salary.currency == "BRL"


def test_field_status_literal_values_are_present_in_model() -> None:
    # Ensures status contract includes the exact pt-BR values.
    assessment = FieldAssessment(
        field="salary",
        understood=None,
        applied=None,
        status="ignorado",
        reason_code="unsupported_structured_filter",
        reason="Faixa salarial sem filtro nativo.",
    )

    assert assessment.status in {"aplicado", "ignorado", "aproximado"}
    # Exported status type exposes the three expected values (Enum or Literal-compatible usage)
    status_values = {getattr(v, "value", v) for v in getattr(FieldStatus, "__members__", {}).values()} or set(
        getattr(FieldStatus, "__args__", ())
    )
    assert {"aplicado", "ignorado", "aproximado"}.issubset(status_values)
