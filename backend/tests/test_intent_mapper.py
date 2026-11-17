"""Deterministic intent mapper tests (INT-03, D-01..D-12,D-15).

Covers empty intent, whitelist/city normalization, explicit-only sort,
conflicts, non-native approximation/ignored statuses, and applied_params safety.
"""

from __future__ import annotations

from app.services.intent import IntentLLMOutput, IntentSalary, map_intent, build_empty_intent
from app.services.intent.schema import IntentContractType, IntentMode, IntentSeniority


def _field(contract, name: str):
    for fs in contract.field_statuses:
        if fs.field == name:
            return fs
    raise AssertionError(f"missing field status: {name}")


def test_build_empty_intent_returns_valid_contract_with_clear_statuses() -> None:
    contract = build_empty_intent("")

    assert contract.applied_params.q is None
    assert contract.applied_params.city is None
    assert contract.applied_params.sort is None

    assert contract.understood.q is None
    assert contract.understood.city is None
    assert contract.understood.salary is None
    assert contract.understood.work_mode is None
    assert contract.understood.contract_type is None
    assert contract.understood.seniority is None
    assert contract.understood.sort is None

    expected_fields = {"q", "city", "salary", "work_mode", "contract_type", "seniority", "sort"}
    assert expected_fields.issubset({fs.field for fs in contract.field_statuses})

    for name in expected_fields:
        fs = _field(contract, name)
        assert fs.understood is None
        assert fs.applied is None
        assert fs.status == "ignorado"
        assert fs.reason_code in {"empty_input", "no_extractable_params"}
        assert "Nenhum parâmetro extraível" in fs.reason or "extraível" in fs.reason.lower()

    assert "no_extractable_params" in contract.limitations


def test_city_whitelist_mapping_and_safe_rejections() -> None:
    c1 = map_intent(IntentLLMOutput.model_validate({"city": "SP"}))
    assert c1.applied_params.city == "São Paulo"
    assert _field(c1, "city").status == "aplicado"

    c2 = map_intent(IntentLLMOutput.model_validate({"city": "sao paulo"}))
    assert c2.applied_params.city == "São Paulo"

    c3 = map_intent(IntentLLMOutput.model_validate({"city": "home office"}))
    assert c3.applied_params.city == "Remoto"
    assert _field(c3, "city").status == "aplicado"

    c4 = map_intent(IntentLLMOutput.model_validate({"city": "Campinas"}))
    assert c4.applied_params.city is None
    fs_city = _field(c4, "city")
    assert fs_city.status == "ignorado"
    assert fs_city.reason_code == "not_in_whitelist"


def test_sort_is_applied_only_when_explicit_and_conflicts_do_not_apply() -> None:
    s1 = map_intent(IntentLLMOutput.model_validate({"sort": "antigas", "q": "vagas"}), raw_text="vagas mais antigas")
    assert s1.applied_params.sort == "antigas"
    assert _field(s1, "sort").status == "aplicado"

    s2 = map_intent(IntentLLMOutput.model_validate({"q": "vagas dev"}), raw_text="vagas dev")
    assert s2.applied_params.sort is None
    fs_sort = _field(s2, "sort")
    assert fs_sort.status == "ignorado"
    assert fs_sort.reason_code == "not_explicit"

    s3 = map_intent(IntentLLMOutput.model_validate({"q": "dev"}), raw_text="quero vagas mais recentes e mais antigas")
    assert s3.applied_params.sort is None
    assert _field(s3, "sort").reason_code == "conflict_resolved"


def test_non_native_fields_are_approximated_in_q_or_ignored_without_structured_filter() -> None:
    contract = map_intent(
        IntentLLMOutput.model_validate(
            {
                "q": "React",
                "seniority": {"value": "pleno", "raw": "pleno"},
                "contract_type": {"value": "clt", "raw": "CLT"},
                "salary": {"min": 8000, "max": None, "currency": "BRL"},
            }
        ),
        raw_text="vaga dev react pleno clt salario 8000",
    )

    assert contract.applied_params.q is not None
    q_lower = contract.applied_params.q.lower()
    assert "react" in q_lower
    assert "pleno" in q_lower or "clt" in q_lower

    fs_seniority = _field(contract, "seniority")
    assert fs_seniority.status == "aproximado"
    assert fs_seniority.reason_code == "textual_approximation_in_q"

    fs_contract = _field(contract, "contract_type")
    assert fs_contract.status == "aproximado"
    assert fs_contract.reason_code == "textual_approximation_in_q"

    fs_salary = _field(contract, "salary")
    assert fs_salary.status == "ignorado"
    assert fs_salary.reason_code == "unsupported_structured_filter"
    assert fs_salary.applied is None

    assert "non_native_fields_limited" in contract.limitations or "unsupported_structured_filter" in contract.limitations


def test_applied_params_never_invent_city_or_sort() -> None:
    c = map_intent(IntentLLMOutput.model_validate({"city": "Curitiba", "q": "analista"}), raw_text="analista em curitiba")
    assert c.applied_params.city is None
    assert c.applied_params.city not in {"São Paulo", "Rio de Janeiro", "Belo Horizonte", "Remoto"} or c.applied_params.city is None

    s = map_intent(IntentLLMOutput.model_validate({"q": "vaga"}), raw_text="vaga urgente")
    assert s.applied_params.sort is None
    assert s.applied_params.sort in {None, "recentes", "antigas"}
    assert s.applied_params.sort != "recentes"  # must not be invented when not explicit
