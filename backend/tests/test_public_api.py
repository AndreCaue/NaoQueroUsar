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


# --- CORS: the 429 countdown depends on a readable Retry-After (D-10b) -------


async def test_cors_exposes_retry_after_on_actual_response(client, seed_published_job):
    """Starlette only sets Expose-Headers on real responses, never on OPTIONS.

    The reveal UI reads `Retry-After` from a cross-origin 429 (localhost:3000 →
    localhost:8000). Without `expose_headers=["Retry-After"]` that read returns
    `null` and the cooldown silently falls back to 10 s, so this asserts the
    header on a regular GET (B-06).
    """
    resp = await client.get(
        "/api/v1/public/jobs",
        params={"limit": 1},
        headers={"Origin": "http://localhost:3000"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    exposed = resp.headers.get("access-control-expose-headers", "")
    assert "retry-after" in exposed.lower()


async def test_cors_preflight_allows_reveal_post(client):
    """The reveal POST is cross-origin JSON, so the preflight must allow it."""
    resp = await client.options(
        f"/api/v1/public/jobs/{uuid.uuid4()}/reveal-contact",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.status_code == 200
    allowed_methods = resp.headers.get("access-control-allow-methods", "")
    assert "POST" in allowed_methods.upper()
    # Deliberately NO expose-headers assertion here: Starlette omits it on the
    # preflight reply (see the test above for where it actually appears).

