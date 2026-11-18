"""Contract, resilience and safety tests for POST /api/v1/public/chat-search (API-01..03).

LLM/intent extraction is always mocked (no network). DB-backed assertions rely on
the shared test fixtures (real Postgres test DB when configured).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.core.config import get_settings
from app.models.job import Job, JobStatus
from app.services.intent.mapper import build_empty_intent
from app.services.intent.schema import (
    AppliedParams,
    FieldAssessment,
    FieldStatus,
    IntentContract,
    UnderstoodIntent,
)


SAO_PAULO = "São Paulo"


def _job(**overrides) -> Job:
    defaults = {
        "title": "Vaga de Teste",
        "city": "Remoto",
        "contact_phone": "+55 11 90000-0200",
        "status": JobStatus.published,
    }
    defaults.update(overrides)
    return Job(**defaults)


async def _insert(db_session, **overrides) -> Job:
    job = _job(**overrides)
    db_session.add(job)
    await db_session.flush()
    return job


def _contract(
    *,
    q: str | None = None,
    city: str | None = None,
    sort: str | None = None,
    field_statuses: list[FieldAssessment] | None = None,
    limitations: list[str] | None = None,
    meta: dict | None = None,
) -> IntentContract:
    return IntentContract(
        understood=UnderstoodIntent(q=q, city=city, sort=sort),
        field_statuses=field_statuses or [],
        applied_params=AppliedParams(q=q, city=city, sort=sort),
        limitations=list(limitations or []),
        meta=dict(meta or {}),
    )


def _assert_no_contacts(items: list[dict]) -> None:
    for item in items:
        assert "contact_email" not in item
        assert "contact_phone" not in item


async def test_chat_search_equivalent_to_public_jobs_and_hides_contacts(
    db_session, client, monkeypatch
):
    await _insert(
        db_session,
        title="Analista de Dados",
        company="Empresa X",
        city=SAO_PAULO,
        contact_email="segredo@example.com",
        contact_phone="+55 11 98888-0001",
    )
    await _insert(
        db_session,
        title="Vendedor de Loja",
        company="Empresa Y",
        city=SAO_PAULO,
        contact_email="outro@example.com",
    )

    interpretation = _contract(q="analista", city=SAO_PAULO, sort="recentes")

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    chat = await client.post(
        "/api/v1/public/chat-search",
        json={"message": "vaga analista em sao paulo", "page": 1, "limit": 20},
    )
    assert chat.status_code == 200
    body = chat.json()

    jobs = await client.get(
        "/api/v1/public/jobs",
        params={"q": "analista", "city": "sao-paulo", "sort": "recentes", "page": 1, "limit": 20},
    )
    assert jobs.status_code == 200
    jobs_body = jobs.json()

    assert body["results"]["page"] == 1
    assert body["results"]["limit"] == 20
    assert body["results"]["total"] == jobs_body["total"]
    assert [i["id"] for i in body["results"]["items"]] == [i["id"] for i in jobs_body["items"]]
    assert body["interpretation"]["applied_params"]["q"] == "analista"
    assert body["interpretation"]["applied_params"]["city"] == SAO_PAULO
    assert body["interpretation"]["applied_params"]["sort"] == "recentes"
    _assert_no_contacts(body["results"]["items"])


async def test_chat_search_pagination_and_total_consistent(db_session, client, monkeypatch):
    await _insert(db_session, title="Analista Um", city=SAO_PAULO, contact_email="a@example.com")
    await _insert(db_session, title="Analista Dois", city=SAO_PAULO, contact_phone="+55 11 97777-0002")
    await _insert(db_session, title="Vendedor", city=SAO_PAULO)

    interpretation = _contract(q="analista", city=SAO_PAULO, sort="recentes")

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    resp = await client.post(
        "/api/v1/public/chat-search",
        json={"message": "analista em sp", "page": 1, "limit": 1},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"]["page"] == 1
    assert body["results"]["limit"] == 1
    assert len(body["results"]["items"]) == 1
    assert body["results"]["total"] >= 2
    _assert_no_contacts(body["results"]["items"])


async def test_chat_search_response_has_interpretation_and_results_contract(
    db_session, client, monkeypatch
):
    await _insert(db_session, title="Dev Backend", contact_email="c@example.com")

    interpretation = _contract(q="dev", city=None, sort="recentes", meta={})

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    resp = await client.post(
        "/api/v1/public/chat-search",
        json={"message": "dev backend"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "interpretation" in body
    assert "results" in body
    assert set(body["results"].keys()) == {"items", "page", "limit", "total"}
    assert "field_statuses" in body["interpretation"]
    assert "applied_params" in body["interpretation"]
    assert "limitations" in body["interpretation"]
    assert "meta" in body["interpretation"]
    _assert_no_contacts(body["results"]["items"])


def _assert_safe_ptbr_text(value: str) -> None:
    assert isinstance(value, str) and value.strip()
    lowered = value.lower()
    assert "traceback" not in lowered
    assert "exception" not in lowered
    assert "groq" not in lowered


async def test_chat_search_rejects_invalid_or_too_long_message(client):
    resp_spaces = await client.post("/api/v1/public/chat-search", json={"message": "   "})
    assert resp_spaces.status_code in (400, 422)
    assert "detail" in resp_spaces.json()

    resp_empty = await client.post("/api/v1/public/chat-search", json={"message": ""})
    assert resp_empty.status_code in (400, 422)
    assert "detail" in resp_empty.json()

    from app.core.config import get_settings

    max_chars = get_settings().CHAT_SEARCH_MAX_MESSAGE_CHARS
    resp_long = await client.post(
        "/api/v1/public/chat-search", json={"message": "a" * (max_chars + 1)}
    )
    assert resp_long.status_code in (400, 422)
    assert "detail" in resp_long.json()


async def test_chat_search_rate_limit_returns_429_with_retry_after(client, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "CHAT_SEARCH_RATE_LIMIT", "1/minute")

    async def fake_extract(*args, **kwargs):
        return _contract(q="vaga", city=None, sort="recentes")

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    first = await client.post("/api/v1/public/chat-search", json={"message": "vaga remota"})
    assert first.status_code == 200
    second = await client.post("/api/v1/public/chat-search", json={"message": "outra vaga"})
    assert second.status_code == 429
    assert second.headers.get("Retry-After")
    detail = second.json().get("detail")
    _assert_safe_ptbr_text(detail)


async def test_chat_search_llm_failure_degrades_safely(client, monkeypatch):
    async def fake_extract(*args, **kwargs):
        raise Exception("boom")

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    resp = await client.post("/api/v1/public/chat-search", json={"message": "vaga dev"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"]["items"] == []
    assert body["results"]["total"] == 0
    assert body["interpretation"]["applied_params"] == {"q": None, "city": None, "sort": None}
    assert body["interpretation"]["meta"]["degraded"] is True
    assert body["interpretation"]["meta"]["degradation_reason"] in {"llm_unavailable", "timeout"}
    _assert_safe_ptbr_text(body["interpretation"]["meta"]["guidance"])
    _assert_no_contacts(body["results"]["items"])


async def test_chat_search_llm_timeout_degrades_with_timeout_reason(client, monkeypatch):
    async def fake_extract(*args, **kwargs):
        raise Exception("timeout while waiting for provider")

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    resp = await client.post("/api/v1/public/chat-search", json={"message": "vaga dev"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"]["items"] == []
    assert body["results"]["total"] == 0
    assert body["interpretation"]["meta"]["degraded"] is True
    assert body["interpretation"]["meta"]["degradation_reason"] == "timeout"
    _assert_safe_ptbr_text(body["interpretation"]["meta"]["guidance"])


async def test_chat_search_no_extractable_params_returns_degraded_guidance(client, monkeypatch):
    async def fake_extract(*args, **kwargs):
        return build_empty_intent("oi", reason_code="no_extractable_params")

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    resp = await client.post("/api/v1/public/chat-search", json={"message": "oi"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"]["items"] == []
    assert body["results"]["total"] == 0
    assert body["interpretation"]["applied_params"] == {"q": None, "city": None, "sort": None}
    assert body["interpretation"]["meta"]["degraded"] is True
    assert body["interpretation"]["meta"]["degradation_reason"] == "no_extractable_params"
    _assert_safe_ptbr_text(body["interpretation"]["meta"]["guidance"])


async def test_chat_search_partial_support_and_non_whitelist_city_signaled(client, monkeypatch):
    interpretation = IntentContract(
        understood=UnderstoodIntent(
            q="desenvolvedor pleno",
            city="Campinas",
            sort="recentes",
        ),
        field_statuses=[
            FieldAssessment(
                field="city",
                understood="Campinas",
                applied=None,
                status=FieldStatus.IGNORADO,
                reason_code="not_in_whitelist",
                reason="Cidade fora da whitelist suportada; não aplicada.",
            ),
            FieldAssessment(
                field="seniority",
                understood={"value": "pleno", "raw": "pleno"},
                applied={"q_terms": ["pleno"]},
                status=FieldStatus.APROXIMADO,
                reason_code="textual_approximation_in_q",
                reason="Campo sem filtro estruturado nativo; usado como aproximação textual em q.",
            ),
        ],
        applied_params=AppliedParams(q="desenvolvedor pleno", city=None, sort="recentes"),
        limitations=["not_in_whitelist", "non_native_fields_limited", "textual_approximation_in_q"],
        meta={"guidance": "Aproximação aplicada; refine na busca manual."},
    )

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    resp = await client.post(
        "/api/v1/public/chat-search",
        json={"message": "vaga pleno em campinas"},
    )
    assert resp.status_code == 200
    body = resp.json()
    interp = body["interpretation"]
    assert interp["applied_params"]["city"] not in {"São Paulo", "Rio de Janeiro", "Belo Horizonte"}
    assert interp["applied_params"]["city"] is None
    limitations = set(interp.get("limitations") or [])
    reason_codes = {fs.get("reason_code") for fs in interp.get("field_statuses") or []}
    assert (
        "not_in_whitelist" in limitations
        or "not_in_whitelist" in reason_codes
        or "non_native_fields_limited" in limitations
        or "textual_approximation_in_q" in limitations
        or "textual_approximation_in_q" in reason_codes
    )
    # honest approximation/limitation signaling in pt-BR guidance/meta or limitations
    guidance = (interp.get("meta") or {}).get("guidance", "")
    combined = " ".join([guidance] + list(interp.get("limitations") or [])).lower()
    assert any(token in combined for token in ["aproxima", "limita", "manual", "whitelist", "suport"])
    assert body["results"]["items"] == [] or isinstance(body["results"]["items"], list)


async def test_chat_search_disabled_returns_controlled_guidance_without_contacts(
    client, monkeypatch
):
    settings = get_settings()
    monkeypatch.setattr(settings, "CHAT_SEARCH_ENABLED", False)

    resp = await client.post(
        "/api/v1/public/chat-search",
        json={"message": "vaga dev em sp", "page": 2, "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()

    interpretation = body["interpretation"]
    assert interpretation["meta"]["degraded"] is True
    assert interpretation["meta"]["degradation_reason"] == "chat_disabled"
    assert (
        interpretation["meta"]["guidance"]
        == "A busca por chat está indisponível no momento. Use a busca manual para encontrar vagas."
    )
    assert interpretation["applied_params"] == {"q": None, "city": None, "sort": None}
    assert "chat_disabled" in (interpretation.get("limitations") or [])
    for fs in interpretation.get("field_statuses") or []:
        assert fs["status"] == "ignorado"
        assert fs["applied"] is None
        assert fs.get("reason_code") == "chat_disabled"

    assert body["results"] == {"items": [], "page": 2, "limit": 10, "total": 0}
    _assert_no_contacts(body["results"]["items"])

    dumped = str(body).lower()
    assert "traceback" not in dumped
    assert "exception" not in dumped
    assert "groq" not in dumped


async def test_chat_search_disabled_short_circuits_intent_and_db(
    client, monkeypatch
):
    settings = get_settings()
    monkeypatch.setattr(settings, "CHAT_SEARCH_ENABLED", False)

    async def fail_extract(*args, **kwargs):
        raise AssertionError("extract_and_map_intent must not be called when chat is disabled")

    async def fail_list(*args, **kwargs):
        raise AssertionError("list_published must not be called when chat is disabled")

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fail_extract)
    monkeypatch.setattr("app.api.v1.public.list_published", fail_list)

    resp = await client.post("/api/v1/public/chat-search", json={"message": "vaga"})
    assert resp.status_code == 200
    assert resp.json()["interpretation"]["meta"]["degradation_reason"] == "chat_disabled"


async def test_chat_search_status_endpoint_reflects_toggle(client, monkeypatch):
    settings = get_settings()

    monkeypatch.setattr(settings, "CHAT_SEARCH_ENABLED", False)
    disabled = await client.get("/api/v1/public/chat-search/status")
    assert disabled.status_code == 200
    assert disabled.json() == {"enabled": False}

    monkeypatch.setattr(settings, "CHAT_SEARCH_ENABLED", True)
    enabled = await client.get("/api/v1/public/chat-search/status")
    assert enabled.status_code == 200
    assert enabled.json() == {"enabled": True}


async def test_public_jobs_remain_independent_when_chat_disabled(
    db_session, client, monkeypatch
):
    settings = get_settings()
    monkeypatch.setattr(settings, "CHAT_SEARCH_ENABLED", False)
    await _insert(db_session, title="Analista QA", city=SAO_PAULO, contact_email="a@example.com")

    jobs = await client.get("/api/v1/public/jobs")
    assert jobs.status_code == 200
    body = jobs.json()
    assert body["total"] >= 1
    assert any(item["title"] == "Analista QA" for item in body["items"])
    _assert_no_contacts(body["items"])


async def test_chat_search_success_emits_structured_log_without_pii(
    db_session, client, monkeypatch, caplog
):
    await _insert(
        db_session,
        title="Analista Dados",
        city=SAO_PAULO,
        contact_email="segredo-log@example.com",
    )
    interpretation = _contract(q="analista", city=SAO_PAULO, sort="recentes")
    sentinel_message = "mensagem sensivel usuario 123"

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    with caplog.at_level(logging.INFO):
        resp = await client.post(
            "/api/v1/public/chat-search",
            json={"message": sentinel_message, "page": 1, "limit": 20},
        )

    assert resp.status_code == 200
    body = resp.json()
    records = [r for r in caplog.records if r.message == "chat_search"]
    assert records, "expected a chat_search log record"
    rec = records[-1]
    assert rec.outcome == "success"
    assert rec.reason is None
    assert isinstance(rec.latency_ms, int) and rec.latency_ms >= 0
    assert rec.results_count == len(body["results"]["items"])
    assert rec.total == body["results"]["total"]
    assert rec.page == 1
    assert rec.limit == 20

    for r in caplog.records:
        rendered = r.getMessage() + " " + " ".join(
            str(v) for v in getattr(r, "__dict__", {}).values()
        )
        assert sentinel_message not in rendered
        assert "segredo-log@example.com" not in rendered
        assert "contact_email" not in rendered
        assert "contact_phone" not in rendered


async def test_chat_search_disabled_emits_structured_log_without_pii(
    client, monkeypatch, caplog
):
    settings = get_settings()
    monkeypatch.setattr(settings, "CHAT_SEARCH_ENABLED", False)
    sentinel_message = "mensagem privada desativada"

    with caplog.at_level(logging.INFO):
        resp = await client.post(
            "/api/v1/public/chat-search",
            json={"message": sentinel_message, "page": 1, "limit": 20},
        )

    assert resp.status_code == 200
    records = [r for r in caplog.records if r.message == "chat_search"]
    assert records, "expected a chat_search log record"
    rec = records[-1]
    assert rec.outcome == "disabled"
    assert rec.reason == "chat_disabled"
    assert isinstance(rec.latency_ms, int) and rec.latency_ms >= 0
    assert rec.results_count == 0
    assert rec.total == 0
    assert rec.page == 1
    assert rec.limit == 20

    for r in caplog.records:
        rendered = r.getMessage() + " " + " ".join(
            str(v) for v in getattr(r, "__dict__", {}).values()
        )
        assert sentinel_message not in rendered
        assert "contact_email" not in rendered
        assert "contact_phone" not in rendered


async def test_chat_search_degraded_timeout_emits_structured_log(client, monkeypatch, caplog):
    async def fake_extract(*args, **kwargs):
        raise Exception("timeout while waiting for provider")

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    with caplog.at_level(logging.INFO):
        resp = await client.post("/api/v1/public/chat-search", json={"message": "vaga dev"})

    assert resp.status_code == 200
    records = [r for r in caplog.records if r.message == "chat_search"]
    assert records
    rec = records[-1]
    assert rec.outcome == "degraded"
    assert rec.reason == "timeout"
    assert rec.results_count == 0
    assert rec.total == 0


async def test_mvp_dev_pleno_sp_salary_equivalence_and_no_contacts(db_session, client, monkeypatch):
    """MVP 1: dev pleno SP salário >= 8k (QA-01) — salary not native, SP applied."""
    await _insert(
        db_session,
        title="Desenvolvedor Pleno React",
        company="Empresa MVP",
        city=SAO_PAULO,
        contact_email="mvp1@example.com",
        contact_phone="+55 11 90000-1001",
    )
    await _insert(
        db_session,
        title="Analista Financeiro",
        company="Outra Empresa",
        city=SAO_PAULO,
        contact_email="nao-mvp1@example.com",
    )

    interpretation = IntentContract(
        understood=UnderstoodIntent(
            q="dev",
            city="São Paulo",
            salary={"min": 8000, "max": None, "currency": "BRL"},
            seniority={"value": "pleno", "raw": "pleno"},
            sort=None,
        ),
        field_statuses=[
            FieldAssessment(
                field="q",
                understood="dev",
                applied="dev pleno",
                status=FieldStatus.APLICADO,
                reason_code="normalized",
                reason="Termo de busca textual composto/normalizado e aplicado.",
            ),
            FieldAssessment(
                field="city",
                understood="SP",
                applied="São Paulo",
                status=FieldStatus.APLICADO,
                reason_code="normalized",
                reason="Cidade normalizada e aplicada via whitelist segura.",
            ),
            FieldAssessment(
                field="salary",
                understood={"min": 8000, "max": None, "currency": "BRL"},
                applied=None,
                status=FieldStatus.IGNORADO,
                reason_code="unsupported_structured_filter",
                reason="Faixa salarial entendida, mas não há filtro salarial nativo; não aplicada.",
            ),
            FieldAssessment(
                field="seniority",
                understood={"value": "pleno", "raw": "pleno"},
                applied={"q_terms": ["pleno"]},
                status=FieldStatus.APROXIMADO,
                reason_code="textual_approximation_in_q",
                reason="Campo sem filtro estruturado nativo; usado como aproximação textual em q.",
            ),
            FieldAssessment(
                field="sort",
                understood=None,
                applied=None,
                status=FieldStatus.IGNORADO,
                reason_code="not_explicit",
                reason="Ordenação não informada explicitamente; nenhuma preferência aplicada.",
            ),
        ],
        applied_params=AppliedParams(q="dev pleno", city=SAO_PAULO, sort=None),
        limitations=["unsupported_structured_filter", "non_native_fields_limited", "textual_approximation_in_q"],
        meta={},
    )

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    chat = await client.post(
        "/api/v1/public/chat-search",
        json={"message": "dev pleno SP salário >= 8k", "page": 1, "limit": 20},
    )
    assert chat.status_code == 200
    body = chat.json()

    jobs = await client.get(
        "/api/v1/public/jobs",
        params={"q": "dev pleno", "city": "sao-paulo", "sort": "recentes", "page": 1, "limit": 20},
    )
    assert jobs.status_code == 200
    jobs_body = jobs.json()

    assert body["interpretation"]["applied_params"] == {"q": "dev pleno", "city": SAO_PAULO, "sort": None}
    assert body["results"]["total"] == jobs_body["total"]
    assert [i["id"] for i in body["results"]["items"]] == [i["id"] for i in jobs_body["items"]]
    _assert_no_contacts(body["results"]["items"])

    salary_fs = next(fs for fs in body["interpretation"]["field_statuses"] if fs["field"] == "salary")
    assert salary_fs["status"] == "ignorado"
    assert salary_fs["reason_code"] == "unsupported_structured_filter"
    assert salary_fs["applied"] is None


async def test_mvp_remoto_frontend_react_clt_textual_approximation(db_session, client, monkeypatch):
    """MVP 2: remoto frontend React preferência CLT (QA-01)."""
    await _insert(
        db_session,
        title="Frontend React CLT",
        company="Empresa Remota",
        city="Remoto",
        contact_email="mvp2@example.com",
    )
    await _insert(
        db_session,
        title="Analista Presencial",
        company="Outra",
        city=SAO_PAULO,
        contact_phone="+55 11 90000-2002",
    )

    interpretation = IntentContract(
        understood=UnderstoodIntent(
            q="frontend React",
            city="Remoto",
            work_mode={"value": "remoto", "raw": "remoto"},
            contract_type={"value": "clt", "raw": "CLT"},
            sort=None,
        ),
        field_statuses=[
            FieldAssessment(
                field="q",
                understood="frontend React",
                applied="frontend React CLT",
                status=FieldStatus.APLICADO,
                reason_code="normalized",
                reason="Termo de busca textual composto/normalizado e aplicado.",
            ),
            FieldAssessment(
                field="city",
                understood="Remoto",
                applied="Remoto",
                status=FieldStatus.APLICADO,
                reason_code="normalized",
                reason="Cidade normalizada e aplicada via whitelist segura.",
            ),
            FieldAssessment(
                field="work_mode",
                understood={"value": "remoto", "raw": "remoto"},
                applied="Remoto",
                status=FieldStatus.APLICADO,
                reason_code="normalized",
                reason="Modalidade remota aplicada como cidade na whitelist.",
            ),
            FieldAssessment(
                field="contract_type",
                understood={"value": "clt", "raw": "CLT"},
                applied={"q_terms": ["CLT"]},
                status=FieldStatus.APROXIMADO,
                reason_code="textual_approximation_in_q",
                reason="Campo sem filtro estruturado nativo; usado como aproximação textual em q.",
            ),
        ],
        applied_params=AppliedParams(q="frontend React CLT", city="Remoto", sort=None),
        limitations=["non_native_fields_limited", "textual_approximation_in_q"],
        meta={},
    )

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    chat = await client.post(
        "/api/v1/public/chat-search",
        json={"message": "remoto frontend React preferência CLT", "page": 1, "limit": 20},
    )
    assert chat.status_code == 200
    body = chat.json()

    jobs = await client.get(
        "/api/v1/public/jobs",
        params={"q": "frontend React CLT", "city": "remoto", "sort": "recentes", "page": 1, "limit": 20},
    )
    assert jobs.status_code == 200
    jobs_body = jobs.json()

    assert body["interpretation"]["applied_params"]["city"] == "Remoto"
    assert "react" in (body["interpretation"]["applied_params"]["q"] or "").lower()
    assert body["results"]["total"] == jobs_body["total"]
    assert [i["id"] for i in body["results"]["items"]] == [i["id"] for i in jobs_body["items"]]
    _assert_no_contacts(body["results"]["items"])


async def test_mvp_parecidas_seed_textual_limitado_no_semantic_link_id(db_session, client, monkeypatch):
    """MVP 3: vagas parecidas com uma vaga = seed textual limitado (QA-01/D-02)."""
    await _insert(
        db_session,
        title="Analista de Marketing Digital",
        company="Empresa Seed",
        city=SAO_PAULO,
        contact_email="seed@example.com",
    )

    interpretation = IntentContract(
        understood=UnderstoodIntent(q="analista marketing", city=None, sort=None),
        field_statuses=[
            FieldAssessment(
                field="q",
                understood="analista marketing",
                applied="analista marketing",
                status=FieldStatus.APLICADO,
                reason_code="normalized",
                reason="Termo de busca textual normalizado e aplicado.",
            ),
        ],
        applied_params=AppliedParams(q="analista marketing", city=None, sort=None),
        limitations=[],
        meta={"guidance": "Busca por termos semelhantes (seed textual limitado), sem similaridade semântica/vetorial e sem link/ID de vaga."},
    )

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    chat = await client.post(
        "/api/v1/public/chat-search",
        json={"message": "vagas parecidas com uma vaga de analista de marketing", "page": 1, "limit": 20},
    )
    assert chat.status_code == 200
    body = chat.json()

    jobs = await client.get(
        "/api/v1/public/jobs",
        params={"q": "analista marketing", "sort": "recentes", "page": 1, "limit": 20},
    )
    assert jobs.status_code == 200
    jobs_body = jobs.json()

    assert body["interpretation"]["applied_params"]["q"] == "analista marketing"
    assert body["results"]["total"] == jobs_body["total"]
    assert [i["id"] for i in body["results"]["items"]] == [i["id"] for i in jobs_body["items"]]
    _assert_no_contacts(body["results"]["items"])

    # Seed is textual-only in q: no semantic/vector similarity and no link/ID-based seed support.
    guidance = str(((body.get("interpretation") or {}).get("meta") or {}).get("guidance", "")).lower()
    assert "seed textual" in guidance
    assert "sem" in guidance and "vet" in guidance
    assert "link/id" in guidance

    forbidden_capability_keys = {
        "seed_id",
        "seed_link",
        "seed_url",
        "reference_job_id",
        "similarity_score",
        "vector",
        "vectors",
        "embedding",
        "embeddings",
        "semantic_search",
    }
    assert forbidden_capability_keys.isdisjoint(set(body.keys()))
    assert forbidden_capability_keys.isdisjoint(set((body.get("interpretation") or {}).keys()))
    assert forbidden_capability_keys.isdisjoint(set(((body.get("interpretation") or {}).get("meta") or {}).keys()))
    applied_params_obj = (body.get("interpretation") or {}).get("applied_params") or {}
    assert isinstance(applied_params_obj, dict)
    assert forbidden_capability_keys.isdisjoint(set(applied_params_obj.keys()))


async def test_mvp_campinas_ou_remoto_salary_partial_support_signaled(db_session, client, monkeypatch):
    """MVP 4: analista de dados Campinas ou remoto 6–10k (QA-01)."""
    await _insert(
        db_session,
        title="Analista de Dados BI",
        company="Empresa Dados",
        city="Remoto",
        contact_email="mvp4@example.com",
    )

    interpretation = IntentContract(
        understood=UnderstoodIntent(
            q="analista de dados",
            city="Campinas",
            salary={"min": 6000, "max": 10000, "currency": "BRL"},
            sort=None,
        ),
        field_statuses=[
            FieldAssessment(
                field="q",
                understood="analista de dados",
                applied="analista de dados",
                status=FieldStatus.APLICADO,
                reason_code="normalized",
                reason="Termo de busca textual normalizado e aplicado.",
            ),
            FieldAssessment(
                field="city",
                understood="Campinas",
                applied=None,
                status=FieldStatus.IGNORADO,
                reason_code="not_in_whitelist",
                reason="Cidade fora da whitelist suportada; não aplicada.",
            ),
            FieldAssessment(
                field="salary",
                understood={"min": 6000, "max": 10000, "currency": "BRL"},
                applied=None,
                status=FieldStatus.IGNORADO,
                reason_code="unsupported_structured_filter",
                reason="Faixa salarial entendida, mas não há filtro salarial nativo; não aplicada.",
            ),
        ],
        applied_params=AppliedParams(q="analista de dados", city=None, sort=None),
        limitations=["not_in_whitelist", "unsupported_structured_filter", "non_native_fields_limited"],
        meta={"guidance": "Cidade fora da whitelist e faixa salarial sem filtro nativo; refine na busca manual."},
    )

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    chat = await client.post(
        "/api/v1/public/chat-search",
        json={"message": "analista de dados Campinas ou remoto 6–10k", "page": 1, "limit": 20},
    )
    assert chat.status_code == 200
    body = chat.json()

    jobs = await client.get(
        "/api/v1/public/jobs",
        params={"q": "analista de dados", "sort": "recentes", "page": 1, "limit": 20},
    )
    assert jobs.status_code == 200
    jobs_body = jobs.json()

    assert body["interpretation"]["applied_params"]["city"] is None
    assert body["interpretation"]["applied_params"]["q"] == "analista de dados"
    assert body["results"]["total"] == jobs_body["total"]
    assert [i["id"] for i in body["results"]["items"]] == [i["id"] for i in jobs_body["items"]]
    _assert_no_contacts(body["results"]["items"])

    interp = body["interpretation"]
    reason_codes = {fs.get("reason_code") for fs in interp.get("field_statuses") or []}
    limitations = set(interp.get("limitations") or [])
    assert "not_in_whitelist" in reason_codes or "not_in_whitelist" in limitations
    assert "unsupported_structured_filter" in reason_codes or "unsupported_structured_filter" in limitations
    combined = " ".join([str((interp.get("meta") or {}).get("guidance", ""))] + list(interp.get("limitations") or [])).lower()
    assert any(token in combined for token in ["campinas", "whitelist", "sal", "manual", "suport", "aproxima", "limita"])


async def test_mvp_estagio_marketing_digital_sp_equivalence(db_session, client, monkeypatch):
    """MVP 5: estágio marketing digital em SP (QA-01)."""
    await _insert(
        db_session,
        title="Estágio Marketing Digital",
        company="Agência SP",
        city=SAO_PAULO,
        contact_email="mvp5@example.com",
    )
    await _insert(
        db_session,
        title="Analista de Dados Remoto",
        company="Outra Empresa",
        city="Remoto",
    )

    interpretation = IntentContract(
        understood=UnderstoodIntent(
            q="marketing digital",
            city="São Paulo",
            seniority={"value": "estagio", "raw": "estágio"},
            sort=None,
        ),
        field_statuses=[
            FieldAssessment(
                field="q",
                understood="marketing digital",
                applied="marketing digital estágio",
                status=FieldStatus.APLICADO,
                reason_code="normalized",
                reason="Termo de busca textual composto/normalizado e aplicado.",
            ),
            FieldAssessment(
                field="city",
                understood="SP",
                applied="São Paulo",
                status=FieldStatus.APLICADO,
                reason_code="normalized",
                reason="Cidade normalizada e aplicada via whitelist segura.",
            ),
            FieldAssessment(
                field="seniority",
                understood={"value": "estagio", "raw": "estágio"},
                applied={"q_terms": ["estágio"]},
                status=FieldStatus.APROXIMADO,
                reason_code="textual_approximation_in_q",
                reason="Campo sem filtro estruturado nativo; usado como aproximação textual em q.",
            ),
        ],
        applied_params=AppliedParams(q="marketing digital estágio", city=SAO_PAULO, sort=None),
        limitations=["non_native_fields_limited", "textual_approximation_in_q"],
        meta={},
    )

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    chat = await client.post(
        "/api/v1/public/chat-search",
        json={"message": "estágio marketing digital em SP", "page": 1, "limit": 20},
    )
    assert chat.status_code == 200
    body = chat.json()

    jobs = await client.get(
        "/api/v1/public/jobs",
        params={"q": "marketing digital estágio", "city": "sao-paulo", "sort": "recentes", "page": 1, "limit": 20},
    )
    assert jobs.status_code == 200
    jobs_body = jobs.json()

    assert body["interpretation"]["applied_params"]["city"] == SAO_PAULO
    assert body["results"]["total"] == jobs_body["total"]
    assert [i["id"] for i in body["results"]["items"]] == [i["id"] for i in jobs_body["items"]]
    _assert_no_contacts(body["results"]["items"])