"""Branch access and daily session helpers."""

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch
from app.models.employee_branch import EmployeeBranch, EmployeeBranchSession


async def get_active_branches(db: AsyncSession) -> list[Branch]:
    result = await db.execute(
        select(Branch).where(Branch.is_active.is_(True)).order_by(Branch.name)
    )
    return list(result.scalars().all())


async def employee_can_use_branch(db: AsyncSession, employee_id: int, branch_id: int) -> bool:
    branch = await db.get(Branch, branch_id)
    if not branch or not branch.is_active:
        return False

    assigned = await db.execute(
        select(EmployeeBranch.id).where(EmployeeBranch.employee_id == employee_id).limit(1)
    )
    if assigned.scalar_one_or_none() is None:
        return True

    result = await db.execute(
        select(EmployeeBranch.id).where(
            EmployeeBranch.employee_id == employee_id,
            EmployeeBranch.branch_id == branch_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def get_employee_branches(db: AsyncSession, employee_id: int) -> list[Branch]:
    assigned = await db.execute(
        select(EmployeeBranch.branch_id).where(EmployeeBranch.employee_id == employee_id)
    )
    branch_ids = list(assigned.scalars().all())
    if not branch_ids:
        return await get_active_branches(db)

    result = await db.execute(
        select(Branch)
        .where(Branch.id.in_(branch_ids), Branch.is_active.is_(True))
        .order_by(Branch.name)
    )
    return list(result.scalars().all())


async def record_branch_session(db: AsyncSession, employee_id: int, branch_id: int) -> EmployeeBranchSession:
    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(EmployeeBranchSession).where(
            EmployeeBranchSession.employee_id == employee_id,
            EmployeeBranchSession.work_date == today,
        )
    )
    session = result.scalar_one_or_none()
    if session:
        session.branch_id = branch_id
        return session

    session = EmployeeBranchSession(employee_id=employee_id, branch_id=branch_id, work_date=today)
    db.add(session)
    await db.flush()
    return session


async def get_branch_price(db: AsyncSession, branch_id: int) -> float:
    branch = await db.get(Branch, branch_id)
    if branch and branch.is_active:
        return branch.price_per_photo
    from app.services.print_pricing import DEFAULT_PRICE_EGP

    return DEFAULT_PRICE_EGP
