"""User management routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_roles
from app.core.roles import UserRole
from app.core.security import hash_password
from app.database import get_db
from app.models.manager_employee import ManagerEmployee
from app.models.user import User
from app.schemas import MessageResponse, PaginatedResponse, UserCreate, UserResponse, UserRoleUpdate, UserUpdate
from app.services.audit import log_action
from app.utils.helpers import paginate, pagination_meta, user_search_filter

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User)
    if current_user.role == UserRole.MANAGER.value:
        stmt = stmt.where(User.role == UserRole.EMPLOYEE.value)
    if role:
        stmt = stmt.where(User.role == role)
    if search_filter := user_search_filter(search):
        stmt = stmt.where(search_filter)
    sort_col = getattr(User, sort_by, User.created_at)
    stmt = stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
    items, total = await paginate(db, stmt, page, page_size)
    return PaginatedResponse(items=items, **pagination_meta(total, page, page_size))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.MANAGER.value:
        if payload.role != UserRole.EMPLOYEE.value:
            raise HTTPException(status_code=403, detail="Managers can only create employees")

    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role,
        is_active=payload.is_active,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()

    if payload.role == UserRole.EMPLOYEE.value:
        if current_user.role == UserRole.MANAGER.value:
            manager_ids = [current_user.id]
        else:
            managers = await db.execute(
                select(User.id).where(User.role == UserRole.MANAGER.value, User.is_active.is_(True))
            )
            manager_ids = list(managers.scalars().all())

        for manager_id in manager_ids:
            existing_assignment = await db.execute(
                select(ManagerEmployee).where(
                    ManagerEmployee.manager_id == manager_id,
                    ManagerEmployee.employee_id == user.id,
                )
            )
            if not existing_assignment.scalar_one_or_none():
                db.add(ManagerEmployee(manager_id=manager_id, employee_id=user.id))

    await log_action(
        db,
        user_id=current_user.id,
        action="create_user",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role == UserRole.MANAGER.value and user.role != UserRole.EMPLOYEE.value:
        raise HTTPException(status_code=403, detail="Access denied")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserRoleUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.role not in (UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.EMPLOYEE.value):
        raise HTTPException(status_code=400, detail="Invalid role")

    user.role = payload.role
    await log_action(
        db,
        user_id=current_user.id,
        action="update_user_role",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await log_action(
        db,
        user_id=current_user.id,
        action="delete_user",
        entity_type="user",
        entity_id=user_id,
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message="User deleted")
