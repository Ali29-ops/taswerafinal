"""Shared query helpers."""

import math
from typing import Optional, Sequence, TypeVar

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import UserRole
from app.models.manager_employee import ManagerEmployee
from app.models.user import User

T = TypeVar("T")


async def paginate(
    db: AsyncSession,
    stmt: Select,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[T], int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total


def pagination_meta(total: int, page: int, page_size: int) -> dict:
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, math.ceil(total / page_size)) if total else 1,
    }


async def get_manager_employee_ids(db: AsyncSession, manager_id: int) -> list[int]:
    result = await db.execute(
        select(ManagerEmployee.employee_id).where(ManagerEmployee.manager_id == manager_id)
    )
    return list(result.scalars().all())


async def get_all_employee_ids(db: AsyncSession) -> list[int]:
    result = await db.execute(
        select(User.id).where(User.role == UserRole.EMPLOYEE.value, User.is_active.is_(True))
    )
    return list(result.scalars().all())


def user_search_filter(search: Optional[str]):
    if not search:
        return None
    term = f"%{search}%"
    return or_(
        User.first_name.ilike(term),
        User.last_name.ilike(term),
        User.email.ilike(term),
        User.phone.ilike(term),
    )


def can_manage_users(role: str) -> bool:
    return role == UserRole.ADMIN.value
