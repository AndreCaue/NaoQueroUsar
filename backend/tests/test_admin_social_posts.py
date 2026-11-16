"""Integration/API tests for admin social post draft and approve flows (POST-03..06, D-04,D-08..D-12,D-17).

These tests are DB-backed and rely on the existing pytest harness in conftest.py.
Groq is never called; generation is mocked.
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.job import Job, JobStatus
from app.models.social_post import SocialPost, SocialPostStatus
from app.services.social.post_generation import (
    ACTIONABLE_SITE_URL_ERROR,
    brt_wall_time_to_utc,
)

VALID_CF_TOKEN = "token-de-teste"


async def _login(client, admin_password="test-password"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _seed_job(db_session, **overrides) -> Job:
    data = dict(
        title="Vaga Social",
        company="Empresa Confidencial",
        activities="Atuar no atendimento",
        requirements=None,
        salary="R$ 2.000",
        benefits="VT",
        city="São Paulo",
        contact_email="rh@empresa.com",
        contact_phone="+55 11 99999-0000",
        status=JobStatus.pending,
        source_snippet="fonte",
    )
    data.update(overrides)
    job = Job(**data)
    db_session.add(job)
    await db_session.flush()
    return job


def _draft_result(text="Texto gerado", origin="llm", warning=None):
    return SimpleNamespace(text=text, origin=origin, warning=warning)


async def _get_social_post(db_session, job_id: uuid.UUID) -> SocialPost | None:
    stmt = select(SocialPost).where(
        SocialPost.job_id == job_id, SocialPost.provider == "facebook"
    )
    return await db_session.scalar(stmt)


@pytest.mark.asyncio
async def test_social_post_get_generate_save_upsert_and_fields(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()

    async def fake_generate(job_arg, settings=None, client=None):
        return _draft_result(text="Rascunho IA https://site.exemplo/?vaga=x", origin="llm", warning=None)

    monkeypatch.setattr("app.api.v1.admin.generate_draft_for_job", fake_generate)

    # GET sem draft -> 404 claro
    resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}/social-post",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Rascunho social não encontrado"

    # POST generate cria/upsert draft e retorna campos esperados
    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["job_id"] == str(job.id)
    assert body["provider"] == "facebook"
    assert body["status"] == "draft"
    assert body["origin"] == "llm"
    assert body["saved"] is True
    assert body["frozen"] is False
    assert body["publish_mode"] == "publish_now"
    assert body["text"]

    # GET retorna draft salvo
    resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}/social-post",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["text"] == body["text"]

    # PUT save atualiza/upsert e aplica política (sem empresa/contato)
    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}/social-post",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": f"Texto editado Empresa Confidencial rh@empresa.com {job.contact_phone}",
            "publish_mode": "publish_now",
        },
    )
    assert resp.status_code == 200, resp.text
    saved = resp.json()
    assert saved["saved"] is True
    assert saved["frozen"] is False
    assert saved["status"] == "draft"
    assert "Empresa Confidencial" not in saved["text"]
    assert "rh@empresa.com" not in saved["text"]
    assert "99999-0000" not in saved["text"]
    assert f"?vaga={job.id}" in saved["text"]


@pytest.mark.asyncio
async def test_save_schedule_persists_brt_as_utc_and_publish_now_accepted(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()

    # schedule com data/hora BRT válidos
    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}/social-post",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "Post agendado",
            "publish_mode": "schedule",
            "scheduled_date": "2026-12-01",
            "scheduled_time": "10:30",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["publish_mode"] == "schedule"
    assert body["scheduled_at"] is not None
    expected = brt_wall_time_to_utc("2026-12-01", "10:30")
    got = datetime.fromisoformat(body["scheduled_at"].replace("Z", "+00:00"))
    assert got == expected
    assert got.tzinfo is not None

    post = await _get_social_post(db_session, job.id)
    assert post is not None
    assert post.scheduled_at == expected

    # publish_now aceito e limpa intenção agendada
    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}/social-post",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "Post agora", "publish_mode": "publish_now"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["publish_mode"] == "publish_now"
    assert resp.json()["scheduled_at"] is None


@pytest.mark.asyncio
async def test_mutation_rejected_when_draft_scheduled_frozen(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()

    # cria draft e aprova para congelar (scheduled)
    async def fake_generate(job_arg, settings=None, client=None):
        return _draft_result(text="Texto draft", origin="llm")

    monkeypatch.setattr("app.api.v1.admin.generate_draft_for_job", fake_generate)
    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert resp.status_code == 200

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["social"]["status"] == "registered"

    post = await _get_social_post(db_session, job.id)
    assert post is not None and post.status == SocialPostStatus.scheduled

    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Texto aprovado e bloqueado para envio."

    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}/social-post",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "Tentativa edição", "publish_mode": "publish_now"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Texto aprovado e bloqueado para envio."


@pytest.mark.asyncio
async def test_generate_returns_actionable_error_when_site_url_missing(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "")
    get_settings.cache_clear()

    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == ACTIONABLE_SITE_URL_ERROR
    assert (
        resp.json()["detail"]
        == "Link público indisponível: configure SITE_PUBLIC_URL no servidor para gerar o rascunho com link da vaga."
    )


@pytest.mark.asyncio
async def test_approve_without_draft_skips_social_and_keeps_job_published(client, db_session, admin_password):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["job"]["status"] == "published"
    assert body["social"]["status"] == "skipped"
    assert body["social"]["code"] == "no_draft"
    assert body["social"]["message"] == "Nenhum rascunho social salvo"

    get_resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "published"


@pytest.mark.asyncio
async def test_approve_with_draft_registers_scheduled(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()

    async def fake_generate(job_arg, settings=None, client=None):
        return _draft_result(text="Texto aprovado", origin="template_fallback", warning="w")

    monkeypatch.setattr("app.api.v1.admin.generate_draft_for_job", fake_generate)
    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert resp.status_code == 200

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["job"]["status"] == "published"
    assert body["social"]["status"] == "registered"

    post = await _get_social_post(db_session, job.id)
    assert post is not None
    assert post.status == SocialPostStatus.scheduled
    assert post.scheduled_at is not None


@pytest.mark.asyncio
async def test_approve_social_registration_failure_returns_warning_but_keeps_job_published(
    client, db_session, admin_password, monkeypatch
):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()

    async def fake_generate(job_arg, settings=None, client=None):
        return _draft_result(text="Texto draft", origin="llm")

    async def failing_mark_scheduled(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.api.v1.admin.generate_draft_for_job", fake_generate)
    monkeypatch.setattr("app.api.v1.admin.mark_scheduled", failing_mark_scheduled)

    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert resp.status_code == 200

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["job"]["status"] == "published"
    assert body["social"]["status"] == "warning"
    assert body["social"]["code"] == "social_registration_failed"

    get_resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "published"


@pytest.mark.asyncio
async def test_generate_uses_persisted_job_state_after_edit(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session, title="Titulo Antigo")
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()

    # edita job persistido antes de gerar
    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Titulo Novo Persistido"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Titulo Novo Persistido"

    captured = {}

    async def fake_generate(job_arg, settings=None, client=None):
        captured["title"] = job_arg.title
        return _draft_result(text=f"Post para {job_arg.title}", origin="llm")

    monkeypatch.setattr("app.api.v1.admin.generate_draft_for_job", fake_generate)

    resp = await client.post(
        f"/api/v1/admin/jobs/{job.id}/social-post/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"publish_mode": "publish_now"},
    )
    assert resp.status_code == 200, resp.text
    assert captured["title"] == "Titulo Novo Persistido"
    assert "Titulo Novo Persistido" in resp.json()["text"]


@pytest.mark.asyncio
async def test_save_schedule_invalid_datetime_returns_422(client, db_session, admin_password, monkeypatch):
    token = await _login(client, admin_password)
    job = await _seed_job(db_session)
    monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
    get_settings.cache_clear()

    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}/social-post",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "Post agendado",
            "publish_mode": "schedule",
            "scheduled_date": "2026-13-40",
            "scheduled_time": "99:99",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Escolha uma data e hora válidas para agendar."
