"""Sales management routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_roles
from app.core.roles import UserRole
from app.database import get_db
from app.models.customer import Customer
from app.models.print_package import PrintPackage
from app.models.sale import Sale
from app.models.user import User
from app.core.security import generate_secure_token
from app.schemas import PaginatedResponse, SaleCreate, SaleInvoiceQRResponse, SaleResponse, SaleUpdate
from app.services.audit import log_action
from app.services.invoices import ensure_invoice_token, invoice_qr_data_url, invoice_url
from app.services.print_pricing import calculate_sale_amount, get_print_price
from app.services.reports import export_csv, export_excel, format_report_filename
from app.utils.helpers import get_manager_employee_ids, paginate, pagination_meta
from app.utils.urls import public_base_url

router = APIRouter(prefix="/sales", tags=["Sales"])


def sale_to_response(sale: Sale, base_url: str | None = None) -> SaleResponse:
    customer_name = sale.customer.name if sale.customer else None
    employee_name = f"{sale.employee.first_name} {sale.employee.last_name}" if sale.employee else None
    branch_name = sale.branch.name if sale.branch else None
    invoice_link = invoice_url(sale.invoice_token, base_url) if sale.invoice_token else None
    return SaleResponse(
        id=sale.id,
        customer_id=sale.customer_id,
        employee_id=sale.employee_id,
        branch_id=sale.branch_id,
        package_id=sale.package_id,
        package_name=sale.package.name if sale.package else None,
        small_photo_count=sale.small_photo_count,
        large_photo_count=sale.large_photo_count,
        photo_count=sale.photo_count,
        price_per_photo=sale.price_per_photo,
        amount=sale.amount,
        payment_status=sale.payment_status,
        payment_method=sale.payment_method,
        notes=sale.notes,
        created_at=sale.created_at,
        customer_name=customer_name,
        employee_name=employee_name,
        branch_name=branch_name,
        invoice_url=invoice_link,
    )


async def _scoped_sales_query(current_user: User, db: AsyncSession):
    stmt = select(Sale).options(
        selectinload(Sale.customer), selectinload(Sale.employee), selectinload(Sale.branch), selectinload(Sale.package)
    )
    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(Sale.employee_id == current_user.id)
    elif current_user.role == UserRole.MANAGER.value:
        employee_ids = await get_manager_employee_ids(db, current_user.id)
        stmt = stmt.where(Sale.employee_id.in_(employee_ids or [-1]))
    return stmt


@router.get("", response_model=PaginatedResponse[SaleResponse])
async def list_sales(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    stmt = await _scoped_sales_query(current_user, db)
    sort_col = getattr(Sale, sort_by, Sale.created_at)
    stmt = stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
    items, total = await paginate(db, stmt, page, page_size)
    return PaginatedResponse(
        items=[sale_to_response(s, public_base_url(request)) for s in items],
        **pagination_meta(total, page, page_size),
    )


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    payload: SaleCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Customer).where(Customer.id == payload.customer_id)
    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(Customer.created_by_employee_id == current_user.id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")

    branch_id = getattr(request.state, "branch_id", None)
    if current_user.role == UserRole.EMPLOYEE.value:
        if not branch_id:
            raise HTTPException(status_code=400, detail="Select a branch when signing in")
    else:
        branch_id = payload.branch_id or branch_id
        if not branch_id:
            raise HTTPException(status_code=400, detail="Branch is required")

    small_count = payload.small_photo_count
    large_count = payload.large_photo_count
    total_count = small_count + large_count
    if total_count <= 0 and payload.photo_count:
        total_count = payload.photo_count
        small_count = payload.photo_count
    if total_count <= 0:
        raise HTTPException(status_code=400, detail="Enter at least one small or large photo")

    price_per_photo = await get_print_price(db, branch_id)
    package = None
    amount = calculate_sale_amount(total_count, price_per_photo)
    if payload.package_id:
        package = await db.get(PrintPackage, payload.package_id)
        if not package or not package.is_active:
            raise HTTPException(status_code=404, detail="Package not found")
        if total_count != package.photo_count:
            raise HTTPException(status_code=400, detail=f"This package requires exactly {package.photo_count} photos")
        amount = package.price
    if payload.payment_status == "paid" and not payload.payment_method:
        raise HTTPException(status_code=400, detail="Choose cash, visa, or scans for paid invoices")
    if payload.payment_status == "unpaid":
        payload.payment_method = None
    sale = Sale(
        customer_id=payload.customer_id,
        employee_id=current_user.id,
        branch_id=branch_id,
        package_id=package.id if package else None,
        small_photo_count=small_count,
        large_photo_count=large_count,
        photo_count=total_count,
        price_per_photo=price_per_photo,
        amount=amount,
        payment_status=payload.payment_status,
        payment_method=payload.payment_method,
        invoice_token=generate_secure_token(24),
        notes=payload.notes,
    )
    db.add(sale)
    await db.flush()
    await db.refresh(sale, ["customer", "employee", "branch", "package"])
    await log_action(
        db,
        user_id=current_user.id,
        action="create_sale",
        entity_type="sale",
        entity_id=sale.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.flush()
    await db.refresh(sale, ["package"])
    return sale_to_response(sale, public_base_url(request))


@router.get("/{sale_id}/invoice-qr", response_model=SaleInvoiceQRResponse)
async def get_sale_invoice_qr(
    sale_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    stmt = (await _scoped_sales_query(current_user, db)).where(Sale.id == sale_id)
    result = await db.execute(stmt)
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    token = await ensure_invoice_token(db, sale)
    url, qr = invoice_qr_data_url(token, public_base_url(request))
    return SaleInvoiceQRResponse(sale_id=sale.id, invoice_url=url, qr_image_base64=qr)


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    stmt = (await _scoped_sales_query(current_user, db)).where(Sale.id == sale_id)
    result = await db.execute(stmt)
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale_to_response(sale, public_base_url(request))


@router.patch("/{sale_id}", response_model=SaleResponse)
async def update_sale(
    sale_id: int,
    payload: SaleUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Sale).options(selectinload(Sale.customer), selectinload(Sale.employee), selectinload(Sale.package)).where(Sale.id == sale_id)
    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(Sale.employee_id == current_user.id)
    result = await db.execute(stmt)
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    data = payload.model_dump(exclude_unset=True)
    package_changed = "package_id" in data
    if package_changed:
        package_id = data.pop("package_id")
        if package_id:
            package = await db.get(PrintPackage, package_id)
            if not package or not package.is_active:
                raise HTTPException(status_code=404, detail="Package not found")
            sale.package_id = package.id
        else:
            sale.package_id = None
    if "small_photo_count" in data or "large_photo_count" in data:
        sale.small_photo_count = data.pop("small_photo_count", sale.small_photo_count)
        sale.large_photo_count = data.pop("large_photo_count", sale.large_photo_count)
        sale.photo_count = sale.small_photo_count + sale.large_photo_count
        if sale.photo_count <= 0:
            raise HTTPException(status_code=400, detail="Enter at least one small or large photo")
        data.pop("photo_count", None)
        sale.amount = calculate_sale_amount(sale.photo_count, sale.price_per_photo)
    elif "photo_count" in data:
        sale.photo_count = data.pop("photo_count")
        sale.small_photo_count = sale.photo_count
        sale.large_photo_count = 0
        sale.amount = calculate_sale_amount(sale.photo_count, sale.price_per_photo)
    if package_changed or sale.package_id:
        if sale.package_id:
            package = await db.get(PrintPackage, sale.package_id)
            if package and sale.photo_count != package.photo_count:
                raise HTTPException(status_code=400, detail=f"This package requires exactly {package.photo_count} photos")
            if package:
                sale.amount = package.price
        else:
            sale.amount = calculate_sale_amount(sale.photo_count, sale.price_per_photo)
    payment_status = data.get("payment_status", sale.payment_status)
    payment_method = data.get("payment_method", sale.payment_method)
    if payment_status == "paid" and not payment_method:
        raise HTTPException(status_code=400, detail="Choose cash, visa, or scans for paid invoices")
    if payment_status == "unpaid":
        data["payment_method"] = None
    for key, value in data.items():
        setattr(sale, key, value)
    await log_action(
        db,
        user_id=current_user.id,
        action="update_sale",
        entity_type="sale",
        entity_id=sale.id,
        ip_address=request.client.host if request.client else None,
    )
    return sale_to_response(sale, public_base_url(request))


@router.get("/export/{format}")
async def export_sales(
    format: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Sale).options(selectinload(Sale.customer), selectinload(Sale.employee), selectinload(Sale.package)).order_by(Sale.created_at.desc())
    result = await db.execute(stmt)
    sales = result.scalars().all()
    headers = ["id", "customer", "employee", "package", "small_photos", "large_photos", "photos_printed", "price_per_photo", "amount_egp", "payment_status", "payment_method", "notes", "created_at"]
    rows = [
        {
            "id": s.id,
            "customer": s.customer.name if s.customer else "",
            "employee": f"{s.employee.first_name} {s.employee.last_name}" if s.employee else "",
            "package": s.package.name if s.package else "",
            "small_photos": s.small_photo_count,
            "large_photos": s.large_photo_count,
            "photos_printed": s.photo_count,
            "price_per_photo": s.price_per_photo,
            "amount_egp": s.amount,
            "payment_status": s.payment_status,
            "payment_method": s.payment_method or "",
            "notes": s.notes or "",
            "created_at": s.created_at.isoformat(),
        }
        for s in sales
    ]
    if format == "csv":
        content = export_csv(rows, headers)
        media = "text/csv"
    elif format == "excel":
        content = export_excel(rows, headers, "Sales")
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        raise HTTPException(status_code=400, detail="Use csv or excel format")
    filename = format_report_filename("sales", format if format != "excel" else "xlsx")
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
