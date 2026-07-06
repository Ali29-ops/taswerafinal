"""Sales and print pricing tests."""

import pytest
from httpx import AsyncClient


async def _get_token(client: AsyncClient, email: str = "employee@system.com", password: str = "Employee123!") -> str:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        response = await client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Admin123!"})
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_get_print_price(client: AsyncClient, db_session):
    from app.services.print_pricing import get_or_create_print_settings
    await get_or_create_print_settings(db_session)
    await db_session.commit()

    token = await _get_token(client)
    response = await client.get(
        "/api/v1/settings/print-price",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["price_per_photo"] == 120.0
    assert response.json()["currency"] == "EGP"
