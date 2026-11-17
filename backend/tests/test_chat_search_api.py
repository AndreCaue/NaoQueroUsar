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
