"""Global search routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.roles import UserRole
from app.database import get_db
from app.models.customer import Customer
from app.models.sale import Sale
from app.models.user import User
from app.schemas import SearchResult
from app.utils.helpers import get_manager_employee_ids, user_search_filter

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=list[SearchResult])
async def global_search(
    q: str = Query(min_length=1),
    type: Optional[str] = Query(None, pattern="^(customers|employees|managers|sales)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    results: list[SearchResult] = []
    term = f"%{q}%"

    if type in (None, "customers") and current_user.role in (
        UserRole.ADMIN.value,
        UserRole.MANAGER.value,
        UserRole.EMPLOYEE.value,
    ):
        stmt = select(Customer).where(
            or_(Customer.name.ilike(term), Customer.email.ilike(term), Customer.phone.ilike(term))
        ).limit(10)
        if current_user.role == UserRole.EMPLOYEE.value:
            stmt = stmt.where(Customer.created_by_employee_id == current_user.id)
        elif current_user.role == UserRole.MANAGER.value:
            employee_ids = await get_manager_employee_ids(db, current_user.id)
            stmt = stmt.where(Customer.created_by_employee_id.in_(employee_ids or [-1]))
        for c in (await db.execute(stmt)).scalars().all():
            results.append(SearchResult(type="customer", id=c.id, title=c.name, subtitle=c.email or c.phone))

    if type in (None, "employees", "managers") and current_user.role == UserRole.ADMIN.value:
        roles = [UserRole.EMPLOYEE.value] if type == "employees" else [UserRole.MANAGER.value] if type == "managers" else [UserRole.EMPLOYEE.value, UserRole.MANAGER.value]
        stmt = select(User).where(User.role.in_(roles))
        if filt := user_search_filter(q):
            stmt = stmt.where(filt)
        stmt = stmt.limit(10)
        for u in (await db.execute(stmt)).scalars().all():
            results.append(
                SearchResult(type=u.role, id=u.id, title=f"{u.first_name} {u.last_name}", subtitle=u.email)
            )

    if type in (None, "sales") and current_user.role in (
        UserRole.ADMIN.value,
        UserRole.MANAGER.value,
        UserRole.EMPLOYEE.value,
    ):
        stmt = select(Sale).where(Sale.notes.ilike(term)).limit(10)
        if current_user.role == UserRole.EMPLOYEE.value:
            stmt = stmt.where(Sale.employee_id == current_user.id)
        elif current_user.role == UserRole.MANAGER.value:
            employee_ids = await get_manager_employee_ids(db, current_user.id)
            stmt = stmt.where(Sale.employee_id.in_(employee_ids or [-1]))
        for s in (await db.execute(stmt)).scalars().all():
            results.append(SearchResult(type="sale", id=s.id, title=f"Sale #{s.id}", subtitle=f"${s.amount:.2f}"))

    return results
