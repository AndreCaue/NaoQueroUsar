"""API-level tests for POST /api/v1/admin/extract (D-01..D-08).

Covers auth gate, happy path with persisted pending/needs_review rows and
source_snippet, discarded-only-in-summary, divergence/truncation alerts,
size/empty validation, missing GROQ_API_KEY, and single-transaction rollback
on commit failure (nada foi gravado).
"""

from typing import Any

import pytest

from app.api.v1 import extract as extract_module
from app.core.config import get_settings
from app.models.job import Job, JobStatus
from app.schemas.extract import ALERT_DISCARDED, ALERT_DIVERGENCE, ALERT_TRUNCATED
from app.services.extraction.blocklist import BLOCKED_TERM_ERROR
from app.services.extraction.client import ExtractionAPIError
from app.services.extraction.extractor import CandidateOutcome, ExtractionResult
from app.services.extraction.schema import JobCandidate


def _make_candidate(**overrides: Any) -> JobCandidate:
    data: dict[str, Any] = {
        "title": "Desenvolvedor Backend",
        "company": "Acme",
        "activities": "APIs em Python",
        "requirements": "FastAPI, SQLAlchemy",
        "salary": "A combinar",
        "benefits": None,
        "city": "São Paulo",
        "contact_email": "rh@acme.com.br",
        "contact_phone": None,
        "source_snippet": "Desenvolvedor Backend - Acme - São Paulo - rh@acme.com.br",
        "raw_city": "São Paulo",
    }
    data.update(overrides)
    return JobCandidate(**data)


def _make_result(**overrides: Any) -> ExtractionResult:
    candidate_save = _make_candidate()
    candidate_review = _make_candidate(
        title="Estágio Suporte",
        company=None,
        activities="Atendimento",
        requirements=None,
        salary=None,
        benefits=None,
        city="Remoto",
        contact_email=None,
        contact_phone="+55 11 99999-0000",
        source_snippet="Estágio Suporte - Remoto - +55 11 99999-0000",
        raw_city="Remoto",
    )
    data: dict[str, Any] = {
        "kept": [
            (candidate_save, CandidateOutcome.save),
            (candidate_review, CandidateOutcome.save_needs_review),
        ],
        "discarded": [
            {"reason": "sem título ou sem contato", "snippet": "Vaga sem dados"},
        ],
        "detected_count": 3,
        "extracted_count": 2,
        "truncated": True,
        "divergent": True,
        "model_used": "openai/gpt-oss-20b",
        "chunks": 1,
    }
    data.update(overrides)
    return ExtractionResult(**data)


async def _get_admin_token(client, admin_password: str) -> str:
    # The admin login is behind the Turnstile gate (SECR-03) — the token is
    # stubbed by the ``fake_turnstile`` fixture, so any non-empty value works.
    login = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": "token-de-teste"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


async def test_extract_requires_auth(client):
    resp = await client.post("/api/v1/admin/extract", json={"text": "qualquer coisa"})
    assert resp.status_code == 401


async def test_extract_invalid_token_401(client):
    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "qualquer coisa"},
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert resp.status_code == 401


async def test_extract_happy_path_persists_and_summarizes(client, admin_password, db_session, monkeypatch):
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    result = _make_result()
    async def fake_extract_jobs(text, s):
        assert text == "texto bruto de vagas"
        return result
    monkeypatch.setattr(extract_module, "extract_jobs", fake_extract_jobs)

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "texto bruto de vagas"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["saved_pending"] == 1
    assert body["saved_needs_review"] == 1
    assert body["extracted_count"] == 2
    assert body["detected_count"] == 3
    assert body["divergent"] is True
    assert body["truncated"] is True
    assert body["model_used"] == "openai/gpt-oss-20b"
    assert body["chunks"] == 1

    # Discarded only in summary, never in DB
    assert len(body["discarded"]) == 1
    assert body["discarded"][0]["reason"] == "sem título ou sem contato"
    assert body["discarded"][0]["snippet"] == "Vaga sem dados"

    # Alerts: divergence + truncation + discarded count
    assert ALERT_DIVERGENCE.format(detected_count=3, extracted_count=2) in body["alerts"]
    assert ALERT_TRUNCATED in body["alerts"]
    assert ALERT_DISCARDED.format(n=1) in body["alerts"]

    # DB state: two rows, correct statuses and source_snippet persisted
    from sqlalchemy import select
    jobs = list((await db_session.execute(select(Job))).scalars().all())
    assert len(jobs) == 2
    by_title = {j.title: j for j in jobs}
    assert by_title["Desenvolvedor Backend"].status == JobStatus.pending
    assert by_title["Estágio Suporte"].status == JobStatus.needs_review
    assert by_title["Desenvolvedor Backend"].source_snippet is not None
    assert "rh@acme.com.br" in by_title["Desenvolvedor Backend"].source_snippet


