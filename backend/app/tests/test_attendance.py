"""Attendance API tests."""

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


async def _create_employee(client: AsyncClient, admin_token: str) -> None:
    response = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "first_name": "Attendance",
            "last_name": "Employee",
            "email": "attendance@test.com",
            "role": "employee",
            "password": "Employee123!",
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_employee_can_check_in_and_out(client: AsyncClient):
    admin_token = await _login(client, "admin@test.com", "Admin123!")
    await _create_employee(client, admin_token)
    employee_token = await _login(client, "attendance@test.com", "Employee123!")

    check_in = await client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert check_in.status_code == 200
    assert check_in.json()["status"] == "checked_in"

    check_out = await client.post(
        "/api/v1/attendance/check-out",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert check_out.status_code == 200
    assert check_out.json()["status"] == "checked_out"


@pytest.mark.asyncio
async def test_admin_can_view_attendance(client: AsyncClient):
    admin_token = await _login(client, "admin@test.com", "Admin123!")
    await _create_employee(client, admin_token)
    employee_token = await _login(client, "attendance@test.com", "Employee123!")
    await client.post("/api/v1/attendance/check-in", headers={"Authorization": f"Bearer {employee_token}"})

    response = await client.get(
        "/api/v1/attendance",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()[0]["employee_name"] == "Attendance Employee"
