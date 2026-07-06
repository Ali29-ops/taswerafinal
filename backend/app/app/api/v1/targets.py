"""Employee monthly targets and commission routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_roles
from app.core.roles import UserRole
from app.database import get_db
from app.models.employee_target import EmployeeMonthlyTarget
from app.models.user import User
from app.schemas import EmployeeTargetResponse, EmployeeTargetSet
from app.services.audit import log_action
from app.services.commission import get_commission_breakdown
from app.utils.helpers import get_all_employee_ids

router = APIRouter(prefix="/targets", tags=["Targets"])


def _current_year_month() -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    return now.year, now.month


async def _can_manage_employee(db: AsyncSession, manager: User, employee_id: int) -> bool:
    if manager.role in (UserRole.ADMIN.value, UserRole.MANAGER.value):
        employee = await db.get(User, employee_id)
        return employee is not None and employee.role == UserRole.EMPLOYEE.value
    return False


async def _build_target_response(db: AsyncSession, target: EmployeeMonthlyTarget) -> EmployeeTargetResponse:
    employee = await db.get(User, target.employee_id)
    breakdown = await get_commission_breakdown(db, target.employee_id, target.year, target.month)
    return EmployeeTargetResponse(
        id=target.id,
        employee_id=target.employee_id,
        employee_name=f"{employee.first_name} {employee.last_name}" if employee else None,
        year=target.year,
        month=target.month,
        target_photos=target.target_photos,
        photos_printed=breakdown.photos_printed,
        progress_percent=breakdown.progress_percent,
        target_met=breakdown.target_met,
        base_commission=breakdown.base_commission,
        bonus_commission=breakdown.bonus_commission,
        total_commission=breakdown.total_commission,
        photos_at_base_rate=breakdown.photos_at_base_rate,
        photos_at_bonus_rate=breakdown.photos_at_bonus_rate,
    )


@router.get("", response_model=list[EmployeeTargetResponse])
async def list_targets(
    year: int | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    y, m = year or _current_year_month()[0], month or _current_year_month()[1]
    stmt = select(EmployeeMonthlyTarget).where(
        EmployeeMonthlyTarget.year == y,
        EmployeeMonthlyTarget.month == m,
    )

    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(EmployeeMonthlyTarget.employee_id == current_user.id)

    result = await db.execute(stmt.order_by(EmployeeMonthlyTarget.employee_id))
    targets = result.scalars().all()
    responses = []
    for t in targets:
        responses.append(await _build_target_response(db, t))

    if current_user.role in (UserRole.MANAGER.value, UserRole.ADMIN.value):
        employee_ids = await get_all_employee_ids(db)
        existing_ids = {r.employee_id for r in responses}
        for emp_id in employee_ids or []:
            if emp_id in existing_ids:
                continue
            emp = await db.get(User, emp_id)
            breakdown = await get_commission_breakdown(db, emp_id, y, m)
            responses.append(
                EmployeeTargetResponse(
                    employee_id=emp_id,
                    employee_name=f"{emp.first_name} {emp.last_name}" if emp else None,
                    year=y,
                    month=m,
                    target_photos=0,
                    photos_printed=breakdown.photos_printed,
                    progress_percent=0,
                    target_met=False,
                    base_commission=breakdown.base_commission,
                    bonus_commission=breakdown.bonus_commission,
                    total_commission=breakdown.total_commission,
                    photos_at_base_rate=breakdown.photos_at_base_rate,
                    photos_at_bonus_rate=breakdown.photos_at_bonus_rate,
                )
            )

    elif current_user.role == UserRole.EMPLOYEE.value and not responses:
        breakdown = await get_commission_breakdown(db, current_user.id, y, m)
        responses.append(
            EmployeeTargetResponse(
                employee_id=current_user.id,
                employee_name=f"{current_user.first_name} {current_user.last_name}",
                year=y,
                month=m,
                target_photos=0,
                photos_printed=breakdown.photos_printed,
                progress_percent=0,
                target_met=False,
                base_commission=breakdown.base_commission,
                bonus_commission=breakdown.bonus_commission,
                total_commission=breakdown.total_commission,
                photos_at_base_rate=breakdown.photos_at_base_rate,
                photos_at_bonus_rate=breakdown.photos_at_bonus_rate,
            )
        )

    return responses


@router.put("", response_model=EmployeeTargetResponse)
async def set_target(
    payload: EmployeeTargetSet,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    employee = await db.get(User, payload.employee_id)
    if not employee or employee.role != UserRole.EMPLOYEE.value:
        raise HTTPException(status_code=400, detail="Invalid employee")

    if not await _can_manage_employee(db, current_user, payload.employee_id):
        raise HTTPException(status_code=403, detail="You cannot set targets for this employee")

    result = await db.execute(
        select(EmployeeMonthlyTarget).where(
            EmployeeMonthlyTarget.employee_id == payload.employee_id,
            EmployeeMonthlyTarget.year == payload.year,
            EmployeeMonthlyTarget.month == payload.month,
        )
    )
    target = result.scalar_one_or_none()
    if target:
        target.target_photos = payload.target_photos
        target.set_by_id = current_user.id
    else:
        target = EmployeeMonthlyTarget(
            employee_id=payload.employee_id,
            year=payload.year,
            month=payload.month,
            target_photos=payload.target_photos,
            set_by_id=current_user.id,
        )
        db.add(target)

    await db.flush()
    await log_action(
        db,
        user_id=current_user.id,
        action="set_employee_target",
        entity_type="employee_target",
        entity_id=target.id,
        ip_address=request.client.host if request.client else None,
    )
    return await _build_target_response(db, target)


@router.get("/commission/me", response_model=EmployeeTargetResponse)
async def my_commission(
    year: int | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    y, m = year or _current_year_month()[0], month or _current_year_month()[1]
    target = await db.execute(
        select(EmployeeMonthlyTarget).where(
            EmployeeMonthlyTarget.employee_id == current_user.id,
            EmployeeMonthlyTarget.year == y,
            EmployeeMonthlyTarget.month == m,
        )
    )
    row = target.scalar_one_or_none()
    if row:
        return await _build_target_response(db, row)
    breakdown = await get_commission_breakdown(db, current_user.id, y, m)
    return EmployeeTargetResponse(
        employee_id=current_user.id,
        employee_name=f"{current_user.first_name} {current_user.last_name}",
        year=y,
        month=m,
        target_photos=0,
        photos_printed=breakdown.photos_printed,
        progress_percent=0,
        target_met=False,
        base_commission=breakdown.base_commission,
        bonus_commission=breakdown.bonus_commission,
        total_commission=breakdown.total_commission,
        photos_at_base_rate=breakdown.photos_at_base_rate,
        photos_at_bonus_rate=breakdown.photos_at_bonus_rate,
    )
