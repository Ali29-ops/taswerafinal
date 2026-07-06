"""Organization hierarchy with monthly target progress."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.core.roles import UserRole
from app.database import get_db
from app.models.manager_employee import ManagerEmployee
from app.models.user import User
from app.schemas import HierarchyNode, HierarchyResponse
from app.services.commission import get_commission_breakdown

router = APIRouter(prefix="/hierarchy", tags=["Hierarchy"])


def _current_year_month() -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    return now.year, now.month


async def _employee_node(
    db: AsyncSession, employee: User, year: int, month: int
) -> HierarchyNode:
    breakdown = await get_commission_breakdown(db, employee.id, year, month)
    return HierarchyNode(
        id=employee.id,
        name=f"{employee.first_name} {employee.last_name}",
        role=UserRole.EMPLOYEE.value,
        target_photos=breakdown.target_photos,
        photos_printed=breakdown.photos_printed,
        progress_percent=breakdown.progress_percent,
        target_met=breakdown.target_met,
        total_commission=breakdown.total_commission,
    )


async def _manager_branch(
    db: AsyncSession, manager: User, employee_ids: list[int], year: int, month: int
) -> HierarchyNode:
    children: list[HierarchyNode] = []
    team_printed = 0
    team_target = 0

    for emp_id in employee_ids:
        employee = await db.get(User, emp_id)
        if not employee or employee.role != UserRole.EMPLOYEE.value:
            continue
        node = await _employee_node(db, employee, year, month)
        children.append(node)
        team_printed += node.photos_printed
        team_target += node.target_photos

    team_progress = round((team_printed / team_target) * 100, 1) if team_target > 0 else 0.0
    return HierarchyNode(
        id=manager.id,
        name=f"{manager.first_name} {manager.last_name}",
        role=UserRole.MANAGER.value,
        children=children,
        team_photos_printed=team_printed,
        team_target_photos=team_target,
        team_progress_percent=team_progress,
    )


@router.get("", response_model=HierarchyResponse)
async def get_hierarchy(
    year: int | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    y, m = year or _current_year_month()[0], month or _current_year_month()[1]

    assignments_result = await db.execute(select(ManagerEmployee))
    assignments = assignments_result.scalars().all()
    manager_to_employees: dict[int, list[int]] = {}
    assigned_employee_ids: set[int] = set()
    for assignment in assignments:
        manager_to_employees.setdefault(assignment.manager_id, []).append(assignment.employee_id)
        assigned_employee_ids.add(assignment.employee_id)

    if current_user.role == UserRole.MANAGER.value:
        employee_ids = manager_to_employees.get(current_user.id, [])
        root = await _manager_branch(db, current_user, employee_ids, y, m)
        return HierarchyResponse(year=y, month=m, tree=root)

    admins_result = await db.execute(
        select(User)
        .where(User.role == UserRole.ADMIN.value, User.is_active.is_(True))
        .order_by(User.first_name, User.last_name)
    )
    admins = admins_result.scalars().all()

    managers_result = await db.execute(
        select(User)
        .where(User.role == UserRole.MANAGER.value, User.is_active.is_(True))
        .order_by(User.first_name, User.last_name)
    )
    managers = managers_result.scalars().all()

    manager_children: list[HierarchyNode] = []
    for manager in managers:
        emp_ids = manager_to_employees.get(manager.id, [])
        manager_children.append(await _manager_branch(db, manager, emp_ids, y, m))

    unassigned_result = await db.execute(
        select(User)
        .where(User.role == UserRole.EMPLOYEE.value, User.is_active.is_(True))
        .order_by(User.first_name, User.last_name)
    )
    unassigned_employees = [
        emp for emp in unassigned_result.scalars().all() if emp.id not in assigned_employee_ids
    ]
    if unassigned_employees:
        unassigned_nodes = [await _employee_node(db, emp, y, m) for emp in unassigned_employees]
        manager_children.append(
            HierarchyNode(
                id=0,
                name="Unassigned Employees",
                role="group",
                children=unassigned_nodes,
            )
        )

    primary_admin = admins[0] if admins else None
    root = HierarchyNode(
        id=primary_admin.id if primary_admin else 0,
        name=f"{primary_admin.first_name} {primary_admin.last_name}" if primary_admin else "TASWERA",
        role=UserRole.ADMIN.value,
        children=manager_children,
    )

    return HierarchyResponse(year=y, month=m, tree=root)
