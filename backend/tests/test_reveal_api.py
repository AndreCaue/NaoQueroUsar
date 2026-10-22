"""Tests for the contact-reveal endpoint (Phase 3, PUBL-05 / SECR-01 / SECR-02).

The contact of a job leaves the database through **one** route only:
``POST /api/v1/public/jobs/{id}/reveal-contact``. Everything else the public
surface serves is contact-free, and the reveal itself is gated by a
server-side Turnstile verification plus a per-IP rate limit.

The reading order of this file *is* the order of the rules (D-03):

1. **404** — the job does not exist, is not published or is expired, and the
   answer comes *before* any Cloudflare call, so a made-up UUID never spends
   a verification;
2. **403** — the challenge was refused, the verification is unavailable or the
   token was minted for another flow. The body never carries a contact;
3. **422** — the body is invalid;
4. **429** — too many attempts from the same IP;
5. **200** — the contact, and only then.

The suite stays 100% offline: the real verifier is replaced by the
``FakeTurnstileVerifier`` through ``dependency_overrides`` (see ``conftest``),
so no request ever reaches Cloudflare.
"""

from __future__ import annotations

import uuid

from app.core.config import get_settings
from app.models.job import Job, JobStatus

REVEAL_PATH = "/api/v1/public/jobs/{job_id}/reveal-contact"
TOKEN = {"cf_token": "a-valid-looking-token"}


# ---------------------------------------------------------------------------
# 404 — the job lookup comes before the Turnstile call (D-03)
# ---------------------------------------------------------------------------


async def test_reveal_unknown_job_returns_404_without_calling_turnstile(
    client, fake_turnstile
):
    """A made-up UUID is a 404 and never reaches Cloudflare (D-03)."""
    resp = await client.post(
        REVEAL_PATH.format(job_id=uuid.uuid4()),
        json=TOKEN,
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Vaga não encontrada ou expirada."
    # The Cloudflare quota is not spent on ids that do not exist.
    assert fake_turnstile.calls == []


async def test_reveal_pending_job_returns_404(client, fake_turnstile, seed_pending_job):
    """A job that is not published yet is invisible to the reveal (D-17)."""
    resp = await client.post(
        REVEAL_PATH.format(job_id=seed_pending_job.id),
        json=TOKEN,
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Vaga não encontrada ou expirada."
    assert fake_turnstile.calls == []


async def test_reveal_expired_job_returns_404(client, fake_turnstile, seed_expired_job):
    """An expired job cannot be revealed either (14-day lifetime)."""
    resp = await client.post(
        REVEAL_PATH.format(job_id=seed_expired_job.id),
        json=TOKEN,
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Vaga não encontrada ou expirada."
    assert fake_turnstile.calls == []


# ---------------------------------------------------------------------------
# 403 — the gate never opens by accident (D-13)
# ---------------------------------------------------------------------------


async def test_reveal_rejected_token_returns_403(client, fake_turnstile, seed_published_job):
    """A refused challenge is a 403 and the contact stays hidden."""
    fake_turnstile.outcome = "timeout-or-duplicate"
    fake_turnstile.error_codes = ["timeout-or-duplicate"]

    resp = await client.post(
        REVEAL_PATH.format(job_id=seed_published_job.id),
        json=TOKEN,
    )

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Verificação anti-bot falhou — tente novamente"
    # The whole point: no contact leaks in the refused answer.
    assert "contact_email" not in resp.text
    assert "contact_phone" not in resp.text


async def test_reveal_unavailable_verification_returns_403(
    client, fake_turnstile, seed_published_job
):
    """A broken verification says "unavailable", not "anti-bot failed" (D-18)."""
    fake_turnstile.outcome = "error"
    fake_turnstile.error_codes = ["internal-error"]

    resp = await client.post(
        REVEAL_PATH.format(job_id=seed_published_job.id),
        json=TOKEN,
    )

    assert resp.status_code == 403
    assert resp.json()["detail"] == (
        "Verificação indisponível — tente novamente em instantes"
    )
    assert "contact_email" not in resp.text
    assert "contact_phone" not in resp.text


async def test_reveal_action_mismatch_returns_403(
    client, fake_turnstile, seed_published_job
):
    """A token minted for another flow does not open the reveal (T-03-03)."""
    fake_turnstile.action = "login"

    resp = await client.post(
        REVEAL_PATH.format(job_id=seed_published_job.id),
        json=TOKEN,
    )

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Verificação anti-bot falhou — tente novamente"
    assert "contact_email" not in resp.text
    assert "contact_phone" not in resp.text


# ---------------------------------------------------------------------------
# 422 — the body is validated before anything else
# ---------------------------------------------------------------------------


async def test_reveal_requires_cf_token(client):
    """A body without the token is refused by the schema (422)."""
    resp = await client.post(
        REVEAL_PATH.format(job_id=uuid.uuid4()),
        json={},
    )

    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 429 — the per-IP rate limit (D-05/D-06/D-08)
# ---------------------------------------------------------------------------


async def test_reveal_rate_limit_returns_429(
    client, seed_published_job, monkeypatch
):
    """The third attempt of the same IP in the window is a 429 (D-05)."""
    monkeypatch.setenv("REVEAL_RATE_LIMIT", "2/minute")
    get_settings.cache_clear()
    try:
        url = REVEAL_PATH.format(job_id=seed_published_job.id)

        assert (await client.post(url, json=TOKEN)).status_code == 200
        assert (await client.post(url, json=TOKEN)).status_code == 200

        resp = await client.post(url, json=TOKEN)

        assert resp.status_code == 429
        assert resp.json()["detail"] == (
            "Muitas tentativas. Aguarde alguns segundos e tente novamente."
        )
        assert resp.headers.get("Retry-After")

        # The bucket is keyed by the **IP**, not by the URL: another job from
        # the same client is blocked too (D-05/D-10). Otherwise a scraper
        # would walk through the job ids and never hit the limit.
        other = await client.post(
            REVEAL_PATH.format(job_id=uuid.uuid4()),
            json=TOKEN,
        )
        assert other.status_code == 429
    finally:
        # The env knob must not leak into the next test — the default
        # (10/minute) is asserted by the plan 03-01 suite.
        monkeypatch.undo()
        get_settings.cache_clear()


# ---------------------------------------------------------------------------
# 200 — the contact, and only then
# ---------------------------------------------------------------------------


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
        json=TOKEN,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == str(job.id)
    assert body["contact_email"] == "vagas@empresa-b.com.br"
    # The phone comes back raw (E.164) — the wa.me link is the frontend's job.
    assert body["contact_phone"] == "+5511900000004"
    assert len(fake_turnstile.calls) == 1


# ---------------------------------------------------------------------------
# The public read surface stays contact-free (PUBL-05 / D-18)
# ---------------------------------------------------------------------------


async def test_public_job_payload_has_no_contact(client, seed_published_job):
    """The public detail never carries the contact (guard of PUBL-05)."""
    resp = await client.get(f"/api/v1/public/jobs/{seed_published_job.id}")

    assert resp.status_code == 200
    assert "contact_email" not in resp.text
    assert "contact_phone" not in resp.text
