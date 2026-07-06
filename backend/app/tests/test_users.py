"""User API tests."""

import pytest
from httpx import AsyncClient


async def _get_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin123!"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    token = await _get_token(client)
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    token = await _get_token(client)
    response = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "first_name": "New",
            "last_name": "Employee",
            "email": "newemp@test.com",
            "role": "employee",
            "password": "Employee123!",
        },
    )
    assert response.status_code == 201
    assert response.json()["email"] == "newemp@test.com"
