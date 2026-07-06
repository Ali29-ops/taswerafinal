"""Employee attendance routes."""

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_roles
from app.core.roles import UserRole
from app.database import get_db
from app.models.attendance import AttendanceRecord
from app.models.user import User
from app.schemas import AttendanceCheckOutRequest, AttendanceResponse, UserResponse
from app.services.audit import log_action
from app.services.reports import export_csv, export_excel, export_pdf, format_report_filename
from app.utils.helpers import get_manager_employee_ids

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _record_response(record: AttendanceRecord) -> AttendanceResponse:
    total_minutes = None
    if record.check_out_at:
        total_minutes = max(0, int((record.check_out_at - record.check_in_at).total_seconds() // 60))
    employee_name = None
    if record.employee:
        employee_name = f"{record.employee.first_name} {record.employee.last_name}"
    partner_name = None
    if record.partner:
        partner_name = f"{record.partner.first_name} {record.partner.last_name}"
    return AttendanceResponse(
        id=record.id,
        employee_id=record.employee_id,
        employee_name=employee_name,
        partner_employee_id=record.partner_employee_id,
        partner_employee_name=partner_name,
        branch_id=record.branch_id,
        branch_name=record.branch.name if record.branch else None,
        work_date=record.work_date,
        check_in_at=record.check_in_at,
        check_out_at=record.check_out_at,
        total_minutes=total_minutes,
        status="checked_out" if record.check_out_at else "checked_in",
    )


async def _get_today_record(db: AsyncSession, employee_id: int) -> AttendanceRecord | None:
    result = await db.execute(
        select(AttendanceRecord)
        .options(
            selectinload(AttendanceRecord.employee),
            selectinload(AttendanceRecord.partner),
            selectinload(AttendanceRecord.branch),
        )
        .where(AttendanceRecord.employee_id == employee_id, AttendanceRecord.work_date == _today())
    )
    return result.scalar_one_or_none()


@router.get("/me/today", response_model=AttendanceResponse | None)
async def my_today_attendance(
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    return _record_response(record) if (record := await _get_today_record(db, current_user.id)) else None


@router.post("/check-in", response_model=AttendanceResponse)
async def check_in(
    request: Request,
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    existing = await _get_today_record(db, current_user.id)
    if existing:
        return _record_response(existing)

    branch_id = getattr(request.state, "branch_id", None)
    record = AttendanceRecord(
        employee_id=current_user.id,
        branch_id=branch_id,
        work_date=_today(),
        check_in_at=datetime.now(timezone.utc),
    )
    db.add(record)
    await db.flush()
    await log_action(
        db,
        user_id=current_user.id,
        action="check_in",
        entity_type="attendance",
        entity_id=record.id,
        ip_address=request.client.host if request.client else None,
    )
    created = await _get_today_record(db, current_user.id)
    return _record_response(created or record)


@router.post("/check-out", response_model=AttendanceResponse)
async def check_out(
    request: Request,
    payload: AttendanceCheckOutRequest | None = None,
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_today_record(db, current_user.id)
    if not record:
        raise HTTPException(status_code=400, detail="You need to check in first")
    partner_id = payload.partner_employee_id if payload else None
    if partner_id:
        if partner_id == current_user.id:
            raise HTTPException(status_code=400, detail="Partner must be another employee")
        partner = await db.get(User, partner_id)
        if not partner or partner.role != UserRole.EMPLOYEE.value or not partner.is_active:
            raise HTTPException(status_code=400, detail="Invalid shift partner")
        record.partner_employee_id = partner_id
    if not record.check_out_at:
        record.check_out_at = datetime.now(timezone.utc)
        await db.flush()
        await log_action(
            db,
            user_id=current_user.id,
            action="check_out",
            entity_type="attendance",
            entity_id=record.id,
            ip_address=request.client.host if request.client else None,
        )
    return _record_response(record)


@router.get("/partners", response_model=list[UserResponse])
async def attendance_partners(
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .where(User.role == UserRole.EMPLOYEE.value, User.is_active.is_(True), User.id != current_user.id)
        .order_by(User.first_name, User.last_name)
    )
    return list(result.scalars().all())


@router.get("", response_model=list[AttendanceResponse])
async def list_attendance(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    records = await _fetch_attendance(db, current_user, start_date, end_date, employee_id)
    return [_record_response(record) for record in records]


@router.get("/sheet")
async def attendance_sheet(
    format: str = Query("excel", pattern="^(csv|excel|pdf)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    records = await _fetch_attendance(db, current_user, start_date, end_date, employee_id)
    rows = [_attendance_row(record) for record in records]
    headers = [
        "employee_id",
        "employee",
        "branch",
        "partner",
        "work_date",
        "check_in_at",
        "check_out_at",
        "total_minutes",
        "status",
    ]
    return _export_sheet(rows, headers, format)


async def _fetch_attendance(
    db: AsyncSession,
    current_user: User,
    start_date: date | None,
    end_date: date | None,
    employee_id: int | None,
) -> list[AttendanceRecord]:
    stmt = (
        select(AttendanceRecord)
        .options(
            selectinload(AttendanceRecord.employee),
            selectinload(AttendanceRecord.partner),
            selectinload(AttendanceRecord.branch),
        )
        .order_by(AttendanceRecord.work_date.desc(), AttendanceRecord.check_in_at.desc())
    )
    if start_date:
        stmt = stmt.where(AttendanceRecord.work_date >= start_date)
    if end_date:
        stmt = stmt.where(AttendanceRecord.work_date <= end_date)
    if employee_id:
        stmt = stmt.where(AttendanceRecord.employee_id == employee_id)
    if current_user.role == UserRole.MANAGER.value:
        employee_ids = await get_manager_employee_ids(db, current_user.id)
        stmt = stmt.where(AttendanceRecord.employee_id.in_(employee_ids or [-1]))
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _attendance_row(record: AttendanceRecord) -> dict:
    response = _record_response(record)
    return {
        "employee_id": response.employee_id,
        "employee": response.employee_name or "",
        "branch": response.branch_name or "",
        "partner": response.partner_employee_name or "",
        "work_date": response.work_date.isoformat(),
        "check_in_at": response.check_in_at.isoformat(),
        "check_out_at": response.check_out_at.isoformat() if response.check_out_at else "",
        "total_minutes": response.total_minutes or "",
        "status": response.status,
    }


def _export_sheet(rows: list[dict], headers: list[str], format: str):
    title = "Attendance Sheet"
    if format == "csv":
        content = export_csv(rows, headers)
        media = "text/csv"
        ext = "csv"
    elif format == "excel":
        content = export_excel(rows, headers, "attendance")
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
    elif format == "pdf":
        content = export_pdf(title, headers, [[row.get(h, "") for h in headers] for row in rows])
        media = "application/pdf"
        ext = "pdf"
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{format_report_filename("attendance", ext)}"'},
    )
