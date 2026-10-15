"""Auth criteria tests (ADMN-01/02/03): login ok/bad + admin guard 401/200."""


async def test_login_ok_returns_bearer_token(client, admin_password):
    resp = await client.post(
        "/api/v1/auth/login", json={"password": admin_password}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 43200
    assert body["access_token"]


async def test_login_wrong_password_401(client):
    resp = await client.post(
        "/api/v1/auth/login", json={"password": "senha-errada"}
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
        "/api/v1/auth/login", json={"password": admin_password}
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
