"""Seed default users and sample data."""

import asyncio

from sqlalchemy import select

from app.core.roles import UserRole
from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models.manager_employee import ManagerEmployee
from app.models.user import User
from app.services.print_pricing import get_or_create_print_settings


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == "admin@system.com"))
        if not existing.scalar_one_or_none():
            admin = User(
                first_name="System",
                last_name="Admin",
                email="admin@system.com",
                phone="+10000000001",
                role=UserRole.ADMIN.value,
                password_hash=hash_password("Admin123!"),
            )
            manager = User(
                first_name="Default",
                last_name="Manager",
                email="manager@system.com",
                phone="+10000000002",
                role=UserRole.MANAGER.value,
                password_hash=hash_password("Manager123!"),
            )
            employee = User(
                first_name="Default",
                last_name="Employee",
                email="employee@system.com",
                phone="+10000000003",
                role=UserRole.EMPLOYEE.value,
                password_hash=hash_password("Employee123!"),
            )
            db.add_all([admin, manager, employee])
            await db.flush()

            assignment = ManagerEmployee(manager_id=manager.id, employee_id=employee.id)
            db.add(assignment)
            print("Seed data created successfully.")
        else:
            print("Seed data already exists, skipping users.")

        await get_or_create_print_settings(db)
        await db.commit()

    print("  Admin:    admin@system.com / Admin123!")
    print("  Manager:  manager@system.com / Manager123!")
    print("  Employee: employee@system.com / Employee123!")
    print("  Default print price: 120 EGP per photo")


if __name__ == "__main__":
    asyncio.run(seed())
