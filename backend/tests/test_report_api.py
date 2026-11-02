"""Report endpoint tests (TRST-02, D-06).

The report flow is accept-and-log by design: the endpoint never persists
anything and never reveals whether the job exists (no enumeration oracle).
These tests pin that contract plus the log shape (job_id + truncated,
single-line reason — no personal data beyond the resolved IP).
"""

import logging
import uuid


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
