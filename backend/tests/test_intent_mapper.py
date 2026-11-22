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


def test_mvp_dev_pleno_sp_salary_not_native() -> None:
    """MVP: dev pleno SP salário >= 8k (QA-01)."""
    contract = map_intent(
        IntentLLMOutput.model_validate(
            {
                "q": "dev",
                "city": "SP",
                "salary": {"min": 8000, "max": None, "currency": "BRL"},
                "seniority": {"value": "pleno", "raw": "pleno"},
            }
        ),
        raw_text="dev pleno SP salário >= 8k",
    )

    assert contract.applied_params.city == "São Paulo"
    assert _field(contract, "city").status == "aplicado"

    assert contract.applied_params.q is not None
    q_lower = contract.applied_params.q.lower()
    assert "dev" in q_lower
    assert "pleno" in q_lower

    fs_salary = _field(contract, "salary")
    assert fs_salary.status == "ignorado"
    assert fs_salary.reason_code == "unsupported_structured_filter"
    assert fs_salary.applied is None

    fs_seniority = _field(contract, "seniority")
    assert fs_seniority.status == "aproximado"
    assert fs_seniority.reason_code == "textual_approximation_in_q"

    assert contract.applied_params.sort is None
    assert "unsupported_structured_filter" in contract.limitations
    assert all(fs.applied != {"native_salary_filter": True} for fs in contract.field_statuses)


def test_mvp_remoto_frontend_react_clt_textual_approximation() -> None:
    """MVP: remoto frontend React preferência CLT (QA-01)."""
    contract = map_intent(
        IntentLLMOutput.model_validate(
            {
                "q": "frontend React",
                "city": "Remoto",
                "work_mode": {"value": "remoto", "raw": "remoto"},
                "contract_type": {"value": "clt", "raw": "CLT"},
            }
        ),
        raw_text="remoto frontend React preferência CLT",
    )

    assert contract.applied_params.city == "Remoto"
    assert _field(contract, "city").status == "aplicado"

    # Remote modality represented via applied whitelist city (safe behavior).
    assert _field(contract, "work_mode").status == "aplicado"

    assert contract.applied_params.q is not None
    q_lower = contract.applied_params.q.lower()
    assert "react" in q_lower
    assert "frontend" in q_lower
    assert "clt" in q_lower

    fs_contract = _field(contract, "contract_type")
    assert fs_contract.status == "aproximado"
    assert fs_contract.reason_code == "textual_approximation_in_q"


def test_mvp_parecidas_com_vaga_seed_textual_limitado_sem_link_id() -> None:
    """MVP: vagas parecidas com uma vaga (seed textual limitado, QA-01/D-02)."""
    raw_text = "vagas parecidas com uma vaga de analista de marketing"
    contract = map_intent(
        IntentLLMOutput.model_validate({"q": "analista marketing"}),
        raw_text=raw_text,
    )

    assert contract.applied_params.q is not None
    q_lower = contract.applied_params.q.lower()
    assert "analista" in q_lower
    assert "marketing" in q_lower
    assert contract.applied_params.city is None
    assert contract.applied_params.sort is None

    # No semantic/vector similarity and no link/ID-based seed support in contract.
    dumped = contract.model_dump(mode="json")
    blob = str(dumped).lower()
    assert "semantic" not in blob
    assert "semant" not in blob
    assert "vector" not in blob
    assert "embedding" not in blob
    assert "seed_id" not in blob
    assert "vaga_id" not in blob
    assert "job_id" not in blob
    assert "http://" not in blob
    assert "https://" not in blob

    for key in ("seed_id", "seed_link", "seed_url", "reference_job_id", "similarity", "vector", "embedding"):
        assert key not in dumped
        assert key not in (dumped.get("meta") or {})
        assert key not in (dumped.get("understood") or {})
        assert key not in (dumped.get("applied_params") or {})


def test_mvp_analista_dados_campinas_ou_remoto_salary_combo() -> None:
    """MVP: analista de dados Campinas ou remoto 6–10k (QA-01)."""
    raw_text = "analista de dados Campinas ou remoto 6–10k"
    contract = map_intent(
        IntentLLMOutput.model_validate(
            {
                "q": "analista de dados",
                "city": "Campinas",
                "salary": {"min": 6000, "max": 10000, "currency": "BRL"},
            }
        ),
        raw_text=raw_text,
    )

    # Campinas is outside whitelist and must not be applied as city.
    # Raw text has explicit non-whitelist vs supported conflict (Campinas ou Remoto):
    # D-03 requires safe conflict_resolved and must not promote Remoto.
    assert contract.applied_params.city is None
    fs_city = _field(contract, "city")
    assert fs_city.status == "ignorado"
    assert fs_city.reason_code == "conflict_resolved"

    assert contract.applied_params.city != "Remoto"

    # Salary is understood but has no native structured filter.
    fs_salary = _field(contract, "salary")
    assert fs_salary.status == "ignorado"
    assert fs_salary.reason_code == "unsupported_structured_filter"
    assert fs_salary.applied is None

    assert contract.applied_params.q is not None
    q_lower = contract.applied_params.q.lower()
    assert "analista" in q_lower
    assert "dados" in q_lower

    assert "unsupported_structured_filter" in contract.limitations


