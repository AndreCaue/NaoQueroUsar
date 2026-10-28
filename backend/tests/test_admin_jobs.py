"""Admin job review integration tests (REVW-01..05 + auth gate).

Phase 5 — Admin Review Area.
Tests the admin CRUD endpoints: list by status, approve, update, delete,
and schema exposure (source_snippet + contact).

Auth: login via POST /api/v1/auth/login with password + cf_token.
Bearer token in Authorization header for all subsequent routes.
Routes are under /api/v1/admin/ prefix.
"""

import uuid

import pytest

from app.models.job import Job, JobStatus

VALID_CF_TOKEN = "token-de-teste"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _login(client, admin_password="test-password"):
    """Login and return access_token.  Headers: Authorization: Bearer {token}."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 43200
    assert body["access_token"]
    return body["access_token"]


# ---------------------------------------------------------------------------
# REVW-01: List by status + city filter + pagination
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_pending(client, db_session, admin_password):
    """GET /api/v1/admin/jobs?status=pending lists pending jobs."""
    token = await _login(client, admin_password)
    # Seed 2 pending jobs
    for i in range(2):
        job = Job(
            title=f"Vaga Pendente {i}",
            city="Remoto",
            contact_phone=f"+55 11 90000-{1000 + i}",
            status=JobStatus.pending,
        )
        db_session.add(job)
    await db_session.flush()

    resp = await client.get(
        "/api/v1/admin/jobs",
        headers={"Authorization": f"Bearer {token}"},
        params={"status": "pending"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_list_needs_review(client, db_session, admin_password):
    """GET /api/v1/admin/jobs?status=needs_review lists needs_review jobs."""
    token = await _login(client, admin_password)
    # Seed 2 needs_review jobs
    for i in range(2):
        job = Job(
            title=f"Vaga Needs Review {i}",
            city="São Paulo",
            contact_phone=f"+55 11 90000-{2000 + i}",
            status=JobStatus.needs_review,
        )
        db_session.add(job)
    await db_session.flush()

    resp = await client.get(
        "/api/v1/admin/jobs",
        headers={"Authorization": f"Bearer {token}"},
        params={"status": "needs_review"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_list_city_filter(client, db_session, admin_password):
    """GET /api/v1/admin/jobs?city=Remoto filters by city."""
    token = await _login(client, admin_password)
    # Seed pending jobs in different cities
    jobs = [
        Job(
            title="Vaga SP",
            city="São Paulo",
            contact_phone="+55 11 90000-1111",
            status=JobStatus.pending,
        ),
        Job(
            title="Vaga RJ",
            city="Rio de Janeiro",
            contact_phone="+55 21 90000-2222",
            status=JobStatus.pending,
        ),
        Job(
            title="Vaga BH",
            city="Belo Horizonte",
            contact_phone="+55 31 90000-3333",
            status=JobStatus.pending,
        ),
        # Remoto also counts - use Remoto as the filter city (no accent issues)
        Job(
            title="Vaga Remoto",
            city="Remoto",
            contact_phone="+55 11 90000-4444",
            status=JobStatus.pending,
        ),
    ]
    db_session.add_all(jobs)
    await db_session.flush()

    resp = await client.get(
        "/api/v1/admin/jobs",
        headers={"Authorization": f"Bearer {token}"},
        params={"city": "Remoto"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["city"] == "Remoto"


@pytest.mark.asyncio
async def test_list_pagination(client, db_session, admin_password):
    """GET /api/v1/admin/jobs with pagination (page/limit)."""
    token = await _login(client, admin_password)
    # Seed 5 pending jobs
    for i in range(5):
        job = Job(
            title=f"Vaga Paginacao {i}",
            city="Remoto",
            contact_phone=f"+55 11 90000-{5000 + i}",
            status=JobStatus.pending,
        )
        db_session.add(job)
    await db_session.flush()

    # Page 1, limit 2
    resp = await client.get(
        "/api/v1/admin/jobs",
        headers={"Authorization": f"Bearer {token}"},
        params={"status": "pending", "page": 1, "limit": 2},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["limit"] == 2
    assert body["total"] == 5
    assert len(body["items"]) == 2

    # Page 2, limit 2
    resp = await client.get(
        "/api/v1/admin/jobs",
        headers={"Authorization": f"Bearer {token}"},
        params={"status": "pending", "page": 2, "limit": 2},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 2
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_list_pagination_limit_cap(client, admin_password):
    """Limit above 100 is rejected with 422."""
    token = await _login(client, admin_password)
    resp = await client.get(
        "/api/v1/admin/jobs",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 101},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# REVW-02: Approve
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve(client, db_session, admin_password):
    """PATCH /api/v1/admin/jobs/{id}/approve changes status to published."""
    token = await _login(client, admin_password)
    job = Job(
        title="Vaga Aprovar",
        city="São Paulo",
        contact_phone="+55 11 90000-5555",
        status=JobStatus.pending,
    )
    db_session.add(job)
    await db_session.flush()

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "published"
    # Verify via GET
    get_resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "published"


@pytest.mark.asyncio
async def test_approve_404(client, db_session, admin_password):
    """PATCH /api/v1/admin/jobs/{id}/approve non-existent → 404."""
    token = await _login(client, admin_password)
    resp = await client.patch(
        f"/api/v1/admin/jobs/{uuid.uuid4()}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# REVW-03: Update
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update(client, db_session, admin_password):
    """PUT /api/v1/admin/jobs/{id} updates all fields."""
    token = await _login(client, admin_password)
    job = Job(
        title="Vaga Update",
        city="Remoto",
        contact_phone="+55 11 90000-6666",
        status=JobStatus.pending,
    )
    db_session.add(job)
    await db_session.flush()

    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Vaga Atualizada",
            "company": "Empresa X",
            "activities": "Atividades atualizadas",
            "requirements": "Requisitos atualizados",
            "salary": "R$ 5.000",
            "benefits": "Vale refeição + vale transporte",
            "city": "São Paulo",
            "contact_email": "contato@empresa.com",
            "contact_phone": "",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Vaga Atualizada"
    assert body["company"] == "Empresa X"
    assert body["city"] == "São Paulo"
    assert body["contact_email"] == "contato@empresa.com"


@pytest.mark.asyncio
async def test_update_no_contact_422(client, db_session, admin_password):
    """PUT clearing both contacts → 422 with pt-BR detail."""
    token = await _login(client, admin_password)
    job = Job(
        title="Vaga Update",
        city="Remoto",
        contact_phone="+55 11 90000-6666",
        status=JobStatus.pending,
    )
    db_session.add(job)
    await db_session.flush()

    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Vaga Atualizada",
            "contact_email": "",
            "contact_phone": "",
        },
    )
    assert resp.status_code == 422
    assert " contato" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_update_bad_city_422(client, db_session, admin_password):
    """PUT with invalid city → 422 with pt-BR detail."""
    token = await _login(client, admin_password)
    job = Job(
        title="Vaga Update",
        city="Remoto",
        contact_phone="+55 11 90000-6666",
        status=JobStatus.pending,
    )
    db_session.add(job)
    await db_session.flush()

    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Vaga Atualizada",
            "city": "Cidade Inexistente",
        },
    )
    assert resp.status_code == 422
    assert "Cidade invalida" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# REVW-04: Delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete(client, db_session, admin_password):
    """DELETE /api/v1/admin/jobs/{id} hard delete."""
    token = await _login(client, admin_password)
    job = Job(
        title="Vaga Excluir",
        city="São Paulo",
        contact_phone="+55 11 90000-7777",
        status=JobStatus.pending,
    )
    db_session.add(job)
    await db_session.flush()

    resp = await client.delete(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    # Verify deletion via GET → 404
    get_resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_404(client, db_session, admin_password):
    """DELETE non-existent → 404."""
    token = await _login(client, admin_password)
    resp = await client.delete(
        f"/api/v1/admin/jobs/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# REVW-05: Schema includes source_snippet + contact
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_schema_includes_snippet_contact(client, db_session, admin_password):
    """JobAdmin schema includes source_snippet and contact fields."""
    token = await _login(client, admin_password)
    job = Job(
        title="Vaga Schema",
        city="Remoto",
        contact_email="teste@email.com",
        contact_phone="+55 11 90000-8888",
        status=JobStatus.pending,
        source_snippet="Texto-fonte de exemplo para teste.",
    )
    db_session.add(job)
    await db_session.flush()

    resp = await client.get(
        f"/api/v1/admin/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "source_snippet" in body, "JobAdmin must include source_snippet"
    assert "contact_email" in body, "JobAdmin must include contact_email"
    assert "contact_phone" in body, "JobAdmin must include contact_phone"
    assert body["source_snippet"] == "Texto-fonte de exemplo para teste."


# ---------------------------------------------------------------------------
# Auth gate: all admin routes reject unauthenticated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_requires_auth(client, db_session, admin_password):
    """All admin job routes return 401 without Bearer token."""
    # List
    resp = await client.get("/api/v1/admin/jobs")
    assert resp.status_code == 401

    # Approve
    job = Job(
        title="Vaga",
        city="Remoto",
        contact_phone="+55 11 90000-9999",
        status=JobStatus.pending,
    )
    db_session.add(job)
    await db_session.flush()

    resp = await client.patch(
        f"/api/v1/admin/jobs/{job.id}/approve",
    )
    assert resp.status_code == 401

    # Update
    resp = await client.put(
        f"/api/v1/admin/jobs/{job.id}",
    )
    assert resp.status_code == 401

    # Delete
    resp = await client.delete(
        f"/api/v1/admin/jobs/{job.id}",
    )
    assert resp.status_code == 401