import pytest

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_scaffold_phase17():
    assert True


@pytest.mark.asyncio
async def test_social_worker_requires_cron_secret_configured(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "CRON_SECRET", "")
    resp = await client.post(
        "/api/v1/admin/social/worker",
        headers={"X-Cron-Secret": "qualquer"},
    )
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_social_worker_rejects_missing_or_wrong_secret(client, cron_secret_header):
    resp = await client.post("/api/v1/admin/social/worker")
    assert resp.status_code == 401

    resp = await client.post(
        "/api/v1/admin/social/worker",
        headers={"X-Cron-Secret": "errado"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_social_worker_processes_cycle_idempotent_with_secret(client, cron_secret_header, monkeypatch):
    calls = {"n": 0}

    async def fake_cycle(*, post_id=None, limit=20):
        calls["n"] += 1
        return {
            "claimed": 1,
            "processed": 1,
            "published": 1,
            "retried": 0,
            "failed_final": 0,
            "skipped": 0,
            "idempotent": 0,
        }

    monkeypatch.setattr("app.api.v1.admin.run_social_publish_cycle", fake_cycle)

    resp = await client.post("/api/v1/admin/social/worker", headers=cron_secret_header)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ok"
    assert body["claimed"] == 1
    assert body["processed"] == 1
    assert body["published"] == 1
    assert calls["n"] == 1

    # segunda chamada segue idempotente (endpoint não duplica por si; pipeline decide)
    resp = await client.post("/api/v1/admin/social/worker", headers=cron_secret_header)
    assert resp.status_code == 200
    assert calls["n"] == 2
