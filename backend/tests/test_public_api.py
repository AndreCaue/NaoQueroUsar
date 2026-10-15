"""Public read-surface criteria tests (criterion 4, D-14..D-18).

Proves: only published + non-expired jobs are listed, the payload NEVER
contains contact fields (list or detail), pending/expired/unknown detail is a
404, and pagination is bounded (limit cap 50).
"""

import uuid

from app.models.job import Job, JobStatus


async def test_list_returns_only_published_non_expired(
    client, seed_published_job, seed_pending_job, seed_expired_job
):
    resp = await client.get("/api/v1/public/jobs")
    assert resp.status_code == 200
    body = resp.json()

    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(seed_published_job.id)


async def test_list_payload_has_no_contact_fields(client, seed_published_job):
    resp = await client.get("/api/v1/public/jobs")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items, "expected at least one published job"
    for item in items:
        assert "contact_email" not in item
        assert "contact_phone" not in item


async def test_detail_published_returns_non_contact_fields(
    client, seed_published_job
):
    resp = await client.get(f"/api/v1/public/jobs/{seed_published_job.id}")
    assert resp.status_code == 200
    item = resp.json()
    assert item["id"] == str(seed_published_job.id)
    assert item["title"] == seed_published_job.title
    assert item["city"] == seed_published_job.city
    assert "contact_email" not in item
    assert "contact_phone" not in item


async def test_detail_pending_is_404(client, seed_pending_job):
    resp = await client.get(f"/api/v1/public/jobs/{seed_pending_job.id}")
    assert resp.status_code == 404


async def test_detail_expired_is_404(client, seed_expired_job):
    resp = await client.get(f"/api/v1/public/jobs/{seed_expired_job.id}")
    assert resp.status_code == 404


async def test_detail_unknown_is_404(client):
    resp = await client.get(f"/api/v1/public/jobs/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_pagination_limit_and_total(client, db_session, seed_published_job):
    # A second published job so there is something to page over.
    second = Job(
        title="Vaga Publicada 2 — Teste",
        city="Remoto",
        contact_phone="+55 11 90000-0009",
        status=JobStatus.published,
    )
    db_session.add(second)
    await db_session.flush()

    resp = await client.get("/api/v1/public/jobs", params={"limit": 1, "page": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["limit"] == 1
    assert body["total"] == 2
    assert len(body["items"]) == 1


async def test_limit_above_cap_is_rejected(client):
    resp = await client.get("/api/v1/public/jobs", params={"limit": 999})
    assert resp.status_code == 422
