"""Report endpoint tests (TRST-02, D-06).

The report flow is accept-and-log by design: the endpoint never persists
anything and never reveals whether the job exists (no enumeration oracle).
These tests pin that contract plus the log shape (job_id + truncated,
single-line reason — no personal data beyond the resolved IP).
"""

import logging
import uuid
from sqlalchemy import text


async def test_report_without_body_returns_ok(client):
    resp = await client.post(f"/api/v1/public/jobs/{uuid.uuid4()}/report")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_report_with_reason_returns_ok_and_logs(client, caplog):
    job_id = uuid.uuid4()
    with caplog.at_level(logging.INFO, logger="app.api.v1.public"):
        resp = await client.post(
            f"/api/v1/public/jobs/{job_id}/report",
            json={"reason": "Salário irreal\nLiguei e não atenderam"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    reports = [r for r in caplog.records if r.getMessage().startswith("job_report")]
    assert len(reports) == 1
    message = reports[0].getMessage()
    assert f"job_id={job_id}" in message
    # Newlines are collapsed so a report cannot forge log lines.
    assert "\n" not in message
    assert "Salário irreal" in message


async def test_report_reason_above_500_chars_is_rejected(client):
    resp = await client.post(
        f"/api/v1/public/jobs/{uuid.uuid4()}/report",
        json={"reason": "x" * 501},
    )
    assert resp.status_code == 422


async def test_report_unknown_job_still_returns_ok(client):
    """No enumeration oracle: a made-up id is indistinguishable from a real one."""
    resp = await client.post(
        f"/api/v1/public/jobs/{uuid.uuid4()}/report",
        json={"reason": "suspeita"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_report_whitespace_only_reason_is_treated_as_absent(client, caplog):
    job_id = uuid.uuid4()
    with caplog.at_level(logging.INFO, logger="app.api.v1.public"):
        resp = await client.post(
            f"/api/v1/public/jobs/{job_id}/report",
            json={"reason": "   "},
        )
    assert resp.status_code == 200
    reports = [r for r in caplog.records if r.getMessage().startswith("job_report")]
    assert len(reports) == 1
    assert "reason=None" in reports[0].getMessage()


async def test_report_reason_at_500_chars_is_accepted_and_logged(client, caplog):
    """TRST-11: the cap is inclusive and the log keeps the whole reason."""
    job_id = uuid.uuid4()
    reason = "x" * 500
    with caplog.at_level(logging.INFO, logger="app.api.v1.public"):
        resp = await client.post(
            f"/api/v1/public/jobs/{job_id}/report",
            json={"reason": reason},
        )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    reports = [r for r in caplog.records if r.getMessage().startswith("job_report")]
    assert len(reports) == 1
    assert reason in reports[0].getMessage()


async def test_report_persists_nothing(client, db_session):
    """TRST-11: accept-and-log only — there is no reports table to write to."""
    resp = await client.post(
        f"/api/v1/public/jobs/{uuid.uuid4()}/report",
        json={"reason": "spam"},
    )

    assert resp.status_code == 200

    reports_table = await db_session.scalar(text("SELECT to_regclass('public.reports')"))
    assert reports_table is None


async def test_report_is_rate_limited_per_ip(client):
    """The 6th report inside a minute is answered 429 (WR-01)."""
    for _ in range(5):
        resp = await client.post(f"/api/v1/public/jobs/{uuid.uuid4()}/report")
        assert resp.status_code == 200

    resp = await client.post(f"/api/v1/public/jobs/{uuid.uuid4()}/report")
    assert resp.status_code == 429
    assert resp.json()["detail"]
    assert resp.headers.get("Retry-After")
