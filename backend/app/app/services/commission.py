"""Employee commission calculation based on monthly photo targets."""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance import AttendanceRecord
from app.models.employee_target import EmployeeMonthlyTarget
from app.models.sale import Sale

DEFAULT_COMMISSION_EGP = 6.0
DEFAULT_AFTER_TARGET_COMMISSION_EGP = 12.0


@dataclass
class CommissionBreakdown:
    employee_id: int
    year: int
    month: int
    target_photos: int
    photos_printed: float
    photos_at_base_rate: float
    photos_at_bonus_rate: float
    base_commission: float
    bonus_commission: float
    total_commission: float
    target_met: bool
    progress_percent: float


def month_range(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start, end


async def get_photos_printed_in_month(
    db: AsyncSession, employee_id: int, year: int, month: int
) -> float:
    credited_sales = await get_credited_sales_for_employee(db, employee_id, year, month)
    return round(sum(count for _, count in credited_sales), 2)


async def get_credited_sales_for_employee(
    db: AsyncSession, employee_id: int, year: int, month: int
) -> list[tuple[Sale, float]]:
    start, end = month_range(year, month)
    start_date = start.date()
    end_date = end.date()

    attendance_result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.work_date >= start_date,
            AttendanceRecord.work_date < end_date,
            or_(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.partner_employee_id == employee_id,
            ),
        )
    )
    attendance_rows = list(attendance_result.scalars().all())
    attendance_by_owner_day = {(row.employee_id, row.work_date): row for row in attendance_rows}
    sale_employee_ids = {employee_id}
    sale_employee_ids.update(row.employee_id for row in attendance_rows)

    sales_result = await db.execute(
        select(Sale)
        .options(selectinload(Sale.branch))
        .where(
            Sale.employee_id.in_(sale_employee_ids or {-1}),
            Sale.created_at >= start,
            Sale.created_at < end,
        )
        .order_by(Sale.created_at.asc(), Sale.id.asc())
    )

    credited: list[tuple[Sale, float]] = []
    for sale in sales_result.scalars().all():
        attendance = attendance_by_owner_day.get((sale.employee_id, sale.created_at.date()))
        has_partner = bool(attendance and attendance.partner_employee_id)
        if sale.employee_id == employee_id:
            credited.append((sale, sale.photo_count / 2 if has_partner else float(sale.photo_count)))
        elif attendance and attendance.partner_employee_id == employee_id:
            credited.append((sale, sale.photo_count / 2))
    return credited


async def get_employee_target(
    db: AsyncSession, employee_id: int, year: int, month: int
) -> EmployeeMonthlyTarget | None:
    result = await db.execute(
        select(EmployeeMonthlyTarget).where(
            EmployeeMonthlyTarget.employee_id == employee_id,
            EmployeeMonthlyTarget.year == year,
            EmployeeMonthlyTarget.month == month,
        )
    )
    return result.scalar_one_or_none()


def calculate_commission(
    photos_printed: float,
    target_photos: int,
    base_rate: float = DEFAULT_COMMISSION_EGP,
    after_target_rate: float = DEFAULT_AFTER_TARGET_COMMISSION_EGP,
) -> CommissionBreakdown:
    target = max(target_photos, 0)
    photos = max(photos_printed, 0)
    at_base = min(photos, target) if target > 0 else photos
    at_bonus = max(0, photos - target) if target > 0 else 0
    base_commission = round(at_base * base_rate, 2)
    bonus_commission = round(at_bonus * after_target_rate, 2)
    progress = round((photos / target * 100), 1) if target > 0 else 0.0
    return CommissionBreakdown(
        employee_id=0,
        year=0,
        month=0,
        target_photos=target,
        photos_printed=photos,
        photos_at_base_rate=at_base,
        photos_at_bonus_rate=at_bonus,
        base_commission=base_commission,
        bonus_commission=bonus_commission,
        total_commission=round(base_commission + bonus_commission, 2),
        target_met=photos >= target if target > 0 else False,
        progress_percent=min(progress, 100.0) if target > 0 else 0.0,
    )


async def calculate_branch_commission(
    db: AsyncSession, employee_id: int, year: int, month: int, target_photos: int
) -> CommissionBreakdown:
    credited_sales = await get_credited_sales_for_employee(db, employee_id, year, month)
    target = max(target_photos, 0)
    photos_printed = 0
    photos_at_base = 0
    photos_at_bonus = 0
    base_commission = 0.0
    bonus_commission = 0.0

    for sale, credited_count in credited_sales:
        count = max(credited_count, 0)
        if target > 0:
            remaining_base = max(target - photos_printed, 0)
            base_count = min(count, remaining_base)
            bonus_count = count - base_count
        else:
            base_count = count
            bonus_count = 0

        branch = sale.branch
        base_rate = branch.commission_per_photo if branch else DEFAULT_COMMISSION_EGP
        bonus_rate = (
            branch.commission_after_target_per_photo
            if branch
            else DEFAULT_AFTER_TARGET_COMMISSION_EGP
        )

        photos_at_base += base_count
        photos_at_bonus += bonus_count
        base_commission += base_count * base_rate
        bonus_commission += bonus_count * bonus_rate
        photos_printed += count

    progress = round((photos_printed / target * 100), 1) if target > 0 else 0.0
    return CommissionBreakdown(
        employee_id=employee_id,
        year=year,
        month=month,
        target_photos=target,
        photos_printed=photos_printed,
        photos_at_base_rate=photos_at_base,
        photos_at_bonus_rate=photos_at_bonus,
        base_commission=round(base_commission, 2),
        bonus_commission=round(bonus_commission, 2),
        total_commission=round(base_commission + bonus_commission, 2),
        target_met=photos_printed >= target if target > 0 else False,
        progress_percent=progress if target > 0 else 0.0,
    )


async def get_commission_breakdown(
    db: AsyncSession, employee_id: int, year: int, month: int
) -> CommissionBreakdown:
    target_row = await get_employee_target(db, employee_id, year, month)
    target_photos = target_row.target_photos if target_row else 0
    breakdown = await calculate_branch_commission(db, employee_id, year, month, target_photos)
    if target_photos > 0 and breakdown.photos_printed > target_photos:
        breakdown.progress_percent = round((breakdown.photos_printed / target_photos) * 100, 1)
    return breakdown
