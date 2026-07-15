"""Customer management routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_roles
from app.core.roles import UserRole
from app.core.security import generate_secure_token
from app.database import get_db
from app.models.customer import Customer
from app.models.user import User
from app.schemas import CustomerCreate, CustomerResponse, CustomerUpdate, MessageResponse, PaginatedResponse, QRCodeResponse
from app.services.audit import log_action
from app.services.qr import generate_qr_code_data_url
from app.utils.helpers import get_manager_employee_ids, paginate, pagination_meta
from app.utils.urls import public_base_url

router = APIRouter(prefix="/customers", tags=["Customers"])


async def _scoped_customer_query(current_user: User, db: AsyncSession):
    stmt = select(Customer)
    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(Customer.created_by_employee_id == current_user.id)
    elif current_user.role == UserRole.MANAGER.value:
        employee_ids = await get_manager_employee_ids(db, current_user.id)
        stmt = stmt.where(Customer.created_by_employee_id.in_(employee_ids or [-1]))
    return stmt


@router.get("", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE)
    ),
    db: AsyncSession = Depends(get_db),
):
    stmt = await _scoped_customer_query(current_user, db)
    if search:
        term = f"%{search}%"
        stmt = stmt.where(or_(Customer.name.ilike(term), Customer.email.ilike(term), Customer.phone.ilike(term)))
    sort_col = getattr(Customer, sort_by, Customer.created_at)
    stmt = stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
    items, total = await paginate(db, stmt, page, page_size)
    return PaginatedResponse(items=items, **pagination_meta(total, page, page_size))


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    customer = Customer(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        qr_token=generate_secure_token(32),
        created_by_employee_id=current_user.id if current_user.role == UserRole.EMPLOYEE.value else current_user.id,
    )
    db.add(customer)
    await db.flush()
    await log_action(
        db,
        user_id=current_user.id,
        action="create_customer",
        entity_type="customer",
        entity_id=customer.id,
        ip_address=request.client.host if request.client else None,
    )
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    stmt = (await _scoped_customer_query(current_user, db)).where(Customer.id == customer_id)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Customer).where(Customer.id == customer_id)
    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(Customer.created_by_employee_id == current_user.id)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    await log_action(
        db,
        user_id=current_user.id,
        action="update_customer",
        entity_type="customer",
        entity_id=customer.id,
        ip_address=request.client.host if request.client else None,
    )
    return customer


@router.get("/{customer_id}/qr", response_model=QRCodeResponse)
async def get_customer_qr(
    customer_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Customer).where(Customer.id == customer_id)
    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(Customer.created_by_employee_id == current_user.id)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    qr_url, qr_image = generate_qr_code_data_url(customer.qr_token, public_base_url(request))
    return QRCodeResponse(
        customer_id=customer.id,
        qr_token=customer.qr_token,
        qr_url=qr_url,
        qr_image_base64=qr_image,
    )


@router.post("/{customer_id}/regenerate-qr", response_model=QRCodeResponse)
async def regenerate_qr(
    customer_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Customer).where(Customer.id == customer_id)
    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(Customer.created_by_employee_id == current_user.id)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer.qr_token = generate_secure_token(32)
    qr_url, qr_image = generate_qr_code_data_url(customer.qr_token, public_base_url(request))
    await log_action(
        db,
        user_id=current_user.id,
        action="regenerate_qr",
        entity_type="customer",
        entity_id=customer.id,
        ip_address=request.client.host if request.client else None,
    )
    return QRCodeResponse(
        customer_id=customer.id,
        qr_token=customer.qr_token,
        qr_url=qr_url,
        qr_image_base64=qr_image,
    )
