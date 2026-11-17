"""Contract, resilience and safety tests for POST /api/v1/public/chat-search (API-01..03).

LLM/intent extraction is always mocked (no network). DB-backed assertions rely on
the shared test fixtures (real Postgres test DB when configured).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text

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