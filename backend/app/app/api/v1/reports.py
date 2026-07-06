"""Report generation routes."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_roles
from app.core.roles import UserRole
from app.database import get_db
from app.models.manager_employee import ManagerEmployee
from app.models.sale import Sale
from app.models.user import User
from app.services.commission import get_commission_breakdown
from app.services.reports import export_csv, export_excel, export_pdf, format_report_filename
from app.utils.helpers import get_manager_employee_ids

router = APIRouter(prefix="/reports", tags=["Reports"])


async def _fetch_sales_in_range(db: AsyncSession, start: datetime, end: datetime, employee_ids: Optional[list[int]] = None):
    stmt = (
        select(Sale)
        .options(selectinload(Sale.customer), selectinload(Sale.employee))
        .where(Sale.created_at >= start, Sale.created_at < end)
        .order_by(Sale.created_at.desc())
    )
    if employee_ids is not None:
        stmt = stmt.where(Sale.employee_id.in_(employee_ids or [-1]))
    result = await db.execute(stmt)
    return result.scalars().all()


def _sales_rows(sales) -> list[dict]:
    return [
        {
            "id": s.id,
            "customer": s.customer.name if s.customer else "",
            "employee": f"{s.employee.first_name} {s.employee.last_name}" if s.employee else "",
            "small_photos": s.small_photo_count,
            "large_photos": s.large_photo_count,
            "photos_printed": s.photo_count,
            "price_per_photo_egp": s.price_per_photo,
            "amount_egp": s.amount,
            "notes": s.notes or "",
            "created_at": s.created_at.isoformat(),
        }
        for s in sales
    ]


@router.get("/daily")
async def daily_report(
    format: str = Query("json", pattern="^(json|csv|excel|pdf)$"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    employee_ids = None
    if current_user.role == UserRole.MANAGER.value:
        employee_ids = await get_manager_employee_ids(db, current_user.id)
    sales = await _fetch_sales_in_range(db, start, end, employee_ids)
    return _export_report("daily_sales", "Daily Sales Report", sales, format)


@router.get("/monthly")
async def monthly_report(
    format: str = Query("json", pattern="^(json|csv|excel|pdf)$"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        end = start.replace(year=now.year + 1, month=1)
    else:
        end = start.replace(month=now.month + 1)
    employee_ids = None
    if current_user.role == UserRole.MANAGER.value:
        employee_ids = await get_manager_employee_ids(db, current_user.id)
    sales = await _fetch_sales_in_range(db, start, end, employee_ids)
    return _export_report("monthly_sales", "Monthly Sales Report", sales, format)


@router.get("/employee-performance")
async def employee_performance(
    format: str = Query("json", pattern="^(json|csv|excel|pdf)$"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    stmt = select(User).where(User.role == UserRole.EMPLOYEE.value)
    if current_user.role == UserRole.MANAGER.value:
        employee_ids = await get_manager_employee_ids(db, current_user.id)
        stmt = stmt.where(User.id.in_(employee_ids or [-1]))
    result = await db.execute(stmt.order_by(User.first_name, User.last_name))
    rows = []
    for employee in result.scalars().all():
        stats = await db.execute(
            select(func.count(Sale.id), func.coalesce(func.sum(Sale.amount), 0)).where(Sale.employee_id == employee.id)
        )
        sales_count, revenue = stats.one()
        breakdown = await get_commission_breakdown(db, employee.id, now.year, now.month)
        rows.append(
            {
                "employee_id": employee.id,
                "name": f"{employee.first_name} {employee.last_name}",
                "sales_count": sales_count,
                "photos_printed": breakdown.photos_printed,
                "revenue_egp": float(revenue),
            }
        )
    headers = ["employee_id", "name", "sales_count", "photos_printed", "revenue_egp"]
    return _export_generic("employee_performance", "Employee Performance Report", rows, headers, format)


@router.get("/manager-performance")
async def manager_performance(
    format: str = Query("json", pattern="^(json|csv|excel|pdf)$"),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    managers = (await db.execute(select(User).where(User.role == UserRole.MANAGER.value))).scalars().all()
    rows = []
    for mgr in managers:
        emp_ids = (
            await db.execute(select(ManagerEmployee.employee_id).where(ManagerEmployee.manager_id == mgr.id))
        ).scalars().all()
        if emp_ids:
            stats = await db.execute(
                select(func.count(Sale.id), func.coalesce(func.sum(Sale.amount), 0)).where(
                    Sale.employee_id.in_(emp_ids)
                )
            )
            count, revenue = stats.one()
        else:
            count, revenue = 0, 0
        rows.append(
            {
                "manager_id": mgr.id,
                "name": f"{mgr.first_name} {mgr.last_name}",
                "team_size": len(emp_ids),
                "sales_count": count,
                "revenue": float(revenue),
            }
        )
    headers = ["manager_id", "name", "team_size", "sales_count", "revenue"]
    return _export_generic("manager_performance", "Manager Performance Report", rows, headers, format)


@router.get("/revenue")
async def revenue_report(
    format: str = Query("json", pattern="^(json|csv|excel|pdf)$"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=30)
    employee_ids = None
    if current_user.role == UserRole.MANAGER.value:
        employee_ids = await get_manager_employee_ids(db, current_user.id)
    sales = await _fetch_sales_in_range(db, start, now, employee_ids)
    return _export_report("revenue", "Revenue Report (30 days)", sales, format)


def _export_report(prefix: str, title: str, sales, format: str):
    headers = ["id", "customer", "employee", "small_photos", "large_photos", "photos_printed", "price_per_photo_egp", "amount_egp", "notes", "created_at"]
    rows = _sales_rows(sales)
    if format == "json":
        return {"title": title, "rows": rows, "total_egp": sum(r["amount_egp"] for r in rows), "total_photos": sum(r["photos_printed"] for r in rows)}
    return _export_generic(prefix, title, rows, headers, format)


def _export_generic(prefix: str, title: str, rows: list[dict], headers: list[str], format: str):
    if format == "json":
        return {"title": title, "rows": rows}
    if format == "csv":
        content = export_csv(rows, headers)
        media = "text/csv"
        ext = "csv"
    elif format == "excel":
        content = export_excel(rows, headers, prefix)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
    elif format == "pdf":
        pdf_rows = [[row.get(h, "") for h in headers] for row in rows]
        content = export_pdf(title, headers, pdf_rows)
        media = "application/pdf"
        ext = "pdf"
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
    filename = format_report_filename(prefix, ext)
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
