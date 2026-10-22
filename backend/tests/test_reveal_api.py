"""Tests for the contact-reveal endpoint (Phase 3, PUBL-05 / SECR-01 / SECR-02).

The contact of a job leaves the database through **one** route only:
``POST /api/v1/public/jobs/{id}/reveal-contact``. Everything else the public
surface serves is contact-free, and the reveal itself is gated by a
server-side Turnstile verification plus a per-IP rate limit.

Two properties are worth more than the happy path here:

- **The job lookup comes before the Turnstile call (D-03).** A random UUID
  must be answered with a 404 *without* spending a Cloudflare verification —
  otherwise a scraper can burn the quota with made-up ids.
- **The gate never opens by accident (D-13).** A rejected, replayed or
  expired token answers 403 and the response body carries no contact at all.

The suite stays 100% offline: the real verifier is replaced by the
``FakeTurnstileVerifier`` through ``dependency_overrides`` (see ``conftest``),
so no request ever reaches Cloudflare.
"""

from __future__ import annotations

import uuid

from app.models.job import Job, JobStatus

REVEAL_PATH = "/api/v1/public/jobs/{job_id}/reveal-contact"


async def test_reveal_unknown_job_returns_404_without_calling_turnstile(
    client, fake_turnstile
):
    """A made-up UUID is a 404 and never reaches Cloudflare (D-03)."""
    resp = await client.post(
        REVEAL_PATH.format(job_id=uuid.uuid4()),
        json={"cf_token": "a-valid-looking-token"},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Vaga não encontrada ou expirada."
    # The Cloudflare quota is not spent on ids that do not exist.
    assert fake_turnstile.calls == []


async def test_reveal_returns_contact(client, fake_turnstile, db_session):
    """A published job behind a valid token gives the contact back (200)."""
    job = Job(
        title="Vaga Com Contato — Teste",
        company="Empresa B",
        city="Remoto",
        contact_email="vagas@empresa-b.com.br",
        contact_phone="+5511900000004",
        status=JobStatus.published,
    )
    db_session.add(job)
    await db_session.flush()

    resp = await client.post(
        REVEAL_PATH.format(job_id=job.id),
        json={"cf_token": "a-valid-looking-token"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == str(job.id)
    assert body["contact_email"] == "vagas@empresa-b.com.br"
    # The phone comes back raw (E.164) — the wa.me link is the frontend's job.
    assert body["contact_phone"] == "+5511900000004"
    assert len(fake_turnstile.calls) == 1