async def test_extract_discarded_not_inserted(client, admin_password, db_session, monkeypatch):
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    result = _make_result(
        kept=[],
        discarded=[
            {"reason": "sem título ou sem contato", "snippet": "abc"},
            {"reason": "sem título ou sem contato", "snippet": "def"},
        ],
        detected_count=2,
        extracted_count=0,
        truncated=False,
        divergent=True,
        chunks=1,
    )
    async def fake_extract_jobs(text, s):
        return result
    monkeypatch.setattr(extract_module, "extract_jobs", fake_extract_jobs)

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "texto"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["saved_pending"] == 0
    assert body["saved_needs_review"] == 0
    assert len(body["discarded"]) == 2

    from sqlalchemy import select
    jobs = list((await db_session.execute(select(Job))).scalars().all())
    assert jobs == []


async def test_extract_413_oversize(client, admin_password, monkeypatch):
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(settings, "EXTRACT_MAX_TEXT_BYTES", 10)

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "12345678901"},  # 11 bytes
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 413


async def test_extract_422_blocked_term_skips_groq(client, admin_password, monkeypatch):
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    calls: list[str] = []

    async def should_not_run(text, s):
        calls.append(text)
        raise AssertionError("extract_jobs não deveria ser chamado para texto bloqueado")

    monkeypatch.setattr(extract_module, "extract_jobs", should_not_run)

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "Vaga: jacira\n  chavare — contato segredo-xyz@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert isinstance(detail, str)
    assert detail == BLOCKED_TERM_ERROR
    assert "JACIRA CHAVARE" in detail
    assert "segredo-xyz" not in resp.text  # o texto colado nunca é ecoado
    assert calls == []


async def test_extract_413_wins_over_blocklist(client, admin_password, monkeypatch):
    """The size gate runs before the blocklist: a blocked AND oversized text is 413."""
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(settings, "EXTRACT_MAX_TEXT_BYTES", 10)

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "jacira chavare"},  # 14 bytes, also blocked
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 413


async def test_extract_422_empty_body_validation(client, admin_password, monkeypatch):
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


async def test_extract_503_no_groq_key(client, admin_password, monkeypatch):
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "qualquer coisa"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 503
    assert "GROQ_API_KEY" in resp.text


async def test_extract_504_timeout(client, admin_password, monkeypatch):
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    async def slow(*args, **kwargs):
        import asyncio as _asyncio
        await _asyncio.sleep(10)
        return _make_result()
    monkeypatch.setattr(extract_module, "extract_jobs", slow)
    monkeypatch.setattr(settings, "EXTRACT_TIMEOUT_SECONDS", 0)

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "texto"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 504


async def test_extract_422_from_extractor_value_error(client, admin_password, monkeypatch):
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    async def bad(*args, **kwargs):
        raise ValueError("Texto vazio após normalização")
    monkeypatch.setattr(extract_module, "extract_jobs", bad)

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "texto"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


async def test_extract_503_from_extraction_api_error(client, admin_password, monkeypatch):
    """WR-02: the client's curated pt-BR failure must reach the admin as 503."""
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    detail = (
        "Limite de taxa do Groq atingido (429) mesmo após retries — "
        "aguarde alguns minutos e tente novamente (limite de taxa)."
    )

    async def boom(*args, **kwargs):
        raise ExtractionAPIError(detail)

    monkeypatch.setattr(extract_module, "extract_jobs", boom)

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "texto"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 503
    assert resp.json()["detail"] == detail


async def test_extract_commit_failure_rolls_back_no_rows(client, admin_password, db_session, monkeypatch):
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    result = _make_result(kept=[(_make_candidate(), CandidateOutcome.save)], discarded=[], divergent=False, truncated=False, detected_count=1, extracted_count=1, chunks=1)
    async def fake_extract_jobs(text, s):
        return result
    monkeypatch.setattr(extract_module, "extract_jobs", fake_extract_jobs)

    async def boom(*args, **kwargs):
        raise RuntimeError("db down")
    monkeypatch.setattr(extract_module, "bulk_create_pending", boom)

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "texto"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 500
    assert "nada foi gravado" in resp.text.lower()

    from sqlalchemy import select
    jobs = list((await db_session.execute(select(Job))).scalars().all())
    assert jobs == []