def test_mvp_estagio_marketing_digital_em_sp() -> None:
    """MVP: estágio marketing digital em SP (QA-01)."""
    contract = map_intent(
        IntentLLMOutput.model_validate(
            {
                "q": "marketing digital",
                "city": "SP",
                "seniority": {"value": "estagio", "raw": "estágio"},
            }
        ),
        raw_text="estágio marketing digital em SP",
    )

    assert contract.applied_params.city == "São Paulo"
    assert _field(contract, "city").status == "aplicado"

    assert contract.applied_params.q is not None
    q_lower = contract.applied_params.q.lower()
    assert "marketing" in q_lower
    assert "digital" in q_lower
    assert "estag" in q_lower  # textual approximation/reflection of estágio

    fs_seniority = _field(contract, "seniority")
    assert fs_seniority.status in {"aproximado", "aplicado"}
    if fs_seniority.status == "aproximado":
        assert fs_seniority.reason_code == "textual_approximation_in_q"


def test_absent_candidate_raw_text_applies_supported_city_safely() -> None:
    c1 = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga de analista em São Paulo")
    assert c1.applied_params.city == "São Paulo"
    fs1 = _field(c1, "city")
    assert fs1.status == "aplicado"
    assert fs1.reason_code == "normalized"
    assert fs1.understood is None

    c_sp = map_intent(IntentLLMOutput.model_validate({}), raw_text="emprego em sp")
    assert c_sp.applied_params.city == "São Paulo"
    assert _field(c_sp, "city").status == "aplicado"

    c_rj = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga no Rio de Janeiro")
    assert c_rj.applied_params.city == "Rio de Janeiro"
    assert _field(c_rj, "city").status == "aplicado"

    c_bh = map_intent(IntentLLMOutput.model_validate({}), raw_text="oportunidade em bh")
    assert c_bh.applied_params.city == "Belo Horizonte"
    assert _field(c_bh, "city").status == "aplicado"

    c_remoto = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga home office para dev")
    assert c_remoto.applied_params.city == "Remoto"
    assert _field(c_remoto, "city").status == "aplicado"


def test_absent_candidate_raw_text_city_safeguards() -> None:
    conflict = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga em sp ou rj")
    assert conflict.applied_params.city is None
    fs_conflict = _field(conflict, "city")
    assert fs_conflict.status == "ignorado"
    assert fs_conflict.reason_code == "conflict_resolved"

    campinas = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga em campinas")
    assert campinas.applied_params.city is None
    assert "campinas" not in str(campinas.model_dump()).lower() or _field(campinas, "city").applied is None
    # never produce non-whitelist city
    assert campinas.applied_params.city != "Campinas"

    # present non-whitelist candidate remains not_in_whitelist (existing MVP behavior)
    present = map_intent(IntentLLMOutput.model_validate({"city": "Campinas"}), raw_text="vaga em campinas")
    assert present.applied_params.city is None
    assert _field(present, "city").reason_code == "not_in_whitelist"


def test_absent_candidate_raw_text_rio_false_positive_safeguards() -> None:
    rs = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga no Rio Grande do Sul")
    assert rs.applied_params.city is None
    fs_rs = _field(rs, "city")
    assert fs_rs.status == "ignorado"
    assert fs_rs.reason_code != "normalized"
    assert fs_rs.applied != "Rio de Janeiro"

    rb = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga em Rio Branco")
    assert rb.applied_params.city is None
    assert rb.applied_params.city != "Rio de Janeiro"


