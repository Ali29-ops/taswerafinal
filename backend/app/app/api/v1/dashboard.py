"""Dashboard statistics routes."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.core.roles import UserRole
from app.database import get_db
from app.models.customer import Customer
from app.models.employee_target import EmployeeMonthlyTarget
from app.models.photo import Photo
from app.models.sale import Sale
from app.models.user import User
from app.schemas import (
    ChartDataPoint,
    DashboardResponse,
    DashboardStats,
    EmployeeTargetResponse,
    SaleResponse,
    UserResponse,
)
from app.services.commission import get_commission_breakdown
from app.services.print_pricing import get_print_price
from app.utils.helpers import get_all_employee_ids, get_manager_employee_ids

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def sale_to_response(sale: Sale) -> SaleResponse:
    return SaleResponse(
        id=sale.id,
        customer_id=sale.customer_id,
        employee_id=sale.employee_id,
        small_photo_count=sale.small_photo_count,
        large_photo_count=sale.large_photo_count,
        photo_count=sale.photo_count,
        price_per_photo=sale.price_per_photo,
        amount=sale.amount,
        notes=sale.notes,
        created_at=sale.created_at,
        customer_name=sale.customer.name if sale.customer else None,
        employee_name=f"{sale.employee.first_name} {sale.employee.last_name}" if sale.employee else None,
    )


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = DashboardStats()
    recent_sales: list[SaleResponse] = []
    revenue_chart: list[ChartDataPoint] = []
    assigned_employees: list[UserResponse] = []
    recent_customers = []
    employee_targets: list[EmployeeTargetResponse] = []

    stats.print_price_per_photo = await get_print_price(db)
    now = datetime.now(timezone.utc)
    cy, cm = now.year, now.month

    if current_user.role == UserRole.ADMIN.value:
        stats.total_sales = (await db.execute(select(func.count(Sale.id)))).scalar() or 0
        stats.total_revenue = (await db.execute(select(func.coalesce(func.sum(Sale.amount), 0)))).scalar() or 0
        stats.total_photos_printed = (await db.execute(select(func.coalesce(func.sum(Sale.photo_count), 0)))).scalar() or 0
        stats.total_customers = (await db.execute(select(func.count(Customer.id)))).scalar() or 0
        stats.total_employees = (
            await db.execute(select(func.count(User.id)).where(User.role == UserRole.EMPLOYEE.value))
        ).scalar() or 0
        stats.total_managers = (
            await db.execute(select(func.count(User.id)).where(User.role == UserRole.MANAGER.value))
        ).scalar() or 0
        stats.total_uploads = (await db.execute(select(func.count(Photo.id)))).scalar() or 0

        sales_result = await db.execute(
            select(Sale).options(selectinload(Sale.customer), selectinload(Sale.employee))
            .order_by(Sale.created_at.desc()).limit(10)
        )
        recent_sales = [sale_to_response(s) for s in sales_result.scalars().all()]

    elif current_user.role == UserRole.MANAGER.value:
        employee_ids = await get_manager_employee_ids(db, current_user.id)
        if employee_ids:
            stats.team_sales = (
                await db.execute(select(func.count(Sale.id)).where(Sale.employee_id.in_(employee_ids)))
            ).scalar() or 0
            stats.team_revenue = (
                await db.execute(select(func.coalesce(func.sum(Sale.amount), 0)).where(Sale.employee_id.in_(employee_ids)))
            ).scalar() or 0
            team_photos_printed = 0.0
            for employee_id in employee_ids:
                breakdown = await get_commission_breakdown(db, employee_id, cy, cm)
                team_photos_printed += breakdown.photos_printed
            stats.team_photos_printed = round(team_photos_printed, 2)
            stats.total_uploads = (
                await db.execute(select(func.count(Photo.id)).where(Photo.uploaded_by_employee_id.in_(employee_ids)))
            ).scalar() or 0
            emp_result = await db.execute(select(User).where(User.id.in_(employee_ids)))
            assigned_employees = [UserResponse.model_validate(u) for u in emp_result.scalars().all()]
            sales_result = await db.execute(
                select(Sale).options(selectinload(Sale.customer), selectinload(Sale.employee))
                .where(Sale.employee_id.in_(employee_ids))
                .order_by(Sale.created_at.desc()).limit(10)
            )
            recent_sales = [sale_to_response(s) for s in sales_result.scalars().all()]

            target_employee_ids = await get_all_employee_ids(db)
            for emp_id in target_employee_ids:
                target_row = await db.execute(
                    select(EmployeeMonthlyTarget).where(
                        EmployeeMonthlyTarget.employee_id == emp_id,
                        EmployeeMonthlyTarget.year == cy,
                        EmployeeMonthlyTarget.month == cm,
                    )
                )
                t = target_row.scalar_one_or_none()
                emp = await db.get(User, emp_id)
                breakdown = await get_commission_breakdown(db, emp_id, cy, cm)
                employee_targets.append(
                    EmployeeTargetResponse(
                        id=t.id if t else None,
                        employee_id=emp_id,
                        employee_name=f"{emp.first_name} {emp.last_name}" if emp else None,
                        year=cy,
                        month=cm,
                        target_photos=t.target_photos if t else 0,
                        photos_printed=breakdown.photos_printed,
                        progress_percent=breakdown.progress_percent,
                        target_met=breakdown.target_met,
                        base_commission=breakdown.base_commission,
                        bonus_commission=breakdown.bonus_commission,
                        total_commission=breakdown.total_commission,
                        photos_at_base_rate=breakdown.photos_at_base_rate,
                        photos_at_bonus_rate=breakdown.photos_at_bonus_rate,
                    )
                )

    elif current_user.role == UserRole.EMPLOYEE.value:
        stats.my_sales = (
            await db.execute(select(func.count(Sale.id)).where(Sale.employee_id == current_user.id))
        ).scalar() or 0
        stats.my_revenue = (
            await db.execute(select(func.coalesce(func.sum(Sale.amount), 0)).where(Sale.employee_id == current_user.id))
        ).scalar() or 0
        stats.my_uploads = (
            await db.execute(select(func.count(Photo.id)).where(Photo.uploaded_by_employee_id == current_user.id))
        ).scalar() or 0
        sales_result = await db.execute(
            select(Sale).options(selectinload(Sale.customer), selectinload(Sale.employee))
            .where(Sale.employee_id == current_user.id)
            .order_by(Sale.created_at.desc()).limit(10)
        )
        recent_sales = [sale_to_response(s) for s in sales_result.scalars().all()]
        cust_result = await db.execute(
            select(Customer).where(Customer.created_by_employee_id == current_user.id)
            .order_by(Customer.created_at.desc()).limit(10)
        )
        recent_customers = cust_result.scalars().all()

        breakdown = await get_commission_breakdown(db, current_user.id, cy, cm)
        stats.my_commission = breakdown.total_commission
        stats.my_photos_printed = breakdown.photos_printed
        target_row = await db.execute(
            select(EmployeeMonthlyTarget).where(
                EmployeeMonthlyTarget.employee_id == current_user.id,
                EmployeeMonthlyTarget.year == cy,
                EmployeeMonthlyTarget.month == cm,
            )
        )
        t = target_row.scalar_one_or_none()
        stats.my_target_photos = t.target_photos if t else 0
        stats.my_target_progress = breakdown.progress_percent

    now = datetime.now(timezone.utc)
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        stmt = select(func.coalesce(func.sum(Sale.amount), 0)).where(
            Sale.created_at >= day_start, Sale.created_at < day_end
        )
        if current_user.role == UserRole.EMPLOYEE.value:
            stmt = stmt.where(Sale.employee_id == current_user.id)
        elif current_user.role == UserRole.MANAGER.value:
            employee_ids = await get_manager_employee_ids(db, current_user.id)
            stmt = stmt.where(Sale.employee_id.in_(employee_ids or [-1]))
        value = (await db.execute(stmt)).scalar() or 0
        revenue_chart.append(ChartDataPoint(label=day_start.strftime("%a"), value=float(value)))

    return DashboardResponse(
        stats=stats,
        recent_sales=recent_sales,
        revenue_chart=revenue_chart,
        assigned_employees=assigned_employees,
        recent_customers=recent_customers,
        employee_targets=employee_targets,
    )
