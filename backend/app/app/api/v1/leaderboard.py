"""Monthly employee leaderboard across all branches."""

import calendar
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.roles import UserRole
from app.database import get_db
from app.models.branch import Branch
from app.models.employee_branch import EmployeeBranch
from app.models.employee_target import EmployeeMonthlyTarget
from app.models.sale import Sale
from app.models.user import User
from app.schemas import LeaderboardEntry, LeaderboardResponse
from app.services.commission import get_commission_breakdown

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


def _blur_start(year: int, month: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, max(1, last_day - 4))


async def _employee_branch_name(db: AsyncSession, employee_id: int, year: int, month: int) -> str | None:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end_month = month + 1
    end_year = year
    if end_month == 13:
        end_month = 1
        end_year += 1
    end = datetime(end_year, end_month, 1, tzinfo=timezone.utc)

    active_branch = await db.execute(
        select(Branch.name)
        .join(Sale, Sale.branch_id == Branch.id)
        .where(Sale.employee_id == employee_id, Sale.created_at >= start, Sale.created_at < end)
        .group_by(Branch.id, Branch.name)
        .order_by(func.count(Sale.id).desc())
        .limit(1)
    )
    branch_name = active_branch.scalar_one_or_none()
    if branch_name:
        return branch_name

    assigned_branch = await db.execute(
        select(Branch.name)
        .join(EmployeeBranch, EmployeeBranch.branch_id == Branch.id)
        .where(EmployeeBranch.employee_id == employee_id)
        .order_by(Branch.name.asc())
        .limit(1)
    )
    return assigned_branch.scalar_one_or_none()


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    year: int | None = Query(None, ge=2020, le=2100),
    month: int | None = Query(None, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    selected_year = year or now.year
    selected_month = month or now.month
    blur_starts_on = _blur_start(selected_year, selected_month)
    should_blur = (
        current_user.role == UserRole.EMPLOYEE.value
        and selected_year == now.year
        and selected_month == now.month
        and now.date() >= blur_starts_on
    )

    result = await db.execute(
        select(User)
        .where(User.role == UserRole.EMPLOYEE.value, User.is_active.is_(True))
        .order_by(User.first_name.asc(), User.last_name.asc())
    )
    employees = result.scalars().all()

    rows: list[LeaderboardEntry] = []
    for employee in employees:
        breakdown = await get_commission_breakdown(db, employee.id, selected_year, selected_month)
        target_result = await db.execute(
            select(EmployeeMonthlyTarget.target_photos).where(
                EmployeeMonthlyTarget.employee_id == employee.id,
                EmployeeMonthlyTarget.year == selected_year,
                EmployeeMonthlyTarget.month == selected_month,
            )
        )
        target_photos = target_result.scalar_one_or_none() or 0
        rows.append(
            LeaderboardEntry(
                rank=0,
                employee_id=employee.id,
                employee_name=f"{employee.first_name} {employee.last_name}",
                branch_name=await _employee_branch_name(db, employee.id, selected_year, selected_month),
                photos_printed=breakdown.photos_printed,
                target_photos=target_photos,
                progress_percent=breakdown.progress_percent,
                total_commission=breakdown.total_commission,
            )
        )

    rows.sort(key=lambda item: (item.photos_printed, item.progress_percent, item.total_commission), reverse=True)
    for index, row in enumerate(rows, start=1):
        row.rank = index
        if should_blur:
            row.employee_id = None
            row.employee_name = f"Hidden #{index}"
            row.branch_name = None
            row.photos_printed = 0
            row.target_photos = 0
            row.progress_percent = 0
            row.total_commission = 0

    return LeaderboardResponse(
        year=selected_year,
        month=selected_month,
        is_blurred=should_blur,
        blur_starts_on=blur_starts_on,
        entries=rows,
    )
