"""Custom print package routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_roles
from app.core.roles import UserRole
from app.database import get_db
from app.models.print_package import PrintPackage
from app.models.user import User
from app.schemas import MessageResponse, PrintPackageCreate, PrintPackageResponse, PrintPackageUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/packages", tags=["Packages"])


def _can_manage(package: PrintPackage, user: User) -> bool:
    return user.role in (UserRole.ADMIN.value, UserRole.MANAGER.value) or package.created_by_id == user.id


@router.get("", response_model=list[PrintPackageResponse])
async def list_packages(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PrintPackage).order_by(PrintPackage.photo_count.asc(), PrintPackage.price.asc())
    if not include_inactive:
        stmt = stmt.where(PrintPackage.is_active.is_(True))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=PrintPackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    payload: PrintPackageCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    package = PrintPackage(
        name=payload.name,
        photo_count=payload.photo_count,
        price=payload.price,
        is_active=payload.is_active,
        created_by_id=current_user.id,
    )
    db.add(package)
    await db.flush()
    await log_action(
        db,
        user_id=current_user.id,
        action="create_package",
        entity_type="print_package",
        entity_id=package.id,
        ip_address=request.client.host if request.client else None,
    )
    return package


@router.patch("/{package_id}", response_model=PrintPackageResponse)
async def update_package(
    package_id: int,
    payload: PrintPackageUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    package = await db.get(PrintPackage, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    if not _can_manage(package, current_user):
        raise HTTPException(status_code=403, detail="You can only edit packages you created")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(package, key, value)
    await log_action(
        db,
        user_id=current_user.id,
        action="update_package",
        entity_type="print_package",
        entity_id=package.id,
        ip_address=request.client.host if request.client else None,
    )
    return package


@router.delete("/{package_id}", response_model=MessageResponse)
async def delete_package(
    package_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    package = await db.get(PrintPackage, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    if not _can_manage(package, current_user):
        raise HTTPException(status_code=403, detail="You can only delete packages you created")
    await db.delete(package)
    await log_action(
        db,
        user_id=current_user.id,
        action="delete_package",
        entity_type="print_package",
        entity_id=package_id,
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message="Package deleted")