def test_candidate_present_raw_text_city_conflicts_cr01() -> None:
    c_sp_rj = map_intent(IntentLLMOutput.model_validate({"city": "SP"}), raw_text="vaga em sp ou rio de janeiro")
    assert c_sp_rj.applied_params.city is None
    fs_sp_rj = _field(c_sp_rj, "city")
    assert fs_sp_rj.status == "ignorado"
    assert fs_sp_rj.reason_code == "conflict_resolved"

    c_remoto_sp = map_intent(IntentLLMOutput.model_validate({"city": "Remoto"}), raw_text="vaga remoto ou são paulo")
    assert c_remoto_sp.applied_params.city is None
    fs_remoto_sp = _field(c_remoto_sp, "city")
    assert fs_remoto_sp.status == "ignorado"
    assert fs_remoto_sp.reason_code == "conflict_resolved"

    # alias/abbrev/remoto matrix cases - all conflict_resolved, no city applied
    for raw_text, candidate_city in (
        ("sp ou rj", "SP"),
        ("bh ou remoto", "Belo Horizonte"),
        ("home office ou belo horizonte", "Remoto"),
    ):
        contract = map_intent(IntentLLMOutput.model_validate({"city": candidate_city}), raw_text=raw_text)
        assert contract.applied_params.city is None
        fs_city = _field(contract, "city")
        assert fs_city.status == "ignorado"
        assert fs_city.reason_code == "conflict_resolved"


def test_raw_vs_candidate_supported_divergence_conflict_cr01() -> None:
    contract = map_intent(IntentLLMOutput.model_validate({"city": "RJ"}), raw_text="vaga em sp")
    assert contract.applied_params.city is None
    fs_city = _field(contract, "city")
    assert fs_city.status == "ignorado"
    assert fs_city.reason_code == "conflict_resolved"


def test_same_canonical_city_and_safe_fallbacks_cr01() -> None:
    same = map_intent(IntentLLMOutput.model_validate({"city": "São Paulo"}), raw_text="vaga em sp")
    assert same.applied_params.city == "São Paulo"
    fs_same = _field(same, "city")
    assert fs_same.status == "aplicado"
    assert fs_same.reason_code == "normalized"

    absent = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga em sp")
    assert absent.applied_params.city == "São Paulo"
    assert _field(absent, "city").status == "aplicado"

    non_whitelist = map_intent(IntentLLMOutput.model_validate({"city": "Campinas"}), raw_text="vaga em campinas")
    assert non_whitelist.applied_params.city is None
    fs_nw = _field(non_whitelist, "city")
    assert fs_nw.status == "ignorado"
    assert fs_nw.reason_code == "not_in_whitelist"

    # Explicit conflict between non-whitelist and supported city must not promote supported city (D-03 safe)
    conflict_present = map_intent(
        IntentLLMOutput.model_validate({"city": "Campinas"}),
        raw_text="vaga em campinas ou remoto",
    )
    assert conflict_present.applied_params.city is None
    fs_conflict_present = _field(conflict_present, "city")
    assert fs_conflict_present.status == "ignorado"
    assert fs_conflict_present.reason_code == "conflict_resolved"

    conflict_absent = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga em campinas ou remoto")
    assert conflict_absent.applied_params.city is None
    fs_conflict_absent = _field(conflict_absent, "city")
    assert fs_conflict_absent.status == "ignorado"
    assert fs_conflict_absent.reason_code == "conflict_resolved"


def test_non_whitelist_vs_supported_conflict_guard_cr01() -> None:
    contract = map_intent(
        IntentLLMOutput.model_validate({"city": "Curitiba"}),
        raw_text="vaga em curitiba ou sao paulo",
    )
    assert contract.applied_params.city is None
    fs_city = _field(contract, "city")
    assert fs_city.status == "ignorado"
    assert fs_city.reason_code == "conflict_resolved"

    absent = map_intent(IntentLLMOutput.model_validate({}), raw_text="vaga em curitiba ou remoto")
    assert absent.applied_params.city is None
    fs_absent = _field(absent, "city")
    assert fs_absent.status == "ignorado"
    assert fs_absent.reason_code == "conflict_resolved"


def test_non_native_influence_uses_token_set_not_substring_wr03() -> None:
    # Observable false-positive: "vaga" is a substring of "vagabundo" in applied_q,
    # but it is NOT an equal normalized token-set member. Must not mark as approximated.
    contract = map_intent(
        IntentLLMOutput.model_validate({"q": "vagabundo", "seniority": {"value": None, "raw": "vaga"}}),
        raw_text="vagabundo vaga",
    )
    fs_seniority = _field(contract, "seniority")
    assert fs_seniority.status == "ignorado"
    assert fs_seniority.reason_code == "unsupported_structured_filter"

    # Positive control: genuine token membership in applied_q still approximates.
    contract_pos = map_intent(
        IntentLLMOutput.model_validate(
            {"q": "coordenador pleno", "seniority": {"value": "pleno", "raw": "pleno"}}
        ),
        raw_text="vaga coordenador pleno",
    )
    fs_pos = _field(contract_pos, "seniority")
    assert fs_pos.status == "aproximado"
    assert fs_pos.reason_code == "textual_approximation_in_q"
