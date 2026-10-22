"""Auth criteria tests (ADMN-01/02/03): login ok/bad + admin guard 401/200.

Phase 3 (SECR-03): the admin login is behind the same anti-bot gate as the
contact reveal — rate limit → Turnstile → password → JWT. The order is the
contract (D-17): **the password is never compared before the Turnstile
verifies**, so an attacker without a valid token cannot even probe the
password.
"""

from app.core.config import get_settings

# Any non-empty token works: the Siteverify client is stubbed by the
# ``fake_turnstile`` fixture, so the token is never really validated here.
VALID_CF_TOKEN = "token-de-teste"


async def test_login_ok_returns_bearer_token(client, admin_password):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 43200
    assert body["access_token"]


async def test_login_wrong_password_401(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": "senha-errada", "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 401


async def test_admin_me_without_header_401(client):
    resp = await client.get("/api/v1/admin/me")
    assert resp.status_code == 401


async def test_admin_me_with_tampered_token_401(client):
    resp = await client.get(
        "/api/v1/admin/me",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert resp.status_code == 401


async def test_admin_me_with_valid_token_returns_admin_claims(
    client, admin_password
):
    login = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    token = login.json()["access_token"]

    resp = await client.get(
        "/api/v1/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sub"] == "admin"
    assert body["role"] == "admin"


# ---------------------------------------------------------------------------
# SECR-03 — the login gate (Phase 3, plan 03-04)
# ---------------------------------------------------------------------------


async def test_login_without_cf_token_returns_422(client, admin_password):
    """The Turnstile token is mandatory — a login without it never reaches the
    password check."""
    resp = await client.post(
        "/api/v1/auth/login", json={"password": admin_password}
    )
    assert resp.status_code == 422


async def test_login_rejected_turnstile_returns_403(client, admin_password, fake_turnstile):
    """A refused challenge is a 403 with the anti-bot copy."""
    fake_turnstile.outcome = "timeout-or-duplicate"

    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Verificação anti-bot falhou — tente novamente"


async def test_login_unavailable_turnstile_returns_403(client, admin_password, fake_turnstile):
    """An unavailable verification is a 403 too, but with its own copy — never
    "Senha inválida" (D-18)."""
    fake_turnstile.outcome = "error"

    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 403
    assert (
        resp.json()["detail"]
        == "Verificação indisponível — tente novamente em instantes"
    )


async def test_login_turnstile_failure_does_not_reach_password_check(
    client, fake_turnstile
):
    """D-17: the password is only compared *after* the Turnstile passes.

    A refused token with a wrong password is a 403, not a 401 — the 401 would
    prove that the password was checked (and would leak whether the password
    is right).
    """
    fake_turnstile.outcome = "timeout-or-duplicate"

    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": "senha-errada", "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Verificação anti-bot falhou — tente novamente"


async def test_login_wrong_password_with_valid_token_returns_401(client, fake_turnstile):
    """With a valid token, a wrong password is the 401 we always had."""
    fake_turnstile.outcome = "success"

    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": "senha-errada", "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Senha inválida"


async def test_login_token_minted_for_another_action_returns_403(
    client, admin_password, fake_turnstile
):
    """Action binding (T-03-16): a token minted for ``reveal`` cannot open the
    login — the Siteverify is asked for the ``login`` action."""
    fake_turnstile.action = "reveal"

    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Verificação anti-bot falhou — tente novamente"


async def test_login_rate_limit_returns_429(client, admin_password, monkeypatch):
    """The 6th attempt from the same IP in the window is a 429 (D-06/D-08).

    The env knob is read on every request, so the test sets it explicitly and
    restores the environment afterwards — the knob must not leak into the
    other tests.
    """
    monkeypatch.setenv("LOGIN_RATE_LIMIT", "5/minute")
    get_settings.cache_clear()
    try:
        for _ in range(5):
            resp = await client.post(
                "/api/v1/auth/login",
                json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
            )
            assert resp.status_code == 200

        resp = await client.post(
            "/api/v1/auth/login",
            json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
        )
        assert resp.status_code == 429
        assert (
            resp.json()["detail"]
            == "Muitas tentativas. Aguarde alguns segundos e tente novamente."
        )
        assert resp.headers.get("Retry-After")
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
