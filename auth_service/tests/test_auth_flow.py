import pytest


@pytest.mark.asyncio
async def test_full_auth_flow(client) -> None:
    register_response = await client.post(
        "/auth/register",
        json={"email": "ivanov@email.com", "password": "StrongPassword123"},
    )

    assert register_response.status_code == 201
    registered_user = register_response.json()
    assert registered_user["email"] == "ivanov@email.com"
    assert "password_hash" not in registered_user

    login_response = await client.post(
        "/auth/login",
        data={"username": "ivanov@email.com", "password": "StrongPassword123"},
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "ivanov@email.com"


@pytest.mark.asyncio
async def test_duplicate_registration_returns_409(client) -> None:
    payload = {"email": "petrov@email.com", "password": "StrongPassword123"}

    first_response = await client.post("/auth/register", json=payload)
    second_response = await client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client) -> None:
    await client.post(
        "/auth/register",
        json={"email": "sidorov@email.com", "password": "StrongPassword123"},
    )

    response = await client.post(
        "/auth/login",
        data={"username": "sidorov@email.com", "password": "WrongPassword123"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client) -> None:
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_ping_returns_403_for_regular_user(client) -> None:
    await client.post(
        "/auth/register",
        json={"email": "kozlov@email.com", "password": "StrongPassword123"},
    )

    login_response = await client.post(
        "/auth/login",
        data={"username": "kozlov@email.com", "password": "StrongPassword123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = await client.get(
        "/auth/admin/ping",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]
